from datetime import datetime
from flask import Flask, jsonify, request, send_file, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from models import db, Customer, Sale
from io import BytesIO
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas


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
    try:
        logo = ImageReader("static/logo.png")
        c.drawImage(logo, 5*mm, height-25*mm, width=30*mm, preserveAspectRatio=True, mask='auto')
    except:
        pass  # si no hay logo, seguimos igual

    # Datos de la empresa
    c.setFont("Helvetica-Bold", 8)
    c.drawString(40*mm, height-15*mm, "Lunita Val")
    c.setFont("Helvetica", 7)
    c.drawString(40*mm, height-20*mm, "Del Viso")
    c.drawString(40*mm, height-25*mm, "0113xxxxxxx")
    c.drawString(40*mm, height-30*mm, "lunitavalropa@gmail.com")

    # Línea divisoria
    c.line(5*mm, height-35*mm, width-5*mm, height-35*mm)

    # Datos del cliente y venta
    c.setFont("Helvetica", 8)
    y = height - 40*mm
    c.drawString(5*mm, y, f"Nombre: {customer.first_name} {customer.last_name}"); y -= 6*mm
    c.drawString(5*mm, y, f"Localidad: {customer.city}"); y -= 6*mm
    c.drawString(5*mm, y, f"Dirección: {customer.address}"); y -= 6*mm
    if getattr(customer, 'description', None):
        c.drawString(5*mm, y, f"Descripción: {customer.description}"); y -= 6*mm
    c.drawString(5*mm, y, f"Fecha: {sale.created_at.strftime('%d/%m/%Y %H:%M')}"); y -= 8*mm

    # Línea divisoria antes del total
    c.line(5*mm, y, width-5*mm, y); y -= 5*mm

    # Total
    c.setFont("Helvetica-Bold", 12)
    c.drawString(5*mm, y, f"Total: ${sale.amount}")

    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"venta_{sale.id}.pdf",
        mimetype="application/pdf"
    )


if __name__ == "__main__":
    app.run(debug=True)
