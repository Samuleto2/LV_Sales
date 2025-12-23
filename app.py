import os
from datetime import datetime
from flask import Flask, jsonify, request, send_file, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from models import db, Customer, Sale
from io import BytesIO
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://ventas_user:password@localhost:5432/ventas_app"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

CORS(app)
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/")
def index():
    return render_template("index.html")





##Convertidor de dinero

@app.template_filter('money')
def money_filter(amount):
    """Formatea un número como dinero con separador de miles y símbolo $"""
    if amount is None:
        return "$0"
    return f"${amount:,.0f}".replace(",", ".")


                     ##Endpoints Customers##

@app.route("/customers", methods=["GET"])
def get_costumers():
    customers = Customer.query.all()

    result = []
    for c in customers:
        result.append({
            "id": c.id,
            "first_name": c.first_name,
            "last_name": c.last_name,
            "address": c.address,
            "city": c.city,
            "created_at": c.created_at
        })

    return jsonify(result), 200



@app.route("/customers/<int:customer_id>", methods=["GET"])
def get_customer(customer_id):
    customer = Customer.query.get(customer_id)

    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    
    return jsonify({
        "id": customer.id,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "address": customer.address,
        "city": customer.city,
        "created_at": customer.created_at.isoformat()
    }), 200

@app.route("/customers", methods=["POST"])
def create_customer():
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        required_fields = ["first_name", "last_name","address","city","phone"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Campo faltante: {field}"}), 400 
            
        customer = Customer(
            first_name=data["first_name"],
            last_name=data["last_name"],
            address=data["address"],
            city=data["city"],
            phone=data["phone"],
            description=data.get("description")
        )


        db.session.add(customer)
        db.session.commit()

        return jsonify({"message": "Cliente creado correctamente"
        }), 201

@app.route("/customers/<int:id>", methods=["PUT"])
def update_customer(id):
    customer = db.session.get(Customer,id)
    if not customer:
        return jsonify({"error": "Cliente no existe"}),404
    
    data = request.get_json()
    for field in["first_name", "last_name", "address", "city", "phone", "description"]:
            if field in data:
                setattr(customer,field,data[field])
    

    db.session.commit()
    return jsonify({"message": "Cliente actualizado"})


@app.route("/customers/<int:customer_id>", methods=["DELETE"])
def delete_customer(customer_id):
    customer = Customer.query.get(customer_id)

    if not customer:
        return jsonify({"Error":"El cliente no existe"}), 404
    if customer.sales:
        return jsonify({"error": "No se puede eliminar cliente con ventas asociadas"}), 400
    
    db.session.delete(customer)
    db.session.commit()

    return jsonify({"message":"Cliente eliminado"}), 200

                  ##Endpoints Sales##

@app.route("/sales", methods=["GET"])
def get_sales():
    sales = Sale.query.order_by(Sale.created_at.desc()).limit(25).all()

    return jsonify([{
        "id": s.id,
        "customer_name": f"{s.customer.first_name} {s.customer.last_name}",
        "sale_date": s.sale_date.isoformat(),
        "amount": str(s.amount),
        "payment_method": s.payment_method,
        "paid": s.paid,
        "created_at": s.created_at.isoformat()
    } for s in sales ])

@app.route("/sales/<int:sale_id>", methods=["GET"])
def get_sale(sale_id):
    sale = Sale.query.get(sale_id)
    if not sale:
        return jsonify({"error": "Venta no encontrada"}), 404
    
    customer = Customer.query.get(sale.customer_id)
    return jsonify({
        "id": sale.id,
        "customer_id": sale.customer_id,
        "customer_first_name": customer.first_name,
        "customer_last_name": customer.last_name,
        "customer_address": customer.address,
        "customer_city": customer.city,
        "sale_date": sale.sale_date.isoformat(),
        "amount": str(sale.amount),
        "payment_method": sale.payment_method,
        "paid": sale.paid,
        "created_at": sale.created_at.isoformat()
    })

@app.route("/sales", methods=["POST"])
def create_sale():
    data= request.get_json()

    customer_id = data.get("customer_id")
    amount = data.get("amount")
    payment_method = data.get("payment_method")
    paid = data.get("paid", False)  #por defecto False

    # Validaciones

    if not customer_id or not Customer.query.get(customer_id):
        return jsonify({"Error": "el cliente no existe"}), 404
    if not amount or float(amount) <= 0:
        return jsonify({"Error": "El monto debe ser mayor a 0"}), 400
    if not payment_method or payment_method.lower() not in ["cash", "card", "transfer"]:
        return jsonify({"Error": "Metodo de pago invalido"}), 400
    if not isinstance(paid, bool):
       return jsonify({"Error": "El valor de 'Paid' debe ser booleano"}), 400
    
    sale = Sale(
        customer_id=customer_id,
        amount=amount,
        payment_method=payment_method.lower(),
        paid=paid
    )

    db.session.add(sale)
    db.session.commit()

    return jsonify({"message": "Venta creada", "sale_id": sale.id}), 201


@app.route("/sales/<int:sale_id>", methods=["PUT"])
def update_sale(sale_id):
    sale = Sale.query.get(sale_id)
    if not sale:
        return jsonify({"message": "Venta no encontrada"}), 404
    
    data = request.get_json()
    customer_id = data.get("customer_id")
    amount = data.get("amount")
    payment_method = data.get("payment_method")
    paid = data.get("paid")

    if not customer_id or not Customer.query.get(customer_id):
        return jsonify({"message": "Cliente inválido"}), 400
    if amount is None or payment_method is None or paid is None:
        return jsonify({"message": "Campos incompletos"}), 400
    

    sale.customer_id = customer_id
    sale.amount = amount
    sale.payment_method = payment_method
    sale.paid = paid

    db.session.commit()
    return jsonify({"message": f"Venta {sale_id} actualizada correctamente"})   



@app.route("/sales/<int:sale_id>", methods=["DELETE"])
def delete_sale(sale_id):
    sale = Sale.query.get(sale_id)
    if not sale:
        return jsonify({"Error": "Venta no encontrada"}), 404
    
    db.session.delete(sale)
    db.session.commit()

    return jsonify({"message":"Venta Eliminada"})

## BUSQUEDA DE CLIENTES ##

@app.route("/customers/search", methods=["GET"])
def search_customers():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])
    
     # Buscar por nombre o apellido parcialmente
    results = Customer.query.filter(
         (Customer.first_name.ilike(f"%{query}%")) |
         (Customer.last_name.ilike(f"%{query}%"))
     ).limit(10).all()  # limitar a 10 resultados
     
    return jsonify ([{
        "id": c.id,
        "first_name": c.first_name,
        "last_name": c.last_name,
        "address": c.address,
        "city": c.city,
     }for c in results])


## ENDPOINT CREACION DE ETIQUETAS ##

@app.route("/sales/<int:sale_id>/label", methods=["GET"])
def generate_label(sale_id):
    sale = Sale.query.get(sale_id)
    if not sale:
        return jsonify({"error": "Venta no encontrada"}), 404

    customer = Customer.query.get(sale.customer_id)

    buffer = BytesIO()
    width, height = 100*mm, 150*mm
    c = canvas.Canvas(buffer, pagesize=(width, height))

    # Logo (ajustar ruta y tamaño)
    logo_path = os.path.join(app.root_path, 'static', 'images', 'logo.png')

    try:
        if os.path.exists(logo_path):
            logo = ImageReader(logo_path)
            # Colocado desde arriba izquierda
            c.drawImage(logo, (width - 50*mm)/2, height-50*mm, width=50*mm, height=50*mm, preserveAspectRatio=True, mask='auto')
        else:
            print("Logo no encontrado en:", logo_path)
    except Exception as e:
        print("Error cargando logo:", e)




    # Iconos y datos en una línea horizontal debajo del logo
    icon_size = 4*mm
    line_y = height - 10*mm  # posición vertical debajo del logo

    # Teléfono
    phone_icon_path = os.path.join(app.root_path, 'static', 'images', 'phone.png')
    if os.path.exists(phone_icon_path):
        c.drawImage(ImageReader(phone_icon_path), width/2 - 45*mm, line_y, width=icon_size, height=icon_size, mask='auto')
    c.drawString(width/2 - 40*mm, line_y, "011-32651073")

    # Mail
    email_icon_path = os.path.join(app.root_path, 'static', 'images',  'mail.png')
    if os.path.exists(email_icon_path):
        c.drawImage(ImageReader(email_icon_path), width/2 + -5*mm, line_y, width=icon_size, height=icon_size, mask='auto')
    c.drawString(width/2 + 0*mm, line_y, "lunitavalropa@gmail.com")

    # Línea divisoria
    c.line(5*mm, height-40*mm, width-5*mm, height-40*mm)

    # Datos del cliente (izquierda, título en negrita)
    y = height - 45*mm

    # Cliente en la misma línea
    c.setFont("Helvetica-Bold", 10)
    c.drawString(5*mm, y, "Cliente:")
    c.setFont("Helvetica", 9)
    c.drawString(5*mm + 25*mm, y, f"{customer.first_name} {customer.last_name}")  # desplazamos a la derecha del título
    y -= 6*mm  # bajar para la siguiente línea

    # Localidad
    c.setFont("Helvetica-Bold", 10)
    c.drawString(5*mm, y, "Localidad:")
    c.setFont("Helvetica", 9)
    c.drawString(5*mm + 25*mm, y, f"{customer.city}")
    y -= 6*mm

    # Dirección
    c.setFont("Helvetica-Bold", 10)
    c.drawString(5*mm, y, "Dirección:")
    c.setFont("Helvetica", 9)
    c.drawString(5*mm + 25*mm, y, f"{customer.address}")
    y -= 6*mm

    # Teléfono del cliente
    c.setFont("Helvetica-Bold", 10)
    c.drawString(5*mm, y, "Teléfono:")
    c.setFont("Helvetica", 9)
    c.drawString(5*mm + 25*mm, y, f"{customer.phone}")
    y -= 6*mm

    # Descripción (si existe)
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
    c.drawString(5*mm + 25*mm, y, f"{sale.created_at.strftime('%d/%m/%Y %H:%M')}")
    y -= 8*mm


    # Línea divisoria antes del total
    c.line(5*mm, y, width-5*mm, y); y -= 5*mm

    # Total (centrado, grande y en negrita)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, y, f"Total: ${sale.amount}")

    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"venta_{sale.id}.pdf",
        mimetype="application/pdf"
    )




@app.route("/sales/explore", methods=["GET"])
def explore_sales():
    customer = request.args.get("customer", "")
    payment_method = request.args.get("payment_method", "")
    paid = request.args.get("paid", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")

    query = Sale.query.join(Customer)

    if customer:
        query = query.filter((Customer.first_name + " " + Customer.last_name).ilike(f"%{customer}%"))
    if payment_method:
        query = query.filter(Sale.payment_method.ilike(f"%{payment_method}%"))
    if paid.lower() in ["si","yes","true","1"]:
        query = query.filter(Sale.paid==True)
    elif paid.lower() in ["no","false","0"]:
        query = query.filter(Sale.paid==False)
    if date_from:
        query = query.filter(Sale.created_at>=date_from)
    if date_to:
        query = query.filter(Sale.created_at<=date_to)

    sales = query.all()
    return render_template("explore_sales.html", sales=sales)


##CAMBIAR A PAGO TRUE##

@app.route("/sales/<int:sale_id>/mark_paid", methods=["POST"])
def mark_sale_paid(sale_id):
    sale = Sale.query.get(sale_id)
    if not sale:
        return jsonify({"error": "Venta no encontrada"}), 404

    if sale.paid:
        return jsonify({"message": "La venta ya estaba marcada como pagada"}), 400

    sale.paid = True
    db.session.commit()
    return jsonify({"message": "Venta marcada como pagada correctamente"})





if __name__ == "__main__":
    app.run(debug=True)
