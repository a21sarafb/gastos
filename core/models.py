from django.db import models

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    porcentaje_actual = models.FloatField(default=50)  # % que aporta este usuario

    def __str__(self):
        return self.user.username
    
    def get_pareja(self):
        # Asume que solo hay 2 usuarios en el sistema
        return User.objects.exclude(id=self.user.id).first()

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Gasto(models.Model):
    fecha = models.DateField(auto_now_add=True)
    descripcion = models.TextField()
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    pagado_por = models.ForeignKey(User, on_delete=models.CASCADE)
    porcentaje_pagador = models.FloatField()
    porcentaje_otro = models.FloatField()
    deuda_otro = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.descripcion} - {self.monto_total} €"

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)