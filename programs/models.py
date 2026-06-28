from django.db import models
from django.conf import settings
from routines.models import Routine

class Program(models.Model):
    """ Represents a collection of routines, forming a structured training program. """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)
    weekly_scheduling = models.BooleanField(default=False)
    last_used_routine = models.ForeignKey(
        "routines.Routine",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    primary_carryover = models.BooleanField(default=False)
    secondary_carryover = models.BooleanField(default=False)
    accessory_carryover = models.BooleanField(default=True)
    primary_progression_template = models.ForeignKey(
        "ProgressionTemplate",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    secondary_progression_template = models.ForeignKey(
        "ProgressionTemplate",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    accessory_progression_template = models.ForeignKey(
        "ProgressionTemplate",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_active:
            # Deactivate other active programs for the same user
            Program.objects.filter(user=self.user, is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


DAYS_OF_WEEK_CHOICES = [
    (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
    (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
]

class ProgramRoutine(models.Model):
    program = models.ForeignKey(Program, related_name='program_routines', on_delete=models.CASCADE)
    routine = models.ForeignKey(Routine, related_name='program_associations', on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    assigned_day = models.IntegerField(choices=DAYS_OF_WEEK_CHOICES, null=True, blank=True)

    class Meta:
        ordering = ['program', 'order', 'assigned_day']
        unique_together = [("program", "routine")]

    def __str__(self):
        day_str = f" (Day: {self.get_assigned_day_display()})" if self.assigned_day is not None else ""
        return f"{self.program.name} - {self.routine.name} (Order: {self.order}){day_str}"


class ProgressionTemplate(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="progression_templates",
    )
    is_system = models.BooleanField(default=False)
    name = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ProgressionStep(models.Model):
    template = models.ForeignKey(
        ProgressionTemplate,
        related_name="steps",
        on_delete=models.CASCADE,
    )
    order = models.PositiveIntegerField()
    weight_delta = models.DecimalField(default=0, max_digits=6, decimal_places=1)
    reps_delta = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]
        unique_together = [("template", "order")]

    def __str__(self):
        return f"Step {self.order} for {self.template.name}"


class ProgramExercise(models.Model):
    program = models.ForeignKey(
        Program,
        related_name="program_exercises",
        on_delete=models.CASCADE,
    )
    routine_exercise = models.ForeignKey(
        "routines.RoutineExercise",
        related_name="program_exercises",
        on_delete=models.CASCADE,
    )
    progression_template = models.ForeignKey(
        ProgressionTemplate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="program_exercises",
    )

    class Meta:
        unique_together = [("program", "routine_exercise")]

    def __str__(self):
        return f"{self.program.name} - {self.routine_exercise}"
