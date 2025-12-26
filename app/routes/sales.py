# routes/sales.py
from flask import Blueprint, jsonify, request, render_template, redirect, url_for
from app.models.sale import Sale 
from app.services.sales_services import last_sales_service, create_sale, update_sale, delete_sale, get_sale_by_id, update_sale, filter_sales, mark_sale_paid, explore_sales
from app.serializers.sales_serializer import(
    sales_to_dict,
    sales_to_list
)

sales_bp = Blueprint("sales", __name__, url_prefix="/sales")

# ---------- Helpers ----------

# GET /sales → listado de últimas ventas
@sales_bp.get("")
def list_sales():

    query = Sale.query

    sales_channel = request.args.get("sales_channel")
    has_shipping = request.args.get("has_shipping")

    if sales_channel:
        query = query.filter(Sale.sales_channel == sales_channel)

    if has_shipping is not None:
        query = query.filter(
            Sale.has_shipping == (has_shipping.lower() == "true")
        )

    sales = query.order_by(Sale.created_at.desc()).all()

    return jsonify(sales_to_list(sales)), 200

# GET /sales/<id> → traer venta por ID
@sales_bp.get("/<int:id>")
def get_sale(id):
    sale = get_sale_by_id(id)
    if not sale:
        return jsonify({"error": "Venta no encontrada"}), 404
    return jsonify(sales_to_dict(sale)), 200

# POST /sales → crear nueva venta
@sales_bp.post("")
def create_new_sale():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON inválido"}), 400

    try:
        sale = create_sale(data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print("🔥 ERROR CREATE SALE:", e)
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "message": "Venta creada",
        "sale_id": sale.id
    }), 201

# PUT /sales/<id> → actualizar venta
@sales_bp.put("/<int:id>")
def update_existing_sale(id):
    sale = get_sale_by_id(id)
    if not sale:
        return jsonify({"error": "Venta no encontrada"}), 404

    data = request.get_json()
    try:
        update_sale(sale, data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"message": f"Venta {id} actualizada correctamente"}), 200

# DELETE /sales/<id> → eliminar venta
@sales_bp.delete("/<int:id>")
def delete_existing_sale(id):
    sale = get_sale_by_id(id)
    if not sale:
        return jsonify({"error": "Venta no encontrada"}), 404

    delete_sale(sale)
    return jsonify({"message": "Venta eliminada"}), 200


@sales_bp.get("/explore")
def explore_sales_page():
    filters = {
        "customer": request.args.get("customer", ""),
        "payment_method": request.args.get("payment_method", ""),
        "paid": request.args.get("paid", ""),
        "date_from": request.args.get("date_from", ""),
        "date_to": request.args.get("date_to", ""),
        "page": int(request.args.get("page", 1))
    }

    data = explore_sales(filters)  # llamamos al servicio
    return render_template(
        "explore_sales.html",
        sales=data["sales"],
        page=data["page"],
        per_page=data["per_page"],
        total_sales=data["total_sales"],
        total_pages=data["total_pages"],
        filters=filters
    )

# Endpoint para marcar venta como pagada
@sales_bp.post("/<int:sale_id>/mark_paid")
def mark_sale_paid_endpoint(sale_id):
    sale, message = mark_sale_paid(sale_id)
    if not sale:
        return jsonify({"error": message}), 400
    return jsonify({"message": message}), 200

@sales_bp.get("/last_sales")
def get_last_sales():
    sales = last_sales_service(10)  # ahora llama al servicio
    return jsonify([
        {
            "id": s.id,
            "sale_date": s.created_at.isoformat(),
            "customer_first_name": s.customer.first_name,
            "customer_last_name": s.customer.last_name,
            "amount": s.amount,
            "payment_method": s.payment_method,
            "paid": s.paid
        }
        for s in sales
    ])