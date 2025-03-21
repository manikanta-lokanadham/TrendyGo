from django import template
from django.template.defaultfilters import stringfilter
from django.conf import settings
import os

register = template.Library()

@register.simple_tag
def get_empty_state_image():
    """
    Returns the path to the empty state image for orders.
    """
    # You can customize this path based on your static files structure
    return os.path.join(settings.STATIC_URL, 'images', 'empty-state.png') 