# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2019-02-26 15:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('yats', '0020_auto_20181105_2214'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='day_since_closed_tickets',
            field=models.SmallIntegerField(default=5),
        ),
    ]
