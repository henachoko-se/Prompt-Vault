/* QUARTET MUSIC — data + jacket gradient system */

// image assets
const IMG = {
  group:   "quartet/img/group.jpg",
  chibi:   "quartet/img/chibi.jpg",
  budokan: "quartet/img/budokan.jpg",
  nagi:    "quartet/img/nagi.jpg",
  natsu:   "quartet/img/natsu.jpg",
  ruka:    "quartet/img/ruka.jpg",
  hena:    "quartet/img/hena.jpg",
};

// member palette
const QMEMBERS = {
  nagi:  { name: "凪",   en: "Nagi",  emoji: "🩵", color: "#74d4ff", colorName: "スカイブルー", deep: "#1f8fd6", img: "quartet/img/nagi.jpg" },
  natsu: { name: "ナツ", en: "Natsu", emoji: "💙", color: "#4f7bff", colorName: "ブルー",       deep: "#2b46c8", img: "quartet/img/natsu.jpg" },
  ruka:  { name: "ルカ", en: "Ruka",  emoji: "💜", color: "#b070ff", colorName: "パープル",     deep: "#7d35d6", img: "quartet/img/ruka.jpg" },
  hena:  { name: "へな", en: "Hena",  emoji: "🖤", color: "#c4cbe0", colorName: "ブラック",     deep: "#5a6178", img: "quartet/img/hena.jpg" },
};

// Build a gradient "album jacket" background from a theme.
// theme: array of [hex, hex] focal colors + base shape variant
function jacketBg(a, b, variant = 0) {
  const shapes = [
    `radial-gradient(75% 60% at 24% 22%, ${a}ee, transparent 58%),
     radial-gradient(70% 70% at 82% 30%, ${b}dd, transparent 58%),
     radial-gradient(95% 85% at 60% 105%, ${a}cc, transparent 60%)`,
    `radial-gradient(90% 70% at 70% 18%, ${b}ee, transparent 60%),
     radial-gradient(80% 80% at 16% 80%, ${a}dd, transparent 58%),
     conic-gradient(from 200deg at 40% 60%, ${a}55, ${b}33, transparent 60%)`,
    `linear-gradient(150deg, ${a}dd, transparent 55%),
     radial-gradient(80% 80% at 85% 90%, ${b}ee, transparent 60%),
     radial-gradient(60% 60% at 30% 25%, ${a}aa, transparent 60%)`,
    `radial-gradient(100% 60% at 50% 0%, ${b}ee, transparent 62%),
     radial-gradient(70% 90% at 22% 95%, ${a}dd, transparent 60%),
     radial-gradient(70% 90% at 80% 80%, ${b}99, transparent 58%)`,
  ];
  return `${shapes[variant % shapes.length]}, #0a0d1e`;
}

// the featured songs — real tracks, each wired to an audio src
const QSONGS = [
  { id: "raindrop", title: "Raindrop Silhouette", tag: "Rain Ballad", member: "hena",  lead: "へな",  dur: 218, plays: "128K",
    bg: jacketBg("#4f7bff", "#0e1740", 3), img: IMG.hena, kw: "雨の街 / 夜明け", src: "quartet/audio/raindrop-silhouette.mp3" },
  { id: "bluepulse", title: "Blue Pulse",         tag: "J-ROCK",      member: "natsu", lead: "ナツ",  dur: 196, plays: "104K",
    bg: jacketBg("#4f7bff", "#7d35d6", 0), img: IMG.natsu, kw: "青い炎 / 鼓動", src: "quartet/audio/blue-pulse.mp3" },
  { id: "sky",      title: "Brand New Sky",       tag: "Idol Pop",    member: "nagi",  lead: "凪",    dur: 204, plays: "112K",
    bg: jacketBg("#74d4ff", "#bcd1ff", 1), img: IMG.nagi, kw: "希望 / 清涼感", src: "quartet/audio/brand-new-sky.mp3" },
  { id: "moonlight", title: "Moonlight Harmony",  tag: "City Pop",    member: "ruka",  lead: "ルカ",  dur: 233, plays: "88K",
    bg: jacketBg("#b070ff", "#2a1346", 2), img: IMG.ruka, kw: "夜 / メロウ", src: "quartet/audio/moonlight-harmony.mp3" },
  { id: "rainbow",  title: "Rainbow Arc -雨上がりの軌跡-", tag: "Emotional", member: "all", lead: "QUARTET", dur: 247, plays: "74K",
    bg: jacketBg("#74d4ff", "#b070ff", 0), img: IMG.group, kw: "雨上がり / 軌跡", src: "quartet/audio/rainbow-arc.mp3" },
  { id: "starlight", title: "Starlight Quartet",  tag: "Anthem",      member: "all",   lead: "QUARTET", dur: 252, plays: "97K",
    bg: jacketBg("#74d4ff", "#b070ff", 3), img: IMG.budokan, kw: "武道館 / スポットライト", src: "quartet/audio/starlight-quartet.mp3" },
  { id: "ignition", title: "Ignition -NEXT STAGE-", tag: "Dance",     member: "all",   lead: "QUARTET", dur: 188, plays: "82K",
    bg: jacketBg("#4f7bff", "#74d4ff", 1), img: IMG.chibi, kw: "加速 / NEXT STAGE", src: "quartet/audio/ignition-next-stage.mp3" },
  { id: "maybreeze", title: "May Breeze Drive",   tag: "City Pop",    member: "ruka",  lead: "ルカ",  dur: 211, plays: "79K",
    bg: jacketBg("#74d4ff", "#b070ff", 2), img: IMG.ruka, kw: "5月の風 / ドライブ", src: "quartet/audio/may-breeze-drive.mp3" },
  { id: "heart",    title: "Center of Your Heart", tag: "Fan Song",   member: "all",   lead: "QUARTET", dur: 226, plays: "118K",
    bg: jacketBg("#b070ff", "#4f7bff", 3), img: IMG.group, kw: "絆 / 君に届ける", src: "quartet/audio/center-of-your-heart.mp3" },
];

const QPLAYLISTS = [
  { id: "rain",  title: "雨の日に聴きたいQUARTET", kw: "Rainy Mood", count: 18, min: 64,
    desc: "静かな夜、雨音と一緒に沁みるバラード集。", bg: jacketBg("#4f7bff", "#0e1740", 3) },
  { id: "road",  title: "武道館までの軌跡",        kw: "The Road",   count: 22, min: 81,
    desc: "夢を追いかける4人の成長を感じるエモーショナル楽曲。", bg: jacketBg("#74d4ff", "#b070ff", 0) },
  { id: "color", title: "推し色で選ぶQUARTET",     kw: "Your Color", count: 24, min: 88,
    desc: "🩵💙💜🖤 4人の個性が光るメンバーカラー別プレイリスト。", bg: jacketBg("#b070ff", "#4f7bff", 1) },
  { id: "hype",  title: "テンション上げたい夜に",  kw: "Night Hype", count: 16, min: 52,
    desc: "ナツの熱量とQUARTETのダンスナンバーで一気に加速。", bg: jacketBg("#4f7bff", "#7d35d6", 2) },
];

const QMEMBER_CARDS = [
  { key: "nagi",  catch: "空みたいに澄んだ声で、未来を照らす。",
    voice: "透明感のあるハイトーンボイス", genre: "王道ポップス / 清涼感", pos: "Center" },
  { key: "natsu", catch: "青い炎みたいな熱量で、ステージを動かす。",
    voice: "芯のある力強いボーカル", genre: "J-ROCK / ラップパート", pos: "Performer" },
  { key: "ruka",  catch: "夜に溶けるような低音で、物語を深くする。",
    voice: "艶やかなミドル〜低音", genre: "シティ・ポップ / R&B", pos: "Mood Maker" },
  { key: "hena",  catch: "黒の包容力で、4人の歌を支える。",
    voice: "揺るがないベースボーカル", genre: "バラード / 土台", pos: "Producer ＆ Base" },
];

const QRANKING = [
  { id: "raindrop",  title: "Raindrop Silhouette", member: "hena",  plays: "128K", img: IMG.hena },
  { id: "heart",     title: "Center of Your Heart", member: "all",  plays: "118K", img: IMG.group },
  { id: "sky",       title: "Brand New Sky",       member: "nagi",  plays: "112K", img: IMG.nagi },
  { id: "bluepulse", title: "Blue Pulse",          member: "natsu", plays: "104K", img: IMG.natsu },
  { id: "starlight", title: "Starlight Quartet",   member: "all",   plays: "97K",  img: IMG.budokan },
];

Object.assign(window, { IMG, QMEMBERS, QSONGS, QPLAYLISTS, QMEMBER_CARDS, QRANKING, jacketBg });
