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