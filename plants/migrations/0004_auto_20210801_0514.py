# Generated by Django 3.2.4 on 2021-08-01 05:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('plants', '0003_alter_plant_creation_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='plant',
            name='creator',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='plant',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='attribute',
            name='value_type',
            field=models.IntegerField(choices=[(1, 'String'), (21, 'Number')]),
        ),
    ]
