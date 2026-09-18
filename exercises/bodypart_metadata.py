MIN_EXERCISES_BY_DURATION = {
    "under_45": 4,
    "about_60": 5,
    "75_plus": 6,
}

BODYPART_DISPLAY_GROUPS = {
    "chest": ["chest", "upper_chest", "lower_chest"],
    "back": ["back", "lats", "traps", "lower_back"],
    "shoulders": ["shoulders", "front_delts", "lateral_delts", "rear_delts"],
    "arms": ["arms", "biceps", "triceps", "forearms"],
    "legs": ["legs", "quads", "glutes", "hamstrings", "calves"],
    "core": ["core", "abs", "obliques"],
    "other": ["other", "cardio"],
}

BODYPART_DISPLAY_FILTER_CHOICES = [
    (slug, slug.title()) for slug in BODYPART_DISPLAY_GROUPS
]

TAG_TO_DISPLAY_GROUP = {}
for slug, tags in BODYPART_DISPLAY_GROUPS.items():
    label = slug.title()
    for tag in tags:
        TAG_TO_DISPLAY_GROUP[tag] = label

COVERAGE_GROUP_1_DISPLAY = ["Chest", "Back", "Legs", "Shoulders"]

COVERAGE_GROUP_2_TAGS = ["biceps", "lateral_delts", "rear_delts", "abs"]

COVERAGE_GROUP_3_TAGS = ["quads", "glutes", "hamstrings", "upper_chest", "lats"]

COVERAGE_TIER_2_MIN = 12
COVERAGE_TIER_3_MIN = 24


def coverage_group_number(slots, goal):
    if slots < COVERAGE_TIER_2_MIN:
        return 1
    if slots < COVERAGE_TIER_3_MIN:
        return 2
    if goal == "hypertrophy":
        return 3
    return 2


def required_fine_tags_for_group(group_number):
    tags = []
    if group_number >= 2:
        tags.extend(COVERAGE_GROUP_2_TAGS)
    if group_number >= 3:
        tags.extend(COVERAGE_GROUP_3_TAGS)
    return tags


def build_coverage_prompt_section(intake):
    answers = intake.get("answers") or {}
    goal = answers.get("goal")
    days = int(answers.get("days") or "3")
    duration = answers.get("duration") or "about_60"
    per_day = MIN_EXERCISES_BY_DURATION.get(duration, 5)
    slots = days * per_day
    group = coverage_group_number(slots, goal)
    lines = [
        "Balance pushing and pulling exercises roughly equally across the program.",
        "Include at least one exercise for each bodypart below. These are minimums; "
        "build a coherent program and use other exercises too.",
        "",
        "Required minimum bodyparts (at least one exercise each):",
        "Major: " + ", ".join(COVERAGE_GROUP_1_DISPLAY),
    ]
    fine_tags = required_fine_tags_for_group(group)
    if fine_tags:
        labels = [tag.replace("_", " ") for tag in fine_tags]
        lines.append("Also: " + ", ".join(labels))
    return "\n".join(lines)
