# Generated by Django 5.1.4 on 2025-01-03 19:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0017_alter_paymentdetails_plan'),
    ]

    operations = [
        migrations.CreateModel(
            name='GymReminder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('attendance', 'Attendance'), ('subscription', 'Subscription')], max_length=20)),
                ('is_sent', models.BooleanField(default=False)),
                ('sent_manually', models.BooleanField(default=False)),
                ('sent_date', models.DateTimeField(blank=True, null=True)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='members.member')),
            ],
        ),
    ]
