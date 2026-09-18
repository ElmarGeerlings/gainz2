from django.db import models
from django.conf import settings

# Create your models here.
class Exercise(models.Model):
    """ Represents a single exercise. """
    EXERCISE_TYPE_CHOICES = [
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
        ('accessory', 'Accessory'),
    ]
    
    BODYPART_CHOICES = [
        ('chest', 'Chest'),
        ('upper_chest', 'Upper chest'),
        ('lower_chest', 'Lower chest'),
        ('back', 'Back'),
        ('lats', 'Lats'),
        ('traps', 'Traps'),
        ('lower_back', 'Lower back'),
        ('shoulders', 'Shoulders'),
        ('front_delts', 'Front delts'),
        ('lateral_delts', 'Lateral delts'),
        ('rear_delts', 'Rear delts'),
        ('arms', 'Arms'),
        ('biceps', 'Biceps'),
        ('triceps', 'Triceps'),
        ('forearms', 'Forearms'),
        ('legs', 'Legs'),
        ('quads', 'Quads'),
        ('glutes', 'Glutes'),
        ('hamstrings', 'Hamstrings'),
        ('calves', 'Calves'),
        ('core', 'Core'),
        ('abs', 'Abs'),
        ('obliques', 'Obliques'),
        ('cardio', 'Cardio'),
        ('other', 'Other'),
    ]

    EQUIPMENT_TAG_CHOICES = [
        ('barbell', 'Barbell'),
        ('dumbbell', 'Dumbbell'),
        ('bodyweight', 'Bodyweight'),
        ('machine', 'Machine'),
        ('cable', 'Cable'),
    ]

    MOVEMENT_KIND_CHOICES = [
        ('compound', 'Compound'),
        ('isolation', 'Isolation'),
    ]

    PUSH_PULL_CHOICES = [
        ('push', 'Push'),
        ('pull', 'Pull'),
        ('na', 'N/A'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='custom_exercises'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_custom = models.BooleanField(default=False)  # For user-created exercises
    exercise_type = models.CharField(
        max_length=20,
        choices=EXERCISE_TYPE_CHOICES,
        default='accessory'
    )
    primary_bodypart = models.CharField(
        max_length=20,
        choices=BODYPART_CHOICES,
        null=True,
        blank=True,
        help_text="Primary muscle group targeted by this exercise"
    )
    secondary_bodypart = models.CharField(
        max_length=20,
        choices=BODYPART_CHOICES,
        null=True,
        blank=True,
        help_text="Secondary muscle group targeted by this exercise"
    )
    push_pull = models.CharField(
        max_length=10,
        choices=PUSH_PULL_CHOICES,
        default='na',
    )
    weight_increment = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=0.5,
        help_text="Weight increment in kg for this exercise (0.5, 1, 2.5, or 5)",
    )
    alternative_names = models.JSONField(default=list, blank=True)
    
    equipment_tags = models.JSONField(default=list, blank=True)
    movement_kind = models.CharField(
        max_length=20,
        choices=MOVEMENT_KIND_CHOICES,
        default='compound',
    )

    def __str__(self):
        return self.name
