from rest_framework import serializers
from core.models import User, Budget, Transaction
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active", "currency"]

class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ["user", "category", "amount"]

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField(required=False)
    password = serializers.CharField()

class TransactionSerializer(serializers.Serializer):
    class Meta:
        model = Transaction
        fields = ["user", "category", "date", "amount", "description"]

class ChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if new_password != confirm_password:
            raise serializers.ValidationError("Passwords do not match.")

        # Validate password strength using Django's built-in validators
        try:
            validate_password(new_password, self.context['request'].user)
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': e.messages})

        return data
