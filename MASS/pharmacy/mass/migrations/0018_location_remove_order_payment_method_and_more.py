# Generated by Django 5.1.3 on 2024-12-21 10:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mass', '0017_extendeduser_prescription_cart_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(default='', max_length=255)),
            ],
        ),

        migrations.AddField(
            model_name='medication',
            name='category_tag',
            field=models.CharField(choices=[('pain', 'Ból'), ('allergy', 'Alergia'), ('diabetic', 'Diabetyk'), ('skin', 'Skóra'), ('cold', 'Przeziębienie'), ('wounds', 'Rany i oparzenia'), ('digestive', 'Trawienie'), ('contraception', 'Antykoncepcja'), ('vitamins', 'Witaminy'), ('inne', 'Inne')], default='inne', max_length=20),
        ),
        migrations.AlterField(
            model_name='order',
            name='phone_number',
            field=models.DecimalField(decimal_places=0, max_digits=20),
        ),
    ]
