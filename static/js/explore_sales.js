// ----------------------------
// CONSTANTES
// ----------------------------
const STORAGE_KEY = 'turnSales';

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
                    data.slice(0,5).forEach(c => {
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
// Función para actualizar venta en localStorage
// ----------------------------
function updateSaleInStorage(saleId, updatedData) {
    let turnSales = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
    
    const index = turnSales.findIndex(s => s.id === saleId);
    
    if (index !== -1) {
        // Actualizar venta existente
        turnSales[index] = {
            ...turnSales[index],
            ...updatedData,
            amount: Number(updatedData.amount) || turnSales[index].amount,
            paid: !!updatedData.paid
        };
        
        localStorage.setItem(STORAGE_KEY, JSON.stringify(turnSales));
        console.log(`✅ Venta #${saleId} actualizada en dashboard`);
    } else {
        console.log(`ℹ️ Venta #${saleId} no está en el dashboard del turno actual`);
    }
}

// ----------------------------
// Función para eliminar venta del localStorage
// ----------------------------
function removeSaleFromStorage(saleId) {
    let turnSales = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
    
    const filtered = turnSales.filter(s => s.id !== saleId);
    
    if (filtered.length !== turnSales.length) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
        console.log(`✅ Venta #${saleId} eliminada del dashboard`);
    }
}

// ----------------------------
// Recargar tabla de ventas
// ----------------------------
async function loadSales(page = 1) {
    const params = new URLSearchParams();
    const customer = input.value;
    const payment_method = document.querySelector('input[name="payment_method"]').value;
    const paid = document.querySelector('select[name="paid"]').value;
    const date_from = document.querySelector('input[name="date_from"]').value;
    const date_to = document.querySelector('input[name="date_to"]').value;

    if (customer) params.append('customer', customer);
    if (payment_method) params.append('payment_method', payment_method);
    if (paid) params.append('paid', paid);
    if (date_from) params.append('date_from', date_from);
    if (date_to) params.append('date_to', date_to);
    params.append('page', page);

    const res = await fetch(`/sales/explore?${params.toString()}`);
    const html = await res.text();

    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const newTbody = doc.querySelector('#salesTable tbody');
    document.querySelector("#salesTable tbody").innerHTML = newTbody.innerHTML;

    // Reasignar eventos
    document.querySelectorAll('.button-delete').forEach(btn => {
        btn.addEventListener('click', () => deleteSale(btn.dataset.url, btn));
    });
    document.querySelectorAll('.btn-pay').forEach(btn => {
        btn.addEventListener('click', () => markSalePaid(btn.dataset.sale, btn));
    });

    // Formatear montos
    document.querySelectorAll('.amount').forEach(td => {
        const amount = parseFloat(td.dataset.amount);
        td.textContent = amount.toLocaleString('es-AR', {
            style: 'currency',
            currency: 'ARS',
            minimumFractionDigits: 0
        });
    });
}

// ----------------------------
// Borrar venta
// ----------------------------
async function deleteSale(url, btnElement) {
    if (!confirm("¿Eliminar venta?")) return;
    
    // Extraer ID de la URL
    const saleId = parseInt(url.match(/\/(\d+)$/)[1]);
    
    const res = await fetch(url, { method: "DELETE" });
    const result = await res.json();
    showToast(result.message || "Venta eliminada");
    
    // 🔹 ACTUALIZAR LOCALSTORAGE
    removeSaleFromStorage(saleId);
    
    loadSales();
}

// ----------------------------
// Marcar venta como pagada
// ----------------------------
async function markSalePaid(saleId, btnElement) {
    const res = await fetch(`/sales/${saleId}/mark_paid`, { 
        method: 'POST', 
        headers: {'Content-Type': 'application/json'} 
    });
    
    const data = await res.json();
    
    if (data.message) {
        showToast(data.message);
        
        // 🔹 ACTUALIZAR LOCALSTORAGE
        // Obtener el monto de la fila
        const row = btnElement.closest('tr');
        const amountCell = row.querySelector('.amount');
        const amount = parseFloat(amountCell.dataset.amount);
        
        updateSaleInStorage(parseInt(saleId), {
            paid: true,
            amount: amount
        });
        
        loadSales();
    }
}

// ----------------------------
// Inicializamos tabla al cargar la página
// ----------------------------
document.addEventListener('DOMContentLoaded', () => loadSales());