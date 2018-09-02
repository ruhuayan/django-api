from ectd.applications.models import Template, Company, Application
from rest_framework import serializers
from ectd.manage.serializers import UserSerializer
from django.contrib.auth.models import User

class TemplateSerializer(serializers.HyperlinkedModelSerializer):
    class Meta: 
        model = Template
        fields = ( 'id', 'name', 'destination', 'description', 'version', 'content', 'created_at')

class CompanySerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    class Meta:
        model = Company
        fields = ('id', 'owner', 'name', 'address', 'telephone', 'city', 'province', 'country', 'postal', 'activated', 'created_at')

    def create(self, validated_data):
        owner_data = validated_data.pop('owner')
        user = User.objects.get(pk=owner_data['id'])
        company = Company.objects.create(owner=user, **validated_data)
        return company

    # def update(self, instance, validated_data):
    #     owner_data = validated_data.pop('owner')
    #     company = 

class ApplicationSerializer(serializers.ModelSerializer):
    # template = TemplateSerializer(read_only=True)
    template = serializers.SlugRelatedField(read_only=True, slug_field='name')
    company = CompanySerializer(read_only=True)
    class Meta:
        model = Application
        fields = '__all__'
        # fields = ('id', 'template', 'company', 'number', 'description', 'sequence', 'seqDescription')

    def create(self, validated_data):
        template_data = validated_data.pop('template')
        template = Template.objects.get(pk=template_data['id'])
        company_data = validated_data.pop('company')
        company = Company.objects.get(pk=company_data['id'])
        application = Application.objects.create(template=template, company= company, **validated_data)
        return application

class EmployeeSerializer(serializers.ModelSerializer):
    pass
