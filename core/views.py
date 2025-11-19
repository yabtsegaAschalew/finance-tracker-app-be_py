from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework import status
from core.serializers import UserSerializer, BudgetSerializer, LoginSerializer, TransactionSerializer, ChangePasswordSerializer
from core.models import User, Category, Budget, Transaction
from rest_framework.response import Response
from django.core.mail import send_mail
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

token_generator = PasswordResetTokenGenerator()
tx_ref = f"negade-tx-{uuid.uuid4().hex[:25]}"

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
    print("inside login view")

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
            return Response({"message": "Account activated successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": "Invalid activation link"}, status=status.HTTP_400_BAD_REQUEST)
    
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

    if data.get("status") == "success":
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
        
        verify_tx_ref = verify_payment(tx_ref)
        if verify_tx_ref.get("status") == "Success":
            transaction_update = Transaction.objects.filter(tx_ref=tx_ref)
            transaction_update.status = "Success"
            transaction_update.save()


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
        print({
            "data": get_bank()
        })
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