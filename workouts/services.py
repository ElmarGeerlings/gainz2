from datetime import datetime
from decimal import Decimal

from django.db.models import F, Max, Prefetch
from django.utils import timezone

from exercises.models import Exercise
from workouts.models import Workout, WorkoutExercise, ExerciseSet


def quantize_weight(weight):
    half_steps = (Decimal(weight) * 2).quantize(Decimal("1"))
    return half_steps / Decimal("2")


def get_workout_exercise(workout_exercise_id):
    return WorkoutExercise.objects.prefetch_related(
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


def list_add_exercise_options():
    return Exercise.objects.filter(user__isnull=True).order_by("name")


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

    new_workout_exercise = WorkoutExercise.objects.create(
        workout_id=workout_id,
        exercise_id=exercise_id,
        exercise_type=new_type,
        order=new_order,
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


def update_exercise_set(set_id, weight, reps, is_warmup):
    exercise_set = ExerciseSet.objects.select_related("workout_exercise").get(
        pk=set_id
    )
    workout_exercise = exercise_set.workout_exercise
    old_is_warmup = exercise_set.is_warmup
    exercise_set.weight = quantize_weight(weight)
    exercise_set.reps = reps
    exercise_set.is_warmup = is_warmup
    exercise_set.save()
    warmup_changed = old_is_warmup != is_warmup
    if warmup_changed:
        reorder_sets_for_workout_exercise(workout_exercise)
        exercise_set.refresh_from_db()
        workout_exercise = get_workout_exercise(workout_exercise.pk)
    return exercise_set, workout_exercise, warmup_changed


def get_add_set_defaults(user, workout_exercise_id):
    we = WorkoutExercise.objects.select_related("workout", "exercise").get(
        pk=workout_exercise_id
    )
    last_in_session = get_workout_exercise_last_set(we)
    if last_in_session:
        return last_in_session.weight, last_in_session.reps

    prior_we = (
        WorkoutExercise.objects.filter(
            workout__user=user,
            exercise_id=we.exercise_id,
        )
        .exclude(workout_id=we.workout_id)
        .order_by("-workout__date", "-workout_id")
        .first()
    )
    if prior_we:
        last_historical = get_workout_exercise_last_set(prior_we)
        if last_historical:
            return last_historical.weight, last_historical.reps

    return Decimal("10"), 10


def create_exercise_set(workout_exercise_id, weight, reps, is_warmup):
    workout_exercise = WorkoutExercise.objects.get(pk=workout_exercise_id)
    max_set_number = (
        ExerciseSet.objects.filter(workout_exercise=workout_exercise).aggregate(
            Max("set_number")
        )["set_number__max"]
        or 0
    )
    exercise_set = ExerciseSet.objects.create(
        workout_exercise=workout_exercise,
        set_number=max_set_number + 1,
        weight=quantize_weight(weight),
        reps=reps,
        is_warmup=is_warmup,
    )
    if is_warmup:
        reorder_sets_for_workout_exercise(workout_exercise)
        exercise_set.refresh_from_db()
    workout_exercise = get_workout_exercise(workout_exercise.pk)
    return exercise_set, workout_exercise
