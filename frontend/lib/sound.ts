// Sonidos de la cartelera:
//  • playWhistle()    → silbato de árbitro sintetizado (inicio/HT/2T/final)
//  • playGoalCrowd()  → reproduce /public/goal.mp3 (festejo de gol)
//  • unlockAudio()    → desbloquea el audio tras la 1ª interacción del usuario

let ctx: AudioContext | null = null;

// Audio de gol: se decodifica el MP3 a un AudioBuffer y se reproduce por el
// mismo AudioContext del silbato (más confiable que <audio>, suena también con
// la pestaña en segundo plano una vez desbloqueado el contexto).
let goalBuffer: AudioBuffer | null = null;
let goalBufferLoading: Promise<AudioBuffer | null> | null = null;

function loadGoalBuffer(ac: AudioContext): Promise<AudioBuffer | null> {
  if (goalBuffer) return Promise.resolve(goalBuffer);
  if (!goalBufferLoading) {
    goalBufferLoading = fetch("/goal.mp3")
      .then((r) => r.arrayBuffer())
      .then(
        (data) =>
          new Promise<AudioBuffer>((res, rej) =>
            ac.decodeAudioData(data, res, rej)
          )
      )
      .then((b) => {
        goalBuffer = b;
        return b;
      })
      .catch(() => null);
  }
  return goalBufferLoading;
}

// Fallback con <audio> por si la decodificación fallara en algún navegador.
let goalAudio: HTMLAudioElement | null = null;
function getGoalAudio(): HTMLAudioElement | null {
  if (typeof window === "undefined") return null;
  if (!goalAudio) {
    goalAudio = new Audio("/goal.mp3");
    goalAudio.preload = "auto";
  }
  return goalAudio;
}

function getCtx(): AudioContext | null {
  if (typeof window === "undefined") return null;
  if (!ctx) {
    const AC =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext: typeof AudioContext })
        .webkitAudioContext;
    if (!AC) return null;
    ctx = new AC();
  }
  return ctx;
}

export function unlockAudio(): void {
  const ac = getCtx();
  if (ac) {
    if (ac.state === "suspended") ac.resume().catch(() => {});
    loadGoalBuffer(ac); // precarga/decodifica el MP3 del gol
  }
}

function noiseBuffer(ac: AudioContext, seconds: number): AudioBuffer {
  const len = Math.max(1, Math.floor(ac.sampleRate * seconds));
  const buf = ac.createBuffer(1, len, ac.sampleRate);
  const data = buf.getChannelData(0);
  for (let i = 0; i < len; i++) data[i] = Math.random() * 2 - 1;
  return buf;
}

/** Silbato de árbitro: tono agudo con "warble" del balín + soplo de aire. */
export function playWhistle(): void {
  const ac = getCtx();
  if (!ac) return;
  if (ac.state === "suspended") ac.resume().catch(() => {});
  const now = ac.currentTime;
  const dur = 0.55;

  // Tono principal con vibrato rápido (el balín del silbato)
  const osc = ac.createOscillator();
  osc.type = "triangle";
  osc.frequency.value = 2300;
  const lfo = ac.createOscillator();
  lfo.type = "sine";
  lfo.frequency.value = 28;
  const lfoGain = ac.createGain();
  lfoGain.gain.value = 140; // profundidad del warble
  lfo.connect(lfoGain);
  lfoGain.connect(osc.frequency);

  const g = ac.createGain();
  g.gain.setValueAtTime(0.0001, now);
  g.gain.linearRampToValueAtTime(0.2, now + 0.02);
  g.gain.setValueAtTime(0.2, now + dur - 0.1);
  g.gain.exponentialRampToValueAtTime(0.0001, now + dur);
  osc.connect(g);
  g.connect(ac.destination);

  // Soplo de aire (ruido filtrado agudo)
  const ns = ac.createBufferSource();
  ns.buffer = noiseBuffer(ac, dur);
  const bp = ac.createBiquadFilter();
  bp.type = "bandpass";
  bp.frequency.value = 2600;
  bp.Q.value = 1.2;
  const ng = ac.createGain();
  ng.gain.setValueAtTime(0.035, now);
  ng.gain.exponentialRampToValueAtTime(0.0001, now + dur);
  ns.connect(bp);
  bp.connect(ng);
  ng.connect(ac.destination);

  osc.start(now);
  osc.stop(now + dur);
  lfo.start(now);
  lfo.stop(now + dur);
  ns.start(now);
  ns.stop(now + dur);
}

/** Festejo de gol: reproduce el MP3 vía Web Audio (suena aun en segundo plano).
 *  Si la decodificación no estuviera lista, cae al elemento <audio>. */
export function playGoalCrowd(): void {
  const ac = getCtx();
  if (!ac) {
    fallbackHtmlAudio();
    return;
  }
  if (ac.state === "suspended") ac.resume().catch(() => {});
  loadGoalBuffer(ac).then((buf) => {
    if (!buf) {
      fallbackHtmlAudio();
      return;
    }
    const src = ac.createBufferSource();
    src.buffer = buf;
    const g = ac.createGain();
    g.gain.value = 1.0;
    src.connect(g);
    g.connect(ac.destination);
    src.start();
  });
}

function fallbackHtmlAudio(): void {
  const a = getGoalAudio();
  if (!a) return;
  try {
    a.currentTime = 0;
    a.play().catch(() => {});
  } catch {
    /* ignora */
  }
}
