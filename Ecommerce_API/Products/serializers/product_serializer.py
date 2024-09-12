from ..models import Product
from rest_framework import serializers
from ...Users.serializers import UserSerializer

class ProductSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    quantity = serializers.IntegerField()
    created_at = serializers.DateTimeField(read_only=True)
    seller = UserSerializer(read_only=True)

    def __validate_not_negative(self, value, field_name):
        if value < 0:
            raise serializers.ValidationError(f"{field_name} cannot be negative")
        return value

    def validate(self, attrs):
        attrs['price'] = self.__validate_not_negative(attrs['price'], 'price')
        attrs['quantity'] = self.__validate_not_negative(attrs['quantity'], 'quantity')
        return attrs

    def create(self, validated_data):
        self.seller = self.context.get('request').user
        return Product.objects.create(**validated_data)
    
    def delete(self, instance):
        if self.context.get('request').user.id == instance.seller.id:
            instance.delete()
            return instance
        else:
            raise serializers.ValidationError('You are not allowed to delete this product')