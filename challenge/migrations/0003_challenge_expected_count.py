# Generated by Django 3.0.3 on 2020-09-07 22:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0002_auto_20200908_0543'),
    ]

    operations = [
        migrations.AddField(
            model_name='challenge',
            name='expected_count',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
