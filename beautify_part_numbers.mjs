import fs from "node:fs/promises";
import path from "node:path";

const inputPath = path.join(
  process.cwd(),
  "outputs",
  "v2_completo",
  "Base de Datos de Materiales y Herramientas_V2 - formato_objetivo_desde_imagenes.csv",
);
const outputPath = path.join(
  process.cwd(),
  "outputs",
  "v2_completo",
  "Base de Datos de Materiales y Herramientas_V2 - formato_objetivo_desde_imagenes_partnumbers_bonitos.csv",
);

function parseCsv(text) {
  const rows = [];
  let row = [];
  let cell = "";
  let inQuotes = false;

  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    const next = text[i + 1];

    if (inQuotes) {
      if (ch === '"' && next === '"') {
        cell += '"';
        i += 1;
      } else if (ch === '"') {
        inQuotes = false;
      } else {
        cell += ch;
      }
    } else if (ch === '"') {
      inQuotes = true;
    } else if (ch === ",") {
      row.push(cell);
      cell = "";
    } else if (ch === "\n") {
      row.push(cell.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      cell = "";
    } else {
      cell += ch;
    }
  }

  if (cell.length > 0 || row.length > 0) {
    row.push(cell.replace(/\r$/, ""));
    rows.push(row);
  }

  return rows;
}

function csvEscape(value) {
  const text = value == null ? "" : String(value);
  if (/[",\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

const prefixMap = new Map([
  ["Power Tools", "PWT"],
  ["Cleaning Equipment", "CLE"],
  ["Lighting", "LGT"],
  ["Batteries & Chargers", "BAT"],
  ["Precision Tools", "PRT"],
  ["Hand Tools", "HDT"],
  ["Measuring & Layout Tools", "MEA"],
  ["Tool Accessories", "ACC"],
  ["Cables & Wiring", "CBL"],
  ["Electrical Consumables", "ELC"],
  ["Electrical Installation", "ELI"],
  ["Networking", "NET"],
  ["Cable Management", "CBM"],
  ["Fixings & Fasteners", "FIX"],
  ["Sealants & Adhesives", "SEA"],
  ["Maintenance & Cleaning", "MNT"],
  ["Electrical Testing", "TST"],
  ["PPE", "PPE"],
  ["First Aid", "FAD"],
  ["Access Equipment", "ACS"],
  ["Tool Storage & Transport", "STO"],
  ["Site Supplies", "SIT"],
  ["Marking & Labels", "MRK"],
  ["General Supplies", "GEN"],
]);

const raw = await fs.readFile(inputPath, "utf8");
const rows = parseCsv(raw);
const [header, ...dataRows] = rows;

const counters = new Map();
const outputRows = [header];

for (const row of dataRows) {
  const cloned = [...row];
  while (cloned.length < 9) cloned.push("");
  const category = cloned[6] || "General Supplies";
  const prefix = prefixMap.get(category) ?? "GEN";
  const next = (counters.get(prefix) ?? 0) + 1;
  counters.set(prefix, next);
  cloned[0] = `${prefix}${String(next).padStart(7, "0")}`;
  outputRows.push(cloned);
}

const csvText = outputRows.map((row) => row.map(csvEscape).join(",")).join("\r\n");
await fs.writeFile(outputPath, csvText, "utf8");

console.log(JSON.stringify({ outputPath, rows: outputRows.length - 1 }, null, 2));
