from rest_framework import serializers
from ...Users.serializers import UserSerializer
from ...Products.serializers import ProductSerializer
from ...Products.models import Product
from ..models import Cart


class CartSerializer(serializers.Serializer):
    product = ProductSerializer(read_only=True)
    quantity = serializers.IntegerField()
    user = UserSerializer(read_only=True)

    def validate(self, attrs):
        if self.user.id != self.context.get('request').user.id:
            raise serializers.ValidationError('UnAuthorized access')
        product = Product.objects.filter(id=attrs['product'].id).only('quantity')
        if product.quantity < attrs['quantity']:
            raise serializers.ValidationError('Product quantity is not enough')
        return attrs
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('Quantity must be greater than 0')
        return value
    
    def create(self, validated_data):
        self.user = self.context.get('request').user
        return Cart.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.quantity = validated_data.get('quantity', instance.quantity)
        instance.save()
        return instance