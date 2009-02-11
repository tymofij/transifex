from django import template

import transifex

register = template.Library()

@register.inclusion_tag("common_render_metacount.html")
def render_metacount(list, countable):
    """
    Return meta-style link rendered as superscript to count something.
    
    For example, with list=['a', 'b'] and countable='boxes' return
    the HTML for "2 boxes".
    """
    count = len(list)
    if count > 1:
        return {'count': count,
                'countable': countable}

@register.inclusion_tag("common_homelink.html")
def homelink(text="Home"):
    """Return a link to the homepage."""
    return {'text': text}

@register.simple_tag
def txversion():
    """Return the version of Transifex"""
    return transifex.version
