# Gestión de Pymes — Backend con Django + DRF

API REST para administrar pymes chilenas, sus rubros, productos y usuarios.
Sigue la misma estructura de la guía `IEI_N4_C3` (proyecto `drf`, app `pymes`).

## Estructura

```
drf/            configuración del proyecto (settings.py, urls.py)
pymes/          aplicación: models, serializer, views, urls, admin, tests
  fixtures/     datos iniciales (regiones, comunas, rubros)
  templates/    base.html, bienvenida.html, 404.html
static/         archivos estáticos
sql.sql         creación de BD y usuario MySQL
.env.example    plantilla de variables de ambiente
```

## Modelo de datos

| Modelo   | Descripción                                                              |
|----------|--------------------------------------------------------------------------|
| Region   | 16 regiones de Chile (pk = código numérico)                              |
| Comuna   | Pertenece a una región                                                   |
| Rubro    | Giro/sector de la pyme                                                   |
| Pyme     | RUT validado (módulo 11), razón social, tamaño, ventas UF, contacto      |
| Producto | Producto o servicio de una pyme (SKU único por pyme)                     |
| Usuario  | `AbstractUser` + teléfono, cargo y pyme a la que pertenece               |

## Puesta en marcha

1. **Base de datos** — ejecuta `sql.sql` en MySQL (cambia la contraseña).
2. **Ambiente virtual**
   ```
   python -m venv venv
   .\venv\Scripts\Activate        # Windows
   source venv/bin/activate        # Linux / macOS
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. **Variables de ambiente** — copia `.env.example` a `.env` y completa los valores.
   Para generar una `SECRET_KEY`:
   `python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"`
4. **Migraciones** (el modelo `Usuario` ya está en `AUTH_USER_MODEL`, por eso se migra desde cero)
   ```
   python manage.py makemigrations pymes
   python manage.py migrate
   ```
5. **Datos iniciales** (el orden importa por las llaves foráneas)
   ```
   python manage.py loaddata regiones comunas rubros
   ```
6. **Superusuario y servidor**
   ```
   python manage.py createsuperuser
   python manage.py runserver
   ```

## Endpoints

| Ruta                    | Métodos            | Notas                                              |
|-------------------------|--------------------|----------------------------------------------------|
| `/`                     | GET                | Página de bienvenida                               |
| `/admin/`               | —                  | Panel de administración                            |
| `/api/`                 | GET                | Raíz navegable de la API                           |
| `/api/regiones/`        | GET                | Solo lectura                                       |
| `/api/comunas/?region=9`| GET                | Solo lectura, filtro por región                    |
| `/api/rubros/`          | CRUD               |                                                    |
| `/api/pymes/`           | CRUD               | `?search=`, `?tamano=`, `?rubro=`, `?comuna=`, `?activa=true`, `?ordering=` |
| `/api/pymes/resumen/`   | GET                | Cantidad de pymes por tamaño                       |
| `/api/productos/`       | CRUD               | `?pyme=1`, `?search=`, `?ordering=`                |

Permisos: lectura pública; crear, editar y borrar requiere sesión iniciada
(`/api-auth/login/` o `/admin/`).

Ejemplo de creación (autenticado):
```json
POST /api/pymes/
{
  "rut": "76.123.456-K",
  "razon_social": "Panadería Los Robles SpA",
  "rubro": 2,
  "comuna": 1,
  "tamano": "MICRO",
  "email": "contacto@losrobles.cl"
}
```
> Usa un RUT con dígito verificador válido; la API rechaza los que no lo son.

## Pruebas

```
python manage.py test
```

## Notas

- **Clasificación de tamaño:** la propiedad `clasificacion_sugerida` usa los tramos de la Ley 20.416
  (micro ≤ 2.400 UF, pequeña ≤ 25.000 UF, mediana ≤ 100.000 UF de ventas anuales). Verifica que sigan vigentes.
- **ORM:** Django ya trae su propio ORM; SQLAlchemy (mencionado en la guía original) no es necesario. Solo se requiere `mysqlclient`.
- **Producción:** con `DEBUG=False` el servidor de desarrollo no sirve archivos estáticos. Usa `collectstatic` y un servidor web, o `DEBUG=True` en local.
- Si agregas librerías, actualiza `requirements.txt` con `pip freeze > requirements.txt`.
