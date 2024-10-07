from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import Ship, Fight, FightShip

class Command(BaseCommand):
    help = 'Fills the database with test data: ships, users, fights, and fight-ship relationships'

    def handle(self, *args, **kwargs):
        # Создание пользователей
        for i in range(1, 11):
            password = ''.join(str(x) for x in range(1, i + 1))
            user, created = User.objects.get_or_create(
                username=f'user{i}',
                defaults={'password': password}
            )
            if created:
                user.set_password(password)
                user.save()

                # Назначаем пользователей 9 и 10 администраторами
                if i == 9 or i == 10:
                    user.is_staff = True
                    user.save()

                self.stdout.write(self.style.SUCCESS(f'User "{user.username}" created with password "{password}".'))
            else:
                self.stdout.write(self.style.WARNING(f'User "{user.username}" already exists.'))

        # Создание кораблей
        ships_data = [
            {'ship_name': 'Крейсер Фурутака', 'year': 1922, 'length': 184, 'displacement': 7950, 'country': 'Япония', 'description': 'Тяжёлый крейсер, участвовал в бою у Гуадалканала.', 'photo': 'http://127.0.0.1:9000/navy-sea/1.jpg'},
            {'ship_name': 'Крейсер Кинугаса', 'year': 1926, 'length': 184, 'displacement': 8300, 'country': 'Япония', 'description': 'Крейсер участвовал в боях у Гуадалканала.', 'photo': 'http://127.0.0.1:9000/navy-sea/2.jpg'},
            {'ship_name': 'Крейсер Хелена', 'year': 1939, 'length': 185, 'displacement': 10000, 'country': 'США', 'description': 'Лёгкий крейсер типа «Бруклин», участвовал в боях Второй мировой войны.', 'photo': 'http://127.0.0.1:9000/navy-sea/3.jpg'},
            {'ship_name': 'Эсминец Данкан', 'year': 1942, 'length': 106, 'displacement': 1838, 'country': 'США', 'description': 'Американский эсминец, потоплен в 1942 году.', 'photo': 'http://127.0.0.1:9000/navy-sea/4.jpg'},
            {'ship_name': 'Эсминец Акане', 'year': 1941, 'length': 118, 'displacement': 2500, 'country': 'Япония', 'description': 'Участвовал в бою при Гуадалканале.', 'photo': 'http://127.0.0.1:9000/navy-sea/5.jpg'},
            {'ship_name': 'Крейсер Бостон', 'year': 1943, 'length': 188, 'displacement': 10600, 'country': 'США', 'description': 'Участвовал в боях в Тихом океане.', 'photo': 'http://127.0.0.1:9000/navy-sea/6.jpg'},
            {'ship_name': 'Линкор Ямато', 'year': 1941, 'length': 263, 'displacement': 72000, 'country': 'Япония', 'description': 'Самый мощный линкор в истории.', 'photo': 'http://127.0.0.1:9000/navy-sea/7.jpg'},
            {'ship_name': 'Крейсер Токио', 'year': 1943, 'length': 201, 'displacement': 9000, 'country': 'Япония', 'description': 'Участвовал в боевых действиях.', 'photo': 'http://127.0.0.1:9000/navy-sea/8.jpg'},
            {'ship_name': 'Эсминец Уилкс', 'year': 1942, 'length': 111, 'displacement': 1500, 'country': 'США', 'description': 'Участвовал в бою у Гуадалканала.', 'photo': 'http://127.0.0.1:9000/navy-sea/9.jpg'},
            {'ship_name': 'Подводная лодка Нагацуки', 'year': 1941, 'length': 115, 'displacement': 1800, 'country': 'Япония', 'description': 'Подводная лодка, участвовала в атаке на флоты.', 'photo': 'http://127.0.0.1:9000/navy-sea/10.jpg'},
            {'ship_name': 'Крейсер Шарлотт', 'year': 1944, 'length': 185, 'displacement': 9000, 'country': 'США', 'description': 'Лёгкий крейсер, участвовал в боях на Тихом океане.', 'photo': 'http://127.0.0.1:9000/navy-sea/11.jpg'},
            {'ship_name': 'Линкор Миссури', 'year': 1944, 'length': 270, 'displacement': 45000, 'country': 'США', 'description': 'Линкор, участвовал в боях Второй мировой войны.', 'photo': 'http://127.0.0.1:9000/navy-sea/12.jpg'},
            {'ship_name': 'Крейсер Сент-Луис', 'year': 1945, 'length': 190, 'displacement': 10500, 'country': 'США', 'description': 'Участвовал в бою у Лейте.', 'photo': 'http://127.0.0.1:9000/navy-sea/13.jpg'},
            {'ship_name': 'Крейсер Хайдэ', 'year': 1943, 'length': 185, 'displacement': 10000, 'country': 'Япония', 'description': 'Участвовал в сражениях на Тихом океане.', 'photo': 'http://127.0.0.1:9000/navy-sea/14.jpg'},
            {'ship_name': 'Эсминец Воробей', 'year': 1944, 'length': 103, 'displacement': 2100, 'country': 'США', 'description': 'Эсминец, участвовал в операции Дана.', 'photo': 'http://127.0.0.1:9000/navy-sea/15.jpg'},
            {'ship_name': 'Подводная лодка Акула', 'year': 1943, 'length': 107, 'displacement': 2200, 'country': 'Япония', 'description': 'Подводная лодка, участвовала в атаках на авианосцы.', 'photo': 'http://127.0.0.1:9000/navy-sea/16.jpg'},
            {'ship_name': 'Крейсер Принц Ойген', 'year': 1941, 'length': 210, 'displacement': 12000, 'country': 'Германия', 'description': 'Участвовал в бою при Мидуэе.', 'photo': 'http://127.0.0.1:9000/navy-sea/17.jpg'},
            {'ship_name': 'Корабль Пойнт', 'year': 1942, 'length': 123, 'displacement': 1800, 'country': 'США', 'description': 'Участвовал в боях у Гуадалканала.', 'photo': 'http://127.0.0.1:9000/navy-sea/18.jpg'},
            {'ship_name': 'Эсминец Керри', 'year': 1945, 'length': 109, 'displacement': 2200, 'country': 'США', 'description': 'Эсминец, потоплен в 1945 году.', 'photo': 'http://127.0.0.1:9000/navy-sea/19.jpg'},
            {'ship_name': 'Крейсер Осака', 'year': 1942, 'length': 178, 'displacement': 9700, 'country': 'Япония', 'description': 'Участвовал в бою у Гуадалканала.', 'photo': 'http://127.0.0.1:9000/navy-sea/20.jpg'},
        ]

        for ship_data in ships_data:
            ship, created = Ship.objects.get_or_create(
                ship_name=ship_data['ship_name'],
                defaults={
                    'year': ship_data['year'],
                    'length': ship_data['length'],
                    'displacement': ship_data['displacement'],
                    'country': ship_data['country'],
                    'description': ship_data['description'],
                    'photo': ship_data['photo']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Ship "{ship.ship_name}" added.'))
            else:
                self.stdout.write(self.style.WARNING(f'Ship "{ship.ship_name}" already exists.'))

        # Создание сражений
        fights_data = [
            {'fight_name': 'Бой у мыса Эсперанс', 'result': 'Победа США', 'creator_id': 1},
            {'fight_name': 'Битва при Мидуэе', 'result': 'Победа США', 'creator_id': 2},
            {'fight_name': 'Битва при Гуадалканале', 'result': 'Победа США', 'creator_id': 3},
            {'fight_name': 'Битва за Атолл Тарава', 'result': 'Победа США', 'creator_id': 4},
            {'fight_name': 'Бой у острова Сайпан', 'result': 'Победа США', 'creator_id': 5},
        ]

        for fight_data in fights_data:
            fight, created = Fight.objects.get_or_create(
                fight_name=fight_data['fight_name'],
                result=fight_data['result'],
                creator_id=fight_data['creator_id']
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Fight "{fight.fight_name}" created.'))
            else:
                self.stdout.write(self.style.WARNING(f'Fight "{fight.fight_name}" already exists.'))

        # Связывание кораблей и сражений через таблицу FightShip
        fight_ship_data = [
            {'fight_id': 1, 'ship_id': 1, 'admiral': 'Аритомо Гото'},
            {'fight_id': 1, 'ship_id': 2, 'admiral': 'Аритомо Гото'},
            {'fight_id': 1, 'ship_id': 3, 'admiral': 'Норман Скотт'},
            {'fight_id': 2, 'ship_id': 4, 'admiral': 'Честер Нимиц'},
            {'fight_id': 2, 'ship_id': 5, 'admiral': 'Честер Нимиц'},
            {'fight_id': 3, 'ship_id': 6, 'admiral': 'Элмо Хантер'},
            {'fight_id': 3, 'ship_id': 7, 'admiral': 'Элмо Хантер'},
            {'fight_id': 4, 'ship_id': 8, 'admiral': 'Даниэль Бартон'},
            {'fight_id': 4, 'ship_id': 9, 'admiral': 'Даниэль Бартон'},
            {'fight_id': 5, 'ship_id': 10, 'admiral': 'Уильям Г. Уэст'},
            {'fight_id': 5, 'ship_id': 11, 'admiral': 'Уильям Г. Уэст'},
        ]

        for fs_data in fight_ship_data:
            fight_ship, created = FightShip.objects.get_or_create(
                fight_id=fs_data['fight_id'],
                ship_id=fs_data['ship_id'],
                defaults={'admiral': fs_data['admiral']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'FightShip entry for fight {fs_data["fight_id"]}, ship {fs_data["ship_id"]} created.'))
            else:
                self.stdout.write(self.style.WARNING(f'FightShip entry for fight {fs_data["fight_id"]}, ship {fs_data["ship_id"]} already exists.'))
