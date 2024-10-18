from ..models import Product, ProductVariant, ProductImages, Colors, Sizes
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
        colors = set()
        sizes = set()
        for variant in product_variants:
            if not all(key in variant for key in variant_fields):
                raise serializers.ValidationError('Product variant must have color, images and sizes')
            colors.add(variant['color'])
            
            if 'sizes' in variant:
                variant_sizes = set()
                for size in variant['sizes']:
                    variant_sizes.add(size['size'])
                    sizes.add(size['size'])
                    if not all(key in size for key in sizes_fields):
                        raise serializers.ValidationError('Product variant size must have price, quantity and size')
                    size['price'] = self.__validate_not_negative(size['price'], 'price')
                    self.initial_data['max_price'] = max(self.initial_data.get('max_price', 0), size['price'])
                    self.initial_data['min_price'] = min(self.initial_data.get('min_price', 10000000), size['price'])
                    self.initial_data['quantity'] = self.initial_data.get('quantity', 0) + size['quantity']
                if len(variant_sizes) != len(variant['sizes']):
                    raise serializers.ValidationError('Product variant must have unique sizes')
            else:
                raise serializers.ValidationError('Product variant must have sizes')
        existing_sizes = set(Sizes.objects.filter(id__in=sizes).values_list('id', flat=True))
        invalid_sizes = sizes - existing_sizes
        existing_colors = set(Colors.objects.filter(id__in=colors).values_list('id', flat=True))
        invalid_colors = colors - existing_colors
        if len(invalid_colors):
            raise serializers.ValidationError({'msg': 'invalid colors', 'colors': list(invalid_colors)})
        if len(invalid_sizes):
            raise serializers.ValidationError({'msg': 'invalid sizes', 'sizes': list(invalid_sizes)})
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
            variants = []
            images = []
            for variant in validated_data['product_variants']:
                urls = FileManagment.save_images(self.context.get('request'), variant['images'])
                for url in urls:
                    images.append(ProductImages(url=url, product_id=product.id, color_id=variant['color']))
                for size in variant['sizes']:
                    variants.append(ProductVariant(color_id=variant['color'], size_id=size['size'], parent=product, quantity=size['quantity'], price=size['price']))
            ProductVariant.objects.bulk_create(variants, batch_size=500)
            ProductImages.objects.bulk_create(images, batch_size=500)
            return product

            
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImages
        fields = ['url']
        
    def to_representation(self, instance):
        return instance.url
        

class ProductVariantSerializer(serializers.ModelSerializer):
    size = serializers.PrimaryKeyRelatedField(required=False, queryset=Sizes.objects.all())
    images = ProductImageSerializer(required=False, many=True, source='productimages_set')
    color = serializers.PrimaryKeyRelatedField(required=False, queryset=Colors.objects.all())
    
    class Meta:
        model = ProductVariant
        fields = ['id', 'color', 'size', 'images', 'quantity', 'price']
        
class OutputProductSerializer(serializers.ModelSerializer):
    product_images = serializers.SerializerMethodField()
    seller_name = serializers.CharField(source='seller.name', required=False)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'max_price', 'min_price', 'seller', 'product_images', 'seller_name']
        
    def get_product_images(self, obj):
        return ProductImages.objects.filter(product_id=obj.id, in_use=True).values_list('url', flat=True)


class OutputSingleProductSerializer(InputProductSerializer):
    id = serializers.IntegerField()
    seller = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    seller_name = serializers.CharField(source='seller.name', required=False)
    product_variants = ProductVariantSerializer(required=False, many=True, source='productvariant_set')