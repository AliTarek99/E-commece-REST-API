# Generated by Django 5.0 on 2024-11-16 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0010_orders_updated_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orders',
            name='status',
            field=models.SmallIntegerField(choices=[(0, 'Pending'), (1, 'Completed'), (2, 'Shipped'), (3, 'Delivered'), (4, 'Returned'), (5, 'Cancelled')], default=0),
        ),
    ]
