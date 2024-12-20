from django import template
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def daterange(start_date, end_date):
    """Generate a range of dates between start_date and end_date (inclusive)"""
    if not end_date:
        return [start_date]
        
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)
    return dates
