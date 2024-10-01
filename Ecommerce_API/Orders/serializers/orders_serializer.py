from rest_framework import serializers
from users.models import CustomUser as User
from ..models import Orders
from products.serializers import OutputProductSerializer
import json

class OrdersSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    orders_items = serializers.ListField(child=serializers.JSONField(), required=False)


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
            'total_price': str(instance.total_price)
        }
    
    
class OrderItemsSerializer(serializers.Serializer):
    order = serializers.PrimaryKeyRelatedField(read_only=True)
    product = serializers.PrimaryKeyRelatedField(read_only=True)
    quantity = serializers.IntegerField()

    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value