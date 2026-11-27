from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APITestCase

from . import models


class RutTests(TestCase):
    def test_rut_valido(self):
        models.validar_rut('12.345.678-5')

    def test_rut_invalido(self):
        with self.assertRaises(ValidationError):
            models.validar_rut('12.345.678-9')

    def test_normalizar(self):
        self.assertEqual(models.normalizar_rut('12.345.678-5'), '12345678-5')


class PymeApiTests(APITestCase):
    def setUp(self):
        region = models.Region.objects.create(id=9, nombre='La Araucanía')
        self.comuna = models.Comuna.objects.create(region=region, nombre='Temuco')
        self.rubro = models.Rubro.objects.create(nombre='Comercio')
        self.pyme = models.Pyme.objects.create(
            rut='12.345.678-5', razon_social='Ejemplo SpA', rubro=self.rubro,
            comuna=self.comuna, email='contacto@ejemplo.cl')

    def test_listado_publico(self):
        r = self.client.get('/api/pymes/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['count'], 1)

    def test_crear_requiere_login(self):
        r = self.client.post('/api/pymes/', {})
        self.assertIn(r.status_code, (401, 403))

    def test_resumen(self):
        r = self.client.get('/api/pymes/resumen/')
        self.assertEqual(r.status_code, 200)
