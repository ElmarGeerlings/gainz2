from django.template.loader import render_to_string

from ai.services import (
    accept_draft,
    clear_draft,
    enrich_draft_for_preview,
    get_draft,
    send_chat_message,
)
from gainz2.utils import render_toast


def render_draft_html(user, session_id):
    draft = get_draft(user.id, session_id)
    preview = enrich_draft_for_preview(draft)
    return render_to_string(
        "ai/program_draft.html",
        {
            "draft": preview,
            "session_id": session_id,
        },
    )


def handle_send_message(user, attributes):
    session_id = attributes.get("session_id") or attributes.get("data-session-id", "")
    message = attributes.get("message", "")
    history = send_chat_message(user, session_id, message)
    html = render_to_string(
        "ai/chat_messages.html",
        {"messages": history},
    )
    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "target": "#ai-chat-messages",
            "html": html,
            "draft_target": "#ai-program-draft",
            "draft_html": render_draft_html(user, session_id),
        },
    }


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
    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "target": "#ai-program-draft",
            "html": render_draft_html(user, session_id),
            "toast_html": render_toast("Draft discarded", variant="success"),
            "toast_delay_ms": 1500,
        },
    }
