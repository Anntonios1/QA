/**
 * ============================================================
 *  CAPA DE PRESENTACION - Resumen, Gráficos y Reportes
 *  ControlCash v2.1 - Sistema Profesional de Control Financiero
 * ============================================================
 */

// ============================================================
//  F7: RESUMEN FINANCIERO con Chart.js
// ============================================================
function toggleDetalleResumen(forceState = null) {
  const panel = document.getElementById("resumen-detalle-panel");
  const btn = document.getElementById("btn-resumen-detalle");
  if (!panel || !btn) return;

  const abierto =
    typeof forceState === "boolean"
      ? forceState
      : !estadoApp.resumenDetalleAbierto;
  estadoApp.resumenDetalleAbierto = abierto;
  panel.classList.toggle("active", abierto);
  btn.textContent = abierto ? "Ocultar ↑" : "Ver →";

  if (abierto) {
    requestAnimationFrame(() => {
      if (chartCategorias) chartCategorias.resize();
      if (chartTendencia) chartTendencia.resize();
    });
  }
}

// [NORMA: ISO 9126 - Funcionalidad/Exactitud] Resumen financiero con indicadores clave de rendimiento e ingresos/gastos
async function cargarResumen() {
  try {
    const resp = await apiRequest("/resumen?dias=30");
    const data = resp.data;
    const categorias = data.por_categoria;

    // Métricas
    const v = data.variacion_vs_anterior_pct || 0;
    const signo = v > 0 ? "+" : "";
    const elPromedio = document.getElementById("metric-promedio");
    const elProyeccion = document.getElementById("metric-proyeccion");
    const elVariacion = document.getElementById("metric-variacion");
    const elMovimientos = document.getElementById("metric-movimientos");

    if (elPromedio)
      elPromedio.textContent = formatMoney(data.promedio_diario_gasto || 0);
    if (elProyeccion)
      elProyeccion.textContent = formatMoney(data.proyeccion_30_dias || 0);
    if (elMovimientos) elMovimientos.textContent = data.total_movimientos || 0;
    if (elVariacion) {
      elVariacion.textContent = `${signo}${v}%`;
      elVariacion.className =
        "mini-metric-value " + (v > 0 ? "negative" : v < 0 ? "positive" : "");
    }

    const resumenVacio = (data.total_movimientos || 0) === 0;
    const emptyState = document.getElementById("resumen-empty-state");
    const btnDetalle = document.getElementById("btn-resumen-detalle");
    if (emptyState) emptyState.style.display = resumenVacio ? "block" : "none";
    if (btnDetalle) {
      btnDetalle.style.display = resumenVacio ? "none" : "inline-flex";
    }
    if (resumenVacio && estadoApp.resumenDetalleAbierto) {
      toggleDetalleResumen(false);
    }

    // Top 3 gastos
    const topContainer = document.getElementById("top-gastos");
    const topList = document.getElementById("top-gastos-list");
    if (topContainer && topList) {
      if (data.top_gastos && data.top_gastos.length > 0) {
        topContainer.style.display = "block";
        topList.innerHTML = data.top_gastos
          .map(
            (g) => `
                    <div class="top-gasto-item">
                        <div class="top-gasto-info">
                            <span>${escapeHtml(g.icono || "📦")}</span>
                            <span>${escapeHtml(g.descripcion || g.categoria)}</span>
                        </div>
                        <span class="top-gasto-monto">${formatMoney(g.monto)}</span>
                    </div>
                `,
          )
          .join("");
      } else {
        topContainer.style.display = "none";
      }
    }

    // Charts con Chart.js
    renderizarCharts(data, categorias);
  } catch (err) {
    mostrarToast("Error", "No se pudo cargar el resumen.", "error");
  }
}

function renderizarCharts(data, categorias) {
  // ── Donut chart por categoría ──
  const ctxDonut = document.getElementById("chart-categorias");
  if (ctxDonut && categorias && categorias.length > 0) {
    const gastos = categorias.filter((c) => c.tipo === "gasto");
    const labels = gastos.map((c) => `${c.icono} ${c.nombre}`);
    const valores = gastos.map((c) => c.total);
    const colores = [
      "#6C63FF",
      "#FF5A5F",
      "#00C48C",
      "#FFB800",
      "#00B4D8",
      "#a855f7",
      "#f97316",
      "#84cc16",
      "#14b8a6",
      "#ec4899",
    ];

    if (chartCategorias) {
      chartCategorias.data.labels = labels;
      chartCategorias.data.datasets[0].data = valores;
      chartCategorias.update();
    } else {
      chartCategorias = new Chart(ctxDonut, {
        type: "doughnut",
        data: {
          labels,
          datasets: [
            {
              data: valores,
              backgroundColor: colores.slice(0, labels.length),
              borderColor: "rgba(255,255,255,0.1)",
              borderWidth: 2,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "bottom",
              labels: {
                color: "rgba(255,255,255,0.8)",
                font: { family: "Inter", size: 11 },
                padding: 12,
              },
            },
            tooltip: {
              callbacks: {
                label: (ctx) =>
                  ` ${ctx.label}: ${formatMoney(ctx.raw)} (${ctx.parsed > 0 ? Math.round((ctx.parsed / ctx.dataset.data.reduce((a, b) => a + b, 0)) * 100) : 0}%)`,
              },
            },
          },
          cutout: "60%",
        },
      });
    }
  } else if (ctxDonut) {
    // Sin datos
    const parent = ctxDonut.parentElement;
    if (parent)
      parent.innerHTML = `<div class="empty-state"><div class="empty-icon">📊</div><p>Aún no hay datos para mostrar</p></div>`;
  }

  // ── Line chart tendencia diaria ──
  const ctxLine = document.getElementById("chart-tendencia");
  if (ctxLine && data.diario && data.diario.length > 0) {
    // Agrupar por día
    const diasMap = {};
    data.diario.forEach((d) => {
      if (!diasMap[d.dia]) diasMap[d.dia] = { ingreso: 0, gasto: 0 };
      diasMap[d.dia][d.tipo] = d.total;
    });
    const dias = Object.keys(diasMap).sort();
    const ingresos = dias.map((d) => diasMap[d].ingreso || 0);
    const gastos = dias.map((d) => diasMap[d].gasto || 0);

    const labelsCortos = dias.map((d) => {
      const fecha = new Date(d + "T00:00:00");
      return fecha.toLocaleDateString("es-MX", {
        day: "numeric",
        month: "short",
      });
    });

    if (chartTendencia) {
      chartTendencia.data.labels = labelsCortos;
      chartTendencia.data.datasets[0].data = gastos;
      chartTendencia.data.datasets[1].data = ingresos;
      chartTendencia.update();
    } else {
      chartTendencia = new Chart(ctxLine, {
        type: "line",
        data: {
          labels: labelsCortos,
          datasets: [
            {
              label: "Gastos",
              data: gastos,
              borderColor: "#FF5A5F",
              backgroundColor: "rgba(255,90,95,0.12)",
              fill: true,
              tension: 0.4,
              pointBackgroundColor: "#FF5A5F",
              pointRadius: 3,
            },
            {
              label: "Ingresos",
              data: ingresos,
              borderColor: "#00C48C",
              backgroundColor: "rgba(0,196,140,0.12)",
              fill: true,
              tension: 0.4,
              pointBackgroundColor: "#00C48C",
              pointRadius: 3,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              labels: {
                color: "rgba(255,255,255,0.8)",
                font: { family: "Inter", size: 11 },
              },
            },
            tooltip: {
              callbacks: {
                label: (ctx) =>
                  ` ${ctx.dataset.label}: ${formatMoney(ctx.raw)}`,
              },
            },
          },
          scales: {
            x: {
              ticks: {
                color: "rgba(255,255,255,0.5)",
                font: { size: 10 },
                maxTicksLimit: 8,
              },
              grid: { color: "rgba(255,255,255,0.05)" },
            },
            y: {
              ticks: {
                color: "rgba(255,255,255,0.5)",
                font: { size: 10 },
                callback: (val) => formatMoney(val),
              },
              grid: { color: "rgba(255,255,255,0.05)" },
            },
          },
        },
      });
    }
  }
}

// ============================================================
//  REPORTES POR PERIODO
// ============================================================
async function cargarReportes(periodo = null) {
  const select = document.getElementById("reportes-periodo");
  const periodoElegido =
    periodo || select?.value || estadoApp.reportesPeriodo || "mensual";

  estadoApp.reportesPeriodo = periodoElegido;
  localStorage.setItem("cc_reportes_periodo", periodoElegido);
  if (select) select.value = periodoElegido;

  try {
    const resp = await apiRequest(`/reportes/resumen?periodo=${periodoElegido}`);
    estadoApp.reportesData = resp.data;
    renderReportes(resp.data);
  } catch (err) {
    mostrarToast("Reportes", "No se pudo cargar el reporte.", "error");
  }
}

function renderReportes(data) {
  const rangoEl = document.getElementById("reportes-rango");
  const ingresosEl = document.getElementById("reportes-total-ingresos");
  const gastosEl = document.getElementById("reportes-total-gastos");
  const movEl = document.getElementById("reportes-total-movimientos");
  const list = document.getElementById("reportes-top-list");

  if (!data) return;

  if (rangoEl && data.rango) {
    rangoEl.textContent = `${data.rango.inicio} → ${data.rango.fin}`;
  }

  const tot = data.totales || {};
  if (ingresosEl) ingresosEl.textContent = formatMoney(tot.ingresos || 0);
  if (gastosEl) gastosEl.textContent = formatMoney(tot.gastos || 0);
  if (movEl) movEl.textContent = tot.movimientos || 0;

  if (!list) return;
  if (!data.top_categorias || data.top_categorias.length === 0) {
    list.innerHTML = `
            <div class="empty-state empty-state--compact">
                <p>Sin categorías con movimientos en este periodo</p>
            </div>
        `;
    return;
  }

  list.innerHTML = data.top_categorias
    .map((cat) => {
      const dir = cat.direccion || "flat";
      const arrow = dir === "up" ? "▲" : dir === "down" ? "▼" : "■";
      const trendClass =
        dir === "up" ? "trend-up" : dir === "down" ? "trend-down" : "trend-flat";
      const variacion = Number(cat.variacion_pct || 0);
      const signo = variacion > 0 ? "+" : variacion < 0 ? "-" : "";

      return `
            <div class="reporte-item">
                <div class="reporte-info">
                    <span class="reporte-icon">${escapeHtml(cat.icono || "📦")}</span>
                    <div>
                        <div class="reporte-nombre">${escapeHtml(cat.nombre || "Categoría")}</div>
                        <div class="reporte-total">${formatMoney(cat.total || 0)}</div>
                    </div>
                </div>
                <div class="reporte-trend ${trendClass}">
                    <span>${arrow}</span>
                    <span>${signo}${Math.abs(variacion)}%</span>
                </div>
            </div>
        `;
    })
    .join("");
}

const _emojiPdfCache = new Map();

function emojiToCodepoints(emoji) {
  return Array.from(String(emoji || ""))
    .map((ch) => ch.codePointAt(0).toString(16))
    .join("-");
}

async function cargarEmojiPngDataUrl(emoji) {
  const limpio = String(emoji || "").trim();
  if (!limpio) return null;
  if (_emojiPdfCache.has(limpio)) return _emojiPdfCache.get(limpio);

  const codepoints = emojiToCodepoints(limpio);
  if (!codepoints) return null;

  const url = `https://twemoji.maxcdn.com/v/latest/72x72/${codepoints}.png`;
  try {
    const resp = await fetch(url);
    if (!resp.ok) return null;
    const blob = await resp.blob();
    const dataUrl = await new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = () => resolve(null);
      reader.readAsDataURL(blob);
    });
    _emojiPdfCache.set(limpio, dataUrl);
    return dataUrl;
  } catch (_) {
    return null;
  }
}

async function precargarIconosReporte(categorias) {
  const mapa = new Map();
  const uniques = Array.from(
    new Set(
      (categorias || [])
        .map((c) => String(c?.icono || "").trim())
        .filter(Boolean),
    ),
  ).slice(0, 20);

  for (const icono of uniques) {
    const dataUrl = await cargarEmojiPngDataUrl(icono);
    if (dataUrl) mapa.set(icono, dataUrl);
  }
  return mapa;
}

async function exportarReportePDF() {
  const data = estadoApp.reportesData;
  if (!data) {
    mostrarToast("Reportes", "Primero carga un reporte.", "alerta");
    return;
  }

  const jsPDF = window.jspdf?.jsPDF;
  if (!jsPDF) {
    mostrarToast("Reportes", "jsPDF no disponible.", "error");
    return;
  }

  const doc = new jsPDF();
  doc.setFontSize(14);
  doc.text("ControlCash - Reporte", 14, 18);
  doc.setFontSize(10);
  doc.text(
    `Periodo: ${data.periodo_label || data.periodo} (${data.rango?.inicio} a ${data.rango?.fin})`,
    14,
    26,
  );

  const tot = data.totales || {};
  doc.text(
    `Ingresos: ${formatMoney(tot.ingresos || 0)}  |  Gastos: ${formatMoney(tot.gastos || 0)}  |  Movimientos: ${tot.movimientos || 0}`,
    14,
    34,
  );

  const categorias = data.top_categorias || [];
  const iconosMap = await precargarIconosReporte(categorias);
  const rows = categorias.map((c) => [
    `${c.nombre || ""}`,
    formatMoney(c.total || 0),
    `${c.variacion_pct || 0}%`,
    formatMoney(c.variacion_monto || 0),
  ]);

  const monedaEtiqueta = obtenerEtiquetaMoneda();

  if (doc.autoTable) {
    doc.autoTable({
      startY: 42,
      head: [["Categoría", "Total", "Variación %", `Variación ${monedaEtiqueta}`]],
      body: rows,
      columnStyles: {
        0: { cellPadding: { left: 7 } },
      },
      didDrawCell: (dataCell) => {
        if (dataCell.section !== "body" || dataCell.column.index !== 0) return;
        const icono = categorias[dataCell.row.index]?.icono;
        const img = iconosMap.get(String(icono || "").trim());
        if (!img) return;
        const size = 4.2;
        const x = dataCell.cell.x + 1.4;
        const y = dataCell.cell.y + (dataCell.cell.height - size) / 2;
        try {
          doc.addImage(img, "PNG", x, y, size, size);
        } catch (_) {}
      },
    });
  } else {
    let y = 44;
    doc.text("Top categorías:", 14, y);
    y += 6;
    rows.forEach((r) => {
      doc.text(`${r[0]} | ${r[1]} | ${r[2]} | ${r[3]}`, 14, y);
      y += 5;
    });
  }

  const fecha = new Date().toISOString().split("T")[0];
  doc.save(`controlcash_reporte_${fecha}.pdf`);
}

function exportarReporteExcel() {
  const data = estadoApp.reportesData;
  if (!data) {
    mostrarToast("Reportes", "Primero carga un reporte.", "alerta");
    return;
  }
  if (!window.XLSX) {
    mostrarToast("Reportes", "XLSX no disponible.", "error");
    return;
  }

  const monedaEtiqueta = obtenerEtiquetaMoneda();
  const rows = [
    ["Categoría", "Total", "Variación %", `Variación ${monedaEtiqueta}`],
    ...(data.top_categorias || []).map((c) => [
      `${c.icono || ""} ${c.nombre || ""}`,
      c.total || 0,
      c.variacion_pct || 0,
      c.variacion_monto || 0,
    ]),
  ];

  const wb = XLSX.utils.book_new();
  const ws = XLSX.utils.aoa_to_sheet(rows);
  XLSX.utils.book_append_sheet(wb, ws, "Reporte");

  const fecha = new Date().toISOString().split("T")[0];
  XLSX.writeFile(wb, `controlcash_reporte_${fecha}.xlsx`);
}

document.addEventListener("DOMContentLoaded", () => {
  const selectReportes = document.getElementById("reportes-periodo");
  if (selectReportes) {
    selectReportes.value = estadoApp.reportesPeriodo || "mensual";
    selectReportes.addEventListener("change", () => {
      cargarReportes(selectReportes.value);
    });
  }

  const btnPdf = document.getElementById("btn-exportar-pdf");
  if (btnPdf) {
    btnPdf.addEventListener("click", exportarReportePDF);
  }

  const btnExcel = document.getElementById("btn-exportar-excel");
  if (btnExcel) {
    btnExcel.addEventListener("click", exportarReporteExcel);
  }
});
