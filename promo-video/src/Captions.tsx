import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from "remotion";
import captionsData from "../captions.json";
import {C, F} from "./theme";

type Caption = {
  start: number;
  end: number;
  text: string;
};

const CAPTIONS = captionsData as Caption[];

export const Captions = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const time = frame / fps;
  const active = CAPTIONS.find(
    (caption) => time >= caption.start && time < caption.end,
  );

  if (!active) {
    return null;
  }

  const fadeIn = interpolate(
    time,
    [active.start, active.start + 0.16],
    [0, 1],
    {extrapolateLeft: "clamp", extrapolateRight: "clamp"},
  );
  const fadeOut = interpolate(
    time,
    [active.end - 0.16, active.end],
    [1, 0],
    {extrapolateLeft: "clamp", extrapolateRight: "clamp"},
  );
  const opacity = Math.min(fadeIn, fadeOut);
  const translateY = (1 - opacity) * 8;

  return (
    <AbsoluteFill style={{zIndex: 40, pointerEvents: "none"}}>
      <div
        style={{
          position: "absolute",
          left: 120,
          bottom: 14,
          maxWidth: 980,
          opacity,
          transform: `translateY(${translateY}px)`,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            padding: "8px 14px",
            border: `1px solid ${C.lineStrong}`,
            borderRadius: 5,
            background: "rgba(5, 7, 10, 0.84)",
            boxShadow: "0 10px 30px rgba(0,0,0,0.35)",
          }}
        >
          <span
            style={{
              fontFamily: F.mono,
              fontSize: 10,
              letterSpacing: "0.12em",
              color: C.lime,
            }}
          >
            CC
          </span>
          <span
            style={{
              fontFamily: F.sans,
              fontSize: 23,
              lineHeight: 1.35,
              color: C.ink,
              whiteSpace: "pre-wrap",
            }}
          >
            {active.text}
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
