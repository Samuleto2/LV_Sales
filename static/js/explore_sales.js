// ----------------------------
// Autocompletado de cliente
// ----------------------------
const input = document.getElementById('customer-input');
const suggestions = document.getElementById('customer-suggestions');
const customerIdInput = document.getElementById('customer_id'); // input hidden
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
        btn.addEventListener('click', () => deleteSale(btn.dataset.url));
    });
    document.querySelectorAll('.btn-pay').forEach(btn => {
        btn.addEventListener('click', () => markSalePaid(btn.dataset.sale));
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
async function deleteSale(url) {
    if (!confirm("¿Eliminar venta?")) return;
    const res = await fetch(url, { method: "DELETE" });
    const result = await res.json();
    showToast(result.message || "Venta eliminada");
    loadSales();
}

// ----------------------------
// Marcar venta como pagada
// ----------------------------
function markSalePaid(saleId) {
    fetch(`/sales/${saleId}/mark_paid`, { method: 'POST', headers: {'Content-Type': 'application/json'} })
        .then(res => res.json())
        .then(data => {
            if (data.message) {
                showToast(data.message);
                loadSales();
            }
        })
        .catch(err => console.error(err));
}

// ----------------------------
// Inicializamos tabla al cargar la página
// ----------------------------
document.addEventListener('DOMContentLoaded', () => loadSales());
