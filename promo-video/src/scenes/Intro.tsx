import {useCurrentFrame, useVideoConfig} from "remotion";
import {C, F} from "../theme";
import {Reveal, SceneFrame, SectionTag, Tag} from "../components";

const WireframePhone = ({
  label,
  delay,
  rotate,
}: {
  label: string;
  delay: number;
  rotate: number;
}) => {
  return (
    <Reveal delay={delay} y={54}>
      <div
        style={{
          width: 176,
          height: 356,
          transform: `rotate(${rotate}deg)`,
          border: `1px solid ${C.lineStrong}`,
          borderRadius: 26,
          background: "rgba(17, 21, 26, 0.82)",
          padding: 14,
          position: "relative",
          boxShadow: "0 24px 60px rgba(0,0,0,0.35)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 14,
          }}
        >
          <span
            style={{
              fontFamily: F.mono,
              fontSize: 9,
              letterSpacing: "0.12em",
              color: C.inkDim,
            }}
          >
            {label}
          </span>
          <span
            style={{
              border: `1px solid rgba(255,130,104,0.4)`,
              color: C.danger,
              fontFamily: F.mono,
              fontSize: 7,
              letterSpacing: "0.1em",
              padding: "3px 5px",
              borderRadius: 3,
            }}
          >
            TEMPLATE
          </span>
        </div>
        <div style={{display: "flex", gap: 8, marginBottom: 14}}>
          <div style={{width: 30, height: 30, borderRadius: 8, background: "rgba(245,241,232,0.12)"}} />
          <div style={{flex: 1, paddingTop: 3}}>
            <div style={{height: 7, width: "74%", background: "rgba(245,241,232,0.24)", marginBottom: 7}} />
            <div style={{height: 5, width: "48%", background: "rgba(245,241,232,0.12)"}} />
          </div>
        </div>
        <div
          style={{
            height: 96,
            borderRadius: 10,
            background:
              "linear-gradient(135deg, rgba(245,241,232,0.12), rgba(245,241,232,0.035))",
            border: `1px solid ${C.line}`,
            position: "relative",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              position: "absolute",
              width: 72,
              height: 72,
              borderRadius: "50%",
              border: "1px solid rgba(245,241,232,0.22)",
              right: 14,
              top: 12,
            }}
          />
        </div>
        <div style={{display: "flex", gap: 8, marginTop: 16}}>
          {[0, 1, 2, 3].map((item) => (
            <div
              key={item}
              style={{
                flex: 1,
                height: 44,
                borderRadius: 8,
                border: `1px solid ${C.line}`,
                background: "rgba(245,241,232,0.035)",
              }}
            />
          ))}
        </div>
        <div style={{marginTop: 16, display: "flex", flexDirection: "column", gap: 8}}>
          <div style={{height: 6, width: "90%", background: "rgba(245,241,232,0.18)"}} />
          <div style={{height: 6, width: "66%", background: "rgba(245,241,232,0.10)"}} />
          <div style={{height: 6, width: "78%", background: "rgba(245,241,232,0.10)"}} />
        </div>
        <div
          style={{
            position: "absolute",
            left: 14,
            right: 14,
            bottom: 14,
            height: 28,
            borderRadius: 8,
            background: "rgba(217,255,87,0.20)",
            border: "1px solid rgba(217,255,87,0.35)",
          }}
        />
      </div>
    </Reveal>
  );
};

export const Intro = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const lineHeight = Math.min(1, frame / (fps * 1.4));

  return (
    <SceneFrame duration={190}>
      <div
        style={{
          position: "absolute",
          left: 120,
          top: 122,
          width: 980,
        }}
      >
        <SectionTag index="01" label="THE PROBLEM" />
        <Reveal delay={10}>
          <h1
            style={{
              margin: "42px 0 0",
              fontFamily: F.display,
              fontSize: 86,
              lineHeight: 1.14,
              fontWeight: 800,
              letterSpacing: "-0.055em",
              color: C.ink,
            }}
          >
            AI 做的小程序，
            <br />
            为什么都<span style={{color: C.lime}}>长一个样？</span>
          </h1>
        </Reveal>
        <Reveal delay={24}>
          <p
            style={{
              margin: "34px 0 0",
              width: 780,
              fontFamily: F.sans,
              fontSize: 25,
              lineHeight: 1.85,
              color: C.inkDim,
            }}
          >
            搜索框、轮播、四宫格、卡片。
            <br />
            模板生成得越快，品牌就越模糊。
          </p>
        </Reveal>
        <Reveal delay={39}>
          <div style={{display: "flex", gap: 10, marginTop: 40}}>
            <Tag tone="danger">NO CONTEXT</Tag>
            <Tag>NO STATES</Tag>
            <Tag>NO PLATFORM</Tag>
          </div>
        </Reveal>
        <div
          style={{
            width: 2,
            height: 250,
            background: C.lime,
            position: "absolute",
            right: -48,
            top: 76,
            transform: `scaleY(${lineHeight})`,
            transformOrigin: "top",
            opacity: 0.75,
          }}
        />
      </div>

      <div
        style={{
          position: "absolute",
          right: 104,
          top: 216,
          width: 660,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            marginBottom: 18,
            fontFamily: F.mono,
            fontSize: 12,
            letterSpacing: "0.12em",
            color: C.inkFaint,
          }}
        >
          <span style={{width: 6, height: 6, borderRadius: 99, background: C.danger}} />
          <span>SAME STRUCTURE × 3</span>
          <span style={{flex: 1, height: 1, background: C.line}} />
        </div>
        <div style={{display: "flex", gap: 16, alignItems: "flex-start"}}>
          <WireframePhone label="HOME" delay={22} rotate={-5} />
          <WireframePhone label="SEARCH" delay={30} rotate={0} />
          <WireframePhone label="PROFILE" delay={38} rotate={5} />
        </div>
        <Reveal delay={56}>
          <div
            style={{
              marginTop: 20,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              borderTop: `1px solid ${C.line}`,
              paddingTop: 14,
              fontFamily: F.mono,
              fontSize: 11,
              letterSpacing: "0.12em",
              color: C.inkFaint,
            }}
          >
            <span>EVERY PRODUCT / ONE LAYOUT</span>
            <span style={{color: C.danger}}>TEMPLATE FATIGUE</span>
          </div>
        </Reveal>
      </div>

      <Reveal
        delay={94}
        style={{
          position: "absolute",
          left: 120,
          bottom: 96,
          display: "flex",
          alignItems: "center",
          gap: 14,
          fontFamily: F.mono,
          fontSize: 14,
          letterSpacing: "0.14em",
          color: C.lime,
        }}
      >
        <span>MOVE BEYOND THE TEMPLATE</span>
        <span style={{fontSize: 20}}>→</span>
      </Reveal>

      <div
        style={{
          position: "absolute",
          right: 110,
          bottom: 30,
          fontFamily: F.sans,
          fontSize: 220,
          fontWeight: 800,
          lineHeight: 0.8,
          letterSpacing: "-0.08em",
          color: "rgba(245,241,232,0.035)",
        }}
      >
        01
      </div>
    </SceneFrame>
  );
};
