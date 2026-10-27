// SVG hygiene checks and optimization.
import { optimize } from "svgo";

const BANNED = ["text", "tspan", "textPath", "image", "filter", "script", "foreignObject", "style", "mask", "use", "animate", "animateTransform", "set", "a", "iframe", "feGaussianBlur", "feDropShadow", "feOffset", "feBlend", "feColorMatrix", "feMerge", "feFlood", "feComposite"];

/** @returns {string[]} problems; empty means clean. */
export function hygiene(name, text, { source = true } = {}) {
  const problems = [];
  const bad = msg => problems.push(`${name}: ${msg}`);
  const root = text.match(/<svg\b[^>]*>/)?.[0] ?? "";
  if (!root) return [`${name}: no <svg> root`];
  if (!/xmlns="http:\/\/www\.w3\.org\/2000\/svg"/.test(root)) bad("missing SVG namespace");
  if (!/viewBox="0 0 512 512"/.test(root)) bad('root viewBox must be exactly "0 0 512 512"');
  if (/\s(width|height)=/.test(root)) bad("root must not set width/height (scale by CSS)");
  for (const tag of BANNED) if (new RegExp(`<${tag}[\\s>/]`, "i").test(text)) bad(`banned element <${tag}>`);
  if (/\son[a-z]+\s*=/i.test(text)) bad("event handler attribute");
  if (/(?:href|src)\s*=/i.test(text)) bad("href/src reference");
  if (/data:|https?:\/\/(?!www\.w3\.org\/2000\/svg)|javascript:/i.test(text)) bad("external or embedded reference");
  for (const m of text.matchAll(/url\(([^)]*)\)/g)) if (!/^#[A-Za-z][\w-]*$/.test(m[1].trim())) bad(`url(${m[1]}) is not a local fragment`);
  const ids = [...text.matchAll(/\sid="([^"]+)"/g)].map(m => m[1]);
  for (const id of new Set(ids.filter((v, i) => ids.indexOf(v) !== i))) bad(`duplicate id "${id}"`);
  for (const m of text.matchAll(/url\(#([^)]+)\)/g)) if (!ids.includes(m[1])) bad(`url(#${m[1]}) has no matching id`);
  if (source && /stroke=/.test(text) && !/<g id="bg">[\s\S]*stroke=[\s\S]*<\/g>\s*(?:<g id="glyph"|<\/svg)/.test(text)) bad("stroke is only allowed in the background group (the glyph uses filled shapes)");
  return problems;
}

export function optimizeSvg(text) {
  const out = optimize(text, {
    multipass: true,
    plugins: [{ name: "preset-default", params: { overrides: { cleanupIds: false } } }],
  });
  return out.data.endsWith("\n") ? out.data : out.data + "\n";
}
