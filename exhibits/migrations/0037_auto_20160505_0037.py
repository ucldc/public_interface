# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-05-05 00:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exhibits', '0036_auto_20160425_1820'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exhibit',
            name='hero',
            field=models.ImageField(blank=True, null=True, upload_to='uploads/', verbose_name='Hero Image'),
        ),
    ]