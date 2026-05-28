"""WebSocket message endpoint registry and dispatch.

Endpoint strings are keys in WS_ENDPOINT_REGISTRY (like paths in urls.py); they are
not resolved by Django HTTP urls.py. Channels routing.py maps the socket URL to
MainConsumer; this module maps each message's endpoint string to a handler.

Handlers are sync callables: (user, attributes) -> response dict matching app.js.
"""

from typing import Any, Callable

from workouts.ws_handlers import (
    handle_add_exercise,
    handle_delete_exercise,
    handle_delete_workout,
    handle_create_set,
    handle_delete_set,
    handle_set_edit_modal_form,
    handle_set_modal_form,
    handle_set_performance_feedback,
    handle_toggle_set_done,
    handle_update_set,
    handle_update_workout,
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
    "workouts/set_modal_form": handle_set_modal_form,
    "workouts/set_edit_modal_form": handle_set_edit_modal_form,
    "workouts/create_set": handle_create_set,
    "workouts/update_set": handle_update_set,
    "workouts/update_workout": handle_update_workout,
    "workouts/toggle_set_done": handle_toggle_set_done,
    "workouts/set_performance_feedback": handle_set_performance_feedback,
    "workouts/delete_set": handle_delete_set,
    "workouts/delete_exercise": handle_delete_exercise,
    "workouts/delete_workout": handle_delete_workout,
    "workouts/add_exercise": handle_add_exercise,
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
