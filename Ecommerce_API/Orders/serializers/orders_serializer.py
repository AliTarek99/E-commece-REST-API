from rest_framework import serializers
from ...Users.models import CustomUser as User
from ..models import Orders

class OrdersSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    order_date = serializers.DateTimeField(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    items = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    def validate_total_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Total price cannot be negative.")
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        order = Orders.objects.create(user=user, **validated_data)
        return order

class OrderItemsSerializer(serializers.Serializer):
    order = serializers.PrimaryKeyRelatedField(read_only=True)
    product = serializers.PrimaryKeyRelatedField(read_only=True)
    quantity = serializers.IntegerField()

    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value