from django.urls import path
from . import views


"""
URLConf de la aplicación core.

Incluye rutas para el listado de gastos, creación de gastos, login,
registro y paneles de gastos y fondos. Se añade una ruta específica
``fondos/actualizar/<int:fondo_id>/`` para permitir actualizar el saldo
de un fondo común mediante una petición POST (utilizado por el diálogo
AJAX en el panel de fondos).
"""

urlpatterns = [
    path('lista/', views.lista_gastos, name='lista_gastos'),
    path('nuevo/', views.crear_gasto, name='crear_gasto'),
    path('login/', views.login_usuario, name='login'),
    path('logout/', views.logout_usuario, name='logout'),
    path('registro/', views.registro_usuario, name='registro'),
    path('', views.panel_gastos, name='panel_gastos'),
    path('fondos/', views.panel_fondos, name='panel_fondos'),
    path('resumen/', views.resumen_finanzas, name='resumen'),
    # Ruta para actualizar el saldo de un fondo
    path('fondos/actualizar/<int:fondo_id>/', views.actualizar_fondo, name='actualizar_fondo'),
]