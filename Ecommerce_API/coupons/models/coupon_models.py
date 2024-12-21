from django.db import models
import constants


class Coupon(models.Model):
    code = models.CharField(max_length=8, unique=True)
    uses = models.BigIntegerField(default=0)
    seller = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['seller', 'code']),
            models.Index(fields=['code', 'is_active'])
        ]
        
    def __str__(self):
        return self.code
        

class CouponProduct(models.Model):
    id = None
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='couponproduct')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    
    class Meta:
        unique_together = (
            ('coupon', 'product')
        )
        
        
class CouponUse(models.Model):
    id = None
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='couponuse')
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    uses = models.SmallIntegerField(default=0)
    
    class Meta:
        unique_together = (
            ('coupon', 'user')
        )
        
class CouponRule(models.Model):
    coupon = models.OneToOneField(Coupon, on_delete=models.CASCADE)
    minimum_required_value = models.FloatField(null=True, blank=True)
    max_uses = models.IntegerField(null=True, blank=True)
    max_uses_per_user = models.IntegerField(null=True, blank=True)
    discount_value = models.FloatField()
    discount_limit = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    
    
    DISCOUNT_TYPE_CHOICES = [
        (constants.DISCOUNT_TYPE_PERCENTAGE, 'Percentage'),
        (constants.DISCOUNT_TYPE_FIXED, 'Fixed')
    ]
    
    
    
    COUPON_TYPE_CHOICES = [
        (constants.COUPON_TYPE_ORDER, 'Order'),
        (constants.COUPON_TYPE_PRODUCT, 'Product'),
        (constants.COUPON_TYPE_SELLER, 'Seller'),
        (constants.COUPON_TYPE_SHIPPING, 'Shipping')
    ]
    
    coupon_type = models.SmallIntegerField(choices=COUPON_TYPE_CHOICES)
    discount_type = models.SmallIntegerField(choices=DISCOUNT_TYPE_CHOICES)
    