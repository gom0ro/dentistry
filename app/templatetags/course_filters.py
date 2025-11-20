# app/templatetags/course_filters.py
from django import template

register = template.Library()

@register.filter
def score_class(value):
    """
    Присваивает CSS-класс по проценту теста
    """
    try:
        value = float(value)
    except (ValueError, TypeError):
        return ''
    if value >= 90:
        return 'score-excellent'
    elif value >= 75:
        return 'score-good'
    elif value >= 50:
        return 'score-average'
    else:
        return 'score-bad'
