/**
 * PCM Audio Worklet Processor para Gemini Live
 * Captura audio PCM Float32 y lo envía al hilo principal
 * para convertirlo a Int16 y transmitirlo al WebSocket.
 */
class PCMProcessor extends AudioWorkletProcessor {
  process(inputs) {
    const input = inputs[0];
    if (input && input.length > 0 && input[0].length > 0) {
      // Enviar el canal 0 (mono) al hilo principal
      this.port.postMessage(input[0]);
    }
    return true; // Mantener el procesador vivo
  }
}

registerProcessor("pcm-processor", PCMProcessor);
