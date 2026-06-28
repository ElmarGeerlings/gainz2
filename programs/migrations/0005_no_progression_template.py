from decimal import Decimal
from django.db import migrations


def create_no_progression_template(apps, schema_editor):
    ProgressionTemplate = apps.get_model("programs", "ProgressionTemplate")
    ProgressionStep = apps.get_model("programs", "ProgressionStep")
    Program = apps.get_model("programs", "Program")

    template, created = ProgressionTemplate.objects.get_or_create(
        is_system=True,
        name="System: No progression",
        defaults={"notes": ""},
    )
    ProgressionStep.objects.get_or_create(
        template=template,
        order=1,
        defaults={
            "weight_delta": Decimal("0"),
            "reps_delta": 0,
        },
    )

    Program.objects.filter(primary_progression_template__isnull=True).update(
        primary_progression_template=template
    )
    Program.objects.filter(secondary_progression_template__isnull=True).update(
        secondary_progression_template=template
    )
    Program.objects.filter(accessory_progression_template__isnull=True).update(
        accessory_progression_template=template
    )


class Migration(migrations.Migration):

    dependencies = [
        ("programs", "0004_program_accessory_progression_template_and_more"),
    ]

    operations = [
        migrations.RunPython(create_no_progression_template, migrations.RunPython.noop),
    ]
