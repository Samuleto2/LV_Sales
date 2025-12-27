# app/services/customers_service.py
import re
from app.models.customer import Customer
from app.extensions import db


def get_all_customers():
    return Customer.query.order_by(Customer.created_at.desc()).all()


def get_customer_by_id(customer_id):
    return db.session.get(Customer, customer_id)


def create_customer(data):
    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()
    address = data.get("address", "").strip()
    city = data.get("city", "").strip()
    phone = data.get("phone", "").strip()
    description = data.get("description", "").strip() if data.get("description") else None

    # Validaciones básicas
    if not first_name or not last_name:
        raise ValueError("Nombre y apellido son obligatorios")
    if not city:
        raise ValueError("Ciudad es obligatoria")
    if not re.fullmatch(r"\d{10,12}", phone):
        raise ValueError("Teléfono inválido. Debe tener entre 10 y 12 dígitos")
    if Customer.query.filter_by(phone=phone).first():
        raise ValueError("Ya existe un cliente con este teléfono")

    # Crear cliente
    customer = Customer(
        first_name=first_name,
        last_name=last_name,
        address=address,
        city=city,
        phone=phone,
        description=description
    )
    
    db.session.add(customer)
    db.session.commit()
    return customer

def update_customer(customer, data):
    allowed_fields = [
        "first_name", "last_name", "address",
        "city", "phone", "description"
    ]

    for field in allowed_fields:
        if field in data:
            setattr(customer, field, data[field])

    db.session.commit()
    return customer


def delete_customer(customer):
    if customer.sales:
        raise ValueError("CUSTOMER_HAS_SALES")

    db.session.delete(customer)
    db.session.commit()


def search_customers(query, limit=10):
    return (
        Customer.query
        .filter(
            (Customer.first_name.ilike(f"%{query}%")) |
            (Customer.last_name.ilike(f"%{query}%"))
        )
        .limit(limit)
        .all()
    )
def get_customers_paginated_service(page=1, per_page=10, query=""):
    base_query = Customer.query

    if query:
        q = query.lower()
        base_query = base_query.filter(
            db.or_(
                db.func.lower(Customer.first_name).like(f"%{q}%"),
                db.func.lower(Customer.last_name).like(f"%{q}%")
            )
        )

    base_query = base_query.order_by(Customer.first_name.asc(), Customer.last_name.asc())
    pagination = base_query.paginate(page=page, per_page=per_page, error_out=False)
    return pagination