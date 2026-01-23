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
    

     # 🔹 NUEVO: Tracking de entregas
    delivered_at = db.Column(db.DateTime, nullable=True)  # Cuando se entregó/envió
    shipped_at = db.Column(db.DateTime, nullable=True)    # Para correo: cuando se despachó
    completed_at = db.Column(db.DateTime, nullable=True)  # Ya existía
    
    customer = db.relationship("Customer", back_populates="sales")
    
    # 🔹 NUEVO: Propiedades calculadas
    @property
    def is_delivered(self):
        """Retorna True si ya fue entregado/enviado"""
        return self.delivered_at is not None
    
    @property
    def days_since_creation(self):
        """Días desde que se creó la venta"""
        if not self.created_at:
            return 0
        delta = datetime.utcnow() - self.created_at
        return delta.days
    
    @property
    def is_overdue(self):
        """Retorna True si está vencido según tipo de entrega"""
        if self.is_delivered:
            return False
            
        if self.delivery_type == 'retiro':
            return self.days_since_creation > 15
        elif self.delivery_type == 'correo':
            return self.days_since_creation > 10
        
        return False
