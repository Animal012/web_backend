from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from django.utils import timezone
from django.http import Http404
from .models import Ship, Fight, FightShip
from .serializers import ShipSerializer, FightSerializer, FightShipSerializer, UserSerializer
from django.conf import settings
from minio import Minio
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.response import *
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout


class UserSingleton:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            try:
                cls._instance = User.objects.get(id=11)
            except User.DoesNotExist:
                cls._instance = None
        return cls._instance

    @classmethod
    def clear_instance(cls, user):
        pass


def process_file_upload(file_object: InMemoryUploadedFile, client, image_name):
    try:
        client.put_object('navy-sea', image_name, file_object, file_object.size)
        return f"http://localhost:9000/navy-sea/{image_name}"
    except Exception as e:
        return {"error": str(e)}


def add_pic(new_ship, pic):
    client = Minio(
        endpoint=settings.AWS_S3_ENDPOINT_URL,
        access_key=settings.AWS_ACCESS_KEY_ID,
        secret_key=settings.AWS_SECRET_ACCESS_KEY,
        secure=settings.MINIO_USE_SSL
    )
    img_obj_name = f"{new_ship.id}.jpg"

    if not pic:
        return {"error": "Нет файла для изображения."}

    result = process_file_upload(pic, client, img_obj_name)

    if 'error' in result:
        return {"error": result['error']}

    return result


# View для Ship (кораблей)
class ShipList(APIView):
    model_class = Ship
    serializer_class = ShipSerializer

    def get(self, request, format=None):
        ships = self.model_class.objects.filter(status='a')
        user = UserSingleton.get_instance()
        draft_fight_id = None
        if user:
            draft_fight = Fight.objects.filter(creator=user, status='dr').first()
            if draft_fight:
                draft_fight_id = draft_fight.id

        serializer = self.serializer_class(ships, many=True)
        response_data = {
            'ships': serializer.data,
            'draft_fight_id': draft_fight_id 
        }
        return Response(response_data)

    def post(self, request, format=None):
        pic = request.FILES.get("photo")
        data = request.data.copy()
        data.pop('photo', None)
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            ship = serializer.save()
            if pic:
                pic_url = add_pic(ship, pic)
                if 'error' in pic_url:
                    return Response({"error": pic_url['error']}, status=status.HTTP_400_BAD_REQUEST)
                ship.photo = pic_url
                ship.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShipDetail(APIView):
    model_class = Ship
    serializer_class = ShipSerializer

    def get(self, request, pk, format=None):
        ship = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(ship)
        return Response(serializer.data)

    def post(self, request, pk, format=None):
        if request.path.endswith('/image/'):
            return self.update_image(request, pk)
        elif request.path.endswith('/draft/'):
            return self.add_to_draft(request, pk)
        raise Http404

    def update_image(self, request, pk):
        ship = get_object_or_404(self.model_class, pk=pk)
        pic = request.FILES.get("photo")

        if not pic:
            return Response({"error": "Файл изображения не предоставлен."}, status=status.HTTP_400_BAD_REQUEST)

        if ship.photo:
            client = Minio(
                endpoint=settings.AWS_S3_ENDPOINT_URL,
                access_key=settings.AWS_ACCESS_KEY_ID,
                secret_key=settings.AWS_SECRET_ACCESS_KEY,
                secure=settings.MINIO_USE_SSL
            )
            old_img_name = ship.photo.split('/')[-1]
            try:
                client.remove_object('navy-sea', old_img_name)
            except Exception as e:
                return Response({"error": f"Ошибка при удалении старого изображения: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        pic_url = add_pic(ship, pic)
        if 'error' in pic_url:
            return Response({"error": pic_url['error']}, status=status.HTTP_400_BAD_REQUEST)

        ship.photo = pic_url
        ship.save()

        return Response({"message": "Изображение успешно обновлено.", "photo_url": pic_url}, status=status.HTTP_200_OK)

    def add_to_draft(self, request, pk):
        user = UserSingleton.get_instance()
        if not user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        ship = get_object_or_404(self.model_class, pk=pk)
        draft_fight = Fight.objects.filter(creator=user, status='dr').first()

        if not draft_fight:
            draft_fight = Fight.objects.create(
                table_number = 1,
                creator=user,
                status='dr',
                created_at=timezone.now()
            )
            draft_fight.save()

        if FightShip.objects.filter(fight=draft_fight, ship=ship).exists():
            return Response(data={"error": "Корабль уже добавлено в черновик."}, status=status.HTTP_400_BAD_REQUEST)

        FightShip.objects.create(fight=draft_fight, ship=ship, count=1)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def put(self, request, pk, format=None):
        ship = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(ship, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        ship = get_object_or_404(self.model_class, pk=pk)
        if ship.photo:
            client = Minio(
                endpoint=settings.AWS_S3_ENDPOINT_URL,
                access_key=settings.AWS_ACCESS_KEY_ID,
                secret_key=settings.AWS_SECRET_ACCESS_KEY,
                secure=settings.MINIO_USE_SSL
            )
            image_name = ship.photo.split('/')[-1]
            try:
                client.remove_object('navy-sea', image_name)
            except Exception as e:
                return Response({"error": f"Ошибка при удалении изображения: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        ship.status = 'd'  # Мягкое удаление
        ship.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# View для Fight (сражений)
class FightList(APIView):
    model_class = Fight
    serializer_class = FightSerializer

    def get(self, request, format=None):
        user = UserSingleton.get_instance()

        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        status = request.query_params.get('status')

        fights = self.model_class.objects.filter(creator=user).exclude(status__in=['dr', 'del'])

        if date_from:
            fights = fights.filter(created_at__gte=date_from)
        if date_to:
            fights = fights.filter(created_at__lte=date_to)

        if status:
            fights = fights.filter(status=status)

        serialized_fights = [
            {**self.serializer_class(fight).data, 'creator': fight.creator.username, 'moderator': fight.moderator.username}
            for fight in fights
        ]

        return Response(serialized_fights)

    def put(self, request, format=None):
        user = UserSingleton.get_instance()
        required_fields = ['table_number']  #????????????????????????????
        for field in required_fields:
            if field not in request.data or request.data[field] is None:
                return Response({field: 'Это поле обязательно для заполнения.'}, status=status.HTTP_400_BAD_REQUEST)
            
        fight_id = request.data.get('id')
        if fight_id:
            fight = get_object_or_404(self.model_class, pk=fight_id)
            serializer = self.serializer_class(fight, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(moderator=user)
                return Response(serializer.data)
            
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            fight = serializer.save(creator=user) 
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FightDetail(APIView):
    model_class = Fight
    serializer_class = FightSerializer

    def get(self, request, pk, format=None):
        fight = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(fight)
        data = serializer.data
        data['creator'] = fight.creator.username
        if fight.moderator:
            data['moderator'] = fight.moderator.username 

        return Response(data)

    def put(self, request, pk, format=None):
        fight = get_object_or_404(self.model_class, pk=pk)
        user = UserSingleton.get_instance()

        if 'status' in request.data:
            status_value = request.data['status']
            if status_value not in ['f', 'r']:
                return Response({"error": "Неверный статус."}, status=status.HTTP_400_BAD_REQUEST)
            dinner.completed_at = timezone.now()
            
            serializer = self.serializer_class(dinner, data=updated_data, partial=True)
            if serializer.is_valid():
                serializer.save(moderator=user)
                return Response(serializer.data)

        # Если статус не был передан, пробуем обновить остальные данные
        serializer = self.serializer_class(fight, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(moderator=user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        fight = get_object_or_404(self.model_class, pk=pk)
        fight.status = 'del'  # Мягкое удаление
        fight.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# View для FightShip (кораблей в сражениях)
class FightShipDetail(APIView):
    model_class = FightShip
    serializer_class = FightShipSerializer

    def put(self, request, fight_id, ship_id, format=None):
        fight = get_object_or_404(Fight, pk=fight_id)
        fight_ship = get_object_or_404(self.model_class, fight=fight, ship__id=ship_id)
        
        serializer = self.serializer_class(fight_ship, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, fight_id, ship_id, format=None):
        fight = get_object_or_404(Fight, pk=fight_id)
        fight_ship = get_object_or_404(self.model_class, fight=fight, ship__id=ship_id)
        fight_ship.delete()
        return Response({"message": "Корабль успешно удален из сражения"}, status=status.HTTP_204_NO_CONTENT)


# View для User (пользователей)
class UserView(APIView):
    def post(self, request, action, format=None):
        if action == 'register':
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                validated_data = serializer.validated_data
                user = User(
                    username=validated_data['username'],
                    email=validated_data['email']
                )
                user.set_password(request.data.get('password'))
                user.save()
                return Response({'message': 'Регистрация успешна'}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif action == 'authenticate':
            username = request.data.get('username')
            password = request.data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                user_data = UserSerializer(user).data
                return Response({
                    'message': 'Аутентификация успешна',
                    'user': user_data
                }, status=status.HTTP_200_OK)
            return Response({'error': 'Неправильное имя пользователя или пароль'}, status=status.HTTP_400_BAD_REQUEST)

        elif action == 'logout':
            return Response({'message': 'Вы вышли из системы'}, status=status.HTTP_200_OK)

        return Response({'error': 'Неверное действие'}, status=status.HTTP_400_BAD_REQUEST)

    # Обновление данных профиля пользователя
    def put(self, request, action, format=None):
        if action == 'profile':
            user = UserSingleton.get_instance()
            if user is None:
                return Response({'error': 'Вы не авторизованы'}, status=status.HTTP_401_UNAUTHORIZED)
            
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'message': 'Профиль обновлен', 'user': serializer.data}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': 'Некорректное действие'}, status=status.HTTP_400_BAD_REQUEST)