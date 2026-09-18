import json

from django.conf import settings
from django_redis import get_redis_connection

from ai.intake import (
    CONSTRAINTS_PROMPT,
    DEMOGRAPHICS_PROMPT,
    EDIT_PROMPT,
    FEEDBACK_COMMENT_PROMPT,
    FEEDBACK_RATING_PROMPT,
    FEEDBACK_RATING_RETRY_PROMPT,
    INTAKE_STEPS,
    OTHER_TYPE_PROMPT,
    PROGRAM_READY_MESSAGE,
    SIGNUP_MESSAGE_KIND,
    SIGNUP_PROMPT,
    START_OVER_ASK_PROMPT,
    THANK_YOU_MESSAGE,
    WEIGHTS_PROMPT,
    apply_parsed_intake,
    build_profile_context,
    first_missing_step_index,
    format_history_summary,
    get_current_step,
    new_intake,
    resolve_weight_path,
)
from ai.intake_parse import parse_intake_message
from ai.prompts import (
    CHAT_SYSTEM_PROMPT,
    EDIT_DRAFT_PROMPT,
    GOAL_PROMPT_ADDONS,
    REPAIR_PROMPT,
    STAGE1_SYSTEM_PROMPT,
    STAGE2_SYSTEM_PROMPT,
)
from ai.providers.gemini import API_ERROR_REPLY, RATE_LIMIT_REPLY
from ai.providers.gemini import generate_with_tools as gemini_generate_with_tools
from ai.rubrics import validate_exercise_plan_structure, validate_program_loads
from ai.models import AiChat
from ai.session import ensure_aichat, find_aichat
from ai.tools import (
    CHAT_TOOL_DECLARATIONS,
    STAGE1_TOOL_DECLARATIONS,
    STAGE2_TOOL_DECLARATIONS,
    format_catalog_for_prompt,
    run_get_exercise_catalog,
    run_get_lift_history,
)
from exercises.bodypart_metadata import build_coverage_prompt_section
from exercises.catalog_metadata import (
    allowed_equipment_for_intake,
    exercise_passes_equipment_filter,
)
from exercises.models import Exercise
from exercises.services import list_exercises_for_user

CHAT_HISTORY_TTL_SECONDS = 3600
VALID_EXERCISE_TYPES = {"primary", "secondary", "accessory"}
MIN_EXERCISES_PER_ROUTINE = 4
GUEST_GEN_QUOTA_MAX = 3
GUEST_GEN_QUOTA_TTL = 86400
GUEST_GEN_QUOTA_MESSAGE = (
    "You have reached the limit of 3 program generations per day. Try again tomorrow."
)
GENERATING_PROGRAM_MESSAGE = (
    "Generating your program. This can take up to a few minutes..."
)
SESSION_EXPIRED_MESSAGE = "Your session has expired. Reload to start a new chat."
INTERRUPT_REPLIES = frozenset({RATE_LIMIT_REPLY, API_ERROR_REPLY})


def guest_generation_count(ctx):
    if ctx.user.is_authenticated and ctx.user.is_dev:
        return 0
    redis = get_redis_connection("default")
    raw = redis.get(f"ai_gen_quota:{ctx.owner_key}")
    if raw is None:
        return 0
    return int(raw.decode("utf-8"))


def guest_at_generation_limit(ctx):
    return guest_generation_count(ctx) >= GUEST_GEN_QUOTA_MAX


def check_guest_generation_quota(ctx):
    if ctx.user.is_authenticated and ctx.user.is_dev:
        return None
    redis = get_redis_connection("default")
    key = f"ai_gen_quota:{ctx.owner_key}"
    raw = redis.get(key)
    if raw is None:
        redis.set(key, 1, ex=GUEST_GEN_QUOTA_TTL)
        return None
    count = int(raw.decode("utf-8"))
    if count >= GUEST_GEN_QUOTA_MAX:
        return GUEST_GEN_QUOTA_MESSAGE
    redis.incr(key)
    return None


def set_last_assistant_message(history, content, replace_if=None):
    if (
        replace_if
        and history
        and history[-1].get("role") == "assistant"
        and history[-1].get("content") == replace_if
    ):
        history[-1] = {"role": "assistant", "content": content}
    else:
        history.append({"role": "assistant", "content": content})
    return history


def begin_program_generation(ctx, session_id, history):
    quota_message = check_guest_generation_quota(ctx)
    if quota_message:
        history.append({"role": "assistant", "content": quota_message})
        save_history(ctx.owner_key, session_id, history)
        return history
    history.append({"role": "assistant", "content": GENERATING_PROGRAM_MESSAGE})
    save_history(ctx.owner_key, session_id, history)
    return history


def get_history(owner_key, session_id):
    redis = get_redis_connection("default")
    raw = redis.get(f"ai_chat:{owner_key}:{session_id}")
    if not raw:
        return []
    return json.loads(raw.decode("utf-8"))


def save_history(owner_key, session_id, history, ctx=None):
    redis = get_redis_connection("default")
    redis.set(
        f"ai_chat:{owner_key}:{session_id}",
        json.dumps(history),
        ex=CHAT_HISTORY_TTL_SECONDS,
    )
    if ctx:
        snapshot_aichat(ctx, session_id)


def clear_history(owner_key, session_id):
    redis = get_redis_connection("default")
    redis.delete(f"ai_chat:{owner_key}:{session_id}")


def get_intake(owner_key, session_id):
    redis = get_redis_connection("default")
    raw = redis.get(f"ai_intake:{owner_key}:{session_id}")
    if not raw:
        return None
    return json.loads(raw.decode("utf-8"))


def save_intake(owner_key, session_id, intake, ctx=None):
    redis = get_redis_connection("default")
    redis.set(
        f"ai_intake:{owner_key}:{session_id}",
        json.dumps(intake),
        ex=CHAT_HISTORY_TTL_SECONDS,
    )
    if ctx:
        snapshot_aichat(ctx, session_id)


def clear_intake(owner_key, session_id):
    redis = get_redis_connection("default")
    redis.delete(f"ai_intake:{owner_key}:{session_id}")


def get_draft(owner_key, session_id):
    redis = get_redis_connection("default")
    raw = redis.get(f"ai_draft:{owner_key}:{session_id}")
    if not raw:
        return None
    return json.loads(raw.decode("utf-8"))


def save_draft(owner_key, session_id, draft, ctx=None):
    redis = get_redis_connection("default")
    redis.set(
        f"ai_draft:{owner_key}:{session_id}",
        json.dumps(draft),
        ex=CHAT_HISTORY_TTL_SECONDS,
    )
    if ctx:
        snapshot_aichat(ctx, session_id, draft)


def clear_draft(owner_key, session_id):
    redis = get_redis_connection("default")
    redis.delete(f"ai_draft:{owner_key}:{session_id}")


def get_previous_draft(owner_key, session_id):
    redis = get_redis_connection("default")
    raw = redis.get(f"ai_draft_previous:{owner_key}:{session_id}")
    if not raw:
        return None
    return json.loads(raw.decode("utf-8"))


def save_previous_draft(owner_key, session_id, draft):
    redis = get_redis_connection("default")
    redis.set(
        f"ai_draft_previous:{owner_key}:{session_id}",
        json.dumps(draft),
        ex=CHAT_HISTORY_TTL_SECONDS,
    )


def clear_previous_draft(owner_key, session_id):
    redis = get_redis_connection("default")
    redis.delete(f"ai_draft_previous:{owner_key}:{session_id}")


def get_exercise_plan(owner_key, session_id):
    redis = get_redis_connection("default")
    raw = redis.get(f"ai_exercise_plan:{owner_key}:{session_id}")
    if not raw:
        return None
    return json.loads(raw.decode("utf-8"))


def save_exercise_plan(owner_key, session_id, plan):
    redis = get_redis_connection("default")
    redis.set(
        f"ai_exercise_plan:{owner_key}:{session_id}",
        json.dumps(plan),
        ex=CHAT_HISTORY_TTL_SECONDS,
    )


def clear_exercise_plan(owner_key, session_id):
    redis = get_redis_connection("default")
    redis.delete(f"ai_exercise_plan:{owner_key}:{session_id}")


def get_enforce_plan(owner_key, session_id):
    redis = get_redis_connection("default")
    raw = redis.get(f"ai_enforce_plan:{owner_key}:{session_id}")
    if not raw:
        return False
    return raw.decode("utf-8") == "1"


def set_enforce_plan(owner_key, session_id, enforce):
    redis = get_redis_connection("default")
    if enforce:
        redis.set(
            f"ai_enforce_plan:{owner_key}:{session_id}",
            "1",
            ex=CHAT_HISTORY_TTL_SECONDS,
        )
    else:
        redis.delete(f"ai_enforce_plan:{owner_key}:{session_id}")


def snapshot_aichat(ctx, session_id, draft=None):
    chat = find_aichat(ctx, session_id)
    if not chat:
        return
    chat.intake = get_intake(ctx.owner_key, session_id) or {}
    chat.messages = get_history(ctx.owner_key, session_id)
    update_fields = ["intake", "messages", "updated_at"]
    if draft is not None:
        drafts = list(chat.drafts or [])
        drafts.append(draft)
        chat.drafts = drafts
        update_fields.append("drafts")
    chat.save(update_fields=update_fields)


def init_chat_session(owner_key, session_id):
    intake = new_intake()
    save_intake(owner_key, session_id, intake)
    history = [{"role": "assistant", "content": INTAKE_STEPS[0]["question"]}]
    save_history(owner_key, session_id, history)
    return intake, history


def draft_to_preview(draft):
    if not draft or not isinstance(draft, dict):
        return None
    routines = draft.get("routines")
    if not isinstance(routines, list) or not routines:
        return None
    preview_routines = []
    for routine in routines:
        exercises = []
        for item in routine.get("exercises", []):
            work_sets = [
                set_data for set_data in item.get("sets", [])
                if not set_data.get("is_warmup")
            ]
            exercises.append({
                "exercise_name": item["exercise_name"],
                "exercise_type": item["exercise_type"],
                "sets": work_sets,
            })
        preview_routines.append({
            "name": routine["name"],
            "exercises": exercises,
        })
    return {
        "name": draft["name"],
        "description": draft.get("description") or "",
        "routines": preview_routines,
    }


def build_edit_draft_context(owner_key, session_id, intake):
    if not intake or intake.get("phase") != "chat":
        return None
    draft = get_draft(owner_key, session_id)
    if not draft:
        return None
    lines = [
        EDIT_DRAFT_PROMPT,
        "",
        "Current program draft (JSON):",
        json.dumps(draft, separators=(",", ":")),
    ]
    previous = get_previous_draft(owner_key, session_id)
    if previous:
        lines.extend([
            "",
            "Previous program draft (resubmit unchanged if user asks to revert):",
            json.dumps(previous, separators=(",", ":")),
        ])
    return "\n".join(lines)


def build_exercise_name_lookup(user):
    exercises = list_exercises_for_user(
        user if user.is_authenticated else None,
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


def build_filtered_exercise_lookup(user, intake):
    exercises = list_exercises_for_user(
        user if user.is_authenticated else None,
        search_query="",
        exercise_type="",
        primary_bodypart="",
        custom_filter="",
    )
    allowed_tags = allowed_equipment_for_intake(intake)
    lookup = {}
    for exercise in exercises:
        if not exercise_passes_equipment_filter(exercise, allowed_tags):
            continue
        key = exercise.name.strip().lower()
        if key not in lookup or not exercise.is_custom:
            lookup[key] = exercise
    return lookup


def resolve_allowed_exercise(user, exercise_id):
    exercise = Exercise.objects.filter(pk=exercise_id).first()
    if not exercise:
        return None
    if exercise.is_custom:
        if not user.is_authenticated or exercise.user_id != user.id:
            return None
    return exercise


def text_field(value):
    if not isinstance(value, str):
        return ""
    return value.strip()


def clean_exercise_plan(user, plan, intake):
    if not isinstance(plan, dict):
        return None, ["Exercise plan must be an object."]

    name = text_field(plan.get("name"))
    if not name:
        return None, ["Program name is required."]

    routines = plan.get("routines")
    if not isinstance(routines, list) or not routines:
        return None, ["At least one routine is required."]

    lookup = build_filtered_exercise_lookup(user, intake)
    unknown_names = []
    cleaned_routines = []

    for routine in routines:
        if not isinstance(routine, dict):
            return None, ["A routine entry is invalid."]

        routine_name = (routine.get("name") or "").strip()
        if not routine_name:
            return None, ["Each routine needs a name."]

        exercises = routine.get("exercises")
        if not isinstance(exercises, list) or not exercises:
            return None, [f"Routine {routine_name} needs exercises."]

        cleaned_exercises = []
        for item in exercises:
            if not isinstance(item, dict):
                return None, [f"Routine {routine_name} has an invalid exercise."]

            exercise_name = (item.get("exercise_name") or "").strip()
            if not exercise_name:
                return None, [f"Routine {routine_name} has an exercise without a name."]

            exercise = lookup.get(exercise_name.lower())
            if not exercise:
                unknown_names.append(exercise_name)
                continue

            exercise_type = item.get("exercise_type") or "accessory"
            if exercise_type not in VALID_EXERCISE_TYPES:
                return None, [f"Invalid exercise_type for {exercise.name}."]

            cleaned_exercises.append({
                "exercise_id": exercise.pk,
                "exercise_name": exercise.name,
                "exercise_type": exercise_type,
            })

        cleaned_routines.append({
            "name": routine_name,
            "exercises": cleaned_exercises,
        })

    if unknown_names:
        unique_unknown = sorted(set(unknown_names), key=str.lower)
        return None, [f"Unknown exercise names: {', '.join(unique_unknown)}"]

    cleaned = {
        "name": name,
        "description": text_field(plan.get("description")),
        "routines": cleaned_routines,
    }
    structure_errors = validate_exercise_plan_structure(cleaned, lookup, intake)
    if structure_errors:
        return None, structure_errors
    return cleaned, []


def draft_matches_exercise_plan(draft, plan):
    if len(draft.get("routines", [])) != len(plan.get("routines", [])):
        return False
    for draft_routine, plan_routine in zip(draft["routines"], plan["routines"]):
        if draft_routine.get("name") != plan_routine.get("name"):
            return False
        draft_items = draft_routine.get("exercises", [])
        plan_items = plan_routine.get("exercises", [])
        if len(draft_items) != len(plan_items):
            return False
        for draft_item, plan_item in zip(draft_items, plan_items):
            if draft_item.get("exercise_name", "").lower() != plan_item.get("exercise_name", "").lower():
                return False
            if draft_item.get("exercise_type") != plan_item.get("exercise_type"):
                return False
    return True


def validate_program_draft(user, draft):
    if not isinstance(draft, dict):
        return None, "Draft must be an object.", []

    name = text_field(draft.get("name"))
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

        if len(exercises) < MIN_EXERCISES_PER_ROUTINE:
            return (
                None,
                f"Routine {routine_name} needs at least {MIN_EXERCISES_PER_ROUTINE} exercises.",
                [],
            )

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
                reps_raw = set_data.get("reps")
                if reps_raw is None:
                    return None, f"{exercise.name}: set {set_index} needs reps.", []
                reps = int(reps_raw)
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
        "description": text_field(draft.get("description")),
        "routines": cleaned_routines,
    }
    return cleaned, None, []


def save_interrupt_reply(ctx, session_id, intake, history, reply):
    history.append({"role": "assistant", "content": reply})
    save_history(ctx.owner_key, session_id, history, ctx)
    intake["phase"] = "chat"
    save_intake(ctx.owner_key, session_id, intake, ctx)
    return history


def submit_exercise_plan_tool(ctx, session_id, args, intake):
    cleaned, errors = clean_exercise_plan(ctx.user, args, intake)
    if errors:
        return {"ok": False, "error": "; ".join(errors), "errors": errors}
    save_exercise_plan(ctx.owner_key, session_id, cleaned)
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


def submit_program_draft_tool(ctx, session_id, args, intake, enforce_plan=False):
    if enforce_plan:
        plan = get_exercise_plan(ctx.owner_key, session_id)
        if plan:
            cleaned_preview, error, unknown_names = validate_program_draft(ctx.user, args)
            if error:
                return {"ok": False, "error": error, "unknown_names": unknown_names or []}
            if not draft_matches_exercise_plan(cleaned_preview, plan):
                return {
                    "ok": False,
                    "error": (
                        "Program draft must use the same routines, exercises, "
                        "and order as the locked exercise plan."
                    ),
                }

    cleaned, error, unknown_names = validate_program_draft(ctx.user, args)
    if error:
        result = {"ok": False, "error": error}
        if unknown_names:
            result["unknown_names"] = unknown_names
        return result
    current = get_draft(ctx.owner_key, session_id)
    if current:
        save_previous_draft(ctx.owner_key, session_id, current)
    save_draft(ctx.owner_key, session_id, cleaned, ctx)
    if intake and intake.get("phase") == "chat":
        intake["phase"] = "review"
        save_intake(ctx.owner_key, session_id, intake, ctx)
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


def execute_tool(name, args, ctx, session_id):
    intake = get_intake(ctx.owner_key, session_id)
    if name == "get_exercise_catalog":
        return run_get_exercise_catalog(ctx.user, args, intake)
    if name == "get_lift_history":
        return run_get_lift_history(ctx.user, args)
    if name == "submit_exercise_plan":
        return submit_exercise_plan_tool(ctx, session_id, args, intake)
    if name == "submit_program_draft":
        enforce_plan = get_enforce_plan(ctx.owner_key, session_id)
        return submit_program_draft_tool(
            ctx, session_id, args, intake, enforce_plan=enforce_plan
        )
    return {"ok": False, "error": f"Unknown tool: {name}"}


def build_gemini_messages(ctx, session_id, history):
    intake = get_intake(ctx.owner_key, session_id)
    messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]

    include_profile = False
    if intake:
        if intake.get("answers"):
            include_profile = True
        elif (intake.get("constraints") or "").strip():
            include_profile = True
        elif (intake.get("weight_notes") or "").strip():
            include_profile = True
        elif (intake.get("demographics_notes") or "").strip():
            include_profile = True
        elif intake.get("off_script"):
            include_profile = True

    if include_profile:
        lifts = []
        if ctx.user.is_authenticated:
            lifts = run_get_lift_history(ctx.user, {})["lifts"]
        history_summary = format_history_summary(lifts) if lifts else ""
        profile = build_profile_context(intake, history_summary)
        messages.append({"role": "system", "content": profile})

    edit_context = build_edit_draft_context(ctx.owner_key, session_id, intake)
    if edit_context:
        messages.append({"role": "system", "content": edit_context})

    messages.extend(history)
    return messages


def run_stage_with_repair(ctx, session_id, base_history, system_prompt, tools):
    messages = [{"role": "system", "content": system_prompt}] + base_history
    return gemini_generate_with_tools(
        messages,
        tools,
        ctx,
        session_id,
        model=settings.AI_MODEL_GENERATE,
    )


def run_generation_stages(ctx, session_id, history):
    intake = get_intake(ctx.owner_key, session_id)
    clear_draft(ctx.owner_key, session_id)
    clear_previous_draft(ctx.owner_key, session_id)
    clear_exercise_plan(ctx.owner_key, session_id)
    set_enforce_plan(ctx.owner_key, session_id, False)

    path, lifts = resolve_weight_path(ctx.user, intake)
    history_summary = format_history_summary(lifts) if path == "use_history" else ""
    profile = build_profile_context(intake, history_summary)
    goal = intake.get("answers", {}).get("goal")
    addon = GOAL_PROMPT_ADDONS.get(goal)
    if addon:
        profile = profile + "\n\n" + addon
    base_history = [
        message for message in history
        if message.get("content") != GENERATING_PROGRAM_MESSAGE
    ]

    stage1_prompt = (
        STAGE1_SYSTEM_PROMPT
        + "\n\n"
        + profile
        + "\n\nExercise catalog (JSON):\n"
        + format_catalog_for_prompt(ctx.user, intake)
    )
    stage1_prompt = stage1_prompt + "\n\n" + build_coverage_prompt_section(intake)
    reply = run_stage_with_repair(
        ctx, session_id, base_history, stage1_prompt, STAGE1_TOOL_DECLARATIONS
    )
    if reply in INTERRUPT_REPLIES:
        return save_interrupt_reply(ctx, session_id, intake, history, reply)
    plan = get_exercise_plan(ctx.owner_key, session_id)
    if not plan:
        errors = ["Submit an exercise plan with submit_exercise_plan."]
    else:
        lookup = build_filtered_exercise_lookup(ctx.user, intake)
        errors = validate_exercise_plan_structure(plan, lookup, intake)
    if errors:
        repair_text = REPAIR_PROMPT + "\n" + "\n".join(f"- {item}" for item in errors)
        repair_history = base_history + [{"role": "user", "content": repair_text}]
        reply = run_stage_with_repair(
            ctx,
            session_id,
            repair_history,
            stage1_prompt,
            STAGE1_TOOL_DECLARATIONS,
        )
        if reply in INTERRUPT_REPLIES:
            return save_interrupt_reply(ctx, session_id, intake, history, reply)
        plan = get_exercise_plan(ctx.owner_key, session_id)
        if not plan:
            errors = ["Submit an exercise plan with submit_exercise_plan."]
        else:
            lookup = build_filtered_exercise_lookup(ctx.user, intake)
            errors = validate_exercise_plan_structure(plan, lookup, intake)

    plan = get_exercise_plan(ctx.owner_key, session_id)
    if not plan or errors:
        reply = (
            "I couldn't put together a program just now. "
            "Try again or tell me what you want changed."
        )
        history.append({"role": "assistant", "content": reply})
        save_history(ctx.owner_key, session_id, history, ctx)
        intake["phase"] = "chat"
        save_intake(ctx.owner_key, session_id, intake, ctx)
        return history

    set_enforce_plan(ctx.owner_key, session_id, True)
    locked_plan = json.dumps(plan, indent=2)
    stage2_prompt = (
        STAGE2_SYSTEM_PROMPT
        + "\n\n"
        + profile
        + "\n\nLocked exercise plan (do not change exercises):\n"
        + locked_plan
    )
    reply = run_stage_with_repair(
        ctx, session_id, base_history, stage2_prompt, STAGE2_TOOL_DECLARATIONS
    )
    if reply in INTERRUPT_REPLIES:
        set_enforce_plan(ctx.owner_key, session_id, False)
        return save_interrupt_reply(ctx, session_id, intake, history, reply)
    draft = get_draft(ctx.owner_key, session_id)
    if not draft:
        errors = ["Submit the full program with submit_program_draft."]
    else:
        errors = validate_program_loads(draft, intake)
    if errors:
        repair_text = REPAIR_PROMPT + "\n" + "\n".join(f"- {item}" for item in errors)
        repair_history = base_history + [{"role": "user", "content": repair_text}]
        reply = run_stage_with_repair(
            ctx,
            session_id,
            repair_history,
            stage2_prompt,
            STAGE2_TOOL_DECLARATIONS,
        )
        if reply in INTERRUPT_REPLIES:
            set_enforce_plan(ctx.owner_key, session_id, False)
            return save_interrupt_reply(ctx, session_id, intake, history, reply)

    set_enforce_plan(ctx.owner_key, session_id, False)

    draft = get_draft(ctx.owner_key, session_id)
    if draft:
        reply = PROGRAM_READY_MESSAGE
        intake["phase"] = "review"
    else:
        reply = (
            "I couldn't finish the program details just now. "
            "Tell me what to adjust and we can try again."
        )
        intake["phase"] = "chat"
    set_last_assistant_message(history, reply, replace_if=GENERATING_PROGRAM_MESSAGE)
    save_history(ctx.owner_key, session_id, history, ctx)
    save_intake(ctx.owner_key, session_id, intake, ctx)
    return history


def begin_constraints(ctx, session_id, intake, history):
    intake["phase"] = "awaiting_constraints"
    history.append({"role": "assistant", "content": CONSTRAINTS_PROMPT})
    save_intake(ctx.owner_key, session_id, intake, ctx)
    save_history(ctx.owner_key, session_id, history, ctx)
    return history, intake


def restart_chat_session(ctx, session_id):
    clear_draft(ctx.owner_key, session_id)
    clear_previous_draft(ctx.owner_key, session_id)
    clear_exercise_plan(ctx.owner_key, session_id)
    clear_history(ctx.owner_key, session_id)
    clear_intake(ctx.owner_key, session_id)
    set_enforce_plan(ctx.owner_key, session_id, False)
    intake, history = init_chat_session(ctx.owner_key, session_id)
    snapshot_aichat(ctx, session_id)
    return {"expired": False, "history": history, "intake": intake}


def finish_feedback_flow(ctx, session_id, history, intake):
    after_feedback = intake.get("after_feedback")
    if after_feedback == "start_over_ask":
        intake["phase"] = "start_over_ask"
        history.append({"role": "assistant", "content": START_OVER_ASK_PROMPT})
    elif after_feedback == "done" and ctx.is_guest:
        intake["phase"] = "signup"
        history.append({
            "role": "assistant",
            "content": SIGNUP_PROMPT,
            "kind": SIGNUP_MESSAGE_KIND,
        })
    else:
        intake["phase"] = "done"
        history.append({"role": "assistant", "content": THANK_YOU_MESSAGE})
    save_intake(ctx.owner_key, session_id, intake, ctx)
    save_history(ctx.owner_key, session_id, history, ctx)
    program_id = None
    if after_feedback == "done" and not ctx.is_guest:
        program_id = intake.get("accepted_program_id")
    return {
        "expired": False,
        "history": history,
        "intake": intake,
        "program_id": program_id,
    }


def enter_feedback_comment(ctx, session_id, history, after_feedback, accepted_program_id=None):
    draft = get_draft(ctx.owner_key, session_id)
    if not draft:
        return {"error": "no_draft", "history": history}

    intake = get_intake(ctx.owner_key, session_id)
    intake["after_feedback"] = after_feedback
    intake["phase"] = "feedback_comment"
    intake["feedback"] = {}
    if accepted_program_id:
        intake["accepted_program_id"] = accepted_program_id
    history.append({"role": "assistant", "content": FEEDBACK_COMMENT_PROMPT})
    save_intake(ctx.owner_key, session_id, intake, ctx)
    save_history(ctx.owner_key, session_id, history, ctx)
    return {"expired": False, "history": history, "intake": intake}


def enter_accept_and_feedback(ctx, session_id, history):
    accepted_program_id = None
    if ctx.user.is_authenticated:
        program = accept_draft(ctx, session_id)
        if not program:
            return {"error": "accept_failed", "history": history}
        accepted_program_id = program.pk
    result = enter_feedback_comment(ctx, session_id, history, "done", accepted_program_id)
    if ctx.is_guest:
        intake = get_intake(ctx.owner_key, session_id)
        intake["draft_accepted"] = True
        save_intake(ctx.owner_key, session_id, intake, ctx)
        result["intake"] = intake
    return result


def go_to_feedback_rating(ctx, session_id, history, intake, comment):
    feedback = intake.setdefault("feedback", {})
    feedback["comment"] = comment.strip()
    intake["phase"] = "feedback_rating"
    history.append({"role": "assistant", "content": FEEDBACK_RATING_PROMPT})
    save_intake(ctx.owner_key, session_id, intake, ctx)
    save_history(ctx.owner_key, session_id, history, ctx)
    return {"expired": False, "history": history, "intake": intake}


def complete_feedback_with_score(ctx, session_id, history, intake, score, skipped=False):
    feedback = intake.setdefault("feedback", {})
    feedback["score"] = score
    feedback["skipped"] = skipped
    return finish_feedback_flow(ctx, session_id, history, intake)


def skip_feedback_from_comment(ctx, session_id, history, intake, comment):
    feedback = intake.setdefault("feedback", {})
    feedback["comment"] = (comment or "").strip()
    feedback["score"] = None
    feedback["skipped"] = True
    return finish_feedback_flow(ctx, session_id, history, intake)


def apply_review_choice(ctx, session_id, choice_id, choice_label):
    intake = get_intake(ctx.owner_key, session_id)
    history = get_history(ctx.owner_key, session_id)
    history.append({"role": "user", "content": choice_label})

    if choice_id == "edit":
        intake["phase"] = "chat"
        history.append({"role": "assistant", "content": EDIT_PROMPT})
        save_intake(ctx.owner_key, session_id, intake, ctx)
        save_history(ctx.owner_key, session_id, history, ctx)
        return {"expired": False, "history": history, "intake": intake}

    if choice_id == "discard":
        save_history(ctx.owner_key, session_id, history, ctx)
        result = enter_feedback_comment(ctx, session_id, history, "start_over_ask")
        if result.get("error") == "no_draft":
            return {
                "expired": False,
                "error": "no_draft",
                "history": history,
                "intake": intake,
            }
        return result

    if choice_id == "accept":
        save_history(ctx.owner_key, session_id, history, ctx)
        result = enter_accept_and_feedback(ctx, session_id, history)
        if result.get("error") == "no_draft":
            return {
                "expired": False,
                "error": "no_draft",
                "history": history,
                "intake": intake,
            }
        if result.get("error") == "accept_failed":
            return {
                "expired": False,
                "error": "accept_failed",
                "history": history,
                "intake": intake,
            }
        return result

    save_history(ctx.owner_key, session_id, history, ctx)
    return {"expired": False, "history": history, "intake": intake}


def apply_intake_choice(ctx, session_id, choice_id, attributes=None):
    attributes = attributes or {}
    intake = get_intake(ctx.owner_key, session_id)
    if not intake:
        return {"expired": True}

    phase = intake.get("phase")
    history = get_history(ctx.owner_key, session_id)

    if phase == "feedback_comment" and choice_id == "skip":
        comment = attributes.get("message") or attributes.get("data-message") or ""
        history.append({"role": "user", "content": "Skip"})
        return skip_feedback_from_comment(ctx, session_id, history, intake, comment)

    if phase == "feedback_rating":
        history.append({"role": "user", "content": choice_id if choice_id != "skip" else "Skip"})
        if choice_id == "skip":
            return complete_feedback_with_score(ctx, session_id, history, intake, None, skipped=True)
        if choice_id in ("1", "2", "3", "4", "5"):
            return complete_feedback_with_score(
                ctx, session_id, history, intake, int(choice_id), skipped=False
            )
        save_history(ctx.owner_key, session_id, history, ctx)
        return {"expired": False, "history": history, "intake": intake}

    if phase == "start_over_ask":
        choice_label = choice_id
        if choice_id == "yes":
            choice_label = "Yes"
        if choice_id == "no":
            choice_label = "No"
        history.append({"role": "user", "content": choice_label})
        if choice_id == "yes":
            save_history(ctx.owner_key, session_id, history, ctx)
            return restart_chat_session(ctx, session_id)
        if choice_id == "no":
            intake["phase"] = "done"
            history.append({"role": "assistant", "content": THANK_YOU_MESSAGE})
            save_intake(ctx.owner_key, session_id, intake, ctx)
            save_history(ctx.owner_key, session_id, history, ctx)
            return {"expired": False, "history": history, "intake": intake}
        save_history(ctx.owner_key, session_id, history, ctx)
        return {"expired": False, "history": history, "intake": intake}

    if phase == "review":
        choice_label = choice_id
        for item in [
            {"id": "accept", "label": "Accept"},
            {"id": "edit", "label": "Edit"},
            {"id": "discard", "label": "Discard"},
        ]:
            if item["id"] == choice_id:
                choice_label = item["label"]
                break
        return apply_review_choice(ctx, session_id, choice_id, choice_label)

    if intake.get("phase") != "intake":
        return {
            "expired": False,
            "history": get_history(ctx.owner_key, session_id),
            "intake": intake,
        }

    step_index = intake["step"]
    step = get_current_step(intake)
    if not step:
        return {
            "expired": False,
            "history": get_history(ctx.owner_key, session_id),
            "intake": intake,
        }

    choice = None
    for item in step["choices"]:
        if item["id"] == choice_id:
            choice = item
            break
    if not choice:
        return {
            "expired": False,
            "history": get_history(ctx.owner_key, session_id),
            "intake": intake,
        }

    ensure_aichat(
        ctx,
        session_id,
        {
            "intake": get_intake(ctx.owner_key, session_id) or {},
            "messages": get_history(ctx.owner_key, session_id),
            "drafts": [],
        },
    )
    history = get_history(ctx.owner_key, session_id)
    history.append({"role": "user", "content": choice["label"]})

    if choice["id"] == "other":
        intake["awaiting_free_text_for"] = step["key"]
        history.append({"role": "assistant", "content": OTHER_TYPE_PROMPT})
        save_intake(ctx.owner_key, session_id, intake, ctx)
        save_history(ctx.owner_key, session_id, history, ctx)
        return {"expired": False, "history": history, "intake": intake}

    intake["answers"][step["key"]] = choice["id"]
    intake["step"] = step_index + 1
    if intake["step"] >= len(INTAKE_STEPS):
        save_intake(ctx.owner_key, session_id, intake, ctx)
        history, intake = begin_constraints(ctx, session_id, intake, history)
        return {"expired": False, "history": history, "intake": intake}

    next_step = INTAKE_STEPS[intake["step"]]
    history.append({"role": "assistant", "content": next_step["question"]})
    save_intake(ctx.owner_key, session_id, intake, ctx)
    save_history(ctx.owner_key, session_id, history, ctx)
    return {"expired": False, "history": history, "intake": intake}


def handle_intake_typed_message(ctx, session_id, intake, history, message):
    awaiting = (intake.get("awaiting_free_text_for") or "").strip()
    if awaiting:
        current_key = awaiting
    else:
        current_step = get_current_step(intake)
        current_key = current_step["key"] if current_step else INTAKE_STEPS[0]["key"]
    parsed = parse_intake_message(intake, message, current_key)

    if parsed["constraints"]:
        intake["constraints"] = parsed["constraints"]
    apply_parsed_intake(intake, parsed)

    if (intake.get("awaiting_free_text_for") or "").strip():
        history.append({"role": "assistant", "content": OTHER_TYPE_PROMPT})
        save_intake(ctx.owner_key, session_id, intake, ctx)
        save_history(ctx.owner_key, session_id, history, ctx)
        return history

    if parsed["off_script"]:
        intake["off_script"] = True
        intake["phase"] = "chat"
        save_intake(ctx.owner_key, session_id, intake, ctx)
        reply = gemini_generate_with_tools(
            build_gemini_messages(ctx, session_id, history),
            CHAT_TOOL_DECLARATIONS,
            ctx,
            session_id,
        )
        history.append({"role": "assistant", "content": reply})
        save_history(ctx.owner_key, session_id, history, ctx)
        return history

    intake["step"] = first_missing_step_index(intake)
    if intake["step"] >= len(INTAKE_STEPS):
        save_intake(ctx.owner_key, session_id, intake, ctx)
        return begin_constraints(ctx, session_id, intake, history)[0]

    next_step = INTAKE_STEPS[intake["step"]]
    history.append({"role": "assistant", "content": next_step["question"]})
    save_intake(ctx.owner_key, session_id, intake, ctx)
    save_history(ctx.owner_key, session_id, history, ctx)
    return history


def prepare_chat_send(ctx, session_id, message):
    message = (message or "").strip()
    if not message:
        return {"phase": "complete", "history": get_history(ctx.owner_key, session_id)}

    intake = get_intake(ctx.owner_key, session_id)
    if not intake:
        return {"phase": "expired"}

    ensure_aichat(
        ctx,
        session_id,
        {
            "intake": get_intake(ctx.owner_key, session_id) or {},
            "messages": get_history(ctx.owner_key, session_id),
            "drafts": [],
        },
    )
    history = get_history(ctx.owner_key, session_id)
    history.append({"role": "user", "content": message})

    if intake and intake.get("phase") in ("quota_blocked", "done", "signup", "start_over_ask"):
        history.pop()
        return {"phase": "complete", "history": history}

    if intake and intake.get("phase") == "feedback_comment":
        result = go_to_feedback_rating(ctx, session_id, history, intake, message)
        return {"phase": "complete", "history": result["history"]}

    if intake and intake.get("phase") == "feedback_rating":
        score_text = message.strip()
        if score_text not in ("1", "2", "3", "4", "5"):
            history.pop()
            history.append({"role": "assistant", "content": FEEDBACK_RATING_RETRY_PROMPT})
            save_history(ctx.owner_key, session_id, history, ctx)
            return {"phase": "complete", "history": history}
        result = complete_feedback_with_score(
            ctx, session_id, history, intake, int(score_text), skipped=False
        )
        return {
            "phase": "complete",
            "history": result["history"],
            "program_id": result.get("program_id"),
        }

    if intake and intake.get("phase") == "intake":
        history = handle_intake_typed_message(ctx, session_id, intake, history, message)
        return {"phase": "complete", "history": history}

    if intake and intake.get("phase") == "review":
        intake["phase"] = "chat"
        save_intake(ctx.owner_key, session_id, intake, ctx)
        intake = get_intake(ctx.owner_key, session_id)

    if intake and intake.get("phase") == "awaiting_constraints":
        intake["constraints"] = message
        save_intake(ctx.owner_key, session_id, intake, ctx)
        path, lifts = resolve_weight_path(ctx.user, intake)
        if path == "use_history":
            history = begin_program_generation(ctx, session_id, history)
            if history[-1]["content"] == GENERATING_PROGRAM_MESSAGE:
                return {
                    "phase": "generating",
                    "session_id": session_id,
                    "history": history,
                }
            return {"phase": "complete", "history": history}
        if path == "ask_weights":
            intake["phase"] = "awaiting_weights"
            history.append({"role": "assistant", "content": WEIGHTS_PROMPT})
            save_intake(ctx.owner_key, session_id, intake, ctx)
            save_history(ctx.owner_key, session_id, history, ctx)
            return {"phase": "complete", "history": history}
        intake["phase"] = "awaiting_demographics"
        history.append({"role": "assistant", "content": DEMOGRAPHICS_PROMPT})
        save_intake(ctx.owner_key, session_id, intake, ctx)
        save_history(ctx.owner_key, session_id, history, ctx)
        return {"phase": "complete", "history": history}

    if intake and intake.get("phase") == "awaiting_weights":
        intake["weight_notes"] = message
        save_intake(ctx.owner_key, session_id, intake, ctx)
        history = begin_program_generation(ctx, session_id, history)
        if history[-1]["content"] == GENERATING_PROGRAM_MESSAGE:
            return {
                "phase": "generating",
                "session_id": session_id,
                "history": history,
            }
        return {"phase": "complete", "history": history}

    if intake and intake.get("phase") == "awaiting_demographics":
        intake["demographics_notes"] = message
        save_intake(ctx.owner_key, session_id, intake, ctx)
        history = begin_program_generation(ctx, session_id, history)
        if history[-1]["content"] == GENERATING_PROGRAM_MESSAGE:
            return {
                "phase": "generating",
                "session_id": session_id,
                "history": history,
            }
        return {"phase": "complete", "history": history}

    reply = gemini_generate_with_tools(
        build_gemini_messages(ctx, session_id, history),
        CHAT_TOOL_DECLARATIONS,
        ctx,
        session_id,
        model=settings.AI_MODEL_EDIT,
    )
    history.append({"role": "assistant", "content": reply})
    save_history(ctx.owner_key, session_id, history, ctx)
    return {"phase": "complete", "history": history}


def accept_draft(ctx, session_id):
    if not ctx.user.is_authenticated:
        return None
    from programs.services import create_program_from_ai_draft

    draft = get_draft(ctx.owner_key, session_id)
    if not draft:
        return None
    cleaned, error, unknown_names = validate_program_draft(ctx.user, draft)
    if error:
        return None
    program = create_program_from_ai_draft(ctx.user, cleaned)
    return program


def claim_guest_ai_program(user, guest_id):
    from programs.services import create_program_from_ai_draft

    if not guest_id:
        return None
    owner_key = str(guest_id)
    chat = None
    for candidate in AiChat.objects.filter(guest_id=guest_id).order_by("-updated_at"):
        intake = candidate.intake or {}
        if intake.get("draft_accepted"):
            chat = candidate
            break
    if not chat:
        return None
    session_id = str(chat.session_id)
    draft = get_draft(owner_key, session_id)
    if not draft:
        drafts = chat.drafts or []
        if drafts:
            draft = drafts[-1]
    if not draft:
        return None
    cleaned, error, unknown_names = validate_program_draft(user, draft)
    if error:
        return None
    program = create_program_from_ai_draft(user, cleaned)
    intake = chat.intake or {}
    intake["accepted_program_id"] = program.pk
    chat.user = user
    chat.guest_id = None
    chat.intake = intake
    chat.save(update_fields=["user", "guest_id", "intake", "updated_at"])
    return program
