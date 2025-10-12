import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.query import QuerySet
from django.forms.models import model_to_dict
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using the given key."""
    if dictionary is None:
        return []
    result = dictionary.get(key, [])
    return result if result is not None else [] 

@register.filter(name='to_json')
def to_json(queryset):
    """
    Serializes a queryset into a JSON object.
    """
    # If it's a queryset, we need to extract the values.
    if hasattr(queryset, 'values'):
        data = list(queryset.values('pk', 'name'))
        # Rename 'pk' to 'id' for consistency with JavaScript
        for item in data:
            item['id'] = item.pop('pk')
        return json.dumps(data)
    
    # For other types, try to serialize directly.
    try:
        return json.dumps(queryset)
    except TypeError:
        return json.dumps({})

@register.filter(name='cell_key')
def cell_key(row_pk, col_pk):
    return f"{row_pk}_{col_pk}"

@register.filter(name='get_avatar_color')
def get_avatar_color(user_id):
    """Get a color for user avatar based on their ID."""
    colors = [
        '#FF6B6B',  # Red
        '#4ECDC4',  # Teal
        '#45B7D1',  # Blue
        '#FFA07A',  # Light Salmon
        '#98D8C8',  # Mint
        '#F7DC6F',  # Yellow
        '#BB8FCE',  # Purple
        '#85C1E2',  # Sky Blue
        '#F8B88B',  # Peach
        '#52B788'   # Green
    ]
    try:
        index = int(user_id) % len(colors)
        return colors[index]
    except (ValueError, TypeError):
        return colors[0]

@register.filter(name='get_initials')
def get_initials(name):
    """
    Get initials from a name.
    For full names (2+ words): First letter of first word + first letter of last word
    For single names: Just the first letter
    """
    if not name:
        return ''
    
    name = str(name).strip()
    words = name.split()
    
    if len(words) >= 2:
        # First initial of first word + first initial of last word
        return (words[0][0] + words[-1][0]).upper()
    else:
        # Just the first letter for single names
        return name[0].upper() if name else '' 