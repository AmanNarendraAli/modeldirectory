from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agencies', '0004_alter_agencyrequirement_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='agencyrequirement',
            name='min_bust_cm',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='agencyrequirement',
            name='max_bust_cm',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='agencyrequirement',
            name='min_waist_cm',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='agencyrequirement',
            name='max_waist_cm',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='agencyrequirement',
            name='min_hips_cm',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='agencyrequirement',
            name='max_hips_cm',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='agencyrequirement',
            name='min_inseam_cm',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='agencyrequirement',
            name='max_inseam_cm',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='agencyrequirement',
            name='preferred_hair_colors',
            field=models.CharField(
                blank=True,
                help_text='Comma-separated preferred hair colours, e.g. Brown, Black, Dark',
                max_length=200,
            ),
        ),
        migrations.AddField(
            model_name='agencyrequirement',
            name='preferred_eye_colors',
            field=models.CharField(
                blank=True,
                help_text='Comma-separated preferred eye colours, e.g. Brown, Green, Hazel',
                max_length=200,
            ),
        ),
    ]
