from django.urls import path
from .views import *

urlpatterns = [
    path('', upload_signature, name='signature-upload'),  # POST
    path('list/', UserSignatureListView.as_view(), name='user-signature-list'),  # GET
    path('documents/<int:pk>/assign-signature/', assign_multiple_signatures, name='assign-signature'),
    path("documentsignature/<int:doc_sig_id>/send/", mark_document_signature_final, name="mark-docsig-final"),

    path("signed_documents/<int:user_id>/", user_signed_documents, name="document-list"),

    path("documents/signer/<int:signature_id>/", signature_files_for_person, name="documents-for-signer"),

    path("doc/<int:doc_sig_status_id>/<str:action>/",document_sign_status, name="docsig-status"),

    path("doc-signature/<int:doc_sig_id>/status/", document_signature_status, name="document-signature-status"),

    path("documents/signed/", documents_by_approval_status, name="signed_documents"),


]
