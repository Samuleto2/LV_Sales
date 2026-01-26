// ======================
// TOAST
// ======================
function showToast(message) {
    let toast = document.querySelector(".toast");

    if (!toast) {
        toast = document.createElement("div");
        toast.className = "toast";
        document.body.appendChild(toast);
    }

    toast.textContent = message;
    toast.classList.add("show");

    setTimeout(() => toast.classList.remove("show"), 2500);
}


// ======================
// COLORES POR CANTIDAD
// ======================
function getDayClass(count) {
    if (count <= 9) return "day-green";
    if (count <= 13) return "day-yellow";
    return "day-red";
}


// ======================
// 🔹 OBTENER DÍA DE LA SEMANA
// ======================
function getDayName(date) {
    const days = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
    return days[date.getDay()];
}


// ======================
// CALENDARIO: -5 días a +10 días
// ======================
async function loadCalendar() {
    const calendar = document.getElementById("calendar");
    calendar.innerHTML = "";

    // 🔹 Usar fecha local del navegador (ya está en zona horaria de Argentina)
    const today = new Date();
    today.setHours(0, 0, 0, 0); // Limpiar la hora
    
    const todayIso = formatDateToISO(today);

    const res = await fetch("/sales/shipments/calendar");
    const counts = await res.json();

    console.log("📅 Counts recibidos del servidor:", counts);
    console.log("📍 Hoy es:", todayIso);

    // 🔹 RANGO: -5 días hasta +10 días (total 16 días)
    for (let i = -5; i <= 9; i++) {
        const d = new Date(today);
        d.setDate(today.getDate() + i);

        const iso = formatDateToISO(d);
        const qty = counts[iso] || 0;

        const div = document.createElement("div");
        div.dataset.date = iso;
        
        // 🔹 Clase base + clase de cantidad + clase de pasado
        let classList = `calendar-day ${getDayClass(qty)}`;
        if (i < 0) {
            classList += ' day-past';
        }
        div.className = classList;

        // 🔹 Mostrar: día semana + fecha + cantidad
        const dayName = getDayName(d);
        const dateStr = d.toLocaleDateString("es-AR", { 
            day: '2-digit', 
            month: '2-digit'
        });

        div.innerHTML = `
            ${iso === todayIso ? `<span class="today-badge">HOY</span>` : ""}
            <strong>${dayName} ${dateStr}</strong><br>
            <span class="badge">${qty} envío${qty !== 1 ? 's' : ''}</span>
        `;

        div.addEventListener("click", () => loadDay(iso, div));

        // Drag over
        div.addEventListener("dragover", e => {
            e.preventDefault();
            div.classList.add("drag-hover");
        });

        div.addEventListener("dragleave", () => {
            div.classList.remove("drag-hover");
        });

        // Drop
        div.addEventListener("drop", async e => {
            e.preventDefault();
            div.classList.remove("drag-hover");

            const saleId = e.dataTransfer.getData("text/plain");

            const res = await fetch(`/sales/shipments/${saleId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ shipping_date: iso })
            });

            if (!res.ok) {
                showToast("Error moviendo el envío");
                return;
            }

            showToast("Envío reprogramado");
            await loadCalendar();

            const todayDiv = document.querySelector(
                `.calendar-day[data-date="${todayIso}"]`
            );
            todayDiv?.click();
        });

        calendar.appendChild(div);
    }

    // Auto abrir HOY
    const todayDiv = document.querySelector(
        `.calendar-day[data-date="${todayIso}"]`
    );
    todayDiv?.click();
}


// ======================
// 🔹 HELPER: Formatear Date a ISO local
// ======================
function formatDateToISO(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}


// ======================
// DETALLE DEL DÍA
// ======================
async function loadDay(date, el) {
    document.querySelectorAll(".calendar-day")
        .forEach(d => d.classList.remove("active"));
    el.classList.add("active");

    const res = await fetch(`/sales/shipments/day/${date}`);
    const sales = await res.json();

    console.log(`📦 Envíos del ${date}:`, sales);

    const container = document.getElementById("dayDetail");
    container.innerHTML = "";

    if (!sales.length) {
        container.innerHTML = "<em>No hay envíos</em>";
        document.getElementById("printDayBtn").style.display = "none";
        return;
    }

    sales.forEach(s => {
        container.innerHTML += `
            <div class="shipment-card"
                 id="shipment-${s.id}"
                 draggable="true"
                 data-id="${s.id}">

                <div class="view-mode">
                    <strong>Venta #${s.id}</strong><br>
                    Cliente: ${s.customer_first_name} ${s.customer_last_name}<br>
                    Fecha envío: ${date}<br>
                    Notas: ${s.notes || "-"}<br>

                    <button onclick="enableEdit(${s.id})" class="button-edit">Editar</button>
                    <a href="/pdf/sale/${s.id}/label" target="_blank" class="button-download">Etiqueta</a>
                </div>

                <div class="edit-mode" style="display:none;">
                    Fecha envío:
                    <input type="date" class="input-text" id="edit-date-${s.id}" value="${date}"><br>

                    Notas:
                    <textarea class="input-text" id="edit-notes-${s.id}">${s.notes || ""}</textarea><br>

                    <button onclick="saveEdit(${s.id})" class="button-edit">Guardar</button>
                    <button onclick="cancelEdit(${s.id})" class="button-delete">Cancelar</button>
                </div>
            </div>
        `;
    });

    const printBtn = document.getElementById("printDayBtn");
    printBtn.style.display = "inline-block";
    printBtn.onclick = () => {
        window.open(`/pdf/shipments/day/${date}/labels`, "_blank");
    };
}


// ======================
// EDICIÓN INLINE
// ======================
function enableEdit(id) {
    const card = document.getElementById(`shipment-${id}`);
    card.querySelector(".view-mode").style.display = "none";
    card.querySelector(".edit-mode").style.display = "block";
}

function cancelEdit(id) {
    const card = document.getElementById(`shipment-${id}`);
    card.querySelector(".edit-mode").style.display = "none";
    card.querySelector(".view-mode").style.display = "block";
}

async function saveEdit(id) {
    const shipping_date = document.getElementById(`edit-date-${id}`).value;
    const notes = document.getElementById(`edit-notes-${id}`).value;

    const res = await fetch(`/sales/shipments/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ shipping_date, notes })
    });

    if (!res.ok) {
        showToast("Error al guardar");
        return;
    }

    showToast("Envío actualizado");
    await loadCalendar();
}


// ======================
// DRAG START
// ======================
document.addEventListener("dragstart", e => {
    if (e.target.classList.contains("shipment-card")) {
        e.dataTransfer.setData("text/plain", e.target.dataset.id);
        e.target.classList.add("dragging");
    }
});

document.addEventListener("dragend", e => {
    if (e.target.classList.contains("shipment-card")) {
        e.target.classList.remove("dragging");
    }
});


// ======================
// INIT
// ======================
document.addEventListener("DOMContentLoaded", loadCalendar);