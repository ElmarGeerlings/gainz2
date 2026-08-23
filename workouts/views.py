from django.shortcuts import redirect, render

from utils.pagination import paginate

from exercises.bodypart_metadata import BODYPART_DISPLAY_FILTER_CHOICES
from exercises.models import Exercise
from workouts.models import WorkoutExercise
from workouts.services import (
    attach_prior_set_trends,
    attach_rest_times,
    get_workout,
    list_add_exercise_options,
    list_routines_for_choose,
    list_workouts,
    new_workout,
)


def workouts_list_page(req_event):
    program_routines, other_routines = list_routines_for_choose(req_event.user)
    page_obj = paginate(req_event, list_workouts(req_event.user))
    return render(
        req_event,
        "workouts/workouts_list.html",
        {
            "title": "My Workouts",
            "page_obj": page_obj,
            "program_routines": program_routines,
            "other_routines": other_routines,
        },
    )


def new_workout_page(req_event):
    workout = new_workout(req_event.user)
    return redirect("workout-detail", workout_id=workout.pk)


def workout_detail_page(req_event, workout_id):
    user_settings = req_event.user.settings
    workout = attach_rest_times(get_workout(workout_id), user_settings)
    for workout_exercise in workout.exercises.all():
        attach_prior_set_trends(req_event.user, workout_exercise)
    response = {
        "workout": workout,
        "add_exercise_options": list_add_exercise_options(req_event.user),
        "bodypart_choices": BODYPART_DISPLAY_FILTER_CHOICES,
        "exercise_type_choices": [
            {"value": value, "label": label}
            for value, label in WorkoutExercise.EXERCISE_TYPE_CHOICES
        ],
        "title": "Workout Details",
        "user_settings": user_settings,
    }
    return render(req_event, "workouts/workout_detail.html", response)
