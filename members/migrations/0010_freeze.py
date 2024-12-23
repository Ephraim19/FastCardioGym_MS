# Generated by Django 5.1.4 on 2024-12-21 08:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0009_member_is_frozen'),
    ]

    operations = [
        migrations.CreateModel(
            name='Freeze',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('freeze_time', models.IntegerField()),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='frozen', to='members.member')),
            ],
        ),
    ]
