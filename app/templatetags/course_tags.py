from django import template

register = template.Library()

@register.filter
def score_class(percentage):
    """Возвращает CSS класс для результата теста"""
    if percentage >= 90:
        return "excellent"
    elif percentage >= 70:
        return "good"
    elif percentage >= 50:
        return "average"
    else:
        return "poor"