from ..models import CustomUser as User
from rest_framework import serializers
from orders.services import PaymobServices
from decouple import config

class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    email = serializers.EmailField()
    name = serializers.CharField()
    phone_number = serializers.CharField()
    password = serializers.CharField(max_length=50, write_only=True)
    merchant_id = serializers.CharField(required=False)

    def validate(self, attrs):
        if attrs.get('merchant_id'):
            self.__validate_merchant(attrs)
        return attrs


    def __validate_merchant(self, attrs):
        merchant_data = PaymobServices.get_merchant_data(config("PAYMOB_SECRET_KEY"), attrs['merchant_id'])

        if merchant_data is None:
            raise serializers.ValidationError("Invalid merchant ID")
        
        if merchant_data['email'] != attrs['email']:
            raise serializers.ValidationError("Merchant email should be the same as in paymob account")
        
        if merchant_data['registered_name'] != attrs['name'] and merchant_data['business_name'] != attrs['name']:
            raise serializers.ValidationError("Name should match the registered name or the business name in paymob account")
        if merchant_data['phone_number'] != attrs['phone']:
            raise serializers.ValidationError("phone number should be the same as in paymob account")
        if merchant_data['status'] in ['inactive', 'suspended']:
            raise serializers.ValidationError("Merchant account status must be active")

        return attrs

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
    
    def update(self, user, validated_data):
        user.name = validated_data.get('name', user.name)
        user.set_password(validated_data.get('password', user.password))

        user.save()
        return user
    