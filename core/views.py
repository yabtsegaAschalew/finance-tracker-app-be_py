from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from core.serializers import UserSerializer, BudgetSerializer, LoginSerializer, TransactionSerializer, ChangePasswordSerializer
from core.models import User, Category, Budget
from rest_framework.response import Response
from django.core.mail import send_mail
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_str, force_bytes
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
import time

token_generator = PasswordResetTokenGenerator()

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
@api_view(["POST"])
def create_budget(request):
    if request.method == "POST":
        serializer = BudgetSerializer(data=request.data)
        print(request.user)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == "GET":
        return Response(Budget.objects.all().values)

@permission_classes([IsAuthenticated])
@api_view(["POST"])
def create_transaction(request):
    if request.method == "POST":
        serializer = TransactionSerializer(data = request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
def view_categories(request):
    if request.method == "GET":
        values = Category.objects.all().values()
        return Response(values, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)