from decimal import Decimal

from django.template.loader import render_to_string

from gainz2.utils import render_toast
from programs.services import (
    activate_program,
    create_progression_step,
    deactivate_program,
    delete_program,
    delete_progression_step,
    delete_progression_template,
    duplicate_progression_template,
    get_progression_template,
    parse_progression_template_id,
    set_program_exercise_progression,
    update_program,
    update_progression_step,
    update_progression_template,
)
from utils.templatetags.formatting import weight_display


def handle_activate_program(user, attributes):
    program_id = int(attributes["data-program-id"])
    activate_program(user, program_id)
    return {
        "status": 302,
        "headers": [["Location", "/programs/"]],
        "json_content": {},
    }


def handle_deactivate_program(user, attributes):
    program_id = int(attributes["data-program-id"])
    deactivate_program(user, program_id)
    return {
        "status": 302,
        "headers": [["Location", "/programs/"]],
        "json_content": {},
    }


def handle_delete_program(user, attributes):
    program_id = int(attributes["data-program-id"])
    delete_program(user, program_id)
    return {
        "status": 302,
        "headers": [["Location", "/programs/"]],
        "json_content": {},
    }


def handle_update_program(user, attributes):
    program_id = int(attributes["data-program-id"])
    name = attributes["name"]
    description = attributes.get("description", "")
    is_active = attributes.get("is_active") == "on"
    ordered_ids = [
        routine_id
        for routine_id in attributes.get("data-routine-ids", "").split(",")
        if routine_id
    ]
    primary_carryover = attributes.get("primary_carryover") == "on"
    secondary_carryover = attributes.get("secondary_carryover") == "on"
    accessory_carryover = attributes.get("accessory_carryover") == "on"
    update_program(
        user,
        program_id,
        name,
        description,
        is_active,
        ordered_ids,
        primary_carryover=primary_carryover,
        secondary_carryover=secondary_carryover,
        accessory_carryover=accessory_carryover,
        primary_progression_template_id=parse_progression_template_id(
            attributes.get("primary_progression_template")
        ),
        secondary_progression_template_id=parse_progression_template_id(
            attributes.get("secondary_progression_template")
        ),
        accessory_progression_template_id=parse_progression_template_id(
            attributes.get("accessory_progression_template")
        ),
    )
    return {
        "status": 302,
        "headers": [["Location", "/programs/"]],
        "json_content": {},
    }


def handle_delete_progression_template(user, attributes):
    template_id = int(attributes["data-template-id"])
    delete_progression_template(user, template_id)
    return {
        "status": 302,
        "headers": [["Location", "/programs/progression/"]],
        "json_content": {},
    }


def handle_update_progression_template(user, attributes):
    template_id = int(attributes["template_id"])
    name = attributes["name"]
    notes = attributes.get("notes", "")
    template = update_progression_template(user, template_id, name, notes)
    html = render_to_string(
        "programs/progression/progression_header.html",
        {"template": template},
    )
    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "target": "#progression-header",
            "html": html,
        },
    }


def handle_duplicate_progression_template(user, attributes):
    source_id = int(attributes["data-template-id"])
    copy = duplicate_progression_template(user, source_id)
    return {
        "status": 302,
        "headers": [["Location", f"/programs/progression/{copy.pk}/"]],
        "json_content": {},
    }


def handle_progression_step_modal_form(user, attributes):
    template_id = int(attributes["data-template-id"])
    template = get_progression_template(user, template_id, mutable=False)
    if template.is_system:
        return {
            "status": 404,
            "headers": [],
            "json_content": {"error": "Built-in templates are read-only."},
        }
    step_id = attributes.get("data-step-id")
    step = None
    weight = attributes.get("data-weight-delta", "0")
    reps = attributes.get("data-reps-delta", "0")
    is_add = True
    if step_id:
        is_add = False
        step = template.steps.get(pk=int(step_id))
        weight = str(step.weight_delta)
        reps = str(step.reps_delta)
    html = render_to_string(
        "programs/progression/progression_step_modal.html",
        {
            "is_add": is_add,
            "template": template,
            "step": step,
            "weight_delta": weight,
            "reps_delta": reps,
        },
    )
    return {
        "status": 200,
        "headers": [],
        "json_content": {"html": html},
    }


def render_progression_steps(template):
    return render_to_string(
        "programs/progression/progression_steps_inner.html",
        {"template": template},
    )


def handle_create_progression_step(user, attributes):
    template_id = int(attributes["progression_template_id"])
    weight = Decimal(attributes["weight_delta"])
    reps = int(float(attributes["reps_delta"]))
    step, template = create_progression_step(user, template_id, weight, reps)
    template = get_progression_template(user, template.pk, mutable=True)
    weight_str = weight_display(step.weight_delta)
    if step.weight_delta >= 0:
        weight_str = f"+{weight_str}"
    reps_str = f"+{step.reps_delta}" if step.reps_delta > 0 else str(step.reps_delta)
    message = f"Step added: {weight_str} kg · {reps_str} reps"
    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "target": "#progression-steps-list",
            "html": render_progression_steps(template),
            "toast_html": render_toast(message, variant="success"),
            "toast_delay_ms": 2500,
        },
    }


def handle_update_progression_step(user, attributes):
    step_id = int(attributes["step_id"])
    weight = Decimal(attributes["weight_delta"])
    reps = int(float(attributes["reps_delta"]))
    step, template = update_progression_step(user, step_id, weight, reps)
    template = get_progression_template(user, template.pk, mutable=True)
    weight_str = weight_display(step.weight_delta)
    if step.weight_delta > 0:
        weight_str = f"+{weight_str}"
    reps_str = f"+{step.reps_delta}" if step.reps_delta >= 0 else str(step.reps_delta)
    message = f"Step updated: {weight_str} kg · {reps_str} reps"
    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "target": "#progression-steps-list",
            "html": render_progression_steps(template),
            "toast_html": render_toast(message, variant="success"),
            "toast_delay_ms": 2500,
        },
    }


def handle_delete_progression_step(user, attributes):
    step_id = int(attributes["data-step-id"])
    template = delete_progression_step(user, step_id)
    template = get_progression_template(user, template.pk, mutable=True)
    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "target": "#progression-steps-list",
            "html": render_progression_steps(template),
        },
    }


def handle_set_program_exercise_progression(user, attributes):
    program_id = int(attributes["data-program-id"])
    routine_exercise_id = int(attributes["data-routine-exercise-id"])
    template_id = attributes.get("value", attributes.get("progression_template_id", ""))
    set_program_exercise_progression(
        user,
        program_id,
        routine_exercise_id,
        template_id,
    )
    return {
        "status": 200,
        "headers": [],
        "json_content": {},
    }
