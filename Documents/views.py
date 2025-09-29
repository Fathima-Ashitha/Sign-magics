from rest_framework import generics
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, permissions
from .models import *
from .serializers import *
from django.db.models import Count, Q, F
from signatures.models import *
from django.shortcuts import get_object_or_404


User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer



# Upload a document
class DocumentUploadView(generics.CreateAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_serializer_context(self):
        return {"request": self.request}


# List all documents
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def documents_by_person(request, person_id):
    """
    Fetch all documents uploaded by a specific person (owner).
    """
    try:
        owner = CustomUser.objects.get(id=person_id)
    except CustomUser.DoesNotExist:
        return Response({"detail": "User not found"}, status=404)

    documents = Document.objects.filter(owner=owner).order_by('-created_at')
    serializer = DocumentSerializer(documents, many=True, context={"request": request})

    return Response({
        "status": "success",
        "documents": serializer.data
    })


# Get document details by ID
class DocumentDetailView(generics.RetrieveAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        return {"request": self.request}


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def overview(request):
    """
    Return counts for overview dashboard:
    - total documents
    - total fully signed documents
    - pending documents
    - total users
    """

    # Fully signed documents (all signatures approved, not draft)
    fully_signed_docs = (
        DocumentSignature.objects
        .annotate(
            total_statuses=Count("signature_statuses"),
            approved_statuses=Count("signature_statuses", filter=Q(signature_statuses__status="approved"))
        )
        .filter(total_statuses=F("approved_statuses"), draft=False)
        .count()
    )

    # Pending documents: document signatures with at least one pending status
    pending_docs = (
        DocumentSignature.objects
        .filter(
            draft=False,
            signature_statuses__status="pending"
        )
        .distinct()
        .count()
    )

    total_users = CustomUser.objects.count()
    total_documents = fully_signed_docs + pending_docs

    return Response({
        "status": "success",
        "total_documents": total_documents,
        "fully_signed_documents": fully_signed_docs,
        "pending_documents": pending_docs,
        "total_users": total_users
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_users(request):
    """
    Fetch all users. Optional query params: ?role=signer&department=IT
    """
    queryset = CustomUser.objects.all()

    # Optional filters
    role = request.query_params.get("role")
    if role:
        queryset = queryset.filter(role=role)

    department = request.query_params.get("department")
    if department:
        queryset = queryset.filter(department=department)

    # Prepare response
    users = []
    for user in queryset:
        users.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "department": getattr(user, "department", None),  # if department exists
            "post": user.post
        })

    return Response({
        "status": "success",
        "users": users
    })



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_signers(request):
    """
    Fetch all users with role='signer'
    """
    signers = CustomUser.objects.filter(role="signer")

    # Prepare response
    users = []
    for user in signers:
        users.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "department": getattr(user, "department", None),
            "post": user.post
        })

    return Response({
        "status": "success",
        "signers": users
    })



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_profile_by_id(request, user_id):
    """
    Fetch the profile of a user by their ID
    """
    user = get_object_or_404(CustomUser, id=user_id)

    profile_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "department": getattr(user, "department", None),
        "post": user.post,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
    }

    return Response({
        "status": "success",
        "profile": profile_data
    })
