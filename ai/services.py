import json

from django.conf import settings
from django_redis import get_redis_connection

from ai.providers.gemini import generate_reply as gemini_generate_reply

CHAT_HISTORY_TTL_SECONDS = 3600

CHAT_SYSTEM_PROMPT = (
    "You are a personal fitness coach in a chat. "
    "Ask one short question at a time. "
    "Keep replies brief and conversational. "
    "Do not generate workout programs or JSON yet — only chat to learn what the user needs."
)


def generate_reply(messages):
    provider = settings.AI_PROVIDER

    if provider == "gemini":
        return gemini_generate_reply(messages)

    raise ValueError(f"Unsupported AI provider: {provider}")
    

def get_history(user_id, session_id):
    redis = get_redis_connection("default")
    raw = redis.get(f"ai_chat:{user_id}:{session_id}")
    if not raw:
        return []
    return json.loads(raw.decode("utf-8"))


def save_history(user_id, session_id, history):
    redis = get_redis_connection("default")
    redis.set(
        f"ai_chat:{user_id}:{session_id}",
        json.dumps(history),
        ex=CHAT_HISTORY_TTL_SECONDS,
    )


def send_chat_message(user, session_id, message):
    message = (message or "").strip()
    if not message:
        return get_history(user.id, session_id)

    history = get_history(user.id, session_id)
    history.append({"role": "user", "content": message})

    reply = generate_reply(
        [{"role": "system", "content": CHAT_SYSTEM_PROMPT}] + history
    )
    history.append({"role": "assistant", "content": reply})
    save_history(user.id, session_id, history)
    return history
