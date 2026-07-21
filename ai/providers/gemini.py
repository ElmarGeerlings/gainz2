import requests
from django.conf import settings

MAX_TOOL_ROUNDS = 8


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


def post_generate_content(payload):
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")

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
    return response.json()


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


def generate_reply(messages):
    system_instruction, contents = messages_to_gemini_contents(messages)
    payload = {"contents": contents}
    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}],
        }

    res = post_generate_content(payload)
    candidates = res.get("candidates") or []
    if not candidates:
        return "I didn't get a reply just now. Try sending that again."

    parts = (candidates[0].get("content") or {}).get("parts") or []
    text = text_from_parts(parts)
    if not text:
        return "I didn't get a reply just now. Try sending that again."
    return text


def generate_with_tools(messages, tools, user, session_id):
    from ai.services import execute_tool

    system_instruction, contents = messages_to_gemini_contents(messages)
    tools_payload = [{"functionDeclarations": tools}]

    for round_index in range(MAX_TOOL_ROUNDS):
        payload = {
            "contents": contents,
            "tools": tools_payload,
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}],
            }

        res = post_generate_content(payload)
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
            return text

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
