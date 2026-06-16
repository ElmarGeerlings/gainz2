from django.conf import settings
from django.db import models


class Routine(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class RoutineExercise(models.Model):
    EXERCISE_TYPE_CHOICES = [
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
        ('accessory', 'Accessory'),
    ]

    routine = models.ForeignKey(Routine, related_name='exercises', on_delete=models.CASCADE)
    exercise = models.ForeignKey('exercises.Exercise', on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    exercise_type = models.CharField(
        max_length=20,
        choices=EXERCISE_TYPE_CHOICES,
        null=True,
        blank=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['order']

    def effective_exercise_type(self):
        return self.exercise_type or self.exercise.exercise_type

    def warmup_set_count(self):
        return sum(1 for s in self.sets.all() if s.is_warmup)

    def work_set_count(self):
        return sum(1 for s in self.sets.all() if not s.is_warmup)

    def total_set_count(self):
        return self.warmup_set_count() + self.work_set_count()

    def __str__(self):
        return f"{self.routine.name} - {self.exercise.name}"


class RoutineSet(models.Model):
    routine_exercise = models.ForeignKey(
        RoutineExercise,
        related_name='sets',
        on_delete=models.CASCADE,
    )
    set_number = models.PositiveIntegerField(default=0)
    weight = models.DecimalField(default=0, max_digits=6, decimal_places=1)
    reps = models.PositiveIntegerField(default=0)
    is_warmup = models.BooleanField(default=False)

    class Meta:
        ordering = ["set_number"]

    def __str__(self):
        return f"Set {self.set_number} for {self.routine_exercise}"
