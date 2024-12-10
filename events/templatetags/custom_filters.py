from django import template
from django.utils.text import capfirst

register = template.Library()


@register.filter
def split(path):
    """
    Convert URL path to readable text
    Example: "/events/2024/" -> "2024"
    """
    # Remove leading/trailing slashes and split
    segments = [s for s in path.strip("/").split("/") if s]

    # Return last segment if exists, otherwise empty string
    if segments:
        # Replace hyphens with spaces and capitalize
        return capfirst(segments[-1].replace("-", " "))
    return ""
