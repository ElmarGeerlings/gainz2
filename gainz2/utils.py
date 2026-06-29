import re
from decimal import Decimal, ROUND_HALF_UP

from django.template.loader import render_to_string

WEIGHT_INCREMENT_CHOICES = (
    Decimal("0.5"),
    Decimal("1"),
    Decimal("2.5"),
    Decimal("5"),
)

DEFAULT_WEIGHT_INCREMENT = Decimal("0.5")


def next_numbered_name(prefix, existing_names):
    pattern = re.compile(rf"^{re.escape(prefix)} #(\d+)$")
    max_n = 0
    for name in existing_names:
        match = pattern.match(name)
        if match:
            max_n = max(max_n, int(match.group(1)))
    return f"{prefix} #{max_n + 1}"


def parse_weight_increment(value):
    increment = Decimal(str(value))
    if increment in WEIGHT_INCREMENT_CHOICES:
        return increment
    return DEFAULT_WEIGHT_INCREMENT


def quantize_weight(weight, increment=DEFAULT_WEIGHT_INCREMENT):
    increment = parse_weight_increment(increment)
    weight = Decimal(weight)
    steps = (weight / increment).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return steps * increment


def render_toast(message, variant="success"):
    return render_to_string(
        "components/toast.html",
        {
            "message": message,
            "variant": variant,
        },
    )
