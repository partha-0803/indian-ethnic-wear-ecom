from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def absolute_url(context, path=""):
    request = context.get("request")
    if not request:
        return path or "/"
    if path.startswith("http"):
        return path
    return request.build_absolute_uri(path or "/")


@register.simple_tag
def stars(rating):
    rating = int(rating or 0)
    filled = "★" * max(0, min(5, rating))
    empty = "☆" * (5 - max(0, min(5, rating)))
    return mark_safe(f'<span class="text-gold tracking-wider" aria-label="{rating} out of 5">{escape(filled + empty)}</span>')
