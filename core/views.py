from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework import status
from core.serializers import UserSerializer, BudgetSerializer, LoginSerializer, TransactionSerializer, ChangePasswordSerializer, DashboardMetricsSerializer
from core.models import User, Category, Budget, Transaction
from rest_framework.response import Response
from django.core.mail import send_mail, EmailMultiAlternatives
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_str, force_bytes
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
import time, uuid
from datetime import datetime
from drf_yasg.utils import swagger_auto_schema
from core.utils import payment_gateway, verify_payment, calculate_user_payment, bank_transfer, get_bank, initiate_payment
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.tokens import default_token_generator
from finance_tracker.settings import DEFAULT_FROM_EMAIL
from django.db import transaction
from django.shortcuts import render
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from collections import defaultdict
import calendar

token_generator = PasswordResetTokenGenerator()
tx_ref = f"tx-{uuid.uuid4().hex[:30]}"

@swagger_auto_schema(method='post', request_body=UserSerializer)
@api_view(["POST"])
def sign_up(request):

    serializer = UserSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data.get("username")
    email = serializer.validated_data.get("email")
    phone_number = serializer.validated_data.get("phone_number")

    if User.objects.filter(username=username).exists():
        return Response({"message": "Username taken"}, status=status.HTTP_403_FORBIDDEN)
    if User.objects.filter(email=email).exists():
        return Response({"message": "Email already taken"}, status=status.HTTP_403_FORBIDDEN)
    if User.objects.filter(phone_number=phone_number).exists():
        return Response({"message": "Phone number already taken"}, status=status.HTTP_403_FORBIDDEN)


    user = serializer.save()


    try:
        time.sleep(1)
        token = token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        activation_link = f"{request.scheme}://{request.get_host()}/api/activate/{uid}/{token}"
        send_mail(
            subject="Activate your account",
            from_email="yaba8084@gmail.com",
            message=f"Click the link to activate your account: {activation_link}",
            recipient_list=[email],
            fail_silently=False,
        )
        return Response({"message": "Activation email sent"}, status=status.HTTP_200_OK)
    except Exception:
        return Response({"message": "An error occurred sending activation email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(method='post', request_body=LoginSerializer)
@api_view(["POST"])
def user_login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data.get("username")
    password = serializer.validated_data.get("password")


    if not username or not password:
        return Response({"message": "Username and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request=request, username=username, password=password)
    if user is None:
        return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

    if not user.is_active:
        return Response({"message": "Account is not active"}, status=status.HTTP_403_FORBIDDEN)

    refresh = RefreshToken.for_user(user)
    return Response({
        "refresh": str(refresh), 
        "access": str(refresh.access_token)
        }, status=status.HTTP_200_OK)
            
@api_view(["GET"])
def activate_account_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

        if token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            print("hello active")
            return render(request, "templates/activate.html")
            # return Response({"message": "Account activated successfully"}, status=status.HTTP_200_OK)
        else:
            return render(request, "activate.html")
            # return Response({"message": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return render(request, "activate.html")
        # return Response({"error": "Invalid activation link"}, status=status.HTTP_400_BAD_REQUEST)

def check(request):
    return render(request, "activate.html")
    
@api_view(["POST"])
def password_reset_request(request):

    email = request.data.get("email")

    if not email:
        return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"message": "If an account with that email exists, a reset link has been sent."},
                        status=status.HTTP_200_OK)


    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    reset_link = f"{request.scheme}://{request.get_host()}/api/reset-password-confirm/{uid}/{token}/"

    
    send_mail(
        subject="Password Reset Request",
        message=f"Click the link below to reset your password:\n\n{reset_link}",
        from_email=DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )

    return Response({
        "message": "Password reset email sent successfully."
    }, status=status.HTTP_200_OK)



@api_view(["POST"])
def password_reset_confirm(request, uidb64, token):

    new_password = request.data.get("new_password")
    confirm_new_password = request.data.get("confirm_new_password")

    if new_password == confirm_new_password:

        if not new_password:
            return Response(
                {"error": "New password is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({"error": "Invalid user identifier."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response(
            {"message": "Password has been reset successfully."},
            status=status.HTTP_200_OK
        )
    else:
        return Response(
            {"message": "Password mismatch"},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)

    user = request.user
    user.set_password(serializer.validated_data['new_password'])
    user.save(update_fields=['password'])

    return Response(
        {"message": "Password changed successfully"},
        status=status.HTTP_200_OK
    )  

@swagger_auto_schema(method='post', request_body=BudgetSerializer)
@api_view(["POST", "GET"])
@permission_classes([IsAuthenticated])
def create_budget(request):
    user = request.user

    if request.method == "POST":
        serializer = BudgetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)  
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    elif request.method == "GET":
        budgets = Budget.objects.filter(user=user).select_related("category", "transaction")
        serializer = BudgetSerializer(budgets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@swagger_auto_schema(method='post', request_body=TransactionSerializer)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_transaction(request):
    serializer = TransactionSerializer(data=request.data)
    if serializer.is_valid():
        transaction = serializer.save(user=request.user)
        return Response(
            {
                "message": "Transaction created successfully",
                "transaction": TransactionSerializer(transaction).data
            },
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_transaction(request):
    user = request.user.id

    if request.method == "GET":
        transaction = Transaction.objects.filter(user=user).select_related("category", "user")
        serializer = TransactionSerializer(transaction, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
def view_categories(request):
    if request.method == "GET":
        values = Category.objects.all().values()
        return Response(values, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def chapa_payment(request):
    amount = calculate_user_payment(request.user.id)
    

    response = payment_gateway(
        amount["amount_to_pay"],
        request.user.email,
        request.user.first_name,
        request.user.last_name,
        request,
        request.user.phone_number,
        tx_ref
    )

    data = response.data if isinstance(response, Response) else response

    
    serializer = TransactionSerializer(
        data={
            'user': request.user.id,
            'category': 1,  
            'amount': amount,
            'description': "",
            'tx_ref': tx_ref,
            'status': "Pending"
        }
    )

    if serializer.is_valid():
        serializer.save(user=request.user)
        print("Transaction saved successfully")
    else:
        print("Serializer errors:", serializer.errors)
    
        


    return response  
        
# @api_view(["POST"])
# def chapa_webhook(request):
#     if request.method == "POST":    
#         url = "https://api.chapa.co/v1/transaction/verify/{}"

#         payload = ''
#         headers = {
#             'Authorization': 'Bearer CHASECK_TEST-mgWrd2rhogka8FINIdgfl7wM2Yo1mpwL'
#         }

#         response = requests.get(url, headers=headers, data=payload)
#         data = response.text
#         print(data)

#         return Response("Webhook")

@api_view(["GET"])
def chapa_success(request):

    return Response({"message": "Payment completed successfully!"})


@api_view(["GET"])
def chapa_callback(request):

    return Response({"message": "Callback received successfully!"})  


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chapa_bank_transfer(request, bank_id):

    try:
        account_number = request.data.get("account_number")
        if not account_number:
            return Response({"error": "Account number is required"}, status=400)

        payment_info = calculate_user_payment(request.user.id)
        amount = payment_info.get("amount_to_pay", 0)
        
        if amount <= 0:
            return Response({"error": "No payment required"}, status=400)
        

        bank_response = bank_transfer(account_number, amount, tx_ref, bank_id)
        

        with transaction.atomic():  
            payment_category, _ = Category.objects.get_or_create(
                name='Payment',
                defaults={'type': 'expense', 'priority': 'High'}
            )
            
            transaction_obj = Transaction.objects.create(  
                user=request.user,
                category=payment_category,
                amount=amount,
                description=f"Bank transfer payment via {bank_id}",
                tx_ref=tx_ref,
                status='Pending'
            )
            transaction_obj.save(request.user)
        
        return Response({
            "message": "Bank transfer initiated successfully",
            "transaction_ref": tx_ref,
            "amount": amount,
            "bank_response": bank_response,
            "status": "pending"
        })
        
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_banks_info(request):
    if request.method == "GET":

        return Response(
        {
            "data": get_bank()
        }
    )

@permission_classes([IsAuthenticated])
@api_view(["POST"])
def initiate_payment_ussd(request):
    if request.method == "POST":

        filter_user = User.objects.filter(id=request.user.id).values("phone_number")

        phone_number = filter_user[0]["phone_number"]
        data = initiate_payment(tx_ref, phone_number)

        amount = calculate_user_payment(request.user.id)

        if data["status"] == "success":

            serializer = TransactionSerializer(
            data={
                'user': request.user.id,
                'category': 1,  
                'amount': amount,
                'description': "",
                'tx_ref': tx_ref,
                'status': "Pending"
            })
            serializer.save(user=request.user)
        


        return Response(
            {
                "data": data,
            }
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_metrics(request):

    user = request.user

    today = timezone.now().date()
    current_month_start = today.replace(day=1)
    next_month_start = (current_month_start + timedelta(days=32)).replace(day=1)
    
    transactions = Transaction.objects.filter(user=user)
    
    income_transactions = transactions.filter(category__type='income', status='Success')
    expense_transactions = transactions.filter(category__type='expense', status='Success')
    
    total_income = income_transactions.aggregate(total=Sum('amount'))['total'] or 0
    total_expenses = expense_transactions.aggregate(total=Sum('amount'))['total'] or 0
    total_balance = total_income - total_expenses
    

    current_month_income = income_transactions.filter(
        date__gte=current_month_start,
        date__lt=next_month_start
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    current_month_expenses = expense_transactions.filter(
        date__gte=current_month_start,
        date__lt=next_month_start
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    current_month_savings = current_month_income - current_month_expenses
    

    savings_rate = (current_month_savings / current_month_income * 100) if current_month_income > 0 else 0
    

    current_month_budgets = Budget.objects.filter(
        user=user,
        due_date__gte=current_month_start,
        due_date__lt=next_month_start
    )
    
    total_budget_limit = current_month_budgets.aggregate(total=Sum('amount'))['total'] or 0
    

    budget_spent_data = {}
    for budget in current_month_budgets:
        category_spent = expense_transactions.filter(
            category=budget.category,
            date__gte=current_month_start,
            date__lt=next_month_start
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        budget_spent_data[budget.id] = category_spent
    
    total_budget_spent = sum(budget_spent_data.values())
    

    budget_health = ((total_budget_limit - total_budget_spent) / total_budget_limit * 100) if total_budget_limit > 0 else 100
    

    monthly_data = []
    for i in range(5, -1, -1):
        month_start = (current_month_start - timedelta(days=30*i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        
        month_income = income_transactions.filter(
            date__gte=month_start,
            date__lt=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        month_expenses = expense_transactions.filter(
            date__gte=month_start,
            date__lt=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        month_name = calendar.month_abbr[month_start.month]
        
        monthly_data.append({
            'month': f'{month_name} {month_start.year}',
            'income': float(month_income),
            'expenses': float(month_expenses)
        })
    

    category_spending = []
    expense_categories = Category.objects.filter(type='expense')
    
    total_expenses_current = expense_transactions.filter(
        date__gte=current_month_start,
        date__lt=next_month_start
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    for category in expense_categories:
        category_amount = expense_transactions.filter(
            category=category,
            date__gte=current_month_start,
            date__lt=next_month_start
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        if category_amount > 0:
            percentage = (category_amount / total_expenses_current * 100) if total_expenses_current > 0 else 0
            category_spending.append({
                'name': category.name,
                'amount': float(category_amount),
                'percentage': float(percentage)
            })

    budgets_overview = []
    for budget in current_month_budgets:
        spent_amount = budget_spent_data.get(budget.id, 0)
        remaining_amount = budget.amount - spent_amount
        percentage_used = (spent_amount / budget.amount * 100) if budget.amount > 0 else 0
        
        budgets_overview.append({
            'id': budget.id,
            'category_name': budget.category.name,
            'budget_amount': float(budget.amount),
            'spent_amount': float(spent_amount),
            'remaining_amount': float(remaining_amount),
            'percentage_used': float(percentage_used)
        })
    

    upcoming_bills = []
    future_budgets = Budget.objects.filter(
        user=user,
        due_date__gte=today
    ).order_by('due_date')[:5]
    
    for budget in future_budgets:
        days_remaining = (budget.due_date - today).days
        is_overdue = days_remaining < 0
        
        upcoming_bills.append({
            'id': budget.id,
            'category_name': budget.category.name,
            'amount': float(budget.amount),
            'due_date': budget.due_date,
            'days_remaining': abs(days_remaining) if is_overdue else days_remaining,
            'is_overdue': is_overdue
        })
    

    recent_transactions = Transaction.objects.filter(
        user=user
    ).select_related('category').order_by('-date')[:10]
    

    total_transactions = transactions.count()
    active_categories = Category.objects.filter(
        transaction__user=user,
        transaction__date__gte=current_month_start
    ).distinct().count()
    

    dashboard_data = {
        'total_balance': float(total_balance),
        'total_income': float(total_income),
        'total_expenses': float(total_expenses),
        'savings_rate': float(savings_rate),
        'budget_health': float(budget_health),
        'total_budget_limit': float(total_budget_limit),
        'total_budget_spent': float(total_budget_spent),
        'monthly_data': monthly_data,
        'category_spending': category_spending,
        'budgets_overview': budgets_overview,
        'upcoming_bills': upcoming_bills,
        'recent_transactions': recent_transactions,
        'current_month_income': float(current_month_income),
        'current_month_expenses': float(current_month_expenses),
        'current_month_savings': float(current_month_savings),
        'account_currency': user.currency,
        'user_full_name': f'{user.first_name} {user.last_name}',
        'total_transactions': total_transactions,
        'active_categories': active_categories,
    }
    
    serializer = DashboardMetricsSerializer(dashboard_data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_quick_stats(request):

    user = request.user
    today = timezone.now().date()
    current_month_start = today.replace(day=1)
    next_month_start = (current_month_start + timedelta(days=32)).replace(day=1)
    

    transactions = Transaction.objects.filter(user=user, status='Success')
    
    current_month_transactions = transactions.filter(
        date__gte=current_month_start,
        date__lt=next_month_start
    )
    
    current_income = current_month_transactions.filter(
        category__type='income'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    current_expenses = current_month_transactions.filter(
        category__type='expense'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    budgets = Budget.objects.filter(
        user=user,
        due_date__gte=current_month_start,
        due_date__lt=next_month_start
    )
    
    total_budget = budgets.aggregate(total=Sum('amount'))['total'] or 0
    
    budget_spent = 0
    for budget in budgets:
        category_spent = current_month_transactions.filter(
            category=budget.category,
            category__type='expense'
        ).aggregate(total=Sum('amount'))['total'] or 0
        budget_spent += category_spent
    
    budget_health = ((total_budget - budget_spent) / total_budget * 100) if total_budget > 0 else 100
    
    return Response({
        'current_income': float(current_income),
        'current_expenses': float(current_expenses),
        'current_balance': float(current_income - current_expenses),
        'budget_health': float(budget_health),
        'total_budget': float(total_budget),
        'budget_spent': float(budget_spent),
        'currency': user.currency
    })