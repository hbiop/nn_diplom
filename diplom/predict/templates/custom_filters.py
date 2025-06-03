from django import template

register = template.Library()

@register.filter(name='status_color')
def status_color(status):
    colors = {
        'pending': 'secondary',
        'running': 'info',
        'completed': 'success',
        'failed': 'danger'
    }
    return colors.get(status, 'secondary')