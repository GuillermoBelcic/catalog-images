import fs from "node:fs/promises";
import path from "node:path";

const inputPath =
  "C:/Users/Lenovo/Downloads/Base de Datos de Materiales y Herramientas_V2 - alternativas_mejoradas.csv";
const outputDir = path.join(process.cwd(), "outputs", "v2_completo");
const outputPath = path.join(
  outputDir,
  "Base de Datos de Materiales y Herramientas_V2 - formato_objetivo.csv",
);

function parseTsv(text) {
  const lines = text.replace(/\r\n/g, "\n").replace(/\r/g, "\n").split("\n").filter(Boolean);
  return lines.map((line) => line.split("\t"));
}

function csvEscape(value) {
  const text = value == null ? "" : String(value);
  if (/[",\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

function supplierNameFromUrl(url) {
  if (!url) return "";
  try {
    const host = new URL(url).hostname.toLowerCase().replace(/^www\./, "");
    const parts = host.split(".");
    if (parts.length >= 2) {
      return parts[0]
        .split("-")
        .map((s) => (s ? s[0].toUpperCase() + s.slice(1) : s))
        .join(" ");
    }
  } catch {}
  return "";
}

const raw = await fs.readFile(inputPath, "latin1");
const rows = parseTsv(raw);
const [header, ...dataRows] = rows;

const sourceIndex = Object.fromEntries(header.map((name, idx) => [name, idx]));
const targetHeader = [
  "partNumber",
  "name",
  "unitCost",
  "description",
  "image",
  "manufacturerName",
  "categoryName",
  "Supplier name",
  "Supplier part number",
];

const outputRows = [targetHeader];

for (const row of dataRows) {
  const partNumber = row[sourceIndex["Part Number"]] ?? "";
  const name = row[sourceIndex["Nombre"]] ?? "";
  const description = row[sourceIndex["Descripción"]] ?? "";
  const image = row[sourceIndex["URL imagen"]] ?? "";
  const manufacturerName = row[sourceIndex["Fabricante"]] ?? "";
  const supplierUrl = row[sourceIndex["URL ficha"]] ?? "";
  const supplierName = supplierNameFromUrl(supplierUrl);

  outputRows.push([
    partNumber,
    name,
    "",
    description,
    image,
    manufacturerName,
    "",
    supplierName,
    partNumber,
  ]);
}

const csvText = outputRows.map((row) => row.map(csvEscape).join(",")).join("\r\n");

await fs.mkdir(outputDir, { recursive: true });
await fs.writeFile(outputPath, csvText, "utf8");

console.log(JSON.stringify({ outputPath, rows: outputRows.length - 1 }, null, 2));
