from django.db import models

class Orders(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.user.username} - {self.order_date}"
    
class OrdersItems(models.Model):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.IntegerField()

    class Meta:
        unique_together = ('order', 'product')
        db_table = 'orders_items'

