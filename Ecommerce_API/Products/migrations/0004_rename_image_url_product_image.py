# Generated by Django 5.0 on 2024-09-27 19:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_rename_seller_id_product_seller_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='image_url',
            new_name='image',
        ),
    ]
