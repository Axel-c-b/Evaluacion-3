from django import forms
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import models, serializer


# ----------------------------------------------------------------- formularios
class RegistroUsuarioForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = models.Usuario
        fields = ('username', 'first_name', 'last_name', 'email', 'telefono', 'cargo')


class PymeUsuarioForm(forms.ModelForm):
    class Meta:
        model = models.Pyme
        fields = (
            'rut', 'razon_social', 'nombre_fantasia', 'rubro', 'comuna',
            'direccion', 'tamano', 'ventas_anuales_uf', 'num_trabajadores',
            'email', 'telefono', 'sitio_web', 'fecha_inicio_actividades', 'activa',
        )
        widgets = {
            'fecha_inicio_actividades': forms.DateInput(attrs={'type': 'date'}),
        }


class ProductoUsuarioForm(forms.ModelForm):
    class Meta:
        model = models.Producto
        fields = ('sku', 'nombre', 'descripcion', 'precio', 'stock', 'activo')
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 2}),
        }


# --------------------------------------------------------------- vistas HTML
class UsuarioLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True


class UsuarioLogoutView(LogoutView):
    pass


def registro_usuario(request):
    if request.user.is_authenticated:
        return redirect('portal_usuario')
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            messages.success(request, f'¡Bienvenido/a, {usuario.username}! Tu cuenta fue creada.')
            return redirect('portal_usuario')
    else:
        form = RegistroUsuarioForm()
    return render(request, 'registro.html', {'form': form})


def bienvenida(request):
    pymes_destacadas = (
        models.Pyme.objects.filter(activa=True)
        .select_related('rubro', 'comuna', 'comuna__region')[:6]
    )
    productos_destacados = (
        models.Producto.objects.filter(activo=True, pyme__activa=True)
        .select_related('pyme')[:6]
    )
    total_pymes = models.Pyme.objects.filter(activa=True).count()
    total_productos = models.Producto.objects.filter(activo=True).count()
    total_rubros = models.Rubro.objects.count()
    return render(request, 'bienvenida.html', {
        'pymes_destacadas': pymes_destacadas,
        'productos_destacados': productos_destacados,
        'total_pymes': total_pymes,
        'total_productos': total_productos,
        'total_rubros': total_rubros,
    })


def catalogo_pymes(request):
    q = request.GET.get('q', '').strip()
    tamano = request.GET.get('tamano', '').strip()
    rubro_id = request.GET.get('rubro', '').strip()

    pymes = models.Pyme.objects.filter(activa=True).select_related('rubro', 'comuna', 'comuna__region')
    if q:
        pymes = pymes.filter(
            Q(razon_social__icontains=q)
            | Q(nombre_fantasia__icontains=q)
            | Q(rut__icontains=q)
            | Q(comuna__nombre__icontains=q)
        )
    if tamano:
        pymes = pymes.filter(tamano=tamano)
    if rubro_id.isdigit():
        pymes = pymes.filter(rubro_id=int(rubro_id))

    return render(request, 'catalogo_pymes.html', {
        'pymes': pymes,
        'rubros': models.Rubro.objects.all(),
        'tamanos': models.Pyme.Tamano.choices,
        'q': q,
        'tamano_sel': tamano,
        'rubro_sel': rubro_id,
    })


def catalogo_productos(request):
    q = request.GET.get('q', '').strip()
    pyme_id = request.GET.get('pyme', '').strip()

    productos = models.Producto.objects.filter(activo=True, pyme__activa=True).select_related('pyme')
    if q:
        productos = productos.filter(
            Q(nombre__icontains=q)
            | Q(sku__icontains=q)
            | Q(descripcion__icontains=q)
        )
    if pyme_id.isdigit():
        productos = productos.filter(pyme_id=int(pyme_id))

    return render(request, 'catalogo_productos.html', {
        'productos': productos,
        'pymes': models.Pyme.objects.filter(activa=True),
        'q': q,
        'pyme_sel': pyme_id,
    })


@login_required
def portal_usuario(request):
    pyme = request.user.pyme
    pyme_form = PymeUsuarioForm(instance=pyme)
    producto_form = ProductoUsuarioForm()

    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'guardar_pyme':
            pyme_form = PymeUsuarioForm(request.POST, instance=pyme)
            if pyme_form.is_valid():
                pyme_guardada = pyme_form.save()
                if request.user.pyme_id != pyme_guardada.pk:
                    request.user.pyme = pyme_guardada
                    request.user.save(update_fields=['pyme'])
                messages.success(request, 'Los datos de tu pyme se guardaron correctamente.')
                return redirect('portal_usuario')
        elif accion == 'crear_producto':
            if not pyme:
                messages.error(request, 'Primero debes registrar los datos de tu pyme.')
                return redirect('portal_usuario')
            producto_form = ProductoUsuarioForm(request.POST)
            if producto_form.is_valid():
                nuevo_prod = producto_form.save(commit=False)
                nuevo_prod.pyme = pyme
                # Evitar IntegrityError si el SKU ya existe en la misma pyme
                if models.Producto.objects.filter(pyme=pyme, sku=nuevo_prod.sku).exists():
                    producto_form.add_error('sku', 'Ya tienes un producto con este SKU en tu pyme.')
                else:
                    nuevo_prod.save()
                    messages.success(request, f'Producto "{nuevo_prod.nombre}" agregado correctamente.')
                    return redirect('portal_usuario')

    productos = models.Producto.objects.filter(pyme=pyme) if pyme else models.Producto.objects.none()
    return render(request, 'portal_usuario.html', {
        'pyme': pyme,
        'pyme_form': pyme_form,
        'producto_form': producto_form,
        'productos': productos,
    })


@login_required
def editar_producto(request, pk):
    pyme = request.user.pyme
    if not pyme:
        messages.error(request, 'No tienes una pyme asociada.')
        return redirect('portal_usuario')
    producto = get_object_or_404(models.Producto, pk=pk, pyme=pyme)
    if request.method == 'POST':
        form = ProductoUsuarioForm(request.POST, instance=producto)
        if form.is_valid():
            editado = form.save(commit=False)
            if models.Producto.objects.filter(pyme=pyme, sku=editado.sku).exclude(pk=producto.pk).exists():
                form.add_error('sku', 'Ya existe otro producto con ese SKU en tu pyme.')
            else:
                editado.save()
                messages.success(request, f'Producto "{editado.nombre}" actualizado.')
                return redirect('portal_usuario')
    else:
        form = ProductoUsuarioForm(instance=producto)
    return render(request, 'editar_producto.html', {'form': form, 'producto': producto})


@login_required
def eliminar_producto(request, pk):
    pyme = request.user.pyme
    if request.method == 'POST' and pyme:
        producto = get_object_or_404(models.Producto, pk=pk, pyme=pyme)
        nombre = producto.nombre
        producto.delete()
        messages.success(request, f'Producto "{nombre}" eliminado.')
    return redirect('portal_usuario')


# --------------------------------------------------------------- API ViewSets
class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Region.objects.all()
    serializer_class = serializer.RegionSerializer
    pagination_class = None


class ComunaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Comuna.objects.select_related('region')
    serializer_class = serializer.ComunaSerializer
    pagination_class = None

    def get_queryset(self):
        qs = super().get_queryset()
        region = self.request.query_params.get('region')
        return qs.filter(region_id=region) if region else qs


class RubroViewSet(viewsets.ModelViewSet):
    queryset = models.Rubro.objects.all()
    serializer_class = serializer.RubroSerializer
    pagination_class = None


class PymeViewSet(viewsets.ModelViewSet):
    queryset = models.Pyme.objects.select_related('rubro', 'comuna')
    serializer_class = serializer.PymeSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['rut', 'razon_social', 'nombre_fantasia']
    ordering_fields = ['razon_social', 'created_at', 'num_trabajadores']

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if p.get('tamano'):
            qs = qs.filter(tamano=p['tamano'])
        if p.get('rubro'):
            qs = qs.filter(rubro_id=p['rubro'])
        if p.get('comuna'):
            qs = qs.filter(comuna_id=p['comuna'])
        if p.get('activa') in ('true', 'false'):
            qs = qs.filter(activa=p['activa'] == 'true')
        return qs

    @action(detail=False, methods=['get'])
    def resumen(self, request):
        """GET /api/pymes/resumen/ -> cantidad de pymes por tamaño."""
        datos = models.Pyme.objects.values('tamano').annotate(total=Count('id')).order_by('tamano')
        return Response(list(datos))


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = models.Producto.objects.select_related('pyme')
    serializer_class = serializer.ProductoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['sku', 'nombre']
    ordering_fields = ['nombre', 'precio', 'stock']

    def get_queryset(self):
        qs = super().get_queryset()
        pyme = self.request.query_params.get('pyme')
        return qs.filter(pyme_id=pyme) if pyme else qs
