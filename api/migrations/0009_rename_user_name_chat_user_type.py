# Generated by Django 4.2.1 on 2023-09-19 03:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_rename_user_chat_user_name_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='chat',
            old_name='user_name',
            new_name='user_type',
        ),
    ]
