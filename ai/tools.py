from exercises.services import list_exercises_for_user
from progress.services import get_user_lift_history

TOOL_DECLARATIONS = [
    {
        "name": "get_exercise_catalog",
        "description": (
            "Get the full list of exercise names available for this user "
            "(built-in catalog plus their custom exercises). Call this when "
            "ready to build a program, before submit_program_draft."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_lift_history",
        "description": (
            "Get exercises this user has logged in the app, each with the weight "
            "and reps of their most recent work set. Call early — before asking for "
            "lifting numbers or age/sex/bodyweight. Prefer these exercises when they "
            "fit, and use the weights/reps as the main guide for starting loads."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "submit_program_draft",
        "description": (
            "Submit a structured workout program draft for the user to preview. "
            "Every exercise_name must be an exact match from get_exercise_catalog "
            "(case may differ). Do not invent names. "
            "Every set must include weight (kg): prefer last work-set loads from "
            "get_lift_history when available; otherwise use a conservative starting "
            "load for barbell/dumbbell/machine work; use 0 only for true bodyweight "
            "exercises. Prefer slightly light over heavy when unsure."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "routines": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "exercises": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "exercise_name": {"type": "string"},
                                        "exercise_type": {
                                            "type": "string",
                                            "enum": [
                                                "primary",
                                                "secondary",
                                                "accessory",
                                            ],
                                        },
                                        "sets": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "reps": {"type": "integer"},
                                                    "weight": {
                                                        "type": "number",
                                                        "description": (
                                                            "kg. Required. 0 only for "
                                                            "bodyweight exercises."
                                                        ),
                                                    },
                                                    "is_warmup": {"type": "boolean"},
                                                },
                                                "required": ["reps", "weight"],
                                            },
                                        },
                                    },
                                    "required": [
                                        "exercise_name",
                                        "exercise_type",
                                        "sets",
                                    ],
                                },
                            },
                        },
                        "required": ["name", "exercises"],
                    },
                },
            },
            "required": ["name", "routines"],
        },
    },
]


def run_get_exercise_catalog(user, args):
    exercises = list_exercises_for_user(
        user,
        search_query="",
        exercise_type="",
        primary_bodypart="",
        custom_filter="",
    )
    names = sorted({exercise.name for exercise in exercises}, key=str.lower)
    return {"exercise_names": names}


def run_get_lift_history(user, args):
    return {"lifts": get_user_lift_history(user)}
