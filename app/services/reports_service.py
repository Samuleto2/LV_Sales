# app/services/reports_service.py
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from app.models.sale import Sale
from app.models.customer import Customer
from app.extensions import db
from app.services.sales_services import now_ar, today_ar


def get_date_range(period='month'):
    """Retorna rango de fechas según período"""
    today = today_ar()
    
    if period == 'week':
        start = today - timedelta(days=today.weekday())  # Lunes
        end = today
    elif period == 'month':
        start = today.replace(day=1)
        end = today
    elif period == 'year':
        start = today.replace(month=1, day=1)
        end = today
    else:
        start = end = today
    
    return start, end


def get_sales_summary(start_date=None, end_date=None):
    """
    Resumen general de ventas
    """
    if not start_date:
        start_date = today_ar().replace(day=1)  # Primer día del mes
    if not end_date:
        end_date = today_ar()
    
    query = Sale.query.filter(
        Sale.created_at >= datetime.combine(start_date, datetime.min.time()),
        Sale.created_at <= datetime.combine(end_date, datetime.max.time())
    )
    
    total_sales = query.count()
    total_amount = db.session.query(func.sum(Sale.amount)).filter(
        Sale.created_at >= datetime.combine(start_date, datetime.min.time()),
        Sale.created_at <= datetime.combine(end_date, datetime.max.time())
    ).scalar() or 0
    
    paid_sales = query.filter(Sale.paid == True).count()
    unpaid_sales = query.filter(Sale.paid == False).count()
    
    paid_amount = db.session.query(func.sum(Sale.amount)).filter(
        Sale.created_at >= datetime.combine(start_date, datetime.min.time()),
        Sale.created_at <= datetime.combine(end_date, datetime.max.time()),
        Sale.paid == True
    ).scalar() or 0
    
    unpaid_amount = db.session.query(func.sum(Sale.amount)).filter(
        Sale.created_at >= datetime.combine(start_date, datetime.min.time()),
        Sale.created_at <= datetime.combine(end_date, datetime.max.time()),
        Sale.paid == False
    ).scalar() or 0
    
    avg_ticket = total_amount / total_sales if total_sales > 0 else 0
    
    return {
        'total_sales': total_sales,
        'total_amount': float(total_amount),
        'paid_sales': paid_sales,
        'paid_amount': float(paid_amount),
        'unpaid_sales': unpaid_sales,
        'unpaid_amount': float(unpaid_amount),
        'avg_ticket': float(avg_ticket)
    }


def get_sales_by_channel(start_date=None, end_date=None):
    """Ventas agrupadas por canal"""
    if not start_date:
        start_date = today_ar().replace(day=1)
    if not end_date:
        end_date = today_ar()
    
    results = (
        db.session.query(
            Sale.sales_channel,
            func.count(Sale.id).label('count'),
            func.sum(Sale.amount).label('total')
        )
        .filter(
            Sale.created_at >= datetime.combine(start_date, datetime.min.time()),
            Sale.created_at <= datetime.combine(end_date, datetime.max.time())
        )
        .group_by(Sale.sales_channel)
        .all()
    )
    
    return [
        {
            'channel': r.sales_channel,
            'count': r.count,
            'total': float(r.total or 0)
        }
        for r in results
    ]


def get_sales_by_delivery_type(start_date=None, end_date=None):
    """Ventas agrupadas por tipo de entrega"""
    if not start_date:
        start_date = today_ar().replace(day=1)
    if not end_date:
        end_date = today_ar()
    
    results = (
        db.session.query(
            Sale.delivery_type,
            func.count(Sale.id).label('count'),
            func.sum(Sale.amount).label('total')
        )
        .filter(
            Sale.created_at >= datetime.combine(start_date, datetime.min.time()),
            Sale.created_at <= datetime.combine(end_date, datetime.max.time())
        )
        .group_by(Sale.delivery_type)
        .all()
    )
    
    return [
        {
            'type': r.delivery_type,
            'count': r.count,
            'total': float(r.total or 0)
        }
        for r in results
    ]


def get_daily_sales(start_date=None, end_date=None):
    """Ventas diarias para gráficos"""
    if not start_date:
        start_date = today_ar() - timedelta(days=30)
    if not end_date:
        end_date = today_ar()
    
    results = (
        db.session.query(
            func.date(Sale.created_at).label('date'),
            func.count(Sale.id).label('count'),
            func.sum(Sale.amount).label('total')
        )
        .filter(
            Sale.created_at >= datetime.combine(start_date, datetime.min.time()),
            Sale.created_at <= datetime.combine(end_date, datetime.max.time())
        )
        .group_by(func.date(Sale.created_at))
        .order_by(func.date(Sale.created_at))
        .all()
    )
    
    return [
        {
            'date': r.date.isoformat(),
            'count': r.count,
            'total': float(r.total or 0)
        }
        for r in results
    ]


def get_top_customers(start_date=None, end_date=None, limit=10):
    """Clientes con más compras"""
    if not start_date:
        start_date = today_ar().replace(day=1)
    if not end_date:
        end_date = today_ar()
    
    results = (
        db.session.query(
            Customer.id,
            Customer.first_name,
            Customer.last_name,
            func.count(Sale.id).label('purchases'),
            func.sum(Sale.amount).label('total')
        )
        .join(Sale)
        .filter(
            Sale.created_at >= datetime.combine(start_date, datetime.min.time()),
            Sale.created_at <= datetime.combine(end_date, datetime.max.time())
        )
        .group_by(Customer.id, Customer.first_name, Customer.last_name)
        .order_by(func.sum(Sale.amount).desc())
        .limit(limit)
        .all()
    )
    
    return [
        {
            'id': r.id,
            'name': f"{r.first_name} {r.last_name}",
            'purchases': r.purchases,
            'total': float(r.total or 0)
        }
        for r in results
    ]


def compare_periods(current_start, current_end, previous_start, previous_end):
    """Comparar dos períodos"""
    current = get_sales_summary(current_start, current_end)
    previous = get_sales_summary(previous_start, previous_end)
    
    def calc_change(current_val, previous_val):
        if previous_val == 0:
            return 100 if current_val > 0 else 0
        return ((current_val - previous_val) / previous_val) * 100
    
    return {
        'current': current,
        'previous': previous,
        'changes': {
            'sales_count': calc_change(current['total_sales'], previous['total_sales']),
            'total_amount': calc_change(current['total_amount'], previous['total_amount']),
            'avg_ticket': calc_change(current['avg_ticket'], previous['avg_ticket'])
        }
    }


def get_changes_stats():
    """
    Estadísticas de cambios (has_change=True)
    """
    # Cambios totales
    total_changes = Sale.query.filter(Sale.has_change == True).count()
    
    # Cambios pendientes (no entregados y no vencidos)
    pending_changes = (
        Sale.query
        .filter(
            Sale.has_change == True,
            Sale.delivered_at.is_(None)
        )
        .all()
    )
    
    # Filtrar vencidos (>48 horas)
    now = now_ar()
    overdue = []
    pending = []
    
    for sale in pending_changes:
        sale_created = sale.created_at

        # Si viene naive, asumimos UTC y lo llevamos a AR usando now_ar como referencia
        if sale_created.tzinfo is None:
            sale_created = sale_created.replace(tzinfo=now.tzinfo)

        hours_since = (now - sale_created).total_seconds() / 3600

        if hours_since > 48:
            overdue.append(sale)
        else:
            pending.append(sale)
        
        if hours_since > 48:
            overdue.append(sale)
        else:
            pending.append(sale)
    
    # Cambios del mes
    start_of_month = today_ar().replace(day=1)
    changes_this_month = (
        Sale.query
        .filter(
            Sale.has_change == True,
            Sale.created_at >= datetime.combine(start_of_month, datetime.min.time())
        )
        .count()
    )
    
    return {
        'total_changes': total_changes,
        'pending_count': len(pending),
        'overdue_count': len(overdue),
        'changes_this_month': changes_this_month,
        'pending_sales': pending,
        'overdue_sales': overdue
    }


def get_monthly_changes_trend(months=6):
    """Tendencia de cambios por mes"""
    today = today_ar()
    results = []
    
    for i in range(months):
        target_month = today - timedelta(days=30 * i)
        start = target_month.replace(day=1)
        
        # Último día del mes
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = start.replace(month=start.month + 1, day=1) - timedelta(days=1)
        
        count = (
            Sale.query
            .filter(
                Sale.has_change == True,
                Sale.created_at >= datetime.combine(start, datetime.min.time()),
                Sale.created_at <= datetime.combine(end, datetime.max.time())
            )
            .count()
        )
        
        results.append({
            'month': start.strftime('%b %Y'),
            'count': count
        })
    
    return list(reversed(results))


def mark_change_received(sale_id):
    """Marcar cambio como recibido"""
    sale = Sale.query.get(sale_id)
    
    if not sale:
        return None, "Venta no encontrada"
    
    if not sale.has_change:
        return None, "Esta venta no es un cambio"
    
    if sale.delivered_at:
        return None, "El cambio ya fue recepcionado"
    
    sale.delivered_at = now_ar()
    sale.completed_at = now_ar()
    
    db.session.commit()
    
    return sale, "Cambio marcado como recepcionado"