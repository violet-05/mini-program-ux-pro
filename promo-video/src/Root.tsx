import {Composition} from "remotion";
import {Promo} from "./Promo";
import {VIDEO} from "./theme";

export const RemotionRoot = () => {
  return (
    <Composition
      id="MPUXPromo"
      component={Promo}
      durationInFrames={VIDEO.durationInFrames}
      fps={VIDEO.fps}
      width={VIDEO.width}
      height={VIDEO.height}
    />
  );
};
