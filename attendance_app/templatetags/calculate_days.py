from django import template
register=template.Library()
from datetime import datetime
from datetime import date, timedelta
from attendance_app.views import calculate_days

@register.filter(name='calculate_days')
def calculate_days2(from_days,to_days):
	"""
		Calculate the days.
	"""
	return calculate_days(from_days,to_days)