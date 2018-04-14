import sys, os
import xhtml2pdf.pisa as pisa
from StringIO import StringIO
from business_calendar import Calendar, MO, TU, WE, TH, FR
from calendar import monthrange
from datetime import date, timedelta,datetime
from django.shortcuts import render , render_to_response , get_object_or_404,redirect,resolve_url
from django.http import *
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.sites.models import Site
from django.conf import settings
from django.core.mail import EmailMultiAlternatives,send_mail
from django.core.exceptions import ObjectDoesNotExist,MultipleObjectsReturned
from django.utils.http import int_to_base36, urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.dateformat import DateFormat
from django.template import RequestContext, loader
from django.template.context import Context
from django.template.loader import render_to_string, get_template
from django.template.response import TemplateResponse
from attendance_app.forms import *
from attendance_app.models import *
from attendance_app import event_messages


# Create your views here.

def calculate_days(from_days,to_days):
    """
     This function using to calculate the working days excepy holidays and weekends.
    """
    delta = to_days-from_days
    public_holidays_count = 0
    public_holidays = Events.objects.values_list('date',flat=True)
    l = []
    for i in range(delta.days + 1):
        l.append(from_days + timedelta(days=i))
    for a in public_holidays:
        if a in l:
            public_holidays_count += 1
    all_days = [from_days + timedelta(days=x) for x in range((to_days-from_days).days + 1)]
    weekends = sum(1 for d in all_days if d.weekday()>=5)
    working_days = sum(1 for d in all_days if d.weekday() < 5)
    return working_days - public_holidays_count

def fetch_resources(uri,rel):
    """
     While generating the PDF report if any images to show then we are using this.
    """
    path = os.path.join(settings.MEDIA_ROOT,uri.replace(settings.MEDIA_URL,""))
    return path

def write_pdf(template_src, context_dict,temp_path):
    """
      We are generating the PDF file.
    """
    try:
        template = get_template(template_src)
        context = Context(context_dict)
        print context
        html  = template.render(context_dict)
        result = StringIO()
        f = open(temp_path, "w+b")
        pisaStatus = pisa.CreatePDF(html, dest=f, link_callback=fetch_resources)
    except Exception as e:
        print e

@login_required(login_url='/login/')
@user_passes_test(lambda u: u.is_superuser)
def export_report(request):
    """
     Exporting the monthly attendance report has a PDF format.
    """
    try:
        if request.method == "GET":
            cal = Calendar()
            now = datetime.now()
            this_year = now.year
            this_month = now.month
            date1 = datetime(this_year,this_month,1)
            date2 = cal.addbusdays(date1, monthrange(this_year, this_month)[1])
            nodw = cal.busdaycount(date1, date2)
            all_days = range(1,nodw+1)
            dict = {}
            for u in User.objects.all():
                c = Attendance.objects.filter(month=now.strftime("%b"),username=u,approved_or_not=True)
                l = 0
                for i in c:
                    l = l + calculate_days(i.from_date,i.to_date)
                    print l
                dict[u] = nodw - l
            context = {
                'dict':dict,
                'this_month':now.strftime("%B"),
                'this_year':this_year,
                'nodw':nodw,
            }
            pdf_filename = '{0}.pdf'.format(now.strftime("%B"))
            temp_path = os.path.join(settings.PDF_ROOT,pdf_filename)
            write_pdf('Reports/report.html',context,temp_path)
            with open(temp_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/pdf")
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(temp_path)           
            return response
    except Exception, e:
        return HttpResponseRedirect('/error/')

def send_email_to_users(user, from_email, domain_override, email_template_name,use_https, token_generator):
    """
        Using this function we are sending an email to the respective users.
    """
    from_email = from_email 
    if not user.email:
        raise ValueError('Email address is required to send an email')
    if not domain_override:
        current_site = Site.objects.get_current()
        site_name = current_site.name
        domain = current_site.domain
    else:
        site_name = domain = domain_override
    t = loader.get_template(email_template_name)
    c = {
        'email': user.email,
        'name':user.username,
        'domain': domain,
        'site_name': site_name,
        'uid': urlsafe_base64_encode(str(user.id)),
        'user': user,
        'token': token_generator.make_token(user),
        'protocol': use_https and 'https' or 'http',
    }
    email = EmailMultiAlternatives("Welcome", '', from_email, [user.email])
    email.attach_alternative(t.render(c), "text/html")
    email.send()


def password_change(request, template_name='user_registration/password_change_form.html',
                    post_change_redirect=None,
                    password_change_form=PasswordChangeForm,
                    current_app=None, extra_context=None):
    """
     this function using for  changing  the password.
    """
    if post_change_redirect is None:
        post_change_redirect = reverse('password_change_done')
    else:
        post_change_redirect = resolve_url(post_change_redirect)
    if request.method == "POST":
        form = password_change_form(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return HttpResponseRedirect('/home/')
    else:
        form = password_change_form(user=request.user)
    context = {
        'form': form,
        'title': 'Password change',
    }
    if extra_context is not None:
        context.update(extra_context)

    if current_app is not None:
        request.current_app = current_app

    return TemplateResponse(request, template_name, context)


def resend_pwd(request, resend=None):
    """
     Forgot pasword functionality.
    """
    if request.method == "GET":
        if resend:
            if resend == "success":
                return render(request, 'user_registration/password_reset_success.html')
        resendform = ResendForm()
        return render(request, 'resend_passwd.html',{'resendform':resendform})
    if request.method == "POST":
        resendform = ResendForm(request.POST)
        if resendform.is_valid():
            email = resendform.cleaned_data['email']
            uname = resendform.cleaned_data['uname']
            if email:
                usr = User.objects.get(email=email)
            if uname:               
                usr = User.objects.get(username=uname)  
            # from_email = request.user.org.send_email  
            from_email = 'tilaknayarmelpal@gmail.com' 
            # reset(usr,domain_override=None,email_template_name='user_registration/password_reset_forgot_password.html',use_https=False, token_generator=default_token_generator)
            send_email_to_users(usr, from_email, domain_override=None,email_template_name='user_registration/password_reset_forgot_password.html',use_https=False, token_generator=default_token_generator)
            return HttpResponseRedirect('/reset_password/success/')
        else:
            return render(request, 'resend_passwd.html',{'resendform':resendform})

@login_required(login_url='/login/')
@user_passes_test(lambda u: u.is_superuser)
def update_organization(request, pk):
    """
        In this function we are updating the organization related informations.
    """
    try:
        obj = get_object_or_404(Organization, pk=pk)
        if request.method == "GET":
            form = OrganizationForm(instance=obj)
            context = {
              'form':form
            }
            return render (request, 'organization/update.html', context)
        elif request.method == "POST":
            form = OrganizationForm(request.POST,instance=obj)
            if form.is_valid:
                form.save()
                return HttpResponseRedirect('/update_org/{0}'.format(pk))
            else:
                context = {
                    'form':form
                }
                return render (request, 'organization/update.html', context)
        else:
            return HttpResponseRedirect('/forbidden/')
    except Exception as e:
        return HttpResponseRedirect('/error/')


def login_user(request):
    """
        Login the user using email and password.
    """
    try:
        if request.method == 'GET':
            form = LoginForm()
            return render(request,'login/login.html',{'form':form})
        elif request.method == 'POST':
            form = LoginForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data.get('email', None)
                password = form.cleaned_data.get('password', None)
                user = authenticate(email=email, password=password)
                if user:
                    if user.is_active:
                        login(request, user)
                        return HttpResponseRedirect('/home/')
                    else:
                        return HttpResponse("Your account is disabled.")
                else:
                    user_error = 'Please enter a valid details'
                    return render(request,'login/login.html',{'form':form, 'user_error':user_error})
            else:
                return render(request,'login/login.html',{'form':form})
        else:
            return HttpResponseRedirect('/forbidden/')
    except Exception as e:
        return HttpResponseRedirect('/error/')


@login_required(login_url='/login/')
def logout_user(request):
    """
        Logout functionality.
    """
    logout(request)
    return HttpResponseRedirect('/login/')


@login_required(login_url='/login/')
def home(request):
    """
        Application dashboard.
    """
    try:
        if request.method == "GET":
            if request.user.is_superuser:
                users_list = User.objects.all()
                events = Events.objects.all()
                form = AttendanceEntryForm()
                obj = Attendance.objects.filter(waiting=True)
                obj_ap = Attendance.objects.filter(waiting=False,approved_or_not=True)
                obj_dsp = Attendance.objects.filter(waiting=False,approved_or_not=False)
                obj_all = Attendance.objects.filter(waiting=False)
                time = date.today()
                weekday = time.strftime('%A')
                today_time = datetime.now()
                current_time =  DateFormat(today_time)
                hour = current_time.format
            else:
                users_list = User.objects.all()
                events = Events.objects.all()
                form = AttendanceEntryForm()
                obj = Attendance.objects.filter(username=request.user,waiting=True)
                obj_ap = Attendance.objects.filter(waiting=False,approved_or_not=True)
                obj_dsp = Attendance.objects.filter(waiting=False,approved_or_not=False)
                obj_all = Attendance.objects.filter(username=request.user,waiting=False)
                time = date.today()
                weekday = time.strftime('%A')
                today_time = datetime.now()
                current_time =  DateFormat(today_time)
                hour = current_time.format
            context = {
                'events':events,
                'obj':obj,
                'form':form,
                'obj_all':obj_all,
                'user':users_list,
                'time':time,
                'weekday':weekday,
                'hour':hour,
                'obj_ap':obj_ap,
                'obj_dsp':obj_dsp
            }
            return render(request,'home/home.html',context)
        elif request.method == "POST":
            if request.user.is_superuser:
                if request.is_ajax():
                    pid = request.POST.get('id')
                    if pid:
                        try:
                            obj = Attendance.objects.get(id=pid)
                            obj.approved_or_not = True
                            obj.waiting = False
                            obj.save()
                        except ObjectDoesNotExist:
                            pass
                        obj = Attendance.objects.filter(waiting=True).count()
                    return HttpResponse(obj)
                else:
                    if request.POST.get('sport'):
                        l = request.POST.getlist('sport')
                        for i in l:
                            obj = Attendance.objects.get(id=int(i))
                            obj.approved_or_not = True
                            obj.waiting = False
                            obj.save()
                        sent_from = request.user.email
                        to_emal = request.user.email
                        mail_subject = "Approved"
                        html_content = render_to_string('mail_templates/leave_mail.html')
                        msg = EmailMultiAlternatives(mail_subject,'',sent_from,to_emal)
                        msg.attach_alternative(html_content, "text/html")
                        msg.send()
                        return HttpResponseRedirect('/home/')
                    else:
                        reason = request.POST.get('disapprove_reason')
                        uid = request.POST.get('uid')
                        if reason:
                            try:
                                obj = Attendance.objects.get(id=uid)
                                obj.disapprove_reason = reason
                                obj.waiting = False
                                obj.save()
                            except ObjectDoesNotExist:
                                pass
                        else:
                            messages.error(request,'Please enter the reason')
                to_mail = obj.username.email
                to_name = obj.username.username
                from_date = obj.from_date
                to_date = obj.to_date
                disapprove_reason = reason
                sent_name = request.user.username
                sent_from = request.user.email
                mail_subject = "Disapproved"
                html_content = render_to_string('mail_templates/disapprove_mail.html',{'to_name':to_name,'from_date':from_date,'to_date':to_date,'disapprove_reason':disapprove_reason,'sent_name':sent_name})
                msg = EmailMultiAlternatives(mail_subject,'',sent_from,to_email)
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                return HttpResponseRedirect('/home/')
    except Exception, e:
        return HttpResponseRedirect('/error/')


@login_required(login_url='/login/')
@user_passes_test(lambda u: u.is_superuser)
def employee_creation(request):
    """
        Create New employee
    """
    try:
        if request.method == "GET":            
            form = EmployeeCreationForm()
            return render(request,'Employees/employee_creation.html',{'form':form})
        elif request.method=="POST":
            form = EmployeeCreationForm(request.POST,request.FILES)
            if form.is_valid():
                try:
                    user = User.objects.get(username=form.cleaned_data['username'])
                    user.email = form.cleaned_data['email']
                    user.is_staff = True
                    user.save()
                except ObjectDoesNotExist:
                    user = User.objects.create(
                        username=form.cleaned_data['username'],
                        email=form.cleaned_data['email'],
                        gender=form.cleaned_data['gender'],
                        contact=form.cleaned_data['contact'],
                        alternative_contact=form.cleaned_data['alternative_contact'],
                        blood_grp=form.cleaned_data['blood_grp'],
                        permanent_address=form.cleaned_data['permanent_address'],
                        present_address=form.cleaned_data['present_address'],
                        designation=form.cleaned_data['designation'],                 
                        date_of_joining = form.cleaned_data['date_of_joining'],                       
                        img = form.cleaned_data['img'],
                        is_staff = True,
                        is_superuser = False,
                        org=request.user.org
                        )
                    messages.success(request,'Employee created successfully')    
                    from_email = request.user.org.send_email                         
                    send_email_to_users(user, from_email, domain_override=None,email_template_name='user_registration/password_reset_email_for_module_admin.html',use_https=False, token_generator=default_token_generator)
                    # send_email_to_users(user,domain_override=None,email_template_name='user_registration/password_reset_email_for_module_admin.html',use_https=False, token_generator=default_token_generator)
                return HttpResponseRedirect('/list_employees/')
            else: 
                messages.warning(request,"Please correct the following errors")
                return render(request,'Employees/employee_creation.html',{'form':form})
        else:
            return HttpResponseRedirect('/forbidden/')    
    except Exception, e:
    	exc_type, exc_value, exc_traceback = sys.exc_info()
    	print "Line no :%s Exception %s"%(exc_traceback.tb_lineno,e)
    	messages.error(request,'Oops!!! Error')
    	return HttpResponseRedirect('/error/')


@login_required(login_url='/login/')
@user_passes_test(lambda u: u.is_superuser)
def view_employees(request):
    """
        View the list of employees.
    """
    try:
        if request.method == "GET":
            obj = User.objects.filter(is_superuser=False).all() 
            return render(request,'Employees/view_all_employees.html',{'obj':obj})
        else:
            return HttpResponseRedirect('/forbidden/')
    except Exception, e:
        return HttpResponseRedirect('/error/')


@login_required(login_url='/login/')
@user_passes_test(lambda u: u.is_superuser)
def admin_update_employee(request,id):
    """
        Update the employee
    """
    try:
        obj =  get_object_or_404(User, id=id)     
        if request.method == "GET":           
            form = EmployeeCreationForm(instance=obj)
            context = {
               'form':form
            }
            return render(request,'Employees/employee_creation.html', context)
        elif request.method == "POST":
            form = EmployeeCreationForm(request.POST,request.FILES,instance=obj)  
            if form.is_valid():
                form_save = form.save(commit=False)
                form_save.email = form.cleaned_data['email']
                form_save.img = form.cleaned_data['img']
                form_save.save()
                return HttpResponseRedirect('/list_employees/')            
            else:
                context = {
                   'form':form
                }
                return render(request,'Employees/employee_creation.html', context)   
        else:
            return HttpResponseRedirect('/forbidden/')         
    except Exception, e:
        return HttpResponseRedirect('/error/')      

@login_required(login_url='/login/')
def update_employee(request,id):
    """
        Updating the employee profile.
    """
    try:
        obj = User.objects.get(id=id)
        total_cl = obj.no_of_cl       
        total_sl = obj.no_of_sl       
        total_wh = obj.no_of_wh       
        attendance_cl = Attendance.objects.filter(id=id,leave_type='cl',approved_or_not=True).count()
        attendance_sl = Attendance.objects.filter(id=id,leave_type='sl',approved_or_not=True).count()
        attendance_wh = Attendance.objects.filter(id=id,leave_type='wl',approved_or_not=True).count()        
        taken_cl = (total_cl-attendance_cl)
        taken_sl = (total_sl-attendance_sl)
        taken_wh = (total_wh-attendance_wh)
        if request.method == "GET":           
            form = EmployeeCreationForm(instance=obj,initial={'email':obj.email})
            context = {
                'form':form,
                'obj':obj,
                'attendance_cl':attendance_cl,
                'attendance_sl':attendance_sl,
                'attendance_wh':attendance_wh,
                'taken_cl':taken_cl,
                'taken_sl':taken_sl,
                'taken_wh':taken_wh
            }
            return render (request,'Employees/edit_employee.html', context)
        elif request.method == "POST":
            form = EmployeeCreationForm(request.POST,request.FILES,instance=obj)  
            if form.is_valid():
                form_save = form.save(commit=False)
                form_save.email = form.cleaned_data['email']
                form_save.img = form.cleaned_data['img']
                form_save.save()
                return render(request,'Employees/edit_employee.html',{'form':form})            
            else:
                return render(request,'Employees/edit_employee.html',{'form':form})   
        else:
            return HttpResponseRedirect('/forbidden/')         
    except Exception, e:
        return HttpResponseRedirect('/error/')      

@login_required(login_url='/login/')
@user_passes_test(lambda u: u.is_superuser)
def delete_employee(request,id):
    """
        Deleting the employee.
    """
    try:         
        if request.method == "GET":
            obj = User.objects.filter(is_superuser=False).get(id=id)
            obj.delete()        
            return HttpResponseRedirect('/list_employees/')
        else:
            return HttpResponseRedirect('/forbidden/')
    except Exception, e:
        return HttpResponseRedirect('/error/')


@login_required(login_url='/login/')
def attendance_entry(request):
    """
        Applying the leave
    """
    try:
        un = request.user.username
        obj = User.objects.get(username=un)
        objs = Attendance.objects.filter(waiting=True)
        if request.method == "GET":
            form = AttendanceEntryForm()
            context = {
                'form':form,
                'un':un,
                'obj':obj,
                "objs":objs
            }
            return render(request,'attendance/attendance_entry.html',context)
        elif request.method == "POST":
            month = datetime.now()
            form = AttendanceEntryForm(request.POST)
            form.fields['disapprove_reason'].required = False
            if request.POST['one_or_more_days'] == 'morethan':
                form.fields['one_date'].required = False
                leave_type= request.POST.get('leave_type',None)
                if form.is_valid():
                    subject = form.cleaned_data.get('email_subject', None)
                    to_email = form.cleaned_data.get('approver', None)
                    reason = form.cleaned_data.get('reason', None)
                    from_date = form.cleaned_data.get('from_date', None)
                    to_date = form.cleaned_data.get('to_date', None)
                    form_save=form.save(commit=False)
                    form_save.username=request.user
                    form_save.org = request.user.org
                    form_save.month = month.strftime("%B")
                    form_save.compensated = 0
                    form_save.save()
                    sent_from_name = request.user
                    sent_name = request.user.username
                    sent_from = request.user.email
                    mail_subject = subject
                    plain_mail = "..."
                    html_content = render_to_string('mail_templates/leave_mail.html',{'reason':reason,'sent_name':sent_name,'from_date':from_date,'to_date':to_date,'leave_type':leave_type})
                    msg = EmailMultiAlternatives(mail_subject,plain_mail,sent_from,[to_email])
                    msg.attach_alternative(html_content, "text/html")
                    msg.send()
                    return HttpResponseRedirect('/home/')
                else:
                    context = {
                        'form':form,
                        'un':un,
                        'obj':obj,
                        "objs":objs
                    }
                    return render(request,'attendance/attendance_entry.html',context)
            elif request.POST['one_or_more_days'] == 'oneday':
                month = datetime.now()
                form.fields['from_date'].required= False
                form.fields['to_date'].required= False
                leave_type= request.POST.get('leave_type',None)
                if form.is_valid():
                    subject = form.cleaned_data.get('email_subject', None)
                    to_email = form.cleaned_data.get('approver', None)
                    reason = form.cleaned_data.get('reason', None)
                    one_date = form.cleaned_data.get('one_date', None)
                    form_save=form.save(commit=False)
                    form_save.username=request.user
                    form_save.compensated = 0
                    form_save.org = request.user.org
                    form_save.month = month.strftime("%B")
                    form_save.save()
                    sent_from_name = request.user
                    sent_name = request.user.username
                    sent_from = request.user.email
                    mail_subject = subject
                    plain_mail = "..."
                    html_content = render_to_string('mail_templates/one_day_leave_mail.html',{'reason':reason,'sent_name':sent_name,'one_date':one_date,'leave_type':leave_type})
                    msg = EmailMultiAlternatives(mail_subject,plain_mail,sent_from,[to_email])
                    msg.attach_alternative(html_content, "text/html")
                    msg.send()
                    return HttpResponseRedirect('/home/')
                else:
                    context = {
                        'form':form,
                        'un':un,
                        'obj':obj,
                        "objs":objs
                    }
                    return render(request,'attendance/attendance_entry.html',context)
            else:
                return render(request,'attendance/attendance_entry.html',{'form':form,'un':un})
        else:
            return HttpResponseRedirect('/forbidden/')
    except Exception, e:
        return HttpResponseRedirect('/error/')


@login_required(login_url='/login/')
def attendance_view(request):
    """
        View the list of leaves.
    """
    try:
        if request.method == "GET":
            if request.user.is_superuser:
                form = AttendanceEntryForm()
                obj = Attendance.objects.filter(waiting=True)
                obj_all = Attendance.objects.filter(waiting=False)
            else:
                form = AttendanceEntryForm()
                obj = Attendance.objects.filter(username=request.user,waiting=True)
                obj_all = Attendance.objects.filter(username=request.user,waiting=False)
            context = {
                'obj':obj,
                'form':form,
                'obj_all':obj_all
            }
            return render(request,'attendance/attendance_view.html', context)
        elif request.method == "POST":
            if request.user.is_superuser:
                if request.is_ajax():
                    pid = request.POST.get('id')
                    if pid:
                        try:
                            obj = Attendance.objects.get(id=pid)
                            obj.approved_or_not = True
                            obj.waiting = False
                            obj.save()
                        except ObjectDoesNotExist:
                            pass                    
                        obj = Attendance.objects.filter(waiting=True).count()
                    return HttpResponse(obj)
                else:
                    if request.POST.get('sport'):                        
                        l = request.POST.getlist('sport')
                        for i in l:
                            obj = Attendance.objects.get(id=int(i))
                            obj.approved_or_not = True
                            obj.waiting = False
                            obj.save()
                        return HttpResponseRedirect('/attd_view/')
                    else:
                        reason = request.POST.get('disapprove_reason')
                        uid = request.POST.get('uid')                
                        if reason:                    
                            try:
                                obj = Attendance.objects.get(id=uid)
                                obj.disapprove_reason = reason
                                obj.waiting = False
                                obj.save()
                            except ObjectDoesNotExist:
                                pass
                        else:
                            messages.error(request,'Please enter the reason')
                return HttpResponseRedirect('/attd_view/')
            else:
                return HttpResponseRedirect('/forbidden/')
        else:
            return HttpResponseRedirect('/forbidden/')
    except Exception, e:
        return HttpResponseRedirect('/error/')
        
@login_required(login_url='/login/')
def attendance_disapprove(request):
    """
        Disapproving the leaves.
    """
    try:
        if request.method == "GET":
            if request.user.is_superuser:
                form = AttendanceEntryForm()
                obj = Attendance.objects.filter(waiting=True)
                obj_all = Attendance.objects.filter(waiting=False)
            else:
                form = AttendanceEntryForm()
                obj = Attendance.objects.filter(username=request.user,waiting=True)
                obj_all = Attendance.objects.filter(username=request.user,waiting=False)
            context = {
                'obj':obj,
                'form':form,
                'obj_all':obj_all
            }
            return render(request,'attendance/attendance_disapprove.html', context)
        elif request.method == "POST":
            if request.user.is_superuser:
                if request.is_ajax():
                    pid = request.POST.get('id')
                    if pid:
                        try:
                            obj = Attendance.objects.get(id=pid)
                            obj.approved_or_not = True
                            obj.waiting = False
                            obj.save()
                        except ObjectDoesNotExist:
                            pass                    
                        obj = Attendance.objects.filter(waiting=True).count()
                    return HttpResponse(obj)
                else:
                    if request.POST.get('sport'):                        
                        l = request.POST.getlist('sport')
                        for i in l:
                            obj = Attendance.objects.get(id=int(i))
                            obj.approved_or_not = True
                            obj.waiting = False
                            obj.save()
                        return HttpResponseRedirect('/attd_view/')
                    else:
                        reason = request.POST.get('disapprove_reason')
                        uid = request.POST.get('uid')                
                        if reason:                    
                            try:
                                obj = Attendance.objects.get(id=uid)
                                obj.disapprove_reason = reason
                                obj.waiting = False
                                obj.save()
                            except ObjectDoesNotExist:
                                pass
                        else:
                            messages.error(request,'Please enter the reason')
                return HttpResponseRedirect('/attd_view/')
            else:
                return HttpResponseRedirect('/forbidden/')
        else:
            return HttpResponseRedirect('/forbidden/')
    except Exception, e:
        return HttpResponseRedirect('/error/')

@login_required(login_url='/login/')
def attendance_approved(request):
    """
        Approved Leaves.
    """
    try:
        if request.method == "GET":
            if request.user.is_superuser:
                form = AttendanceEntryForm()
                obj = Attendance.objects.filter(waiting=True)
                obj_all = Attendance.objects.filter(waiting=False)
            else:
                form = AttendanceEntryForm()
                obj = Attendance.objects.filter(username=request.user,waiting=True)
                obj_all = Attendance.objects.filter(username=request.user,waiting=False)
            context = {
                'obj':obj,
                'form':form,
                'obj_all':obj_all
            }
            return render(request,'attendance/attendance_approved.html', context)
        elif request.method == "POST":
            if request.user.is_superuser:
                if request.is_ajax():
                    pid = request.POST.get('id')
                    if pid:
                        try:
                            obj = Attendance.objects.get(id=pid)
                            obj.approved_or_not = True
                            obj.waiting = False
                            obj.save()
                        except ObjectDoesNotExist:
                            pass                    
                        obj = Attendance.objects.filter(waiting=True).count()
                    return HttpResponse(obj)
                else:
                    if request.POST.get('sport'):                        
                        l = request.POST.getlist('sport')
                        for i in l:
                            obj = Attendance.objects.get(id=int(i))
                            obj.approved_or_not = True
                            obj.waiting = False
                            obj.save()
                        return HttpResponseRedirect('/attd_view/')
                    else:
                        reason = request.POST.get('disapprove_reason')
                        uid = request.POST.get('uid')                
                        if reason:                    
                            try:
                                obj = Attendance.objects.get(id=uid)
                                obj.disapprove_reason = reason
                                obj.waiting = False
                                obj.save()
                            except ObjectDoesNotExist:
                                pass
                        else:
                            messages.error(request,'Please enter the reason')
                return HttpResponseRedirect('/attd_view/')
            else:
                return HttpResponseRedirect('/forbidden/')
        else:
            return HttpResponseRedirect('/forbidden/')
    except Exception, e:
        return HttpResponseRedirect('/error/')     

@login_required(login_url='/login/')
def attendance_read(request,id):
    """
        View list of attendance.`
    """
    try:
        if request.method == "GET":
            if request.user.is_superuser:
                form = AttendanceEntryForm()
                obj = Attendance.objects.filter(waiting=True)
                obj_all = Attendance.objects.filter(waiting=False)
            else:
                obj_all = Attendance.objects.filter(username=request.user).get(id=id)
            context = {
                'obj_all':obj_all
            }
            return render(request,'attendance/attendance_read.html', context)
        elif request.method == "POST":
            if request.user.is_superuser:
                if request.is_ajax():
                    pid = request.POST.get('id')
                    if pid:
                        try:
                            obj = Attendance.objects.get(id=pid)
                            obj.approved_or_not = True
                            obj.waiting = False
                            obj.save()
                        except ObjectDoesNotExist:
                            pass                    
                        obj = Attendance.objects.filter(waiting=True).count()
                    return HttpResponse(obj)
                else:
                    if request.POST.get('sport'):                        
                        l = request.POST.getlist('sport')
                        for i in l:
                            obj = Attendance.objects.get(id=int(i))
                            obj.approved_or_not = True
                            obj.waiting = False
                            obj.save()
                        return HttpResponseRedirect('/attd_view/')
                    else:
                        reason = request.POST.get('disapprove_reason')
                        uid = request.POST.get('uid')                
                        if reason:                    
                            try:
                                obj = Attendance.objects.get(id=uid)
                                obj.disapprove_reason = reason
                                obj.waiting = False
                                obj.save()
                            except ObjectDoesNotExist:
                                pass
                        else:
                            messages.error(request,'Please enter the reason')
                return HttpResponseRedirect('/attd_view/')
            else:
                return HttpResponseRedirect('/forbidden/')
        else:
            return HttpResponseRedirect('/forbidden/')
    except Exception, e:
        return HttpResponseRedirect('/error/')    



@login_required(login_url='/login/')
@user_passes_test(lambda u: u.is_superuser)
def create_events(request):
    """
        create an events like holidays.
    """
    try:
        if request.method == "GET":            
            form = EventsForm()
            context = {
                'form':form
            }
            return render (request,'Events/events_create.html', context)
        elif request.method == "POST":
            form = EventsForm(request.POST)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect('/events_create/')
            else:
                context = {
                    'form':form
                }
                return render(request,'Events/events_create.html', context)
        else:
            return HttpResponseRedirect('/forbidden/')
    except Exception, e:
        return HttpResponseRedirect('/error/')
      

@login_required(login_url='/login/')
def task_assign(request):
    """
        Asigning the task to the employees.
    """
    try:
        un = request.user.username        
        if request.method == "GET":
            form = TaskForm()
            context = {
                'form':form
            }
            return render(request,'task/create_task.html', context)
        elif request.method == "POST":
            form = TaskForm(request.POST)
            if form.is_valid():
                form_save = form.save(commit=False)
                try:
                    un = User.objects.get(username=un)
                except ObjectDoesNotExist:
                    return HttpResponseRedirect('/error/')
                except MultipleObjectsReturned:
                    return HttpResponseRedirect('/error/') 
                form_save.assigner = un
                form_save.pending_task = True
                # form_save.assigned = form.cleaned_data['assigned']
                # form_save.task_name = form.cleaned_data['task_name']
                # form_save.desc = form.cleaned_data['desc']
                # form_save.priority = form.cleaned_data['priority']               
                form_save.org = request.user.org     
                form_save.save()                
                return HttpResponseRedirect('/home/')
            else:
                context = {
                    'form':form
                }                
                return render(request,'task/create_task.html', context)
        else:
            return HttpResponseRedirect('/forbidden/')
    except Exception, e:
        return HttpResponseRedirect('/error/')

@login_required(login_url='/login/')
def task_pending(request):
    """
        View the pendng tasks.
    """
    try:
        if request.method == "GET":
            if request.user.is_superuser:                
                obj_all = Task.objects.filter(pending_task=True)
            else:
                obj_all = Task.objects.filter(username=request.user,pending_task=True).get(id=id)  
            context = {
                'obj_all':obj_all
            }             
            return render (request,'task/pending_task.html', context)
        else:
            return HttpResponseRedirect('/forbidden/')
    except Exception, e:
        return HttpResponseRedirect('/error/')

@login_required(login_url='/login/')
def task_work_in_progress(request,id):
    """
        Work in progress tasks.
    """
    try:
        obj = get_object_or_404(Task, id=id)
        if request.method == "GET":            
            form = UpdateTaskForm(instance=obj)
            if request.user.is_superuser: 
                obj_all = Task.objects.all()
            else:
                obj_all = Task.objects.filter(username=request.user).get(id=id)
            context = {
                'form' : form,
                'obj_all' : obj_all
            }
            return render (request,'task/task_process.html', context)
        elif request.method == "POST":            
            form = UpdateTaskForm(request.POST,instance=obj)
            if request.user.is_superuser: 
                obj_all = Task.objects.all()
            else:
                obj_all = Task.objects.filter(username=request.user).get(id=id)
            if form.is_valid():
                form_save = form.save(commit=False)
                obj.work_in_task = form.cleaned_data.get('work_in_task', None)
                obj.work_in_status = form.cleaned_data.get('work_in_status', None)
                obj.save()
                form_save.save()
                return HttpResponseRedirect('/home/')
            else:
                context = {
                    'form':form,
                    'obj_all' : obj_all
                }
                print form.errors
                return render(request,'task/task_process.html', context)
        else:
            return HttpResponseRedirect ('/forbidden/')
    except Exception, e:
        print e
        return HttpResponseRedirect ('/error/')

@login_required(login_url='/login/')
def task_final_status_view(request):
    """
        view the work in progress tasks.
    """
    try:
        if request.method == "GET":
            if request.user.is_superuser:
                obj = Task.objects.filter(work_in_task=True)
            else:
                obj = Task.objects.filter(work_in_task=True, assigned__in=request.user, assigner=request.user)
            context = {
               'obj':obj
            }
            return render (request, 'task/task_final_status.html', context)
        else:
            return HttpResponseRedirect('/forbidden/')
    except Exception as e:
        return HttpResponseRedirect('/error/')

@login_required(login_url='/login/')
def task_final_status_update(request, pk):
    """
        Update the tasks.
    """
    try:
        obj = get_object_or_404(Task, pk=pk)
        if request.method == "GET":
            form = UpdateTaskForm(instance=obj)
            context = {
                'form' : form,
                'obj' : obj
            }
            return render (request, 'task/update_final_status.html', context)
        elif request.method == "POST":
            form = UpdateTaskForm(request.POST,  instance=obj)
            if form.is_valid():
                form_save = form.save(commit=False)
                obj.completed_task = form.cleaned_data.get('completed_task', None)
                obj.complete_status = form.cleaned_data.get('complete_status', None)
                obj.pending_task = False
                obj.save()
                form_save.save()
                return HttpResponseRedirect('/home/')
            else:
                context = {
                    'form' : form,
                    'obj' : obj
                }
                return render (request, 'task/update_final_status.html', context)
        else:
            return HttpResponseRedirect('/forbidden/')
    except Exception as e:
        print e
        return HttpResponseRedirect('/error/')

@login_required(login_url='/login/')
def completed_tasks(request):
    """
        View the completed Tasks.
    """
    try:
        if request.method == "GET":
            obj = Task.objects.filter(completed_task=True)
            context = {
                'obj':obj

            }
            return render (request, 'task/completed_task.html', context)
        else:
            return HttpResponseRedirect('/forbidden/')
    except Exception as e:
        return HttpResponseRedirect('/error/')


def forbidden(request):
    """
        Forbidden error pages
    """
    if request.method == "GET":
        return render (request, 'error/forbidden.html')

def error(request):
    """
        Error Pages.
    """
    if request.method == "GET":
        return render (request, 'error/error.html')
        

# End-Of-File