# models/sale.py
from datetime import datetime
from app.extensions import db

class Sale(db.Model):
    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)
    paid = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ##Update logistics
    has_shipping = db.Column(db.Boolean, default=False)
    shipping_date = db.Column(db.Date, nullable=True)
    sales_channel = db.Column(db.String(20), nullable=False)
    is_cash = db.Column(db.Boolean, default=False, nullable=False)
    has_change = db.Column(db.Boolean, default=False, nullable=False)
    delivery_type = db.Column(db.String(20), nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    

    customer = db.relationship("Customer", back_populates="sales")
