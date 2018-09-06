from ectd.applications.models import *
from rest_framework import serializers
from ectd.manage.serializers import UserSerializer
from django.contrib.auth.models import User

class TemplateSerializer(serializers.HyperlinkedModelSerializer):
    class Meta: 
        model = Template
        fields = ( 'id', 'name', 'destination', 'description', 'version', 'content', 'created_at')

class CompanySerializer(serializers.ModelSerializer):
    # owner = UserSerializer(read_only=True)
    # employees = EmployeeSerializer(many=True)
    class Meta:
        model = Company
        fields = ('id',  'name', 'address', 'telephone', 'city', 'province', 'country', 'postal', 'activated', 'created_at')

    # def create(self, validated_data):
    #     owner_data = validated_data.pop('owner')
    #     user = User.objects.get(pk=owner_data['id'])
    #     company = Company.objects.create(owner=user, **validated_data)
    #     return company

class EmployeeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    company = CompanySerializer(read_only=True)
    class Meta:
        model = Employee
        fields = '__all__'

    #def create(self, validated_data):
        # user_data = validated_data.pop('user')
        # role = validated_data.pop('role')
        # user = User.objects.get(pk=user_data['id'])
        # company_data = validated_data.pop('company')
        # company = Company.objects.get(pk=company_data['id'])
        # employee = Employee.objects.create(user=user, company= company, **validated_data)
        # return employee

class ApplicationSerializer(serializers.ModelSerializer):
    # template = TemplateSerializer(read_only=True)
    template = serializers.SlugRelatedField(read_only=True, slug_field='name')
    company = CompanySerializer(read_only=True)
    class Meta:
        model = Application
        fields = '__all__'
        depth = 1
        # fields = ('id', 'template', 'company', 'number', 'description', 'sequence', 'seqDescription')


class ContactSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Contact
        fields = '__all__'

class AppinfoSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Appinfo
        fields = '__all__'

class FileSerializer(serializers.ModelSerializer):
    class Meta: 
        model = File
        fields = '__all__'

class FileStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileState
        fields = '__all__'

class NodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = '__all__'

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'
