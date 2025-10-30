from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.contrib.auth.models import User
from decimal import Decimal
import datetime

from .models import UserProfile, Categoria, Gasto, FondoComun, IngresoFondo, GastoRecurrente, ObjetivoAhorro
from .forms import GastoForm, RegistroForm
import json
from django.db.models import Sum
from django.db.models.functions import TruncMonth

from django.db import transaction

from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.timezone import now


def aplicar_gastos_recurrentes_y_objetivos():
    hoy = datetime.date.today()

    def ya_aplicado(ultimo_ano, ultimo_mes):
        return ultimo_ano == hoy.year and ultimo_mes == hoy.month

    with transaction.atomic():
        # === Gastos recurrentes (suscripciones / caldera) ===
        for rec in GastoRecurrente.objects.filter(activo=True):
            if ya_aplicado(rec.ultimo_ano_aplicado, rec.ultimo_mes_aplicado):
                continue

            # mensual completo o anual prorrateado
            monto_mes = (
                rec.monto if rec.periodicidad == 'MENSUAL'
                else (rec.monto / Decimal('12')) if rec.prorratear
                else rec.monto
            ).quantize(Decimal('0.01'))

            # crea el gasto (siempre de la cuenta conjunta; da igual quién aparezca como pagador)
            gasto = Gasto.objects.create(
                descripcion=f"[Recurrente] {rec.nombre}",
                monto_total=monto_mes,
                categoria=rec.categoria,
                pagado_por=User.objects.filter(username__in=['sara','adri']).first(),
                fecha=hoy,
                fondo=rec.fondo
            )

            # descuenta manualmente del saldo del fondo si corresponde
            if rec.fondo:
                rec.fondo.saldo -= monto_mes
                rec.fondo.save(update_fields=['saldo'])

            # marca como aplicado este mes
            rec.ultimo_ano_aplicado = hoy.year
            rec.ultimo_mes_aplicado = hoy.month
            rec.save(update_fields=['ultimo_ano_aplicado', 'ultimo_mes_aplicado'])

        # === Objetivos de ahorro ===
        for obj in ObjetivoAhorro.objects.filter(activo=True):
            if ya_aplicado(obj.ultimo_ano_aplicado, obj.ultimo_mes_aplicado):
                continue

            aporte = obj.aporte_mensual.quantize(Decimal('0.01'))

            # ingreso automático al fondo (no se adjudica a Sara/Adri)
            IngresoFondo.objects.create(
                fondo=obj.fondo_destino,
                cantidad=aporte,
                usuario=None,
                es_automatico=True
            )
            # si tienes señal post_save en IngresoFondo, el saldo se suma automáticamente

            obj.ultimo_ano_aplicado = hoy.year
            obj.ultimo_mes_aplicado = hoy.month
            obj.save(update_fields=['ultimo_ano_aplicado', 'ultimo_mes_aplicado'])



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

# Nota: los montos mensuales ya no se definen de forma estática.
#       En lugar de ello se registran como objetos ``IngresoFondo``
#       desde el panel de administración.  Los saldos de cada
#       ``FondoComun`` se actualizan automáticamente cuando se crea
#       un ``IngresoFondo`` (ver señal en ``models.py``) y el panel
#       de fondos calcula las aportaciones mensuales de forma
#       dinámica.
MONTOS_MENSUALES = {}



def actualizar_fondos_mensuales() -> None:
    """
    Mantenemos esta función por compatibilidad con código antiguo, pero ya no
    realiza ingresos automáticos a los fondos comunes.  La lógica de
    aportaciones mensuales se gestiona de forma dinámica mediante objetos
    ``IngresoFondo`` creados por el administrador.  Puedes eliminar la
    llamada a esta función en ``panel_fondos`` para evitar efectos secundarios.
    """
    # No hacemos nada: las aportaciones se gestionan manualmente a través de
    # ingresos registrados desde el panel de administración.
    return


@login_required
def lista_gastos(request):
    gastos = Gasto.objects.select_related('categoria','fondo','pagado_por')

    # filtros por búsqueda, categoría, fondo y fechas
    q      = request.GET.get('q','').strip()
    cat_id = request.GET.get('cat')
    fondo_id = request.GET.get('fondo')
    year   = request.GET.get('year')
    month  = request.GET.get('month')
    order  = request.GET.get('order','fecha_desc')

    if q:
        gastos = gastos.filter(
            Q(descripcion__icontains=q) |
            Q(categoria__nombre__icontains=q) |
            Q(fondo__nombre__icontains=q) |
            Q(pagado_por__username__icontains=q)
        )
    if cat_id:
        gastos = gastos.filter(categoria_id=cat_id)
    if fondo_id:
        gastos = gastos.filter(fondo_id=fondo_id)
    if year and month:
        gastos = gastos.filter(fecha__year=year, fecha__month=month)
    elif year:
        gastos = gastos.filter(fecha__year=year)

    # ordenación
    if order == 'importe_desc':
        gastos = gastos.order_by('-monto_total','-fecha','-id')
    elif order == 'importe_asc':
        gastos = gastos.order_by('monto_total','-fecha','-id')
    else:
        gastos = gastos.order_by('-fecha','-id')

    # paginación (12 tarjetas por página)
    paginator  = Paginator(gastos, 12)
    page_number = request.GET.get('page',1)
    gastos_page = paginator.get_page(page_number)

    # selectores para los filtros
    categorias = Categoria.objects.order_by('nombre')
    fondos     = FondoComun.objects.order_by('nombre')
    today      = now().date()
    years  = list(range(today.year, today.year - 5, -1))
    months = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]

    # total de la página (opcional)
    total_pagina = sum((g.monto_total for g in gastos_page.object_list), Decimal('0.00'))

    context = {
        'gastos': gastos_page,
        'categorias': categorias,
        'fondos': fondos,
        'total_pagina': total_pagina,
        'q': q,
        'cat': cat_id,
        'fondo': fondo_id,
        'year': year,
        'month': month,
        'order': order,
        'years': years,
        'months': months,
    }
    return render(request, 'core/lista_gastos.html', context)



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
            # Fondo enviado desde el formulario (puede venir vacío)
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
            # Determinar el fondo asociado a la categoría si no se ha seleccionado uno
            categoria_map = {
                '1': 'SUPERMERCADO',  # Supermercado
                '3': 'GASTOS',       # Gastos piso
                '2': 'VIAJES',       # Viajes
                '6': 'COMPRAS',      # Compras piso
            }
            fondo = None
            # Si el usuario no seleccionó un fondo manualmente y la categoría está
            # asociada a un fondo, lo asignamos automáticamente.
            if not fondo_id and categoria in categoria_map:
                try:
                    fondo = FondoComun.objects.get(tipo=categoria_map[categoria])
                except FondoComun.DoesNotExist:
                    fondo = None
            # Si el formulario incluye un fondo manualmente lo usamos en su lugar
            elif fondo_id:
                try:
                    fondo = FondoComun.objects.get(id=fondo_id)
                except FondoComun.DoesNotExist:
                    fondo = None
            """# Verificar saldo suficiente si hay fondo
            if fondo:
                if fondo.saldo < Decimal(monto_total):
                    messages.error(request, 'No hay saldo suficiente en el fondo')
                    return redirect('crear_gasto')"""
            # Avisar si el gasto supera el saldo pero permitir su creación
            if fondo and fondo.saldo < Decimal(monto_total):
                messages.warning(request, 'El gasto supera el saldo disponible del fondo; el saldo quedará en negativo.')


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

from decimal import Decimal
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Gasto, FondoComun, IngresoFondo, User
from .views import PORCENTAJE_SARA, PORCENTAJE_ADRI  # Asegúrate de importar tus constantes

@login_required
def panel_gastos(request):
    aplicar_gastos_recurrentes_y_objetivos()

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

    # Obtener filtros de la URL
    cat_filter  = request.GET.get('cat')
    year_filter = request.GET.get('year')
    month_filter = request.GET.get('month')

    # Obtener todos los gastos y aplicar filtros
    todos_los_gastos = Gasto.objects.all()
    if cat_filter:
        todos_los_gastos = todos_los_gastos.filter(categoria=cat_filter)
    if year_filter:
        if month_filter:
            todos_los_gastos = todos_los_gastos.filter(
                fecha__year=year_filter, fecha__month=month_filter
            )
        else:
            todos_los_gastos = todos_los_gastos.filter(fecha__year=year_filter)
    todos_los_gastos = todos_los_gastos.order_by('-fecha')

    # Procesar gastos para calcular deuda y partes correspondientes
    deuda_total = Decimal('0')
    gastos_procesados = []
    for gasto in todos_los_gastos:
        categoria_nombre = gasto.get_categoria_display() or ''
        # Calcular el reparto proporcional independientemente de quién paga
        parte_sara = gasto.monto_total * PORCENTAJE_SARA
        parte_adri = gasto.monto_total * PORCENTAJE_ADRI
        # Si el gasto pertenece a un fondo común, no afecta a la deuda
        if gasto.fondo:
            gastos_procesados.append(
                {
                    'fecha': gasto.fecha,
                    'descripcion': gasto.descripcion,
                    'monto_total': gasto.monto_total,
                    'parte_sara': parte_sara,
                    'parte_adri': parte_adri,
                    'pagado_por': 'Cuenta común',
                    'categoria': categoria_nombre,
                    'color_clase': CATEGORIA_COLORES.get(categoria_nombre, ''),
                }
            )
            continue  # saltamos el cálculo de deuda para este gasto

        # Balance de deuda según quién pagó cuando no hay fondo asociado
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

    # Construir selectores para filtros (años, meses y categorías)
    today = now().date()
    years = list(range(today.year, today.year - 5, -1))
    months = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
    ]
    categorias_filtro = Gasto.CATEGORIAS  # Lista de tuplas (código, nombre)

    context = {
        'gastos': gastos_procesados,
        'deuda_total': deuda_total,
        'otro_usuario': otro_usuario,
        'mi_porcentaje': mi_porcentaje * 100,
        'otro_porcentaje': otro_porcentaje * 100,
        'categoria_colores': CATEGORIA_COLORES,
        'usuario_actual': usuario_actual.username,
        'categorias': categorias_filtro,
        'years': years,
        'months': months,
        'cat': cat_filter,
        'year': year_filter,
        'month': month_filter,
    }
    return render(request, 'core/panel_gastos.html', context)


@login_required
def panel_fondos(request):
    aplicar_gastos_recurrentes_y_objetivos()
    """
    Muestra el panel de fondos comunes.

    En lugar de basarse en montos fijos predefinidos, esta vista calcula las
    aportaciones del mes actual sumando los registros de ``IngresoFondo``.
    De este modo, el administrador puede ingresar diferentes cantidades en
    distintos meses y crear o eliminar aportaciones sin tener que tocar el
    código.
    """
    fondos = FondoComun.objects.all()
    # Fecha del primer día del mes actual para filtrar ingresos
    primer_dia_mes = datetime.date.today().replace(day=1)
    # Calculamos las aportaciones del mes para cada fondo y cada usuaria
    aportaciones = {}
    for fondo in fondos:
        # Ingresos del mes para este fondo
        ingresos_mes = IngresoFondo.objects.filter(fondo=fondo, fecha__gte=primer_dia_mes)
        total = ingresos_mes.aggregate(suma=Sum('cantidad'))['suma'] or Decimal('0')
        # Suma por usuaria
        sara_total = ingresos_mes.filter(usuario__username='sara').aggregate(suma=Sum('cantidad'))['suma'] or Decimal('0')
        adri_total = ingresos_mes.filter(usuario__username='adri').aggregate(suma=Sum('cantidad'))['suma'] or Decimal('0')
        # Guardamos usando el id del fondo para poder acceder fácilmente desde la plantilla
        aportaciones[fondo.id] = {
            'total': total.quantize(Decimal('0.01')),
            'sara': sara_total.quantize(Decimal('0.01')),
            'adri': adri_total.quantize(Decimal('0.01')),
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
    JSON para que puedan ser consumidos por Chart.js en la plantilla."""

    hoy = datetime.date.today()
    inicio_mes = hoy.replace(day=1)

    # Totales por categoría en el mes actual (agrupar por nombre legible)
    gastos_categoria = (
        Gasto.objects
        .filter(fecha__gte=inicio_mes, fecha__lte=hoy)
        .values('categoria')
        .annotate(total=Sum('monto_total'))
    )
    categorias_dict = dict(Gasto.CATEGORIAS)
    totales_por_categoria = {}
    for item in gastos_categoria:
        codigo = item['categoria']
        nombre = categorias_dict.get(codigo, codigo)
        total = item['total'] or Decimal('0')
        # Suma al total existente si el nombre ya se ha añadido
        totales_por_categoria[nombre] = totales_por_categoria.get(nombre, Decimal('0')) + total

    # Preparar datos para el gráfico y la tabla
    labels_categoria = list(totales_por_categoria.keys())
    data_categoria = [float(t) for t in totales_por_categoria.values()]
    tabla_categoria = [
        {'nombre': nombre, 'total': totales_por_categoria[nombre].quantize(Decimal('0.01'))}
        for nombre in labels_categoria
    ]
    # total general del mes
    total_general = sum(totales_por_categoria.values(), Decimal('0')).quantize(Decimal('0.01'))


    # Totales mensuales de los últimos seis meses (sin cambios)
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
        'tabla_categoria': tabla_categoria,
        'total_general': total_general,  # para la tabla en la plantilla
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