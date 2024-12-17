from django import template
from django.utils.text import capfirst

register = template.Library()

@register.filter
def split(path):
    """
    Convert URL path to readable segments
    Example: "/events/2024/" -> ["Events", "2024"]
    """
    # Remove leading/trailing slashes and split
    segments = [s for s in path.strip("/").split("/") if s]
    
    # Convert segments to readable format
    return [capfirst(segment.replace("-", " ")) for segment in segments]

@register.filter(name="get_item")
def get_item(dictionary, key):
    """
    Get an item from a dictionary using bracket notation.
    Usage: {{ mydict|get_item:item.id }}
    """
    return dictionary.get(key)
