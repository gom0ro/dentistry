from django import template

register = template.Library()

@register.filter
def chr_(value):
    return chr(int(value))
