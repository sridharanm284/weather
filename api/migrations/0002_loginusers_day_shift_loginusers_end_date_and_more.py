# Generated by Django 4.2.1 on 2023-07-11 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='loginusers',
            name='day_shift',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='loginusers',
            name='end_date',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='loginusers',
            name='expected_date',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='loginusers',
            name='last_bill_update',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='loginusers',
            name='lat',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='loginusers',
            name='lon',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='loginusers',
            name='night_shift',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='loginusers',
            name='project_no',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='loginusers',
            name='service_types',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='loginusers',
            name='site_route',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='loginusers',
            name='start_date',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
