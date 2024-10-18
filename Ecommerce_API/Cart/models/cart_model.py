from django.db import models
from products.models import Sizes



class Cart(models.Model):
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    product_variant = models.ForeignKey('products.ProductVariant', on_delete=models.CASCADE)
    quantity = models.IntegerField()


    class Meta:
        unique_together = ['user', 'product_variant']
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'


    def __str__(self):
        ret = ""
        for keys in self.__dict__:
            ret += f"{keys} : {self.__dict__[keys]} \n"
        return ret