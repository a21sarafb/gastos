from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import UserProfile, Categoria, Gasto

admin.site.register(UserProfile)
admin.site.register(Categoria)
admin.site.register(Gasto)
