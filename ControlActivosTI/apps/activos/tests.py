from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.catalogos.models import EstadoActivo, TipoActivo, TipoEventoActivo

from apps.activos.admin import ActivoAdminForm, EventoActivoAdminForm, FotoActivoInlineForm
from apps.activos.models import Activo, EventoActivo, FotoActivo


User = get_user_model()


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


class EventoActivoAdminFormTests(TestCase):
    def test_labels_aclaran_valor_tecnico_y_costo(self):
        form = EventoActivoAdminForm()

        self.assertEqual(
            form.fields["valor_nuevo"].label,
            "Nuevo valor final del dato seleccionado",
        )
        self.assertIn("No es el precio", form.fields["valor_nuevo"].help_text)
        self.assertEqual(
            form.fields["costo_adicional"].label,
            "Costo del repuesto o mejora",
        )


class EventoActivoImpactoTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username="soporte", password="testpass123")
        self.estado_disponible = EstadoActivo.objects.create(
            nombre="Disponible",
            permite_asignacion=True,
        )
        self.estado_mantenimiento = EstadoActivo.objects.create(
            nombre="Mantenimiento",
            permite_asignacion=False,
        )
        self.tipo_laptop = TipoActivo.objects.create(nombre="Laptop")
        self.tipo_mouse = TipoActivo.objects.create(nombre="Mouse")
        self.tipo_evento = TipoEventoActivo.objects.create(nombre="Cambio de RAM")
        self.tipo_mantenimiento = TipoEventoActivo.objects.create(nombre="Mantenimiento")

    def test_evento_tecnico_actualiza_ram_y_suma_valor(self):
        activo = Activo.objects.create(
            tipo_activo=self.tipo_laptop,
            marca="Dell",
            modelo="Latitude",
            serie="ABC123",
            ram="8 GB",
            valor=Decimal("500.00"),
            estado_activo=self.estado_disponible,
        )

        evento = EventoActivo.objects.create(
            activo=activo,
            tipo_evento=self.tipo_evento,
            detalle="Se instala modulo adicional de memoria.",
            campo_afectado=EventoActivo.CampoAfectado.RAM,
            valor_nuevo="16 GB",
            costo_adicional=Decimal("40.00"),
            sumar_costo_al_valor=True,
            usuario_responsable=self.usuario,
        )

        activo.refresh_from_db()
        evento.refresh_from_db()

        self.assertEqual(evento.valor_anterior, "8 GB")
        self.assertEqual(activo.ram, "16 GB")
        self.assertEqual(activo.valor, Decimal("540.00"))

    def test_evento_puede_actualizar_estado_del_activo(self):
        activo = Activo.objects.create(
            tipo_activo=self.tipo_laptop,
            marca="HP",
            modelo="ProBook",
            serie="DEF456",
            ram="8 GB",
            estado_activo=self.estado_disponible,
        )

        EventoActivo.objects.create(
            activo=activo,
            tipo_evento=self.tipo_mantenimiento,
            detalle="Equipo pasa a revision preventiva.",
            nuevo_estado_activo=self.estado_mantenimiento,
            usuario_responsable=self.usuario,
        )

        activo.refresh_from_db()

        self.assertEqual(activo.estado_activo, self.estado_mantenimiento)

    def test_evento_informativo_no_modifica_ficha_del_activo(self):
        activo = Activo.objects.create(
            tipo_activo=self.tipo_laptop,
            marca="Lenovo",
            modelo="ThinkPad",
            serie="GHI789",
            ram="8 GB",
            valor=Decimal("600.00"),
            estado_activo=self.estado_disponible,
        )

        EventoActivo.objects.create(
            activo=activo,
            tipo_evento=self.tipo_mantenimiento,
            detalle="Limpieza general sin cambio de componentes.",
            usuario_responsable=self.usuario,
        )

        activo.refresh_from_db()

        self.assertEqual(activo.ram, "8 GB")
        self.assertEqual(activo.valor, Decimal("600.00"))

    def test_no_permite_evento_tecnico_en_activo_sin_especificaciones(self):
        activo = Activo.objects.create(
            tipo_activo=self.tipo_mouse,
            marca="Logitech",
            modelo="MX",
            serie="S/N",
            estado_activo=self.estado_disponible,
        )

        evento = EventoActivo(
            activo=activo,
            tipo_evento=self.tipo_evento,
            detalle="Intento de cambio tecnico no aplicable.",
            campo_afectado=EventoActivo.CampoAfectado.RAM,
            valor_nuevo="16 GB",
            usuario_responsable=self.usuario,
        )

        with self.assertRaises(ValidationError):
            evento.full_clean()


class ActivoListViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="inventario", password="testpass123")
        self.estado = EstadoActivo.objects.create(nombre="Disponible", permite_asignacion=True)
        self.tipo_laptop = TipoActivo.objects.create(nombre="Laptop")
        self.tipo_mouse = TipoActivo.objects.create(nombre="Mouse")

        Activo.objects.create(
            tipo_activo=self.tipo_mouse,
            marca="Logitech",
            modelo="M185",
            serie="MOU-001",
            estado_activo=self.estado,
        )
        Activo.objects.create(
            tipo_activo=self.tipo_laptop,
            marca="Dell",
            modelo="Latitude",
            serie="LAP-001",
            estado_activo=self.estado,
        )

    def test_list_view_shows_type_separators(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("activos:lista"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Laptop")
        self.assertContains(response, "Mouse")
        self.assertContains(response, 'text-[11px] font-semibold uppercase')
