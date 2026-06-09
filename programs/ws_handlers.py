from programs.services import activate_program, deactivate_program, delete_program, update_program


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
    )
    return {
        "status": 302,
        "headers": [["Location", "/programs/"]],
        "json_content": {},
    }
