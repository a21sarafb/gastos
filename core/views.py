from django.shortcuts import render
from .models import UserProfile, Categoria, Gasto

from django.shortcuts import redirect
from django.contrib.auth.models import User
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Gasto, Categoria
from .forms import GastoForm, RegistroForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

@login_required
def lista_gastos(request):
    gastos = Gasto.objects.filter(pagado_por=request.user).order_by('-fecha')
    return render(request, 'core/lista_gastos.html', {'gastos': gastos})

@login_required
def crear_gasto(request):
    if request.method == 'POST':
        form = GastoForm(request.POST)
        if form.is_valid():
            gasto = form.save(commit=False)
            gasto.pagado_por = request.user
            perfil_pagador = request.user.userprofile
            otro = perfil_pagador.get_pareja()
            perfil_otro = otro.userprofile
            gasto.porcentaje_pagador = perfil_pagador.porcentaje_actual
            gasto.porcentaje_otro = perfil_otro.porcentaje_actual
            gasto.deuda_otro = gasto.monto_total * (perfil_otro.porcentaje_actual / 100)
            gasto.save()
            return redirect('lista_gastos')
    else:
        form = GastoForm()
    return render(request, 'core/crear_gasto.html', {'form': form})

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
