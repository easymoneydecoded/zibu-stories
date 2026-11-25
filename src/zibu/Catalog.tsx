import { loadFont } from "@remotion/google-fonts/Baloo2";
import { AbsoluteFill } from "remotion";
import { Backdrop } from "./Backgrounds";
import { Critter, Lila, SPECIES, StarKid, Zibu } from "./Characters";
import { Prop } from "./Props";
import { CharState, PropItem, Scene } from "./types";

const { fontFamily } = loadFont("normal", { weights: ["800"], subsets: ["latin"] });
const pose: CharState = { talk: false, mood: "happy", actionFrame: 0, dancing: false, glow: false, balloons: false };
const PROPS: PropItem["what"][] = ["ball", "firefly", "stone", "balloon", "bigstar", "brightstar", "apple", "flower",
  "butterfly", "gift", "cookie", "kite", "umbrella", "shell", "leaf", "cupcake"];
const BGS: Scene["bg"][] = ["garden", "forest", "river", "hill", "sky", "beach", "room"];
const TIMES: Scene["time"][] = ["day", "sunset", "night"];

const Label: React.FC<{ t: string }> = ({ t }) => (
  <div style={{ fontFamily, fontSize: 30, color: "#3a2a7a", textAlign: "center", marginTop: 4 }}>{t}</div>
);
const Cell: React.FC<{ children: React.ReactNode; t: string; w?: number; h?: number }> = ({ children, t, w = 260, h = 260 }) => (
  <div style={{ width: w, display: "flex", flexDirection: "column", alignItems: "center" }}>
    <div style={{ width: w, height: h, background: "#fff", borderRadius: 24, position: "relative", overflow: "hidden",
      boxShadow: "0 4px 0 rgba(0,0,0,0.12)", display: "flex", alignItems: "center", justifyContent: "center" }}>{children}</div>
    <Label t={t} />
  </div>
);
const H: React.FC<{ t: string }> = ({ t }) => (
  <div style={{ fontFamily, fontSize: 64, color: "#ff5d8f", WebkitTextStroke: "10px white", paintOrder: "stroke fill",
    margin: "30px 0 16px" }}>{t}</div>
);

/** Lamina con todos los personajes y objetos que se pueden dibujar en un episodio. */
export const Catalog: React.FC = () => (
  <AbsoluteFill style={{ background: "#ffe9b0", padding: 40, display: "block" }}>
    <H t={`Personajes (${2 + Object.keys(SPECIES).length + 1})`} />
    <div style={{ display: "flex", flexWrap: "wrap", gap: 24 }}>
      <Cell t="Zibu"><div style={{ scale: "0.62" }}><Zibu s={pose} size={330} /></div></Cell>
      <Cell t="Lila"><div style={{ scale: "0.62" }}><Lila s={pose} size={300} /></div></Cell>
      {Object.keys(SPECIES).map((sp) => (
        <Cell key={sp} t={sp}><div style={{ scale: "0.75" }}><Critter s={pose} species={sp as keyof typeof SPECIES} size={260} /></div></Cell>
      ))}
      <Cell t="star"><StarKid s={{ ...pose, glow: true }} size={170} /></Cell>
    </div>
    <H t={`Objetos (${PROPS.length})`} />
    <div style={{ display: "flex", flexWrap: "wrap", gap: 24 }}>
      {PROPS.map((w) => (
        <Cell key={w} t={w}>
          <div style={{ position: "absolute", left: 130 - 960, top: 130 - 540 + (w === "balloon" ? 40 : 0), width: 1920, height: 1080,
            scale: w === "balloon" ? "0.7" : "1" }}>
            <Prop p={{ what: w, x: 0.5, y: 0.5 } as PropItem} appear={1} />
          </div>
        </Cell>
      ))}
    </div>
  </AbsoluteFill>
);

/** Todos los fondos: 7 lugares x 3 momentos del dia. */
export const CatalogBgs: React.FC = () => (
  <AbsoluteFill style={{ background: "#ffe9b0", padding: 40, display: "block" }}>
    <H t={`Fondos (${BGS.length} lugares x ${TIMES.length} momentos = ${BGS.length * TIMES.length})`} />
    <div style={{ display: "flex", flexWrap: "wrap", gap: 24 }}>
      {BGS.flatMap((bg) => TIMES.map((tm) => (
        <Cell key={bg + tm} t={`${bg} · ${tm}`} w={384} h={216}>
          <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, scale: "0.2", transformOrigin: "0 0" }}>
            <Backdrop bg={bg} time={tm} />
          </div>
        </Cell>
      )))}
    </div>
  </AbsoluteFill>
);
