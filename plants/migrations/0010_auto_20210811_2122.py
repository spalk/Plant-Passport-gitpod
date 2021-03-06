# Generated by Django 3.2.4 on 2021-08-11 21:22

from django.db import migrations, models
import django.db.models.deletion
import plants.models


class Migration(migrations.Migration):

    dependencies = [
        ('plants', '0009_auto_20210802_2028'),
    ]

    operations = [
        migrations.CreateModel(
            name='Photo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(blank=True, max_length=255)),
                ('photo', models.FileField(upload_to=plants.models.user_directory_path)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='RichPlant',
            fields=[
                ('plant_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='plants.plant')),
            ],
            bases=('plants.plant',),
        ),
        migrations.AlterModelManagers(
            name='plant',
            managers=[
            ],
        ),
    ]
