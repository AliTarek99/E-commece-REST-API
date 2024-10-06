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
    quantity = serializers.IntegerField(required=False, default=0)
    

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
            if not all(key in variant for key in variant_fields):
                raise serializers.ValidationError('Product variant must have color, images and sizes')
            if 'sizes' in variant:
                sizes = set()
                for size in variant['sizes']:
                    sizes.add(size['size'])
                    if not all(key in size for key in sizes_fields):
                        raise serializers.ValidationError('Product variant size must have price, quantity and size')
                    size['price'] = self.__validate_not_negative(size['price'], 'price')
                    self.initial_data['max_price'] = max(self.initial_data.get('max_price', 0), size['price'])
                    self.initial_data['min_price'] = min(self.initial_data.get('min_price', 10000000), size['price'])
                    self.initial_data['quantity'] = self.initial_data.get('quantity', 0) + size['quantity']
                if len(sizes) != len(variant['sizes']):
                    raise serializers.ValidationError('Product variant must have unique sizes')
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
                product_variant = ProductVariant.objects.create(color=variant['color'], parent_id=product.id)
                urls = FileManagment.save_images(self.context.get('request'), variant['images'])
                for url in urls:
                    images.append(ProductImages(url=url, product_id=product.id, product_variant_id=product_variant.id))
                for size in variant['sizes']:
                    size['product_variant_id'] = product_variant.id
                    sizes.append(ProductVariantSizes(**size))
            ProductVariantSizes.objects.bulk_create(sizes, batch_size=500)
            ProductImages.objects.bulk_create(images, batch_size=500)
            return product

            
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImages
        fields = ['url']
        
    def to_representation(self, instance):
        return instance.url
        
        
class ProductVariantSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariantSizes
        fields = ['price', 'quantity', 'size']

class ProductVariantSerializer(serializers.ModelSerializer):
    sizes = ProductVariantSizeSerializer(required=False, many=True, source='productvariantsizes_set')
    images = ProductImageSerializer(required=False, many=True, source='productimages_set')
    class Meta:
        model = ProductVariant
        fields = ['id', 'color', 'sizes', 'images']
        
class OutputProductSerializer(serializers.ModelSerializer):
    product_images = ProductImageSerializer(required=False, many=True, source='productimages_set')
    seller_name = serializers.CharField(source='seller.name', required=False)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'max_price', 'min_price', 'seller', 'product_images', 'seller_name']

class OutputSingleProductSerializer(InputProductSerializer):
    id = serializers.IntegerField()
    seller = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    seller_name = serializers.CharField(source='seller.name', required=False)
    product_variants = ProductVariantSerializer(required=False, many=True, source='productvariant_set')
    product_variant_sizes = ProductVariantSizeSerializer(required=False, many=True, source='productvariantsizes_set')