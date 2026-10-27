// pnpm build:icons [projectId] [--variant <name>] [--out <dir>]
// Generates every export for a project from its SVG masters. Exports are never edited by hand.
import { readFile, writeFile, mkdir, rm, rename } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { EXPORTS, ROOT, paths, parseArgs, selectProjects, SOURCE_FILES } from "./lib/project.mjs";
import { openBrowser, renderSvg } from "./lib/render.mjs";
import { encode } from "./lib/png.mjs";
import { buildIco } from "./lib/ico.mjs";
import { hygiene, optimizeSvg } from "./lib/svg.mjs";

/** Build one project into outDir. Returns Map<relativeFile, Buffer>. Used by verify for determinism checks. */
export async function buildProject(browser, id, outDir, variant = null) {
  const p = paths(id, variant), sources = {};
  for (const name of SOURCE_FILES) {
    sources[name] = await readFile(join(p.source, name), "utf8").catch(() => { throw new Error(`${join(p.source, name)} is missing`); });
    const problems = hygiene(name, sources[name]);
    if (problems.length) throw new Error(`Refusing to build ${id}:\n  ${problems.join("\n  ")}`);
  }
  const out = new Map();
  for (const spec of EXPORTS.filter(e => e.src || e.svg)) {
    if (spec.svg) { out.set(spec.file, Buffer.from(optimizeSvg(sources[spec.svg]))); continue; }
    if (spec.ico) {
      const frames = [];
      for (const size of spec.ico) frames.push({ size, png: encode(await renderSvg(browser, sources[spec.src], size)) });
      out.set(spec.file, buildIco(frames)); continue;
    }
    out.set(spec.file, encode(await renderSvg(browser, sources[spec.src], spec.size), { opaque: spec.alpha === "opaque" }));
  }
  for (const spec of EXPORTS.filter(e => e.copyOf)) out.set(spec.file, out.get(spec.copyOf));
  for (const [file, bytes] of out) {
    await mkdir(dirname(join(outDir, file)), { recursive: true });
    await writeFile(join(outDir, file), bytes);
  }
  return out;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const args = parseArgs(process.argv.slice(2));
  if (args.out && !args.id) throw new Error("--out needs a project id (several projects would overwrite each other in one directory)");
  const outOverride = args.out ? resolve(args.out) : null;
  const browser = await openBrowser();
  try {
    for (const id of await selectProjects(args.id, args.variant)) {
      const target = outOverride ?? paths(id, args.variant).exports;
      // Build into a staging directory first. The existing exports are only replaced once the whole build succeeded,
      // so a failed build (for example an SVG hygiene error) can never leave a project without its exports.
      const stage = join(ROOT, ".cache", `build-${id}${args.variant ? "-" + args.variant : ""}-${process.pid}`);
      await rm(stage, { recursive: true, force: true });
      const out = await buildProject(browser, id, stage, args.variant);
      const backup = `${stage}.previous`;
      await mkdir(dirname(target), { recursive: true });
      await rm(backup, { recursive: true, force: true });
      await rename(target, backup).catch(error => { if (error.code !== "ENOENT") throw error; }); // nothing to back up on a first build
      await rename(stage, target);
      await rm(backup, { recursive: true, force: true });
      console.log(`${id}${args.variant ? "/" + args.variant : ""}: wrote ${out.size} files to ${target}`);
      for (const [file, bytes] of out) console.log(`  ${file.padEnd(34)} ${String(bytes.length).padStart(6)} B`);
    }
  } finally { await browser.close(); }
}
