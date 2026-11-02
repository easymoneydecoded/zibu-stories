import { useCurrentFrame } from "remotion";
import { PropItem } from "./types";

export const BalloonShape: React.FC<{ color: string; size?: number }> = ({ color, size = 150 }) => (
  <svg width={size} height={size * 1.75} viewBox="0 0 190 330" style={{ overflow: "visible" }}>
    <path d="M95 225 Q 80 270 100 300 Q 115 320 95 330" stroke="#777" strokeWidth={3} fill="none" />
    <ellipse cx={95} cy={110} rx={85} ry={105} fill={color} />
    <path d="M85 212 L105 212 L95 228 Z" fill={color} />
    <ellipse cx={62} cy={70} rx={18} ry={30} fill="rgba(255,255,255,0.45)" />
  </svg>
);

const FaceStar: React.FC<{ size: number; glow?: number }> = ({ size, glow = 0 }) => (
  <svg width={size} height={size} viewBox="0 0 200 200" style={{ overflow: "visible" }}>
    {glow > 0 && <circle cx={100} cy={105} r={110 * glow} fill="rgba(255,246,176,0.35)" />}
    <path d="M100 8 L124 72 L192 74 L138 116 L158 182 L100 142 L42 182 L62 116 L8 74 L76 72 Z"
      fill="#ffe066" stroke="#f0a800" strokeWidth={7} strokeLinejoin="round" />
    <circle cx={80} cy={100} r={8} fill="#6b4200" /><circle cx={120} cy={100} r={8} fill="#6b4200" />
    <path d="M84 122 Q 100 136 116 122" stroke="#6b4200" strokeWidth={6} fill="none" strokeLinecap="round" />
  </svg>
);

/** Objetos sencillos (viewBox 100x100). El color opcional cambia el color principal. */
export const SIMPLE = {
  apple: (c?: string) => (<g><circle cx={50} cy={58} r={36} fill={c ?? "#ff4d4d"} /><path d="M50 24 q 4 -14 14 -16" stroke="#7a4a1a" strokeWidth={5} fill="none" /><ellipse cx={62} cy={18} rx={10} ry={6} fill="#3cc45a" /><ellipse cx={38} cy={46} rx={7} ry={11} fill="rgba(255,255,255,0.5)" /></g>),
  flower: (c?: string) => (<g><line x1={50} y1={60} x2={50} y2={100} stroke="#3e9a2c" strokeWidth={6} />{[0, 72, 144, 216, 288].map((a) => <circle key={a} cx={50 + Math.cos(a * Math.PI / 180) * 20} cy={40 + Math.sin(a * Math.PI / 180) * 20} r={16} fill={c ?? "#ff7aa8"} />)}<circle cx={50} cy={40} r={13} fill="#ffd43b" /></g>),
  butterfly: (c?: string) => (<g><ellipse cx={30} cy={40} rx={24} ry={28} fill={c ?? "#a66bff"} /><ellipse cx={70} cy={40} rx={24} ry={28} fill={c ?? "#a66bff"} /><ellipse cx={34} cy={72} rx={16} ry={18} fill={c ?? "#ff7aa8"} /><ellipse cx={66} cy={72} rx={16} ry={18} fill={c ?? "#ff7aa8"} /><rect x={46} y={30} width={8} height={52} rx={4} fill="#3b2a1a" /></g>),
  gift: (c?: string) => (<g><rect x={14} y={38} width={72} height={56} rx={6} fill={c ?? "#3d86f0"} /><rect x={8} y={26} width={84} height={18} rx={5} fill={c ?? "#3d86f0"} /><rect x={44} y={26} width={12} height={68} fill="#ffd23f" /><path d="M50 26 q -24 -24 -30 -4 q 10 8 30 4 q 20 4 30 -4 q -6 -20 -30 4" fill="#ffd23f" /></g>),
  cookie: () => (<g><circle cx={50} cy={50} r={40} fill="#d9a05b" stroke="#b77a35" strokeWidth={4} />{[[35, 38], [60, 32], [52, 58], [32, 62], [68, 60]].map(([x, y]) => <circle key={x} cx={x} cy={y} r={6} fill="#5a3415" />)}</g>),
  kite: (c?: string) => (<g><path d="M50 4 L 82 40 L 50 80 L 18 40 Z" fill={c ?? "#ff4d4d"} stroke="#c22f2f" strokeWidth={3} /><line x1={50} y1={4} x2={50} y2={80} stroke="white" strokeWidth={3} /><line x1={18} y1={40} x2={82} y2={40} stroke="white" strokeWidth={3} /><path d="M50 80 q 10 10 0 20 q -10 10 0 20" stroke="#777" strokeWidth={3} fill="none" /></g>),
  umbrella: (c?: string) => (<g><path d="M8 50 Q 50 -4 92 50 Z" fill={c ?? "#ff7aa8"} /><line x1={50} y1={50} x2={50} y2={88} stroke="#5a4a3a" strokeWidth={5} /><path d="M50 88 q 0 10 -10 8" stroke="#5a4a3a" strokeWidth={5} fill="none" /></g>),
  shell: (c?: string) => (<g><path d="M50 90 L 12 40 Q 50 0 88 40 Z" fill={c ?? "#ffb3c7"} stroke="#e58aa5" strokeWidth={3} />{[30, 40, 50, 60, 70].map((x) => <line key={x} x1={50} y1={88} x2={x} y2={20} stroke="#e58aa5" strokeWidth={3} />)}</g>),
  leaf: (c?: string) => (<g><path d="M50 92 Q 6 50 50 8 Q 94 50 50 92 Z" fill={c ?? "#ff9f1c"} /><line x1={50} y1={92} x2={50} y2={14} stroke="rgba(0,0,0,0.25)" strokeWidth={3} /></g>),
  cupcake: (c?: string) => (<g><path d="M22 54 L 78 54 L 70 94 L 30 94 Z" fill="#7fc8ff" /><circle cx={50} cy={46} r={28} fill={c ?? "#ffd1e3"} /><circle cx={50} cy={16} r={8} fill="#ff4d4d" /></g>),
};

/** Un objeto de la escena; la posicion (x, y) es su centro en fraccion del cuadro. */
export const Prop: React.FC<{ p: PropItem; appear: number }> = ({ p, appear }) => {
  const frame = useCurrentFrame();
  const t = frame;
  let node: React.ReactNode;
  let w = 120;
  let dy = 0;
  if (p.what === "ball") {
    w = 110;
    dy = p.anim === "bounce" ? -Math.abs(Math.sin(t / 10)) * 90 : 0;
    node = (
      <svg width={w} height={w} viewBox="0 0 100 100" style={{ rotate: `${t * 4}deg` }}>
        <circle cx={50} cy={50} r={46} fill="#ff4d4d" stroke="#c22f2f" strokeWidth={4} />
        <path d="M6 50 Q 50 30 94 50" stroke="white" strokeWidth={9} fill="none" />
      </svg>
    );
  } else if (p.what === "firefly") {
    w = 90;
    dy = Math.sin(t / 15 + p.x * 10) * 25;
    const g = 0.6 + Math.abs(Math.sin(t / 7 + p.x * 20)) * 0.4;
    node = (
      <svg width={w} height={w} viewBox="0 0 100 100" style={{ overflow: "visible", translate: `${Math.sin(t / 22 + p.y * 9) * 30}px 0px` }}>
        <circle cx={50} cy={50} r={46 * g} fill="rgba(255,240,120,0.35)" />
        <ellipse cx={38} cy={38} rx={14} ry={9} fill="rgba(255,255,255,0.7)" style={{ rotate: `${Math.sin(t) * 20}deg`, transformOrigin: "50px 50px" }} />
        <ellipse cx={62} cy={38} rx={14} ry={9} fill="rgba(255,255,255,0.7)" style={{ rotate: `${-Math.sin(t) * 20}deg`, transformOrigin: "50px 50px" }} />
        <circle cx={50} cy={52} r={14} fill="#fff27a" />
      </svg>
    );
  } else if (p.what === "stone") {
    w = 150;
    node = (
      <svg width={w} height={w * 0.45} viewBox="0 0 150 68">
        <ellipse cx={75} cy={36} rx={72} ry={30} fill="#8d97a6" />
        <ellipse cx={60} cy={26} rx={36} ry={12} fill="#aab3c0" />
      </svg>
    );
  } else if (p.what === "balloon") {
    w = 130;
    dy = Math.sin(t / 14 + p.x * 10) * 12;
    node = <BalloonShape color={p.color ?? "#ff4d4d"} size={w} />;
  } else if (p.what in SIMPLE) {
    w = 120;
    dy = p.anim === "float" ? Math.sin(t / 14 + p.x * 10) * 18 : p.anim === "bounce" ? -Math.abs(Math.sin(t / 10)) * 60 : 0;
    const flap = p.what === "butterfly" ? Math.abs(Math.sin(t / 3)) : 1;
    node = (
      <svg width={w} height={w} viewBox="0 0 100 100" style={{ overflow: "visible", scale: p.what === "butterfly" ? `${flap * 0.6 + 0.4} 1` : undefined }}>
        {SIMPLE[p.what as keyof typeof SIMPLE](p.color)}
      </svg>
    );
  } else if (p.what === "bigstar") {
    w = 240;
    dy = Math.sin(t / 20 + p.x * 5) * 14;
    node = <FaceStar size={w} glow={0.9 + Math.sin(t / 9) * 0.1} />;
  } else {
    w = 120;
    node = <FaceStar size={w} glow={1.2 + Math.sin(t / 5) * 0.35} />;
  }
  const h = p.what === "balloon" ? w * 1.75 : w;
  return (
    <div style={{ position: "absolute", left: p.x * 1920 - w / 2, top: p.y * 1080 - h / 2 + dy, scale: `${appear}` }}>
      {node}
    </div>
  );
};

export const IconStar: React.FC = () => <FaceStar size={260} glow={1} />;
