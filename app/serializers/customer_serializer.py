from app.models.customer import Customer


def customer_to_dict(customer):
    return {
        "id": customer.id,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "address": customer.address,
        "city": customer.city,
        "phone": customer.phone,
        "description": customer.description,
        "created_at": customer.created_at.isoformat()
    }

def customers_to_list(customers):
    return [customer_to_dict(c) for c in customers]