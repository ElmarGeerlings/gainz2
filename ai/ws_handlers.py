from django.template.loader import render_to_string

from ai.services import send_chat_message


def handle_send_message(user, attributes):
    session_id = attributes.get("session_id", "")
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
        },
    }
