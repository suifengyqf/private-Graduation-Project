from django import template

register = template.Library()

@register.filter
def extract_filename(value):
    return value.split('/')[-1]