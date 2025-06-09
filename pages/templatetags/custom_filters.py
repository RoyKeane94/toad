from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using the given key."""
    if dictionary is None:
        return []
    result = dictionary.get(key, [])
    return result if result is not None else [] 

@register.filter
def cell_key(row_pk, col_pk):
    """Create a cell key by combining row and column primary keys."""
    return f"{row_pk}_{col_pk}" 