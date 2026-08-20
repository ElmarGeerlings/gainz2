import re

import requests
from django.conf import settings

MAX_TOOL_ROUNDS = 8
RATE_LIMIT_REPLY = "I've hit the API rate limit. Wait a minute and try again."
API_ERROR_REPLY = "Sorry, something went wrong. Please try again later."


def strip_markdown(text):
    if not text:
        return text
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    return text


def messages_to_gemini_contents(messages):
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
    return system_instruction, contents


def generate_content_url(model):
    api_key = settings.GEMINI_API_KEY
    return (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )


def post_generate_request(payload, model):
    try:
        return requests.post(
            generate_content_url(model),
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )
    except requests.RequestException:
        return None


def post_generate_content(payload, model=None, use_generate_fallback=False):
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return None, "api_error"

    if model is None:
        model = settings.AI_MODEL

    response = post_generate_request(payload, model)
    if response is None:
        return None, "api_error"

    if response.status_code == 429 and use_generate_fallback:
        fallback = settings.AI_MODEL_GENERATE_FALLBACK
        if fallback and model != fallback:
            response = post_generate_request(payload, fallback)
            if response is None:
                return None, "api_error"
            model = fallback

    if response.status_code == 429:
        return None, "rate_limit"

    if response.status_code >= 400:
        return None, "api_error"

    return response.json(), None


def text_from_parts(parts):
    texts = []
    for part in parts:
        if "text" in part:
            texts.append(part["text"])
    return "\n".join(texts).strip()


def function_calls_from_parts(parts):
    calls = []
    for part in parts:
        if "functionCall" in part:
            calls.append(part["functionCall"])
    return calls


def generate_reply(messages, model=None):
    system_instruction, contents = messages_to_gemini_contents(messages)
    payload = {"contents": contents}
    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}],
        }

    use_generate_fallback = model == settings.AI_MODEL_GENERATE
    res, err = post_generate_content(
        payload,
        model=model,
        use_generate_fallback=use_generate_fallback,
    )
    if err == "rate_limit":
        return RATE_LIMIT_REPLY
    if err == "api_error" or not res:
        return API_ERROR_REPLY

    candidates = res.get("candidates") or []
    if not candidates:
        return "I didn't get a reply just now. Try sending that again."

    parts = (candidates[0].get("content") or {}).get("parts") or []
    text = text_from_parts(parts)
    if not text:
        return "I didn't get a reply just now. Try sending that again."
    return strip_markdown(text)


def generate_with_tools(messages, tools, user, session_id, model=None):
    from ai.services import execute_tool

    system_instruction, contents = messages_to_gemini_contents(messages)
    tools_payload = [{"functionDeclarations": tools}]
    use_generate_fallback = model == settings.AI_MODEL_GENERATE

    for round_index in range(MAX_TOOL_ROUNDS):
        payload = {
            "contents": contents,
            "tools": tools_payload,
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}],
            }

        res, err = post_generate_content(
            payload,
            model=model,
            use_generate_fallback=use_generate_fallback,
        )
        if err == "rate_limit":
            return RATE_LIMIT_REPLY
        if err == "api_error" or not res:
            return API_ERROR_REPLY

        candidates = res.get("candidates") or []
        if not candidates:
            return "I didn't get a reply just now. Try sending that again."

        model_content = candidates[0].get("content") or {}
        parts = model_content.get("parts") or []
        calls = function_calls_from_parts(parts)

        if not calls:
            text = text_from_parts(parts)
            if not text:
                return "I didn't get a reply just now. Try sending that again."
            return strip_markdown(text)

        if "role" not in model_content:
            model_content = {
                "role": "model",
                "parts": parts,
            }
        contents.append(model_content)

        response_parts = []
        for call in calls:
            name = call["name"]
            args = call.get("args") or {}
            result = execute_tool(name, args, user, session_id)
            function_response = {
                "name": name,
                "response": result,
            }
            if "id" in call:
                function_response["id"] = call["id"]
            response_parts.append({"functionResponse": function_response})

        contents.append({
            "role": "user",
            "parts": response_parts,
        })

    return "I hit the tool-call limit. Please try again with a simpler request."
