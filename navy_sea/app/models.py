from django.db import models
from django.contrib.auth.models import User


class ShipManager(models.Manager):
    def get_one_ship(self, ship_id):
        return self.get(id=ship_id)


class Ship(models.Model):
    STATUS_CHOICES = [
        ("a", "Active"), 
        ("d", "Deleted")
    ]
    ship_name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    year = models.IntegerField()
    length = models.IntegerField()
    displacement = models.IntegerField()
    country = models.CharField(max_length=255)
    photo = models.CharField(null=True, blank=True, max_length=255)
    status = models.CharField(choices=STATUS_CHOICES, max_length=7, default='a')

    objects = ShipManager()

    def __str__(self):
        return self.ship_name


class FightManager(models.Manager):
    def get_one_fight(self, fight_id):
        return self.get(id=fight_id)

    def get_total_ships(self, fight):
        return FightShip.objects.filter(fight=fight).count()


class Fight(models.Model):
    STATUS_CHOICES = [
        ('dr', "Draft"),
        ('del', "Deleted"), 
        ('f', "Formed"), 
        ('c', "Completed"), 
        ('r', "Rejected")
    ]
    fight_name = models.CharField(max_length=255)
    result = models.CharField(max_length=255)
    status = models.CharField(choices=STATUS_CHOICES, max_length=9, default='dr')
    created_at = models.DateTimeField(auto_now_add=True)
    formed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_fights')
    moderator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_fights')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['creator'], condition=models.Q(status='draft'), name='unique_draft_per_user')
        ]

    objects = FightManager()

    def __str__(self):
        return self.fight_name


class FightShip(models.Model):
    fight = models.ForeignKey(Fight, on_delete=models.CASCADE)
    ship = models.ForeignKey(Ship, on_delete=models.CASCADE)
    admiral = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['fight', 'ship'], name='unique_fight_ship')
        ]
