from django.test import TestCase

from apps.catalogos.admin import CentroCostoAdminForm
from apps.catalogos.models import CentroCosto, DepartamentoEmpresa, Empresa


class DepartamentoEmpresaTests(TestCase):
    def setUp(self):
        self.empresa_ilsa = Empresa.objects.create(nombre="ILSA")
        self.empresa_grafa = Empresa.objects.create(nombre="GRAFA")

    def test_allows_same_department_name_in_different_companies(self):
        dep_ilsa = DepartamentoEmpresa.objects.create(
            empresa=self.empresa_ilsa,
            nombre="Sistemas",
        )
        dep_grafa = DepartamentoEmpresa.objects.create(
            empresa=self.empresa_grafa,
            nombre="Sistemas",
        )

        self.assertEqual(str(dep_ilsa), "ILSA - Sistemas")
        self.assertEqual(str(dep_grafa), "GRAFA - Sistemas")

    def test_centrocosto_can_group_multiple_departments_from_same_company(self):
        sistemas = DepartamentoEmpresa.objects.create(
            empresa=self.empresa_ilsa,
            nombre="Sistemas",
        )
        administracion = DepartamentoEmpresa.objects.create(
            empresa=self.empresa_ilsa,
            nombre="Administracion",
        )
        ceco = CentroCosto.objects.create(
            codigo="230100001",
            nombre="Sistemas Compartido",
            empresa=self.empresa_ilsa,
        )

        ceco.departamentos.add(sistemas, administracion)

        self.assertEqual(ceco.departamentos_resumen, "Administracion, Sistemas")
        self.assertEqual(
            list(ceco.departamentos.order_by("nombre").values_list("nombre", flat=True)),
            ["Administracion", "Sistemas"],
        )


class CentroCostoAdminFormTests(TestCase):
    def setUp(self):
        self.empresa_ilsa = Empresa.objects.create(nombre="ILSA")
        self.empresa_grafa = Empresa.objects.create(nombre="GRAFA")
        self.dep_ilsa = DepartamentoEmpresa.objects.create(
            empresa=self.empresa_ilsa,
            nombre="Sistemas",
        )
        self.dep_grafa = DepartamentoEmpresa.objects.create(
            empresa=self.empresa_grafa,
            nombre="Administracion",
        )

    def test_only_shows_departments_from_selected_company(self):
        form = CentroCostoAdminForm(data={"empresa": self.empresa_ilsa.pk})

        departamentos = list(form.fields["departamentos"].queryset)

        self.assertIn(self.dep_ilsa, departamentos)
        self.assertNotIn(self.dep_grafa, departamentos)

    def test_rejects_departments_from_another_company(self):
        form = CentroCostoAdminForm(
            data={
                "codigo": "230100010",
                "nombre": "CECO Compartido",
                "empresa": self.empresa_ilsa.pk,
                "tipo": CentroCosto.TipoCentroCosto.OPERATIVO,
                "departamentos": [self.dep_grafa.pk],
                "acepta_asignaciones": True,
                "activo": True,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("departamentos", form.errors)

    def test_accepts_departments_from_the_same_company(self):
        form = CentroCostoAdminForm(
            data={
                "codigo": "230100011",
                "nombre": "CECO Compartido",
                "empresa": self.empresa_ilsa.pk,
                "tipo": CentroCosto.TipoCentroCosto.OPERATIVO,
                "departamentos": [self.dep_ilsa.pk],
                "acepta_asignaciones": True,
                "activo": True,
            }
        )

        self.assertTrue(form.is_valid())
