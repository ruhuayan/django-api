# Generated by Django 2.1.1 on 2018-10-15 02:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('applications', '0013_auto_20181014_2230'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appinfo',
            name='description',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='appinfo',
            name='effType',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]