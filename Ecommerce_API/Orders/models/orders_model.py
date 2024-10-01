from django.db import models
from products.models import ProductVariant, ProductVariantSizes


class Orders(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('users.CustomUser', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=7, decimal_places=2)
    address = models.CharField(max_length=255)
    paymob_response = models.JSONField(null=True)
    
    PENDING = 0
    PAID = 1

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PAID, 'Completed'),
    ]

    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=PENDING)


    def __str__(self):
        return f"{self.user.username} - {self.order_date}"
    
class OrdersItems(models.Model):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='orders_items')
    product_variant = models.ForeignKey('products.ProductVariant', on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    quantity = models.SmallIntegerField()
    seller = models.ForeignKey('users.CustomUser', on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    description = models.TextField()
    color = models.SmallIntegerField(choices=ProductVariant.COLOR_CHOICES)
    size = models.SmallIntegerField(choices=ProductVariantSizes.SIZE_CHOICES)


    class Meta:
        unique_together = ('order', 'product_variant')
        db_table = 'orders_items'

