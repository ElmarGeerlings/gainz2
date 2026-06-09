from types import SimpleNamespace

from django.shortcuts import redirect, render
from programs.services import (
    get_program,
    import_program_from_parsed,
    list_addable_routines_for_program,
    list_programs,
    new_program,
    prepare_program_import,
    routines_catalog,
)
from routines.services import resolve_import_exercises

SAMPLE_PROGRAM_IMPORT_FORMAT = """Bench 3x3 90
Squat 2x4 100

OHP 3x3 60"""


def programs_list_page(req_event):
    response = {
        "title": "My Programs",
        "programs": list_programs(req_event.user),
    }
    return render(req_event, "programs/programs_list.html", response)


def new_program_page(req_event):
    program = new_program(req_event.user)
    return redirect("program-detail", program_id=program.pk)


def render_import_program_page(req_event, context):
    base = {
        "title": "Import Program",
        "sample_format": SAMPLE_PROGRAM_IMPORT_FORMAT,
        "program_name": "",
        "workout_text": "",
        "errors": [],
        "show_confirm_modal": False,
        "unmatched_names": [],
    }
    base.update(context)
    return render(req_event, "programs/import_program.html", base)


def import_program_page(req_event):
    if req_event.method == "GET":
        return render_import_program_page(req_event, {})

    step = req_event.POST.get("step", "parse")
    program_name = req_event.POST.get("program_name", "").strip()
    workout_text = req_event.POST.get("workout_text", "").strip()

    errors = []
    if not program_name:
        errors.append("Program name is required.")
    if not workout_text:
        errors.append("Workout text is required.")
    if errors:
        return render_import_program_page(
            req_event,
            {
                "program_name": program_name,
                "workout_text": workout_text,
                "errors": errors,
            },
        )

    prepared = prepare_program_import(req_event.user, workout_text)
    if prepared.get("error"):
        return render_import_program_page(
            req_event,
            {
                "program_name": program_name,
                "workout_text": workout_text,
                "errors": [prepared["error"]],
            },
        )

    routine_groups = prepared["routine_groups"]
    unmatched_names = prepared["unmatched_names"]
    all_parsed = [line for group in routine_groups for line in group]

    if step == "confirm":
        name_to_exercise = resolve_import_exercises(
            req_event.user,
            unmatched_names,
            all_parsed,
        )
        program = import_program_from_parsed(
            req_event.user,
            program_name,
            routine_groups,
            name_to_exercise,
        )
        return redirect("program-detail", program_id=program.pk)

    if not unmatched_names:
        name_to_exercise = resolve_import_exercises(
            req_event.user,
            unmatched_names,
            all_parsed,
        )
        program = import_program_from_parsed(
            req_event.user,
            program_name,
            routine_groups,
            name_to_exercise,
        )
        return redirect("program-detail", program_id=program.pk)

    return render_import_program_page(
        req_event,
        {
            "program_name": program_name,
            "workout_text": workout_text,
            "show_confirm_modal": True,
            "unmatched_names": unmatched_names,
        },
    )


def program_detail_page(req_event, program_id):
    program = get_program(req_event.user, program_id)
    response = {
        "title": program.name,
        "program": program,
        "available_routines": list_addable_routines_for_program(req_event.user, program),
        "routines_catalog": routines_catalog(req_event.user),
        "template_routine": SimpleNamespace(pk=0, name="", exercise_count=0),
    }
    return render(req_event, "programs/program_detail.html", response)
