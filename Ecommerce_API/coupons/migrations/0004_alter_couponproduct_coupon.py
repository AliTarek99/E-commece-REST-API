# Generated by Django 5.0 on 2024-12-11 11:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coupons', '0003_alter_couponproduct_coupon_alter_couponuse_coupon'),
    ]

    operations = [
        migrations.AlterField(
            model_name='couponproduct',
            name='coupon',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='couponproduct', to='coupons.coupon'),
        ),
    ]
