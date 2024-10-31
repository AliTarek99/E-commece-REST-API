from django.db import models
from shared.services.models import TimeStamp
from django.contrib.postgres.fields import ArrayField

class Product(TimeStamp):
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
        
        
class Colors(TimeStamp):
    id = models.SmallAutoField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'Colors'

class Sizes(TimeStamp):
    id = models.SmallAutoField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'Sizes'
        
class ProductVariant(TimeStamp):
    id = models.AutoField(primary_key=True)
    parent = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.ForeignKey(Colors, on_delete=models.PROTECT)
    size = models.ForeignKey(Sizes, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    price = models.FloatField()
    
    class Meta:
        db_table = 'Product_Variant'
        indexes = [
            models.Index(fields=['parent', 'id'], name='unique_product_variant'),
            models.Index(fields=['color', 'size', 'id'], name='unique_color_size'),
            models.Index(fields=['size', 'color', 'id'], name='unique_size_color')
        ]
    
class ProductImages(TimeStamp):
    url = models.URLField()
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    color = models.ForeignKey(Colors, on_delete=models.SET_NULL, null=True)
    default = models.BooleanField(default=False)
    in_use = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'Product_Images'
        indexes = [
            models.Index(fields=['product_id', 'in_use']),
            models.Index(fields=['product_id', 'color', 'created_at']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['product_id', 'url'], name='unique_product_variant_image')
        ]