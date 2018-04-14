"""EmployeesManagement URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf.urls import  include, url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.contrib import admin
from django.views.static import *
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.views import password_reset as auth_password_reset,\
    password_reset_done as auth_password_reset_done,\
    password_reset_complete as auth_password_reset_complete,\
    password_reset_confirm as auth_password_reset_confirm
from attendance_app.models import *
from attendance_app.views import *
from attendance_app.password import ValidatingPasswordChangeForm, ValidatingSetPasswordForm

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', login_user),    
    url(r'^user/password/reset/$',auth_password_reset,{'post_reset_redirect' : '/user/password/reset/done/'}),
    url(r'^user/password/reset/done/$', auth_password_reset_done), 
    url(r'^user/password/reset/(?P<uidb64>[0-9A-Za-z=]+)-(?P<token>.+)/$',auth_password_reset_confirm, {'post_reset_redirect' : '/user/password/done/','template_name':'user_registration/password_reset_confirm.html'}),
    url(r'^user/password/done/$',auth_password_reset_complete,{'template_name':'user_registration/password_reset_complete.html'}),
    url(r'^reset_password/$', resend_pwd),    
    url(r'^reset_password/(?P<resend>[a-z]+)/$', resend_pwd),
    url(r'^password_change/$',password_change,{'post_change_redirect' : '/','template_name':'user_registration/password_change.html'}),    

    url(r'^login/', login_user),  
    url(r'^logout/', logout_user),  

    url(r'^update_org/(?P<pk>\d+)/$', update_organization), 

    url(r'^create_employee/$', employee_creation),   
    url(r'^admin_edit_emp/(?P<id>\d+)/$', admin_update_employee),
    url(r'^edit_emp/(?P<id>\d+)/$', update_employee),   
    url(r'^delete_emp/(?P<id>\d+)/$', delete_employee),   
    url(r'^list_employees/$', view_employees),   

    url(r'^attendance/$', attendance_entry),     
    url(r'^disapproved/$', attendance_disapprove),     
    url(r'^approved/$', attendance_approved),     
    url(r'^attd_view/$', attendance_view),     
    url(r'^read/(?P<id>\d+)/$',attendance_read),   

    url(r'^home/$', home), 

    url(r'^export_report/$', export_report),
    
    url(r'^events_create/$', create_events), 

    url(r'^task_create/$', task_assign), 
    url(r'^task_pending/$', task_pending), 
    url(r'^edit_task/(?P<id>\d+)$', task_work_in_progress), 
    url(r'^update_tasks/(?P<pk>\d+)$', task_final_status_update), 
    url(r'^update_tasks/$', task_final_status_view), 
    url(r'^completed_tasks/$', completed_tasks), 

    url(r'^forbidden/$', forbidden),
    url(r'^error/$', error),

    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# End-Of-File