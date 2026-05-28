from decimal import Decimal, ROUND_HALF_UP

from django import template
from django.utils import timezone

register = template.Library()


@register.filter(name="datetime_format")
def datetime_format(value):
    local = timezone.localtime(value)
    return local.strftime("%A, %B %d, %Y, %H:%M")


@register.filter(name="weight_display")
def weight_display(value):
    d = Decimal(value).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    if d == d.to_integral_value():
        return str(int(d))
    return format(d, "f")