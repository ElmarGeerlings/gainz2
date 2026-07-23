import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gainz2.settings")

import django
django.setup()

from decimal import Decimal

from exercises.models import Exercise


EXERCISES = [
    # Back
    {"name": "Sumo Deadlift", "description": "Wide-stance deadlift variant with a more upright torso, shifting more load to the hips and quads than conventional pulling.", "exercise_type": "primary", "primary_bodypart": "back", "secondary_bodypart": "legs", "weight_increment": Decimal("2.5")},
    {"name": "Rack Pull", "description": "Partial deadlift performed from pins or blocks, overloading the lockout portion of the pull.", "exercise_type": "secondary", "primary_bodypart": "back", "secondary_bodypart": "legs", "weight_increment": Decimal("2.5")},
    {"name": "Barbell Row", "description": "Bent-over row with a barbell, building thickness across the mid-back and lats.", "exercise_type": "secondary", "primary_bodypart": "back", "secondary_bodypart": "arms", "weight_increment": Decimal("2.5")},
    {"name": "Pendlay Row", "description": "Strict barbell row starting each rep from a dead stop on the floor, removing momentum from the pull.", "exercise_type": "secondary", "primary_bodypart": "back", "secondary_bodypart": "arms", "weight_increment": Decimal("2.5")},
    {"name": "Dumbbell Row", "description": "Single-arm row supported on a bench, allowing a longer stretch and unilateral loading of the lats.", "exercise_type": "secondary", "primary_bodypart": "back", "secondary_bodypart": "arms", "weight_increment": Decimal("1")},
    {"name": "T-Bar Row", "description": "Chest-supported or landmine row that targets the mid-back with reduced lower-back strain.", "exercise_type": "secondary", "primary_bodypart": "back", "secondary_bodypart": "arms", "weight_increment": Decimal("2.5")},
    {"name": "Chin-Up", "description": "Underhand-grip variant of the pull-up that recruits more biceps alongside the lats.", "exercise_type": "secondary", "primary_bodypart": "back", "secondary_bodypart": "arms", "weight_increment": Decimal("1")},
    {"name": "Shrugs", "description": "Vertical shoulder shrug with a barbell or dumbbells, isolating the upper traps.", "exercise_type": "accessory", "primary_bodypart": "back", "secondary_bodypart": None, "weight_increment": Decimal("2.5")},
    # Chest
    {"name": "Dumbbell Bench Press", "description": "Flat bench press with dumbbells, allowing a greater range of motion and independent arm paths.", "exercise_type": "secondary", "primary_bodypart": "chest", "secondary_bodypart": "shoulders", "weight_increment": Decimal("1")},
    {"name": "Incline Dumbbell Press", "description": "Dumbbell press on an incline bench combining upper-chest emphasis with a free range of motion.", "exercise_type": "secondary", "primary_bodypart": "chest", "secondary_bodypart": "shoulders", "weight_increment": Decimal("1")},
    {"name": "Decline Bench Press", "description": "Bench press on a downward-angled bench that emphasizes the lower chest.", "exercise_type": "secondary", "primary_bodypart": "chest", "secondary_bodypart": "shoulders", "weight_increment": Decimal("2.5")},
    {"name": "Close-Grip Bench Press", "description": "Bench press with a narrow grip that shifts load onto the triceps while still pressing through the chest.", "exercise_type": "secondary", "primary_bodypart": "chest", "secondary_bodypart": "arms", "weight_increment": Decimal("2.5")},
    {"name": "Dips", "description": "Bodyweight press on parallel bars that loads the lower chest and triceps.", "exercise_type": "secondary", "primary_bodypart": "chest", "secondary_bodypart": "arms", "weight_increment": Decimal("1")},
    {"name": "Cable Flye", "description": "Cable crossover bringing the arms together in an arc, isolating the pecs under constant tension.", "exercise_type": "accessory", "primary_bodypart": "chest", "secondary_bodypart": None, "weight_increment": Decimal("0.5")},
    {"name": "Dumbbell Flye", "description": "Flat or incline dumbbell fly that stretches and isolates the chest through a wide arcing motion.", "exercise_type": "accessory", "primary_bodypart": "chest", "secondary_bodypart": None, "weight_increment": Decimal("1")},
    # Legs
    {"name": "Front Squat", "description": "Barbell squat with the bar racked across the front delts, demanding a more upright torso and greater quad emphasis.", "exercise_type": "primary", "primary_bodypart": "legs", "secondary_bodypart": "back", "weight_increment": Decimal("2.5")},
    {"name": "Romanian Deadlift", "description": "Hip-hinge movement performed with minimal knee bend, targeting the hamstrings and glutes.", "exercise_type": "secondary", "primary_bodypart": "legs", "secondary_bodypart": "back", "weight_increment": Decimal("2.5")},
    {"name": "Bulgarian Split Squat", "description": "Single-leg squat with the rear foot elevated, building unilateral leg strength and stability.", "exercise_type": "secondary", "primary_bodypart": "legs", "secondary_bodypart": None, "weight_increment": Decimal("1")},
    {"name": "Hip Thrust", "description": "Barbell hip extension performed with the upper back supported on a bench, directly targeting the glutes.", "exercise_type": "secondary", "primary_bodypart": "legs", "secondary_bodypart": None, "weight_increment": Decimal("2.5")},
    {"name": "Good Morning", "description": "Hip-hinge exercise with the bar on the back, working the hamstrings, glutes, and lower back.", "exercise_type": "accessory", "primary_bodypart": "legs", "secondary_bodypart": "back", "weight_increment": Decimal("2.5")},
    {"name": "Walking Lunge", "description": "Alternating forward-stepping lunge that builds unilateral leg strength and balance.", "exercise_type": "accessory", "primary_bodypart": "legs", "secondary_bodypart": None, "weight_increment": Decimal("1")},
    {"name": "Glute Ham Raise", "description": "Posterior-chain exercise performed on a GHD, isolating the hamstrings through hip and knee extension.", "exercise_type": "accessory", "primary_bodypart": "legs", "secondary_bodypart": None, "weight_increment": Decimal("1")},
    {"name": "Calf Raise", "description": "Standing raise onto the toes that isolates the calves, primarily the gastrocnemius.", "exercise_type": "accessory", "primary_bodypart": "legs", "secondary_bodypart": None, "weight_increment": Decimal("5")},
    {"name": "Seated Calf Raise", "description": "Calf raise performed seated with the knee bent, shifting emphasis onto the soleus.", "exercise_type": "accessory", "primary_bodypart": "legs", "secondary_bodypart": None, "weight_increment": Decimal("5")},
    # Shoulders
    {"name": "Push Press", "description": "Overhead press using a slight leg drive to help move heavier loads than a strict press.", "exercise_type": "secondary", "primary_bodypart": "shoulders", "secondary_bodypart": "legs", "weight_increment": Decimal("2.5")},
    {"name": "Arnold Press", "description": "Dumbbell press that rotates from a palms-in to palms-out grip, hitting all three delt heads through the rotation.", "exercise_type": "accessory", "primary_bodypart": "shoulders", "secondary_bodypart": "arms", "weight_increment": Decimal("1")},
    {"name": "Upright Row", "description": "Vertical pull of a bar or dumbbells to chest height, targeting the side delts and traps.", "exercise_type": "accessory", "primary_bodypart": "shoulders", "secondary_bodypart": "back", "weight_increment": Decimal("2.5")},
    {"name": "Rear Delt Flye", "description": "Bent-over or machine fly isolating the rear delts through horizontal abduction.", "exercise_type": "accessory", "primary_bodypart": "shoulders", "secondary_bodypart": None, "weight_increment": Decimal("1")},
    # Arms
    {"name": "Hammer Curl", "description": "Curl performed with a neutral grip, emphasizing the brachialis and forearm alongside the biceps.", "exercise_type": "accessory", "primary_bodypart": "arms", "secondary_bodypart": None, "weight_increment": Decimal("1")},
    {"name": "Preacher Curl", "description": "Curl performed with the arm braced on an angled pad, removing momentum and isolating the biceps.", "exercise_type": "accessory", "primary_bodypart": "arms", "secondary_bodypart": None, "weight_increment": Decimal("2.5")},
    {"name": "Skull Crusher", "description": "Lying elbow extension with a bar or dumbbells, isolating the triceps.", "exercise_type": "accessory", "primary_bodypart": "arms", "secondary_bodypart": None, "weight_increment": Decimal("2.5")},
    {"name": "Overhead Tricep Extension", "description": "Elbow extension performed overhead, emphasizing the long head of the triceps.", "exercise_type": "accessory", "primary_bodypart": "arms", "secondary_bodypart": None, "weight_increment": Decimal("1")},
    {"name": "Wrist Curl", "description": "Seated curl of the wrist, isolating the forearm flexors.", "exercise_type": "accessory", "primary_bodypart": "arms", "secondary_bodypart": None, "weight_increment": Decimal("1")},
    # Core
    {"name": "Hanging Leg Raise", "description": "Leg raise performed hanging from a bar, adding grip and core-control demands over the lying version.", "exercise_type": "accessory", "primary_bodypart": "core", "secondary_bodypart": None, "weight_increment": Decimal("1")},
    {"name": "Cable Crunch", "description": "Kneeling crunch against a cable, allowing progressive loading of the abs.", "exercise_type": "accessory", "primary_bodypart": "core", "secondary_bodypart": None, "weight_increment": Decimal("0.5")},
    {"name": "Plank", "description": "Isometric hold on the forearms and toes that builds core and anti-extension stability.", "exercise_type": "accessory", "primary_bodypart": "core", "secondary_bodypart": None, "weight_increment": Decimal("1")},
    {"name": "Pallof Press", "description": "Anti-rotation press against a cable or band, training the core to resist twisting.", "exercise_type": "accessory", "primary_bodypart": "core", "secondary_bodypart": None, "weight_increment": Decimal("0.5")},
    # Olympic lifts
    {"name": "Snatch", "description": "Competition lift taking the bar from the floor to overhead in one continuous motion, caught in a deep squat.", "exercise_type": "primary", "primary_bodypart": "legs", "secondary_bodypart": "shoulders", "weight_increment": Decimal("2.5")},
    {"name": "Clean and Jerk", "description": "Two-part competition lift: the bar is pulled to the shoulders, then driven overhead.", "exercise_type": "primary", "primary_bodypart": "legs", "secondary_bodypart": "shoulders", "weight_increment": Decimal("2.5")},
    {"name": "Clean", "description": "Pulling the bar from the floor to the shoulders in one motion, without the following jerk.", "exercise_type": "secondary", "primary_bodypart": "legs", "secondary_bodypart": "back", "weight_increment": Decimal("2.5")},
    {"name": "Power Clean", "description": "Clean caught in a partial squat rather than a full front squat, demanding more pulling power and less mobility.", "exercise_type": "secondary", "primary_bodypart": "legs", "secondary_bodypart": "back", "weight_increment": Decimal("2.5")},
    {"name": "Hang Clean", "description": "Clean initiated from a hang position above the knee rather than the floor, emphasizing the second pull.", "exercise_type": "secondary", "primary_bodypart": "legs", "secondary_bodypart": "back", "weight_increment": Decimal("2.5")},
    {"name": "Power Snatch", "description": "Snatch caught in a partial squat rather than a full overhead squat.", "exercise_type": "secondary", "primary_bodypart": "legs", "secondary_bodypart": "shoulders", "weight_increment": Decimal("2.5")},
    {"name": "Hang Snatch", "description": "Snatch initiated from a hang position above the knee rather than the floor.", "exercise_type": "secondary", "primary_bodypart": "legs", "secondary_bodypart": "shoulders", "weight_increment": Decimal("2.5")},
    {"name": "Split Jerk", "description": "Jerk variation where the lifter splits one foot forward and one back to catch the bar overhead.", "exercise_type": "secondary", "primary_bodypart": "shoulders", "secondary_bodypart": "legs", "weight_increment": Decimal("2.5")},
]


created_count = 0
existing_count = 0
for data in EXERCISES:
    exercise, created = Exercise.objects.get_or_create(
        name=data["name"],
        is_custom=False,
        user=None,
        defaults={
            "description": data["description"],
            "exercise_type": data["exercise_type"],
            "primary_bodypart": data["primary_bodypart"],
            "secondary_bodypart": data["secondary_bodypart"],
            "weight_increment": data["weight_increment"],
            "alternative_names": [],
        },
    )
    if created:
        created_count += 1
        print(f"Created: {exercise.name}")
    else:
        existing_count += 1
        print(f"Exists:  {exercise.name}")

print(f"\nDone. Created {created_count}, already existed {existing_count}.")
