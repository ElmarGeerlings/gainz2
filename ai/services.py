import json

from django.conf import settings
from django_redis import get_redis_connection

from ai.providers.gemini import generate_reply as gemini_generate_reply
from ai.providers.gemini import generate_with_tools as gemini_generate_with_tools
from ai.tools import TOOL_DECLARATIONS, run_get_exercise_catalog, run_get_lift_history
from exercises.models import Exercise
from exercises.services import list_exercises_for_user

CHAT_HISTORY_TTL_SECONDS = 3600
VALID_EXERCISE_TYPES = {"primary", "secondary", "accessory"}

CHAT_SYSTEM_PROMPT = (
    "You are a personal fitness coach helping the user design a workout program. "
    "Write in plain text only: no markdown, no bold (**), no italics, no headings with #. "
    "Ask one short question at a time. "
    "Gather goals, experience, training days, and equipment. "
    "Early on (once you know they want a program), call get_lift_history before asking "
    "for lifting numbers or body details. Use logged work sets for exercise preference "
    "and starting loads when present. "
    "If history is missing or thin and they have training experience, ask for a few "
    "typical working weights. "
    "Ask age, sex, or bodyweight as fallback for total beginners with no "
    "history and no useful numbers — never block generation on those. "
    "Match the program to their stated goal; do not default to a powerlifting template. "
    "When ready, call get_exercise_catalog (and get_lift_history if not yet called), "
    "then submit_program_draft using only catalog exercise names (case may differ). "
    "Never invent exercise names; substitute from the catalog if needed. "
    "Prefer lift-history exercises when they fit. "
    "Every set needs a deliberate weight: use history or user numbers when you can; "
    "infer related lifts cautiously; use 0 only for true bodyweight moves; "
    "prefer slightly light when unsure. "
    "After a successful draft, tell them to review the preview and accept or ask for changes."
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


def clear_history(user_id, session_id):
    redis = get_redis_connection("default")
    redis.delete(f"ai_chat:{user_id}:{session_id}")


def get_draft(user_id, session_id):
    redis = get_redis_connection("default")
    raw = redis.get(f"ai_draft:{user_id}:{session_id}")
    if not raw:
        return None
    return json.loads(raw.decode("utf-8"))


def save_draft(user_id, session_id, draft):
    redis = get_redis_connection("default")
    redis.set(
        f"ai_draft:{user_id}:{session_id}",
        json.dumps(draft),
        ex=CHAT_HISTORY_TTL_SECONDS,
    )


def clear_draft(user_id, session_id):
    redis = get_redis_connection("default")
    redis.delete(f"ai_draft:{user_id}:{session_id}")


def build_exercise_name_lookup(user):
    exercises = list_exercises_for_user(
        user,
        search_query="",
        exercise_type="",
        primary_bodypart="",
        custom_filter="",
    )
    lookup = {}
    for exercise in exercises:
        key = exercise.name.strip().lower()
        if key not in lookup or not exercise.is_custom:
            lookup[key] = exercise
    return lookup


def resolve_allowed_exercise(user, exercise_id):
    exercise = Exercise.objects.filter(pk=exercise_id).first()
    if not exercise:
        return None
    if exercise.is_custom and exercise.user_id != user.id:
        return None
    return exercise


def validate_program_draft(user, draft):
    if not isinstance(draft, dict):
        return None, "Draft must be an object.", []

    name = (draft.get("name") or "").strip()
    if not name:
        return None, "Program name is required.", []

    routines = draft.get("routines")
    if not isinstance(routines, list) or not routines:
        return None, "At least one routine is required.", []

    lookup = build_exercise_name_lookup(user)
    unknown_names = []
    cleaned_routines = []

    for routine_index, routine in enumerate(routines, start=1):
        if not isinstance(routine, dict):
            return None, f"Routine {routine_index} is invalid.", []

        routine_name = (routine.get("name") or "").strip()
        if not routine_name:
            return None, f"Routine {routine_index} needs a name.", []

        exercises = routine.get("exercises")
        if not isinstance(exercises, list) or not exercises:
            return None, f"Routine {routine_name} needs at least one exercise.", []

        cleaned_exercises = []
        for exercise_index, item in enumerate(exercises, start=1):
            if not isinstance(item, dict):
                return None, f"Routine {routine_name}: exercise {exercise_index} is invalid.", []

            exercise_name = (item.get("exercise_name") or "").strip()
            if not exercise_name:
                return None, f"Routine {routine_name}: exercise {exercise_index} needs a name.", []

            exercise = lookup.get(exercise_name.lower())
            if not exercise:
                unknown_names.append(exercise_name)
                continue

            exercise_type = item.get("exercise_type") or "accessory"
            if exercise_type not in VALID_EXERCISE_TYPES:
                return None, f"Invalid exercise_type for {exercise.name}.", []

            sets = item.get("sets")
            if not isinstance(sets, list) or not sets:
                return None, f"{exercise.name} needs at least one set.", []

            cleaned_sets = []
            for set_index, set_data in enumerate(sets, start=1):
                if not isinstance(set_data, dict):
                    return None, f"{exercise.name}: set {set_index} is invalid.", []
                reps = int(set_data["reps"])
                if reps < 0:
                    return None, f"{exercise.name}: reps must be >= 0.", []
                weight = set_data.get("weight", 0)
                if weight is None or weight == "":
                    weight = 0
                weight = float(weight)
                is_warmup = bool(set_data.get("is_warmup", False))
                cleaned_sets.append({
                    "reps": reps,
                    "weight": weight,
                    "is_warmup": is_warmup,
                })

            cleaned_exercises.append({
                "exercise_id": exercise.pk,
                "exercise_name": exercise.name,
                "exercise_type": exercise_type,
                "sets": cleaned_sets,
            })

        cleaned_routines.append({
            "name": routine_name,
            "exercises": cleaned_exercises,
        })

    if unknown_names:
        unique_unknown = sorted(set(unknown_names), key=str.lower)
        return None, f"Unknown exercise names: {', '.join(unique_unknown)}", unique_unknown

    cleaned = {
        "name": name,
        "description": (draft.get("description") or "").strip(),
        "routines": cleaned_routines,
    }
    return cleaned, None, []


def enrich_draft_for_preview(draft):
    if not draft:
        return None
    routines = []
    for routine in draft["routines"]:
        exercises = []
        for item in routine["exercises"]:
            exercises.append({
                "exercise_name": item["exercise_name"],
                "exercise_type": item["exercise_type"],
                "sets": item["sets"],
            })
        routines.append({
            "name": routine["name"],
            "exercises": exercises,
        })
    return {
        "name": draft["name"],
        "description": draft.get("description") or "",
        "routines": routines,
    }


def submit_program_draft_tool(user, session_id, args):
    cleaned, error, unknown_names = validate_program_draft(user, args)
    if error:
        result = {"ok": False, "error": error}
        if unknown_names:
            result["unknown_names"] = unknown_names
        return result
    save_draft(user.id, session_id, cleaned)
    exercise_count = sum(
        len(routine["exercises"]) for routine in cleaned["routines"]
    )
    return {
        "ok": True,
        "summary": (
            f"{cleaned['name']}: {len(cleaned['routines'])} routine(s), "
            f"{exercise_count} exercise(s)."
        ),
    }


def execute_tool(name, args, user, session_id):
    if name == "get_exercise_catalog":
        return run_get_exercise_catalog(user, args)
    if name == "get_lift_history":
        return run_get_lift_history(user, args)
    if name == "submit_program_draft":
        return submit_program_draft_tool(user, session_id, args)
    return {"ok": False, "error": f"Unknown tool: {name}"}


def send_chat_message(user, session_id, message):
    message = (message or "").strip()
    if not message:
        return get_history(user.id, session_id)

    history = get_history(user.id, session_id)
    history.append({"role": "user", "content": message})

    reply = gemini_generate_with_tools(
        [{"role": "system", "content": CHAT_SYSTEM_PROMPT}] + history,
        TOOL_DECLARATIONS,
        user,
        session_id,
    )
    history.append({"role": "assistant", "content": reply})
    save_history(user.id, session_id, history)
    return history


def accept_draft(user, session_id):
    from programs.services import create_program_from_ai_draft

    draft = get_draft(user.id, session_id)
    if not draft:
        return None
    cleaned, error, unknown_names = validate_program_draft(user, draft)
    if error:
        return None
    program = create_program_from_ai_draft(user, cleaned)
    clear_draft(user.id, session_id)
    clear_history(user.id, session_id)
    return program
