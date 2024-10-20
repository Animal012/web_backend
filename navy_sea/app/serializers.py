from rest_framework import serializers
from django.contrib.auth.models import User
from app.models import Ship, Fight, FightShip

class ShipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ship
        fields = ['id', 'ship_name', 'description', 'year', 'length', 'displacement', 'country', 'photo']
    
    def __init__(self, *args, **kwargs):
        # Получаем контекст запроса
        super(ShipSerializer, self).__init__(*args, **kwargs)
        context = self.context

        # Если это запрос списка, исключаем поле description
        if context.get('is_list', False):
            self.fields.pop('description')

    def get_fields(self):
        fields = super().get_fields()

        # Если это запрос сражения, отображаем только ship_name и photo
        if self.context.get('is_fight', False):
            return {
                'ship_name': fields['ship_name'],
                'photo': fields['photo']
            }

        return fields

class FightShipSerializer(serializers.ModelSerializer):
    ship = ShipSerializer(read_only=True)
    
    class Meta:
        model = FightShip
        fields = ['ship', 'admiral']

class FightSerializer(serializers.ModelSerializer):
    ships = FightShipSerializer(many=True, read_only=True, source='fightship_set')

    class Meta:
        model = Fight
        fields = ['id', 'fight_name', 'result', 'status', 'created_at', 'formed_at', 'completed_at', 'creator', 'moderator', 'ships']

    def __init__(self, *args, **kwargs):
        # Получаем контекст из сериализатора
        exclude_ships = kwargs.pop('exclude_ships', False)
        super(FightSerializer, self).__init__(*args, **kwargs)

        # Убираем поле 'ships' если exclude_ships=True
        if exclude_ships:
            self.fields.pop('ships', None)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']