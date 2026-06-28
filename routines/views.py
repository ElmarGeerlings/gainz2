from django.shortcuts import get_object_or_404, redirect, render

from exercises.models import Exercise
from programs.services import list_programs_for_filter, list_programs_for_routine
from routines.models import Routine, RoutineExercise
from routines.services import (
    get_routine,
    import_routine_from_parsed,
    list_routines,
    new_routine,
    prepare_routine_import,
    resolve_import_exercises,
)
from workouts.services import list_add_exercise_options

SAMPLE_IMPORT_FORMAT = """OHP 3x5 70
Pull ups 3x10
Triceps 4x10 40"""


def render_import_routine_page(req_event, context):
    base = {
        "title": "Import Routine",
        "sample_format": SAMPLE_IMPORT_FORMAT,
        "routine_name": "",
        "workout_text": "",
        "errors": [],
        "show_confirm_modal": False,
        "unmatched_names": [],
    }
    base.update(context)
    return render(req_event, "routines/import_routine.html", base)


def routines_list_page(req_event):
    response = {
        "title": "My Routines",
        "programs": list_programs_for_filter(req_event.user),
        "routines": list_routines(req_event.user),
    }
    return render(req_event, "routines/routines_list.html", response)


def new_routine_page(req_event):
    routine = new_routine(req_event.user)
    return redirect("routine-detail", routine_id=routine.pk)


def routine_detail_page(req_event, routine_id):
    get_object_or_404(Routine, pk=routine_id, user=req_event.user)
    routine = get_routine(routine_id)
    programs_for_routine = list(list_programs_for_routine(req_event.user, routine))
    response = {
        "title": routine.name,
        "routine": routine,
        "programs_for_routine": programs_for_routine,
        "add_exercise_options": list_add_exercise_options(),
        "bodypart_choices": Exercise.BODYPART_CHOICES,
        "exercise_type_choices": [
            {"value": value, "label": label}
            for value, label in RoutineExercise.EXERCISE_TYPE_CHOICES
        ],
    }
    return render(req_event, "routines/routine_detail.html", response)


def import_routine_page(req_event):
    if req_event.method == "GET":
        return render_import_routine_page(req_event, {})

    step = req_event.POST.get("step", "parse")
    routine_name = req_event.POST.get("routine_name", "").strip()
    workout_text = req_event.POST.get("workout_text", "").strip()

    errors = []
    if not routine_name:
        errors.append("Routine name is required.")
    if not workout_text:
        errors.append("Workout text is required.")
    if errors:
        return render_import_routine_page(
            req_event,
            {
                "routine_name": routine_name,
                "workout_text": workout_text,
                "errors": errors,
            },
        )

    prepared = prepare_routine_import(req_event.user, workout_text)
    if prepared.get("error"):
        return render_import_routine_page(
            req_event,
            {
                "routine_name": routine_name,
                "workout_text": workout_text,
                "errors": [prepared["error"]],
            },
        )

    parsed_lines = prepared["parsed_lines"]
    unmatched_names = prepared["unmatched_names"]

    if step == "confirm":
        name_to_exercise = resolve_import_exercises(
            req_event.user,
            unmatched_names,
            parsed_lines,
        )
        routine = import_routine_from_parsed(
            req_event.user,
            routine_name,
            parsed_lines,
            name_to_exercise,
        )
        return redirect("routine-detail", routine_id=routine.pk)

    if not unmatched_names:
        name_to_exercise = resolve_import_exercises(
            req_event.user,
            unmatched_names,
            parsed_lines,
        )
        routine = import_routine_from_parsed(
            req_event.user,
            routine_name,
            parsed_lines,
            name_to_exercise,
        )
        return redirect("routine-detail", routine_id=routine.pk)

    return render_import_routine_page(
        req_event,
        {
            "routine_name": routine_name,
            "workout_text": workout_text,
            "show_confirm_modal": True,
            "unmatched_names": unmatched_names,
        },
    )
