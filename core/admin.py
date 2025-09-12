from django.contrib import admin

from .models import UserProfile, Categoria, Gasto, FondoComun, IngresoFondo, GastoRecurrente, ObjetivoAhorro


"""
Configuración de administración para los modelos de la aplicación.

Se registran todos los modelos relevantes para poder gestionarlos desde el
panel de administración de Django. Incluir ``FondoComun`` e ``IngresoFondo``
en el admin permite comprobar y ajustar manualmente los fondos y sus
aportaciones.
"""

admin.site.register(UserProfile)
admin.site.register(Categoria)
admin.site.register(Gasto)
admin.site.register(FondoComun)
admin.site.register(IngresoFondo)
@admin.register(GastoRecurrente)
class GastoRecurrenteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'monto', 'periodicidad', 'categoria', 'fondo', 'prorratear', 'activo')

@admin.register(ObjetivoAhorro)
class ObjetivoAhorroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'monto_objetivo', 'aporte_mensual', 'fondo_destino', 'activo')
