/**
 * ============================================================
 *  CAPA DE PRESENTACION - Logica de Aplicacion (Estado y Utilidades)
 *  ControlCash v2.1 - Sistema Profesional de Control Financiero
 * ============================================================
 */

// ============================================================
//  CONFIGURACIÓN
// ============================================================
const API_BASE = (() => {
  const protocol = window.location.protocol;
  const hostname = window.location.hostname;
  if ((protocol === "http:" || protocol === "https:") && hostname) {
    return `${protocol}//${hostname}:5000/api`;
  }
  return "http://127.0.0.1:5000/api";
})();
const ACCESS_TOKEN_KEY = "cc_access_token";
const REFRESH_TOKEN_KEY = "cc_refresh_token";

// ============================================================
//  ESTADO DE LA APLICACION
// ============================================================
let estadoApp = {
  usuario: (() => {
    try {
      const raw = localStorage.getItem("cc_user_info");
      return raw ? JSON.parse(raw) : null;
    } catch (_) {
      return null;
    }
  })(),
  filtroActual: "todos",
  notifPanelAbierto: false,
  sesionTimeoutId: null,
  biometricoDisponible: false,
  modoOscuro: localStorage.getItem("cc_modo") !== "light",
  movimientoEditandoId: null,
  movimientosBorrandoId: null,
  categoriaEditandoId: null,
  movimientosPagina: 1,
  movimientosPaginaSize: 20,
  movimientosTotal: 0,
  movimientosTotalPaginas: 1,
  movimientosExpandido: false,
  reportesPeriodo: localStorage.getItem("cc_reportes_periodo") || "mensual",
  reportesData: null,
  resumenDetalleAbierto: false,
  seccionActiva: localStorage.getItem("cc_dashboard_section") || "overview",
  accessToken: localStorage.getItem(ACCESS_TOKEN_KEY),
  refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY),
  iaDisponible: null,
  ocrEnProceso: false,
  notificacionesNativasHabilitadas: false,
  notificacionesPollingId: null,
  notificacionesNativasVistas: (() => {
    try {
      const raw = sessionStorage.getItem("cc_notif_native_seen");
      const parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed) ? parsed : [];
    } catch (_) {
      return [];
    }
  })(),
};

// Chart.js instances
let chartCategorias = null;
let chartTendencia = null;
let categoriasCache = [];

// ISO/IEC 27001 - Session timeout (15 minutes)
// [NORMA: ISO/IEC 27001 - Control A.9.4.2] Cierre automático de sesión por inactividad tras periodo configurado (15 minutos)
// [NORMA: OWASP Mobile Top 10 - M4] Protección contra robo de dispositivo en sesiones abiertas
const SESSION_TIMEOUT_MS = 15 * 60 * 1000;

// ============================================================
//  UTILIDADES: Peticiones HTTP
// ============================================================
function endpointPublico(endpoint) {
  return (
    endpoint === "/auth/login" ||
    endpoint === "/auth/registro" ||
    endpoint === "/auth/refresh"
  );
}

function guardarTokens(tokens) {
  if (!tokens) return;
  if (tokens.access_token) {
    estadoApp.accessToken = tokens.access_token;
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  }
  if (tokens.refresh_token) {
    estadoApp.refreshToken = tokens.refresh_token;
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  }
}

function limpiarTokens() {
  estadoApp.accessToken = null;
  estadoApp.refreshToken = null;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem("cc_user_info");  // limpiar info de usuario también
}

async function verificarDisponibilidadIA() {
  if (estadoApp.iaDisponible !== null) {
    actualizarBadgeIA(estadoApp.iaDisponible);
    return estadoApp.iaDisponible;
  }
  try {
    const resp = await apiRequest("/health");
    estadoApp.iaDisponible = !!resp?.data?.ia?.nvidia_configurada;
    actualizarBadgeIA(estadoApp.iaDisponible);
  } catch (_) {
    estadoApp.iaDisponible = false;
    actualizarBadgeIA(false);
  }
  return estadoApp.iaDisponible;
}

function actualizarBadgeIA(disponible) {
  const badge = document.getElementById("ia-status-badge");
  if (!badge) return;
  badge.style.display = disponible ? "none" : "inline-flex";
}

function mostrarMensajeIADeshabilitada() {
  actualizarBadgeIA(false);
  ocultarSkeletonPerfilIA();
  const panel = document.getElementById("perfil-ia-contenido");
  if (panel) {
    panel.innerHTML = `
            <p class="text-muted" style="text-align:center; padding: var(--space-md);">
                🔑 Configura NVIDIA_API_KEY para activar el perfil IA
            </p>
        `;
  }
}

async function renovarAccessToken() {
  const refreshToken =
    estadoApp.refreshToken || localStorage.getItem(REFRESH_TOKEN_KEY);
  if (!refreshToken) return false;

  try {
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    const data = await response.json();
    if (!response.ok || !data?.data?.access_token) {
      limpiarTokens();
      return false;
    }

    guardarTokens(data.data);
    return true;
  } catch (_) {
    limpiarTokens();
    return false;
  }
}

async function apiRequest(
  endpoint,
  method = "GET",
  body = null,
  permitirReintento = true,
) {
  const headers = {};
  const accessToken =
    estadoApp.accessToken || localStorage.getItem(ACCESS_TOKEN_KEY);
  if (accessToken && !endpointPublico(endpoint)) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  const options = {
    method,
    headers,
    credentials: "include",
  };
  if (body !== null && body !== undefined) {
    headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE}${endpoint}`, options);

  // CSV download handling
  if (response.headers.get("content-type")?.includes("text/csv")) {
    return response;
  }

  const isJson = response.headers
    .get("content-type")
    ?.includes("application/json");
  const data = isJson
    ? await response.json()
    : { mensaje: await response.text() };

  if (
    response.status === 401 &&
    permitirReintento &&
    !endpointPublico(endpoint)
  ) {
    const renovado = await renovarAccessToken();
    if (renovado) {
      return apiRequest(endpoint, method, body, false);
    }
  }

  if (!response.ok) throw { status: response.status, ...data };
  return data;
}

// ============================================================
//  UTILIDADES: Formato
// ============================================================
const MONEDA_POR_DEFECTO = "COP";
const MONEDA_LOCALES = {
  COP: "es-CO",
  USD: "en-US",
};

function obtenerMonedaPreferida() {
  const moneda =
    estadoApp.usuario?.moneda || localStorage.getItem("cc_moneda") || "";
  return (moneda || MONEDA_POR_DEFECTO).toUpperCase();
}

function guardarMonedaPreferida(moneda) {
  if (!moneda) return;
  localStorage.setItem("cc_moneda", String(moneda).toUpperCase());
}

function formatMoney(amount) {
  const num = parseFloat(amount);
  const safeNum = Number.isFinite(num) ? num : 0;
  const moneda = obtenerMonedaPreferida();
  const locale = MONEDA_LOCALES[moneda] || "es-CO";
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: moneda,
    currencyDisplay: "code",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(safeNum);
}

function formatMoneyAbs(amount) {
  return formatMoney(Math.abs(parseFloat(amount) || 0));
}

function obtenerEtiquetaMoneda() {
  return obtenerMonedaPreferida();
}

function actualizarMonedaUI() {
  const etiqueta = obtenerEtiquetaMoneda();

  document.querySelectorAll("[data-currency-label]").forEach((el) => {
    const base = el.getAttribute("data-currency-label") || el.textContent || "";
    el.textContent = `${base} (${etiqueta})`;
  });

  document.querySelectorAll("[data-currency-placeholder]").forEach((el) => {
    const base = el.getAttribute("data-currency-placeholder") || "0";
    el.placeholder = `${etiqueta} ${base}`.trim();
  });

  document.querySelectorAll("[data-money-placeholder]").forEach((el) => {
    el.textContent = formatMoney(0);
  });

  if (chartTendencia?.options?.scales?.y?.ticks) {
    chartTendencia.options.scales.y.ticks.callback = (val) => formatMoney(val);
    chartTendencia.update();
  }
}

function formatDate(dateStr) {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  return date.toLocaleDateString("es-MX", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// SVG icons for password toggle
const _EYE_OPEN_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
const _EYE_CLOSED_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`;

function togglePasswordVisibility(inputId, btnEl) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const isPassword = input.type === 'password';
  input.type = isPassword ? 'text' : 'password';
  if (btnEl) {
    btnEl.innerHTML = isPassword ? _EYE_CLOSED_SVG : _EYE_OPEN_SVG;
    btnEl.setAttribute('aria-label', isPassword ? 'Ocultar contraseña' : 'Mostrar contraseña');
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/* ============================================================
   UX: Animación de contadores numéricos
   ============================================================ */
function animateCounter(el, from, to, duration = 800) {
  if (!el) return;
  const startTime = performance.now();
  const isNegative = to < 0;
  const absTo = Math.abs(to);
  const absFrom = Math.abs(from);

  function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
  }

  function tick(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = easeOutCubic(progress);
    const current = absFrom + (absTo - absFrom) * eased;
    const signed = isNegative ? -current : current;
    el.textContent = formatMoney(signed);
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

function renderMarkdownSafe(markdownText) {
  const text = String(markdownText || "");

  // Prioridad: parser Markdown robusto del navegador si está disponible.
  if (window.marked && window.DOMPurify) {
    if (!window.__cc_marked_configured) {
      window.marked.setOptions({ gfm: true, breaks: true });
      window.__cc_marked_configured = true;
    }
    const rawHtml = window.marked.parse(text);
    return window.DOMPurify.sanitize(rawHtml, {
      USE_PROFILES: { html: true },
      FORBID_TAGS: ["style", "script"],
    });
  }

  // Fallback seguro si no cargó la librería.
  return escapeHtml(text).replace(/\n/g, "<br>");
}

function crearMensajeChat(role, contenido = "", esMarkdown = false) {
  const wrapper = document.createElement("div");
  wrapper.className = `chat-msg chat-msg--${role}`;

  const avatar = document.createElement("span");
  avatar.className = "chat-avatar";
  avatar.textContent = role === "user" ? "👤" : "🤖";

  const bubble = document.createElement("div");
  bubble.className = "chat-bubble";
  if (esMarkdown) {
    bubble.classList.add("chat-bubble--markdown");
    bubble.innerHTML = renderMarkdownSafe(contenido);
  } else {
    bubble.textContent = contenido;
  }

  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  return wrapper;
}

async function animarRespuestaStreaming(bubbleEl, textoMarkdown, containerEl) {
  const reduceMotion =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const text = String(textoMarkdown || "");
  if (!text) {
    bubbleEl.innerHTML = "";
    return;
  }

  if (reduceMotion || text.length < 25) {
    bubbleEl.innerHTML = renderMarkdownSafe(text);
    return;
  }

  const step =
    text.length > 1000
      ? 14
      : text.length > 600
        ? 10
        : text.length > 300
          ? 6
          : 4;
  const delayMs = text.length > 1000 ? 8 : text.length > 600 ? 11 : 15;

  for (let i = step; i < text.length; i += step) {
    const partial = text.slice(0, i);
    bubbleEl.innerHTML = `${renderMarkdownSafe(partial)}<span class="chat-stream-cursor">|</span>`;
    containerEl.scrollTop = containerEl.scrollHeight;
    await sleep(delayMs);
  }

  bubbleEl.innerHTML = renderMarkdownSafe(text);
}

// ============================================================
//  MODO OSCURO / CLARO
// ============================================================
function aplicarModo(oscuro) {
  document.body.classList.toggle("light-mode", !oscuro);
  const btn = document.getElementById("btn-toggle-modo");
  if (btn) {
    const icon = btn.querySelector(".btn-icon-emoji");
    if (icon) icon.textContent = oscuro ? "☀️" : "🌙";
  }
  localStorage.setItem("cc_modo", oscuro ? "dark" : "light");
}

function toggleModo() {
  estadoApp.modoOscuro = !estadoApp.modoOscuro;
  aplicarModo(estadoApp.modoOscuro);
}

// ============================================================
//  F6: SISTEMA DE NOTIFICACIONES (Toast)
// ============================================================
function mostrarToast(titulo, mensaje, tipo = "info") {
  const container = document.getElementById("toast-container");
  const iconos = { exito: "✅", error: "❌", alerta: "⚠️", info: "ℹ️" };
  const toast = document.createElement("div");
  toast.className = `glass-toast glass-toast--${tipo}`;
  toast.innerHTML = `
        <span class="toast-icon">${iconos[tipo] || "ℹ️"}</span>
        <div class="toast-content">
            <div class="toast-title">${escapeHtml(titulo)}</div>
            <div class="toast-message">${escapeHtml(mensaje)}</div>
        </div>
    `;
  toast.addEventListener("click", () => {
    toast.classList.add("removing");
    setTimeout(() => toast.remove(), 300);
  });
  container.appendChild(toast);
  setTimeout(() => {
    if (toast.parentNode) {
      toast.classList.add("removing");
      setTimeout(() => toast.remove(), 300);
    }
  }, 5000);
}

// Toast especial para insight diario (tipo Duolingo)
function mostrarToastInsight(insight) {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = "glass-toast glass-toast--insight";
  toast.innerHTML = `
        <span class="toast-icon">💡</span>
        <div class="toast-content">
            <div class="toast-title">Tu análisis del día está listo</div>
            <div class="toast-message">${escapeHtml(insight.substring(0, 120))}${insight.length > 120 ? "..." : ""}</div>
            <button class="toast-action-btn" onclick="this.closest('.glass-toast').remove(); scrollToPerfilIA();">Ver perfil completo →</button>
        </div>
    `;
  toast.addEventListener("click", (e) => {
    if (e.target.tagName !== "BUTTON") {
      toast.classList.add("removing");
      setTimeout(() => toast.remove(), 300);
    }
  });
  container.appendChild(toast);
  setTimeout(() => {
    if (toast.parentNode) {
      toast.classList.add("removing");
      setTimeout(() => toast.remove(), 300);
    }
  }, 8000);
}

function scrollToPerfilIA() {
  mostrarSeccionDashboard("profile");
  const el = document.getElementById("seccion-perfil-ia");
  if (el) el.scrollIntoView({ behavior: "smooth" });
}

// ============================================================
//  SKELETON LOADERS
// ============================================================
function mostrarSkeletonMovimientos() {
  const container = document.getElementById("lista-movimientos");
  container.innerHTML = Array(4)
    .fill(0)
    .map(
      () => `
        <div class="skeleton-item">
            <div class="skeleton skeleton-icon"></div>
            <div class="skeleton-lines">
                <div class="skeleton skeleton-line-lg"></div>
                <div class="skeleton skeleton-line-sm"></div>
            </div>
            <div class="skeleton skeleton-amount"></div>
        </div>
    `,
    )
    .join("");
}

function mostrarSkeletonPerfilIA() {
  const sk = document.getElementById("perfil-skeleton");
  if (sk) sk.style.display = "flex";
}

function ocultarSkeletonPerfilIA() {
  const sk = document.getElementById("perfil-skeleton");
  if (sk) sk.style.display = "none";
}

// ============================================================
//  F6: NOTIFICACIONES
// ============================================================
function persistirNotificacionesNativasVistas() {
  try {
    const compact = estadoApp.notificacionesNativasVistas.slice(-200);
    sessionStorage.setItem("cc_notif_native_seen", JSON.stringify(compact));
  } catch (_) {}
}

function marcarNotificacionNativaVista(id) {
  const key = String(id);
  if (estadoApp.notificacionesNativasVistas.includes(key)) return;
  estadoApp.notificacionesNativasVistas.push(key);
  persistirNotificacionesNativasVistas();
}

function yaSeMostroNotificacionNativa(id) {
  return estadoApp.notificacionesNativasVistas.includes(String(id));
}

async function mostrarNotificacionNativaSistema(notificacion) {
  if (!estadoApp.notificacionesNativasHabilitadas) return;
  if (!("Notification" in window) || Notification.permission !== "granted")
    return;

  const titulo = String(notificacion?.titulo || "ControlCash");
  const mensaje = String(
    notificacion?.mensaje || "Tienes una notificación nueva.",
  );
  const tag = `controlcash-notif-${notificacion?.id || Date.now()}`;

  try {
    if ("serviceWorker" in navigator) {
      const reg = await navigator.serviceWorker.getRegistration();
      if (reg && typeof reg.showNotification === "function") {
        await reg.showNotification(titulo, {
          body: mensaje,
          tag,
          icon: "/icons/icon-192.svg",
          badge: "/icons/icon-72.svg",
        });
        return;
      }
    }

    new Notification(titulo, {
      body: mensaje,
      tag,
      icon: "icons/icon-192.svg",
    });
  } catch (_) {}
}

async function emitirNotificacionesNativas(notificaciones) {
  if (!Array.isArray(notificaciones) || notificaciones.length === 0) return;

  const nuevas = notificaciones.filter(
    (n) => !yaSeMostroNotificacionNativa(n.id),
  );
  if (nuevas.length === 0) return;

  // Evita inundar el sistema si llegan muchas a la vez.
  const ultimas = nuevas.slice(-3);
  for (const n of ultimas) {
    await mostrarNotificacionNativaSistema(n);
    marcarNotificacionNativaVista(n.id);
  }
}

function vapidKeyToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

async function inicializarSuscripcionWebPush() {
  if (esLocalhost) return;
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) return;
  if (Notification.permission !== "granted") return;

  try {
    const registration = await navigator.serviceWorker.ready;
    if (!registration?.pushManager) return;

    const existente = await registration.pushManager.getSubscription();
    if (existente) return;

    const keyResp = await apiRequest("/push/vapid-key");
    const publicKey = keyResp?.data?.publicKey;
    if (!publicKey) return;

    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: vapidKeyToUint8Array(publicKey),
    });

    await apiRequest("/push/subscribe", "POST", {
      subscription: subscription.toJSON ? subscription.toJSON() : subscription,
    });
  } catch (_) {}
}

async function inicializarNotificacionesNativas() {
  if (!("Notification" in window)) return;

  if (Notification.permission === "granted") {
    estadoApp.notificacionesNativasHabilitadas = true;
    await inicializarSuscripcionWebPush();
    return;
  }

  if (Notification.permission === "denied") {
    estadoApp.notificacionesNativasHabilitadas = false;
    return;
  }

  try {
    const permission = await Notification.requestPermission();
    estadoApp.notificacionesNativasHabilitadas = permission === "granted";
    if (estadoApp.notificacionesNativasHabilitadas) {
      await inicializarSuscripcionWebPush();
    }
  } catch (_) {
    estadoApp.notificacionesNativasHabilitadas = false;
  }
}

async function cargarNotificaciones() {
  try {
    const resp = await apiRequest("/notificaciones?no_leidas=true");
    const notificaciones = resp.data;
    const countEl = document.getElementById("notif-count");

    if (notificaciones.length > 0) {
      countEl.textContent = notificaciones.length;
      countEl.style.display = "flex";
    } else {
      countEl.style.display = "none";
    }

    const panel = document.getElementById("notification-panel");
    if (notificaciones.length === 0) {
      panel.innerHTML = `
                <div class="empty-state" style="padding: var(--space-lg);">
                    <p style="font-size: var(--font-size-sm);">Sin notificaciones nuevas</p>
                </div>
            `;
      return;
    }

    let html = "";
    notificaciones.forEach((n) => {
      html += `
                <div class="notification-item unread" onclick="marcarNotificacionLeida(${n.id}, this)">
                    <div class="notif-title">${escapeHtml(n.titulo)}</div>
                    <div class="notif-message">${escapeHtml(n.mensaje)}</div>
                    <div class="notif-time">${formatDate(n.fecha)}</div>
                </div>
            `;
    });
    panel.innerHTML = html;

    await emitirNotificacionesNativas(notificaciones);
  } catch (_) {}
}

function toggleNotificationPanel() {
  if ("Notification" in window && Notification.permission === "default") {
    inicializarNotificacionesNativas();
  }
  const panel = document.getElementById("notification-panel");
  estadoApp.notifPanelAbierto = !estadoApp.notifPanelAbierto;
  panel.classList.toggle("active", estadoApp.notifPanelAbierto);
}

async function marcarNotificacionLeida(id, element) {
  try {
    await apiRequest(`/notificaciones/${id}`, "PUT");
    element.classList.remove("unread");
    cargarNotificaciones();
  } catch (_) {}
}

document.addEventListener("click", (e) => {
  const panel = document.getElementById("notification-panel");
  const btn = document.getElementById("notif-btn");
  if (
    estadoApp.notifPanelAbierto &&
    !panel.contains(e.target) &&
    !btn.contains(e.target)
  ) {
    estadoApp.notifPanelAbierto = false;
    panel.classList.remove("active");
  }
});
