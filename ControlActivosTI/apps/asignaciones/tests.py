from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.activos.models import Activo
from apps.catalogos.models import Area, Cargo, EstadoActivo, TipoActivo, Ubicacion
from apps.colaboradores.models import Colaborador

from apps.asignaciones.forms import AsignacionCreateForm


class AsignacionCreateFormTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester",
            password="secret123",
        )
        self.area = Area.objects.create(nombre="TI")
        self.cargo = Cargo.objects.create(nombre="Analista")
        self.ubicacion = Ubicacion.objects.create(nombre="Matriz")
        self.tipo_activo = TipoActivo.objects.create(nombre="Laptop")
        self.estado_disponible = EstadoActivo.objects.create(
            nombre="Disponible",
            permite_asignacion=True,
        )
        self.estado_no_disponible = EstadoActivo.objects.create(
            nombre="Danado",
            permite_asignacion=False,
        )
        self.colaborador = Colaborador.objects.create(
            nombres="Ana",
            apellidos="Perez",
            cedula="0123456789",
            correo_corporativo="ana.perez@example.com",
            cargo=self.cargo,
            area=self.area,
            ubicacion=self.ubicacion,
            fecha_ingreso=date(2024, 1, 10),
        )
        self.activo_disponible = Activo.objects.create(
            tipo_activo=self.tipo_activo,
            marca="Dell",
            modelo="Latitude 5440",
            serie="ABC123",
            cpu="Intel Core i7",
            ram="16 GB",
            disco="512 GB SSD",
            sistema_operativo="Windows 11",
            estado_activo=self.estado_disponible,
        )
        self.activo_no_disponible = Activo.objects.create(
            tipo_activo=self.tipo_activo,
            marca="HP",
            modelo="ProBook",
            serie="XYZ999",
            estado_activo=self.estado_no_disponible,
        )

    def test_form_only_lists_assignable_assets(self):
        form = AsignacionCreateForm()

        queryset = form.fields["activos"].queryset

        self.assertIn(self.activo_disponible, queryset)
        self.assertNotIn(self.activo_no_disponible, queryset)

    def test_form_renders_detailed_asset_labels_and_filter_metadata(self):
        form = AsignacionCreateForm()
        rendered = str(form["activos"])

        self.assertIn(self.activo_disponible.codigo, rendered)
        self.assertIn("Laptop", rendered)
        self.assertIn("Dell Latitude 5440", rendered)
        self.assertIn("Serie: ABC123", rendered)
        self.assertIn("CPU: Intel Core i7", rendered)
        self.assertIn('data-search="', rendered)
        self.assertIn('data-especificaciones="CPU: Intel Core i7 | RAM: 16 GB | Disco: 512 GB SSD | SO: Windows 11"', rendered)

    def test_create_view_renders_asset_table_with_checkboxes(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("asignaciones:nueva"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Seleccionar visibles")
        self.assertContains(response, "Marca / Modelo")
        self.assertContains(response, 'type="checkbox"', html=False)
        self.assertContains(response, f'value="{self.activo_disponible.pk}"', html=False)
