from ..models import CustomUser as User, Address
from rest_framework import serializers
from orders.services import PaymobServices
from decouple import config

class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    email = serializers.EmailField()
    name = serializers.CharField()
    phone_number = serializers.CharField()
    password = serializers.CharField(max_length=50, write_only=True)

    def validate(self, attrs):
        if attrs.get('merchant_id'):
            self.__validate_merchant(attrs)
        return attrs

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Phone number already exists")
        return value
    
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
    
    def update(self, user, validated_data):
        user.name = validated_data.get('name', user.name)
        user.set_password(validated_data.get('password', user.password))

        user.save()
        return user
    
    
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'city', 'street', 'country', 'apartment_no', 'building_no', 'created_at', 'updated_at', 'default']
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def create(self, validated_data):
        if validated_data.get('default'):
            Address.objects.filter(user=self.context['request'].user, default=True).update(default=False)
        return super().create(validated_data)