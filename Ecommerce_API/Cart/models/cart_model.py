from django.db import models
from products.models import ProductVariantSizes



class Cart(models.Model):
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    product_variant = models.ForeignKey('products.ProductVariant', on_delete=models.CASCADE)
    quantity = models.IntegerField()
    size = models.SmallIntegerField(choices=ProductVariantSizes.SIZE_CHOICES)

    class Meta:
        unique_together = ['user', 'product_variant', 'size']
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'


    def __str__(self):
        return f'{self.user} - {self.product}'