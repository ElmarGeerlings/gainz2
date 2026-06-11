import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gainz2.settings")

import django
django.setup()

from django.db import transaction

from accounts.models import User
from exercises.models import Exercise
from programs.models import Program, ProgramRoutine
from routines.models import Routine, RoutineExercise, RoutineSet


EXERCISES = [
    {"name": "Ab Roller",           "description": "Roll a wheel forward while kneeling to engage the entire core.", "exercise_type": "accessory", "primary_bodypart": "core",  "secondary_bodypart": None},
    {"name": "Bench Press",         "description": "Classic compound chest exercise performed lying on a flat bench with a barbell.", "exercise_type": "primary",   "primary_bodypart": "chest", "secondary_bodypart": "shoulders"},
    {"name": "Biceps Bar",          "description": "Seated or standing curl with an EZ-bar to target the biceps.",   "exercise_type": "accessory", "primary_bodypart": "arms",  "secondary_bodypart": None},
    {"name": "Biceps Cable",        "description": "Cable curl for bicep isolation, allowing constant tension throughout the movement.", "exercise_type": "accessory", "primary_bodypart": "arms",    "secondary_bodypart": None},
    {"name": "Deadlift",            "description": "Lift a barbell from the ground to standing position, primarily targeting the back and posterior chain.", "exercise_type": "primary", "primary_bodypart": "back", "secondary_bodypart": "legs"},
    {"name": "Dumbbell Curl",       "description": "Isolation exercise for the biceps using dumbbells for unilateral control.",  "exercise_type": "accessory", "primary_bodypart": "arms",  "secondary_bodypart": None},
    {"name": "Dumbbell Side Crunch","description": "Crunch while holding a dumbbell to one side for oblique development.", "exercise_type": "accessory", "primary_bodypart": "core", "secondary_bodypart": None},
    {"name": "Face Pulls",          "description": "Cable exercise pulling a rope toward the face to target the rear deltoids and upper back.", "exercise_type": "accessory", "primary_bodypart": "shoulders", "secondary_bodypart": "back"},
    {"name": "Hamstring Curls",     "description": "Machine exercise curling the legs to target the hamstrings.",    "exercise_type": "accessory", "primary_bodypart": "legs",  "secondary_bodypart": None},
    {"name": "Hip Abductor",        "description": "Machine exercise pushing the legs outward to isolate the hip abductor muscles.",  "exercise_type": "accessory", "primary_bodypart": "legs",  "secondary_bodypart": None},
    {"name": "Incline Bench Press", "description": "Pressing movement on an inclined bench to emphasise the upper chest.",        "exercise_type": "secondary", "primary_bodypart": "chest", "secondary_bodypart": "shoulders"},
    {"name": "Lateral Raises",      "description": "Dumbbell isolation exercise raising the arms to the sides to target the lateral deltoids.", "exercise_type": "accessory", "primary_bodypart": "shoulders", "secondary_bodypart": None},
    {"name": "Leg Extension",       "description": "Machine isolation exercise extending the legs to target the quadriceps.",      "exercise_type": "accessory", "primary_bodypart": "legs",  "secondary_bodypart": None},
    {"name": "Leg Press",           "description": "Machine-based pressing movement for the quads, hamstrings, and glutes.",     "exercise_type": "secondary", "primary_bodypart": "legs",  "secondary_bodypart": None},
    {"name": "Leg Raises",          "description": "Lie on your back and raise straight legs upward to target the lower abdominals.", "exercise_type": "accessory", "primary_bodypart": "core",  "secondary_bodypart": None},
    {"name": "Low Rows",            "description": "Cable or machine row performed at a low angle to target the lats and middle back.", "exercise_type": "accessory", "primary_bodypart": "back",  "secondary_bodypart": "arms"},
    {"name": "Overhead Press",      "description": "Vertical pressing movement for the shoulders and triceps, performed standing or seated.", "exercise_type": "primary",   "primary_bodypart": "shoulders", "secondary_bodypart": "arms"},
    {"name": "Peck Deck",           "description": "Machine fly bringing the arms together in front of the chest to isolate the pectorals.", "exercise_type": "accessory", "primary_bodypart": "chest", "secondary_bodypart": None},
    {"name": "Pull-Ups",            "description": "Bodyweight vertical pulling exercise targeting the lats and biceps.",       "exercise_type": "secondary", "primary_bodypart": "back",  "secondary_bodypart": "arms"},
    {"name": "Squat",               "description": "Fundamental lower body exercise squatting with bodyweight, barbell, or dumbbells.", "exercise_type": "primary", "primary_bodypart": "legs", "secondary_bodypart": None},
    {"name": "Tricep Pushdown",     "description": "Cable isolation exercise pushing a bar or rope down to target the triceps.",   "exercise_type": "accessory", "primary_bodypart": "arms",  "secondary_bodypart": None},
]

ROUTINES = [
    {
        "name": "Deadlift Day",
        "exercises": [
            {"name": "Deadlift",            "exercise_type": "primary",   "order": 0, "sets": [
                {"weight": 200, "reps": 4},
                {"weight": 215, "reps": 3},
                {"weight": 215, "reps": 3},
                {"weight": 215, "reps": 3},
            ]},
            {"name": "Leg Press",           "exercise_type": "secondary", "order": 1, "sets": [
                {"weight": 230, "reps": 12},
                {"weight": 230, "reps": 12},
                {"weight": 230, "reps": 12},
                {"weight": 230, "reps": 12},
            ]},
            {"name": "Face Pulls",          "exercise_type": "accessory", "order": 2, "sets": [
                {"weight": 60, "reps": 10},
                {"weight": 60, "reps": 10},
                {"weight": 60, "reps": 10},
                {"weight": 60, "reps": 10},
            ]},
            {"name": "Hamstring Curls",     "exercise_type": "accessory", "order": 3, "sets": [
                {"weight": 35, "reps": 9},
                {"weight": 35, "reps": 9},
                {"weight": 35, "reps": 9},
                {"weight": 30, "reps": 15},
            ]},
            {"name": "Biceps Cable",        "exercise_type": "accessory", "order": 4, "sets": [
                {"weight": 50, "reps": 9},
                {"weight": 50, "reps": 9},
                {"weight": 50, "reps": 9},
                {"weight": 50, "reps": 9},
            ]},
            {"name": "Dumbbell Side Crunch","exercise_type": "accessory", "order": 5, "sets": [
                {"weight": 60, "reps": 13},
                {"weight": 60, "reps": 13},
                {"weight": 60, "reps": 13},
                {"weight": 60, "reps": 13},
            ]},
            {"name": "Hip Abductor",        "exercise_type": "accessory", "order": 6, "sets": [
                {"weight": 50, "reps": 12},
                {"weight": 45, "reps": 12},
            ]},
        ],
    },
    {
        "name": "Bench Day",
        "exercises": [
            {"name": "Bench Press",   "exercise_type": "primary",   "order": 0, "sets": [
                {"weight": 107.5, "reps": 3},
                {"weight": 107.5, "reps": 3},
                {"weight": 107.5, "reps": 3},
                {"weight": 107.5, "reps": 3},
            ]},
            {"name": "Pull-Ups",      "exercise_type": "secondary", "order": 1, "sets": [
                {"weight": 0, "reps": 10},
                {"weight": 0, "reps": 9},
                {"weight": 0, "reps": 9},
            ]},
            {"name": "Peck Deck",     "exercise_type": "accessory", "order": 2, "sets": [
                {"weight": 55, "reps": 11},
                {"weight": 55, "reps": 11},
                {"weight": 55, "reps": 11},
                {"weight": 55, "reps": 11},
            ]},
            {"name": "Lateral Raises","exercise_type": "accessory", "order": 3, "sets": [
                {"weight": 16, "reps": 11},
                {"weight": 16, "reps": 11},
                {"weight": 16, "reps": 11},
                {"weight": 16, "reps": 11},
            ]},
            {"name": "Tricep Pushdown","exercise_type": "accessory", "order": 4, "sets": [
                {"weight": 45, "reps": 9},
                {"weight": 45, "reps": 9},
                {"weight": 40, "reps": 10},
                {"weight": 40, "reps": 10},
            ]},
            {"name": "Biceps Bar",        "exercise_type": "accessory", "order": 5, "sets": [
                {"weight": 35, "reps": 8},
                {"weight": 35, "reps": 8},
                {"weight": 35, "reps": 8},
                {"weight": 25, "reps": 16},
            ]},
            {"name": "Leg Raises",    "exercise_type": "accessory", "order": 6, "sets": [
                {"weight": 0, "reps": 13},
                {"weight": 0, "reps": 13},
                {"weight": 0, "reps": 13},
                {"weight": 0, "reps": 13},
            ]},
        ],
    },
    {
        "name": "Squat Day",
        "exercises": [
            {"name": "Squat",               "exercise_type": "primary",   "order": 0, "sets": [
                {"weight": 170, "reps": 3},
                {"weight": 170, "reps": 3},
                {"weight": 170, "reps": 3},
                {"weight": 170, "reps": 3},
            ]},
            {"name": "Leg Extension",       "exercise_type": "accessory", "order": 1, "sets": [
                {"weight": 40, "reps": 9},
                {"weight": 40, "reps": 9},
                {"weight": 40, "reps": 9},
                {"weight": 40, "reps": 9},
            ]},
            {"name": "Hamstring Curls",     "exercise_type": "accessory", "order": 2, "sets": [
                {"weight": 35, "reps": 10},
                {"weight": 35, "reps": 10},
                {"weight": 35, "reps": 10},
                {"weight": 35, "reps": 10},
            ]},
            {"name": "Face Pulls",          "exercise_type": "accessory", "order": 3, "sets": [
                {"weight": 60, "reps": 11},
                {"weight": 60, "reps": 11},
                {"weight": 60, "reps": 11},
                {"weight": 60, "reps": 11},
            ]},
            {"name": "Biceps Cable",        "exercise_type": "accessory", "order": 4, "sets": [
                {"weight": 55, "reps": 9},
                {"weight": 55, "reps": 9},
                {"weight": 55, "reps": 9},
            ]},
            {"name": "Dumbbell Side Crunch","exercise_type": "accessory", "order": 5, "sets": [
                {"weight": 60, "reps": 13},
                {"weight": 60, "reps": 13},
                {"weight": 60, "reps": 13},
                {"weight": 60, "reps": 13},
            ]},
            {"name": "Hip Abductor",        "exercise_type": "accessory", "order": 6, "sets": [
                {"weight": 50, "reps": 12},
                {"weight": 45, "reps": 12},
            ]},
        ],
    },
    {
        "name": "OHP Day",
        "exercises": [
            {"name": "Overhead Press",    "exercise_type": "primary",   "order": 0, "sets": [
                {"weight": 72.5, "reps": 4},
                {"weight": 72.5, "reps": 4},
                {"weight": 77.5, "reps": 3},
                {"weight": 77.5, "reps": 3},
            ]},
            {"name": "Low Rows",          "exercise_type": "secondary", "order": 1, "sets": [
                {"weight": 70, "reps": 10},
                {"weight": 70, "reps": 10},
                {"weight": 70, "reps": 10},
                {"weight": 70, "reps": 10},
            ]},
            {"name": "Incline Bench Press","exercise_type": "secondary", "order": 2, "sets": [
                {"weight": 36, "reps": 10},
                {"weight": 36, "reps": 10},
                {"weight": 36, "reps": 10},
            ]},
            {"name": "Lateral Raises",    "exercise_type": "accessory", "order": 3, "sets": [
                {"weight": 16, "reps": 11},
                {"weight": 16, "reps": 11},
                {"weight": 16, "reps": 11},
                {"weight": 16, "reps": 11},
            ]},
            {"name": "Tricep Pushdown",   "exercise_type": "accessory", "order": 4, "sets": [
                {"weight": 45, "reps": 9},
                {"weight": 45, "reps": 9},
                {"weight": 40, "reps": 10},
                {"weight": 40, "reps": 10},
            ]},
            {"name": "Dumbbell Curl", "exercise_type": "accessory", "order": 5, "sets": [
                {"weight": 22, "reps": 8},
                {"weight": 22, "reps": 9},
                {"weight": 20, "reps": 9},
                {"weight": 20, "reps": 10},
            ]},
            {"name": "Ab Roller",         "exercise_type": "accessory", "order": 6, "sets": [
                {"weight": 0, "reps": 10},
                {"weight": 0, "reps": 10},
                {"weight": 0, "reps": 10},
            ]},
        ],
    },
]


def ensure_exercises():
    lookup = {}
    for data in EXERCISES:
        exercise, created = Exercise.objects.get_or_create(
            name=data["name"],
            is_custom=False,
            user=None,
            defaults={
                "description": data["description"],
                "exercise_type": data["exercise_type"],
                "primary_bodypart": data["primary_bodypart"],
                "secondary_bodypart": data["secondary_bodypart"],
                "alternative_names": [],
            },
        )
        if created:
            print(f"  Created exercise: {exercise.name}")
        else:
            print(f"  Found exercise:   {exercise.name}")
        lookup[exercise.name] = exercise
    return lookup


def create_routines(user, exercise_lookup):
    routines = []
    for routine_data in ROUTINES:
        routine = Routine.objects.create(user=user, name=routine_data["name"])
        print(f"  Created routine: {routine.name}")
        for ex_data in routine_data["exercises"]:
            exercise = exercise_lookup[ex_data["name"]]
            routine_exercise = RoutineExercise.objects.create(
                routine=routine,
                exercise=exercise,
                order=ex_data["order"],
                exercise_type=ex_data["exercise_type"],
            )
            for set_number, set_data in enumerate(ex_data["sets"], start=1):
                RoutineSet.objects.create(
                    routine_exercise=routine_exercise,
                    set_number=set_number,
                    weight=set_data["weight"],
                    reps=set_data["reps"],
                    is_warmup=False,
                )
        routines.append(routine)
    return routines


def create_program(user, routines):
    program = Program.objects.create(
        user=user,
        name="Gainz",
        description="4-day split: Deadlift, Bench, Squat, OHP.",
        is_active=True,
    )
    print(f"  Created program: {program.name}")
    for order, routine in enumerate(routines, start=1):
        ProgramRoutine.objects.create(program=program, routine=routine, order=order)


def run(username):
    user = User.objects.get(username=username)
    with transaction.atomic():
        exercise_lookup = ensure_exercises()
        routines = create_routines(user, exercise_lookup)
        create_program(user, routines)
    print(f"Done — created 4 routines and program 'Gainz' for {username}.")


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "elmar")
