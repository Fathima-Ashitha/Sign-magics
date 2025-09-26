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

    def validate_signature_id(self, value):
        for sig_id in value:
            if not Signature.objects.filter(id=sig_id).exists():
                raise serializers.ValidationError(f"Signature ID {sig_id} not found")
        return value
