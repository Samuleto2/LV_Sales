// ======================
// TOAST
// ======================
function showToast(message, type = "success") {
    const toast = document.createElement("div");
    toast.textContent = message;
    toast.style.position = "fixed";
    toast.style.top = "20px";
    toast.style.right = "20px";
    toast.style.padding = "10px 20px";
    toast.style.borderRadius = "5px";
    toast.style.backgroundColor = type === "success" ? "#4caf50" : "#f44336";
    toast.style.color = "white";
    toast.style.zIndex = 9999;
    toast.style.boxShadow = "0 2px 6px rgba(0,0,0,0.2)";
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// ======================
// FORMATEAR FECHA
// ======================
function formatDate(isoString) {
    if (!isoString) return "";
    const date = new Date(isoString);
    return date.toLocaleString('es-AR', { 
        day: '2-digit', 
        month: '2-digit', 
        year: 'numeric' 
    });
}

// ======================
// FORMATEAR DINERO
// ======================
function formatMoney(amount) {
    return Number(amount).toLocaleString('es-AR', {
        style: 'currency',
        currency: 'ARS',
        minimumFractionDigits: 0
    });
}

// ======================
// CARGAR RETIROS
// ======================
async function loadRetiros() {
    try {
        const res = await fetch('/delivery/retiro/stats');
        const data = await res.json();
        
        // Actualizar dashboard
        document.getElementById('totalPending').textContent = data.total_pending;
        document.getElementById('totalOverdue').textContent = data.total_overdue;
        
        // Mostrar/ocultar sección de vencidos
        const overdueSection = document.getElementById('overdueSection');
        if (data.total_overdue > 0) {
            overdueSection.style.display = 'block';
            renderTable('overdueTable', data.overdue, true);
        } else {
            overdueSection.style.display = 'none';
        }
        
        // Renderizar tabla de pendientes
        renderTable('pendingTable', data.pending, false);
        
    } catch (error) {
        console.error('Error cargando retiros:', error);
        showToast('Error al cargar datos', 'error');
    }
}

// ======================
// RENDERIZAR TABLA
// ======================
function renderTable(tableId, sales, isOverdue) {
    const tbody = document.getElementById(tableId);
    tbody.innerHTML = '';
    
    if (!sales.length) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;">No hay pedidos</td></tr>';
        return;
    }
    
    sales.forEach(sale => {
        const days = sale.days_since_creation || 0;
        const isVencido = days > 15;
        
        const row = document.createElement('tr');
        row.className = isVencido ? 'row-overdue' : '';
        
        row.innerHTML = `
            <td><strong>#${sale.id}</strong></td>
            <td>${sale.customer_first_name} ${sale.customer_last_name}</td>
            <td>${sale.customer_phone || '-'}</td>
            <td>${formatMoney(sale.amount)}</td>
            <td class="${isVencido ? 'days-overdue' : 'days-ok'}">${days} días</td>
            <td>${formatDate(sale.created_at)}</td>
            <td>${sale.notes || '-'}</td>
            <td>
                <button class="btn btn-deliver" onclick="markAsDelivered(${sale.id})">
                     Entregado
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// ======================
// MARCAR COMO ENTREGADO
// ======================
async function markAsDelivered(saleId) {
    if (!confirm(`¿Marcar pedido #${saleId} como entregado?`)) return;
    
    try {
        const res = await fetch(`/delivery/retiro/${saleId}/mark-delivered`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await res.json();
        
        if (res.ok) {
            showToast(data.message);
            loadRetiros(); // Recargar tabla
        } else {
            showToast(data.error || 'Error al marcar como entregado', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al procesar solicitud', 'error');
    }
}

// ======================
// INIT
// ======================
document.addEventListener('DOMContentLoaded', loadRetiros);