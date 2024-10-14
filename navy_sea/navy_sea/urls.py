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

router = routers.DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('ships/', views.ShipList.as_view(), name='ship-list'),
    path('ships/<int:pk>/', views.ShipDetail.as_view(), name='ship-detail'),
    path('ships/<int:pk>/image/', views.ShipDetail.as_view(), name='ship-update-image'),
    path('ships/<int:pk>/draft/', views.ShipDetail.as_view(), name='ship-add-to-draft'),
    path('fights/', views.FightList.as_view(), name='fight-list'),
    path('fights/<int:pk>/', views.FightDetail.as_view(), name='fight-detail'),
    path('fights/<int:fight_id>/ships/<int:ship_id>/', views.FightShipDetail.as_view(), name='fight-ship-detail'),
    path('users/<str:action>/', views.UserView.as_view(), name='user-action'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('admin/', admin.site.urls),
]
