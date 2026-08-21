from django.template.loader import render_to_string

from ai.intake import get_choices_context
from ai.services import (
    SESSION_EXPIRED_MESSAGE,
    accept_draft,
    apply_intake_choice,
    clear_draft,
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


def build_ai_chat_response(user, session_id, history):
    intake = get_intake(user.id, session_id)
    choices = get_choices_context(intake)
    choices_html = render_to_string(
        "ai/chat_choices.html",
        {
            "choices": choices,
            "session_id": session_id,
        },
    )

    draft = get_draft(user.id, session_id)
    preview = draft_to_preview(draft)
    draft_html = render_to_string(
        "ai/program_draft.html",
        {
            "draft": preview,
            "session_id": session_id,
        },
    )

    composer_placeholder = DEFAULT_COMPOSER_PLACEHOLDER
    if intake and (intake.get("awaiting_free_text_for") or "").strip():
        composer_placeholder = "Type your answer..."

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
    }
    return {
        "status": 200,
        "headers": [],
        "json_content": json_content,
    }


def prepare_send_message(user, attributes):
    session_id = attributes.get("session_id") or attributes.get("data-session-id", "")
    message = attributes.get("message", "")
    prep = prepare_chat_send(user, session_id, message)
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
            "payload": build_ai_chat_response(user, session_id, prep["history"]),
        }
    return {
        "phase": "complete",
        "payload": build_ai_chat_response(user, session_id, prep["history"]),
    }


def run_send_message_generation(user, session_id, history):
    history = run_generation_stages(user, session_id, history)
    return build_ai_chat_response(user, session_id, history)


def handle_intake_choice(user, attributes):
    session_id = attributes.get("session_id") or attributes.get("data-session-id", "")
    choice_id = attributes.get("choice") or attributes.get("data-choice", "")
    result = apply_intake_choice(user, session_id, choice_id)
    if result.get("expired"):
        return build_expired_chat_response()
    return build_ai_chat_response(user, session_id, result["history"])


def handle_accept_draft(user, attributes):
    session_id = attributes.get("session_id") or attributes.get("data-session-id", "")
    program = accept_draft(user, session_id)
    if not program:
        toast_html = render_toast("No program draft to accept.", variant="danger")
        return {
            "status": 400,
            "headers": [],
            "json_content": {
                "toast_html": toast_html,
                "toast_delay_ms": 2500,
            },
        }
    return {
        "status": 302,
        "headers": [["Location", f"/programs/{program.pk}/"]],
        "json_content": {},
    }


def handle_discard_draft(user, attributes):
    session_id = attributes.get("session_id") or attributes.get("data-session-id", "")
    clear_draft(user.id, session_id)
    draft_html = render_to_string(
        "ai/program_draft.html",
        {
            "draft": None,
            "session_id": session_id,
        },
    )
    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "target": "#ai-program-draft",
            "html": draft_html,
            "toast_html": render_toast("Draft discarded", variant="success"),
            "toast_delay_ms": 1500,
        },
    }
