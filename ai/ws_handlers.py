from django.template.loader import render_to_string

from ai.intake import get_choices_context
from ai.services import (
    accept_draft,
    apply_intake_choice,
    clear_draft,
    get_draft,
    get_intake,
    send_chat_message,
)
from gainz2.utils import render_toast

DEFAULT_COMPOSER_PLACEHOLDER = "Type a message..."


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
    preview = None
    if draft:
        routines = []
        for routine in draft["routines"]:
            exercises = []
            for item in routine["exercises"]:
                exercises.append({
                    "exercise_name": item["exercise_name"],
                    "exercise_type": item["exercise_type"],
                    "sets": item["sets"],
                })
            routines.append({
                "name": routine["name"],
                "exercises": exercises,
            })
        preview = {
            "name": draft["name"],
            "description": draft.get("description") or "",
            "routines": routines,
        }
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

    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "target": "#ai-chat-messages",
            "html": render_to_string(
                "ai/chat_messages.html",
                {"messages": history},
            ),
            "choices_target": "#ai-chat-choices",
            "choices_html": choices_html,
            "draft_target": "#ai-program-draft",
            "draft_html": draft_html,
            "composer_placeholder": composer_placeholder,
        },
    }


def handle_send_message(user, attributes):
    session_id = attributes.get("session_id") or attributes.get("data-session-id", "")
    message = attributes.get("message", "")
    history = send_chat_message(user, session_id, message)
    return build_ai_chat_response(user, session_id, history)


def handle_intake_choice(user, attributes):
    session_id = attributes.get("session_id") or attributes.get("data-session-id", "")
    choice_id = attributes.get("choice") or attributes.get("data-choice", "")
    history, intake = apply_intake_choice(user, session_id, choice_id)
    return build_ai_chat_response(user, session_id, history)


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
