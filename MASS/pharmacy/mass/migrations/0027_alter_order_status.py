# Generated by Django 5.1.3 on 2025-01-09 15:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mass', '0026_symptom_medication_symptoms'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('received', 'Received'), ('expired', 'Expired')], default='pending', max_length=10),
        ),
    ]
