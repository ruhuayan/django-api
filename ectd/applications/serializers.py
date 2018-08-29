from ectd.applications.models import Template, Company, Application
from rest_framework import serializers
from ectd.manage.serializers import UserSerializer
from django.contrib.auth.models import User

class TemplateSerializer(serializers.HyperlinkedModelSerializer):
    class Meta: 
        model = Template
        fields = ( 'id', 'name', 'destination', 'description', 'version', 'content', 'created_at')

class CompanySerializer(serializers.ModelSerializer):
    owner = UserSerializer(required=True)
    class Meta:
        model = Company
        fields = ('id', 'owner', 'name', 'address', 'telephone', 'city', 'province', 'country', 'postal', 'activated', 'created_at')
    def create(self, validated_data):
        owner_data = validated_data.pop('owner')
        user = User.objects.get(pk=owner_data['id'])
        company = Company.objects.create(owner=user, **validated_data)
        return company

class ApplicationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Application
        fields = '__all__'
