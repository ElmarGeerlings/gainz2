from django.db import models
from django.conf import settings
from django.utils import timezone
# Create your models here.
class Workout(models.Model):
    """ Represents a single logged workout session. """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now)
    name = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    routine = models.ForeignKey(
        "routines.Routine",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="workouts",
    )

    def __str__(self):
        return self.name


class WorkoutExercise(models.Model):
    """ Represents a specific exercise performed during a logged workout. """
    FEEDBACK_CHOICES = [
        ('increase', 'Increase'),
        ('stay', 'Stay'),
        ('decrease', 'Decrease'),
    ]
    # Existing choices retained from original file
    EXERCISE_TYPE_CHOICES = [
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
        ('accessory', 'Accessory'),
    ]

    workout = models.ForeignKey(Workout, related_name='exercises', on_delete=models.CASCADE)
    exercise = models.ForeignKey('exercises.Exercise', on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    exercise_type = models.CharField(
        max_length=20,
        choices=EXERCISE_TYPE_CHOICES,
        null=True,
        blank=True
    )
    performance_feedback = models.CharField(
        max_length=10,
        choices=FEEDBACK_CHOICES,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['order']

    def effective_exercise_type(self):
        return self.exercise_type or self.exercise.exercise_type

    def warmup_set_count(self):
        return sum(1 for s in self.sets.all() if s.is_warmup)

    def work_set_count(self):
        return sum(1 for s in self.sets.all() if not s.is_warmup)

    def completed_set_count(self):
        return sum(1 for s in self.sets.all() if s.is_completed)

    def total_set_count(self):
        return self.warmup_set_count() + self.work_set_count()

    def __str__(self):
        return f"{self.workout.name} - {self.exercise.name}"


class ExerciseSet(models.Model):
    """ Represents a single set performed for a WorkoutExercise. """
    workout_exercise = models.ForeignKey(WorkoutExercise, related_name='sets', on_delete=models.CASCADE)
    set_number = models.PositiveIntegerField(default=0)
    weight = models.DecimalField(default=0, max_digits=6, decimal_places=1)
    reps = models.PositiveIntegerField(default=0)
    is_warmup = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ["set_number"]

    def __str__(self):
        # Adding a basic __str__ for ExerciseSet
        return f"Set {self.set_number} for {self.workout_exercise}"