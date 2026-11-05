from django.db import models


class Gym(models.Model):
    VIBE_CHOICES = [
        ("unknown", "Unknown"),
        ("serious", "Serious"),
        ("casual", "Casual"),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    vibe = models.CharField(max_length=20, choices=VIBE_CHOICES, default="unknown")
    address_street = models.CharField(max_length=200, blank=True)
    address_postal_code = models.CharField(max_length=20, blank=True)
    address_city = models.CharField(max_length=100, blank=True)
    address_country = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    timezone = models.CharField(max_length=64, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.CharField(max_length=200, blank=True)
    website = models.CharField(max_length=200, blank=True)
    instagram = models.CharField(max_length=100, blank=True)
    monday_closed = models.BooleanField(default=False)
    monday_opens = models.TimeField(null=True, blank=True)
    monday_closes = models.TimeField(null=True, blank=True)
    tuesday_closed = models.BooleanField(default=False)
    tuesday_opens = models.TimeField(null=True, blank=True)
    tuesday_closes = models.TimeField(null=True, blank=True)
    wednesday_closed = models.BooleanField(default=False)
    wednesday_opens = models.TimeField(null=True, blank=True)
    wednesday_closes = models.TimeField(null=True, blank=True)
    thursday_closed = models.BooleanField(default=False)
    thursday_opens = models.TimeField(null=True, blank=True)
    thursday_closes = models.TimeField(null=True, blank=True)
    friday_closed = models.BooleanField(default=False)
    friday_opens = models.TimeField(null=True, blank=True)
    friday_closes = models.TimeField(null=True, blank=True)
    saturday_closed = models.BooleanField(default=False)
    saturday_opens = models.TimeField(null=True, blank=True)
    saturday_closes = models.TimeField(null=True, blank=True)
    sunday_closed = models.BooleanField(default=False)
    sunday_opens = models.TimeField(null=True, blank=True)
    sunday_closes = models.TimeField(null=True, blank=True)
    info_updated_at = models.DateTimeField(null=True, blank=True)
    equipment_updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name


class GymPrice(models.Model):
    BILLING_UNIT_CHOICES = [
        ("day", "Day"),
        ("week", "Week"),
        ("month", "Month"),
        ("year", "Year"),
        ("session", "Session"),
    ]

    gym = models.ForeignKey(Gym, related_name="prices", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    billing_count = models.PositiveSmallIntegerField(default=1)
    billing_unit = models.CharField(max_length=10, choices=BILLING_UNIT_CHOICES, default="month")
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.gym.name} - {self.title}"

class Rule(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class GymRule(models.Model):
    STATE_CHOICES = [
        ("yes", "Yes"),
        ("no", "No"),
        ("unknown", "Unknown"),
    ]

    gym = models.ForeignKey(Gym, related_name="rules", on_delete=models.CASCADE)
    rule = models.ForeignKey(Rule, related_name="gym_rules", on_delete=models.CASCADE)
    state = models.CharField(max_length=10, choices=STATE_CHOICES, default="unknown")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["gym", "rule"], name="gymrule_gym_rule_uniq"),
        ]

    def __str__(self):
        return f"{self.gym.name} - {self.rule.name}"


class Amenity(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class GymAmenity(models.Model):
    gym = models.ForeignKey(Gym, related_name="amenities", on_delete=models.CASCADE)
    amenity = models.ForeignKey(Amenity, related_name="gym_amenities", on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["gym", "amenity"], name="gymamenity_gym_amenity_uniq"),
        ]

    def __str__(self):
        return f"{self.gym.name} - {self.amenity.name}"


class Equipment(models.Model):
    GROUP_CHOICES = [
        ("essentials", "Essentials"),
        ("cardio", "Cardio"),
        ("chest", "Chest"),
        ("back", "Back"),
        ("shoulders", "Shoulders"),
        ("arms", "Arms"),
        ("legs", "Legs"),
        ("core", "Core"),
    ]

    name = models.CharField(max_length=200, unique=True)
    group = models.CharField(max_length=20, choices=GROUP_CHOICES)

    def __str__(self):
        return self.name


class GymEquipment(models.Model):
    STATUS_CHOICES = [
        ("confirmed", "Confirmed"),
        ("assumed", "Assumed"),
        ("missing", "Missing"),
    ]

    gym = models.ForeignKey(Gym, related_name="equipment_items", on_delete=models.CASCADE)
    equipment = models.ForeignKey(Equipment, related_name="gym_items", on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    quantity = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["gym", "equipment"], name="gymequipment_gym_equipment_uniq"),
        ]

    def __str__(self):
        return f"{self.gym.name} - {self.equipment.name}"

