from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


# ---------------------------------------------------------------- validadores
def validar_rut(valor):
    """Valida un RUT chileno (con o sin puntos/guion) usando módulo 11."""
    rut = str(valor).replace('.', '').replace('-', '').upper()
    if len(rut) < 2 or not rut[:-1].isdigit():
        raise ValidationError('El RUT no tiene un formato válido.')
    cuerpo, dv = rut[:-1], rut[-1]
    suma, multiplicador = 0, 2
    for digito in reversed(cuerpo):
        suma += int(digito) * multiplicador
        multiplicador = 2 if multiplicador == 7 else multiplicador + 1
    resto = 11 - (suma % 11)
    esperado = '0' if resto == 11 else 'K' if resto == 10 else str(resto)
    if dv != esperado:
        raise ValidationError('El dígito verificador del RUT no es válido.')


def normalizar_rut(valor):
    """12.345.678-5 -> 12345678-5"""
    rut = str(valor).replace('.', '').replace('-', '').upper()
    return f'{rut[:-1]}-{rut[-1]}'


# ------------------------------------------------------------- base abstracta
class Auditable(models.Model):
    created_at = models.DateTimeField('Fecha creación', auto_now_add=True)
    updated_at = models.DateTimeField('Fecha actualización', auto_now=True)

    class Meta:
        abstract = True


# ------------------------------------------------------------------ catálogos
class Region(models.Model):
    nombre = models.CharField('Región', max_length=80, unique=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'Región'
        verbose_name_plural = 'Regiones'

    def __str__(self):
        return self.nombre


class Comuna(models.Model):
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name='comunas')
    nombre = models.CharField('Comuna', max_length=80)

    class Meta:
        ordering = ['nombre']
        constraints = [
            models.UniqueConstraint(fields=['region', 'nombre'], name='comuna_unica_por_region')
        ]

    def __str__(self):
        return f'{self.nombre} ({self.region_id})'


class Rubro(models.Model):
    nombre = models.CharField('Rubro', max_length=80, unique=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


# ------------------------------------------------------------------- negocio
class Pyme(Auditable):
    class Tamano(models.TextChoices):
        MICRO = 'MICRO', 'Microempresa'
        PEQUENA = 'PEQUENA', 'Pequeña empresa'
        MEDIANA = 'MEDIANA', 'Mediana empresa'

    rut = models.CharField('RUT', max_length=12, unique=True, validators=[validar_rut],
                           help_text='Ej: 76.123.456-7')
    razon_social = models.CharField('Razón social', max_length=150)
    nombre_fantasia = models.CharField('Nombre de fantasía', max_length=150, blank=True)
    rubro = models.ForeignKey(Rubro, on_delete=models.PROTECT, related_name='pymes')
    comuna = models.ForeignKey(Comuna, on_delete=models.PROTECT, related_name='pymes')
    direccion = models.CharField('Dirección', max_length=200, blank=True)
    tamano = models.CharField('Tamaño', max_length=10, choices=Tamano.choices,
                              default=Tamano.MICRO)
    ventas_anuales_uf = models.DecimalField('Ventas anuales (UF)', max_digits=12,
                                            decimal_places=2, null=True, blank=True)
    num_trabajadores = models.PositiveIntegerField('N° de trabajadores', default=0)
    email = models.EmailField('Correo de contacto')
    telefono = models.CharField('Teléfono', max_length=20, blank=True)
    sitio_web = models.URLField('Sitio web', blank=True)
    fecha_inicio_actividades = models.DateField('Inicio de actividades', null=True, blank=True)
    activa = models.BooleanField('Activa', default=True)

    class Meta:
        ordering = ['razon_social']
        verbose_name = 'Pyme'
        verbose_name_plural = 'Pymes'

    def __str__(self):
        return f'{self.nombre_fantasia or self.razon_social} ({self.rut})'

    def save(self, *args, **kwargs):
        self.rut = normalizar_rut(self.rut)
        super().save(*args, **kwargs)

    @property
    def clasificacion_sugerida(self):
        """Tramos de la Ley 20.416 según ventas anuales en UF (verificar vigencia)."""
        if self.ventas_anuales_uf is None:
            return None
        ventas = Decimal(self.ventas_anuales_uf)
        if ventas <= 2400:
            return self.Tamano.MICRO
        if ventas <= 25000:
            return self.Tamano.PEQUENA
        if ventas <= 100000:
            return self.Tamano.MEDIANA
        return None  # supera el tramo pyme


class Producto(Auditable):
    pyme = models.ForeignKey(Pyme, on_delete=models.CASCADE, related_name='productos')
    sku = models.CharField('SKU', max_length=40)
    nombre = models.CharField('Producto o servicio', max_length=150)
    descripcion = models.TextField('Descripción', blank=True)
    precio = models.DecimalField('Precio (CLP)', max_digits=12, decimal_places=0)
    stock = models.IntegerField('Stock', default=0)
    activo = models.BooleanField('Activo', default=True)

    class Meta:
        ordering = ['pyme', 'nombre']
        constraints = [
            models.UniqueConstraint(fields=['pyme', 'sku'], name='sku_unico_por_pyme')
        ]

    def __str__(self):
        return f'{self.nombre} [{self.sku}]'


# ------------------------------------------------------------------- usuarios
class Usuario(AbstractUser):
    """Extiende el usuario nativo de Django conservando login, permisos y contraseñas."""
    telefono = models.CharField(max_length=20, blank=True)
    cargo = models.CharField(max_length=80, blank=True)
    pyme = models.ForeignKey(Pyme, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='usuarios')

    def __str__(self):
        return self.username
