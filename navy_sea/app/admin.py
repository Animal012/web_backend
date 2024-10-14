from django.contrib import admin
from app import models

admin.site.register(models.Fight)
admin.site.register(models.FightShip)
admin.site.register(models.Ship)