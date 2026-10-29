import {interpolate, useCurrentFrame} from "remotion";
import {C, F} from "../theme";
import {Reveal, SceneFrame, SectionTag, Tag} from "../components";

const STEPS = [
  {label: "识别技术栈", sub: "native / uni-app / Taro"},
  {label: "分析产品", sub: "用户 · 场景 · 任务"},
  {label: "检索知识", sub: "347 条本地记录"},
  {label: "生成 Master", sub: "tokens + 页面覆盖"},
  {label: "实现页面", sub: "按技术栈落地"},
  {label: "审查验收", sub: "静态 + 模拟器"},
];

const PipelineNode = ({
  index,
  label,
  sub,
  progress,
}: {
  index: number;
  label: string;
  sub: string;
  progress: number;
}) => {
  const active = progress >= index / (STEPS.length - 1) - 0.02;
  return (
    <div
      style={{
        width: 220,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 13,
        opacity: active ? 1 : 0.38,
      }}
    >
      <div
        style={{
          width: 58,
          height: 58,
          borderRadius: "50%",
          border: `1px solid ${active ? C.lime : C.lineStrong}`,
          background: active ? "rgba(217,255,87,0.08)" : "rgba(11,13,16,0.7)",
          color: active ? C.lime : C.inkDim,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: F.mono,
          fontSize: 15,
          boxShadow: active ? "0 0 30px rgba(217,255,87,0.10)" : "none",
          transform: `scale(${active ? 1 : 0.92})`,
        }}
      >
        {String(index + 1).padStart(2, "0")}
      </div>
      <div
        style={{
          textAlign: "center",
          fontFamily: F.sans,
          fontSize: 20,
          fontWeight: 700,
          color: active ? C.ink : C.inkDim,
        }}
      >
        {label}
      </div>
      <div
        style={{
          textAlign: "center",
          fontFamily: F.mono,
          fontSize: 11,
          lineHeight: 1.5,
          letterSpacing: "0.04em",
          color: active ? C.inkDim : C.inkFaint,
        }}
      >
        {sub}
      </div>
    </div>
  );
};

export const Workflow = () => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [36, 170], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const cursorVisible = Math.floor(frame / 14) % 2 === 0;

  return (
    <SceneFrame duration={285}>
      <div style={{position: "absolute", left: 120, top: 120, width: 1420}}>
        <SectionTag index="03" label="WORKFLOW" />
        <Reveal delay={8}>
          <h2
            style={{
              margin: "30px 0 0",
              fontFamily: F.display,
              fontSize: 64,
              lineHeight: 1.15,
              fontWeight: 800,
              letterSpacing: "-0.05em",
              color: C.ink,
            }}
          >
            从需求到验收，
            <span style={{color: C.lime}}>一条可执行的链路。</span>
          </h2>
        </Reveal>
        <Reveal delay={18}>
          <p
            style={{
              margin: "16px 0 0",
              fontFamily: F.sans,
              fontSize: 20,
              color: C.inkDim,
            }}
          >
            每一步都有输入、输出和验证边界。不是一次性提示词。
          </p>
        </Reveal>
      </div>

      <div
        style={{
          position: "absolute",
          left: 120,
          right: 120,
          top: 390,
          height: 200,
        }}
      >
        <div
          style={{
            position: "absolute",
            left: 58,
            right: 58,
            top: 29,
            height: 1,
            background: C.line,
          }}
        />
        <div
          style={{
            position: "absolute",
            left: 58,
            right: 58,
            top: 29,
            height: 1,
            background: C.lime,
            opacity: 0.8,
            transform: `scaleX(${progress})`,
            transformOrigin: "left",
          }}
        />
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            position: "relative",
          }}
        >
          {STEPS.map((step, index) => (
            <PipelineNode
              key={step.label}
              index={index}
              label={step.label}
              sub={step.sub}
              progress={progress}
            />
          ))}
        </div>
      </div>

      <Reveal
        delay={55}
        style={{
          position: "absolute",
          left: 120,
          top: 650,
          width: 1020,
        }}
      >
        <div
          style={{
            borderRadius: 16,
            border: `1px solid ${C.lineStrong}`,
            background: "rgba(8, 10, 13, 0.88)",
            boxShadow: "0 26px 80px rgba(0,0,0,0.4)",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              height: 44,
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "0 18px",
              borderBottom: `1px solid ${C.line}`,
              fontFamily: F.mono,
              fontSize: 11,
              letterSpacing: "0.12em",
              color: C.inkFaint,
            }}
          >
            <div style={{display: "flex", gap: 7}}>
              <span style={{width: 7, height: 7, borderRadius: 99, background: C.danger}} />
              <span style={{width: 7, height: 7, borderRadius: 99, background: C.warm}} />
              <span style={{width: 7, height: 7, borderRadius: 99, background: C.teal}} />
            </div>
            <span>mpux-cli / design-system</span>
            <span>LOCAL</span>
          </div>
          <div
            style={{
              padding: "24px 28px 28px",
              fontFamily: F.mono,
              fontSize: 19,
              lineHeight: 1.85,
              color: C.inkDim,
            }}
          >
            <Reveal delay={66} y={8}>
              <div>
                <span style={{color: C.lime}}>$</span> python scripts/generate_design_system.py \
              </div>
            </Reveal>
            <Reveal delay={74} y={8}>
              <div style={{paddingLeft: 26}}>
                --product <span style={{color: C.warm}}>"音乐播放器小程序"</span> \
              </div>
            </Reveal>
            <Reveal delay={82} y={8}>
              <div style={{paddingLeft: 26}}>
                --stack <span style={{color: C.warm}}>uni-app</span>
              </div>
            </Reveal>
            <Reveal delay={94} y={8}>
              <div style={{marginTop: 10, color: C.ink}}>
                <span style={{color: C.lime}}>→</span> MASTER.md · tokens.scss · pages/
                <span style={{color: C.lime, opacity: cursorVisible ? 1 : 0}}>_</span>
              </div>
            </Reveal>
          </div>
        </div>
      </Reveal>

      <Reveal
        delay={80}
        style={{
          position: "absolute",
          right: 120,
          top: 650,
          width: 540,
        }}
      >
        <div
          style={{
            minHeight: 250,
            border: `1px solid ${C.line}`,
            borderRadius: 16,
            padding: 28,
            background: "rgba(245,241,232,0.022)",
          }}
        >
          <div
            style={{
              fontFamily: F.mono,
              fontSize: 11,
              letterSpacing: "0.14em",
              color: C.inkFaint,
              marginBottom: 18,
            }}
          >
            ONE SYSTEM / THREE STACKS
          </div>
          <div style={{display: "flex", flexWrap: "wrap", gap: 10}}>
            <Tag tone="lime">WECHAT NATIVE</Tag>
            <Tag>UNI-APP</Tag>
            <Tag>TARO</Tag>
          </div>
          <div
            style={{
              marginTop: 20,
              paddingTop: 16,
              borderTop: `1px solid ${C.line}`,
              display: "flex",
              alignItems: "center",
              gap: 10,
              fontFamily: F.sans,
              fontSize: 17,
              color: C.inkDim,
            }}
          >
            <span style={{color: C.danger, fontFamily: F.mono}}>×</span>
            <span>浏览器原型不等于已验证小程序</span>
          </div>
          <div
            style={{
              marginTop: 12,
              fontFamily: F.mono,
              fontSize: 11,
              letterSpacing: "0.08em",
              color: C.inkFaint,
            }}
          >
            技术栈识别优先于猜测
          </div>
        </div>
      </Reveal>

      <Reveal
        delay={110}
        style={{
          position: "absolute",
          left: 120,
          bottom: 70,
          fontFamily: F.mono,
          fontSize: 12,
          letterSpacing: "0.14em",
          color: C.inkFaint,
        }}
      >
        INPUT → DECISION → SPEC → IMPLEMENTATION → EVIDENCE
      </Reveal>
    </SceneFrame>
  );
};
