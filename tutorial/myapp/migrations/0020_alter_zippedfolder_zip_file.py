# Generated by Django 5.2 on 2025-05-09 11:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0019_delete_databasemodel'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zippedfolder',
            name='zip_file',
            field=models.FileField(upload_to='tutorial/myapp/staticfiles/'),
        ),
    ]
