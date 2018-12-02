# from django.shortcuts import render
from ectd.applications.models import *
from ectd.applications.serializers import *
from ectd.extra.msg import Msg
from ectd.settings import APP_DIR
from ectd.extra.tokens import account_activation_token
from django.template.loader import render_to_string

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
import json
import hashlib
import uuid
import re
from ectd.PyPDF2 import PdfFileWriter, PdfFileReader
from ectd.PyPDF2.canvas import drawBackground, drasString
from ectd.PyPDF2.utils import b_
import io
import shutil
from reportlab.pdfgen import canvas
# from reportlab.lib.pagesizes import letter
from reportlab.graphics.shapes import Rect
from reportlab.lib.colors import Color
from xml.etree.ElementTree import Element, SubElement, tostring
# import xml.etree.ElementTree as ET

# from rest_framework import mixins
# from rest_framework import generics

class TemplateViewSet(viewsets.ModelViewSet):
   
    def list(self, request):
        queryset = Template.objects.all()
        serializer = TemplateSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            template = Template.objects.get(pk=pk)
        except Template.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        serializer = TemplateSerializer(template)
        return Response(serializer.data)
    
    def create(self, request):
        if not request.user.is_superuser:
            return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        try: 
            template = Template.objects.create(**request.data)
            serializer = TemplateSerializer(template)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response(Msg.INTETRITY_ERROR, status=status.HTTP_406_NOT_ACCEPTABLE)

    def update(self, request, pk=None):
        if not request.user.is_superuser:
            return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        try:
            template = Template.objects.get(pk=pk)
        except Template.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        serializer = TemplateSerializer(template, data=request.data)
       
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        if not request.user.is_superuser:
            return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        try: 
            template = Template.objects.get(pk=pk)
        except Template.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        
        template.delete()
        return Response({'msg': "employee deleted"}, status=status.HTTP_204_NO_CONTENT)

class CompanyViewSet(viewsets.ViewSet):

    def list(self, request):
        if request.user.is_superuser:
            queryset = Company.objects.all().filter(deleted=False)
            serializer = CompanySerializer(queryset, many=True)
            return Response(serializer.data)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def retrieve(self, request, pk=None):
        try:
            company = Company.objects.get(pk=pk)
            employee = Employee.objects.get(user=request.user)
        except Company.DoesNotExist:
            return Response(Msg.COMPANY_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Employee.DoesNotExist:
            return Response(Msg.EMPLOYEE_NOT_FOUND,status=status.HTTP_404_NOT_FOUND )  
        if request.user.is_superuser or company.id == employee.company.id:
            serializer = CompanySerializer(company)
            return Response(serializer.data)

        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
    
    def create(self, request):
        try: 
            company = Company.objects.create(**request.data)
            employee = Employee.objects.create(user=request.user, company=company, role='ADMIN')

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

    @action(methods=['post'], detail=True)
    def invite(self, request, pk=None):
        try: 
            company = Company.objects.get(pk=pk)
            if request.user == company.owner:
                self.__send_invite(request.data['email'], company)
            return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        except Company.DoesNotExist:
            return Response(Msg.COMPANY_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
    
    def __send_invite(self, to_email, company):
        mail_subject = 'You are invited to join {} in Ectd}.'.format(company.name)   
        message = render_to_string('invite_email.html', {
            'email': to_email,
            'domain': 'Ectd',
            'company_id': urlsafe_base64_encode(force_bytes(company.pk)).decode(), #urlsafe_base64_encode(force_bytes(user.pk)),
            'token':account_activation_token.make_token(company),
        })
        email = EmailMessage( mail_subject, message, to=[to_email])
        email.send()

class EmployeeConfirm(APIView):
    permission_classes = (AllowAny ,)

    def post(self, request, format=None):
        try:
            company_id = force_text(urlsafe_base64_decode(request.data.pop['company_id']))
            company = Company.objects.get(pk=company_id)
            if not account_activation_token.check_token(company, request.data.pop['token']):
                return Response({'msg':'Company Token is invalid!'}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                request.data['is_active'] = True
                user = User.objects.create_user(**request.data)
                employee = Employee.objects.create(company=company, user=user, firstName='', lastName='')
                serializer = EmployeeSerializer(employee)
                return Response({'msg': 'Account Created under {}'.format(company.name)})
                
        except(TypeError, ValueError, OverflowError, User.DoesNotExist, Company.DoesNotExist):
            return Response({'msg':'error'}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response(Msg.INTETRITY_ERROR, status.HTTP_406_NOT_ACCEPTABLE)

class ApplicationViewSet(viewsets.ViewSet):

    def list(self, request):
        if request.user.is_superuser:
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
            if not len(nodes): 
                raise ValueError('no nodes')
            
            with transaction.atomic():
                application = Application.objects.create(company=company, template=template, **request.data)
                path = os.path.join(APP_DIR, company.name, 'app_{}'.format(application.id))
                
                application.path = path 
                application.save()
                # create app folder 
                # APP_PATH = '/home/ectd/{}/app_{}/{}'.format(company.name, application.id, application.number)
                APP_PATH = os.path.join(path, application.number, application.sequence)
                # APP_PATH = 'C:\shares\django\{}\\app_{}\{}'.format(company.name, application.id, application.number)

                os.makedirs(APP_PATH, exist_ok=True)
                # print(os.path.exists(APP_PATH))
                util_path = os.path.join(APP_PATH, 'util')
                os.makedirs(util_path, exist_ok=True)
                self.__copytree(os.path.join(APP_DIR, 'util'), util_path)
                
                for n in nodes:
                    if n['id']=='sub1':
                        n['text'] = application.sequence
                        # print(repr(n))
                    n['original'] = True;
                    # print(repr(n))
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
            return Response(Msg.INTETRITY_ERROR, status=status.HTTP_406_NOT_ACCEPTABLE)
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

    #API /application/5/size
    @action(methods=['get'], detail=True,)
    def size(self, request, pk=None):
        try: 
            employee = Employee.objects.get(user=request.user)
            application = Application.objects.get(pk=pk)
            if request.user.is_superuser or application.company.id == employee.company.id:
                queryset = File.objects.filter(application=application, deleted = False)
                size = 0 #######################################files total size
                return Response({'size': size})
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
                ori_nodes = Node.objects.filter(application = application)
                APP_PATH = os.path.join(application.path, application.number, application.sequence)
                if not len(nodes): 
                    raise ValueError('no nodes')
                query_set=[]
                with transaction.atomic():
                    for n in nodes:
                        # print(repr(n))
                        node, created = Node.objects.update_or_create(application=application, id=n['id'], defaults=n)
                        query_set.append(node)

                        if node.type == 'file':
                            node_path = self.__get_node_path(ori_nodes, node.parent, [])
                            print(node_path)
                            path = os.path.join(APP_PATH, node_path)
                            if not os.path.exists(path):
                                os.makedirs(path, exist_ok=True)
                            try:
                                file = File.objects.get(pk=node.id)
                                if created: 
                                    shutil.copy2(os.path.join(file.url, file.name), path)
                                else:
                                    shutil.move(os.path.join(file.dest_url, file.name), path)
                                file.dest_url = path
                                file.save()

                            except File.DoesNotExist:
                                return Response(Msg.FILE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

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
            if not application.company.id == employee.company.id:
                return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

            app_path = os.path.join(application.path, application.number, application.sequence)
            # self.__remove_empty_folders(app_path)
            md5sum = self.__create_index(application, app_path)
            with open(os.path.join(app_path, 'index_md5.txt'), 'w') as f:
                f.write(md5sum)
            # create zip file first time
            import zipfile
            output = io.BytesIO()
            len_path = len(application.path)
            with zipfile.ZipFile(output, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
                for dirname, subdirs, files in os.walk(app_path):
                    # zf.write(dirname)
                    for filename in files:
                        file_path = os.path.join(dirname, filename)
                        zf.write(file_path, file_path[len_path:])

            response = HttpResponse(output.getvalue(), content_type='application/x-zip-compressed')
            response['Content-Disposition'] = 'attachment; filename={}.zip'.format(application.number)
            response['Content-Length'] = output.tell()
            return response
        except OSError:
            return Response({'msg': 'Cannot read file from server'}, status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Employee.DoesNotExist:
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)   

    def __create_index(self, application, app_path):
        
        nodes = Node.objects.filter(application=application)
        root = Element('ectd:ectd') 
        root.set('dtd-version', '3.2')
        root.set('xmlns:ectd', 'http://www.ich.org/ectd')
        root.set('xmlns:xlink', 'http://www.w3c.org/1999/xlink')
        elems = {}
        for node in nodes:
            if node.parent == '#':
                continue
            elif node.parent=='sub1':
                elems[node.id] = SubElement(root, 'm{}'.format(node.text.lower().replace(' ', '-')))
                if node.id == 'm1':
                    md5sum = self.__create_regional(application, nodes)
                    leaf = SubElement(elems['m1'], 'leaf')
                    leaf.set('ID', uuid.uuid4().hex)
                    leaf.set('operation', 'new')
                    leaf.set('xlink:href', 'm1/us/us-regional.xml')
                    leaf.set('checksum', str(md5sum))
                    leaf.set('checksum-type', 'MD5')
                    title = SubElement(leaf, 'title')
                    title.text = 'USA'

            elif node.type=='file' and not node.parent.rfind('m1') >= 0:
                file = File.objects.get(pk=node.id)
                if node.parent.rfind('m4')>=0 or node.parent.rfind('m5')>=0:

                    md5sum = self.__md5sum(os.path.join(file.dest_url, file.name))
                    leaf = SubElement(elems[node.parent], 'leaf')
                    leaf_id = uuid.uuid4().hex
                    leaf.set('ID', leaf_id)
                    leaf.set('operation', 'new')
                    leaf.set('xlink:href', '{}/{}'.format(file.dest_url, file.name))
                    leaf.set('checksum', str(md5sum))
                    leaf.set('checksum-type', 'MD5')
                    title = SubElement(leaf, 'title')
                    title.text = node.text
                    try: 
                        tag = Tag.objects.get(node=node)
                        path, md5sum = self.__create_stf(file.dest_url, tag, leaf_id, app_path)
                        elem.set('xlink:href', path)
                        elem.set('checksum', str(md5sum))
                    except Tag.DoesNotExist: 
                        pass          #return false;
                    elem = SubElement(elems[node.parent], 'leaf')
                    elem.set('ID', uuid.uuid4().hex)
                    elem.set('operation', 'new')
                    
                    
                    elem.set('checksum-type', 'MD5')
                    elem.set('version', 'STF Version 2.2')
                    title = SubElement(elem, 'title')
                    title.text = node.text

                else: 
                    md5sum = self.__md5sum(os.path.join(file.dest_url, file.name))
                    elem = SubElement(elems[node.parent], 'leaf')
                    elem.set('ID', uuid.uuid4().hex)
                    elem.set('operation', 'new')
                    elem.set('xlink:href', '{}/{}'.format(file.dest_url, file.name))
                    elem.set('checksum', str(md5sum))
                    elem.set('checksum-type', 'MD5')
                    title = SubElement(elem, 'title')
                    title.text = node.text
            else:
                elems[node.id] = SubElement(elems[node.parent], 'm{}'.format(node.text.lower().replace(' ', '-')))
                try: 
                    tag = Tag.objects.get(node = node)
                    if re.search('m[23].3S', node.text):
                        elems[node.id].set('manufacturer', tag.manufacturer)
                        elems[node.id].set('substance', tag.substance)
                    elif re.search('m2.3P', node.text) or re.search('m3.3P', node.text):
                        elems[node.id].set('manufacturer', tag.manufacturer)
                        elems[node.id].set('dosageform', tag.dosage)
                        elems[node.id].set('product-name', tag.productName)
                    # else:
                    #     for k, v in vars(tag).items():
                    #         if v:
                    #             elems[node.id].set(k, v)
                except Tag.DoesNotExist:
                    continue
        header = '''<?xml version="1.0" encoding="utf-8"?>
        <!DOCTYPE ectd:ectd SYSTEM "util/dtd/ich-ectd-3-2.dtd">
        <?xml-stylesheet href="util/style/ectd-2-0.xsl" type="text/xsl"?>'''
        index_xml = tostring(root).decode('utf-8')
        md5sum = None
        with open(os.path.join(app_path, "index.xml"), "w+") as index_file:
            index_file.write(header)
            index_file.write(index_xml)
            md5sum = hashlib.md5(index_file.read().encode('utf-8')).hexdigest()
        return md5sum
    
    def __md5sum(self, filename, blocksize=65536):
        hash = hashlib.md5()
        with open(filename, "rb") as f:
            for block in iter(lambda: f.read(blocksize), b""):
                hash.update(block)
        return hash.hexdigest()

    def __create_regional(self, application, nodes):
        app = Appinfo.objects.get(application = application)
        contacts = Contact.objects.filter(application = application)
        contact = contacts.filter(contactType = 'AGT')
        if not contact:
            contact = contacts[0]
        header = '''<?xml version="1.0" encoding="utf-8"?>
        <!DOCTYPE fda-regional:fda-regional SYSTEM "http://www.accessdata.fda.gov/static/eCTD/us-regional-v3-3.dtd">
        <?xml-stylesheet href="http://www.accessdata.fda.gov/static/eCTD/us-regional.xsl" type="text/xsl"?>'''
        root = Element('fda-regional:fda-regional') 
        root.set('dtd-version', '3,3')
        root.set('xmlns:fda-regional','http://www.ich.org/fda')
        root.set('xmlns:xlink', 'http://www.w3c.org/1999/xlink')

        admin = SubElement(root, 'admin')

        # start Element appinfo
        appinfo = SubElement(admin, 'application-info')
        appinfo_id = SubElement(appinfo, 'id')
        appinfo_id.text = app.dunso  #not sure
        c_name = SubElement(appinfo, 'company-name')
        c_name.text = app.companyName
        s_description = SubElement(appinfo, 'submission-description')
        s_description.text = app.description
        app_contacts = SubElement(appinfo, 'applicant-contacts')
        app_contact = SubElement(app_contacts, 'applicant-contact')
        contact_name = SubElement(app_contact, 'applicant-contact-name')
        contact_name.set('applicant-contact-type', 'fdaact3')
        contact_name.text = contact.contactName
        telephones = SubElement(app_contact, 'telephones')
        telephone = SubElement(telephones, 'telephone')
        telephone.set('telephone-number-type', 'fdatnt1')
        telephone.text = contact.phone
        emails = SubElement(app_contacts, 'emails')
        email = SubElement(emails, 'email')
        email.text = contact.email
        #end Element appinfo

        app_set = SubElement(admin, 'application-set')
        app_application = SubElement(app_set, '<application')
        app_application.set('application-containing-files', 'true')
        app_information = SubElement(app_application, 'application-information')
        app_number = SubElement(app_information, 'application-number')
        app_number.set('application-type', 'fdaat4')       # not sure
        app_number.text = application.number
        s_information = SubElement(app_application, 'submission-information')
        s_id = SubElement(s_information, 'submission-id')
        s_id.set('submission-type', 'fdast1')   #not sure
        s_id.text = app.subId
        s_number = SubElement(s_information, 'sequence-number')
        s_number.set('submission-sub-type', 'fdasst3')
        s_number.text = application.sequence
        ######
        form_path = os.path.join(application.path, application.number, application.sequence, 'm1/m1us/m11.1/fda-form-1571.pdf')
        if os.path.exists(form_path):
            md5sum = self.__md5sum(form_path)
            form = SubElement(s_information, 'form')
            form.set('form-type', 'fdaft1')  #not sure
            leaf = SubElement(form, 'leaf')
            leaf.set('ID', uuid.uuid4().hex)
            leaf.set('operation', 'new')
            leaf.set('xlink:href', '11-forms/fda-form-1571.pdf')
            leaf.set('checksum', md5sum)
            leaf.set('checksum-type', 'MD5')
            title = SubElement(leaf, 'title')
            title.text = '1.1.1 FDA 1571'
        #end admin

        #m1-regional
        form_path = os.path.join(application.path, application.number, application.sequence, 'm1/m1us/m11.1/fda-form-3674.pdf')
        if os.path.exists(form_path):
            reg = SubElement(root, 'm1-regional')

            md5sum = self.__md5sum(form_path)
            forms = SubElement(reg, 'm1-1-forms')
            form = SubElement(forms, 'form')
            form.set('form-type', 'fdaft7')  #not sure
            leaf = SubElement(form, 'leaf')
            leaf.set('ID', uuid.uuid4().hex)
            leaf.set('operation', 'new')
            leaf.set('xlink:href', '11-forms/fda-form-3674.pdf')
            leaf.set('checksum', md5sum)
            leaf.set('checksum-type', 'MD5')
            title = SubElement(leaf, 'title')
            title.text = '1.1.7 FDA 3674'
        reg_xml = tostring(root).decode("utf-8")
        app_path = os.path.join(application.path, application.number, application.sequence)
        # print(os.path.join(app_path, 'm1','m1us', 'us-regional.xml'))
        with open(os.path.join(app_path, 'm1','m1us','us-regional.xml'), 'w+') as reg_file:
            reg_file.write(header)
            reg_file.write(reg_xml)
            md5sum = hashlib.md5(reg_file.read().encode('utf-8')).hexdigest()
            # print(md5sum)
        if md5sum: 
            return md5sum
        return null

    def __create_stf(self, file_path, tag, leaf_id, app_path):
        root = Element('ectd:study') 
        root.set('dtd-version', '2.2')
        root.set('xmlns:ectd','http://www.ich.org/ect')
        root.set('xmlns:xlink', 'http://www.w3c.org/1999/xlink')

        identifier = SubElement(root, 'study-identifier')
        title = SubElement(identifier, 'title')
        title.text = tag.title
        study_id = SubElement(identifier, 'study-id')
        study_id.text = tag.studyNumber

        document = SubElement(root, 'study-document')
        content = SubElement(document, 'doc-content')
        relpath = os.path.relpath(app_path, file_path)
        print(relpath)
        content.set('xlink:href', '{}index.xml#{}'.format(relpath, leaf_id))             #file path
        file_tag = SubElement(content, 'file-tag')
        file_tag.set('name', tag.stfType)
        file_tag.set('info-type', 'ich')
        
        stf = tostring(root)
        stf_path = os.path.join(file_path, '{}.xml'.format(tag.studyNumer))

        header = '''<?xml version="1.0" encoding="utf-8"?>
        <!DOCTYPE ectd:study SYSTEM "{}">
        <?xml-stylesheet href="{}" type="text/xsl"?>
        '''.format(os.path.relpath('util/dtd/ich-stf-v2-2.dtd', stf_path), os.path.relpath('util/style/ich-stf-stylesheet-2-2a.xsl', stf_path))
        with open(sft_path, 'w+') as stf_file:
            stf_file.write(header)
            stf_file.write(stf)
            md5sum = hashlib.md5(stf_file.read()).hexdigest()
        # if md5sum:
        return stf_path, md5sum

    def indent(self, elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def __get_node_path(self, nodes, parent, parents):
        # print(repr(parents))
        if parent =='sub1':
            return os.path.join(*reversed(parents))
        for node in nodes:
            if node.id == parent:
                parents.append(parent)
                return self.__get_node_path(nodes, node.parent, parents)

    def __remove_empty_folders(self, path):
        if not os.path.isdir(path):
            return
        try:
            for root, dirs, files in os.walk(path, topdown = False):
                for d in dirs:
                    full_path = os.path.join(root, d)
                    if all(os.path.isdir(file) for file in os.listdir(full_path)):
                        os.rmdir(full_path)  
        except OSError as ex:
            print('Error :', ex)
    
    def __copytree(self, src, dst, symlinks=False, ignore=None):
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, symlinks, ignore)
            else:
                shutil.copy2(s, d)

class EmployeeViewSet(viewsets.ModelViewSet):
    def list(self, request):
        if request.user.is_superuser:
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
    
    # def update(self, request, pk=None):   
    #     try:
    #         employee = Employee.objects.get(user=request.user)
    #         file = File.objects.get(pk=pk)
    #         application = Application.objects.get(pk=file.application.id)
    #     except Employee.DoesNotExist:
    #         return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
    #     except File.DoesNotExist:
    #         return Response(Msg.FILE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
    #     except Application.DoesNotExist:
    #         return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        
    #     request.data['application'] = application.id
    #     serializer = FileSerializer(contact, data=request.data)
       
    #     if request.user.is_superuser or application.company.id == employee.company.id:
    #         if serializer.is_valid():
    #             serializer.save()
    #             return Response(serializer.data)
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #     return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

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
                if file.des_url:
                    last_file = os.path.join(file.dest_url, file.name)
                    if os.path.exists(last_file):
                        os.remove(last_file)
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
            # state = FileState.objects.filter(file=file).last()
            application = Application.objects.get(pk=file.application.id)
            employee = Employee.objects.get(user=request.user)
        except File.DoesNotExist:
            return Response(Msg.FILE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        # except FileState.DoesNotExist:
        #     return Response(Msg.FILESTATE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Application.DoesNotExist:
            return Response(Msg.APPLICATION_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        except Employee.DoesNotExist: 
            return Response(Msg.EMPLOYEE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
            
        if not request.user.is_superuser and not application.company.id == employee.company.id:
            return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        if file.dest_url:
            path = os.path.join(file.dest_url, file.name)
        else:
            path = os.path.join(file.url, file.name)
        try: 
            fileobj = open(path, 'rb')
            buffer = io.BytesIO(b_(fileobj.read()))
            fileobj.close()
            return HttpResponse(buffer.getvalue(), content_type='application/pdf')
        except OSError:
            return Response({'msg': 'Cannot read file from server'}, status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            # path = '/home/ectd/{}/app_{}/{}'.format(application.company.name, app_id,file_folder)                 # ubuntu
            # path = 'C:/shares/django/app_{}/{}'.format(app_id,file_folder)  # Window path
            path = os.path.join(application.path, file_folder)
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
                            # print(page_w, page_h)
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
                            # print(link['rect'])
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
                dest_file = File.objects.get(pk=link['tfid'])
                path = os.path.relpath(dest_file.dest_url, f.dest_url)
                uri = os.path.join(path, dest_file.name)
                writer.addURI(int(link['page'])-1, uri, link['rect'])

            if f.dest_url == None:
                return Response({'msg': 'file dest path does not exist'}, status=status.HTTP_404_NOT_FOUND)
            output_path = f.dest_url #os.path.join(f.url, 'states')
            try:
                if not os.path.exists(output_path):
                    os.mkdir(output_path)
                with open(os.path.join(output_path, f.name), 'wb+') as destination:
                    writer.write(destination)
            except OSError as err:
                print("OS error: {0}".format(err))
                return Response({'msg': 'Cannot write file to server'}, status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            fileState = FileState.objects.create(file=f, action=request.data['action'])
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

     