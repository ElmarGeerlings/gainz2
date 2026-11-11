import json
from django.template.defaultfilters import date
from django.template.loader import render_to_string

from gainz2.utils import render_toast
from gyms.services import (
    DAY_SCHEDULE,
    build_price_plans,
    gym_amenity_rows,
    gym_hours_context,
    gym_rule_rows,
    replace_gym_prices,
    update_gym_amenities,
    update_gym_description,
    update_gym_hours,
    update_gym_rules,
    update_gym_vibe,
)


def gym_footer(updated_at):
    return f"Last updated {date(updated_at, 'j M Y')}"

def handle_update_gym_description(user, attributes):
    gym_id = int(attributes["data-gym-id"])
    description = attributes["description"]
    gym = update_gym_description(gym_id, description)
    morphs = [
        {
            "target": "#gym-description-block",
            "html": render_to_string(
                "gyms/gym_description_block.html",
                {"gym": gym},
            ),
        },
        {
            "target": "#gym-edit-description-body",
            "html": render_to_string(
                "gyms/gym_edit_description_modal.html",
                {"gym": gym},
            ),
        },
        {
            "target": "#gym-footer-info",
            "html": gym_footer(gym.info_updated_at),
        },
    ]
    return {
        "status": 200,
        "headers": [],
        "json_content": {"morphs": morphs},
    }


def handle_update_gym_vibe(user, attributes):
    gym_id = int(attributes["data-gym-id"])
    vibe = attributes["vibe"]
    gym = update_gym_vibe(gym_id, vibe)
    morphs = [
        {
            "target": "#gym-vibe-display",
            "html": gym.get_vibe_display(),
        },
        {
            "target": "#gym-edit-vibe-body",
            "html": render_to_string(
                "gyms/gym_edit_vibe_modal.html",
                {"gym": gym},
            ),
        },
        {
            "target": "#gym-footer-info",
            "html": gym_footer(gym.info_updated_at),
        },
    ]
    return {
        "status": 200,
        "headers": [],
        "json_content": {"morphs": morphs},
    }


def handle_update_gym_rules(user, attributes):
    gym_id = int(attributes["data-gym-id"])
    states = {}
    for key, value in attributes.items():
        if key.startswith("rule_"):
            states[key[5:]] = value
    gym = update_gym_rules(gym_id, states)
    rules = gym_rule_rows(gym)
    morphs = [
        {
            "target": "#gym-rules-display",
            "html": render_to_string(
                "gyms/gym_rules_display.html",
                {"rules": rules},
            ),
        },
        {
            "target": "#gym-edit-rules-body",
            "html": render_to_string(
                "gyms/gym_edit_rules_modal.html",
                {"gym": gym, "rules": rules},
            ),
        },
        {
            "target": "#gym-footer-info",
            "html": gym_footer(gym.info_updated_at),
        },
    ]
    return {
        "status": 200,
        "headers": [],
        "json_content": {"morphs": morphs},
    }


def handle_update_gym_hours(user, attributes):
    gym_id = int(attributes["data-gym-id"])
    schedule = {}
    for day_label, prefix in DAY_SCHEDULE:
        schedule[prefix] = {
            "closed": attributes.get(f"{prefix}_closed") == "on",
            "open": attributes.get(f"{prefix}_open", ""),
            "close": attributes.get(f"{prefix}_close", ""),
        }
    result = update_gym_hours(gym_id, schedule)
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
    gym = result["gym"]
    ctx = gym_hours_context(gym)
    morphs = [
        {
            "target": "#gym-hours-panel-body",
            "html": render_to_string(
                "gyms/gym_hours_panel_body.html",
                {
                    "hours": ctx["hours"],
                    "has_hours": ctx["has_hours"],
                },
            ),
        },
        {
            "target": "#gym-edit-hours-body",
            "html": render_to_string(
                "gyms/gym_edit_hours_modal.html",
                {
                    "gym": gym,
                    "hours": ctx["hours"],
                    "hour_open_options": ctx["hour_open_options"],
                    "hour_close_options": ctx["hour_close_options"],
                },
            ),
        },
        {
            "target": "#gym-overview-hours",
            "html": render_to_string(
                "gyms/gym_overview_hours.html",
                {
                    "has_hours": ctx["has_hours"],
                    "is_open_now": ctx["is_open_now"],
                    "today_hours": ctx["today_hours"],
                },
            ),
        },
        {
            "target": "#gym-footer-info",
            "html": gym_footer(gym.info_updated_at),
        },
    ]
    return {
        "status": 200,
        "headers": [],
        "json_content": {"morphs": morphs},
    }


def handle_update_gym_amenities(user, attributes):
    gym_id = int(attributes["data-gym-id"])
    selected_slugs = []
    for key, value in attributes.items():
        if key.startswith("amenity_") and value == "on":
            selected_slugs.append(key[8:])
    gym = update_gym_amenities(gym_id, selected_slugs)
    amenities = gym_amenity_rows(gym)
    amenities_present = [row["label"] for row in amenities if row["selected"]]
    morphs = [
        {
            "target": "#gym-amenities-display",
            "html": render_to_string(
                "gyms/gym_amenities_display.html",
                {"amenities_present": amenities_present},
            ),
        },
        {
            "target": "#gym-edit-amenities-body",
            "html": render_to_string(
                "gyms/gym_edit_amenities_modal.html",
                {"gym": gym, "amenities": amenities},
            ),
        },
        {
            "target": "#gym-footer-info",
            "html": gym_footer(gym.info_updated_at),
        },
    ]
    return {
        "status": 200,
        "headers": [],
        "json_content": {"morphs": morphs},
    }


def handle_update_gym_prices(user, attributes):
    gym_id = int(attributes["data-gym-id"])
    rows = json.loads(attributes["prices"])
    gym = replace_gym_prices(gym_id, rows)
    price_plans = build_price_plans(gym)
    morphs = [
        {
            "target": "#gym-prices-table-body",
            "html": render_to_string(
                "gyms/gym_prices_table_body.html",
                {"price_plans": price_plans},
            ),
        },
        {
            "target": "#gym-price-headlines",
            "html": render_to_string(
                "gyms/gym_price_headlines.html",
                {"gym": gym, "price_plans": price_plans},
            ),
        },
        {
            "target": "#gym-footer-info",
            "html": gym_footer(gym.info_updated_at),
        },
    ]
    return {
        "status": 200,
        "headers": [],
        "json_content": {"morphs": morphs},
    }
