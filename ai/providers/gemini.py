import requests
from django.conf import settings


def generate_reply(messages):
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")

    system_instruction = None
    contents = []

    for message in messages:
        role = message["role"]
        content = message["content"]

        if role == "system":
            system_instruction = content
            continue

        gemini_role = "model" if role == "assistant" else "user"
        contents.append({
            "role": gemini_role,
            "parts": [{"text": content}],
        })

    payload = {"contents": contents}
    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}],
        }

    model = settings.AI_MODEL
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )

    response = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    response.raise_for_status()

    res = response.json()
    candidates = res.get("candidates") or []
    if not candidates:
        return "I didn't get a reply just now. Try sending that again."

    parts = (candidates[0].get("content") or {}).get("parts") or []
    if not parts or "text" not in parts[0]:
        return "I didn't get a reply just now. Try sending that again."

    return parts[0]["text"]
