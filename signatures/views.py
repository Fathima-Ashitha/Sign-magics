from rest_framework import generics, permissions, status
from rest_framework.response import Response
from Documents.models import Document
from .serializers import *
from .models import *


# Upload a signature (POST)
class SignatureUploadView(generics.CreateAPIView):
    queryset = Signature.objects.all()
    serializer_class = SignatureSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # automatically set current user as owner
        serializer.save(user=self.request.user)


# List all signatures of current user (GET)
class UserSignatureListView(generics.ListAPIView):
    serializer_class = SignatureSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Signature.objects.filter(user=self.request.user).order_by('-created_at')



class AssignMultipleSignaturesView(generics.GenericAPIView):
    serializer_class = AssignMultipleSignaturesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):

        try:
            document = Document.objects.get(id=pk)
        except Document.DoesNotExist:
            return Response({"detail": "Document not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        signature_ids = serializer.validated_data['signature_id']
        edited_file = serializer.validated_data['file']

        # Create DocumentSignature with signer as the current user
        doc_sig_obj = DocumentSignature.objects.create(
            document=document,
            signer=request.user,
            edited_file=edited_file
        )

        assigned_statuses = []

        for sig_id in signature_ids:
            signature = Signature.objects.get(id=sig_id)

            # Create status row for each signature
            status_obj = DocumentSignatureStatus.objects.create(
                document_signature=doc_sig_obj,
                signature=signature,
                status="pending"
            )

            assigned_statuses.append({
                "signature_id": signature.id,
                "signature_file_url": request.build_absolute_uri(signature.file.url) if signature.file else None,
                "status": status_obj.status
            })

        return Response({
            "detail": "Signatures assigned successfully",
            "document_id": document.id,
            "document_signature_id": doc_sig_obj.id,
            "signer_id": doc_sig_obj.signer.id,
            "edited_file_url": request.build_absolute_uri(doc_sig_obj.edited_file.url),
            "assigned_signatures": assigned_statuses
        }, status=status.HTTP_201_CREATED)
