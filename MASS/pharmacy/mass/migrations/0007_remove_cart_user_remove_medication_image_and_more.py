# Generated by Django 5.1.3 on 2024-11-18 16:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mass', '0006_alter_extendeduser_cart'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cart',
            name='user',
        ),
        migrations.RemoveField(
            model_name='medication',
            name='image',
        ),
        migrations.AddField(
            model_name='medication',
            name='stock_quantity',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='extendeduser',
            name='cart',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='mass.cart'),
        ),
        migrations.AlterField(
            model_name='medication',
            name='description',
            field=models.TextField(default='null'),
        ),
        migrations.AlterField(
            model_name='medication',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='medication',
            name='side_effects',
            field=models.TextField(blank=True),
        ),
    ]
