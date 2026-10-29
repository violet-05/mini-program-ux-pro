import {C, F} from "../theme";
import {LogoMark, Reveal, SceneFrame, SectionTag, Tag} from "../components";

export const Close = () => {
  return (
    <SceneFrame duration={125} fadeOut={false}>
      <div style={{position: "absolute", left: 120, top: 148, width: 1150}}>
        <SectionTag index="07" label="GET STARTED" />
        <Reveal delay={8}>
          <h2
            style={{
              margin: "34px 0 0",
              fontFamily: F.display,
              fontSize: 104,
              lineHeight: 1.08,
              fontWeight: 800,
              letterSpacing: "-0.06em",
              color: C.ink,
            }}
          >
            让 AI
            <span style={{color: C.lime}}> 不再靠猜。</span>
          </h2>
        </Reveal>
        <Reveal delay={20}>
          <p
            style={{
              margin: "26px 0 0",
              fontFamily: F.sans,
              fontSize: 31,
              letterSpacing: "0.02em",
              color: C.inkDim,
            }}
          >
            让每一个设计决定，都有出处。
          </p>
        </Reveal>
      </div>

      <Reveal delay={12}>
        <div
          style={{
            position: "absolute",
            right: 120,
            top: 190,
            width: 430,
            borderLeft: `1px solid ${C.lineStrong}`,
            paddingLeft: 30,
          }}
        >
          <div style={{display: "flex", alignItems: "center", gap: 18}}>
            <LogoMark size={74} />
            <div>
              <div
                style={{
                  fontFamily: F.sans,
                  fontSize: 24,
                  fontWeight: 800,
                  letterSpacing: "-0.04em",
                  lineHeight: 1.1,
                  color: C.ink,
                }}
              >
                MINI PROGRAM
                <br />
                <span style={{color: C.lime}}>UX PRO</span>
              </div>
            </div>
          </div>
          <div
            style={{
              marginTop: 22,
              fontFamily: F.sans,
              fontSize: 17,
              lineHeight: 1.8,
              color: C.inkDim,
            }}
          >
            微信小程序 UI/UX 设计智能
            <br />
            WeChat Mini Program UX System
          </div>
          <div
            style={{
              marginTop: 24,
              fontFamily: F.mono,
              fontSize: 11,
              lineHeight: 1.8,
              letterSpacing: "0.1em",
              color: C.inkFaint,
            }}
          >
            DESIGN WITH EVIDENCE
            <br />
            NOT WITH TEMPLATES
          </div>
        </div>
      </Reveal>

      <Reveal
        delay={16}
        style={{
          position: "absolute",
          left: 120,
          right: 120,
          bottom: 190,
        }}
      >
        <div
          style={{
            border: `1px solid ${C.lineStrong}`,
            borderRadius: 10,
            padding: "24px 28px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "rgba(245,241,232,0.035)",
          }}
        >
          <div style={{display: "flex", alignItems: "center", gap: 18}}>
            <span style={{fontFamily: F.mono, fontSize: 11, letterSpacing: "0.12em", color: C.lime}}>
              GITHUB
            </span>
            <span style={{width: 1, height: 24, background: C.lineStrong}} />
            <span
              style={{
                fontFamily: F.mono,
                fontSize: 25,
                letterSpacing: "-0.02em",
                color: C.ink,
              }}
            >
              github.com/violet-05/mini-program-ux-pro
            </span>
          </div>
          <span
            style={{
              fontFamily: F.sans,
              fontSize: 30,
              color: C.lime,
              lineHeight: 1,
            }}
          >
            ↗
          </span>
        </div>
      </Reveal>

      <Reveal
        delay={26}
        style={{
          position: "absolute",
          left: 120,
          right: 120,
          bottom: 104,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{display: "flex", gap: 9}}>
            <Tag>MIT</Tag>
            <Tag>PYTHON 3.10+</Tag>
            <Tag>LOCAL / NO API KEY</Tag>
            <Tag>WECHAT NATIVE · UNI-APP · TARO</Tag>
          </div>
          <span
            style={{
              fontFamily: F.mono,
              fontSize: 11,
              letterSpacing: "0.12em",
              color: C.inkFaint,
            }}
          >
            V1.0.0 / 2026
          </span>
        </div>
      </Reveal>

      <div
        style={{
          position: "absolute",
          right: 100,
          bottom: -50,
          fontFamily: F.sans,
          fontSize: 280,
          fontWeight: 800,
          lineHeight: 0.8,
          letterSpacing: "-0.09em",
          color: "rgba(245,241,232,0.03)",
        }}
      >
        UX
      </div>
    </SceneFrame>
  );
};
