# Generated by Django 3.1 on 2023-08-06 11:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_variation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variation',
            name='variation_category',
            field=models.CharField(choices=[('color', 'color'), ('size', 'size'), ('ssd', 'ssd'), ('ram', 'ram')], max_length=100),
        ),
    ]
