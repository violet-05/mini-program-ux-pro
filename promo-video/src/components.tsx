import type {CSSProperties, ReactNode} from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {C, F} from "./theme";

type SceneFrameProps = {
  duration: number;
  children: ReactNode;
  fadeOut?: boolean;
  style?: CSSProperties;
};

export const SceneFrame = ({
  duration,
  children,
  fadeOut = true,
  style,
}: SceneFrameProps) => {
  const frame = useCurrentFrame();
  const fadeIn = interpolate(frame, [0, 16], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const fade = fadeOut
    ? interpolate(frame, [duration - 16, duration], [1, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : 1;
  const scale = interpolate(frame, [0, duration], [1, 1.012], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        opacity: Math.min(fadeIn, fade),
        transform: `scale(${scale})`,
        transformOrigin: "50% 50%",
        ...style,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

export const Reveal = ({
  children,
  delay = 0,
  y = 26,
  style,
}: {
  children: ReactNode;
  delay?: number;
  y?: number;
  style?: CSSProperties;
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const value = spring({
    frame: frame - delay,
    fps,
    config: {damping: 200, stiffness: 110, mass: 0.8},
  });
  const progress = Math.min(1, Math.max(0, value));
  return (
    <div
      style={{
        opacity: progress,
        transform: `translateY(${(1 - progress) * y}px)`,
        filter: `blur(${(1 - progress) * 5}px)`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

export const SectionTag = ({
  index,
  label,
  delay = 0,
}: {
  index: string;
  label: string;
  delay?: number;
}) => {
  return (
    <Reveal delay={delay} y={10}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 14,
          fontFamily: F.mono,
          fontSize: 15,
          letterSpacing: "0.18em",
          textTransform: "uppercase",
          color: C.inkDim,
        }}
      >
        <span style={{color: C.lime}}>{index}</span>
        <span style={{width: 44, height: 1, background: C.lineStrong}} />
        <span>{label}</span>
      </div>
    </Reveal>
  );
};

export const LogoMark = ({
  size = 64,
  accent = C.lime,
}: {
  size?: number;
  accent?: string;
}) => {
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: size * 0.27,
        border: `1.5px solid ${C.ink}`,
        background: "rgba(245, 241, 232, 0.035)",
        boxShadow: `inset 0 0 0 1px rgba(245, 241, 232, 0.06)`,
        flexShrink: 0,
      }}
    >
      <svg width="100%" height="100%" viewBox="0 0 64 64" fill="none">
        <path
          d="M16 45V22L26 38L36 22V45"
          stroke={accent}
          strokeWidth="3.2"
          strokeLinecap="square"
          strokeLinejoin="miter"
        />
        <path
          d="M42 45V22H48C52 22 54.5 24.2 54.5 27.8C54.5 31.4 52 33.6 48 33.6H42"
          stroke={C.ink}
          strokeWidth="2.2"
          strokeLinecap="square"
        />
        <circle cx="48" cy="17" r="2.6" fill={accent} />
      </svg>
    </div>
  );
};

export const Tag = ({
  children,
  tone = "default",
  style,
}: {
  children: ReactNode;
  tone?: "default" | "lime" | "danger";
  style?: CSSProperties;
}) => {
  const color =
    tone === "lime" ? C.lime : tone === "danger" ? C.danger : C.inkDim;
  const border =
    tone === "lime"
      ? "rgba(217, 255, 87, 0.35)"
      : tone === "danger"
        ? "rgba(255, 130, 104, 0.35)"
        : C.line;
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        border: `1px solid ${border}`,
        borderRadius: 999,
        padding: "9px 15px",
        fontFamily: F.mono,
        fontSize: 14,
        letterSpacing: "0.06em",
        color,
        background:
          tone === "lime" ? "rgba(217, 255, 87, 0.06)" : "rgba(245, 241, 232, 0.025)",
        ...style,
      }}
    >
      {children}
    </span>
  );
};

export const Stat = ({
  value,
  label,
  delay = 0,
  size = 48,
  suffix = "",
}: {
  value: number;
  label: string;
  delay?: number;
  size?: number;
  suffix?: string;
}) => {
  const frame = useCurrentFrame();
  const count = Math.round(
    interpolate(frame, [delay, delay + 34], [0, value], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }),
  );
  return (
    <div>
      <div
        style={{
          fontFamily: F.sans,
          fontSize: size,
          lineHeight: 1,
          fontWeight: 800,
          letterSpacing: "-0.05em",
          fontVariantNumeric: "tabular-nums",
          color: C.ink,
        }}
      >
        {count}
        <span style={{color: C.lime, fontSize: size * 0.48}}>{suffix}</span>
      </div>
      <div
        style={{
          marginTop: 10,
          fontFamily: F.mono,
          fontSize: 13,
          letterSpacing: "0.08em",
          color: C.inkDim,
        }}
      >
        {label}
      </div>
    </div>
  );
};

export const CheckRow = ({
  children,
  delay = 0,
  tone = "default",
}: {
  children: ReactNode;
  delay?: number;
  tone?: "default" | "lime";
}) => {
  return (
    <Reveal delay={delay} y={12}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 14,
          color: tone === "lime" ? C.ink : C.inkDim,
          fontFamily: F.sans,
          fontSize: 20,
        }}
      >
        <span
          style={{
            width: 24,
            height: 24,
            borderRadius: 999,
            border: `1px solid ${tone === "lime" ? C.lime : C.lineStrong}`,
            color: tone === "lime" ? C.lime : C.inkDim,
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            fontFamily: F.mono,
            fontSize: 13,
            flexShrink: 0,
          }}
        >
          ✓
        </span>
        {children}
      </div>
    </Reveal>
  );
};

export const GridBackground = () => {
  const frame = useCurrentFrame();
  const drift = Math.sin(frame / 210) * 22;
  const glow = Math.sin(frame / 170) * 26;

  return (
    <AbsoluteFill style={{backgroundColor: C.bg, overflow: "hidden"}}>
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle at 72% 18%, rgba(217,255,87,0.10), transparent 38%), radial-gradient(circle at 14% 84%, rgba(118,227,200,0.07), transparent 42%), radial-gradient(circle at 52% 50%, rgba(240,201,168,0.045), transparent 55%)",
        }}
      />
      <AbsoluteFill
        style={{
          backgroundImage:
            "linear-gradient(rgba(245,241,232,0.042) 1px, transparent 1px), linear-gradient(90deg, rgba(245,241,232,0.042) 1px, transparent 1px)",
          backgroundSize: "72px 72px",
          transform: `translate(${drift}px, ${drift * 0.45}px)`,
          opacity: 0.78,
        }}
      />
      <div
        style={{
          position: "absolute",
          width: 860,
          height: 860,
          right: -260,
          top: -260,
          borderRadius: "50%",
          border: `1px solid rgba(217,255,87,0.12)`,
          transform: `translateY(${glow}px)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          width: 520,
          height: 520,
          right: -90,
          top: -90,
          borderRadius: "50%",
          border: `1px dashed rgba(217,255,87,0.10)`,
          transform: `rotate(${frame / 8}deg)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          left: -220,
          bottom: -260,
          width: 700,
          height: 700,
          borderRadius: "50%",
          background:
            "radial-gradient(circle, rgba(118,227,200,0.065), transparent 67%)",
          transform: `translateY(${-glow}px)`,
        }}
      />
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle at 50% 44%, transparent 34%, rgba(0,0,0,0.58) 100%)",
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};

export const Chrome = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const opacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const progress = Math.min(1, Math.max(0, frame / (durationInFrames - 1)));

  return (
    <AbsoluteFill
      style={{
        zIndex: 50,
        pointerEvents: "none",
        opacity,
        fontFamily: F.mono,
        color: C.inkDim,
      }}
    >
      <div
        style={{
          position: "absolute",
          top: 42,
          left: 56,
          right: 56,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div style={{display: "flex", alignItems: "center", gap: 13}}>
          <LogoMark size={28} />
          <span style={{fontSize: 13, letterSpacing: "0.16em", color: C.ink}}>
            MPUX PRO
          </span>
          <span style={{width: 1, height: 16, background: C.lineStrong}} />
          <span style={{fontSize: 11, letterSpacing: "0.12em"}}>
            WECHAT MINI PROGRAM
          </span>
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            fontSize: 11,
            letterSpacing: "0.15em",
          }}
        >
          <span style={{width: 7, height: 7, borderRadius: 99, background: C.lime}} />
          <span>UX SYSTEM / 2026</span>
        </div>
      </div>

      {[
        {top: 24, left: 24, borderTop: true, borderLeft: true},
        {top: 24, right: 24, borderTop: true, borderLeft: false, borderRight: true},
        {bottom: 24, left: 24, borderTop: false, borderLeft: true, borderBottom: true},
        {
          bottom: 24,
          right: 24,
          borderTop: false,
          borderLeft: false,
          borderRight: true,
          borderBottom: true,
        },
      ].map((mark, index) => (
        <div
          key={index}
          style={{
            position: "absolute",
            width: 26,
            height: 26,
            ...mark,
            borderTop: mark.borderTop ? `1px solid ${C.lineStrong}` : undefined,
            borderLeft: mark.borderLeft ? `1px solid ${C.lineStrong}` : undefined,
            borderRight: mark.borderRight ? `1px solid ${C.lineStrong}` : undefined,
            borderBottom: mark.borderBottom ? `1px solid ${C.lineStrong}` : undefined,
            opacity: 0.7,
          }}
        />
      ))}

      <div
        style={{
          position: "absolute",
          left: 0,
          bottom: 0,
          width: `${progress * 100}%`,
          height: 3,
          background: `linear-gradient(90deg, ${C.lime}, ${C.teal})`,
          opacity: 0.65,
        }}
      />
    </AbsoluteFill>
  );
};

export const Phone = ({
  src,
  width,
  label,
  rotate = 0,
  opacity = 1,
  style,
  glow = false,
}: {
  src: string;
  width: number;
  label?: string;
  rotate?: number;
  opacity?: number;
  style?: CSSProperties;
  glow?: boolean;
}) => {
  const height = width * (762 / 353);
  return (
    <div
      style={{
        width,
        opacity,
        transform: `rotate(${rotate}deg)`,
        ...style,
      }}
    >
      <div
        style={{
          width,
          height,
          borderRadius: width * 0.125,
          padding: Math.max(7, width * 0.028),
          background: "#050607",
          border: `1px solid ${glow ? "rgba(217,255,87,0.55)" : C.lineStrong}`,
          boxShadow: glow
            ? "0 30px 90px rgba(0,0,0,0.65), 0 0 0 1px rgba(217,255,87,0.14), 0 0 80px rgba(217,255,87,0.10)"
            : "0 24px 70px rgba(0,0,0,0.55)",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <Img
          src={staticFile(src)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            borderRadius: width * 0.10,
            display: "block",
          }}
        />
        <div
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: width * 0.10,
            background:
              "linear-gradient(120deg, rgba(255,255,255,0.08), transparent 22%, transparent 78%, rgba(255,255,255,0.025))",
            pointerEvents: "none",
          }}
        />
      </div>
      {label ? (
        <div
          style={{
            marginTop: 18,
            textAlign: "center",
            fontFamily: F.mono,
            fontSize: 13,
            letterSpacing: "0.16em",
            color: C.inkDim,
            textTransform: "uppercase",
          }}
        >
          {label}
        </div>
      ) : null}
    </div>
  );
};
