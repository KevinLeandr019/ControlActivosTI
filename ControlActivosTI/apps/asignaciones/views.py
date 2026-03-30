from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from .forms import AsignacionCreateForm, AsignacionDevolucionForm
from .models import Asignacion


class AsignacionListView(LoginRequiredMixin, ListView):
    model = Asignacion
    template_name = "asignaciones/lista.html"
    context_object_name = "asignaciones"
    paginate_by = 10

    def get_queryset(self):
        return (
            Asignacion.objects.select_related(
                "activo",
                "colaborador",
                "usuario_responsable",
                "usuario_recepcion",
                "estado_activo_devolucion",
            )
            .order_by("-fecha_asignacion", "-id")
        )


class AsignacionCreateView(LoginRequiredMixin, CreateView):
    model = Asignacion
    form_class = AsignacionCreateForm
    template_name = "asignaciones/formulario.html"
    success_url = reverse_lazy("asignaciones:lista")

    def form_valid(self, form):
        form.instance.usuario_responsable = self.request.user
        messages.success(self.request, "La asignación fue creada correctamente.")
        return super().form_valid(form)


class AsignacionDevolucionView(LoginRequiredMixin, UpdateView):
    model = Asignacion
    form_class = AsignacionDevolucionForm
    template_name = "asignaciones/devolucion.html"
    success_url = reverse_lazy("asignaciones:lista")

    def get_queryset(self):
        return Asignacion.objects.select_related(
            "activo",
            "colaborador",
            "usuario_responsable",
        ).filter(
            estado_asignacion=Asignacion.EstadoAsignacion.ACTIVA
        )

    def form_valid(self, form):
        asignacion = form.save(commit=False)
        asignacion.estado_asignacion = Asignacion.EstadoAsignacion.CERRADA
        asignacion.usuario_recepcion = self.request.user
        asignacion.save()

        messages.success(self.request, "La devolución fue registrada correctamente.")
        return super().form_valid(form)