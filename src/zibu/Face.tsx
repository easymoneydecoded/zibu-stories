import { useCurrentFrame } from "remotion";
import { Mood } from "./types";

/**
 * Cara comun de los personajes (coordenadas del SVG de cada uno): ojos con parpadeo y
 * expresion, mejillas y boca que se abre al hablar.
 */
export const Face: React.FC<{
  cx: number;
  eyeY: number;
  eyeDx: number;
  eyeR: number;
  mouthY: number;
  mouthW: number;
  mood: Mood;
  talk: boolean;
  ink?: string;
  cheek?: string;
  seed?: number;
}> = ({ cx, eyeY, eyeDx, eyeR, mouthY, mouthW, mood, talk, ink = "#1d3d73", cheek = "#ff8fb1", seed = 0 }) => {
  const frame = useCurrentFrame();
  const blink = (frame + seed * 37) % 110 > 104 ? 0.1 : 1;
  const open = talk ? 8 + Math.abs(Math.sin((frame + seed) / 2.3)) * 22 : 0;
  const look = Math.sin((frame + seed * 50) / 45) * eyeR * 0.12;
  const big = mood === "surprised" || mood === "scared" ? 1.15 : 1;
  const pupil = mood === "scared" ? 0.38 : mood === "surprised" ? 0.42 : 0.5;
  const sw = eyeR * 0.11;

  const eyes = [-1, 1].map((side) => {
    const x = cx + side * eyeDx;
    if (mood === "laugh" && !talk) {
      return (
        <path key={side} d={`M${x - eyeR * 0.8} ${eyeY + 4} Q ${x} ${eyeY - eyeR * 0.9} ${x + eyeR * 0.8} ${eyeY + 4}`}
          stroke={ink} strokeWidth={sw * 1.4} fill="none" strokeLinecap="round" />
      );
    }
    return (
      <g key={side}>
        <ellipse cx={x} cy={eyeY} rx={eyeR * 0.9 * big} ry={eyeR * big * blink} fill="white" stroke={ink} strokeWidth={sw} />
        {blink > 0.5 && (
          <>
            <circle cx={x + look} cy={eyeY + eyeR * 0.12} r={eyeR * pupil} fill={ink} />
            <circle cx={x + look + eyeR * 0.18} cy={eyeY - eyeR * 0.1} r={eyeR * 0.17} fill="white" />
          </>
        )}
        {(mood === "sad" || mood === "scared") && (
          <path
            d={mood === "sad"
              ? `M${x - side * eyeR * 0.9} ${eyeY - eyeR * 1.15} L ${x + side * eyeR * 0.7} ${eyeY - eyeR * 1.45}`
              : `M${x - eyeR * 0.8} ${eyeY - eyeR * 1.5} Q ${x} ${eyeY - eyeR * 1.9} ${x + eyeR * 0.8} ${eyeY - eyeR * 1.5}`}
            stroke={ink} strokeWidth={sw * 1.2} fill="none" strokeLinecap="round" />
        )}
      </g>
    );
  });

  const w = mouthW;
  let mouth: React.ReactNode;
  if (mood === "surprised" || (mood === "scared" && !talk)) {
    mouth = <ellipse cx={cx} cy={mouthY + 10} rx={w * 0.32} ry={14 + open * 0.6} fill="#b3243f" stroke={ink} strokeWidth={sw} />;
  } else if (mood === "sad" && !talk) {
    mouth = <path d={`M${cx - w * 0.7} ${mouthY + 18} Q ${cx} ${mouthY - 6} ${cx + w * 0.7} ${mouthY + 18}`} stroke={ink} strokeWidth={sw * 1.2} fill="none" strokeLinecap="round" />;
  } else if (mood === "laugh") {
    const h = 34 + open * 0.8;
    mouth = (
      <g>
        <path d={`M${cx - w} ${mouthY} L ${cx + w} ${mouthY} Q ${cx} ${mouthY + h * 1.6} ${cx - w} ${mouthY} Z`} fill="#b3243f" stroke={ink} strokeWidth={sw} strokeLinejoin="round" />
        <ellipse cx={cx} cy={mouthY + h * 0.62} rx={w * 0.36} ry={h * 0.22} fill="#ff6f8f" />
      </g>
    );
  } else {
    const o = talk ? open : 6;
    mouth = (
      <g>
        <path d={`M${cx - w} ${mouthY} Q ${cx} ${mouthY + 14 + o} ${cx + w} ${mouthY} Q ${cx} ${mouthY + 14 + o * 1.9} ${cx - w} ${mouthY} Z`}
          fill="#b3243f" stroke={ink} strokeWidth={sw} strokeLinejoin="round" />
        {o > 14 && <ellipse cx={cx} cy={mouthY + 12 + o * 1.1} rx={w * 0.38} ry={o * 0.26} fill="#ff6f8f" />}
      </g>
    );
  }

  return (
    <g>
      {eyes}
      <ellipse cx={cx - eyeDx * 1.3} cy={mouthY - 8} rx={eyeR * 0.5} ry={eyeR * 0.3} fill={cheek} opacity={0.75} />
      <ellipse cx={cx + eyeDx * 1.3} cy={mouthY - 8} rx={eyeR * 0.5} ry={eyeR * 0.3} fill={cheek} opacity={0.75} />
      {mouth}
      {mood === "sad" && (
        <ellipse cx={cx + eyeDx * 1.05} cy={eyeY + eyeR * 1.1 + (frame % 36) * 1.6} rx={eyeR * 0.16} ry={eyeR * 0.24}
          fill="#7fc8ff" opacity={1 - (frame % 36) / 40} />
      )}
    </g>
  );
};
