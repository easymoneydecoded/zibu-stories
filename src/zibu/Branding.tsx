import { loadFont } from "@remotion/google-fonts/Baloo2";
import { AbsoluteFill, CalculateMetadataFunction, staticFile } from "remotion";
import { Backdrop } from "./Backgrounds";
import { Critter, Lila, Species, StarKid, Zibu } from "./Characters";
import { CharState, Timeline } from "./types";

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

export type ThumbProps = { lang: "en" | "es" | "pt"; episode: string; timeline?: Timeline };

export const calculateThumb: CalculateMetadataFunction<ThumbProps> = async ({ props }) => {
  const res = await fetch(staticFile(`ep/${props.episode}/${props.lang}/timeline.json`));
  return { props: { ...props, timeline: (await res.json()) as Timeline } };
};

const THUMB_EP001 = { en: ["The Lost", "Little Star!"], es: ["¡La estrellita", "perdida!"], pt: ["A estrelinha", "perdida!"] };

/** Miniatura 1280x720 de un episodio: texto corto y grande, Zibu sorprendido, Lila y el invitado. */
export const Thumbnail: React.FC<ThumbProps> = ({ lang, timeline: tl }) => {
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
