import { Audio } from "@remotion/media";
import { loadFont } from "@remotion/google-fonts/Baloo2";
import {
  AbsoluteFill, CalculateMetadataFunction, Easing, interpolate, Sequence, spring, staticFile, useCurrentFrame,
} from "remotion";
import { Backdrop } from "./Backgrounds";
import { Critter, Lila, SPECIES, Species, StarKid, Zibu } from "./Characters";
import { BalloonShape, IconStar, Prop } from "./Props";
import { CharState, Line, Mood, Scene, Timeline } from "./types";

const { fontFamily } = loadFont("normal", { weights: ["800"], subsets: ["latin"] });

export type EpisodeProps = { episode: string; lang: string; timeline?: Timeline };

export const calculateEpisode: CalculateMetadataFunction<EpisodeProps> = async ({ props }) => {
  const res = await fetch(staticFile(`ep/${props.episode}/${props.lang}/timeline.json`));
  const timeline = (await res.json()) as Timeline;
  return { durationInFrames: timeline.durationInFrames, fps: timeline.fps, props: { ...props, timeline } };
};

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

const SceneView: React.FC<{ scene: Scene; tl: Timeline }> = ({ scene, tl }) => {
  const local = useCurrentFrame();
  const f = local + scene.start;
  const fade = interpolate(local, [0, 10], [0, 1], clamp);
  const zoom = interpolate(local, [0, scene.end - scene.start], [1, 1.05]);
  // Numero o palabra grande: se ve desde su frase hasta que empieza la siguiente
  const shownIdx = scene.lines.reduce((acc, l, i) => (l.show && f >= l.start ? i : acc), -1);
  const shownNext = scene.lines[shownIdx + 1];
  const shown = shownIdx >= 0 && f < (shownNext ? shownNext.start : scene.lines[shownIdx].start + scene.lines[shownIdx].dur + 45)
    ? scene.lines[shownIdx] : undefined;
  const propLine = scene.lines.find((l) => l.showProp && f >= l.start && f <= l.start + l.dur + 20);
  const lyric = scene.type === "song" ? [...scene.lines].reverse().find((l) => l.start <= f && l.who !== "star") : undefined;

  return (
    <AbsoluteFill style={{ opacity: fade }}>
      <AbsoluteFill style={{ scale: `${zoom}`, transformOrigin: "50% 80%" }}>
        <Backdrop bg={scene.bg} time={scene.time} />
        {(scene.props ?? []).map((p, i) => {
          const at = p.at ? scene.lines[p.at].start : scene.start;
          const until = p.until !== undefined ? scene.lines[p.until].start : Infinity;
          if (f < at || f >= until) return null;
          const appear = p.at ? spring({ frame: f - at, fps: 30, config: { damping: 9 } }) : 1;
          return <Prop key={i} p={p} appear={appear} />;
        })}
        {scene.cast.map((c) => {
          const { x, y } = position(scene, c.who, f);
          const s = charState(scene, c.who, f);
          const species = (tl.guest ?? "star") as Species;
          const isGuest = c.who === "guest" || c.who === "star";
          if (isGuest && species === "star") {
            return (
              <div key={c.who} style={{ position: "absolute", left: x * 1920 - 85, top: y * 1080 - 85 }}>
                <StarKid s={s} />
              </div>
            );
          }
          const w = c.who === "zibu" ? 330 : isGuest ? 260 : 300;
          const h = c.who === "lila" ? w * 1.6 : w * 1.15;
          // Un animalito con "y" en el guion vuela (p. ej. el buho); si no, va por el suelo
          const top = isGuest && c.y ? y * 1080 - h / 2 : GROUND - h;
          return (
            <div key={c.who} style={{ position: "absolute", left: x * 1920 - w / 2, top }}>
              {c.who === "zibu" ? <Zibu s={s} size={w} /> : c.who === "lila" ? <Lila s={s} size={w} />
                : <Critter s={s} species={species as keyof typeof SPECIES} size={w} />}
            </div>
          );
        })}
        {(scene.type === "dance" || scene.type === "bye") && <Confetti local={local} />}
      </AbsoluteFill>

      {scene.type === "title" && <BigText text={tl.title} since={local - 5} color="#ff5d8f" size={120} top={300} />}
      {scene.type === "bye" && (
        <BigText text={tl.lang === "es" ? "¡Hasta pronto!" : "See you soon!"} since={local - 5} color="#3cc45a" size={150} top={120} />
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

export const Episode: React.FC<EpisodeProps> = ({ timeline: tl }) => {
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
