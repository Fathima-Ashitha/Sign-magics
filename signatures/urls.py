from django.urls import path
from .views import *

urlpatterns = [
    path('', SignatureUploadView.as_view(), name='signature-upload'),  # POST
    path('list/', UserSignatureListView.as_view(), name='user-signature-list'),  # GET
    path('documents/<int:pk>/assign-signature/', AssignMultipleSignaturesView.as_view(), name='assign-signature'),

]
