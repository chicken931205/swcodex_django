# Generated by Django 5.0.7 on 2024-08-12 19:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('connector', '0022_column_default_column_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='column',
            name='comment',
        ),
        migrations.RemoveField(
            model_name='column',
            name='default_column_name',
        ),
        migrations.RemoveField(
            model_name='column',
            name='sample_value',
        ),
        migrations.AddField(
            model_name='column',
            name='foreign_key',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='column',
            name='primary_key',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='column',
            name='data_type',
            field=models.CharField(blank=True, choices=[('DATE', 'Date'), ('TIMESTAMP', 'Datetime'), ('INTEGER', 'Integer'), ('TEXT', 'String'), ('NUMERIC', 'Decimal'), ('BIGINT', 'Big Integer'), ('BOOLEAN', 'Boolean')], default=None, max_length=10, null=True),
        ),
    ]
