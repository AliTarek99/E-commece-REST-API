from rest_framework import serializers
from products.models import ProductVariant
from ..models import CartItem, Cart
from shared.services import FileManagment

class CartItemSerializer(serializers.ModelSerializer):
    # user_id=serializers.IntegerField()
    
    class Meta:
        model = CartItem
        fields = ['user', 'quantity', 'discount_price']


    def validate(self, attrs):
        product = self.context.get('product_variant')
        if product.quantity < attrs['quantity']:
            attrs['quantity'] = product.quantity
        return attrs
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('Quantity must be greater than 0')
        return value

    
    def create(self, validated_data):
        validated_data['product_variant'] = self.context.get('product_variant')
        validated_data['discount_price'] = self.context.get('product_variant').price
        return CartItem.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.quantity = validated_data.get('quantity', instance.quantity)
        instance.save(update_fields=['quantity'])
        return instance
    
class VariantItemSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ProductVariant
        fields = ['id', 'color_id', 'size_id']
        
    
class OutputCartItemSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    product_variant = VariantItemSerializer()
    price = serializers.FloatField(source='product_variant.price')
    product_id = serializers.IntegerField(source='product_variant.parent_id', required=False) 
    product_name = serializers.CharField(source='product_variant.parent.name', required=False)
    
    
    class Meta:
        model = CartItem
        fields = ['product_variant', 'quantity', 'images', 'product_id', 'product_name', 'discount_price', 'price']
        
    def get_images(self, obj):
        images = obj.product_variant.parent.productimages_set.all()
        return [
            {
                'color_id': img.color_id,
                'image': FileManagment.file_to_base64(img.url)[0:10],
                'default': img.default
            }
            for img in images
        ]
        
        
class OutputCartSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    coupons = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['total_price', 'discount_price', 'items', 'coupons']
    
    def get_items(self, obj):
        return OutputCartItemSerializer(obj.cartitem.all(), many=True).data
    
    def get_coupons(self, obj):
        return [coupon.coupon.code for coupon in obj.cartcoupon.all()]