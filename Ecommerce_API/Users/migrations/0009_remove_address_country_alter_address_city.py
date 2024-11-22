# Generated by Django 5.0 on 2024-11-21 23:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shipping', '0001_initial'),
        ('users', '0008_address_default_customuser_created_at_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='address',
            name='country',
        ),
        migrations.AlterField(
            model_name='address',
            name='city',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='shipping.city'),
        ),
    ]
