from django.db import models

class Country(models.Model):
    id = models.SmallAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name'], name='unique_country')
        ]
    
    def __str__(self):
        return self.name
    
    
class City(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    shipping_fee = models.FloatField()
    
    class Meta:
        unique_together = ['name', 'country']
        
    def __str__(self):
        return self.name