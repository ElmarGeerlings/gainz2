"""WebSocket message handlers for the workouts app.

Each handler is a sync function (user, attributes) -> dict matching static/js/app.js
(status, headers, html_content, json_content).

Register handlers in gainz2.ws_dispatch.WS_ENDPOINT_REGISTRY.

Business logic belongs in workouts.services; keep these thin.
"""

from decimal import Decimal

from django.template.loader import render_to_string

from gainz2.utils import render_toast
from utils.templatetags.formatting import weight_display
from workouts.services import (
    add_exercise_to_workout,
    create_exercise_set,
    delete_exercise_set,
    delete_workout,
    delete_workout_exercise,
    get_add_set_defaults,
    get_workout_exercise,
    set_workout_exercise_feedback,
    toggle_exercise_set_completed,
    update_exercise_set,
    update_workout,
)
from workouts.models import ExerciseSet


def handle_set_modal_form(user, attributes):
    workout_exercise_id = int(attributes["data-exercise-id"])
    weight, reps = get_add_set_defaults(user, workout_exercise_id)
    we = get_workout_exercise(workout_exercise_id)
    html = render_to_string(
        "workouts/set_modal.html",
        {
            "is_add": True,
            "we": we,
            "weight": weight,
            "reps": reps,
            "is_warmup": False,
            "uses_wheel": True,
            "reps_range": range(100),
        },
    )
    return {
        "status": 200,
        "headers": [],
        "json_content": {"html": html},
    }


def handle_set_edit_modal_form(user, attributes):
    set_id = int(attributes["data-set-id"])
    exercise_set = ExerciseSet.objects.select_related("workout_exercise").get(pk=set_id)
    html = render_to_string(
        "workouts/set_modal.html",
        {
            "is_add": False,
            "set": exercise_set,
            "weight": exercise_set.weight,
            "reps": exercise_set.reps,
            "is_warmup": exercise_set.is_warmup,
            "uses_wheel": True,
            "reps_range": range(100),
        },
    )
    return {
        "status": 200,
        "headers": [],
        "json_content": {"html": html},
    }


def handle_create_set(user, attributes):
    workout_exercise_id = int(attributes["workout_exercise_id"])
    weight = Decimal(attributes["weight"])
    reps = int(float(attributes["reps"]))
    is_warmup = attributes.get("is_warmup", False)
    exercise_set, workout_exercise = create_exercise_set(
        workout_exercise_id, weight, reps, bool(is_warmup)
    )
    html = render_to_string(
        "workouts/exercise_sets_block.html",
        {"we": workout_exercise},
    )
    target = f'[data-exercise-sets-for="{workout_exercise.pk}"]'
    message = (
        f"Set added: {weight_display(exercise_set.weight)} x {exercise_set.reps}"
    )
    toast_html = render_toast(message, variant="success")
    delay_ms = 2500
    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "target": target,
            "html": html,
            "toast_html": toast_html,
            "toast_delay_ms": delay_ms,
        },
    }


def handle_set_performance_feedback(user, attributes):
    workout_exercise_id = int(attributes["data-exercise-id"])
    feedback = attributes["data-feedback"]
    set_workout_exercise_feedback(user, workout_exercise_id, feedback)
    return {
        "status": 200,
        "headers": [],
        "json_content": {},
    }


def handle_toggle_set_done(user, attributes):
    set_id = int(attributes["data-set-id"])
    exercise_set, workout_exercise, is_completed = toggle_exercise_set_completed(set_id)
    html = render_to_string(
        "workouts/set_row_cells.html",
        {"set": exercise_set, "we": workout_exercise},
    )
    target = f'[data-set-id="{exercise_set.pk}"]'
    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "target": target,
            "html": html,
        },
    }


def handle_add_exercise(user, attributes):
    workout_id = int(attributes["data-workout-id"])
    exercise_id = int(attributes["exercise"])
    exercise_type = attributes.get("exercise_type") or None
    current_workout_exercise_id = attributes.get("data-current-exercise-id")
    if current_workout_exercise_id:
        current_workout_exercise_id = int(current_workout_exercise_id)
    else:
        current_workout_exercise_id = None
    workout, new_workout_exercise, new_exercise_index = add_exercise_to_workout(
        workout_id,
        exercise_id,
        current_workout_exercise_id,
        exercise_type,
    )
    html = render_to_string(
        "workouts/workout_exercise_ui.html",
        {
            "workout": workout,
            "active_exercise_index": new_exercise_index,
        },
    )
    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "target": "#workout-exercise-ui",
            "html": html,
            "new_exercise_index": new_exercise_index,
        },
    }


def handle_delete_set(user, attributes):
    set_id = int(attributes["data-set-id"])
    workout_exercise = delete_exercise_set(set_id)
    html = render_to_string(
        "workouts/exercise_sets_block.html",
        {"we": workout_exercise},
    )
    target = f'[data-exercise-sets-for="{workout_exercise.pk}"]'
    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "target": target,
            "html": html,
        },
    }


def handle_delete_exercise(user, attributes):
    workout_exercise_id = int(attributes["data-exercise-id"])
    current_exercise_index = int(attributes["data-current-exercise-index"])
    workout, active_exercise_index = delete_workout_exercise(
        workout_exercise_id,
        current_exercise_index,
    )
    html = render_to_string(
        "workouts/workout_exercise_ui.html",
        {
            "workout": workout,
            "active_exercise_index": active_exercise_index,
        },
    )
    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "target": "#workout-exercise-ui",
            "html": html,
            "active_exercise_index": active_exercise_index,
        },
    }


def handle_delete_workout(user, attributes):
    workout_id = int(attributes["data-workout-id"])
    delete_workout(user, workout_id)
    return {
        "status": 302,
        "headers": [["Location", "/workouts/"]],
        "json_content": {},
    }


def handle_update_workout(user, attributes):
    workout_id = int(attributes["workout_id"])
    name = attributes["name"]
    date_str = attributes["date"]
    notes = attributes.get("notes", "")
    workout = update_workout(user, workout_id, name, date_str, notes)
    html = render_to_string(
        "workouts/workout_header.html",
        {"workout": workout},
    )
    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "target": "#workout-header",
            "html": html,
        },
    }


def handle_update_set(user, attributes):
    set_id = int(attributes["set_id"])
    weight = Decimal(attributes["weight"])
    reps = int(float(attributes["reps"]))
    is_warmup = attributes.get("is_warmup", False)
    exercise_set, workout_exercise, warmup_changed = update_exercise_set(
        set_id, weight, reps, bool(is_warmup)
    )
    if warmup_changed:
        html = render_to_string(
            "workouts/exercise_sets_block.html",
            {"we": workout_exercise},
        )
        target = f'[data-exercise-sets-for="{workout_exercise.pk}"]'
    else:
        html = render_to_string(
            "workouts/set_row_cells.html",
            {"set": exercise_set, "we": workout_exercise},
        )
        target = f'[data-set-id="{exercise_set.pk}"]'
    message = (
        f"Set updated to {weight_display(exercise_set.weight)} kg x {exercise_set.reps}"
    )
    toast_html = render_toast(message, variant="success")
    delay_ms = 2500
    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "target": target,
            "html": html,
            "toast_html": toast_html,
            "toast_delay_ms": delay_ms,
        },
    }
