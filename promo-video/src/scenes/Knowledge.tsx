import {useCurrentFrame} from "remotion";
import {C, F} from "../theme";
import {Reveal, SceneFrame, SectionTag, Stat, Tag} from "../components";

const SearchRow = ({
  id,
  name,
  score,
  active = false,
  delay = 0,
}: {
  id: string;
  name: string;
  score: string;
  active?: boolean;
  delay?: number;
}) => {
  return (
    <Reveal delay={delay} y={12}>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "180px 1fr 74px",
          alignItems: "center",
          gap: 16,
          padding: "16px 16px",
          border: `1px solid ${active ? "rgba(217,255,87,0.38)" : C.line}`,
          borderLeft: active ? `2px solid ${C.lime}` : `1px solid ${C.line}`,
          background: active ? "rgba(217,255,87,0.055)" : "rgba(245,241,232,0.018)",
          borderRadius: 6,
        }}
      >
        <div style={{fontFamily: F.mono, fontSize: 13, color: active ? C.lime : C.inkFaint}}>
          {id}
        </div>
        <div style={{fontFamily: F.sans, fontSize: 19, color: active ? C.ink : C.inkDim}}>
          {name}
        </div>
        <div
          style={{
            fontFamily: F.mono,
            fontSize: 13,
            color: active ? C.lime : C.inkFaint,
            textAlign: "right",
          }}
        >
          {score}
        </div>
      </div>
    </Reveal>
  );
};

export const Knowledge = () => {
  const frame = useCurrentFrame();
  const sweep = Math.min(1, Math.max(0, (frame - 30) / 90));

  return (
    <SceneFrame duration={280}>
      <div style={{position: "absolute", left: 120, top: 120, width: 900}}>
        <SectionTag index="04" label="KNOWLEDGE BASE" />
        <Reveal delay={8}>
          <h2
            style={{
              margin: "30px 0 0",
              fontFamily: F.display,
              fontSize: 66,
              lineHeight: 1.16,
              fontWeight: 800,
              letterSpacing: "-0.05em",
              color: C.ink,
            }}
          >
            不是感觉，
            <br />
            <span style={{color: C.lime}}>是有依据的设计判断。</span>
          </h2>
        </Reveal>
        <Reveal delay={20}>
          <p
            style={{
              margin: "18px 0 0",
              width: 660,
              fontFamily: F.sans,
              fontSize: 20,
              lineHeight: 1.7,
              color: C.inkDim,
            }}
          >
            产品、风格、配色、布局、组件、UX 与微信平台规则，全部结构化保存。
          </p>
        </Reveal>
      </div>

      <div
        style={{
          position: "absolute",
          left: 120,
          top: 436,
          width: 840,
          display: "flex",
          gap: 38,
          alignItems: "flex-end",
        }}
      >
        <div style={{width: 2, height: 210, background: C.lime, opacity: 0.8}} />
        <div>
          <Stat value={347} label="STRUCTURED RECORDS" size={150} suffix=" 条" delay={20} />
        </div>
        <div
          style={{
            paddingBottom: 20,
            fontFamily: F.mono,
            fontSize: 12,
            lineHeight: 1.8,
            letterSpacing: "0.08em",
            color: C.inkFaint,
          }}
        >
          <div>LOCAL / CSV</div>
          <div>TRACEABLE / SOURCED</div>
          <div>NO API KEY</div>
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          left: 120,
          top: 690,
          width: 900,
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 26,
        }}
      >
        <Stat value={31} label="产品类型" size={42} delay={38} />
        <Stat value={22} label="设计风格" size={42} delay={44} />
        <Stat value={24} label="配色方案" size={42} delay={50} />
        <Stat value={27} label="页面布局" size={42} delay={56} />
        <Stat value={33} label="组件规则" size={42} delay={62} />
        <Stat value={40} label="反模式" size={42} delay={68} />
      </div>

      <Reveal
        delay={82}
        style={{
          position: "absolute",
          left: 120,
          bottom: 92,
          fontFamily: F.mono,
          fontSize: 12,
          letterSpacing: "0.1em",
          color: C.inkFaint,
        }}
      >
        36 UX 规则 · 34 微信平台规则 · 16 设计推理 · 12 排版方案
      </Reveal>

      <div style={{position: "absolute", right: 120, top: 264, width: 720}}>
        <Reveal delay={42}>
          <div
            style={{
              border: `1px solid ${C.lineStrong}`,
              borderRadius: 16,
              background: "rgba(8,10,13,0.90)",
              boxShadow: "0 30px 90px rgba(0,0,0,0.42)",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: "18px 20px",
                borderBottom: `1px solid ${C.line}`,
                fontFamily: F.mono,
                fontSize: 11,
                letterSpacing: "0.13em",
                color: C.inkFaint,
              }}
            >
              <span>LOCAL SEARCH</span>
              <span style={{color: C.lime}}>BM25 / ZH BIGRAM</span>
            </div>
            <div style={{padding: 22}}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  height: 56,
                  padding: "0 16px",
                  border: `1px solid rgba(217,255,87,0.28)`,
                  borderRadius: 7,
                  background: "rgba(217,255,87,0.04)",
                }}
              >
                <span
                  style={{
                    width: 15,
                    height: 15,
                    borderRadius: "50%",
                    border: `1.5px solid ${C.lime}`,
                    position: "relative",
                    flexShrink: 0,
                  }}
                />
                <span style={{fontFamily: F.sans, fontSize: 19, color: C.ink}}>
                  微信小程序 底部安全区域
                </span>
                <span
                  style={{
                    marginLeft: "auto",
                    fontFamily: F.mono,
                    fontSize: 11,
                    color: C.lime,
                  }}
                >
                  ↵
                </span>
              </div>

              <div style={{display: "flex", flexDirection: "column", gap: 8, marginTop: 16}}>
                <SearchRow id="mp-safe-area" name="底部安全区域与固定底栏" score="0.91" active delay={66} />
                <SearchRow id="mp-tabbar" name="TabBar 视觉与交互" score="0.64" delay={74} />
                <SearchRow id="comp-bottom-action" name="底部操作栏" score="0.51" delay={82} />
              </div>

              <div
                style={{
                  height: 3,
                  marginTop: 18,
                  background: C.line,
                  overflow: "hidden",
                  borderRadius: 2,
                }}
              >
                <div
                  style={{
                    width: "100%",
                    height: "100%",
                    background: C.lime,
                    transform: `scaleX(${sweep})`,
                    transformOrigin: "left",
                    opacity: 0.8,
                  }}
                />
              </div>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginTop: 12,
                  fontFamily: F.mono,
                  fontSize: 10,
                  letterSpacing: "0.08em",
                  color: C.inkFaint,
                }}
              >
                <span>MATCHED FIELDS / NAME · SCENARIO</span>
                <span>0 NETWORK</span>
              </div>
            </div>
          </div>
        </Reveal>

        <Reveal delay={95}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginTop: 20,
              paddingTop: 16,
              borderTop: `1px solid ${C.line}`,
              fontFamily: F.sans,
              fontSize: 17,
              color: C.inkDim,
            }}
          >
            <span>中文 bigram · 同义词 · 字段权重</span>
            <Tag tone="lime">EXPLAINABLE</Tag>
          </div>
        </Reveal>
      </div>
    </SceneFrame>
  );
};
