from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Count, F, Max, Prefetch, Q
from django.utils import timezone

from exercises.models import Exercise
from gainz2.utils import next_numbered_name, parse_weight_increment, quantize_weight
from programs.models import Program, ProgramExercise, ProgramRoutine, ProgressionStep, ProgressionTemplate
from programs.services import get_program_type_progression_template
from routines.models import Routine, RoutineExercise
from routines.services import list_routines
from workouts.models import Workout, WorkoutExercise, ExerciseSet

def get_active_program(user):
    return Program.objects.filter(user=user, is_active=True).first()


def get_next_routine_for_program(program):
    program_routines = list(
        ProgramRoutine.objects.filter(program=program)
        .select_related("routine")
        .order_by("order")
    )
    if not program_routines:
        return None
    last = program.last_used_routine
    if last is None:
        return program_routines[0].routine
    current_ids = [pr.routine_id for pr in program_routines]
    if last.pk not in current_ids:
        return program_routines[0].routine
    next_index = (current_ids.index(last.pk) + 1) % len(program_routines)
    return program_routines[next_index].routine


def find_prior_workout_exercise(
    user,
    exercise,
    exercise_type,
    routine,
    program=None,
    exclude_workout=None,
    global_fallback=False,
):
    exercise_id = exercise.pk if hasattr(exercise, "pk") else exercise
    if program is None:
        program = get_active_program(user)
    if program:
        if exercise_type == "primary":
            carryover = program.primary_carryover
        elif exercise_type == "secondary":
            carryover = program.secondary_carryover
        else:
            carryover = program.accessory_carryover
    else:
        carryover = False

    base_qs = (
        WorkoutExercise.objects.filter(
            workout__user=user,
            exercise_id=exercise_id,
        )
        .filter(
            Q(exercise_type=exercise_type)
            | Q(exercise_type__isnull=True, exercise__exercise_type=exercise_type)
        )
        .select_related("exercise")
        .order_by("-workout__date", "-workout__pk")
        .prefetch_related("sets")
    )
    if exclude_workout:
        base_qs = base_qs.exclude(workout=exclude_workout)

    if carryover and program:
        routine_ids = ProgramRoutine.objects.filter(program=program).values_list(
            "routine_id", flat=True
        )
        prior = base_qs.filter(workout__routine_id__in=routine_ids).first()
        if prior:
            return prior
    elif routine:
        prior = base_qs.filter(workout__routine=routine).first()
        if prior:
            return prior

    if global_fallback:
        return base_qs.first()
    return None


def find_prior_workout(user, routine, exclude_workout=None):
    workouts = Workout.objects.filter(user=user, routine=routine).order_by(
        "-date", "-pk"
    )
    if exclude_workout:
        workouts = workouts.exclude(pk=exclude_workout.pk)
    return workouts.first()


def resolve_progression(
    program,
    program_includes_routine,
    routine_exercise,
    prior,
    exercise_type,
):
    if prior:
        feedback = prior.performance_feedback or "stay"
        prior_step = prior.progression_step
    else:
        feedback = "stay"
        prior_step = 0

    template = None
    step_count = 0
    if program_includes_routine:
        template_pk = None
        if routine_exercise:
            program_exercise = (
                ProgramExercise.objects.filter(
                    program=program,
                    routine_exercise=routine_exercise,
                )
                .select_related("progression_template")
                .first()
            )
            if program_exercise and program_exercise.progression_template_id:
                template_pk = program_exercise.progression_template_id
        if template_pk is None:
            type_template = get_program_type_progression_template(
                program, exercise_type
            )
            template_pk = type_template.pk if type_template else None
        if template_pk:
            template = (
                ProgressionTemplate.objects.filter(pk=template_pk)
                .prefetch_related(
                    Prefetch(
                        "steps",
                        queryset=ProgressionStep.objects.order_by("order"),
                    )
                )
                .first()
            )
            if template:
                step_count = template.steps.count()

    step_to_apply = None
    reverse = False
    if prior and template and step_count:
        if prior_step >= step_count:
            if feedback == "increase":
                prior_step = 0
            else:
                prior_step = step_count - 1
        if feedback == "stay":
            new_step = prior_step
        elif feedback == "increase":
            if prior_step == step_count - 1:
                step_to_apply = step_count
                new_step = 0
            else:
                step_to_apply = prior_step + 1
                new_step = prior_step + 1
        else:
            if prior_step == 0:
                step_to_apply = step_count
                new_step = step_count - 1
            else:
                step_to_apply = prior_step
                new_step = prior_step - 1
            reverse = True
    elif prior:
        new_step = prior_step
    else:
        new_step = 0

    return template, step_to_apply, reverse, new_step, feedback


def apply_progression_to_set_values(
    set_values, step_to_apply, reverse, template, weight_increment
):
    if step_to_apply is None or template is None:
        return set_values
    step = None
    for template_step in template.steps.all():
        if template_step.order == step_to_apply:
            step = template_step
            break
    if not step:
        return set_values
    sign = -1 if reverse else 1
    increment = parse_weight_increment(weight_increment)
    progression_delta = Decimal(step.weight_delta)
    if progression_delta == 0:
        weight_delta = Decimal("0")
    else:
        steps = int(
            (abs(progression_delta) / increment).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        )
        if steps == 0:
            weight_delta = Decimal("0")
        elif progression_delta > 0:
            weight_delta = steps * increment
        else:
            weight_delta = -steps * increment
    return [
        (
            quantize_weight(
                max(0, weight + sign * weight_delta),
                weight_increment,
            ),
            max(0, reps + sign * step.reps_delta),
            is_warmup,
        )
        for weight, reps, is_warmup in set_values
    ]


def create_workout_exercise_with_sets(
    workout,
    exercise,
    order,
    exercise_type,
    notes,
    feedback,
    new_step,
    set_values,
):
    workout_exercise = WorkoutExercise.objects.create(
        workout=workout,
        exercise=exercise,
        order=order,
        exercise_type=exercise_type,
        notes=notes,
        performance_feedback=feedback,
        progression_step=new_step,
    )
    for set_number, (weight, reps, is_warmup) in enumerate(set_values, start=1):
        ExerciseSet.objects.create(
            workout_exercise=workout_exercise,
            set_number=set_number,
            weight=weight,
            reps=reps,
            is_warmup=is_warmup,
        )
    return workout_exercise


def complete_latest_workout(user, workout=None):
    if workout is None:
        workout = Workout.objects.filter(user=user).order_by("-date", "-pk").first()
    if workout:
        ExerciseSet.objects.filter(
            workout_exercise__workout=workout,
            is_completed=False,
        ).update(is_completed=True)


def new_workout_from_routine(user, routine):
    complete_latest_workout(user)
    names = Workout.objects.filter(user=user, routine=routine).values_list(
        "name", flat=True
    )
    name = next_numbered_name(routine.name, names)
    workout = Workout.objects.create(user=user, name=name, routine=routine)
    program = get_active_program(user)
    program_includes_routine = (
        program
        and ProgramRoutine.objects.filter(program=program, routine=routine).exists()
    )
    if routine.recently_changed:
        for routine_exercise in routine.exercises.prefetch_related(
            "sets", "exercise"
        ).order_by("order"):
            prior = find_prior_workout_exercise(
                user,
                routine_exercise.exercise,
                routine_exercise.effective_exercise_type(),
                workout.routine,
                program=program,
                exclude_workout=workout,
            )
            notes = routine_exercise.notes or (prior.notes if prior else "")
            template, step_to_apply, reverse, new_step, feedback = resolve_progression(
                program,
                program_includes_routine,
                routine_exercise,
                prior,
                routine_exercise.effective_exercise_type(),
            )
            routine_sets = list(routine_exercise.sets.order_by("set_number"))
            if prior:
                prior_sets = list(prior.sets.order_by("set_number"))
                prior_warmups = [s for s in prior_sets if s.is_warmup]
                prior_work = [s for s in prior_sets if not s.is_warmup]
                set_values = []
                warmup_index = 0
                work_index = 0
                for routine_set in routine_sets:
                    if routine_set.is_warmup:
                        if warmup_index < len(prior_warmups):
                            source = prior_warmups[warmup_index]
                            warmup_index += 1
                        elif prior_warmups:
                            source = prior_warmups[-1]
                        else:
                            set_values.append(
                                (routine_set.weight, routine_set.reps, True)
                            )
                            continue
                        set_values.append((source.weight, source.reps, True))
                    else:
                        if work_index < len(prior_work):
                            source = prior_work[work_index]
                            work_index += 1
                        elif prior_work:
                            source = prior_work[-1]
                        else:
                            set_values.append(
                                (routine_set.weight, routine_set.reps, False)
                            )
                            continue
                        set_values.append((source.weight, source.reps, False))
            else:
                set_values = [
                    (rs.weight, rs.reps, rs.is_warmup) for rs in routine_sets
                ]
            set_values = apply_progression_to_set_values(
                set_values,
                step_to_apply,
                reverse,
                template,
                routine_exercise.exercise.weight_increment,
            )
            create_workout_exercise_with_sets(
                workout,
                routine_exercise.exercise,
                routine_exercise.order,
                routine_exercise.effective_exercise_type(),
                notes,
                feedback,
                new_step,
                set_values,
            )
    else:
        prior_workout = find_prior_workout(user, routine, exclude_workout=workout)
        prior_workout = Workout.objects.prefetch_related(
            Prefetch(
                "exercises",
                queryset=WorkoutExercise.objects.select_related(
                    "exercise"
                ).prefetch_related(
                    Prefetch(
                        "sets",
                        queryset=ExerciseSet.objects.order_by("set_number"),
                    )
                ),
            ),
        ).get(pk=prior_workout.pk)
        for prior_we in prior_workout.exercises.all():
            routine_exercise = RoutineExercise.objects.filter(
                routine=routine,
                exercise_id=prior_we.exercise_id,
            ).first()
            template, step_to_apply, reverse, new_step, feedback = resolve_progression(
                program,
                program_includes_routine,
                routine_exercise,
                prior_we,
                prior_we.effective_exercise_type(),
            )
            set_values = [
                (s.weight, s.reps, s.is_warmup) for s in prior_we.sets.all()
            ]
            set_values = apply_progression_to_set_values(
                set_values,
                step_to_apply,
                reverse,
                template,
                prior_we.exercise.weight_increment,
            )
            create_workout_exercise_with_sets(
                workout,
                prior_we.exercise,
                prior_we.order,
                prior_we.effective_exercise_type(),
                prior_we.notes,
                feedback,
                new_step,
                set_values,
            )
    Routine.objects.filter(pk=routine.pk).update(recently_changed=False)
    return workout


def list_routines_for_choose(user):
    program = get_active_program(user)
    program_routine_ids = []
    program_routines = []
    if program:
        prs = list(
            ProgramRoutine.objects.filter(program=program)
            .select_related("routine")
            .order_by("order")
        )
        program_routines = [pr.routine for pr in prs]
        program_routine_ids = [r.pk for r in program_routines]
    other_routines = list(
        list_routines(user)
        .exclude(pk__in=program_routine_ids)
        .order_by("name")
    )
    return program_routines, other_routines


def list_workouts(user):
    return (
        Workout.objects.filter(user=user)
        .annotate(
            exercise_count=Count("exercises", distinct=True),
            set_count=Count("exercises__sets", distinct=True),
        )
        .order_by("-date")
    )


def new_workout(user):
    names = Workout.objects.filter(user=user).values_list("name", flat=True)
    return Workout.objects.create(
        user=user,
        name=next_numbered_name("Workout", names),
        notes="",
    )


def get_workout_exercise(workout_exercise_id):
    return WorkoutExercise.objects.select_related("exercise").prefetch_related(
        Prefetch(
            "sets",
            queryset=ExerciseSet.objects.order_by("set_number"),
        )
    ).get(pk=workout_exercise_id)


def get_workout_exercise_last_set(workout_exercise):
    return (
        ExerciseSet.objects.filter(workout_exercise=workout_exercise)
        .order_by("-set_number")
        .first()
    )


def get_workout(workout_id):
    return Workout.objects.prefetch_related(
        Prefetch(
            "exercises",
            queryset=WorkoutExercise.objects.all(),
        ),
        "exercises__exercise",
        Prefetch(
            "exercises__sets",
            queryset=ExerciseSet.objects.order_by("set_number").all(),
        ),
    ).get(pk=workout_id)


def update_workout(user, workout_id, name=None, date_str=None, notes=None):
    workout = Workout.objects.get(pk=workout_id, user=user)
    if date_str:
        local_date = timezone.localtime(workout.date)
        new_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        workout.date = timezone.make_aware(
            datetime.combine(new_date, local_date.time()),
            timezone.get_current_timezone(),
        )
    if name:
        workout.name = name
    if notes:
        workout.notes = notes
    workout.save()
    return workout


def delete_workout(user, workout_id):
    workout = Workout.objects.get(pk=workout_id, user=user)
    workout.delete()


def set_workout_exercise_feedback(user, workout_exercise_id, feedback):
    valid_feedback = {choice[0] for choice in WorkoutExercise.FEEDBACK_CHOICES}
    if feedback not in valid_feedback:
        raise ValueError(feedback)
    workout_exercise = WorkoutExercise.objects.get(
        pk=workout_exercise_id,
        workout__user=user,
    )
    workout_exercise.performance_feedback = feedback
    workout_exercise.save(update_fields=["performance_feedback"])
    return workout_exercise


def update_workout_exercise_notes(user, workout_exercise_id, notes):
    workout_exercise = WorkoutExercise.objects.get(
        pk=workout_exercise_id,
        workout__user=user,
    )
    workout_exercise.notes = notes
    workout_exercise.save(update_fields=["notes"])
    return workout_exercise


def list_add_exercise_options(primary_bodypart=None):
    exercises = Exercise.objects.filter(user__isnull=True)
    if primary_bodypart:
        exercises = exercises.filter(primary_bodypart=primary_bodypart)
    return exercises.order_by("name")


TYPE_PRIORITY = {
    "primary": 3,
    "secondary": 2,
    "accessory": 1,
}

def index_at_start_of_type_section(existing_list, new_type):
    new_priority = TYPE_PRIORITY[new_type]
    return sum(
        1
        for we in existing_list
        if TYPE_PRIORITY[we.effective_exercise_type()] > new_priority
    )


def index_after_last_of_type(existing_list, new_type):
    same_type_indices = [
        index
        for index, we in enumerate(existing_list)
        if we.effective_exercise_type() == new_type
    ]
    if same_type_indices:
        return max(same_type_indices) + 1
    return index_at_start_of_type_section(existing_list, new_type)


def compute_add_exercise_insert_index(existing_list, new_type, current_workout_exercise_id=None):
    if not existing_list:
        return 0

    if not current_workout_exercise_id:
        return index_after_last_of_type(existing_list, new_type)

    current_index = None
    current_we = None
    for index, we in enumerate(existing_list):
        if we.pk == current_workout_exercise_id:
            current_index = index
            current_we = we
            break

    if current_we is None:
        return index_after_last_of_type(existing_list, new_type)

    current_type = current_we.effective_exercise_type()
    new_priority = TYPE_PRIORITY[new_type]
    current_priority = TYPE_PRIORITY[current_type]

    if new_priority == current_priority:
        return current_index + 1
    if new_priority > current_priority:
        return index_after_last_of_type(existing_list, new_type)

    same_type_indices = [
        index
        for index, we in enumerate(existing_list)
        if we.effective_exercise_type() == new_type
    ]
    if same_type_indices:
        return min(same_type_indices)
    return index_at_start_of_type_section(existing_list, new_type)


def add_exercise_to_workout(
    user,
    workout_id,
    exercise_id,
    current_workout_exercise_id=None,
    exercise_type=None,
):
    exercise = Exercise.objects.get(pk=exercise_id)
    new_type = exercise_type if exercise_type else exercise.exercise_type

    existing_list = list(
        WorkoutExercise.objects.filter(workout_id=workout_id)
        .select_related("exercise")
    )
    insert_index = compute_add_exercise_insert_index(
        existing_list,
        new_type,
        current_workout_exercise_id,
    )
    new_order = insert_index

    WorkoutExercise.objects.filter(
        workout_id=workout_id,
        order__gte=new_order,
    ).update(order=F("order") + 1)

    notes = ""
    prior = None
    if user.settings.set_carryover:
        workout_for_lookup = Workout.objects.get(pk=workout_id)
        prior = find_prior_workout_exercise(
            user,
            exercise,
            new_type,
            workout_for_lookup.routine,
            program=get_active_program(user),
            exclude_workout=workout_for_lookup,
        )
        if prior:
            notes = prior.notes

    new_workout_exercise = WorkoutExercise.objects.create(
        workout_id=workout_id,
        exercise_id=exercise_id,
        exercise_type=new_type,
        order=new_order,
        notes=notes,
    )

    if prior and prior.sets.exists():
        for prior_set in prior.sets.order_by("set_number"):
            new_set = ExerciseSet.objects.create(
                workout_exercise=new_workout_exercise,
                set_number=prior_set.set_number,
                weight=prior_set.weight,
                reps=prior_set.reps,
                is_warmup=prior_set.is_warmup,
            )

    new_exercise_index = insert_index
    workout = get_workout(workout_id)
    return workout, new_workout_exercise, new_exercise_index


def reorder_sets_for_workout_exercise(workout_exercise):
    sets = list(
        ExerciseSet.objects.filter(workout_exercise=workout_exercise).order_by(
            "set_number"
        )
    )
    warmups = [s for s in sets if s.is_warmup]
    working = [s for s in sets if not s.is_warmup]
    ordered = warmups + working
    for index, exercise_set in enumerate(ordered, start=1):
        exercise_set.set_number = index
        exercise_set.save(update_fields=["set_number"])


def workout_exercise_has_incomplete_sets(workout_exercise):
    sets = list(workout_exercise.sets.all())
    if not sets:
        return False
    return any(not exercise_set.is_completed for exercise_set in sets)


def workout_exercise_all_sets_complete(workout_exercise):
    sets = list(workout_exercise.sets.all())
    return bool(sets) and all(exercise_set.is_completed for exercise_set in sets)


def find_next_exercise_with_incomplete_sets(workout_id, current_workout_exercise_id):
    exercises = list(
        WorkoutExercise.objects.filter(workout_id=workout_id)
        .prefetch_related("sets")
        .order_by("order")
    )
    current_index = None
    for index, workout_exercise in enumerate(exercises):
        if workout_exercise.pk == current_workout_exercise_id:
            current_index = index
            break
    if current_index is None:
        return None
    for index in range(current_index + 1, len(exercises)):
        if workout_exercise_has_incomplete_sets(exercises[index]):
            return index
    for index in range(0, current_index):
        if workout_exercise_has_incomplete_sets(exercises[index]):
            return index
    return None


def toggle_exercise_set_completed(set_id):
    exercise_set = ExerciseSet.objects.select_related("workout_exercise").get(
        pk=set_id
    )
    exercise_set.is_completed = not exercise_set.is_completed
    exercise_set.save(update_fields=["is_completed"])
    return exercise_set, exercise_set.workout_exercise, exercise_set.is_completed


def delete_exercise_set(set_id):
    exercise_set = ExerciseSet.objects.select_related("workout_exercise").get(
        pk=set_id
    )
    workout_exercise = exercise_set.workout_exercise
    exercise_set.delete()
    reorder_sets_for_workout_exercise(workout_exercise)
    workout_exercise = get_workout_exercise(workout_exercise.pk)
    return workout_exercise


def delete_workout_exercise(workout_exercise_id, current_exercise_index):
    workout_exercise = WorkoutExercise.objects.get(pk=workout_exercise_id)
    workout_id = workout_exercise.workout_id
    workout_exercise.delete()

    WorkoutExercise.objects.filter(
        workout_id=workout_id,
        order__gt=current_exercise_index,
    ).update(order=F("order") - 1)

    remaining_count = WorkoutExercise.objects.filter(workout_id=workout_id).count()
    if remaining_count == 0:
        active_exercise_index = 0
    elif current_exercise_index < remaining_count:
        active_exercise_index = current_exercise_index
    else:
        active_exercise_index = remaining_count - 1

    workout = get_workout(workout_id)
    return workout, active_exercise_index


def reorder_workout_exercises(user, workout_id, ordered_exercise_ids):
    Workout.objects.get(pk=workout_id, user=user)
    exercises = {
        exercise.pk: exercise
        for exercise in WorkoutExercise.objects.filter(workout_id=workout_id)
    }
    for index, exercise_id in enumerate(ordered_exercise_ids):
        exercise_id = int(exercise_id)
        workout_exercise = exercises[exercise_id]
        workout_exercise.order = index
        workout_exercise.save(update_fields=["order"])


def apply_smartchange(
    workout_exercise,
    edited_set_id,
    weight_delta,
    reps_delta,
    is_warmup,
    smartchange_warmup,
    weight_increment,
):
    siblings = ExerciseSet.objects.filter(
        workout_exercise=workout_exercise
    ).exclude(pk=edited_set_id)
    siblings = siblings.filter(is_completed=False)
    if not smartchange_warmup:
        siblings = siblings.filter(is_warmup=is_warmup)
    updated_count = 0
    for sibling in siblings:
        new_weight = sibling.weight + weight_delta
        if new_weight < 0:
            new_weight = Decimal("0")
        else:
            new_weight = quantize_weight(new_weight, weight_increment)
        new_reps = max(1, sibling.reps + reps_delta)
        if new_weight != sibling.weight or new_reps != sibling.reps:
            sibling.weight = new_weight
            sibling.reps = new_reps
            sibling.save(update_fields=["weight", "reps"])
            updated_count += 1
    return updated_count


def update_exercise_set(set_id, weight, reps, is_warmup, *, user=None, smartchange=False):
    exercise_set = ExerciseSet.objects.select_related(
        "workout_exercise__exercise"
    ).get(pk=set_id)
    workout_exercise = exercise_set.workout_exercise
    weight_increment = workout_exercise.exercise.weight_increment
    old_weight = exercise_set.weight
    old_reps = exercise_set.reps
    old_is_warmup = exercise_set.is_warmup
    exercise_set.weight = quantize_weight(weight, weight_increment)
    exercise_set.reps = reps
    exercise_set.is_warmup = is_warmup
    exercise_set.save()
    warmup_changed = old_is_warmup != is_warmup
    if warmup_changed:
        reorder_sets_for_workout_exercise(workout_exercise)
        exercise_set.refresh_from_db()
        workout_exercise = get_workout_exercise(workout_exercise.pk)
    weight_delta = exercise_set.weight - old_weight
    reps_delta = exercise_set.reps - old_reps
    siblings_updated_count = 0
    if smartchange and user and (weight_delta != 0 or reps_delta != 0):
        siblings_updated_count = apply_smartchange(
            workout_exercise,
            exercise_set.pk,
            weight_delta,
            reps_delta,
            exercise_set.is_warmup,
            user.settings.smartchange_warmup,
            weight_increment,
        )
        if siblings_updated_count:
            workout_exercise = get_workout_exercise(workout_exercise.pk)
    return exercise_set, workout_exercise, warmup_changed, siblings_updated_count


def get_add_set_defaults(user, workout_exercise_id):
    we = WorkoutExercise.objects.select_related("workout", "exercise").get(
        pk=workout_exercise_id
    )
    last_in_session = get_workout_exercise_last_set(we)
    if last_in_session:
        return last_in_session.weight, last_in_session.reps

    if user.settings.set_carryover:
        prior_we = find_prior_workout_exercise(
            user,
            we.exercise,
            we.effective_exercise_type(),
            we.workout.routine,
            program=get_active_program(user),
            exclude_workout=we.workout,
            global_fallback=True,
        )
        if prior_we:
            prior_sets = list(prior_we.sets.order_by("set_number"))
            if prior_sets:
                current_set_count = ExerciseSet.objects.filter(
                    workout_exercise=we
                ).count()
                source = (
                    prior_sets[current_set_count]
                    if current_set_count < len(prior_sets)
                    else prior_sets[-1]
                )
                return source.weight, source.reps

    return Decimal("10"), 10


def create_exercise_set(workout_exercise_id, weight, reps, is_warmup):
    workout_exercise = WorkoutExercise.objects.select_related("exercise").get(
        pk=workout_exercise_id
    )
    weight_increment = workout_exercise.exercise.weight_increment
    max_set_number = (
        ExerciseSet.objects.filter(workout_exercise=workout_exercise).aggregate(
            Max("set_number")
        )["set_number__max"]
        or 0
    )
    exercise_set = ExerciseSet.objects.create(
        workout_exercise=workout_exercise,
        set_number=max_set_number + 1,
        weight=quantize_weight(weight, weight_increment),
        reps=reps,
        is_warmup=is_warmup,
    )
    if is_warmup:
        reorder_sets_for_workout_exercise(workout_exercise)
        exercise_set.refresh_from_db()
    workout_exercise = get_workout_exercise(workout_exercise.pk)
    return exercise_set, workout_exercise
