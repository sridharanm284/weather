# Generated by Django 4.2.1 on 2023-07-11 13:29

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Chat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('date_time', models.DateTimeField(auto_now_add=True)),
                ('file', models.ImageField(blank=True, upload_to='uploads/')),
                ('chat_id', models.CharField(max_length=100)),
                ('user', models.CharField(default='user', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='ChatRooms',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField()),
                ('chat_id', models.CharField(max_length=100)),
                ('user', models.CharField(blank=True, max_length=100)),
                ('read_user', models.CharField(default='false', max_length=100)),
                ('read_admin', models.CharField(default='false', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='ForecastID',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('forecast_id', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='LoginUsers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('password', models.CharField(max_length=100)),
                ('user_type', models.CharField(default='user', max_length=100)),
                ('operation', models.CharField(blank=True, max_length=100)),
                ('email_address', models.CharField(blank=True, max_length=100)),
                ('client_id', models.CharField(blank=True, max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='ObservationForm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_time', models.DateTimeField()),
                ('wind_speed', models.IntegerField()),
                ('combined', models.IntegerField()),
                ('swell_ht', models.IntegerField()),
                ('swell_period', models.IntegerField()),
                ('swell_direction', models.IntegerField()),
                ('vis', models.IntegerField()),
                ('present', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Tokens',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField()),
                ('user', models.CharField(max_length=100)),
                ('token', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='UserTicks',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('txt', models.BooleanField(default=False)),
                ('amwia', models.BooleanField(default=False)),
                ('amwaa', models.BooleanField(default=False)),
                ('amsatpic', models.BooleanField(default=False)),
                ('amwap', models.BooleanField(default=False)),
                ('zip', models.BooleanField(default=False)),
                ('amcurrent', models.BooleanField(default=False)),
                ('pmcurrent', models.BooleanField(default=False)),
                ('osf', models.BooleanField(default=False)),
                ('pmwifa', models.BooleanField(default=False)),
                ('pmwaa', models.BooleanField(default=False)),
                ('pmsatpic', models.BooleanField(default=False)),
                ('pmwip', models.BooleanField(default=False)),
                ('pmwap', models.BooleanField(default=False)),
                ('user_id', models.IntegerField(default=0)),
            ],
        ),
    ]
