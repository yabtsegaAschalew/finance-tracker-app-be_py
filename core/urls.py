from django.urls import path, re_path
from . import views
from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView)
from django.contrib.auth import views as auth_views
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
   openapi.Info(
      title="User Management",
      default_version='v1',
      description="Your API Description",
      terms_of_service="https://www.example.com/policies/terms/",
      contact=openapi.Contact(email="contact@yourdomain.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

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
    path("activate/<str:uidb64>/<str:token>", views.activate_account_confirm, name="activate-account-confirm"),
    path("create-budget/", views.create_budget),
    path("login/", views.user_login),
    path("create-transaction/", views.create_transaction),
    path("view-categories", views.view_categories),


    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

]
