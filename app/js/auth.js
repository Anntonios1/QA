/**
 * ============================================================
 *  CAPA DE PRESENTACION - Logica de Autenticación y Seguridad
 *  ControlCash v2.1 - Sistema Profesional de Control Financiero
 * ============================================================
 */

// ============================================================
//  F1: REGISTRARSE
// ============================================================
// [NORMA: ISO 9126 - Usabilidad] Separación limpia de flujos de registro e inicio de sesión
function toggleAuthForm(mode) {
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");
  const subtitle = document.getElementById("auth-subtitle");
  const errorDiv = document.getElementById("auth-error");

  errorDiv.classList.remove("visible");
  errorDiv.textContent = "";

  if (mode === "register") {
    loginForm.style.display = "none";
    registerForm.style.display = "block";
    subtitle.textContent = "Crea tu cuenta gratuita";
  } else {
    loginForm.style.display = "block";
    registerForm.style.display = "none";
    subtitle.textContent = "Control financiero inteligente y seguro";
  }
}

document
  .getElementById("register-form")
  .addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorDiv = document.getElementById("auth-error");
    errorDiv.classList.remove("visible");

    const nombre = document.getElementById("reg-nombre").value.trim();
    const email = document.getElementById("reg-email").value.trim();
    const password = document.getElementById("reg-password").value;
    const confirmPassword = document.getElementById("reg-password-confirm").value;

    if (password !== confirmPassword) {
      errorDiv.textContent = "Las contraseñas no coinciden.";
      errorDiv.classList.add("visible");
      return;
    }

    // Validación de nombre: sin números ni caracteres especiales
    if (/\d/.test(nombre)) {
      errorDiv.textContent = "El nombre no puede contener números.";
      errorDiv.classList.add("visible");
      return;
    }
    if (!/^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-']+$/.test(nombre)) {
      errorDiv.textContent = "El nombre solo puede contener letras, espacios y guiones.";
      errorDiv.classList.add("visible");
      return;
    }
    if (nombre.length < 2) {
      errorDiv.textContent = "El nombre debe tener al menos 2 caracteres.";
      errorDiv.classList.add("visible");
      return;
    }

    const moneda =
      document.getElementById("reg-moneda")?.value || MONEDA_POR_DEFECTO;
    const presupuestoRaw =
      document.getElementById("reg-presupuesto")?.value || "";
    const presupuestoMensual = Number(presupuestoRaw);

    if (!presupuestoRaw || !Number.isFinite(presupuestoMensual)) {
      errorDiv.textContent = "Ingresa un presupuesto mensual válido.";
      errorDiv.classList.add("visible");
      return;
    }
    if (presupuestoMensual <= 0) {
      errorDiv.textContent = "El presupuesto mensual debe ser mayor a cero.";
      errorDiv.classList.add("visible");
      return;
    }

    try {
      const resp = await apiRequest("/auth/registro", "POST", {
        nombre,
        email,
        password,
        moneda,
        presupuesto_mensual: presupuestoMensual,
      });
      guardarMonedaPreferida(moneda);
      mostrarToast("¡Bienvenido!", resp.mensaje, "exito");
      toggleAuthForm("login");
      document.getElementById("login-email").value = email;
    } catch (err) {
      const msg = err.errores
        ? err.errores.join(" ")
        : err.mensaje || "Error al registrarse.";
      errorDiv.textContent = msg;
      errorDiv.classList.add("visible");
    }
  });

// ============================================================
//  F2: INICIAR SESIÓN
// ============================================================
// [NORMA: ISO/IEC 27001 - Control A.9.4.2] Verificación de identidad y control de inicio de sesión con persistencia segura de tokens
// [NORMA: OWASP Mobile Top 10 - M4] Prevención de sesiones inseguras y soporte para autenticación biométrica
document.getElementById("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorDiv = document.getElementById("auth-error");
  errorDiv.classList.remove("visible");

  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;

  try {
    const resp = await apiRequest("/auth/login", "POST", { email, password });
    guardarTokens(resp.data?.tokens);
    estadoApp.usuario = resp.data;
    // Persistir datos básicos del usuario para restaurar en recargas
    try {
      localStorage.setItem("cc_user_info", JSON.stringify({
        nombre: resp.data?.nombre || "",
        email:  resp.data?.email  || "",
        moneda: resp.data?.moneda || "COP",
      }));
    } catch (_) {}
    guardarMonedaPreferida(resp.data?.moneda);
    iniciarDashboard();
    resetearSessionTimeout();
    guardarCredencialesBiometrico(email, password);
    mostrarToast(
      "Sesion iniciada",
      `Hola, ${escapeHtml(resp.data.nombre)}`,
      "exito",
    );
  } catch (err) {
    const msg = err.errores
      ? err.errores.join(" ")
      : err.mensaje || "Error al iniciar sesión.";
    errorDiv.textContent = msg;
    errorDiv.classList.add("visible");
  }
});

// ============================================================
//  CERRAR SESIÓN
// ============================================================
// [NORMA: ISO/IEC 27001 - Control A.9.4.2] Cierre seguro de sesión y revocación inmediata de tokens activos en la API
// [NORMA: OWASP Mobile Top 10 - M4] Cierre automático y limpieza de credenciales en el cliente
async function cerrarSesion() {
  const refreshToken =
    estadoApp.refreshToken || localStorage.getItem(REFRESH_TOKEN_KEY);
  if (refreshToken) {
    try {
      await fetch(`${API_BASE}/auth/revoke`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    } catch (_) {}
  }
  try {
    await apiRequest("/auth/logout", "POST");
  } catch (_) {}
  limpiarTokens();
  estadoApp.usuario = null;
  if (estadoApp.sesionTimeoutId) {
    clearTimeout(estadoApp.sesionTimeoutId);
    estadoApp.sesionTimeoutId = null;
  }
  if (estadoApp.notificacionesPollingId) {
    clearInterval(estadoApp.notificacionesPollingId);
    estadoApp.notificacionesPollingId = null;
  }
  // Destruir charts
  if (chartCategorias) {
    chartCategorias.destroy();
    chartCategorias = null;
  }
  if (chartTendencia) {
    chartTendencia.destroy();
    chartTendencia = null;
  }
  document.getElementById("auth-view").classList.remove("hidden");
  document.getElementById("dashboard").classList.remove("active");
  const fab = document.getElementById("fab-acciones");
  if (fab) fab.style.display = "none";
  document.getElementById("login-form").reset();
  document.getElementById("register-form").reset();
  document.getElementById("auth-error").classList.remove("visible");
}

// ============================================================
//  PWA: Registro del Service Worker
// ============================================================
const esLocalhost =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1";

if ("serviceWorker" in navigator && !esLocalhost) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/service-worker.js")
      .then((reg) => console.log("[PWA] Service Worker registrado:", reg.scope))
      .catch((err) => console.warn("[PWA] Error registrando SW:", err));
  });
} else if ("serviceWorker" in navigator && esLocalhost) {
  window.addEventListener("load", async () => {
    const regs = await navigator.serviceWorker.getRegistrations();
    await Promise.all(regs.map((reg) => reg.unregister()));
    console.log(
      "[PWA] Service Worker desactivado en localhost para evitar cache obsoleta.",
    );
  });
}

// ============================================================
//  AUTENTICACION BIOMETRICA (Capacitor)
// ============================================================
async function verificarBiometrico() {
  try {
    if (typeof Capacitor !== "undefined" && Capacitor.isNativePlatform()) {
      const { BiometricAuth } = Capacitor.Plugins;
      if (BiometricAuth) {
        const result = await BiometricAuth.isAvailable();
        if (result.isAvailable) {
          estadoApp.biometricoDisponible = true;
          const btnBio = document.getElementById("btn-biometric");
          const dividerBio = document.getElementById("auth-divider-biometric");
          if (btnBio) btnBio.style.display = "flex";
          if (dividerBio) dividerBio.style.display = "flex";
        }
      }
    }
  } catch (err) {
    console.log("[Bio] Biometrico no disponible:", err.message || err);
  }
}

async function autenticacionBiometrica() {
  if (!estadoApp.biometricoDisponible) {
    mostrarToast(
      "No disponible",
      "Autenticacion biometrica no disponible.",
      "alerta",
    );
    return;
  }
  try {
    const { BiometricAuth } = Capacitor.Plugins;
    await BiometricAuth.authenticate({
      reason: "Verificar identidad para acceder a ControlCash",
      title: "ControlCash - Acceso Seguro",
      subtitle: "Usa tu huella o Face ID",
      cancelTitle: "Cancelar",
      allowDeviceCredential: true,
    });
    const { Preferences } = Capacitor.Plugins;
    const emailResult = await Preferences.get({ key: "cc_bio_email" });
    const passResult = await Preferences.get({ key: "cc_bio_pass" });
    if (emailResult.value && passResult.value) {
      const resp = await apiRequest("/auth/login", "POST", {
        email: emailResult.value,
        password: passResult.value,
      });
      guardarTokens(resp.data?.tokens);
      estadoApp.usuario = resp.data;
      iniciarDashboard();
      mostrarToast(
        "Acceso biometrico",
        `Bienvenido, ${escapeHtml(resp.data.nombre)}`,
        "exito",
      );
    } else {
      mostrarToast(
        "Configurar",
        "Inicie sesion primero para activar el acceso biometrico.",
        "info",
      );
    }
  } catch (err) {
    if (err.message && err.message.includes("cancel")) return;
    mostrarToast(
      "Error biometrico",
      "No se pudo verificar la identidad.",
      "error",
    );
  }
}

async function guardarCredencialesBiometrico(email, password) {
  try {
    if (typeof Capacitor !== "undefined" && Capacitor.isNativePlatform()) {
      const { Preferences } = Capacitor.Plugins;
      if (Preferences) {
        await Preferences.set({ key: "cc_bio_email", value: email });
        await Preferences.set({ key: "cc_bio_pass", value: password });
      }
    }
  } catch (_) {}
}

// ============================================================
//  PERFIL DE USUARIO
// ============================================================
async function cargarPerfil() {
  // Mostrar estado de carga en el header
  const nombreEl = document.getElementById("profile-nombre");
  const emailEl  = document.getElementById("profile-email");
  if (nombreEl && nombreEl.textContent === "Cargando...") {
    // ya está en estado cargando, no reasignar
  }

  try {
    const resp = await apiRequest("/auth/perfil");
    const data = resp?.data;
    if (!data) {
      console.warn("[Perfil] Respuesta sin datos:", resp);
      return;
    }

    // Avatar: primera letra del nombre (sin emoji)
    const avatarEl = document.getElementById("profile-avatar");
    if (avatarEl) {
      const nameStr = String(data.nombre || estadoApp.usuario?.nombre || "U");
      const initial = nameStr.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ]/g, "").charAt(0).toUpperCase();
      // Limpiar contenido y poner la letra
      avatarEl.innerHTML = "";
      avatarEl.textContent = initial || "U";
    }

    // Header: nombre y email
    if (nombreEl) nombreEl.textContent = data.nombre || "";
    if (emailEl)  emailEl.textContent  = data.email  || "";

    // Chips de datos
    const monedaEl = document.getElementById("profile-moneda");
    if (monedaEl) monedaEl.textContent = data.moneda || "COP";

    const fechaEl = document.getElementById("profile-fecha");
    if (fechaEl) {
      if (data.fecha_creacion) {
        try {
          // Normalizar formato de fecha
          const fechaStr = String(data.fecha_creacion).replace(" ", "T");
          fechaEl.textContent = formatDate(fechaStr);
        } catch (_) {
          fechaEl.textContent = data.fecha_creacion;
        }
      } else {
        fechaEl.textContent = "--";
      }
    }

    // Pre-fill formulario de edición
    const inputNombre = document.getElementById("perfil-nombre");
    if (inputNombre) inputNombre.value = data.nombre || "";

    const selectMoneda = document.getElementById("perfil-moneda");
    if (selectMoneda) selectMoneda.value = data.moneda || "COP";

  } catch (err) {
    console.error("[Perfil] Error al cargar perfil:", err);

    // Fallback: usar datos ya en memoria si están disponibles
    const usuario = estadoApp.usuario;
    if (usuario) {
      const avatarEl = document.getElementById("profile-avatar");
      if (avatarEl) {
        const nameStr = String(usuario.nombre || "U");
        const initial = nameStr.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ]/g, "").charAt(0).toUpperCase();
        avatarEl.innerHTML = "";
        avatarEl.textContent = initial || "U";
      }
      if (nombreEl) nombreEl.textContent = usuario.nombre || "";
      if (emailEl)  emailEl.textContent  = usuario.email  || "";
      const monedaEl = document.getElementById("profile-moneda");
      if (monedaEl) monedaEl.textContent = usuario.moneda || "COP";
      const inputNombre = document.getElementById("perfil-nombre");
      if (inputNombre) inputNombre.value = usuario.nombre || "";
      const selectMoneda = document.getElementById("perfil-moneda");
      if (selectMoneda) selectMoneda.value = usuario.moneda || "COP";
    } else {
      mostrarToast("Error", "No se pudo cargar el perfil.", "error");
    }
  }
}

async function guardarPerfil(event) {
  event.preventDefault();
  const errorDiv = document.getElementById("perfil-edit-error");
  if (errorDiv) { errorDiv.classList.remove("visible"); errorDiv.textContent = ""; }

  const nombre = document.getElementById("perfil-nombre")?.value?.trim() || "";
  const moneda = document.getElementById("perfil-moneda")?.value || "COP";

  // Validación frontend del nombre
  if (/\d/.test(nombre)) {
    if (errorDiv) { errorDiv.textContent = "El nombre no puede contener números."; errorDiv.classList.add("visible"); }
    return;
  }
  if (!/^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-']+$/.test(nombre)) {
    if (errorDiv) { errorDiv.textContent = "El nombre solo puede contener letras, espacios y guiones."; errorDiv.classList.add("visible"); }
    return;
  }
  if (nombre.length < 2) {
    if (errorDiv) { errorDiv.textContent = "El nombre debe tener al menos 2 caracteres."; errorDiv.classList.add("visible"); }
    return;
  }

  const btn = document.getElementById("btn-guardar-perfil");
  const txt = btn?.textContent;
  if (btn) { btn.disabled = true; btn.textContent = "Guardando..."; }

  try {
    await apiRequest("/auth/perfil", "PUT", { nombre, moneda });
    mostrarToast("Perfil", "Datos actualizados correctamente.", "exito");
    // Actualizar navbar y estado
    document.getElementById("navbar-user").textContent = `Hola, ${nombre}`;
    if (estadoApp.usuario) {
      estadoApp.usuario.nombre = nombre;
      estadoApp.usuario.moneda = moneda;
    }
    guardarMonedaPreferida(moneda);
    actualizarMonedaUI();
    cargarPerfil();
  } catch (err) {
    const msg = err?.errores ? err.errores.join(" ") : err?.mensaje || "Error al guardar.";
    if (errorDiv) { errorDiv.textContent = msg; errorDiv.classList.add("visible"); }
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = txt || "Guardar cambios"; }
  }
}

async function cambiarPassword(event) {
  event.preventDefault();
  const errorDiv = document.getElementById("password-change-error");
  if (errorDiv) { errorDiv.classList.remove("visible"); errorDiv.textContent = ""; }

  const actual = document.getElementById("perfil-password-actual")?.value || "";
  const nueva = document.getElementById("perfil-password-nueva")?.value || "";
  const confirmar = document.getElementById("perfil-password-confirmar")?.value || "";

  if (!actual) {
    if (errorDiv) { errorDiv.textContent = "Ingresa tu contraseña actual."; errorDiv.classList.add("visible"); }
    return;
  }
  if (nueva.length < 8) {
    if (errorDiv) { errorDiv.textContent = "La nueva contraseña debe tener al menos 8 caracteres."; errorDiv.classList.add("visible"); }
    return;
  }
  if (nueva !== confirmar) {
    if (errorDiv) { errorDiv.textContent = "Las contraseñas nuevas no coinciden."; errorDiv.classList.add("visible"); }
    return;
  }
  if (actual === nueva) {
    if (errorDiv) { errorDiv.textContent = "La nueva contraseña debe ser diferente a la actual."; errorDiv.classList.add("visible"); }
    return;
  }

  const btn = document.getElementById("btn-cambiar-password");
  const txt = btn?.textContent;
  if (btn) { btn.disabled = true; btn.textContent = "Cambiando..."; }

  try {
    await apiRequest("/auth/password", "PUT", {
      password_actual: actual,
      password_nueva: nueva,
    });
    mostrarToast("Seguridad", "Contraseña actualizada correctamente.", "exito");
    document.getElementById("form-cambiar-password")?.reset();
  } catch (err) {
    const msg = err?.errores ? err.errores.join(" ") : err?.mensaje || "Error al cambiar la contraseña.";
    if (errorDiv) { errorDiv.textContent = msg; errorDiv.classList.add("visible"); }
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = txt || "Cambiar contraseña"; }
  }
}
