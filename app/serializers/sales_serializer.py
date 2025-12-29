from app.models.sale import Sale


def sales_to_dict(sale):
    customer = sale.customer

    return {
        "id": sale.id,
        "customer_id": customer.id if customer else None,
        "customer_first_name": customer.first_name if customer else "",
        "customer_last_name": customer.last_name if customer else "",
        "customer_address": customer.address if customer else "",
        "customer_city": customer.city if customer else "",

        "sale_date": sale.sale_date.isoformat() if sale.sale_date else None,
        "created_at": sale.created_at.isoformat() if sale.created_at else None,

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
        "completed_at": sale.completed_at
    }

def sales_to_list(sales):
    return [sales_to_dict(s) for s in sales]