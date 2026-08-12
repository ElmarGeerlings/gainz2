MIN_EXERCISES_BY_DURATION = {
    "under_45": 4,
    "about_60": 5,
    "75_plus": 6,
}


def validate_exercise_plan_structure(plan, lookup, intake):
    errors = []
    if not isinstance(plan, dict):
        return ["Exercise plan must be an object."]

    routines = plan.get("routines")
    if not isinstance(routines, list) or not routines:
        return ["At least one routine is required."]

    duration = "about_60"
    if intake:
        duration = intake.get("answers", {}).get("duration") or "about_60"
    min_exercises = MIN_EXERCISES_BY_DURATION.get(duration, 5)

    for routine in routines:
        routine_name = (routine.get("name") or "Routine").strip()
        exercises = routine.get("exercises")
        if not isinstance(exercises, list) or not exercises:
            errors.append(f"Routine {routine_name} needs at least one exercise.")
            continue
        if len(exercises) < min_exercises:
            errors.append(
                f"Routine {routine_name} needs at least {min_exercises} exercises."
            )
        for item in exercises:
            exercise_name = (item.get("exercise_name") or "").strip()
            if not exercise_name:
                errors.append(f"Routine {routine_name} has an exercise without a name.")
                continue
            if exercise_name.lower() not in lookup:
                errors.append(f"Unknown exercise: {exercise_name}.")

    goal = None
    if intake:
        goal = intake.get("answers", {}).get("goal")
    if goal == "hypertrophy":
        compound_count = 0
        isolation_count = 0
        for routine in plan.get("routines", []):
            for item in routine.get("exercises", []):
                name = (item.get("exercise_name") or "").strip().lower()
                exercise = lookup.get(name)
                if not exercise:
                    continue
                if exercise.movement_kind == "isolation":
                    isolation_count += 1
                else:
                    compound_count += 1
        if isolation_count <= compound_count:
            errors.append(
                "Hypertrophy plan needs more isolation than compound exercises."
            )

    return errors


def validate_program_loads(draft, intake):
    errors = []
    if not isinstance(draft, dict):
        return ["Draft must be an object."]

    goal = None
    if intake:
        goal = intake.get("answers", {}).get("goal")
    work_sets = []
    primary_work_sets = []

    for routine in draft.get("routines", []):
        for item in routine.get("exercises", []):
            exercise_type = item.get("exercise_type") or "accessory"
            for set_data in item.get("sets", []):
                if set_data.get("is_warmup"):
                    continue
                reps = int(set_data["reps"])
                work_sets.append(reps)
                if exercise_type == "primary":
                    primary_work_sets.append(reps)

            work_set_count = sum(
                1 for set_data in item.get("sets", []) if not set_data.get("is_warmup")
            )
            if work_set_count < 2:
                errors.append(
                    f"{item.get('exercise_name')} needs at least 2 work sets."
                )

    if not work_sets:
        errors.append("Program needs work sets with reps and weight.")
        return errors

    if goal == "hypertrophy":
        in_range = sum(1 for reps in work_sets if 6 <= reps <= 15)
        if in_range / len(work_sets) < 0.7:
            errors.append(
                "Hypertrophy work sets should mostly use 6-15 reps."
            )
    if goal == "strength" and primary_work_sets:
        low_rep = sum(1 for reps in primary_work_sets if reps <= 6)
        if low_rep / len(primary_work_sets) < 0.7:
            errors.append(
                "Strength primary work sets should mostly use 6 reps or fewer."
            )

    return errors
