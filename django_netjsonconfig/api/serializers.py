from rest_framework import serializers
from taggit_serializer.serializers import TaggitSerializer, TagListSerializerField

from openwisp_utils.api.serializers import ValidatedModelSerializer


class JSONSerializerField(serializers.Field):
    """
    Ensures json fields are serialized in json format
    """

    def to_representation(self, value):
        return value


class CaSerializer(ValidatedModelSerializer):
    extensions = JSONSerializerField()

    class Meta:
        model = None
        exclude = ('id', 'created', 'modified')


class CertSerializer(ValidatedModelSerializer):
    extensions = JSONSerializerField()

    class Meta:
        model = None
        exclude = ('id', 'created', 'modified')


class VpnSerializer(ValidatedModelSerializer):
    ca = CaSerializer()
    cert = CertSerializer()
    config = JSONSerializerField()

    class Meta:
        model = None
        exclude = ('id', 'created', 'modified')


class TemplateDetailSerializer(TaggitSerializer, ValidatedModelSerializer):
    vpn = VpnSerializer()
    tags = TagListSerializerField()
    config = JSONSerializerField()
    default_values = JSONSerializerField()

    class Meta:
        model = None
        exclude = ('created', 'modified')


class ListTemplateSerializer(ValidatedModelSerializer):

    class Meta:
        model = None
        fields = ['name', 'id', 'description']


class ListSubscriptionCountSerializer(serializers.Serializer):
    count = serializers.IntegerField(read_only=True)
