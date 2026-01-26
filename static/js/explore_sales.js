// ----------------------------
// Autocompletado de cliente
// ----------------------------
const input = document.getElementById('customer-input');
const suggestions = document.getElementById('customer-suggestions');
const customerIdInput = document.getElementById('customer_id');
let timeout = null;

if (input) {
    input.addEventListener('input', () => {
        clearTimeout(timeout);
        const query = input.value.trim();
        if (!query) {
            suggestions.innerHTML = '';
            customerIdInput.value = '';
            return;
        }

        timeout = setTimeout(() => {
            fetch(`/customers/search?q=${encodeURIComponent(query)}`)
                .then(res => res.json())
                .then(data => {
                    suggestions.innerHTML = '';
                    data.slice(0, 5).forEach(c => {
                        const div = document.createElement('div');
                        div.classList.add('suggestion-item');
                        div.textContent = `${c.first_name} ${c.last_name} (${c.city})`;
                        div.addEventListener('click', () => {
                            input.value = `${c.first_name} ${c.last_name}`;
                            customerIdInput.value = c.id;
                            suggestions.innerHTML = '';
                        });
                        suggestions.appendChild(div);
                    });
                })
                .catch(err => console.error(err));
        }, 300);
    });

    input.addEventListener('blur', () => {
        setTimeout(() => suggestions.innerHTML = '', 100);
    });
}

// ----------------------------
// Toast
// ----------------------------
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

// ----------------------------
// Formatear montos
// ----------------------------
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.amount').forEach(td => {
        const amount = parseFloat(td.dataset.amount);
        td.textContent = amount.toLocaleString('es-AR', {
            style: 'currency',
            currency: 'ARS',
            minimumFractionDigits: 0
        });
    });
});

// ----------------------------
// Ir a página manteniendo filtros
// ----------------------------
function goToPage(pageNum) {
    const form = document.getElementById('filterForm');
    const formData = new FormData(form);
    
    const params = new URLSearchParams();
    for (let [key, value] of formData.entries()) {
        if (value) params.append(key, value);
    }
    params.set('page', pageNum);
    
    window.location.href = '/sales/explore?' + params.toString();
}

// ----------------------------
// Borrar venta
// ----------------------------
async function deleteSale(saleId) {
    if (!confirm(`¿Eliminar venta #${saleId}?`)) return;
    
    try {
        const res = await fetch(`/sales/${saleId}`, { method: "DELETE" });
        const result = await res.json();
        
        if (res.ok) {
            showToast(result.message || "Venta eliminada", "success");
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(result.error || "Error al eliminar", "error");
        }
    } catch (error) {
        console.error(error);
        showToast("Error al eliminar venta", "error");
    }
}

// ----------------------------
// Marcar como pagado
// ----------------------------
async function markSalePaid(saleId) {
    try {
        const res = await fetch(`/sales/${saleId}/mark_paid`, { 
            method: 'POST', 
            headers: {'Content-Type': 'application/json'} 
        });
        
        const data = await res.json();
        
        if (res.ok) {
            showToast(data.message, "success");
            
            // 🔹 Actualizar visualmente sin recargar
            const row = document.querySelector(`button[onclick="markSalePaid(${saleId})"]`)?.closest('tr');
            if (row) {
                const paidCell = row.querySelector('.paid-status');
                if (paidCell) paidCell.textContent = "Si";
                
                const payBtn = row.querySelector(`button[onclick="markSalePaid(${saleId})"]`);
                if (payBtn) payBtn.remove();
            }
        } else {
            showToast(data.error || 'Error al marcar como pagado', 'error');
        }
    } catch (error) {
        console.error(error);
        showToast('Error al procesar solicitud', 'error');
    }
}

// ----------------------------
// 🔹 MODAL DE EDICIÓN
// ----------------------------
const editModal = document.getElementById('editSaleModal');
const editForm = document.getElementById('editSaleForm');

async function openEditModal(saleId) {
    try {
        const res = await fetch(`/sales/${saleId}`);
        if (!res.ok) throw new Error("Error cargando venta");
        
        const sale = await res.json();
        
        // Llenar modal
        document.getElementById('modalSaleId').textContent = saleId;
        document.getElementById('edit_sale_id').value = saleId;
        document.getElementById('edit_amount').value = sale.amount;
        document.getElementById('edit_notes').value = sale.notes || '';
        
        // Pagado
        document.querySelectorAll('input[name="edit_paid"]').forEach(radio => {
            radio.checked = radio.value === (sale.paid ? 'true' : 'false');
        });
        
        // Método pago
        document.querySelectorAll('input[name="edit_payment_method"]').forEach(radio => {
            radio.checked = radio.value === sale.payment_method;
        });
        
        // Tipo entrega
        document.querySelectorAll('input[name="edit_delivery_type"]').forEach(radio => {
            radio.checked = radio.value === sale.delivery_type;
        });
        
        // Fecha envío
        updateShippingDateVisibility();
        if (sale.shipping_date) {
            document.getElementById('edit_shipping_date').value = sale.shipping_date;
        }
        
        // 🔹 Es un cambio
        document.getElementById('edit_has_change').checked = sale.has_change || false;
        
        editModal.style.display = 'block';
        
    } catch (error) {
        console.error(error);
        showToast("Error al cargar venta", "error");
    }
}

function closeEditModal() {
    editModal.style.display = 'none';
}

// Cerrar modal al hacer clic fuera
window.onclick = function(event) {
    if (event.target === editModal) {
        closeEditModal();
    }
}

// Toggle fecha envío según delivery_type
function updateShippingDateVisibility() {
    const deliveryType = document.querySelector('input[name="edit_delivery_type"]:checked')?.value;
    const shippingGroup = document.getElementById('edit_shipping_date_group');
    
    if (deliveryType === 'cadeteria') {
        shippingGroup.style.display = 'block';
    } else {
        shippingGroup.style.display = 'none';
        document.getElementById('edit_shipping_date').value = '';
    }
}

document.querySelectorAll('input[name="edit_delivery_type"]').forEach(radio => {
    radio.addEventListener('change', updateShippingDateVisibility);
});

// Submit modal
editForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const saleId = document.getElementById('edit_sale_id').value;
    const deliveryType = document.querySelector('input[name="edit_delivery_type"]:checked')?.value;
    
    const data = {
        amount: parseFloat(document.getElementById('edit_amount').value),
        notes: document.getElementById('edit_notes').value,
        paid: document.querySelector('input[name="edit_paid"]:checked')?.value === 'true',
        payment_method: document.querySelector('input[name="edit_payment_method"]:checked')?.value,
        delivery_type: deliveryType,
        shipping_date: deliveryType === 'cadeteria' ? document.getElementById('edit_shipping_date').value : null,
        has_change: document.getElementById('edit_has_change').checked  // 🔹 AGREGADO
    };
    
    try {
        const res = await fetch(`/sales/${saleId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await res.json();
        
        if (res.ok) {
            showToast(result.message || "Venta actualizada", "success");
            closeEditModal();
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(result.error || "Error al actualizar", "error");
        }
        
    } catch (error) {
        console.error(error);
        showToast("Error al guardar cambios", "error");
    }
});