from django.db import models

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    porcentaje_actual = models.FloatField(default=50)

    def __str__(self):
        return self.user.username
    
    def get_pareja(self):
        return User.objects.exclude(id=self.user.id).first()

import logging

logger = logging.getLogger(__name__)

class FondoComun(models.Model):
    TIPOS_FONDO = [
        ('GASTOS', 'Gastos del piso'),
        ('COMPRAS', 'Compras del piso'),
        ('VIAJES', 'Fondo para viajes'),
        ('AHORRO', 'Ahorro de pareja'),
    ]
    
    tipo = models.CharField(max_length=20, choices=TIPOS_FONDO)
    saldo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ultima_actualizacion = models.DateField(auto_now=True)
    
    class Meta:
        verbose_name = 'Fondo común'
        verbose_name_plural = 'Fondos comunes'
    
    def __str__(self):
        return f"{self.get_tipo_display()} - Saldo: {self.saldo}€"

class IngresoFondo(models.Model):
    fondo = models.ForeignKey(FondoComun, on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = 'Ingreso a fondo'
        verbose_name_plural = 'Ingresos a fondos'
class Gasto(models.Model):
    CATEGORIAS = [
        ('1', 'Supermercado'),
        ('2', 'Viajes'),
        ('3', 'Gastos piso'),
        ('4', 'Ocio'),
        ('5', 'Otros'),
    ]
    descripcion = models.CharField(max_length=200)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField(auto_now_add=False)  # Cambiamos auto_now_add a False
    categoria = models.CharField(max_length=20, choices=CATEGORIAS)
    pagado_por = models.ForeignKey(User, on_delete=models.CASCADE)
    fondo = models.ForeignKey(FondoComun, on_delete=models.CASCADE, null=True, blank=True)
    class Meta:
        ordering = ['-fecha']

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)