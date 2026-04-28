from decimal import Decimal
from io import BytesIO

from django.core.files.base import ContentFile

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from .models import ActaEntrega


TIPO_ENTREGA = ActaEntrega.TipoActa.ENTREGA
TIPO_RECEPCION = ActaEntrega.TipoActa.RECEPCION


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


def _nombre_archivo(asignacion, tipo, devolucion=None):
    codigo = asignacion.codigo_asignacion or f"ASG-{asignacion.pk}"
    if devolucion:
        codigo = devolucion.codigo_devolucion or f"{codigo}-DEV-{devolucion.pk}"
    prefijo = "acta_recepcion" if tipo == TIPO_RECEPCION else "acta_entrega"
    return f"{prefijo}_{codigo}.docx"


def _fecha_acta(asignacion, tipo, devolucion=None):
    if devolucion:
        return devolucion.fecha_devolucion
    if tipo == TIPO_RECEPCION:
        return asignacion.fecha_devolucion or asignacion.fecha_asignacion
    return asignacion.fecha_asignacion


def _configuracion_acta(tipo):
    if tipo == TIPO_RECEPCION:
        return {
            "titulo": "ACTA DE RECEPCION DE BIENES INFORMATICOS",
            "intro": (
                "Por medio de la presente se deja constancia de la recepcion de los bienes "
                "informaticos detallados a continuacion, devueltos por el colaborador al area responsable."
            ),
            "declaracion": (
                "El area responsable declara haber recibido los bienes descritos y registra el estado "
                "final informado al momento de la devolucion."
            ),
            "firma_izquierda": "Entrega conforme",
            "firma_derecha": "Recibe",
        }
    return {
        "titulo": "ACTA DE ENTREGA DE BIENES INFORMATICOS",
        "intro": (
            "Por medio de la presente se deja constancia de la entrega de los bienes "
            "informaticos detallados a continuacion, los cuales quedan bajo custodia del colaborador."
        ),
        "declaracion": (
            "El colaborador declara haber recibido los bienes descritos en buen estado y se compromete "
            "a su uso adecuado, custodia y devolucion cuando corresponda."
        ),
        "firma_izquierda": "Entrega",
        "firma_derecha": "Recibe conforme",
    }


def _estado_detalle(detalle, tipo):
    if tipo == TIPO_RECEPCION and detalle.estado_activo_devolucion_id:
        return detalle.estado_activo_devolucion.nombre
    return detalle.activo.estado_activo.nombre


def _observaciones_detalle(detalle, tipo, devolucion_detalle=None):
    if devolucion_detalle:
        partes = []
        if devolucion_detalle.observaciones:
            partes.append(devolucion_detalle.observaciones.strip())
        if devolucion_detalle.devolucion.observaciones:
            partes.append(devolucion_detalle.devolucion.observaciones.strip())
        return " | ".join([parte for parte in partes if parte]) or "-"
    if tipo == TIPO_RECEPCION:
        partes = []
        if detalle.observaciones_devolucion:
            partes.append(detalle.observaciones_devolucion.strip())
        if detalle.asignacion.observaciones_devolucion:
            partes.append(detalle.asignacion.observaciones_devolucion.strip())
        return " | ".join([parte for parte in partes if parte]) or "-"
    return detalle.observaciones_acta


def _firmas(asignacion, tipo, devolucion=None):
    colaborador = f"{_texto(asignacion.nombre_colaborador_completo)}\n{_texto(asignacion.colaborador.cargo)}"
    responsable_entrega = _texto(
        asignacion.usuario_responsable.get_full_name() or asignacion.usuario_responsable.username
    )
    responsable_recepcion = responsable_entrega
    if devolucion:
        responsable_recepcion = _texto(
            devolucion.usuario_recepcion.get_full_name() or devolucion.usuario_recepcion.username
        )
    elif asignacion.usuario_recepcion_id:
        responsable_recepcion = _texto(
            asignacion.usuario_recepcion.get_full_name() or asignacion.usuario_recepcion.username
        )

    if tipo == TIPO_RECEPCION:
        return colaborador, responsable_recepcion
    return responsable_entrega, colaborador


def construir_documento_acta(asignacion, tipo=TIPO_ENTREGA, devolucion=None):
    config = _configuracion_acta(tipo)
    document = Document()

    style = document.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)

    titulo = document.add_paragraph()
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = titulo.add_run(config["titulo"])
    run.bold = True
    run.font.size = Pt(14)

    subtitulo = document.add_paragraph()
    subtitulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if devolucion:
        subtitulo.add_run(f"Codigo de devolucion: {_texto(devolucion.codigo_devolucion)}").bold = True
        referencia = document.add_paragraph()
        referencia.alignment = WD_ALIGN_PARAGRAPH.CENTER
        referencia.add_run(f"Asignacion original: {_texto(asignacion.codigo_asignacion)}")
    else:
        subtitulo.add_run(f"Codigo de asignacion: {_texto(asignacion.codigo_asignacion)}").bold = True

    document.add_paragraph()

    fecha_acta = _fecha_acta(asignacion, tipo, devolucion=devolucion)
    datos = [
        ("Fecha de suscripcion", fecha_acta.strftime("%d/%m/%Y")),
        ("Colaborador", asignacion.nombre_colaborador_completo),
        ("Cedula", _texto(asignacion.colaborador.cedula)),
        ("Cargo", _texto(asignacion.colaborador.cargo)),
        ("Area", _texto(asignacion.colaborador.area)),
        ("Empresa", _texto(asignacion.colaborador.empresa)),
        ("Ubicacion", _texto(asignacion.colaborador.ubicacion)),
    ]

    tabla_datos = document.add_table(rows=0, cols=2)
    tabla_datos.style = "Table Grid"
    for etiqueta, valor in datos:
        row = tabla_datos.add_row().cells
        row[0].text = etiqueta
        row[1].text = _texto(valor)

    document.add_paragraph()
    document.add_paragraph(config["intro"])

    document.add_paragraph()

    tabla = document.add_table(rows=1, cols=6)
    tabla.style = "Table Grid"
    encabezados = ["Articulo", "Marca", "Valor", "Estado", "Caracteristicas", "Observaciones"]
    for idx, texto in enumerate(encabezados):
        tabla.rows[0].cells[idx].text = texto

    if devolucion:
        detalles = devolucion.detalles.select_related(
            "detalle_asignacion__activo__tipo_activo",
            "detalle_asignacion__activo__estado_activo",
            "estado_activo_devolucion",
            "devolucion",
        ).order_by("detalle_asignacion__orden", "id")
    else:
        detalles = asignacion.detalles.select_related(
            "activo__tipo_activo",
            "activo__estado_activo",
            "estado_activo_devolucion",
        ).order_by("orden", "id")

    for item in detalles:
        detalle = item.detalle_asignacion if devolucion else item
        row = tabla.add_row().cells
        row[0].text = _texto(detalle.articulo_acta)
        row[1].text = _texto(detalle.activo.marca)
        row[2].text = _moneda(detalle.activo.valor)
        estado = item.estado_activo_devolucion.nombre if devolucion else _estado_detalle(detalle, tipo)
        row[3].text = _texto(estado)
        row[4].text = detalle.caracteristicas_acta
        row[5].text = _observaciones_detalle(detalle, tipo, devolucion_detalle=item if devolucion else None)

    document.add_paragraph()
    document.add_paragraph(config["declaracion"])

    document.add_paragraph()
    firmas = document.add_table(rows=2, cols=2)
    firmas.style = "Table Grid"
    firmas.cell(0, 0).text = config["firma_izquierda"]
    firmas.cell(0, 1).text = config["firma_derecha"]
    firma_izquierda, firma_derecha = _firmas(asignacion, tipo, devolucion=devolucion)
    firmas.cell(1, 0).text = firma_izquierda
    firmas.cell(1, 1).text = firma_derecha

    salida = BytesIO()
    document.save(salida)
    salida.seek(0)
    return salida.getvalue()


def generar_o_actualizar_acta(asignacion, usuario, tipo=TIPO_ENTREGA, devolucion=None):
    contenido = construir_documento_acta(asignacion, tipo=tipo, devolucion=devolucion)
    nombre_archivo = _nombre_archivo(asignacion, tipo, devolucion=devolucion)

    filtros = {"asignacion": asignacion, "tipo": tipo, "devolucion": devolucion}
    acta, _ = ActaEntrega.objects.get_or_create(
        **filtros,
        defaults={"usuario_generador": usuario},
    )
    acta.usuario_generador = usuario
    acta.nombre_archivo = nombre_archivo
    acta.archivo.save(nombre_archivo, ContentFile(contenido), save=False)
    acta.save()
    return acta


def generar_o_actualizar_actas_devolucion(devolucion, usuario):
    asignacion = devolucion.asignacion
    acta_entrega = ActaEntrega.objects.filter(
        asignacion=asignacion,
        tipo=TIPO_ENTREGA,
        devolucion__isnull=True,
        archivo__isnull=False,
    ).exclude(archivo="").first()
    if not acta_entrega:
        acta_entrega = generar_o_actualizar_acta(asignacion, usuario, tipo=TIPO_ENTREGA)
    acta_recepcion = generar_o_actualizar_acta(
        asignacion,
        usuario,
        tipo=TIPO_RECEPCION,
        devolucion=devolucion,
    )
    return acta_entrega, acta_recepcion
