# from django.shortcuts import render
from ectd.applications.models import Template, Company, Application, Employee
from rest_framework import viewsets, status
# from django.core import serializers as core_serializers
# from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from ectd.applications.serializers import *
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.parsers import FileUploadParser, MultiPartParser, FormParser
from ectd.extra.msg import Msg
from django.db import IntegrityError
import os
import uuid

# from rest_framework import mixins
# from rest_framework import generics

class TemplateViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser,)
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer

class CompanyViewSet(viewsets.ViewSet):

    def list(self, request):
        if request.user.is_superuser or True:
            queryset = Company.objects.all()
            serializer = CompanySerializer(queryset, many=True)
            return Response(serializer.data)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def retrieve(self, request, pk=None):
        try:
            company = Company.objects.get(pk=pk)
            print(company.employees)
        except Company.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        if request.user.is_superuser or True:
            serializer = CompanySerializer(company)
            return Response(serializer.data)

        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
    
    def create(self, request):
        try: 
            company = Company.objects.create(**request.data)
            print(repr(company))
            employee = Employee.objects.create(user=request.user, company=company, role='ADMIN')
            # serializer_comp = CompanySerializer(company)
            serializer = CompanySerializer(company)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            if company:
                company.delete()
            return Response({'msg': 'IntegrityError'}, status.HTTP_406_NOT_ACCEPTABLE)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def update(self, request, pk=None):
        try:
            company = Company.objects.get(pk=pk)
        except Company.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
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
        try:
            company = Company.objects.get(pk=pk)
        except Company.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        company.delete()
        return Response({'msg': "company deleted"}, status=status.HTTP_204_NO_CONTENT)

class ApplicationViewSet(viewsets.ViewSet):

    def list(self, request):
        if request.user.is_superuser or True:
            queryset = Application.objects.all()
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
            return Response({'msg': 'Employee Not Found'},status=status.HTTP_404_NOT_FOUND )    
        
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

            application = Application.objects.create(company=company, template=template, **request.data)
            serializer = ApplicationSerializer(application)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Employee.DoesNotExist:
            return Response({'msg': 'Employee Not Found'},status=status.HTTP_404_NOT_FOUND )
        except Template.DoesNotExist:
            return Response({'msg': 'Template Not Found'}, status=status.HTTP_404_NOT_FOUND)
        except Company.DoesNotExist:
            return Response({'msg': 'User has not a company'},status=status.HTTP_404_NOT_FOUND )
        except IntegrityError:
            return Response({'msg': 'IntegrityError'}, status.HTTP_406_NOT_ACCEPTABLE)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def update(self, request, pk=None):
        try:
            application = Application.objects.get(pk=pk)
            employee = Employee.objects.get(user=request.user)
        except Application.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Employee.DoesNotExist:
            return Response({'msg': 'Employee Not Found'},status=status.HTTP_404_NOT_FOUND) 
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
                Application.delete = True
                return Response({'msg': "application deleted"}, status=status.HTTP_204_NO_CONTENT)
            return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        except Employee.DoesNotExist:
            return Response({'msg': 'User is not an owner'},status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION )
        except Application.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        
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
            return Response({'msg': 'Company Not Found'},status=status.HTTP_404_NOT_FOUND )
        except IntegrityError:
            return Response({'msg': 'IntegrityError'}, status.HTTP_406_NOT_ACCEPTABLE)

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
        if request.user.is_superuser or True:
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
            return Response({'msg': 'Application Not Found'}, status=status.HTTP_404_NOT_FOUND)
        except Employee.DoesNotExist: 
            return Response({'msg': 'Employee Not Found'}, status=status.HTTP_404_NOT_FOUND)
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
            return Response({'msg': 'Application Not Found'}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response({'msg': 'IntegrityError'}, status.HTTP_406_NOT_ACCEPTABLE)
    
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def update(self, request, pk=None):
        try:
            employee = Employee.objects.get(user=request.user)
            contact = Contact.objects.get(pk=pk)
            application = Application.objects.get(pk=contact.application.id)
        except Employee.DoesNotExist:
            return Response({'msg': 'Employee Not Found'}, status=status.HTTP_404_NOT_FOUND)
        except Contact.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response({'msg': 'Application Not Found'}, status=status.HTTP_404_NOT_FOUND)
        
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
            return Response({'msg': 'Employee Not Found'}, status=status.HTTP_404_NOT_FOUND)
        except Contact.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response({'msg': 'Application Not Found'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.is_superuser or application.company.id == employee.company.id:
            contact.delete()
            return Response({'msg': "employee deleted"}, status=status.HTTP_204_NO_CONTENT)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

class AppinfoViewSet(viewsets.ModelViewSet):
    def list(self, request):
        if request.user.is_superuser or True:
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
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response({'msg': 'Application Not Found'}, status=status.HTTP_404_NOT_FOUND)
        except Employee.DoesNotExist: 
            return Response({'msg': 'Employee Not Found'}, status=status.HTTP_404_NOT_FOUND)

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
            return Response({'msg': 'Application Not Found'}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response({'msg': 'IntegrityError'}, status.HTTP_406_NOT_ACCEPTABLE)
    
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def update(self, request, pk=None):
        try:
            employee = Employee.objects.get(user=request.user)
            appinfo = Appinfo.objects.get(pk=pk)
            application = Application.objects.get(pk=appinfo.application.id)
        except Employee.DoesNotExist:
            return Response({'msg': 'Employee Not Found'}, status=status.HTTP_404_NOT_FOUND)
        except Appinfo.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response({'msg': 'Application Not Found'}, status=status.HTTP_404_NOT_FOUND)
        
        request.data['application'] = application.id
        serializer = Appinfo.Serializer(appinfo, data=request.data)
       
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
            return Response({'msg': 'Employee Not Found'}, status=status.HTTP_404_NOT_FOUND)
        except Appinfo.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response({'msg': 'Application Not Found'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.is_superuser or application.company.id == employee.company.id:
            appinfo.delete()
            return Response({'msg': "employee deleted"}, status=status.HTTP_204_NO_CONTENT)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

class FileViewSet(viewsets.ModelViewSet):
    def list(self, request):
        if request.user.is_superuser or True:
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
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response({'msg': 'Application Not Found'}, status=status.HTTP_404_NOT_FOUND)
        except Employee.DoesNotExist: 
            return Response({'msg': 'Employee Not Found'}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user.is_superuser or application.company.id == employee.company.id:
            serializer = FileSerializer(file)
            return Response(serializer.data)

        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
    
    #def create(self, request):
        # try: 
        #     app_id = request.data.pop('application')
        #     application = Application.objects.get(pk=app_id) 

        #     contact = Contact.objects.create(application=application, **request.data)
        #     serializer = ContactSerializer(contact)
        #     return Response(serializer.data, status=status.HTTP_201_CREATED)
        # except Application.DoesNotExist:
        #     return Response({'msg': 'Application Not Found'}, status=status.HTTP_404_NOT_FOUND)
        # except IntegrityError:
        #     return Response({'msg': 'IntegrityError'}, status.HTTP_406_NOT_ACCEPTABLE)
    
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        return Response({'msg': 'Cannot update file'}, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        
        try:
            employee = Employee.objects.get(user=request.user)
            file = File.objects.get(pk=pk)
            application = Application.objects.get(pk=file.application.id)
        except Employee.DoesNotExist:
            return Response({'msg': 'Employee Not Found'}, status=status.HTTP_404_NOT_FOUND)
        except File.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response({'msg': 'Application Not Found'}, status=status.HTTP_404_NOT_FOUND)
        
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
            return Response({'msg': 'Employee Not Found'}, status=status.HTTP_404_NOT_FOUND)
        except File.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response({'msg': 'Application Not Found'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.is_superuser or application.company.id == employee.company.id:
            # setattr(file, 'deleted', 'True')
            # print(getattr(file,'deleted'))
            file.deleted = True
            file.save()
            return Response({'msg': 'file deleted'}, status=status.HTTP_204_NO_CONTENT)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

class FileUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, id=None, format='pdf'):
        
        try:
            application = Application.objects.get(pk=id)
            employee = Employee.objects.get(user=request.user)
        # except File.DoesNotExist:
        #     return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response({'msg': 'Application Not Found'}, status=status.HTTP_404_NOT_FOUND)
        except Employee.DoesNotExist: 
            return Response({'msg': 'Employee Not Found'}, status=status.HTTP_404_NOT_FOUND)
    
        if application.company.id != employee.company.id:
            return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
            
        up_file = request.FILES['files']
        file_folder = uuid.uuid4().hex
        # path = '/Users/nebula-ai/Desktop/django/app_'+ id +'/'+file_folder         # MAC path
        path = 'C:/shares/django/app_'+id+'/'+file_folder  # Window path
        url = path+'/' + up_file.name
        try:
            if not os.path.exists(path):
                os.mkdir(path)
            with open(url, 'wb+') as destination:
                for chunk in up_file.chunks():
                    destination.write(chunk)
        except OSError as err:
            print("OS error: {0}".format(err))
            return Response({'msg': 'Cannot write file to server'}, status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        file = File.objects.create(application=application, name=up_file.name, url=url)
        serializer = FileSerializer(file)
        # if serializer.is_valid():
        return Response(serializer.data, status.HTTP_201_CREATED)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)