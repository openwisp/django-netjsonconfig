from rest_framework import serializers

from ..models import Template


class SearchTemplateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Template
        fields = ('name', 'id', 'description')
