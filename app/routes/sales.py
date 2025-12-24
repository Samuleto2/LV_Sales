# routes/sales.py
from flask import Blueprint, jsonify, request, render_template, redirect, url_for
from app.services.sales_services import get_last_sales, create_sale, update_sale, delete_sale, get_sale_by_id, update_sale
from app.serializers.sales_serializer import(
    sales_to_dict,
    sales_to_list
)

sales_bp = Blueprint("sales", __name__, url_prefix="/sales")

# ---------- Helpers ----------

# GET /sales → listado de últimas ventas
@sales_bp.get("")
def list_sales():
    sales = get_last_sales(limit=25)
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
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se recibió data"}), 400

    try:
        sale = create_sale(data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"message": "Venta creada", "sale_id": sale.id}), 201

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
