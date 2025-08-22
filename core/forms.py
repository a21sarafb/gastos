from django import forms
from .models import Gasto
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class GastoForm(forms.ModelForm):
    pagado_por = forms.ModelChoiceField(
        queryset=User.objects.filter(username__in=['sara', 'adri']),
        label='Pagado por'
    )

    class Meta:
        model = Gasto
        fields = ['descripcion', 'monto_total', 'categoria', 'fecha', 'pagado_por']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'monto_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
        }

class RegistroForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']