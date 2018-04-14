import sys
from django import forms
from django.utils.safestring import mark_safe
from attendance_app.models import *
from attendance_app import event_messages
from tinymce.widgets import TinyMCE

# Create your forms here.

class LoginForm(forms.Form):
    """
        Login form
    """
    email = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder':'Email','class':'form-control','autocomplete':"off",'autofocus':True}))
    password = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'placeholder':'Password','class':'form-control','autocomplete':"off"}))


class HorizRadioRenderer(forms.RadioSelect): 
    """
        for radio inline button
    """
    template_name = 'horizontal_select.html'
    def render(self):
        return mark_safe(u'\n'.join([u'%s\n' % w for w in self]))

class EmployeeCreationForm(forms.ModelForm):
    """
        Create Employee form.
    """
    gender_choices = (
        ('male', 'Male'),
        ('female', 'Female'),
    )
    blood_groups_choices = (
        ('op', 'O Positive'),
        ('on', 'O Negative'),
        ('ap', 'A Positive'),
        ('an', 'A Negative'),
        ('bp', 'B Positive'),
        ('bn', 'B Negative'),
        ('abp', 'AB Positive'),
        ('abn', 'AB Negative'),
    )
    username = forms.CharField(required=True,widget=forms.TextInput(attrs={'class':'form-control','autocomplete':'off'}))
    email = forms.EmailField(required=True, widget=forms.TextInput(attrs={'class':'form-control','autocomplete':'off'}))
    gender = forms.ChoiceField(widget = forms.Select(attrs={'class':'form-control'}),choices=(gender_choices))
    contact = forms.CharField(widget = forms.TextInput(attrs={'class':'form-control'}))
    alternative_contact = forms.CharField(widget = forms.TextInput(attrs={'class':'form-control'}))
    blood_grp = forms.ChoiceField(widget = forms.Select(attrs={'class':'form-control'}),choices=(blood_groups_choices))
    present_address = forms.CharField(widget=forms.Textarea(attrs={'class':'form-control','cols':'65','rows':'5'}))
    permanent_address = forms.CharField(widget=forms.Textarea(attrs={'class':'form-control','cols':'65','rows':'5'}))   	
    designation=forms.CharField(widget=forms.TextInput(attrs={'class':'form-control','autocomplete':'off'}))    
    date_of_birth = forms.DateField(input_formats=['%d-%b-%Y'],required = False, widget=forms.TextInput(attrs={'data-date-format':'dd-M-yyyy','class':'form-control dpd1','id': 'dp1','size': 27,'placeholder':'dd-month-yyyy'}))
    date_of_joining = forms.DateField(input_formats=['%d-%b-%Y'],required = False, widget=forms.TextInput(attrs={'data-date-format':'dd-M-yyyy','class':'form-control dpd2','id': 'dp2','size': 27,'placeholder':'dd-month-yyyy'}))    
    img = forms.ImageField(required=False,max_length=100,label='Upload',widget=forms.FileInput(attrs={'title': 'upload img','id':'browsebtn','autocomplete':'off'}))
   
    class Meta:
        model = User
        fields = ['username','email','gender','contact','alternative_contact','blood_grp','present_address','permanent_address','designation','date_of_joining','date_of_birth','img']


class SetPasswordForm(forms.Form):
    """ 
        Set password form
    """
    error_messages = {
        'password_mismatch': "The two password fields didn't match.",
    }
    new_password1 = forms.CharField(label="New password",
                                    widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'New Password'}))
    new_password2 = forms.CharField(label="New password confirmation",
                                    widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'Confirm Password'}))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(SetPasswordForm, self).__init__(*args, **kwargs)

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        return password2

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.user.save()
        return self.user


class PasswordChangeForm(SetPasswordForm):
    """
        Change password form.
    """
    error_messages = dict(SetPasswordForm.error_messages, **{
        'password_incorrect': "Your old password was entered incorrectly. "
                                "Please enter it again.",
    })

class ResendForm(forms.Form):
    """
        Forgot password form.
    """
    uname = forms.CharField(required=False, widget=forms.TextInput(attrs={'autocomplete':'off','class':'form-control','placeholder':'Username'}))
    email = forms.EmailField(required=False, widget=forms.TextInput(attrs={'autocomplete':'off','class':'form-control','placeholder':'Email address'}),help_text='A valid email address, please.')

    def clean_uname(self):
        cleaned_data = super(ResendForm,self).clean()
        uname = cleaned_data.get("uname")
        if uname:
            usr = User.objects.filter(username=uname)
            if not usr:
                raise forms.ValidationError(" Username does not exist")                     
        return uname

    def clean_email(self):
        cleaned_data = super(ResendForm,self).clean()
        email = cleaned_data.get("email")
        if email:
            usr = User.objects.filter(email=email)
            if not usr:
                raise forms.ValidationError("Email-id does not exist")                      
        return email

    def clean(self):
        cleaned_data = super(ResendForm,self).clean()
        uname = cleaned_data.get("uname")
        email = cleaned_data.get("email")
        if not email and not uname:
            if email is not None and uname is not None:
                raise forms.ValidationError("Please enter email-id")                      
        return cleaned_data

class AttendanceEntryForm(forms.ModelForm):
    """
        Attendance entry form.
    """
    leave_choices=(
        ('cl','CASUAL LEAVE'),
        ('sl','SICK LEAVE'),
        ('wh','WORK FROM HOME'),
        ('other','OTHER'),
        )
    one_or_more_choices = (
        ('oneday','one day'),
        ('morethan','More than one day')
        )
    from_date = forms.DateField(input_formats=['%d-%b-%Y'],required = False, widget=forms.TextInput(attrs={'data-date-format':'dd-M-yyyy','class':'form-control dpd1','id': 'dp1','size': 27,'placeholder':'dd-month-yyyy'}))
    to_date = forms.DateField(input_formats=['%d-%b-%Y'],required = False, widget = forms.TextInput(attrs={'data-date-format':'dd-M-yyyy','class':'form-control dpd2','id': 'dp2','size': 27,'placeholder':'dd-month-yyyy'}))
    one_date = forms.DateField(input_formats=['%d-%b-%Y'],required = False, widget = forms.TextInput(attrs={'data-date-format':'dd-M-yyyy','class':'form-control dpd2','id': 'dp1','size': 27,'placeholder':'dd-month-yyyy'}))
    leave_type = forms.ChoiceField(initial='cl',choices=leave_choices,widget=forms.RadioSelect(attrs={'id':'leave_type', 'class':'leave_type'}) )
    one_or_more_days = forms.ChoiceField(initial='oneday',choices=one_or_more_choices,widget=forms.RadioSelect(attrs={'id':'one_more'}) )
    reason = forms.CharField(label='', widget=TinyMCE(attrs={'class':'form-control'}), initial=event_messages.reason_mail_default)
    approver = forms.CharField(label='', widget=forms.TextInput(attrs={'id':'appuser_email','class':'form-control','placeholder': 'E-mail', 'title': 'E-mail','type':'email','autocomplete':'off'}))    
    approved_or_not = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class':'icheckbox_square-blue checkbox_select'}))
    email_subject = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control',"id":"subject","name":"subject"}),initial=event_messages.reason_mail_subject)
    disapprove_reason = forms.CharField(label='Reason',widget=forms.Textarea(attrs={'class':'form-control','placeholder': 'Dis Approve Reason','cols':'65','rows':'5'}))      

    class Meta:
        model = Attendance
        fields = ['from_date','to_date','one_date','leave_type','one_or_more_days','reason','approver','email_subject']

class EventsForm(forms.ModelForm): 
    """
        Event creation form.
    """ 
    event_name = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}))    
    date = forms.DateField(input_formats=['%d-%b-%Y'],required = False, widget=forms.TextInput(attrs={'data-date-format':'dd-M-yyyy','class':'form-control dpd1','id': 'dp1','size': 27,'placeholder':'dd-month-yyyy'}))
    class Meta:
        model = Events
        fields = ['event_name','date']


class OrganizationForm(forms.ModelForm):  
    """
        Organization form
    """
    name = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}))    
    send_email = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}))    
    logo = forms.ImageField(required=False,max_length=100,label='Upload',widget=forms.FileInput(attrs={'title': 'upload logo','id':'logo','autocomplete':'off'}))
    class Meta:
        model = Organization
        fields = ['name','send_email', 'logo']


class TaskForm(forms.ModelForm):
    """
        Task form.
    """
    priority_choices = (
        ('High','High'),
        ('Medium','Medium'),
        ('Low','Low')
        )
    assigned = forms.ModelMultipleChoiceField(widget=forms.SelectMultiple( attrs={'class':'form-control select2','id':'tagPicker','multiple':'multiple'}),queryset=User.objects.all())    
    name = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}))
    desc = forms.CharField(label='', widget=TinyMCE(attrs={'class':'form-control'}), initial=event_messages.reason_mail_default)
    priority = forms.ChoiceField(initial='hight',choices=priority_choices,widget=forms.RadioSelect(attrs={'id':'one_more'}) )
    work_in_task = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class':'icheckbox_square-blue checkbox_select'}))
    work_in_status = forms.CharField(required=False,label='', widget=TinyMCE(attrs={'class':'form-control'}), initial=event_messages.reason_mail_default)
    completed_task = models.BooleanField(default=False)
    complete_status = forms.CharField(required=False,label='', widget=TinyMCE(attrs={'class':'form-control'}), initial=event_messages.reason_mail_default)
    cancel_task = models.BooleanField(default=False)
    cancel_status = forms.CharField(required=False,label='', widget=TinyMCE(attrs={'class':'form-control'}), initial=event_messages.reason_mail_default)

    class Meta:
        model = Task
        fields = ['assigner','assigned','name','desc','priority','pending_task','work_in_task','work_in_status','completed_task','complete_status','cancel_task','cancel_status']


class UpdateTaskForm(forms.ModelForm):  
    """
        Task form.
    """  
    work_in_task = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class':'icheckbox_square-blue checkbox_select'}))
    work_in_status = forms.CharField(required=False,label='', widget=TinyMCE(attrs={'class':'form-control'}), initial=event_messages.reason_mail_default)
    completed_task = models.BooleanField(default=False)
    complete_status = forms.CharField(required=False,label='', widget=TinyMCE(attrs={'class':'form-control'}), initial=event_messages.reason_mail_default)
    cancel_task = models.BooleanField(default=False)
    cancel_status = forms.CharField(required=False,label='', widget=TinyMCE(attrs={'class':'form-control'}), initial=event_messages.reason_mail_default)

    class Meta:
        model = Task
        fields = ['work_in_task','work_in_status','completed_task','complete_status','cancel_task','cancel_status']

# End-Of-File