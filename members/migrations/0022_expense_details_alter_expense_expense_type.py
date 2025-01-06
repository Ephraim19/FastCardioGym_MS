# Generated by Django 5.1.4 on 2025-01-04 20:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0021_alter_gym_reminder_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='expense',
            name='details',
            field=models.TextField(default='New year'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='expense',
            name='expense_type',
            field=models.CharField(max_length=20),
        ),
    ]