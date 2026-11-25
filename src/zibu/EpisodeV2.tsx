import { Audio } from "@remotion/media";
import { loadFont } from "@remotion/google-fonts/Baloo2";
import {
  AbsoluteFill, Easing, interpolate, Sequence, spring, staticFile, useCurrentFrame,
} from "remotion";
import { Img } from "remotion";
import { Backdrop } from "./Backgrounds";
import { BalloonShape, IconStar, Prop } from "./Props";
import { CharState, Line, Mood, PropItem, Scene, Timeline } from "./types";

const { fontFamily } = loadFont("normal", { weights: ["800"], subsets: ["latin"] });

import { calculateEpisode, EpisodeProps } from "./Episode";
export { calculateEpisode };

// ---------------------------------------------------------------------------------------------------------------
// Estilo nuevo (prueba 2026-11-25): piezas dibujadas con IA (public/v2, scripts/v2_assets.py) animadas por codigo.
// ---------------------------------------------------------------------------------------------------------------
const ALTO: Record<string, number> = { zibu: 520, lila: 660, guest: 470 };  // alto en pantalla (px)
// Caras por parejas (public/v2/chars3, scripts/v2_assets.py pairs): cada expresion con boca cerrada y abierta
type Expr = "happy" | "neutral" | "surprised" | "sad" | "laugh";
const EXPR: Record<Mood, Expr> = { happy: "happy", laugh: "laugh", surprised: "surprised", scared: "surprised", sad: "sad" };

const cara = (s: CharState, f: number, seed: number): string => {
  const e = EXPR[s.mood] ?? "happy";
  if (s.talk) return `${e}_${(Math.floor(f / 4) + seed) % 2 === 0 ? "open" : "closed"}`;  // al hablar: abre y cierra
  if (e === "happy" && (f + seed * 37) % 110 < 4) return "happy_blink";                      // parpadeo cada ~3,5 s
  return `${e}_closed`;
};

const Sprite: React.FC<{ who: string; folder: string; s: CharState; f: number; seed: number }> = ({ who, folder, s, f, seed }) => {
  const h = ALTO[who] ?? 400;
  const t = s.actionFrame;
  let dy = Math.sin((f + seed * 20) / 14) * 4;          // respira
  let sx = 1 + Math.sin((f + seed * 20) / 18) * 0.012, sy = 2 - sx, rot = 0, dx = 0;
  if (s.talk) dy -= Math.abs(Math.sin(f / 3.2)) * 7;     // rebota un poco al hablar
  if (s.action === "jump" || s.action === "bigjump") {
    const dur = s.action === "bigjump" ? 26 : 20;
    if (t < dur) {
      const p = t / dur;
      dy -= Math.sin(Math.PI * p) * h * (s.action === "bigjump" ? 0.42 : 0.25);
      const squash = p < 0.12 ? 1 - (0.12 - p) * 1.6 : p > 0.88 ? 1 - (p - 0.88) * 1.6 : 1.06;  // encoge al saltar y aterrizar
      sy *= squash; sx *= 2 - squash;
    }
  }
  if (s.action === "wave" && t < 60) rot = Math.sin(t / 3) * 6;
  if (s.action === "shake" && t < 30) dx = Math.sin(t * 2.2) * 10;
  if (s.action === "spin" && t < 30) sx *= Math.cos((t / 30) * Math.PI * 2);
  if (s.dancing) { dy -= Math.abs(Math.sin(f / 8)) * 30; rot = Math.sin(f / 8) * 8; }
  const src = staticFile(`v2/chars3/${folder}/${cara(s, f, seed)}.png`);
  return (
    <div style={{ position: "relative", width: h * 0.8, height: h }}>
      <div style={{ position: "absolute", left: "10%", right: "10%", bottom: -14, height: 28, borderRadius: "50%",
        background: "rgba(40,80,20,0.28)", filter: "blur(6px)", scale: `${1 - Math.min(0.5, -dy / h)}` }} />
      <Img src={src} style={{ position: "absolute", bottom: 0, left: "50%", height: h, translate: `calc(-50% + ${dx}px) ${dy}px`,
        scale: `${sx} ${sy}`, rotate: `${rot}deg`, transformOrigin: "50% 100%",
        filter: s.glow ? "drop-shadow(0 0 30px #fff6a8)" : undefined }} />
    </div>
  );
};

const PROP_V2 = ["balloon"];
const hue = (hex?: string) => {
  if (!hex) return 0;
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
  if (!d) return 0;
  const h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return h * 60;
};
const PropV2: React.FC<{ p: PropItem; appear: number; f: number }> = ({ p, appear, f }) => {
  if (!PROP_V2.includes(p.what)) return <Prop p={p} appear={appear} />;
  const size = p.what === "balloon" ? 230 : 170;
  const flota = Math.sin((f + p.x * 100) / 20) * 12;
  return (
    <Img src={staticFile(`v2/props/${p.what}.png`)} style={{ position: "absolute", left: p.x * 1920 - size * 0.32,
      top: p.y * 1080 - size / 2 + flota, height: size, scale: `${appear}`, rotate: `${Math.sin(f / 25) * 4}deg`,
      filter: `hue-rotate(${hue(p.color)}deg) drop-shadow(0 8px 6px rgba(0,0,0,0.15))` }} />
  );
};
const FONDOS_V2 = ["garden-day"];

const GROUND = 1010; // linea del suelo (px) donde apoyan los pies
const ease = Easing.inOut(Easing.cubic);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** Posicion del personaje en el fotograma f, aplicando en orden los desplazamientos del guion. */
const position = (scene: Scene, who: string, f: number) => {
  const c = scene.cast.find((m) => m.who === who)!;
  let x = c.x;
  let y = c.y ?? 0;
  for (const l of scene.lines) {
    if (f < l.start) break;
    for (const m of l.moves ?? []) {
      if (m.who !== who) continue;
      const p = ease(Math.min(1, (f - l.start) / l.moveDur));
      x += (m.to - x) * p;
      if (m.toY !== undefined) y += (m.toY - y) * p;
    }
  }
  return { x, y };
};

const charState = (scene: Scene, who: string, f: number): CharState => {
  const past = scene.lines.filter((l) => l.start <= f);
  let mood: Mood = "happy";
  for (const l of past) if (l.who === who) mood = l.mood ?? "happy";
  const act = [...past].reverse().find((l) => l.who === who && l.action && l.action !== "glow" && f < l.start + Math.max(l.dur, 75));
  const sonando = !!scene.song && f >= scene.song.start && f < scene.song.start + scene.song.dur;
  if (scene.type === "bye") {  // despedida: todos dicen adios con la mano, contentos
    return { talk: false, mood: "laugh", action: "wave", actionFrame: (f - scene.start) % 60, dancing: false,
      glow: false, balloons: false };
  }
  return {
    talk: scene.lines.some((l) => l.who === who && f >= l.start && f <= l.start + l.dur),
    mood,
    action: act?.action,
    actionFrame: act ? f - act.start : 0,
    dancing: scene.type === "song" || sonando,
    glow: past.some((l) => l.action === "glow" && (l.who === who || l.glowWho === who)),
    balloons: (who === "star" || who === "guest") && past.some((l) => l.balloons),
  };
};

const BigText: React.FC<{ text: string; color?: string | null; since: number; top?: number; size?: number }> = ({
  text, color, since, top = 60, size = 210,
}) => {
  const s = spring({ frame: since, fps: 30, config: { damping: 9, mass: 0.6 } });
  return (
    <div style={{
      position: "absolute", top, width: "100%", textAlign: "center", fontFamily, fontWeight: 800, fontSize: size, lineHeight: 1,
      color: color ?? "#ff9f1c", WebkitTextStroke: "12px white", paintOrder: "stroke fill", scale: `${s}`,
      textShadow: "0 10px 0 rgba(0,0,0,0.12)",
    }}>{text}</div>
  );
};

// Camara del primer minuto: la mayoria de los ninos se va en los primeros 25 s, asi que en cada frase la camara se
// acerca a quien habla (planos alternos, cambio rapido) para que siempre pase algo. Despues, el zoom lento de siempre.
const DYNAMIC_UNTIL = 60 * 30;
const camera = (scene: Scene, f: number): { z: number; ox: number; w: number } => {
  const w = interpolate(f, [DYNAMIC_UNTIL - 30, DYNAMIC_UNTIL], [1, 0], clamp);
  const idx = scene.lines.reduce((acc, l, i) => (l.start <= f ? i : acc), -1);
  if (w === 0 || idx < 0) return { z: 1, ox: 0.5, w: 0 };
  const shot = (i: number) => {
    const l = scene.lines[i];
    if (!l || !scene.cast.some((c) => c.who === l.who)) return { z: 1.06, ox: 0.5 };  // narradora: plano general
    const x = Math.min(0.78, Math.max(0.22, position(scene, l.who, l.start).x));
    return { z: i % 2 === 0 ? 1.12 : 1.06, ox: x };
  };
  const a = shot(idx - 1), b = shot(idx);
  const t = spring({ frame: f - scene.lines[idx].start, fps: 30, config: { damping: 20, stiffness: 200 } });
  return { z: a.z + (b.z - a.z) * t, ox: a.ox + (b.ox - a.ox) * t, w };
};

const SceneView: React.FC<{ scene: Scene; tl: Timeline }> = ({ scene, tl }) => {
  const local = useCurrentFrame();
  const f = local + scene.start;
  const fade = interpolate(local, [0, 10], [0, 1], clamp);
  const slow = interpolate(local, [0, scene.end - scene.start], [1, 1.05]);
  const cam = camera(scene, f);
  const zoom = slow * (1 - cam.w) + cam.z * cam.w;
  const originX = 50 * (1 - cam.w) + cam.ox * 100 * cam.w;
  // Numero o palabra grande: se ve desde su frase hasta que empieza la siguiente
  const shownIdx = scene.lines.reduce((acc, l, i) => (l.show && f >= l.start ? i : acc), -1);
  const shownNext = scene.lines[shownIdx + 1];
  const shown = shownIdx >= 0 && f < (shownNext ? shownNext.start : scene.lines[shownIdx].start + scene.lines[shownIdx].dur + 45)
    ? scene.lines[shownIdx] : undefined;
  const propLine = scene.lines.find((l) => l.showProp && f >= l.start && f <= l.start + l.dur + 20);
  const lyric = scene.type === "song" ? [...scene.lines].reverse().find((l) => l.start <= f && l.who !== "star") : undefined;

  return (
    <AbsoluteFill style={{ opacity: fade }}>
      <AbsoluteFill style={{ scale: `${zoom}`, transformOrigin: `${originX}% 75%` }}>
        {FONDOS_V2.includes(`${scene.bg}-${scene.time}`)
          ? <Img src={staticFile(`v2/bg/${scene.bg}-${scene.time}.png`)} style={{ width: 1920, height: 1080 }} />
          : <Backdrop bg={scene.bg} time={scene.time} />}
        {(scene.props ?? []).map((p, i) => {
          const at = p.at ? scene.lines[p.at].start : scene.start;
          const until = p.until !== undefined ? scene.lines[p.until].start : Infinity;
          if (f < at || f >= until) return null;
          const appear = p.at ? spring({ frame: f - at, fps: 30, config: { damping: 9 } }) : 1;
          return <PropV2 key={i} p={p} appear={appear} f={f} />;
        })}
        {scene.cast.map((c, i) => {
          const { x, y } = position(scene, c.who, f);
          const s = charState(scene, c.who, f);
          const isGuest = c.who === "guest" || c.who === "star";
          const folder = isGuest ? (tl.guest ?? "piglet") : c.who;
          const h = ALTO[isGuest ? "guest" : c.who] ?? 400;
          const top = isGuest && c.y ? y * 1080 - h / 2 : GROUND - h;
          return (
            <div key={c.who} style={{ position: "absolute", left: x * 1920 - h * 0.4, top }}>
              <Sprite who={isGuest ? "guest" : c.who} folder={folder} s={s} f={f} seed={i + 1} />
            </div>
          );
        })}
        {(scene.type === "dance" || scene.type === "bye" || (scene.type === "sing" && !!scene.song && f >= scene.song.start)) && <Confetti local={local} />}
      </AbsoluteFill>

      {scene.type === "title" && <BigText text={tl.title} since={local - 5} color="#ff5d8f" size={120} top={300} />}
      {scene.type === "bye" && (
        <BigText text={({ es: "¡Hasta pronto!", pt: "Até logo!" } as Record<string, string>)[tl.lang] ?? "See you soon!"} since={local - 5} color="#3cc45a" size={150} top={120} />
      )}
      {shown?.show && <BigText text={shown.show.text} color={shown.show.color} since={f - shown.start} />}
      {propLine && (
        <div style={{ position: "absolute", top: 120, width: "100%", display: "flex", justifyContent: "center", gap: 30,
          scale: `${spring({ frame: f - propLine.start, fps: 30, config: { damping: 9 } })}` }}>
          {propLine.showProp === "star" ? <IconStar /> :
            ["#ff4d4d", "#3d86f0", "#ffd23f", "#3cc45a"].map((c) => <BalloonShape key={c} color={c} size={120} />)}
        </div>
      )}
      {lyric && (
        <div style={{
          position: "absolute", top: 50, left: 160, right: 160, textAlign: "center", fontFamily, fontWeight: 800, fontSize: 64,
          color: "#3a2a7a", background: "rgba(255,255,255,0.88)", borderRadius: 40, padding: "14px 30px",
          scale: `${0.85 + 0.15 * spring({ frame: f - lyric.start, fps: 30, config: { damping: 12 } })}`,
        }}>♪ {lyric.text} ♪</div>
      )}
    </AbsoluteFill>
  );
};

const Confetti: React.FC<{ local: number }> = ({ local }) => (
  <>
    {Array.from({ length: 70 }, (_, i) => {
      const t = local - (i * 7) % 40;
      if (t < 0) return null;
      return (
        <div key={i} style={{
          position: "absolute", left: (i * 137) % 1920 + Math.sin(t / 8 + i) * 30, top: -40 + ((t * (6 + (i % 5) * 1.6)) % 1160),
          width: 22, height: 34, borderRadius: 6, rotate: `${(i * 47) % 360 + t * 6}deg`,
          background: ["#ff4d4d", "#3d86f0", "#3cc45a", "#ffd23f", "#ff7aa8", "#a66bff"][i % 6],
        }} />
      );
    })}
  </>
);

export const EpisodeV2: React.FC<EpisodeProps> = ({ timeline: tl }) => {
  if (!tl) return null;
  const lines: Line[] = tl.scenes.flatMap((s) => s.lines);
  return (
    <AbsoluteFill style={{ background: "#9fdcff", fontFamily }}>
      {tl.scenes.map((s) => (
        <Sequence key={s.id} from={s.start} durationInFrames={s.end - s.start} name={`Escena: ${s.id}`}>
          <SceneView scene={s} tl={tl} />
        </Sequence>
      ))}
      <Audio src={staticFile(tl.music)} volume={0.5} />
      {tl.scenes.filter((s) => s.song).map((s) => (
        <Sequence key={`cancion-${s.id}`} from={s.song!.start} durationInFrames={s.song!.dur + 15} name={`Cancion: ${s.song!.src}`}>
          <Audio src={staticFile(s.song!.src)} volume={0.9} />
        </Sequence>
      ))}
      {lines.map((l) => (
        <Sequence key={l.src} from={l.start} name={`Voz: ${l.text}`}>
          <Audio src={staticFile(l.src)} />
        </Sequence>
      ))}
      {tl.sfx.map((s, i) => (
        <Sequence key={`sfx${i}`} from={s.at} durationInFrames={30} name={`Efecto: ${s.name}`}>
          <Audio src={staticFile(`sfx/${s.name}.wav`)} volume={0.45} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
