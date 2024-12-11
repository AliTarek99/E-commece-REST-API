from rest_framework import serializers
from products.models import ProductVariant
from ..models import CartItem, Cart
from shared.services import FileManagment

class CartItemSerializer(serializers.ModelSerializer):
    user_id=serializers.IntegerField()
    
    class Meta:
        model = CartItem
        fields = ['user_id', 'quantity', 'discount_price']


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
        validated_data['discount_price'] = self.context.get('product_variant').price
        return CartItem.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.quantity = validated_data.get('quantity', instance.quantity)
        instance.save()
        return instance
    
class VariantItemSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ProductVariant
        fields = ['id', 'color_id', 'size_id']
        
    
class OutputCartItemSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    product_variant = VariantItemSerializer()
    price = serializers.DecimalField(max_digits=10, decimal_places=2, source='product_variant.price')
    product_id = serializers.IntegerField(source='product_variant.parent_id', required=False) 
    product_name = serializers.CharField(source='product_variant.parent.name', required=False)
    
    
    class Meta:
        model = CartItem
        fields = ['product_variant', 'quantity', 'images', 'product_id', 'product_name', 'discount_price', 'price']
        
    def get_images(self, obj):
        images = obj.product_variant.parent.productimages_set.all()
        print(images)
        return [
            {
                'color_id': img.color_id,
                'image': FileManagment.file_to_base64(img.url),
                'default': img.default
            }
            for img in images
        ]
        
        
class OutputCartSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['total_price', 'discount_price', 'items']
    
    def get_items(self, obj):
        return OutputCartItemSerializer(obj.user.cartitem_set.all(), many=True).data