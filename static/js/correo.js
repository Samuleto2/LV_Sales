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
// CARGAR CORREOS
// ======================
async function loadCorreos() {
    try {
        const res = await fetch('/delivery/correo/stats');
        const data = await res.json();
        
        // Actualizar dashboard
        document.getElementById('totalPending').textContent = data.total_pending;
        document.getElementById('totalOverdue').textContent = data.total_overdue;
        
        // Mostrar/ocultar sección de demorados
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
        console.error('Error cargando correos:', error);
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
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;">No hay pedidos</td></tr>';
        return;
    }
    
    sales.forEach(sale => {
        const days = sale.days_since_creation || 0;
        const isDemorado = days > 10;
        
        const row = document.createElement('tr');
        row.className = isDemorado ? 'row-overdue' : '';
        
        row.innerHTML = `
            <td><strong>#${sale.id}</strong></td>
            <td>${sale.customer_first_name} ${sale.customer_last_name}</td>
            <td>${sale.customer_address || '-'}</td>
            <td>${sale.customer_city || '-'}</td>
            <td>${formatMoney(sale.amount)}</td>
            <td class="${isDemorado ? 'days-overdue' : 'days-ok'}">${days} días</td>
            <td>${formatDate(sale.created_at)}</td>
            <td>${sale.notes || '-'}</td>
            <td>
                <button class="btn btn-ship" onclick="markAsShipped(${sale.id})">
                     Enviado
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// ======================
// MARCAR COMO ENVIADO
// ======================
async function markAsShipped(saleId) {
    if (!confirm(`¿Marcar pedido #${saleId} como enviado?`)) return;
    
    try {
        const res = await fetch(`/delivery/correo/${saleId}/mark-shipped`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await res.json();
        
        if (res.ok) {
            showToast(data.message);
            loadCorreos(); // Recargar tabla
        } else {
            showToast(data.error || 'Error al marcar como enviado', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al procesar solicitud', 'error');
    }
}

// ======================
// INIT
// ======================
document.addEventListener('DOMContentLoaded', loadCorreos);