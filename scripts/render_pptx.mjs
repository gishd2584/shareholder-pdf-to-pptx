import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

function usage() {
  console.error("Usage: node render_pptx.mjs --input graph.json --output chart.pptx [--preview chart.png] [--audit chart.ndjson]");
  process.exit(2);
}

function argsFrom(argv) {
  const result = {};
  for (let index = 0; index < argv.length; index += 2) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (!flag?.startsWith("--") || value === undefined) usage();
    result[flag.slice(2)] = value;
  }
  if (!result.input || !result.output) usage();
  return result;
}

function numberOr(value, fallback) {
  return Number.isFinite(value) ? value : fallback;
}

function computeLevels(nodes, edges) {
  const levels = new Map(nodes.map((node) => [node.id, numberOr(node.level, 0)]));
  for (let pass = 0; pass < nodes.length; pass += 1) {
    let changed = false;
    for (const edge of edges) {
      const proposed = levels.get(edge.from) + 1;
      if (!Number.isFinite(edge.toLevel) && proposed > levels.get(edge.to)) {
        levels.set(edge.to, proposed);
        changed = true;
      }
    }
    if (!changed) break;
  }
  const minimum = Math.min(...levels.values(), 0);
  for (const [id, level] of levels) levels.set(id, level - minimum);
  return levels;
}

function groupByLevel(nodes, levels) {
  const groups = new Map();
  for (const node of nodes) {
    const level = levels.get(node.id);
    if (!groups.has(level)) groups.set(level, []);
    groups.get(level).push(node);
  }
  for (const group of groups.values()) {
    group.sort((left, right) => numberOr(left.order, 9999) - numberOr(right.order, 9999) || left.id.localeCompare(right.id));
  }
  return groups;
}

function clamp(value, lower, upper) {
  return Math.max(lower, Math.min(value, upper));
}

async function writeBlob(filePath, blob) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

function addText(slide, name, text, position, style) {
  const box = slide.shapes.add({
    geometry: "textbox",
    name,
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  box.text = text;
  box.text.style = {
    typeface: "Microsoft YaHei",
    color: "#111111",
    alignment: "center",
    verticalAlignment: "middle",
    autoFit: "shrinkText",
    ...style,
  };
  return box;
}

async function main() {
  const args = argsFrom(process.argv.slice(2));
  const graph = JSON.parse(await fs.readFile(args.input, "utf8"));
  const nodes = graph.nodes || [];
  const edges = graph.edges || [];
  if (!nodes.length) throw new Error("graph must contain at least one node");

  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  for (const edge of edges) {
    if (!nodeById.has(edge.from) || !nodeById.has(edge.to)) {
      throw new Error(`Unknown edge endpoint: ${edge.from} -> ${edge.to}`);
    }
    edge.toLevel = Number.isFinite(nodeById.get(edge.to).level);
  }

  const levels = computeLevels(nodes, edges);
  const groups = groupByLevel(nodes, levels);
  const maxLevel = Math.max(...groups.keys());
  const maxCount = Math.max(...[...groups.values()].map((group) => group.length));
  const slideWidth = clamp(320 + maxCount * 270, 1920, 7200);
  const slideHeight = Math.max(1080, 290 + (maxLevel + 1) * 255);
  const marginX = 150;
  const levelTop = 160;
  const levelGap = 230;
  const nodeHeight = 86;
  const presentation = Presentation.create({ slideSize: { width: slideWidth, height: slideHeight } });
  const slide = presentation.slides.add();
  slide.background.fill = "#FFFFFF";
  addText(slide, "chart-title", graph.title || "股权架构图", {
    left: marginX,
    top: 44,
    width: slideWidth - marginX * 2,
    height: 64,
  }, { fontSize: 38, bold: true });

  const positioned = new Map();
  for (const [level, group] of groups) {
    const count = group.length;
    const available = slideWidth - marginX * 2;
    const gap = count === 1 ? 0 : clamp(available / (count * 4.2), 38, 92);
    const nodeWidth = clamp((available - gap * (count - 1)) / count, 174, 320);
    const groupWidth = nodeWidth * count + gap * (count - 1);
    const left = (slideWidth - groupWidth) / 2;
    const top = levelTop + level * levelGap;
    group.forEach((node, index) => {
      positioned.set(node.id, { left: left + index * (nodeWidth + gap), top, width: nodeWidth, height: nodeHeight });
    });
  }

  const shapes = new Map();
  for (const node of nodes) {
    const position = positioned.get(node.id);
    const shape = slide.shapes.add({
      geometry: node.shape === "ellipse" ? "ellipse" : "rect",
      name: `node-${node.id}`,
      position,
      fill: "#FFFFFF",
      line: { style: "solid", fill: "#111111", width: 2 },
    });
    shape.text = node.label;
    shape.text.style = {
      typeface: "Microsoft YaHei",
      fontSize: clamp(position.width / Math.max(7, node.label.length), 20, 30),
      bold: false,
      color: "#111111",
      alignment: "center",
      verticalAlignment: "middle",
      autoFit: "shrinkText",
      insets: { top: 8, right: 12, bottom: 8, left: 12 },
    };
    shapes.set(node.id, shape);
  }

  for (const edge of edges) {
    const source = shapes.get(edge.from);
    const target = shapes.get(edge.to);
    const sourcePos = positioned.get(edge.from);
    const targetPos = positioned.get(edge.to);
    slide.shapes.connect(source, target, {
      kind: Math.abs(sourcePos.left - targetPos.left) < 12 ? "straight" : "elbow",
      fromSide: "bottom",
      toSide: "top",
      line: { style: "solid", fill: "#111111", width: 1.6 },
      // Artifact Tool places `tail` on the target end of a connector.
      tail: { type: "triangle", width: "med", length: "med" },
    });
    if (edge.holding || edge.label) {
      const label = String(edge.holding || edge.label);
      addText(slide, `holding-${edge.from}-${edge.to}`, label, {
        left: clamp(sourcePos.left + sourcePos.width / 2 - 78, 18, slideWidth - 174),
        top: sourcePos.top + sourcePos.height + 9,
        width: 156,
        height: 35,
      }, { fontSize: 23, bold: false });
    }
  }

  for (const node of nodes) {
    if (!node.tag) continue;
    const position = positioned.get(node.id);
    addText(slide, `tag-${node.id}`, String(node.tag), {
      left: position.left,
      top: position.top - 42,
      width: position.width,
      height: 32,
    }, { fontSize: 22, bold: false });
  }

  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(args.output);
  if (args.preview) await writeBlob(args.preview, await presentation.export({ slide, format: "png", scale: 1 }));
  if (args.audit) {
    const audit = await presentation.inspect({ kind: "slide,textbox,shape", maxChars: 20000 });
    await fs.mkdir(path.dirname(args.audit), { recursive: true });
    await fs.writeFile(args.audit, audit.ndjson, "utf8");
  }
  console.log(`Created editable PowerPoint: ${args.output}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
