# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytz
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager,PermissionsMixin

# Create your models here.

class BaseModel(models.Model):
	"""
		Base model for all the below models
	"""
	created_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)
	edited_on = models.DateTimeField(auto_now=True, null=True, blank=True)

	class Meta:
		abstract = True

class Organization(BaseModel):
	"""
		Organization model
	"""
	name = models.CharField(max_length=200, unique=True)
	logo = models.ImageField(upload_to="logo/%Y/%m/%d")
	send_email  = models.EmailField(null=True, blank=True)

	def __unicode__(self):
		return self.name

	def get_logo_filename(i):
		ipath = settings.MEDIA_ROOT
		logopath = os.path.join(ipath,i.logo.name)
		return str(logopath)

class UserManager(BaseUserManager):
	"""
		Customizing the default user model.
	"""
	def _create_user(self, username, org, email, password, is_staff, is_superuser, **extra_fields):
		now = timezone.now()
		if not username:
			raise ValueError(('The given username must be set'))
		email = self.normalize_email(email)
		user = self.model(username=username, email=email, org=org,first_name=username.title(),
			is_staff=is_staff, is_active=True,is_superuser=is_superuser, last_login=now,
			date_of_joining=now, **extra_fields)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_user(self, username, email=None, password=None, **extra_fields):
		user = self._create_user(username, email, password, False, False,**extra_fields)
		return user

	def create_superuser(self, username, email, password, **extra_fields):
		try:
			org = Organization.objects.get(id=1)
		except:
			org_dict = {
				'name':'Admin Organization',
			}
			org = Organization.objects.create(**org_dict)
		user = self._create_user(username, org, email, password, True, True,**extra_fields)
		user.is_active = True
		user.is_staff = True
		user.save(using=self._db)
		return user



class User(AbstractBaseUser, PermissionsMixin):
	"""
		Overiding the default user model.
	"""
	org = models.ForeignKey(Organization)
	username = models.CharField(('username'), max_length=30, unique=False,error_messages={'unique':"This email has already been added."})
	first_name = models.CharField(('first name'), max_length=30, blank=True, null=True)
	last_name = models.CharField(('last name'), max_length=30, blank=True, null=True)
	email = models.EmailField(('email address'),unique=True, max_length=255)
	is_staff = models.BooleanField(('staff status'), default=False)
	is_active = models.BooleanField(('active'), default=True)
	contact = models.CharField(max_length=20,blank=True,null=True)
	alternative_contact = models.CharField(max_length=20,blank=True,null=True)
	blood_grp =models.CharField(max_length=25,blank=True,null=True)
	present_address = models.TextField(blank=True,null=True)
	permanent_address = models.TextField(blank=True,null=True)	
	gender = models.CharField(max_length=9,blank=True,null=True)	
	designation = models.CharField(max_length=60,blank=True,null=True)
	id_card_no=models.IntegerField(null=True,blank=True,unique=True)	
	date_of_birth = models.DateField(('date Birth'), blank=True, null=True)
	date_of_joining = models.DateField(('date joining'), blank=True, null=True)
	date_of_leaving = models.DateField(('date leaving'), blank=True, null=True)
	no_of_cl =models.IntegerField(null=True,blank=True,default=12)
	no_of_sl =models.IntegerField(null=True,blank=True,default=12)
	no_of_wh =models.IntegerField(null=True,blank=True,default=12)
	oth =models.IntegerField(null=True,blank=True)
	img = models.ImageField(null=True,blank=True,upload_to="gallery")
	objects = UserManager()
	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ['username',]

	class Meta:
		verbose_name = ('user')
		verbose_name_plural = ('users')

	def get_full_name(self):
		full_name = '%s %s' % (self.first_name, self.last_name)
		return full_name.strip()

	def get_short_name(self):
		return self.first_name


class Attendance(BaseModel):
	"""
		User attendance model.
	"""
	username = models.ForeignKey(User)	
	one_or_more_days = models.CharField(max_length=25,null=True,blank=True)
	leave_type = models.CharField(max_length=25,null=True,blank=True)
	email_subject = models.CharField(max_length=250,null=True,blank=True)
	approver =models.CharField(max_length=100,null=True,blank=True)
	approved_or_not =models.BooleanField(default=False)
	waiting =models.BooleanField(default=True)
	reason=models.TextField(null=True,blank=True)
	disapprove_reason=models.TextField(null=True,blank=True)
	one_date=models.DateField(null=True,blank=True)
	from_date=models.DateField(null=True,blank=True)
	to_date=models.DateField(null=True,blank=True)
	compensated=models.IntegerField(null=True,blank=True)
	month = models.CharField(max_length=20,null=True,blank=True)
	org = models.ForeignKey(Organization, null=True, blank=True,editable=False)

	def __unicode__(self):
		return self.username

class Events(models.Model):
	"""
		Events model like holidays.
	"""
	event_name = models.CharField(max_length=250,null=True,blank=True)	
	date = models.DateField(null=True,blank=True)
	org = models.ForeignKey(Organization, null=True, blank=True,editable=False)


	def __unicode__(self):
		return self.event_name


class Task(models.Model):
	"""
		Task Model
	"""
	name = models.CharField(max_length=250,null=True,blank=True)
	assigner = models.CharField(max_length=100,null=True,blank=True)
	assigned = models.CharField(max_length=100,null=True,blank=True)
	desc = models.TextField(null=True,blank=True)
	priority = models.CharField(max_length=25,null=True,blank=True)
	pending_task = models.BooleanField(default=True)
	work_in_task = models.BooleanField(default=False)
	work_in_status = models.TextField(null=True,blank=True)
	completed_task = models.BooleanField(default=False)
	complete_status = models.TextField(null=True,blank=True)
	cancel_task = models.BooleanField(default=False)
	cancel_status = models.TextField(null=True,blank=True)
	org = models.ForeignKey(Organization, null=True, blank=True,editable=False)

	def __unicode__(self):
		return self.name

# End-Of-File