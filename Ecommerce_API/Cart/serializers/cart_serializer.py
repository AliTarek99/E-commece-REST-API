from rest_framework import serializers
from users.models import CustomUser as User
from products.serializers import ProductSerializer
from products.models import Product
from ..models import Cart


class CartSerializer(serializers.Serializer):
    product = ProductSerializer()
    quantity = serializers.IntegerField()
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)


    def validate(self, attrs):
        if self.initial_data['user_id'] != self.context.get('request').user.id:
            raise serializers.ValidationError('UnAuthorized access')
        product = Product.objects.filter(id=attrs['product']['id']).only('quantity').first()
        if product.quantity < attrs['quantity']:
            raise serializers.ValidationError('Product quantity is not enough')
        return attrs
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('Quantity must be greater than 0')
        return value
    
    def create(self, validated_data):
        validated_data['user_id'] = self.context.get('request').user
        return Cart.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.quantity = validated_data.get('quantity', instance.quantity)
        instance.save()
        return instance