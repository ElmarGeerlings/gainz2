import re
from decimal import Decimal

from django.db import transaction
from django.db.models import Case, Count, F, IntegerField, Max, Prefetch, Q, When
from django.utils import timezone

from exercises.models import Exercise
from routines.models import Routine, RoutineExercise, RoutineSet
from workouts.services import quantize_weight


def list_routines(user):
    return (
        Routine.objects.filter(user=user)
        .annotate(
            exercise_count=Count("exercises", distinct=True),
            set_count=Count("exercises__sets", distinct=True),
        )
        .order_by("-updated_at")
    )


def list_routines_for_program(user, program_id):
    if not program_id:
        return list_routines(user)
    from programs.models import Program, ProgramRoutine

    program = Program.objects.get(pk=program_id, user=user)
    routine_ids = list(
        ProgramRoutine.objects.filter(program=program)
        .order_by("order", "assigned_day")
        .values_list("routine_id", flat=True)
    )
    if not routine_ids:
        return Routine.objects.none()
    preserved = Case(
        *[When(pk=pk, then=pos) for pos, pk in enumerate(routine_ids)],
        output_field=IntegerField(),
    )
    return (
        Routine.objects.filter(user=user, pk__in=routine_ids)
        .annotate(
            exercise_count=Count("exercises", distinct=True),
            set_count=Count("exercises__sets", distinct=True),
        )
        .order_by(preserved)
    )


def new_routine(user):
    count = Routine.objects.filter(user=user).count()
    return Routine.objects.create(
        user=user,
        name=f"Routine #{count + 1}",
        notes="",
    )


def delete_routine(user, routine_id):
    routine = Routine.objects.get(pk=routine_id, user=user)
    routine.delete()


def get_routine(routine_id):
    return Routine.objects.prefetch_related(
        Prefetch(
            "exercises",
            queryset=RoutineExercise.objects.all(),
        ),
        "exercises__exercise",
        Prefetch(
            "exercises__sets",
            queryset=RoutineSet.objects.order_by("set_number").all(),
        ),
    ).get(pk=routine_id)


def update_routine(user, routine_id, name=None, notes=None):
    routine = Routine.objects.get(pk=routine_id, user=user)
    if name:
        routine.name = name
    if notes is not None:
        routine.notes = notes
    routine.save()
    return routine


def get_routine_exercise(routine_exercise_id):
    return RoutineExercise.objects.prefetch_related(
        Prefetch(
            "sets",
            queryset=RoutineSet.objects.order_by("set_number"),
        )
    ).get(pk=routine_exercise_id)


def get_routine_exercise_last_set(routine_exercise):
    return (
        RoutineSet.objects.filter(routine_exercise=routine_exercise)
        .order_by("-set_number")
        .first()
    )


TYPE_PRIORITY = {
    "primary": 3,
    "secondary": 2,
    "accessory": 1,
}


def index_at_start_of_type_section(existing_list, new_type):
    new_priority = TYPE_PRIORITY[new_type]
    return sum(
        1
        for re in existing_list
        if TYPE_PRIORITY[re.effective_exercise_type()] > new_priority
    )


def index_after_last_of_type(existing_list, new_type):
    same_type_indices = [
        index
        for index, re in enumerate(existing_list)
        if re.effective_exercise_type() == new_type
    ]
    if same_type_indices:
        return max(same_type_indices) + 1
    return index_at_start_of_type_section(existing_list, new_type)


def compute_add_exercise_insert_index(
    existing_list, new_type, current_routine_exercise_id=None
):
    if not existing_list:
        return 0

    if not current_routine_exercise_id:
        return index_after_last_of_type(existing_list, new_type)

    current_index = None
    current_re = None
    for index, re in enumerate(existing_list):
        if re.pk == current_routine_exercise_id:
            current_index = index
            current_re = re
            break

    if current_re is None:
        return index_after_last_of_type(existing_list, new_type)

    current_type = current_re.effective_exercise_type()
    new_priority = TYPE_PRIORITY[new_type]
    current_priority = TYPE_PRIORITY[current_type]

    if new_priority == current_priority:
        return current_index + 1
    if new_priority > current_priority:
        return index_after_last_of_type(existing_list, new_type)

    same_type_indices = [
        index
        for index, re in enumerate(existing_list)
        if re.effective_exercise_type() == new_type
    ]
    if same_type_indices:
        return min(same_type_indices)
    return index_at_start_of_type_section(existing_list, new_type)


def add_exercise_to_routine(
    routine_id,
    exercise_id,
    current_routine_exercise_id=None,
    exercise_type=None,
):
    exercise = Exercise.objects.get(pk=exercise_id)
    new_type = exercise_type if exercise_type else exercise.exercise_type

    existing_list = list(
        RoutineExercise.objects.filter(routine_id=routine_id).select_related(
            "exercise"
        )
    )
    insert_index = compute_add_exercise_insert_index(
        existing_list,
        new_type,
        current_routine_exercise_id,
    )
    new_order = insert_index

    RoutineExercise.objects.filter(
        routine_id=routine_id,
        order__gte=new_order,
    ).update(order=F("order") + 1)

    RoutineExercise.objects.create(
        routine_id=routine_id,
        exercise_id=exercise_id,
        exercise_type=new_type,
        order=new_order,
    )

    new_exercise_index = insert_index
    routine = get_routine(routine_id)
    return routine, new_exercise_index


def reorder_sets_for_routine_exercise(routine_exercise):
    sets = list(
        RoutineSet.objects.filter(routine_exercise=routine_exercise).order_by(
            "set_number"
        )
    )
    warmups = [s for s in sets if s.is_warmup]
    working = [s for s in sets if not s.is_warmup]
    ordered = warmups + working
    for index, routine_set in enumerate(ordered, start=1):
        routine_set.set_number = index
        routine_set.save(update_fields=["set_number"])


def delete_routine_set(set_id):
    routine_set = RoutineSet.objects.select_related("routine_exercise").get(
        pk=set_id
    )
    routine_exercise = routine_set.routine_exercise
    routine_set.delete()
    reorder_sets_for_routine_exercise(routine_exercise)
    routine_exercise = get_routine_exercise(routine_exercise.pk)
    return routine_exercise


def delete_routine_exercise(routine_exercise_id, current_exercise_index):
    routine_exercise = RoutineExercise.objects.get(pk=routine_exercise_id)
    routine_id = routine_exercise.routine_id
    routine_exercise.delete()

    RoutineExercise.objects.filter(
        routine_id=routine_id,
        order__gt=current_exercise_index,
    ).update(order=F("order") - 1)

    remaining_count = RoutineExercise.objects.filter(routine_id=routine_id).count()
    if remaining_count == 0:
        active_exercise_index = 0
    elif current_exercise_index < remaining_count:
        active_exercise_index = current_exercise_index
    else:
        active_exercise_index = remaining_count - 1

    routine = get_routine(routine_id)
    return routine, active_exercise_index


def reorder_routine_exercises(user, routine_id, ordered_exercise_ids):
    Routine.objects.get(pk=routine_id, user=user)
    exercises = {
        exercise.pk: exercise
        for exercise in RoutineExercise.objects.filter(routine_id=routine_id)
    }
    for index, exercise_id in enumerate(ordered_exercise_ids):
        exercise_id = int(exercise_id)
        routine_exercise = exercises[exercise_id]
        routine_exercise.order = index
        routine_exercise.save(update_fields=["order"])


def apply_smartchange(
    routine_exercise,
    edited_set_id,
    weight_delta,
    reps_delta,
    is_warmup,
    smartchange_warmup,
):
    siblings = RoutineSet.objects.filter(
        routine_exercise=routine_exercise
    ).exclude(pk=edited_set_id)
    if not smartchange_warmup:
        siblings = siblings.filter(is_warmup=is_warmup)
    updated_count = 0
    for sibling in siblings:
        new_weight = sibling.weight + weight_delta
        if new_weight < 0:
            new_weight = Decimal("0")
        else:
            new_weight = quantize_weight(new_weight)
        new_reps = max(1, sibling.reps + reps_delta)
        if new_weight != sibling.weight or new_reps != sibling.reps:
            sibling.weight = new_weight
            sibling.reps = new_reps
            sibling.save(update_fields=["weight", "reps"])
            updated_count += 1
    return updated_count


def update_routine_set(set_id, weight, reps, is_warmup, *, user=None, smartchange=False):
    routine_set = RoutineSet.objects.select_related("routine_exercise").get(
        pk=set_id
    )
    routine_exercise = routine_set.routine_exercise
    old_weight = routine_set.weight
    old_reps = routine_set.reps
    old_is_warmup = routine_set.is_warmup
    routine_set.weight = quantize_weight(weight)
    routine_set.reps = reps
    routine_set.is_warmup = is_warmup
    routine_set.save()
    warmup_changed = old_is_warmup != is_warmup
    if warmup_changed:
        reorder_sets_for_routine_exercise(routine_exercise)
        routine_set.refresh_from_db()
        routine_exercise = get_routine_exercise(routine_exercise.pk)
    weight_delta = routine_set.weight - old_weight
    reps_delta = routine_set.reps - old_reps
    siblings_updated_count = 0
    if smartchange and user and (weight_delta != 0 or reps_delta != 0):
        siblings_updated_count = apply_smartchange(
            routine_exercise,
            routine_set.pk,
            weight_delta,
            reps_delta,
            routine_set.is_warmup,
            user.settings.smartchange_warmup,
        )
        if siblings_updated_count:
            routine_exercise = get_routine_exercise(routine_exercise.pk)
    return routine_set, routine_exercise, warmup_changed, siblings_updated_count


def get_add_set_defaults(user, routine_exercise_id):
    re = RoutineExercise.objects.select_related("routine", "exercise").get(
        pk=routine_exercise_id
    )
    last_in_routine = get_routine_exercise_last_set(re)
    if last_in_routine:
        return last_in_routine.weight, last_in_routine.reps

    prior_re = (
        RoutineExercise.objects.filter(
            routine__user=user,
            exercise_id=re.exercise_id,
        )
        .exclude(routine_id=re.routine_id)
        .order_by("-routine__updated_at", "-routine_id")
        .first()
    )
    if prior_re:
        last_historical = get_routine_exercise_last_set(prior_re)
        if last_historical:
            return last_historical.weight, last_historical.reps

    return Decimal("10"), 10


def create_routine_set(routine_exercise_id, weight, reps, is_warmup):
    routine_exercise = RoutineExercise.objects.get(pk=routine_exercise_id)
    max_set_number = (
        RoutineSet.objects.filter(routine_exercise=routine_exercise).aggregate(
            Max("set_number")
        )["set_number__max"]
        or 0
    )
    routine_set = RoutineSet.objects.create(
        routine_exercise=routine_exercise,
        set_number=max_set_number + 1,
        weight=quantize_weight(weight),
        reps=reps,
        is_warmup=is_warmup,
    )
    if is_warmup:
        reorder_sets_for_routine_exercise(routine_exercise)
        routine_set.refresh_from_db()
    routine_exercise = get_routine_exercise(routine_exercise.pk)
    return routine_set, routine_exercise


def resolve_reps_to_int(reps_str, default_amrap_reps=10):
    if not reps_str:
        return default_amrap_reps
    reps_str = str(reps_str).lower()
    if "amrap" in reps_str:
        return default_amrap_reps
    match = re.match(r"(\d+)\s*-\s*(\d+)", reps_str)
    if match:
        return int(match.group(1))
    match = re.match(r"(\d+)", reps_str)
    if match:
        return int(match.group(1))
    return default_amrap_reps


def parse_exercise_line(line):
    if not line.strip():
        return None
    bilateral_pattern = r"^(.+?)\s+(\d+)x(\d+)x(\d+(?:-\d+)?)\s*(\d+(?:\.\d+)?)?$"
    normal_pattern = r"^(.+?)\s+(\d+)x(\d+(?:-\d+)?)\s*(\d+(?:\.\d+)?)?$"
    match = re.match(bilateral_pattern, line)
    if match:
        exercise_name = match.group(1).strip()
        bilateral_sets = int(match.group(2))
        sets_per_side = int(match.group(3))
        reps = match.group(4)
        weight = float(match.group(5)) if match.group(5) else None
        total_sets = bilateral_sets * sets_per_side
        return {
            "exercise_name": exercise_name,
            "sets": total_sets,
            "reps": reps,
            "weight": weight,
            "raw_line": line,
        }
    match = re.match(normal_pattern, line)
    if match:
        exercise_name = match.group(1).strip()
        sets = int(match.group(2))
        reps = match.group(3)
        weight = float(match.group(4)) if match.group(4) else None
        return {
            "exercise_name": exercise_name,
            "sets": sets,
            "reps": reps,
            "weight": weight,
            "raw_line": line,
        }
    return None


def parse_workout_text(text):
    lines = text.strip().split("\n")
    exercises = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parsed = parse_exercise_line(line)
        if parsed:
            exercises.append(parsed)
    return exercises


def parse_workout_days(text):
    lines = text.strip().split("\n")
    workout_days = []
    current_day_exercises = []
    for line in lines:
        line = line.strip()
        if not line:
            if current_day_exercises:
                workout_days.append(current_day_exercises)
                current_day_exercises = []
            continue
        parsed = parse_exercise_line(line)
        if parsed:
            current_day_exercises.append(parsed)
    if current_day_exercises:
        workout_days.append(current_day_exercises)
    return workout_days


def import_lookup_key(name):
    return " ".join(name.strip().split()).casefold()


def build_exercise_lookup(user):
    exercises = Exercise.objects.filter(
        Q(user__isnull=True) | Q(user=user)
    ).order_by("pk")
    lookup = {}
    for exercise in exercises:
        keys = [import_lookup_key(exercise.name)]
        for alt_name in exercise.alternative_names or []:
            if isinstance(alt_name, str) and alt_name.strip():
                keys.append(import_lookup_key(alt_name))
        for key in keys:
            if key not in lookup:
                lookup[key] = exercise
    return lookup


def find_exercise_for_import(name, lookup):
    return lookup.get(import_lookup_key(name))


def create_custom_exercise_for_import(user, name):
    return Exercise.objects.create(
        name=name.strip(),
        user=user,
        is_custom=True,
        exercise_type="accessory",
        alternative_names=[],
    )


def match_parsed_lines(user, parsed_lines):
    if not parsed_lines:
        return {
            "error": "No exercises could be parsed from the text. Please check the format.",
        }
    lookup = build_exercise_lookup(user)
    unmatched_names = []
    seen_keys = set()
    for parsed in parsed_lines:
        if find_exercise_for_import(parsed["exercise_name"], lookup) is None:
            key = import_lookup_key(parsed["exercise_name"])
            if key not in seen_keys:
                seen_keys.add(key)
                unmatched_names.append(parsed["exercise_name"])
    return {
        "parsed_lines": parsed_lines,
        "unmatched_names": unmatched_names,
    }


def prepare_routine_import(user, text):
    parsed_lines = parse_workout_text(text)
    return match_parsed_lines(user, parsed_lines)


def build_import_name_to_exercise(parsed_lines, lookup):
    name_to_exercise = {}
    for parsed in parsed_lines:
        key = import_lookup_key(parsed["exercise_name"])
        exercise = find_exercise_for_import(parsed["exercise_name"], lookup)
        name_to_exercise[key] = exercise
    return name_to_exercise


def resolve_import_exercises(user, unmatched_names, parsed_lines):
    for name in unmatched_names:
        create_custom_exercise_for_import(user, name)
    lookup = build_exercise_lookup(user)
    return build_import_name_to_exercise(parsed_lines, lookup)


def import_routine_from_parsed(user, routine_name, parsed_lines, name_to_exercise):
    with transaction.atomic():
        routine = Routine.objects.create(
            user=user,
            name=routine_name,
            notes=f"Imported from text on {timezone.now().strftime('%Y-%m-%d %H:%M')}",
        )
        for order, parsed in enumerate(parsed_lines):
            key = import_lookup_key(parsed["exercise_name"])
            exercise = name_to_exercise[key]
            routine_exercise = RoutineExercise.objects.create(
                routine=routine,
                exercise=exercise,
                order=order,
            )
            weight_value = parsed["weight"] if parsed["weight"] is not None else 0
            reps_value = resolve_reps_to_int(parsed["reps"])
            for set_num in range(1, parsed["sets"] + 1):
                RoutineSet.objects.create(
                    routine_exercise=routine_exercise,
                    set_number=set_num,
                    weight=quantize_weight(Decimal(str(weight_value))),
                    reps=reps_value,
                    is_warmup=False,
                )
    return routine
