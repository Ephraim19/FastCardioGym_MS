# Generated by Django 5.1.4 on 2025-01-14 12:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0032_task_member'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='member',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='members.member'),
        ),
    ]