from django.db.models import Q
from exercises.models import Exercise


def list_exercises_for_user(
    user,
    *,
    search_query,
    exercise_type,
    primary_bodypart,
    custom_filter,
):
    exercises = Exercise.objects.all()

    if custom_filter == "custom":
        exercises = exercises.filter(is_custom=True, user=user)
    elif custom_filter == "non_custom":
        exercises = exercises.filter(is_custom=False)
    else:
        exercises = exercises.filter(
            Q(is_custom=False) | Q(is_custom=True, user=user)
        )

    if search_query:
        exercises = exercises.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    if exercise_type:
        exercises = exercises.filter(exercise_type=exercise_type)

    if primary_bodypart:
        exercises = exercises.filter(primary_bodypart=primary_bodypart)

    return exercises.select_related("user").order_by("name")


def group_exercises_by_bodypart(exercises):
    grouped = {}
    for exercise in exercises:
        label = exercise.get_primary_bodypart_display()
        if label not in grouped:
            grouped[label] = []
        grouped[label].append(exercise)
    for label in grouped:
        grouped[label] = sorted(
            grouped[label], key=lambda e: (e.is_custom, e.name.lower())
        )
    section_names = sorted(
        grouped.keys(),
        key=lambda name: (name == "Other", name.lower()),
    )
    return [(name, grouped[name]) for name in section_names]


def exercise_name_exists(user, name, exclude_id=None):
    normalized = name.strip()
    built_ins = Exercise.objects.filter(is_custom=False, name__iexact=normalized)
    customs = Exercise.objects.filter(is_custom=True, user=user, name__iexact=normalized)
    if exclude_id is not None:
        built_ins = built_ins.exclude(pk=exclude_id)
        customs = customs.exclude(pk=exclude_id)
    if built_ins.exists():
        return True
    if customs.exists():
        return True
    return False


def get_exercise_for_modal(user, exercise_id):
    exercise = Exercise.objects.get(pk=exercise_id)
    if exercise.is_custom:
        return Exercise.objects.get(pk=exercise_id, is_custom=True, user=user)
    return exercise


def create_custom_exercise(user, attributes):
    name = attributes.get("name", "").strip()
    if exercise_name_exists(user, name):
        return {"error": f'An exercise named "{name}" already exists.'}

    description = attributes.get("description", "")
    primary_bodypart = attributes.get("primary_bodypart") or None
    secondary_bodypart = attributes.get("secondary_bodypart") or None
    exercise_type = attributes.get("exercise_type") or "accessory"

    exercise = Exercise.objects.create(
        user=user,
        name=name,
        description=description,
        is_custom=True,
        exercise_type=exercise_type,
        primary_bodypart=primary_bodypart,
        secondary_bodypart=secondary_bodypart,
    )
    return {"exercise": exercise}


def update_custom_exercise(user, exercise_id, attributes):
    exercise = Exercise.objects.get(pk=exercise_id, is_custom=True, user=user)
    name = attributes.get("name", "").strip()
    if exercise_name_exists(user, name, exclude_id=exercise_id):
        return {"error": f'An exercise named "{name}" already exists.'}

    exercise.name = name
    exercise.description = attributes.get("description", "")
    exercise.primary_bodypart = attributes.get("primary_bodypart") or None
    exercise.secondary_bodypart = attributes.get("secondary_bodypart") or None
    exercise.exercise_type = attributes.get("exercise_type") or "accessory"
    exercise.save()
    return {"exercise": exercise}
