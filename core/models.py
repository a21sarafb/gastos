from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
import logging


"""
Model definitions for the gastos application.

Se añaden dos ampliaciones importantes respecto al código base del repositorio:

1. **Nuevo tipo de fondo** ``SUPERMERCADO``: permite llevar un control
   independiente del saldo destinado a la compra de comida y productos de
   supermercado. Este nuevo valor queda registrado en ``TIPOS_FONDO`` y se
   mostrará en el panel de fondos como «Supermercado».

2. **Nueva categoría de gasto** ``Compras piso``: dentro de la lista
   ``CATEGORIAS`` se incorpora una clave adicional (``'6'``) para agrupar
   desembolsos destinados a mobiliario, arreglos o compras puntuales del
   hogar. Esta ampliación garantiza que los usuarios puedan distinguir
   claramente entre gastos recurrentes del piso y compras de objetos.

Además se mantiene la relación entre ``Gasto`` y ``FondoComun``, de modo que
cuando un gasto vaya vinculado a un fondo se pueda descontar del saldo de
dicho fondo.
"""

logger = logging.getLogger(__name__)


class Categoria(models.Model):
    """Modelo sencillo para almacenar categorías personalizadas.

    Aunque no se utiliza directamente en el código actual, este modelo
    permanece por compatibilidad y posibles extensiones futuras.
    """
    nombre = models.CharField(max_length=100)

    def __str__(self) -> str:  # pragma: no cover - representación trivial
        return self.nombre


class UserProfile(models.Model):
    """Perfil extendido de usuario para almacenar información adicional.

    Actualmente solamente se utiliza el campo ``porcentaje_actual`` para
    representar la participación del usuario en gastos compartidos. Se
    define una relación uno a uno con ``django.contrib.auth.models.User``.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    porcentaje_actual = models.FloatField(default=50)

    def __str__(self) -> str:  # pragma: no cover - representación trivial
        return self.user.username

    def get_pareja(self):
        """Devuelve la otra persona registrada en el sistema.

        Se asume que el sistema está pensado para dos usuarios; por tanto se
        devuelve el primer usuario distinto al actual.
        """
        return User.objects.exclude(id=self.user.id).first()


class FondoComun(models.Model):
    """Modelo que representa un fondo común de la pareja.

    Cada fondo almacena el tipo (por ejemplo, «Gastos del piso» o
    «Supermercado»), el saldo disponible y la fecha de última actualización.
    Los tipos se definen mediante la constante ``TIPOS_FONDO``. Se ha
    añadido un nuevo tipo ``SUPERMERCADO`` para poder gestionar el dinero
    destinado específicamente a la compra de alimentos.
    """

    TIPOS_FONDO = [
        ('GASTOS', 'Gastos del piso'),
        ('COMPRAS', 'Compras del piso'),
        ('VIAJES', 'Fondo para viajes'),
        ('AHORRO', 'Ahorro de pareja'),
        ('SUPERMERCADO', 'Supermercado'),  # Nuevo fondo para supermercado
    ]

    tipo = models.CharField(max_length=20, choices=TIPOS_FONDO)
    saldo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ultima_actualizacion = models.DateField(auto_now=True)

    class Meta:
        verbose_name = 'Fondo común'
        verbose_name_plural = 'Fondos comunes'

    def __str__(self) -> str:  # pragma: no cover - representación trivial
        return f"{self.get_tipo_display()} - Saldo: {self.saldo}€"


class IngresoFondo(models.Model):
    """Registro de aportaciones realizadas a un fondo común.

    Se guarda la referencia al fondo, la cantidad ingresada y quién ha
    aportado el dinero. La fecha se asigna automáticamente al crearse
    el registro.
    """

    fondo = models.ForeignKey(FondoComun, on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Ingreso a fondo'
        verbose_name_plural = 'Ingresos a fondos'


class Gasto(models.Model):
    """Modelo que representa un gasto individual.

    Cada gasto contiene una descripción, la cantidad total, una fecha,
    una categoría seleccionada de la lista ``CATEGORIAS``, el usuario que
    pagó y opcionalmente el fondo del que se descontará el importe.

    Se amplía ``CATEGORIAS`` con una entrada para «Compras piso» (clave
    ``'6'``) para diferenciar los gastos en muebles o arreglos puntuales
    respecto a los gastos recurrentes del piso.
    """

    CATEGORIAS = [
        ('1', 'Supermercado'),
        ('2', 'Viajes'),
        ('3', 'Gastos piso'),
        ('4', 'Ocio'),
        ('5', 'Otros'),
        ('6', 'Compras piso'),  # Nueva categoría para compras de mobiliario
    ]

    descripcion = models.CharField(max_length=200)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField(auto_now_add=False)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS)
    pagado_por = models.ForeignKey(User, on_delete=models.CASCADE)
    fondo = models.ForeignKey(FondoComun, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-fecha']


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Crea automáticamente un perfil de usuario asociado al User.

    Django no genera ``UserProfile`` por defecto; esta señal se asegura de
    crear una entrada al registrar un nuevo usuario.
    """
    if created:
        UserProfile.objects.create(user=instance)


# core/models.py
from django.db import connection, OperationalError, ProgrammingError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    try:
        # si la DB aún no tiene la tabla (primer arranque), salimos sin hacer nada
        if 'core_userprofile' not in connection.introspection.table_names():
            return
        # si existe, intentamos guardar
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)
    except (OperationalError, ProgrammingError):
        # base aún sin migrar: no bloqueamos el login
        pass
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=IngresoFondo)
def actualizar_saldo_fondo(sender, instance, created, **kwargs):
    if created:
        fondo = instance.fondo
        fondo.saldo += instance.cantidad
        fondo.save()
