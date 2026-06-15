// Sonido de gol sintetizado con Web Audio API: sutil, sin archivos externos.
// Dos notas ascendentes suaves (tipo campanita), volumen bajo.

let ctx: AudioContext | null = null;

function getCtx(): AudioContext | null {
  if (typeof window === "undefined") return null;
  if (!ctx) {
    const AC =
      window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    if (!AC) return null;
    ctx = new AC();
  }
  return ctx;
}

/** Los navegadores bloquean audio hasta una interacción del usuario. */
export function unlockAudio(): void {
  const ac = getCtx();
  if (ac && ac.state === "suspended") ac.resume().catch(() => {});
}

export function playGoalSound(): void {
  const ac = getCtx();
  if (!ac) return;
  if (ac.state === "suspended") ac.resume().catch(() => {});
  const now = ac.currentTime;

  // notas: A5 -> E6 (campanita ascendente)
  const notes: Array<[number, number]> = [
    [880.0, 0.0],
    [1318.5, 0.11],
  ];
  for (const [freq, offset] of notes) {
    const osc = ac.createOscillator();
    const gain = ac.createGain();
    osc.type = "sine";
    osc.frequency.value = freq;
    const t0 = now + offset;
    gain.gain.setValueAtTime(0.0001, t0);
    gain.gain.linearRampToValueAtTime(0.1, t0 + 0.02); // volumen bajo (sutil)
    gain.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.38);
    osc.connect(gain);
    gain.connect(ac.destination);
    osc.start(t0);
    osc.stop(t0 + 0.42);
  }
}
