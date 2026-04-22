from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.views.generic import TemplateView

from apps.activos.models import Activo
from apps.asignaciones.models import Asignacion
from apps.colaboradores.models import Colaborador


class InicioView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/inicio.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        total_activos = Activo.objects.count()
        total_colaboradores = Colaborador.objects.count()
        total_colaboradores_activos = Colaborador.objects.filter(
            estado=Colaborador.EstadoColaborador.ACTIVO
        ).count()
        asignaciones_activas = Asignacion.objects.filter(
            estado_asignacion=Asignacion.EstadoAsignacion.ACTIVA
        ).count()
        activos_disponibles = Activo.objects.filter(
            estado_activo__permite_asignacion=True
        ).count()
        activos_asignados = Activo.objects.filter(
            estado_activo__nombre__iexact="Asignado"
        ).count()
        valor_total_activos = Activo.objects.aggregate(total=Sum("valor")).get("total") or 0

        activos_por_estado = list(
            Activo.objects.values("estado_activo__nombre")
            .annotate(total=Count("id"))
            .order_by("-total", "estado_activo__nombre")
        )
        activos_por_tipo = list(
            Activo.objects.values("tipo_activo__nombre")
            .annotate(total=Count("id"))
            .order_by("-total", "tipo_activo__nombre")[:8]
        )
        asignaciones_por_mes = list(
            Asignacion.objects.annotate(mes=TruncMonth("fecha_asignacion"))
            .values("mes")
            .annotate(total=Count("id"))
            .order_by("mes")
        )
        colaboradores_por_area = list(
            Colaborador.objects.values("area__nombre")
            .annotate(total=Count("id"))
            .order_by("-total", "area__nombre")[:8]
        )

        ultimas_asignaciones = (
            Asignacion.objects.select_related(
                "colaborador",
                "usuario_responsable",
            )
            .prefetch_related("detalles__activo")
            .order_by("-fecha_asignacion", "-id")[:5]
        )

        alertas = [
            {
                "titulo": "Activos listos para asignacion",
                "valor": activos_disponibles,
                "tono": "emerald",
                "detalle": "Equipos que pueden entregarse de inmediato.",
            },
            {
                "titulo": "Activos actualmente asignados",
                "valor": activos_asignados,
                "tono": "cyan",
                "detalle": "Inventario que ya esta en manos de colaboradores.",
            },
            {
                "titulo": "Colaboradores no activos",
                "valor": total_colaboradores - total_colaboradores_activos,
                "tono": "amber",
                "detalle": "Registros para revisar antes de nuevas asignaciones.",
            },
            {
                "titulo": "Asignaciones activas",
                "valor": asignaciones_activas,
                "tono": "rose",
                "detalle": "Procesos abiertos pendientes de devolucion o seguimiento.",
            },
        ]

        context.update(
            {
                "total_activos": total_activos,
                "total_colaboradores": total_colaboradores,
                "total_colaboradores_activos": total_colaboradores_activos,
                "asignaciones_activas": asignaciones_activas,
                "activos_disponibles": activos_disponibles,
                "activos_asignados": activos_asignados,
                "valor_total_activos": valor_total_activos,
                "ultimas_asignaciones": ultimas_asignaciones,
                "alertas": alertas,
                "activos_estado_labels": [
                    item["estado_activo__nombre"] for item in activos_por_estado
                ],
                "activos_estado_data": [item["total"] for item in activos_por_estado],
                "activos_tipo_labels": [
                    item["tipo_activo__nombre"] for item in activos_por_tipo
                ],
                "activos_tipo_data": [item["total"] for item in activos_por_tipo],
                "asignaciones_mes_labels": [
                    item["mes"].strftime("%b %Y") for item in asignaciones_por_mes if item["mes"]
                ],
                "asignaciones_mes_data": [
                    item["total"] for item in asignaciones_por_mes if item["mes"]
                ],
                "colaboradores_area_labels": [
                    item["area__nombre"] for item in colaboradores_por_area
                ],
                "colaboradores_area_data": [
                    item["total"] for item in colaboradores_por_area
                ],
            }
        )
        return context
