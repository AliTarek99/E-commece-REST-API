from rest_framework import serializers
from products.models import ProductVariant
from ..models import Cart

class CartSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Cart
        fields = ['user', 'product_variant', 'quantity']


    def validate(self, attrs):
        if self.initial_data['user'] != self.context.get('user').id:
            raise serializers.ValidationError('UnAuthorized access')
        product = ProductVariant.objects.filter(id=attrs['product_variant'].id).only('quantity').first()
        if product.quantity < attrs['quantity']:
            raise serializers.ValidationError('Product quantity is not enough')
        return attrs
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('Quantity must be greater than 0')
        return value

    
    def create(self, validated_data):
        validated_data['user'] = self.context.get('user')
        return Cart.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.quantity = validated_data.get('quantity', instance.quantity)
        instance.save()
        return instance
    
class VariantItemSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source='parent.seller.name')
    seller_id = serializers.IntegerField(source='parent.seller.id')
    name = serializers.CharField(source='parent.name')
    
    class Meta:
        model = ProductVariant
        fields = ['id', 'color', 'price', 'seller_name', 'seller_id', 'name']
    
class OutputCartSerializer(serializers.ModelSerializer):
    images = serializers.ListField(child=serializers.URLField())
    product_variant = VariantItemSerializer()
    
    class Meta:
        model = Cart
        fields = ['product_variant', 'quantity', 'images']