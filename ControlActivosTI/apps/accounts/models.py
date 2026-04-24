import os

from django.conf import settings
from django.db import models


def ruta_foto_perfil(instance, filename):
    extension = os.path.splitext(filename)[1].lower() or ".jpg"
    username = instance.user.get_username() or f"user-{instance.user_id}"
    safe_username = "".join(char for char in username if char.isalnum() or char in {"-", "_"})
    return f"perfiles/{safe_username}{extension}"


class PerfilUsuario(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil",
    )
    foto = models.ImageField(upload_to=ruta_foto_perfil, blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True)
    cargo_visible = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "perfil de usuario"
        verbose_name_plural = "perfiles de usuario"

    def __str__(self):
        return f"Perfil de {self.user.get_username()}"
