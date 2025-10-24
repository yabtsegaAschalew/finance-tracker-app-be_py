from rest_framework.decorators import api_view
from rest_framework import status
from core.serializers import UserSerializer
from core.models import User
from rest_framework.response import Response
from django.core.mail import send_mail
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_str, force_bytes


token_generator = PasswordResetTokenGenerator()

@api_view(["POST", "GET"])
def sign_up(request):
    if request.method == "POST":
        username = request.data.get("username")
        email = request.data.get("email")

        if User.objects.filter(username=username).exists():
            return Response({"message": "Username taken"}, status=status.HTTP_403_FORBIDDEN)
        if User.objects.filter(email=email).exists():
            return Response({"message": "Email already taken"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = UserSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    elif request.method == "GET":
        return Response(User.objects.all().values())
    

@api_view(["POST"])
def activate_account(request):
    email = request.data.get("email")
    if User.objects.filter(email=email).exists():
        user = User.objects.get(email=email)
        if user.is_active:
            return Response({"message": "Account already activated"}, status=status.HTTP_400_BAD_REQUEST)

        token = token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        activation_link = f"{request.scheme}://{request.get_host()}/api/activate/{uid}/{token}"

        try:
            send_mail(
                subject= "Activate your account",
                from_email="yaba8084@gmail.com",
                message=f"Click the link to activate your account: {activation_link}",
                recipient_list=[email],
                fail_silently=False
            )
            return Response({"message": "Activation email sent"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": "An error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({"message": "Email not in use"})
    
@api_view(["GET"])
def activate_account_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        print(user)

        if token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response({"message": "Account activated successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": "Invalid activation link"}, status=status.HTTP_400_BAD_REQUEST)

      

