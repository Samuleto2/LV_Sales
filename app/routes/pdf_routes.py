import os
from io import BytesIO
from flask import Blueprint, send_file, jsonify, current_app
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from app.models.sale import Sale
from app.models.customer import Customer

pdf_bp = Blueprint("pdf", __name__, url_prefix="/pdf")


@pdf_bp.get("/sale/<int:sale_id>/label")
def download_sale_label(sale_id):
    sale = Sale.query.get(sale_id)
    if not sale:
        return jsonify({"error": "Venta no encontrada"}), 404

    customer = Customer.query.get(sale.customer_id)

    buffer = BytesIO()
    width, height = 100 * mm, 150 * mm
    c = canvas.Canvas(buffer, pagesize=(width, height))

    # Logo
    logo_path = os.path.join(current_app.root_path, 'static', 'images', 'logo.png')
    try:
        if os.path.exists(logo_path):
            logo = ImageReader(logo_path)
            c.drawImage(logo, (width - 50*mm)/2, height-50*mm, width=50*mm, height=50*mm, preserveAspectRatio=True, mask='auto')
    except Exception as e:
        print("Error cargando logo:", e)

    # Datos del cliente
    y = height - 60*mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(5*mm, y, "Cliente:")
    c.setFont("Helvetica", 9)
    c.drawString(5*mm + 25*mm, y, f"{customer.first_name} {customer.last_name}")
    y -= 6*mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(5*mm, y, "Localidad:")
    c.setFont("Helvetica", 9)
    c.drawString(5*mm + 25*mm, y, customer.city)
    y -= 6*mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(5*mm, y, "Dirección:")
    c.setFont("Helvetica", 9)
    c.drawString(5*mm + 25*mm, y, customer.address)
    y -= 6*mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(5*mm, y, "Teléfono:")
    c.setFont("Helvetica", 9)
    c.drawString(5*mm + 25*mm, y, customer.phone)
    y -= 6*mm

    # Fecha
    c.setFont("Helvetica-Bold", 10)
    c.drawString(5*mm, y, "Fecha:")
    c.setFont("Helvetica", 9)
    c.drawString(5*mm + 25*mm, y, sale.created_at.strftime('%d/%m/%Y'))
    y -= 8*mm

    # Total
    c.setFont("Helvetica-Bold", 14)
    total_formatted = f"{sale.amount:,.0f}".replace(",", ".")
    c.drawCentredString(width/2, y, f"Total: ${total_formatted}")

    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"venta_{sale.id}.pdf",
        mimetype="application/pdf"
    )
