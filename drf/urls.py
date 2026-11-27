from django.contrib import admin
from django.urls import path, include

from pymes import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.bienvenida, name='bienvenida'),
    path('pymes/', views.catalogo_pymes, name='catalogo_pymes'),
    path('productos/', views.catalogo_productos, name='catalogo_productos'),
    path('login/', views.UsuarioLoginView.as_view(), name='login'),
    path('logout/', views.UsuarioLogoutView.as_view(), name='logout'),
    path('registro/', views.registro_usuario, name='registro'),
    path('mi-panel/', views.portal_usuario, name='portal_usuario'),
    path('mi-panel/productos/<int:pk>/editar/', views.editar_producto, name='editar_producto'),
    path('mi-panel/productos/<int:pk>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    path('api/', include('pymes.urls')),
    path('api-auth/', include('rest_framework.urls')),  # login para la API navegable
]
