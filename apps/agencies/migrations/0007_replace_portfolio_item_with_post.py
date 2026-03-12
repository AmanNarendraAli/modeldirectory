import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agencies', '0006_agencyportfolioitem'),
    ]

    operations = [
        migrations.DeleteModel(
            name='AgencyPortfolioItem',
        ),
        migrations.CreateModel(
            name='AgencyPortfolioPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField(blank=True)),
                ('caption', models.TextField(blank=True)),
                ('cover_image', models.ImageField(blank=True, null=True, upload_to='agencies/portfolio/covers/')),
                ('is_public', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('agency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='portfolio_posts', to='agencies.agency')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AgencyPortfolioAsset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='agencies/portfolio/assets/')),
                ('alt_text', models.CharField(blank=True, max_length=255)),
                ('display_order', models.PositiveSmallIntegerField(default=0)),
                ('portfolio_post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assets', to='agencies.agencyportfoliopost')),
            ],
            options={
                'ordering': ['display_order'],
            },
        ),
    ]
