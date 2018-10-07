"""ectd URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url, include
from rest_framework import routers
from ectd.manage import views
from ectd.applications.views import *
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token

from ectd.applications.models import *
router = routers.DefaultRouter()
# router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'templates', TemplateViewSet)
router.register(r'companies', CompanyViewSet, base_name='company')
router.register(r'applications', ApplicationViewSet, base_name='application')
router.register(r'users', views.UserViewSet, base_name='user')
router.register(r'employees', EmployeeViewSet, base_name='employee')
router.register(r'contacts', ContactViewSet, base_name='contact')
router.register(r'appinfos', AppinfoViewSet, base_name='appinfo')
router.register(r'files', FileViewSet, base_name='file')
router.register(r'files/(?P<file_id>\d+)/states', FileStateViewSet, base_name='fileState')
router.register(r'nodes', NodeViewSet, base_name='node')
router.register(r'tags', TagViewSet, base_name='tag')   #only delete API

tag_detail = NodeTagViewSet.as_view({
    'get': 'retrieve',
    'post': 'create',
})
admin.autodiscover()
admin.site.register(Application)
admin.site.register(Company)
admin.site.register(Employee)
urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^', include(router.urls)),
    # url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
    url(r'^api-token-auth/', obtain_jwt_token),
    url(r'^api-token-refresh/', refresh_jwt_token),
    url(r'^users/register', views.AccountList.as_view()),
    url(r'^fileUpload/(?P<app_id>[0-9]+)/$', FileUploadView.as_view()),
    url(r'applications/(?P<app_id>\d+)/nodes/(?P<node_id>[0-9a-zA-z]+)/tag', tag_detail, name='tag'),
    # url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
    #     views.activate, name='activate')
]
