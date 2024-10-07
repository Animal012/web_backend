"""
URL configuration for navy_sea project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name="index"),
    path('ships/<int:ship_id>', views.ship, name="ship"),
    path('fight/<int:fight_id>', views.fight, name="fight"),
    path('add-to-fight/<int:ship_id>', views.add_ship_to_fight, name="add_ship_to_fight"),
    path('delete-fight/<int:fight_id>', views.delete_fight, name="delete_fight")
]
