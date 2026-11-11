import datetime
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from gyms.models import Amenity, Gym, GymAmenity, GymPrice, GymRule, Rule

DAY_SCHEDULE = [
    ("Monday", "monday"),
    ("Tuesday", "tuesday"),
    ("Wednesday", "wednesday"),
    ("Thursday", "thursday"),
    ("Friday", "friday"),
    ("Saturday", "saturday"),
    ("Sunday", "sunday"),
]

PERIOD_SINGULAR = {
    "day": "day",
    "week": "week",
    "month": "month",
    "year": "year",
    "session": "session",
}

PERIOD_PLURAL = {
    "day": "days",
    "week": "weeks",
    "month": "months",
    "year": "years",
    "session": "sessions",
}


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


def build_price_plans(gym):
    price_plans = []
    for row in gym.prices.all():
        count = row.billing_count
        unit = row.billing_unit
        normalized = row.amount.normalize()
        if normalized == normalized.to_integral_value():
            amount_text = str(int(normalized))
        else:
            amount_text = format(normalized, "f").rstrip("0").rstrip(".")
        if count == 1:
            read_period = PERIOD_SINGULAR[unit]
        else:
            read_period = f"{count} {PERIOD_PLURAL[unit]}"
        price_plans.append({
            "name": row.title,
            "price": f"€{amount_text}",
            "amount": amount_text,
            "billing_count": count,
            "billing_unit": unit,
            "read_period": read_period,
            "note": row.subtitle,
        })
    return price_plans


def replace_gym_prices(gym_id, rows):
    gym = Gym.objects.get(pk=gym_id)
    with transaction.atomic():
        gym.prices.all().delete()
        sort_order = 0
        for row in rows:
            title = str(row.get("title", "")).strip()
            subtitle = str(row.get("subtitle", "")).strip()
            amount_raw = str(row.get("amount", "")).strip()
            if title == "" and amount_raw == "":
                continue
            amount = Decimal(amount_raw.replace(",", "."))
            billing_count = int(row.get("billing_count") or 1)
            billing_unit = row.get("billing_unit") or "month"
            GymPrice.objects.create(
                gym=gym,
                title=title,
                subtitle=subtitle,
                amount=amount,
                billing_count=billing_count,
                billing_unit=billing_unit,
                sort_order=sort_order,
            )
            sort_order += 1
        refresh_gym_price_headlines(gym)
        save_gym_info(gym, [])
    return Gym.objects.prefetch_related("prices").get(pk=gym_id)


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


def gym_rule_rows(gym):
    state_by_rule_id = {row.rule_id: row.state for row in gym.rules.all()}
    rows = []
    for rule in Rule.objects.order_by("name"):
        rows.append({
            "slug": slugify(rule.name),
            "label": rule.name,
            "state": state_by_rule_id.get(rule.id, "unknown"),
        })
    return rows


def update_gym_rules(gym_id, states):
    gym = Gym.objects.get(pk=gym_id)
    rules_by_slug = {slugify(rule.name): rule for rule in Rule.objects.all()}
    for slug, state in states.items():
        rule = rules_by_slug.get(slug)
        if rule is None:
            continue
        gym_rule, created = GymRule.objects.get_or_create(
            gym=gym,
            rule=rule,
            defaults={"state": state},
        )
        if not created:
            gym_rule.state = state
            gym_rule.save(update_fields=["state"])
    save_gym_info(gym, [])
    return Gym.objects.prefetch_related("rules").get(pk=gym_id)


def gym_amenity_rows(gym):
    selected_amenity_ids = {row.amenity_id for row in gym.amenities.all()}
    rows = []
    for amenity in Amenity.objects.order_by("name"):
        rows.append({
            "slug": slugify(amenity.name),
            "label": amenity.name,
            "selected": amenity.id in selected_amenity_ids,
        })
    return rows


def update_gym_amenities(gym_id, selected_slugs):
    gym = Gym.objects.get(pk=gym_id)
    selected_slug_set = set(selected_slugs)
    existing_ids = {row.amenity_id for row in gym.amenities.all()}
    for amenity in Amenity.objects.order_by("name"):
        slug = slugify(amenity.name)
        selected = slug in selected_slug_set
        has_row = amenity.id in existing_ids
        if selected and not has_row:
            GymAmenity.objects.create(gym=gym, amenity=amenity)
        elif not selected and has_row:
            gym.amenities.filter(amenity_id=amenity.id).delete()
    save_gym_info(gym, [])
    return Gym.objects.prefetch_related("amenities").get(pk=gym_id)


def hour_time_options(for_close=False):
    options = []
    for hour in range(24):
        for minute in (0, 30):
            if for_close and hour == 0 and minute == 0:
                continue
            options.append(f"{hour:02d}:{minute:02d}")
    if for_close:
        options.append("24:00")
    return options


def parse_hour_time(text):
    if not text:
        return None
    if text == "24:00":
        return datetime.time(23, 59, 59)
    return datetime.datetime.strptime(text, "%H:%M").time()


def gym_hours_context(gym):
    tz_name = gym.timezone if gym.timezone else "UTC"
    now = datetime.datetime.now(ZoneInfo(tz_name))
    today_name = now.strftime("%A")
    hours = []
    today_hours = ""
    is_open_now = False
    has_hours = False
    for day_label, prefix in DAY_SCHEDULE:
        closed = getattr(gym, f"{prefix}_closed")
        opening_time = getattr(gym, f"{prefix}_opening_time")
        closing_time = getattr(gym, f"{prefix}_closing_time")
        if closed or opening_time or closing_time:
            has_hours = True
        open_text = opening_time.strftime("%H:%M") if opening_time else ""
        if (
            not closed
            and opening_time == datetime.time(0, 0)
            and closing_time == datetime.time(0, 0)
        ):
            close_text = "24:00"
        elif closing_time == datetime.time(23, 59, 59):
            close_text = "24:00"
        elif closing_time:
            close_text = closing_time.strftime("%H:%M")
        else:
            close_text = ""
        is_today = day_label == today_name
        if closed:
            hours_text = "Closed"
        else:
            hours_text = f"{open_text} – {close_text}"
        hours.append({
            "day": day_label,
            "prefix": prefix,
            "open": open_text,
            "close": close_text,
            "closed": closed,
            "is_today": is_today,
            "hours": hours_text,
        })
        if is_today and has_hours:
            today_hours = hours_text
            if not closed and opening_time and closing_time:
                now_time = now.time()
                if opening_time == datetime.time(0, 0) and closing_time == datetime.time(0, 0):
                    is_open_now = True
                else:
                    is_open_now = opening_time <= now_time < closing_time
    return {
        "hours": hours,
        "has_hours": has_hours,
        "today_hours": today_hours,
        "is_open_now": is_open_now,
        "hour_open_options": hour_time_options(for_close=False),
        "hour_close_options": hour_time_options(for_close=True),
    }


def update_gym_hours(gym_id, schedule):
    gym = Gym.objects.get(pk=gym_id)
    for day_label, prefix in DAY_SCHEDULE:
        day = schedule[prefix]
        if day["closed"]:
            continue
        opening_time = parse_hour_time(day["open"])
        closing_time = parse_hour_time(day["close"])
        if closing_time <= opening_time:
            return {
                "error": f"{day_label}: closing time must be after opening time.",
            }
    update_fields = []
    for day_label, prefix in DAY_SCHEDULE:
        day = schedule[prefix]
        closed = day["closed"]
        setattr(gym, f"{prefix}_closed", closed)
        update_fields.append(f"{prefix}_closed")
        if not closed:
            setattr(gym, f"{prefix}_opening_time", parse_hour_time(day["open"]))
            setattr(gym, f"{prefix}_closing_time", parse_hour_time(day["close"]))
            update_fields.append(f"{prefix}_opening_time")
            update_fields.append(f"{prefix}_closing_time")
    save_gym_info(gym, update_fields)
    return {"gym": gym}
