from django.db import models


class Cart(models.Model):
    user_id = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.IntegerField()

    class Meta:
        unique_together = ['user_id', 'product_id']
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'


    def __str__(self):
        return f'{self.user_id} - {self.product_id}'