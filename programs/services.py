from django.db import transaction
from django.db.models import Case, Count, IntegerField, Max, Prefetch, Q, When
from django.utils import timezone

from gainz2.utils import next_numbered_name, quantize_weight
from programs.models import Program, ProgramExercise, ProgramRoutine, ProgressionStep, ProgressionTemplate
from routines.models import Routine, RoutineExercise
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
    no_progression = ProgressionTemplate.objects.get(
        is_system=True,
        name="System: No progression",
    )
    return Program.objects.create(
        user=user,
        name=next_numbered_name("Program", names),
        description="",
        primary_progression_template=no_progression,
        secondary_progression_template=no_progression,
        accessory_progression_template=no_progression,
    )


def get_program(user, program_id):
    return (
        Program.objects.filter(user=user)
        .select_related(
            "primary_progression_template",
            "secondary_progression_template",
            "accessory_progression_template",
        )
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
    no_progression = ProgressionTemplate.objects.get(
        is_system=True,
        name="System: No progression",
    )
    with transaction.atomic():
        program = Program.objects.create(
            user=user,
            name=program_name,
            description=f"Imported from text on {timezone.now().strftime('%Y-%m-%d %H:%M')}",
            primary_progression_template=no_progression,
            secondary_progression_template=no_progression,
            accessory_progression_template=no_progression,
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


def parse_progression_template_id(value):
    if value is None or value == "":
        return None
    return int(value)


def get_program_type_progression_template(program, exercise_type):
    if exercise_type == "primary":
        return program.primary_progression_template
    if exercise_type == "secondary":
        return program.secondary_progression_template
    return program.accessory_progression_template


def list_programs_for_routine(user, routine):
    return (
        Program.objects.filter(user=user, program_routines__routine=routine)
        .distinct()
        .order_by("name")
    )


def get_program_in_routine_context(user, routine, program_id):
    if not program_id:
        return None
    return (
        Program.objects.filter(
            user=user,
            pk=program_id,
            program_routines__routine=routine,
        )
        .select_related(
            "primary_progression_template",
            "secondary_progression_template",
            "accessory_progression_template",
        )
        .first()
    )


def set_program_exercise_progression(user, program_id, routine_exercise_id, template_id):
    program = Program.objects.get(pk=program_id, user=user)
    routine_exercise = RoutineExercise.objects.select_related("routine").get(
        pk=routine_exercise_id,
        routine__user=user,
    )
    ProgramRoutine.objects.get(program=program, routine=routine_exercise.routine)
    template = get_progression_template(
        user, parse_progression_template_id(template_id), mutable=False
    )
    program_default = get_program_type_progression_template(
        program, routine_exercise.effective_exercise_type()
    )
    if program_default and template.pk == program_default.pk:
        progression_template = None
    else:
        progression_template = template
    ProgramExercise.objects.update_or_create(
        program=program,
        routine_exercise=routine_exercise,
        defaults={"progression_template": progression_template},
    )


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
    primary_progression_template_id=None,
    secondary_progression_template_id=None,
    accessory_progression_template_id=None,
):
    program = Program.objects.get(pk=program_id, user=user)
    program.name = name
    program.description = description
    program.is_active = is_active
    program.primary_carryover = primary_carryover
    program.secondary_carryover = secondary_carryover
    program.accessory_carryover = accessory_carryover
    program.primary_progression_template_id = primary_progression_template_id
    program.secondary_progression_template_id = secondary_progression_template_id
    program.accessory_progression_template_id = accessory_progression_template_id
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


def list_progression_templates(user):
    return (
        ProgressionTemplate.objects.filter(Q(is_system=True) | Q(user=user))
        .annotate(step_count=Count("steps", distinct=True))
        .order_by(
            Case(When(is_system=True, then=0), default=1, output_field=IntegerField()),
            "pk",
        )
    )


def get_progression_template(user, pk, mutable=False):
    qs = ProgressionTemplate.objects.filter(pk=pk).prefetch_related("steps")
    if mutable:
        return qs.get(user=user, is_system=False)
    return qs.filter(Q(is_system=True) | Q(user=user)).get()


def new_progression_template(user):
    names = ProgressionTemplate.objects.filter(user=user, is_system=False).values_list(
        "name", flat=True
    )
    return ProgressionTemplate.objects.create(
        user=user,
        is_system=False,
        name=next_numbered_name("Progression", names),
        notes="",
    )


def update_progression_template(user, pk, name, notes):
    template = get_progression_template(user, pk, mutable=True)
    template.name = name
    template.notes = notes
    template.save(update_fields=["name", "notes", "updated_at"])
    return template


def delete_progression_template(user, pk):
    template = get_progression_template(user, pk, mutable=True)
    template.delete()


def duplicate_progression_template(user, source_pk):
    source = get_progression_template(user, source_pk, mutable=False)
    copy = ProgressionTemplate.objects.create(
        user=user,
        is_system=False,
        name=f"{source.name} (copy)",
        notes=source.notes,
    )
    for step in source.steps.all():
        ProgressionStep.objects.create(
            template=copy,
            order=step.order,
            weight_delta=step.weight_delta,
            reps_delta=step.reps_delta,
        )
    return copy


def create_progression_step(user, template_id, weight_delta, reps_delta):
    template = get_progression_template(user, template_id, mutable=True)
    max_order = (
        ProgressionStep.objects.filter(template=template).aggregate(Max("order"))[
            "order__max"
        ]
        or 0
    )
    step = ProgressionStep.objects.create(
        template=template,
        order=max_order + 1,
        weight_delta=quantize_weight(weight_delta),
        reps_delta=reps_delta,
    )
    template.updated_at = timezone.now()
    template.save(update_fields=["updated_at"])
    return step, template


def update_progression_step(user, step_id, weight_delta, reps_delta):
    step = ProgressionStep.objects.select_related("template").get(pk=step_id)
    template = get_progression_template(user, step.template_id, mutable=True)
    step.weight_delta = quantize_weight(weight_delta)
    step.reps_delta = reps_delta
    step.save(update_fields=["weight_delta", "reps_delta"])
    template.updated_at = timezone.now()
    template.save(update_fields=["updated_at"])
    return step, template


def delete_progression_step(user, step_id):
    step = ProgressionStep.objects.select_related("template").get(pk=step_id)
    template = get_progression_template(user, step.template_id, mutable=True)
    step.delete()
    remaining = list(
        ProgressionStep.objects.filter(template=template).order_by("order")
    )
    for index, remaining_step in enumerate(remaining, start=1):
        if remaining_step.order != index:
            remaining_step.order = index
            remaining_step.save(update_fields=["order"])
    template.updated_at = timezone.now()
    template.save(update_fields=["updated_at"])
    return template
