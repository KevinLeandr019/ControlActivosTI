from decimal import Decimal
from io import BytesIO

from django.core.files.base import ContentFile

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from .models import ActaEntrega


def _texto(valor, default="-"):
    if valor is None:
        return default
    valor = str(valor).strip()
    return valor or default


def _moneda(valor):
    if valor in (None, ""):
        return "-"
    if isinstance(valor, Decimal):
        return f"USD {valor:,.2f}"
    try:
        return f"USD {Decimal(valor):,.2f}"
    except Exception:
        return _texto(valor)


def _caracteristicas(detalle):
    return detalle.caracteristicas_acta


def _observaciones(detalle):
    return detalle.observaciones_acta


def _nombre_archivo(asignacion):
    codigo = asignacion.codigo_asignacion or f"ASG-{asignacion.pk}"
    return f"acta_entrega_{codigo}.docx"


def construir_documento_acta(asignacion):
    document = Document()

    style = document.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)

    titulo = document.add_paragraph()
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = titulo.add_run("ACTA DE ENTREGA DE BIENES INFORMÁTICOS")
    run.bold = True
    run.font.size = Pt(14)

    subtitulo = document.add_paragraph()
    subtitulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitulo.add_run(f"Código de asignación: {_texto(asignacion.codigo_asignacion)}").bold = True

    document.add_paragraph()

    datos = [
        ("Fecha de suscripción", asignacion.fecha_asignacion.strftime("%d/%m/%Y")),
        ("Colaborador", asignacion.nombre_colaborador_completo),
        ("Cédula", _texto(asignacion.colaborador.cedula)),
        ("Cargo", _texto(asignacion.colaborador.cargo)),
        ("Área", _texto(asignacion.colaborador.area)),
        ("Empresa", _texto(asignacion.colaborador.empresa)),
        ("Ubicación", _texto(asignacion.colaborador.ubicacion)),
    ]

    tabla_datos = document.add_table(rows=0, cols=2)
    tabla_datos.style = "Table Grid"
    for etiqueta, valor in datos:
        row = tabla_datos.add_row().cells
        row[0].text = etiqueta
        row[1].text = _texto(valor)

    document.add_paragraph()
    document.add_paragraph(
        "Por medio de la presente se deja constancia de la entrega de los bienes "
        "informáticos detallados a continuación, los cuales quedan bajo custodia del colaborador."
    )

    document.add_paragraph()

    tabla = document.add_table(rows=1, cols=6)
    tabla.style = "Table Grid"
    encabezados = ["Artículo", "Marca", "Valor", "Estado", "Características", "Observaciones"]
    for idx, texto in enumerate(encabezados):
        tabla.rows[0].cells[idx].text = texto

    detalles = asignacion.detalles.select_related(
        "activo__tipo_activo",
        "activo__estado_activo",
    ).order_by("orden", "id")

    for detalle in detalles:
        row = tabla.add_row().cells
        row[0].text = _texto(detalle.articulo_acta)
        row[1].text = _texto(detalle.activo.marca)
        row[2].text = _moneda(detalle.activo.valor)
        row[3].text = _texto(detalle.activo.estado_activo.nombre)
        row[4].text = _caracteristicas(detalle)
        row[5].text = _observaciones(detalle)

    document.add_paragraph()
    document.add_paragraph(
        "El colaborador declara haber recibido los bienes descritos en buen estado y se compromete "
        "a su uso adecuado, custodia y devolución cuando corresponda."
    )

    document.add_paragraph()
    firmas = document.add_table(rows=2, cols=2)
    firmas.style = "Table Grid"
    firmas.cell(0, 0).text = "Entrega"
    firmas.cell(0, 1).text = "Recibe conforme"
    firmas.cell(1, 0).text = _texto(asignacion.usuario_responsable.get_full_name() or asignacion.usuario_responsable.username)
    firmas.cell(1, 1).text = (
        f"{_texto(asignacion.nombre_colaborador_completo)}\n"
        f"{_texto(asignacion.colaborador.cargo)}"
    )

    salida = BytesIO()
    document.save(salida)
    salida.seek(0)
    return salida.getvalue()


def generar_o_actualizar_acta(asignacion, usuario):
    contenido = construir_documento_acta(asignacion)
    nombre_archivo = _nombre_archivo(asignacion)

    acta, _ = ActaEntrega.objects.get_or_create(
        asignacion=asignacion,
        defaults={"usuario_generador": usuario},
    )
    acta.usuario_generador = usuario
    acta.nombre_archivo = nombre_archivo
    acta.archivo.save(nombre_archivo, ContentFile(contenido), save=False)
    acta.save()
    return acta
