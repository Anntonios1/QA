/**
 * ============================================================
 *  CAPA DE PRESENTACION - Logica de Aplicacion
 *  ControlCash v2.1 - Sistema Profesional de Control Financiero
 * ============================================================
 *  Normas aplicadas:
 *    - ISO 9126: Funcionalidad, Usabilidad
 *    - ISO/IEC 25000: Calidad en uso
 *    - ISO/IEC 27001: Seguridad de la informacion
 *    - OWASP Mobile Top 10: Seguridad en aplicaciones
 *    - ISO 9001:2000: Enfoque basado en procesos
 *    - IEEE 730: Aseguramiento de calidad
 * ============================================================
 */

// ============================================================
//  CONFIGURACIÓN
// ============================================================
const API_BASE = '/api';

// ============================================================
//  ESTADO DE LA APLICACION
// ============================================================
let estadoApp = {
    usuario: null,
    filtroActual: 'todos',
    notifPanelAbierto: false,
    sesionTimeoutId: null,
    biometricoDisponible: false,
    modoOscuro: localStorage.getItem('cc_modo') !== 'light',
    movimientoEditandoId: null,
    movimientosBorrandoId: null,
};

// Chart.js instances
let chartCategorias = null;
let chartTendencia = null;

// ISO/IEC 27001 - Session timeout (15 minutes)
const SESSION_TIMEOUT_MS = 15 * 60 * 1000;

// ============================================================
//  UTILIDADES: Peticiones HTTP
// ============================================================
async function apiRequest(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
    };
    if (body) options.body = JSON.stringify(body);
    const response = await fetch(`${API_BASE}${endpoint}`, options);
    // CSV download handling
    if (response.headers.get('content-type')?.includes('text/csv')) {
        return response;
    }
    const data = await response.json();
    if (!response.ok) throw { status: response.status, ...data };
    return data;
}

// ============================================================
//  UTILIDADES: Formato
// ============================================================
function formatMoney(amount) {
    const num = parseFloat(amount) || 0;
    return '$' + num.toLocaleString('es-MX', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-MX', {
        day: 'numeric', month: 'short', year: 'numeric'
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================
//  MODO OSCURO / CLARO
// ============================================================
function aplicarModo(oscuro) {
    document.body.classList.toggle('light-mode', !oscuro);
    const btn = document.getElementById('btn-toggle-modo');
    if (btn) btn.textContent = oscuro ? '☀️' : '🌙';
    localStorage.setItem('cc_modo', oscuro ? 'dark' : 'light');
}

function toggleModo() {
    estadoApp.modoOscuro = !estadoApp.modoOscuro;
    aplicarModo(estadoApp.modoOscuro);
}

// ============================================================
//  F6: SISTEMA DE NOTIFICACIONES (Toast)
// ============================================================
function mostrarToast(titulo, mensaje, tipo = 'info') {
    const container = document.getElementById('toast-container');
    const iconos = { exito: '✅', error: '❌', alerta: '⚠️', info: 'ℹ️' };
    const toast = document.createElement('div');
    toast.className = `glass-toast glass-toast--${tipo}`;
    toast.innerHTML = `
        <span class="toast-icon">${iconos[tipo] || 'ℹ️'}</span>
        <div class="toast-content">
            <div class="toast-title">${escapeHtml(titulo)}</div>
            <div class="toast-message">${escapeHtml(mensaje)}</div>
        </div>
    `;
    toast.addEventListener('click', () => {
        toast.classList.add('removing');
        setTimeout(() => toast.remove(), 300);
    });
    container.appendChild(toast);
    setTimeout(() => {
        if (toast.parentNode) {
            toast.classList.add('removing');
            setTimeout(() => toast.remove(), 300);
        }
    }, 5000);
}

// Toast especial para insight diario (tipo Duolingo)
function mostrarToastInsight(insight) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'glass-toast glass-toast--insight';
    toast.innerHTML = `
        <span class="toast-icon">💡</span>
        <div class="toast-content">
            <div class="toast-title">Tu análisis del día está listo</div>
            <div class="toast-message">${escapeHtml(insight.substring(0, 120))}${insight.length > 120 ? '...' : ''}</div>
            <button class="toast-action-btn" onclick="this.closest('.glass-toast').remove(); scrollToPerfilIA();">Ver perfil completo →</button>
        </div>
    `;
    toast.addEventListener('click', (e) => {
        if (e.target.tagName !== 'BUTTON') {
            toast.classList.add('removing');
            setTimeout(() => toast.remove(), 300);
        }
    });
    container.appendChild(toast);
    setTimeout(() => {
        if (toast.parentNode) {
            toast.classList.add('removing');
            setTimeout(() => toast.remove(), 300);
        }
    }, 8000);
}

function scrollToPerfilIA() {
    const el = document.getElementById('seccion-perfil-ia');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
}

// ============================================================
//  SKELETON LOADERS
// ============================================================
function mostrarSkeletonMovimientos() {
    const container = document.getElementById('lista-movimientos');
    container.innerHTML = Array(4).fill(0).map(() => `
        <div class="skeleton-item">
            <div class="skeleton skeleton-icon"></div>
            <div class="skeleton-lines">
                <div class="skeleton skeleton-line-lg"></div>
                <div class="skeleton skeleton-line-sm"></div>
            </div>
            <div class="skeleton skeleton-amount"></div>
        </div>
    `).join('');
}

function mostrarSkeletonPerfilIA() {
    const sk = document.getElementById('perfil-skeleton');
    if (sk) sk.style.display = 'flex';
}

function ocultarSkeletonPerfilIA() {
    const sk = document.getElementById('perfil-skeleton');
    if (sk) sk.style.display = 'none';
}

// ============================================================
//  F1: REGISTRARSE
// ============================================================
function toggleAuthForm(mode) {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const subtitle = document.getElementById('auth-subtitle');
    const errorDiv = document.getElementById('auth-error');

    errorDiv.classList.remove('visible');
    errorDiv.textContent = '';

    if (mode === 'register') {
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
        subtitle.textContent = 'Crea tu cuenta gratuita';
    } else {
        loginForm.style.display = 'block';
        registerForm.style.display = 'none';
        subtitle.textContent = 'Control financiero inteligente y seguro';
    }
}

document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const errorDiv = document.getElementById('auth-error');
    errorDiv.classList.remove('visible');

    const nombre = document.getElementById('reg-nombre').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;

    try {
        const resp = await apiRequest('/auth/registro', 'POST', { nombre, email, password });
        mostrarToast('¡Bienvenido!', resp.mensaje, 'exito');
        toggleAuthForm('login');
        document.getElementById('login-email').value = email;
    } catch (err) {
        const msg = err.errores ? err.errores.join(' ') : (err.mensaje || 'Error al registrarse.');
        errorDiv.textContent = msg;
        errorDiv.classList.add('visible');
    }
});

// ============================================================
//  F2: INICIAR SESIÓN
// ============================================================
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const errorDiv = document.getElementById('auth-error');
    errorDiv.classList.remove('visible');

    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;

    try {
        const resp = await apiRequest('/auth/login', 'POST', { email, password });
        estadoApp.usuario = resp.data;
        iniciarDashboard();
        resetearSessionTimeout();
        guardarCredencialesBiometrico(email, password);
        mostrarToast('Sesion iniciada', `Hola, ${escapeHtml(resp.data.nombre)}`, 'exito');
    } catch (err) {
        const msg = err.errores ? err.errores.join(' ') : (err.mensaje || 'Error al iniciar sesión.');
        errorDiv.textContent = msg;
        errorDiv.classList.add('visible');
    }
});

// ============================================================
//  CERRAR SESIÓN
// ============================================================
async function cerrarSesion() {
    try { await apiRequest('/auth/logout', 'POST'); } catch (_) {}
    estadoApp.usuario = null;
    if (estadoApp.sesionTimeoutId) {
        clearTimeout(estadoApp.sesionTimeoutId);
        estadoApp.sesionTimeoutId = null;
    }
    // Destruir charts
    if (chartCategorias) { chartCategorias.destroy(); chartCategorias = null; }
    if (chartTendencia) { chartTendencia.destroy(); chartTendencia = null; }
    document.getElementById('auth-view').classList.remove('hidden');
    document.getElementById('dashboard').classList.remove('active');
    document.getElementById('login-form').reset();
    document.getElementById('register-form').reset();
    document.getElementById('auth-error').classList.remove('visible');
}

// ============================================================
//  DASHBOARD: Inicialización
// ============================================================
function iniciarDashboard() {
    document.getElementById('auth-view').classList.add('hidden');
    document.getElementById('dashboard').classList.add('active');
    document.getElementById('navbar-user').textContent = `Hola, ${estadoApp.usuario.nombre}`;
    aplicarModo(estadoApp.modoOscuro);
    cargarBalance();
    cargarMovimientos();
    cargarResumen();
    cargarNotificaciones();
    // Insight diario tipo Duolingo (async, no bloquea)
    verificarInsightDiario();
    // Perfil IA (async, no bloquea)
    cargarPerfilIA();
}

// ============================================================
//  F4: SOLICITAR BALANCE
// ============================================================
async function cargarBalance() {
    try {
        const resp = await apiRequest('/balance');
        const data = resp.data;
        const balanceEl = document.getElementById('balance-total');
        balanceEl.textContent = formatMoney(data.balance);
        balanceEl.className = 'balance-amount ' + (data.balance >= 0 ? 'positive' : 'negative');
        document.getElementById('balance-ingresos').textContent = formatMoney(data.total_ingresos);
        document.getElementById('balance-gastos').textContent = formatMoney(data.total_gastos);
        document.getElementById('balance-movimientos').textContent = data.total_movimientos;
    } catch (err) {
        mostrarToast('Error', 'No se pudo cargar el balance.', 'error');
    }
}

// ============================================================
//  F3: GESTIONAR MOVIMIENTO - Listar con filtros avanzados
// ============================================================
async function cargarMovimientos(tipo = null) {
    const container = document.getElementById('lista-movimientos');
    mostrarSkeletonMovimientos();

    try {
        const filtroDesde = document.getElementById('filtro-desde')?.value || '';
        const filtroHasta = document.getElementById('filtro-hasta')?.value || '';
        const filtroCat   = document.getElementById('filtro-categoria')?.value || '';
        const filtroMontoMin = document.getElementById('filtro-monto-min')?.value || '';
        const filtroMontoMax = document.getElementById('filtro-monto-max')?.value || '';

        let endpoint = '/movimientos?limite=100';
        const filtroTipo = tipo || (estadoApp.filtroActual !== 'todos' ? estadoApp.filtroActual : null);
        if (filtroTipo && filtroTipo !== 'todos') endpoint += `&tipo=${filtroTipo}`;
        if (filtroDesde) endpoint += `&fecha_desde=${filtroDesde}`;
        if (filtroHasta) endpoint += `&fecha_hasta=${filtroHasta}`;
        if (filtroCat)   endpoint += `&categoria_id=${filtroCat}`;
        if (filtroMontoMin) endpoint += `&monto_min=${filtroMontoMin}`;
        if (filtroMontoMax) endpoint += `&monto_max=${filtroMontoMax}`;

        const resp = await apiRequest(endpoint);
        const movimientos = resp.data;

        if (movimientos.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">💸</div>
                    <p>No hay movimientos que coincidan</p>
                </div>
            `;
            return;
        }

        let html = '';
        movimientos.forEach(mov => {
            const esIngreso = mov.tipo === 'ingreso';
            const tipoClass = esIngreso ? 'income' : 'expense';
            const signo = esIngreso ? '+' : '-';
            const dataMov = escapeHtml(JSON.stringify({
                id: mov.id, tipo: mov.tipo, monto: mov.monto,
                categoria_id: mov.categoria_id, descripcion: mov.descripcion,
                fecha: mov.fecha ? mov.fecha.substring(0, 10) : '',
                categoria_nombre: mov.categoria_nombre
            }));

            html += `
                <div class="transaction-item fade-in" data-id="${mov.id}">
                    <div class="transaction-icon ${tipoClass}">
                        ${escapeHtml(mov.categoria_icono || '💰')}
                    </div>
                    <div class="transaction-details">
                        <div class="transaction-category">${escapeHtml(mov.categoria_nombre)}</div>
                        <div class="transaction-description">${escapeHtml(mov.descripcion || 'Sin descripción')}</div>
                    </div>
                    <div class="transaction-meta">
                        <div class="transaction-amount ${tipoClass}">${signo}${formatMoney(mov.monto)}</div>
                        <div class="transaction-date">${formatDate(mov.fecha)}</div>
                    </div>
                    <div class="transaction-actions">
                        <button class="transaction-edit" onclick='abrirModalEditarMovimiento(${mov.id}, ${dataMov})' title="Editar">✏️</button>
                        <button class="transaction-delete" onclick="confirmarBorrado(${mov.id})" title="Eliminar">🗑️</button>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    } catch (err) {
        mostrarToast('Error', 'No se pudieron cargar los movimientos.', 'error');
        container.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><p>Error al cargar</p></div>`;
    }
}

function filtrarMovimientos(tipo, tabElement) {
    estadoApp.filtroActual = tipo;
    document.querySelectorAll('.glass-tab').forEach(t => t.classList.remove('active'));
    if (tabElement) tabElement.classList.add('active');
    cargarMovimientos(tipo);
}

// ============================================================
//  FILTROS AVANZADOS
// ============================================================
async function aplicarFiltrosAvanzados() {
    await cargarMovimientos(estadoApp.filtroActual !== 'todos' ? estadoApp.filtroActual : null);
    mostrarToast('Filtros', 'Filtros aplicados correctamente.', 'info');
}

function limpiarFiltrosAvanzados() {
    const campos = ['filtro-desde', 'filtro-hasta', 'filtro-categoria', 'filtro-monto-min', 'filtro-monto-max'];
    campos.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    cargarMovimientos();
}

async function cargarCategoriasEnFiltro() {
    try {
        const resp = await apiRequest('/categorias');
        const select = document.getElementById('filtro-categoria');
        if (!select) return;
        select.innerHTML = '<option value="">Todas las categorías</option>';
        resp.data.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat.id;
            opt.textContent = `${cat.icono} ${cat.nombre}`;
            select.appendChild(opt);
        });
    } catch (_) {}
}

// ============================================================
//  EXPORTAR CSV
// ============================================================
async function exportarCSV() {
    try {
        const filtroDesde = document.getElementById('filtro-desde')?.value || '';
        const filtroHasta = document.getElementById('filtro-hasta')?.value || '';
        const filtroTipo  = estadoApp.filtroActual !== 'todos' ? estadoApp.filtroActual : '';

        let endpoint = '/movimientos/export/csv?';
        if (filtroTipo) endpoint += `tipo=${filtroTipo}&`;
        if (filtroDesde) endpoint += `fecha_desde=${filtroDesde}&`;
        if (filtroHasta) endpoint += `fecha_hasta=${filtroHasta}&`;

        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'GET',
            credentials: 'include'
        });

        if (!response.ok) throw new Error('Error al exportar');

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const fecha = new Date().toISOString().split('T')[0].replace(/-/g, '');
        a.download = `controlcash_${fecha}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);

        mostrarToast('Exportado', 'Movimientos exportados en CSV.', 'exito');
    } catch (err) {
        mostrarToast('Error', 'No se pudo exportar el CSV.', 'error');
    }
}

// ============================================================
//  F3: GESTIONAR MOVIMIENTO - Crear
// ============================================================
async function abrirModalMovimiento(tipo) {
    document.getElementById('mov-tipo').value = tipo;
    const titulo = tipo === 'ingreso' ? '📥 Nuevo Ingreso' : '📤 Nuevo Gasto';
    document.getElementById('modal-movimiento-titulo').textContent = titulo;

    try {
        const resp = await apiRequest(`/categorias?tipo=${tipo}`);
        const select = document.getElementById('mov-categoria');
        select.innerHTML = '<option value="">Seleccionar categoría</option>';
        resp.data.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat.id;
            option.textContent = `${cat.icono} ${cat.nombre}`;
            select.appendChild(option);
        });
    } catch (err) {
        mostrarToast('Error', 'No se pudieron cargar las categorías.', 'error');
    }

    document.getElementById('mov-fecha').value = new Date().toISOString().split('T')[0];
    document.getElementById('modal-error').classList.remove('visible');
    document.getElementById('form-movimiento').reset();
    document.getElementById('mov-fecha').value = new Date().toISOString().split('T')[0];
    document.getElementById('mov-tipo').value = tipo;
    document.getElementById('modal-movimiento').classList.add('active');
}

function cerrarModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

document.getElementById('modal-movimiento').addEventListener('click', function(e) {
    if (e.target === this) cerrarModal('modal-movimiento');
});

document.getElementById('form-movimiento').addEventListener('submit', async (e) => {
    e.preventDefault();
    const errorDiv = document.getElementById('modal-error');
    errorDiv.classList.remove('visible');

    const datos = {
        tipo: document.getElementById('mov-tipo').value,
        monto: document.getElementById('mov-monto').value,
        categoria_id: document.getElementById('mov-categoria').value,
        descripcion: document.getElementById('mov-descripcion').value,
        fecha: document.getElementById('mov-fecha').value
    };

    try {
        const resp = await apiRequest('/movimientos', 'POST', datos);
        mostrarToast('Registrado', resp.mensaje, 'exito');
        cerrarModal('modal-movimiento');
        cargarBalance();
        cargarMovimientos(estadoApp.filtroActual);
        cargarResumen();
        cargarNotificaciones();
    } catch (err) {
        const msg = err.errores ? err.errores.join(' ') : (err.mensaje || 'Error al guardar.');
        errorDiv.textContent = msg;
        errorDiv.classList.add('visible');
    }
});

// ============================================================
//  F3: GESTIONAR MOVIMIENTO - Editar
// ============================================================
async function abrirModalEditarMovimiento(id, datos) {
    estadoApp.movimientoEditandoId = id;

    // Cargar categorías
    try {
        const resp = await apiRequest(`/categorias?tipo=${datos.tipo}`);
        const select = document.getElementById('edit-mov-categoria');
        if (select) {
            select.innerHTML = '<option value="">Seleccionar categoría</option>';
            resp.data.forEach(cat => {
                const option = document.createElement('option');
                option.value = cat.id;
                option.textContent = `${cat.icono} ${cat.nombre}`;
                if (cat.id == datos.categoria_id) option.selected = true;
                select.appendChild(option);
            });
        }
    } catch (_) {}

    // Rellenar campos
    const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.value = val || ''; };
    setVal('edit-mov-tipo', datos.tipo);
    setVal('edit-mov-monto', datos.monto);
    setVal('edit-mov-descripcion', datos.descripcion);
    setVal('edit-mov-fecha', datos.fecha ? datos.fecha.substring(0, 10) : '');

    // Título del modal
    const titulo = datos.tipo === 'ingreso' ? '✏️ Editar Ingreso' : '✏️ Editar Gasto';
    const tituloEl = document.getElementById('modal-editar-titulo');
    if (tituloEl) tituloEl.textContent = titulo;

    const errDiv = document.getElementById('edit-modal-error');
    if (errDiv) errDiv.classList.remove('visible');

    document.getElementById('modal-editar-movimiento').classList.add('active');
}

document.addEventListener('DOMContentLoaded', () => {
    const formEditar = document.getElementById('form-editar-movimiento');
    if (formEditar) {
        formEditar.addEventListener('submit', async (e) => {
            e.preventDefault();
            const errDiv = document.getElementById('edit-modal-error');
            if (errDiv) errDiv.classList.remove('visible');

            const datos = {
                tipo: document.getElementById('edit-mov-tipo').value,
                monto: document.getElementById('edit-mov-monto').value,
                categoria_id: document.getElementById('edit-mov-categoria').value,
                descripcion: document.getElementById('edit-mov-descripcion').value,
                fecha: document.getElementById('edit-mov-fecha').value,
            };

            try {
                const resp = await apiRequest(`/movimientos/${estadoApp.movimientoEditandoId}`, 'PUT', datos);
                mostrarToast('Actualizado', 'Movimiento actualizado correctamente.', 'exito');
                cerrarModal('modal-editar-movimiento');
                cargarBalance();
                cargarMovimientos(estadoApp.filtroActual);
                cargarResumen();
            } catch (err) {
                const msg = err.errores ? err.errores.join(' ') : (err.mensaje || 'Error al actualizar.');
                if (errDiv) { errDiv.textContent = msg; errDiv.classList.add('visible'); }
            }
        });
    }

    const editOverlay = document.getElementById('modal-editar-movimiento');
    if (editOverlay) {
        editOverlay.addEventListener('click', function(e) {
            if (e.target === this) cerrarModal('modal-editar-movimiento');
        });
    }
});

// ============================================================
//  F3: GESTIONAR MOVIMIENTO - Confirmación de borrado
// ============================================================
function confirmarBorrado(id) {
    estadoApp.movimientosBorrandoId = id;
    const modal = document.getElementById('modal-confirmar-borrado');
    if (modal) modal.classList.add('active');
}

document.addEventListener('DOMContentLoaded', () => {
    const btnConfirmarBorrado = document.getElementById('btn-confirmar-borrado');
    if (btnConfirmarBorrado) {
        btnConfirmarBorrado.addEventListener('click', async () => {
            const id = estadoApp.movimientosBorrandoId;
            if (!id) return;
            cerrarModal('modal-confirmar-borrado');
            estadoApp.movimientosBorrandoId = null;

            try {
                await apiRequest(`/movimientos/${id}`, 'DELETE');
                mostrarToast('Eliminado', 'Movimiento eliminado correctamente.', 'info');
                cargarBalance();
                cargarMovimientos(estadoApp.filtroActual);
                cargarResumen();
            } catch (err) {
                mostrarToast('Error', 'No se pudo eliminar el movimiento.', 'error');
            }
        });
    }

    const cancelarBorrado = document.getElementById('btn-cancelar-borrado');
    if (cancelarBorrado) {
        cancelarBorrado.addEventListener('click', () => {
            cerrarModal('modal-confirmar-borrado');
            estadoApp.movimientosBorrandoId = null;
        });
    }

    const borradoOverlay = document.getElementById('modal-confirmar-borrado');
    if (borradoOverlay) {
        borradoOverlay.addEventListener('click', function(e) {
            if (e.target === this) {
                cerrarModal('modal-confirmar-borrado');
                estadoApp.movimientosBorrandoId = null;
            }
        });
    }
});

// ============================================================
//  F7: RESUMEN FINANCIERO con Chart.js
// ============================================================
async function cargarResumen() {
    try {
        const resp = await apiRequest('/resumen?dias=30');
        const data = resp.data;
        const categorias = data.por_categoria;

        // Métricas
        const v = data.variacion_vs_anterior_pct || 0;
        const signo = v > 0 ? '+' : '';
        const elPromedio   = document.getElementById('metric-promedio');
        const elProyeccion = document.getElementById('metric-proyeccion');
        const elVariacion  = document.getElementById('metric-variacion');
        const elMovimientos = document.getElementById('metric-movimientos');

        if (elPromedio) elPromedio.textContent = formatMoney(data.promedio_diario_gasto || 0);
        if (elProyeccion) elProyeccion.textContent = formatMoney(data.proyeccion_30_dias || 0);
        if (elMovimientos) elMovimientos.textContent = data.total_movimientos || 0;
        if (elVariacion) {
            elVariacion.textContent = `${signo}${v}%`;
            elVariacion.className = 'metric-value ' + (v > 0 ? 'negative' : v < 0 ? 'positive' : '');
        }

        // Top 3 gastos
        const topContainer = document.getElementById('top-gastos');
        const topList = document.getElementById('top-gastos-list');
        if (topContainer && topList) {
            if (data.top_gastos && data.top_gastos.length > 0) {
                topContainer.style.display = 'block';
                topList.innerHTML = data.top_gastos.map(g => `
                    <div class="top-gasto-item">
                        <div class="top-gasto-info">
                            <span>${escapeHtml(g.icono || '📦')}</span>
                            <span>${escapeHtml(g.descripcion || g.categoria)}</span>
                        </div>
                        <span class="top-gasto-monto">${formatMoney(g.monto)}</span>
                    </div>
                `).join('');
            } else {
                topContainer.style.display = 'none';
            }
        }

        // Charts con Chart.js
        renderizarCharts(data, categorias);

    } catch (err) {
        mostrarToast('Error', 'No se pudo cargar el resumen.', 'error');
    }
}

function renderizarCharts(data, categorias) {
    // ── Donut chart por categoría ──
    const ctxDonut = document.getElementById('chart-categorias');
    if (ctxDonut && categorias && categorias.length > 0) {
        const gastos = categorias.filter(c => c.tipo === 'gasto');
        const labels = gastos.map(c => `${c.icono} ${c.nombre}`);
        const valores = gastos.map(c => c.total);
        const colores = [
            '#6C63FF','#FF5A5F','#00C48C','#FFB800','#00B4D8',
            '#a855f7','#f97316','#84cc16','#14b8a6','#ec4899'
        ];

        if (chartCategorias) {
            chartCategorias.data.labels = labels;
            chartCategorias.data.datasets[0].data = valores;
            chartCategorias.update();
        } else {
            chartCategorias = new Chart(ctxDonut, {
                type: 'doughnut',
                data: {
                    labels,
                    datasets: [{
                        data: valores,
                        backgroundColor: colores.slice(0, labels.length),
                        borderColor: 'rgba(255,255,255,0.1)',
                        borderWidth: 2,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: 'rgba(255,255,255,0.8)', font: { family: 'Inter', size: 11 }, padding: 12 }
                        },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => ` ${ctx.label}: ${formatMoney(ctx.raw)} (${ctx.parsed > 0 ? Math.round(ctx.parsed / ctx.dataset.data.reduce((a,b) => a+b, 0) * 100) : 0}%)`
                            }
                        }
                    },
                    cutout: '60%',
                }
            });
        }
    } else if (ctxDonut) {
        // Sin datos
        const parent = ctxDonut.parentElement;
        if (parent) parent.innerHTML = `<div class="empty-state"><div class="empty-icon">📊</div><p>Aún no hay datos para mostrar</p></div>`;
    }

    // ── Line chart tendencia diaria ──
    const ctxLine = document.getElementById('chart-tendencia');
    if (ctxLine && data.diario && data.diario.length > 0) {
        // Agrupar por día
        const diasMap = {};
        data.diario.forEach(d => {
            if (!diasMap[d.dia]) diasMap[d.dia] = { ingreso: 0, gasto: 0 };
            diasMap[d.dia][d.tipo] = d.total;
        });
        const dias = Object.keys(diasMap).sort();
        const ingresos = dias.map(d => diasMap[d].ingreso || 0);
        const gastos = dias.map(d => diasMap[d].gasto || 0);

        const labelsCortos = dias.map(d => {
            const fecha = new Date(d + 'T00:00:00');
            return fecha.toLocaleDateString('es-MX', { day: 'numeric', month: 'short' });
        });

        if (chartTendencia) {
            chartTendencia.data.labels = labelsCortos;
            chartTendencia.data.datasets[0].data = gastos;
            chartTendencia.data.datasets[1].data = ingresos;
            chartTendencia.update();
        } else {
            chartTendencia = new Chart(ctxLine, {
                type: 'line',
                data: {
                    labels: labelsCortos,
                    datasets: [
                        {
                            label: 'Gastos',
                            data: gastos,
                            borderColor: '#FF5A5F',
                            backgroundColor: 'rgba(255,90,95,0.12)',
                            fill: true,
                            tension: 0.4,
                            pointBackgroundColor: '#FF5A5F',
                            pointRadius: 3,
                        },
                        {
                            label: 'Ingresos',
                            data: ingresos,
                            borderColor: '#00C48C',
                            backgroundColor: 'rgba(0,196,140,0.12)',
                            fill: true,
                            tension: 0.4,
                            pointBackgroundColor: '#00C48C',
                            pointRadius: 3,
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { color: 'rgba(255,255,255,0.8)', font: { family: 'Inter', size: 11 } }
                        },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => ` ${ctx.dataset.label}: ${formatMoney(ctx.raw)}`
                            }
                        }
                    },
                    scales: {
                        x: {
                            ticks: { color: 'rgba(255,255,255,0.5)', font: { size: 10 }, maxTicksLimit: 8 },
                            grid: { color: 'rgba(255,255,255,0.05)' }
                        },
                        y: {
                            ticks: {
                                color: 'rgba(255,255,255,0.5)', font: { size: 10 },
                                callback: (val) => '$' + val.toLocaleString('es-MX')
                            },
                            grid: { color: 'rgba(255,255,255,0.05)' }
                        }
                    }
                }
            });
        }
    }
}

// ============================================================
//  PERFIL IA — Panel en dashboard
// ============================================================
async function cargarPerfilIA(forzar = false) {
    mostrarSkeletonPerfilIA();
    try {
        const endpoint = forzar ? '/ai/perfil?force=1' : '/ai/perfil';
        const resp = await apiRequest(endpoint);
        renderizarPerfilIA(resp.data);
    } catch (err) {
        ocultarSkeletonPerfilIA();
        const panel = document.getElementById('perfil-ia-contenido');
        if (panel) panel.innerHTML = `
            <p class="text-muted" style="text-align:center; padding: var(--space-md);">
                ${err.mensaje && err.mensaje.includes('NVIDIA') ? '🔑 Configura NVIDIA_API_KEY para activar el perfil IA' : '⚠️ No se pudo generar el perfil'}
            </p>
        `;
    }
}

function renderizarPerfilIA(data) {
    ocultarSkeletonPerfilIA();
    if (!data) return;

    const tipoLabel = data.tipo_label || 'Tu Perfil Financiero';
    const score = Math.max(0, Math.min(100, parseInt(data.score) || 0));
    const tags = data.tags || [];
    const narrativa = data.narrativa || '';
    const habitos = data.habitos || data.habitos_positivos || [];
    const areas = data.areas_mejora || [];

    // Avatar basado en score
    let avatar = '🧑';
    if (score >= 80) avatar = '🏆';
    else if (score >= 60) avatar = '😊';
    else if (score >= 40) avatar = '😐';
    else avatar = '📉';

    // Color del score
    let scoreColor = '#FF5A5F';
    if (score >= 70) scoreColor = '#00C48C';
    else if (score >= 40) scoreColor = '#FFB800';

    const el = document.getElementById('perfil-avatar');
    if (el) el.textContent = avatar;

    const labelEl = document.getElementById('perfil-tipo-label');
    if (labelEl) labelEl.textContent = tipoLabel;

    const scoreNumEl = document.getElementById('perfil-score-num');
    if (scoreNumEl) {
        scoreNumEl.textContent = score;
        scoreNumEl.style.color = scoreColor;
    }

    // Animar barra de score
    setTimeout(() => {
        const fillEl = document.getElementById('perfil-score-fill');
        if (fillEl) {
            fillEl.style.width = score + '%';
            fillEl.style.background = `linear-gradient(90deg, #FF5A5F, #FFB800, ${scoreColor})`;
        }
    }, 100);

    // Tags
    const tagsEl = document.getElementById('perfil-tags');
    if (tagsEl) {
        tagsEl.innerHTML = tags.map(t => `<span class="tag-pill">${escapeHtml(t)}</span>`).join('');
    }

    // Narrativa
    const narrEl = document.getElementById('perfil-narrativa');
    if (narrEl) narrEl.textContent = narrativa;

    // Hábitos y áreas de mejora
    const detEl = document.getElementById('perfil-detalles');
    if (detEl) {
        let html = '';
        if (habitos.length > 0) {
            html += `<div class="perfil-detalles-seccion">
                <h5>✅ Hábitos positivos</h5>
                <ul>${habitos.map(h => `<li>${escapeHtml(h)}</li>`).join('')}</ul>
            </div>`;
        }
        if (areas.length > 0) {
            html += `<div class="perfil-detalles-seccion">
                <h5>💡 Áreas de mejora</h5>
                <ul>${areas.map(a => `<li>${escapeHtml(a)}</li>`).join('')}</ul>
            </div>`;
        }
        detEl.innerHTML = html;
    }
}

// Botón actualizar perfil
document.addEventListener('DOMContentLoaded', () => {
    const btnActualizarPerfil = document.getElementById('btn-actualizar-perfil');
    if (btnActualizarPerfil) {
        btnActualizarPerfil.addEventListener('click', async () => {
            btnActualizarPerfil.disabled = true;
            btnActualizarPerfil.textContent = '⏳ Analizando...';
            // Forzar regeneración borrando caché del día temporalmente
            mostrarSkeletonPerfilIA();
            try {
                const resp = await apiRequest('/ai/perfil');
                renderizarPerfilIA(resp.data);
                mostrarToast('Perfil IA', 'Perfil actualizado correctamente.', 'exito');
            } catch (err) {
                ocultarSkeletonPerfilIA();
                mostrarToast('Error', 'No se pudo actualizar el perfil.', 'error');
            } finally {
                btnActualizarPerfil.disabled = false;
                btnActualizarPerfil.textContent = '↻ Actualizar';
            }
        });
    }
});

// ============================================================
//  INSIGHT DIARIO (tipo Duolingo)
// ============================================================
async function verificarInsightDiario() {
    try {
        const resp = await apiRequest('/ai/daily-insight', 'POST');
        if (resp.data && !resp.data.ya_existia && resp.data.insight) {
            // Mostrar toast especial con animación
            mostrarToastInsight(resp.data.insight);
            // Actualizar badge de notificaciones
            cargarNotificaciones();
        }
    } catch (_) {
        // Silent: insight diario es opcional, no interrumpir experiencia
    }
}

// ============================================================
//  F6: NOTIFICACIONES
// ============================================================
async function cargarNotificaciones() {
    try {
        const resp = await apiRequest('/notificaciones?no_leidas=true');
        const notificaciones = resp.data;
        const countEl = document.getElementById('notif-count');

        if (notificaciones.length > 0) {
            countEl.textContent = notificaciones.length;
            countEl.style.display = 'flex';
        } else {
            countEl.style.display = 'none';
        }

        const panel = document.getElementById('notification-panel');
        if (notificaciones.length === 0) {
            panel.innerHTML = `
                <div class="empty-state" style="padding: var(--space-lg);">
                    <p style="font-size: var(--font-size-sm);">Sin notificaciones nuevas</p>
                </div>
            `;
            return;
        }

        let html = '';
        notificaciones.forEach(n => {
            html += `
                <div class="notification-item unread" onclick="marcarNotificacionLeida(${n.id}, this)">
                    <div class="notif-title">${escapeHtml(n.titulo)}</div>
                    <div class="notif-message">${escapeHtml(n.mensaje)}</div>
                    <div class="notif-time">${formatDate(n.fecha)}</div>
                </div>
            `;
        });
        panel.innerHTML = html;
    } catch (_) {}
}

function toggleNotificationPanel() {
    const panel = document.getElementById('notification-panel');
    estadoApp.notifPanelAbierto = !estadoApp.notifPanelAbierto;
    panel.classList.toggle('active', estadoApp.notifPanelAbierto);
}

async function marcarNotificacionLeida(id, element) {
    try {
        await apiRequest(`/notificaciones/${id}`, 'PUT');
        element.classList.remove('unread');
        cargarNotificaciones();
    } catch (_) {}
}

document.addEventListener('click', (e) => {
    const panel = document.getElementById('notification-panel');
    const btn = document.getElementById('notif-btn');
    if (estadoApp.notifPanelAbierto && !panel.contains(e.target) && !btn.contains(e.target)) {
        estadoApp.notifPanelAbierto = false;
        panel.classList.remove('active');
    }
});

// ============================================================
//  TECLADO: Escape para cerrar modales
// ============================================================
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        cerrarModal('modal-movimiento');
        cerrarModal('modal-editar-movimiento');
        cerrarModal('modal-confirmar-borrado');
        cerrarModal('modal-ocr');
        cerrarModal('modal-chat');
        if (estadoApp.notifPanelAbierto) {
            estadoApp.notifPanelAbierto = false;
            document.getElementById('notification-panel').classList.remove('active');
        }
    }
});

// ============================================================
//  F4-OCR: ESCANEO DE RECIBOS
// ============================================================
let ocrDatosActuales = null;

function abrirModalOCR() {
    ocrDatosActuales = null;
    document.getElementById('ocr-preview').style.display = 'none';
    document.getElementById('ocr-placeholder').style.display = 'block';
    document.getElementById('ocr-resultado').style.display = 'none';
    document.getElementById('ocr-loading').style.display = 'none';
    document.getElementById('btn-escanear').disabled = true;
    document.getElementById('btn-usar-ocr').style.display = 'none';
    document.getElementById('modal-ocr').classList.add('active');
}

document.getElementById('ocr-drop-zone').addEventListener('click', () => {
    document.getElementById('ocr-file-input').click();
});

document.getElementById('ocr-file-input').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) {
        mostrarToast('Error', 'Imagen demasiado grande (máx 10 MB).', 'error');
        return;
    }
    const reader = new FileReader();
    reader.onload = (ev) => {
        const img = document.getElementById('ocr-preview');
        img.src = ev.target.result;
        img.style.display = 'block';
        document.getElementById('ocr-placeholder').style.display = 'none';
        document.getElementById('btn-escanear').disabled = false;
        estadoApp.ocrBase64 = ev.target.result.split(',')[1];
    };
    reader.readAsDataURL(file);
});

const dropZone = document.getElementById('ocr-drop-zone');
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        const input = document.getElementById('ocr-file-input');
        const dt = new DataTransfer();
        dt.items.add(file);
        input.files = dt.files;
        input.dispatchEvent(new Event('change'));
    }
});

async function escanearRecibo() {
    if (!estadoApp.ocrBase64) return;
    document.getElementById('ocr-loading').style.display = 'block';
    document.getElementById('btn-escanear').disabled = true;

    try {
        const resp = await apiRequest('/ocr/recibo', 'POST', { imagen: estadoApp.ocrBase64 });
        ocrDatosActuales = resp.data;
        const datosDiv = document.getElementById('ocr-datos');
        datosDiv.innerHTML = `
            <p><strong>Total:</strong> ${ocrDatosActuales.total != null ? formatMoney(ocrDatosActuales.total) : 'No detectado'}</p>
            <p><strong>Fecha:</strong> ${escapeHtml(ocrDatosActuales.fecha || 'No detectada')}</p>
            <p><strong>Descripción:</strong> ${escapeHtml(ocrDatosActuales.descripcion || 'N/A')}</p>
            ${ocrDatosActuales.items && ocrDatosActuales.items.length > 0
                ? '<p><strong>Items:</strong></p><ul>' + ocrDatosActuales.items.map(i =>
                    `<li>${escapeHtml(i.nombre || '?')} — ${i.precio != null ? formatMoney(i.precio) : '?'}</li>`
                  ).join('') + '</ul>'
                : ''}
        `;
        document.getElementById('ocr-resultado').style.display = 'block';
        document.getElementById('btn-usar-ocr').style.display = 'block';
        mostrarToast('OCR', 'Recibo analizado exitosamente.', 'exito');
    } catch (err) {
        mostrarToast('Error OCR', err.mensaje || 'No se pudo analizar el recibo.', 'error');
    } finally {
        document.getElementById('ocr-loading').style.display = 'none';
        document.getElementById('btn-escanear').disabled = false;
    }
}

function usarDatosOCR() {
    if (!ocrDatosActuales) return;
    cerrarModal('modal-ocr');
    abrirModalMovimiento('gasto');
    setTimeout(() => {
        if (ocrDatosActuales.total != null) document.getElementById('mov-monto').value = ocrDatosActuales.total;
        if (ocrDatosActuales.descripcion) document.getElementById('mov-descripcion').value = ocrDatosActuales.descripcion;
        if (ocrDatosActuales.fecha) document.getElementById('mov-fecha').value = ocrDatosActuales.fecha;
    }, 100);
}

// ============================================================
//  F5-CHAT: ASISTENTE FINANCIERO LLM
// ============================================================
function abrirModalChat() {
    document.getElementById('modal-chat').classList.add('active');
    document.getElementById('chat-input').focus();
}

async function enviarChat(e) {
    e.preventDefault();
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;

    const container = document.getElementById('chat-messages');
    container.innerHTML += `
        <div class="chat-msg chat-msg--user">
            <span class="chat-avatar">👤</span>
            <div class="chat-bubble">${escapeHtml(msg)}</div>
        </div>
    `;
    input.value = '';
    container.scrollTop = container.scrollHeight;

    const loadingId = 'chat-loading-' + Date.now();
    container.innerHTML += `
        <div class="chat-msg chat-msg--bot" id="${loadingId}">
            <span class="chat-avatar">🤖</span>
            <div class="chat-bubble"><div class="loading-spinner" style="width:20px;height:20px;border-width:2px;"></div></div>
        </div>
    `;
    container.scrollTop = container.scrollHeight;

    try {
        const resp = await apiRequest('/chat', 'POST', { mensaje: msg });
        const loadEl = document.getElementById(loadingId);
        if (loadEl) loadEl.remove();
        container.innerHTML += `
            <div class="chat-msg chat-msg--bot">
                <span class="chat-avatar">🤖</span>
                <div class="chat-bubble">${escapeHtml(resp.data.respuesta)}</div>
            </div>
        `;
    } catch (err) {
        const loadEl = document.getElementById(loadingId);
        if (loadEl) loadEl.remove();
        container.innerHTML += `
            <div class="chat-msg chat-msg--bot">
                <span class="chat-avatar">🤖</span>
                <div class="chat-bubble">Lo siento, hubo un error. Intenta de nuevo.</div>
            </div>
        `;
    }
    container.scrollTop = container.scrollHeight;
}

// ============================================================
//  PWA: Registro del Service Worker
// ============================================================
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/service-worker.js')
            .then((reg) => console.log('[PWA] Service Worker registrado:', reg.scope))
            .catch((err) => console.warn('[PWA] Error registrando SW:', err));
    });
}

// ============================================================
//  AUTENTICACION BIOMETRICA (Capacitor)
// ============================================================
async function verificarBiometrico() {
    try {
        if (typeof Capacitor !== 'undefined' && Capacitor.isNativePlatform()) {
            const { BiometricAuth } = Capacitor.Plugins;
            if (BiometricAuth) {
                const result = await BiometricAuth.isAvailable();
                if (result.isAvailable) {
                    estadoApp.biometricoDisponible = true;
                    const btnBio = document.getElementById('btn-biometric');
                    const dividerBio = document.getElementById('auth-divider-biometric');
                    if (btnBio) btnBio.style.display = 'flex';
                    if (dividerBio) dividerBio.style.display = 'flex';
                }
            }
        }
    } catch (err) {
        console.log('[Bio] Biometrico no disponible:', err.message || err);
    }
}

async function autenticacionBiometrica() {
    if (!estadoApp.biometricoDisponible) {
        mostrarToast('No disponible', 'Autenticacion biometrica no disponible.', 'alerta');
        return;
    }
    try {
        const { BiometricAuth } = Capacitor.Plugins;
        await BiometricAuth.authenticate({
            reason: 'Verificar identidad para acceder a ControlCash',
            title: 'ControlCash - Acceso Seguro',
            subtitle: 'Usa tu huella o Face ID',
            cancelTitle: 'Cancelar',
            allowDeviceCredential: true
        });
        const { Preferences } = Capacitor.Plugins;
        const emailResult = await Preferences.get({ key: 'cc_bio_email' });
        const passResult  = await Preferences.get({ key: 'cc_bio_pass' });
        if (emailResult.value && passResult.value) {
            const resp = await apiRequest('/auth/login', 'POST', {
                email: emailResult.value, password: passResult.value
            });
            estadoApp.usuario = resp.data;
            iniciarDashboard();
            mostrarToast('Acceso biometrico', `Bienvenido, ${escapeHtml(resp.data.nombre)}`, 'exito');
        } else {
            mostrarToast('Configurar', 'Inicie sesion primero para activar el acceso biometrico.', 'info');
        }
    } catch (err) {
        if (err.message && err.message.includes('cancel')) return;
        mostrarToast('Error biometrico', 'No se pudo verificar la identidad.', 'error');
    }
}

async function guardarCredencialesBiometrico(email, password) {
    try {
        if (typeof Capacitor !== 'undefined' && Capacitor.isNativePlatform()) {
            const { Preferences } = Capacitor.Plugins;
            if (Preferences) {
                await Preferences.set({ key: 'cc_bio_email', value: email });
                await Preferences.set({ key: 'cc_bio_pass', value: password });
            }
        }
    } catch (_) {}
}

// ============================================================
//  PASSWORD STRENGTH CHECKER
// ============================================================
function evaluarPasswordStrength(password) {
    let score = 0;
    if (!password || password.length === 0) return { score: 0, label: 'Seguridad de contrasena', class: '' };
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++;
    if (/\d/.test(password)) score++;
    if (/[^a-zA-Z0-9]/.test(password)) score++;
    if (/^(.)\1+$/.test(password)) score = Math.max(0, score - 2);
    if (/^(123|abc|qwe|password|admin)/i.test(password)) score = 0;
    if (score <= 1) return { score: 1, label: 'Debil', class: 'weak' };
    if (score === 2) return { score: 2, label: 'Regular', class: 'fair' };
    if (score === 3) return { score: 3, label: 'Buena', class: 'good' };
    return { score: 4, label: 'Fuerte', class: 'strong' };
}

function actualizarPasswordStrength() {
    const password = document.getElementById('reg-password').value;
    const result = evaluarPasswordStrength(password);
    const fill = document.getElementById('strength-fill');
    const text = document.getElementById('strength-text');
    if (fill) fill.className = 'strength-fill' + (result.class ? ' ' + result.class : '');
    if (text) { text.textContent = result.label; text.className = 'strength-text' + (result.class ? ' ' + result.class : ''); }
}

document.getElementById('reg-password').addEventListener('input', actualizarPasswordStrength);

// ============================================================
//  SESSION TIMEOUT (ISO/IEC 27001)
// ============================================================
function resetearSessionTimeout() {
    if (estadoApp.sesionTimeoutId) clearTimeout(estadoApp.sesionTimeoutId);
    if (estadoApp.usuario) {
        estadoApp.sesionTimeoutId = setTimeout(() => {
            mostrarToast('Sesion expirada', 'Se cerro la sesion por inactividad (ISO 27001).', 'alerta');
            cerrarSesion();
        }, SESSION_TIMEOUT_MS);
    }
}

['click', 'keydown', 'mousemove', 'touchstart', 'scroll'].forEach(event => {
    document.addEventListener(event, () => {
        if (estadoApp.usuario) resetearSessionTimeout();
    }, { passive: true });
});

// ============================================================
//  INICIALIZACION
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    verificarBiometrico();
    aplicarModo(estadoApp.modoOscuro);
    cargarCategoriasEnFiltro();

    // Botón toggle modo claro/oscuro
    const btnModo = document.getElementById('btn-toggle-modo');
    if (btnModo) btnModo.addEventListener('click', toggleModo);
});
