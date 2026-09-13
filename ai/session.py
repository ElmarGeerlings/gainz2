import uuid
from types import SimpleNamespace

from ai.models import AiChat

GUEST_COOKIE_NAME = "ai_guest_id"
GUEST_COOKIE_MAX_AGE = 60 * 60 * 24 * 365


class ChatContext(SimpleNamespace):
    pass


def resolve_chat_context(user, guest_id):
    is_guest = not user.is_authenticated
    if is_guest and not guest_id:
        raise ValueError("guest_id is required for anonymous chat")
    owner_key = str(user.pk) if user.is_authenticated else str(guest_id)
    return ChatContext(
        user=user,
        guest_id=guest_id,
        is_guest=is_guest,
        owner_key=owner_key,
    )


def guest_id_from_cookies(cookies):
    raw = cookies.get(GUEST_COOKIE_NAME)
    if not raw:
        return None
    return uuid.UUID(raw)


def find_aichat(ctx, session_id):
    if ctx.is_guest:
        return AiChat.objects.filter(
            guest_id=ctx.guest_id,
            session_id=session_id,
        ).first()
    return AiChat.objects.filter(user=ctx.user, session_id=session_id).first()


def ensure_aichat(ctx, session_id, defaults):
    if ctx.is_guest:
        return AiChat.objects.get_or_create(
            guest_id=ctx.guest_id,
            session_id=session_id,
            defaults=defaults,
        )
    return AiChat.objects.get_or_create(
        user=ctx.user,
        session_id=session_id,
        defaults=defaults,
    )
