from ..models import Product, ProductVariant, ProductImages, Colors, Sizes
from rest_framework import serializers
from users.models import CustomUser as User
import json
from django.db import transaction
from shared.services import FileManagment
from django.db import connection

class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField(required=False)
    
    class Meta:
        model = ProductImages
        fields = ['url', 'color', 'image', 'default']
        
    def get_image(self, obj):
        try:
            return FileManagment.file_to_base64(obj.url)
        except Exception as e:
            return None
    
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep.pop('url', None)
        return rep

    
class ProductImageInputSerializer(serializers.ModelSerializer):
    image = serializers.CharField(required=True)
    class Meta:
        model = ProductImages
        fields = ['image', 'color', 'default']
        
    def to_representation(self, instance):
        return instance.url
    
    
class ProductVariantSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    size = serializers.PrimaryKeyRelatedField(required=False, queryset=Sizes.objects.all())
    color = serializers.PrimaryKeyRelatedField(required=False, queryset=Colors.objects.all())
    
    class Meta:
        model = ProductVariant
        fields = ['id', 'color', 'size', 'quantity', 'price']
    
class InputProductSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=255)
    product_variants = ProductVariantSerializer(many=True, source='productvariant_set')
    max_price = serializers.FloatField(required=False, default=0.0)
    min_price = serializers.FloatField(required=False, default=0.0)
    quantity = serializers.IntegerField(required=False, default=0)
    images = ProductImageInputSerializer(required=False, many=True, source='productimages_set')
    
    # def to_internal_value(self, data):
    #     data['product_variants'] = self.__validate_product_variants(data['product_variants'])
    #     return super(InputProductSerializer, self).to_internal_value(data)
    
    # def __populate_colors_and_sizes(self, product_variants):
    #     colors = []
    #     sizes = []
    #     for variant in product_variants:
    #         colors.append(variant['color'])
    #         sizes.append(variant['size'])
        
    #     with connection.cursor() as cursor:
    #         cursor.execute("""
    #             SELECT json_object_agg(id, json_build_object('id', id, 'name', name))
    #             FROM "Colors";
    #         """)
    #         colors = cursor.fetchone()[0]
    #     with connection.cursor() as cursor:
    #         cursor.execute("""
    #             SELECT json_object_agg(id, json_build_object('id', id, 'name', name))
    #             FROM "Sizes";
    #         """)
    #         sizes = cursor.fetchone()[0]
    #         for i, variant in enumerate(product_variants):
    #             product_variants[i] = {**variant}
    #             product_variants[i]['color'] = colors.get(f"{variant.get('color').get('id')}")
    #             product_variants[i]['size'] = sizes.get(f"{variant.get('size').get('id')}")
    #         return product_variants
        
        
    def __validate_not_negative(self, value, field_name):
        if value < 0:
            raise serializers.ValidationError(f"{field_name} cannot be negative")
        return value

    def validate(self, attrs):
        if 'price' in attrs:
            attrs['price'] = self.__validate_not_negative(attrs['price'], 'price')
        if 'quantity' in attrs:    
            attrs['quantity'] = self.__validate_not_negative(attrs['quantity'], 'quantity')
        cnt = 0
        for i in attrs['productimages_set']:
            if i['default']:
                cnt += 1
        if cnt > 1:
            raise serializers.ValidationError('Only one default image is allowed')
        return attrs
    
    def validate_product_variants(self, product_variants):
        variants = set()
        sizes = set()
        colors = set()
        for variant in product_variants:
            variants.add((variant['color'].id, variant['size'].id))
            sizes.add(variant['size'].id)
            colors.add(variant['color'].id)
            variant['price'] = self.__validate_not_negative(variant['price'], 'price')
            self.initial_data['max_price'] = max(self.initial_data.get('max_price', 0), variant['price'])
            self.initial_data['min_price'] = min(self.initial_data.get('min_price', 10000000), variant['price'])
            self.initial_data['quantity'] = self.initial_data.get('quantity', 0) + variant['quantity']
        if len(variants) != len(product_variants):
            raise serializers.ValidationError('Product variant must have unique sizes')
        existing_sizes = set(Sizes.objects.filter(id__in=sizes).values_list('id', flat=True))
        invalid_sizes = sizes - existing_sizes
        existing_colors = set(Colors.objects.filter(id__in=colors).values_list('id', flat=True))
        invalid_colors = colors - existing_colors
        if len(invalid_colors):
            raise serializers.ValidationError({'msg': 'invalid colors', 'colors': list(invalid_colors)})
        if len(invalid_sizes):
            raise serializers.ValidationError({'msg': 'invalid sizes', 'sizes': list(invalid_sizes)})
        # product_variants = self.__populate_colors_and_sizes(product_variants)
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
            
            for variant in validated_data.get('productvariant_set', []):
                variants.append(ProductVariant(color=variant['color'], size=variant['size'], parent=product, quantity=variant['quantity'], price=variant['price']))
            images = FileManagment.save_images(self.context.get('request'), validated_data.get('productimages_set'))
            image_objects = []
            for image in images:
                image_objects.append(ProductImages(url=image['url'], product=product, color=image['color']))
            ProductVariant.objects.bulk_create(variants, batch_size=500)
            ProductImages.objects.bulk_create(image_objects, batch_size=500)
            return product

            
        
class BaseProductSerializer(serializers.ModelSerializer):
    product_images = serializers.SerializerMethodField()
    seller_name = serializers.CharField(source='seller.name', required=False)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'max_price', 'min_price', 'seller', 'product_images', 'seller_name']
        
    def get_product_images(self, obj):
        return ProductImages.objects.filter(product_id=obj.id, in_use=True).values_list('url', flat=True)


class OutputProductSerializer(InputProductSerializer):
    id = serializers.IntegerField()
    seller_id = serializers.IntegerField(source='seller.id')
    seller_name = serializers.CharField(required=False, source='seller.name')
    product_variants = ProductVariantSerializer(required=False, many=True, source='filtered_variants')
    images = ProductImageSerializer(many=True, source='filtered_images')