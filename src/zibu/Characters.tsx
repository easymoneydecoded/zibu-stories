import { useCurrentFrame } from "remotion";
import { Face } from "./Face";
import { CharState } from "./types";

const BEAT_FRAMES = (30 * 60) / 112; // la musica alegre va a 112 bpm

/** Desplazamiento y giro del cuerpo segun la accion en curso, el baile y el animo. */
const useMotion = (s: CharState, seed: number) => {
  const frame = useCurrentFrame();
  let dy = Math.abs(Math.sin((frame + seed * 13) / 9)) * 8;
  let rot = 0;
  let dx = 0;
  const a = s.actionFrame;
  if (s.dancing) {
    dy = Math.abs(Math.sin((frame * Math.PI) / BEAT_FRAMES)) * 34;
    rot = Math.sin((frame * Math.PI) / (BEAT_FRAMES * 2) + seed) * 9;
  }
  if (s.action === "jump" && a < 24) dy += Math.sin((a / 24) * Math.PI) * 90;
  if (s.action === "bigjump" && a < 28) dy += Math.sin((a / 28) * Math.PI) * 180;
  if (s.action === "spin" && a < 30) rot = (a / 30) * 360;
  if (s.action === "shake" && a < 40) dx = Math.sin(a * 1.3) * 16 * (1 - a / 40);
  if (s.mood === "scared") dx += Math.sin(frame * 2.1) * 3;
  const wave = s.action === "wave" && a < 75;
  return { dy, rot, dx, wave, frame };
};

export const Zibu: React.FC<{ s: CharState; size?: number }> = ({ s, size = 330 }) => {
  const { dy, rot, dx, wave, frame } = useMotion(s, 0);
  const arm = wave ? 12 + Math.sin(frame / 4) * 22 : s.dancing ? 20 + Math.sin(frame / 5) * 30 : 55 + Math.sin(frame / 12) * 6;
  const squash = 1 + Math.sin(frame / 4.5) * 0.02;
  return (
    <svg width={size} height={size * 1.15} viewBox="0 0 400 460"
      style={{ overflow: "visible", translate: `${dx}px ${-dy}px`, rotate: `${rot}deg`, transformOrigin: "50% 90%" }}>
      <ellipse cx={200} cy={448} rx={120} ry={14} fill="rgba(0,40,0,0.18)" style={{ translate: `0px ${dy}px` }} />
      <path d="M200 92 Q 215 40 240 30" stroke="#2b6fd6" strokeWidth={10} fill="none" strokeLinecap="round" />
      <circle cx={242} cy={28} r={20 + Math.sin(frame / 6) * 2} fill="#ffcf3f" stroke="#e6a800" strokeWidth={5} />
      <ellipse cx={140} cy={425} rx={50} ry={26} fill="#2b6fd6" />
      <ellipse cx={260} cy={425} rx={50} ry={26} fill="#2b6fd6" />
      <g style={{ transformOrigin: "75px 270px", rotate: `${s.dancing ? -arm : -10 - Math.sin(frame / 12) * 6}deg` }}>
        <path d="M75 270 Q 20 300 30 350" stroke="#3d86f0" strokeWidth={30} fill="none" strokeLinecap="round" />
      </g>
      <g style={{ transformOrigin: "200px 420px", scale: `${1 / squash} ${squash}` }}>
        <ellipse cx={200} cy={265} rx={160} ry={165} fill="#4b95ff" />
        <ellipse cx={200} cy={300} rx={105} ry={95} fill="#8cc0ff" />
        <ellipse cx={150} cy={170} rx={40} ry={20} fill="rgba(255,255,255,0.35)" transform="rotate(-20 150 170)" />
        <Face cx={200} eyeY={215} eyeDx={60} eyeR={46} mouthY={285} mouthW={45} mood={s.mood} talk={s.talk} seed={1} />
      </g>
      <g style={{ transformOrigin: "325px 270px", rotate: `${arm}deg` }}>
        <path d="M325 270 Q 385 230 380 170" stroke="#3d86f0" strokeWidth={30} fill="none" strokeLinecap="round" />
      </g>
    </svg>
  );
};

export const Lila: React.FC<{ s: CharState; size?: number }> = ({ s, size = 300 }) => {
  const { dy, rot, dx, wave, frame } = useMotion(s, 3);
  const arm = wave ? -12 - Math.sin(frame / 4) * 22 : s.dancing ? -20 - Math.sin(frame / 5) * 30 : -50 - Math.sin(frame / 12) * 6;
  const earL = Math.sin(frame / 14) * 6 + (s.mood === "sad" ? -35 : s.mood === "surprised" ? 6 : 0);
  const earR = Math.sin(frame / 14 + 1) * 6 + (s.mood === "sad" ? 35 : s.mood === "surprised" ? -6 : 0);
  return (
    <svg width={size} height={size * 1.6} viewBox="0 0 400 640"
      style={{ overflow: "visible", translate: `${dx}px ${-dy}px`, rotate: `${rot}deg`, transformOrigin: "50% 92%" }}>
      <ellipse cx={200} cy={628} rx={115} ry={14} fill="rgba(0,40,0,0.18)" style={{ translate: `0px ${dy}px` }} />
      {/* orejas */}
      {[{ x: 145, r: earL - 8 }, { x: 255, r: earR + 8 }].map((e, i) => (
        <g key={i} style={{ transformOrigin: `${e.x}px 250px`, rotate: `${e.r}deg` }}>
          <ellipse cx={e.x} cy={140} rx={42} ry={120} fill="#ffd1e3" stroke="#f3a6c4" strokeWidth={4} />
          <ellipse cx={e.x} cy={150} rx={22} ry={88} fill="#ff9fc2" />
        </g>
      ))}
      {/* lazo */}
      <g style={{ transformOrigin: "255px 250px", rotate: `${earR + 8}deg` }}>
        <path d="M255 215 L 222 192 L 226 238 Z M255 215 L 288 192 L 284 238 Z" fill="#a66bff" />
        <circle cx={255} cy={215} r={11} fill="#8a4fe0" />
      </g>
      <ellipse cx={145} cy={605} rx={46} ry={24} fill="#ffc0d8" />
      <ellipse cx={255} cy={605} rx={46} ry={24} fill="#ffc0d8" />
      <g style={{ transformOrigin: "95px 440px", rotate: `${s.dancing ? -arm : 10 + Math.sin(frame / 12) * 6}deg` }}>
        <path d="M95 440 Q 50 470 60 520" stroke="#ffc0d8" strokeWidth={28} fill="none" strokeLinecap="round" />
      </g>
      <ellipse cx={200} cy={470} rx={125} ry={145} fill="#ffd1e3" />
      <ellipse cx={200} cy={505} rx={78} ry={92} fill="#fff4f8" />
      <ellipse cx={200} cy={330} rx={130} ry={110} fill="#ffd1e3" />
      <Face cx={200} eyeY={315} eyeDx={52} eyeR={38} mouthY={372} mouthW={30} mood={s.mood} talk={s.talk} ink="#5b2a4a" cheek="#ff7aa8" seed={5} />
      <ellipse cx={200} cy={352} rx={11} ry={8} fill="#ff6f9c" />
      <g style={{ transformOrigin: "305px 440px", rotate: `${arm}deg` }}>
        <path d="M305 440 Q 360 400 355 345" stroke="#ffc0d8" strokeWidth={28} fill="none" strokeLinecap="round" />
      </g>
    </svg>
  );
};

/** Estrella invitada: flota, brilla (glow) y puede llevar cuatro globos. */
export const StarKid: React.FC<{ s: CharState; size?: number }> = ({ s, size = 170 }) => {
  const { dy, rot, dx, frame } = useMotion(s, 7);
  const glow = s.glow ? 1 + Math.sin(frame / 6) * 0.15 : 0.55 + Math.sin(frame / 10) * 0.1;
  return (
    <svg width={size} height={size} viewBox="0 0 200 200"
      style={{ overflow: "visible", translate: `${dx}px ${-dy * 0.6 + Math.sin(frame / 12) * 10}px`, rotate: `${rot + Math.sin(frame / 18) * 6}deg` }}>
      <defs>
        <radialGradient id="halo">
          <stop offset="0%" stopColor="#fff6b0" stopOpacity={0.9} />
          <stop offset="100%" stopColor="#fff6b0" stopOpacity={0} />
        </radialGradient>
      </defs>
      {s.balloons && (
        <g>
          {[["#ff4d4d", -70, -190], ["#3d86f0", -25, -225], ["#ffd23f", 25, -225], ["#3cc45a", 70, -190]].map(([c, x, y], i) => (
            <g key={i} style={{ rotate: `${Math.sin(frame / 14 + i) * 4}deg`, transformOrigin: "100px 60px" }}>
              <line x1={100} y1={60} x2={100 + Number(x)} y2={100 + Number(y) + 70} stroke="#777" strokeWidth={2.5} />
              <ellipse cx={100 + Number(x)} cy={100 + Number(y)} rx={42} ry={52} fill={String(c)} />
              <ellipse cx={86 + Number(x)} cy={82 + Number(y)} rx={9} ry={15} fill="rgba(255,255,255,0.45)" />
            </g>
          ))}
        </g>
      )}
      <circle cx={100} cy={105} r={95 * glow * (s.glow ? 1.5 : 1)} fill="url(#halo)" />
      <path d="M100 8 L124 72 L192 74 L138 116 L158 182 L100 142 L42 182 L62 116 L8 74 L76 72 Z"
        fill="#ffd94a" stroke="#f0a800" strokeWidth={7} strokeLinejoin="round" />
      <Face cx={100} eyeY={98} eyeDx={24} eyeR={15} mouthY={124} mouthW={14} mood={s.mood} talk={s.talk} ink="#6b4200" cheek="#ff9e6b" seed={9} />
    </svg>
  );
};
