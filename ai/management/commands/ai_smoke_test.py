from django.core.management.base import BaseCommand

from ai.services import generate_reply


class Command(BaseCommand):
    help = "Smoke test the AI provider with a single prompt"

    def handle(self, *args, **options):
        reply = generate_reply([
            {"role": "user", "content": "Reply with exactly: ok"},
        ])
        self.stdout.write(reply)
