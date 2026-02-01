from app.models.sale import Sale
from zoneinfo import ZoneInfo

TIMEZONE = ZoneInfo("America/Argentina/Buenos_Aires")
UTC = ZoneInfo("UTC")

def utc_to_ar(dt):
    if not dt:
        return None

    # Si viene naive, asumimos UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    return dt.astimezone(TIMEZONE)

def sales_to_dict(sale):
    customer = sale.customer

    return {
        "id": sale.id,
        "customer_id": customer.id if customer else None,
        "customer_first_name": customer.first_name if customer else "",
        "customer_last_name": customer.last_name if customer else "",
        "customer_address": customer.address if customer else "",
        "customer_city": customer.city if customer else "",

        "sale_date": (utc_to_ar(sale.sale_date).isoformat()
                    if sale.sale_date else None
                        ),
        "created_at": (
                utc_to_ar(sale.created_at).isoformat()
                if sale.created_at else None
            ),

        "amount": float(sale.amount),
        "payment_method": sale.payment_method,
        "paid": sale.paid,
        "notes": sale.notes or "",

        # 🔹 NUEVOS CAMPOS
        "has_shipping": sale.has_shipping,
        "shipping_date": (
                    sale.shipping_date.isoformat()
                    if sale.shipping_date else None
                ),

        "sales_channel": sale.sales_channel,
        "is_cash": sale.is_cash,
        "has_change": sale.has_change,
        "delivery_type": sale.delivery_type,
        "completed_at": (
                    utc_to_ar(sale.completed_at).isoformat()
                    if sale.completed_at else None
                ),
        
        # 🔹 NUEVO: Campos de entrega
        "delivered_at": (
                    utc_to_ar(sale.delivered_at).isoformat()
                    if sale.delivered_at else None
                ),
        "shipped_at": (
                    utc_to_ar(sale.shipped_at).isoformat()
                    if sale.shipped_at else None
                ),
        "is_delivered": sale.is_delivered,
        "days_since_creation": sale.days_since_creation,
        "is_overdue": sale.is_overdue,
        
        # Info del customer (para evitar queries adicionales)
        "customer_phone": customer.phone if customer else None

        
    }

def sales_to_list(sales):
    return [sales_to_dict(s) for s in sales]