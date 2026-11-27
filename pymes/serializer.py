from rest_framework import serializers

from . import models


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Region
        fields = '__all__'


class ComunaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Comuna
        fields = '__all__'


class RubroSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Rubro
        fields = '__all__'


class PymeSerializer(serializers.ModelSerializer):
    # Campos de solo lectura para facilitar el consumo desde el frontend
    rubro_nombre = serializers.CharField(source='rubro.nombre', read_only=True)
    comuna_nombre = serializers.CharField(source='comuna.nombre', read_only=True)
    clasificacion_sugerida = serializers.CharField(read_only=True)

    class Meta:
        model = models.Pyme
        fields = '__all__'

    def validate_rut(self, value):
        return models.normalizar_rut(value)


class ProductoSerializer(serializers.ModelSerializer):
    pyme_nombre = serializers.CharField(source='pyme.razon_social', read_only=True)

    class Meta:
        model = models.Producto
        fields = ('id', 'pyme', 'pyme_nombre', 'sku', 'nombre', 'descripcion',
                  'precio', 'stock', 'activo')
        # De esta forma decidimos qué atributos se serializan


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Usuario
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'telefono', 'cargo', 'pyme')
