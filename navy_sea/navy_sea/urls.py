"""
URL configuration for navy_sea project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from app import views
from django.urls import path, include
from rest_framework import routers
from rest_framework import permissions
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

router = routers.DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('ships/', views.ShipList.as_view(), name='ship-list'),
    path('ships/<int:pk>/', views.ShipDetail.as_view(), name='ship-detail'),
    path('ships/<int:pk>/image/', views.ShipDetail.as_view(), name='ship-update-image'),
    path('ships/<int:pk>/draft/', views.ShipDetail.as_view(), name='ship-add-to-draft'),
    path('fights/', views.FightList.as_view(), name='fight-list'),
    path('fights/<int:pk>/edit/', views.FightDetail.as_view(), name='fight-detail-edit'),
    path('fights/<int:pk>/form/', views.FightDetail.as_view(), name='fight-detail-form'),
    path('fights/<int:pk>/complete/', views.FightDetail.as_view(), name='fight-detail-complete'),
    path('fights/<int:pk>/', views.FightDetail.as_view(), name='fight-detail'),
    path('fights/<int:fight_id>/ships/<int:ship_id>/', views.FightShipDetail.as_view(), name='fight-ship-detail'),
    path('login/',  views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('users/auth/', views.UserViewSet.as_view({'post': 'create'}), name='user-register'),
    path('users/profile/', views.UserViewSet.as_view({'put': 'profile'}), name='user-profile'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('csrf/', views.get_csrf_token),
    path('users/check/', views.check_session)
]
