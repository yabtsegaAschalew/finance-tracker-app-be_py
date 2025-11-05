from rest_framework import serializers
from core.models import User, Budget, Transaction
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active", "currency", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ["user_id", "category", "amount", "month", "transaction"]
        read_only_fields = ['user_id']

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField(required=False)
    password = serializers.CharField()

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["user", "category", "date", "amount", "description"]

class ChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')

        if new_password != confirm_password:
            raise serializers.ValidationError("Passwords do not match.")

        
        try:
            
            req = self.context.get('request')
            user = getattr(req, 'user', None)
            validate_password(new_password, user)
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': e.messages})

        return attrs
