from django.test import TestCase

from apps.catalogos.models import EstadoActivo, TipoActivo

from apps.activos.admin import ActivoAdminForm, FotoActivoInlineForm
from apps.activos.models import Activo, FotoActivo


class ActivoAdminFormTests(TestCase):
    def setUp(self):
        self.estado = EstadoActivo.objects.create(nombre="Disponible", permite_asignacion=True)
        self.tipo_mouse = TipoActivo.objects.create(nombre="Mouse")
        self.tipo_laptop = TipoActivo.objects.create(nombre="Laptop")

    def _data_base(self, tipo_activo):
        return {
            "tipo_activo": tipo_activo.pk,
            "marca": "Logitech",
            "modelo": "MX",
            "serie": "S/N",
            "cpu": "Intel Core i5",
            "ram": "16 GB",
            "disco": "512 GB SSD",
            "sistema_operativo": "Windows",
            "fecha_compra": "",
            "valor": "",
            "estado_activo": self.estado.pk,
            "observaciones": "",
        }

    def test_limpia_especificaciones_tecnicas_si_no_aplican_al_tipo(self):
        form = ActivoAdminForm(data=self._data_base(self.tipo_mouse))

        self.assertTrue(form.is_valid(), form.errors)
        activo = form.save()

        self.assertEqual(activo.cpu, "")
        self.assertEqual(activo.ram, "")
        self.assertEqual(activo.disco, "")
        self.assertEqual(activo.sistema_operativo, "")

    def test_conserva_especificaciones_tecnicas_para_laptops(self):
        form = ActivoAdminForm(data=self._data_base(self.tipo_laptop))

        self.assertTrue(form.is_valid(), form.errors)
        activo = form.save()

        self.assertEqual(activo.cpu, "Intel Core i5")
        self.assertEqual(activo.ram, "16 GB")
        self.assertEqual(activo.disco, "512 GB SSD")
        self.assertEqual(activo.sistema_operativo, "Windows")


class FotoActivoInlineFormTests(TestCase):
    def test_conserva_imagen_existente_si_no_se_sube_otra(self):
        estado = EstadoActivo.objects.create(nombre="Disponible", permite_asignacion=True)
        tipo_mouse = TipoActivo.objects.create(nombre="Mouse")
        activo = Activo.objects.create(
            tipo_activo=tipo_mouse,
            marca="Logitech",
            modelo="MX",
            serie="S/N",
            estado_activo=estado,
        )
        foto = FotoActivo.objects.create(
            activo=activo,
            imagen="activos/MOU-0001/mouse.jpg",
            descripcion="Foto frontal",
            orden=1,
        )

        form = FotoActivoInlineForm(
            data={
                "activo": activo.pk,
                "descripcion": "Foto actualizada",
                "orden": 1,
            },
            instance=foto,
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["imagen"], foto.imagen)
