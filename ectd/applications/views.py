# from django.shortcuts import render
from ectd.applications.models import *
from ectd.applications.serializers import *
from ectd.extra.msg import Msg
# from django.core import serializers as core_serializers
# from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.parsers import FileUploadParser, MultiPartParser, FormParser
from rest_framework.decorators import action
from django.utils.datastructures import MultiValueDictKeyError
from django.utils import timezone
from django.db import IntegrityError
from django.db import transaction
from django.conf import settings
from django.views.generic import View
from django.http import HttpResponse
import os
import uuid
import json
from ectd.PyPDF2 import PdfFileWriter, PdfFileReader

from ectd.PyPDF2.canvas import drawBackground, drasString
from ectd.PyPDF2.utils import b_
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.graphics.shapes import Rect
from reportlab.lib.colors import Color
# from rest_framework import mixins
# from rest_framework import generics

class TemplateViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser,)
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer

class CompanyViewSet(viewsets.ViewSet):

    def list(self, request):
        if request.user.is_superuser or True:
            queryset = Company.objects.all().filter(deleted=False)
            serializer = CompanySerializer(queryset, many=True)
            return Response(serializer.data)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def retrieve(self, request, pk=None):
        try:
            company = Company.objects.get(pk=pk)
            print(company.employees)
        except Company.DoesNotExist:
            return Response(Msg.COMPANY_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        if request.user.is_superuser or True:
            serializer = CompanySerializer(company)
            return Response(serializer.data)

        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
    
    def create(self, request):
        try: 
            company = Company.objects.create(**request.data)
            # print(repr(company))
            employee = Employee.objects.create(user=request.user, company=company, role='ADMIN')
            # serializer_comp = CompanySerializer(company)
            serializer = CompanySerializer(company)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            if company:
                company.delete()
            return Response(Msg.INTETRITY_ERROR, status.HTTP_406_NOT_ACCEPTABLE)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def update(self, request, pk=None):
        try:
            company = Company.objects.get(pk=pk)
        except Company.DoesNotExist:
            return Response(Msg.COMPANY_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        serializer = CompanySerializer(company, data=request.data)
        if request.user.is_superuser or request.user == company.owner:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def destroy(self, request, pk=None):
        if  not request.user.is_superuser:
           return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION) 
        # try:
        #     company = Company.objects.get(pk=pk)
        # except Company.DoesNotExist:
        #     return Response(Msg.COMPANY_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        # company.delete()
        # company.deleted = True
        # company.deleted_at = timezone.now()
        # company.deleted_by = request.user
        Company.objects.filter(pk=pk).update(deleted=True, deleted_at=timezone.now(), deleted_by=request.user)
        return Response({'msg': "company deleted"}, status=status.HTTP_204_NO_CONTENT)
    
    #API: /companies/2/applications
    @action(methods=['get'], detail=True,)
    def applications(self, request, pk=None):
        try: 
            employee = Employee.objects.get(user=request.user)
            company = Company.objects.get(pk=pk)
            if request.user.is_superuser or company.id == employee.company.id:
                apps = Application.objects.filter(company=company)
                serializer = ApplicationSerializer(apps, many=True)
                return Response(serializer.data)
            return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        except Employee.DoesNotExist:
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Company.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND) 

    #API: /companies/2/employees
    @action(methods=['get'], detail=True,)
    def employees(self, request, pk=None):
        try: 
            employee = Employee.objects.get(user=request.user)
            company = Company.objects.get(pk=pk)
            if request.user.is_superuser or company.id == employee.company.id:
                emps = Employee.objects.filter(company=company)
                serializer = EmployeeSerializer(emps, many=True)
                return Response(serializer.data)
            return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        except Employee.DoesNotExist:
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Company.DoesNotExist:
            return Response(Msg.COMPANY_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

class ApplicationViewSet(viewsets.ViewSet):

    def list(self, request):
        if request.user.is_superuser or True:
            queryset = Application.objects.filter(deleted=False)
            serializer = ApplicationSerializer(queryset, many=True)
            return Response(serializer.data)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def retrieve(self, request, pk=None):
        try:
            application = Application.objects.get(pk=pk)
            employee = Employee.objects.get(user=request.user)
        except Application.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Employee.DoesNotExist:
            return Response(Msg.EMPLOYEE_NOT_FOUND,status=status.HTTP_404_NOT_FOUND )    
        
        if request.user.is_superuser or application.company.id == employee.company.id:
            serializer = ApplicationSerializer(application)
            return Response(serializer.data)

        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
    
    def create(self, request):
        try: 
            template = Template.objects.get(pk=request.data.pop('template'))
            employee = Employee.objects.get(user=request.user)
            company = Company.objects.get(pk=employee.company.id)
            if not employee.role == 'ADMIN':
                print('not authorized')
            
            if not company.activated:
                print('company not activated')
           
            nodes = json.loads(template.content)
            # print(repr(nodes))
            if not len(nodes): 
                raise ValueError('no nodes')
            with transaction.atomic():
                application = Application.objects.create(company=company, template=template, **request.data)
                # create app folder 
                # APP_PATH = '/home/ectd/{}/app_{}/{}'.format(company.name, application.id, application.number)
                APP_PATH = 'C:\shares\django\{}\\app_{}\{}'.format(company.name, application.id, application.number)

                os.makedirs(APP_PATH, exist_ok=True)
                print(os.path.exists(APP_PATH))
                for n in nodes:
                    if(n['parent']=='#'):
                        n['text'] = application.sequence
                    n['original'] = True;
                    node = Node.objects.create(application=application, **n)
                    
                    #need to create folders
            serializer = ApplicationSerializer(application) 
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Employee.DoesNotExist:
            return Response(Msg.EMPLOYEE_NOT_FOUND,status=status.HTTP_404_NOT_FOUND )
        except Template.DoesNotExist:
            return Response(Msg.TEMPLATE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Company.DoesNotExist:
            return Response(Msg.COMPANY_NOT_FOUND,status=status.HTTP_404_NOT_FOUND )
        except IntegrityError:
            return Response(Msg.INTETRITY_ERROR, status.HTTP_406_NOT_ACCEPTABLE)
        except ValueError:
            return Response({'msg': 'template content error'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as error:
            print(repr(error))
            return Response({'msg': 'error creating application'}, status=status.HTTP_204_NO_CONTENT)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        try:
            application = Application.objects.get(pk=pk)
            employee = Employee.objects.get(user=request.user)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Employee.DoesNotExist:
            return Response(Msg.EMPLOYEE_NOT_FOUND,status=status.HTTP_404_NOT_FOUND) 
        serializer = ApplicationSerializer(application, data=request.data)
       
        if request.user.is_superuser or application.company.id == employee.company.id:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def destroy(self, request, pk=None):
        try: 
            employee = Employee.objects.get(user=request.user)
            application = Application.objects.get(pk=pk)
            if  application.company.id == employee.company.id and employee.role=='ADMIN':
                # application.deleted = True
                # application.deleted_at = timezone.now()
                # application.deleted_by = request.user
                Application.objects.filter(pk=pk).update(deleted=True, deleted_at=timezone.now(), deleted_by=request.user)
                return Response({'msg': "application deleted"}, status=status.HTTP_204_NO_CONTENT)
            return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        except Employee.DoesNotExist:
            return Response({'msg': 'User is not an owner'},status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION )
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
    
    #API: /applications/5/contacts
    @action(methods=['get'], detail=True,)
    def contacts(self, request, pk=None):
        try: 
            employee = Employee.objects.get(user=request.user)
            application = Application.objects.get(pk=pk)
            if request.user.is_superuser or application.company.id == employee.company.id:
                queryset = Contact.objects.filter(application=application)
                serializer = ContactSerializer(queryset, many=True)
                return Response(serializer.data)
            return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        except Employee.DoesNotExist:
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

    #API: /applications/1/files
    @action(methods=['get'], detail=True,)
    def files(self, request, pk=None):
        try: 
            employee = Employee.objects.get(user=request.user)
            application = Application.objects.get(pk=pk)
            if request.user.is_superuser or application.company.id == employee.company.id:
                queryset = File.objects.filter(application=application, deleted = False)
                serializer = FileSerializer(queryset, many=True)
                return Response(serializer.data)
            return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        except Employee.DoesNotExist:
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
            
    #API: /applications/5/appinfo
    @action(methods=['get'], detail=True,)
    def appinfo(self, request, pk=None):
        try: 
            employee = Employee.objects.get(user=request.user)
            application = Application.objects.get(pk=pk)
            if request.user.is_superuser or application.company.id == employee.company.id:
                appinfos = Appinfo.objects.filter(application=application)
                if  appinfos:
                    appinfo = appinfos[0]
                    # print(repr(appinfo))
                    serializer = AppinfoSerializer(appinfo)
                    return Response(serializer.data)
                return Response(Msg.APPINFO_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
            return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        except Employee.DoesNotExist:
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

    #API: /applications/5/nodes
    @action(methods=['get'], detail=True,)
    def nodes(self, request, pk=None):
        try: 
            employee = Employee.objects.get(user=request.user)
            application = Application.objects.get(pk=pk)
            if request.user.is_superuser or application.company.id == employee.company.id:
                nodes = Node.objects.filter(application=application)
                serializer = NodeSerializer(nodes, many=True)
                return Response(serializer.data)
            return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        except Employee.DoesNotExist:
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

    #API: /applications/5/batch_nodes
    @action(methods=['post'], detail=True,)
    def batch_nodes(self, request, pk=None):
        try: 
            employee = Employee.objects.get(user=request.user)
            application = Application.objects.get(pk=pk)
            if request.user.is_superuser or application.company.id == employee.company.id:
                nodes = json.loads(request.data['nodes'])
                if not len(nodes): 
                    raise ValueError('no nodes')
                query_set=[]
                with transaction.atomic():
                    for n in nodes:
                        print(repr(n))
                        node, created = Node.objects.update_or_create(application=application, id=n['id'], defaults=n)
                        #try:
                        #   node = Node.objects.get(application=application, id=n['id'])
                        #   for key, value in n.items():
                        #       setattr(obj, key, value)
                        #   node.save()
                        # except Node.DoesNotExist:
                        #     node = Node.objects.create(application=application, **n)
                        query_set.append(node)
                serializer = NodeSerializer(query_set, many=True)
                return Response(serializer.data)
            return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        except Employee.DoesNotExist:
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({'msg': 'no nodes in request'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as error:
            print(repr(error))
            return Response({'msg': 'error batch creating nodes'}, status=status.HTTP_204_NO_CONTENT)

    #API: /applications/5/tags
    @action(methods=['get'], detail=True,)
    def tags(self, request, pk=None):
        try: 
            employee = Employee.objects.get(user=request.user)
            application = Application.objects.get(pk=pk)
            
            if request.user.is_superuser or application.company.id == employee.company.id:
                nodes = Node.objects.filter(application=application)
                tags = Tag.objects.filter(node__in=nodes)
                serializer = TagSerializer(tags, many=True)
                return Response(serializer.data)
            return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        except Employee.DoesNotExist:
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)  
    
    #API: /application/5/download
    @action(methods=['get'], detail=True,)
    def download(self, request, pk=None):
        try: 
            employee = Employee.objects.get(user=request.user)
            application = Application.objects.get(pk=pk)
            if request.user.is_superuser or application.company.id == employee.company.id:
                return Response({'data': 'folders and files'})
            return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        except Employee.DoesNotExist:
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)      

class EmployeeViewSet(viewsets.ModelViewSet):
    def list(self, request):
        if request.user.is_superuser or True:
            queryset = Employee.objects.all()
            serializer = EmployeeSerializer(queryset, many=True)
            return Response(serializer.data)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def retrieve(self, request, pk=None):
        try:
            employee = Employee.objects.get(pk=pk)
        except Employee.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        user = User.objects.get(pk=employee.user.id)
        # print(company.owner, request.user)
        if request.user.is_superuser or request.user == user:
            serializer = EmployeeSerializer(employee)
            return Response(serializer.data)

        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
    
    def create(self, request):
        try: 
            user = User.objects.get(username=request.user)
            company_data = request.data.pop('company')
            request.data['role'] = 'BAS'
            company = Company.objects.get(pk=company_data['id'])
            employee = Employee.objects.create(user=user, company=company, **request.data)
            serializer = EmployeeSerializer(employee)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({'msg': 'User Not Found'},status=status.HTTP_404_NOT_FOUND )
        except Company.DoesNotExist:
            return Response(Msg.COMPANY_NOT_FOUND,status=status.HTTP_404_NOT_FOUND )
        except IntegrityError:
            return Response(Msg.INTETRITY_ERROR, status=status.HTTP_406_NOT_ACCEPTABLE)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def update(self, request, pk=None):
        try:
            employee = Employee.objects.get(pk=pk)
        except Employee.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        serializer = EmployeeSerializer(employee, data=request.data)
       
        if request.user.is_superuser or employee.user == request.user:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def destroy(self, request, pk=None):
        try: 
            employee = Employee.objects.get(pk=pk)
        except Employee.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        # print(employee.user)
        if request.user.is_superuser or employee.user == request.user:
            # employee.delete = True
            employee.delete()
            return Response({'msg': "employee deleted"}, status=status.HTTP_204_NO_CONTENT)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

class ContactViewSet(viewsets.ModelViewSet):
    def list(self, request):
        if request.user.is_superuser:
            queryset = Contact.objects.all()
            serializer = ContactSerializer(queryset, many=True)
            return Response(serializer.data)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def retrieve(self, request, pk=None):
        try:
            contact = Contact.objects.get(pk=pk)
            application = Application.objects.get(pk=contact.application.id)
            employee = Employee.objects.get(user=request.user)
        except Contact.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Employee.DoesNotExist: 
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        # user = User.objects.get(pk=employee.user.id)
        if request.user.is_superuser or application.company.id == employee.company.id:
            serializer = ContactSerializer(contact)
            return Response(serializer.data)

        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
    
    def create(self, request):
        # serializer = ContactSerializer(data=request.data)
        try: 
            app_id = request.data.pop('application')
            application = Application.objects.get(pk=app_id) 
            contact = Contact.objects.create(application=application, **request.data)
            serializer = ContactSerializer(contact)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response(Msg.INTETRITY_ERROR, status.HTTP_406_NOT_ACCEPTABLE)
    
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def update(self, request, pk=None):
        try:
            employee = Employee.objects.get(user=request.user)
            contact = Contact.objects.get(pk=pk)
            application = Application.objects.get(pk=contact.application.id)
        except Employee.DoesNotExist:
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Contact.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        
        request.data['application'] = application.id
        serializer = ContactSerializer(contact, data=request.data)
       
        if request.user.is_superuser or application.company.id == employee.company.id:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def destroy(self, request, pk=None):
        try: 
            employee = Employee.objects.get(user=request.user)
            contact = Contact.objects.get(pk=pk)
            application = Application.objects.get(pk=contact.application.id)
        except Employee.DoesNotExist:
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Contact.DoesNotExist:
            return Response(Msg.CONTACT_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        if request.user.is_superuser or application.company.id == employee.company.id:
            contact.delete()
            return Response({'msg': "employee deleted"}, status=status.HTTP_204_NO_CONTENT)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

class AppinfoViewSet(viewsets.ModelViewSet):
    def list(self, request):
        if request.user.is_superuser:
            queryset = Appinfo.objects.all()
            serializer = AppinfoSerializer(queryset, many=True)
            return Response(serializer.data)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def retrieve(self, request, pk=None):
        try:
            appinfo = Appinfo.objects.get(pk=pk)
            application = Application.objects.get(pk=appinfo.application.id)
            employee = Employee.objects.get(user=request.user)
        except Appinfo.DoesNotExist:
            return Response(Msg.APPINFO_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Employee.DoesNotExist: 
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        if request.user.is_superuser or application.company.id == employee.company.id:
            serializer = AppinfoSerializer(appinfo)
            return Response(serializer.data)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
    
    def create(self, request):
        try: 
            app_id = request.data.pop('application')
            application = Application.objects.get(pk=app_id) 
            appinfo = Appinfo.objects.create(application=application, **request.data)
            serializer = AppinfoSerializer(appinfo)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response(Msg.INTETRITY_ERROR, status.HTTP_406_NOT_ACCEPTABLE)
    
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        try:
            employee = Employee.objects.get(user=request.user)
            appinfo = Appinfo.objects.get(pk=pk)
            application = Application.objects.get(pk=appinfo.application.id)
        except Employee.DoesNotExist:
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Appinfo.DoesNotExist:
            return Response(Msg.APPINFO_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        
        request.data['application'] = application.id
        serializer = AppinfoSerializer(appinfo, data=request.data)
       
        if request.user.is_superuser or application.company.id == employee.company.id:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def destroy(self, request, pk=None):
        try: 
            employee = Employee.objects.get(user=request.user)
            appinfo = Appinfo.objects.get(pk=pk)
            application = Application.objects.get(pk=appinfo.application.id)
        except Employee.DoesNotExist:
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Appinfo.DoesNotExist:
            return Response(Msg.APPINFO_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        if request.user.is_superuser or application.company.id == employee.company.id:
            appinfo.delete()
            return Response({'msg': "employee deleted"}, status=status.HTTP_204_NO_CONTENT)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

class FileViewSet(viewsets.ModelViewSet):

    def list(self, request):
        if request.user.is_superuser:
            queryset = File.objects.all().filter(deleted=False)
            serializer = FileSerializer(queryset, many=True)
            return Response(serializer.data)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def retrieve(self, request, pk=None):
        try:
            file = File.objects.get(pk=pk)
            application = Application.objects.get(pk=file.application.id)
            employee = Employee.objects.get(user=request.user)
        except File.DoesNotExist:
            return Response(Msg.FILE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Employee.DoesNotExist: 
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        
        if request.user.is_superuser or application.company.id == employee.company.id:
            serializer = FileSerializer(file)
            return Response(serializer.data)

        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
    
    def update(self, request, pk=None):   
        try:
            employee = Employee.objects.get(user=request.user)
            file = File.objects.get(pk=pk)
            application = Application.objects.get(pk=file.application.id)
        except Employee.DoesNotExist:
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except File.DoesNotExist:
            return Response(Msg.FILE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        
        request.data['application'] = application.id
        serializer = FileSerializer(contact, data=request.data)
       
        if request.user.is_superuser or application.company.id == employee.company.id:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def destroy(self, request, pk=None):
        try: 
            employee = Employee.objects.get(user=request.user)
            file = File.objects.get(pk=pk)
            application = Application.objects.get(pk=file.application.id)
        except Employee.DoesNotExist:
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except File.DoesNotExist:
            return Response(Msg.FILE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        if request.user.is_superuser or application.company.id == employee.company.id:
            try: 
                file_path = os.path.join(file.url, file.name)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except OSError as err:
                return Response({'msg': 'Cannot write file to server'}, status.HTTP_500_INTERNAL_SERVER_ERROR)
            # File.objects.filter(pk=pk).update(deleted=True,deleted_at=timezone.now(), deleted_by=request.user)
            file.deleted = True
            file.deleted_at = timezone.now()
            file.deleted_by = request.user
            file.save()
            return Response({'msg': 'file deleted'}, status=status.HTTP_204_NO_CONTENT)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    @action(methods=['get'], detail=True,)
    def read_file(self, request, pk=None):
        try:
            file = File.objects.get(pk=pk)
            application = Application.objects.get(pk=file.application.id)
            employee = Employee.objects.get(user=request.user)
        except File.DoesNotExist:
            return Response(Msg.FILE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Employee.DoesNotExist: 
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        
        if not request.user.is_superuser and not application.company.id == employee.company.id:
            return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

        try: 
            path = os.path.join(file.url, file.name)
            fileobj = open(path, 'rb')
            buffer = io.BytesIO(b_(fileobj.read()))
            fileobj.close()
            return HttpResponse(buffer.getvalue(), content_type='application/pdf')
            # with open(path, 'rb') as f:
            #     data = f.read() 
            # print(data)
            # data = '%s'%data
            # return Response(data)
        except OSError:
            return Response({'msg': 'Cannot read file from server'}, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(methods=['get'], detail=True,)
    def last_file(self, request, pk=None):
        try:
            file = File.objects.get(pk=pk)
            state = FileState.objects.filter(file=file).last()
            application = Application.objects.get(pk=file.application.id)
            employee = Employee.objects.get(user=request.user)
        except File.DoesNotExist:
            return Response(Msg.FILE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except FileState.DoesNotExist:
            return Response(Msg.FILESTATE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Employee.DoesNotExist: 
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
            
        if not request.user.is_superuser and not application.company.id == employee.company.id:
            return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        if state:
            # state = states[-1]
            path = os.path.join(state.path, file.name)
        else:
            path = os.path.join(file.url, file.name)
        try: 
            # with open(path, 'r',  errors='ignore') as f:
            #     data = f.read() 
            fileobj = open(path, 'rb')
            buffer = io.BytesIO(b_(fileobj.read()))
            fileobj.close()
            return HttpResponse(buffer.getvalue(), content_type='application/pdf')
        except OSError:
            return Response({'msg': 'Cannot read file from server'}, status.HTTP_500_INTERNAL_SERVER_ERROR)
        # return Response({'data': data})

    @action(methods=['get'], detail=True,)
    def last_state(self, request, pk=None):
        try:
            file = File.objects.get(pk=pk)
            application = Application.objects.get(pk=file.application.id)
            employee = Employee.objects.get(user=request.user)

            if not request.user.is_superuser and not application.company.id == employee.company.id:
                return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
            states = FileState.objects.filter(file=file)
            if not states:
                return Response(Msg.FILESTATE_NOT_FOUND)
            state = states.latest('id')
        except File.DoesNotExist:
            return Response(Msg.FILE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except FileState.DoesNotExist:
            return Response(Msg.FILESTATE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Employee.DoesNotExist: 
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        serializer = FileStateSerializer(state)
        return Response(serializer.data)
    
class FileUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, app_id=None):
        
        try:
            application = Application.objects.get(pk=app_id)
            employee = Employee.objects.get(user=request.user)
            # print(repr(request.FILES))
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Employee.DoesNotExist: 
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        # print(application.company.id, employee.company.id)
        if application.company.id != employee.company.id:
            return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
            
        try:
            up_file = request.FILES['file']
            print(up_file.size, up_file.content_type)
            if up_file.content_type != 'application/pdf':
                return Response({'msg': 'File type not allowed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            if up_file.size > 100000000: #100M
                return Response({'msg': 'File size over limit'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            file_folder = uuid.uuid4().hex
            #path = '/Users/nebula-ai/Desktop/django/{}/app_{}/{}'.format(application.company.name, app_id, file_folder)         # MAC path
            #path = '/home/ectd/{}/app_{}/{}'.format(application.company.name, app_id,file_folder)                 # ubuntu
            path = 'C:/shares/django/app_{}/{}'.format(app_id,file_folder)  # Window path
            url = os.path.join(path, up_file.name) #path+'/' + up_file.name

            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
            with open(url, 'wb+') as destination:
                for chunk in up_file.chunks():
                    destination.write(chunk)
        except MultiValueDictKeyError: 
            return Response({'msg': 'Empty file'}, status.HTTP_500_INTERNAL_SERVER_ERROR)
        except OSError as err:
            # print("OS error: {0}".format(err))
            return Response({'msg': 'Cannot write file to server'}, status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        file = File.objects.create(application=application, name=up_file.name, url=path, size=up_file.size)
        serializer = FileSerializer(file)
        return Response(serializer.data, status.HTTP_201_CREATED)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FileStateViewSet(viewsets.ModelViewSet):
    def list(self, request, file_id=None):
        try:
            file = File.objects.get(pk=file_id)
            application = Application.objects.get(pk=file.application.id)
            employee = Employee.objects.get(user=request.user)
        except File.DoesNotExist:
            return Response(Msg.FILE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND) 
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Employee.DoesNotExist: 
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        if application.company.id == employee.company.id:
            queryset = FileState.objects.filter(file=file)
            serializer = FileStateSerializer(queryset, many=True)
            return Response(serializer.data)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    # def retrieve(self, request, pk=None):
    #     try:
    #         fileState = FileState.objects.get(pk=pk)
    #         file = File.objects.get(pk=fileState.file.id)
    #         application = Application.objects.get(pk=file.application.id)
    #         employee = Employee.objects.get(user=request.user)
    #     except FileState.DoesNotExist:
    #         return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
    #     except File.DoesNotExist:
    #         return Response(Msg.FILE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND) 
    #     except Application.DoesNotExist:
    #         return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
    #     except Employee.DoesNotExist: 
    #         return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        
    #     if request.user.is_superuser or application.company.id == employee.company.id:
    #         serializer = FileStateSerializer(file)
    #         return Response(serializer.data)

    #     return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
    
    def create(self, request, file_id=None):
        #"action": "{\"links\":[{\"pageNum\":0, \"rect\":[0, 0, 20, 10], \"uri\":\"www.richyan.com\"}]}"
        try: 
            f = File.objects.get(pk=file_id)
            application = Application.objects.get(pk=f.application.id) 
            employee = Employee.objects.get(user=request.user) 

            if application.company.id!=employee.company.id:
                return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
            
            actions = json.loads(request.data['action'])
            if 'links' not in actions:
                links = None
            else: 
                links = actions['links']
                
            if 'texts' not in actions:
                texts = None
            else: 
                texts = actions['texts']
            if not links and not texts:
                return Response({'msg': 'Not actions found'}, status=status.HTTP_404_NOT_FOUND)

            pdf = PdfFileReader(open(os.path.join(f.url, f.name), 'rb'))
            writer = PdfFileWriter()

            for i in range(0, pdf.getNumPages()):
                page = pdf.getPage(i)
                if links:
                    for link in links:
                        if i==int(link['page'])-1:
                            # writer.addURI(i, link['uri'], link['rect'])
                            page_w = page.mediaBox.getWidth()
                            page_h = page.mediaBox.getHeight()
                            print(page_w, page_h)
                            x1 = float(link['rect']['left'])
                            y1 = float(link['rect']['top'])
                            w = float(link['rect']['width'])
                            h = float(link['rect']['height'])
                            x2 = w + x1
                            y2 = h + y1
                            # x1, y1, x2, y2 = link['rect']
                            # w = x2 - x1
                            # h = y2 - y1
                            y1 = page_h - y1
                            y2 = page_h - y2
                            link['rect'] = [x1, y1, x2, y2]
                            print(link['rect'])
                            packet = io.BytesIO()
                            blue50transparent = Color( 0, 0, 255, alpha=0.5)
                            can = canvas.Canvas(packet, pagesize=(page_w, page_h))
                            can.setFillColor(blue50transparent)
                            can.rect(x1, y1-h, w, h, fill=True, stroke=False)
                            can.save()
                            packet.seek(0)
                            new_pdf = PdfFileReader(packet)
                            page.mergePage(new_pdf.getPage(0))
                if texts:
                    for text in texts:
                        if i==int(text['page'])-1: 
                            page_w = page.mediaBox.getWidth()
                            page_h = page.mediaBox.getHeight()
                            packet = io.BytesIO()
                            can = canvas.Canvas(packet, pagesize=(page_w, page_h))
                            y = page_h - text['y']
                            can.drawString(text['x'], text['y'], text['txt'])
                            can.save()
                            packet.seek(0)    
                            new_pdf = PdfFileReader(packet)
                            page.mergePage(new_pdf.getPage(0))
                writer.addPage(page)
                
            for link in links:
                print(repr(link['rect']))
                writer.addURI(int(link['page'])-1, link['uri'], link['rect'])

            output_path = os.path.join(f.url, 'states')
            try:
                if not os.path.exists(output_path):
                    os.mkdir(output_path)
                with open(os.path.join(output_path, f.name), 'wb+') as destination:
                    writer.write(destination)
            except OSError as err:
                print("OS error: {0}".format(err))
                return Response({'msg': 'Cannot write file to server'}, status.HTTP_500_INTERNAL_SERVER_ERROR)
            # writer.write(open(output_path, "wb"))
            # with file("destination.pdf", "wb") as outfp:
            #     writer.write(outfp)
            fileState = FileState.objects.create(file=f, action=request.data['action'], path=output_path)
            serializer = FileStateSerializer(fileState)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            # return Response(links)
        except File.DoesNotExist:
            return Response(Msg.FILE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response(Msg.INTETRITY_ERROR, status.HTTP_406_NOT_ACCEPTABLE)
        # except Error:
        #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NodeViewSet(viewsets.ModelViewSet):
    # def list(self, request):
    #     if request.user.is_superuser or True:
    #         queryset = Node.objects.all()
    #         serializer = NodeSerializer(queryset, many=True)
    #         return Response(serializer.data)
    #     return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def retrieve(self, request, pk=None):
        try:
            node = Node.objects.get(pk=pk)
            application = Application.objects.get(pk=node.application.id)
            employee = Employee.objects.get(user=request.user)
        except Node.DoesNotExist:
            return Response(Msg.NODE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Employee.DoesNotExist: 
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        if request.user.is_superuser or application.company.id == employee.company.id:
            serializer = NodeSerializer(node)
            return Response(serializer.data)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
    
    def create(self, request):
        try: 
            app_id = request.data.pop('application')
            application = Application.objects.get(pk=app_id) 
            node = Node.objects.create(application=application, **request.data)
            serializer = NodeSerializer(node)
            #add folders if node type = file
            if node.type == 'file':
                print(node.parent) 
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response(Msg.INTETRITY_ERROR, status=status.HTTP_406_NOT_ACCEPTABLE)
    
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        try:
            employee = Employee.objects.get(user=request.user)
            node = Node.objects.get(pk=pk)
            application = Application.objects.get(pk=node.application.id)
        except Employee.DoesNotExist:
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Node.DoesNotExist:
            return Response(Msg.NODE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        
        request.data['application'] = application.id
        serializer = NodeSerializer(node, data=request.data)
       
        if request.user.is_superuser or application.company.id == employee.company.id:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def destroy(self, request, pk=None):
        try: 
            employee = Employee.objects.get(user=request.user)
            node = Node.objects.get(pk=pk)
            application = Application.objects.get(pk=node.application.id)
        except Employee.DoesNotExist:
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Node.DoesNotExist:
            return Response(Msg.NODE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        if request.user.is_superuser or application.company.id == employee.company.id:
            if node.original:
                return Response({'msg', 'original node cant be deleted'}, status=status.HTTP_406_NOT_ACCEPTABLE )
            node.delete()
            return Response({'msg': "node deleted"}, status=status.HTTP_204_NO_CONTENT)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

class NodeTagViewSet(viewsets.ModelViewSet):
    
    def retrieve(self, request, app_id=None, node_id=None):
        try:
            application = Application.objects.get(pk=app_id)
            employee = Employee.objects.get(user=request.user)

            node = Node.objects.get(application=application, id=node_id)
            # if nodes:
            #     node=nodes[0]
            # else:
            #     return Response(Msg.NODE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
            tag = Tag.objects.get(node=node)
        except Tag.DoesNotExist:
            return Response(Msg.TAG_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Node.DoesNotExist:
            return Response(Msg.NODE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)    
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Employee.DoesNotExist: 
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        if request.user.is_superuser or application.company.id == employee.company.id:
            # if not tags: 
            #     return Response(Msg.TAG_NOT_FOUND, status=status.HTTP_404_NOT_FOUND )
            # tag = tags[0]
            serializer = TagSerializer(tag)
            return Response(serializer.data)

        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def create(self, request, app_id=None, node_id=None):
        try: 
            application = Application.objects.get(pk=app_id) 
            employee = Employee.objects.get(user=request.user)

            if application.company.id == employee.company.id:
                node = Node.objects.get(application=application, id=node_id)
                # if nodes:
                #     node = nodes[0]
                # else: 
                #     return Response(Msg.NODE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
                tag = Tag.objects.create(node=node, **request.data)
                serializer = TagSerializer(tag)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
            
        except Node.DoesNotExist:
            return Response(Msg.NODE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Employee.DoesNotExist: 
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response(Msg.INTETRITY_ERROR, status.HTTP_406_NOT_ACCEPTABLE)
    
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TagViewSet(viewsets.ModelViewSet):

    def update(self, request, pk=None):
        try: 
            node = Node.objects.get(pk=pk)
            application = Application.objects.get(pk=node.application.id) 
            employee = Employee.objects.get(user=request.user)

            if application.company.id == employee.company.id:
                tag = Tag.objects.get(pk=pk)
                # if not tags:
                #     return Response(Msg.TAG_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
                # for key in request.data.keys():
                #     if not request.data[key]:
                #         request.data.pop(key)
                #     print(request.data)
                serializer = TagSerializer(tag, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
            
        except Node.DoesNotExist:
            return Response(Msg.NODE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Employee.DoesNotExist: 
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Tag.DoesNotExist:
            return Response(Msg.TAG_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response(Msg.INTETRITY_ERROR, status.HTTP_406_NOT_ACCEPTABLE)
    
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        try: 
            employee = Employee.objects.get(user=request.user)
            node = Node.objects.get(pk=pk)
            tag = Tag.objects.get(pk=pk)
            application = Application.objects.get(pk=node.application.id)
        except Employee.DoesNotExist:
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Node.DoesNotExist:
            return Response(Msg.NODE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Tag.DoesNotExist:
            return Response(Msg.TAG_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        if request.user.is_superuser or application.company.id == employee.company.id:
            tag.delete()
            return Response({'msg': "tag deleted"}, status=status.HTTP_204_NO_CONTENT)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

# class Pdf(View):
#     def get(self, request, fid=None):
#         try: 
#             file = File.objects.get(pk=fid)
#             path = os.path.join(file.url, file.name)
#             fileobj = open(path, 'rb')
#             buffer = io.BytesIO(b_(fileobj.read()))
#             fileobj.close()
#             return HttpResponse(buffer.getvalue(), content_type='application/pdf')
#         except OSError as e:
#             print(e)

     