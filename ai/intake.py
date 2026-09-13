from progress.services import get_user_lift_history

INTAKE_STEPS = [
    {
        "key": "goal",
        "question": "What is your main fitness goal?",
        "choices": [
            {"id": "hypertrophy", "label": "Hypertrophy"},
            {"id": "strength", "label": "Strength"},
            {"id": "general_fitness", "label": "General fitness"},
            {"id": "other", "label": "Other"},
        ],
    },
    {
        "key": "level",
        "question": "How would you describe your training experience?",
        "choices": [
            {"id": "beginner", "label": "Beginner"},
            {"id": "intermediate", "label": "Intermediate"},
            {"id": "advanced", "label": "Advanced"},
            {"id": "other", "label": "Other"},
        ],
    },
    {
        "key": "days",
        "question": "How many days per week do you want to train?",
        "choices": [
            {"id": "1", "label": "1 day"},
            {"id": "2", "label": "2 days"},
            {"id": "3", "label": "3 days"},
            {"id": "4", "label": "4 days"},
            {"id": "5", "label": "5 days"},
            {"id": "6", "label": "6 days"},
            {"id": "7", "label": "7 days"},
        ],
    },
    {
        "key": "duration",
        "question": "How long do you usually want each gym session to be?",
        "choices": [
            {"id": "under_45", "label": "Under 45 min"},
            {"id": "about_60", "label": "About 60 min"},
            {"id": "75_plus", "label": "75+ min"},
            {"id": "other", "label": "Other"},
        ],
    },
    {
        "key": "equipment",
        "question": "What equipment do you have access to?",
        "choices": [
            {"id": "full_gym", "label": "Full gym"},
            {"id": "dumbbells_bar", "label": "Dumbbells and bar"},
            {"id": "bodyweight", "label": "Bodyweight"},
            {"id": "other", "label": "Other"},
        ],
    },
]

INTAKE_STEP_KEYS = {step["key"] for step in INTAKE_STEPS}

CONSTRAINTS_PROMPT = (
    "Anything you want to avoid or must include? "
    "For example injuries, lifts you skip, or exercises you always want. "
    "Optional — reply with none or leave blank to skip."
)

WEIGHTS_PROMPT = (
    "What are your typical working weights for a few main lifts — "
    "for example squat, bench press, and overhead press? Rough numbers are fine."
)

DEMOGRAPHICS_PROMPT = (
    "To set sensible starting weights, what is your age, sex, and bodyweight in kg?"
)

OTHER_TYPE_PROMPT = "Other — type your answer below."

PROGRAM_READY_MESSAGE = "Your program is ready — see it above."

EDIT_PROMPT = "Please tell me how you want to change this program."

FEEDBACK_COMMENT_PROMPT = (
    "Please share any feedback you have and we will use it to improve the program builder!"
)

FEEDBACK_RATING_PROMPT = "Please rate your experience from 1 to 5."

FEEDBACK_RATING_RETRY_PROMPT = "Please rate your experience from 1 to 5, or tap Skip."

START_OVER_ASK_PROMPT = "Would you like to start over?"

THANK_YOU_MESSAGE = "Thanks for your feedback!"

FEEDBACK_SKIP_CHOICE = {"id": "skip", "label": "Skip"}

FEEDBACK_RATING_CHOICES = [
    {"id": "1", "label": "1"},
    {"id": "2", "label": "2"},
    {"id": "3", "label": "3"},
    {"id": "4", "label": "4"},
    {"id": "5", "label": "5"},
]

START_OVER_CHOICES = [
    {"id": "yes", "label": "Yes"},
    {"id": "no", "label": "No"},
]

GOAL_LABELS = {
    "hypertrophy": "Hypertrophy",
    "strength": "Strength",
    "general_fitness": "General fitness",
}

LEVEL_LABELS = {
    "beginner": "Beginner",
    "intermediate": "Intermediate",
    "advanced": "Advanced",
}

DAYS_LABELS = {
    "1": "1 day per week",
    "2": "2 days per week",
    "3": "3 days per week",
    "4": "4 days per week",
    "5": "5 days per week",
    "6": "6 days per week",
    "7": "7 days per week",
}

DURATION_LABELS = {
    "under_45": "Under 45 min per session",
    "about_60": "About 60 min per session",
    "75_plus": "75+ min per session",
}

EQUIPMENT_LABELS = {
    "full_gym": "Full gym",
    "dumbbells_bar": "Dumbbells and bar",
    "bodyweight": "Bodyweight only",
}

PROFILE_ANSWER_LABELS = {
    "goal": "Goal",
    "level": "Experience",
    "days": "Training frequency",
    "duration": "Session length",
    "equipment": "Equipment",
}


def new_intake():
    return {
        "phase": "intake",
        "step": 0,
        "answers": {},
        "other_notes": {},
        "awaiting_free_text_for": "",
        "constraints": "",
        "weight_notes": "",
        "demographics_notes": "",
        "off_script": False,
    }


def profile_answer_text(intake, step_key):
    answers = intake.get("answers") or {}
    value = answers.get(step_key)
    if not value:
        return None
    label_maps = {
        "goal": GOAL_LABELS,
        "level": LEVEL_LABELS,
        "days": DAYS_LABELS,
        "duration": DURATION_LABELS,
        "equipment": EQUIPMENT_LABELS,
    }
    label = label_maps.get(step_key, {}).get(value, value)
    other_notes = intake.get("other_notes") or {}
    if value == "other" and other_notes.get(step_key):
        label = f"{other_notes[step_key]} (Other)"
    return label


def format_history_summary(lifts):
    if not lifts:
        return ""
    lines = []
    for lift in lifts[:20]:
        weight = lift["weight"]
        if weight == int(weight):
            weight_text = str(int(weight))
        else:
            weight_text = str(weight)
        lines.append(f"- {lift['name']}: {weight_text} kg x {lift['reps']} reps")
    if len(lifts) > 20:
        lines.append(f"- ... and {len(lifts) - 20} more logged exercises")
    return "Recent logged work sets:\n" + "\n".join(lines)


def build_profile_context(intake, history_summary):
    lines = ["User program profile:"]

    for step_key, prefix in PROFILE_ANSWER_LABELS.items():
        text = profile_answer_text(intake, step_key)
        if text:
            lines.append(f"- {prefix}: {text}")

    constraints = (intake.get("constraints") or "").strip()
    if constraints:
        lines.append(f"- Constraints: {constraints}")

    if intake.get("off_script"):
        lines.append("- User went off-script for one or more intake answers; respect their free-text replies in the chat.")

    weight_notes = (intake.get("weight_notes") or "").strip()
    if weight_notes:
        lines.append(f"- Typical working weights: {weight_notes}")

    demographics_notes = (intake.get("demographics_notes") or "").strip()
    if demographics_notes:
        lines.append(f"- Age, sex, bodyweight: {demographics_notes}")

    if history_summary:
        lines.append("")
        lines.append(history_summary)

    return "\n".join(lines)


def resolve_weight_path(user, intake):
    if not user.is_authenticated:
        lifts = []
    else:
        lifts = get_user_lift_history(user)
    if lifts:
        return "use_history", lifts

    level = intake.get("answers", {}).get("level")
    if level in ("intermediate", "advanced"):
        return "ask_weights", lifts
    return "ask_demographics", lifts


def get_current_step(intake):
    if not intake or intake.get("phase") != "intake":
        return None
    step_index = intake.get("step", 0)
    if step_index < 0 or step_index >= len(INTAKE_STEPS):
        return None
    return INTAKE_STEPS[step_index]


def first_missing_step_index(intake):
    answers = intake.get("answers") or {}
    for index, step in enumerate(INTAKE_STEPS):
        if step["key"] not in answers:
            return index
    return len(INTAKE_STEPS)


def apply_parsed_intake(intake, parsed):
    answers = intake.setdefault("answers", {})
    overwrite_fields = parsed.get("overwrite_fields") or []
    fields = parsed.get("fields") or {}
    for key, value in fields.items():
        if key not in answers or key in overwrite_fields:
            answers[key] = value

    other_notes = parsed.get("other_notes") or {}
    intake_notes = intake.setdefault("other_notes", {})
    for key, note in other_notes.items():
        if key not in INTAKE_STEP_KEYS:
            continue
        note_text = str(note).strip()
        if note_text:
            intake_notes[key] = note_text

    awaiting = (intake.get("awaiting_free_text_for") or "").strip()
    if awaiting and awaiting in answers:
        intake["awaiting_free_text_for"] = ""


def get_choices_context(intake):
    if not intake:
        return None
    phase = intake.get("phase")
    if phase == "feedback_comment":
        return {"choices": [FEEDBACK_SKIP_CHOICE]}
    if phase == "feedback_rating":
        return {"choices": FEEDBACK_RATING_CHOICES + [FEEDBACK_SKIP_CHOICE]}
    if phase == "start_over_ask":
        return {"choices": START_OVER_CHOICES}
    if phase != "intake":
        return None
    if (intake.get("awaiting_free_text_for") or "").strip():
        return None
    step = get_current_step(intake)
    if not step:
        return None
    return {
        "question": step["question"],
        "choices": step["choices"],
    }
