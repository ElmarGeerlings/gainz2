import uuid
from django.shortcuts import render
from ai.intake import get_choices_context
from ai.services import init_chat_session


def chat_page(req_event):
    session_id = str(uuid.uuid4())
    intake, messages = init_chat_session(req_event.user.id, session_id)
    choices = get_choices_context(intake)
    return render(
        req_event,
        "ai/chat.html",
        {
            "title": "AI Chat",
            "session_id": session_id,
            "chat_messages": messages,
            "choices": choices,
        },
    )
