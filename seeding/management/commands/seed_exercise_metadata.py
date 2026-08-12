from django.core.management.base import BaseCommand

from seeding.exercise_metadata import seed_builtin_exercise_metadata


class Command(BaseCommand):
    help = "Seed equipment_tags and movement_kind on built-in exercises"

    def handle(self, *args, **options):
        updated = seed_builtin_exercise_metadata()
        self.stdout.write(f"Updated metadata on {updated} built-in exercise(s).")
