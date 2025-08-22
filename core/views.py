from django.shortcuts import render, redirect
from .models import UserProfile, Categoria, Gasto

from django.contrib.auth.models import User
from decimal import Decimal
from django.db.models import Sum, Q
from django.contrib.auth.decorators import login_required
from .forms import GastoForm, RegistroForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

@login_required
def lista_gastos(request):
    gastos = Gasto.objects.filter(pagado_por=request.user).order_by('-fecha')
    return render(request, 'core/lista_gastos.html', {'gastos': gastos})

@login_required
def crear_gasto(request):
    if request.method == 'POST':
        try:
            # Validar que todos los campos necesarios estén presentes
            descripcion = request.POST.get('descripcion')
            monto_total = request.POST.get('monto_total')
            categoria = request.POST.get('categoria')  # Cambiado de categoria_id
            pagado_por_id = request.POST.get('pagado_por')
            fecha = request.POST.get('fecha')
            fondo_id = request.POST.get('fondo')  # Añadido para manejar el fondo

            
            if not all([descripcion, monto_total, categoria, pagado_por_id, fecha]):
                messages.error(request, 'Todos los campos son obligatorios')
                return render(request, 'core/crear_gasto.html', {
                    'categorias': ['Gastos piso', 'Supermercado', 'Viajes', 'Ocio', 'Otros'],
                    'usuarios': User.objects.filter(username__in=['sara', 'adri'])
                })

            # Obtener el usuario que pagó
            pagador = User.objects.get(id=pagado_por_id)
            
            # Obtener el fondo si existe
            fondo = None
            if fondo_id:
                try:
                    fondo = FondoComun.objects.get(id=fondo_id)
                    # Verificar si hay saldo suficiente
                    if fondo.saldo < Decimal(monto_total):
                        messages.error(request, 'No hay saldo suficiente en el fondo')
                        return redirect('crear_gasto')
                except FondoComun.DoesNotExist:
                    pass

            # Crear el gasto
            gasto = Gasto(
                descripcion=descripcion,
                monto_total=monto_total,
                categoria=categoria,  # Cambiado de categoria_id
                pagado_por=pagador,
                fecha=fecha,
                fondo=fondo
            )
            gasto.save()

            # Actualizar el saldo del fondo si existe
            if fondo:
                fondo.saldo -= Decimal(monto_total)
                fondo.save()
            
            messages.success(request, 'Gasto creado correctamente')
            return redirect('panel_gastos')
            
        except Exception as e:
            messages.error(request, f'Error al crear el gasto: {str(e)}')
            
    # GET request
    fondo_id = request.GET.get('fondo')  # Para pre-seleccionar el fondo
    fondos = FondoComun.objects.exclude(tipo='AHORRO')  # Excluir fondo de ahorro

    return render(request, 'core/crear_gasto.html', {
        'categorias': ['Gastos piso', 'Supermercado', 'Viajes', 'Ocio', 'Otros'],
        'usuarios': User.objects.filter(username__in=['sara', 'adri']),
        'fondos': fondos,
        'fondo_seleccionado': fondo_id
    })

def registro_usuario(request):
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
    logout(request)
    return redirect('login')

@login_required
def panel_gastos(request):
    # Mapeo de IDs a nombres de categoría
    CATEGORIA_NOMBRES = {
        '1': 'Supermercado',
        '2': 'Viajes',
        '3': 'Gastos piso',
        '4': 'Ocio',
        '5': 'Otros'
    }
    # Definir colores para categorías
    CATEGORIA_COLORES = {
        'Viajes': 'bg-warning bg-opacity-50',
        'Ocio': 'bg-danger bg-opacity-50',
        'Supermercado': 'bg-info bg-opacity-50',
        'Gastos piso': 'bg-success bg-opacity-50',
        'Otros': 'bg-secondary bg-opacity-50'
    }
    # Porcentajes fijos por usuario
    PORCENTAJE_SARA = Decimal('0.63')
    PORCENTAJE_ADRI = Decimal('0.37')
    
    # Obtener usuarios
    try:
        sara = User.objects.get(username='sara')
        adri = User.objects.get(username='adri')
    except User.DoesNotExist:
        return render(request, 'core/error.html', {
            'mensaje': 'Error: Los usuarios sara y adri deben existir en el sistema'
        })

    usuario_actual = request.user
    otro_usuario = adri if usuario_actual == sara else sara

    # Determinar el porcentaje del usuario actual
    if usuario_actual == sara:
        mi_porcentaje = PORCENTAJE_SARA
        otro_porcentaje = PORCENTAJE_ADRI
    else:
        mi_porcentaje = PORCENTAJE_ADRI
        otro_porcentaje = PORCENTAJE_SARA

    # Obtener todos los gastos
    todos_los_gastos = Gasto.objects.all().order_by('-fecha')
    
    # Calcular deudas
    deuda_total = Decimal('0')
    gastos_procesados = []

    for gasto in todos_los_gastos:
        categoria_nombre = gasto.get_categoria_display() or ''
        print(f"DEBUG - Gasto: {gasto.descripcion}, Categoría: {gasto.categoria}, Nombre: {categoria_nombre}")
        
        #categoria_nombre = CATEGORIA_NOMBRES.get(gasto.categoria, '')

        if gasto.pagado_por == sara:
            parte_sara = gasto.monto_total * PORCENTAJE_SARA
            parte_adri = gasto.monto_total * PORCENTAJE_ADRI
        else:
            parte_sara = gasto.monto_total * PORCENTAJE_SARA
            parte_adri = gasto.monto_total * PORCENTAJE_ADRI

        # Si el usuario actual es quien pagó, suma lo que le deben
        # Si no, resta lo que debe
        if gasto.pagado_por == usuario_actual:
            if usuario_actual == sara:
                deuda_total += parte_adri  # Adri le debe a Sara
            else:
                deuda_total += parte_sara  # Sara le debe a Adri
        else:
            if usuario_actual == sara:
                deuda_total -= parte_sara  # Sara le debe a Adri
            else:
                deuda_total -= parte_adri  # Adri le debe a Sara

        gastos_procesados.append({
            'fecha': gasto.fecha,
            'descripcion': gasto.descripcion,
            'monto_total': gasto.monto_total,
            'parte_sara': gasto.monto_total * PORCENTAJE_SARA,
            'parte_adri': gasto.monto_total * PORCENTAJE_ADRI,
            'pagado_por': gasto.pagado_por.username,
            'categoria': categoria_nombre,  # Obtiene el nombre legible
            'color_clase': CATEGORIA_COLORES.get(categoria_nombre, '')
        })

        # Crear diccionario para la leyenda
    leyenda_categorias = {}
    for id_cat, nombre in Gasto.CATEGORIAS:
        leyenda_categorias[nombre] = CATEGORIA_COLORES.get(id_cat, '')


    context = {
        'gastos': gastos_procesados,
        'deuda_total': deuda_total,
        'otro_usuario': otro_usuario,
        'mi_porcentaje': mi_porcentaje * 100,
        'otro_porcentaje': otro_porcentaje * 100,
        'categoria_colores': CATEGORIA_COLORES,
        'usuario_actual': usuario_actual.username
    }
    print("DEBUG - Gastos procesados:", [(g['categoria'], g['color_clase']) for g in gastos_procesados])
    return render(request, 'core/panel_gastos.html', context)

from .models import FondoComun, IngresoFondo

@login_required
def panel_fondos(request):
    PORCENTAJE_SARA = Decimal('0.63')
    PORCENTAJE_ADRI = Decimal('0.37')
    
    # Obtener todos los fondos
    fondos = FondoComun.objects.all()
    
    # Calcular las aportaciones mensuales por persona
    aportaciones = {
        'GASTOS': {'total': 200, 'sara': 200 * PORCENTAJE_SARA, 'adri': 200 * PORCENTAJE_ADRI},
        'COMPRAS': {'total': 200, 'sara': 200 * PORCENTAJE_SARA, 'adri': 200 * PORCENTAJE_ADRI},
        'VIAJES': {'total': 100, 'sara': 100 * PORCENTAJE_SARA, 'adri': 100 * PORCENTAJE_ADRI},
        'AHORRO': {'total': 200, 'sara': 200 * PORCENTAJE_SARA, 'adri': 200 * PORCENTAJE_ADRI},
    }
    
    context = {
        'fondos': fondos,
        'aportaciones': aportaciones,
    }
    
    return render(request, 'core/panel_fondos.html', context)

from django.http import JsonResponse
from decimal import Decimal

@login_required
def actualizar_fondo(request, fondo_id):
    if request.method == 'POST':
        try:
            fondo = FondoComun.objects.get(id=fondo_id)
            nuevo_saldo = Decimal(request.POST.get('saldo', 0))
            fondo.saldo = nuevo_saldo
            fondo.save()
            return JsonResponse({
                'success': True, 
                'nuevo_saldo': float(nuevo_saldo)
            })
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': str(e)
            }, status=400)
    return JsonResponse({'success': False}, status=405)