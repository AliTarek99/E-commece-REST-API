from django.db import models
from django.contrib.postgres.fields import ArrayField

class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    max_price = models.DecimalField(max_digits=6, decimal_places=2)
    min_price = models.DecimalField(max_digits=6, decimal_places=2)
    quantity = models.IntegerField()
    seller = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        indexes = [
            models.Index(fields=['seller_id', 'id'])
        ]
        
        
class ProductVariant(models.Model):
    id = models.AutoField(primary_key=True)
    parent = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    RED = 1
    BLUE = 2
    GREEN = 3
    YELLOW = 4
    BLACK = 5
    WHITE = 6
    ORANGE = 7
    PURPLE = 8

    COLOR_CHOICES = [
        (RED, 'Red'),
        (BLUE, 'Blue'),
        (GREEN, 'Green'),
        (YELLOW, 'Yellow'),
        (BLACK, 'Black'),
        (WHITE, 'White'),
        (ORANGE, 'Orange'),
        (PURPLE, 'Purple'),
    ]

    color = models.SmallIntegerField(choices=COLOR_CHOICES)
    
    class Meta:
        db_table = 'Product_Variant'
        constraints = [
            models.UniqueConstraint(fields=['parent', 'id'], name='unique_product_variant'),
            models.UniqueConstraint(fields=['color', 'id'], name='unique_color')
        ]
    
class ProductImages(models.Model):
    url = models.URLField()
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    in_use = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'Product_Images'
        indexes = [
            models.Index(fields=['product_id', 'in_use']),
            models.Index(fields=['product_variant', 'created_at']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['product_variant_id', 'in_use', 'url'], name='unique_product_variant_image')
        ]


class ProductVariantSizes(models.Model):
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
    price = models.FloatField()
    
    SMALL=0
    MEDIUM=1
    LARGE=2
    XLARGE=3
    XXLARGE=4
    XXXLARGE=5
    
    SIZE_CHOICES = [
        (SMALL, 'Small'),
        (MEDIUM, 'Medium'),
        (LARGE, 'Large'),
        (XLARGE, 'XLarge'),
        (XXLARGE, 'XXLarge'),
        (XXXLARGE, 'XXXLarge'),
    ]
    
    size = models.SmallIntegerField(choices=SIZE_CHOICES)
    
    class Meta:
        db_table = 'Product_Variant_Sizes'
        constraints = [
            models.UniqueConstraint(fields=['product_variant', 'size'], name='unique_product_variant_size')
        ]