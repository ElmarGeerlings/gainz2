EXPLICIT_PRIMARY_BODYPART = {
    "bench press": "chest",
    "incline bench press": "upper_chest",
    "decline bench press": "lower_chest",
    "close-grip bench press": "chest",
    "dumbbell bench press": "chest",
    "incline dumbbell press": "upper_chest",
    "dumbbell curl": "biceps",
    "biceps bar": "biceps",
    "biceps cable": "biceps",
    "hammer curl": "biceps",
    "preacher curl": "biceps",
    "tricep pushdown": "triceps",
    "skull crusher": "triceps",
    "overhead tricep extension": "triceps",
    "lateral raises": "lateral_delts",
    "lateral raise": "lateral_delts",
    "face pulls": "rear_delts",
    "rear delt flye": "rear_delts",
    "leg extension": "quads",
    "hamstring curls": "hamstrings",
    "romanian deadlift": "hamstrings",
    "hip thrust": "glutes",
    "glute ham raise": "hamstrings",
    "chin-up": "lats",
    "pull-ups": "lats",
    "pull-up": "lats",
    "low rows": "back",
    "cable crunch": "abs",
    "leg raises": "abs",
    "ab roller": "abs",
    "dumbbell side crunch": "obliques",
    "calf raise": "calves",
    "seated calf raise": "calves",
    "shrugs": "traps",
    "upright row": "lateral_delts",
    "overhead press": "shoulders",
    "peck deck": "chest",
}


EXPLICIT_EXERCISE_METADATA = {
    "squat": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "na"},
    "front squat": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "na"},
    "bench press": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "push"},
    "bench": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "push"},
    "incline bench press": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "push"},
    "decline bench press": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "push"},
    "close-grip bench press": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "push"},
    "deadlift": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "na"},
    "sumo deadlift": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "na"},
    "rack pull": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "na"},
    "romanian deadlift": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "na"},
    "good morning": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "na"},
    "overhead press": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "push"},
    "push press": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "push"},
    "barbell row": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "pull"},
    "pendlay row": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "pull"},
    "t-bar row": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "pull"},
    "hip thrust": {"equipment_tags": ["barbell"], "movement_kind": "isolation", "push_pull": "na"},
    "shrugs": {"equipment_tags": ["barbell", "dumbbell"], "movement_kind": "isolation", "push_pull": "pull"},
    "upright row": {"equipment_tags": ["barbell", "dumbbell"], "movement_kind": "isolation", "push_pull": "pull"},
    "snatch": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "na"},
    "clean and jerk": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "na"},
    "clean": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "na"},
    "power clean": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "na"},
    "hang clean": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "na"},
    "power snatch": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "na"},
    "hang snatch": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "na"},
    "split jerk": {"equipment_tags": ["barbell"], "movement_kind": "compound", "push_pull": "push"},
    "dumbbell bench press": {"equipment_tags": ["dumbbell"], "movement_kind": "compound", "push_pull": "push"},
    "incline dumbbell press": {"equipment_tags": ["dumbbell"], "movement_kind": "compound", "push_pull": "push"},
    "dumbbell row": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation", "push_pull": "pull"},
    "bulgarian split squat": {"equipment_tags": ["dumbbell"], "movement_kind": "compound", "push_pull": "na"},
    "walking lunge": {"equipment_tags": ["dumbbell"], "movement_kind": "compound", "push_pull": "na"},
    "arnold press": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation", "push_pull": "push"},
    "dumbbell flye": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation", "push_pull": "push"},
    "dumbbell curl": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation", "push_pull": "pull"},
    "hammer curl": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation", "push_pull": "pull"},
    "lateral raise": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation", "push_pull": "na"},
    "lateral raises": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation", "push_pull": "na"},
    "front raise": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation", "push_pull": "na"},
    "rear delt flye": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation", "push_pull": "na"},
    "overhead tricep extension": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation", "push_pull": "push"},
    "preacher curl": {"equipment_tags": ["barbell", "dumbbell"], "movement_kind": "isolation", "push_pull": "pull"},
    "skull crusher": {"equipment_tags": ["barbell", "dumbbell"], "movement_kind": "isolation", "push_pull": "push"},
    "wrist curl": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation", "push_pull": "pull"},
    "pull-up": {"equipment_tags": ["bodyweight"], "movement_kind": "compound", "push_pull": "pull"},
    "pull-ups": {"equipment_tags": ["bodyweight"], "movement_kind": "compound", "push_pull": "pull"},
    "chin-up": {"equipment_tags": ["bodyweight"], "movement_kind": "compound", "push_pull": "pull"},
    "dips": {"equipment_tags": ["bodyweight"], "movement_kind": "compound", "push_pull": "push"},
    "hanging leg raise": {"equipment_tags": ["bodyweight"], "movement_kind": "isolation", "push_pull": "na"},
    "leg raises": {"equipment_tags": ["bodyweight"], "movement_kind": "isolation", "push_pull": "na"},
    "plank": {"equipment_tags": ["bodyweight"], "movement_kind": "isolation", "push_pull": "na"},
    "ab roller": {"equipment_tags": ["bodyweight"], "movement_kind": "isolation", "push_pull": "na"},
    "dumbbell side crunch": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation", "push_pull": "na"},
    "leg press": {"equipment_tags": ["machine"], "movement_kind": "isolation", "push_pull": "na"},
    "leg extension": {"equipment_tags": ["machine"], "movement_kind": "isolation", "push_pull": "na"},
    "hamstring curls": {"equipment_tags": ["machine"], "movement_kind": "isolation", "push_pull": "na"},
    "peck deck": {"equipment_tags": ["machine"], "movement_kind": "isolation", "push_pull": "push"},
    "hip abductor": {"equipment_tags": ["machine"], "movement_kind": "isolation", "push_pull": "na"},
    "seated calf raise": {"equipment_tags": ["machine"], "movement_kind": "isolation", "push_pull": "na"},
    "calf raise": {"equipment_tags": ["machine", "barbell"], "movement_kind": "isolation", "push_pull": "na"},
    "glute ham raise": {"equipment_tags": ["machine"], "movement_kind": "isolation", "push_pull": "na"},
    "cable flye": {"equipment_tags": ["cable"], "movement_kind": "isolation", "push_pull": "push"},
    "cable crunch": {"equipment_tags": ["cable"], "movement_kind": "isolation", "push_pull": "na"},
    "face pulls": {"equipment_tags": ["cable"], "movement_kind": "isolation", "push_pull": "pull"},
    "tricep pushdown": {"equipment_tags": ["cable"], "movement_kind": "isolation", "push_pull": "push"},
    "biceps cable": {"equipment_tags": ["cable"], "movement_kind": "isolation", "push_pull": "pull"},
    "biceps bar": {"equipment_tags": ["cable"], "movement_kind": "isolation", "push_pull": "pull"},
    "low rows": {"equipment_tags": ["cable"], "movement_kind": "isolation", "push_pull": "pull"},
    "pallof press": {"equipment_tags": ["cable"], "movement_kind": "isolation", "push_pull": "na"},
}


def infer_exercise_metadata(name):
    key = (name or "").strip().lower()
    if key in EXPLICIT_EXERCISE_METADATA:
        return dict(EXPLICIT_EXERCISE_METADATA[key])

    equipment_tags = []
    movement_kind = "compound"

    if "dumbbell" in key or "db " in key:
        equipment_tags.append("dumbbell")
    if "barbell" in key or "bar " in key:
        equipment_tags.append("barbell")
    if "cable" in key:
        equipment_tags.append("cable")
    if "machine" in key or "smith" in key:
        equipment_tags.append("machine")

    isolation_words = (
        "curl", "flye", "fly", "raise", "extension", "crunch", "pushdown",
        "kickback", "pullover", "shrug",
    )
    if any(word in key for word in isolation_words):
        movement_kind = "isolation"

    bodyweight_words = (
        "pull-up", "pull up", "chin-up", "chin up", "dip", "plank", "push-up",
        "push up", "leg raise", "ab roller",
    )
    if any(word in key for word in bodyweight_words):
        equipment_tags.append("bodyweight")

    if not equipment_tags:
        if movement_kind == "isolation":
            equipment_tags = ["dumbbell"]
        else:
            equipment_tags = ["barbell"]

    return {
        "equipment_tags": sorted(set(equipment_tags)),
        "movement_kind": movement_kind,
        "push_pull": "na",
    }


def seed_builtin_exercise_metadata():
    from exercises.models import Exercise

    updated = 0
    for exercise in Exercise.objects.filter(is_custom=False):
        metadata = infer_exercise_metadata(exercise.name)
        exercise.equipment_tags = metadata["equipment_tags"]
        exercise.movement_kind = metadata["movement_kind"]
        exercise.push_pull = metadata["push_pull"]
        key = exercise.name.strip().lower()
        update_fields = ["equipment_tags", "movement_kind", "push_pull"]
        if key in EXPLICIT_PRIMARY_BODYPART:
            exercise.primary_bodypart = EXPLICIT_PRIMARY_BODYPART[key]
            update_fields.append("primary_bodypart")
        exercise.save(update_fields=update_fields)
        updated += 1
    return updated
