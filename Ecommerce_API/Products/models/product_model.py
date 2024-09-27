from django.db import models
from django.contrib.postgres.fields import ArrayField

class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    seller = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    related_products = ArrayField(
        models.JSONField(),
        default=list,
        blank=True,
        null=True
    )
    image = models.URLField(max_length=255, blank=True, null=True)
    visible_in_search = models.BooleanField(default=True)
    

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        indexes = [
            models.Index(fields=['seller_id', 'id'])
        ]

