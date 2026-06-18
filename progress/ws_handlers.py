from django.template.loader import render_to_string
from progress.services import (
    get_exercise_chart_data,
    get_exercise_sets_for_date,
    get_user_logged_exercises,
)


def handle_refresh_progress_exercise_options(user, attributes):
    primary_bodypart = attributes.get("primary_bodypart") or None
    selected_exercise_id = attributes.get("data-selected-exercise-id") or ""
    html = render_to_string(
        "progress/exercise_select.html",
        {
            "exercises": get_user_logged_exercises(user, primary_bodypart),
            "selected_exercise_id": selected_exercise_id,
        },
    )
    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "target": "#progress-exercise-select-wrap",
            "html": html,
        },
    }


def parse_rep_range_attributes(attributes):
    min_reps_raw = attributes.get("min_reps") or None
    max_reps_raw = attributes.get("max_reps") or None
    if min_reps_raw is None or max_reps_raw is None:
        return None, None
    return int(min_reps_raw), int(max_reps_raw)


def handle_progress_chart_data(user, attributes):
    exercise_id = attributes.get("exercise") or None
    period_days = int(attributes.get("period") or 90)
    rep_range = attributes.get("rep_range") or ""
    chart_type = attributes.get("chart_type") or "1rm"
    min_reps, max_reps = parse_rep_range_attributes(attributes)
    result = get_exercise_chart_data(
        user,
        exercise_id,
        period_days,
        rep_range,
        chart_type,
        min_reps=min_reps,
        max_reps=max_reps,
    )
    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "data": result["points"],
            "rep_bounds": result["rep_bounds"],
        },
    }


def handle_progress_workout_sets(user, attributes):
    date_str = attributes.get("data-date")
    exercise_id = int(attributes.get("data-exercise-id"))
    sets = get_exercise_sets_for_date(user, date_str, exercise_id)
    html = render_to_string("progress/workout_sets.html", {"sets": sets})
    return {
        "status": 200,
        "headers": [],
        "json_content": {
            "target": "#progress-sets-detail",
            "html": html,
        },
    }
