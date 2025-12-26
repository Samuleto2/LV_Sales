from datetime import datetime, date
from app.models.sale import Sale
from app.models.customer import Customer
from app.extensions import db
from sqlalchemy.orm import joinedload

def last_sales_service(limit=10):
    return (
        Sale.query
        .options(joinedload(Sale.customer))
        .order_by(Sale.created_at.desc())
        .limit(limit)
        .all()
    )

def get_sale_by_id(sale_id):
    """Trae una venta por su ID"""
    return Sale.query.get(sale_id)

def parse_sale_data(data, is_update=False):

    if not isinstance(data, dict):
        raise ValueError("Datos inválidos")

    # --- Punto de venta ---
    if not is_update and not data.get("sales_channel"):
        raise ValueError("Punto de venta requerido")

    has_shipping = bool(data.get("has_shipping", False))

    if has_shipping and not data.get("shipping_date"):
        raise ValueError("Fecha de envío requerida")

    # --- Fechas ---
    shipping_date = None
    if has_shipping:
        shipping_date = datetime.fromisoformat(
            data["shipping_date"]
        ).date()

        if shipping_date < date.today():
            raise ValueError("La fecha de envío no puede ser pasada")
        
     # --- Restricciones efectivo vs pagado ---
    is_cash = bool(data.get("is_cash", False))
    paid = bool(data.get("paid", False))
    if is_cash and paid:
        raise ValueError("No se puede marcar como pagado si es efectivo")
    if paid and is_cash:
        raise ValueError("No se puede marcar como efectivo si ya está pagado")

    parsed = {
        "customer_id": data.get("customer_id"),
        "amount": data.get("amount"),
        "payment_method": data.get("payment_method"),
        "paid": bool(data.get("paid", False)),
        "notes": data.get("notes"),
        "has_shipping": has_shipping,
        "shipping_date": shipping_date,
        "sales_channel": data.get("sales_channel"),
        "is_cash": bool(data.get("is_cash", False)),
        "has_change": bool(data.get("has_change", False))
    }

    return parsed


def create_sale(data):

    parsed = parse_sale_data(data)

    sale = Sale(
        **parsed,
        sale_date=date.today(),
        created_at=datetime.utcnow()
    )

    db.session.add(sale)
    db.session.commit()
    return sale

def update_sale(sale, data):

    parsed = parse_sale_data(data, is_update=True)

    for field, value in parsed.items():
        if value is not None:
            setattr(sale, field, value)

    db.session.commit()
    return sale

def delete_sale(sale):
    """Elimina una venta"""
    db.session.delete(sale)
    db.session.commit()



def mark_sale_paid(sale_id):
    sale = Sale.query.get(sale_id)
    if not sale:
        return None, "Venta no encontrada"

    if sale.paid:
        return None, "La venta ya estaba marcada como pagada"

    sale.paid = True
    db.session.commit()
    return sale, "Venta marcada como pagada correctamente"


def filter_sales(customer="", payment_method="", paid="", date_from="", date_to=""):
    query = Sale.query.join(Customer)

    if customer:
        query = query.filter(
            (Customer.first_name + " " + Customer.last_name).ilike(f"%{customer}%")
        )
    if payment_method:
        query = query.filter(Sale.payment_method.ilike(f"%{payment_method}%"))
    if paid.lower() in ["si", "yes", "true", "1"]:
        query = query.filter(Sale.paid == True)
    elif paid.lower() in ["no", "false", "0"]:
        query = query.filter(Sale.paid == False)
    if date_from:
        query = query.filter(Sale.created_at >= date_from)
    if date_to:
        query = query.filter(Sale.created_at <= date_to)

    return query.order_by(Sale.created_at.desc()).all()



def explore_sales(filters):
    customer = filters.get("customer", "")
    payment_method = filters.get("payment_method", "")
    paid = filters.get("paid", "")
    date_from = filters.get("date_from", "")
    date_to = filters.get("date_to", "")
    page = filters.get("page", 1)
    per_page = 10  # <-- número de ventas por página

    query = Sale.query.join(Customer)

    if customer:
        query = query.filter((Customer.first_name + " " + Customer.last_name).ilike(f"%{customer}%"))
    if payment_method:
        query = query.filter(Sale.payment_method.ilike(f"%{payment_method}%"))
    if paid.lower() in ["si", "yes", "true", "1"]:
        query = query.filter(Sale.paid == True)
    elif paid.lower() in ["no", "false", "0"]:
        query = query.filter(Sale.paid == False)
    if date_from:
        query = query.filter(Sale.created_at >= date_from)
    if date_to:
        query = query.filter(Sale.created_at <= date_to)

    total_sales = query.count()
    sales = query.order_by(Sale.created_at.desc()).offset((page-1)*per_page).limit(per_page).all()
    total_pages = (total_sales + per_page - 1) // per_page  # cálculo de páginas totales

    return {
        "sales": sales,
        "page": page,
        "per_page": per_page,
        "total_sales": total_sales,
        "total_pages": total_pages
    }