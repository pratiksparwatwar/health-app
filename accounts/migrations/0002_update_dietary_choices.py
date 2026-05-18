from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='dietary_preference',
            field=models.CharField(
                choices=[
                    ('veg', 'Vegetarian (No Egg)'),
                    ('veg_egg', 'Vegetarian + Egg'),
                    ('non_veg', 'Non-Vegetarian'),
                ],
                default='non_veg',
                max_length=20,
            ),
        ),
    ]
