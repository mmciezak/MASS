# Generated by Django 5.1.3 on 2025-01-17 17:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mass', '0030_pharmacyorder_pharmacyorderitem'),
    ]

    operations = [
        migrations.AlterField(
            model_name='medicationstock',
            name='quantity',
            field=models.IntegerField(default=0),
        ),
    ]
