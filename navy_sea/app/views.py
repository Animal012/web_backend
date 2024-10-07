from django.shortcuts import render, get_object_or_404, redirect
from .models import Ship, Fight, FightShip
from django.db import connection


def add_ship_to_fight(request, ship_id):
    ship = get_object_or_404(Ship, id=ship_id)
    user = request.user

    try:
        fight = Fight.objects.get(creator=user, status='dr')
    except Fight.DoesNotExist:
        fight = Fight.objects.create(creator=user, status='dr')

    fight_ship, created = FightShip.objects.get_or_create(fight=fight, ship=ship)
    fight_ship.save()

    return redirect('index')

def delete_fight(request, fight_id):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE app_fight SET status = 'del' WHERE id = %s", [fight_id])
    
    return redirect('index')

def index(request):
    ship_name = request.GET.get('ship')
    first_battle = Fight.objects.first()
    count_ships = FightShip.objects.filter(fight=first_battle).count() if first_battle else 0
    user = request.user
    curr_fight = Fight.objects.filter(creator=user, status='dr').first()
    if curr_fight:
        fight_info = {
            'id': curr_fight.id,
            'count': Fight.objects.get_total_ships(curr_fight)
        }
    else:
        fight_info = None

    if ship_name:
        ships = Ship.objects.filter(ship_name__icontains=ship_name)
        return render(request, 'index.html', {
            "ships": ships,
            'query': ship_name,
            "fight": fight_info
        })
    else:
        ships = Ship.objects.all()
        return render(request, 'index.html', {"ships": ships, "fight": fight_info})

def ship(request, ship_id):
    ship = get_object_or_404(Ship, id=ship_id)
    return render(request, 'ship.html', {"ship": ship})

def fight(request, fight_id):
    try:
        curr_fight = Fight.objects.get(id=fight_id)
        if curr_fight.status == 'del':
            raise Fight.DoesNotExist 
    except Fight.DoesNotExist:
        return render(request, 'fight.html', {"error_message": "Нельзя просмотреть сражение."})

    fight_data = get_object_or_404(Fight, id=fight_id)

    battle_ships = Ship.objects.filter(fightship__fight=fight_data)

    battle_admirals = {}
    for fight_ship in FightShip.objects.filter(fight=fight_data):
        battle_admirals[fight_ship.ship.id] = fight_ship.admiral

    context = {
        'fight': fight_data,
        'battle_name': fight_data.fight_name,
        'battle_ships': battle_ships,
        'battle_admirals': battle_admirals,
        'battle_result': fight_data.result
    }
   
    return render(request, 'fight.html', context)

