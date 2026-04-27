from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404
from django.views import View

from .models import ActaEntrega


class DescargarActaPorAsignacionView(LoginRequiredMixin, View):
    def get(self, request, asignacion_id, tipo, *args, **kwargs):
        tipo = tipo.upper()
        if tipo not in ActaEntrega.TipoActa.values:
            raise Http404("Tipo de acta no valido.")

        acta = (
            ActaEntrega.objects.select_related("asignacion")
            .filter(asignacion_id=asignacion_id, tipo=tipo)
            .first()
        )
        if not acta or not acta.archivo:
            raise Http404("No existe un acta generada para esta asignacion.")

        archivo = acta.archivo.open("rb")
        nombre = acta.nombre_archivo or f"acta_{acta.asignacion.codigo_asignacion}.docx"
        return FileResponse(archivo, as_attachment=True, filename=nombre)
