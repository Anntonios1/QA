/**
 * ============================================================
 *  CAPA DE PRESENTACION - Categorías, Presupuestos y Automatización
 *  ControlCash v2.1 - Sistema Profesional de Control Financiero
 * ============================================================
 */

// ============================================================
//  UX: Onboarding rapido
// ============================================================
function mostrarOnboardingRapido() {
  const card = document.getElementById("onboarding-card");
  if (!card) return;
  const flag = localStorage.getItem("cc_onboarding_done");
  card.style.display = flag === "false" ? "block" : "none";
}

function cerrarOnboarding(permanente = false) {
  const card = document.getElementById("onboarding-card");
  if (card) card.style.display = "none";
  if (permanente) {
    localStorage.setItem("cc_onboarding_done", "true");
  }
}

// ============================================================
//  GESTIÓN DE CATEGORÍAS
// ============================================================
async function cargarCategoriasAdmin() {
  const container = document.getElementById("categorias-lista");
  if (!container) return;
  try {
    const resp = await apiRequest("/categorias");
    renderCategoriasAdmin(resp.data || []);
  } catch (_) {
    container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚠️</div>
                <p>No se pudieron cargar las categorías</p>
            </div>
        `;
  }
}

function renderCategoriasAdmin(categorias) {
  const container = document.getElementById("categorias-lista");
  if (!container) return;
  categoriasCache = Array.isArray(categorias) ? categorias : [];

  if (categoriasCache.length === 0) {
    container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📁</div>
                <p>Sin categorías disponibles</p>
                <button class="glass-btn glass-btn--sm empty-cta" onclick="document.getElementById('categoria-nombre')?.focus()">Crear categoría</button>
            </div>
        `;
    return;
  }

  let html = "";
  categoriasCache.forEach((cat) => {
    const icono = cat.icono || "🏷️";
    const tipoLabel = cat.tipo === "ingreso" ? "Ingreso" : "Gasto";
    const usos = Number(cat.usos || 0);
    const usoLabel = usos === 1 ? "1 uso" : `${usos} usos`;
    const descTxt = (cat.descripcion || "").trim();
    const descHtml = descTxt
      ? `<span class="categoria-desc">${escapeHtml(descTxt)}</span>`
      : "";
    html += `
            <div class="categoria-item">
                <div class="categoria-info">
                    <div class="categoria-icon">${escapeHtml(icono)}</div>
                    <div class="categoria-text">
                        <strong>${escapeHtml(cat.nombre)}</strong>
                        <span class="categoria-meta">${tipoLabel} · ${usoLabel}</span>
                        ${descHtml}
                    </div>
                </div>
                <div class="categoria-actions">
                    <button class="glass-btn glass-btn--sm" onclick="editarCategoria(${cat.id})">Editar</button>
                    <button class="glass-btn glass-btn--danger glass-btn--sm" onclick="desactivarCategoria(${cat.id})">Borrar</button>
                </div>
            </div>
        `;
  });

  container.innerHTML = html;
}

function editarCategoria(id) {
  const cat = categoriasCache.find((c) => String(c.id) === String(id));
  if (!cat) return;

  estadoApp.categoriaEditandoId = cat.id;
  const formTitle = document.getElementById("categoria-form-title");
  const btnGuardar = document.getElementById("btn-guardar-categoria");

  if (formTitle) formTitle.textContent = "Editar categoría";
  if (btnGuardar) btnGuardar.textContent = "Actualizar categoría";

  const inputNombre = document.getElementById("categoria-nombre");
  const inputTipo = document.getElementById("categoria-tipo");
  const inputIcono = document.getElementById("categoria-icono");
  const inputDescripcion = document.getElementById("categoria-descripcion");

  if (inputNombre) inputNombre.value = cat.nombre || "";
  if (inputTipo) inputTipo.value = cat.tipo || "gasto";
  if (inputIcono) inputIcono.value = cat.icono || "";
  if (inputDescripcion) inputDescripcion.value = cat.descripcion || "";
  actualizarIconPickerSeleccion(cat.icono || "");
}

function cancelarEdicionCategoria() {
  estadoApp.categoriaEditandoId = null;
  const form = document.getElementById("form-categoria");
  if (form) form.reset();
  const formTitle = document.getElementById("categoria-form-title");
  const btnGuardar = document.getElementById("btn-guardar-categoria");
  if (formTitle) formTitle.textContent = "Crear categoría";
  if (btnGuardar) btnGuardar.textContent = "Guardar categoría";
  actualizarIconPickerSeleccion("");
}

const ICONOS_CATEGORIA = [
  "💼",
  "💻",
  "📈",
  "🍔",
  "🚗",
  "🏠",
  "💡",
  "🏥",
  "📚",
  "🎮",
  "👕",
  "📦",
  "💳",
  "🧾",
  "🎯",
  "🛠️",
];

function actualizarIconPickerSeleccion(icono) {
  const container = document.getElementById("categoria-icon-picker");
  if (!container) return;
  const valor = String(icono || "").trim();
  container.querySelectorAll(".icon-option").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.icon === valor);
  });
}

function inicializarIconPicker() {
  const container = document.getElementById("categoria-icon-picker");
  if (!container) return;

  container.addEventListener("click", (e) => {
    const btn = e.target.closest(".icon-option");
    if (!btn) return;
    const icono = btn.dataset.icon || "";
    const input = document.getElementById("categoria-icono");
    if (input) input.value = icono;
    actualizarIconPickerSeleccion(icono);
  });

  const input = document.getElementById("categoria-icono");
  if (input) {
    input.addEventListener("input", () => {
      actualizarIconPickerSeleccion(input.value.trim());
    });
  }
}

async function desactivarCategoria(id) {
  try {
    await apiRequest(`/categorias/${id}`, "DELETE");
    mostrarToast("Categorías", "Categoría borrada.", "info");
    cargarCategoriasAdmin();
    cargarCategoriasEnFiltro();
    cargarCategoriasPresupuestos();
  } catch (err) {
    const msg = err?.mensaje || "No se pudo borrar la categoría.";
    mostrarToast("Error", msg, "error");
  }
}

async function cargarCategoriasPresupuestos() {
  const select = document.getElementById("presupuesto-categoria");
  const selectComp = document.getElementById("presupuesto-comparativo-categoria");
  if (!select) return;
  try {
    const resp = await apiRequest("/categorias?tipo=gasto");
    select.innerHTML =
      '<option value="">🌐 Global (todas las categorías)</option>';
    if (selectComp) {
      selectComp.innerHTML =
        '<option value="">🌐 Global (todas las categorías)</option>';
    }
    resp.data.forEach((cat) => {
      const opt = document.createElement("option");
      opt.value = cat.id;
      const icono = cat.icono || "🏷️";
      opt.textContent = `${icono} ${cat.nombre}`;
      select.appendChild(opt);

      if (selectComp) {
        const opt2 = document.createElement("option");
        opt2.value = cat.id;
        opt2.textContent = `${icono} ${cat.nombre}`;
        selectComp.appendChild(opt2);
      }
    });
  } catch (_) {}
}

// ============================================================
//  GESTIÓN DE PRESUPUESTOS
// ============================================================
function obtenerMesActualInput() {
  const now = new Date();
  const mes = String(now.getMonth() + 1).padStart(2, "0");
  return `${now.getFullYear()}-${mes}`;
}

function normalizarMesInput(mesInput) {
  if (!mesInput) return "";
  return `${mesInput}-01`;
}

function inicializarPresupuestosUI() {
  const mesActual = obtenerMesActualInput();
  const filtroMes = document.getElementById("presupuesto-filtro-mes");
  const formMes = document.getElementById("presupuesto-mes");
  if (filtroMes && !filtroMes.value) filtroMes.value = mesActual;
  if (formMes && !formMes.value) formMes.value = mesActual;
}

function limpiarFormularioPresupuesto() {
  const form = document.getElementById("form-presupuesto");
  if (form) form.reset();
  const mes = obtenerMesActualInput();
  const formMes = document.getElementById("presupuesto-mes");
  if (formMes) formMes.value = mes;
}

async function cargarPresupuestos() {
  const container = document.getElementById("presupuestos-lista");
  if (!container) return;
  const filtroMes = document.getElementById("presupuesto-filtro-mes");
  const mesInput = filtroMes?.value || "";
  const mes = normalizarMesInput(mesInput);
  const endpoint = mes ? `/presupuestos?mes=${mes}` : "/presupuestos";

  try {
    const resp = await apiRequest(endpoint);
    renderPresupuestos(resp.data || []);
    cargarComparativoPresupuesto();
  } catch (err) {
    container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚠️</div>
                <p>No se pudieron cargar los presupuestos</p>
            </div>
        `;
  }
}

function renderPresupuestos(presupuestos) {
  const container = document.getElementById("presupuestos-lista");
  if (!container) return;

  if (!Array.isArray(presupuestos) || presupuestos.length === 0) {
    container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📌</div>
                <p>Sin presupuestos definidos</p>
                <button class="glass-btn glass-btn--sm empty-cta" onclick="document.getElementById('presupuesto-monto')?.focus()">Crear presupuesto</button>
            </div>
        `;
    return;
  }

  const globales = presupuestos.filter((p) => !p.categoria_id);
  const porCategoria = presupuestos.filter((p) => p.categoria_id);
  const grupos = [
    { titulo: "Presupuesto global", items: globales, icono: "🌐" },
    { titulo: "Por categoría", items: porCategoria, icono: "🏷️" },
  ];

  let html = "";
  grupos.forEach((grupo) => {
    html += `<div class="budget-group">
                <div class="budget-group-title">${grupo.icono} ${grupo.titulo}</div>`;

    if (grupo.items.length === 0) {
      html += `<div class="empty-state empty-state--compact">
                    <p>Sin presupuestos en esta sección</p>
                </div>`;
    } else {
      grupo.items.forEach((p) => {
        const nombre = p.categoria_nombre || "Global";
        const icono = p.categoria_icono || (p.categoria_id ? "🏷️" : "🌐");
        const porcentaje = Number(p.porcentaje_usado || 0);
        const excedido = p.excedido === true || porcentaje > 100;
        const statusClass = excedido
          ? "danger"
          : porcentaje >= 80
            ? "warning"
            : "ok";
        const statusLabel = excedido
          ? "Excedido"
          : porcentaje >= 80
            ? "Alerta 80%"
            : "En rango";
        const width = Math.min(porcentaje, 100);
        const mesTxt = p.mes ? String(p.mes).substring(0, 7) : "";
        const catId = p.categoria_id ? String(p.categoria_id) : "";
        const itemClass =
          statusClass === "danger"
            ? "budget-item--danger"
            : statusClass === "warning"
              ? "budget-item--warning"
              : "";

        html += `
                <div class="budget-item ${itemClass}">
                    <div class="budget-header">
                        <div>
                            <div class="budget-title">${escapeHtml(icono)} ${escapeHtml(nombre)}</div>
                            <div class="budget-meta">Mes ${escapeHtml(mesTxt)}</div>
                        </div>
                        <div class="budget-meta">${porcentaje}% usado</div>
                    </div>
                    <div class="budget-track">
                        <div class="budget-fill ${statusClass}" style="width: ${width}%"></div>
                    </div>
                    <div class="budget-values">
                        <span>${formatMoney(p.gasto_actual || 0)}</span>
                        <span>${formatMoney(p.monto_limite || 0)}</span>
                    </div>
                    <div class="budget-actions">
                        <span class="budget-status ${statusClass}">${statusLabel}</span>
                        <div class="flex" style="gap: var(--space-xs)">
                            <button class="glass-btn glass-btn--sm" onclick="prefillPresupuesto('${mesTxt}', '${catId}', '${p.monto_limite}')">Usar</button>
                            <button class="glass-btn glass-btn--danger glass-btn--sm" onclick="eliminarPresupuesto(${p.id})">Eliminar</button>
                        </div>
                    </div>
                </div>
            `;
      });
    }

    html += "</div>";
  });

  container.innerHTML = html;
}

async function cargarComparativoPresupuesto() {
  const output = document.getElementById("presupuesto-comparativo-resumen");
  if (!output) return;

  const filtroMes = document.getElementById("presupuesto-filtro-mes");
  const mesInput = filtroMes?.value || obtenerMesActualInput();
  const mes = normalizarMesInput(mesInput);
  const select = document.getElementById("presupuesto-comparativo-categoria");
  const categoriaId = select?.value || "";

  let endpoint = `/presupuestos/comparativo?mes=${mes}`;
  if (categoriaId) endpoint += `&categoria_id=${categoriaId}`;

  try {
    const resp = await apiRequest(endpoint);
    renderComparativoPresupuesto(resp.data || {});
  } catch (err) {
    output.innerHTML = `<p class="text-muted">No se pudo cargar el comparativo.</p>`;
  }
}

function renderComparativoPresupuesto(data) {
  const output = document.getElementById("presupuesto-comparativo-resumen");
  if (!output) return;

  const actual = Number(data.gasto_actual || 0);
  const anterior = Number(data.gasto_anterior || 0);
  const variacion = Number(data.variacion_monto || 0);
  const variacionPct = Number(data.variacion_pct || 0);
  const direction =
    variacion > 0 ? "trend-up" : variacion < 0 ? "trend-down" : "trend-flat";
  const signo = variacion > 0 ? "+" : variacion < 0 ? "-" : "";

  output.innerHTML = `
        <div class="comparativo-grid">
            <div>
                <div class="comparativo-label">Mes actual</div>
                <div class="comparativo-value">${formatMoney(actual)}</div>
            </div>
            <div>
                <div class="comparativo-label">Mes anterior</div>
                <div class="comparativo-value">${formatMoney(anterior)}</div>
            </div>
            <div class="comparativo-variacion ${direction}">
                <span>${signo}${formatMoneyAbs(variacion)}</span>
                <small>${signo}${Math.abs(variacionPct)}%</small>
            </div>
        </div>
    `;
}

async function cargarPresupuestoHome() {
  const card = document.getElementById("home-presupuesto-card");
  if (!card) return;

  try {
    const now = new Date();
    const mes = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-01`;
    const resp = await apiRequest(`/presupuestos?mes=${mes}`);
    const budgets = resp.data || [];

    // Find global budget (no categoria_id)
    const global = budgets.find(p => !p.categoria_id);
    if (!global) {
      card.style.display = "none";
      return;
    }

    card.style.display = "block";
    const porcentaje = Number(global.porcentaje_usado || 0);
    const gastoActual = Number(global.gasto_actual || 0);
    const montoLimite = Number(global.monto_limite || 0);
    const excedido = global.excedido === true || porcentaje > 100;
    const statusClass = excedido ? "danger" : porcentaje >= 80 ? "warning" : "ok";

    const pctEl = document.getElementById("home-budget-pct");
    if (pctEl) {
      pctEl.textContent = `${Math.round(porcentaje)}%`;
      pctEl.className = `home-budget-pct ${statusClass}`;
    }

    const fillEl = document.getElementById("home-budget-fill");
    if (fillEl) {
      fillEl.className = `budget-fill ${statusClass}`;
      fillEl.style.width = `${Math.min(porcentaje, 100)}%`;
    }

    const gastadoEl = document.getElementById("home-budget-gastado");
    if (gastadoEl) gastadoEl.textContent = `Gastado: ${formatMoney(gastoActual)}`;

    const limiteEl = document.getElementById("home-budget-limite");
    if (limiteEl) limiteEl.textContent = `Límite: ${formatMoney(montoLimite)}`;
  } catch (_) {
    card.style.display = "none";
  }
}

// ============================================================
//  AUTOMATIZACIONES (RECURRENCIAS)
// ============================================================
async function cargarCategoriasRecurrencias(tipo) {
  const select = document.getElementById("rec-categoria");
  if (!select) return;

  try {
    const resp = await apiRequest(`/categorias?tipo=${tipo}`);
    select.innerHTML = '<option value="">Seleccionar categoría</option>';
    resp.data.forEach((cat) => {
      const option = document.createElement("option");
      option.value = cat.id;
      const icono = cat.icono || "🏷️";
      option.textContent = `${icono} ${cat.nombre}`;
      select.appendChild(option);
    });
  } catch (_) {
    select.innerHTML = '<option value="">Sin categorías</option>';
  }
}

function actualizarRecurrenciaForm() {
  const freq = document.getElementById("rec-frecuencia")?.value || "mensual";
  const diaWrap = document.getElementById("rec-dia-ejecucion-wrap");
  if (diaWrap) {
    diaWrap.style.display =
      freq === "mensual" || freq === "anual" ? "block" : "none";
  }
}

async function cargarRecurrencias() {
  const container = document.getElementById("recurrencias-lista");
  if (!container) return;

  try {
    const resp = await apiRequest("/recurrencias?incluir_inactivas=true");
    renderRecurrencias(resp.data || []);
  } catch (err) {
    container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚠️</div>
                <p>No se pudieron cargar las automatizaciones</p>
            </div>
        `;
  }
}

function renderRecurrencias(recurrencias) {
  const container = document.getElementById("recurrencias-lista");
  if (!container) return;

  if (!Array.isArray(recurrencias) || recurrencias.length === 0) {
    container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⏱️</div>
                <p>Sin automatizaciones configuradas</p>
                <button class="glass-btn glass-btn--sm empty-cta" onclick="document.getElementById('rec-descripcion')?.focus()">Crear automatización</button>
            </div>
        `;
    return;
  }

  container.innerHTML = recurrencias
    .map((r) => {
      const activo = r.activo === 1 || r.activo === true;
      const tipoLabel = r.tipo === "ingreso" ? "Ingreso" : "Gasto";
      const status = activo ? "Activa" : "Pausada";
      const statusClass = activo ? "status-ok" : "status-muted";
      const icono = r.categoria_icono || "🔁";

      return `
            <div class="recurrencia-item ${activo ? "" : "recurrencia-item--paused"}">
                <div class="recurrencia-info">
                    <div class="recurrencia-icon">${escapeHtml(icono)}</div>
                    <div>
                        <div class="recurrencia-title">${escapeHtml(r.descripcion || "Recurrencia")}</div>
                        <div class="recurrencia-meta">${tipoLabel} · ${escapeHtml(r.frecuencia)} · Próxima ${formatDate(r.proxima_fecha)}</div>
                        <div class="recurrencia-status ${statusClass}">${status}</div>
                    </div>
                </div>
                <div class="recurrencia-actions">
                    ${
                      activo
                        ? `<button class="glass-btn glass-btn--sm" onclick="pausarRecurrencia(${r.id})">Pausar</button>`
                        : `<button class="glass-btn glass-btn--sm" onclick="reactivarRecurrencia(${r.id})">Reactivar</button>`
                    }
                    <button class="glass-btn glass-btn--danger glass-btn--sm" onclick="eliminarRecurrencia(${r.id})">Eliminar</button>
                </div>
            </div>
        `;
    })
    .join("");
}

async function guardarRecurrencia(event) {
  event.preventDefault();
  const tipo = document.getElementById("rec-tipo")?.value || "gasto";
  const categoriaId = document.getElementById("rec-categoria")?.value || "";
  const monto = document.getElementById("rec-monto")?.value || "";
  const descripcion = document.getElementById("rec-descripcion")?.value || "";
  const frecuencia = document.getElementById("rec-frecuencia")?.value || "mensual";
  const proximaFecha = document.getElementById("rec-proxima-fecha")?.value || "";
  const diaEjecucion = document.getElementById("rec-dia-ejecucion")?.value || "";

  if (!categoriaId) {
    mostrarToast("Validación", "Selecciona una categoría.", "alerta");
    return;
  }
  if (!monto || Number(monto) <= 0) {
    mostrarToast("Validación", "Ingresa un monto válido.", "alerta");
    return;
  }
  if (!proximaFecha) {
    mostrarToast("Validación", "Selecciona una fecha válida.", "alerta");
    return;
  }

  const datos = {
    categoria_id: Number(categoriaId),
    tipo,
    monto: Number(monto),
    descripcion,
    frecuencia,
    proxima_fecha: proximaFecha,
  };
  if (diaEjecucion) datos.dia_ejecucion = Number(diaEjecucion);

  try {
    await apiRequest("/recurrencias", "POST", datos);
    mostrarToast("Automatizaciones", "Recurrencia creada.", "exito");
    document.getElementById("form-recurrencia")?.reset();
    const fechaHoy = new Date().toISOString().split("T")[0];
    const fechaInput = document.getElementById("rec-proxima-fecha");
    if (fechaInput) fechaInput.value = fechaHoy;
    actualizarRecurrenciaForm();
    cargarRecurrencias();
  } catch (err) {
    const msg = err?.mensaje || "No se pudo crear la recurrencia.";
    mostrarToast("Error", msg, "error");
  }
}

async function ejecutarRecurrencias() {
  try {
    const resp = await apiRequest("/recurrencias/ejecutar", "POST");
    const total = resp?.data?.movimientos_creados || 0;
    mostrarToast("Automatizaciones", `Ejecutadas: ${total}`, "info");
    cargarMovimientos(estadoApp.filtroActual);
    cargarBalance();
    cargarPresupuestos();
    cargarRecurrencias();
  } catch (err) {
    mostrarToast("Error", "No se pudieron ejecutar recurrencias.", "error");
  }
}

async function pausarRecurrencia(id) {
  try {
    await apiRequest(`/recurrencias/${id}`, "DELETE");
    mostrarToast("Automatizaciones", "Recurrencia pausada.", "info");
    cargarRecurrencias();
  } catch (err) {
    mostrarToast("Error", "No se pudo pausar la recurrencia.", "error");
  }
}

async function eliminarRecurrencia(id) {
  if (!confirm("¿Deseas eliminar esta recurrencia?")) return;
  return pausarRecurrencia(id);
}

async function reactivarRecurrencia(id) {
  const fecha = prompt("Nueva fecha (YYYY-MM-DD)");
  if (!fecha) return;
  try {
    await apiRequest(`/recurrencias/${id}/reactivar`, "POST", {
      proxima_fecha: fecha,
    });
    mostrarToast("Automatizaciones", "Recurrencia reactivada.", "exito");
    cargarRecurrencias();
  } catch (err) {
    mostrarToast("Error", "No se pudo reactivar la recurrencia.", "error");
  }
}

function prefillPresupuesto(mesTxt, categoriaId, monto) {
  const mes = mesTxt ? String(mesTxt).substring(0, 7) : "";
  const inputMes = document.getElementById("presupuesto-mes");
  const inputMonto = document.getElementById("presupuesto-monto");
  const selectCat = document.getElementById("presupuesto-categoria");

  if (inputMes && mes) inputMes.value = mes;
  if (inputMonto) inputMonto.value = monto != null ? String(monto) : "";
  if (selectCat) selectCat.value = categoriaId || "";
  inputMonto?.focus();
}

// [NORMA: ISO/IEC 12207 - Proceso de Operación del Software] Registro y control del presupuesto mensual
// [NORMA: ISO 9001:2000 - Enfoque basado en procesos] Proceso estandarizado para establecimiento de límites presupuestarios
async function guardarPresupuesto(event) {
  event.preventDefault();
  const mesInput = document.getElementById("presupuesto-mes")?.value || "";
  const monto = document.getElementById("presupuesto-monto")?.value || "";
  const categoriaRaw =
    document.getElementById("presupuesto-categoria")?.value || "";

  if (!mesInput) {
    mostrarToast("Validación", "Selecciona un mes válido.", "alerta");
    return;
  }
  if (!monto || Number(monto) <= 0) {
    mostrarToast("Validación", "El monto límite debe ser mayor a cero.", "alerta");
    return;
  }

  const datos = {
    monto_limite: monto,
    mes: normalizarMesInput(mesInput),
  };
  if (categoriaRaw) datos.categoria_id = Number(categoriaRaw);

  const btn = document.getElementById("btn-guardar-presupuesto");
  const txt = btn?.textContent;
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Guardando...";
  }

  try {
    await apiRequest("/presupuestos", "POST", datos);
    mostrarToast("Presupuestos", "Presupuesto guardado.", "exito");

    const filtroMes = document.getElementById("presupuesto-filtro-mes");
    if (filtroMes && !filtroMes.value) filtroMes.value = mesInput;

    cargarPresupuestos();
    limpiarFormularioPresupuesto();
  } catch (err) {
    const msg = err?.errores
      ? err.errores.join(" ")
      : err?.mensaje || "No se pudo guardar el presupuesto.";
    mostrarToast("Error", msg, "error");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = txt || "Guardar presupuesto";
    }
  }
}

async function eliminarPresupuesto(id) {
  if (!confirm("¿Deseas eliminar este presupuesto?")) return;
  try {
    await apiRequest(`/presupuestos/${id}`, "DELETE");
    mostrarToast("Presupuestos", "Presupuesto eliminado.", "info");
    cargarPresupuestos();
  } catch (err) {
    const msg = err?.mensaje || "No se pudo eliminar el presupuesto.";
    mostrarToast("Error", msg, "error");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  inicializarIconPicker();

  const formCategoria = document.getElementById("form-categoria");
  if (formCategoria) {
    formCategoria.addEventListener("submit", async (e) => {
      e.preventDefault();
      const nombre = document.getElementById("categoria-nombre")?.value || "";
      const tipo = document.getElementById("categoria-tipo")?.value || "gasto";
      const icono = document.getElementById("categoria-icono")?.value || "";
      const descripcion =
        document.getElementById("categoria-descripcion")?.value || "";

      const datos = { nombre, tipo, icono, descripcion };
      const editId = estadoApp.categoriaEditandoId;

      const nombreNorm = normalizarTextoBusqueda(nombre).trim();
      const duplicada = categoriasCache.some((c) => {
        const mismoNombre =
          normalizarTextoBusqueda(c.nombre || "").trim() === nombreNorm;
        const distintoId = String(c.id) !== String(editId || "");
        return mismoNombre && distintoId;
      });

      if (duplicada) {
        mostrarToast(
          "Validación",
          "Ya existe una categoría con ese nombre.",
          "alerta",
        );
        return;
      }

      try {
        if (editId) {
          await apiRequest(`/categorias/${editId}`, "PUT", datos);
          mostrarToast("Categorías", "Categoría actualizada.", "exito");
        } else {
          await apiRequest("/categorias", "POST", datos);
          mostrarToast("Categorías", "Categoría creada.", "exito");
        }

        cancelarEdicionCategoria();
        cargarCategoriasAdmin();
        cargarCategoriasEnFiltro();
        cargarCategoriasPresupuestos();
      } catch (err) {
        const msg = err?.errores
          ? err.errores.join(" ")
          : err?.mensaje || "No se pudo guardar la categoría.";
        mostrarToast("Error", msg, "error");
      }
    });
  }

  const formPresupuesto = document.getElementById("form-presupuesto");
  if (formPresupuesto) {
    formPresupuesto.addEventListener("submit", guardarPresupuesto);
  }

  const filtroMes = document.getElementById("presupuesto-filtro-mes");
  if (filtroMes) {
    filtroMes.addEventListener("change", () => {
      cargarPresupuestos();
      cargarComparativoPresupuesto();
    });
  }

  const compSelect = document.getElementById("presupuesto-comparativo-categoria");
  if (compSelect) {
    compSelect.addEventListener("change", () => cargarComparativoPresupuesto());
  }

  const formRec = document.getElementById("form-recurrencia");
  if (formRec) formRec.addEventListener("submit", guardarRecurrencia);

  const recTipo = document.getElementById("rec-tipo");
  if (recTipo) {
    recTipo.addEventListener("change", () => {
      cargarCategoriasRecurrencias(recTipo.value || "gasto");
    });
  }

  const recFrecuencia = document.getElementById("rec-frecuencia");
  if (recFrecuencia) {
    recFrecuencia.addEventListener("change", actualizarRecurrenciaForm);
  }

  const recFecha = document.getElementById("rec-proxima-fecha");
  if (recFecha && !recFecha.value) {
    recFecha.value = new Date().toISOString().split("T")[0];
  }

  const btnEjecutar = document.getElementById("btn-ejecutar-recurrencias");
  if (btnEjecutar) {
    btnEjecutar.addEventListener("click", ejecutarRecurrencias);
  }
});
