import fs from "node:fs/promises";
import path from "node:path";

const inputPath = path.join(
  process.cwd(),
  "outputs",
  "v2_completo",
  "Base de Datos de Materiales y Herramientas_V2 - formato_objetivo.csv",
);
const outputPath = path.join(
  process.cwd(),
  "outputs",
  "v2_completo",
  "Base de Datos de Materiales y Herramientas_V2 - formato_objetivo_enriquecido.csv",
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

function normalize(text) {
  return String(text || "")
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();
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
  { test: ["taladro", "atornillador", "martillo perforador", "amoladora", "sierra", "multiherramienta"], category: "Power Tools", price: 179.9 },
  { test: ["aspirador"], category: "Cleaning Equipment", price: 89.9 },
  { test: ["linterna", "proyector led"], category: "Lighting", price: 39.9 },
  { test: ["bateria", "cargador", "adaptador usb"], category: "Batteries & Chargers", price: 49.9 },
  { test: ["destornillador de precision"], category: "Precision Tools", price: 29.9 },
  { test: ["destornillador", "llave", "alicate", "pelacables", "crimpadora", "cutter", "tijera", "martillo", "maza"], category: "Hand Tools", price: 24.9 },
  { test: ["nivel", "flexometro", "escuadra", "punta trazadora"], category: "Measuring & Layout Tools", price: 26.9 },
  { test: ["broca", "corona", "puntas de atornillar", "vasos magneticos", "discos", "lijas"], category: "Tool Accessories", price: 19.9 },
  { test: ["cable h07v", "cable flexible", "cable ethernet", "cable coaxial"], category: "Cables & Wiring", price: 49.9 },
  { test: ["bridas", "cinta aislante", "tubo corrugado", "canaleta", "regleta de conexion", "clemas", "wago", "terminales electricos", "termorretractil"], category: "Electrical Consumables", price: 9.9 },
  { test: ["enchufe", "interruptor", "conmutador", "caja de mecanismos", "caja de derivacion", "base multiple", "alargador", "diferencial", "magnetotermico"], category: "Electrical Installation", price: 17.9 },
  { test: ["keystone", "roseta rj45", "patch cord", "patch panel", "organizador de cables"], category: "Networking", price: 14.9 },
  { test: ["velcro"], category: "Cable Management", price: 8.9 },
  { test: ["tornillos", "tirafondos", "taco", "varilla roscada", "tuercas", "arandelas", "remaches", "grapas"], category: "Fixings & Fasteners", price: 7.9 },
  { test: ["silicona", "adhesivo", "espuma de poliuretano", "lubricante", "alcohol isopropilico", "limpiador de contactos", "trapos de limpieza"], category: "Chemicals & Consumables", price: 10.9 },
  { test: ["multimetro", "pinza amperimetrica", "detector", "comprobador"], category: "Electrical Testing", price: 59.9 },
  { test: ["guantes", "gafas", "casco", "chaleco", "protectores auditivos", "mascarillas", "botiquin"], category: "PPE & Safety", price: 14.9 },
  { test: ["escalera"], category: "Access Equipment", price: 129.9 },
  { test: ["caja de herramientas", "organizador de tornilleria", "mochila de herramientas", "carro de transporte"], category: "Storage & Transport", price: 39.9 },
  { test: ["bidon de agua"], category: "Site Supplies", price: 34.9 },
  { test: ["rotulador", "etiquetas"], category: "Marking & Identification", price: 12.9 },
];

function assignCategoryAndPrice(row) {
  const partNumber = row[0];
  const name = row[1];
  const description = row[3];
  const combined = `${name} ${description}`;
  const normalized = normalize(combined);

  if (manualAssignments.has(partNumber)) {
    return manualAssignments.get(partNumber);
  }

  for (const rule of keywordRules) {
    if (rule.test.some((term) => normalized.includes(normalize(term)))) {
      return { category: rule.category, price: rule.price };
    }
  }

  return { category: "General Supplies", price: 19.9 };
}

const raw = await fs.readFile(inputPath, "utf8");
const rows = parseCsv(raw);
const [header, ...dataRows] = rows;

const outputRows = [header];

for (const row of dataRows) {
  const cloned = [...row];
  while (cloned.length < 9) cloned.push("");
  const { category, price } = assignCategoryAndPrice(cloned);
  cloned[2] = price.toFixed(2);
  cloned[6] = category;
  outputRows.push(cloned);
}

const csvText = outputRows.map((row) => row.map(csvEscape).join(",")).join("\r\n");
await fs.writeFile(outputPath, csvText, "utf8");

console.log(JSON.stringify({ outputPath, rows: outputRows.length - 1 }, null, 2));
