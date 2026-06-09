from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from exercises.models import Exercise
from exercises.services import group_exercises_by_bodypart, list_exercises_for_user


def exercise_list_page(req_event):
    choice_context = {
        "exercise_type_choices": Exercise.EXERCISE_TYPE_CHOICES,
        "bodypart_choices": Exercise.BODYPART_CHOICES,
    }

    if req_event.headers.get("x-requested-with") == "XMLHttpRequest":
        exercises = list_exercises_for_user(
            req_event.user,
            search_query=req_event.GET.get("search_query", ""),
            exercise_type=req_event.GET.get("exercise_type", ""),
            primary_bodypart=req_event.GET.get("primary_bodypart", ""),
            custom_filter=req_event.GET.get("custom_filter", ""),
        )
        context = {
            "grouped_exercises": group_exercises_by_bodypart(exercises),
        }
        html = render_to_string(
            "exercises/exercise_list_items.html",
            context,
            request=req_event,
        )
        return HttpResponse(html)

    exercises = list_exercises_for_user(
        req_event.user,
        search_query="",
        exercise_type="",
        primary_bodypart="",
        custom_filter="",
    )
    response = {
        "title": "Exercises",
        "grouped_exercises": group_exercises_by_bodypart(exercises),
        **choice_context,
    }
    return render(req_event, "exercises/exercise_list.html", response)
