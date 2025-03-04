from rest_framework_simplejwt import TokenObtainPairView, TokenRefreshView
from django.urls import path
from .views import *

urlpatterns=[
    path('register/',UserRegistration.as_view(),name='user_register'),
    path('verifyotp/',otpverify.as_view(),name='verifyotp'),
    path('login/', TokenObtainPairView.as_view(), name='token-obtain-pair'),  # JWT login
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'), 
    path('loans/', LoanListCreate.as_view(), name='loan-list-create'),
    path('loans/<int:pk>/', LoanDetailView.as_view(), name='loan-detail'),
    path('loans/<int:pk>/foreclose/', LoanForeclosure.as_view(), name='loan-foreclose'),

]