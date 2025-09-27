from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('documents/', DocumentUploadView.as_view(), name='document-upload'),       # POST
    path('documents/list/<int:person_id>/', documents_by_person, name='document-list'),       # GET
    path('documents/<int:pk>/', DocumentDetailView.as_view(), name='document-detail'), # GET

    path("overview/", overview, name="overview"),
    path("users/", list_users, name="list-users"),
    path("users/signers/", list_signers, name="list-signers"),
    path("profile/<int:user_id>/", user_profile_by_id, name="current-user-profile"),

]
