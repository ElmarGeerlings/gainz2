from decimal import Decimal

from django.db import migrations, models


def backfill_weight_increment(apps, schema_editor):
    Exercise = apps.get_model("exercises", "Exercise")
    Exercise.objects.filter(weight_increment__isnull=True).update(
        weight_increment=Decimal("0.5")
    )


class Migration(migrations.Migration):

    dependencies = [
        ("exercises", "0003_alter_exercise_primary_bodypart_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_weight_increment, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="exercise",
            name="weight_increment",
            field=models.DecimalField(
                decimal_places=1,
                default=Decimal("0.5"),
                help_text="Weight increment in kg for this exercise (0.5, 1, 2.5, or 5)",
                max_digits=4,
            ),
        ),
    ]
