import json

from exercises.catalog_metadata import (
    allowed_equipment_for_intake,
    exercise_passes_equipment_filter,
)
from exercises.services import list_exercises_for_user
from progress.services import get_user_lift_history

EXERCISE_PLAN_TOOL = {
    "name": "submit_exercise_plan",
    "description": (
        "Submit the exercise list for the program (no sets yet). "
        "Every exercise_name must match an entry in the exercise catalog."
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
                                },
                                "required": [
                                    "exercise_name",
                                    "exercise_type",
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
}

PROGRAM_DRAFT_TOOL = {
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
}

CATALOG_TOOL = {
    "name": "get_exercise_catalog",
    "description": (
        "Get exercises available for this user, filtered by their equipment. "
        "Call before submit_exercise_plan or submit_program_draft."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
    },
}

HISTORY_TOOL = {
    "name": "get_lift_history",
    "description": (
        "Get exercises this user has logged, each with the weight "
        "and reps of their most recent work set. Use for starting loads."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
    },
}

STAGE1_TOOL_DECLARATIONS = [
    EXERCISE_PLAN_TOOL,
]

STAGE2_TOOL_DECLARATIONS = [
    PROGRAM_DRAFT_TOOL,
]

CHAT_TOOL_DECLARATIONS = [
    CATALOG_TOOL,
    HISTORY_TOOL,
    PROGRAM_DRAFT_TOOL,
]

TOOL_DECLARATIONS = CHAT_TOOL_DECLARATIONS


def build_filtered_catalog(user, intake):
    exercises = list_exercises_for_user(
        user if user.is_authenticated else None,
        search_query="",
        exercise_type="",
        primary_bodypart="",
        custom_filter="",
    )
    allowed_tags = allowed_equipment_for_intake(intake)
    items = []
    for exercise in exercises:
        if not exercise_passes_equipment_filter(exercise, allowed_tags):
            continue
        items.append({
            "name": exercise.name,
            "primary_bodypart": exercise.primary_bodypart or "",
            "movement_kind": exercise.movement_kind,
            "push_pull": exercise.push_pull or "na",
        })
    items.sort(key=lambda item: item["name"].lower())
    return {"exercises": items}


def format_catalog_for_prompt(user, intake):
    catalog = build_filtered_catalog(user, intake)
    return json.dumps(catalog, separators=(",", ":"))


def run_get_exercise_catalog(user, args, intake=None):
    return build_filtered_catalog(user, intake)


def run_get_lift_history(user, args):
    if not user.is_authenticated:
        return {"lifts": []}
    return {"lifts": get_user_lift_history(user)}
