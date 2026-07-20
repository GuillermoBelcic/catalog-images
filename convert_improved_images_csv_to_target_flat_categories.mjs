import fs from "node:fs/promises";
import path from "node:path";

const inputPath =
  "C:/Users/Lenovo/Documents/TicTap cosas/outputs/v2_completo/Base de Datos de Materiales y Herramientas_V2 - alternativas_mejoradas_imagenes.csv";
const outputPath = path.join(
  process.cwd(),
  "outputs",
  "v2_completo",
  "Base de Datos de Materiales y Herramientas_V2 - formato_objetivo_desde_imagenes.csv",
);

function parseTsv(text) {
  return text
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .split("\n")
    .filter(Boolean)
    .map((line) => line.split("\t"));
}

function csvEscape(value) {
  const text = value == null ? "" : String(value);
  if (/[",\n]/.test(text)) return `"${text.replace(/"/g, '""')}"`;
  return text;
}

function normalize(text) {
  return String(text || "")
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();
}

function supplierNameFromUrl(url) {
  if (!url) return "";
  try {
    const host = new URL(url).hostname.toLowerCase().replace(/^www\./, "");
    const root = host.split(".")[0] || "";
    return root
      .split("-")
      .map((s) => (s ? s[0].toUpperCase() + s.slice(1) : s))
      .join(" ");
  } catch {
    return "";
  }
}

const manualAssignments = new Map([
  ["06019H5300", { category: "Power Tools", price: 189.0 }],
  ["DCD710D2", { category: "Power Tools", price: 129.0 }],
  ["DHR242Z", { category: "Power Tools", price: 219.0 }],
  ["06019F2000", { category: "Power Tools", price: 199.0 }],
  ["DJV180Z", { category: "Power Tools", price: 145.0 }],
  ["DCS367N", { category: "Power Tools", price: 179.0 }],
  ["71292760000", { category: "Power Tools", price: 229.0 }],
  ["1.198-301.0", { category: "Cleaning Equipment", price: 84.9 }],
  ["M18 TLED-0", { category: "Lighting", price: 49.9 }],
  ["1171630", { category: "Lighting", price: 59.9 }],
  ["1600Z00036", { category: "Batteries & Chargers", price: 44.9 }],
  ["197280-8", { category: "Batteries & Chargers", price: 79.9 }],
  ["DCB118-QW", { category: "Batteries & Chargers", price: 89.9 }],
  ["DEAADP05", { category: "Batteries & Chargers", price: 24.9 }],
  ["5051010001", { category: "Hand Tools", price: 34.9 }],
  ["526", { category: "Electrical Testing", price: 6.9 }],
  ["5118150001", { category: "Precision Tools", price: 42.9 }],
  ["5073593001", { category: "Hand Tools", price: 29.9 }],
  ["366RS9", { category: "Hand Tools", price: 24.9 }],
]);

const keywordRules = [
  { terms: ["taladro", "atornillador", "martillo perforador", "amoladora", "sierra", "multiherramienta"], category: "Power Tools", price: 179.9 },
  { terms: ["aspirador"], category: "Cleaning Equipment", price: 89.9 },
  { terms: ["linterna", "proyector led"], category: "Lighting", price: 39.9 },
  { terms: ["bateria", "cargador", "adaptador usb"], category: "Batteries & Chargers", price: 49.9 },
  { terms: ["destornillador de precision"], category: "Precision Tools", price: 29.9 },
  { terms: ["destornillador", "llave", "alicate", "pelacables", "crimpadora", "cuter", "cutter", "tijera", "martillo", "maza"], category: "Hand Tools", price: 24.9 },
  { terms: ["nivel", "flexometro", "escuadra", "punta trazadora"], category: "Measuring & Layout Tools", price: 26.9 },
  { terms: ["broca", "corona", "puntas de atornillar", "vasos magneticos", "discos", "lijas"], category: "Tool Accessories", price: 19.9 },
  { terms: ["cable h07v", "cable flexible", "cable ethernet", "cable coaxial"], category: "Cables & Wiring", price: 49.9 },
  { terms: ["bridas", "cinta aislante", "tubo corrugado", "canaleta", "regleta de conexion", "clemas", "wago", "terminales electricos", "termorretractil"], category: "Electrical Consumables", price: 9.9 },
  { terms: ["enchufe", "interruptor", "conmutador", "caja de mecanismos", "caja de derivacion", "base multiple", "alargador", "diferencial", "magnetotermico"], category: "Electrical Installation", price: 17.9 },
  { terms: ["keystone", "roseta rj45", "patch cord", "patch panel", "organizador de cables"], category: "Networking", price: 14.9 },
  { terms: ["velcro"], category: "Cable Management", price: 8.9 },
  { terms: ["tornillos", "tirafondos", "taco", "varilla roscada", "tuercas", "arandelas", "remaches", "grapas"], category: "Fixings & Fasteners", price: 7.9 },
  { terms: ["silicona", "adhesivo", "espuma de poliuretano"], category: "Sealants & Adhesives", price: 10.9 },
  { terms: ["lubricante", "alcohol isopropilico", "limpiador de contactos", "trapos de limpieza"], category: "Maintenance & Cleaning", price: 10.9 },
  { terms: ["multimetro", "pinza amperimetrica", "detector", "comprobador"], category: "Electrical Testing", price: 59.9 },
  { terms: ["guantes", "gafas", "casco", "chaleco", "protectores auditivos", "mascarillas"], category: "PPE", price: 14.9 },
  { terms: ["botiquin"], category: "First Aid", price: 14.9 },
  { terms: ["escalera"], category: "Access Equipment", price: 129.9 },
  { terms: ["caja de herramientas", "organizador de tornilleria", "mochila de herramientas", "carro de transporte"], category: "Tool Storage & Transport", price: 39.9 },
  { terms: ["bidon de agua"], category: "Site Supplies", price: 34.9 },
  { terms: ["rotulador", "etiquetas"], category: "Marking & Labels", price: 12.9 },
];

function assignCategoryAndPrice(partNumber, name, description) {
  if (manualAssignments.has(partNumber)) return manualAssignments.get(partNumber);
  const combined = normalize(`${name} ${description}`);
  for (const rule of keywordRules) {
    if (rule.terms.some((term) => combined.includes(normalize(term)))) {
      return { category: rule.category, price: rule.price };
    }
  }
  return { category: "General Supplies", price: 19.9 };
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
  const { category, price } = assignCategoryAndPrice(partNumber, name, description);

  outputRows.push([
    partNumber,
    name,
    price.toFixed(2),
    description,
    image,
    manufacturerName,
    category,
    supplierName,
    partNumber,
  ]);
}

const csvText = outputRows.map((row) => row.map(csvEscape).join(",")).join("\r\n");
await fs.writeFile(outputPath, csvText, "utf8");

console.log(JSON.stringify({ outputPath, rows: outputRows.length - 1 }, null, 2));
