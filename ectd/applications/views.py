# from django.shortcuts import render
from ectd.applications.models import Template, Company, Application
from rest_framework import viewsets, status
# from django.core import serializers as core_serializers
# from django.http import JsonResponse
import json;
from django.forms.models import model_to_dict
from rest_framework.views import APIView
from rest_framework.response import Response
from ectd.applications.serializers import *
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from ectd.extra.msg import Msg
from django.db import IntegrityError
# from rest_framework import mixins
# from rest_framework import generics

class TemplateViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser,)
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer

class CompanyViewSet(viewsets.ViewSet):

    def list(self, request):
        if request.user.is_superuser:
            queryset = Company.objects.all()
            serializer = CompanySerializer(queryset, many=True)
            return Response(serializer.data)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def retrieve(self, request, pk=None):
        try:
            company = Company.objects.get(pk=pk)
        except Company.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        if request.user.is_superuser or request.user == company.owner:
            serializer = CompanySerializer(company)
            return Response(serializer.data)

        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
    
    def create(self, request):
        request.data['owner'] ={'id': request.user.id }  #User.objects.get(username=request.user.username)
        
        serializer = CompanySerializer(data=request.data)
        # print(serializer.is_valid())
        if serializer.is_valid():
            try: 
                serializer.create(validated_data=request.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError:
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
        except Application.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        company = Company.objects.get(pk=application.company.id)
        print(company.owner, request.user)
        if request.user.is_superuser or request.user == company.owner:
            serializer = ApplicationSerializer(application)
            return Response(serializer.data)

        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
    
    def create(self, request):
        try: 
            company = Company.objects.get(owner=request.user)
        except Company.DoesNotExist:
            return Response({'msg': 'User has not a company'},status=status.HTTP_404_NOT_FOUND )
        request.data['company'] = {'id': company.id}
        serializer = ApplicationSerializer(data=request.data)

        if serializer.is_valid():
            try: 
                application = serializer.create(validated_data=request.data)
                # data = core_serializers.serialize('json', application)
                app_data = model_to_dict(application)
                print(repr(app_data))
                return Response(json.dumps(app_data), status=status.HTTP_201_CREATED)
                # return JsonResponse(Application, safe=False)
            except IntegrityError:
                return Response({'msg': 'IntegrityError'}, status.HTTP_406_NOT_ACCEPTABLE)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def update(self, request, pk=None):
        try:
            application = Application.objects.get(pk=pk)
        except Application:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        serializer = ApplicationSerializer(application, data=request.data)
        try: 
            company = Company.objects.get(owner=request.user)
        except Company.DoesNotExist:
            return Response({'msg': 'User has not a company'},status=status.HTTP_404_NOT_FOUND )
        # print(application.company.id,company_user.id )
        if request.user.is_superuser or application.company.id == company.id:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def destroy(self, request, pk=None):
        # if  not request.user.is_superuser:
        #    return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION) 
        try: 
            company = Company.objects.get(owner=request.user)
            application = Application.objects.get(pk=pk)
            if  application.company.id == company.id:
                Application.delete = True
                return Response({'msg': "application deleted"}, status=status.HTTP_204_NO_CONTENT)
            return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        except Company.DoesNotExist:
            return Response({'msg': 'User is not an owner'},status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION )
        except Application.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        
class EmployeeViewSet(viewsets.ViewSet):
    pass

class TemplateList(APIView):

    def get(self, request, format=None):
        templates = Template.objects.all()
        serializer = TemplateSerializer(templates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        serializer = TemplateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)