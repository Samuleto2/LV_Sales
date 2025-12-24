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
        "sale_date": sale.sale_date.isoformat(),
        "amount": str(sale.amount),
        "payment_method": sale.payment_method,
        "paid": sale.paid,
        "created_at": sale.created_at.isoformat(),
        "sales_notes": sale.notes or ""
    }

def sales_to_list(sales):
    return [sales_to_dict(s) for s in sales]