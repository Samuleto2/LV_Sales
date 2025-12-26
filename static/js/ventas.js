document.addEventListener("DOMContentLoaded", () => {

    const apiUrl = "http://127.0.0.1:5000/sales";
    const customerSearchUrl = "/customers/search";

    const customerInput = document.querySelector("#customer_name");
    const suggestionsDiv = document.querySelector("#suggestions");
    let selectedCustomer = null;
    let editingSaleId = null;

    /** ----------------------------
     * Función para mostrar mensajes tipo toast
     * ---------------------------- */
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

    /** ----------------------------
     * Función para formatear montos
     * ---------------------------- */
    function formatMoney(amount) {
        amount = Number(amount) || 0;
        return amount.toLocaleString('es-AR', {
            style: 'currency',
            currency: 'ARS',
            minimumFractionDigits: 0
        });
    }

    /** ----------------------------
     * Formatear fecha
     * ---------------------------- */
    function formatDate(isoString) {
        if (!isoString) return "";
        const clean = isoString.split('.')[0];
        const date = new Date(clean);
        return date.toLocaleString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' });
    }

    /** ----------------------------
     * Función para cargar ventas en tabla
     * ---------------------------- */
    async function loadSales(highlightId = null) {
        const res = await fetch(`${apiUrl}/last_sales`);
        const sales = await res.json();
        const tbody = document.querySelector("#salesTable tbody");
        tbody.innerHTML = "";

        sales.forEach(s => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${formatDate(s.sale_date)}</td>
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
            if (highlightId && s.id === highlightId) {
                row.style.backgroundColor = "#d4edda"; // verde claro
                setTimeout(() => row.style.backgroundColor = "", 2000);
            }
            tbody.appendChild(row);
        });
    }

    /** ----------------------------
     * Búsqueda de clientes con highlight y navegación
     * ---------------------------- */
    let selectedIndex = -1;
    customerInput.addEventListener("input", async () => {
        const query = customerInput.value.trim().toLowerCase();
        suggestionsDiv.innerHTML = "";
        selectedIndex = -1;

        if (!query) {
            selectedCustomer = null;
            document.querySelector("#customer_info").style.display = "none";
            return;
        }

        const res = await fetch(`${customerSearchUrl}?q=${encodeURIComponent(query)}`);
        const customers = await res.json();

        customers.forEach((c, index) => {
            const div = document.createElement("div");
            const name = `${c.first_name} ${c.last_name}`;
            const address = `${c.address}, ${c.city}`;
            const regex = new RegExp(`(${query})`, "gi");
            div.innerHTML = `${name.replace(regex, "<strong>$1</strong>")} - ${address.replace(regex, "<strong>$1</strong>")}`;
            div.style.padding = "5px";
            div.style.cursor = "pointer";

            div.addEventListener("click", () => selectCustomer(c));

            suggestionsDiv.appendChild(div);
        });
    });

    customerInput.addEventListener("keydown", (e) => {
        const items = suggestionsDiv.querySelectorAll("div");
        if (!items.length) return;

        if (e.key === "ArrowDown") {
            e.preventDefault();
            if (selectedIndex < items.length - 1) selectedIndex++;
            updateSelection(items);
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            if (selectedIndex > 0) selectedIndex--;
            updateSelection(items);
        } else if (e.key === "Enter") {
            e.preventDefault();
            if (selectedIndex >= 0) items[selectedIndex].click();
        }
    });

    function updateSelection(items) {
        items.forEach((item, i) => item.style.backgroundColor = i === selectedIndex ? "#cce5ff" : "#fff");
    }

    function selectCustomer(c) {
        customerInput.value = `${c.first_name} ${c.last_name}`;
        selectedCustomer = c;
        document.querySelector("#customer_id").value = c.id;
        suggestionsDiv.innerHTML = "";

        const infoDiv = document.querySelector("#customer_info");
        document.querySelector("#info_name").textContent = `${c.first_name} ${c.last_name}`;
        document.querySelector("#info_address").textContent = c.address;
        document.querySelector("#info_city").textContent = c.city;
        infoDiv.style.display = "block";
    }

    /** ----------------------------
     * Crear o editar venta
     * ---------------------------- */
    const saleForm = document.querySelector("#saleForm");
    const hasShippingCheckbox = document.getElementById("hasShipping");
    const shippingDateContainer = document.getElementById("shippingDateContainer");
    const shippingDateInput = document.getElementById("shippingDate");
    const isCashCheckbox = document.getElementById("isCash");
    const hasChangeCheckbox = document.getElementById("hasChange");
    const paidSelect = document.getElementById("paid");

/* ----------------------------
   Mostrar / ocultar fecha envío
---------------------------- */
hasShippingCheckbox.addEventListener("change", () => {
    if (!hasShippingCheckbox.checked) {
        shippingDateContainer.style.display = "none";
        if (shippingDateInput) shippingDateInput.value = "";
        return;
    }

    shippingDateContainer.style.display = "block";

    if (!shippingDateInput) return;

    /* Bloquear fechas pasadas */
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    shippingDateInput.min = today.toISOString().split("T")[0];
});

/* ----------------------------
   Restricciones UX: Efectivo vs Pagado
---------------------------- */
function updatePaidCashConstraints() {
    if (isCashCheckbox.checked) {
        paidSelect.value = "false";
        paidSelect.disabled = true;
    } else {
        paidSelect.disabled = false;
    }

    if (paidSelect.value === "true") {
        isCashCheckbox.checked = false;
        isCashCheckbox.disabled = true;
    } else {
        isCashCheckbox.disabled = false;
    }
}

isCashCheckbox.addEventListener("change", updatePaidCashConstraints);
paidSelect.addEventListener("change", updatePaidCashConstraints);

// Ejecutar al cargar para sincronizar con valores existentes
updatePaidCashConstraints();

/* ----------------------------
   Submit del formulario
---------------------------- */
saleForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!selectedCustomer) {
        return showToast("Seleccione un cliente válido", "error");
    }

    const hasShipping = hasShippingCheckbox.checked;
    const salesChannel = document.querySelector(
        "input[name='salesChannel']:checked"
    )?.value;

    if (!salesChannel) {
        return showToast("Seleccione un punto de venta", "error");
    }

    if (hasShipping && !shippingDateInput.value) {
        return showToast("Seleccione fecha de envío", "error");
    }

    const data = {
        customer_id: selectedCustomer.id,
        amount: parseFloat(document.querySelector("#amount").value),
        payment_method: document.querySelector("#payment_method").value,
        paid: paidSelect.value === "true",
        notes: document.querySelector("#notes").value,

        // Logística
        has_shipping: hasShipping,
        shipping_date: hasShipping ? shippingDateInput.value : null,
        sales_channel: salesChannel,

        // Nuevos tags
        is_cash: isCashCheckbox.checked,
        has_change: hasChangeCheckbox.checked
    };

    const method = editingSaleId ? "PUT" : "POST";
    const url = apiUrl + (editingSaleId ? `/${editingSaleId}` : "");

    const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });

    const result = await res.json();

    showToast(result.message || "Operación completada");

    resetSaleForm();
    loadSales(editingSaleId);
});


    // cachear ultimo punto de venta // 
    const channelRadios = document.querySelectorAll("input[name='salesChannel']");

// Al cargar la página
const lastChannel = localStorage.getItem("lastSalesChannel");
if (lastChannel) {
    const radio = document.querySelector(
        `input[name='salesChannel'][value='${lastChannel}']`
    );
    if (radio) radio.checked = true;
}

// Al cambiar
channelRadios.forEach(radio => {
    radio.addEventListener("change", () => {
        localStorage.setItem("lastSalesChannel", radio.value);
    });
});


// EDITAR VENTAS //

 
    window.editSale = async function(id) {
    const res = await fetch(`${apiUrl}/${id}`);
    const sale = await res.json();

    editingSaleId = id;
    selectedCustomer = { 
        id: sale.customer_id, 
        first_name: sale.customer_first_name, 
        last_name: sale.customer_last_name, 
        address: sale.customer_address, 
        city: sale.customer_city 
    };
    // Marcar el radio que coincide con la venta
    const channelRadios = document.querySelectorAll("input[name='salesChannel']");
    channelRadios.forEach(radio => {
        radio.checked = radio.value === sale.sales_channel;
    });

    customerInput.value = `${selectedCustomer.first_name} ${selectedCustomer.last_name}`;
    document.querySelector("#customer_id").value = sale.customer_id;

    document.querySelector("#amount").value = sale.amount;
    document.querySelector("#payment_method").value = sale.payment_method;
    document.querySelector("#paid").value = sale.paid ? "true" : "false";
    document.querySelector("#notes").value = sale.notes || "";

    const isCashCheckbox = document.getElementById("isCash");
    const hasChangeCheckbox = document.getElementById("hasChange");
    if (isCashCheckbox) isCashCheckbox.checked = sale.is_cash || false;
    if (hasChangeCheckbox) hasChangeCheckbox.checked = sale.has_change || false;

    const hasShippingCheckbox = document.getElementById("hasShipping");
    const shippingDateContainer = document.getElementById("shippingDateContainer");
    const shippingDateInput = document.getElementById("shippingDate");

    if (hasShippingCheckbox) {
        hasShippingCheckbox.checked = sale.has_shipping || false;
        shippingDateContainer.style.display = hasShippingCheckbox.checked ? "block" : "none";
        if (shippingDateInput) shippingDateInput.value = sale.shipping_date || "";
    }

        
        // Scroll suave al top de la página
        window.scrollTo({ top: 0, left: 0, behavior: "smooth" });

    updatePaidCashConstraints();

    const infoDiv = document.querySelector("#customer_info");
    document.querySelector("#info_name").textContent = `${selectedCustomer.first_name} ${selectedCustomer.last_name}`;
    document.querySelector("#info_address").textContent = selectedCustomer.address;
    document.querySelector("#info_city").textContent = selectedCustomer.city;
    infoDiv.style.display = "block";
    

    const submitBtn = saleForm.querySelector("button[type=submit]");
    submitBtn.textContent = "Guardar cambios";
    submitBtn.style.backgroundColor = "green";
    submitBtn.style.color = "white";

    if (!saleForm.querySelector(".cancel-btn")) {
        const cancelBtn = document.createElement("button");
        cancelBtn.type = "button";
        cancelBtn.textContent = "Cancelar";
        cancelBtn.className = "button button-delete cancel-btn";
        cancelBtn.addEventListener("click", resetSaleForm);
        submitBtn.insertAdjacentElement("afterend", cancelBtn);
    }

    const headerH2 = document.querySelector("#headerForm h2");
    if (headerH2) headerH2.textContent = `Editar venta #${id}`;

    const formContainer = document.getElementById("saleFormContainer");
    formContainer.style.display = "block";



};


    /** ----------------------------
     * Reset formulario
     * ---------------------------- */
    function resetSaleForm() {
        saleForm.reset();
        editingSaleId = null;
        selectedCustomer = null;
        document.querySelector("#customer_id").value = "";
        document.querySelector("#customer_info").style.display = "none";

        const submitBtn = saleForm.querySelector("button[type=submit]");
        submitBtn.textContent = "Crear venta";
        submitBtn.style.backgroundColor = "";
        submitBtn.style.color = "";

        const cancelBtn = saleForm.querySelector(".cancel-btn");
        if (cancelBtn) cancelBtn.remove();

        const headerH2 = document.querySelector("#headerForm h2");
        if (headerH2) headerH2.textContent = "Crear venta";
        customerInput.focus();
    }

    /** ----------------------------
     * Borrar venta
     * ---------------------------- */
    window.deleteSale = async function(id) {
        if (!confirm("¿Eliminar venta " + id + "?")) return;
        const res = await fetch(`${apiUrl}/${id}`, { method: "DELETE" });
        const result = await res.json();
        showToast(result.message || "Venta eliminada");
        loadSales();
    }

    /** ----------------------------
     * Inicializar
     * ---------------------------- */
    loadSales();

    /** ----------------------------
     * Funciones de cliente (nuevo cliente)
     * ---------------------------- */
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

        let method = id ? "PUT" : "POST";
        let url = "http://127.0.0.1:5000/customers" + (id ? `/${id}` : "");

        const res = await fetch(url, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        let result;
        try {
            result = await res.json();
        } catch {
            result = { error: "Respuesta no válida del servidor" };
        }

        // Validar status
        if (!res.ok) {
            // Mostrar error del servidor
            alert(result.error || "Ocurrió un error");
        } else {
            
            showToast(result.message || "Cliente creado correctamente");
            customerFormDiv.style.display = "none";
        }
    });

    /** ----------------------------
     * Descargar PDF
     * ---------------------------- */
    window.downloadPDF = async function(saleId) {
        try {
            const response = await fetch(`/pdf/sale/${saleId}/label`);
            if (!response.ok) throw new Error("No se pudo generar el comprobante");
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
            showToast("Error al descargar el comprobante", "error");
        }
    }

});



function showSaleFormAndScroll() {
    const formContainer = document.getElementById("saleFormContainer");
    formContainer.style.display = "block";

    // Scroll al top cuando el layout ya esté listo
    requestAnimationFrame(() => {
        formContainer.scrollIntoView({ behavior: "smooth", block: "start" });
    });
}
