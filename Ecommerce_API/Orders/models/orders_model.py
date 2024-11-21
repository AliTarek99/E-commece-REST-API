from django.db import models
from shared.services.models import TimeStamp
from products.models import Sizes, Colors


class Orders(TimeStamp):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=7, decimal_places=2)
    address = models.ForeignKey('users.Address', on_delete=models.PROTECT)
    paymob_response = models.JSONField(null=True)
    
    PENDING = 0
    PAID = 1
    SHIPPED = 2
    DELIVERED = 3
    RETURNED = 4
    CANCELLED = 5

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PAID, 'Preparing your order'),
        (SHIPPED, 'Shipped'),
        (DELIVERED, 'Delivered'),
        (RETURNED, 'Returned'),
        (CANCELLED, 'Cancelled'),
    ]

    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=PENDING)

    
class OrdersItems(models.Model):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='orders_items')
    product_variant = models.ForeignKey('products.ProductVariant', on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    quantity = models.SmallIntegerField()
    seller = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    color = models.ForeignKey(Colors, on_delete=models.PROTECT)
    size = models.ForeignKey(Sizes, on_delete=models.PROTECT)


    class Meta:
        unique_together = ('order', 'product_variant')
        db_table = 'orders_items'

