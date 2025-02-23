# Generated by Django 5.0 on 2024-10-04 00:29

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import random


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0005_rename_user_id_cart_user_alter_cart_unique_together'),
        ('products', '0006_remove_productimages_unique_product_variant_image_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='product_variant',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='products.productvariant'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cart',
            name='size',
            field=models.SmallIntegerField(choices=[(0, 'Small'), (1, 'Medium'), (2, 'Large'), (3, 'XLarge'), (4, 'XXLarge'), (5, 'XXXLarge')], default=random.randint(0, 5)),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='cart',
            unique_together={('user', 'product_variant', 'size')},
        ),
        migrations.RemoveField(
            model_name='cart',
            name='product',
        ),
    ]
