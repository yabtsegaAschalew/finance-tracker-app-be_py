from rest_framework import serializers
from core.models import User, Budget, Transaction
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "currency", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
class BudgetSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)  
    month = serializers.DateField(format="%Y-%m-%d", read_only=True) 
    class Meta:
        model = Budget
        fields = ["id", "user", "category", "amount", "month", "due_date", "transaction"]
        read_only_fields = ["id", "user", "month"]

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField(required=False)
    password = serializers.CharField()


class TransactionSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    date = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            "id", "user", "category", "amount", "description",
            "tx_ref", "status", "date", "created_at"
        ]
        read_only_fields = ["id", "user", "date", "created_at"]

    def get_date(self, obj):
        return obj.date if isinstance(obj.date, str) else obj.date.isoformat()

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        current_password = attrs.get('current_password')
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')


        if not user.check_password(current_password):
            raise serializers.ValidationError({"current_password": "Current password is incorrect."})

        if current_password == new_password:
            raise serializers.ValidationError({"new_password": "New password cannot be the same as current password."})

        if new_password != confirm_password:
            raise serializers.ValidationError({"new_password": "New password and confirm password do not match."})

        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": e.messages})

        return attrs
