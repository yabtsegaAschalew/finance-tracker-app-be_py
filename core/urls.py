from django.urls import path
from . import views
from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView)
from django.contrib.auth import views as auth_views
urlpatterns = [

    path("sign-up/", views.sign_up),
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("reset-password/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("reset-password/done", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset-password/<uidb64>/<token>", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset-password-complete/done", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
    path("change-password/", auth_views.PasswordChangeView.as_view(), name="password_change"),
    path("change-password/done/", auth_views.PasswordChangeDoneView.as_view(), name="password_change_done"),
    path("activate/", views.activate_account, name="activate_account"),
    path("activate/<str:uidb64>/<str:token>", views.activate_account_confirm, name="activate-account-confirm")

    
]
