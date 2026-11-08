from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from gyms.models import Gym


def save_gym_info(gym, update_fields):
    gym.info_updated_at = timezone.now()
    fields = list(update_fields)
    fields.append("info_updated_at")
    gym.save(update_fields=fields)


def update_gym_description(gym_id, description):
    gym = Gym.objects.get(pk=gym_id)
    gym.description = description
    save_gym_info(gym, ["description"])
    return gym


def update_gym_vibe(gym_id, vibe):
    gym = Gym.objects.get(pk=gym_id)
    gym.vibe = vibe
    save_gym_info(gym, ["vibe"])
    return gym


def refresh_gym_price_headlines(gym):
    day_pass_price = None
    cheapest_monthly = None
    for row in gym.prices.all():
        count = row.billing_count
        unit = row.billing_unit
        amount = row.amount
        is_day_pass = (unit == "day" and count == 1) or (unit == "session" and count == 1)
        if is_day_pass:
            if day_pass_price is None or amount < day_pass_price:
                day_pass_price = amount
            continue
        if count <= 0 or unit == "session":
            continue
        monthly = None
        value = float(amount)
        if unit == "day":
            monthly = value * 30 / count
        elif unit == "week":
            monthly = value * (52 / 12) / count
        elif unit == "month":
            monthly = value / count
        elif unit == "year":
            monthly = value / (count * 12)
        if monthly is not None and (cheapest_monthly is None or monthly < cheapest_monthly):
            cheapest_monthly = monthly
    if cheapest_monthly is not None:
        monthly_price = Decimal(str(cheapest_monthly)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    else:
        monthly_price = None
    gym.day_pass_price = day_pass_price
    gym.monthly_price = monthly_price
    gym.save(update_fields=["day_pass_price", "monthly_price"])
