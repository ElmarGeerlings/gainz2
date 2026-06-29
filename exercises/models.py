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
        ('back', 'Back'),
        ('shoulders', 'Shoulders'),
        ('arms', 'Arms'),
        ('legs', 'Legs'),
        ('core', 'Core'),
        ('cardio', 'Cardio'),
        ('other', 'Other'),
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
    weight_increment = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=0.5,
        help_text="Weight increment in kg for this exercise (0.5, 1, 2.5, or 5)",
    )
    alternative_names = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.name