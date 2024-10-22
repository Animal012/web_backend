from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes, action
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from django.utils import timezone
from django.http import Http404, HttpResponse, JsonResponse
from .models import Ship, Fight, FightShip
from .serializers import *
from django.conf import settings
from minio import Minio
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.response import *
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from drf_yasg.utils import swagger_auto_schema
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from app.permissions import *
import redis
import uuid


session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes        
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)
        return decorated_func
    return decorator

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
        ship_name = request.query_params.get('ship_name')
        ships = self.model_class.objects.filter(status='a')
        if ship_name:
            ships = ships.filter(ship_name__icontains=ship_name)
        user = request.user
        draft_fight_id = None
        count = 0
        if user.is_authenticated:
            draft_fight = Fight.objects.filter(creator=user, status='dr').first()
            if draft_fight:
                draft_fight_id = draft_fight.id
                count = FightShip.objects.filter(fight=draft_fight).count()

        #serializer = self.serializer_class(ships, many=True)
        serializer = self.serializer_class(ships, many=True, context={'is_list': True})
        response_data = {
            'ships': serializer.data,
            'draft_fight_id': draft_fight_id, 
            'count': count
        }
        return Response(response_data)

    @swagger_auto_schema(request_body=serializer_class)
    @method_permission_classes([IsManager])
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

    @swagger_auto_schema(request_body=serializer_class)
    @method_permission_classes([IsManager])
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

    @swagger_auto_schema(request_body=serializer_class)
    def add_to_draft(self, request, pk):
        user = request.user
        if not user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        ship = get_object_or_404(self.model_class, pk=pk)
        draft_fight = Fight.objects.filter(creator=user, status='dr').first()

        if not draft_fight:
            draft_fight = Fight.objects.create(
                creator=user,
                status='dr',
                created_at=timezone.now()
            )
            draft_fight.save()

        if FightShip.objects.filter(fight=draft_fight, ship=ship).exists():
            return Response(data={"error": "Корабль уже добавлен в черновик."}, status=status.HTTP_400_BAD_REQUEST)

        FightShip.objects.create(fight=draft_fight, ship=ship)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(request_body=serializer_class)
    @method_permission_classes([IsManager])
    def put(self, request, pk, format=None):
        ship = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(ship, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @method_permission_classes([IsManager])
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
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user

        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        status = request.query_params.get('status')

        if user.is_authenticated:
            if user.is_staff:
                fights = self.model_class.objects.all()
            else:
                fights = self.model_class.objects.filter(creator=user).exclude(status__in=['dr', 'del'])
        else:
            return Response({"error": "Вы не авторизованы"}, status=401)

        if date_from:
            fights = fights.filter(created_at__gte=date_from)
        if date_to:
            fights = fights.filter(created_at__lte=date_to)

        if status:
            fights = fights.filter(status=status)

        serialized_fights = [
        {
            **self.serializer_class(fight, exclude_ships=True).data,
            'creator': fight.creator.email,
            'moderator': fight.moderator.email if fight.moderator else None
        }
        for fight in fights
        ]

        return Response(serialized_fights)

    @swagger_auto_schema(request_body=serializer_class)
    @method_permission_classes([IsAdmin, IsManager])
    def put(self, request, format=None):
        user = request.user
        required_fields = ['fight_name']
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
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, format=None):
        fight = get_object_or_404(self.model_class, pk=pk)
        if fight.status == 'del':
            return Response({"detail": "Эта заявка удалена и недоступна для просмотра."}, status=403)
        #serializer = self.serializer_class(fight)
        serializer = self.serializer_class(fight, context={'is_fight': True})
        data = serializer.data
        print(fight.creator)
        data['creator'] = fight.creator.email
        if fight.moderator:
            data['moderator'] = fight.moderator.email

        return Response(data)

    def put(self, request, pk, format=None):
        full_path = request.path

        if full_path.endswith('/form/'):
            return self.put_creator(request, pk)
        elif full_path.endswith('/complete/'):
            return self.put_moderator(request, pk)
        elif full_path.endswith('/edit/'):
            return self.put_edit(request, pk)

        return Response({"error": "Неверный путь"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=serializer_class)
    def put_creator(self, request, pk):
        fight = get_object_or_404(self.model_class, pk=pk)
        user = request.user

        if user == fight.creator:

            if 'status' in request.data and request.data['status'] == 'f':
                fight.formed_at = timezone.now()
                updated_data = request.data.copy()

                serializer = self.serializer_class(fight, data=updated_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response({"error": "Создатель может только формировать заявку."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": "Отказано в доступе"}, status=status.HTTP_403_FORBIDDEN)        

    @swagger_auto_schema(request_body=serializer_class)
    @method_permission_classes([IsManager])
    def put_moderator(self, request, pk):
        fight = get_object_or_404(self.model_class, pk=pk)
        user = request.user
        
        if 'status' in request.data:
            status_value = request.data['status']

            # Модератор может завершить ('c') или отклонить ('r') заявку
            if status_value in ['c', 'r']:
                if fight.status != 'f':
                    return Response({"error": "Заявка должна быть сначала сформирована."}, status=status.HTTP_403_FORBIDDEN)

                if status_value == 'c':
                    fight.completed_at = timezone.now()
                    updated_data = request.data.copy()

                serializer = self.serializer_class(fight, data=updated_data, partial=True)
                if serializer.is_valid():
                    serializer.save(moderator=user)
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": "Модератор может только завершить или отклонить заявку."}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=serializer_class)
    def put_edit(self, request, pk):
        fight = get_object_or_404(self.model_class, pk=pk)

        serializer = self.serializer_class(fight, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        fight = get_object_or_404(self.model_class, pk=pk)
        if fight.creator != request.user:
            return Response({"detail": "Только создатель может удалить заказ."}, status=403)
        if fight.status != 'dr':
            return Response({"detail": "Данную заявку нельзя удалить."}, status=403)
        fight.status = 'del'  # Мягкое удаление
        fight.formed_at = timezone.now()
        fight.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# View для FightShip (кораблей в сражениях)
class FightShipDetail(APIView):
    model_class = FightShip
    serializer_class = FightShipSerializer

    @swagger_auto_schema(request_body=serializer_class)
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
class UserViewSet(ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    model_class = CustomUser

    # def get_permissions(self):
    #     # Удаляем ненужные проверки, чтобы любой пользователь мог обновить свой профиль
    #     if self.action == 'create':
    #         return [AllowAny()]
    #     return [IsAuthenticated()]

    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [AllowAny]
        elif self.action in ['list']:
            permission_classes = [IsAdmin | IsManager]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

    def create(self, request):
        if self.model_class.objects.filter(email=request.data['email']).exists():
            return Response({'status': 'Exist'}, status=400)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            self.model_class.objects.create_user(
                email=serializer.data['email'],
                password=serializer.data['password'],
                is_superuser=serializer.data['is_superuser'],
                is_staff=serializer.data['is_staff']
            )
            return Response({'status': 'Success'}, status=200)
        return Response({'status': 'Error', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    # Обновление данных профиля пользователя
    @action(detail=False, methods=['put'], permission_classes=[AllowAny])
    def profile(self, request, format=None):
        user = request.user
        if user is None:
            return Response({'error': 'Вы не авторизованы'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.serializer_class(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Профиль обновлен', 'user': serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@authentication_classes([])
@swagger_auto_schema(method='post', request_body=UserSerializer)
@api_view(['Post'])
@csrf_exempt
@permission_classes([AllowAny])
def login_view(request):
    username = request.data["email"] 
    password = request.data["password"]

    user = authenticate(request, email=username, password=password)
    if user is not None:
        random_key = str(uuid.uuid4())
        session_storage.set(random_key, username)
        response = HttpResponse("{'status': 'ok'}")
        response.set_cookie("session_id", random_key)
        return response
        # login(request, user)
        # return HttpResponse("{'status': 'ok'}")
    else:
        return HttpResponse("{'status': 'error', 'error': 'login failed'}")

def logout_view(request):
    session_id = request.COOKIES.get("session_id")

    if session_id:
        session_storage.delete(session_id)
        response = HttpResponse("{'status': 'ok'}")
        response.delete_cookie("session_id")
        return response
    else:
        return HttpResponse("{'status': 'error', 'error': 'no session found'}")
    # logout(request)
    # return Response({'status': 'Success'})