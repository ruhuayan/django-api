# Generated by Django 2.1.1 on 2018-10-06 23:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('applications', '0006_auto_20181006_1903'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='appinfo',
            name='refNumber',
        ),
        migrations.RemoveField(
            model_name='appinfo',
            name='refType',
        ),
        migrations.RemoveField(
            model_name='appinfo',
            name='subNumber',
        ),
    ]