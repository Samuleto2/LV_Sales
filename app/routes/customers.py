from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required
from app.serializers.customer_serializer import(
    customer_to_dict,
    customers_to_list
)
from app.services.customers_services import (
    get_all_customers,
    get_customer_by_id,
    create_customer,
    update_customer,
    delete_customer,
    search_customers,
    get_customers_paginated_service
)

customers_bp = Blueprint("customers", __name__, url_prefix="/customers")

@customers_bp.get("/manage")
@login_required
def manage_customers_view():
    return render_template("clientes.html")

@customers_bp.get("")
@login_required
def get_customers():
    customers = get_all_customers()
    return jsonify(customers_to_list(customers)), 200

@customers_bp.get("/<int:id>")
@login_required
def get_customer(id):
    customer = get_customer_by_id(id)
    if not customer:
        return jsonify({"error": "Cliente no encontrado"}), 404
    return jsonify(customer_to_dict(customer)), 200

@customers_bp.post("")
@login_required
def create_new_customer():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se recibió data"}), 400
    try:
        customer = create_customer(data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({
        "message": "Cliente creado correctamente",
        "customer": customer_to_dict(customer)
    }), 201

@customers_bp.put("/<int:id>")
@login_required
def update_existing_customer(id):
    customer = get_customer_by_id(id)
    if not customer:
        return jsonify({"error": "Cliente no existe"}), 404
    data = request.get_json()
    update_customer(customer, data)
    return jsonify({"message": "Cliente actualizado"}), 200

@customers_bp.delete("/<int:id>")
@login_required
def delete_existing_customer(id):
    customer = get_customer_by_id(id)
    if not customer:
        return jsonify({"error": "Cliente no existe"}), 404
    try:
        delete_customer(customer)
    except ValueError:
        return jsonify({"error": "No se puede eliminar cliente con ventas asociadas"}), 400
    return jsonify({"message": "Cliente eliminado"}), 200

@customers_bp.get("/search")
@login_required
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])
    customers = search_customers(query)
    result = [customer_to_dict(c) for c in customers]
    return jsonify(result), 200

@customers_bp.get("/paginated")
@login_required
def get_customers_paginated():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
    except ValueError:
        return jsonify({"error": "Parámetros de página inválidos"}), 400

    query = request.args.get("q", "").strip()
    
    pagination = get_customers_paginated_service(page=page, per_page=per_page, query=query)
    
    customers_list = [customer_to_dict(c) for c in pagination.items]

    return jsonify({
        "customers": customers_list,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages
    })