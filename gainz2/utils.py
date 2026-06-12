import re
from decimal import Decimal

from django.template.loader import render_to_string


def next_numbered_name(prefix, existing_names):
    pattern = re.compile(rf"^{re.escape(prefix)} #(\d+)$")
    max_n = 0
    for name in existing_names:
        match = pattern.match(name)
        if match:
            max_n = max(max_n, int(match.group(1)))
    return f"{prefix} #{max_n + 1}"


def quantize_weight(weight):
    half_steps = (Decimal(weight) * 2).quantize(Decimal("1"))
    return half_steps / Decimal("2")


def render_toast(message, variant="success"):
    return render_to_string(
        "components/toast.html",
        {
            "message": message,
            "variant": variant,
        },
    )
