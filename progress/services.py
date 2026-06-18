from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from django.db.models import Max, Min
from django.utils import timezone
from exercises.models import Exercise
from workouts.models import ExerciseSet


def estimate_1rm(weight, reps):
    weight = Decimal(weight)
    reps = int(reps)
    if reps == 1:
        return weight
    if 2 <= reps <= 5:
        return weight * (Decimal("1") + Decimal("0.033") * reps)
    return weight / (Decimal("1.0278") - Decimal("0.0278") * reps)


def get_user_logged_exercises(user, primary_bodypart=None):
    exercises = Exercise.objects.filter(
        workoutexercise__workout__user=user,
        workoutexercise__sets__isnull=False,
    )
    if primary_bodypart:
        exercises = exercises.filter(primary_bodypart=primary_bodypart)
    return exercises.distinct().order_by("name")


def get_exercise_chart_data(
    user,
    exercise_id,
    period_days,
    rep_range,
    chart_type,
    min_reps=None,
    max_reps=None,
):
    if not exercise_id:
        return {"points": [], "rep_bounds": None}

    end_date = timezone.now()
    start_date = end_date - timedelta(days=period_days)

    sets_query = ExerciseSet.objects.filter(
        workout_exercise__workout__user=user,
        workout_exercise__exercise_id=exercise_id,
        workout_exercise__workout__date__gte=start_date,
        is_warmup=False,
    ).select_related("workout_exercise__workout")

    rep_agg = sets_query.aggregate(min_reps=Min("reps"), max_reps=Max("reps"))
    all_min_reps = rep_agg["min_reps"]
    all_max_reps = rep_agg["max_reps"]
    if all_min_reps is None or all_max_reps is None:
        rep_bounds = None
    else:
        rep_bounds = {"min": int(all_min_reps), "max": int(all_max_reps)}

    if min_reps is not None and max_reps is not None:
        if rep_bounds and min_reps == rep_bounds["min"] and max_reps == rep_bounds["max"]:
            pass
        else:
            sets_query = sets_query.filter(reps__range=(min_reps, max_reps))

    days = defaultdict(
        lambda: {
            "estimates": [],
            "volume": Decimal("0"),
        }
    )

    for set_obj in sets_query.order_by(
        "workout_exercise__workout__date",
        "set_number",
    ):
        day = set_obj.workout_exercise.workout.date.date()
        entry = days[day]

        volume = Decimal(set_obj.weight) * Decimal(set_obj.reps)
        entry["volume"] += volume

        entry["estimates"].append(float(estimate_1rm(set_obj.weight, set_obj.reps)))

    chart_type = (chart_type or "1rm").lower()
    points = []
    for day, entry in sorted(days.items()):
        estimate_value = max(entry["estimates"]) if entry["estimates"] else None
        volume_total = float(entry["volume"])
        y_value = volume_total if chart_type == "volume" else estimate_value
        points.append(
            {
                "date": day.isoformat(),
                "y": y_value,
                "estimated_1rm": estimate_value,
                "volume": volume_total,
            }
        )

    return {"points": points, "rep_bounds": rep_bounds}


def get_exercise_sets_for_date(user, date_str, exercise_id):
    sets = ExerciseSet.objects.filter(
        workout_exercise__workout__user=user,
        workout_exercise__workout__date__date=date_str,
        workout_exercise__exercise_id=exercise_id,
        is_warmup=False,
    ).order_by("workout_exercise__workout__date", "set_number")

    best_1rm = None
    for set_obj in sets:
        estimate = estimate_1rm(set_obj.weight, set_obj.reps)
        if estimate is not None:
            estimate_value = float(estimate)
            if best_1rm is None or estimate_value > best_1rm:
                best_1rm = estimate_value

    result = []
    for set_obj in sets:
        estimate = estimate_1rm(set_obj.weight, set_obj.reps)
        estimate_value = float(estimate) if estimate is not None else None
        result.append(
            {
                "set_number": set_obj.set_number,
                "weight": float(set_obj.weight),
                "reps": set_obj.reps,
                "estimated_1rm": estimate_value,
                "is_best": estimate_value is not None and estimate_value == best_1rm,
            }
        )
    return result
