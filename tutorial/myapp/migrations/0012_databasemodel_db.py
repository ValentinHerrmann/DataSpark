# Generated by Django 5.2 on 2025-04-16 13:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0011_delete_todoitem_alter_databasemodel_sql_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='databasemodel',
            name='db',
            field=models.BinaryField(blank=True, default=b'', null=True),
        ),
    ]
