from datetime import datetime, date, timedelta
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from zoneinfo import ZoneInfo

from app.models.sale import Sale
from app.models.customer import Customer
from app.extensions import db


# 🔹 Zona horaria de Argentina
TIMEZONE = ZoneInfo("America/Argentina/Buenos_Aires")


def now_ar():
    """Retorna datetime actual en zona horaria de Argentina"""
    return datetime.now(TIMEZONE)


def today_ar():
    """Retorna date de hoy en Argentina (sin hora)"""
    return now_ar().date()


def to_ar_date(iso_string):
    """Convierte string ISO a date de Argentina"""
    if not iso_string:
        return None
    
    # Si es solo fecha (YYYY-MM-DD), parsearlo directamente
    if len(iso_string) == 10:
        return date.fromisoformat(iso_string)
    
    # Si tiene timestamp, convertir a zona horaria
    dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    return dt.astimezone(TIMEZONE).date()


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

        # 🔹 Parsear fecha sin conversión de zona horaria
        shipping_date = date.fromisoformat(data["shipping_date"])

        # 🔹 Validar que no sea anterior a HOY en Argentina
        if shipping_date < today_ar():
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

    # 🔹 Usar fecha y hora de Argentina
    sale = Sale(
        **parsed,
        sale_date=now_ar(),
        created_at=now_ar()
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


def update_shipment(sale, data):
    if not sale:
        return False

    if data.get("shipping_date"):
        # 🔹 Parsear fecha sin conversión de zona horaria
        sale.shipping_date = date.fromisoformat(data["shipping_date"])

    if "notes" in data:
        sale.notes = data["notes"]

    db.session.commit()
    return True


def get_shipping_calendar(days_back=5, days_forward=10):
    """
    🔹 CORREGIDO: Obtiene calendario de envíos incluyendo días pasados
    
    Args:
        days_back: Días hacia atrás desde hoy
        days_forward: Días hacia adelante desde hoy
    
    Returns:
        Dict con fecha ISO como key y cantidad de envíos como value
    """
    today = today_ar()
    start_date = today - timedelta(days=days_back)
    end_date = today + timedelta(days=days_forward)

    # 🔹 Query que agrupa por shipping_date
    rows = (
        db.session.query(
            Sale.shipping_date,
            func.count(Sale.id)
        )
        .filter(
            Sale.has_shipping.is_(True),
            Sale.shipping_date.between(start_date, end_date)
        )
        .group_by(Sale.shipping_date)
        .all()
    )

    # 🔹 Convertir a diccionario con formato ISO
    result = {}
    for shipping_date, count in rows:
        if shipping_date:
            result[shipping_date.isoformat()] = count

    return result


def get_shipments_by_day(shipping_date_str: str):
    """
    🔹 CORREGIDO: Obtiene envíos de un día específico
    
    Args:
        shipping_date_str: Fecha en formato ISO (YYYY-MM-DD)
    
    Returns:
        Lista de Sales
    """
    # 🔹 Parsear fecha sin conversión de zona horaria
    target_date = date.fromisoformat(shipping_date_str)
    
    return (
        Sale.query
        .filter(
            Sale.has_shipping.is_(True),
            Sale.shipping_date == target_date
        )
        .order_by(Sale.id.asc())
        .all()
    )