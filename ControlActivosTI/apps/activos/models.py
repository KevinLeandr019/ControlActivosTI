from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max
from django.utils import timezone

from apps.catalogos.models import EstadoActivo, TipoActivo, TipoEventoActivo


TIPOS_ACTIVO_CON_ESPECIFICACIONES = (
    "laptop",
    "pc",
    "desktop",
    "escritorio",
    "computador",
    "computadora",
)


def ruta_foto_activo(instance, filename):
    codigo = instance.activo.codigo if instance.activo and instance.activo.codigo else "sin-codigo"
    return f"activos/{codigo}/{filename}"


class Activo(models.Model):
    codigo = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        db_index=True,
    )
    tipo_activo = models.ForeignKey(
        TipoActivo,
        on_delete=models.PROTECT,
        related_name="activos",
    )
    marca = models.CharField(max_length=80)
    modelo = models.CharField(max_length=80)
    serie = models.CharField(
    max_length=120,
    db_index=True,
    blank=True,
    default="S/N",
    )
    cpu = models.CharField(max_length=150, blank=True)
    ram = models.CharField(max_length=50, blank=True)
    disco = models.CharField(max_length=80, blank=True)
    sistema_operativo = models.CharField(max_length=50, blank=True, default="")
    fecha_compra = models.DateField(null=True, blank=True)
    valor = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    estado_activo = models.ForeignKey(
        EstadoActivo,
        on_delete=models.PROTECT,
        related_name="activos",
    )
    observaciones = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Activo"
        verbose_name_plural = "Activos"
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} - {self.marca} {self.modelo}"

    def _obtener_prefijo_tipo(self):
        nombre_tipo = (self.tipo_activo.nombre or "").strip().lower()

        mapa_prefijos = {
            "laptop": "LAP",
            "pc": "PC",
            "monitor": "MON",
            "mouse": "MOU",
            "teclado": "TEC",
            "base": "BAS",
            "cargador": "CAR",
        }

        return mapa_prefijos.get(nombre_tipo, "ACT")

    def requiere_especificaciones_tecnicas(self):
        nombre_tipo = (self.tipo_activo.nombre if self.tipo_activo_id else "").strip().lower()
        return any(clave in nombre_tipo for clave in TIPOS_ACTIVO_CON_ESPECIFICACIONES)

    def limpiar_especificaciones_no_aplicables(self):
        if self.requiere_especificaciones_tecnicas():
            return

        self.cpu = ""
        self.ram = ""
        self.disco = ""
        self.sistema_operativo = ""

    def _generar_codigo(self):
        prefijo = self._obtener_prefijo_tipo()
        ultimo = (
            Activo.objects.filter(codigo__startswith=f"{prefijo}-")
            .order_by("-codigo")
            .first()
        )

        if ultimo and ultimo.codigo:
            try:
                ultimo_numero = int(ultimo.codigo.split("-")[-1])
            except (ValueError, IndexError):
                ultimo_numero = 0
        else:
            ultimo_numero = 0

        siguiente_numero = ultimo_numero + 1
        return f"{prefijo}-{siguiente_numero:04d}"

    def save(self, *args, **kwargs):
        if not self.serie or not self.serie.strip():
            self.serie = "S/N"
        self.limpiar_especificaciones_no_aplicables()
        if not self.codigo:
            self.codigo = self._generar_codigo()
        super().save(*args, **kwargs)


class FotoActivo(models.Model):
    activo = models.ForeignKey(
        Activo,
        on_delete=models.CASCADE,
        related_name="fotos",
    )
    imagen = models.ImageField(upload_to=ruta_foto_activo)
    descripcion = models.CharField(max_length=255, blank=True)
    orden = models.PositiveSmallIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Foto de activo"
        verbose_name_plural = "Fotos de activos"
        ordering = ["activo", "orden"]
        constraints = [
            models.UniqueConstraint(
                fields=["activo", "orden"],
                name="unique_orden_foto_por_activo",
            )
        ]

    def __str__(self):
        codigo = self.activo.codigo if self.activo_id else "sin-activo"
        return f"Foto {self.orden or '-'} - {codigo}"

    def clean(self):
        super().clean()

        if not self.activo_id:
            return

        fotos_existentes = FotoActivo.objects.filter(activo_id=self.activo_id)
        if self.pk:
            fotos_existentes = fotos_existentes.exclude(pk=self.pk)

        if fotos_existentes.count() >= 5:
            raise ValidationError("Un activo no puede tener más de 5 fotos.")

        if self.orden is not None:
            if fotos_existentes.filter(orden=self.orden).exists():
                raise ValidationError({"orden": "Ya existe una foto con ese orden para este activo."})

    def save(self, *args, **kwargs):
        if self.activo_id and not self.orden:
            ultimo_orden = (
                FotoActivo.objects
                .filter(activo_id=self.activo_id)
                .exclude(pk=self.pk)
                .aggregate(max_orden=Max("orden"))
                .get("max_orden") or 0
            )
            self.orden = ultimo_orden + 1

        self.full_clean()
        super().save(*args, **kwargs)


class EventoActivo(models.Model):
    activo = models.ForeignKey(
        Activo,
        on_delete=models.CASCADE,
        related_name="eventos",
    )
    tipo_evento = models.ForeignKey(
        TipoEventoActivo,
        on_delete=models.PROTECT,
        related_name="eventos",
    )
    fecha_evento = models.DateTimeField(default=timezone.now)
    detalle = models.TextField()
    usuario_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="eventos_activo_registrados",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Evento de activo"
        verbose_name_plural = "Eventos de activos"
        ordering = ["-fecha_evento", "-id"]

    def __str__(self):
        return f"{self.activo.codigo} - {self.tipo_evento.nombre}"
