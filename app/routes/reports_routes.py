# app/routes/reports_routes.py
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from datetime import datetime, timedelta
from app.services.reports_service import (
    get_sales_summary,
    get_sales_by_channel,
    get_sales_by_delivery_type,
    get_daily_sales,
    get_top_customers,
    compare_periods,
    get_changes_stats,
    get_monthly_changes_trend,
    mark_change_received
)
from app.services.sales_services import today_ar
from app.serializers.sales_serializer import sales_to_dict

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")

# PIN de acceso (debería estar en variables de entorno)
REPORTS_PIN = "1234"  # 🔹 Cambiar en producción


@reports_bp.get("/")
@login_required
def reports_view():
    """Vista principal de reportes"""
    return render_template("reports.html")


@reports_bp.post("/verify-pin")
@login_required
def verify_pin():
    """Verificar PIN de acceso"""
    data = request.get_json()
    pin = data.get('pin', '')
    
    if pin == REPORTS_PIN:
        return jsonify({'valid': True}), 200
    
    return jsonify({'valid': False, 'message': 'PIN incorrecto'}), 401


@reports_bp.get("/dashboard")
@login_required
def get_dashboard():
    """Datos principales del dashboard"""
    today = today_ar()
    
    # Mes actual vs mes anterior
    current_month_start = today.replace(day=1)
    current_month_end = today
    
    if today.month == 1:
        previous_month_start = today.replace(year=today.year - 1, month=12, day=1)
        previous_month_end = today.replace(year=today.year - 1, month=12, day=31)
    else:
        previous_month_start = today.replace(month=today.month - 1, day=1)
        # Último día del mes anterior
        previous_month_end = current_month_start - timedelta(days=1)
    
    comparison = compare_periods(
        current_month_start, current_month_end,
        previous_month_start, previous_month_end
    )
    
    return jsonify({
        'comparison': comparison,
        'channels': get_sales_by_channel(current_month_start, current_month_end),
        'delivery_types': get_sales_by_delivery_type(current_month_start, current_month_end),
        'daily_sales': get_daily_sales(today - timedelta(days=30), today),
        'top_customers': get_top_customers(current_month_start, current_month_end, limit=5)
    })


@reports_bp.get("/sales-summary")
@login_required
def sales_summary():
    """Resumen de ventas con filtros"""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    start_date = datetime.fromisoformat(start_date_str).date() if start_date_str else None
    end_date = datetime.fromisoformat(end_date_str).date() if end_date_str else None
    
    summary = get_sales_summary(start_date, end_date)
    channels = get_sales_by_channel(start_date, end_date)
    delivery = get_sales_by_delivery_type(start_date, end_date)
    
    return jsonify({
        'summary': summary,
        'by_channel': channels,
        'by_delivery': delivery
    })


@reports_bp.get("/changes-stats")
@login_required
def changes_stats():
    """Estadísticas de cambios"""
    stats = get_changes_stats()
    trend = get_monthly_changes_trend(months=6)
    
    return jsonify({
        'stats': {
            'total_changes': stats['total_changes'],
            'pending_count': stats['pending_count'],
            'overdue_count': stats['overdue_count'],
            'changes_this_month': stats['changes_this_month']
        },
        'trend': trend,
        'pending': [sales_to_dict(s) for s in stats['pending_sales']],
        'overdue': [sales_to_dict(s) for s in stats['overdue_sales']]
    })


@reports_bp.get("/top-customers")
@login_required
def top_customers():
    """Top clientes con filtros"""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    limit = int(request.args.get('limit', 10))
    
    start_date = datetime.fromisoformat(start_date_str).date() if start_date_str else None
    end_date = datetime.fromisoformat(end_date_str).date() if end_date_str else None
    
    customers = get_top_customers(start_date, end_date, limit)
    
    return jsonify(customers)