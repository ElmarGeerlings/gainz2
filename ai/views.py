import uuid

from django.shortcuts import render


def chat_page(req_event):
    session_id = str(uuid.uuid4())
    return render(
        req_event,
        "ai/chat.html",
        {
            "title": "AI Chat",
            "session_id": session_id,
            "messages": [],
        },
    )
