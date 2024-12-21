from rest_framework import serializers
from shared.services.util import FileManagment
from ..models import Orders, OrdersItems
from orders.services import PaymobServices
from users.serializers import AddressListSerializer
from users.models import Address


    
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
        fields = ['id', 'created_at', 'total_price', 'address', 'discount_price', 'status', 'user', 'orders_items']

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
        try:
            self.order = Orders.objects.get(id=value)
        except Orders.DoesNotExist:
            raise serializers.ValidationError("Order does not exist.")
        return value
    
    def update(self, instance, validated_data):
        self.order.status = Orders.PAID
        self.order.paymob_response = self.context['request'].data
        self.order.save()
        return self.order
    

class CreateOrderSerializer(serializers.Serializer):
    email  = serializers.EmailField()
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