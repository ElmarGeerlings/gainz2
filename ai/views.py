import json
import uuid

from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from ai.intake import get_choices_context
from ai.models import AiChat
from ai.services import draft_to_preview, init_chat_session
from utils.pagination import paginate


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


def dev_chats_list_page(req_event):
    if not req_event.user.is_dev:
        raise Http404()

    chats = AiChat.objects.select_related("user").annotate(
        api_call_count=Count("api_calls"),
    ).order_by("-created_at")
    page_obj = paginate(req_event, chats)
    return render(
        req_event,
        "ai/dev_chats_list.html",
        {
            "title": "Dev AI Chats",
            "page_obj": page_obj,
        },
    )


def dev_chat_detail_page(req_event, chat_id):
    if not req_event.user.is_dev:
        raise Http404()

    chat = get_object_or_404(AiChat.objects.select_related("user"), pk=chat_id)
    api_calls = []
    for call in chat.api_calls.order_by("created_at"):
        api_calls.append({
            "call": call,
            "request_json": json.dumps(call.request, indent=2) if call.request else "",
            "response_json": json.dumps(call.response, indent=2) if call.response else "",
        })
    draft_previews = []
    for index, draft in enumerate(chat.drafts or [], start=1):
        preview = draft_to_preview(draft)
        if preview:
            draft_previews.append({
                "index": index,
                "preview": preview,
            })

    return render(
        req_event,
        "ai/dev_chat_detail.html",
        {
            "title": f"Dev AI Chat {chat.pk}",
            "chat": chat,
            "intake_json": json.dumps(chat.intake, indent=2),
            "draft_previews": draft_previews,
            "api_calls": api_calls,
            "api_call_count": chat.api_calls.count(),
            "message_count": len(chat.messages or []),
            "draft_count": len(chat.drafts or []),
        },
    )
