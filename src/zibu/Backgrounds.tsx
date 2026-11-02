import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Scene } from "./types";

const SKY = {
  day: ["#7fd4ff", "#e9f9ff"],
  sunset: ["#ff9a76", "#ffe0a3"],
  night: ["#14214d", "#3a4c8c"],
};
const GRASS = {
  day: ["#8fdc6a", "#6cc84a"],
  sunset: ["#9ccf5e", "#78b847"],
  night: ["#3f7a52", "#2f6342"],
};

const Cloud: React.FC<{ x: number; y: number; s: number; speed: number; night?: boolean }> = ({ x, y, s, speed, night }) => {
  const frame = useCurrentFrame();
  return (
    <svg width={260 * s} height={120 * s} viewBox="0 0 260 120"
      style={{ position: "absolute", left: ((x + frame * speed) % 2300) - 300, top: y, opacity: night ? 0.25 : 1 }}>
      <g fill="white">
        <circle cx={70} cy={70} r={45} /><circle cx={130} cy={50} r={50} /><circle cx={190} cy={72} r={40} />
        <rect x={60} y={70} width={150} height={45} rx={22} />
      </g>
    </svg>
  );
};

const Stars: React.FC<{ n?: number }> = ({ n = 60 }) => {
  const frame = useCurrentFrame();
  return (
    <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
      {Array.from({ length: n }, (_, i) => {
        const x = (i * 193) % 1920;
        const y = (i * 97) % 620;
        const tw = 0.5 + 0.5 * Math.sin(frame / (8 + (i % 7)) + i);
        return <circle key={i} cx={x} cy={y} r={2 + (i % 3)} fill="#fffbe0" opacity={0.35 + tw * 0.65} />;
      })}
    </svg>
  );
};

const SunOrMoon: React.FC<{ time: Scene["time"]; big?: boolean }> = ({ time, big }) => {
  const frame = useCurrentFrame();
  if (time === "night") {
    const r = big ? 170 : 80;
    return (
      <svg width={r * 3} height={r * 3} style={{ position: "absolute", right: big ? 200 : 140, top: big ? 60 : 70 }}>
        <circle cx={r * 1.5} cy={r * 1.5} r={r * 1.4} fill="rgba(255,250,210,0.12)" />
        <circle cx={r * 1.5} cy={r * 1.5} r={r} fill="#fff6c9" />
        <circle cx={r * 1.2} cy={r * 1.3} r={r * 0.18} fill="#efe3a8" />
        <circle cx={r * 1.8} cy={r * 1.8} r={r * 0.12} fill="#efe3a8" />
        <path d={`M${r * 1.25} ${r * 1.65} Q ${r * 1.5} ${r * 1.85} ${r * 1.75} ${r * 1.65}`} stroke="#c9b46a" strokeWidth={r * 0.05} fill="none" strokeLinecap="round" />
      </svg>
    );
  }
  const low = time === "sunset";
  return (
    <svg width={260} height={260} viewBox="0 0 260 260" style={{ position: "absolute", right: 120, top: low ? 330 : 60 }}>
      <g style={{ transformOrigin: "130px 130px", rotate: `${frame * 0.6}deg` }}>
        {Array.from({ length: 12 }, (_, i) => (
          <rect key={i} x={124} y={0} width={12} height={40} rx={6} fill={low ? "#ff9d3c" : "#ffc93c"}
            style={{ transformOrigin: "130px 130px", rotate: `${i * 30}deg` }} />
        ))}
      </g>
      <circle cx={130} cy={130} r={78} fill={low ? "#ffb04d" : "#ffdb4d"} />
      <circle cx={106} cy={122} r={8} fill="#7a4a00" /><circle cx={154} cy={122} r={8} fill="#7a4a00" />
      <path d="M100 148 Q 130 175 160 148" stroke="#7a4a00" strokeWidth={7} fill="none" strokeLinecap="round" />
    </svg>
  );
};

const Flowers: React.FC<{ night: boolean }> = ({ night }) => {
  const frame = useCurrentFrame();
  return (
    <svg width={1920} height={1080} style={{ position: "absolute", inset: 0, opacity: night ? 0.7 : 1 }}>
      {[120, 380, 640, 1180, 1460, 1760].map((x, i) => (
        <g key={x} style={{ transformOrigin: `${x}px 1040px`, rotate: `${Math.sin(frame / 15 + i) * 6}deg` }}>
          <line x1={x} y1={1040} x2={x} y2={990} stroke="#3e9a2c" strokeWidth={6} />
          {[0, 72, 144, 216, 288].map((a) => (
            <circle key={a} cx={x + Math.cos((a * Math.PI) / 180) * 15} cy={980 + Math.sin((a * Math.PI) / 180) * 15}
              r={12} fill={["#ff7aa8", "#ffffff", "#ffb84d"][i % 3]} />
          ))}
          <circle cx={x} cy={980} r={10} fill="#ffd43b" />
        </g>
      ))}
    </svg>
  );
};

const Tree: React.FC<{ x: number; s: number; dark: boolean }> = ({ x, s, dark }) => (
  <svg width={300 * s} height={520 * s} viewBox="0 0 300 520" style={{ position: "absolute", left: x, bottom: 120 }}>
    <rect x={125} y={260} width={50} height={260} rx={18} fill={dark ? "#4a3326" : "#8b5a3c"} />
    <circle cx={150} cy={170} r={120} fill={dark ? "#1f5a3a" : "#3fae49"} />
    <circle cx={80} cy={230} r={80} fill={dark ? "#246642" : "#4cbc55"} />
    <circle cx={220} cy={230} r={80} fill={dark ? "#246642" : "#4cbc55"} />
  </svg>
);

const Room: React.FC<{ time: Scene["time"] }> = ({ time }) => {
  const night = time === "night";
  return (
    <AbsoluteFill style={{ background: night ? "#4a4f8a" : time === "sunset" ? "#ffd9b0" : "#ffe9c7" }}>
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        {/* papel pintado con lunares */}
        {Array.from({ length: 60 }, (_, i) => (
          <circle key={i} cx={(i % 12) * 170 + (Math.floor(i / 12) % 2) * 85 + 40} cy={Math.floor(i / 12) * 150 + 60} r={14}
            fill={night ? "rgba(255,255,255,0.08)" : "rgba(255,160,120,0.25)"} />
        ))}
        {/* ventana */}
        <rect x={1300} y={150} width={420} height={380} rx={20} fill={night ? "#14214d" : time === "sunset" ? "#ff9a76" : "#9fdcff"} stroke="#b77a35" strokeWidth={18} />
        {night ? <circle cx={1600} cy={260} r={50} fill="#fff6c9" /> : <circle cx={1600} cy={260} r={55} fill={time === "sunset" ? "#ffb04d" : "#ffdb4d"} />}
        {night && [[1380, 220], [1450, 400], [1530, 330], [1660, 440], [1400, 470]].map(([x, y]) => <circle key={x} cx={x} cy={y} r={5} fill="#fffbe0" />)}
        <line x1={1510} y1={150} x2={1510} y2={530} stroke="#b77a35" strokeWidth={14} />
        <line x1={1300} y1={340} x2={1720} y2={340} stroke="#b77a35" strokeWidth={14} />
        {/* cuadro */}
        <rect x={300} y={200} width={260} height={200} rx={10} fill="#fff" stroke="#ff9f1c" strokeWidth={14} />
        <path d="M320 380 L 400 290 L 460 350 L 500 310 L 540 380 Z" fill="#6cc84a" /><circle cx={480} cy={250} r={22} fill="#ffd23f" />
        {/* suelo y alfombra */}
        <rect x={0} y={760} width={1920} height={320} fill={night ? "#7a5a4a" : "#d9a774"} />
        {Array.from({ length: 12 }, (_, i) => <line key={i} x1={i * 170} y1={760} x2={i * 170 - 60} y2={1080} stroke="rgba(0,0,0,0.08)" strokeWidth={4} />)}
        <ellipse cx={960} cy={960} rx={620} ry={95} fill={night ? "#8a5fbf" : "#ff9fc2"} />
        <ellipse cx={960} cy={960} rx={520} ry={70} fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth={8} strokeDasharray="30 20" />
        {/* cama */}
        <rect x={40} y={600} width={420} height={200} rx={30} fill="#7fc8ff" />
        <rect x={40} y={560} width={110} height={260} rx={20} fill="#b77a35" />
        <ellipse cx={230} cy={600} rx={70} ry={34} fill="white" />
      </svg>
    </AbsoluteFill>
  );
};

const Beach: React.FC<{ time: Scene["time"] }> = ({ time }) => {
  const frame = useCurrentFrame();
  const night = time === "night";
  return (
    <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
      <rect x={0} y={600} width={1920} height={260} fill={night ? "#1f4f8a" : "#3fa9f5"} />
      {Array.from({ length: 14 }, (_, i) => (
        <path key={i} d={`M${((i * 160 + frame * 2) % 2100) - 100} ${640 + (i % 4) * 50} q 25 -14 50 0 q 25 14 50 0`}
          stroke="rgba(255,255,255,0.6)" strokeWidth={5} fill="none" strokeLinecap="round" />
      ))}
      <path d={`M0 840 Q 480 ${800 + Math.sin(frame / 20) * 10} 960 830 T 1920 820 V 1080 H 0 Z`} fill="rgba(255,255,255,0.75)" />
      <path d="M0 860 Q 480 820 960 850 T 1920 840 V 1080 H 0 Z" fill={night ? "#c9b27a" : "#ffe2a3"} />
      {/* palmera */}
      <path d="M1700 1000 Q 1690 800 1640 620" stroke="#a0703f" strokeWidth={36} fill="none" strokeLinecap="round" />
      {[-60, -20, 20, 60, 100].map((a) => (
        <ellipse key={a} cx={1640} cy={620} rx={150} ry={34} fill={night ? "#2f6a45" : "#3cc45a"}
          style={{ transformOrigin: "1640px 620px", rotate: `${a + Math.sin(frame / 25) * 4}deg`, translate: "120px 0px" }} />
      ))}
      <circle cx={1660} cy={650} r={20} fill="#7a4a1a" /><circle cx={1690} cy={660} r={20} fill="#7a4a1a" />
    </svg>
  );
};

export const Backdrop: React.FC<{ bg: Scene["bg"]; time: Scene["time"] }> = ({ bg, time }) => {
  const frame = useCurrentFrame();
  const night = time === "night";
  if (bg === "room") return <Room time={time} />;
  const [s1, s2] = SKY[time];
  const [g1, g2] = GRASS[time];
  return (
    <AbsoluteFill style={{ background: bg === "sky" ? "linear-gradient(#0d1640, #2b3a7a 70%, #4a5aa0)" : `linear-gradient(${s1} 0%, ${s2} 75%)` }}>
      {(night || bg === "sky") && <Stars n={bg === "sky" ? 110 : 60} />}
      {bg !== "sky" && <SunOrMoon time={time} big={bg === "hill"} />}
      {bg !== "sky" && bg !== "forest" && (
        <>
          <Cloud x={100} y={110} s={1} speed={0.5} night={night} />
          <Cloud x={900} y={60} s={0.75} speed={0.35} night={night} />
          <Cloud x={1500} y={200} s={0.9} speed={0.45} night={night} />
        </>
      )}
      {bg === "beach" && <Beach time={time} />}
      {bg === "garden" && (
        <>
          <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
            <path d="M0 760 Q 480 640 960 740 T 1920 720 V1080 H0 Z" fill={g1} />
            <path d="M0 850 Q 600 760 1100 850 T 1920 830 V1080 H0 Z" fill={g2} />
          </svg>
          <Flowers night={night} />
        </>
      )}
      {bg === "forest" && (
        <>
          <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
            <path d="M0 820 Q 960 760 1920 820 V1080 H0 Z" fill={night ? "#26493a" : g1} />
          </svg>
          {[-60, 260, 560, 900, 1220, 1540].map((x, i) => <Tree key={x} x={x} s={i % 2 ? 1.05 : 1.25} dark={night} />)}
          <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
            <path d="M0 900 Q 960 860 1920 900 V1080 H0 Z" fill={night ? "#2f5a3f" : g2} />
          </svg>
        </>
      )}
      {bg === "river" && (
        <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
          <path d="M0 740 Q 480 660 960 720 T 1920 700 V1080 H0 Z" fill={g1} />
          <path d="M520 1080 Q 600 940 700 900 L 1500 900 Q 1600 940 1680 1080 Z" fill={night ? "#2c5c9c" : "#4aa8ff"} />
          {Array.from({ length: 8 }, (_, i) => (
            <path key={i} d={`M${640 + i * 110 + ((frame * 1.5) % 110)} ${960 + (i % 3) * 30} q 20 -10 40 0`} stroke="rgba(255,255,255,0.55)" strokeWidth={5} fill="none" strokeLinecap="round" />
          ))}
          <path d="M0 1080 L 0 930 Q 300 900 600 940 Q 560 1010 520 1080 Z" fill={g2} />
          <path d="M1920 1080 L 1920 930 Q 1650 900 1520 940 Q 1600 1010 1680 1080 Z" fill={g2} />
        </svg>
      )}
      {bg === "hill" && (
        <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
          <path d="M0 1080 L 0 900 Q 600 700 960 740 Q 1400 780 1920 950 L 1920 1080 Z" fill={night ? "#3a6b4a" : g1} />
          <path d="M0 1080 L 0 1000 Q 700 900 1920 1020 L 1920 1080 Z" fill={night ? "#2f5a3f" : g2} />
        </svg>
      )}
      {bg === "sky" && (
        <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
          {Array.from({ length: 9 }, (_, i) => (
            <circle key={i} cx={i * 240 + Math.sin(frame / 40 + i) * 20} cy={1060} r={170} fill="rgba(255,255,255,0.85)" />
          ))}
        </svg>
      )}
    </AbsoluteFill>
  );
};
