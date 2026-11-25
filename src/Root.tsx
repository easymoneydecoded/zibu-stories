import { Composition, Still } from "remotion";
import { AIThumb, Avatar, Banner, BrandProps, calculateThumb, CastProps, CastSheet, Thumbnail, ThumbProps } from "./zibu/Branding";
import { Catalog, CatalogBgs } from "./zibu/Catalog";
import { calculateEpisode, Episode, EpisodeProps } from "./zibu/Episode";
import { EpisodeV2 } from "./zibu/EpisodeV2";

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
      <Composition id="EpisodeV2" component={EpisodeV2} durationInFrames={300} fps={30} width={1920} height={1080}
        defaultProps={{ episode: "ep023-zibu-piglet-colorful-balloons", lang: "es" } satisfies EpisodeProps}
        calculateMetadata={calculateEpisode} />
      {/* Imagenes del canal: npx remotion still Banner out/banner-es.png --props='{"lang":"es"}' */}
      <Still id="Avatar" component={Avatar} width={800} height={800} defaultProps={{ lang: "en" } satisfies BrandProps} />
      <Still id="Banner" component={Banner} width={2560} height={1440} defaultProps={{ lang: "en" } satisfies BrandProps} />
      <Still id="Thumbnail" component={Thumbnail} width={1280} height={720}
        defaultProps={{ lang: "en", episode: "ep001-lost-star" } satisfies ThumbProps} calculateMetadata={calculateThumb} />
      <Still id="AIThumb" component={AIThumb} width={1280} height={720}
        defaultProps={{ lang: "en", episode: "ep001-lost-star" } satisfies ThumbProps} calculateMetadata={calculateThumb} />
      {/* Lamina de todo lo dibujable: npx remotion still Catalog out/catalogo.png */}
      <Still id="Catalog" component={Catalog} width={1960} height={2000} />
      <Still id="CatalogBgs" component={CatalogBgs} width={1960} height={2000} />
      {/* Referencia para la IA: npx remotion still CastSheet public/ref/cast-piglet.png --props='{"species":"piglet"}' */}
      <Still id="CastSheet" component={CastSheet} width={1280} height={720} defaultProps={{ species: "piglet" } satisfies CastProps} />
    </>
  );
};
