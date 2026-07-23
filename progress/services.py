from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from django.db.models import F, Max, Min, Sum
from django.utils import timezone
from exercises.models import Exercise
from workouts.models import ExerciseSet


PERIOD_CHOICES = [30, 90, 180, 365]
EXERCISE_TYPE_ORDER = ["primary", "secondary", "accessory"]
EXERCISE_TYPE_LABELS = {
    "primary": "Primary",
    "secondary": "Secondary",
    "accessory": "Accessory",
}


def set_beats(weight, reps, before_weight, before_reps):
    if before_weight is None:
        return True
    weight_value = float(weight)
    before_weight_value = float(before_weight)
    if weight_value > before_weight_value:
        return True
    if weight_value == before_weight_value and int(reps) > int(before_reps):
        return True
    return False


def same_best(weight, reps, best_weight, best_reps):
    return float(weight) == float(best_weight) and int(reps) == int(best_reps)


def format_pr_display(weight, reps):
    weight_value = float(weight)
    if weight_value == int(weight_value):
        weight_str = str(int(weight_value))
    else:
        weight_str = f"{weight_value:.1f}"
    reps_value = int(reps)
    if reps_value > 1:
        return f"{weight_str}kg ({reps_value})"
    return f"{weight_str}kg"


def make_best_record(weight, reps, date):
    return {
        "weight": float(weight),
        "reps": int(reps),
        "date": date,
        "display": format_pr_display(weight, reps),
    }


def update_best_record(current, weight, reps, date):
    if current is None:
        return make_best_record(weight, reps, date)
    if set_beats(weight, reps, current["weight"], current["reps"]):
        return make_best_record(weight, reps, date)
    if same_best(weight, reps, current["weight"], current["reps"]):
        if date < current["date"]:
            return make_best_record(weight, reps, date)
    return current


def empty_exercise_state(name, exercise_type, primary_bodypart):
    return {
        "name": name,
        "exercise_type": exercise_type,
        "primary_bodypart": primary_bodypart,
        "running_best_weight": None,
        "running_best_reps": None,
        "all_time": None,
        "pre_period_best_weight": None,
        "pre_period_best_reps": None,
        "period_best": None,
        "work_set_count": 0,
    }


def aggregate_exercise_prs(user, period_days):
    start_date = timezone.now() - timedelta(days=period_days)
    rows = ExerciseSet.objects.filter(
        workout_exercise__workout__user=user,
        is_warmup=False,
    ).values(
        "workout_exercise__exercise_id",
        "workout_exercise__exercise__name",
        "workout_exercise__exercise__exercise_type",
        "workout_exercise__exercise__primary_bodypart",
        "weight",
        "reps",
        "set_number",
        "workout_exercise__order",
        "workout_exercise__workout__date",
    ).order_by(
        "workout_exercise__workout__date",
        "workout_exercise__order",
        "set_number",
    )

    exercises = {}
    pr_events = []

    for row in rows:
        exercise_id = row["workout_exercise__exercise_id"]
        if exercise_id not in exercises:
            exercises[exercise_id] = empty_exercise_state(
                row["workout_exercise__exercise__name"],
                row["workout_exercise__exercise__exercise_type"],
                row["workout_exercise__exercise__primary_bodypart"],
            )

        state = exercises[exercise_id]
        weight = row["weight"]
        reps = row["reps"]
        workout_date = row["workout_exercise__workout__date"]
        state["work_set_count"] += 1

        if set_beats(
            weight,
            reps,
            state["running_best_weight"],
            state["running_best_reps"],
        ):
            pr_events.append(
                {
                    "exercise_id": exercise_id,
                    "exercise_name": state["name"],
                    "primary_bodypart": state["primary_bodypart"],
                    "weight": float(weight),
                    "reps": int(reps),
                    "date": workout_date,
                    "workout_exercise_order": row["workout_exercise__order"],
                    "set_number": row["set_number"],
                    "display": format_pr_display(weight, reps),
                }
            )
            state["running_best_weight"] = float(weight)
            state["running_best_reps"] = int(reps)

        state["all_time"] = update_best_record(
            state["all_time"],
            weight,
            reps,
            workout_date,
        )

        if workout_date < start_date:
            if set_beats(
                weight,
                reps,
                state["pre_period_best_weight"],
                state["pre_period_best_reps"],
            ):
                state["pre_period_best_weight"] = float(weight)
                state["pre_period_best_reps"] = int(reps)
        else:
            state["period_best"] = update_best_record(
                state["period_best"],
                weight,
                reps,
                workout_date,
            )

    return {
        "start_date": start_date,
        "exercises": exercises,
        "pr_events": pr_events,
    }


def count_period_prs(exercises):
    personal_records = 0
    for state in exercises.values():
        period_best = state["period_best"]
        if period_best is None:
            continue
        if set_beats(
            period_best["weight"],
            period_best["reps"],
            state["pre_period_best_weight"],
            state["pre_period_best_reps"],
        ):
            personal_records += 1
    return personal_records


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


def get_user_lift_history(user):
    work_sets = (
        ExerciseSet.objects.filter(
            workout_exercise__workout__user=user,
            is_warmup=False,
        )
        .select_related(
            "workout_exercise__exercise",
            "workout_exercise__workout",
        )
        .order_by(
            "-workout_exercise__workout__date",
            "-set_number",
        )
    )
    lifts = []
    seen_exercise_ids = set()
    for exercise_set in work_sets:
        exercise_id = exercise_set.workout_exercise.exercise_id
        if exercise_id in seen_exercise_ids:
            continue
        seen_exercise_ids.add(exercise_id)
        lifts.append({
            "name": exercise_set.workout_exercise.exercise.name,
            "weight": float(exercise_set.weight),
            "reps": exercise_set.reps,
        })
    return lifts


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


def get_progress_page_stats(user, period_days):
    start_date = timezone.now() - timedelta(days=period_days)
    sets_in_period = ExerciseSet.objects.filter(
        workout_exercise__workout__user=user,
        workout_exercise__workout__date__gte=start_date,
        is_warmup=False,
    )

    total_workouts = sets_in_period.values("workout_exercise__workout_id").distinct().count()

    volume_agg = sets_in_period.aggregate(total=Sum(F("weight") * F("reps")))
    total_volume = float(volume_agg["total"] or 0)

    pr_data = aggregate_exercise_prs(user, period_days)
    personal_records = count_period_prs(pr_data["exercises"])

    primary_counts = defaultdict(int)
    secondary_counts = defaultdict(int)
    for row in sets_in_period.values(
        "workout_exercise__exercise__primary_bodypart",
        "workout_exercise__exercise__secondary_bodypart",
    ):
        primary = row["workout_exercise__exercise__primary_bodypart"]
        secondary = row["workout_exercise__exercise__secondary_bodypart"]
        if primary:
            primary_counts[primary] += 1
        if secondary:
            secondary_counts[secondary] += 1

    bodypart_labels = dict(Exercise.BODYPART_CHOICES)
    most_trained_bodypart = None
    if primary_counts:
        winner = sorted(
            primary_counts.keys(),
            key=lambda code: (
                -primary_counts[code],
                -secondary_counts.get(code, 0),
                bodypart_labels.get(code, code),
            ),
        )[0]
        most_trained_bodypart = bodypart_labels.get(winner, winner)

    return {
        "total_workouts": total_workouts,
        "total_volume": total_volume,
        "personal_records": personal_records,
        "most_trained_bodypart": most_trained_bodypart,
    }


def get_progress_records(user, period_days):
    pr_data = aggregate_exercise_prs(user, period_days)
    start_date = pr_data["start_date"]
    exercises = pr_data["exercises"]
    pr_events = pr_data["pr_events"]
    bodypart_labels = dict(Exercise.BODYPART_CHOICES)

    total_prs = count_period_prs(exercises)

    bodypart_pr_counts = defaultdict(int)
    for state in exercises.values():
        period_best = state["period_best"]
        if period_best is None:
            continue
        if not set_beats(
            period_best["weight"],
            period_best["reps"],
            state["pre_period_best_weight"],
            state["pre_period_best_reps"],
        ):
            continue
        bodypart_code = state["primary_bodypart"]
        if bodypart_code:
            bodypart_pr_counts[bodypart_code] += 1

    prs_by_bodypart = []
    for code, count in bodypart_pr_counts.items():
        prs_by_bodypart.append(
            {
                "code": code,
                "label": bodypart_labels.get(code, code),
                "count": count,
            }
        )
    prs_by_bodypart.sort(key=lambda row: (-row["count"], row["label"]))

    period_pr_events = [
        event for event in pr_events if event["date"] >= start_date
    ]
    most_recent_pr = None
    if period_pr_events:
        latest = max(
            period_pr_events,
            key=lambda event: (
                event["date"],
                event["workout_exercise_order"],
                event["set_number"],
            ),
        )
        most_recent_pr = {
            "exercise_name": latest["exercise_name"],
            "weight": latest["weight"],
            "reps": latest["reps"],
            "date": latest["date"],
            "display": latest["display"],
        }

    grouped_exercises = {exercise_type: [] for exercise_type in EXERCISE_TYPE_ORDER}
    for exercise_id, state in exercises.items():
        if state["work_set_count"] < 1:
            continue
        period_best = state["period_best"]
        is_period_pr = False
        if period_best is not None and set_beats(
            period_best["weight"],
            period_best["reps"],
            state["pre_period_best_weight"],
            state["pre_period_best_reps"],
        ):
            is_period_pr = True

        exercise_type = state["exercise_type"] or "accessory"
        if exercise_type not in grouped_exercises:
            exercise_type = "accessory"
        grouped_exercises[exercise_type].append(
            {
                "exercise_id": exercise_id,
                "name": state["name"],
                "all_time": state["all_time"],
                "period_best": period_best,
                "is_period_pr": is_period_pr,
            }
        )

    groups = []
    for exercise_type in EXERCISE_TYPE_ORDER:
        type_exercises = grouped_exercises[exercise_type]
        if not type_exercises:
            continue
        type_exercises.sort(key=lambda row: row["name"].lower())
        groups.append(
            {
                "type": exercise_type,
                "label": EXERCISE_TYPE_LABELS[exercise_type],
                "exercises": type_exercises,
            }
        )

    return {
        "period_days": period_days,
        "total_prs": total_prs,
        "prs_by_bodypart": prs_by_bodypart,
        "most_recent_pr": most_recent_pr,
        "groups": groups,
    }
