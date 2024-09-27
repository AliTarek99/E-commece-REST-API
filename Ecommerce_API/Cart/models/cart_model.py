from django.db import models


class Cart(models.Model):
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.IntegerField()

    class Meta:
        unique_together = ['user', 'product']
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'


    def __str__(self):
        return f'{self.user} - {self.product}'