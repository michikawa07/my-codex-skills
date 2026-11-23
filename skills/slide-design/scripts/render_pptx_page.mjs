#!/usr/bin/env node
// Render selected pages of the saved PPTX with a single import.
import { writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";
import { pathToFileURL } from "node:url";

const [source, ...requests] = process.argv.slice(2);
if (!source || requests.length < 2 || requests.length % 2) {
  throw new Error("Usage: node render_pptx_page.mjs INPUT.pptx PAGE OUTPUT.png [PAGE OUTPUT.png ...]");
}
const pages = [];
for (let i = 0; i < requests.length; i += 2) {
  const number = Number(requests[i]);
  const output = requests[i + 1];
  if (!Number.isInteger(number) || number < 1 || path.extname(output).toLowerCase() !== ".png") {
    throw new Error("Specify a positive page number and a PNG path for each page.");
  }
  pages.push({ number, output });
}
const modules = process.env.RUNTIME_NODE_MODULES || process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES
  || path.resolve(path.dirname(process.execPath), "..", "node_modules");
const requireFromRuntime = createRequire(path.join(modules, "__runtime__.cjs"));
const entry = requireFromRuntime.resolve("@oai/artifact-tool");
const { FileBlob, PresentationFile } = await import(pathToFileURL(entry).href);
const deck = await PresentationFile.importPptx(await FileBlob.load(source));
for (const { number, output } of pages) {
  const slide = deck.slides.items[number - 1];
  if (!slide) throw new Error("Page outside the presentation");
  const png = await deck.export({ slide, format: "png", scale: 1 });
  await writeFile(output, new Uint8Array(await png.arrayBuffer()));
  console.log(output);
}
