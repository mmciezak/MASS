# Generated by Django 5.1.2 on 2024-12-03 19:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mass', '0013_rename_method_of_payment_order_payment_method'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='prescription',
            name='dosage',
        ),
    ]
