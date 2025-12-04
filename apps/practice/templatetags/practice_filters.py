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


@register.filter
def get_attr(obj, attr_name):
    """
    Get attribute from object.
    
    Usage: {{ obj|get_attr:'attribute_name' }}
    """
    try:
        return getattr(obj, attr_name, None)
    except:
        return None


@register.filter
def sum_attr(items, attr_name):
    """
    Sum a specific attribute from a list of dictionaries.
    
    Usage: {{ items|sum_attr:'total_attempted' }}
    """
    try:
        return sum(item.get(attr_name, 0) for item in items)
    except:
        return 0


@register.filter
def calculate_domain_accuracy(skills):
    """
    Calculate overall accuracy for a domain based on its skills.
    
    Usage: {{ skills|calculate_domain_accuracy }}
    """
    try:
        total_attempted = sum(skill.get('total_attempted', 0) for skill in skills)
        total_correct = sum(skill.get('correct_answers', 0) for skill in skills)
        
        if total_attempted > 0:
            return round((total_correct / total_attempted) * 100, 1)
        return 0
    except:
        return 0
