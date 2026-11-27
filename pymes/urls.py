from django.urls import path, include
from rest_framework import routers

from pymes import views

enrutador = routers.DefaultRouter()

enrutador.register(r'regiones', views.RegionViewSet)
enrutador.register(r'comunas', views.ComunaViewSet)
enrutador.register(r'rubros', views.RubroViewSet)
enrutador.register(r'pymes', views.PymeViewSet)
enrutador.register(r'productos', views.ProductoViewSet)

urlpatterns = [
    path('', include(enrutador.urls)),
]
