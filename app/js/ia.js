/**
 * ============================================================
 *  CAPA DE PRESENTACION - Inteligencia Artificial, OCR y Chat
 *  ControlCash v2.1 - Sistema Profesional de Control Financiero
 * ============================================================
 */

// ============================================================
//  PERFIL IA — Panel en dashboard
// ============================================================
async function cargarPerfilIA(forzar = false) {
  if (estadoApp.iaDisponible === false) {
    mostrarMensajeIADeshabilitada();
    return;
  }

  mostrarSkeletonPerfilIA();
  try {
    const endpoint = forzar ? "/ai/perfil?force=1" : "/ai/perfil";
    const resp = await apiRequest(endpoint);
    actualizarBadgeIA(true);
    renderizarPerfilIA(resp.data);
  } catch (err) {
    if (err?.status === 503) {
      estadoApp.iaDisponible = false;
      mostrarMensajeIADeshabilitada();
      return;
    }
    ocultarSkeletonPerfilIA();
    const panel = document.getElementById("perfil-ia-contenido");
    if (panel)
      panel.innerHTML = `
            <p class="text-muted" style="text-align:center; padding: var(--space-md);">
                ${err.mensaje && err.mensaje.includes("NVIDIA") ? "🔑 Configura NVIDIA_API_KEY para activar el perfil IA" : "⚠️ No se pudo generar el perfil"}
            </p>
        `;
    if (err?.mensaje && err.mensaje.includes("NVIDIA")) {
      actualizarBadgeIA(false);
    }
  }
}

function renderizarPerfilIA(data) {
  ocultarSkeletonPerfilIA();
  if (!data) return;

  const tipoLabel = data.tipo_label || "Tu Perfil Financiero";
  const score = Math.max(0, Math.min(100, parseInt(data.score) || 0));
  const tags = data.tags || [];
  const narrativa = data.narrativa || "";
  const habitos = data.habitos || data.habitos_positivos || [];
  const areas = data.areas_mejora || [];

  // Avatar basado en score
  let avatar = "🧑";
  if (score >= 80) avatar = "🏆";
  else if (score >= 60) avatar = "😊";
  else if (score >= 40) avatar = "😐";
  else avatar = "📉";

  // Color del score
  let scoreColor = "#FF5A5F";
  if (score >= 70) scoreColor = "#00C48C";
  else if (score >= 40) scoreColor = "#FFB800";

  const el = document.getElementById("perfil-avatar");
  if (el) el.textContent = avatar;

  const labelEl = document.getElementById("perfil-tipo-label");
  if (labelEl) labelEl.textContent = tipoLabel;

  const scoreNumEl = document.getElementById("perfil-score-num");
  if (scoreNumEl) {
    scoreNumEl.textContent = score;
    scoreNumEl.style.color = scoreColor;
  }

  // Animar barra de score
  setTimeout(() => {
    const fillEl = document.getElementById("perfil-score-fill");
    if (fillEl) {
      fillEl.style.background = `linear-gradient(90deg, #FF5A5F, #FFB800, ${scoreColor})`;
      fillEl.style.width = "0%";
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          fillEl.style.width = score + "%";
        });
      });
    }
  }, 100);

  // Tags
  const tagsEl = document.getElementById("perfil-tags");
  if (tagsEl) {
    tagsEl.innerHTML = tags
      .map((t) => `<span class="tag-pill">${escapeHtml(t)}</span>`)
      .join("");
  }

  // Narrativa
  const narrEl = document.getElementById("perfil-narrativa");
  if (narrEl) narrEl.textContent = narrativa;

  // Hábitos y áreas de mejora
  const detEl = document.getElementById("perfil-detalles");
  if (detEl) {
    let html = "";
    if (habitos.length > 0) {
      html += `<div class="perfil-detalles-seccion">
                <h5>✅ Hábitos positivos</h5>
                <ul>${habitos.map((h) => `<li>${escapeHtml(h)}</li>`).join("")}</ul>
            </div>`;
    }
    if (areas.length > 0) {
      html += `<div class="perfil-detalles-seccion">
                <h5>💡 Áreas de mejora</h5>
                <ul>${areas.map((a) => `<li>${escapeHtml(a)}</li>`).join("")}</ul>
            </div>`;
    }
    detEl.innerHTML = html;
  }
}

function refrescarPerfilIATrasCambio() {
  if (estadoApp.iaDisponible === false) return;
  cargarPerfilIA(true).catch(() => {});
}

// Botón actualizar perfil
document.addEventListener("DOMContentLoaded", () => {
  const btnActualizarPerfil = document.getElementById("btn-actualizar-perfil");
  if (btnActualizarPerfil) {
    btnActualizarPerfil.addEventListener("click", async () => {
      const iaActiva = await verificarDisponibilidadIA();
      if (!iaActiva) {
        mostrarMensajeIADeshabilitada();
        mostrarToast(
          "Perfil IA",
          "Configura NVIDIA_API_KEY para habilitar esta función.",
          "info",
        );
        return;
      }

      btnActualizarPerfil.disabled = true;
      btnActualizarPerfil.textContent = "⏳ Analizando...";
      // Forzar regeneración borrando caché del día temporalmente
      mostrarSkeletonPerfilIA();
      try {
        await cargarPerfilIA(true);
        mostrarToast("Perfil IA", "Perfil actualizado correctamente.", "exito");
      } catch (err) {
        ocultarSkeletonPerfilIA();
        mostrarToast("Error", "No se pudo actualizar el perfil.", "error");
      } finally {
        btnActualizarPerfil.disabled = false;
        btnActualizarPerfil.textContent = "↻ Actualizar";
      }
    });
  }
});

// ============================================================
//  INSIGHT DIARIO (tipo Duolingo)
// ============================================================
async function verificarInsightDiario() {
  if (estadoApp.iaDisponible === false) return;
  try {
    const resp = await apiRequest("/ai/daily-insight", "POST");
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
//  F4-OCR: ESCANEO DE RECIBOS
// ============================================================
let ocrDatosActuales = null;

function parseMontoOCRInput(rawValue) {
  let txt = String(rawValue || "").trim();
  if (!txt) return NaN;

  txt = txt.replace(/\s+/g, "").replace(/\$/g, "");

  if (txt.includes(",") && txt.includes(".")) {
    if (txt.lastIndexOf(",") > txt.lastIndexOf(".")) {
      txt = txt.replace(/\./g, "").replace(",", ".");
    } else {
      txt = txt.replace(/,/g, "");
    }
  } else {
    txt = txt.replace(",", ".");
  }

  return Number.parseFloat(txt);
}

function normalizarTextoBusqueda(texto) {
  return String(texto || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function sugerirCategoriaOCR(categorias, descripcion) {
  if (!Array.isArray(categorias) || categorias.length === 0) return null;
  const desc = normalizarTextoBusqueda(descripcion);
  if (!desc) return categorias[0]?.id || null;

  const pistas = [
    { re: /nequi|transfer|envio|pago movi|pse|banco/, key: "transfer" },
    {
      re: /mercado|super|tienda|comida|restaur|cafe|almuerzo|desayuno/,
      key: "alimento",
    },
    { re: /taxi|uber|bus|transporte|gasolina|peaje/, key: "transporte" },
    { re: /salario|nomina|sueldo|pago recibido|abono/, key: "ingreso" },
    { re: /internet|celular|luz|agua|arriendo|servicio/, key: "servicio" },
  ];

  const pista = pistas.find((p) => p.re.test(desc));
  if (!pista) return categorias[0]?.id || null;

  const match = categorias.find((c) => {
    const nombre = normalizarTextoBusqueda(c?.nombre || "");
    return pointer = nombre.includes(pista.key);
  });

  return match?.id || categorias[0]?.id || null;
}

async function cargarCategoriasOCR(tipo, descripcionSugerida = "") {
  const select = document.getElementById("ocr-categoria");
  if (!select) return;

  try {
    const resp = await apiRequest(`/categorias?tipo=${tipo}`);
    const categorias = Array.isArray(resp?.data) ? resp.data : [];

    select.innerHTML = '<option value="">Seleccionar categoría</option>';
    categorias.forEach((cat) => {
      const option = document.createElement("option");
      option.value = cat.id;
      const icono = cat.icono || "🏷️";
      option.textContent = `${icono} ${cat.nombre}`;
      select.appendChild(option);
    });

    const sugerida = sugerirCategoriaOCR(categorias, descripcionSugerida);
    if (sugerida != null) {
      select.value = String(sugerida);
    }
  } catch (_) {
    select.innerHTML = '<option value="">Sin categorías disponibles</option>';
  }
}

async function poblarFormularioOCR(tipoSugerido) {
  const montoInput = document.getElementById("ocr-monto");
  const fechaInput = document.getElementById("ocr-fecha");
  const descInput = document.getElementById("ocr-descripcion");
  const tipoSelect = document.getElementById("ocr-tipo-mov");

  if (tipoSelect) tipoSelect.value = tipoSugerido;
  if (montoInput)
    montoInput.value =
      ocrDatosActuales?.total != null ? String(ocrDatosActuales.total) : "";
  if (fechaInput)
    fechaInput.value =
      ocrDatosActuales?.fecha || new Date().toISOString().split("T")[0];
  if (descInput) descInput.value = ocrDatosActuales?.descripcion || "";

  await cargarCategoriasOCR(tipoSugerido, ocrDatosActuales?.descripcion || "");
}

function abrirModalOCR() {
  ocrDatosActuales = null;
  estadoApp.ocrBase64 = null;
  estadoApp.ocrEnProceso = false;
  document.getElementById("ocr-preview").style.display = "none";
  document.getElementById("ocr-placeholder").style.display = "block";
  document.getElementById("ocr-resultado").style.display = "none";
  document.getElementById("ocr-editable").style.display = "none";
  document.getElementById("ocr-loading").style.display = "none";
  document.getElementById("btn-escanear").disabled = true;
  document.getElementById("btn-usar-ocr").style.display = "none";
  document.getElementById("ocr-file-input").value = "";
  const tipoSelect = document.getElementById("ocr-tipo-mov");
  if (tipoSelect) tipoSelect.value = "gasto";
  const catSelect = document.getElementById("ocr-categoria");
  if (catSelect)
    catSelect.innerHTML = '<option value="">Seleccionar categoría</option>';
  const montoInput = document.getElementById("ocr-monto");
  if (montoInput) montoInput.value = "";
  const fechaInput = document.getElementById("ocr-fecha");
  if (fechaInput) fechaInput.value = new Date().toISOString().split("T")[0];
  const descInput = document.getElementById("ocr-descripcion");
  if (descInput) descInput.value = "";
  document.getElementById("modal-ocr").classList.add("active");
}

document.getElementById("ocr-drop-zone").addEventListener("click", () => {
  const input = document.getElementById("ocr-file-input");
  input.value = "";
  input.click();
});

document.getElementById("ocr-file-input").addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (!file) return;
  if (file.type && !file.type.startsWith("image/")) {
    mostrarToast("Error", "Selecciona una imagen válida.", "error");
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    mostrarToast("Error", "Imagen demasiado grande (máx 10 MB).", "error");
    return;
  }
  const reader = new FileReader();
  reader.onload = (ev) => {
    const img = document.getElementById("ocr-preview");
    img.src = ev.target.result;
    img.style.display = "block";
    document.getElementById("ocr-placeholder").style.display = "none";
    document.getElementById("btn-escanear").disabled = false;
    estadoApp.ocrBase64 = ev.target.result.split(",")[1];
    escanearRecibo();
  };
  reader.readAsDataURL(file);
});

const dropZone = document.getElementById("ocr-drop-zone");
dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("dragover");
});
dropZone.addEventListener("dragleave", () =>
  dropZone.classList.remove("dragover"),
);
dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("dragover");
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith("image/")) {
    const input = document.getElementById("ocr-file-input");
    const dt = new DataTransfer();
    dt.items.add(file);
    input.files = dt.files;
    input.dispatchEvent(new Event("change"));
  }
});

async function escanearRecibo() {
  if (!estadoApp.ocrBase64 || estadoApp.ocrEnProceso) return;
  estadoApp.ocrEnProceso = true;
  document.getElementById("ocr-loading").style.display = "block";
  document.getElementById("btn-escanear").disabled = true;

  try {
    const resp = await apiRequest("/ocr/recibo", "POST", {
      imagen: estadoApp.ocrBase64,
    });
    ocrDatosActuales = resp.data;

    const tipoSugeridoRaw = String(
      ocrDatosActuales.tipo_sugerido || "",
    ).toLowerCase();
    const tipoSugerido = tipoSugeridoRaw === "ingreso" ? "ingreso" : "gasto";
    const tipoConf = Number(ocrDatosActuales.tipo_confianza || 0);
    const tipoLabel =
      tipoSugerido === "ingreso" ? "Entrada / Ingreso" : "Salida / Gasto";

    const datosDiv = document.getElementById("ocr-datos");
    datosDiv.innerHTML = `
            <p><strong>Total:</strong> ${ocrDatosActuales.total != null ? formatMoney(ocrDatosActuales.total) : "No detectado"}</p>
            <p><strong>Fecha:</strong> ${escapeHtml(ocrDatosActuales.fecha || "No detectada")}</p>
            <p><strong>Descripción:</strong> ${escapeHtml(ocrDatosActuales.descripcion || "N/A")}</p>
            <p><strong>Tipo sugerido:</strong> ${escapeHtml(tipoLabel)} (${Math.round(tipoConf * 100)}%)</p>
            ${
              ocrDatosActuales.items && ocrDatosActuales.items.length > 0
                ? "<p><strong>Items:</strong></p><ul>" +
                  ocrDatosActuales.items
                    .map(
                      (i) =>
                        `<li>${escapeHtml(i.nombre || "?")} — ${i.precio != null ? formatMoney(i.precio) : "?"}</li>`,
                    )
                    .join("") +
                  "</ul>"
                : ""
            }
        `;

    const tipoSelect = document.getElementById("ocr-tipo-mov");
    if (tipoSelect) tipoSelect.value = tipoSugerido;

    await poblarFormularioOCR(tipoSugerido);

    document.getElementById("ocr-resultado").style.display = "block";
    document.getElementById("ocr-editable").style.display = "block";
    document.getElementById("btn-usar-ocr").style.display = "block";
    mostrarToast("OCR", "Recibo analizado exitosamente.", "exito");
  } catch (err) {
    mostrarToast(
      "Error OCR",
      err.mensaje || "No se pudo analizar el recibo.",
      "error",
    );
  } finally {
    document.getElementById("ocr-loading").style.display = "none";
    document.getElementById("btn-escanear").disabled = false;
    estadoApp.ocrEnProceso = false;
  }
}

async function confirmarOCRYGuardar() {
  if (!ocrDatosActuales) return;

  const tipoSelect = document.getElementById("ocr-tipo-mov");
  const tipo =
    tipoSelect && tipoSelect.value === "ingreso" ? "ingreso" : "gasto";

  const categoriaId = document.getElementById("ocr-categoria")?.value || "";
  const montoRaw = document.getElementById("ocr-monto")?.value || "";
  const monto = parseMontoOCRInput(montoRaw);
  const descripcion = document.getElementById("ocr-descripcion")?.value || "";
  const fecha = document.getElementById("ocr-fecha")?.value || "";

  if (!categoriaId) {
    mostrarToast(
      "Validación",
      "Selecciona una categoría para guardar.",
      "alerta",
    );
    return;
  }
  if (!Number.isFinite(monto) || monto <= 0) {
    mostrarToast("Validación", "El monto debe ser mayor a cero.", "alerta");
    return;
  }
  if (!fecha) {
    mostrarToast("Validación", "Selecciona una fecha válida.", "alerta");
    return;
  }

  const btn = document.getElementById("btn-usar-ocr");
  const textoOriginal = btn ? btn.textContent : "";
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Guardando...";
  }

  try {
    await apiRequest("/movimientos", "POST", {
      tipo,
      categoria_id: categoriaId,
      monto,
      descripcion,
      fecha,
    });

    cerrarModal("modal-ocr");
    mostrarToast(
      "OCR",
      "Movimiento guardado correctamente en la base de datos.",
      "exito",
    );

    cargarBalance();
    cargarMovimientos(estadoApp.filtroActual);
    cargarResumen();
    cargarPresupuestos();
    cargarNotificaciones();
    refrescarPerfilIATrasCambio();
  } catch (err) {
    const msg = err?.errores
      ? err.errores.join(" ")
      : err?.mensaje || "No se pudo guardar el movimiento OCR.";
    mostrarToast("Error", msg, "error");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = textoOriginal || "Confirmar y guardar en DB";
    }
  }
}

function usarDatosOCR() {
  confirmarOCRYGuardar();
}

document.getElementById("ocr-tipo-mov").addEventListener("change", () => {
  const tipo =
    document.getElementById("ocr-tipo-mov").value === "ingreso"
      ? "ingreso"
      : "gasto";
  const descripcion =
    document.getElementById("ocr-descripcion")?.value ||
    ocrDatosActuales?.descripcion ||
    "";
  cargarCategoriasOCR(tipo, descripcion);
});

// ============================================================
//  F5-CHAT: ASISTENTE FINANCIERO LLM
// ============================================================
function abrirModalChat() {
  document.getElementById("modal-chat").classList.add("active");
  document.getElementById("chat-input").focus();
}

async function enviarChat(e) {
  e.preventDefault();
  const input = document.getElementById("chat-input");
  const msg = input.value.trim();
  if (!msg) return;

  const container = document.getElementById("chat-messages");
  const userEl = crearMensajeChat("user", msg, false);
  container.appendChild(userEl);
  input.value = "";
  container.scrollTop = container.scrollHeight;

  const loadingId = "chat-loading-" + Date.now();
  const loadingWrapper = document.createElement("div");
  loadingWrapper.className = "chat-msg chat-msg--bot";
  loadingWrapper.id = loadingId;

  const loadingAvatar = document.createElement("span");
  loadingAvatar.className = "chat-avatar";
  loadingAvatar.textContent = "🤖";

  const loadingBubble = document.createElement("div");
  loadingBubble.className = "chat-bubble chat-bubble--loading";
  loadingBubble.innerHTML =
    '<div class="loading-spinner" style="width:20px;height:20px;border-width:2px;"></div>';

  loadingWrapper.appendChild(loadingAvatar);
  loadingWrapper.appendChild(loadingBubble);
  container.appendChild(loadingWrapper);
  container.scrollTop = container.scrollHeight;

  try {
    const resp = await apiRequest("/chat", "POST", { mensaje: msg });
    const loadEl = document.getElementById(loadingId);
    if (loadEl) loadEl.remove();

    const botEl = crearMensajeChat("bot", "", true);
    container.appendChild(botEl);

    const bubbleEl = botEl.querySelector(".chat-bubble");
    const respuesta = String(
      resp?.data?.respuesta || "No pude generar una respuesta.",
    );
    await animarRespuestaStreaming(bubbleEl, respuesta, container);
  } catch (err) {
    const loadEl = document.getElementById(loadingId);
    if (loadEl) loadEl.remove();

    const errorEl = crearMensajeChat(
      "bot",
      "Lo siento, hubo un error. Intenta de nuevo.",
      false,
    );
    container.appendChild(errorEl);
  }
  container.scrollTop = container.scrollHeight;
}
