from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.catalogos.models import Area, Cargo, Empresa, Ubicacion

from apps.colaboradores.models import Colaborador


User = get_user_model()


class ColaboradorListViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="rrhh", password="testpass123")
        self.area = Area.objects.create(nombre="TI")
        self.cargo = Cargo.objects.create(nombre="Soporte")
        self.ubicacion = Ubicacion.objects.create(nombre="Matriz")
        self.empresa_a = Empresa.objects.create(nombre="Andes Corp")
        self.empresa_b = Empresa.objects.create(nombre="Beta Tech")

        Colaborador.objects.create(
            nombres="Ana",
            apellidos="Zambrano",
            cedula="0102030405",
            correo_corporativo="ana@example.com",
            empresa=self.empresa_b,
            cargo=self.cargo,
            area=self.area,
            ubicacion=self.ubicacion,
            fecha_ingreso=date(2024, 1, 10),
        )
        Colaborador.objects.create(
            nombres="Luis",
            apellidos="Alvarez",
            cedula="0203040506",
            correo_corporativo="luis@example.com",
            empresa=self.empresa_a,
            cargo=self.cargo,
            area=self.area,
            ubicacion=self.ubicacion,
            fecha_ingreso=date(2024, 2, 15),
        )

    def test_list_view_shows_company_separators(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("colaboradores:lista"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Andes Corp")
        self.assertContains(response, "Beta Tech")
        self.assertContains(response, 'text-[11px] font-semibold uppercase')
        self.assertLess(
            response.content.decode().index("Andes Corp"),
            response.content.decode().index("Beta Tech"),
        )

    def test_table_colspan_matches_selected_columns_plus_action(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("colaboradores:lista"), {"cols": ["apellidos"]})

        self.assertEqual(response.context["total_columnas_tabla"], 2)
        self.assertContains(response, 'colspan="2"')
