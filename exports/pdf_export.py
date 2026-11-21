from io import BytesIO
from pathlib import Path
from datetime import datetime

from PIL import Image


LOGO_PATH = Path(__file__).with_name(
    "Logo bordado de Chilchota con torre y flores.png"
)


def load_logo_image():
    if not LOGO_PATH.is_file():
        raise FileNotFoundError(f"No se encontró el logo para los PDF: {LOGO_PATH}")

    with Image.open(LOGO_PATH) as source:
        image = source.convert("RGB")
        image.thumbnail((480, 320), Image.Resampling.LANCZOS)
        output = BytesIO()
        image.save(output, format="JPEG", quality=82, optimize=True)
    return output.getvalue(), image.width, image.height


def build_simple_pdf(lines, logo_image):
    def pdf_escape(value):
        value = str(value).encode("latin-1", "replace").decode("latin-1")
        return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    image_data, image_width, image_height = logo_image
    display_width = 96
    display_height = display_width * image_height / image_width
    display_x = (612 - display_width) / 2
    display_y = 756
    pages = [lines[index:index + 40] for index in range(0, len(lines), 40)]
    if not pages:
        pages = [[]]
    page_ids = [5 + 2 * index for index in range(len(pages))]
    content_ids = [page_id + 1 for page_id in page_ids]
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        (
            f"<< /Type /Pages /Kids [{' '.join(f'{page_id} 0 R' for page_id in page_ids)}] "
            f"/Count {len(pages)} >>"
        ).encode(),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        (
            f"<< /Type /XObject /Subtype /Image /Width {image_width} "
            f"/Height {image_height} /ColorSpace /DeviceRGB /BitsPerComponent 8 "
            f"/Filter /DCTDecode /Length {len(image_data)} >>\nstream\n"
        ).encode() + image_data + b"\nendstream",
    ]
    for page_id, content_id, page_lines in zip(page_ids, content_ids, pages):
        commands = [
            f"q {display_width:.2f} 0 0 {display_height:.2f} "
            f"{display_x:.2f} {display_y:.2f} cm /Im1 Do Q",
            "BT",
            "/F1 10 Tf",
            "50 700 Td",
            "14 TL",
        ]
        for index, line in enumerate(page_lines):
            if index:
                commands.append("T*")
            commands.append(f"({pdf_escape(line)}) Tj")
        commands.append("ET")
        stream = "\n".join(commands).encode("latin-1", "replace")
        objects.extend([
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] "
                f"/Resources << /Font << /F1 3 0 R >> "
                f"/XObject << /Im1 4 0 R >> >> /Contents {content_id} 0 R >>"
            ).encode(),
            b"<< /Length " + str(len(stream)).encode()
            + b" >>\nstream\n" + stream + b"\nendstream",
        ])
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode())
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects)+1}\n".encode())
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(
        f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\n"
        f"startxref\n{xref}\n%%EOF".encode()
    )
    return bytes(pdf)


def build_quote_pdfs(quote, margin_tiers):
    logo_image = load_logo_image()
    design_lines_internal = []
    design_lines_client = []
    for item in quote.get("disenos", []):
        description = (
            f"{item['codigo']} - {item['nombre'] or 'Diseno sin nombre'}"
        )
        design_lines_client.extend([
            f"{description} | {item['cantidad']} piezas",
            f"  Precio por pieza: ${item['price_unit']:,.2f} | "
            f"Subtotal: ${item['price_total']:,.2f}",
        ])
        design_lines_internal.extend([
            f"{description} | {item['cantidad']} piezas | "
            f"Margen: {item['margen_pct']:.2f}%",
            f"  Costo: ${item['cost_total']:,.2f} | "
            f"Precio unitario: ${item['price_unit']:,.2f} | "
            f"Subtotal: ${item['price_total']:,.2f}",
        ])
    internal_lines = [
        "COTIZACION INTERNA - BORDADOS",
        f"Folio: {quote['folio'] or 'Sin folio'}",
        f"Cliente: {quote['cliente'] or 'Sin especificar'}",
        f"Fecha de cotizacion: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Fecha estimada de entrega: {quote['fecha_entrega']}",
        f"Cantidad: {int(quote['cantidad'])} piezas",
        f"Margen aplicado al pedido: {quote['margen_pct']:.2f}%",
        "",
        "DISENOS COTIZADOS",
        *design_lines_internal,
        "",
        "MARGENES CONFIGURADOS",
    ]
    for _, tier in margin_tiers.iterrows():
        internal_lines.append(
            f"{int(tier['Desde piezas'])}-{int(tier['Hasta piezas'])} piezas: "
            f"{float(tier['Margen (%)']):.2f}%"
        )
    internal_lines.extend([
        "",
        "COSTOS TOTALES",
        f"Capacidad productiva combinada: ${quote['costo_capacidad_combinada_pedido']:,.2f}",
        f"Materiales directos: ${quote['materiales']:,.2f}",
        f"Otros costos directos: ${quote['otros_directos']:,.2f}",
        f"COSTO TOTAL: ${quote['costo_total']:,.2f}",
        f"Costo unitario base: ${quote['costo_unitario_base']:,.2f}",
        "",
        "RESULTADO DE VENTA",
        f"PRECIO DE VENTA POR PIEZA: ${quote['precio_unitario']:,.2f}",
        f"PRECIO TOTAL DEL PEDIDO: ${quote['precio_total']:,.2f}",
        "",
        f"Corridas: {quote['corridas']} | Minutos maquina: {quote['minutos_maquina']:.1f}",
        f"Minutos operador: {quote['minutos_operador']:.1f} | "
        f"Minutos-recurso: {quote['minutos_recurso_combinados']:.1f}",
        "",
        "Documento de control interno. No incluye IVA.",
    ])

    client_lines = [
        "COTIZACION - BORDADOS",
        f"Folio: {quote['folio'] or 'Sin folio'}",
        f"Cliente: {quote['cliente'] or 'Sin especificar'}",
        f"Fecha: {datetime.now().strftime('%Y-%m-%d')}",
        f"Fecha estimada de entrega: {quote['fecha_entrega']}",
        "",
        "DISENOS COTIZADOS",
        *design_lines_client,
        "",
        f"Cantidad total: {int(quote['cantidad'])} piezas",
        f"Precio promedio por pieza: ${quote['precio_unitario']:,.2f}",
        f"TOTAL DE LA COTIZACION: ${quote['precio_total']:,.2f}",
        "",
        "Precios expresados en pesos mexicanos. No incluye IVA.",
    ]
    return (
        build_simple_pdf(client_lines, logo_image),
        build_simple_pdf(internal_lines, logo_image),
    )
