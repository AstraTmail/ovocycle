import builtins
from django import template

register = template.Library()


@register.filter
def col_letter(value):
    """Convertit un numéro de colonne en lettre : 1→A, 2→B, 3→C, 4→D, 5→E"""
    try:
        return builtins.chr(64 + int(value))
    except Exception:
        return str(value)


@register.filter
def get_item(dictionary, key):
    """Accès dict dans les templates: {{ dict|get_item:key }}"""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def chr(value):
    """Convertit un entier en lettre: {{ 1|chr }} → A (1=A, 2=B…)"""
    try:
        return builtins.chr(int(value) + 64)
    except Exception:
        return str(value)


@register.filter
def percent_bar_width(value, max_val=100):
    """Retourne la largeur en % pour une barre de progression."""
    try:
        return min(100, max(0, int((float(value) / float(max_val)) * 100)))
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def status_color(status):
    """Retourne la classe Tailwind correspondant au statut d'un œuf."""
    colors = {
        'pending':     'bg-amber-100 text-amber-700',
        'fertile':     'bg-green-100 text-green-700',
        'clear':       'bg-gray-100 text-gray-500',
        'dead_embryo': 'bg-red-100 text-red-600',
        'cracked':     'bg-orange-100 text-orange-600',
        'hatched':     'bg-emerald-100 text-emerald-700',
        'failed':      'bg-red-200 text-red-700',
        'removed':     'bg-gray-200 text-gray-500',
    }
    return colors.get(status, 'bg-gray-100 text-gray-500')


@register.filter
def get_initials(user):
    """Retourne les initiales d'un utilisateur : 'Jean Dupont' → 'JD'"""
    if not user:
        return '?'
    full = user.get_full_name() if hasattr(user, 'get_full_name') else str(user)
    if full.strip():
        parts = full.strip().split()
        return ''.join(p[0].upper() for p in parts[:2])
    return str(user)[:1].upper()
    colors = {
        'active':    'bg-green-100 text-green-700',
        'lockdown':  'bg-amber-100 text-amber-700',
        'hatching':  'bg-orange-100 text-orange-700',
        'completed': 'bg-blue-100 text-blue-700',
        'aborted':   'bg-gray-100 text-gray-500',
    }
    return colors.get(status, 'bg-gray-100 text-gray-500')



@register.simple_tag
def incubation_day_label(day):
    """Retourne un label lisible pour un jour d'incubation."""
    labels = {7: 'Mirage 1', 14: 'Mirage 2', 18: 'Mirage 3 / Lockdown', 21: 'Éclosion'}
    return labels.get(day, f'J{day}')

@register.filter
def batch_status_color(status):
    colors = {
        'active':    'bg-green-100 text-green-700',
        'lockdown':  'bg-amber-100 text-amber-700',
        'hatching':  'bg-orange-100 text-orange-700',
        'completed': 'bg-blue-100 text-blue-700',
        'aborted':   'bg-gray-100 text-gray-500',
    }
    return colors.get(status, 'bg-gray-100 text-gray-500')