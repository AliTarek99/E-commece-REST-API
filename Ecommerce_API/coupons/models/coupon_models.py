from django.db import models


class Coupons(models.Model):
    code = models.CharField(max_length=8, unique=True)
    uses = models.BigIntegerField(default=0)
    seller = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = (
            ('seller_id', 'id'),
            ('id', 'is_active')
        )
        
    def __str__(self):
        return self.code
        

class CouponProducts(models.Model):
    id = None
    coupon = models.ForeignKey(Coupons, on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    
    class Meta:
        unique_together = (
            ('coupon', 'product')
        )
        
        
class CouponUse(models.Model):
    id = None
    coupon = models.ForeignKey(Coupons, on_delete=models.CASCADE)
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    uses = models.SmallIntegerField(default=0)
    
    class Meta:
        unique_together = (
            ('coupon', 'user')
        )
        
class CouponRule(models.Model):
    coupon = models.OneToOneField(Coupons, on_delete=models.CASCADE)
    rule_value = models.FloatField(null=True, blank=True)
    max_uses = models.IntegerField(null=True, blank=True)
    max_uses_per_user = models.IntegerField(null=True, blank=True)
    discount_value = models.FloatField()
    discount_limit = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    RULE_TYPE_MIN_PRODUCT_PRICE = 0
    RULE_TYPE_MIN_ORDER_TOTAL_PRICE = 1
    
    RULE_TYPE_CHOICES = [
        (RULE_TYPE_MIN_PRODUCT_PRICE, 'Min Product Price'),
        (RULE_TYPE_MIN_ORDER_TOTAL_PRICE, 'Min Order Total Price')
    ]
    
    DISCOUNT_TYPE_PERCENTAGE = 0
    DISCOUNT_TYPE_FIXED = 1
    
    DISCOUNT_TYPE_CHOICES = [
        (DISCOUNT_TYPE_PERCENTAGE, 'Percentage'),
        (DISCOUNT_TYPE_FIXED, 'Fixed')
    ]
    
    COUPON_TYPE_ORDER = 0
    COUPON_TYPE_PRODUCT = 1
    COUPON_TYPE_SELLER = 2
    COUPON_TYPE_SHIPPING = 3
    
    COUPON_TYPE_CHOICES = [
        (COUPON_TYPE_ORDER, 'Order'),
        (COUPON_TYPE_PRODUCT, 'Product'),
        (COUPON_TYPE_SELLER, 'Seller'),
        (COUPON_TYPE_SHIPPING, 'Shipping')
    ]
    
    rule_type = models.SmallIntegerField(choices=RULE_TYPE_CHOICES, null=True, blank=True)
    coupon_type = models.SmallIntegerField(choices=COUPON_TYPE_CHOICES)
    discount_type = models.SmallIntegerField(choices=DISCOUNT_TYPE_CHOICES)
    