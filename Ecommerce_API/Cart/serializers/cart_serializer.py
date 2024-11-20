from rest_framework import serializers
from products.models import ProductVariant
from ..models import Cart
from shared.services import FileManagment

class CartSerializer(serializers.ModelSerializer):
    user_id=serializers.IntegerField()
    
    class Meta:
        model = Cart
        fields = ['user_id', 'quantity']


    def validate(self, attrs):
        if self.initial_data['user_id'] != self.context.get('user').id:
            raise serializers.ValidationError('UnAuthorized access')
        product = self.context.get('product_variant')
        if product.quantity < attrs['quantity']:
            attrs['quantity'] = product.quantity
        return attrs
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('Quantity must be greater than 0')
        return value

    
    def create(self, validated_data):
        validated_data['user'] = self.context.get('user')
        validated_data['product_variant'] = self.context.get('product_variant')
        return Cart.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.quantity = validated_data.get('quantity', instance.quantity)
        instance.save()
        return instance
    
class VariantItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'color_id', 'price', 'size_id']
    
class OutputCartSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    product_variant = VariantItemSerializer()
    product_id = serializers.IntegerField(source='product_variant.parent_id', required=False)
    product_name = serializers.CharField(source='product_variant.parent.name', required=False)
    
    class Meta:
        model = Cart
        fields = ['product_variant', 'quantity', 'images', 'product_id', 'product_name']
        
    def get_images(self, obj):
        images = obj.get('images', [])
        return [
            {
                'color_id': img.get('color_id'),
                'image': FileManagment.file_to_base64(img.get('url')),
                'default': img.get('default', False)
            }
            for img in images
        ]