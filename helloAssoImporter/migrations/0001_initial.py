import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=20)),
                ('current', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Saison',
                'verbose_name_plural': 'Saisons',
            },
        ),
        migrations.CreateModel(
            name='MemberShipForm',
            fields=[
                ('form_slug', models.CharField(primary_key=True, serialize=False)),
                ('title', models.CharField()),
                ('form_type', models.CharField()),
                ('description', models.CharField()),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('updated_at', models.DateTimeField()),
                ('created_at', models.DateTimeField()),
                ('season', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='helloAssoImporter.season')),
            ],
        ),
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.CharField()),
                ('first_name', models.CharField()),
                ('last_name', models.CharField()),
            ],
        ),
        migrations.AddConstraint(
            model_name='member',
            constraint=models.UniqueConstraint(fields=['email', 'first_name', 'last_name'], name='unique_member_identity'),
        ),
        migrations.CreateModel(
            name='MemberShipFormOrder',
            fields=[
                ('item_id', models.IntegerField(primary_key=True, serialize=False)),
                ('order_id', models.IntegerField(db_index=True)),
                ('payer_email', models.CharField()),
                ('payer_first_name', models.CharField()),
                ('payer_last_name', models.CharField()),
                ('category', models.CharField(blank=True, null=True)),
                ('birthdate', models.DateField(blank=True, null=True)),
                ('licence_number', models.CharField(blank=True, default='')),
                ('sex', models.CharField(blank=True, null=True)),
                ('caci_expiration', models.DateField(blank=True, null=True)),
                ('updated_at', models.DateTimeField()),
                ('created_at', models.DateTimeField()),
                ('form', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='helloAssoImporter.membershipform')),
                ('member', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='helloAssoImporter.member')),
            ],
        ),
        migrations.CreateModel(
            name='EventForm',
            fields=[
                ('form_slug', models.CharField(primary_key=True, serialize=False)),
                ('title', models.CharField()),
                ('form_type', models.CharField()),
                ('description', models.CharField()),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('last_registration_updated', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField()),
                ('created_at', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='EventFormOrder',
            fields=[
                ('order_id', models.IntegerField(primary_key=True, serialize=False)),
                ('payer_email', models.CharField(null=True)),
                ('payer_first_name', models.CharField(null=True)),
                ('payer_last_name', models.CharField(null=True)),
                ('created_at', models.DateTimeField(null=True)),
                ('updated_at', models.DateTimeField(null=True)),
                ('form', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='helloAssoImporter.eventform')),
            ],
        ),
        migrations.CreateModel(
            name='EventRegistration',
            fields=[
                ('item_id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField()),
                ('first_name', models.CharField()),
                ('last_name', models.CharField()),
                ('state', models.CharField(choices=[('Waiting', 'En attente'), ('Processed', 'Traité'), ('Registered', 'Inscrit'), ('Deleted', 'Supprimé'), ('Refunded', 'Remboursé'), ('Canceled', 'Annulé'), ('Refused', 'Refusé'), ('Contested', 'Contesté'), ('Abandoned', 'Abandonné'), ('Unknown', 'Inconnu')], default='Unknown', max_length=20)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='helloAssoImporter.eventformorder')),
            ],
        ),
    ]
