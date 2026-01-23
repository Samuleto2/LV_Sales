from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from app.services.delivery_services import (
    get_retiro_stats,
    get_correo_stats,
    mark_as_delivered,
    mark_as_shipped
)
from app.serializers.sales_serializer import sales_to_dict

delivery_bp = Blueprint("delivery", __name__, url_prefix="/delivery")


@delivery_bp.get("/retiro")
@login_required
def retiro_view():
    """Vista de gestión de retiros"""
    return render_template("retiro.html")


@delivery_bp.get("/correo")
@login_required
def correo_view():
    """Vista de gestión de correo"""
    return render_template("correo.html")


@delivery_bp.get("/retiro/stats")
@login_required
def retiro_stats():
    """API: Estadísticas de retiros"""
    stats = get_retiro_stats()
    
    return jsonify({
        'total_pending': stats['total_pending'],
        'total_overdue': stats['total_overdue'],
        'pending': [sales_to_dict(s) for s in stats['pending_sales']],
        'overdue': [sales_to_dict(s) for s in stats['overdue_sales']]
    })


@delivery_bp.get("/correo/stats")
@login_required
def correo_stats():
    """API: Estadísticas de correo"""
    stats = get_correo_stats()
    
    return jsonify({
        'total_pending': stats['total_pending'],
        'total_overdue': stats['total_overdue'],
        'pending': [sales_to_dict(s) for s in stats['pending_sales']],
        'overdue': [sales_to_dict(s) for s in stats['overdue_sales']]
    })


@delivery_bp.post("/retiro/<int:sale_id>/mark-delivered")
@login_required
def mark_retiro_delivered(sale_id):
    """API: Marcar retiro como entregado"""
    sale, message = mark_as_delivered(sale_id)
    
    if not sale:
        return jsonify({'error': message}), 400
    
    return jsonify({
        'message': message,
        'sale': sales_to_dict(sale)
    })


@delivery_bp.post("/correo/<int:sale_id>/mark-shipped")
@login_required
def mark_correo_shipped(sale_id):
    """API: Marcar correo como enviado"""
    sale, message = mark_as_shipped(sale_id)
    
    if not sale:
        return jsonify({'error': message}), 400
    
    return jsonify({
        'message': message,
        'sale': sales_to_dict(sale)
    })