// Light field of ASCII + paw glyphs. A faint full wash, plus 9 moving elliptical "blobs"
// where the glyphs show strongly (a CSS mask of radial gradients that drift with the frame).
import { AbsoluteFill, useCurrentFrame } from "remotion";

const GLYPHS = ["/", "\\", "+", "*", "~", "^", "o", "#", "=", "u", "·", ":", "<", ">"];

// one tile of glyphs, as an SVG data URI (bright glyphs on transparent)
const tile = (color: string) => {
  const cell = 26, cols = 20, rows = 13;
  let s = "", n = 7;
  for (let y = 0; y < rows; y++)
    for (let x = 0; x < cols; x++) {
      n = (n * 9301 + 49297) % 233280; // deterministic pseudo-random
      const g = GLYPHS[n % GLYPHS.length];
      const esc = g === "<" ? "&lt;" : g === ">" ? "&gt;" : g;
      s += `<text x="${x * cell + 4}" y="${y * cell + 19}">${esc}</text>`;
    }
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${cols * cell}" height="${rows * cell}" font-family="monospace" font-size="17" fill="${color}">${s}</svg>`;
  return `url("data:image/svg+xml;utf8,${encodeURIComponent(svg)}")`;
};

const BLOBS = Array.from({ length: 9 }, (_, i) => ({
  x: 10 + ((i * 37) % 80), y: 12 + ((i * 53) % 76), rx: 14 + (i % 3) * 5, ry: 10 + (i % 4) * 4,
  sx: 0.004 + (i % 5) * 0.0015, sy: 0.003 + (i % 3) * 0.002, p: i * 1.7,
}));

export const GlyphBackground: React.FC = () => {
  const f = useCurrentFrame();
  const drift = `${-f * 0.35}px ${-f * 0.2}px`;
  const mask = BLOBS.map((b) => {
    const cx = b.x + Math.sin(f * b.sx * 6 + b.p) * 12;
    const cy = b.y + Math.cos(f * b.sy * 6 + b.p) * 10;
    return `radial-gradient(ellipse ${b.rx}% ${b.ry}% at ${cx}% ${cy}%, #000 0%, rgba(0,0,0,.55) 45%, transparent 72%)`;
  }).join(",");
  return (
    <AbsoluteFill style={{ background: "#FFFFFF" }}>
      <AbsoluteFill style={{ backgroundImage: tile("#B9E2FF"), backgroundSize: "338px", backgroundPosition: drift, opacity: 0.45 }} />
      <AbsoluteFill style={{ backgroundImage: tile("#38BDF8"), backgroundSize: "338px", backgroundPosition: drift, opacity: 0.62,
        WebkitMaskImage: mask, maskImage: mask }} />
    </AbsoluteFill>
  );
};
