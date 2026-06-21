from django.shortcuts import render
from exercises.models import Exercise
from progress.services import (
    PERIOD_CHOICES,
    get_progress_records,
    get_user_logged_exercises,
)


def progress_page(req_event):
    period_days = int(req_event.GET.get("period", 90))
    exercise_id = req_event.GET.get("exercise") or None
    chart_type = req_event.GET.get("chart_type", "1rm")
    selected_bodypart = req_event.GET.get("primary_bodypart") or ""

    exercises = get_user_logged_exercises(
        req_event.user,
        selected_bodypart or None,
    )

    response = {
        "title": "Progress",
        "exercises": exercises,
        "selected_exercise_id": exercise_id,
        "selected_bodypart": selected_bodypart,
        "bodypart_choices": Exercise.BODYPART_CHOICES,
        "period_days": period_days,
        "chart_type": chart_type,
        "period_choices": PERIOD_CHOICES,
    }
    return render(req_event, "progress/exercise_progress.html", response)


def progress_records_page(req_event):
    period_days = int(req_event.GET.get("period", 90))
    records = get_progress_records(req_event.user, period_days)
    response = {
        "title": "Personal records",
        "period_days": period_days,
        "period_choices": PERIOD_CHOICES,
        "records": records,
    }
    return render(req_event, "progress/records.html", response)
