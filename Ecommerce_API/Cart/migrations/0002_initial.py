# Generated by Django 5.0 on 2024-09-13 10:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cart', '0001_initial'),
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='product_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product'),
        ),
    ]
