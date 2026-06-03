from django.shortcuts import redirect, render, get_object_or_404

from workouts.models import WorkoutExercise
from workouts.services import (
    get_workout,
    list_add_exercise_options,
    list_workouts,
    start_empty_workout,
)


def workouts_list_page(req_event):
    response = {
        "title": "My Workouts",
        "workouts": list_workouts(req_event.user),
    }
    return render(req_event, "workouts/workouts_list.html", response)


def start_empty_workout_page(req_event):
    workout = start_empty_workout(req_event.user)
    return redirect("workout-detail", workout_id=workout.pk)


def workout_detail_page(req_event, workout_id):
    workout = get_workout(workout_id)
    response = {
        "workout": workout,
        "add_exercise_options": list_add_exercise_options(),
        "exercise_type_choices": [
            {"value": value, "label": label}
            for value, label in WorkoutExercise.EXERCISE_TYPE_CHOICES
        ],
        "title": "Workout Details",
    }
    return render(req_event, "workouts/workout_detail.html", response)
