import {C, F} from "../theme";
import {Reveal, SceneFrame, SectionTag, Tag} from "../components";

const TreeLine = ({
  text,
  delay,
  active = false,
  indent = 0,
}: {
  text: string;
  delay: number;
  active?: boolean;
  indent?: number;
}) => {
  return (
    <Reveal delay={delay} y={7}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          padding: "6px 0",
          paddingLeft: indent,
          borderBottom: `1px solid rgba(245,241,232,0.055)`,
          fontFamily: F.mono,
          fontSize: 15,
          color: active ? C.lime : C.inkDim,
        }}
      >
        <span style={{color: active ? C.lime : C.inkFaint}}>
          {active ? "▸" : "·"}
        </span>
        <span>{text}</span>
        {active ? (
          <span
            style={{
              marginLeft: "auto",
              fontFamily: F.mono,
              fontSize: 9,
              letterSpacing: "0.1em",
              color: C.lime,
            }}
          >
            {text === "MASTER.md" ? "SOURCE OF TRUTH" : ""}
          </span>
        ) : null}
      </div>
    </Reveal>
  );
};

const RuleCard = ({
  index,
  title,
  detail,
  delay,
}: {
  index: string;
  title: string;
  detail: string;
  delay: number;
}) => {
  return (
    <Reveal delay={delay}>
      <div
        style={{
          border: `1px solid ${C.line}`,
          borderRadius: 10,
          padding: "22px 24px",
          background: "rgba(245,241,232,0.022)",
          minHeight: 112,
        }}
      >
        <div style={{display: "flex", justifyContent: "space-between"}}>
          <span style={{fontFamily: F.mono, fontSize: 11, color: C.lime}}>{index}</span>
          <span style={{fontFamily: F.mono, fontSize: 13, color: C.lime}}>✓</span>
        </div>
        <div
          style={{
            marginTop: 12,
            fontFamily: F.sans,
            fontSize: 20,
            fontWeight: 700,
            color: C.ink,
          }}
        >
          {title}
        </div>
        <div
          style={{
            marginTop: 6,
            fontFamily: F.sans,
            fontSize: 14,
            lineHeight: 1.5,
            color: C.inkDim,
          }}
        >
          {detail}
        </div>
      </div>
    </Reveal>
  );
};

export const System = () => {
  return (
    <SceneFrame duration={275}>
      <div style={{position: "absolute", left: 120, top: 120, width: 1500}}>
        <SectionTag index="05" label="DESIGN SYSTEM" />
        <Reveal delay={8}>
          <h2
            style={{
              margin: "28px 0 0",
              fontFamily: F.display,
              fontSize: 64,
              lineHeight: 1.15,
              fontWeight: 800,
              letterSpacing: "-0.05em",
              color: C.ink,
            }}
          >
            一个 Master，
            <span style={{color: C.lime}}>管住整站设计。</span>
          </h2>
        </Reveal>
        <Reveal delay={18}>
          <p
            style={{
              margin: "15px 0 0",
              fontFamily: F.sans,
              fontSize: 20,
              color: C.inkDim,
            }}
          >
            先有事实源，再写页面。页面只允许有限覆盖。
          </p>
        </Reveal>
      </div>

      <div
        style={{
          position: "absolute",
          left: 120,
          top: 338,
          width: 620,
          height: 460,
          border: `1px solid ${C.lineStrong}`,
          borderRadius: 16,
          padding: 24,
          background: "rgba(8,10,13,0.82)",
          boxShadow: "0 24px 70px rgba(0,0,0,0.35)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            paddingBottom: 12,
            borderBottom: `1px solid ${C.line}`,
            fontFamily: F.mono,
            fontSize: 11,
            letterSpacing: "0.12em",
            color: C.inkFaint,
          }}
        >
          <span>GENERATED / DESIGN-SYSTEM</span>
          <span style={{color: C.lime}}>LOCAL</span>
        </div>
        <div style={{marginTop: 12}}>
          <TreeLine text="design-system/" delay={28} active />
          <TreeLine text="MASTER.md" delay={34} indent={22} active />
          <TreeLine text="MASTER.json" delay={40} indent={22} />
          <TreeLine text="tokens.wxss" delay={46} indent={22} />
          <TreeLine text="pages/" delay={52} indent={22} />
          <TreeLine text="home.md" delay={58} indent={44} />
          <TreeLine text="music-player.md" delay={64} indent={44} />
          <TreeLine text="profile.md" delay={70} indent={44} />
        </div>
        <Reveal delay={82}>
          <div
            style={{
              marginTop: 18,
              paddingTop: 14,
              borderTop: `1px solid ${C.line}`,
              fontFamily: F.mono,
              fontSize: 11,
              lineHeight: 1.7,
              color: C.inkFaint,
            }}
          >
            <div>
              <span style={{color: C.lime}}>$</span> python scripts/generate_design_system.py
            </div>
            <div style={{paddingLeft: 20}}>--product "音乐播放器小程序"</div>
            <div style={{paddingLeft: 20}}>--stack uni-app</div>
          </div>
        </Reveal>
      </div>

      <Reveal
        delay={44}
        style={{
          position: "absolute",
          left: 1020,
          top: 338,
          width: 780,
          height: 460,
        }}
      >
        <div
          style={{
            width: "100%",
            height: "100%",
            border: `1px solid ${C.lineStrong}`,
            borderRadius: 16,
            background: "rgba(245,241,232,0.035)",
            overflow: "hidden",
            boxShadow: "0 30px 90px rgba(0,0,0,0.35)",
          }}
        >
          <div
            style={{
              height: 48,
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "0 24px",
              borderBottom: `1px solid ${C.line}`,
              fontFamily: F.mono,
              fontSize: 12,
              letterSpacing: "0.12em",
              color: C.inkFaint,
            }}
          >
            <span>MASTER.md</span>
            <span style={{color: C.lime}}>v1.0.0</span>
          </div>
          <div style={{padding: "22px 28px", position: "relative"}}>
            <div
              style={{
                position: "absolute",
                left: 0,
                top: 22,
                bottom: 22,
                width: 2,
                background: C.lime,
                opacity: 0.7,
              }}
            />
            <Reveal delay={52}>
              <div style={{fontFamily: F.mono, fontSize: 11, color: C.lime, letterSpacing: "0.12em"}}>
                01 / 产品定位
              </div>
              <div style={{fontFamily: F.sans, fontSize: 25, color: C.ink, marginTop: 8}}>
                音乐播放器
                <span style={{fontFamily: F.mono, fontSize: 12, color: C.inkFaint, marginLeft: 12}}>
                  prod-music
                </span>
              </div>
            </Reveal>
            <Reveal delay={62}>
              <div
                style={{
                  marginTop: 22,
                  paddingTop: 16,
                  borderTop: `1px solid ${C.line}`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <div style={{fontFamily: F.mono, fontSize: 11, color: C.lime, letterSpacing: "0.12em"}}>
                  04 / 设计风格
                </div>
                <div style={{display: "flex", gap: 8}}>
                  <span style={{width: 34, height: 16, background: C.bg, border: `1px solid ${C.line}`}} />
                  <span style={{width: 34, height: 16, background: C.ink}} />
                  <span style={{width: 34, height: 16, background: C.lime}} />
                  <span style={{width: 34, height: 16, background: C.teal}} />
                </div>
              </div>
              <div style={{fontFamily: F.sans, fontSize: 18, color: C.inkDim, marginTop: 10}}>
                内容优先 / Content-first
              </div>
            </Reveal>
            <Reveal delay={74}>
              <div
                style={{
                  marginTop: 22,
                  paddingTop: 16,
                  borderTop: `1px solid ${C.line}`,
                  fontFamily: F.mono,
                  fontSize: 11,
                  color: C.lime,
                  letterSpacing: "0.12em",
                }}
              >
                08 / TOKENS
              </div>
              <div style={{display: "flex", gap: 8, flexWrap: "wrap", marginTop: 12}}>
                <Tag style={{fontSize: 11, padding: "6px 9px"}}>--bg #0D0F12</Tag>
                <Tag style={{fontSize: 11, padding: "6px 9px"}}>--space 32rpx</Tag>
                <Tag style={{fontSize: 11, padding: "6px 9px"}}>--radius 8rpx</Tag>
                <Tag tone="lime" style={{fontSize: 11, padding: "6px 9px"}}>touch 88rpx</Tag>
              </div>
            </Reveal>
            <Reveal delay={86}>
              <div
                style={{
                  marginTop: 22,
                  paddingTop: 16,
                  borderTop: `1px solid ${C.line}`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <span style={{fontFamily: F.mono, fontSize: 11, color: C.lime, letterSpacing: "0.1em"}}>
                  PAGE OVERRIDE
                </span>
                <span style={{fontFamily: F.sans, fontSize: 14, color: C.inkDim}}>
                  只允许顺序 / 间距 / 状态
                </span>
              </div>
            </Reveal>
          </div>
        </div>
      </Reveal>

      <div
        style={{
          position: "absolute",
          left: 120,
          top: 820,
          width: 1680,
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 24,
        }}
      >
        <RuleCard
          index="01"
          title="页面只允许有限覆盖"
          detail="顺序、局部间距、本页状态。"
          delay={86}
        />
        <RuleCard
          index="02"
          title="不另起配色与字体"
          detail="所有页面继承同一套 token。"
          delay={94}
        />
        <RuleCard
          index="03"
          title="默认不覆盖 Master"
          detail="只有显式 --force 才覆盖。"
          delay={102}
        />
      </div>

      <Reveal
        delay={112}
        style={{
          position: "absolute",
          left: 120,
          bottom: 78,
          fontFamily: F.mono,
          fontSize: 12,
          letterSpacing: "0.12em",
          color: C.inkFaint,
        }}
      >
        MASTER → PAGE OVERRIDES → IMPLEMENTATION
      </Reveal>
    </SceneFrame>
  );
};
