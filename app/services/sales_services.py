from datetime import datetime, date, timedelta
from sqlalchemy import func
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

    # --- Tipo de entrega ---
    delivery_type = data.get("delivery_type")

    if not is_update and delivery_type not in ("cadeteria", "retiro", "correo"):
        raise ValueError("Tipo de entrega inválido")

    # Regla de negocio: SOLO cadetería tiene envío
    has_shipping = delivery_type == "cadeteria"

    # --- Punto de venta ---
    if not is_update and not data.get("sales_channel"):
        raise ValueError("Punto de venta requerido")

    # --- Fecha de envío (solo cadetería) ---
    shipping_date = None
    if has_shipping:
        if not data.get("shipping_date"):
            raise ValueError("Fecha de envío requerida para cadetería")

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
        "paid": paid,
        "notes": data.get("notes"),
        "delivery_type": delivery_type,
        "has_shipping": has_shipping,
        "shipping_date": shipping_date,
        "sales_channel": data.get("sales_channel"),
        "is_cash": is_cash,
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

def get_sales_by_turn(start_time: datetime, end_time: datetime):
    """
    Devuelve las ventas entre start_time y end_time.
    """
    return (
        db.session.query(Sale)
        .filter(Sale.sale_date >= start_time)
        .filter(Sale.sale_date <= end_time)
        .order_by(Sale.sale_date.asc())
        .all()
    )


def get_shipments_calendar(from_date: date, to_date: date):
    """
    Devuelve un dict con los envíos agrupados por día
    entre from_date y to_date.
    """
    sales = (
        Sale.query
        .filter(
            Sale.has_shipping.is_(True),
            Sale.shipping_date.isnot(None),
            Sale.shipping_date.between(from_date, to_date)
        )
        .order_by(Sale.shipping_date.asc())
        .all()
    )

    result = {}

    for s in sales:
        key = s.shipping_date.isoformat()

        if key not in result:
            result[key] = {
                "count": 0,
                "sales": []
            }

        result[key]["count"] += 1
        result[key]["sales"].append({
            "id": s.id,
            "customer": f"{s.customer.customer_first_name} {s.customer.customer_last_name}",
            "address": s.customer.customer_address,
            "city": s.customer.customer_city,
            "notes": s.notes,
            "label_url": f"/sales/{s.id}/label"
        })

    return result


def update_shipment(sale, data):
    """
    Actualiza fecha de envío y/o notas del envío.
    """
    if not sale:
        return False

    if data.get("shipping_date"):
        sale.shipping_date = date.fromisoformat(data["shipping_date"])

    if "notes" in data:
        sale.notes = data["notes"]

    db.session.commit()
    return True


def get_shipping_calendar(days=15):
    """
    Devuelve un dict con la cantidad de envíos por día
    desde hoy hasta hoy + days.
    """
    today = date.today()
    end_date = today + timedelta(days=days)

    rows = (
        db.session.query(
            Sale.shipping_date,
            func.count(Sale.id)
        )
        .filter(
            Sale.has_shipping.is_(True),
            Sale.shipping_date.isnot(None),
            Sale.shipping_date >= today,
            Sale.shipping_date <= end_date
        )
        .group_by(Sale.shipping_date)
        .all()
    )

    return {row[0].isoformat(): row[1] for row in rows}


def get_shipments_by_day(shipping_date: date):
    """
    Devuelve los envíos de un día específico.
    """
    return (
        Sale.query
        .filter(
            Sale.has_shipping.is_(True),
            Sale.shipping_date == shipping_date
        )
        .order_by(Sale.id.asc())
        .all()
    )
