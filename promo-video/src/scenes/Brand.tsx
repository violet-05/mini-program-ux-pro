import {useCurrentFrame} from "remotion";
import {C, F} from "../theme";
import {LogoMark, Reveal, SceneFrame, SectionTag, Tag} from "../components";

export const Brand = () => {
  const frame = useCurrentFrame();
  const ringRotation = frame / 7;
  const pulse = 1 + Math.sin(frame / 22) * 0.015;

  return (
    <SceneFrame duration={220}>
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: 154,
          width: 1320,
          transform: "translateX(-50%)",
          display: "flex",
          justifyContent: "center",
        }}
      >
        <SectionTag index="02" label="MEET THE SYSTEM" />
      </div>

      <div
        style={{
          position: "absolute",
          left: "50%",
          top: 230,
          width: 1260,
          transform: "translateX(-50%)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <div style={{position: "relative", width: 230, height: 230, display: "flex", alignItems: "center", justifyContent: "center"}}>
          <div
            style={{
              position: "absolute",
              inset: 0,
              borderRadius: "50%",
              border: `1px solid rgba(217,255,87,0.18)`,
              transform: `rotate(${ringRotation}deg) scale(${pulse})`,
            }}
          />
          <div
            style={{
              position: "absolute",
              inset: 30,
              borderRadius: "50%",
              border: `1px dashed rgba(245,241,232,0.16)`,
              transform: `rotate(${-ringRotation * 0.7}deg)`,
            }}
          />
          <Reveal delay={4} y={30}>
            <LogoMark size={112} />
          </Reveal>
        </div>

        <Reveal delay={12} y={30}>
          <div
            style={{
              marginTop: 36,
              fontFamily: F.display,
              fontSize: 86,
              lineHeight: 0.98,
              fontWeight: 800,
              letterSpacing: "-0.065em",
              color: C.ink,
            }}
          >
            MINI PROGRAM
            <br />
            <span style={{color: C.lime}}>UX PRO</span>
          </div>
        </Reveal>

        <Reveal delay={24}>
          <div
            style={{
              marginTop: 26,
              fontFamily: F.sans,
              fontSize: 28,
              letterSpacing: "0.08em",
              color: C.inkDim,
            }}
          >
            微信小程序 UX 设计智能
          </div>
        </Reveal>

        <Reveal delay={34}>
          <p
            style={{
              margin: "28px 0 0",
              maxWidth: 760,
              fontFamily: F.sans,
              fontSize: 24,
              lineHeight: 1.8,
              color: C.ink,
            }}
          >
            把设计判断变成
            <span style={{color: C.lime}}> 可检索、可解释、可验证 </span>
            的流程。
          </p>
        </Reveal>

        <Reveal delay={47}>
          <div style={{display: "flex", gap: 10, marginTop: 32}}>
            <Tag tone="lime">31 类产品</Tag>
            <Tag>347 条知识</Tag>
            <Tag>3 种技术栈</Tag>
            <Tag>本地运行</Tag>
          </div>
        </Reveal>
      </div>

      <Reveal
        delay={70}
        style={{
          position: "absolute",
          left: 120,
          right: 120,
          bottom: 84,
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            borderTop: `1px solid ${C.line}`,
            paddingTop: 18,
            fontFamily: F.mono,
            fontSize: 12,
            letterSpacing: "0.14em",
            color: C.inkFaint,
          }}
        >
          <span>
            NOT A TEMPLATE LIBRARY
            <span style={{color: C.lime, marginLeft: 12}}>/</span>
            A DESIGN DECISION SYSTEM
          </span>
          <span>MPUX / V1.0.0</span>
        </div>
      </Reveal>

      <div
        style={{
          position: "absolute",
          right: 60,
          top: 180,
          fontFamily: F.mono,
          fontSize: 340,
          lineHeight: 0.7,
          letterSpacing: "-0.08em",
          color: "rgba(245,241,232,0.025)",
        }}
      >
        1.0
      </div>
    </SceneFrame>
  );
};
