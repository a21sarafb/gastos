from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.contrib.auth.models import User
from decimal import Decimal
import datetime

from .models import UserProfile, Categoria, Gasto, FondoComun, IngresoFondo
from .forms import GastoForm, RegistroForm
import json
from django.db.models import Sum
from django.db.models.functions import TruncMonth


"""
Vistas para la aplicación de gastos.

Se han introducido varias mejoras para soportar fondos comunes con
aportaciones mensuales proporcionales al salario de cada usuaria:

* Un helper ``actualizar_fondos_mensuales`` que se encarga de añadir
  automáticamente las aportaciones mensuales a cada fondo cuando cambia
  el mes. Estas aportaciones se reparten entre Sara y Adri según
  constantes ``PORCENTAJE_SARA`` y ``PORCENTAJE_ADRI`` y se registran
  en la tabla ``IngresoFondo``.
* Actualización del panel de fondos para mostrar los nuevos fondos
  (incluido «Supermercado») y las aportaciones mensuales correctas según
  la especificación del usuario (200 € para supermercado, 150 € para
  gastos del piso, 100 € para viajes, 100 € para compras del piso y
  150 € para ahorro de pareja).
* Ampliación de la lista de categorías disponible al crear un gasto
  para incluir «Compras piso». Esta lista se ofrece como nombres
  legibles y se almacena en el campo ``categoria`` del modelo ``Gasto``.

El resto de vistas (listado de gastos, panel de gastos, registro y
login) se mantienen prácticamente igual, corrigiendo la identación y
añadiendo los nuevos colores para la categoría ``Compras piso``.
"""

# Porcentajes de aportación fijos por usuaria
PORCENTAJE_SARA = Decimal('0.63')
PORCENTAJE_ADRI = Decimal('0.37')

# Montos mensuales asignados a cada fondo común
MONTOS_MENSUALES = {
    'SUPERMERCADO': Decimal('200'),  # Comida y supermercado
    'GASTOS': Decimal('150'),        # Facturas del piso (luz, agua, etc.)
    'VIAJES': Decimal('100'),        # Ahorro para viajes
    'COMPRAS': Decimal('100'),       # Compras puntuales del piso
    'AHORRO': Decimal('150'),        # Ahorro de pareja (boda, hijos, ...)
}


def actualizar_fondos_mensuales() -> None:
    """Actualiza el saldo de todos los fondos una vez al mes.

    Comprueba la fecha de ``ultima_actualizacion`` de cada ``FondoComun`` y,
    si es anterior al primer día del mes en curso, se añaden las aportaciones
    correspondientes. Las aportaciones se reparten entre Sara y Adri según
    los porcentajes definidos y se registran en ``IngresoFondo``.
    """
    hoy = datetime.date.today()
    primer_dia_mes = hoy.replace(day=1)
    fondos = FondoComun.objects.all()
    for fondo in fondos:
        # Si el fondo no se ha actualizado este mes, se añaden las aportaciones
        if fondo.ultima_actualizacion < primer_dia_mes:
            total_mensual = MONTOS_MENSUALES.get(fondo.tipo)
            if not total_mensual:
                continue
            # Actualizar saldo y fecha de última actualización
            fondo.saldo += total_mensual
            fondo.ultima_actualizacion = hoy
            fondo.save()
            # Obtener usuarios (se asume que existen usuarios con username 'sara' y 'adri')
            try:
                sara = User.objects.get(username='sara')
                adri = User.objects.get(username='adri')
            except User.DoesNotExist:
                # Si no existen, no podemos registrar aportaciones individuales
                continue
            # Calcular aportación de cada usuaria
            sara_amount = (total_mensual * PORCENTAJE_SARA).quantize(Decimal('0.01'))
            adri_amount = (total_mensual * PORCENTAJE_ADRI).quantize(Decimal('0.01'))
            # Registrar ingresos individuales en la tabla IngresoFondo
            IngresoFondo.objects.create(fondo=fondo, cantidad=sara_amount, usuario=sara)
            IngresoFondo.objects.create(fondo=fondo, cantidad=adri_amount, usuario=adri)


@login_required
def lista_gastos(request):
    """Muestra un listado de gastos pagados por el usuario autenticado."""
    gastos = Gasto.objects.filter(pagado_por=request.user).order_by('-fecha')
    return render(request, 'core/lista_gastos.html', {'gastos': gastos})


@login_required
def crear_gasto(request):
    """Permite crear un nuevo gasto.

    Al crear un gasto se selecciona la categoría, la fecha, quién pagó y
    opcionalmente de qué fondo se descontará. Si se selecciona un fondo y
    existe saldo suficiente, se resta el monto del gasto al saldo del
    fondo.
    """
    if request.method == 'POST':
        try:
            descripcion = request.POST.get('descripcion')
            monto_total = request.POST.get('monto_total')
            categoria = request.POST.get('categoria')
            pagado_por_id = request.POST.get('pagado_por')
            fecha = request.POST.get('fecha')
            fondo_id = request.POST.get('fondo')

            if not all([descripcion, monto_total, categoria, pagado_por_id, fecha]):
                messages.error(request, 'Todos los campos son obligatorios')
                return render(
                    request,
                    'core/crear_gasto.html',
                    {
                        'categorias': ['Gastos piso', 'Compras piso', 'Supermercado', 'Viajes', 'Ocio', 'Otros'],
                        'usuarios': User.objects.filter(username__in=['sara', 'adri']),
                        'fondos': FondoComun.objects.exclude(tipo='AHORRO'),
                    },
                )

            # Obtener el usuario que pagó
            pagador = User.objects.get(id=pagado_por_id)
            # Obtener el fondo seleccionado si existe
            fondo = None
            if fondo_id:
                try:
                    fondo = FondoComun.objects.get(id=fondo_id)
                    # Verificar saldo suficiente
                    if fondo.saldo < Decimal(monto_total):
                        messages.error(request, 'No hay saldo suficiente en el fondo')
                        return redirect('crear_gasto')
                except FondoComun.DoesNotExist:
                    fondo = None

            # Crear y guardar el gasto
            gasto = Gasto(
                descripcion=descripcion,
                monto_total=monto_total,
                categoria=categoria,
                pagado_por=pagador,
                fecha=fecha,
                fondo=fondo,
            )
            gasto.save()

            # Descontar del fondo si corresponde
            if fondo:
                fondo.saldo -= Decimal(monto_total)
                fondo.save()

            messages.success(request, 'Gasto creado correctamente')
            return redirect('panel_gastos')

        except Exception as e:
            messages.error(request, f'Error al crear el gasto: {str(e)}')

    # En peticiones GET se muestran los formularios
    fondo_id = request.GET.get('fondo')
    fondos = FondoComun.objects.exclude(tipo='AHORRO')
    return render(
        request,
        'core/crear_gasto.html',
        {
            'categorias': ['Gastos piso', 'Compras piso', 'Supermercado', 'Viajes', 'Ocio', 'Otros'],
            'usuarios': User.objects.filter(username__in=['sara', 'adri']),
            'fondos': fondos,
            'fondo_seleccionado': fondo_id,
        },
    )


def registro_usuario(request):
    """Gestiona el registro de nuevos usuarios."""
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('lista_gastos')
    else:
        form = RegistroForm()
    return render(request, 'core/registro.html', {'form': form})


def login_usuario(request):
    """Autentica al usuario y lo redirige al panel de gastos."""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('lista_gastos')
        else:
            return render(request, 'core/login.html', {'error': 'Credenciales inválidas'})
    return render(request, 'core/login.html')


def logout_usuario(request):
    """Cierra la sesión actual y redirige al formulario de login."""
    logout(request)
    return redirect('login')


@login_required
def panel_gastos(request):
    """Muestra el panel de gastos con balance y listado de todos los gastos."""
    # Mapeo de identificadores a nombres de categoría (por compatibilidad)
    CATEGORIA_NOMBRES = {
        '1': 'Supermercado',
        '2': 'Viajes',
        '3': 'Gastos piso',
        '4': 'Ocio',
        '5': 'Otros',
        '6': 'Compras piso',
    }
    # Colores para cada categoría
    CATEGORIA_COLORES = {
        'Viajes': 'bg-warning bg-opacity-50',
        'Ocio': 'bg-danger bg-opacity-50',
        'Supermercado': 'bg-info bg-opacity-50',
        'Gastos piso': 'bg-success bg-opacity-50',
        'Compras piso': 'bg-primary bg-opacity-50',
        'Otros': 'bg-secondary bg-opacity-50',
    }
    # Obtener usuarios fijos
    try:
        sara = User.objects.get(username='sara')
        adri = User.objects.get(username='adri')
    except User.DoesNotExist:
        return render(
            request,
            'core/error.html',
            {'mensaje': 'Error: Los usuarios sara y adri deben existir en el sistema'},
        )
    usuario_actual = request.user
    otro_usuario = adri if usuario_actual == sara else sara
    # Determinar los porcentajes de cada usuaria
    if usuario_actual == sara:
        mi_porcentaje = PORCENTAJE_SARA
        otro_porcentaje = PORCENTAJE_ADRI
    else:
        mi_porcentaje = PORCENTAJE_ADRI
        otro_porcentaje = PORCENTAJE_SARA
    # Obtener todos los gastos
    todos_los_gastos = Gasto.objects.all().order_by('-fecha')
    deuda_total = Decimal('0')
    gastos_procesados = []
    for gasto in todos_los_gastos:
        categoria_nombre = gasto.get_categoria_display() or ''
        # Calcular el reparto (mismo porcentaje independientemente de quién paga)
        parte_sara = gasto.monto_total * PORCENTAJE_SARA
        parte_adri = gasto.monto_total * PORCENTAJE_ADRI
        # Balance de deuda según quién pagó
        if gasto.pagado_por == usuario_actual:
            if usuario_actual == sara:
                deuda_total += parte_adri  # Adri le debe a Sara
            else:
                deuda_total += parte_sara  # Sara le debe a Adri
        else:
            if usuario_actual == sara:
                deuda_total -= parte_sara  # Sara debe a Adri
            else:
                deuda_total -= parte_adri  # Adri debe a Sara
        gastos_procesados.append(
            {
                'fecha': gasto.fecha,
                'descripcion': gasto.descripcion,
                'monto_total': gasto.monto_total,
                'parte_sara': parte_sara,
                'parte_adri': parte_adri,
                'pagado_por': gasto.pagado_por.username,
                'categoria': categoria_nombre,
                'color_clase': CATEGORIA_COLORES.get(categoria_nombre, ''),
            }
        )
    # Construir leyenda de categorías para mostrar
    leyenda_categorias = {nombre: CATEGORIA_COLORES.get(nombre, '') for nombre in CATEGORIA_NOMBRES.values()}
    context = {
        'gastos': gastos_procesados,
        'deuda_total': deuda_total,
        'otro_usuario': otro_usuario,
        'mi_porcentaje': mi_porcentaje * 100,
        'otro_porcentaje': otro_porcentaje * 100,
        'categoria_colores': CATEGORIA_COLORES,
        'usuario_actual': usuario_actual.username,
    }
    return render(request, 'core/panel_gastos.html', context)


@login_required
def panel_fondos(request):
    """Muestra el panel de fondos comunes y actualiza los saldos mensuales."""
    # Actualizar fondos al inicio de mes si es necesario
    actualizar_fondos_mensuales()
    # Obtener todos los fondos para mostrar
    fondos = FondoComun.objects.all()
    # Calcular aportaciones previstas para cada fondo según los montos mensuales
    aportaciones = {}
    for tipo, total in MONTOS_MENSUALES.items():
        aportaciones[tipo] = {
            'total': total,
            'sara': (total * PORCENTAJE_SARA).quantize(Decimal('0.01')),
            'adri': (total * PORCENTAJE_ADRI).quantize(Decimal('0.01')),
        }
    # Calcular saldo total en todos los fondos
    saldo_total = sum(f.saldo for f in fondos)
    context = {
        'fondos': fondos,
        'aportaciones': aportaciones,
        'saldo_total': saldo_total,
    }
    return render(request, 'core/panel_fondos.html', context)


@login_required
def resumen_finanzas(request):
    """Vista de resumen financiero con gráficos mensuales y por categoría.

    Prepara datos agregados para representar los gastos de los últimos meses
    y del mes actual desglosados por categoría. Los datos se serializan a
    JSON para que puedan ser consumidos por Chart.js en la plantilla.
    """
    hoy = datetime.date.today()
    # Totales por categoría en el mes actual
    inicio_mes = hoy.replace(day=1)
    gastos_categoria = (
        Gasto.objects
        .filter(fecha__gte=inicio_mes, fecha__lte=hoy)
        .values('categoria')
        .annotate(total=Sum('monto_total'))
    )
    labels_categoria = []
    data_categoria = []
    # Convertimos las claves de categoría a sus nombres legibles
    categorias_dict = dict(Gasto.CATEGORIAS)
    for item in gastos_categoria:
        codigo = item['categoria']
        label = categorias_dict.get(codigo, codigo)
        labels_categoria.append(label)
        data_categoria.append(float(item['total']))
    # Totales mensuales de los últimos seis meses
    seis_meses_atras = hoy - datetime.timedelta(days=180)
    gastos_mes = (
        Gasto.objects
        .filter(fecha__gte=seis_meses_atras, fecha__lte=hoy)
        .annotate(mes=TruncMonth('fecha'))
        .values('mes')
        .annotate(total=Sum('monto_total'))
        .order_by('mes')
    )
    labels_mes = []
    data_mes = []
    for item in gastos_mes:
        mes_date = item['mes']
        labels_mes.append(mes_date.strftime('%b %Y'))
        data_mes.append(float(item['total']))
    context = {
        'labels_categoria': json.dumps(labels_categoria),
        'data_categoria': json.dumps(data_categoria),
        'labels_mes': json.dumps(labels_mes),
        'data_mes': json.dumps(data_mes),
    }
    return render(request, 'core/resumen.html', context)


@login_required
def actualizar_fondo(request, fondo_id: int):
    """Permite actualizar manualmente el saldo de un fondo (AJAX)."""
    if request.method == 'POST':
        try:
            fondo = FondoComun.objects.get(id=fondo_id)
            nuevo_saldo = Decimal(request.POST.get('saldo', '0'))
            fondo.saldo = nuevo_saldo
            fondo.save()
            return JsonResponse({'success': True, 'nuevo_saldo': float(nuevo_saldo)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False}, status=405)