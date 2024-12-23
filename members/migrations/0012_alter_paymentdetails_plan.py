# Generated by Django 5.1.4 on 2024-12-23 11:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0011_freeze_member_delete_freeze'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentdetails',
            name='plan',
            field=models.CharField(choices=[('daily', 'Daily'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('biannually', 'Biannually'), ('yearly', 'Yearly'), ('student', 'Student Package')], max_length=20, verbose_name='Payment Plan'),
        ),
    ]
