# Generated by Django 5.1.4 on 2024-12-21 08:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0010_freeze'),
    ]

    operations = [
        migrations.CreateModel(
            name='Freeze_member',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('freeze_time', models.IntegerField()),
                ('frozen_date', models.DateField(auto_now_add=True)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='frozen', to='members.member')),
            ],
        ),
        migrations.DeleteModel(
            name='Freeze',
        ),
    ]