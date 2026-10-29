import {C, F} from "../theme";
import {
  CheckRow,
  Phone,
  Reveal,
  SceneFrame,
  SectionTag,
  Stat,
  Tag,
} from "../components";

export const Proof = () => {
  return (
    <SceneFrame duration={275}>
      <div style={{position: "absolute", left: 120, top: 120, width: 600}}>
        <SectionTag index="06" label="VERIFICATION" />
        <Reveal delay={8}>
          <h2
            style={{
              margin: "30px 0 0",
              fontFamily: F.display,
              fontSize: 66,
              lineHeight: 1.16,
              fontWeight: 800,
              letterSpacing: "-0.055em",
              color: C.ink,
            }}
          >
            不只看起来对，
            <br />
            <span style={{color: C.lime}}>还要跑得通。</span>
          </h2>
        </Reveal>
        <Reveal delay={18}>
          <p
            style={{
              margin: "20px 0 0",
              width: 520,
              fontFamily: F.sans,
              fontSize: 20,
              lineHeight: 1.75,
              color: C.inkDim,
            }}
          >
            真实微信原生示例，在开发者工具模拟器中运行、交互、截图，并记录证据。
          </p>
        </Reveal>

        <div style={{marginTop: 48, display: "flex", flexDirection: "column", gap: 18}}>
          <CheckRow delay={36} tone="lime">
            加载 / 空 / 错误 / 重试
          </CheckRow>
          <CheckRow delay={44}>安全区 / TabBar / 自定义导航</CheckRow>
          <CheckRow delay={52}>触摸目标 ≥ 44px</CheckRow>
          <CheckRow delay={60}>console.error = 0</CheckRow>
        </div>

        <Reveal delay={78}>
          <div
            style={{
              marginTop: 42,
              display: "inline-flex",
              alignItems: "center",
              gap: 10,
              border: `1px dashed rgba(240,201,168,0.45)`,
              borderRadius: 4,
              padding: "10px 13px",
              fontFamily: F.mono,
              fontSize: 11,
              letterSpacing: "0.06em",
              color: C.warm,
            }}
          >
            <span style={{width: 6, height: 6, borderRadius: 99, background: C.warm}} />
            微信开发者工具模拟器 · 非真机结论
          </div>
        </Reveal>
      </div>

      <div
        style={{
          position: "absolute",
          left: 840,
          right: 120,
          top: 136,
          display: "flex",
          justifyContent: "space-between",
          borderBottom: `1px solid ${C.line}`,
          paddingBottom: 20,
        }}
      >
        <Stat value={24} suffix="/24" label="AUTOMATED CHECKS" size={46} delay={28} />
        <Stat value={9} label="SIMULATOR SHOTS" size={46} delay={36} />
        <Stat value={0} label="CONSOLE ERRORS" size={46} delay={44} />
      </div>

      <div
        style={{
          position: "absolute",
          left: 840,
          top: 290,
          width: 920,
          height: 720,
        }}
      >
        <div
          style={{
            position: "absolute",
            left: 240,
            top: 170,
            width: 440,
            height: 440,
            borderRadius: "50%",
            background:
              "radial-gradient(circle, rgba(217,255,87,0.09), transparent 68%)",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: 40,
            top: 90,
            display: "flex",
            alignItems: "flex-start",
            gap: 28,
          }}
        >
          <Reveal delay={34} y={70}>
            <Phone
              src="screens/home.png"
              width={228}
              label="HOME"
              rotate={-7}
              opacity={0.82}
              style={{marginTop: 70}}
            />
          </Reveal>
          <Reveal delay={22} y={80}>
            <Phone
              src="screens/player.png"
              width={300}
              label="PLAYER / NOW"
              glow
            />
          </Reveal>
          <Reveal delay={42} y={70}>
            <Phone
              src="screens/profile.png"
              width={228}
              label="PROFILE"
              rotate={7}
              opacity={0.82}
              style={{marginTop: 70}}
            />
          </Reveal>
        </div>

        <div
          style={{
            position: "absolute",
            right: 40,
            top: 10,
            display: "flex",
            gap: 8,
          }}
        >
          <Tag>WECHAT NATIVE</Tag>
          <Tag>BASE LIB 3.17.4</Tag>
          <Tag tone="lime">VERIFIED</Tag>
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          left: 120,
          bottom: 78,
          display: "flex",
          alignItems: "center",
          gap: 18,
          fontFamily: F.mono,
          fontSize: 11,
          letterSpacing: "0.12em",
          color: C.inkFaint,
        }}
      >
        <span style={{color: C.lime}}>EVIDENCE</span>
        <span>RESULTS.JSON</span>
        <span style={{width: 36, height: 1, background: C.line}} />
        <span>9 PNG</span>
        <span style={{width: 36, height: 1, background: C.line}} />
        <span>STATIC AUDIT / 0 ISSUES</span>
      </div>
    </SceneFrame>
  );
};
