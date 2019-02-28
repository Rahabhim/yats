# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-11-05 21:14
from __future__ import unicode_literals

from django.db import migrations, models

def convertDeadline(apps, schema_editor):
    tickets = apps.get_model('web', 'test')
    for ticket in tickets.objects.all():
        if hasattr(ticket, 'deadline'):
            ticket.show_start = ticket.deadline
            ticket.deadline = None
            ticket.save()

class Migration(migrations.Migration):

    dependencies = [
        ('yats', '0019_tickets_ignorants'),
    ]

    operations = [
        migrations.AddField(
            model_name='tickets',
            name='show_start',
            field=models.DateTimeField(blank=True, null=True, verbose_name='show from'),
        ),
        migrations.AlterField(
            model_name='tickets',
            name='hasAttachments',
            field=models.BooleanField(default=False, verbose_name='has attachments'),
        ),
        migrations.AlterField(
            model_name='tickets',
            name='hasComments',
            field=models.BooleanField(default=False, verbose_name='has comments'),
        ),
        migrations.RunPython(convertDeadline),

    ]