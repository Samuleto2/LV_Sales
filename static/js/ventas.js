document.addEventListener("DOMContentLoaded", () => {

    const apiUrl = "/sales";
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

// ----------------------------
// Variables globales - AHORA CON PERSISTENCIA
// ----------------------------
const STORAGE_KEY = 'turnSales';

// Cargar ventas del localStorage al iniciar
let turnSales = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];

// ----------------------------
// Función para actualizar el dashboard
// ----------------------------
function updateDashboard(sales) {
    let totalVendido = 0;
    let cantidadVentas = 0;
    let totalPagado = 0;
    let totalImpago = 0;

    sales.forEach(sale => {
        const amount = Number(sale.amount) || 0;
        const paid = !!sale.paid;

        totalVendido += amount;
        cantidadVentas += 1;
        if (paid) totalPagado += amount;
        else totalImpago += amount;
    });

    document.getElementById("totalVendido").textContent = formatMoney(totalVendido);
    document.getElementById("cantidadVentas").textContent = cantidadVentas;
    document.getElementById("totalPagado").textContent = formatMoney(totalPagado);
    document.getElementById("totalImpago").textContent = formatMoney(totalImpago);
}

// ----------------------------
// Función para agregar una venta al turno
// ----------------------------
function addSaleToTurn(sale) {
    sale.amount = Number(sale.amount) || 0;
    sale.paid = !!sale.paid;
    sale.id = sale.id || Date.now(); // Asegurar que tiene ID

    turnSales.push(sale);
    
    // 🔹 GUARDAR EN LOCALSTORAGE
    localStorage.setItem(STORAGE_KEY, JSON.stringify(turnSales));
    
    updateDashboard(turnSales);
}

// ----------------------------
// Función para actualizar una venta existente en el turno
// ----------------------------
function updateSaleInTurn(saleId, updatedData) {
    const index = turnSales.findIndex(s => s.id === saleId);
    
    if (index !== -1) {
        // Actualizar la venta existente
        turnSales[index] = {
            ...turnSales[index],
            ...updatedData,
            amount: Number(updatedData.amount) || turnSales[index].amount,
            paid: !!updatedData.paid
        };
    } else {
        // Si no existe, agregarla
        addSaleToTurn({
            id: saleId,
            amount: Number(updatedData.amount) || 0,
            paid: !!updatedData.paid
        });
    }
    
    // 🔹 GUARDAR EN LOCALSTORAGE
    localStorage.setItem(STORAGE_KEY, JSON.stringify(turnSales));
    
    updateDashboard(turnSales);
}

// ----------------------------
// Función para eliminar una venta del turno
// ----------------------------
function removeSaleFromTurn(saleId) {
    turnSales = turnSales.filter(s => s.id !== saleId);
    
    // 🔹 GUARDAR EN LOCALSTORAGE
    localStorage.setItem(STORAGE_KEY, JSON.stringify(turnSales));
    
    updateDashboard(turnSales);
}

// ----------------------------
// Botón de reset
// ----------------------------
document.getElementById("resetTurnBtn").addEventListener("click", () => {
    if (confirm("¿Estás seguro de resetear el contador del turno?")) {
        turnSales = [];
        
        // 🔹 LIMPIAR LOCALSTORAGE
        localStorage.removeItem(STORAGE_KEY);
        
        updateDashboard(turnSales);
        showToast("Contador reseteado");
    }
});

// 🔹 ACTUALIZAR DASHBOARD AL CARGAR LA PÁGINA
updateDashboard(turnSales);

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
                row.style.backgroundColor = "#d4edda";
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

    const saleForm = document.querySelector("#saleForm");
    const hasShippingCheckbox = document.getElementById("hasShipping");
    const shippingDateContainer = document.getElementById("shippingDateContainer");
    const shippingDateInput = document.getElementById("shippingDate");  
    const hasChangeCheckbox = document.getElementById("hasChange");
    const paidRadios = document.querySelectorAll("input[name='paid']");
    const paymentRadios = document.querySelectorAll("input[name='PaidMethod']");
    const isCashRadio = document.getElementById("isCash");
    const deliveryRadios = document.querySelectorAll("input[name='deliveryType']");

    const updateShippingDateVisibility = () => {
        const deliveryType = document.querySelector(
            "input[name='deliveryType']:checked"
        )?.value;

        const hasShipping = deliveryType === "cadeteria";

        shippingDateContainer.classList.toggle("hidden", !hasShipping);

        if (!hasShipping) {
            shippingDateInput.value = "";
            return;
        }

        const today = new Date();
        today.setHours(0, 0, 0, 0);
        shippingDateInput.min = today.toISOString().split("T")[0];
    };

    deliveryRadios.forEach(radio =>
        radio.addEventListener("change", updateShippingDateVisibility)
    );

    updateShippingDateVisibility();

    function syncPaymentConstraints() {
        const paymentMethod = document.querySelector("input[name='PaidMethod']:checked")?.value;
        const paidValue = document.querySelector("input[name='paid']:checked")?.value === "true";

        if (paymentMethod === "cash") {
            paidRadios.forEach(radio => {
                if (radio.value === "false") radio.disabled = true;
                if (radio.value === "true") radio.checked = false;
            });
        } else {
            paidRadios.forEach(radio => radio.disabled = false);
        }

        if (paidValue) {
            if (isCashRadio) isCashRadio.disabled = true;
            if (paymentMethod === "cash" && isCashRadio) isCashRadio.checked = false;
        } else {
            if (isCashRadio) isCashRadio.disabled = false;
        }
    }

    paymentRadios.forEach(radio => radio.addEventListener("change", syncPaymentConstraints));
    paidRadios.forEach(radio => radio.addEventListener("change", syncPaymentConstraints));

    syncPaymentConstraints();

    saleForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!selectedCustomer) {
            return showToast("Seleccione un cliente válido", "error");
        }

        const salesChannel = document.querySelector(
            "input[name='salesChannel']:checked"
        )?.value;

        if (!salesChannel) {
            return showToast("Seleccione un punto de venta", "error");
        }

        const deliveryType = document.querySelector(
            "input[name='deliveryType']:checked"
        )?.value;

        if (!deliveryType) {
            return showToast("Seleccione tipo de entrega", "error");
        }

        if (deliveryType === "cadeteria" && !shippingDateInput.value) {
            return showToast("Seleccione fecha de envío", "error");
        }

        const paymentMethod = document.querySelector(
            "input[name='PaidMethod']:checked"
        )?.value;

        const paid =
            document.querySelector("input[name='paid']:checked")?.value === "true";

        const data = {
            customer_id: selectedCustomer.id,
            amount: parseFloat(document.querySelector("#amount").value),
            payment_method: paymentMethod || null,
            paid,
            notes: document.querySelector("#notes").value,

            delivery_type: deliveryType,
            has_shipping: deliveryType === "cadeteria",
            shipping_date:
                deliveryType === "cadeteria" ? shippingDateInput.value : null,

            sales_channel: salesChannel,
            is_cash: paymentMethod === "cash",
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

        // 🔹 ACTUALIZAR DASHBOARD
        if (editingSaleId) {
            // Si es edición, actualizar venta existente
            updateSaleInTurn(editingSaleId, {
                amount: data.amount,
                paid: data.paid
            });
        } else {
            // Si es nueva, agregarla con el ID del servidor
            addSaleToTurn({
                id: result.sale_id,
                amount: data.amount,
                paid: data.paid
            });
        }

        resetSaleForm();
        loadSales(editingSaleId || result.sale_id);
    });

    const channelRadios = document.querySelectorAll("input[name='salesChannel']");

    const lastChannel = localStorage.getItem("lastSalesChannel");
    if (lastChannel) {
        const radio = document.querySelector(
            `input[name='salesChannel'][value='${lastChannel}']`
        );
        if (radio) radio.checked = true;
    }

    channelRadios.forEach(radio => {
        radio.addEventListener("change", () => {
            localStorage.setItem("lastSalesChannel", radio.value);
        });
    });

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

        const channelRadios = document.querySelectorAll("input[name='salesChannel']");
        channelRadios.forEach(radio => {
            radio.checked = radio.value === sale.sales_channel;
        });

        customerInput.value = `${selectedCustomer.first_name} ${selectedCustomer.last_name}`;
        document.querySelector("#customer_id").value = sale.customer_id;

        document.querySelector("#amount").value = sale.amount;
        document.querySelector("#notes").value = sale.notes || "";

        const paidRadios = document.querySelectorAll("input[name='paid']");
        paidRadios.forEach(radio => {
            radio.checked = (radio.value === (sale.paid ? "true" : "false"));
        });

        const paymentRadios = document.querySelectorAll("input[name='PaidMethod']");
        paymentRadios.forEach(radio => {
            radio.checked = (radio.value === sale.payment_method);
        });

        const isCashRadio = document.getElementById("isCash");
        const hasChangeCheckbox = document.getElementById("hasChange");
        if (isCashRadio) isCashRadio.checked = sale.is_cash || false;
        if (hasChangeCheckbox) hasChangeCheckbox.checked = sale.has_change || false;

        const hasShippingCheckbox = document.getElementById("hasShipping");
        const shippingDateContainer = document.getElementById("shippingDateContainer");
        const shippingDateInput = document.getElementById("shippingDate");
        if (hasShippingCheckbox) {
            hasShippingCheckbox.checked = sale.has_shipping || false;
            shippingDateContainer.style.display = hasShippingCheckbox.checked ? "block" : "none";
            if (shippingDateInput) shippingDateInput.value = sale.shipping_date || "";
        }

        window.scrollTo({ top: 0, left: 0, behavior: "smooth" });

        syncPaymentConstraints();

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

    window.deleteSale = async function(id) {
        if (!confirm("¿Eliminar venta " + id + "?")) return;
        const res = await fetch(`${apiUrl}/${id}`, { method: "DELETE" });
        const result = await res.json();
        showToast(result.message || "Venta eliminada");
        
        // 🔹 REMOVER DEL DASHBOARD
        removeSaleFromTurn(id);
        
        loadSales();
    }

    loadSales();

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
        let url = "/customers" + (id ? `/${id}` : "");

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

        if (!res.ok) {
            alert(result.error || "Ocurrió un error");
        } else {
            showToast(result.message || "Cliente creado correctamente");
            customerFormDiv.style.display = "none";
        }
    });

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




