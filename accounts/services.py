from uuid import uuid4

from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.utils import timezone

from accounts.models import User, UserSettings
from exercises.models import Exercise
from programs.models import Program, ProgramRoutine
from routines.models import Routine, RoutineExercise, RoutineSet
from workouts.models import ExerciseSet, Workout, WorkoutExercise


def create_user_with_settings(username, password, **extra_user_fields):
    user = User.objects.create_user(username=username, password=password, **extra_user_fields)
    UserSettings.objects.create(user=user)
    return user


def register_user(username, password):
    errors = []
    if User.objects.filter(username=username).exists():
        errors.append("Username already taken.")
    if errors:
        return None, errors
    try:
        password_validation.validate_password(password)
    except ValidationError as exc:
        return None, list(exc.messages)
    user = create_user_with_settings(username, password)
    return user, []


def create_demo_user():
    username = f"demo_{uuid4().hex[:8]}"
    password = uuid4().hex
    return create_user_with_settings(username, password, is_demo=True)

def create_routine_exercise_with_sets(routine, exercise, order, sets):
    routine_exercise = RoutineExercise.objects.create(
        routine=routine,
        exercise=exercise,
        order=order,
    )
    for set_number, set_data in enumerate(sets, start=1):
        RoutineSet.objects.create(
            routine_exercise=routine_exercise,
            set_number=set_number,
            weight=set_data["weight"],
            reps=set_data["reps"],
            is_warmup=set_data.get("is_warmup", False),
        )
    return routine_exercise


def create_workout_from_routine(user, routine, workout_date, name):
    workout = Workout.objects.create(
        user=user,
        date=workout_date,
        name=name,
        routine=routine,
    )
    for routine_exercise in routine.exercises.all():
        workout_exercise = WorkoutExercise.objects.create(
            workout=workout,
            exercise=routine_exercise.exercise,
            order=routine_exercise.order,
            exercise_type=routine_exercise.exercise_type,
        )
        for routine_set in routine_exercise.sets.all():
            ExerciseSet.objects.create(
                workout_exercise=workout_exercise,
                set_number=routine_set.set_number,
                weight=routine_set.weight,
                reps=routine_set.reps,
                is_warmup=routine_set.is_warmup,
                is_completed=True,
            )
    return workout


def seed_demo_user(user):
    bench_press = Exercise.objects.get(name="Bench Press", user=None)
    overhead_press = Exercise.objects.get(name="Overhead Press", user=None)
    lateral_raise = Exercise.objects.get(name="Lateral Raises", user=None)
    deadlift = Exercise.objects.get(name="Deadlift", user=None)
    pull_up = Exercise.objects.get(name="Pull-Ups", user=None)
    squat = Exercise.objects.get(name="Squat", user=None)

    push_day = Routine.objects.create(
        user=user,
        name="Push Day",
        notes="Chest, shoulders, and triceps.",
    )
    create_routine_exercise_with_sets(push_day, bench_press, 0, [
        {"weight": 60, "reps": 5, "is_warmup": True},
        {"weight": 80, "reps": 5},
        {"weight": 80, "reps": 5},
        {"weight": 80, "reps": 5},
    ])
    create_routine_exercise_with_sets(push_day, overhead_press, 1, [
        {"weight": 55, "reps": 5},
        {"weight": 55, "reps": 5},
        {"weight": 55, "reps": 5},
    ])
    create_routine_exercise_with_sets(push_day, lateral_raise, 2, [
        {"weight": 12, "reps": 12},
        {"weight": 12, "reps": 12},
        {"weight": 12, "reps": 12},
    ])

    pull_day = Routine.objects.create(
        user=user,
        name="Pull Day",
        notes="Back and legs.",
    )
    create_routine_exercise_with_sets(pull_day, deadlift, 0, [
        {"weight": 80, "reps": 5, "is_warmup": True},
        {"weight": 120, "reps": 5},
        {"weight": 120, "reps": 5},
        {"weight": 120, "reps": 5},
    ])
    create_routine_exercise_with_sets(pull_day, pull_up, 1, [
        {"weight": 0, "reps": 8},
        {"weight": 0, "reps": 8},
        {"weight": 0, "reps": 8},
    ])
    create_routine_exercise_with_sets(pull_day, squat, 2, [
        {"weight": 70, "reps": 5, "is_warmup": True},
        {"weight": 100, "reps": 5},
        {"weight": 100, "reps": 5},
        {"weight": 100, "reps": 5},
    ])

    program = Program.objects.create(
        user=user,
        name="Push/Pull Program",
        description="A simple push and pull split.",
        is_active=True,
    )
    ProgramRoutine.objects.create(program=program, routine=push_day, order=1)
    ProgramRoutine.objects.create(program=program, routine=pull_day, order=2)

    now = timezone.now()
    create_workout_from_routine(
        user,
        push_day,
        now - timezone.timedelta(days=8),
        "Push Day",
    )
    create_workout_from_routine(
        user,
        pull_day,
        now - timezone.timedelta(days=5),
        "Pull Day",
    )
    create_workout_from_routine(
        user,
        push_day,
        now - timezone.timedelta(days=2),
        "Push Day",
    )
