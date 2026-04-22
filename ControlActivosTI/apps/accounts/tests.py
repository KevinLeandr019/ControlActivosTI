from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.activos.models import Activo
from apps.asignaciones.models import Asignacion, AsignacionDetalle
from apps.catalogos.models import Area, Cargo, EstadoActivo, TipoActivo, Ubicacion
from apps.colaboradores.models import Colaborador


class Admin2ViewsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="staffuser",
            password="secret123",
            is_staff=True,
        )
        self.area = Area.objects.create(nombre="TI")
        self.cargo = Cargo.objects.create(nombre="Analista")
        self.ubicacion = Ubicacion.objects.create(nombre="Matriz")
        self.tipo_activo = TipoActivo.objects.create(nombre="Laptop")
        self.estado_disponible = EstadoActivo.objects.create(
            nombre="Disponible",
            permite_asignacion=True,
        )
        self.estado_asignado = EstadoActivo.objects.create(
            nombre="Asignado",
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
        self.activo = Activo.objects.create(
            tipo_activo=self.tipo_activo,
            marca="Dell",
            modelo="Latitude 5440",
            serie="ABC123",
            estado_activo=self.estado_disponible,
        )
        self.asignacion = Asignacion.objects.create(
            colaborador=self.colaborador,
            fecha_asignacion=date(2026, 4, 20),
            usuario_responsable=self.user,
        )
        AsignacionDetalle.objects.create(
            asignacion=self.asignacion,
            activo=self.activo,
            orden=1,
        )

    def test_admin2_requires_staff_access(self):
        response = self.client.get(reverse("admin2-inicio"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_admin2_home_renders_real_operational_data(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("admin2-inicio"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Backoffice activo")
        self.assertContains(response, self.activo.codigo)
        self.assertContains(response, self.asignacion.codigo_asignacion)
        self.assertContains(response, "Activos registrados")

    def test_admin2_inventory_module_shows_asset_rows(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("admin2-inventario"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ultimos activos incorporados")
        self.assertContains(response, self.activo.codigo)
        self.assertContains(response, "Disponibles")

    def test_admin2_catalog_can_create_records(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("admin2-catalogo-crear", args=["areas"]),
            {
                "nombre": "Finanzas",
                "descripcion": "Area administrativa",
                "activo": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Area.objects.filter(nombre="Finanzas", activo=True).exists())
