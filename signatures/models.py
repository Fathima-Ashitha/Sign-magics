from django.db import models
from Documents.models import *

class Signature(models.Model):
    user = models.ForeignKey("Documents.CustomUser", on_delete=models.CASCADE)
    file = models.FileField(upload_to="signatures/")  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Signature of {self.user.username}"



class DocumentSignature(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="document_signatures")
    edited_file = models.FileField(upload_to="documents/with_signatures/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,null= True, blank=True)
    signer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null= True, blank=True)
    

class DocumentSignatureStatus(models.Model):
    document_signature = models.ForeignKey(DocumentSignature, on_delete=models.CASCADE, related_name="signature_statuses")
    signature = models.ForeignKey(Signature, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
        default="pending"
    )
    updated_at = models.DateTimeField(auto_now=True)
