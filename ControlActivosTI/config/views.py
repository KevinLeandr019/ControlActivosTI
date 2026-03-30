from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.activos.models import Activo
from apps.asignaciones.models import Asignacion
from apps.colaboradores.models import Colaborador


class InicioView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/inicio.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_activos"] = Activo.objects.count()
        context["total_colaboradores"] = Colaborador.objects.count()
        context["asignaciones_activas"] = Asignacion.objects.filter(
            estado_asignacion="ACTIVA"
        ).count()
        context["activos_disponibles"] = Activo.objects.filter(
            estado_activo__permite_asignacion=True
        ).count()
        return context