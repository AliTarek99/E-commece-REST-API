from rest_framework import serializers
from shared.services.util import FileManagment
from ..models import Orders, OrdersItems, ReturnRequest
from orders.services import PaymobServices
from users.serializers import AddressListSerializer
from users.models import Address
import constants
from orders.models import ReturnItem
from django.db import models
from products.models import ProductVariant



    
class OrderItemsSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = OrdersItems
        fields = ['product_variant_id', 'price', 'discount_price', 'seller', 'quantity', 'name', 'description', 'color', 'size', 'images']
        
    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value
    
    def get_images(self, obj):
        images = obj.product_variant.parent.productimages_set.filter(created_at__lt=obj.order.created_at).values('url', 'color_id', 'default')
        return [
            {
                'color_id': img.get('color_id'),
                'image': FileManagment.file_to_base64(img.get('url')),
                'default': img.get('default', False)
            }
            for img in images
        ]
   
   
class AddressListSerializer(serializers.ModelSerializer):
    country = serializers.CharField(source='city.country.name')
    class Meta:
        model = Address
        fields = ['id', 'city', 'street', 'country', 'building_no', 'apartment_no']

class OrdersListSerializer(serializers.ModelSerializer):
    address = AddressListSerializer()
    class Meta:
        model = Orders
        fields = ['id', 'created_at', 'total_price', 'address', 'total_price', 'discount_price', 'status']
    
class OrdersSerializer(OrdersListSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    orders_items = OrderItemsSerializer(many=True, required=False)
    class Meta:
        model = Orders
        fields = ['id', 'created_at', 'total_price', 'address', 'discount_price', 'status', 'user', 'orders_items', 'payment_link']

    def validate_total_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Total price cannot be negative.")
        return value
        
class PaymobCallbackSerializer(serializers.Serializer):
    hmac = serializers.CharField(max_length=255)
    store_order_id = serializers.CharField(max_length=255)
    order = None
    
    def validate_hmac(self, value):
        if not PaymobServices.verify_hmac(value, self.context['request']):
            raise serializers.ValidationError("Invalid HMAC.")
        return value
    
    def validate_store_order_id(self, value):
        self.order = Orders.objects.filter(id=value).first()
        if not self.order:
            raise serializers.ValidationError("Order does not exist.")
        return value
    
    def update(self, instance, validated_data):
        self.order.status = constants.ORDER_PAID
        self.order.paymob_response = self.context['request'].data
        self.order.save()
        return self.order
    

class CreateOrderSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=20)
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    address = AddressListSerializer(required=False)
    address_id = serializers.PrimaryKeyRelatedField(queryset=Address.objects.defer('created_at', 'updated_at') , required=False)
    use_default_address = serializers.BooleanField(required=False)
    
    def validate(self, attrs):
        if attrs.get('use_default_address'):
            attrs['address'] = Address.objects.filter(user=self.context['request'].user, default=True).first()
        elif attrs.get('address_id'):
            attrs['address'] = attrs['address_id']
        if not attrs.get('address'):
            raise serializers.ValidationError("Either address or address_id or use_default_address set to true is required.")
        return attrs
    
    def validate_address(self, value):
        if value.is_valid():
            value = Address.objects.create(**value, user=self.context.get('request').user)
            return value
        else:
            raise serializers.ValidationError(value.errors)
    
    def validate_address_id(self, value):
        if not value.user == self.context['request'].user:
            raise serializers.ValidationError("Address does not belong to user.")
        return value
    

class ReturnOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdersItems
        fields = ['product_variant', 'quantity']
        
    
    def validate_id(self, value):
        if not value:
            raise serializers.ValidationError("Order item id is required.")
        return value


class ReturnOrderRequestSerializer(serializers.ModelSerializer):
    items = ReturnOrderItemSerializer(many=True, required=True)
    
    class Meta:
        model = ReturnRequest
        fields = ['order', 'reason', 'items']
        
    def validate(self, attrs):
        order = attrs.get('order')
        items = attrs.get('items')
        
        if order.status != constants.ORDER_DELIVERED:
            raise serializers.ValidationError("Order must be delivered to request a return.")
        
        for item in items:
            product_variant = item['product_variant']
            quantity = item['quantity']
            
            # Get the total quantity of this product variant in the order
            order_item = OrdersItems.objects.filter(order=order, product_variant=product_variant).first()
            if not order_item:
                raise serializers.ValidationError(f"Product variant {product_variant.id} not found in the order.")
            
            # Get the total quantity of this product variant in existing return requests
            existing_return_quantity = ReturnItem.objects.filter(
                return_request__order=order,
                product_variant=product_variant
            ).aggregate(total_quantity=models.Sum('quantity'))['total_quantity'] or 0
            
            # Check if the sum of existing return requests and the new request exceeds the quantity in the order
            if existing_return_quantity + quantity > order_item.quantity:
                raise serializers.ValidationError(f"Total return quantity for product variant {product_variant.id} exceeds the quantity in the order.")
            item['price'] = order_item.price * quantity
        
        return attrs
