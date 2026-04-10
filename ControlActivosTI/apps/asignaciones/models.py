from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone

from apps.activos.models import Activo
from apps.catalogos.models import EstadoActivo
from apps.colaboradores.models import Colaborador


class Asignacion(models.Model):
    class EstadoAsignacion(models.TextChoices):
        ACTIVA = "ACTIVA", "Activa"
        CERRADA = "CERRADA", "Cerrada"

    codigo_asignacion = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        db_index=True,
        null=True,
        blank=True,
    )
    colaborador = models.ForeignKey(
        Colaborador,
        on_delete=models.PROTECT,
        related_name="asignaciones",
    )
    fecha_asignacion = models.DateField(default=timezone.now)
    observaciones_entrega = models.TextField(blank=True)
    usuario_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="asignaciones_registradas",
    )
    estado_asignacion = models.CharField(
        max_length=10,
        choices=EstadoAsignacion.choices,
        default=EstadoAsignacion.ACTIVA,
    )
    fecha_devolucion = models.DateField(null=True, blank=True)
    observaciones_devolucion = models.TextField(blank=True)
    usuario_recepcion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="devoluciones_registradas",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Asignación"
        verbose_name_plural = "Asignaciones"
        ordering = ["-fecha_asignacion", "-id"]

    def __str__(self):
        codigo = self.codigo_asignacion or "SIN-CODIGO"
        return f"{codigo} - {self.colaborador}"

    def clean(self):
        super().clean()

        if self.colaborador_id and self.colaborador.estado != Colaborador.EstadoColaborador.ACTIVO:
            raise ValidationError({"colaborador": "Solo se puede asignar a colaboradores activos."})

        if self.estado_asignacion == self.EstadoAsignacion.ACTIVA:
            if self.fecha_devolucion:
                raise ValidationError(
                    {"fecha_devolucion": "Una asignación activa no puede tener fecha de devolución."}
                )
            if self.usuario_recepcion_id:
                raise ValidationError(
                    {"usuario_recepcion": "Una asignación activa no debe tener usuario de recepción."}
                )
        elif self.estado_asignacion == self.EstadoAsignacion.CERRADA:
            if not self.fecha_devolucion:
                raise ValidationError({"fecha_devolucion": "Debes indicar la fecha de devolución."})
            if not self.usuario_recepcion_id:
                raise ValidationError(
                    {"usuario_recepcion": "Debes indicar el usuario que recibe los activos."}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        with transaction.atomic():
            super().save(*args, **kwargs)
            if not self.codigo_asignacion:
                anio = self.fecha_asignacion.year if self.fecha_asignacion else timezone.localdate().year
                codigo = f"ASG-{anio}-{self.pk:05d}"
                Asignacion.objects.filter(pk=self.pk).update(codigo_asignacion=codigo)
                self.codigo_asignacion = codigo

    @property
    def nombre_colaborador_completo(self):
        return f"{self.colaborador.nombres} {self.colaborador.apellidos}".strip()

    @property
    def total_activos(self):
        return self.detalles.count()

    @property
    def resumen_activos(self):
        codigos = [detalle.activo.codigo for detalle in self.detalles.select_related("activo")]
        return ", ".join(codigos) if codigos else "-"


class AsignacionDetalle(models.Model):
    asignacion = models.ForeignKey(
        Asignacion,
        on_delete=models.CASCADE,
        related_name="detalles",
    )
    activo = models.ForeignKey(
        Activo,
        on_delete=models.PROTECT,
        related_name="detalles_asignacion",
    )
    orden = models.PositiveIntegerField(default=1)
    observaciones_linea = models.TextField(blank=True)
    activa = models.BooleanField(default=True, db_index=True)
    estado_activo_devolucion = models.ForeignKey(
        EstadoActivo,
        on_delete=models.PROTECT,
        related_name="detalles_asignacion_cerrados",
        null=True,
        blank=True,
    )
    observaciones_devolucion = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Detalle de asignación"
        verbose_name_plural = "Detalles de asignación"
        ordering = ["orden", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["activo"],
                condition=Q(activa=True),
                name="unique_detalle_asignacion_activa_por_activo",
            ),
            models.UniqueConstraint(
                fields=["asignacion", "activo"],
                name="unique_activo_por_asignacion",
            ),
        ]

    def __str__(self):
        codigo = self.asignacion.codigo_asignacion or "SIN-CODIGO"
        return f"{codigo} - {self.activo.codigo}"

    def _obtener_estado_asignado(self):
        estado = EstadoActivo.objects.filter(nombre__iexact="Asignado").first()
        if not estado:
            raise ValidationError("Debe existir un estado de activo llamado 'Asignado'.")
        return estado

    def clean(self):
        super().clean()

        if self.activa:
            if self.activo_id and not self.activo.estado_activo.permite_asignacion:
                raise ValidationError({"activo": "El activo seleccionado no está disponible para asignación."})

            existe_otra_activa = AsignacionDetalle.objects.filter(activo_id=self.activo_id, activa=True)
            if self.pk:
                existe_otra_activa = existe_otra_activa.exclude(pk=self.pk)
            if existe_otra_activa.exists():
                raise ValidationError({"activo": "Este activo ya tiene una asignación activa."})

            if self.estado_activo_devolucion_id:
                raise ValidationError(
                    {"estado_activo_devolucion": "Un detalle activo no puede tener estado de devolución."}
                )
        else:
            if not self.estado_activo_devolucion_id:
                raise ValidationError(
                    {"estado_activo_devolucion": "Debes indicar el estado final del activo."}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        with transaction.atomic():
            super().save(*args, **kwargs)

            if self.activa:
                estado_asignado = self._obtener_estado_asignado()
                if self.activo.estado_activo_id != estado_asignado.id:
                    Activo.objects.filter(pk=self.activo_id).update(estado_activo=estado_asignado)
                    self.activo.estado_activo = estado_asignado
            elif self.estado_activo_devolucion_id:
                if self.activo.estado_activo_id != self.estado_activo_devolucion_id:
                    Activo.objects.filter(pk=self.activo_id).update(
                        estado_activo=self.estado_activo_devolucion
                    )
                    self.activo.estado_activo = self.estado_activo_devolucion

    @property
    def articulo_acta(self):
        if self.activo_id and self.activo.tipo_activo_id:
            return self.activo.tipo_activo.nombre
        return self.activo.codigo

    @property
    def caracteristicas_acta(self):
        partes = []
        if self.activo.modelo:
            partes.append(f"Modelo: {self.activo.modelo}")
        if self.activo.serie:
            partes.append(f"Serie: {self.activo.serie}")
        if self.activo.cpu:
            partes.append(f"CPU: {self.activo.cpu}")
        if self.activo.ram:
            partes.append(f"RAM: {self.activo.ram}")
        if self.activo.disco:
            partes.append(f"Disco: {self.activo.disco}")
        if self.activo.sistema_operativo:
            partes.append(f"SO: {self.activo.sistema_operativo}")
        return " | ".join(partes) if partes else "-"

    @property
    def observaciones_acta(self):
        partes = []
        if self.activo.observaciones:
            partes.append(self.activo.observaciones.strip())
        if self.observaciones_linea:
            partes.append(self.observaciones_linea.strip())
        if self.asignacion.observaciones_entrega:
            partes.append(self.asignacion.observaciones_entrega.strip())
        return " | ".join([p for p in partes if p]) or "-"

    @property
    def foto_principal(self):
        fotos = list(self.activo.fotos.all())
        return fotos[0] if fotos else None
