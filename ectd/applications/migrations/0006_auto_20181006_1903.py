# Generated by Django 2.1.1 on 2018-10-06 23:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('applications', '0005_auto_20180930_1117'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appinfo',
            name='refNumber',
            field=models.CharField(max_length=15, null=True),
        ),
        migrations.AlterField(
            model_name='appinfo',
            name='refType',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='appinfo',
            name='subNumber',
            field=models.CharField(max_length=15, null=True),
        ),
    ]
