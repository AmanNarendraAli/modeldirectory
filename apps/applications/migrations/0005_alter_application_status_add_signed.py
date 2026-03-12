from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('applications', '0004_alter_applicationsnapshot_bust_cm_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='status',
            field=models.CharField(
                choices=[
                    ('draft', 'Draft'),
                    ('submitted', 'Submitted'),
                    ('under_review', 'Under Review'),
                    ('shortlisted', 'Shortlisted'),
                    ('contacted', 'Contacted'),
                    ('signed', 'Signed'),
                    ('rejected', 'Rejected'),
                    ('withdrawn', 'Withdrawn'),
                ],
                default='draft',
                max_length=20,
            ),
        ),
    ]
