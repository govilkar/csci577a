# Generated by Django 3.1.2 on 2020-11-03 23:58

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app1', '0014_auto_20201103_1545'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comments',
            name='created_at',
            field=models.DateField(default=datetime.datetime(2020, 11, 3, 15, 58, 40, 305814)),
        ),
        migrations.AlterField(
            model_name='posts',
            name='created_at',
            field=models.DateField(default=datetime.datetime(2020, 11, 3, 15, 58, 40, 305814)),
        ),
    ]
