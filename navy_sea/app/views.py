from django.shortcuts import render
from test_data import SHIPS
from test_data import FIGHTS_DATA

def index(request):
    ship_name = request.GET.get('sh')
    first_battle = FIGHTS_DATA[0]
    count_ships = len(first_battle['side1']['ships']) + len(first_battle['side2']['ships'])
    if ship_name:
        ships=[]
        for ship in SHIPS:
            if ship_name.lower() in ship['name'].lower():
                ships.append(ship)
        return render(request, 'index.html', {
            "ships": ships,
            'query': ship_name,
            "fight": 1,
            "count": count_ships
            })
    
    else:
        return render(request, 'index.html', {"ships": SHIPS, "fight": 1, "count": count_ships})

def ship(request, ship_id):
    for boat in SHIPS:
        if boat['id'] == ship_id:
            ship = boat
            break
    return render(request, 'ship.html', {"ship": ship})

def get_ships_by_ids(ship_ids):
    return [ship for ship in SHIPS if ship['id'] in ship_ids]

def fight(request, fight_id):
    fight_data = next((fight for fight in FIGHTS_DATA if fight['id'] == fight_id), None)
    
    if fight_data:
        side1_ships = get_ships_by_ids(fight_data['side1']['ships'])
        side2_ships = get_ships_by_ids(fight_data['side2']['ships'])

        context = {
            'battle_name': fight_data['battle'],
            'side1_name': fight_data['side1']['side_name'],
            'side1_admiral': fight_data['side1']['captain'],
            'side1_ships': side1_ships,
            'side2_name': fight_data['side2']['side_name'],
            'side2_admiral': fight_data['side2']['captain'],
            'side2_ships': side2_ships,
            'battle_result': fight_data['result'],
        }

        return render(request, 'fight.html', context)
