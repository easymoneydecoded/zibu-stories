import { Composition } from "remotion";
import { calculateEpisode, Episode, EpisodeProps } from "./zibu/Episode";

// Un episodio se elige con --props='{"episode":"ep001-lost-star","lang":"es"}'
export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Episode"
      component={Episode}
      durationInFrames={300}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{ episode: "ep001-lost-star", lang: "en" } satisfies EpisodeProps}
      calculateMetadata={calculateEpisode}
    />
  );
};
