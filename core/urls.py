from django.urls import path
from . import views
urlpatterns = [
    path('lista/', views.lista_gastos, name='lista_gastos'),
    path('nuevo/', views.crear_gasto, name='crear_gasto'),
    path('login/', views.login_usuario, name='login'),
    path('logout/', views.logout_usuario, name='logout'),
    path('registro/', views.registro_usuario, name='registro'),
    path('', views.panel_gastos, name='panel_gastos'),
    path('fondos/', views.panel_fondos, name='panel_fondos'),

]
