from datetime import datetime, date, timedelta
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.models.sale import Sale
from app.models.customer import Customer
from app.extensions import db


# =========================
#   CONSULTAS BÁSICAS
# =========================

def last_sales_service(limit=10):
    return (
        Sale.query
        .options(joinedload(Sale.customer))
        .order_by(Sale.created_at.desc())
        .limit(limit)
        .all()
    )


def get_sale_by_id(sale_id):
    return Sale.query.get(sale_id)


# =========================
#   PARSEO / VALIDACIONES
# =========================

def parse_sale_data(data, is_update=False):
    if not isinstance(data, dict):
        raise ValueError("Datos inválidos")

    delivery_type = data.get("delivery_type")

    if not is_update and delivery_type not in ("cadeteria", "retiro", "correo"):
        raise ValueError("Tipo de entrega inválido")

    has_shipping = delivery_type == "cadeteria"

    if not is_update and not data.get("sales_channel"):
        raise ValueError("Punto de venta requerido")

    shipping_date = None
    if has_shipping:
        if not data.get("shipping_date"):
            raise ValueError("Fecha de envío requerida para cadetería")

        shipping_date = date.fromisoformat(data["shipping_date"])

        if shipping_date < date.today():
            raise ValueError("La fecha de envío no puede ser pasada")

    is_cash = bool(data.get("is_cash", False))
    paid = bool(data.get("paid", False))

    if is_cash and paid:
        raise ValueError("Una venta en efectivo no puede estar marcada como pagada")

    return {
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


# =========================
#   CRUD VENTAS
# =========================

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


# =========================
#   FILTROS / LISTADOS
# =========================

def filter_sales(customer="", payment_method="", paid="", date_from="", date_to=""):
    query = Sale.query.join(Customer)

    if customer:
        query = query.filter(
            (Customer.first_name + " " + Customer.last_name).ilike(f"%{customer}%")
        )

    if payment_method:
        query = query.filter(Sale.payment_method.ilike(f"%{payment_method}%"))

    if paid.lower() in ("si", "yes", "true", "1"):
        query = query.filter(Sale.paid.is_(True))
    elif paid.lower() in ("no", "false", "0"):
        query = query.filter(Sale.paid.is_(False))

    if date_from:
        query = query.filter(Sale.created_at >= datetime.fromisoformat(date_from))

    if date_to:
        query = query.filter(Sale.created_at <= datetime.fromisoformat(date_to))

    return query.order_by(Sale.created_at.desc()).all()


def explore_sales(filters):
    customer = filters.get("customer", "")
    payment_method = filters.get("payment_method", "")
    paid = filters.get("paid", "")
    date_from = filters.get("date_from", "")
    date_to = filters.get("date_to", "")
    page = int(filters.get("page", 1))
    per_page = 10

    query = Sale.query.join(Customer)

    if customer:
        query = query.filter(
            (Customer.first_name + " " + Customer.last_name).ilike(f"%{customer}%")
        )

    if payment_method:
        query = query.filter(Sale.payment_method.ilike(f"%{payment_method}%"))

    if paid.lower() in ("si", "yes", "true", "1"):
        query = query.filter(Sale.paid.is_(True))
    elif paid.lower() in ("no", "false", "0"):
        query = query.filter(Sale.paid.is_(False))

    if date_from:
        query = query.filter(Sale.created_at >= datetime.fromisoformat(date_from))

    if date_to:
        query = query.filter(Sale.created_at <= datetime.fromisoformat(date_to))

    total = query.count()

    sales = (
        query
        .order_by(Sale.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "sales": sales,
        "page": page,
        "per_page": per_page,
        "total_sales": total,
        "total_pages": (total + per_page - 1) // per_page
    }


# =========================
#   REPORTES / ENVÍOS
# =========================

def get_sales_by_turn(start_time: datetime, end_time: datetime):
    return (
        Sale.query
        .filter(Sale.sale_date.between(start_time, end_time))
        .order_by(Sale.sale_date.asc())
        .all()
    )


def get_shipments_calendar(from_date: date, to_date: date):
    sales = (
        Sale.query
        .filter(
            Sale.has_shipping.is_(True),
            Sale.shipping_date.between(from_date, to_date)
        )
        .order_by(Sale.shipping_date.asc())
        .all()
    )

    result = {}

    for s in sales:
        key = s.shipping_date.isoformat()
        result.setdefault(key, {"count": 0, "sales": []})

        result[key]["count"] += 1
        result[key]["sales"].append({
            "id": s.id,
            "customer": f"{s.customer.first_name} {s.customer.last_name}",
            "address": s.customer.address,
            "city": s.customer.city,
            "notes": s.notes,
            "label_url": f"/sales/{s.id}/label"
        })

    return result


def update_shipment(sale, data):
    if not sale:
        return False

    if data.get("shipping_date"):
        sale.shipping_date = date.fromisoformat(data["shipping_date"])

    if "notes" in data:
        sale.notes = data["notes"]

    db.session.commit()
    return True


def get_shipping_calendar(days=15):
    today = date.today()
    end_date = today + timedelta(days=days)

    rows = (
        db.session.query(Sale.shipping_date, func.count(Sale.id))
        .filter(
            Sale.has_shipping.is_(True),
            Sale.shipping_date.between(today, end_date)
        )
        .group_by(Sale.shipping_date)
        .all()
    )

    return {row[0].isoformat(): row[1] for row in rows}


def get_shipments_by_day(shipping_date: date):
    return (
        Sale.query
        .filter(
            Sale.has_shipping.is_(True),
            Sale.shipping_date == shipping_date
        )
        .order_by(Sale.id.asc())
        .all()
    )
