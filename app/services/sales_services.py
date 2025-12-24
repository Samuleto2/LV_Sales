from app.models.sale import Sale
from app.models.customer import Customer
from app.extensions import db
from sqlalchemy.orm import joinedload

def get_last_sales(limit=50):
    return (
        Sale.query
        .options(joinedload(Sale.customer))  # carga los datos del cliente
        .order_by(Sale.created_at.desc())
        .limit(limit)
        .all()
    )

def get_sale_by_id(sale_id):
    """Trae una venta por su ID"""
    return Sale.query.get(sale_id)

def create_sale(data):
    sale = Sale(**data)
    db.session.add(sale)
    db.session.commit()
    return sale

def update_sale(sale, data):
    """Actualiza los campos de una venta existente"""
    for key, value in data.items():
        if hasattr(sale, key):
            setattr(sale, key, value)
    db.session.commit()
    return sale

def delete_sale(sale):
    """Elimina una venta"""
    db.session.delete(sale)
    db.session.commit()
