# Generated by Django 5.1.4 on 2024-12-23 17:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0012_alter_paymentdetails_plan'),
    ]

    operations = [
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('expense_type', models.TextField()),
                ('date', models.DateField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.AlterField(
            model_name='paymentdetails',
            name='plan',
            field=models.CharField(choices=[('daily', 'Daily'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('biannually', 'Biannually'), ('annually', 'Annually'), ('student', 'Student Package')], max_length=20, verbose_name='Payment Plan'),
        ),
    ]
