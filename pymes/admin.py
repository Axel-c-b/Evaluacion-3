from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import models


@admin.register(models.Pyme)
class PymeAdmin(admin.ModelAdmin):
    list_display = ('rut', 'razon_social', 'rubro', 'comuna', 'tamano', 'activa')
    list_filter = ('tamano', 'activa', 'rubro', 'comuna__region')
    search_fields = ('rut', 'razon_social', 'nombre_fantasia')


@admin.register(models.Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('sku', 'nombre', 'pyme', 'precio', 'stock', 'activo')
    list_filter = ('activo',)
    search_fields = ('sku', 'nombre', 'pyme__razon_social')


@admin.register(models.Comuna)
class ComunaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'region')
    list_filter = ('region',)
    search_fields = ('nombre',)


admin.site.register(models.Region)
admin.site.register(models.Rubro)


@admin.register(models.Usuario)
class UsuarioAdmin(UserAdmin):
    # Muestra los campos heredados y los nuevos
    fieldsets = UserAdmin.fieldsets + (
        ('Datos Pyme', {'fields': ('telefono', 'cargo', 'pyme')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Datos Pyme', {'fields': ('telefono', 'cargo', 'pyme')}),
    )
