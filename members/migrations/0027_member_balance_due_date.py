# Generated by Django 5.1.4 on 2025-01-08 06:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0026_task'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='balance_due_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]