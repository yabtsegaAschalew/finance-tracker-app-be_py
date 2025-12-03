from django.urls import path, re_path
from . import views
from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView)
from django.contrib.auth import views as auth_views



urlpatterns = [

    path("sign-up/", views.sign_up),
    path("activate/<str:uidb64>/<str:token>", views.activate_account_confirm, name="activate-account-confirm"),
    path("login/", views.user_login, name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),    
    path("reset-password/", views.password_reset_request, name="password_reset_api"),
    path("reset-password-confirm/<uidb64>/<token>/", views.password_reset_confirm, name="password_reset_confirm_api"),

    path("change-password/", views.change_password, name="password_change"),
    
    path("create-budget/", views.create_budget),
    
    path("create-transaction/", views.create_transaction),
    path("get-transaction/", views.get_transaction),
    path("view-categories/", views.view_categories),

    path("pay/", views.chapa_payment, name="payment_gateway"),
    path("payment-success/", views.chapa_success),

    # path("chapa-webhook/", views.chapa_webhook),
    path("get-bank/", views.get_banks_info),
    path("chapa-bank-transfer/<int:bank_id>", views.chapa_bank_transfer),
    path("ussd-payment/", views.initiate_payment_ussd),

    path('dashboard/metrics/', views.dashboard_metrics, name='dashboard-metrics'),
    path('dashboard/quick-stats/', views.dashboard_quick_stats, name='dashboard-quick-stats'),
]
