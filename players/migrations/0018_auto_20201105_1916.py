# Generated by Django 3.1.2 on 2020-11-05 18:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0017_case_is_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]