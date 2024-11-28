# Generated by Django 5.0 on 2024-11-28 00:12

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('products', '0011_colors_created_at_colors_updated_at_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Coupons',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=8, unique=True)),
                ('uses', models.BigIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('seller', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('id', 'is_active'), ('seller_id', 'id')},
            },
        ),
        migrations.CreateModel(
            name='CouponRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rule_value', models.FloatField(blank=True, null=True)),
                ('max_uses', models.IntegerField(blank=True, null=True)),
                ('max_uses_per_user', models.IntegerField(blank=True, null=True)),
                ('discount_value', models.FloatField()),
                ('discount_limit', models.FloatField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('rule_type', models.SmallIntegerField(blank=True, choices=[(0, 'Min Product Price'), (1, 'Min Order Total Price')], null=True)),
                ('coupon_type', models.SmallIntegerField(choices=[(0, 'Order'), (1, 'Product'), (2, 'Seller'), (3, 'Shipping')])),
                ('discount_type', models.SmallIntegerField(choices=[(0, 'Percentage'), (1, 'Fixed')])),
                ('coupon', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='coupons.coupons')),
            ],
        ),
        migrations.CreateModel(
            name='CouponProducts',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product')),
                ('coupon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='coupons.coupons')),
            ],
            options={
                'unique_together': {('coupon', 'product')},
            },
        ),
        migrations.CreateModel(
            name='CouponUse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uses', models.SmallIntegerField(default=0)),
                ('coupon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='coupons.coupons')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('coupon', 'user')},
            },
        ),
    ]
