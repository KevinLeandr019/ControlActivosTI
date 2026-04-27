from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch, Q
from django.views.generic import DetailView, ListView

from apps.activos.models import FotoActivo
from apps.asignaciones.models import Asignacion, AsignacionDetalle

from .models import Colaborador


class ColaboradorListView(LoginRequiredMixin, ListView):
    model = Colaborador
    template_name = "colaboradores/lista.html"
    context_object_name = "colaboradores"
    paginate_by = 10

    COLUMNAS_DISPONIBLES = [
        ("apellidos", "Apellidos"),
        ("nombres", "Nombres"),
        ("cedula", "Cédula"),
        ("correo_corporativo", "Correo"),
        ("empresa", "Empresa"),
        ("area", "Área"),
        ("cargo", "Cargo"),
        ("ubicacion", "Ubicación"),
        ("estado", "Estado"),
        ("fecha_ingreso", "Fecha de ingreso"),
    ]

    COLUMNAS_POR_DEFECTO = [
        "apellidos",
        "nombres",
        "cedula",
        "correo_corporativo",
        "empresa",
        "area",
        "cargo",
        "ubicacion",
        "estado",
    ]

    def get_selected_columns(self):
        columnas_validas = {key for key, _ in self.COLUMNAS_DISPONIBLES}
        seleccionadas = [
            col for col in self.request.GET.getlist("cols") if col in columnas_validas
        ]
        return seleccionadas or self.COLUMNAS_POR_DEFECTO

    def get_queryset(self):
        queryset = (
            Colaborador.objects.select_related("empresa", "area", "cargo", "ubicacion")
            .order_by("apellidos", "nombres")
        )

        busqueda = self.request.GET.get("q", "").strip()
        if busqueda:
            queryset = queryset.filter(
                Q(nombres__icontains=busqueda)
                | Q(apellidos__icontains=busqueda)
                | Q(cedula__icontains=busqueda)
                | Q(correo_corporativo__icontains=busqueda)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["columnas_disponibles"] = self.COLUMNAS_DISPONIBLES
        context["columnas_seleccionadas"] = self.get_selected_columns()
        context["busqueda"] = self.request.GET.get("q", "").strip()
        return context


class ColaboradorDetailView(LoginRequiredMixin, DetailView):
    model = Colaborador
    template_name = "colaboradores/detalle.html"
    context_object_name = "colaborador"

    def get_queryset(self):
        detalles_qs = (
            AsignacionDetalle.objects.select_related(
                "activo",
                "activo__tipo_activo",
                "activo__estado_activo",
                "estado_activo_devolucion",
            )
            .prefetch_related(
                Prefetch(
                    "activo__fotos",
                    queryset=FotoActivo.objects.order_by("orden", "id"),
                )
            )
            .order_by("orden", "id")
        )

        asignaciones_qs = (
            Asignacion.objects.select_related(
                "usuario_responsable",
                "usuario_recepcion",
            )
            .prefetch_related(Prefetch("detalles", queryset=detalles_qs))
            .order_by("-fecha_asignacion", "-id")
        )

        return (
            Colaborador.objects.select_related("empresa", "area", "cargo", "ubicacion")
            .prefetch_related(Prefetch("asignaciones", queryset=asignaciones_qs))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        colaborador = self.object
        asignaciones = list(colaborador.asignaciones.all())

        detalles_activos_actuales = []
        historial_detalles = []

        for asignacion in asignaciones:
            detalles = list(asignacion.detalles.all())
            historial_detalles.extend(detalles)

            if asignacion.estado_asignacion == Asignacion.EstadoAsignacion.ACTIVA:
                detalles_activos_actuales.extend(
                    [detalle for detalle in detalles if detalle.activa]
                )

        context["detalles_activos_actuales"] = detalles_activos_actuales
        context["historial_asignaciones"] = historial_detalles
        context["total_activos_asignados"] = len(detalles_activos_actuales)
        context["valor_total_activos_asignados"] = sum(
            (
                detalle.activo.valor or Decimal("0.00")
                for detalle in detalles_activos_actuales
            ),
            Decimal("0.00"),
        )
        context["puede_generar_acta"] = bool(detalles_activos_actuales)
        return context
