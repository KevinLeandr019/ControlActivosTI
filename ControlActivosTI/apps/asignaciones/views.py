from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from apps.actas.services import generar_o_actualizar_acta

from .forms import (
    AsignacionCreateForm,
    AsignacionDevolucionForm,
    AsignacionDetalleDevolucionFormSet,
)
from .models import Asignacion


class AsignacionListView(LoginRequiredMixin, ListView):
    model = Asignacion
    template_name = "asignaciones/lista.html"
    context_object_name = "asignaciones"
    paginate_by = 10

    def get_queryset(self):
        return (
            Asignacion.objects.select_related(
                "colaborador",
                "usuario_responsable",
                "usuario_recepcion",
            )
            .prefetch_related(
                "detalles__activo__tipo_activo",
                "detalles__activo__estado_activo",
            )
            .order_by("-fecha_asignacion", "-id")
        )


class AsignacionCreateView(LoginRequiredMixin, CreateView):
    model = Asignacion
    form_class = AsignacionCreateForm
    template_name = "asignaciones/formulario.html"
    success_url = reverse_lazy("asignaciones:lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context["form"]
        activos_seleccionados = form["activos"].value() or []
        context["activos_disponibles"] = form.fields["activos"].queryset
        context["activos_seleccionados"] = [int(activo_id) for activo_id in activos_seleccionados]
        return context

    def form_valid(self, form):
        form.instance.usuario_responsable = self.request.user
        self.object = form.save()

        try:
            generar_o_actualizar_acta(self.object, self.request.user)
            messages.success(
                self.request,
                "La asignación fue creada correctamente y el acta fue generada.",
            )
        except Exception:
            messages.warning(
                self.request,
                "La asignación fue creada correctamente, pero el acta no pudo generarse todavía.",
            )

        return HttpResponseRedirect(self.get_success_url())


class AsignacionDevolucionView(LoginRequiredMixin, UpdateView):
    model = Asignacion
    form_class = AsignacionDevolucionForm
    template_name = "asignaciones/devolucion.html"
    success_url = reverse_lazy("asignaciones:lista")

    def get_queryset(self):
        return (
            Asignacion.objects.select_related(
                "colaborador",
                "usuario_responsable",
            )
            .prefetch_related(
                "detalles__activo__tipo_activo",
                "detalles__activo__estado_activo",
            )
            .filter(estado_asignacion=Asignacion.EstadoAsignacion.ACTIVA)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.method == "POST":
            context["formset"] = AsignacionDetalleDevolucionFormSet(
                self.request.POST,
                instance=self.object,
                prefix="detalles",
            )
        else:
            context["formset"] = AsignacionDetalleDevolucionFormSet(
                instance=self.object,
                prefix="detalles",
            )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        form.instance.estado_asignacion = Asignacion.EstadoAsignacion.CERRADA
        form.instance.usuario_recepcion = request.user
        formset = AsignacionDetalleDevolucionFormSet(
            request.POST,
            instance=self.object,
            prefix="detalles",
        )

        if form.is_valid() and formset.is_valid():
            return self.forms_valid(form, formset)
        return self.forms_invalid(form, formset)

    def forms_valid(self, form, formset):
        with transaction.atomic():
            asignacion = form.save(commit=False)
            asignacion.estado_asignacion = Asignacion.EstadoAsignacion.CERRADA
            asignacion.usuario_recepcion = self.request.user
            asignacion.save()

            for detalle_form in formset.forms:
                detalle = detalle_form.save(commit=False)
                detalle.asignacion = asignacion
                detalle.activa = False
                detalle.save()

        messages.success(self.request, "La devolución fue registrada correctamente.")
        return HttpResponseRedirect(self.get_success_url())

    def forms_invalid(self, form, formset):
        return self.render_to_response(self.get_context_data(form=form, formset=formset))
