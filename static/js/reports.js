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
// VERIFICAR PIN
// ======================
const pinModal = document.getElementById('pinModal');
const pinForm = document.getElementById('pinForm');
const pinInput = document.getElementById('pinInput');
const lockedContent = document.getElementById('lockedContent');
const reportsContent = document.getElementById('reportsContent');

pinForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const pin = pinInput.value;
    
    try {
        const res = await fetch('/reports/verify-pin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pin })
        });
        
        const data = await res.json();
        
        if (data.valid) {
            pinModal.style.display = 'none';
            lockedContent.classList.add('hidden');
            reportsContent.classList.remove('hidden');
            loadDashboard();
        } else {
            pinInput.value = '';
            pinInput.style.borderColor = '#f44336';
            showToast('PIN incorrecto', 'error');
            setTimeout(() => {
                pinInput.style.borderColor = '';
            }, 1000);
        }
    } catch (error) {
        console.error(error);
        showToast('Error al verificar PIN', 'error');
    }
});

// ======================
// CARGAR DASHBOARD
// ======================
let charts = {};

async function loadDashboard() {
    try {
        const res = await fetch('/reports/dashboard');
        const data = await res.json();
        
        console.log('📊 Dashboard data:', data);
        
        // Actualizar tarjetas
        updateStatsCards(data.comparison);
        
        // Gráficos
        renderDailySalesChart(data.daily_sales);
        renderChannelChart(data.channels);
        renderDeliveryChart(data.delivery_types);
        
        // Top clientes
        renderTopCustomers(data.top_customers);
        
        // Cargar stats de cambios
        loadChangesStats();
        
    } catch (error) {
        console.error(error);
        showToast('Error cargando dashboard', 'error');
    }
}

// ======================
// ACTUALIZAR TARJETAS
// ======================
function updateStatsCards(comparison) {
    const { current, previous, changes } = comparison;
    
    // Ventas mes actual
    document.getElementById('currentSales').textContent = formatMoney(current.total_amount);
    document.getElementById('currentCount').textContent = current.total_sales;
    
    const salesChange = document.getElementById('salesChange');
    salesChange.textContent = `${changes.total_amount >= 0 ? '+' : ''}${changes.total_amount.toFixed(1)}%`;
    salesChange.className = `stat-change ${changes.total_amount >= 0 ? 'positive' : 'negative'}`;
    
    // Ticket promedio
    document.getElementById('avgTicket').textContent = formatMoney(current.avg_ticket);
    
    const ticketChange = document.getElementById('ticketChange');
    ticketChange.textContent = `${changes.avg_ticket >= 0 ? '+' : ''}${changes.avg_ticket.toFixed(1)}%`;
    ticketChange.className = `stat-change ${changes.avg_ticket >= 0 ? 'positive' : 'negative'}`;
    
    // Por cobrar
    document.getElementById('unpaidAmount').textContent = formatMoney(current.unpaid_amount);
    document.getElementById('unpaidCount').textContent = current.unpaid_sales;
}

// ======================
// CARGAR STATS DE CAMBIOS
// ======================
async function loadChangesStats() {
    try {
        const res = await fetch('/reports/changes-stats');
        const data = await res.json();
        
        document.getElementById('changesCount').textContent = data.stats.changes_this_month;
        document.getElementById('pendingChanges').textContent = data.stats.pending_count;
        
    } catch (error) {
        console.error('Error cargando stats de cambios:', error);
    }
}

// ======================
// GRÁFICO: VENTAS DIARIAS
// ======================
function renderDailySalesChart(data) {
    const ctx = document.getElementById('dailySalesChart').getContext('2d');
    
    if (charts.daily) charts.daily.destroy();
    
    charts.daily = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => new Date(d.date).toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit' })),
            datasets: [{
                label: 'Ventas ($)',
                data: data.map(d => d.total),
                borderColor: '#4A90E2',
                backgroundColor: 'rgba(74, 144, 226, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: value => '$' + value.toLocaleString('es-AR')
                    }
                }
            }
        }
    });
}

// ======================
// GRÁFICO: POR CANAL
// ======================
function renderChannelChart(data) {
    const ctx = document.getElementById('channelChart').getContext('2d');
    
    if (charts.channel) charts.channel.destroy();
    
    charts.channel = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.channel),
            datasets: [{
                data: data.map(d => d.total),
                backgroundColor: ['#4A90E2', '#F59E0B', '#28a745']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

// ======================
// GRÁFICO: POR ENTREGA
// ======================
function renderDeliveryChart(data) {
    const ctx = document.getElementById('deliveryChart').getContext('2d');
    
    if (charts.delivery) charts.delivery.destroy();
    
    const labels = {
        'cadeteria': '📦 Cadetería',
        'retiro': '🏪 Retiro',
        'correo': '📮 Correo'
    };
    
    charts.delivery = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => labels[d.type] || d.type),
            datasets: [{
                label: 'Cantidad',
                data: data.map(d => d.count),
                backgroundColor: ['#4A90E2', '#28a745', '#F59E0B']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

// ======================
// TOP CLIENTES
// ======================
function renderTopCustomers(customers) {
    const tbody = document.getElementById('topCustomersTable');
    tbody.innerHTML = '';
    
    if (!customers.length) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">No hay datos</td></tr>';
        return;
    }
    
    customers.forEach((c, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${c.name}</td>
            <td>${c.purchases}</td>
            <td>${formatMoney(c.total)}</td>
        `;
        tbody.appendChild(row);
    });
}

// ======================
// 🔹 REPORTES PERSONALIZADOS
// ======================
const customReportForm = document.getElementById('customReportForm');
const customReportResult = document.getElementById('customReportResult');

// Setear fechas por defecto (mes actual)
document.addEventListener('DOMContentLoaded', () => {
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
    
    document.getElementById('report_end_date').value = today.toISOString().split('T')[0];
    document.getElementById('report_start_date').value = firstDay.toISOString().split('T')[0];
});

customReportForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const startDate = document.getElementById('report_start_date').value;
    const endDate = document.getElementById('report_end_date').value;
    const reportType = document.getElementById('report_type').value;
    
    // Validar fechas
    if (new Date(startDate) > new Date(endDate)) {
        showToast('La fecha de inicio debe ser anterior a la fecha final', 'error');
        return;
    }
    
    customReportResult.classList.remove('hidden');
    document.getElementById('reportContent').innerHTML = '<p>Cargando reporte...</p>';
    
    try {
        switch(reportType) {
            case 'general':
                await generateGeneralReport(startDate, endDate);
                break;
            case 'delivery':
                await generateDeliveryReport(startDate, endDate);
                break;
            case 'channel':
                await generateChannelReport(startDate, endDate);
                break;
            case 'payment':
                await generatePaymentReport(startDate, endDate);
                break;
            case 'changes':
                await generateChangesReport(startDate, endDate);
                break;
            case 'top_customers':
                await generateTopCustomersReport(startDate, endDate);
                break;
        }
    } catch (error) {
        console.error(error);
        showToast('Error generando reporte', 'error');
        document.getElementById('reportContent').innerHTML = '<p style="color: red;">Error al generar reporte</p>';
    }
});

// ======================
// REPORTE GENERAL
// ======================
async function generateGeneralReport(startDate, endDate) {
    const res = await fetch(`/reports/sales-summary?start_date=${startDate}&end_date=${endDate}`);
    const data = await res.json();
    
    const { summary, by_channel, by_delivery } = data;
    
    document.getElementById('reportTitle').textContent = '📊 Reporte General de Ventas';
    document.getElementById('reportContent').innerHTML = `
        <div class="report-grid">
            <div class="report-card">
                <h4>Resumen del Período</h4>
                <p><strong>Total Ventas:</strong> ${summary.total_sales}</p>
                <p><strong>Monto Total:</strong> ${formatMoney(summary.total_amount)}</p>
                <p><strong>Ticket Promedio:</strong> ${formatMoney(summary.avg_ticket)}</p>
                <p><strong>Ventas Pagadas:</strong> ${summary.paid_sales} (${formatMoney(summary.paid_amount)})</p>
                <p><strong>Ventas Impagas:</strong> ${summary.unpaid_sales} (${formatMoney(summary.unpaid_amount)})</p>
            </div>
            
            <div class="report-card">
                <h4>Por Canal de Venta</h4>
                ${by_channel.map(c => `
                    <p><strong>${c.channel}:</strong> ${c.count} ventas - ${formatMoney(c.total)}</p>
                `).join('')}
            </div>
            
            <div class="report-card">
                <h4>Por Tipo de Entrega</h4>
                ${by_delivery.map(d => `
                    <p><strong>${getDeliveryName(d.type)}:</strong> ${d.count} ventas - ${formatMoney(d.total)}</p>
                `).join('')}
            </div>
        </div>
    `;
}

// ======================
// REPORTE POR ENTREGA
// ======================
async function generateDeliveryReport(startDate, endDate) {
    const res = await fetch(`/reports/sales-summary?start_date=${startDate}&end_date=${endDate}`);
    const data = await res.json();
    
    document.getElementById('reportTitle').textContent = '📦 Reporte por Tipo de Entrega';
    document.getElementById('reportContent').innerHTML = `
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>Tipo de Entrega</th>
                        <th>Cantidad</th>
                        <th>Monto Total</th>
                        <th>% del Total</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.by_delivery.map(d => {
                        const percentage = (d.total / data.summary.total_amount * 100).toFixed(1);
                        return `
                            <tr>
                                <td>${getDeliveryName(d.type)}</td>
                                <td>${d.count}</td>
                                <td>${formatMoney(d.total)}</td>
                                <td>${percentage}%</td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        </div>
    `;
}

// ======================
// REPORTE POR CANAL
// ======================
async function generateChannelReport(startDate, endDate) {
    const res = await fetch(`/reports/sales-summary?start_date=${startDate}&end_date=${endDate}`);
    const data = await res.json();
    
    document.getElementById('reportTitle').textContent = '📍 Reporte por Canal de Venta';
    document.getElementById('reportContent').innerHTML = `
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>Canal</th>
                        <th>Cantidad</th>
                        <th>Monto Total</th>
                        <th>Ticket Promedio</th>
                        <th>% del Total</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.by_channel.map(c => {
                        const avgTicket = c.total / c.count;
                        const percentage = (c.total / data.summary.total_amount * 100).toFixed(1);
                        return `
                            <tr>
                                <td>${c.channel}</td>
                                <td>${c.count}</td>
                                <td>${formatMoney(c.total)}</td>
                                <td>${formatMoney(avgTicket)}</td>
                                <td>${percentage}%</td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        </div>
    `;
}

// ======================
// REPORTE DE PAGOS
// ======================
async function generatePaymentReport(startDate, endDate) {
    const res = await fetch(`/reports/sales-summary?start_date=${startDate}&end_date=${endDate}`);
    const data = await res.json();
    
    const { summary } = data;
    const paidPercentage = (summary.paid_sales / summary.total_sales * 100).toFixed(1);
    const unpaidPercentage = (summary.unpaid_sales / summary.total_sales * 100).toFixed(1);
    
    document.getElementById('reportTitle').textContent = '💰 Análisis de Pagos';
    document.getElementById('reportContent').innerHTML = `
        <div class="report-grid">
            <div class="report-card">
                <h4>Ventas Pagadas</h4>
                <p class="report-big-number">${summary.paid_sales}</p>
                <p><strong>Monto:</strong> ${formatMoney(summary.paid_amount)}</p>
                <p><strong>Porcentaje:</strong> ${paidPercentage}%</p>
            </div>
            
            <div class="report-card">
                <h4>Ventas Impagas</h4>
                <p class="report-big-number warning">${summary.unpaid_sales}</p>
                <p><strong>Monto:</strong> ${formatMoney(summary.unpaid_amount)}</p>
                <p><strong>Porcentaje:</strong> ${unpaidPercentage}%</p>
            </div>
            
            <div class="report-card">
                <h4>Resumen</h4>
                <p><strong>Total Ventas:</strong> ${summary.total_sales}</p>
                <p><strong>Efectividad de Cobro:</strong> ${paidPercentage}%</p>
                <p><strong>Por Cobrar:</strong> ${formatMoney(summary.unpaid_amount)}</p>
            </div>
        </div>
    `;
}

// ======================
// REPORTE DE CAMBIOS
// ======================
async function generateChangesReport(startDate, endDate) {
    const res = await fetch('/reports/changes-stats');
    const data = await res.json();
    
    document.getElementById('reportTitle').textContent = '🔄 Reporte de Cambios';
    document.getElementById('reportContent').innerHTML = `
        <div class="report-grid">
            <div class="report-card">
                <h4>Cambios Este Mes</h4>
                <p class="report-big-number">${data.stats.changes_this_month}</p>
            </div>
            
            <div class="report-card">
                <h4>Cambios Pendientes</h4>
                <p class="report-big-number">${data.stats.pending_count}</p>
            </div>
            
            <div class="report-card">
                <h4>Cambios Vencidos</h4>
                <p class="report-big-number warning">${data.stats.overdue_count}</p>
            </div>
        </div>
        
        <h4 style="margin-top: 20px;">Tendencia de Cambios (Últimos 6 Meses)</h4>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>Mes</th>
                        <th>Cantidad de Cambios</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.trend.map(t => `
                        <tr>
                            <td>${t.month}</td>
                            <td>${t.count}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

// ======================
// TOP CLIENTES PERSONALIZADO
// ======================
async function generateTopCustomersReport(startDate, endDate) {
    const res = await fetch(`/reports/top-customers?start_date=${startDate}&end_date=${endDate}&limit=20`);
    const customers = await res.json();
    
    document.getElementById('reportTitle').textContent = '⭐ Top 20 Clientes';
    document.getElementById('reportContent').innerHTML = `
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Cliente</th>
                        <th>Compras</th>
                        <th>Total Gastado</th>
                        <th>Ticket Promedio</th>
                    </tr>
                </thead>
                <tbody>
                    ${customers.map((c, index) => {
                        const avgTicket = c.total / c.purchases;
                        return `
                            <tr>
                                <td>${index + 1}</td>
                                <td>${c.name}</td>
                                <td>${c.purchases}</td>
                                <td>${formatMoney(c.total)}</td>
                                <td>${formatMoney(avgTicket)}</td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        </div>
    `;
}

// ======================
// HELPERS
// ======================
function getDeliveryName(type) {
    const names = {
        'cadeteria': '📦 Cadetería',
        'retiro': '🏪 Retiro',
        'correo': '📮 Correo'
    };
    return names[type] || type;
}