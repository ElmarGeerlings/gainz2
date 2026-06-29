"""WebSocket message handlers for the exercises app."""

from django.template.loader import render_to_string

from gainz2.utils import WEIGHT_INCREMENT_CHOICES, render_toast
from exercises.services import (
    create_custom_exercise,
    get_exercise_for_modal,
    update_custom_exercise,
)
from exercises.models import Exercise


def handle_exercise_form(user, attributes):
    exercise_id_raw = attributes.get("data-exercise-id", "")
    choice_context = {
        "bodypart_choices": Exercise.BODYPART_CHOICES,
        "exercise_type_choices": Exercise.EXERCISE_TYPE_CHOICES,
        "weight_increment_choices": WEIGHT_INCREMENT_CHOICES,
    }

    if not exercise_id_raw:
        html = render_to_string(
            "exercises/exercise_modal.html",
            {
                "mode": "add",
                "exercise": None,
                **choice_context,
            },
        )
        return {
            "status": 200,
            "headers": [],
            "json_content": {"html": html},
        }

    exercise = get_exercise_for_modal(user, int(exercise_id_raw))
    if exercise.is_custom:
        html = render_to_string(
            "exercises/exercise_modal.html",
            {
                "mode": "edit",
                "exercise": exercise,
                **choice_context,
            },
        )
    else:
        html = render_to_string(
            "exercises/exercise_modal_view.html",
            {"exercise": exercise},
        )
    return {
        "status": 200,
        "headers": [],
        "json_content": {"html": html},
    }


def handle_create_exercise(user, attributes):
    result = create_custom_exercise(user, attributes)
    if "error" in result:
        toast_html = render_toast(result["error"], variant="danger")
        return {
            "status": 400,
            "headers": [],
            "json_content": {
                "toast_html": toast_html,
                "toast_delay_ms": 3000,
            },
        }
    exercise = result["exercise"]
    toast_html = render_toast(
        f'Exercise "{exercise.name}" created.',
        variant="success",
    )
    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "toast_html": toast_html,
            "toast_delay_ms": 2500,
        },
    }


def handle_update_exercise(user, attributes):
    exercise_id = int(attributes["exercise_id"])
    result = update_custom_exercise(user, exercise_id, attributes)
    if "error" in result:
        toast_html = render_toast(result["error"], variant="danger")
        return {
            "status": 400,
            "headers": [],
            "json_content": {
                "toast_html": toast_html,
                "toast_delay_ms": 3000,
            },
        }
    exercise = result["exercise"]
    toast_html = render_toast(
        f'Exercise "{exercise.name}" updated.',
        variant="success",
    )
    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "toast_html": toast_html,
            "toast_delay_ms": 2500,
        },
    }
