from decimal import Decimal

from django.template.loader import render_to_string


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
