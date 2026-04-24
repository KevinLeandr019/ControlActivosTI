from datetime import date
from pathlib import Path
import shutil
import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.utils import override_settings

from apps.activos.models import Activo
from apps.asignaciones.models import Asignacion, AsignacionDetalle
from apps.accounts.models import PerfilUsuario
from apps.catalogos.models import Area, Cargo, CentroCosto, EstadoActivo, TipoActivo, Ubicacion
from apps.colaboradores.models import Colaborador


def make_test_media_root():
    media_root = Path.cwd() / "test-media" / uuid.uuid4().hex
    media_root.mkdir(parents=True, exist_ok=True)
    return media_root


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
        self.ceco = CentroCosto.objects.create(
            codigo="TI001",
            nombre="Tecnologia",
            acepta_asignaciones=True,
            activo=True,
        )
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
            centro_costo=self.ceco,
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
        self.assertContains(response, "Lanzador administrativo")
        self.assertContains(response, "Usuarios")
        self.assertContains(response, "Activos")
        self.assertContains(response, "Asignaciones")
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

    def test_admin2_topbar_uses_profile_photo_when_available(self):
        media_root = make_test_media_root()
        try:
            with override_settings(MEDIA_ROOT=media_root):
                profile = PerfilUsuario.objects.create(
                    user=self.user,
                    foto=SimpleUploadedFile("staff-avatar.jpg", b"filecontent", content_type="image/jpeg"),
                )
                self.client.force_login(self.user)

                response = self.client.get(reverse("admin2-inicio"))
                profile.refresh_from_db()

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, profile.foto.url)
        finally:
            shutil.rmtree(media_root, ignore_errors=True)


class PerfilUsuarioViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="maria",
            password="secret123",
            first_name="Maria",
            last_name="Lopez",
            email="maria@example.com",
        )

    def test_profile_requires_login(self):
        response = self.client.get(reverse("accounts:perfil"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_profile_view_creates_profile_if_missing(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:perfil"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(PerfilUsuario.objects.filter(user=self.user).exists())
        self.assertContains(response, "Actualiza tu informacion basica")

    def test_profile_view_updates_basic_data(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:perfil"),
            {
                "first_name": "Maria Jose",
                "last_name": "Lopez Vera",
                "email": "mjose@example.com",
                "telefono": "0999999999",
                "cargo_visible": "Analista TI",
                "bio": "Encargada de soporte interno.",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        profile = PerfilUsuario.objects.get(user=self.user)
        self.assertEqual(self.user.first_name, "Maria Jose")
        self.assertEqual(self.user.last_name, "Lopez Vera")
        self.assertEqual(self.user.email, "mjose@example.com")
        self.assertEqual(profile.telefono, "0999999999")
        self.assertEqual(profile.cargo_visible, "Analista TI")
        self.assertEqual(profile.bio, "Encargada de soporte interno.")

    def test_profile_photo_is_available_in_shared_layouts(self):
        media_root = make_test_media_root()
        try:
            with override_settings(MEDIA_ROOT=media_root):
                profile = PerfilUsuario.objects.create(
                    user=self.user,
                    foto=SimpleUploadedFile("avatar.jpg", b"filecontent", content_type="image/jpeg"),
                )
                self.client.force_login(self.user)

                dashboard_response = self.client.get(reverse("dashboard-inicio"))
                profile.refresh_from_db()

                self.assertEqual(dashboard_response.status_code, 200)
                self.assertContains(dashboard_response, profile.foto.url)
        finally:
            shutil.rmtree(media_root, ignore_errors=True)
