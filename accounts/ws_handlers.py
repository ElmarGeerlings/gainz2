from gainz2.utils import render_toast
from accounts.services import (
    REST_TIME_MAX_SECONDS,
    REST_TIME_MIN_SECONDS,
    USER_SETTING_BOOLEAN_KEYS,
    USER_SETTING_REST_KEYS,
    update_user_setting,
)


def handle_update_user_setting(user, attributes):
    setting_key = attributes.get("data-setting")
    if setting_key in USER_SETTING_BOOLEAN_KEYS:
        checked = attributes.get("checked")
        if checked is True or checked == "true":
            value = True
        elif checked is False or checked == "false":
            value = False
        else:
            toast_html = render_toast("Invalid value.", variant="danger")
            return {
                "status": 400,
                "headers": [],
                "json_content": {
                    "toast_html": toast_html,
                    "toast_delay_ms": 2500,
                },
            }
        update_user_setting(user, setting_key, value)
        toast_html = render_toast("Saved", variant="success")
        return {
            "status": 200,
            "headers": [],
            "json_content": {
                "toast_html": toast_html,
                "toast_delay_ms": 1500,
            },
        }

    if setting_key in USER_SETTING_REST_KEYS:
        minutes_raw = attributes.get("rest_minutes", "0")
        seconds_raw = attributes.get("rest_seconds", "0")
        if minutes_raw in (None, "") or seconds_raw in (None, ""):
            toast_html = render_toast("Invalid rest time.", variant="danger")
            return {
                "status": 400,
                "headers": [],
                "json_content": {
                    "toast_html": toast_html,
                    "toast_delay_ms": 2500,
                },
            }
        minutes = int(minutes_raw)
        seconds = int(seconds_raw)
        if minutes < 0 or seconds < 0 or seconds > 59:
            toast_html = render_toast("Invalid rest time.", variant="danger")
            return {
                "status": 400,
                "headers": [],
                "json_content": {
                    "toast_html": toast_html,
                    "toast_delay_ms": 2500,
                },
            }
        total_seconds = minutes * 60 + seconds
        if total_seconds < REST_TIME_MIN_SECONDS or total_seconds > REST_TIME_MAX_SECONDS:
            toast_html = render_toast("Rest time must be between 0:10 and 10:00.", variant="danger")
            return {
                "status": 400,
                "headers": [],
                "json_content": {
                    "toast_html": toast_html,
                    "toast_delay_ms": 2500,
                },
            }
        update_user_setting(user, setting_key, total_seconds)
        toast_html = render_toast("Saved", variant="success")
        return {
            "status": 200,
            "headers": [],
            "json_content": {
                "toast_html": toast_html,
                "toast_delay_ms": 1500,
            },
        }

    toast_html = render_toast("Unknown setting.", variant="danger")
    return {
        "status": 400,
        "headers": [],
        "json_content": {
            "toast_html": toast_html,
            "toast_delay_ms": 2500,
        },
    }
