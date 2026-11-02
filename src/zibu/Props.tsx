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
