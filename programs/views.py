from types import SimpleNamespace

from django.shortcuts import get_object_or_404, redirect, render
from programs.models import ProgramExercise, ProgramRoutine
from programs.services import (
    get_program,
    get_program_type_progression_template,
    get_progression_template,
    import_program_from_parsed,
    list_addable_routines_for_program,
    list_programs,
    list_progression_templates,
    new_program,
    new_progression_template,
    prepare_program_import,
    routines_catalog,
)
from routines.models import Routine
from routines.services import get_routine, resolve_import_exercises

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
        "progression_templates": list_progression_templates(req_event.user),
        "template_routine": SimpleNamespace(pk=0, name="", exercise_count=0),
    }
    return render(req_event, "programs/program_detail.html", response)


def program_routine_page(req_event, program_id, routine_id):
    program = get_program(req_event.user, program_id)
    get_object_or_404(Routine, pk=routine_id, user=req_event.user)
    routine = get_routine(routine_id)
    program_routine = get_object_or_404(
        ProgramRoutine,
        program=program,
        routine=routine,
    )
    program_exercises = {
        program_exercise.routine_exercise_id: program_exercise
        for program_exercise in ProgramExercise.objects.filter(
            program=program,
            routine_exercise__routine=routine,
        ).select_related("progression_template")
    }
    for routine_exercise in routine.exercises.all():
        program_exercise = program_exercises.get(routine_exercise.pk)
        if program_exercise and program_exercise.progression_template_id:
            routine_exercise.effective_template_id = (
                program_exercise.progression_template_id
            )
        else:
            type_template = get_program_type_progression_template(
                program,
                routine_exercise.effective_exercise_type(),
            )
            routine_exercise.effective_template_id = (
                type_template.pk if type_template else None
            )
    response = {
        "title": f"{program.name} – {routine.name}",
        "program": program,
        "routine": routine,
        "program_routine": program_routine,
        "progression_templates": list_progression_templates(req_event.user),
    }
    return render(req_event, "programs/program_routine_detail.html", response)


def progression_templates_list_page(req_event):
    response = {
        "title": "Progression templates",
        "templates": list_progression_templates(req_event.user),
    }
    return render(req_event, "programs/progression/progression_list.html", response)


def new_progression_template_page(req_event):
    template = new_progression_template(req_event.user)
    return redirect("progression-template-detail", template_id=template.pk)


def progression_template_detail_page(req_event, template_id):
    template = get_progression_template(req_event.user, template_id, mutable=False)
    response = {
        "title": template.name,
        "template": template,
    }
    return render(req_event, "programs/progression/progression_detail.html", response)
