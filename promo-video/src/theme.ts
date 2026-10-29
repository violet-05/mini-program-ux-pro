export const C = {
  bg: "#0B0D10",
  bgSoft: "#11151A",
  panel: "rgba(245, 241, 232, 0.035)",
  ink: "#F5F1E8",
  inkDim: "#A3A7A0",
  inkFaint: "rgba(245, 241, 232, 0.42)",
  line: "rgba(245, 241, 232, 0.13)",
  lineStrong: "rgba(245, 241, 232, 0.24)",
  lime: "#D9FF57",
  limeSoft: "rgba(217, 255, 87, 0.13)",
  teal: "#76E3C8",
  warm: "#F0C9A8",
  danger: "#FF8268",
} as const;

export const F = {
  sans: '"Microsoft YaHei", "PingFang SC", "Noto Sans SC", "Segoe UI", sans-serif',
  display: '"Microsoft YaHei", "PingFang SC", "Noto Sans SC", "Segoe UI", sans-serif',
  mono: '"Cascadia Code", "Consolas", "SFMono-Regular", monospace',
} as const;

export const VIDEO = {
  width: 1920,
  height: 1080,
  fps: 30,
  durationInFrames: 1560,
} as const;

export const SCENES = [
  {id: "intro", from: 0, duration: 190},
  {id: "brand", from: 175, duration: 220},
  {id: "workflow", from: 380, duration: 285},
  {id: "knowledge", from: 650, duration: 280},
  {id: "system", from: 915, duration: 275},
  {id: "proof", from: 1175, duration: 275},
  {id: "close", from: 1435, duration: 125},
] as const;
