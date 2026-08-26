from django import template

register = template.Library()


@register.simple_tag
def field_widget(field, describedby=''):
    """Render a bound field with the ARIA wiring its template needs.

    `aria-describedby` has to point at the help/error nodes rendered around the
    widget, and those ids are only known in the template, so the widget is
    rendered here rather than with a plain {{ field }}.
    """
    attrs = {}
    if field.errors:
        attrs['aria-invalid'] = 'true'
    if describedby:
        attrs['aria-describedby'] = describedby
    return field.as_widget(attrs=attrs)
