import os
import sys
from datetime import *
import celery
from celery.result import AsyncResult
from celery.decorators import periodic_task
from django.conf import settings
from django.core.mail import send_mail,EmailMultiAlternatives
from django.template.loader import render_to_string
from attendance_app import event_messages
from attendance_app.models import *



@periodic_task(run_every=timedelta(seconds=5))
def birthday_reminder():
	try:
		time = date.today()        
		all_users = User.objects.filter(is_superuser=False)
		for usr in all_users:
			if usr.date_of_birth.day == time.day and usr.date_of_birth.month == time.month:
				user_name= usr.username
				to_email= usr.email
				sent_from = "Company <noreply@gmail.com>"
                mail_subject = "Birthday"                                                    
                html_content = render_to_string('mail_templates/birthday.html',{"user_name":user_name})
                msg = EmailMultiAlternatives(mail_subject,'',sent_from,[to_email])
                msg.attach_alternative(html_content, "text/html")
                msg.send()
	except Exception, e:
		print e
		
@periodic_task(run_every=timedelta(days=1))		
def birthday_reminder_others():
	try:
		time = date.today()        
		all_users = User.objects.filter(is_superuser=False)
		for usr in all_users:
			if usr.date_of_birth.day == time.day and usr.date_of_birth.month == time.month:
				user_name= usr.username
				to_email= usr.email
				sent_from = "Company <noreply@gmail.com>"
                mail_subject = "Birthday"                                                    
                html_content = render_to_string('mail_templates/birthday.html',{"user_name":user_name})
                msg = EmailMultiAlternatives(mail_subject,'',sent_from,[to_email])
                msg.attach_alternative(html_content, "text/html")
                msg.send()
	except Exception, e:
		print e

# End-Of-File
