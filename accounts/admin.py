from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import User, UserSettings


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    pass


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'set_carryover',
        'smartchange_enabled',
        'smartchange_warmup',
        'primary_rest_time',
        'secondary_rest_time',
        'accessory_rest_time',
        'notification_sound_enabled',
        'notification_vibration_enabled',
    )
