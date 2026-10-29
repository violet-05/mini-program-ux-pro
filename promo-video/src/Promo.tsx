import type {ComponentType} from "react";
import {AbsoluteFill, Audio, Sequence, staticFile} from "remotion";
import {Captions} from "./Captions";
import {Chrome, GridBackground} from "./components";
import {SCENES} from "./theme";
import {Brand} from "./scenes/Brand";
import {Close} from "./scenes/Close";
import {Intro} from "./scenes/Intro";
import {Knowledge} from "./scenes/Knowledge";
import {Proof} from "./scenes/Proof";
import {System} from "./scenes/System";
import {Workflow} from "./scenes/Workflow";

const SCENE_COMPONENTS: Record<string, ComponentType> = {
  intro: Intro,
  brand: Brand,
  workflow: Workflow,
  knowledge: Knowledge,
  system: System,
  proof: Proof,
  close: Close,
};

export const Promo = () => {
  return (
    <AbsoluteFill>
      <GridBackground />
      <Audio src={staticFile("audio/bed.mp3")} volume={0.55} />
      <Audio src={staticFile("audio/voiceover.mp3")} volume={1} />
      {SCENES.map((scene) => {
        const Scene = SCENE_COMPONENTS[scene.id];
        return (
          <Sequence
            key={scene.id}
            from={scene.from}
            durationInFrames={scene.duration}
          >
            <Scene />
          </Sequence>
        );
      })}
      <Captions />
      <Chrome />
    </AbsoluteFill>
  );
};
