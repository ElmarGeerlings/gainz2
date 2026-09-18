import json
import re

from django.conf import settings

from ai.intake import INTAKE_STEPS, INTAKE_STEP_KEYS
from ai.providers.gemini import generate_reply

VALID_INTAKE_VALUES = {
    step["key"]: {choice["id"] for choice in step["choices"]}
    for step in INTAKE_STEPS
}

PARSE_SYSTEM_PROMPT = (
    "You extract structured intake fields from a user message during program setup. "
    "Return JSON only, no markdown. Schema: "
    '{"off_script": false, "fields": {"goal": "hypertrophy", "level": "intermediate", '
    '"days": "4", "duration": "about_60", "equipment": "full_gym"}, '
    '"overwrite_fields": ["days"], '
    '"other_notes": {"goal": "powerbuilding"}, '
    '"constraints": "no deadlifts"}. '
    "Use only these field keys when confident: goal, level, days, duration, equipment. "
    "Use only these canonical values: "
    "goal: hypertrophy, strength, general_fitness, other; "
    "level: beginner, intermediate, advanced, other; "
    "days: 1, 2, 3, 4, 5, 6, 7; "
    "duration: under_45, about_60, 75_plus, other; "
    "equipment: full_gym, dumbbells_bar, bodyweight, other. "
    "Omit fields you are not confident about. "
    "If the user corrects a prior answer, include the field in fields and list its key in overwrite_fields. "
    "If answering via Other or free text and no chip id fits, set fields[key] to other and put the wording in other_notes[key]. "
    "When awaiting_free_text_for is set, prioritize filling that key from the message. "
    "Put avoid/include lift preferences in constraints. "
    "Set off_script true only if the message is unrelated to program setup "
    "(questions, chit-chat, asking for advice before intake is done)."
)


def parse_intake_message(intake, message, current_step_key):
    known_answers = json.dumps(intake.get("answers") or {})
    known_other_notes = json.dumps(intake.get("other_notes") or {})
    awaiting = (intake.get("awaiting_free_text_for") or "").strip()
    prompt = (
        f"Current intake question key: {current_step_key}. "
        f"Awaiting free-text answer for: {awaiting or 'none'}. "
        f"Known answers so far: {known_answers}. "
        f"Known other_notes: {known_other_notes}. "
        f"User message: {message}"
    )
    raw = generate_reply(
        [
            {"role": "system", "content": PARSE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        model=settings.AI_MODEL,
    )
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    parsed = json.loads(text)

    if not isinstance(parsed, dict):
        return {
            "off_script": True,
            "fields": {},
            "overwrite_fields": [],
            "other_notes": {},
            "constraints": "",
        }

    off_script = bool(parsed.get("off_script"))
    fields = parsed.get("fields") or {}
    if not isinstance(fields, dict):
        fields = {}

    cleaned_fields = {}
    for key, value in fields.items():
        if key not in VALID_INTAKE_VALUES:
            continue
        value = str(value).strip()
        if value in VALID_INTAKE_VALUES[key]:
            cleaned_fields[key] = value

    overwrite_fields = parsed.get("overwrite_fields") or []
    if not isinstance(overwrite_fields, list):
        overwrite_fields = []
    cleaned_overwrite = [
        key for key in overwrite_fields
        if key in INTAKE_STEP_KEYS and key in cleaned_fields
    ]

    other_notes = parsed.get("other_notes") or {}
    if not isinstance(other_notes, dict):
        other_notes = {}
    cleaned_other_notes = {}
    for key, note in other_notes.items():
        if key not in INTAKE_STEP_KEYS:
            continue
        note_text = str(note).strip()
        if note_text:
            cleaned_other_notes[key] = note_text

    constraints = parsed.get("constraints") or ""
    if constraints is None:
        constraints = ""
    constraints = str(constraints).strip()

    return {
        "off_script": off_script,
        "fields": cleaned_fields,
        "overwrite_fields": cleaned_overwrite,
        "other_notes": cleaned_other_notes,
        "constraints": constraints,
    }
