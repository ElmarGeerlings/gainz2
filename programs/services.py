from django.db import transaction
from django.db.models import Count, Prefetch
from django.utils import timezone

from gainz2.utils import next_numbered_name
from programs.models import Program, ProgramRoutine
from routines.models import Routine
from routines.services import (
    import_routine_from_parsed,
    list_routines,
    match_parsed_lines,
    parse_workout_days,
)


def program_routine_prefetch():
    routine_qs = Routine.objects.annotate(
        exercise_count=Count("exercises", distinct=True),
    )
    return Prefetch(
        "program_routines",
        queryset=(
            ProgramRoutine.objects.prefetch_related(
                Prefetch("routine", queryset=routine_qs)
            )
            .order_by("order", "assigned_day")
        ),
    )


def list_programs(user):
    return (
        Program.objects.filter(user=user)
        .prefetch_related(program_routine_prefetch())
        .order_by("-is_active", "name")
    )


def list_programs_for_filter(user):
    return Program.objects.filter(user=user).order_by("-is_active", "name")


def new_program(user):
    names = Program.objects.filter(user=user).values_list("name", flat=True)
    return Program.objects.create(
        user=user,
        name=next_numbered_name("Program", names),
        description="",
    )


def get_program(user, program_id):
    return (
        Program.objects.filter(user=user)
        .prefetch_related(program_routine_prefetch())
        .get(pk=program_id)
    )


def activate_program(user, program_id):
    program = Program.objects.get(pk=program_id, user=user)
    program.is_active = True
    program.last_used_routine = None
    program.save(update_fields=["is_active", "last_used_routine"])
    return program


def deactivate_program(user, program_id):
    program = Program.objects.get(pk=program_id, user=user)
    program.is_active = False
    program.save()
    return program


def delete_program(user, program_id):
    program = Program.objects.get(pk=program_id, user=user)
    program.delete()


def list_addable_routines_for_program(user, program):
    in_program = program.program_routines.values_list("routine_id", flat=True)
    return list_routines(user).exclude(pk__in=in_program)


def routines_catalog(user):
    return [
        {
            "id": routine.pk,
            "name": routine.name,
            "exercise_count": routine.exercise_count,
        }
        for routine in list_routines(user)
    ]


def routine_name_for_program_import(program_name, index):
    day_names = ["A", "B", "C", "D", "E", "F", "G"]
    if index < len(day_names):
        return f"{program_name} - {day_names[index]}"
    return f"{program_name} - Day {index + 1}"


def prepare_program_import(user, text):
    routine_groups = parse_workout_days(text)
    all_parsed = [line for group in routine_groups for line in group]
    matched = match_parsed_lines(user, all_parsed)
    if matched.get("error"):
        return matched
    return {
        "routine_groups": routine_groups,
        "unmatched_names": matched["unmatched_names"],
    }


def import_program_from_parsed(user, program_name, routine_groups, name_to_exercise):
    with transaction.atomic():
        program = Program.objects.create(
            user=user,
            name=program_name,
            description=f"Imported from text on {timezone.now().strftime('%Y-%m-%d %H:%M')}",
        )
        for order, parsed_lines in enumerate(routine_groups, start=1):
            routine_name = routine_name_for_program_import(program_name, order - 1)
            routine = import_routine_from_parsed(
                user,
                routine_name,
                parsed_lines,
                name_to_exercise,
            )
            ProgramRoutine.objects.create(
                program=program,
                routine=routine,
                order=order,
            )
    return program


def update_program(
    user,
    program_id,
    name,
    description,
    is_active,
    ordered_routine_ids,
    primary_carryover=False,
    secondary_carryover=False,
    accessory_carryover=True,
):
    program = Program.objects.get(pk=program_id, user=user)
    program.name = name
    program.description = description
    program.is_active = is_active
    program.primary_carryover = primary_carryover
    program.secondary_carryover = secondary_carryover
    program.accessory_carryover = accessory_carryover
    program.save()

    routines = {
        r.pk: r
        for r in Routine.objects.filter(user=user, pk__in=ordered_routine_ids)
    }
    program.program_routines.all().delete()
    for index, routine_id in enumerate(ordered_routine_ids):
        routine = routines[int(routine_id)]
        ProgramRoutine.objects.create(
            program=program,
            routine=routine,
            order=index + 1,
        )
    return program
