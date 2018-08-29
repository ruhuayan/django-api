# from django.shortcuts import render
from ectd.applications.models import Template, Company, Application
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from ectd.applications.serializers import *
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from ectd.extra.msg import Msg
# from rest_framework import mixins
# from rest_framework import generics

class TemplateViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser,)
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer

# class CompanyViewSet(viewsets.ModelViewSet):
#     queryset = Company.objects.all()
#     serializer_class = CompanySerializer
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
        # request.data['owner'] = request.user.username
        print(repr(request.data))
        serializer = CompanySerializer(data=request.data)
        if serializer.is_valid():
            serializer.create(validated_data=request.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
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
        return Response(status=status.HTTP_204_NO_CONTENT)

class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer

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