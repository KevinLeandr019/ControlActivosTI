import apps.accounts.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PerfilUsuario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("foto", models.ImageField(blank=True, null=True, upload_to=apps.accounts.models.ruta_foto_perfil)),
                ("telefono", models.CharField(blank=True, max_length=30)),
                ("cargo_visible", models.CharField(blank=True, max_length=120)),
                ("bio", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="perfil", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "perfil de usuario",
                "verbose_name_plural": "perfiles de usuario",
            },
        ),
    ]
