import { Composition } from "remotion";
import { DogifyBTS, TOTAL } from "./Video";
import { GlyphBackground } from "./Glyphs";

export const Root = () => (
  <>
    <Composition id="DogifyBTS" component={DogifyBTS} durationInFrames={TOTAL} fps={30} width={1920} height={1080} />
    <Composition id="AsciiBackground" component={GlyphBackground} durationInFrames={300} fps={30} width={1920} height={1080} />
  </>
);
