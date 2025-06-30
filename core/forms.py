from django import forms
from .models import Gasto
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class GastoForm(forms.ModelForm):
    class Meta:
        model = Gasto
        fields = ['descripcion', 'monto_total', 'categoria']

class RegistroForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']