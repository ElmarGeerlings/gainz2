from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    is_demo = models.BooleanField(default=False)


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')

    smartchange_enabled = models.BooleanField(default=False)
    smartchange_warmup = models.BooleanField(default=True)
    set_carryover = models.BooleanField(default=True)

    notification_sound_enabled = models.BooleanField(default=True)
    notification_vibration_enabled = models.BooleanField(default=True)

    primary_rest_time = models.IntegerField(default=180)
    secondary_rest_time = models.IntegerField(default=120)
    accessory_rest_time = models.IntegerField(default=60)

    def __str__(self):
        return f"Settings for {self.user}"
