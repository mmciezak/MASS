# Generated by Django 5.1.2 on 2024-11-17 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mass', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='extendeduser',
            name='cart',
            field=models.ManyToManyField(to='mass.medication'),
        ),
    ]
