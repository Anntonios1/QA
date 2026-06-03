/**
 * ============================================================
 *  CAPA DE PRESENTACION - Logica de Aplicacion (Punto de Entrada)
 *  ControlCash v2.1 - Sistema Profesional de Control Financiero
 * ============================================================
 */

// ============================================================
//  DASHBOARD: Inicialización
// ============================================================
function iniciarDashboard() {
  mostrarDashboardConTransicion();
  actualizarMonedaUI();
  document.getElementById("navbar-user").textContent =
    `Hola, ${estadoApp.usuario.nombre}`;
  if (estadoApp.seccionActiva === "all") {
    estadoApp.seccionActiva = "overview";
  }
  estadoApp.movimientosExpandido = estadoApp.seccionActiva === "movimientos";
  aplicarModo(estadoApp.modoOscuro);
  inicializarMenuSecciones();
  mostrarOnboardingRapido();
  cargarCategoriasEnFiltro();
  cargarCategoriasAdmin();
  cargarCategoriasPresupuestos();
  cargarCategoriasRecurrencias("gasto");
  actualizarRecurrenciaForm();
  inicializarPresupuestosUI();
  cargarPresupuestos();
  cargarPresupuestoHome();
  cargarBalance();
  estadoApp.movimientosPagina = 1;
  if (
    estadoApp.seccionActiva !== "overview" &&
    estadoApp.seccionActiva !== "movimientos"
  ) {
    cargarMovimientos();
  }
  cargarResumen();
  cargarReportes();
  cargarRecurrencias();
  cargarNotificaciones();
  inicializarNotificacionesNativas();

  if (estadoApp.notificacionesPollingId) {
    clearInterval(estadoApp.notificacionesPollingId);
  }
  estadoApp.notificacionesPollingId = setInterval(() => {
    cargarNotificaciones();
  }, 60000);

  // Cargar funciones IA solo si el backend las tiene habilitadas
  (async () => {
    const iaActiva = await verificarDisponibilidadIA();
    if (!iaActiva) {
      mostrarMensajeIADeshabilitada();
      return;
    }
    actualizarBadgeIA(true);
    verificarInsightDiario();
    cargarPerfilIA();
  })();

  // IntersectionObserver para animación staggered de secciones
  const secciones = document.querySelectorAll(".dashboard-section");
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry, i) => {
          if (entry.isIntersecting) {
            // Stagger delay basado en la posición en el DOM
            const index = Array.from(secciones).indexOf(entry.target);
            setTimeout(() => {
              entry.target.classList.add("visible");
            }, index * 90);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.08, rootMargin: "0px 0px -30px 0px" },
    );
    secciones.forEach((s) => observer.observe(s));
  } else {
    // Fallback: mostrar todo de inmediato
    secciones.forEach((s) => s.classList.add("visible"));
  }
}

// ============================================================
//  SESSION TIMEOUT (ISO/IEC 27001)
// ============================================================
// [NORMA: ISO/IEC 27001 - Control A.9.4.2] Cierre automático de sesión en cliente tras periodo de inactividad
// [NORMA: OWASP Mobile Top 10 - M4] Protección contra sesiones no cerradas en dispositivo compartido
function resetearSessionTimeout() {
  if (estadoApp.sesionTimeoutId) clearTimeout(estadoApp.sesionTimeoutId);
  if (estadoApp.usuario) {
    estadoApp.sesionTimeoutId = setTimeout(() => {
      mostrarToast(
        "Sesion expirada",
        "Se cerro la sesion por inactividad (ISO 27001).",
        "alerta",
      );
      cerrarSesion();
    }, SESSION_TIMEOUT_MS);
  }
}

// ============================================================
//  UX: Ripple effect en todos los botones
// ============================================================
document.addEventListener(
  "click",
  function (e) {
    const btn = e.target.closest(".glass-btn");
    if (!btn) return;
    const rect = btn.getBoundingClientRect();
    const ripple = document.createElement("span");
    ripple.className = "ripple";
    ripple.style.left = e.clientX - rect.left + "px";
    ripple.style.top = e.clientY - rect.top + "px";
    btn.appendChild(ripple);
    ripple.addEventListener("animationend", () => ripple.remove());
  },
  { passive: true },
);

// ============================================================
//  UX: Toggle filtros avanzados colapsables
// ============================================================
function toggleFiltros() {
  const filtros =
    document.getElementById("filtros-inline-panel") ||
    document.querySelector(".filtros-avanzados");
  const chevron = document.getElementById("filtros-chevron");
  if (!filtros) return;
  const collapsed = filtros.classList.toggle("collapsed");
  if (chevron) chevron.textContent = collapsed ? "▶" : "🔽";
}

// ============================================================
//  UX: Menu interactivo de secciones
// ============================================================
function mostrarSeccionDashboard(seccionId, silent = false) {
  const target = seccionId || "overview";
  const sections = document.querySelectorAll(
    ".dashboard-section[data-section-id]",
  );

  sections.forEach((section) => {
    if (section.dataset.sectionFixed === "true") return;
    if (target === "all") {
      section.classList.remove("section-hidden");
      section.classList.add("visible");
      return;
    }
    const sectionId = section.dataset.sectionId;
    const visible = target === "overview" ? sectionId === "overview" : sectionId === target;
    section.classList.toggle("section-hidden", !visible);
    if (visible) {
      section.classList.add("visible");
    }
  });

  document.querySelectorAll(".dashboard-menu-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.target === target);
  });

  document.querySelectorAll(".bottom-nav-btn").forEach((btn) => {
    const activeTarget =
      target === "movimientos" ||
      target === "profile" ||
      target === "settings"
        ? target
        : "overview";
    btn.classList.toggle("active", btn.dataset.target === activeTarget);
  });

  if (target === "movimientos") {
    estadoApp.movimientosExpandido = true;
    actualizarBotonVistaMovimientos();
    cargarMovimientos(
      estadoApp.filtroActual !== "todos" ? estadoApp.filtroActual : null,
    );
  } else if (target === "overview") {
    estadoApp.movimientosExpandido = false;
    actualizarBotonVistaMovimientos();
    cargarMovimientos(
      estadoApp.filtroActual !== "todos" ? estadoApp.filtroActual : null,
    );
  } else if (target === "categorias") {
    cargarCategoriasAdmin();
    cargarCategoriasEnFiltro();
    cargarCategoriasPresupuestos();
  } else if (target === "profile") {
    cargarPerfil();
  }

  estadoApp.seccionActiva = target;
  if (!silent) {
    localStorage.setItem("cc_dashboard_section", target);
  }
  if (target !== "overview") {
    cerrarSheetTransacciones();
  }
}

function inicializarMenuSecciones() {
  const menu = document.getElementById("dashboard-menu");
  if (!menu) return;

  menu.querySelectorAll(".dashboard-menu-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.target || "all";
      mostrarSeccionDashboard(target);
    });
  });

  mostrarSeccionDashboard(estadoApp.seccionActiva || "overview", true);
}

function navegarVistaPrincipal(vista) {
  mostrarSeccionDashboard(vista || "overview");
  if (vista === "movimientos") {
    const seccionMovimientos = document.querySelector(
      '.dashboard-section[data-section-id="movimientos"]',
    );
    seccionMovimientos?.scrollIntoView({ behavior: "smooth", block: "start" });
  } else {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}

function abrirModuloHome(vista) {
  mostrarSeccionDashboard(vista || "overview");
  window.scrollTo({ top: 0, behavior: "smooth" });
  if (vista === "categorias") {
    cargarCategoriasAdmin();
    setTimeout(() => {
      document.getElementById("categoria-nombre")?.focus();
    }, 120);
  }
}

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
//  UX: Transición auth → dashboard mejorada
// ============================================================
function mostrarDashboardConTransicion() {
  const authView = document.getElementById("auth-view");
  const dashboard = document.getElementById("dashboard");
  if (!authView || !dashboard) return;
  authView.classList.add("hiding");
  setTimeout(() => {
    authView.classList.add("hidden");
    authView.classList.remove("hiding");
    dashboard.classList.add("active", "showing");
    const fab = document.getElementById("fab-acciones");
    if (fab) fab.style.display = "inline-flex";
    setTimeout(() => dashboard.classList.remove("showing"), 400);
  }, 320);
}

// ============================================================
//  PASSWORD STRENGTH CHECKER
// ============================================================
// [NORMA: OWASP Mobile Top 10 - M4] Verificación de complejidad mínima de contraseña y descarte de patrones predecibles
// [NORMA: ISO/IEC 27001 - Control A.9.3.1] Uso de contraseñas con robustez de seguridad
function evaluarPasswordStrength(password) {
  let score = 0;
  if (!password || password.length === 0)
    return { score: 0, label: "Seguridad de contrasena", class: "" };
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++;
  if (/\d/.test(password)) score++;
  if (/[^a-zA-Z0-9]/.test(password)) score++;
  if (/^(.)\1+$/.test(password)) score = Math.max(0, score - 2);
  if (/^(123|abc|qwe|password|admin)/i.test(password)) score = 0;
  if (score <= 1) return { score: 1, label: "Debil", class: "weak" };
  if (score === 2) return { score: 2, label: "Regular", class: "fair" };
  if (score === 3) return { score: 3, label: "Buena", class: "good" };
  return { score: 4, label: "Fuerte", class: "strong" };
}

function actualizarPasswordStrength() {
  const password = document.getElementById("reg-password").value;
  const result = evaluarPasswordStrength(password);
  const fill = document.getElementById("strength-fill");
  const text = document.getElementById("strength-text");
  if (fill)
    fill.className = "strength-fill" + (result.class ? " " + result.class : "");
  if (text) {
    text.textContent = result.label;
    text.className = "strength-text" + (result.class ? " " + result.class : "");
  }
}

// ============================================================
//  INICIALIZACION GENERAL
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
  verificarBiometrico();
  aplicarModo(estadoApp.modoOscuro);
  actualizarMonedaUI();

  // Botón toggle modo claro/oscuro
  const btnModo = document.getElementById("btn-toggle-modo");
  if (btnModo) btnModo.addEventListener("click", toggleModo);

  // Validación inline del nombre en registro
  const regNombre = document.getElementById("reg-nombre");
  if (regNombre) {
    regNombre.addEventListener("input", () => {
      const val = regNombre.value;
      const errorEl = document.getElementById("reg-nombre-error");
      if (!errorEl) return;
      if (val && /\d/.test(val)) {
        errorEl.classList.add("visible");
        errorEl.textContent = "El nombre no puede contener números.";
      } else if (val && !/^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-']*$/.test(val)) {
        errorEl.classList.add("visible");
        errorEl.textContent = "Solo se permiten letras, espacios y guiones.";
      } else {
        errorEl.classList.remove("visible");
      }
    });
  }

  // Listener de fortaleza de contraseña
  const regPass = document.getElementById("reg-password");
  if (regPass) {
    regPass.addEventListener("input", actualizarPasswordStrength);
  }

  // Session Timeout activity listeners
  ["click", "keydown", "mousemove", "touchstart", "scroll"].forEach((event) => {
    document.addEventListener(
      event,
      () => {
        if (estadoApp.usuario) resetearSessionTimeout();
      },
      { passive: true },
    );
  });

  // UX: 3D Tilt hover en stat-cards
  function initTilt() {
    document.querySelectorAll(".stat-card").forEach((card) => {
      card.addEventListener("mousemove", (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const cx = rect.width / 2;
        const cy = rect.height / 2;
        const rotX = ((y - cy) / cy) * -7;
        const rotY = ((x - cx) / cx) * 7;
        card.style.transform = `perspective(600px) rotateX(${rotX}deg) rotateY(${rotY}deg) translateY(-3px)`;
        card.style.boxShadow = `0 16px 40px rgba(108,99,255,0.22)`;
      });
      card.addEventListener("mouseleave", () => {
        card.style.transform = "";
        card.style.boxShadow = "";
      });
    });
  }
  initTilt();
  window._initTilt = initTilt;
});
