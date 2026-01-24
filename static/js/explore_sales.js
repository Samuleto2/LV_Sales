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
// Variables de paginación
// ----------------------------
let currentPage = 1;
let totalPages = 1;

// ----------------------------
// Recargar tabla de ventas
// ----------------------------
async function loadSales(page = 1) {
    const params = new URLSearchParams();
    const customerId = customerIdInput.value;
    const payment_method = document.querySelector('input[name="payment_method"]').value;
    const paid = document.querySelector('select[name="paid"]').value;
    const date_from = document.querySelector('input[name="date_from"]').value;
    const date_to = document.querySelector('input[name="date_to"]').value;

    if (customerId) params.append('customer_id', customerId);
    if (payment_method) params.append('payment_method', payment_method);
    if (paid) params.append('paid', paid);
    if (date_from) params.append('date_from', date_from);
    if (date_to) params.append('date_to', date_to);
    params.append('page', page);

    try {
        const res = await fetch(`/sales/explore/json?${params.toString()}`);
        const data = await res.json();

        const tbody = document.querySelector("#salesTable tbody");
        tbody.innerHTML = '';

        if (!data.sales.length) {
            tbody.innerHTML = "<tr><td colspan='8'>Sin resultados</td></tr>";
            return;
        }

        data.sales.forEach(s => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${s.customer_name}</td>
                <td>${s.sale_date}</td>
                <td class="amount" data-amount="${s.amount}">${s.amount}</td>
                <td>${s.payment_method}</td>
                <td>${s.paid ? 'Sí' : 'No'}</td>
                <td>${s.delivery_type || ''}</td>
                <td><button class="btn btn-pay" data-sale="${s.id}" ${s.paid ? 'disabled' : ''}>Pagar</button></td>
                <td><button class="button-delete" data-url="/sales/${s.id}">Eliminar</button></td>
            `;
            tbody.appendChild(tr);
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

        // Reasignar eventos
        document.querySelectorAll('.button-delete').forEach(btn => {
            btn.addEventListener('click', () => deleteSale(btn.dataset.url));
        });
        document.querySelectorAll('.btn-pay').forEach(btn => {
            btn.addEventListener('click', () => markSalePaid(btn.dataset.sale));
        });

        // Actualizar paginación
        currentPage = data.page;
        totalPages = data.total_pages;
        renderPagination();
    } catch (err) {
        console.error(err);
        showToast("Error cargando ventas", "error");
    }
}

// ----------------------------
// Renderizar paginación
// ----------------------------
function renderPagination() {
    const paginationDiv = document.getElementById('pagination');
    if (!paginationDiv) return;

    paginationDiv.innerHTML = '';

    const prevBtn = document.createElement('button');
    prevBtn.textContent = 'Anterior';
    prevBtn.disabled = currentPage <= 1;
    prevBtn.addEventListener('click', () => loadSales(currentPage - 1));
    paginationDiv.appendChild(prevBtn);

    const nextBtn = document.createElement('button');
    nextBtn.textContent = 'Siguiente';
    nextBtn.disabled = currentPage >= totalPages;
    nextBtn.addEventListener('click', () => loadSales(currentPage + 1));
    paginationDiv.appendChild(nextBtn);

    const info = document.createElement('span');
    info.textContent = ` Página ${currentPage} de ${totalPages} `;
    paginationDiv.appendChild(info);
}

// ----------------------------
// Borrar venta
// ----------------------------
async function deleteSale(url) {
    if (!confirm("¿Eliminar venta?")) return;
    const res = await fetch(url, { method: "DELETE" });
    const result = await res.json();
    showToast(result.message || "Venta eliminada");
    loadSales(currentPage);
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
                loadSales(currentPage);
            }
        })
        .catch(err => console.error(err));
}

// ----------------------------
// Inicializamos tabla al cargar la página
// ----------------------------
document.addEventListener('DOMContentLoaded', () => loadSales());
