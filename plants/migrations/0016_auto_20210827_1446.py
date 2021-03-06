# Generated by Django 3.2.6 on 2021-08-27 14:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plants', '0015_attribute_filterable'),
    ]

    operations = [
        migrations.AddField(
            model_name='attribute',
            name='max_text_length',
            field=models.IntegerField(default=100),
        ),
        migrations.AddField(
            model_name='log',
            name='hidden',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='attribute',
            name='value_type',
            field=models.IntegerField(choices=[(1, 'String'), (2, 'Number'), (3, 'Text'), (4, 'Date')]),
        ),
    ]
