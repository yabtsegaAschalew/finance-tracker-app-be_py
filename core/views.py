from rest_framework.decorators import api_view, permission_classes
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
import requests
from finance_tracker.settings import CHAPA_PRIVATE_KEY

token_generator = PasswordResetTokenGenerator()

@swagger_auto_schema(method='post', request_body=UserSerializer)
@api_view(["POST"])
def sign_up(request):

    serializer = UserSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data.get("username")
    email = serializer.validated_data.get("email")

    if User.objects.filter(username=username).exists():
        return Response({"message": "Username taken"}, status=status.HTTP_403_FORBIDDEN)
    if User.objects.filter(email=email).exists():
        return Response({"message": "Email already taken"}, status=status.HTTP_403_FORBIDDEN)


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
            return Response({"message": "Account activated successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": "Invalid activation link"}, status=status.HTTP_400_BAD_REQUEST)
    

@permission_classes([IsAuthenticated])
@api_view(["POST"])
def change_password(request):
    if request.method == "POST":
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])

        return Response(
            {"message": "Password changed successfully"},
            status=status.HTTP_200_OK
        )
    
    
@permission_classes([IsAuthenticated])
@swagger_auto_schema(method='post', request_body=BudgetSerializer)
@api_view(["POST", "GET"])
def create_budget(request):
    if request.method == "POST":
        serializer = BudgetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # current_month = timezone.now().month
        #duplicate_values = Budget.objects.filter(user=request.user, month__month=timezone.now().month, transaction="null")

        # #filter by category
        
        # if duplicate_values:
        #      return Response({"message": "Values already exist update are allowed"})

        serializer.save(user=request.user)
        return Response(serializer.data)
    elif request.method == "GET":
        query = Budget.objects.filter(user=request.user)
        print(query)
        serializer = BudgetSerializer(query, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@permission_classes([IsAuthenticated])
@swagger_auto_schema(method='post', request_body=TransactionSerializer)
@api_view(["POST"])
def create_transaction(request):
    if request.method == "POST":
        serializer = TransactionSerializer(data = request.data)
        
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
def view_categories(request):
    if request.method == "GET":
        values = Category.objects.all().values()
        return Response(values, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

@permission_classes([IsAuthenticated])    
@api_view(["POST"])
def manage_budget(request):
    """
    get current user
    add a column concerning with priority
    find a way to set the payment date of certain fields so that payment could be set however the user likes,
    when the time comes to pay send a reminder email to the user for them to pay the required amount with the correct information
    set up a payment method so that they can pay
    bonus: set up a way for the payment to be done automatically so that 
    
    """
    if request.method == "POST":
        get_income = Budget.objects.filter(user=request.user).select_related("user", "category", "transaction").values("user__first_name", "transaction__id", "amount", "category__name", "category__type", "category__priority", "due_date", "user__email")

        today = datetime.now()

        for val in get_income:

            # modify this code to run intervally

            if today.month == val["due_date"].month and today.day == val["due_date"].day - 1:
                send_mail(
                    subject="Reminder to pay your bills",
                    from_email="yaba8084@gmail.com",
                    message=f"Your due date is on {val["due_date"].day}/{val["due_date"].month}/{val["due_date"].year}",
                    recipient_list=[request.user.email],
                    fail_silently=False,
                )     

            if (val["category__priority"] == "High" or val["category__priority"] == "high") and (val["category__type"] == "Expense" or val["category__type"]=="expense"):

                send_mail(
                    subject=f"Payment for {val["category__name"]}",
                    from_email="yaba8084@gmail.com",
                    message=(
                        f"Your {val["category__name"]} payment due date is on {val["due_date"].day}/{val["due_date"].month}/{val["due_date"].year} \n please pay the payment to avoid additional fees. \n You can pay through our website {request.scheme}://{request.get_host()}/api/login"
                        ),
                    recipient_list=[request.user.email],
                    fail_silently=False,
                )   

        return Response({"message": f"{get_income.all()}"})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chapa_payment(request):
    if request.method == "POST":
        api_url = "https://api.chapa.co/v1/transaction/initialize"
        private_key = CHAPA_PRIVATE_KEY

        amount = request.data.get("amount", 500)
        email = request.data.get("email", "test@example.com")
        first_name = request.data.get("first_name", "Test")
        last_name = request.data.get("last_name", "User")

        tx_ref = f"negade-tx-{uuid.uuid4().hex[:12]}"

        payload = {
            "amount": str(amount),
            "currency": "ETB",
            "email": "yabtsegaaschalew1@gmail.com",
            "first_name": first_name,
            "last_name": last_name,
            "tx_ref": tx_ref,
            "callback_url": "http://127.0.0.1:8000/api/chapa/callback/",
            "return_url": "http://127.0.0.1:8000/api/chapa/success/",
            "customization": {
                "title": "Let us do this",
                "description": "Paying with Confidence with Chapa",
            },
        }

        headers = {
            "Authorization": f"Bearer {private_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(api_url, json=payload, headers=headers)
            print("RAW:", response.text)

            if not response.text.strip():
                return Response(
                    {"error": "Empty response from Chapa"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            data = response.json()

            if response.status_code == 200 and data.get("status") == "success":
                checkout_url = data["data"]["checkout_url"]
                return Response(
                    {"checkout_url": checkout_url, "tx_ref": tx_ref, "amount": amount},
                    status=status.HTTP_200_OK,
                )

            return Response(
                {"error": data},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def chapa_success(request):

    return Response({"message": "Payment completed successfully!"})


@api_view(["GET"])
def chapa_callback(request):

    return Response({"message": "Callback received successfully!"})

