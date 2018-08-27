from ectd.applications.models import Template, Company, Application
from rest_framework import serializers

class TemplateSerializer(serializers.HyperlinkedModelSerializer):
    class Meta: 
        model = Template
        fields = ( 'id', 'name', 'destination', 'description', 'version', 'content', 'created_at')

class CompanySerializer(serializers.HyperlinkedModelSerializer):
    # owner = serializers.ReadOnlyField(source='owner.username')
    class Meta:
        model = Company
        fields = ('id', 'owner', 'name', 'address', 'telephone', 'city', 'province', 'country', 'postal', 'activated', 'created_at')
class ApplicationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Application
        fields = ('id', 'template', 'description', 'description')
