from rest_framework import serializers
from taggit_serializer.serializers import TaggitSerializer, TagListSerializerField


class JSONSerializerField(serializers.Field):
    """
    Ensures json fields are serialized in json format
    """

    def to_representation(self, value):
        return value


class CaSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = "__all__"


class CertSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = "__all__"


class VpnSerializer(serializers.ModelSerializer):
    ca = CaSerializer(read_only=True)
    cert = CertSerializer(read_only=True)
    config = JSONSerializerField()

    class Meta:
        model = None
        fields = "__all__"


class TemplateDetailSerializer(TaggitSerializer, serializers.ModelSerializer):
    vpn = VpnSerializer(read_only=True)
    tags = TagListSerializerField()
    config = JSONSerializerField()
    default_values = JSONSerializerField()

    class Meta:
        model = None
        fields = "__all__"


class ListTemplateSerializer(serializers.ModelSerializer):

    class Meta:
        model = None
        fields = ('name', 'id', 'description')
