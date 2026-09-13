import json
import uuid

from django.db.models import Count
from django.shortcuts import get_object_or_404, render

from ai.intake import get_choices_context
from ai.models import AiChat
from ai.services import (
    GUEST_GEN_QUOTA_MESSAGE,
    draft_to_preview,
    guest_at_generation_limit,
    init_chat_session,
)
from programs.models import Program


def dev_chat_review_outcome(intake):
    if not intake:
        return None
    after_feedback = intake.get("after_feedback")
    if after_feedback == "done":
        return "accepted"
    if after_feedback == "start_over_ask":
        return "discarded"
    return None


def dev_chat_outcome_display(outcome, program_name=None):
    if outcome == "accepted":
        if program_name:
            return f"Accepted ({program_name})"
        return "Accepted"
    if outcome == "discarded":
        return "Discarded"
    return "—"
from ai.session import GUEST_COOKIE_MAX_AGE, GUEST_COOKIE_NAME, guest_id_from_cookies, resolve_chat_context
from utils.pagination import paginate


def chat_page(req_event):
    session_id = str(uuid.uuid4())
    guest_id = None
    if not req_event.user.is_authenticated:
        guest_id = guest_id_from_cookies(req_event.COOKIES)
        if not guest_id:
            guest_id = uuid.uuid4()
    ctx = resolve_chat_context(req_event.user, guest_id)
    composer_disabled = False
    if guest_at_generation_limit(ctx):
        intake = {"phase": "quota_blocked"}
        messages = [{"role": "assistant", "content": GUEST_GEN_QUOTA_MESSAGE}]
        composer_disabled = True
    else:
        intake, messages = init_chat_session(ctx.owner_key, session_id)
    choices = get_choices_context(intake)
    response = render(
        req_event,
        "ai/chat.html",
        {
            "title": "AI Chat",
            "session_id": session_id,
            "chat_messages": messages,
            "choices": choices,
            "is_guest": ctx.is_guest,
            "composer_disabled": composer_disabled,
        },
    )
    if ctx.is_guest:
        response.set_cookie(
            GUEST_COOKIE_NAME,
            str(guest_id),
            max_age=GUEST_COOKIE_MAX_AGE,
            httponly=True,
            samesite="Lax",
        )
    return response


def dev_chats_list_page(req_event):
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

    intake = chat.intake or {}
    review_outcome = dev_chat_review_outcome(intake)
    accepted_program_name = None
    program_id = intake.get("accepted_program_id")
    if program_id:
        program = Program.objects.filter(pk=program_id).first()
        if program:
            accepted_program_name = program.name
    review_outcome_label = dev_chat_outcome_display(review_outcome, accepted_program_name)

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
            "review_outcome_label": review_outcome_label,
        },
    )
