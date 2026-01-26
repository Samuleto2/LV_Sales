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
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
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
// CALCULAR HORAS TRANSCURRIDAS
// ======================
function getHoursSince(isoString) {
    const created = new Date(isoString);
    const now = new Date();
    const hours = Math.floor((now - created) / (1000 * 60 * 60));
    return hours;
}

// ======================
// CARGAR CAMBIOS
// ======================
async function loadChanges() {
    try {
        const res = await fetch('/changes/stats');
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
        console.error('Error cargando cambios:', error);
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
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;">No hay cambios</td></tr>';
        return;
    }
    
    sales.forEach(sale => {
        const hours = getHoursSince(sale.created_at);
        const isExpired = hours > 48;
        
        const row = document.createElement('tr');
        row.className = isExpired ? 'row-overdue' : '';
        
        row.innerHTML = `
            <td><strong>#${sale.id}</strong></td>
            <td>${sale.customer_first_name} ${sale.customer_last_name}</td>
            <td>${sale.customer_phone || '-'}</td>
            <td>${formatMoney(sale.amount)}</td>
            <td class="${isExpired ? 'days-overdue' : 'days-ok'}">${hours} hs</td>
            <td>${formatDate(sale.created_at)}</td>
            <td>${sale.notes || '-'}</td>
            <td>
                <button class="btn-deliver" onclick="markAsReceived(${sale.id})">
                    ✅ Recibido
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// ======================
// MARCAR COMO RECIBIDO
// ======================
async function markAsReceived(saleId) {
    if (!confirm(`¿Marcar cambio #${saleId} como recibido?`)) return;
    
    try {
        const res = await fetch(`/changes/${saleId}/mark-received`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await res.json();
        
        if (res.ok) {
            showToast(data.message);
            loadChanges(); // Recargar tabla
        } else {
            showToast(data.error || 'Error al marcar como recibido', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al procesar solicitud', 'error');
    }
}

// ======================
// INIT
// ======================
document.addEventListener('DOMContentLoaded', loadChanges);