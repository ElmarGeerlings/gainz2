from django.shortcuts import render
from django.utils.text import slugify

from gyms.models import Equipment, Gym, GymPrice
from gyms.services import build_price_plans, gym_amenity_rows, gym_hours_context, gym_rule_rows

STATUS_SORT_ORDER = {"confirmed": 0, "assumed": 1, "missing": 2}

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

    hours_ctx = gym_hours_context(gym)
    hours = hours_ctx["hours"]
    has_hours = hours_ctx["has_hours"]
    today_hours = hours_ctx["today_hours"]
    is_open_now = hours_ctx["is_open_now"]
    hour_open_options = hours_ctx["hour_open_options"]
    hour_close_options = hours_ctx["hour_close_options"]

    rules = gym_rule_rows(gym)

    amenities = gym_amenity_rows(gym)
    amenities_present = [row["label"] for row in amenities if row["selected"]]

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
        "hour_open_options": hour_open_options,
        "hour_close_options": hour_close_options,
    }
    return render(req_event, "gyms/gym_detail.html", response)
