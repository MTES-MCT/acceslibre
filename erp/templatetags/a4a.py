from django.template import Library


register = Library()


@register.filter(name="pluriel")
def pluriel(n):
    "Because not everyone speaks English, this is for French plural."
    try:
        return "s" if int(n) > 1 else ""
    except (TypeError, ValueError):
        return ""
