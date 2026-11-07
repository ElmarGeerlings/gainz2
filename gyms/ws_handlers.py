from django.template.defaultfilters import date
from django.template.loader import render_to_string
from gyms.services import update_gym_description


def gym_footer(updated_at):
    return f"Last updated {date(updated_at, 'j M Y')}"

def handle_update_gym_description(user, attributes):
    gym_id = int(attributes["gym_id"])
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
