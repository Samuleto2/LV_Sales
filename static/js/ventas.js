document.addEventListener("DOMContentLoaded", () => {

    const apiUrl = "http://127.0.0.1:5000/sales";
    const customerSearchUrl = "/customers/search";

    const customerInput = document.querySelector("#customer_name");
    const suggestionsDiv = document.querySelector("#suggestions");
    let selectedCustomer = null; // guardamos cliente seleccionado

    // Buscar clientes al escribir
    customerInput.addEventListener("input", async () => {
        const query = customerInput.value.trim();
        if (!query) {
            suggestionsDiv.innerHTML = "";
            selectedCustomer = null;
            document.querySelector("#customer_info").style.display = "none";
            return;
        }

        const res = await fetch(`${customerSearchUrl}?q=${encodeURIComponent(query)}`);
        const customers = await res.json();

        suggestionsDiv.innerHTML = "";

        customers.forEach(c => {
            const div = document.createElement("div");
            div.textContent = `${c.first_name} ${c.last_name} - ${c.address}, ${c.city}`;
            div.style.padding = "5px";
            div.style.cursor = "pointer";

            div.addEventListener("click", () => {
                // Guardar selección
                customerInput.value = `${c.first_name} ${c.last_name}`;
                selectedCustomer = c;
                document.querySelector("#customer_id").value = c.id;
                suggestionsDiv.innerHTML = "";

                // Mostrar info del cliente
                const infoDiv = document.querySelector("#customer_info");
                document.querySelector("#info_name").textContent = `${c.first_name} ${c.last_name}`;
                document.querySelector("#info_address").textContent = c.address;
                document.querySelector("#info_city").textContent = c.city;
                infoDiv.style.display = "block";
            });

            suggestionsDiv.appendChild(div);
        });
    });
let editingSaleId = null; // null si es nueva venta
    // Crear venta
    document.querySelector("#saleForm").addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!selectedCustomer) {
            alert("Seleccione un cliente válido de la lista");
            return;
        }

        const data = {
            customer_id: selectedCustomer.id,
            amount: parseFloat(document.querySelector("#amount").value),
            payment_method: document.querySelector("#payment_method").value,
            paid: document.querySelector("#paid").value === "true",
            notes: document.querySelector("#notes").value  // <- esto es clave
        };

        let method = "POST";
        let url = apiUrl;
        if (editingSaleId) {
        method = "PUT";
        url += `/${editingSaleId}`;
        }

        const res = await fetch(url, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const result = await res.json();
        alert(result.message || JSON.stringify(result));

        // Reset formulario
        selectedCustomer = null;
        editingSaleId = null;
        customerInput.value = "";
        document.querySelector("#customer_id").value = "";
        document.querySelector("#customer_info").style.display = "none";

        document.querySelector("#saleForm button[type=submit]").textContent = "Crear venta";

        // Función para formatear montos al estilo argentino
        function formatMoney(amount) {
            return amount.toLocaleString('es-AR', {
                style: 'currency',
                currency: 'ARS',
                minimumFractionDigits: 0
            });
        }



        loadSales(); // recargar tabla

        // Limpiar input y reset
        selectedCustomer = null;
        customerInput.value = "";
        document.querySelector("#customer_id").value = "";
        document.querySelector("#customer_info").style.display = "none";

        loadSales(); // recargar tabla de ventas
    });

    function formatMoney(amount) {
        amount = Number(amount) || 0;  // convierte a número, 0 si es inválido
        return amount.toLocaleString('es-AR', {
            style: 'currency',
            currency: 'ARS',
            minimumFractionDigits: 0
        });
    }


// Cargar listado de ventas con botón editar
async function loadSales() {
    const res = await fetch(apiUrl);
    const sales = await res.json();
    const tbody = document.querySelector("#salesTable tbody");
    tbody.innerHTML = "";

    sales.forEach(s => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${s.sale_date}</td>
            <td>${s.customer_first_name} ${s.customer_last_name}</td>
            <td>${formatMoney(s.amount)}</td>
            <td>${s.payment_method}</td>
            <td>${s.paid ? "Si" : "No"}</td>
            <td>
                <button class="button button-edit" onclick="editSale(${s.id})">Editar</button>
                <button class="button button-delete" onclick="deleteSale(${s.id})">Borrar</button>
                <button class="button button-download" onclick="downloadPDF(${s.id})">Descargar comprobante</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Función para precargar venta en formulario
window.editSale = async function(id) {
    const res = await fetch(`${apiUrl}/${id}`);
    const sale = await res.json();

    // Precargar campos
    editingSaleId = id;
    selectedCustomer = { id: sale.customer_id, first_name: sale.customer_first_name, last_name: sale.customer_last_name, address: sale.customer_address, city: sale.customer_city };
    customerInput.value = `${sale.customer_first_name} ${sale.customer_last_name}`;
    document.querySelector("#customer_id").value = sale.customer_id;

    document.querySelector("#amount").value = sale.amount;
    document.querySelector("#payment_method").value = sale.payment_method;
    document.querySelector("#paid").value = sale.paid ? "true" : "false";

    // Mostrar info cliente
    const infoDiv = document.querySelector("#customer_info");
    document.querySelector("#info_name").textContent = `${selectedCustomer.first_name} ${selectedCustomer.last_name}`;
    document.querySelector("#info_address").textContent = selectedCustomer.address;
    document.querySelector("#info_city").textContent = selectedCustomer.city;
    infoDiv.style.display = "block";

    // Cambiar texto del botón
    document.querySelector("#saleForm button[type=submit]").textContent = "Guardar cambios";
    
    
}




    // Borrar venta
    window.deleteSale = async function(id) {
        if (!confirm("¿Eliminar venta " + id + "?")) return;
        const res = await fetch(`${apiUrl}/${id}`, { method: "DELETE" });
        const result = await res.json();
        alert(result.message || JSON.stringify(result));
        loadSales();
    }

    // Inicializar listado
    loadSales();

    // NUEVO CLIENTE:

const btnNewCustomer = document.querySelector("#btnNewCustomer");
const customerFormDiv = document.querySelector("#customerFormDiv");
const customerForm = document.querySelector("#customerForm");

btnNewCustomer.addEventListener("click", () => {
    document.querySelector("#customerFormTitle").textContent = "Crear Cliente";
    customerForm.reset();
    document.querySelector("#customerFormId").value = "";
    customerFormDiv.style.display = "block";
});

document.querySelector("#customerFormCancel").addEventListener("click", () => {
    customerFormDiv.style.display = "none";
});

customerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.querySelector("#customerFormId").value;
    const data = {
        first_name: document.querySelector("#cf_first_name").value,
        last_name: document.querySelector("#cf_last_name").value,
        address: document.querySelector("#cf_address").value,
        city: document.querySelector("#cf_city").value,
        phone: document.querySelector("#cf_phone").value,
        description: document.querySelector("#cf_description").value
    };

    let method = "POST";
    let url = "http://127.0.0.1:5000/customers";
    if (id) {
        method = "PUT";
        url += `/${id}`;
    }

    const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });

    const result = await res.json();
    alert(result.message || JSON.stringify(result));
    customerFormDiv.style.display = "none";
});

});



async function downloadPDF(saleId) {
    try {
    const response = await fetch(`/pdf/sale/${saleId}/label`, { method: 'GET' });

        if (!response.ok) {
            throw new Error('No se pudo generar el comprobante');
        }

        const blob = await response.blob();

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `venta_${saleId}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);

    } catch (error) {
        console.error(error);
        alert('Error al descargar el comprobante');
    }





    
}

