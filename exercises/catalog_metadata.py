EQUIPMENT_TAGS = {"barbell", "dumbbell", "bodyweight", "machine", "cable"}

EQUIPMENT_FILTER_BY_INTAKE = {
    "full_gym": None,
    "dumbbells_bar": {"barbell", "dumbbell", "bodyweight"},
    "bodyweight": {"bodyweight"},
}


def allowed_equipment_for_intake(intake):
    if not intake:
        return None
    equipment = intake.get("answers", {}).get("equipment")
    return EQUIPMENT_FILTER_BY_INTAKE.get(equipment)


def exercise_passes_equipment_filter(exercise, allowed_tags):
    if not allowed_tags:
        return True
    tags = exercise.equipment_tags or []
    if not tags:
        return True
    return bool(set(tags) & allowed_tags)
