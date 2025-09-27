from rest_framework import generics, permissions, status
from Documents.models import Document
from .serializers import *
from .models import *
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as drf_status
from django.db.models import Count, Q, F
from django.shortcuts import get_object_or_404



# Upload a signature (POST)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_signature(request):
    """
    Allow a user with role 'signer' to upload a signature.
    If a signature already exists, override it.
    """
    # Check if user is a signer
    if request.user.role != "signer":
        return Response({"detail": "Only users with role 'signer' can upload signatures."},
                        status=status.HTTP_403_FORBIDDEN)

    try:
        # Check if user already has a signature
        signature = Signature.objects.filter(user=request.user).first()
        serializer = SignatureSerializer(signature, data=request.data) if signature else SignatureSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)  # assign current user

        return Response({
            "detail": "Signature uploaded successfully",
            "signature_id": serializer.instance.id,
            "signature_file_url": request.build_absolute_uri(serializer.instance.file.url)
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# List all signatures 
class UserSignatureListView(generics.ListAPIView):
    serializer_class = SignatureSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Signature.objects.all().order_by('-created_at')


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def assign_multiple_signatures(request, pk):
    """
    Assign multiple signatures to a document for the current user
    and store the edited file (single DocumentSignature)
    """
    # Get document
    try:
        document = Document.objects.get(id=pk)
    except Document.DoesNotExist:
        return Response({"detail": "Document not found"}, status=drf_status.HTTP_404_NOT_FOUND)

    # Validate input
    serializer = AssignMultipleSignaturesSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    signature_ids = serializer.validated_data['signature_id']
    edited_file = serializer.validated_data['file']
    status_flag = serializer.validated_data.get('status', None)  # None if not provided

    # Determine draft based on status
    is_draft = True if status_flag and status_flag.lower() == "draft" else False

    # Create one DocumentSignature for the edited file
    doc_sig_obj = DocumentSignature.objects.create(
        document=document,
        creator=request.user,
        edited_file=edited_file,
        draft=is_draft
    )

    assigned_statuses = []

    
    for sig_id in signature_ids:
        try:
            signature = Signature.objects.get(id=sig_id)
        except Signature.DoesNotExist:
            return Response({"detail": f"Signature ID {sig_id} not found"}, status=drf_status.HTTP_404_NOT_FOUND)

            # Create a status row for each signature
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
        "signer_id": doc_sig_obj.creator.id,
        "edited_file_url": request.build_absolute_uri(doc_sig_obj.edited_file.url),
        "assigned_signatures": assigned_statuses
    }, status=drf_status.HTTP_201_CREATED)



from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import DocumentSignature

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_document_signature_final(request, doc_sig_id):
    """
    Change a DocumentSignature's draft status from True to False (final)
    Only the creator can mark it as final
    """
    try:
        doc_sig = DocumentSignature.objects.get(id=doc_sig_id, creator=request.user)
    except DocumentSignature.DoesNotExist:
        return Response(
            {"detail": "DocumentSignature not found or you are not the creator."},
            status=status.HTTP_404_NOT_FOUND
        )

    if not doc_sig.draft:
        return Response(
            {"detail": "DocumentSignature is already final."},
            status=status.HTTP_400_BAD_REQUEST
        )

    doc_sig.draft = False
    doc_sig.save()

    return Response({
        "detail": "DocumentSignature marked as final.",
        "document_signature_id": doc_sig.id,
        "draft": doc_sig.draft
    }, status=status.HTTP_200_OK)




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_signed_documents(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    signed_docs = (
        DocumentSignature.objects.filter(creator=user, draft=False)
        .annotate(
            total_statuses=Count("signature_statuses"),
            approved_statuses=Count("signature_statuses", filter=Q(signature_statuses__status="approved")),
        )
        .filter(total_statuses=F("approved_statuses"))  # Only if all are approved
        .values("id", "document_id", "edited_file", "created_at")
    )

    return Response({
        "status": "success",
        "signed_documents": list(signed_docs)
    })


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import DocumentSignature, DocumentSignatureStatus, Signature, CustomUser
from .serializers import DocumentSignatureSerializer

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def signature_files_for_person(request, signature_id):
    """
    Fetch all DocumentSignature entries where:
    - The DocumentSignatureStatus has the given signature ID
    - DocumentSignature is not draft
    """
    try:
        signature = Signature.objects.get(id=signature_id)
    except Signature.DoesNotExist:
        return Response({"detail": "Signature not found"}, status=404)

    # Fetch all DocumentSignatureStatus entries for this signature
    doc_statuses = DocumentSignatureStatus.objects.filter(
        signature=signature,
        document_signature__draft=False
    ).select_related("document_signature", "document_signature__document")

    # Collect unique DocumentSignature entries
    doc_signatures = {ds.document_signature for ds in doc_statuses}

    # Serialize
    serializer = DocumentSignatureSerializer(doc_signatures, many=True, context={"request": request})

    return Response({
        "status": "success",
        "document_signatures": serializer.data
    })


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def document_sign_status(request, doc_sig_status_id, action):
    """
    Approve or reject a signature on a DocumentSignature by the signer.
    action: 'approve' or 'reject'
    """
    # Validate action
    if action not in ["approve", "reject"]:
        return Response({"detail": "Invalid action. Must be 'approve' or 'reject'."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        doc_status = DocumentSignatureStatus.objects.get(id=doc_sig_status_id)
    except DocumentSignatureStatus.DoesNotExist:
        return Response({"detail": "DocumentSignatureStatus not found."}, status=status.HTTP_404_NOT_FOUND)

    # Only signer of the signature can change the status
    if doc_status.signature.user != request.user:
        return Response({"detail": "You are not authorized to update this signature status."}, status=status.HTTP_403_FORBIDDEN)

    # Update status
    doc_status.status = "approved" if action == "approve" else "rejected"
    doc_status.save()

    return Response({
        "detail": f"Signature status updated to {doc_status.status}.",
        "document_signature_status_id": doc_status.id,
        "document_signature_id": doc_status.document_signature.id,
        "signature_id": doc_status.signature.id
    }, status=status.HTTP_200_OK)


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import DocumentSignature, DocumentSignatureStatus

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def document_signature_status(request, doc_sig_id):
    """
    Fetch all signature statuses for a single DocumentSignature
    """
    try:
        doc_sig = DocumentSignature.objects.get(id=doc_sig_id)
    except DocumentSignature.DoesNotExist:
        return Response({"detail": "DocumentSignature not found."}, status=404)

    # Fetch all statuses related to this DocumentSignature
    statuses = DocumentSignatureStatus.objects.filter(document_signature=doc_sig).select_related("signature", "signature__user")

    # Prepare response
    response_data = []
    for s in statuses:
        response_data.append({
            "status_id": s.id,
            "signature_id": s.signature.id,
            "signer_id": s.signature.user.id,
            "signer_name": s.signature.user.username,
            "status": s.status,
            "updated_at": s.updated_at
        })

    return Response({
        "document_signature_id": doc_sig.id,
        "edited_file_url": request.build_absolute_uri(doc_sig.edited_file.url) if doc_sig.edited_file else None,
        "draft": doc_sig.draft,
        "statuses": response_data
    })



from django.db.models import Count, Q, F
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def documents_by_approval_status(request):
    """
    Fetch DocumentSignature objects filtered by approval status.
    Query param: ?approved=true or ?approved=false
    """
    approved_param = request.query_params.get("approved", "true").lower()
    approved_flag = True if approved_param == "true" else False

    docs = (
        DocumentSignature.objects
        .annotate(
            total_statuses=Count("signature_statuses"),
            approved_statuses=Count("signature_statuses", filter=Q(signature_statuses__status="approved"))
        )
        .filter(draft=False)
    )

    if approved_flag:
        docs = docs.filter(total_statuses=F("approved_statuses"))  # Fully approved
    else:
        docs = docs.exclude(total_statuses=F("approved_statuses"))  # Not fully approved

    response_data = []
    for doc in docs:
        response_data.append({
            "document_signature_id": doc.id,
            "edited_file_url": request.build_absolute_uri(doc.edited_file.url) if doc.edited_file else None,
            "creator_id": doc.creator.id if doc.creator else None,
            "document_id": doc.document.id,
            "created_at": doc.created_at
        })

    return Response({
        "status": "success",
        "approved": approved_flag,
        "documents": response_data
    })
