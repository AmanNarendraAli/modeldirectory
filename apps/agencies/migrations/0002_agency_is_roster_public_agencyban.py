from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('agencies', '0001_initial'),
        ('models_app', '0003_modelprofile_phone_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='agency',
            name='is_roster_public',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='AgencyBan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('banned_at', models.DateTimeField(auto_now_add=True)),
                ('agency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='banned_models', to='agencies.agency')),
                ('model_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agency_bans', to='models_app.modelprofile')),
            ],
            options={
                'unique_together': {('model_profile', 'agency')},
            },
        ),
    ]
