import datetime
from zoneinfo import ZoneInfo

from django.shortcuts import render
from django.utils.text import slugify

from gyms.models import Amenity, Equipment, Gym, GymPrice, Rule
from gyms.services import build_price_plans

STATUS_SORT_ORDER = {"confirmed": 0, "assumed": 1, "missing": 2}

DAY_SCHEDULE = [
    ("Monday", "monday"),
    ("Tuesday", "tuesday"),
    ("Wednesday", "wednesday"),
    ("Thursday", "thursday"),
    ("Friday", "friday"),
    ("Saturday", "saturday"),
    ("Sunday", "sunday"),
]

def gym_detail_page(req_event):
    tab = req_event.GET.get("tab", "overview")
    if tab not in ("overview", "info", "equipment"):
        tab = "overview"

    gym = Gym.objects.prefetch_related(
        "prices",
        "rules",
        "amenities",
        "equipment_items__equipment",
    ).get(name="Iron District Lisboa")

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
        close_text = closing_time.strftime("%H:%M") if closing_time else ""
        is_today = day_label == today_name
        if closed:
            hours_text = "Closed"
        else:
            hours_text = f"{open_text} – {close_text}"
        hours.append({
            "day": day_label,
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
                is_open_now = opening_time <= now_time < closing_time

    hour_time_options = []
    for hour in range(24):
        for minute in (0, 30):
            hour_time_options.append(f"{hour:02d}:{minute:02d}")
    hour_time_options.append("00:00")

    state_by_rule_id = {row.rule_id: row.state for row in gym.rules.all()}
    rules = []
    for rule in Rule.objects.order_by("name"):
        rules.append({
            "slug": slugify(rule.name),
            "label": rule.name,
            "state": state_by_rule_id.get(rule.id, "unknown"),
        })

    selected_amenity_ids = {row.amenity_id for row in gym.amenities.all()}
    amenities = []
    amenities_present = []
    for amenity in Amenity.objects.order_by("name"):
        selected = amenity.id in selected_amenity_ids
        amenities.append({
            "slug": slugify(amenity.name),
            "label": amenity.name,
            "selected": selected,
        })
        if selected:
            amenities_present.append(amenity.name)

    price_plans = build_price_plans(gym)

    gym_items = list(gym.equipment_items.all())
    on_page_equipment_ids = {row.equipment_id for row in gym_items}
    equipment_groups = []
    for group_slug, group_title in Equipment.GROUP_CHOICES:
        group_rows = [row for row in gym_items if row.equipment.group == group_slug]
        if not group_rows:
            continue
        group_rows.sort(key=lambda row: (STATUS_SORT_ORDER.get(row.status, 9), row.id))
        items = []
        for row in group_rows:
            if row.quantity is None:
                qty = "?"
            else:
                qty = str(row.quantity)
            status_qty = ""
            if row.status == "confirmed" and row.quantity:
                status_qty = qty
            items.append({
                "slug": slugify(row.equipment.name),
                "name": row.equipment.name,
                "quantity": qty,
                "status": row.status,
                "status_word": row.get_status_display(),
                "status_qty": status_qty,
                "bodypart_slug": group_slug,
            })
        equipment_groups.append({
            "title": group_title,
            "filter_slug": group_slug,
            "items": items,
        })
    equipment_catalog_not_on_page = [
        row.name
        for row in Equipment.objects.exclude(id__in=on_page_equipment_ids).order_by("name")
    ]
    equipment_filter_groups = [
        {"slug": group["filter_slug"], "label": group["title"]}
        for group in equipment_groups
    ]

    address_parts = []
    if gym.address_street:
        address_parts.append(gym.address_street)
    city_line = " ".join(
        part for part in (gym.address_postal_code, gym.address_city) if part
    )
    if city_line:
        address_parts.append(city_line)
    if gym.address_country:
        address_parts.append(gym.address_country)
    address = ", ".join(address_parts)
    has_map = gym.latitude is not None and gym.longitude is not None
    maps_search_url = ""
    osm_embed_url = ""
    if address:
        maps_search_url = (
            "https://www.google.com/maps/search/?api=1&query=" + address.replace(" ", "+")
        )
    if has_map:
        lat = float(gym.latitude)
        lng = float(gym.longitude)
        map_bbox_delta = 0.0018
        osm_embed_url = (
            "https://www.openstreetmap.org/export/embed.html?bbox="
            f"{lng - map_bbox_delta}%2C{lat - map_bbox_delta}%2C{lng + map_bbox_delta}%2C{lat + map_bbox_delta}"
            f"&layer=mapnik&marker={lat}%2C{lng}"
        )

    photos = [
        {"src": "img/samples/sample1.jpg", "label": "Main floor"},
        {"src": "img/samples/sample2.png", "label": "Platforms"},
        {"src": "img/samples/sample3.png", "label": "Cardio area"},
    ]
    powerlifting_checklist = [
        {"label": "Power rack or squat rack", "checked": True},
        {"label": "Power bar", "checked": True},
        {"label": "Competition-style bench", "checked": False},
        {"label": "Deadlift platform", "checked": True},
        {"label": "Calibrated plates", "checked": False},
        {"label": "Deadlifts allowed", "checked": True},
        {"label": "Chalk allowed", "checked": True},
        {"label": "Monolift (optional)", "checked": False},
        {"label": "Belt-friendly deadlift area", "checked": True},
    ]
    olympic_checklist = [
        {"label": "Bumper plates", "checked": True},
        {"label": "Platform", "checked": False},
        {"label": "Olympic barbells", "checked": True},
        {"label": "Squat stands or rack", "checked": True},
        {"label": "Chalk allowed", "checked": True},
        {"label": "Drop weights allowed", "checked": False},
    ]
    discipline_scores = [
        {
            "name": "Powerlifting",
            "confirmed": sum(1 for item in powerlifting_checklist if item["checked"]),
            "total": len(powerlifting_checklist),
            "checklist": powerlifting_checklist,
        },
        {
            "name": "Olympic lifting",
            "confirmed": sum(1 for item in olympic_checklist if item["checked"]),
            "total": len(olympic_checklist),
            "checklist": olympic_checklist,
        },
    ]

    response = {
        "title": gym.name,
        "tab": tab,
        "gym": gym,
        "address": address,
        "has_hours": has_hours,
        "has_map": has_map,
        "is_open_now": is_open_now,
        "today_hours": today_hours,
        "photos": photos,
        "hours": hours,
        "rules": rules,
        "amenities": amenities,
        "amenities_present": amenities_present,
        "discipline_scores": discipline_scores,
        "price_plans": price_plans,
        "price_billing_unit_choices": GymPrice.BILLING_UNIT_CHOICES,
        "equipment_groups": equipment_groups,
        "equipment_catalog_not_on_page": equipment_catalog_not_on_page,
        "equipment_filter_groups": equipment_filter_groups,
        "maps_search_url": maps_search_url,
        "osm_embed_url": osm_embed_url,
        "hour_time_options": hour_time_options,
    }
    return render(req_event, "gyms/gym_detail.html", response)
