from rest_framework import serializers
from ..models import Orders, OrdersItems
from orders.services import PaymobServices

    
class OrderItemsSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrdersItems
        fields = '__all__'
    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value
    
    
class OrdersSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    orders_items = OrderItemsSerializer(many=True)

    def validate_total_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Total price cannot be negative.")
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        order = Orders.objects.create(user=user, **validated_data)
        return order
    def to_representation(self, instance):
        return {
            'id': instance.id,
            'user': instance.user_id,
            'created_at': instance.created_at.isoformat() if instance.created_at else None,
            'total_price': str(instance.total_price),
            'orders_items': instance.orders_items.all(),

        }
        
class PaymobCallbackSerializer(serializers.Serializer):
    hmac = serializers.CharField(max_length=255)
    merchant_order_id = serializers.CharField(max_length=255)
    
    def validate_hmac(self, value):
        if not PaymobServices.verify_hmac(value, self.context['request']):
            raise serializers.ValidationError("Invalid HMAC.")
        return value
    
    def validate_merchant_order_id(self, value):
        try:
            order = Orders.objects.get(merchant_order_id=value)
            value = order
        except Orders.DoesNotExist:
            raise serializers.ValidationError("Order does not exist.")
        return value
    
    def upadte(self, instance, validated_data):
        validated_data.get('merchant_order_id').status = Orders.PAID
        validated_data.get('merchant_order_id').paymob_response = self.context['request'].data
        validated_data.get('merchant_order_id').save()
        return validated_data.get('merchant_order_id')
    

class CreateOrderSerializer(serializers.Serializer):
    email  = serializers.EmailField()
    phone_number = serializers.CharField(max_length=20)
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    street = serializers.CharField(max_length=255)
    building = serializers.CharField(max_length=255)
    floor  = serializers.IntegerField()
    apartment = serializers.IntegerField()
    country = serializers.CharField(max_length=255)
    state  = serializers.CharField(max_length=255, required=False)