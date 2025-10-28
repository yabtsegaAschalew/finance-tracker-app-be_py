from django.urls import path
from . import views
from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView)
from django.contrib.auth import views as auth_views
urlpatterns = [

    path("sign-up/", views.sign_up),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("reset-password/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("reset-password/done", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset-password/<uidb64>/<token>", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset-password-complete/done", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
    # To be advanced later
    path("change-password/", views.change_password, name="password_change"),
    path("change-password/done/", auth_views.PasswordChangeDoneView.as_view(), name="password_change_done"),
    # Till here
    path("activate/", views.activate_account, name="activate_account"),
    path("activate/<str:uidb64>/<str:token>", views.activate_account_confirm, name="activate-account-confirm"),
    path("create-budget/", views.create_budget),
    path("login/", views.user_login),
    path("create-transaction/", views.create_transaction),

    
]
