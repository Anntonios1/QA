/**
 * ============================================================
 *  CAPA DE PRESENTACION - Gestión de Movimientos y Balance
 *  ControlCash v2.1 - Sistema Profesional de Control Financiero
 * ============================================================
 */

// ============================================================
//  F4: SOLICITAR BALANCE
// ============================================================
// [NORMA: ISO 9126 - Funcionalidad/Exactitud] Cálculo preciso del balance según movimientos registrados en la API
// [NORMA: ISO/IEC 25000 - Característica de Corrección Funcional] Resultado correcto para el caso de uso principal: visualización de saldos
async function cargarBalance() {
  try {
    const resp = await apiRequest("/balance");
    const data = resp.data;
    const balanceEl = document.getElementById("balance-total");
    balanceEl.textContent = formatMoney(data.balance);
    balanceEl.className =
      "balance-amount " + (data.balance >= 0 ? "positive" : "negative");
    document.getElementById("balance-ingresos").textContent = formatMoney(
      data.total_ingresos,
    );
    document.getElementById("balance-gastos").textContent = formatMoney(
      data.total_gastos,
    );
    document.getElementById("balance-movimientos").textContent =
      data.total_movimientos;
    animateCounter(
      document.getElementById("balance-total"),
      0,
      parseFloat(data.balance || 0),
      900,
    );
    document.querySelector(".balance-card")?.classList.add("pulse");
    setTimeout(
      () => document.querySelector(".balance-card")?.classList.remove("pulse"),
      1000,
    );
    cargarPresupuestoHome();
  } catch (err) {
    mostrarToast("Error", "No se pudo cargar el balance.", "error");
  }
}

// ============================================================
//  F3: GESTIONAR MOVIMIENTO - Listar con filtros avanzados
// ============================================================
function actualizarBotonVistaMovimientos() {
  const btn = document.getElementById("btn-toggle-movimientos");
  if (!btn) return;
  btn.textContent = estadoApp.movimientosExpandido ? "Ver menos" : "Ver todos →";
}

function setMovimientosExpandido(expandido, recargar = true) {
  estadoApp.movimientosExpandido = !!expandido;
  actualizarBotonVistaMovimientos();
  if (recargar) {
    cargarMovimientos(
      estadoApp.filtroActual !== "todos" ? estadoApp.filtroActual : null,
    );
  }
}

function toggleVistaMovimientos() {
  setMovimientosExpandido(!estadoApp.movimientosExpandido);
}

async function cargarMovimientos(tipo = null, page = null) {
  const container = document.getElementById("lista-movimientos");
  mostrarSkeletonMovimientos();

  if (page !== null) {
    estadoApp.movimientosPagina = page;
  }

  try {
    const filtroDesde = document.getElementById("filtro-desde")?.value || "";
    const filtroHasta = document.getElementById("filtro-hasta")?.value || "";
    const filtroCat = document.getElementById("filtro-categoria")?.value || "";
    const filtroMontoMin =
      document.getElementById("filtro-monto-min")?.value || "";
    const filtroMontoMax =
      document.getElementById("filtro-monto-max")?.value || "";

    const tipoRaw = tipo || estadoApp.filtroActual;
    const filtroTipo = (tipoRaw && tipoRaw !== "todos") ? tipoRaw : null;

    let endpoint = `/movimientos?page=${estadoApp.movimientosPagina}&page_size=${estadoApp.movimientosPaginaSize}`;
    if (filtroTipo && filtroTipo !== "todos") endpoint += `&tipo=${filtroTipo}`;
    if (filtroDesde) endpoint += `&fecha_desde=${filtroDesde}`;
    if (filtroHasta) endpoint += `&fecha_hasta=${filtroHasta}`;
    if (filtroCat) endpoint += `&categoria_id=${filtroCat}`;
    if (filtroMontoMin) endpoint += `&monto_min=${filtroMontoMin}`;
    if (filtroMontoMax) endpoint += `&monto_max=${filtroMontoMax}`;

    const resp = await apiRequest(endpoint);
    const data = resp.data;
    const movimientos = Array.isArray(data) ? data : data.items || [];
    const pagination = Array.isArray(data) ? null : data.pagination;

    if (pagination) {
      estadoApp.movimientosTotal = pagination.total || 0;
      estadoApp.movimientosTotalPaginas = pagination.total_pages || 1;
      estadoApp.movimientosPagina = pagination.page || 1;
    }

    if (estadoApp.movimientosExpandido) {
      renderPaginacionMovimientos(pagination);
    } else {
      renderPaginacionMovimientos(null);
    }

    if (movimientos.length === 0) {
      container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">💸</div>
                    <p>No hay movimientos que coincidan</p>
                    <button class="glass-btn glass-btn--sm empty-cta" onclick="abrirModalMovimiento('gasto')">Registrar gasto</button>
                </div>
            `;
      return;
    }

    const movimientosRender = estadoApp.movimientosExpandido
      ? movimientos
      : movimientos.slice(0, 3);

    let html = "";
    movimientosRender.forEach((mov) => {
      const esIngreso = mov.tipo === "ingreso";
      const tipoClass = esIngreso ? "income" : "expense";
      const signo = esIngreso ? "+" : "-";
      const dataMov = escapeHtml(
        JSON.stringify({
          id: mov.id,
          tipo: mov.tipo,
          monto: mov.monto,
          categoria_id: mov.categoria_id,
          descripcion: mov.descripcion,
          fecha: mov.fecha ? mov.fecha.substring(0, 10) : "",
          categoria_nombre: mov.categoria_nombre,
        }),
      );

      html += `
                <div class="transaction-item fade-in" data-id="${mov.id}">
                    <div class="transaction-icon ${tipoClass}">
                        ${escapeHtml(mov.categoria_icono || "💰")}
                    </div>
                    <div class="transaction-details">
                        <div class="transaction-category">${escapeHtml(mov.categoria_nombre)}</div>
                        <div class="transaction-description">${escapeHtml(mov.descripcion || "Sin descripción")}</div>
                    </div>
                    <div class="transaction-meta">
                        <div class="transaction-amount ${tipoClass}">${signo}${formatMoneyAbs(mov.monto)}</div>
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
    if (window._initTilt) window._initTilt();

    const btnToggle = document.getElementById("btn-toggle-movimientos");
    if (btnToggle) {
      const totalBackend = pagination?.total || movimientos.length;
      btnToggle.style.display =
        totalBackend > 3 || estadoApp.movimientosExpandido
          ? "inline-flex"
          : "none";
    }
  } catch (err) {
    mostrarToast("Error", "No se pudieron cargar los movimientos.", "error");
    container.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><p>Error al cargar</p></div>`;
  }
}

function renderPaginacionMovimientos(pagination) {
  const wrapper = document.getElementById("movimientos-paginacion");
  if (!wrapper) return;

  if (!pagination || !estadoApp.movimientosExpandido) {
    wrapper.style.display = "none";
    return;
  }

  wrapper.style.display = "flex";
  const info = document.getElementById("mov-page-info");
  if (info) {
    info.textContent = `Página ${pagination.page} de ${pagination.total_pages}`;
  }
  const btnPrev = document.getElementById("mov-page-prev");
  const btnNext = document.getElementById("mov-page-next");
  if (btnPrev) btnPrev.disabled = pagination.page <= 1;
  if (btnNext) btnNext.disabled = pagination.page >= pagination.total_pages;
}

function cambiarPaginaMovimientos(delta) {
  const nueva = Math.max(1, estadoApp.movimientosPagina + delta);
  cargarMovimientos(estadoApp.filtroActual, nueva);
}

function filtrarMovimientos(tipo, tabElement) {
  estadoApp.filtroActual = tipo;
  estadoApp.movimientosPagina = 1;
  document
    .querySelectorAll(".glass-tab")
    .forEach((t) => t.classList.remove("active"));
  if (tabElement) tabElement.classList.add("active");
  cargarMovimientos(tipo);
}

// ============================================================
//  FILTROS AVANZADOS
// ============================================================
async function aplicarFiltrosAvanzados() {
  estadoApp.movimientosPagina = 1;
  await cargarMovimientos(
    estadoApp.filtroActual !== "todos" ? estadoApp.filtroActual : null,
  );
}

function limpiarFiltrosAvanzados() {
  const campos = [
    "filtro-desde",
    "filtro-hasta",
    "filtro-categoria",
    "filtro-monto-min",
    "filtro-monto-max",
  ];
  campos.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.value = "";
  });
  estadoApp.movimientosPagina = 1;
  cargarMovimientos();
}

async function cargarCategoriasEnFiltro() {
  try {
    const resp = await apiRequest("/categorias");
    const select = document.getElementById("filtro-categoria");
    if (!select) return;
    select.innerHTML = '<option value="">Todas las categorías</option>';
    const cats = Array.isArray(resp?.data) ? resp.data : [];
    cats.forEach((cat) => {
      const option = document.createElement("option");
      option.value = cat.id;
      const icono = cat.icono || "🏷️";
      option.textContent = `${icono} ${cat.nombre}`;
      select.appendChild(option);
    });
  } catch (_) {}
}

// ============================================================
//  EXPORTAR CSV
// ============================================================
async function exportarCSV() {
  try {
    const filtroDesde = document.getElementById("filtro-desde")?.value || "";
    const filtroHasta = document.getElementById("filtro-hasta")?.value || "";
    const filtroTipo =
      estadoApp.filtroActual !== "todos" ? estadoApp.filtroActual : "";

    let endpoint = "/movimientos/export/csv?";
    if (filtroTipo) endpoint += `tipo=${filtroTipo}&`;
    if (filtroDesde) endpoint += `fecha_desde=${filtroDesde}&`;
    if (filtroHasta) endpoint += `fecha_hasta=${filtroHasta}&`;

    const response = await apiRequest(endpoint);
    if (!response || typeof response.blob !== "function") {
      throw new Error("Respuesta inesperada");
    }
    if (!response.ok) throw new Error("Error al exportar");

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const fecha = new Date().toISOString().split("T")[0].replace(/-/g, "");
    a.download = `controlcash_${fecha}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);

    mostrarToast("Exportado", "Movimientos exportados en CSV.", "exito");
  } catch (err) {
    mostrarToast("Error", "No se pudo exportar el CSV.", "error");
  }
}

// ============================================================
//  F3: GESTIONAR MOVIMIENTO - Crear
// ============================================================
function abrirSheetTransacciones() {
  document.getElementById("transacciones-sheet-overlay")?.classList.add("active");
  const fab = document.getElementById("fab-acciones");
  const icon = document.getElementById("fab-acciones-icon");
  fab?.classList.add("active");
  if (icon) icon.textContent = "✕";
}

function cerrarSheetTransacciones() {
  document
    .getElementById("transacciones-sheet-overlay")
    ?.classList.remove("active");
  const fab = document.getElementById("fab-acciones");
  const icon = document.getElementById("fab-acciones-icon");
  fab?.classList.remove("active");
  if (icon) icon.textContent = "＋";
}

function toggleFabAcciones() {
  const overlay = document.getElementById("transacciones-sheet-overlay");
  if (!overlay) return;
  if (overlay.classList.contains("active")) {
    cerrarSheetTransacciones();
    return;
  }
  abrirSheetTransacciones();
}

function abrirTransaccionDesdeSheet(tipo) {
  cerrarSheetTransacciones();
  abrirModalMovimiento(tipo);
}

function abrirOCRDesdeSheet() {
  cerrarSheetTransacciones();
  abrirModalOCR();
}

function abrirChatDesdeSheet() {
  cerrarSheetTransacciones();
  abrirModalChat();
}

function abrirCategoriasDesdeSheet() {
  cerrarSheetTransacciones();
  mostrarSeccionDashboard("categorias");
  cargarCategoriasAdmin();
  window.scrollTo({ top: 0, behavior: "smooth" });
  setTimeout(() => {
    document.getElementById("categoria-nombre")?.focus();
  }, 120);
}

async function abrirModalMovimiento(tipo) {
  const formMovimiento = document.getElementById("form-movimiento");
  if (formMovimiento) formMovimiento.reset();

  document.getElementById("mov-tipo").value = tipo;
  const titulo = tipo === "ingreso" ? "📥 Nuevo Ingreso" : "📤 Nuevo Gasto";
  document.getElementById("modal-movimiento-titulo").textContent = titulo;
  document.getElementById("mov-fecha").value = new Date()
    .toISOString()
    .split("T")[0];
  document.getElementById("modal-error").classList.remove("visible");

  try {
    const resp = await apiRequest(`/categorias?tipo=${tipo}`);
    let categorias = Array.isArray(resp?.data) ? resp.data : [];

    if (categorias.length === 0) {
      const fallbackResp = await apiRequest("/categorias");
      categorias = Array.isArray(fallbackResp?.data) ? fallbackResp.data : [];
    }

    const select = document.getElementById("mov-categoria");
    select.innerHTML = '<option value="">Seleccionar categoría</option>';
    categorias.forEach((cat) => {
      const option = document.createElement("option");
      option.value = cat.id;
      const icono = cat.icono || "🏷️";
      option.textContent = `${icono} ${cat.nombre}`;
      select.appendChild(option);
    });

    if (categorias.length === 0) {
      select.innerHTML = '<option value="">Sin categorías disponibles</option>';
    }
  } catch (err) {
    mostrarToast("Error", "No se pudieron cargar las categorías.", "error");
  }

  document.getElementById("mov-tipo").value = tipo;
  document.getElementById("modal-movimiento").classList.add("active");
}

function cerrarModal(modalId) {
  document.getElementById(modalId).classList.remove("active");
}

document
  .getElementById("modal-movimiento")
  .addEventListener("click", function (e) {
    if (e.target === this) cerrarModal("modal-movimiento");
  });

document
  .getElementById("form-movimiento")
  .addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorDiv = document.getElementById("modal-error");
    errorDiv.classList.remove("visible");

    const datos = {
      tipo: document.getElementById("mov-tipo").value,
      monto: document.getElementById("mov-monto").value,
      categoria_id: document.getElementById("mov-categoria").value,
      descripcion: document.getElementById("mov-descripcion").value,
      fecha: document.getElementById("mov-fecha").value,
    };

    try {
      const resp = await apiRequest("/movimientos", "POST", datos);
      mostrarToast("Registrado", resp.mensaje, "exito");
      cerrarModal("modal-movimiento");
      cargarBalance();
      cargarMovimientos(estadoApp.filtroActual);
      cargarResumen();
      cargarPresupuestos();
      cargarNotificaciones();
      refrescarPerfilIATrasCambio();
    } catch (err) {
      const msg = err.errores
        ? err.errores.join(" ")
        : err.mensaje || "Error al guardar.";
      errorDiv.textContent = msg;
      errorDiv.classList.add("visible");
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
    const select = document.getElementById("edit-mov-categoria");
    if (select) {
      select.innerHTML = '<option value="">Seleccionar categoría</option>';
      resp.data.forEach((cat) => {
        const option = document.createElement("option");
        option.value = cat.id;
        const icono = cat.icono || "🏷️";
        option.textContent = `${icono} ${cat.nombre}`;
        if (cat.id == datos.categoria_id) option.selected = true;
        select.appendChild(option);
      });
    }
  } catch (_) {}

  // Rellenar campos
  const setVal = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.value = val || "";
  };
  setVal("edit-mov-tipo", datos.tipo);
  setVal("edit-mov-monto", datos.monto);
  setVal("edit-mov-descripcion", datos.descripcion);
  setVal("edit-mov-fecha", datos.fecha ? datos.fecha.substring(0, 10) : "");

  // Título del modal
  const titulo =
    datos.tipo === "ingreso" ? "✏️ Editar Ingreso" : "✏️ Editar Gasto";
  const tituloEl = document.getElementById("modal-editar-titulo");
  if (tituloEl) tituloEl.textContent = titulo;

  const errDiv = document.getElementById("edit-modal-error");
  if (errDiv) errDiv.classList.remove("visible");

  document.getElementById("modal-editar-movimiento").classList.add("active");
}

document.addEventListener("DOMContentLoaded", () => {
  const formEditar = document.getElementById("form-editar-movimiento");
  if (formEditar) {
    formEditar.addEventListener("submit", async (e) => {
      e.preventDefault();
      const errDiv = document.getElementById("edit-modal-error");
      if (errDiv) errDiv.classList.remove("visible");

      const datos = {
        tipo: document.getElementById("edit-mov-tipo").value,
        monto: document.getElementById("edit-mov-monto").value,
        categoria_id: document.getElementById("edit-mov-categoria").value,
        descripcion: document.getElementById("edit-mov-descripcion").value,
        fecha: document.getElementById("edit-mov-fecha").value,
      };

      try {
        const resp = await apiRequest(
          `/movimientos/${estadoApp.movimientoEditandoId}`,
          "PUT",
          datos,
        );
        mostrarToast(
          "Actualizado",
          "Movimiento actualizado correctamente.",
          "exito",
        );
        cerrarModal("modal-editar-movimiento");
        cargarBalance();
        cargarMovimientos(estadoApp.filtroActual);
        cargarResumen();
        cargarPresupuestos();
        refrescarPerfilIATrasCambio();
      } catch (err) {
        const msg = err.errores
          ? err.errores.join(" ")
          : err.mensaje || "Error al actualizar.";
        if (errDiv) {
          errDiv.textContent = msg;
          errDiv.classList.add("visible");
        }
      }
    });
  }

  const editOverlay = document.getElementById("modal-editar-movimiento");
  if (editOverlay) {
    editOverlay.addEventListener("click", function (e) {
      if (e.target === this) cerrarModal("modal-editar-movimiento");
    });
  }
});

// ============================================================
//  F3: GESTIONAR MOVIMIENTO - Confirmación de borrado
// ============================================================
function confirmarBorrado(id) {
  estadoApp.movimientosBorrandoId = id;
  const modal = document.getElementById("modal-confirmar-borrado");
  if (modal) modal.classList.add("active");
}

document.addEventListener("DOMContentLoaded", () => {
  const btnConfirmarBorrado = document.getElementById("btn-confirmar-borrado");
  if (btnConfirmarBorrado) {
    btnConfirmarBorrado.addEventListener("click", async () => {
      const id = estadoApp.movimientosBorrandoId;
      if (!id) return;
      cerrarModal("modal-confirmar-borrado");
      estadoApp.movimientosBorrandoId = null;

      try {
        await apiRequest(`/movimientos/${id}`, "DELETE");
        mostrarToast(
          "Eliminado",
          "Movimiento eliminado correctamente.",
          "info",
        );
        cargarBalance();
        cargarMovimientos(estadoApp.filtroActual);
        cargarResumen();
        cargarPresupuestos();
        refrescarPerfilIATrasCambio();
      } catch (err) {
        mostrarToast("Error", "No se pudo eliminar el movimiento.", "error");
      }
    });
  }

  const cancelarBorrado = document.getElementById("btn-cancelar-borrado");
  if (cancelarBorrado) {
    cancelarBorrado.addEventListener("click", () => {
      cerrarModal("modal-confirmar-borrado");
      estadoApp.movimientosBorrandoId = null;
    });
  }

  const borradoOverlay = document.getElementById("modal-confirmar-borrado");
  if (borradoOverlay) {
    borradoOverlay.addEventListener("click", function (e) {
      if (e.target === this) {
        cerrarModal("modal-confirmar-borrado");
        estadoApp.movimientosBorrandoId = null;
      }
    });
  }

  const btnPrev = document.getElementById("mov-page-prev");
  if (btnPrev) {
    btnPrev.addEventListener("click", () => cambiarPaginaMovimientos(-1));
  }

  const btnNext = document.getElementById("mov-page-next");
  if (btnNext) {
    btnNext.addEventListener("click", () => cambiarPaginaMovimientos(1));
  }
});
