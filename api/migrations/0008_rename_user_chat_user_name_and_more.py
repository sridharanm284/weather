# Generated by Django 4.2.1 on 2023-09-10 12:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_chatrooms_unread_admin_chatrooms_unread_user'),
    ]

    operations = [
        migrations.RenameField(
            model_name='chat',
            old_name='user',
            new_name='user_name',
        ),
        migrations.RenameField(
            model_name='chatrooms',
            old_name='user',
            new_name='user_name',
        ),
        migrations.RenameField(
            model_name='tokens',
            old_name='user',
            new_name='user_name',
        ),
    ]
