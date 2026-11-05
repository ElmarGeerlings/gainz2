import datetime

from django.shortcuts import render

STATUS_SORT_ORDER = {"confirmed": 0, "assumed": 1, "missing": 2}


def equipment_status_parts(status, quantity):
    if status == "confirmed":
        word = "Confirmed"
        if quantity and quantity != "?":
            return word, quantity
        return word, ""
    if status == "missing":
        return "Missing", ""
    return "Assumed", ""


def gym_detail_page(req_event):
    tab = req_event.GET.get("tab", "overview")
    if tab not in ("overview", "info", "equipment"):
        tab = "overview"

    gym = {
        "name": "Iron District Lisboa",
        "city": "Lisbon",
        "address_street": "Rua das Flores 42",
        "address_postal_code": "1200-195",
        "address_city": "Lisboa",
        "address_country": "Portugal",
        "address": "Rua das Flores 42, 1200-195 Lisboa, Portugal",
        "description": (
            "Independent strength-focused gym in the heart of Lisbon. "
            "Two floors: free weights and platforms downstairs, machines and cardio upstairs. "
            "Busy after 17:00 on weekdays; quieter before 10:00."
        ),
        "is_open_now": True,
        "today_hours": "06:00 – 23:00",
        "info_updated_at": "15 Sep 2026",
        "equipment_updated_at": "28 Sep 2026",
        "phone": "+351 21 123 4567",
        "email": "hello@irondistrict.pt",
        "website": "https://example.com/iron-district",
        "instagram": "https://instagram.com/irondistrictlisboa",
        "instagram_handle": "irondistrictlisboa",
        "latitude": 38.7071,
        "longitude": -9.1456,
        "saved": False,
        "has_photos": True,
        "vibe": "unknown",
    }

    hour_time_options = []
    for hour in range(24):
        for minute in (0, 30):
            hour_time_options.append(f"{hour:02d}:{minute:02d}")
    hour_time_options.append(f"00:00")

    photos = [
        {"src": "img/samples/sample1.jpg", "label": "Main floor"},
        {"src": "img/samples/sample2.png", "label": "Platforms"},
        {"src": "img/samples/sample3.png", "label": "Cardio area"},
    ]

    today_name = datetime.date.today().strftime("%A")
    hours = [
        {"day": "Monday", "open": "06:00", "close": "23:00", "closed": False},
        {"day": "Tuesday", "open": "06:00", "close": "23:00", "closed": False},
        {"day": "Wednesday", "open": "06:00", "close": "23:00", "closed": False},
        {"day": "Thursday", "open": "06:00", "close": "23:00", "closed": False},
        {"day": "Friday", "open": "06:00", "close": "23:00", "closed": False},
        {"day": "Saturday", "open": "08:00", "close": "20:00", "closed": False},
        {"day": "Sunday", "open": "08:00", "close": "18:00", "closed": False},
    ]
    for row in hours:
        row["is_today"] = row["day"] == today_name
        if row["closed"]:
            row["hours"] = "Closed"
        else:
            row["hours"] = f"{row['open']} – {row['close']}"

    rules = [
        {"slug": "deadlifts", "label": "Deadlifts allowed", "state": "yes"},
        {"slug": "chalk", "label": "Chalk allowed", "state": "yes"},
        {"slug": "dropping", "label": "Dropping weights allowed", "state": "unknown"},
        {"slug": "filming", "label": "Filming allowed", "state": "no"},
    ]

    amenities = [
        {"slug": "changing-rooms", "label": "Changing rooms", "selected": True},
        {"slug": "showers", "label": "Showers", "selected": True},
        {"slug": "sauna", "label": "Sauna", "selected": False},
        {"slug": "parking", "label": "Parking", "selected": False},
        {"slug": "towel-service", "label": "Towel service", "selected": False},
        {"slug": "lockers", "label": "Lockers", "selected": True},
        {"slug": "wifi", "label": "Wi‑Fi", "selected": False},
        {"slug": "classes", "label": "Group classes", "selected": False},
    ]
    amenities = sorted(amenities, key=lambda row: row["label"].lower())
    amenities_present = sorted(
        [row["label"] for row in amenities if row["selected"]],
        key=str.lower,
    )

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

    price_plans = [
        {"name": "Day pass", "price": "€12", "billing_count": 1, "billing_unit": "day", "read_period": "day", "note": "Includes locker"},
        {"name": "Weekly", "price": "€35", "billing_count": 1, "billing_unit": "week", "read_period": "week", "note": ""},
        {"name": "Fortnight", "price": "€60", "billing_count": 2, "billing_unit": "week", "read_period": "2 weeks", "note": ""},
        {"name": "Monthly", "price": "€49", "billing_count": 1, "billing_unit": "month", "read_period": "month", "note": "No contract"},
        {"name": "Yearly", "price": "€399", "billing_count": 1, "billing_unit": "year", "read_period": "year", "note": ""},
        {"name": "Student monthly", "price": "€39", "billing_count": 1, "billing_unit": "month", "read_period": "month", "note": "Student ID required"},
    ]
    price_headline_day = "€12"
    price_headline_subscription = "€33.25 / mo"

    equipment_groups = [
        {
            "title": "Essentials",
            "filter_slug": "essentials",
            "items": [
                {"slug": "squat-rack", "name": "Squat rack", "quantity": "4", "status": "confirmed"},
                {"slug": "power-rack", "name": "Power rack", "quantity": "2", "status": "confirmed"},
                {"slug": "olympic-barbells", "name": "Olympic barbells", "quantity": "8", "status": "confirmed"},
                {"slug": "flat-bench", "name": "Flat bench", "quantity": "6", "status": "assumed"},
                {"slug": "adjustable-bench", "name": "Adjustable bench", "quantity": "?", "status": "confirmed"},
                {"slug": "deadlift-platform", "name": "Deadlift platform", "quantity": "2", "status": "confirmed"},
                {"slug": "bumper-plates", "name": "Bumper plates", "quantity": "?", "status": "assumed"},
                {"slug": "dumbbells", "name": "Dumbbells", "quantity": "?", "status": "assumed"},
                {"slug": "cable-stations", "name": "Cable stations", "quantity": "3", "status": "confirmed"},
            ],
        },
        {
            "title": "Cardio",
            "filter_slug": "cardio",
            "items": [
                {"slug": "treadmills", "name": "Treadmills", "quantity": "6", "status": "confirmed"},
                {"slug": "rowing-machines", "name": "Rowing machines", "quantity": "4", "status": "assumed"},
                {"slug": "assault-bikes", "name": "Assault bikes", "quantity": "?", "status": "missing"},
            ],
        },
        {
            "title": "Chest",
            "filter_slug": "chest",
            "items": [
                {"slug": "flat-bench-press", "name": "Flat bench press station", "quantity": "2", "status": "confirmed"},
                {"slug": "incline-bench-press", "name": "Incline bench press", "quantity": "1", "status": "assumed"},
                {"slug": "pec-deck", "name": "Pec deck", "quantity": "?", "status": "assumed"},
            ],
        },
        {
            "title": "Back",
            "filter_slug": "back",
            "items": [
                {"slug": "lat-pulldown", "name": "Lat pulldown", "quantity": "2", "status": "confirmed"},
                {"slug": "seated-cable-row", "name": "Seated cable row", "quantity": "2", "status": "assumed"},
                {"slug": "pull-up-station", "name": "Pull-up station", "quantity": "3", "status": "confirmed"},
            ],
        },
        {
            "title": "Shoulders",
            "filter_slug": "shoulders",
            "items": [
                {"slug": "shoulder-press-machine", "name": "Shoulder press machine", "quantity": "1", "status": "assumed"},
            ],
        },
        {
            "title": "Arms",
            "filter_slug": "arms",
            "items": [
                {"slug": "preacher-curl", "name": "Preacher curl bench", "quantity": "1", "status": "missing"},
                {"slug": "triceps-pushdown", "name": "Triceps pushdown station", "quantity": "?", "status": "assumed"},
            ],
        },
        {
            "title": "Legs",
            "filter_slug": "legs",
            "items": [
                {"slug": "leg-press", "name": "Leg press", "quantity": "2", "status": "confirmed"},
                {"slug": "hack-squat", "name": "Hack squat", "quantity": "1", "status": "assumed"},
                {"slug": "leg-extension", "name": "Leg extension", "quantity": "2", "status": "assumed"},
                {"slug": "leg-curl", "name": "Leg curl", "quantity": "2", "status": "assumed"},
            ],
        },
        {
            "title": "Core",
            "filter_slug": "core",
            "items": [
                {"slug": "ab-crunch", "name": "Ab crunch machine", "quantity": "1", "status": "assumed"},
            ],
        },
    ]

    for group in equipment_groups:
        group["items"].sort(key=lambda item: STATUS_SORT_ORDER.get(item["status"], 9))
        for item in group["items"]:
            word, qty = equipment_status_parts(item["status"], item["quantity"])
            item["status_word"] = word
            item["status_qty"] = qty
            item["bodypart_slug"] = group["filter_slug"]

    equipment_on_page = set()
    for group in equipment_groups:
        for item in group["items"]:
            equipment_on_page.add(item["name"])

    equipment_catalog = [
        "GHD machine",
        "Belt squat",
        "Sled track",
        "Smith machine",
        "Hammer Strength chest press",
        "Reverse hyper",
        "Landmine station",
        "Kettlebells",
    ]
    equipment_catalog_not_on_page = [
        name for name in equipment_catalog if name not in equipment_on_page
    ]

    maps_search_url = (
        "https://www.google.com/maps/search/?api=1&query="
        + gym["address"].replace(" ", "+")
    )
    lat = gym["latitude"]
    lng = gym["longitude"]
    map_bbox_delta = 0.0018
    osm_embed_url = (
        "https://www.openstreetmap.org/export/embed.html?bbox="
        f"{lng - map_bbox_delta}%2C{lat - map_bbox_delta}%2C{lng + map_bbox_delta}%2C{lat + map_bbox_delta}"
        f"&layer=mapnik&marker={lat}%2C{lng}"
    )

    equipment_filter_groups = [{"slug": group["filter_slug"], "label": group["title"]} for group in equipment_groups]

    vibe_labels = {"unknown": "Unknown", "serious": "Serious", "casual": "Casual"}
    gym["vibe_label"] = vibe_labels.get(gym["vibe"], "Unknown")

    response = {
        "title": gym["name"],
        "tab": tab,
        "gym": gym,
        "photos": photos,
        "hours": hours,
        "rules": rules,
        "amenities": amenities,
        "amenities_present": amenities_present,
        "discipline_scores": discipline_scores,
        "price_plans": price_plans,
        "price_headline_day": price_headline_day,
        "price_headline_subscription": price_headline_subscription,
        "equipment_groups": equipment_groups,
        "equipment_catalog_not_on_page": equipment_catalog_not_on_page,
        "equipment_filter_groups": equipment_filter_groups,
        "maps_search_url": maps_search_url,
        "osm_embed_url": osm_embed_url,
        "hour_time_options": hour_time_options,
    }
    return render(req_event, "gyms/gym_detail.html", response)
