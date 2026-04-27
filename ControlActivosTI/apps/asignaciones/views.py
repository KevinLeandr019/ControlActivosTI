from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.dateparse import parse_date
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.actas.services import generar_o_actualizar_acta, generar_o_actualizar_actas_devolucion

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
    ORDENES_FECHA = {
        "recientes": ("-fecha_asignacion", "-id"),
        "antiguas": ("fecha_asignacion", "id"),
    }

    def get_queryset(self):
        queryset = (
            Asignacion.objects.select_related(
                "colaborador",
                "centro_costo",
                "usuario_responsable",
                "usuario_recepcion",
            )
            .prefetch_related(
                "actas",
                "detalles__activo__tipo_activo",
                "detalles__activo__estado_activo",
            )
        )

        busqueda = self.request.GET.get("q", "").strip()
        if busqueda:
            queryset = queryset.filter(
                Q(codigo_asignacion__icontains=busqueda)
                | Q(colaborador__nombres__icontains=busqueda)
                | Q(colaborador__apellidos__icontains=busqueda)
                | Q(colaborador__cedula__icontains=busqueda)
                | Q(detalles__activo__codigo__icontains=busqueda)
            )

        estado = self.request.GET.get("estado", "").strip()
        if estado in {
            Asignacion.EstadoAsignacion.ACTIVA,
            Asignacion.EstadoAsignacion.CERRADA,
        }:
            queryset = queryset.filter(estado_asignacion=estado)

        acta = self.request.GET.get("acta", "").strip()
        if acta == "con":
            queryset = queryset.filter(actas__isnull=False)
        elif acta == "sin":
            queryset = queryset.filter(actas__isnull=True)

        fecha_desde = parse_date(self.request.GET.get("fecha_desde", "").strip())
        if fecha_desde:
            queryset = queryset.filter(fecha_asignacion__gte=fecha_desde)

        fecha_hasta = parse_date(self.request.GET.get("fecha_hasta", "").strip())
        if fecha_hasta:
            queryset = queryset.filter(fecha_asignacion__lte=fecha_hasta)

        orden = self.request.GET.get("orden", "recientes").strip()
        campos_orden = self.ORDENES_FECHA.get(orden, self.ORDENES_FECHA["recientes"])

        return queryset.distinct().order_by(*campos_orden)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["busqueda"] = self.request.GET.get("q", "").strip()
        context["estado_seleccionado"] = self.request.GET.get("estado", "").strip()
        context["acta_seleccionada"] = self.request.GET.get("acta", "").strip()
        context["fecha_desde"] = self.request.GET.get("fecha_desde", "").strip()
        context["fecha_hasta"] = self.request.GET.get("fecha_hasta", "").strip()
        context["orden_seleccionado"] = self.request.GET.get("orden", "recientes").strip()
        return context
class AsignacionDetailView(LoginRequiredMixin, DetailView):
    model = Asignacion
    template_name = "asignaciones/detalle.html"
    context_object_name = "asignacion"

    def get_queryset(self):
        return (
            Asignacion.objects.select_related(
                "colaborador",
                "colaborador__empresa",
                "colaborador__area",
                "colaborador__cargo",
                "colaborador__ubicacion",
                "centro_costo",
                "usuario_responsable",
                "usuario_recepcion",
            )
            .prefetch_related(
                "actas",
                "detalles__activo__tipo_activo",
                "detalles__activo__estado_activo",
                "detalles__activo__fotos",
            )
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

            if not asignacion.actas.filter(tipo="ENTREGA").exclude(archivo="").exists():
                generar_o_actualizar_acta(asignacion, self.request.user)

            for detalle_form in formset.forms:
                detalle = detalle_form.save(commit=False)
                detalle.asignacion = asignacion
                detalle.activa = False
                detalle.save()

            generar_o_actualizar_actas_devolucion(asignacion, self.request.user)

        messages.success(self.request, "La devolución fue registrada correctamente.")
        return HttpResponseRedirect(self.get_success_url())

    def forms_invalid(self, form, formset):
        return self.render_to_response(self.get_context_data(form=form, formset=formset))
