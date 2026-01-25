from datetime import datetime
from sqlalchemy import and_
from app.models.sale import Sale
from app.extensions import db


def get_retiro_pending():
    """Obtiene pedidos de retiro pendientes (no entregados Y pagados)"""
    return (
        Sale.query
        .filter(
            Sale.delivery_type == 'retiro',
            Sale.delivered_at.is_(None),
            Sale.paid.is_(True)  # 🔹 SOLO PAGADOS
        )
        .order_by(Sale.created_at.asc())
        .all()
    )


def get_retiro_overdue():
    """Obtiene pedidos de retiro vencidos (>15 días sin retirar)"""
    sales = get_retiro_pending()
    return [s for s in sales if s.is_overdue]


def get_correo_pending():
    """Obtiene pedidos de correo pendientes (no enviados Y pagados)"""
    return (
        Sale.query
        .filter(
            Sale.delivery_type == 'correo',
            Sale.delivered_at.is_(None),
            Sale.paid.is_(True)  # 🔹 SOLO PAGADOS
        )
        .order_by(Sale.created_at.asc())
        .all()
    )


def get_correo_overdue():
    """Obtiene pedidos de correo vencidos (>10 días sin enviar)"""
    sales = get_correo_pending()
    return [s for s in sales if s.is_overdue]


def mark_as_delivered(sale_id):
    """Marca un pedido como entregado"""
    sale = Sale.query.get(sale_id)
    
    if not sale:
        return None, "Venta no encontrada"
    
    if sale.is_delivered:
        return None, "El pedido ya fue entregado"
    
    sale.delivered_at = datetime.utcnow()
    sale.completed_at = datetime.utcnow()
    
    db.session.commit()
    
    return sale, "Pedido marcado como entregado"


def mark_as_shipped(sale_id):
    """Marca un pedido de correo como enviado"""
    sale = Sale.query.get(sale_id)
    
    if not sale:
        return None, "Venta no encontrada"
    
    if sale.delivery_type != 'correo':
        return None, "Solo pedidos de correo pueden marcarse como enviados"
    
    if sale.is_delivered:
        return None, "El pedido ya fue enviado"
    
    sale.shipped_at = datetime.utcnow()
    sale.delivered_at = datetime.utcnow()
    sale.completed_at = datetime.utcnow()
    
    db.session.commit()
    
    return sale, "Pedido marcado como enviado"


def get_retiro_stats():
    """Estadísticas de retiros"""
    pending = get_retiro_pending()
    overdue = [s for s in pending if s.is_overdue]
    
    return {
        'total_pending': len(pending),
        'total_overdue': len(overdue),
        'pending_sales': pending,
        'overdue_sales': overdue
    }


def get_correo_stats():
    """Estadísticas de correo"""
    pending = get_correo_pending()
    overdue = [s for s in pending if s.is_overdue]
    
    return {
        'total_pending': len(pending),
        'total_overdue': len(overdue),
        'pending_sales': pending,
        'overdue_sales': overdue
    }