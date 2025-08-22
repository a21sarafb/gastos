from django import template

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
    return dictionary.get(key)