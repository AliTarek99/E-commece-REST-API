from django.db import models
from shared.services.models import TimeStamp
from products.models import Sizes, Colors
import constants


class Orders(TimeStamp):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=7, decimal_places=2)
    discount_price = models.DecimalField(max_digits=7, decimal_places=2)
    address = models.ForeignKey('users.Address', on_delete=models.PROTECT)
    paymob_response = models.JSONField(null=True)
    payment_link = models.CharField(null=True)
    shipping_price = models.FloatField()

    STATUS_CHOICES = [
        (constants.ORDER_PENDING, 'Pending'),
        (constants.ORDER_PAID, 'Preparing your order'),
        (constants.ORDER_SHIPPED, 'Shipped'),
        (constants.ORDER_DELIVERED, 'Delivered'),
        (constants.ORDER_RETURNED, 'Returned'),
        (constants.ORDER_CANCELLED, 'Cancelled'),
        (constants.ORDER_FAILED, 'Payment Failed')
    ]

    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=constants.ORDER_PENDING)

    
class OrdersItems(models.Model):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='orders_items')
    product_variant = models.ForeignKey('products.ProductVariant', on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    discount_price = models.DecimalField(max_digits=7, decimal_places=2)
    quantity = models.SmallIntegerField()
    seller = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    color = models.ForeignKey(Colors, on_delete=models.PROTECT)
    size = models.ForeignKey(Sizes, on_delete=models.PROTECT)
    image_url = models.URLField()

    class Meta:
        unique_together = ('order', 'product_variant')
        db_table = 'orders_items'

class OrderCoupons(models.Model):
    id = None
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='order_coupons')
    coupon = models.ForeignKey('coupons.Coupon', on_delete=models.PROTECT, related_name='coupon_orders')

    class Meta:
        unique_together = ('order', 'coupon')
        
        
class ReturnRequest(models.Model):
    STATUS_CHOICES = [
        (constants.RETURN_WAITING_FOR_SHIPPING, 'Waiting for shipping back'),
        (constants.RETURN_SHIPPING_BACK, 'Shipping back'),
        (constants.RETURN_CHECKING_PACKAGE, 'Checking package'),
        (constants.RETURN_APPROVED, 'Approved'),
        (constants.RETURN_REJECTED, 'Rejected')
    ]
    
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=constants.RETURN_WAITING_FOR_SHIPPING)
    
    class Meta:
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['user'])
        ]
        
class ReturnItem(models.Model):
    return_request = models.ForeignKey(ReturnRequest, on_delete=models.CASCADE, related_name='return_items')
    product_variant = models.ForeignKey('products.ProductVariant', on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
    
    class Meta:
        unique_together = ('return_request', 'product_variant')
        indexes = [
            models.Index(fields=['return_request'])
        ]
        