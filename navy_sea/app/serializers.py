from rest_framework import serializers
from django.contrib.auth.models import User
from app.models import Ship, Fight, FightShip

class ShipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ship
        fields = ['id', 'ship_name', 'description', 'year', 'length', 'displacement', 'country', 'photo', 'status']

class FightShipSerializer(serializers.ModelSerializer):
    ship = ShipSerializer(read_only=True)
    
    class Meta:
        model = FightShip
        fields = ['id', 'fight', 'ship', 'admiral']

class FightSerializer(serializers.ModelSerializer):
    ships = FightShipSerializer(many=True, read_only=True, source='fightship_set')

    class Meta:
        model = Fight
        fields = ['id', 'fight_name', 'result', 'status', 'created_at', 'formed_at', 'completed_at', 'creator', 'moderator', 'ships']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']