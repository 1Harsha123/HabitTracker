# Home/templatetags/form_tags.py
from django import template
from datetime import datetime

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """Add CSS class to form field"""
    return field.as_widget(attrs={"class": css_class})

@register.filter(name='timeformat')
def timeformat(timestamp):
    """Convert timestamp to HH:MM:SS format"""
    if not timestamp:
        return "00:00:00"
    
    try:
        # If timestamp is in seconds, convert to datetime
        dt = datetime.fromtimestamp(int(timestamp))
        return dt.strftime("%H:%M:%S")
    except (ValueError, TypeError):
        return "00:00:00"

# form_tags.py
@register.filter(name='durationformat')
def durationformat(value, format_type='simple'):
    """Format duration in seconds to readable format"""
    if not value:
        return "0s"
    
    try:
        seconds = int(value)
        
        if format_type == 'full':
            # Always return HH:MM:SS
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            # Simple format: 1h 30m 15s
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            
            if hours > 0:
                return f"{hours}h {minutes}m {secs}s"
            elif minutes > 0:
                return f"{minutes}m {secs}s"
            else:
                return f"{secs}s"
    except (ValueError, TypeError):
        return "0s"