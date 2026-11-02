import { Composition, Still } from "remotion";
import { Avatar, Banner, BrandProps, Thumbnail } from "./zibu/Branding";
import { calculateEpisode, Episode, EpisodeProps } from "./zibu/Episode";

// Un episodio se elige con --props='{"episode":"ep001-lost-star","lang":"es"}'
export const RemotionRoot: React.FC = () => {
  return (
    <>
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
      {/* Imagenes del canal: npx remotion still Banner out/banner-es.png --props='{"lang":"es"}' */}
      <Still id="Avatar" component={Avatar} width={800} height={800} defaultProps={{ lang: "en" } satisfies BrandProps} />
      <Still id="Banner" component={Banner} width={2560} height={1440} defaultProps={{ lang: "en" } satisfies BrandProps} />
      <Still id="Thumbnail" component={Thumbnail} width={1280} height={720} defaultProps={{ lang: "en" } satisfies BrandProps} />
    </>
  );
};
