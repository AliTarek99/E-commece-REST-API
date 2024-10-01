from ..models import Product
from rest_framework import serializers
from users.models import CustomUser as User
import json

class InputProductSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    # description = serializers.CharField(max_length=500)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    quantity = serializers.IntegerField()
    # image = serializers.ImageField()
    # related_products = serializers.ListField(child=serializers.JSONField(), required=False)

    def __validate_not_negative(self, value, field_name):
        if value < 0:
            raise serializers.ValidationError(f"{field_name} cannot be negative")
        return value

    def validate(self, attrs):
        if 'price' in attrs:
            attrs['price'] = self.__validate_not_negative(attrs['price'], 'price')
        if 'quantity' in attrs:    
            attrs['quantity'] = self.__validate_not_negative(attrs['quantity'], 'quantity')
        return attrs
    
    # def validate_related_products(self, value):
    #     ids = []
    #     tmp = []
    #     for product in value:
    #         product = json.loads(product)
    #         tmp.append(product)
    #         if 'relation' not in product:
    #             raise serializers.ValidationError("relation field is required")
    #         if 'id' not in product:
    #             raise serializers.ValidationError("id field is required")
    #         if 'name' not in product:
    #             raise serializers.ValidationError("name field is required")
            
    #         product['relation'] = str.lower(product['relation'])
    #         ids.append(product['id'])
    #     value = tmp
    #     if len(ids) != len(set(ids)):
    #         raise serializers.ValidationError("Duplicate product ids are not allowed")
    #     if Product.objects.filter(id__in=ids).count() != len(ids):
    #         raise serializers.ValidationError("One or more product ids do not exist")
    #     return value
    
    def create(self, validated_data):
        validated_data['seller_id'] = self.context.get('request').user.id
        return Product.objects.create(**validated_data)
    
    def delete(self, instance):
        if self.context.get('request').user.id == instance.seller.id:
            instance.delete()
            return instance
        else:
            raise serializers.ValidationError('You are not allowed to delete this product')
        
    def update(self, instance, validated_data):
        if self.context.get('request').user.id == instance.seller.id:
            instance.name = validated_data.get('name', instance.name)
            instance.description = validated_data.get('description', instance.description)
            instance.price = validated_data.get('price', instance.price)
            instance.quantity = validated_data.get('quantity', instance.quantity)
            instance.image = validated_data.get('image', instance.image)
            instance.related_products = validated_data.get('related_products', instance.related_products)

            instance.save()
            return instance
        else:
            raise serializers.ValidationError('You are not allowed to update this product')
            


class OutputProductSerializer(InputProductSerializer):
    id = serializers.IntegerField()
    seller = serializers.PrimaryKeyRelatedField(queryset=User.objects.all().only('id', 'name'))
    # image = serializers.URLField()