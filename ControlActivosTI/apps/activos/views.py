from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch, Q
from django.views.generic import DetailView, ListView

from apps.asignaciones.models import Asignacion

from .models import Activo, EventoActivo, FotoActivo


class ActivoListView(LoginRequiredMixin, ListView):
    model = Activo
    template_name = "activos/lista.html"
    context_object_name = "activos"
    paginate_by = 10

    COLUMNAS_DISPONIBLES = [
        ("codigo", "Código"),
        ("tipo_activo", "Tipo"),
        ("marca", "Marca"),
        ("modelo", "Modelo"),
        ("serie", "Serie"),
        ("cpu", "CPU"),
        ("ram", "RAM"),
        ("disco", "Disco"),
        ("sistema_operativo", "Sistema operativo"),
        ("fecha_compra", "Fecha de compra"),
        ("valor", "Valor"),
        ("estado_activo", "Estado"),
    ]

    COLUMNAS_POR_DEFECTO = [
        "codigo",
        "tipo_activo",
        "marca",
        "modelo",
        "serie",
        "estado_activo",
    ]

    def get_selected_columns(self):
        columnas_validas = {key for key, _ in self.COLUMNAS_DISPONIBLES}
        seleccionadas = [
            col for col in self.request.GET.getlist("cols")
            if col in columnas_validas
        ]
        return seleccionadas or self.COLUMNAS_POR_DEFECTO

    def get_queryset(self):
        queryset = (
            Activo.objects.select_related("tipo_activo", "estado_activo")
            .prefetch_related("fotos")
            .order_by("codigo")
        )

        busqueda = self.request.GET.get("q", "").strip()
        if busqueda:
            queryset = queryset.filter(
                Q(codigo__icontains=busqueda) |
                Q(marca__icontains=busqueda) |
                Q(modelo__icontains=busqueda) |
                Q(serie__icontains=busqueda)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["columnas_disponibles"] = self.COLUMNAS_DISPONIBLES
        context["columnas_seleccionadas"] = self.get_selected_columns()
        context["busqueda"] = self.request.GET.get("q", "").strip()
        return context


class ActivoDetailView(LoginRequiredMixin, DetailView):
    model = Activo
    template_name = "activos/detalle.html"
    context_object_name = "activo"

    def get_queryset(self):
        return (
            Activo.objects.select_related("tipo_activo", "estado_activo")
            .prefetch_related(
                Prefetch(
                    "fotos",
                    queryset=FotoActivo.objects.order_by("orden", "id"),
                ),
                Prefetch(
                    "eventos",
                    queryset=EventoActivo.objects.select_related(
                        "tipo_evento",
                        "usuario_responsable",
                    ).order_by("-fecha_evento", "-id"),
                ),
                Prefetch(
                    "asignaciones",
                    queryset=Asignacion.objects.select_related(
                        "colaborador",
                        "usuario_responsable",
                        "usuario_recepcion",
                        "estado_activo_devolucion",
                    ).order_by("-fecha_asignacion", "-id"),
                ),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        activo = self.object

        asignaciones = list(activo.asignaciones.all())
        context["asignacion_activa"] = next(
            (
                asignacion
                for asignacion in asignaciones
                if asignacion.estado_asignacion == Asignacion.EstadoAsignacion.ACTIVA
            ),
            None,
        )
        context["historial_asignaciones"] = asignaciones
        context["historial_eventos"] = list(activo.eventos.all())

        return context