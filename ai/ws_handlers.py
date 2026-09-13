from django.template.loader import render_to_string

from ai.intake import get_choices_context
from ai.services import (
    SESSION_EXPIRED_MESSAGE,
    apply_intake_choice,
    draft_to_preview,
    get_draft,
    get_intake,
    prepare_chat_send,
    run_generation_stages,
)
from gainz2.utils import render_toast

DEFAULT_COMPOSER_PLACEHOLDER = "Type a message..."


def build_expired_chat_response():
    history = [{"role": "assistant", "content": SESSION_EXPIRED_MESSAGE}]
    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "target": "#ai-chat-messages",
            "html": render_to_string(
                "ai/chat_messages.html",
                {"chat_messages": history},
            ),
            "choices_target": "#ai-chat-choices",
            "choices_html": "",
            "draft_target": "#ai-program-draft",
            "draft_html": "",
            "composer_disabled": True,
        },
    }


def build_ai_chat_response(ctx, session_id, history):
    intake = get_intake(ctx.owner_key, session_id)
    phase = intake.get("phase") if intake else None

    choices = get_choices_context(intake)
    choices_html = render_to_string(
        "ai/chat_choices.html",
        {
            "choices": choices,
            "session_id": session_id,
        },
    )

    draft = get_draft(ctx.owner_key, session_id)
    preview = draft_to_preview(draft)
    draft_html = render_to_string(
        "ai/program_draft.html",
        {
            "draft": preview,
            "session_id": session_id,
            "phase": phase,
        },
    )

    composer_placeholder = DEFAULT_COMPOSER_PLACEHOLDER
    if intake and (intake.get("awaiting_free_text_for") or "").strip():
        composer_placeholder = "Type your answer..."

    composer_disabled = phase in ("quota_blocked", "done")

    json_content = {
        "target": "#ai-chat-messages",
        "html": render_to_string(
            "ai/chat_messages.html",
            {"chat_messages": history},
        ),
        "choices_target": "#ai-chat-choices",
        "choices_html": choices_html,
        "draft_target": "#ai-program-draft",
        "draft_html": draft_html,
        "composer_placeholder": composer_placeholder,
        "composer_disabled": composer_disabled,
        "scroll_to_draft": phase == "review" and preview is not None,
    }
    return {
        "status": 200,
        "headers": [],
        "json_content": json_content,
    }


def apply_program_redirect(response, program_id):
    if program_id:
        response["status"] = 302
        response["headers"] = [["Location", f"/programs/{program_id}/"]]
    return response


def prepare_send_message(ctx, attributes):
    session_id = attributes.get("session_id") or attributes.get("data-session-id", "")
    message = attributes.get("message", "")
    prep = prepare_chat_send(ctx, session_id, message)
    if prep["phase"] == "expired":
        return {
            "phase": "complete",
            "payload": build_expired_chat_response(),
        }
    if prep["phase"] == "generating":
        return {
            "phase": "generating",
            "session_id": prep["session_id"],
            "history": prep["history"],
            "payload": build_ai_chat_response(ctx, session_id, prep["history"]),
        }
    payload = build_ai_chat_response(ctx, session_id, prep["history"])
    apply_program_redirect(payload, prep.get("program_id"))
    return {
        "phase": "complete",
        "payload": payload,
    }


def run_send_message_generation(ctx, session_id, history):
    history = run_generation_stages(ctx, session_id, history)
    return build_ai_chat_response(ctx, session_id, history)


def handle_intake_choice(ctx, attributes):
    session_id = attributes.get("session_id") or attributes.get("data-session-id", "")
    choice_id = attributes.get("choice") or attributes.get("data-choice", "")
    result = apply_intake_choice(ctx, session_id, choice_id, attributes)
    if result.get("expired"):
        return build_expired_chat_response()
    if result.get("error") == "no_draft":
        toast_html = render_toast("No program draft to accept.", variant="danger")
        return {
            "status": 400,
            "headers": [],
            "json_content": {
                "toast_html": toast_html,
                "toast_delay_ms": 2500,
            },
        }
    if result.get("error") == "accept_failed":
        toast_html = render_toast("Could not save the program.", variant="danger")
        return {
            "status": 400,
            "headers": [],
            "json_content": {
                "toast_html": toast_html,
                "toast_delay_ms": 2500,
            },
        }
    response = build_ai_chat_response(ctx, session_id, result["history"])
    return apply_program_redirect(response, result.get("program_id"))
