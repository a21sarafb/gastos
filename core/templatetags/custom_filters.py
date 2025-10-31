from django import template
from django.utils.http import urlencode



"""
Filtros personalizados utilizados en las plantillas.

Se define un filtro ``absolute`` que devuelve el valor absoluto y un filtro
``get_item`` que permite obtener un elemento de un diccionario usando una
clave dinámica (útil para acceder a diccionarios en plantillas de Django).

Este fichero debe mantenerse dentro del paquete ``templatetags`` para que
Django pueda cargar automáticamente los filtros.
"""

register = template.Library()


@register.filter(name='absolute')
def absolute(value):
    """Retorna el valor absoluto de un número."""
    try:
        return abs(float(value))
    except (TypeError, ValueError):
        return value


@register.filter
def get_item(dictionary, key):
    """Devuelve el valor asociado a ``key`` en ``dictionary`` o ``None``."""
    return dictionary.get(key)


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    query = context['request'].GET.copy()
    
    # Limpiar los valores de lista
    for k in query.keys():
        if isinstance(query[k], list):
            query[k] = query[k][0]
    
    # Actualizar con nuevos valores
    for k, v in kwargs.items():
        query[k] = str(v)
    
    return '?' + urlencode(query)