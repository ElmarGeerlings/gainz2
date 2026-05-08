from django.shortcuts import render


def workout_detail_page(req_event, workout_id):
    response = {
        "workout": {
            "id": workout_id,
            "name": "Upper Body A",
            "datetime_display": "Wednesday, May 6, 2026, 18:12",
            "notes": "Focus on controlled reps and full range of motion.",
            "routine_source": {
                "id": 5,
                "name": "Hypertrophy Base",
            },
        },
        "exercises": [
            {
                "id": 101,
                "order": 1,
                "name": "Bench Press",
                "exercise_type": "primary",
                "feedback": "increase",
                "notes": "",
                "weight_increment": "2.5",
                "sets": [
                    {
                        "id": 1001,
                        "reps": 8,
                        "weight": "80.0",
                        "is_amrap": False,
                        "is_warmup": True,
                        "is_completed": True,
                    },
                    {
                        "id": 1002,
                        "reps": 8,
                        "weight": "82.5",
                        "is_amrap": False,
                        "is_warmup": False,
                        "is_completed": False,
                    },
                ],
            },
            {
                "id": 102,
                "order": 2,
                "name": "Incline Dumbbell Press",
                "exercise_type": "secondary",
                "feedback": "stay",
                "notes": "",
                "weight_increment": "2.5",
                "sets": [
                    {
                        "id": 1003,
                        "reps": 10,
                        "weight": "30.0",
                        "is_amrap": False,
                        "is_warmup": False,
                        "is_completed": False,
                    }
                ],
            },
            {
                "id": 103,
                "order": 3,
                "name": "Cable Fly",
                "exercise_type": "accessory",
                "feedback": "",
                "notes": "",
                "weight_increment": "2.5",
                "sets": [],
            },
        ],
        "add_exercise_options": [
            {"id": 1, "name": "Bench Press"},
            {"id": 2, "name": "Incline Dumbbell Press"},
            {"id": 3, "name": "Cable Fly"},
            {"id": 4, "name": "Lateral Raise"},
        ],
        "exercise_type_choices": [
            {"value": "primary", "label": "Primary"},
            {"value": "secondary", "label": "Secondary"},
            {"value": "accessory", "label": "Accessory"},
        ],
        "title": "Workout Details",
    }
    return render(req_event, "workouts/workout_detail.html", response)
