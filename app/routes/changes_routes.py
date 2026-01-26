# app/routes/changes_routes.py
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from app.services.reports_service import get_changes_stats, mark_change_received
from app.serializers.sales_serializer import sales_to_dict

changes_bp = Blueprint("changes", __name__, url_prefix="/changes")


@changes_bp.get("/")
@login_required
def changes_view():
    """Vista de gestión de cambios"""
    return render_template("changes.html")


@changes_bp.get("/stats")
@login_required
def get_stats():
    """API: Estadísticas de cambios"""
    stats = get_changes_stats()
    
    return jsonify({
        'total_pending': stats['pending_count'],
        'total_overdue': stats['overdue_count'],
        'pending': [sales_to_dict(s) for s in stats['pending_sales']],
        'overdue': [sales_to_dict(s) for s in stats['overdue_sales']]
    })


@changes_bp.post("/<int:sale_id>/mark-received")
@login_required
def mark_received(sale_id):
    """API: Marcar cambio como recepcionado"""
    sale, message = mark_change_received(sale_id)
    
    if not sale:
        return jsonify({'error': message}), 400
    
    return jsonify({
        'message': message,
        'sale': sales_to_dict(sale)
    })