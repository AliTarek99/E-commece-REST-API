from rest_framework import serializers
from users.models import CustomUser as User
from products.models import ProductVariantSizes
from ..models import Cart
from products.serializers import ProductVariantSerializer

class CartSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Cart
        fields = ['user', 'product_variant', 'quantity', 'size']


    def validate(self, attrs):
        if self.initial_data['user'] != self.context.get('user').id:
            raise serializers.ValidationError('UnAuthorized access')
        product = ProductVariantSizes.objects.filter(product_variant=attrs['product_variant'].id, size=attrs['size']).only('quantity').first()
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
    
class VariantItemSerializer(serializers.Serializer):
    seller_name = serializers.CharField(source='parent.seller.name')
    seller_id = serializers.IntegerField(source='parent.seller.id')
    id = serializers.IntegerField()
    name = serializers.CharField(source='parent.name')
    price = serializers.FloatField(source='productvariantsizes_set.first.price')
    color = serializers.CharField()
    
class OutputCartSerializer(serializers.ModelSerializer):
    images = serializers.ListField(child=serializers.URLField())
    product_variant = VariantItemSerializer()
    
    class Meta:
        model = Cart
        fields = ['product_variant', 'quantity', 'size', 'images']