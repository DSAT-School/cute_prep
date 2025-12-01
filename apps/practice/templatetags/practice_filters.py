"""
Custom template filters for practice app.
"""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Get item from dictionary by key.
    
    Usage: {{ dict|get_item:key }}
    """
    if dictionary is None:
        return []
    return dictionary.get(key, [])
