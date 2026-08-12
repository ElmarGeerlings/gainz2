from django.core.management.base import BaseCommand

from seeding.exercise_catalog import seed_builtin_exercises


class Command(BaseCommand):
    help = "Create built-in catalog exercises if they do not exist"

    def handle(self, *args, **options):
        created_count, existing_count = seed_builtin_exercises()
        self.stdout.write(
            f"Done. Created {created_count}, already existed {existing_count}."
        )
