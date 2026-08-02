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
            {"id": "2", "label": "2 days"},
            {"id": "3", "label": "3 days"},
            {"id": "4", "label": "4 days"},
            {"id": "5_plus", "label": "5+ days"},
            {"id": "other", "label": "Other"},
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

WEIGHTS_PROMPT = (
    "What are your typical working weights for a few main lifts — "
    "for example squat, bench press, and overhead press? Rough numbers are fine."
)

DEMOGRAPHICS_PROMPT = (
    "To set sensible starting weights, what is your age, sex, and bodyweight in kg?"
)

OFF_SCRIPT_PROMPT = "Tell me in your own words."

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
    "2": "2 days per week",
    "3": "3 days per week",
    "4": "4 days per week",
    "5_plus": "5+ days per week",
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


def new_intake():
    return {
        "phase": "intake",
        "step": 0,
        "answers": {},
        "weight_notes": "",
        "demographics_notes": "",
        "off_script": False,
    }


def find_choice(step_index, choice_id):
    step = INTAKE_STEPS[step_index]
    for choice in step["choices"]:
        if choice["id"] == choice_id:
            return choice
    return None


def choice_label_for_answer(step_key, answer_value):
    if answer_value == "other":
        return "Other"
    label_maps = {
        "goal": GOAL_LABELS,
        "level": LEVEL_LABELS,
        "days": DAYS_LABELS,
        "duration": DURATION_LABELS,
        "equipment": EQUIPMENT_LABELS,
    }
    return label_maps.get(step_key, {}).get(answer_value, answer_value)


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
    answers = intake.get("answers") or {}
    lines = ["User program profile:"]

    goal = answers.get("goal")
    if goal:
        lines.append(f"- Goal: {choice_label_for_answer('goal', goal)}")

    level = answers.get("level")
    if level:
        lines.append(f"- Experience: {choice_label_for_answer('level', level)}")

    days = answers.get("days")
    if days:
        lines.append(f"- Training frequency: {choice_label_for_answer('days', days)}")

    duration = answers.get("duration")
    if duration:
        lines.append(f"- Session length: {choice_label_for_answer('duration', duration)}")

    equipment = answers.get("equipment")
    if equipment:
        lines.append(f"- Equipment: {choice_label_for_answer('equipment', equipment)}")

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

    lines.append("")
    lines.append(
        "Design a complete program matching this profile. "
        "Use get_exercise_catalog and submit_program_draft when ready."
    )
    return "\n".join(lines)


def resolve_weight_path(user, intake):
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


def get_choices_context(intake):
    step = get_current_step(intake)
    if not step:
        return None
    return {
        "question": step["question"],
        "choices": step["choices"],
    }
