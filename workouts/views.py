from django.shortcuts import redirect, render

from exercises.models import Exercise
from workouts.models import WorkoutExercise
from workouts.services import (
    attach_rest_times,
    get_workout,
    list_add_exercise_options,
    list_routines_for_choose,
    list_workouts,
    new_workout,
)


def workouts_list_page(req_event):
    program_routines, other_routines = list_routines_for_choose(req_event.user)
    response = {
        "title": "My Workouts",
        "workouts": list_workouts(req_event.user),
        "program_routines": program_routines,
        "other_routines": other_routines,
    }
    return render(req_event, "workouts/workouts_list.html", response)


def new_workout_page(req_event):
    workout = new_workout(req_event.user)
    return redirect("workout-detail", workout_id=workout.pk)


def workout_detail_page(req_event, workout_id):
    user_settings = req_event.user.settings
    workout = attach_rest_times(get_workout(workout_id), user_settings)
    response = {
        "workout": workout,
        "add_exercise_options": list_add_exercise_options(),
        "bodypart_choices": Exercise.BODYPART_CHOICES,
        "exercise_type_choices": [
            {"value": value, "label": label}
            for value, label in WorkoutExercise.EXERCISE_TYPE_CHOICES
        ],
        "title": "Workout Details",
        "user_settings": user_settings,
    }
    return render(req_event, "workouts/workout_detail.html", response)
