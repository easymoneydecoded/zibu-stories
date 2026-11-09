import { loadFont } from "@remotion/google-fonts/Baloo2";
import { AbsoluteFill, CalculateMetadataFunction, staticFile } from "remotion";
import { Backdrop } from "./Backgrounds";
import { Critter, Lila, Species, StarKid, Zibu } from "./Characters";
import { Prop } from "./Props";
import { CharState, PropItem, Timeline } from "./types";

const { fontFamily } = loadFont("normal", { weights: ["800"], subsets: ["latin"] });

export type BrandProps = { lang: "en" | "es" | "pt" };

const NAME = { en: ["Zibu", "and Friends"], es: ["Zibu", "y sus amigos"], pt: ["Zibu", "e seus amigos"] };
const TAGLINE = { en: "Stories, songs & fun for little ones!", es: "¡Cuentos, canciones y diversión para peques!",
  pt: "Histórias, músicas e diversão para os pequenos!" };

const pose = (mood: CharState["mood"], extra: Partial<CharState> = {}): CharState => ({
  talk: false, mood, actionFrame: 0, dancing: false, glow: false, balloons: false, ...extra,
});

const Rainbow: React.FC<{ r: number; width: number }> = ({ r, width }) => (
  <svg width={r * 2 + width} height={r + width} viewBox={`0 0 ${r * 2 + width} ${r + width}`} style={{ overflow: "visible" }}>
    {["#ff4d4d", "#ff9f1c", "#ffd23f", "#3cc45a", "#3d86f0", "#a66bff"].map((c, i) => {
      const rr = r - i * (width / 6);
      const cx = r + width / 2;
      return <path key={c} d={`M${cx - rr} ${r + width / 2} A ${rr} ${rr} 0 0 1 ${cx + rr} ${r + width / 2}`}
        stroke={c} strokeWidth={width / 6 + 1} fill="none" />;
    })}
  </svg>
);

const Title: React.FC<{ lang: BrandProps["lang"]; size: number }> = ({ lang, size }) => (
  <div style={{ fontFamily, fontWeight: 800, textAlign: "center", lineHeight: 0.95 }}>
    <div style={{ fontSize: size, color: "#3d86f0", WebkitTextStroke: `${size * 0.09}px white`, paintOrder: "stroke fill",
      textShadow: `0 ${size * 0.07}px 0 rgba(0,0,0,0.15)`, letterSpacing: 2 }}>
      {NAME[lang][0].split("").map((ch, i) => (
        <span key={i} style={{ color: ["#3d86f0", "#ff5d8f", "#ffb300", "#3cc45a"][i % 4], display: "inline-block",
          rotate: `${[-6, 4, -3, 6][i % 4]}deg` }}>{ch}</span>
      ))}
    </div>
    <div style={{ fontSize: size * 0.42, color: "#ff5d8f", WebkitTextStroke: `${size * 0.05}px white`, paintOrder: "stroke fill",
      marginTop: size * 0.05, textShadow: `0 ${size * 0.04}px 0 rgba(0,0,0,0.12)` }}>{NAME[lang][1]}</div>
  </div>
);

export type ThumbProps = { lang: "en" | "es" | "pt"; episode: string; variant?: "A" | "B" | "C"; timeline?: Timeline };

export const calculateThumb: CalculateMetadataFunction<ThumbProps> = async ({ props }) => {
  const res = await fetch(staticFile(`ep/${props.episode}/${props.lang}/timeline.json`));
  return { props: { ...props, timeline: (await res.json()) as Timeline } };
};

const THUMB_EP001 = { en: ["The Lost", "Little Star!"], es: ["¡La estrellita", "perdida!"], pt: ["A estrelinha", "perdida!"] };

/** El objeto de la historia (cometa, globo...) en grande, centrado en (x, y) px de la miniatura 1280x720. */
const BigProp: React.FC<{ p?: PropItem; x: number; y: number; scale: number; rotate?: number }> = ({ p, x, y, scale, rotate = 0 }) =>
  p ? (
    // el globo es mas alto que ancho: algo mas pequeno y mas abajo para no tapar el texto
    <div style={{ position: "absolute", left: x - 960, top: y - 540 + (p.what === "balloon" ? 70 : 0), width: 1920, height: 1080,
      scale: `${p.what === "balloon" ? scale * 0.62 : scale}`, rotate: `${rotate}deg`,
      filter: "drop-shadow(0 6px 0 rgba(0,0,0,0.25))" }}>
      <Prop p={{ ...p, x: 0.5, y: 0.5, anim: undefined }} appear={1} />
    </div>
  ) : null;

const Sunburst: React.FC<{ c1: string; c2: string }> = ({ c1, c2 }) => (
  <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 55%, ${c1} 0%, ${c2} 100%)` }}>
    <svg width={1280} height={720} style={{ position: "absolute", inset: 0 }}>
      {Array.from({ length: 18 }, (_, i) => (
        <path key={i} d="M640 400 L 600 -900 L 680 -900 Z" fill="rgba(255,255,255,0.18)"
          style={{ transformOrigin: "640px 400px", rotate: `${i * 20}deg` }} />
      ))}
    </svg>
  </AbsoluteFill>
);

const BigText: React.FC<{ t: string; size: number; color: string; style?: React.CSSProperties }> = ({ t, size, color, style }) => (
  <div style={{ position: "absolute", fontFamily, fontWeight: 800, lineHeight: 0.95, whiteSpace: "nowrap", fontSize: size, color,
    WebkitTextStroke: `${Math.round(size / 7)}px #3a2a7a`, paintOrder: "stroke fill", textShadow: "0 8px 0 rgba(0,0,0,0.3)", ...style }}>{t}</div>
);

/**
 * Miniatura 1280x720 de un episodio. variant:
 *  A: texto de 2 lineas, Zibu sorprendido, Lila y el invitado en el escenario (la original)
 *  B (por defecto desde 2026-11-08): primer plano: Zibu enorme y sorprendido, el objeto de la historia gigante y una sola frase
 *  C: fondo de rayos de color saturado, personajes grandes riendo y el objeto en el centro
 */
export const Thumbnail: React.FC<ThumbProps> = (props) =>
  props.variant === "A" ? <ThumbA {...props} /> : props.variant === "C" ? <ThumbC {...props} /> : <ThumbB {...props} />;

const Guest: React.FC<{ species: Species; mood: CharState["mood"]; size: number }> = ({ species, mood, size }) =>
  species === "star" ? <StarKid s={pose(mood, { glow: true })} size={size * 0.8} /> : <Critter s={pose(mood)} species={species} size={size} />;

const ThumbB: React.FC<ThumbProps> = ({ lang, timeline: tl }) => {
  const text = tl?.thumb?.text ?? THUMB_EP001[lang];
  const species = (tl?.guest ?? "star") as Species;
  // las dos lineas: la primera sola puede quedar a medias ("¡ÁNIMO," sin el nombre)
  const size = (t: string, max: number) => Math.min(max, Math.floor(1150 / (t.length * 0.6)));
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <AbsoluteFill style={{ scale: "0.6667", transformOrigin: "0 0", width: 1920, height: 1080, filter: "saturate(1.35)" }}>
        <Backdrop bg={tl?.thumb?.bg ?? "hill"} time={tl?.thumb?.time ?? "day"} />
      </AbsoluteFill>
      <BigProp p={tl?.thumb?.prop} x={930} y={360} scale={2.2} rotate={-8} />
      <div style={{ position: "absolute", left: 830, top: 400 }}>
        <Guest species={species} mood="surprised" size={330} />
      </div>
      <div style={{ position: "absolute", left: -90, top: 150 }}>
        <Zibu s={pose("surprised")} size={640} />
      </div>
      {text.map((t, i) => (
        <BigText key={t} t={t} size={size(t, i ? 100 : 118)} color={i ? "#ffffff" : "#ffd23f"}
          style={{ left: 40, top: 20 + i * 118, right: 40, textAlign: "right", rotate: "-3deg" }} />
      ))}
    </AbsoluteFill>
  );
};

const ThumbC: React.FC<ThumbProps> = ({ lang, timeline: tl }) => {
  const text = tl?.thumb?.text ?? THUMB_EP001[lang];
  const species = (tl?.guest ?? "star") as Species;
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <Sunburst c1="#fff3a6" c2="#ff9f1c" />
      <BigProp p={tl?.thumb?.prop} x={640} y={330} scale={2.2} rotate={6} />
      <div style={{ position: "absolute", left: -20, top: 250 }}>
        <Zibu s={pose("laugh")} size={470} />
      </div>
      <div style={{ position: "absolute", left: 480, top: 390 }}>
        <Lila s={pose("laugh")} size={260} />
      </div>
      <div style={{ position: "absolute", left: 860, top: 330 }}>
        <Guest species={species} mood="laugh" size={400} />
      </div>
      {text.map((t, i) => (
        <BigText key={t} t={t} size={Math.min(i ? 104 : 116, Math.floor(1180 / (t.length * 0.6)))} color={i ? "#ffffff" : "#ff4d8f"}
          style={{ left: 0, right: 0, top: 18 + i * 108, textAlign: "center", rotate: i ? "2deg" : "-3deg" }} />
      ))}
    </AbsoluteFill>
  );
};

const ThumbA: React.FC<ThumbProps> = ({ lang, timeline: tl }) => {
  const text = tl?.thumb?.text ?? THUMB_EP001[lang];
  const species = (tl?.guest ?? "star") as Species;
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ scale: "0.6667", transformOrigin: "0 0", width: 1920, height: 1080 }}>
        <Backdrop bg={tl?.thumb?.bg ?? "hill"} time={tl?.thumb?.time ?? "night"} />
      </AbsoluteFill>
      <div style={{ position: "absolute", left: 40, top: 40, right: 40, fontFamily, fontWeight: 800, lineHeight: 0.95, rotate: "-4deg" }}>
        {text.map((t, i) => (
          // El tamano baja con la longitud para que cada texto quepa en una sola linea (~1150 px de ancho)
          <div key={t} style={{ fontSize: Math.min(i ? 112 : 96, Math.floor(1150 / (t.length * 0.58))), whiteSpace: "nowrap",
            color: i ? "#ffd23f" : "white", WebkitTextStroke: "14px #3a2a7a",
            paintOrder: "stroke fill", textShadow: "0 8px 0 rgba(0,0,0,0.3)" }}>{t}</div>
        ))}
      </div>
      <div style={{ position: "absolute", left: 60, top: 330 }}>
        <Zibu s={pose("surprised")} size={330} />
      </div>
      {species === "star" ? (
        <div style={{ position: "absolute", left: 800, top: 330 }}>
          <StarKid s={pose("laugh", { glow: true, balloons: !tl?.thumb })} size={240} />
        </div>
      ) : (
        <div style={{ position: "absolute", left: 830, top: 360 }}>
          <Critter s={pose("laugh")} species={species} size={300} />
        </div>
      )}
      <div style={{ position: "absolute", left: 470, top: 420 }}>
        <Lila s={pose("laugh")} size={200} />
      </div>
    </AbsoluteFill>
  );
};

/** Foto de perfil 800x800 (YouTube la recorta en circulo): Zibu en primer plano. */
export const Avatar: React.FC<BrandProps> = () => (
  <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 40%, #fff3a6 0%, #ffd23f 45%, #ff9f1c 100%)" }}>
    <svg width={800} height={800} style={{ position: "absolute", inset: 0 }}>
      {Array.from({ length: 16 }, (_, i) => (
        <path key={i} d="M400 400 L 380 -100 L 420 -100 Z" fill="rgba(255,255,255,0.22)"
          style={{ transformOrigin: "400px 400px", rotate: `${i * 22.5}deg` }} />
      ))}
    </svg>
    <div style={{ position: "absolute", left: 160, top: 150 }}>
      <Zibu s={pose("laugh")} size={480} />
    </div>
  </AbsoluteFill>
);

/**
 * Banner 2560x1440. En movil solo se ve la franja central de 1546x423 (x 507-2053, y 508-931):
 * ahi van el nombre, Zibu, Lila y la estrella; el resto es decorado.
 */
export const Banner: React.FC<BrandProps> = ({ lang }) => (
  <AbsoluteFill style={{ background: "#9fdcff" }}>
    <AbsoluteFill style={{ scale: "1.3334", transformOrigin: "0 0", width: 1920, height: 1080 }}>
      <Backdrop bg="garden" time="day" />
    </AbsoluteFill>
    <div style={{ position: "absolute", left: 1280 - 620, top: 520 }}>
      <Rainbow r={620} width={150} />
    </div>
    <div style={{ position: "absolute", left: 0, right: 0, top: 520, display: "flex", justifyContent: "center" }}>
      <Title lang={lang} size={185} />
    </div>
    <div style={{ position: "absolute", left: 0, right: 0, top: 838, textAlign: "center", fontFamily, fontWeight: 800,
      fontSize: 44, color: "#5a3b9e", WebkitTextStroke: "7px white", paintOrder: "stroke fill" }}>
      {TAGLINE[lang]}
    </div>
    <div style={{ position: "absolute", left: 525, top: 540 }}>
      <Zibu s={pose("laugh", { action: "wave", actionFrame: 10 })} size={330} />
    </div>
    <div style={{ position: "absolute", left: 1740, top: 525 }}>
      <Lila s={pose("happy", { action: "wave", actionFrame: 10 })} size={245} />
    </div>
    <div style={{ position: "absolute", left: 1620, top: 525, scale: "0.85" }}>
      <StarKid s={pose("happy", { glow: true })} size={150} />
    </div>
  </AbsoluteFill>
);
