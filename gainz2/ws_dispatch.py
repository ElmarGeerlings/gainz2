"""WebSocket message endpoint registry and dispatch.

Endpoint strings are keys in WS_ENDPOINT_REGISTRY (like paths in urls.py); they are
not resolved by Django HTTP urls.py. Channels routing.py maps the socket URL to
MainConsumer; this module maps each message's endpoint string to a handler.

Handlers are sync callables: (user, attributes) -> response dict matching app.js.
"""

from typing import Any, Callable

from programs.ws_handlers import (
    handle_activate_program,
    handle_deactivate_program,
    handle_delete_program,
    handle_update_program,
)
from exercises.ws_handlers import (
    handle_create_exercise,
    handle_exercise_form,
    handle_update_exercise,
)
from routines.ws_handlers import (
    handle_add_exercise as handle_routine_add_exercise,
    handle_create_set as handle_routine_create_set,
    handle_delete_exercise as handle_routine_delete_exercise,
    handle_delete_routine,
    handle_delete_set as handle_routine_delete_set,
    handle_filter_routines,
    handle_reorder_exercises as handle_routine_reorder_exercises,
    handle_refresh_exercise_view as handle_routine_refresh_exercise_view,
    handle_set_edit_modal_form as handle_routine_set_edit_modal_form,
    handle_set_modal_form as handle_routine_set_modal_form,
    handle_update_routine,
    handle_update_exercise_notes as handle_routine_update_exercise_notes,
    handle_update_set as handle_routine_update_set,
)
from workouts.ws_handlers import (
    handle_add_exercise,
    handle_delete_exercise,
    handle_delete_workout,
    handle_create_set,
    handle_delete_set,
    handle_reorder_exercises,
    handle_refresh_add_exercise_options,
    handle_refresh_exercise_view,
    handle_set_edit_modal_form,
    handle_set_modal_form,
    handle_set_performance_feedback,
    handle_start_routine_workout,
    handle_start_workout,
    handle_toggle_set_done,
    handle_update_set,
    handle_update_workout,
    handle_update_exercise_notes as handle_workout_update_exercise_notes,
)

Handler = Callable[[Any, dict], dict]


def handle_ping(user, attributes):
    return {
        "status": 200,
        "headers": [],
        "html_content": None,
        "json_content": {"message": "pong", "echo_attributes": attributes},
    }


WS_ENDPOINT_REGISTRY: dict[str, Handler] = {
    "ping": handle_ping,
    "exercises/exercise_form": handle_exercise_form,
    "exercises/create_exercise": handle_create_exercise,
    "exercises/update_exercise": handle_update_exercise,
    "workouts/set_modal_form": handle_set_modal_form,
    "workouts/set_edit_modal_form": handle_set_edit_modal_form,
    "workouts/create_set": handle_create_set,
    "workouts/update_set": handle_update_set,
    "workouts/update_workout": handle_update_workout,
    "workouts/toggle_set_done": handle_toggle_set_done,
    "workouts/set_performance_feedback": handle_set_performance_feedback,
    "workouts/update_exercise_notes": handle_workout_update_exercise_notes,
    "workouts/delete_set": handle_delete_set,
    "workouts/delete_exercise": handle_delete_exercise,
    "workouts/delete_workout": handle_delete_workout,
    "workouts/add_exercise": handle_add_exercise,
    "workouts/refresh_add_exercise_options": handle_refresh_add_exercise_options,
    "workouts/refresh_exercise_view": handle_refresh_exercise_view,
    "workouts/reorder_exercises": handle_reorder_exercises,
    "workouts/start_workout": handle_start_workout,
    "workouts/start_routine_workout": handle_start_routine_workout,
    "routines/delete_routine": handle_delete_routine,
    "routines/filter_routines": handle_filter_routines,
    "routines/set_modal_form": handle_routine_set_modal_form,
    "routines/set_edit_modal_form": handle_routine_set_edit_modal_form,
    "routines/create_set": handle_routine_create_set,
    "routines/update_set": handle_routine_update_set,
    "routines/delete_set": handle_routine_delete_set,
    "routines/add_exercise": handle_routine_add_exercise,
    "routines/refresh_add_exercise_options": handle_refresh_add_exercise_options,
    "routines/delete_exercise": handle_routine_delete_exercise,
    "routines/update_routine": handle_update_routine,
    "routines/update_exercise_notes": handle_routine_update_exercise_notes,
    "routines/refresh_exercise_view": handle_routine_refresh_exercise_view,
    "routines/reorder_exercises": handle_routine_reorder_exercises,
    "programs/activate_program": handle_activate_program,
    "programs/deactivate_program": handle_deactivate_program,
    "programs/delete_program": handle_delete_program,
    "programs/update_program": handle_update_program,
}


def dispatch_ws_endpoint(user, endpoint, attributes):
    if not endpoint or endpoint not in WS_ENDPOINT_REGISTRY:
        return {
            "status": 404,
            "headers": [],
            "html_content": None,
            "json_content": {"error": f"unknown endpoint: {endpoint}"},
        }
    handler = WS_ENDPOINT_REGISTRY[endpoint]
    return handler(user, attributes)
