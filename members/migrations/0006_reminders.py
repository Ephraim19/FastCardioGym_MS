# Generated by Django 5.1.4 on 2024-12-19 14:57

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0005_member_gender'),
    ]

    operations = [
        migrations.CreateModel(
            name='reminders',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reminder', models.TextField()),
                ('reminder_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('category', models.CharField(blank=True, max_length=50, null=True)),
                ('status', models.BooleanField(choices=[('sent', 'Sent'), ('not sent', 'Not sent')], default='not sent')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reminders', to='members.member')),
            ],
            options={
                'ordering': ['reminder_date'],
            },
        ),
    ]
