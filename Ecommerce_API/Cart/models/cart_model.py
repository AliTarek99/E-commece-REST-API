from django.db import models
from products.models import Sizes


class Cart(models.Model):
    id = None
    user = models.OneToOneField('users.CustomUser', on_delete=models.CASCADE, primary_key=True)
    total_price = models.FloatField(default=0)
    discount_price = models.FloatField(default=0)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cartitem')
    product_variant = models.ForeignKey('products.ProductVariant', on_delete=models.CASCADE)
    discount_price = models.FloatField()
    quantity = models.IntegerField()


    class Meta:
        unique_together = ['cart', 'product_variant']


    def __str__(self):
        ret = ""
        for keys in self.__dict__:
            ret += f"{keys} : {self.__dict__[keys]} \n"
        return ret
    
    
class CartCoupon(models.Model):
    id = None
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE , related_name='cartcoupon')
    coupon = models.ForeignKey('coupons.Coupon', on_delete=models.CASCADE, related_name='cartcoupon')
    primary_key = False 
    
    class Meta:
        unique_together = ['cart', 'coupon']
        