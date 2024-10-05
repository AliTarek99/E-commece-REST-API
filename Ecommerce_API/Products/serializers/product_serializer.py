from ..models import Product, ProductVariant, ProductImages, ProductVariantSizes
from rest_framework import serializers
from users.models import CustomUser as User
import json
from django.db import transaction
from shared.services import FileManagment


class InputProductSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=255)
    product_variants = serializers.ListField(child=serializers.JSONField())
    max_price = serializers.FloatField(required=False, default=0.0)
    min_price = serializers.FloatField(required=False, default=0.0)
    

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
    
    def validate_product_variants(self, product_variants):
        variant_fields = ['color', 'images', 'sizes']
        sizes_fields = ['price', 'quantity', 'size']
        for variant in product_variants:
            if variant_fields not in variant:
                raise serializers.ValidationError('Product variant must have color, images and sizes')
            if 'sizes' in variant:
                for size in variant['sizes']:
                    if sizes_fields not in size:
                        raise serializers.ValidationError('Product variant size must have price, quantity and size')
                    size['price'] = self.__validate_not_negative(size['price'], 'price')
                    self.validated_data['max_price'] = max(self.validated_data['max_price'], size['price'])
                    self.validated_data['min_price'] = min(self.validated_data['min_price'], size['price'])
                    self.validated_data['quantity'] += size['quantity']
            else:
                raise serializers.ValidationError('Product variant must have sizes')
        return product_variants

    
    def create(self, validated_data):
        validated_data['seller_id'] = self.context.get('request').user.id
        with transaction.atomic():
            product = Product.objects.create(
                seller_id=validated_data['seller_id'], 
                name=validated_data['name'], 
                description=validated_data['description'], 
                max_price=validated_data['max_price'], 
                min_price=validated_data['min_price'],
                quantity=validated_data['quantity'],
                )
            sizes = []
            images = []
            for variant in validated_data['product_variants']:
                variant['parent_id'] = product.id
                product_variant = ProductVariant.objects.create(**variant)
                urls = FileManagment.save_images(self.context.get('request'), variant['images'], 'images')
                for url in urls:
                    images.append(ProductImages(url=url, product_id=product.id, product_variant_id=product_variant.id))
                for size in variant['sizes']:
                    size['product_variant_id'] = product_variant.id
                    sizes.append(ProductVariantSizes(**size))
            ProductVariantSizes.objects.bulk_create(sizes, batch_size=500)
            ProductImages.objects.bulk_create(images, batch_size=500)
            return product

            


class OutputProductSerializer(InputProductSerializer):
    id = serializers.IntegerField()
    seller = serializers.PrimaryKeyRelatedField(queryset=User.objects.all().only('id', 'name'))
    product_variants = serializers.ListField(child=serializers.JSONField())
    product_variant_sizes = serializers.ListField(child=serializers.JSONField())
    image = serializers.ListField(child=serializers.URLField())