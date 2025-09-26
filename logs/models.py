from django.db import models

class VerificationLog(models.Model):
    document = models.ForeignKey("Documents.Document", on_delete=models.CASCADE)
    signer = models.ForeignKey("Documents.CustomUser", on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=[("approved", "Approved"), ("rejected", "Rejected")])
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document.title} - {self.signer.username} {self.action}"
