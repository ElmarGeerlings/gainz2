from decimal import Decimal

from django.template.loader import render_to_string

from gainz2.utils import render_toast
from routines.models import RoutineSet
from routines.models import Routine
from routines.services import (
    add_exercise_to_routine,
    create_routine_set,
    delete_routine,
    delete_routine_exercise,
    delete_routine_set,
    get_add_set_defaults,
    get_routine,
    get_routine_exercise,
    list_routines_for_program,
    reorder_routine_exercises,
    update_routine,
    update_routine_exercise_notes,
    update_routine_set,
)
from utils.templatetags.formatting import weight_display
from workouts.services import attach_rest_times


def handle_delete_routine(user, attributes):
    routine_id = int(attributes["data-routine-id"])
    delete_routine(user, routine_id)
    return {
        "status": 302,
        "headers": [["Location", "/routines/"]],
        "json_content": {},
    }


def handle_filter_routines(user, attributes):
    program_id = attributes.get("program_id") or attributes.get("value") or ""
    if program_id:
        program_id = int(program_id)
    else:
        program_id = None
    routines = list_routines_for_program(user, program_id)
    html = render_to_string(
        "routines/routines_list_items.html",
        {
            "routines": routines,
            "filtered_by_program": program_id is not None,
        },
    )
    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "target": "#routines-list-container",
            "html": html,
        },
    }


def handle_set_modal_form(user, attributes):
    routine_exercise_id = int(attributes["data-exercise-id"])
    weight, reps = get_add_set_defaults(user, routine_exercise_id)
    re = get_routine_exercise(routine_exercise_id)
    html = render_to_string(
        "workouts/set_modal.html",
        {
            "is_add": True,
            "we": re,
            "weight": weight,
            "reps": reps,
            "is_warmup": False,
            "weight_increment": re.exercise.weight_increment,
            "reps_range": range(100),
            "is_routine": True,
            "endpoint_ns": "routines",
        },
    )
    return {
        "status": 200,
        "headers": [],
        "json_content": {"html": html},
    }


def handle_set_edit_modal_form(user, attributes):
    set_id = int(attributes["data-set-id"])
    routine_set = RoutineSet.objects.select_related(
        "routine_exercise__exercise"
    ).get(pk=set_id)
    html = render_to_string(
        "workouts/set_modal.html",
        {
            "is_add": False,
            "set": routine_set,
            "weight": routine_set.weight,
            "reps": routine_set.reps,
            "is_warmup": routine_set.is_warmup,
            "smartchange_enabled": user.settings.smartchange_enabled,
            "weight_increment": routine_set.routine_exercise.exercise.weight_increment,
            "reps_range": range(100),
            "is_routine": True,
            "endpoint_ns": "routines",
        },
    )
    return {
        "status": 200,
        "headers": [],
        "json_content": {"html": html},
    }


def handle_create_set(user, attributes):
    routine_exercise_id = int(attributes["routine_exercise_id"])
    weight = Decimal(attributes["weight"])
    reps = int(float(attributes["reps"]))
    is_warmup = attributes.get("is_warmup", False)
    routine_set, routine_exercise = create_routine_set(
        routine_exercise_id, weight, reps, bool(is_warmup)
    )
    html = render_to_string(
        "workouts/exercise_sets_block.html",
        {
            "we": routine_exercise,
            "is_routine": True,
            "endpoint_ns": "routines",
        },
    )
    target = f'[data-exercise-sets-for="{routine_exercise.pk}"]'
    message = (
        f"Set added: {weight_display(routine_set.weight)} x {routine_set.reps}"
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


def handle_add_exercise(user, attributes):
    routine_id = int(attributes["data-session-id"])
    exercise_id = int(attributes["exercise"])
    exercise_type = attributes.get("exercise_type") or None
    current_routine_exercise_id = attributes.get("data-current-exercise-id")
    if current_routine_exercise_id:
        current_routine_exercise_id = int(current_routine_exercise_id)
    else:
        current_routine_exercise_id = None
    routine, new_exercise_index = add_exercise_to_routine(
        routine_id,
        exercise_id,
        current_routine_exercise_id,
        exercise_type,
    )
    attach_rest_times(routine, user.settings)
    html = render_to_string(
        "workouts/workout_exercise_ui.html",
        {
            "session": routine,
            "is_routine": True,
            "endpoint_ns": "routines",
            "active_exercise_index": new_exercise_index,
            "user_settings": user.settings,
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
    routine_exercise = delete_routine_set(set_id)
    html = render_to_string(
        "workouts/exercise_sets_block.html",
        {
            "we": routine_exercise,
            "is_routine": True,
            "endpoint_ns": "routines",
        },
    )
    target = f'[data-exercise-sets-for="{routine_exercise.pk}"]'
    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "target": target,
            "html": html,
        },
    }


def handle_delete_exercise(user, attributes):
    routine_exercise_id = int(attributes["data-exercise-id"])
    current_exercise_index = int(attributes["data-current-exercise-index"])
    routine, active_exercise_index = delete_routine_exercise(
        routine_exercise_id,
        current_exercise_index,
    )
    attach_rest_times(routine, user.settings)
    html = render_to_string(
        "workouts/workout_exercise_ui.html",
        {
            "session": routine,
            "is_routine": True,
            "endpoint_ns": "routines",
            "active_exercise_index": active_exercise_index,
            "user_settings": user.settings,
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


def handle_update_routine(user, attributes):
    routine_id = int(attributes["routine_id"])
    name = attributes["name"]
    notes = attributes.get("notes", "")
    routine = update_routine(user, routine_id, name, notes)
    html = render_to_string(
        "routines/routine_header.html",
        {"routine": routine},
    )
    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "target": "#routine-header",
            "html": html,
        },
    }


def handle_update_exercise_notes(user, attributes):
    routine_exercise_id = int(attributes["data-exercise-id"])
    notes = attributes.get("data-notes", "")
    update_routine_exercise_notes(user, routine_exercise_id, notes)
    return {
        "status": 200,
        "headers": [],
        "json_content": {},
    }


def handle_reorder_exercises(user, attributes):
    session_id = int(attributes["data-session-id"])
    ordered_exercise_ids = [
        exercise_id
        for exercise_id in attributes["data-exercise-ids"].split(",")
        if exercise_id
    ]
    reorder_routine_exercises(user, session_id, ordered_exercise_ids)
    return {
        "status": 200,
        "headers": [],
        "json_content": {},
    }


def handle_refresh_exercise_view(user, attributes):
    view = attributes.get("data-view")
    session_id = int(attributes["data-session-id"])
    Routine.objects.get(pk=session_id, user=user)
    routine = get_routine(session_id)
    attach_rest_times(routine, user.settings)
    exercises = list(routine.exercises.all())
    active_exercise_index = 0
    if view == "detail":
        active_exercise_id = attributes.get("data-active-exercise-id")
        if active_exercise_id:
            active_exercise_id = int(active_exercise_id)
            for index, exercise in enumerate(exercises):
                if exercise.pk == active_exercise_id:
                    active_exercise_index = index
                    break
    if view == "detail":
        target = "#exercise-detail-view"
        html = render_to_string(
            "workouts/exercise_detail_view.html",
            {
                "session": routine,
                "endpoint_ns": "routines",
                "is_routine": True,
                "active_exercise_index": active_exercise_index,
                "user_settings": user.settings,
            },
        )
    elif view == "overview":
        target = "#exercise-overview-view"
        html = render_to_string(
            "workouts/exercise_overview_view.html",
            {
                "session": routine,
                "endpoint_ns": "routines",
                "is_routine": True,
                "active_exercise_index": active_exercise_index,
                "user_settings": user.settings,
            },
        )
    else:
        return {
            "status": 400,
            "headers": [],
            "json_content": {"error": f"unknown view: {view}"},
        }
    json_content = {
        "target": target,
        "html": html,
    }
    if view == "detail":
        json_content["active_exercise_index"] = active_exercise_index
    return {
        "status": 200,
        "headers": [],
        "json_content": json_content,
    }


def handle_update_set(user, attributes):
    set_id = int(attributes["set_id"])
    weight = Decimal(attributes["weight"])
    reps = int(float(attributes["reps"]))
    is_warmup = attributes.get("is_warmup", False)
    smartchange = bool(attributes.get("smartchange", False))
    routine_set, routine_exercise, warmup_changed, siblings_updated_count = update_routine_set(
        set_id, weight, reps, bool(is_warmup), user=user, smartchange=smartchange
    )
    user.settings.smartchange_enabled = smartchange
    user.settings.save(update_fields=["smartchange_enabled"])
    if warmup_changed or siblings_updated_count > 0:
        html = render_to_string(
            "workouts/exercise_sets_block.html",
            {
                "we": routine_exercise,
                "is_routine": True,
                "endpoint_ns": "routines",
            },
        )
        target = f'[data-exercise-sets-for="{routine_exercise.pk}"]'
    else:
        html = render_to_string(
            "workouts/set_row_cells.html",
            {
                "set": routine_set,
                "we": routine_exercise,
                "is_routine": True,
                "endpoint_ns": "routines",
            },
        )
        target = f'[data-set-id="{routine_set.pk}"]'
    if siblings_updated_count > 0:
        total_updated = siblings_updated_count + 1
        message = f"{total_updated} sets updated"
    else:
        message = (
            f"Set updated to {weight_display(routine_set.weight)} kg x {routine_set.reps}"
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
