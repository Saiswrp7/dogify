// Dogify: 60 s behind-the-scenes MVP video. 1920x1080, 30 fps.
// Scenes: hook → problem → validation → "let's see it work" → 3 x (input | action | output) → behind the scenes → end card.
import { AbsoluteFill, Audio, Img, Loop, OffthreadVideo, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Dithering } from "@paper-design/shaders-react";
import { loadFont } from "@remotion/google-fonts/BricolageGrotesque";
import { loadFont as loadHand } from "@remotion/google-fonts/GochiHand";
import { GlyphBackground } from "./Glyphs";

const { fontFamily } = loadFont("normal", { weights: ["500", "800"], subsets: ["latin"] });
const { fontFamily: hand } = loadHand();
const INK = "#111", BLUE = "#011ADD", SKY = "#38BDF8";

// ---------- building blocks ----------

// Headline filled with animated blue dither: dither layer + white box with black text on top (screen),
// so only the letters show the dither; the whole thing multiplies onto the background so white vanishes.
const Dither: React.FC<{ children: React.ReactNode; size: number; weight?: number }> = ({ children, size, weight = 800 }) => {
  const f = useCurrentFrame();
  return (
    <div style={{ position: "relative", display: "inline-block", isolation: "isolate", mixBlendMode: "multiply" }}>
      <Dithering style={{ position: "absolute", inset: 3 }} colorBack={BLUE} colorFront="#33FFFF" shape="warp" type="4x4"
        pxSize={3} speed={0} frame={(f * 1000) / 30} />
      <div style={{ position: "relative", background: "#fff", color: "#000", mixBlendMode: "screen", fontFamily,
        fontWeight: weight, fontSize: size, lineHeight: 1.05, letterSpacing: "-0.03em", padding: "0 0.06em 0.08em" }}>{children}</div>
    </div>
  );
};

// Jitter-style reveal: each word fades in from blur, one after another.
const Words: React.FC<{ text: string; at?: number; stagger?: number }> = ({ text, at = 0, stagger = 4 }) => {
  const f = useCurrentFrame();
  return (
    <>
      {text.split(" ").map((w, i) => {
        const t = f - at - i * stagger;
        const p = interpolate(t, [0, 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        return (
          <span key={i} style={{ display: "inline-block", marginRight: "0.24em", opacity: p,
            filter: `blur(${(1 - p) * 14}px)`, transform: `translateY(${(1 - p) * 18}px)` }}>{w}</span>
        );
      })}
    </>
  );
};

const Headline: React.FC<{ text: string; size?: number; at?: number }> = ({ text, size = 120, at = 0 }) => (
  <Dither size={size}><Words text={text} at={at} /></Dither>
);

const Chip: React.FC<{ children: React.ReactNode; at?: number }> = ({ children, at = 0 }) => {
  const f = useCurrentFrame();
  const p = interpolate(f - at, [0, 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: 12, background: "#EFEFEF", color: INK, fontFamily, fontWeight: 500,
      fontSize: 30, padding: "12px 24px", borderRadius: 999, border: "1.5px solid rgba(0,0,0,0.22)", outline: "1px solid rgba(0,0,0,0.08)",
      outlineOffset: 3, opacity: p, transform: `scale(${0.9 + p * 0.1})` }}>{children}</div>
  );
};

const Photo: React.FC<{ src: string; w: number; h: number; at?: number; rot?: number; fit?: "cover" | "contain" }> = ({ src, w, h, at = 0, rot = 0, fit = "cover" }) => {
  const f = useCurrentFrame(), { fps } = useVideoConfig();
  const s = spring({ frame: f - at, fps, config: { damping: 14 } });
  return (
    <div style={{ width: w, height: h, borderRadius: 28, overflow: "hidden", border: "1.5px solid rgba(0,0,0,0.22)",
      transform: `rotate(${rot}deg) scale(${0.85 + s * 0.15})`, opacity: s, background: "#000" }}>
      <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: fit }} />
    </div>
  );
};

const Clip: React.FC<{ src: string; w: number; h: number; from?: number; loop?: number }> = ({ src, w, h, from = 0, loop }) => {
  const video = <OffthreadVideo src={staticFile(src)} muted startFrom={from} style={{ width: "100%", height: "100%", objectFit: "cover" }} />;
  return (
    <div style={{ position: "relative", width: w, height: h, borderRadius: 28, overflow: "hidden", border: "1.5px solid rgba(0,0,0,0.22)", background: "#000" }}>
      {loop ? <Loop durationInFrames={loop}>{video}</Loop> : video}
    </div>
  );
};

const Center: React.FC<{ children: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", textAlign: "center", ...style }}>{children}</AbsoluteFill>
);

const Label: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div style={{ fontFamily: hand, fontSize: 34, color: INK, marginBottom: 10 }}>{children}</div>
);

// ---------- scenes ----------

const Hook = () => {
  const f = useCurrentFrame();
  const beat = f < 62 ? "Netflix" : f < 92 ? "Tinder" : f < 138 ? "endless scrolling" : null; // hard cuts on the voice
  return (
    <>
      {beat && (
        <Center>
          <Headline text="Humans have" size={110} />
          <div style={{ height: 10 }} />
          <Headline key={beat} text={beat} size={150} at={f < 62 ? 8 : f < 92 ? 62 : 92} />
        </Center>
      )}
      <Sequence from={138} durationInFrames={72}>
        <Center style={{ flexDirection: "row", gap: 80 }}>
          <div style={{ textAlign: "left" }}><Headline text="Dogs have" size={110} /><br /><Headline text="a door" size={150} at={14} /></div>
          <Photo src="img/pablo_side.jpg" w={380} h={500} at={4} rot={3} />
        </Center>
      </Sequence>
      <Sequence from={210}>
        <Center>
          <Headline text="Dogify" size={260} />
          <div style={{ height: 8 }} />
          <Headline text="for dogs" size={90} at={10} />
          <div style={{ height: 44 }} />
          <Chip at={22}>🐘 Built by Team Sober Hathi</Chip>
        </Center>
      </Sequence>
    </>
  );
};

const Problem = () => (
  <AbsoluteFill style={{ flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 120 }}>
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 36 }}>
      <Photo src="img/ravi.jpg" w={440} h={500} rot={-2} />
      <Headline text="Ravi feels guilty" size={78} at={6} />
      <Chip at={70}>90% of owners feel guilty</Chip>
    </div>
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 36 }}>
      <Photo src="img/pablo_yawn.jpg" w={440} h={500} rot={2} at={30} />
      <Headline text="Pablo feels lonely" size={78} at={36} />
      <Chip at={90}>anxious within 3 minutes</Chip>
    </div>
  </AbsoluteFill>
);

const Validation = () => (
  <Center style={{ gap: 30 }}>
    <Headline text="We read 15 research papers" size={100} />
    <Headline text="plus Reddit and Twitter" size={66} at={14} />
    <div style={{ display: "flex", gap: 24, marginTop: 40 }}>
      <Chip at={30}>14 to 20% of dogs have separation anxiety</Chip>
      <Chip at={48}>barking starts 3 min after you leave</Chip>
    </div>
    <Chip at={66}>India pet care: $3.6B → $7B by FY28</Chip>
  </Center>
);

// Recreated Telegram chat for the INPUT column (the real bot has the same buttons)
const Telegram: React.FC<{ kind: "voice" | "treat" | "video" }> = ({ kind }) => {
  const f = useCurrentFrame();
  const sent = interpolate(f, [8, 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const reply = interpolate(f, [40, 52], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const bubble = (mine: boolean, p: number, child: React.ReactNode) => (
    <div style={{ alignSelf: mine ? "flex-end" : "flex-start", maxWidth: "82%", background: mine ? "#E1FFC7" : "#fff", color: INK,
      borderRadius: 22, padding: "16px 20px", fontSize: 28, fontFamily, fontWeight: 500, opacity: p, transform: `translateY(${(1 - p) * 20}px)`,
      border: "1px solid rgba(0,0,0,0.08)" }}>{child}</div>
  );
  const bars = Array.from({ length: 22 }, (_, i) => 8 + Math.abs(Math.sin(i * 1.3 + f * 0.25)) * 30);
  const mine = kind === "voice"
    ? <div style={{ display: "flex", alignItems: "center", gap: 4 }}>🎤&nbsp;{bars.map((h, i) => <div key={i} style={{ width: 5, height: h, background: "#4FAE4E", borderRadius: 3 }} />)}&nbsp;0:04</div>
    : kind === "treat" ? "🦴 Treat"
    : <div style={{ width: 210, height: 210, borderRadius: "50%", overflow: "hidden" }}><Img src={staticFile("img/ravi.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover" }} /></div>;
  const answer = { voice: "Playing your voice note to Pablo now.", treat: "Treat dropped. 🦴", video: "Playing your video on Pablo's screen now." }[kind];
  return (
    <div style={{ width: 440, height: 800, borderRadius: 28, overflow: "hidden", background: "#CFE5F6", border: "1.5px solid rgba(0,0,0,0.22)",
      display: "flex", flexDirection: "column" }}>
      <div style={{ background: "#fff", padding: "18px 22px", fontFamily, fontWeight: 600, fontSize: 26, color: INK }}>Dogify 🐶<span style={{ fontWeight: 500, color: "#888", fontSize: 20 }}> · bot</span></div>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "flex-end", gap: 14, padding: 20 }}>
        {bubble(true, sent, mine)}
        {bubble(false, reply, answer)}
      </div>
    </div>
  );
};

const Arrow = () => <div style={{ fontFamily, fontSize: 56, color: INK, margin: "0 14px", paddingTop: 50 }}>→</div>;

const Beat: React.FC<{ n: string; title: string; kind: "voice" | "treat" | "video"; act: string; actLen: number; out: string; outFrom?: number; soundAt: number }> = ({ n, title, kind, act, actLen, out, outFrom = 0, soundAt }) => {
  const f = useCurrentFrame();
  const show = (at: number) => ({ opacity: interpolate(f, [at, at + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) });
  return (
    <AbsoluteFill style={{ alignItems: "center", paddingTop: 34 }}>
      <Headline text={`${n} · ${title}`} size={64} />
      <div style={{ display: "flex", alignItems: "center", marginTop: 22 }}>
        <div style={show(0)}><Label>INPUT · RAVI TAPS</Label><Telegram kind={kind} /></div>
        <div style={show(30)}><Arrow /></div>
        <Sequence from={soundAt} layout="none"><Audio src={staticFile(`clips/snd_${kind}.m4a`)} /></Sequence>
        <div style={show(34)}><Label>ACTION · DOG SCREEN</Label>
          <Sequence from={34} layout="none"><Clip src={act} w={700} h={800} loop={actLen} /></Sequence></div>
        <div style={show(64)}><Arrow /></div>
        <div style={show(68)}><Label>OUTPUT · PABLO</Label>
          <Sequence from={68} layout="none"><Clip src={out} w={450} h={800} from={outFrom} /></Sequence></div>
      </div>
    </AbsoluteFill>
  );
};

const BTS_ITEMS: { src: string; video?: boolean; cap: string }[] = [
  { src: "clips/bts_notes.mp4", video: true, cap: "planning" },
  { src: "clips/bts_laptops.mp4", video: true, cap: "building" },
  { src: "img/hardware.jpg", cap: "wiring the box" },
  { src: "clips/bts_wiring.mp4", video: true, cap: "more wiring" },
  { src: "clips/bts_talk.mp4", video: true, cap: "arguing, a bit" },
  { src: "clips/bts_setup.mp4", video: true, cap: "testing with Pablo" },
];
const BTS_EACH = 38;

const BehindTheScenes = () => {
  const f = useCurrentFrame();
  const i = Math.min(BTS_ITEMS.length - 1, Math.floor((f - 30) / BTS_EACH));
  return (
    <>
      <Sequence durationInFrames={30}><Center><Headline text="Behind the scenes" size={130} /></Center></Sequence>
      {BTS_ITEMS.map((it, k) => (
        <Sequence key={k} from={30 + k * BTS_EACH} durationInFrames={BTS_EACH}>
          <Center style={{ flexDirection: "row", gap: 70 }}>
            {it.video ? <Clip src={it.src} w={520} h={780} /> : <Photo src={it.src} w={520} h={780} />}
            <div style={{ width: 620, textAlign: "left" }}><Headline text={it.cap} size={96} /></div>
          </Center>
        </Sequence>
      ))}
      <Sequence from={30 + BTS_ITEMS.length * BTS_EACH}>
        <Center style={{ gap: 36 }}>
          <Photo src="img/team.jpg" w={900} h={675} rot={-1.5} />
          <Chip at={12}>🐘 Team Sober Hathi</Chip>
        </Center>
      </Sequence>
      {i >= 0 && null}
    </>
  );
};

const End = () => (
  <AbsoluteFill style={{ flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 90 }}>
    <Photo src="img/pablo_highfive.jpg" w={560} h={746} rot={-3} />
    <div style={{ width: 900 }}>
      <Dither size={70} weight={500}><Words text="Dogs do speak, but only to those who know how to listen" stagger={3} /></Dither>
      <div style={{ fontFamily: hand, fontSize: 36, color: "#555", margin: "22px 0 60px" }}>Orhan Pamuk</div>
      <Headline text="Dogify" size={170} at={40} />
      <div style={{ height: 30 }} />
      <Chip at={60}>🐘 Team Sober Hathi</Chip>
    </div>
  </AbsoluteFill>
);

// ---------- timeline ----------
const SCENES: [React.FC, number][] = [
  [Hook, 300],
  [Problem, 190],
  [Validation, 215],
  [() => <Center><Headline text="Let's see it work" size={140} /></Center>, 60],
  [() => <Beat n="01" title="Voice note" kind="voice" act="clips/act_voice.mp4" actLen={150} out="clips/out_voice.mp4" soundAt={78} />, 275],
  [() => <Beat n="02" title="Treat" kind="treat" act="clips/act_treat.mp4" actLen={84} out="clips/out_treat.mp4" soundAt={58} />, 220],
  [() => <Beat n="03" title="Video from Ravi" kind="video" act="clips/act_video.mp4" actLen={150} out="clips/out_video.mp4" outFrom={60} soundAt={70} />, 285],
  [BehindTheScenes, 30 + BTS_ITEMS.length * BTS_EACH + 75],
  [End, 150],
];
export const TOTAL = SCENES.reduce((a, [, d]) => a + d, 0);

// voiceover lines: [file, start frame, length in frames]
const VO: [string, number, number][] = [
  ["h1", 4, 60], ["h2", 62, 27], ["h3", 92, 40], ["h4", 140, 64], ["h5", 212, 82],
  ["p1", 308, 180], ["v1", 496, 202], ["l1", 711, 34],
  ["b1a", 767, 73], ["b1b", 995, 38], ["b2a", 1042, 55], ["b2b", 1208, 44], ["b3a", 1262, 67], ["b3b", 1482, 56],
  ["s1", 1549, 208], ["s2", 1807, 52], ["e1", 1898, 84],
];
// the real dog-screen sounds inside each beat: [start, length]
const SOUNDS: [number, number][] = [[765 + 78, 150], [1040 + 58, 108], [1260 + 70, 150]];

// music sits at 0.30 and dips to 0.09 under any voice or dog-screen sound (8-frame ramps)
const musicVolume = (f: number) => {
  const busy = [...VO.map(([, s, d]) => [s, d] as [number, number]), ...SOUNDS];
  const duck = Math.max(0, ...busy.map(([s, d]) =>
    interpolate(f, [s - 8, s, s + d, s + d + 8], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })));
  return 0.30 - duck * 0.21;
};

export const DogifyBTS: React.FC = () => {
  let at = 0;
  return (
    <AbsoluteFill>
      <GlyphBackground />
      <Audio src={staticFile("music.wav")} volume={musicVolume} />
      {VO.map(([file, start]) => (
        <Sequence key={file} from={start} layout="none"><Audio src={staticFile(`vo/${file}.mp3`)} /></Sequence>
      ))}
      {SCENES.map(([Scene, d], k) => {
        const from = at; at += d;
        return <Sequence key={k} from={from} durationInFrames={d}><Scene /></Sequence>;
      })}
    </AbsoluteFill>
  );
};
