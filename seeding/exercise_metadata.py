EXPLICIT_EXERCISE_METADATA = {
    "squat": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "front squat": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "bench press": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "bench": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "incline bench press": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "decline bench press": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "close-grip bench press": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "deadlift": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "sumo deadlift": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "rack pull": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "romanian deadlift": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "good morning": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "overhead press": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "push press": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "barbell row": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "pendlay row": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "t-bar row": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "hip thrust": {"equipment_tags": ["barbell"], "movement_kind": "isolation"},
    "shrugs": {"equipment_tags": ["barbell", "dumbbell"], "movement_kind": "isolation"},
    "upright row": {"equipment_tags": ["barbell", "dumbbell"], "movement_kind": "isolation"},
    "snatch": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "clean and jerk": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "clean": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "power clean": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "hang clean": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "power snatch": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "hang snatch": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "split jerk": {"equipment_tags": ["barbell"], "movement_kind": "compound"},
    "dumbbell bench press": {"equipment_tags": ["dumbbell"], "movement_kind": "compound"},
    "incline dumbbell press": {"equipment_tags": ["dumbbell"], "movement_kind": "compound"},
    "dumbbell row": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation"},
    "bulgarian split squat": {"equipment_tags": ["dumbbell"], "movement_kind": "compound"},
    "walking lunge": {"equipment_tags": ["dumbbell"], "movement_kind": "compound"},
    "arnold press": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation"},
    "dumbbell flye": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation"},
    "dumbbell curl": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation"},
    "hammer curl": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation"},
    "lateral raise": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation"},
    "lateral raises": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation"},
    "front raise": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation"},
    "rear delt flye": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation"},
    "overhead tricep extension": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation"},
    "preacher curl": {"equipment_tags": ["barbell", "dumbbell"], "movement_kind": "isolation"},
    "skull crusher": {"equipment_tags": ["barbell", "dumbbell"], "movement_kind": "isolation"},
    "wrist curl": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation"},
    "pull-up": {"equipment_tags": ["bodyweight"], "movement_kind": "compound"},
    "pull-ups": {"equipment_tags": ["bodyweight"], "movement_kind": "compound"},
    "chin-up": {"equipment_tags": ["bodyweight"], "movement_kind": "compound"},
    "dips": {"equipment_tags": ["bodyweight"], "movement_kind": "compound"},
    "hanging leg raise": {"equipment_tags": ["bodyweight"], "movement_kind": "isolation"},
    "leg raises": {"equipment_tags": ["bodyweight"], "movement_kind": "isolation"},
    "plank": {"equipment_tags": ["bodyweight"], "movement_kind": "isolation"},
    "ab roller": {"equipment_tags": ["bodyweight"], "movement_kind": "isolation"},
    "dumbbell side crunch": {"equipment_tags": ["dumbbell"], "movement_kind": "isolation"},
    "leg press": {"equipment_tags": ["machine"], "movement_kind": "isolation"},
    "leg extension": {"equipment_tags": ["machine"], "movement_kind": "isolation"},
    "hamstring curls": {"equipment_tags": ["machine"], "movement_kind": "isolation"},
    "peck deck": {"equipment_tags": ["machine"], "movement_kind": "isolation"},
    "hip abductor": {"equipment_tags": ["machine"], "movement_kind": "isolation"},
    "seated calf raise": {"equipment_tags": ["machine"], "movement_kind": "isolation"},
    "calf raise": {"equipment_tags": ["machine", "barbell"], "movement_kind": "isolation"},
    "glute ham raise": {"equipment_tags": ["machine"], "movement_kind": "isolation"},
    "cable flye": {"equipment_tags": ["cable"], "movement_kind": "isolation"},
    "cable crunch": {"equipment_tags": ["cable"], "movement_kind": "isolation"},
    "face pulls": {"equipment_tags": ["cable"], "movement_kind": "isolation"},
    "tricep pushdown": {"equipment_tags": ["cable"], "movement_kind": "isolation"},
    "biceps cable": {"equipment_tags": ["cable"], "movement_kind": "isolation"},
    "biceps bar": {"equipment_tags": ["cable"], "movement_kind": "isolation"},
    "low rows": {"equipment_tags": ["cable"], "movement_kind": "isolation"},
    "pallof press": {"equipment_tags": ["cable"], "movement_kind": "isolation"},
}


def infer_exercise_metadata(name):
    key = (name or "").strip().lower()
    if key in EXPLICIT_EXERCISE_METADATA:
        return EXPLICIT_EXERCISE_METADATA[key]

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
    }


def seed_builtin_exercise_metadata():
    from exercises.models import Exercise

    updated = 0
    for exercise in Exercise.objects.filter(is_custom=False):
        metadata = infer_exercise_metadata(exercise.name)
        exercise.equipment_tags = metadata["equipment_tags"]
        exercise.movement_kind = metadata["movement_kind"]
        exercise.save(update_fields=["equipment_tags", "movement_kind"])
        updated += 1
    return updated
