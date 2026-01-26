import os
from datetime import datetime, date
from io import BytesIO
from flask import Blueprint, send_file, current_app, jsonify, request
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
from app.models.sale import Sale
from app.models.customer import Customer

pdf_bp = Blueprint("pdf", __name__, url_prefix="/pdf")


def get_image_paths():
    """Retorna paths de las imágenes"""
    static_path = os.path.abspath(
        os.path.join(current_app.root_path, '..', 'static', 'images')
    )
    return {
        'logo': os.path.join(static_path, 'logo.png'),
        'phone': os.path.join(static_path, 'phone.png'),
        'email': os.path.join(static_path, 'mail.png')
    }


def draw_header(c, width, height, sale_id, images):
    """Dibuja el header común (logo, contacto, número)"""
    # Número de venta
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, height - 6*mm, f"VENTA Nº{sale_id}000")
    
    # Logo
    try:
        if os.path.exists(images['logo']):
            logo = ImageReader(images['logo'])
            c.drawImage(
                logo, 
                (width - 50*mm)/2, 
                height - 50*mm,
                width=50*mm, 
                height=50*mm,
                preserveAspectRatio=True, 
                mask='auto'
            )
    except Exception as e:
        print(f"Error cargando logo: {e}")
    
    # Contacto
    icon_size = 4 * mm
    line_y = height - 55*mm
    
    c.setFont("Helvetica", 8)
    
    if os.path.exists(images['phone']):
        c.drawImage(
            ImageReader(images['phone']),
            width/2 - 45*mm,
            line_y,
            width=icon_size,
            height=icon_size,
            mask='auto'
        )
    c.drawString(width/2 - 40*mm, line_y, "011-32651073")
    
    if os.path.exists(images['email']):
        c.drawImage(
            ImageReader(images['email']),
            width/2 - 5*mm,
            line_y,
            width=icon_size,
            height=icon_size,
            mask='auto'
        )
    c.drawString(width/2 + 0*mm, line_y, "lunitavalropa@gmail.com")
    
    # Línea divisoria
    c.line(5*mm, height - 60*mm, width - 5*mm, height - 60*mm)


def draw_change_badge(c, width, y):
    """🔹 Dibuja badge de CAMBIO si corresponde"""
    c.setFillColor(HexColor('#F59E0B'))
    c.rect(5*mm, y - 10*mm, width - 10*mm, 10*mm, fill=1, stroke=0)
    
    c.setFillColor(HexColor('#000000'))
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, y - 7*mm, "🔄 ES UN CAMBIO")
    
    c.setFillColor(HexColor('#000000'))
    return y - 15*mm


def draw_customer_info(c, customer, y_start):
    """Dibuja información del cliente"""
    y = y_start
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(5*mm, y, "Cliente:")
    c.setFont("Helvetica", 9)
    c.drawString(5*mm + 25*mm, y, f"{customer.first_name} {customer.last_name}")
    y -= 6*mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(5*mm, y, "Localidad:")
    c.setFont("Helvetica", 9)
    c.drawString(5*mm + 25*mm, y, f"{customer.city}")
    y -= 6*mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(5*mm, y, "Dirección:")
    c.setFont("Helvetica", 9)
    c.drawString(5*mm + 25*mm, y, f"{customer.address}")
    y -= 6*mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(5*mm, y, "Teléfono:")
    c.setFont("Helvetica", 9)
    c.drawString(5*mm + 25*mm, y, f"{customer.phone}")
    y -= 6*mm

    if getattr(customer, 'description', None):
        c.setFont("Helvetica-Bold", 10)
        c.drawString(5*mm, y, "Descripción:")
        c.setFont("Helvetica", 9)
        c.drawString(5*mm + 25*mm, y, f"{customer.description}")
        y -= 6*mm

    return y


def draw_cadeteria_label(c, sale, customer, width, height, images):
    """Etiqueta para CADETERÍA"""
    draw_header(c, width, height, sale.id, images)
    
    y = height - 65*mm
    
    # 🔹 Badge de CAMBIO si corresponde
    if sale.has_change:
        y = draw_change_badge(c, width, y)
    
    # Info del cliente
    y = draw_customer_info(c, customer, y)
    
    # Fecha
    c.setFont("Helvetica-Bold", 10)
    c.drawString(5*mm, y, "Fecha:")
    c.setFont("Helvetica", 9)
    c.drawString(5*mm + 25*mm, y, sale.created_at.strftime("%d/%m/%Y"))
    y -= 8*mm

    # Línea divisoria
    c.line(5*mm, y, width - 5*mm, y)
    y -= 5*mm

    # Total
    c.setFont("Helvetica-Bold", 14)
    total_formatted = f"{sale.amount:,.0f}".replace(",", ".")
    c.drawCentredString(width/2, y, f"Total: ${total_formatted}")
    y -= 10*mm
    
    # Indicador de pago
    if not sale.paid:
        c.setFillColor(HexColor('#B91C1C'))
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(width/2, y, "⚠️ PENDIENTE DE PAGO")
        c.setFillColor(HexColor('#000000'))
        y -= 8*mm
    else:
        y -= 5*mm
    
    # Recuadro de notas
    notes_height = 25*mm
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1)
    c.rect(5*mm, y - notes_height, width - 10*mm, notes_height, stroke=1, fill=0)

    c.setFont("Helvetica", 9)
    text_y = y - 4*mm
    if sale.notes:
        lines = sale.notes.split('\n')
        for line in lines:
            if text_y > (y - notes_height + 2*mm):
                c.drawString(7*mm, text_y, line[:60])
                text_y -= 4*mm


def draw_retiro_label(c, sale, customer, width, height, images):
    """Etiqueta para RETIRO"""
    # Banner RETIRO
    c.setFillColor(HexColor('#4A90E2'))
    c.rect(0, height - 35*mm, width, 25*mm, fill=1, stroke=0)
    
    c.setFillColor(HexColor('#FFFFFF'))
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(width/2, height - 25*mm, "RETIRO")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height - 32*mm, f"Venta #{sale.id}000")
    
    c.setFillColor(HexColor('#000000'))
    
    # Logo
    try:
        if os.path.exists(images['logo']):
            logo = ImageReader(images['logo'])
            c.drawImage(
                logo,
                (width - 35*mm)/2,
                height - 68*mm,
                width=35*mm,
                height=35*mm,
                preserveAspectRatio=True,
                mask='auto'
            )
    except:
        pass
    
    y = height - 75*mm
    
    # 🔹 Badge de CAMBIO
    if sale.has_change:
        y = draw_change_badge(c, width, y)
    
    # Info cliente
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, y, f"{customer.first_name} {customer.last_name}")
    y -= 10*mm
    
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, y, f"Tel: {customer.phone}")
    y -= 15*mm
    
    # Total
    c.setFont("Helvetica-Bold", 24)
    total_formatted = f"{sale.amount:,.0f}".replace(",", ".")
    c.drawCentredString(width/2, y, f"$ {total_formatted}")
    y -= 10*mm
    
    # Fecha
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2, y, f"Fecha: {sale.created_at.strftime('%d/%m/%Y')}")
    y -= 10*mm
    
    # Advertencia
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(HexColor('#B91C1C'))
    c.drawCentredString(width/2, y, "⚠️ Válido 15 días desde la fecha de venta")
    c.setFillColor(HexColor('#000000'))
    y -= 15*mm

    if not sale.paid:
        c.setFillColor(HexColor('#B91C1C'))
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(width/2, y, "⚠️ PENDIENTE DE PAGO")
        c.setFillColor(HexColor('#000000'))
    
    # Notas
    if sale.notes:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(5*mm, y, "Notas:")
        y -= 5*mm
        
        c.setFont("Helvetica", 9)
        lines = sale.notes.split('\n')
        for line in lines[:3]:
            c.drawString(5*mm, y, line[:80])
            y -= 4*mm


def draw_correo_label(c, sale, customer, width, height, images):
    """Etiqueta para CORREO"""
    # Banner CORREO
    c.setFillColor(HexColor('#F59E0B'))
    c.rect(0, height - 35*mm, width, 25*mm, fill=1, stroke=0)
    
    c.setFillColor(HexColor('#000000'))
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(width/2, height - 25*mm, "CORREO")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height - 32*mm, f"Venta #{sale.id}000")
    
    c.setFillColor(HexColor('#000000'))
    
    # Logo
    try:
        if os.path.exists(images['logo']):
            logo = ImageReader(images['logo'])
            c.drawImage(
                logo,
                5*mm,
                height - 60*mm,
                width=25*mm,
                height=25*mm,
                preserveAspectRatio=True,
                mask='auto'
            )
    except:
        pass
    
    y = height - 70*mm
    
    # 🔹 Badge de CAMBIO
    if sale.has_change:
        y = draw_change_badge(c, width, y)
    
    # Dirección de envío
    c.setFont("Helvetica-Bold", 14)
    c.drawString(5*mm, y, "ENVIAR A:")
    y -= 8*mm
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(5*mm, y, f"{customer.first_name} {customer.last_name}")
    y -= 8*mm
    
    c.setFont("Helvetica", 12)
    c.drawString(5*mm, y, f"{customer.address}")
    y -= 6*mm
    
    c.drawString(5*mm, y, f"{customer.city}")
    y -= 6*mm
    
    c.drawString(5*mm, y, f"Tel: {customer.phone}")
    y -= 12*mm
    
    # Total
    c.setFont("Helvetica-Bold", 18)
    total_formatted = f"{sale.amount:,.0f}".replace(",", ".")
    c.drawString(5*mm, y, f"Total: $ {total_formatted}")
    y -= 8*mm
    
    # Indicador de pago
    if not sale.paid:
        c.setFillColor(HexColor('#B91C1C'))
        c.setFont("Helvetica-Bold", 12)
        c.drawString(5*mm, y, "⚠️ PENDIENTE DE PAGO")
        c.setFillColor(HexColor('#000000'))
        y -= 8*mm
    
    # Fecha
    c.setFont("Helvetica", 10)
    c.drawString(5*mm, y, f"Fecha: {sale.created_at.strftime('%d/%m/%Y')}")
    y -= 12*mm
    
    # Recuadro de descripción
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1)
    c.rect(5*mm, y - 20*mm, width - 10*mm, 20*mm, stroke=1, fill=0)
    
    c.setFont("Helvetica-Bold", 9)
    c.drawString(7*mm, y - 4*mm, "Descripción / Notas:")
    
    if sale.notes:
        c.setFont("Helvetica", 8)
        text_y = y - 8*mm
        lines = sale.notes.split('\n')
        for line in lines[:2]:
            c.drawString(7*mm, text_y, line[:70])
            text_y -= 4*mm


@pdf_bp.get("/sale/<int:sale_id>/label")
def download_sale_label(sale_id):
    """Genera etiqueta según tipo de entrega"""
    sale = Sale.query.get(sale_id)
    if not sale:
        return jsonify({"error": "Venta no encontrada"}), 404

    customer = Customer.query.get(sale.customer_id)
    if not customer:
        return jsonify({"error": "Cliente no encontrado"}), 404

    # Crear PDF
    buffer = BytesIO()
    width, height = 100 * mm, 150 * mm
    c = canvas.Canvas(buffer, pagesize=(width, height))

    images = get_image_paths()

    # Seleccionar diseño según tipo de entrega
    if sale.delivery_type == 'cadeteria':
        draw_cadeteria_label(c, sale, customer, width, height, images)
    elif sale.delivery_type == 'retiro':
        draw_retiro_label(c, sale, customer, width, height, images)
    elif sale.delivery_type == 'correo':
        draw_correo_label(c, sale, customer, width, height, images)
    else:
        draw_cadeteria_label(c, sale, customer, width, height, images)

    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=f"venta_{sale.id}.pdf"
    )


@pdf_bp.get("/shipments/day/<shipping_date>/labels")
def download_labels_by_day(shipping_date):
    """Genera todas las etiquetas del día (solo cadetería)"""
    try:
        ship_date = date.fromisoformat(shipping_date)
    except ValueError:
        return jsonify({"error": "Fecha inválida"}), 400

    sales = (
        Sale.query
        .filter(
            Sale.delivery_type == 'cadeteria',
            Sale.has_shipping.is_(True),
            Sale.shipping_date == ship_date
        )
        .order_by(Sale.id.asc())
        .all()
    )

    if not sales:
        return jsonify({"error": "No hay envíos ese día"}), 404

    buffer = BytesIO()
    width, height = 100 * mm, 150 * mm
    c = canvas.Canvas(buffer, pagesize=(width, height))

    images = get_image_paths()

    for sale in sales:
        customer = Customer.query.get(sale.customer_id)
        if not customer:
            continue

        draw_cadeteria_label(c, sale, customer, width, height, images)
        c.showPage()

    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"etiquetas_{shipping_date}.pdf",
        mimetype="application/pdf"
    )


@pdf_bp.get("/batch-labels")
def download_batch_labels():
    """Genera PDF con múltiples etiquetas seleccionadas"""
    ids_param = request.args.get('ids', '')
    
    if not ids_param:
        return jsonify({"error": "No se proporcionaron IDs"}), 400
    
    try:
        sale_ids = [int(id_str) for id_str in ids_param.split(',')]
    except ValueError:
        return jsonify({"error": "IDs inválidos"}), 400
    
    if len(sale_ids) > 100:
        return jsonify({"error": "Máximo 100 etiquetas por lote"}), 400
    
    sales = Sale.query.filter(Sale.id.in_(sale_ids)).order_by(Sale.id.asc()).all()
    
    if not sales:
        return jsonify({"error": "No se encontraron ventas"}), 404
    
    buffer = BytesIO()
    width, height = 100 * mm, 150 * mm
    c = canvas.Canvas(buffer, pagesize=(width, height))
    
    images = get_image_paths()
    
    for sale in sales:
        customer = Customer.query.get(sale.customer_id)
        if not customer:
            continue
        
        if sale.delivery_type == 'cadeteria':
            draw_cadeteria_label(c, sale, customer, width, height, images)
        elif sale.delivery_type == 'retiro':
            draw_retiro_label(c, sale, customer, width, height, images)
        elif sale.delivery_type == 'correo':
            draw_correo_label(c, sale, customer, width, height, images)
        else:
            draw_cadeteria_label(c, sale, customer, width, height, images)
        
        c.showPage()
    
    c.save()
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"etiquetas_lote_{len(sales)}.pdf",
        mimetype="application/pdf"
    )