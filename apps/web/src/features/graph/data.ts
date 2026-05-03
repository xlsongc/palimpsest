export type ReadingStatus = "read" | "reading" | "want";

export type ThemeKey =
  | "finance"
  | "cs"
  | "history"
  | "ai"
  | "literature"
  | "psychology"
  | "math"
  | "biography";

export interface BookNode {
  id: string;
  title: string;
  status: ReadingStatus;
  theme: ThemeKey;
  x: number;
  y: number;
  size?: "sm" | "md" | "lg";
  faded?: boolean;
}

export interface Edge {
  from: string;
  to: string;
  path: string;
  theme: ThemeKey;
  strong?: boolean;
}

export interface BookDetail {
  title: string;
  theme: ThemeKey;
  status: ReadingStatus;
  note: string;
  related: [string, string][];
  stats: [string, string, string];
}

export const themes: Record<ThemeKey, { label: string; color: string }> = {
  finance: { label: "投资 / 金融", color: "#294f86" },
  cs: { label: "CS / 技术", color: "#19785c" },
  history: { label: "历史 / 人文", color: "#8b3a2b" },
  ai: { label: "AI / 科技传记", color: "#51308b" },
  literature: { label: "文学 / 小说", color: "#28723e" },
  psychology: { label: "心理 / 社科", color: "#175d6b" },
  math: { label: "数学 / 信息论", color: "#7a6414" },
  biography: { label: "传记 / 思想", color: "#7d2857" },
};

export const statusLabels: Record<ReadingStatus, string> = {
  read: "读过",
  reading: "在读",
  want: "想读",
};

export const nodes: BookNode[] = [
  { id: "python", title: "流畅的Python", status: "reading", theme: "cs", x: 14, y: 20 },
  { id: "clrs", title: "算法导论", status: "want", theme: "cs", x: 8, y: 30 },
  { id: "csapp", title: "深入理解计算机系统", status: "reading", theme: "cs", x: 20, y: 38 },
  { id: "coding", title: "编码", status: "read", theme: "cs", x: 10, y: 48 },
  { id: "prml", title: "PRML", status: "reading", theme: "ai", x: 28, y: 28 },
  { id: "d2l", title: "Dive into Deep Learning", status: "reading", theme: "ai", x: 32, y: 42 },
  { id: "understanding", title: "Understanding Deep Learning", status: "reading", theme: "ai", x: 26, y: 54 },
  { id: "ming", title: "明朝那些事儿", status: "read", theme: "history", x: 42, y: 18 },
  { id: "wei", title: "魏晋南北朝", status: "read", theme: "history", x: 52, y: 12 },
  { id: "golden", title: "黄金时代", status: "read", theme: "literature", x: 82, y: 8 },
  { id: "almanack", title: "The Almanack of Naval", status: "read", theme: "biography", x: 55, y: 40 },
  { id: "poor", title: "Poor Charlie's Almanack", status: "read", theme: "finance", x: 65, y: 35, size: "lg" },
  { id: "lynch", title: "彼得·林奇的成功投资", status: "read", theme: "finance", x: 70, y: 50, size: "lg" },
  { id: "index", title: "指数基金投资指南", status: "read", theme: "finance", x: 58, y: 48 },
  { id: "common", title: "Common Stocks...", status: "want", theme: "finance", x: 72, y: 62 },
  { id: "growth", title: "怎样选择成长股", status: "reading", theme: "finance", x: 60, y: 68 },
  { id: "selfish", title: "The Selfish Gene", status: "reading", theme: "psychology", x: 78, y: 28 },
  { id: "animal", title: "社会性动物", status: "want", theme: "psychology", x: 85, y: 38 },
  { id: "mistakes", title: "错误的行为", status: "want", theme: "psychology", x: 88, y: 48 },
  { id: "principles", title: "经济学原理", status: "reading", theme: "finance", x: 90, y: 58 },
  { id: "xue", title: "薛兆丰经济学讲义", status: "read", theme: "finance", x: 92, y: 72 },
  { id: "deng", title: "邓小平传", status: "read", theme: "history", x: 80, y: 78 },
  { id: "lost", title: "失去的三十年", status: "read", theme: "history", x: 70, y: 82 },
  { id: "ocean", title: "海洋帝国", status: "read", theme: "history", x: 48, y: 85 },
  { id: "dutch", title: "荷兰海洋帝国史", status: "want", theme: "history", x: 55, y: 92 },
  { id: "war", title: "芯片战争", status: "read", theme: "ai", x: 6, y: 58 },
  { id: "animalfarm", title: "动物农场", status: "read", theme: "literature", x: 76, y: 15 },
  { id: "moon", title: "月亮与六便士", status: "read", theme: "literature", x: 68, y: 22 },
];

export const edges: Edge[] = [
  { from: "python", to: "csapp", path: "M140 144 C160 180 170 210 200 270", theme: "cs" },
  { from: "python", to: "clrs", path: "M140 144 C120 170 100 190 80 216", theme: "cs" },
  { from: "csapp", to: "coding", path: "M200 270 C180 290 140 310 100 346", theme: "cs" },
  { from: "prml", to: "d2l", path: "M280 200 C290 240 300 260 320 300", theme: "ai" },
  { from: "d2l", to: "understanding", path: "M320 300 C300 330 280 350 260 388", theme: "ai" },
  { from: "ming", to: "wei", path: "M420 130 C450 100 480 90 520 86", theme: "history", strong: true },
  { from: "almanack", to: "index", path: "M550 290 C560 310 570 330 580 346", theme: "biography" },
  { from: "index", to: "poor", path: "M580 346 C600 330 630 280 650 250", theme: "finance" },
  { from: "poor", to: "lynch", path: "M650 250 C660 290 680 330 700 360", theme: "finance", strong: true },
  { from: "poor", to: "animal", path: "M650 250 C700 230 780 240 850 274", theme: "psychology" },
  { from: "poor", to: "mistakes", path: "M650 250 C720 260 800 300 880 346", theme: "psychology" },
  { from: "growth", to: "common", path: "M600 488 C640 470 680 450 720 446", theme: "finance" },
  { from: "principles", to: "xue", path: "M900 418 C910 460 915 490 920 518", theme: "finance" },
  { from: "lost", to: "deng", path: "M700 588 C740 570 770 555 800 558", theme: "history" },
  { from: "ocean", to: "dutch", path: "M480 610 C500 630 520 650 550 662", theme: "history" },
  { from: "golden", to: "animalfarm", path: "M820 60 C790 80 770 95 760 108", theme: "literature", strong: true },
  { from: "moon", to: "golden", path: "M680 158 C720 120 770 80 820 60", theme: "literature" },
];

export const detailById: Record<string, BookDetail> = {
  poor: {
    title: "Poor Charlie's Almanack",
    theme: "finance",
    status: "read",
    note: "芒格思维体系核心，护城河 + 多元思维模型",
    related: [
      ["彼得·林奇的成功投资", "读过 · 投资哲学"],
      ["影响力", "想读 · 芒格推荐"],
      ["错误的行为", "想读 · 思维模型"],
      ["The Selfish Gene", "在读 · 芒格推荐书单"],
    ],
    stats: ["4", "1", "2"],
  },
  wei: {
    title: "魏晋南北朝",
    theme: "history",
    status: "read",
    note: "门阀政治 / 历史背景",
    related: [
      ["东晋门阀政治", "想读 · 魏晋延伸"],
      ["明朝那些事儿", "读过 · 中国史脉络"],
    ],
    stats: ["2", "1", "1"],
  },
};
