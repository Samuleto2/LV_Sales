# app/routes/pdf_routes.py
import os
from datetime import datetime, date
from io import BytesIO
from flask import Blueprint, send_file, current_app, jsonify
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from app.models.sale import Sale
from app.models.customer import Customer

pdf_bp = Blueprint("pdf", __name__, url_prefix="/pdf")

@pdf_bp.get("/sale/<int:sale_id>/label")
def download_sale_label(sale_id):
    # Traer la venta
    sale = Sale.query.get(sale_id)
    if not sale:
        return jsonify({"error": "Venta no encontrada"}), 404

    customer = Customer.query.get(sale.customer_id)
    if not customer:
        return jsonify({"error": "Cliente no encontrado"}), 404

    # Crear buffer PDF
    buffer = BytesIO()
    width, height = 100 * mm, 150 * mm
    c = canvas.Canvas(buffer, pagesize=(width, height))

    # --- Paths de imágenes ---
    static_path = os.path.abspath(os.path.join(current_app.root_path, '..', 'static', 'images'))
    logo_path = os.path.join(static_path, 'logo.png')
    phone_icon_path = os.path.join(static_path, 'phone.png')
    email_icon_path = os.path.join(static_path, 'mail.png')

    # --- Numero de venta --- #
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, height - 6*mm, f"VENTA Nº{sale.id}000")
    

    # --- Logo ---
    try:
        if os.path.exists(logo_path):
            logo = ImageReader(logo_path)
            c.drawImage(logo, (width - 50*mm)/2, height-50*mm, width=50*mm, height=50*mm, preserveAspectRatio=True, mask='auto')
    except Exception as e:
        print("Error cargando logo:", e)

    # --- Contacto ---
    icon_size = 4 * mm
    line_y = height - 55*mm

    if os.path.exists(phone_icon_path):
        c.drawImage(ImageReader(phone_icon_path), width/2 - 45*mm, line_y, width=icon_size, height=icon_size, mask='auto')
    c.drawString(width/2 - 40*mm, line_y, "011-32651073")

    if os.path.exists(email_icon_path):
        c.drawImage(ImageReader(email_icon_path), width/2 - 5*mm, line_y, width=icon_size, height=icon_size, mask='auto')
    c.drawString(width/2 + 0*mm, line_y, "lunitavalropa@gmail.com")

    # Línea divisoria
    c.line(5*mm, height-60*mm, width-5*mm, height-60*mm)

    # --- Datos cliente ---
    y = height - 65*mm
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

    # Fecha
    c.setFont("Helvetica-Bold", 10)
    c.drawString(5*mm, y, "Fecha:")
    c.setFont("Helvetica", 9)
    c.drawString(5*mm + 25*mm, y, sale.created_at.strftime("%d/%m/%Y"))
    y -= 8*mm

    # Línea divisoria antes del total
    c.line(5*mm, y, width-5*mm, y)
    y -= 5*mm

    # Total
    c.setFont("Helvetica-Bold", 14)
    total_formatted = f"{sale.amount:,.0f}".replace(",", ".")
    c.drawCentredString(width/2, y, f"Total: ${total_formatted}")
    y -= 15*mm

    # --- Recuadro notas ---
    notes_height = 25*mm
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1)
    c.rect(5*mm, y - notes_height, width-10*mm, notes_height, stroke=1, fill=0)

    # Escribir texto dentro del recuadro
    c.setFont("Helvetica", 9)
    text_y = y - 4*mm  # un poquito de padding desde arriba
    if sale.notes:
        # Si el texto es largo, lo dividimos en varias líneas
        lines = sale.notes.split('\n')
        for line in lines:
            c.drawString(7*mm, text_y, line)
            text_y -= 4*mm  # espacio entre líneas

    # Finalizar PDF
    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=False,   # 👈 CLAVE
        download_name=f"venta_{sale.id}.pdf"
    )



@pdf_bp.get("/shipments/day/<shipping_date>/labels")
def download_labels_by_day(shipping_date):
    try:
        ship_date = date.fromisoformat(shipping_date)
    except ValueError:
        return jsonify({"error": "Fecha inválida"}), 400

    sales = (
        Sale.query
        .filter(
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

    # Paths (una sola vez)
    static_path = os.path.abspath(
        os.path.join(current_app.root_path, '..', 'static', 'images')
    )
    logo_path = os.path.join(static_path, 'logo.png')
    phone_icon_path = os.path.join(static_path, 'phone.png')
    email_icon_path = os.path.join(static_path, 'mail.png')

    for sale in sales:
        customer = Customer.query.get(sale.customer_id)




            # --- Numero de venta --- #
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(width / 2, height - 6*mm, f"VENTA Nº{sale.id}000")
        

        # --- Logo ---
        try:
            if os.path.exists(logo_path):
                logo = ImageReader(logo_path)
                c.drawImage(logo, (width - 50*mm)/2, height-50*mm, width=50*mm, height=50*mm, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print("Error cargando logo:", e)

        # --- Contacto ---
        icon_size = 4 * mm
        line_y = height - 55*mm

        if os.path.exists(phone_icon_path):
            c.drawImage(ImageReader(phone_icon_path), width/2 - 45*mm, line_y, width=icon_size, height=icon_size, mask='auto')
        c.drawString(width/2 - 40*mm, line_y, "011-32651073")

        if os.path.exists(email_icon_path):
            c.drawImage(ImageReader(email_icon_path), width/2 - 7*mm, line_y, width=icon_size, height=icon_size, mask='auto')
        c.drawString(width/2 - 2*mm, line_y, "lunitavalropa@gmail.com")

        # Línea divisoria
        c.line(5*mm, height-60*mm, width-5*mm, height-60*mm)

        # --- Datos cliente ---
        y = height - 65*mm
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

        # Fecha
        c.setFont("Helvetica-Bold", 10)
        c.drawString(5*mm, y, "Fecha:")
        c.setFont("Helvetica", 9)
        c.drawString(5*mm + 25*mm, y, sale.created_at.strftime("%d/%m/%Y"))
        y -= 8*mm

        # Línea divisoria antes del total
        c.line(5*mm, y, width-5*mm, y)
        y -= 5*mm

        # Total
        c.setFont("Helvetica-Bold", 14)
        total_formatted = f"{sale.amount:,.0f}".replace(",", ".")
        c.drawCentredString(width/2, y, f"Total: ${total_formatted}")
        y -= 15*mm

        # --- Recuadro notas ---
        notes_height = 25*mm
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(1)
        c.rect(5*mm, y - notes_height, width-10*mm, notes_height, stroke=1, fill=0)

        # Escribir texto dentro del recuadro
        c.setFont("Helvetica", 9)
        text_y = y - 4*mm  # un poquito de padding desde arriba
        if sale.notes:
            # Si el texto es largo, lo dividimos en varias líneas
            lines = sale.notes.split('\n')
            for line in lines:
                c.drawString(7*mm, text_y, line)
                text_y -= 4*mm;  # espacio entre líneas

        c.showPage()  


    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"etiquetas_{shipping_date}.pdf",
        mimetype="application/pdf"
    )      
   



