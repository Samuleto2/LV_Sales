# app/services/customers_service.py
from app.models.customer import Customer
from app.extensions import db


def get_all_customers():
    return Customer.query.order_by(Customer.created_at.desc()).all()


def get_customer_by_id(customer_id):
    return db.session.get(Customer, customer_id)


def create_customer(data):
    customer = Customer(
        first_name=data["first_name"].strip(),
        last_name=data["last_name"].strip(),
        address=data["address"].strip(),
        city=data["city"].strip(),
        phone=data["phone"].strip(),
        description=data.get("description"),
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
