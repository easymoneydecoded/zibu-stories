export type Mood = "happy" | "laugh" | "sad" | "surprised" | "scared";
export type Action = "jump" | "bigjump" | "wave" | "shake" | "spin" | "glow";

export type Move = { who: string; to: number; toY?: number };

export type Line = {
  who: string;
  text: string;
  src: string;
  start: number; // fotograma absoluto
  dur: number;
  moveDur: number;
  mood?: Mood;
  action?: Action;
  moves?: Move[];
  show?: { text: string; color?: string | null };
  showProp?: "star" | "balloons";
  balloons?: boolean;
  glowWho?: string;
  pause?: number;
};

export type CastMember = { who: string; x: number; y?: number };

export type PropItem = {
  what: "ball" | "firefly" | "stone" | "balloon" | "bigstar" | "brightstar";
  x: number;
  y: number;
  at?: number; // indice de la frase en la que aparece
  until?: number; // indice de la frase en la que desaparece
  anim?: "bounce" | "float";
  color?: string;
};

export type Scene = {
  id: string;
  type?: "title" | "song" | "recap" | "dance";
  bg: "garden" | "forest" | "river" | "hill" | "sky";
  time: "day" | "sunset" | "night";
  cast: CastMember[];
  props?: PropItem[];
  start: number;
  end: number;
  lines: Line[];
};

export type Timeline = {
  id: string;
  lang: string;
  title: string;
  fps: number;
  durationInFrames: number;
  music: string;
  names: Record<string, string>;
  sfx: { name: string; at: number }[];
  scenes: Scene[];
};

/** Estado de un personaje en un fotograma, calculado a partir del guion. */
export type CharState = {
  talk: boolean;
  mood: Mood;
  action?: Action;
  actionFrame: number; // fotogramas desde que empezo la accion
  dancing: boolean;
  glow: boolean;
  balloons: boolean;
};
