# Generated by Django 3.0.3 on 2020-09-07 11:33

import datetime
from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CaptureMethod',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True, default=None, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CaptureType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True, default=None, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ImageQuality',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True, default=None, null=True)),
            ],
            options={
                'verbose_name_plural': 'Image Quality',
            },
        ),
        migrations.CreateModel(
            name='Photographer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unique_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('business_name', models.CharField(max_length=200)),
                ('business_website', models.TextField()),
                ('business_email', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('type', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(default='1', max_length=3), null=True, size=None)),
                ('capture_method', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(default='1', max_length=3), null=True, size=None)),
                ('image_quality', models.CharField(default='0', max_length=3)),
                ('geometry', models.TextField(default='')),
                ('is_published', models.BooleanField(default=False)),
                ('zoom', models.FloatField(default=5)),
                ('created_at', models.DateTimeField(blank=True, default=datetime.datetime.now)),
                ('updated_at', models.DateTimeField(blank=True, default=datetime.datetime.now)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PhotographerEnquire',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=100)),
                ('email', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, default=None, null=True)),
                ('status', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(blank=True, default=datetime.datetime.now)),
                ('updated_at', models.DateTimeField(blank=True, default=datetime.datetime.now)),
                ('photographer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='photographer.Photographer')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]