from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404
from django.views import View

from .models import ActaEntrega


class DescargarActaPorAsignacionView(LoginRequiredMixin, View):
    def get(self, request, asignacion_id, *args, **kwargs):
        acta = (
            ActaEntrega.objects.select_related("asignacion")
            .filter(asignacion_id=asignacion_id)
            .first()
        )
        if not acta or not acta.archivo:
            raise Http404("No existe un acta generada para esta asignación.")

        archivo = acta.archivo.open("rb")
        nombre = acta.nombre_archivo or f"acta_{acta.asignacion.codigo_asignacion}.docx"
        return FileResponse(archivo, as_attachment=True, filename=nombre)
