/**
 * ============================================================
 *  CAPA DE PRESENTACION - Gemini Live API (Voz en Vivo)
 *  ControlCash v2.3 - Sistema Profesional de Control Financiero
 *  Usa API key directa con WebSocket (enfoque oficial v1beta)
 *  Modelo: gemini-3.1-flash-live-preview
 *  Normas: ISO/IEC 25000 (Usabilidad, Calidad), ISO 14598 (UX)
 * ============================================================
 */

// ── Constantes de Audio (coinciden con ejemplo oficial) ──
const LIVE_SEND_SAMPLE_RATE = 16000;
const LIVE_RECEIVE_SAMPLE_RATE = 24000;
const LIVE_CHANNELS = 1;

// ── Estado global del módulo ──
let liveSocket = null;
let liveAudioContext = null;
let liveMicrophoneStream = null;
let liveAudioProcessor = null;
let liveAudioAnalyser = null;
let liveIsMuted = false;
let liveSetupCompleted = false;

// Cola para la reproducción de audio fluida
let livePlaybackQueue = [];
let liveIsPlaying = false;
let liveNextPlaybackTime = 0;
let liveAnimationRequest = null;

/**
 * 1. ABRIR MODAL PRINCIPAL
 */
function abrirModalChatLive() {
  cerrarModal("modal-chat");

  const modal = document.getElementById("modal-chat-live");
  if (modal) modal.classList.add("active");

  actualizarEstadoUI("disconnected", "Desconectado");
  resetearTranscripcion(
    "Pulsa 'Iniciar' para comenzar la conversación por voz con Gemini..."
  );

  document.getElementById("btn-live-hangup").style.display = "none";
  document.getElementById("btn-live-start").style.display = "inline-flex";
  document.getElementById("btn-live-start").disabled = false;
  document.getElementById("btn-live-mute").disabled = true;
  document.getElementById("btn-live-mute").textContent = "🎤 Silenciar";
  liveIsMuted = false;
}

/**
 * 2. CERRAR / FINALIZAR CHAT EN VIVO
 */
function cerrarGeminiLive() {
  detenerTransmisionVoz();

  const modal = document.getElementById("modal-chat-live");
  if (modal) modal.classList.remove("active");

  setTimeout(() => {
    abrirModalChat();
  }, 350);
}

/**
 * 3. CONTROLADOR DE ESTADO UI
 */
function actualizarEstadoUI(estado, texto) {
  const dot = document.getElementById("live-status-dot");
  const txt = document.getElementById("live-status-text");

  if (!dot || !txt) return;

  txt.textContent = texto;
  dot.className = "live-status-dot";

  if (estado === "connecting") {
    dot.classList.add("connecting");
  } else if (estado === "active") {
    dot.classList.add("active");
  }
}

function resetearTranscripcion(msg) {
  const t = document.getElementById("live-transcript-body");
  if (t) t.textContent = msg;
}

function agregarTextoTranscripcion(sender, texto) {
  const t = document.getElementById("live-transcript-body");
  if (!t) return;

  if (
    t.textContent.includes("Pulsa 'Iniciar'") ||
    t.textContent.includes("Conectando...") ||
    t.textContent.includes("Solicitando")
  ) {
    t.innerHTML = "";
  }

  const prefix = sender === "user" ? "🗣️ Tú: " : "🤖 Gemini: ";
  const p = document.createElement("p");
  p.style.margin = "4px 0";
  p.innerHTML = `<strong>${prefix}</strong> ${escapeHtml(texto)}`;
  t.appendChild(p);
  t.scrollTop = t.scrollHeight;
}

/**
 * 4. INICIAR CONEXIÓN — Obtener API key y conectar WebSocket
 */
async function activarGeminiLiveConectando() {
  actualizarEstadoUI("connecting", "Conectando...");
  resetearTranscripcion("Solicitando configuración al servidor...");

  document.getElementById("btn-live-start").disabled = true;

  try {
    // Pedir la API key y config al backend (requiere auth)
    const resp = await apiRequest("/chat/live/config");
    const config = resp.data;

    if (!config?.key) {
      throw new Error("El servidor no devolvió una API key válida.");
    }

    resetearTranscripcion("Estableciendo canal WebSocket con Gemini Live...");
    await iniciarConexionWebSocket(config.key, config.model, config.ws_url);
  } catch (err) {
    actualizarEstadoUI("disconnected", "Error de conexión");
    mostrarToast(
      "Error Gemini Live",
      err.mensaje || err.message || "No se pudo iniciar la sesión en vivo.",
      "error"
    );
    resetearTranscripcion(
      "Fallo al conectar: " +
        (err.mensaje || err.message || "Error del servidor.")
    );
    document.getElementById("btn-live-start").disabled = false;
  }
}

/**
 * 5. INICIALIZAR WEBSOCKET DE GEMINI LIVE (v1beta, API key directo)
 */
async function iniciarConexionWebSocket(apiKey, model, wsBaseUrl) {
  try {
    liveSetupCompleted = false;

    // URL oficial: wss://...BidiGenerateContent?key=API_KEY
    const wsUrl = `${wsBaseUrl}?key=${apiKey}`;

    liveSocket = new WebSocket(wsUrl);

    liveSocket.onopen = () => {
      console.log("[Gemini Live] WebSocket conectado, enviando setup...");
      enviarConfiguracionInicial(model);
    };

    liveSocket.onmessage = async (event) => {
      await procesarMensajeServidorLive(event.data);
    };

    liveSocket.onerror = (e) => {
      console.error("[Gemini Live] Error WebSocket:", e);
      mostrarToast(
        "Error de Red",
        "Fallo en el canal WebSocket de Gemini Live.",
        "error"
      );
      detenerTransmisionVoz();
    };

    liveSocket.onclose = (e) => {
      console.log("[Gemini Live] WebSocket cerrado:", e.code, e.reason);
      if (liveSetupCompleted) {
        detenerTransmisionVoz();
      }
    };
  } catch (err) {
    throw new Error("No se pudo instanciar el WebSocket: " + err.message);
  }
}

/**
 * 6. ENVIAR SETUP MESSAGE (coincide con el protocolo oficial v1beta)
 *    Basado en el ejemplo oficial de google-genai SDK
 */
function enviarConfiguracionInicial(model) {
  if (!liveSocket || liveSocket.readyState !== WebSocket.OPEN) return;

  const setupMsg = {
    setup: {
      model: model || "models/gemini-3.1-flash-live-preview",
      generationConfig: {
        responseModalities: ["AUDIO"],
        speechConfig: {
          voiceConfig: {
            prebuiltVoiceConfig: {
              voiceName: "Zephyr",
            },
          },
        },
        // ✅ Thinking/razonamiento: el modelo razona antes de responder
        // Mejora la calidad del análisis financiero
        thinkingConfig: {
          includeThoughts: false, // Las thoughts no se envían por audio, ahorran tokens
          thinkingBudget: 1024,   // Tokens de razonamiento interno
        },
      },
      systemInstruction: {
        parts: [
          {
            text: "Eres un asesor financiero por voz en tiempo real para ControlCash. Tu rol es responder consultas utilizando las herramientas provistas. Responde siempre de forma clara, directa y por voz en español. Explica las cifras de forma amigable. Antes de responder, analiza bien los datos para dar consejos precisos.",
          },
        ],
      },
      tools: [
        {
          functionDeclarations: [
            {
              name: "obtener_balance_actual",
              description: "Devuelve el balance financiero actual del usuario: ingresos totales, gastos totales y balance neto disponible.",
            },
            {
              name: "obtener_resumen_30_dias",
              description: "Devuelve métricas de rendimiento financiero de los últimos 30 días: promedio diario de gasto, proyección mensual y variación vs mes anterior.",
            },
            {
              name: "obtener_movimientos_recientes",
              description: "Obtiene la lista de los últimos movimientos de ingreso o gasto registrados.",
              parameters: {
                type: "OBJECT",
                properties: {
                  limite: { type: "INTEGER", description: "Número de movimientos a obtener (máx 20)" },
                  tipo: { type: "STRING", enum: ["todos", "ingreso", "gasto"], description: "Filtrar por tipo" }
                }
              }
            },
            {
              name: "obtener_presupuestos_mes",
              description: "Obtiene los presupuestos mensuales configurados y su nivel de ejecución actual: cuánto se ha gastado vs el límite fijado por categoría.",
              parameters: {
                type: "OBJECT",
                properties: {
                  mes: { type: "STRING", description: "Mes en formato YYYY-MM-DD (opcional, usa el mes actual si se omite)" }
                }
              }
            },
          ],
        },
      ],
    },
  };

  liveSocket.send(JSON.stringify(setupMsg));
  console.log("[Gemini Live] Setup enviado (con thinkingConfig).");
}

/**
 * 6b. HELPERS PARA INDICADORES VISUALES
 */
function mostrarIndicadorHerramienta(nombreFn) {
  const toolNames = {
    obtener_balance_actual: "Consultando balance...",
    obtener_resumen_30_dias: "Consultando resumen 30 días...",
    obtener_movimientos_recientes: "Consultando movimientos recientes...",
    obtener_presupuestos_mes: "Consultando presupuestos del mes...",
  };
  const texto = toolNames[nombreFn] || `Ejecutando: ${nombreFn}...`;
  const el = document.getElementById("live-tool-indicator");
  const textEl = document.getElementById("live-tool-text");
  if (el && textEl) {
    textEl.textContent = texto;
    el.style.display = "flex";
  }
  console.log(`[Gemini Live] Tool call: ${nombreFn}`);
}

function ocultarIndicadorHerramienta() {
  const el = document.getElementById("live-tool-indicator");
  if (el) el.style.display = "none";
}

function mostrarIndicadorRazonamiento(visible) {
  const el = document.getElementById("live-thinking-indicator");
  if (el) el.style.display = visible ? "flex" : "none";
}

/**
 * 7. ENTRADA DE MICRÓFONO (AudioWorkletNode → PCM 16kHz Int16)
 *    Usa AudioWorkletNode (moderno) en lugar del deprecated ScriptProcessorNode.
 *    Envía chunks como base64 via realtimeInput.audio (protocolo actual).
 */
async function iniciarCapturaAudioMicrofono() {
  try {
    liveMicrophoneStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: LIVE_CHANNELS,
        sampleRate: LIVE_SEND_SAMPLE_RATE,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });

    liveAudioContext = new (window.AudioContext || window.webkitAudioContext)({
      sampleRate: LIVE_SEND_SAMPLE_RATE,
    });

    // Analizador para las ondas animadas
    liveAudioAnalyser = liveAudioContext.createAnalyser();
    liveAudioAnalyser.fftSize = 64;

    const source = liveAudioContext.createMediaStreamSource(
      liveMicrophoneStream
    );
    source.connect(liveAudioAnalyser);

    // ✅ AudioWorkletNode reemplaza al deprecated ScriptProcessorNode
    try {
      // Determinar la ruta del worklet relativa a la página actual
      const workletUrl = new URL('js/pcm-processor.js', window.location.href).href;
      await liveAudioContext.audioWorklet.addModule(workletUrl);

      liveAudioProcessor = new AudioWorkletNode(liveAudioContext, 'pcm-processor');

      // Recibir buffers Float32 desde el worklet y enviar al WebSocket
      liveAudioProcessor.port.onmessage = (event) => {
        if (liveIsMuted) return;
        if (!liveSocket || liveSocket.readyState !== WebSocket.OPEN) return;
        if (!liveSetupCompleted) return;

        const float32Data = event.data; // Float32Array del worklet
        const pcmBuffer = floatTo16BitPCM(float32Data);
        enviarChunkAudioGemini(pcmBuffer);
      };

      source.connect(liveAudioProcessor);
      liveAudioProcessor.connect(liveAudioContext.destination);
      console.log('[Gemini Live] AudioWorkletNode activo.');

    } catch (workletErr) {
      // Fallback: ScriptProcessorNode si el worklet no carga (poco probable)
      console.warn('[Gemini Live] AudioWorklet falló, usando ScriptProcessor como fallback:', workletErr);
      const bufferSize = 4096;
      liveAudioProcessor = liveAudioContext.createScriptProcessor(bufferSize, 1, 1);
      source.connect(liveAudioProcessor);
      liveAudioProcessor.connect(liveAudioContext.destination);
      liveAudioProcessor.onaudioprocess = (e) => {
        if (liveIsMuted) return;
        if (!liveSocket || liveSocket.readyState !== WebSocket.OPEN) return;
        if (!liveSetupCompleted) return;
        const inputData = e.inputBuffer.getChannelData(0);
        const pcmBuffer = floatTo16BitPCM(inputData);
        enviarChunkAudioGemini(pcmBuffer);
      };
    }

    // Actualizar UI
    actualizarEstadoUI("active", "Escuchando...");
    animarEsferaNebulosa("listening");
    resetearTranscripcion(
      "¡Conectado! Habla por el micrófono para conversar con Gemini Live..."
    );

    document.getElementById("btn-live-start").disabled = false;
    document.getElementById("btn-live-start").style.display = "none";
    document.getElementById("btn-live-hangup").style.display = "inline-flex";
    document.getElementById("btn-live-mute").disabled = false;

    // Arrancar animación de ondas
    arrancarAnimacionVisualizador();
  } catch (err) {
    console.error("[Gemini Live] Error micrófono:", err);
    mostrarToast(
      "Permiso de Micrófono",
      "No se pudo acceder al micrófono para el chat en vivo.",
      "alerta"
    );
    detenerTransmisionVoz();
  }
}

/**
 * 8. CODIFICAR FLOAT32 → INT16 PCM
 */
function floatTo16BitPCM(input) {
  const buffer = new ArrayBuffer(input.length * 2);
  const view = new DataView(buffer);
  for (let i = 0; i < input.length; i++) {
    const s = Math.max(-1, Math.min(1, input[i]));
    view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
  return buffer;
}

/**
 * 9. ENVIAR CHUNK DE AUDIO — formato nuevo (realtimeInput.audio)
 *    "realtime_input.media_chunks" está deprecado desde la API v1beta actual.
 *    El formato correcto es realtimeInput: { audio: { data, mimeType } }
 */
function enviarChunkAudioGemini(pcmBuffer) {
  if (!liveSocket || liveSocket.readyState !== WebSocket.OPEN) return;

  // Convertir ArrayBuffer a base64
  const bytes = new Uint8Array(pcmBuffer);
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  const base64Data = window.btoa(binary);

  // ✅ Formato nuevo: realtimeInput.audio (no mediaChunks)
  const audioPayload = {
    realtimeInput: {
      audio: {
        data: base64Data,
        mimeType: `audio/pcm;rate=${LIVE_SEND_SAMPLE_RATE}`,
      },
    },
  };

  liveSocket.send(JSON.stringify(audioPayload));
}

/**
 * 10. SILENCIAR MICRÓFONO
 */
function toggleMuteMicrofono() {
  liveIsMuted = !liveIsMuted;
  const btn = document.getElementById("btn-live-mute");
  if (btn) {
    btn.textContent = liveIsMuted ? "🎙️ Activar Mic" : "🎤 Silenciar";
    btn.className = liveIsMuted
      ? "glass-btn glass-btn--success live-btn-mute"
      : "glass-btn glass-btn--warning live-btn-mute";
  }
  mostrarToast(
    "Micrófono",
    liveIsMuted ? "Micrófono silenciado." : "Micrófono activado.",
    "info"
  );
}

/**
 * 11. PROCESAR RESPUESTA DEL SERVIDOR DE GEMINI LIVE
 *     Maneja: setupComplete, audio, texto, toolCall, thinking
 */
async function procesarMensajeServidorLive(data) {
  try {
    let msg;
    if (typeof data === "string") {
      msg = JSON.parse(data);
    } else if (data instanceof Blob) {
      const text = await data.text();
      msg = JSON.parse(text);
    } else {
      return;
    }

    // 0. Setup completado
    if (msg.setupComplete) {
      console.log("[Gemini Live] Setup completado, iniciando micrófono...");
      liveSetupCompleted = true;
      iniciarCapturaAudioMicrofono();
      return;
    }

    // 1. Audio + texto entrante del modelo (serverContent.modelTurn.parts)
    const parts = msg.serverContent?.modelTurn?.parts || [];
    let tieneAudio = false;

    parts.forEach((part) => {
      // Audio: inlineData
      if (part.inlineData && part.inlineData.mimeType?.startsWith("audio/")) {
        tieneAudio = true;
        ocultarIndicadorHerramienta();
        mostrarIndicadorRazonamiento(false);
        const rawAudio = base64ToArrayBuffer(part.inlineData.data);
        encolarAudioParaReproduccion(rawAudio);
      }
      // Formato alternativo de audio
      if (part.mimeType && part.mimeType.startsWith("audio/") && part.data) {
        tieneAudio = true;
        const rawAudio = base64ToArrayBuffer(part.data);
        encolarAudioParaReproduccion(rawAudio);
      }
      // Transcripción de texto del modelo
      if (part.text && !part.thought) {
        agregarTextoTranscripcion("bot", part.text);
      }
      // Thoughts/razonamiento interno (si includeThoughts=true)
      if (part.thought && part.text) {
        console.log("[Gemini Live] Thought:", part.text.substring(0, 80));
        mostrarIndicadorRazonamiento(true);
      }
    });

    // Indicador de razonamiento mientras el modelo está procesando pero no habla aún
    if (parts.length > 0 && !tieneAudio) {
      mostrarIndicadorRazonamiento(true);
      animarEsferaNebulosa("listening");
    } else if (tieneAudio) {
      mostrarIndicadorRazonamiento(false);
      animarEsferaNebulosa("speaking");
    }

    // 2. Turn complete
    if (msg.serverContent?.turnComplete) {
      console.log("[Gemini Live] Turn complete.");
      mostrarIndicadorRazonamiento(false);
      ocultarIndicadorHerramienta();
      animarEsferaNebulosa("listening");
    }

    // 3. Tool Calling — mostrar indicador antes de ejecutar
    const functionCalls = msg.toolCall?.functionCalls || [];
    if (functionCalls.length > 0) {
      // Mostrar indicador para la primera herramienta llamada
      mostrarIndicadorHerramienta(functionCalls[0].name);
      mostrarIndicadorRazonamiento(false);
      await procesarToolCallsLive(functionCalls);
      // El indicador se oculta cuando llegue el audio de respuesta
    }
  } catch (err) {
    console.error("[Gemini Live] Error procesando mensaje:", err);
  }
}

/**
 * 12. DECODIFICAR BASE64 → ArrayBuffer
 */
function base64ToArrayBuffer(base64) {
  const binaryString = window.atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
}

/**
 * 13. ENCOLAR Y REPRODUCIR AUDIO DE SALIDA (24kHz PCM Int16)
 *     Gemini Live envía audio PCM a 24000Hz como el ejemplo oficial
 */
function encolarAudioParaReproduccion(arrayBuffer) {
  const int16Array = new Int16Array(arrayBuffer);
  const float32Array = new Float32Array(int16Array.length);

  for (let i = 0; i < int16Array.length; i++) {
    float32Array[i] = int16Array[i] / 32768.0;
  }

  livePlaybackQueue.push(float32Array);

  if (!liveIsPlaying) {
    reproducirSiguienteBloqueAudio();
  }
}

function reproducirSiguienteBloqueAudio() {
  if (livePlaybackQueue.length === 0) {
    liveIsPlaying = false;
    return;
  }

  if (!liveAudioContext) return;

  liveIsPlaying = true;
  const rawBlock = livePlaybackQueue.shift();

  // Buffer a 24000Hz — frecuencia de retorno estándar de Gemini Live
  const sampleRate = LIVE_RECEIVE_SAMPLE_RATE;
  const audioBuffer = liveAudioContext.createBuffer(
    1,
    rawBlock.length,
    sampleRate
  );
  audioBuffer.getChannelData(0).set(rawBlock);

  const source = liveAudioContext.createBufferSource();
  source.buffer = audioBuffer;
  source.connect(liveAudioContext.destination);

  // También conectar al analizador para animar ondas con la voz del bot
  if (liveAudioAnalyser) {
    source.connect(liveAudioAnalyser);
  }

  const now = liveAudioContext.currentTime;
  if (liveNextPlaybackTime < now) {
    liveNextPlaybackTime = now;
  }

  source.start(liveNextPlaybackTime);
  liveNextPlaybackTime += audioBuffer.duration;

  source.onended = () => {
    reproducirSiguienteBloqueAudio();
  };
}

/**
 * 14. EJECUTAR LLAMADAS A FUNCIONES LOCALES (Tool Calling)
 */
async function procesarToolCallsLive(calls) {
  const responses = [];

  for (const call of calls) {
    const fnName = call.name;
    const callId = call.id;
    const args = call.args || {};

    let output = {};

    try {
      if (fnName === "obtener_balance_actual") {
        const resp = await apiRequest("/balance");
        output = {
          total_ingresos: parseFloat(resp.data?.total_ingresos || 0),
          total_gastos: parseFloat(resp.data?.total_gastos || 0),
          balance: parseFloat(resp.data?.balance || 0),
          total_movimientos: parseInt(resp.data?.total_movimientos || 0),
        };
      } else if (fnName === "obtener_resumen_30_dias") {
        const resp = await apiRequest("/resumen?dias=30");
        output = {
          promedio_diario_gasto: parseFloat(
            resp.data?.promedio_diario_gasto || 0
          ),
          variacion_vs_anterior_pct: parseFloat(
            resp.data?.variacion_vs_anterior_pct || 0
          ),
          proyeccion_30_dias: parseFloat(resp.data?.proyeccion_30_dias || 0),
          total_movimientos: parseInt(resp.data?.total_movimientos || 0),
        };
      } else if (fnName === "obtener_presupuestos_mes") {
        const mes = args.mes || new Date().toISOString().substring(0, 8) + '01';
        const resp = await apiRequest(`/presupuestos?mes=${mes}`);
        const presup = Array.isArray(resp.data) ? resp.data : (resp.data?.presupuestos || []);
        output = {
          presupuestos: presup.map(p => ({
            categoria: p.categoria_nombre || p.nombre || p.categoria,
            limite: parseFloat(p.limite || p.monto_limite || 0),
            gastado: parseFloat(p.gastado || p.monto_gastado || 0),
            porcentaje: parseFloat(p.porcentaje || 0),
            excedido: (p.excedido === true) || (parseFloat(p.porcentaje || 0) >= 100),
          }))
        };
      } else if (fnName === "obtener_movimientos_recientes") {
        const limit = args.limite || 10;
        const tipo = args.tipo || "todos";
        let endpoint = `/movimientos?page=1&page_size=${limit}`;
        if (tipo !== "todos") endpoint += `&tipo=${tipo}`;

        const resp = await apiRequest(endpoint);
        const movs = Array.isArray(resp.data)
          ? resp.data
          : resp.data?.items || [];

        output = {
          movimientos: movs.slice(0, limit).map((m) => ({
            monto: parseFloat(m.monto || 0),
            tipo: m.tipo,
            categoria: m.categoria_nombre,
            descripcion: m.descripcion,
            fecha: m.fecha ? m.fecha.substring(0, 10) : "",
          })),
        };
      } else {
        output = { error: "Tool no soportada en vivo" };
      }
    } catch (err) {
      output = { error: "Fallo al consultar base de datos local." };
    }

    responses.push({
      name: fnName,
      id: callId,
      response: {
        output: output,
      },
    });
  }

  // Devolver respuestas al WebSocket
  if (liveSocket && liveSocket.readyState === WebSocket.OPEN) {
    const payload = {
      toolResponse: {
        functionResponses: responses,
      },
    };
    liveSocket.send(JSON.stringify(payload));
  }
}

/**
 * 15. DETENER TODO Y HACER LIMPIEZA
 */
/**
 * ANIMAR ESFERA NEBULOSA según el estado de la sesión
 */
function animarEsferaNebulosa(estado) {
  const sphere = document.getElementById("live-nebula-sphere");
  if (!sphere) return;
  sphere.classList.remove("is-listening", "is-speaking");
  if (estado === "listening") sphere.classList.add("is-listening");
  else if (estado === "speaking") sphere.classList.add("is-speaking");
}

function detenerTransmisionVoz() {
  // 1. Cerrar WebSocket
  if (liveSocket) {
    try {
      liveSocket.close();
    } catch (_) {}
    liveSocket = null;
  }

  // 2. Detener Micrófono
  if (liveMicrophoneStream) {
    liveMicrophoneStream.getTracks().forEach((track) => track.stop());
    liveMicrophoneStream = null;
  }

  // 3. Detener procesadores de Audio
  if (liveAudioProcessor) {
    try {
      liveAudioProcessor.disconnect();
    } catch (_) {}
    liveAudioProcessor = null;
  }

  if (liveAudioContext) {
    try {
      liveAudioContext.close();
    } catch (_) {}
    liveAudioContext = null;
  }

  liveAudioAnalyser = null;
  liveSetupCompleted = false;

  // 4. Limpiar animaciones
  if (liveAnimationRequest) {
    cancelAnimationFrame(liveAnimationRequest);
    liveAnimationRequest = null;
  }

  // Resetear cola de audio
  livePlaybackQueue = [];
  liveIsPlaying = false;
  liveNextPlaybackTime = 0;

  // Actualizar UI
  actualizarEstadoUI("disconnected", "Desconectado");
  animarEsferaNebulosa("");

  const btnHang = document.getElementById("btn-live-hangup");
  if (btnHang) btnHang.style.display = "none";
  const btnStart = document.getElementById("btn-live-start");
  if (btnStart) {
    btnStart.style.display = "inline-flex";
    btnStart.disabled = false;
  }
  const btnMute = document.getElementById("btn-live-mute");
  if (btnMute) btnMute.disabled = true;

  // Apagar barras del visualizador
  const bars = document.querySelectorAll(".wave-bar");
  bars.forEach((bar) => {
    bar.style.height = "10px";
  });
}

/**
 * 16. ANIMACIÓN PREMIUM DEL VISUALIZADOR DE ONDAS SONORAS
 */
function arrancarAnimacionVisualizador() {
  const bars = document.querySelectorAll(".wave-bar");
  if (bars.length === 0) return;

  const dataArray = new Uint8Array(32);

  function animar() {
    if (!liveAudioAnalyser) return;

    liveAnimationRequest = requestAnimationFrame(animar);
    liveAudioAnalyser.getByteFrequencyData(dataArray);

    bars.forEach((bar, i) => {
      const val = dataArray[i % 16] || 0;
      let height = 10 + (val / 255) * 55;

      // Micro-movimiento ambiental cuando está en silencio pero conectado
      if (
        val === 0 &&
        liveSocket &&
        liveSocket.readyState === WebSocket.OPEN
      ) {
        height = 10 + Math.sin(Date.now() * 0.004 + i) * 3;
      } else if (val === 0) {
        height = 10;
      }

      bar.style.height = `${height}px`;
    });
  }

  animar();
}
