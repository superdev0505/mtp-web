# Generated by Django 3.0.3 on 2020-08-29 10:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sequence', '0006_auto_20200829_1143'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transporttype',
            name='icon',
        ),
        migrations.RemoveField(
            model_name='transporttype',
            name='parent',
        ),
        migrations.AlterField(
            model_name='transporttype',
            name='name',
            field=models.CharField(max_length=50),
        ),
    ]