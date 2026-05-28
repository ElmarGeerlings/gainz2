from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

from accounts.models import User, UserSettings

def create_user_with_settings(username, password, **extra_user_fields):
    user = User.objects.create_user(username=username, password=password, **extra_user_fields)
    UserSettings.objects.create(user=user)
    return user


def register_user(username, password):
    errors = []
    if User.objects.filter(username=username).exists():
        errors.append("Username already taken.")
    if errors:
        return None, errors
    try:
        password_validation.validate_password(password)
    except ValidationError as exc:
        return None, list(exc.messages)
    user = create_user_with_settings(username, password)
    return user, []
