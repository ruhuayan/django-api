# from django.shortcuts import render
from ectd.applications.models import Template, Company, Application
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from ectd.applications.serializers import *
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
# from rest_framework import mixins
# from rest_framework import generics

class TemplateViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser,)
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

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