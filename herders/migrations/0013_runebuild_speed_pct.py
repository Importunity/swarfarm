# Generated by Django 2.2.13 on 2020-07-23 19:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('herders', '0012_auto_20200328_1741'),
    ]

    operations = [
        migrations.AddField(
            model_name='runebuild',
            name='speed_pct',
            field=models.IntegerField(default=0),
        ),
    ]