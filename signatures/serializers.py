from rest_framework import serializers
from .models import *

class SignatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signature
        fields = ['id', 'user', 'file', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']



class AssignMultipleSignaturesSerializer(serializers.Serializer):
    signature_id = serializers.ListField(
        child=serializers.IntegerField(), write_only=True
    )
    file = serializers.FileField(write_only=True)
    status = serializers.CharField(required=False, write_only=True)  # ✅ Add this

    def validate_signature_id(self, value):
        for sig_id in value:
            if not Signature.objects.filter(id=sig_id).exists():
                raise serializers.ValidationError(f"Signature ID {sig_id} not found")
        return value



class DocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ['id', 'title', 'file', 'file_url', 'owner_id', 'created_at']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class DocumentSignatureSerializer(serializers.ModelSerializer):
    document = DocumentSerializer(read_only=True)
    edited_file_url = serializers.SerializerMethodField()
    creator_id = serializers.IntegerField(source='creator.id', read_only=True)
    creator_username = serializers.CharField(source='creator.username', read_only=True)

    class Meta:
        model = DocumentSignature
        fields = ['id', 'document', 'edited_file', 'edited_file_url', 'creator_id', 'creator_username', 'created_at']

    def get_edited_file_url(self, obj):
        request = self.context.get('request')
        if obj.edited_file and request:
            return request.build_absolute_uri(obj.edited_file.url)
        return None
