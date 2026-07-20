import fs from "node:fs/promises";
import path from "node:path";

const inputPath = path.join(
  process.cwd(),
  "outputs",
  "v2_completo",
  "Base de Datos de Materiales y Herramientas_V2 - formato_objetivo_enriquecido.csv",
);
const outputPath = path.join(
  process.cwd(),
  "outputs",
  "v2_completo",
  "Base de Datos de Materiales y Herramientas_V2 - formato_objetivo_categorias_jerarquicas.csv",
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

const rules = [
  { terms: ["taladro", "atornillador", "martillo perforador", "amoladora", "sierra", "multiherramienta"], category: "Tools > Power Tools" },
  { terms: ["aspirador"], category: "Tools > Cleaning Equipment" },
  { terms: ["linterna", "proyector led"], category: "Electrical > Lighting" },
  { terms: ["bateria", "cargador", "adaptador usb"], category: "Electrical > Batteries & Chargers" },
  { terms: ["destornillador de precision"], category: "Tools > Precision Tools" },
  { terms: ["destornillador", "llave", "alicate", "pelacables", "crimpadora", "cutter", "tijera", "martillo", "maza"], category: "Tools > Hand Tools" },
  { terms: ["nivel", "flexometro", "escuadra", "punta trazadora"], category: "Tools > Measuring & Layout" },
  { terms: ["broca", "corona", "puntas de atornillar", "vasos magneticos", "discos", "lijas"], category: "Tools > Tool Accessories" },
  { terms: ["cable h07v", "cable flexible", "cable ethernet", "cable coaxial"], category: "Electrical > Cables & Wiring" },
  { terms: ["bridas", "cinta aislante", "tubo corrugado", "canaleta", "regleta de conexion", "clemas", "wago", "terminales electricos", "termorretractil"], category: "Electrical > Wiring Accessories" },
  { terms: ["enchufe", "interruptor", "conmutador", "caja de mecanismos", "caja de derivacion", "base multiple", "alargador", "diferencial", "magnetotermico"], category: "Electrical > Installation Devices" },
  { terms: ["keystone", "roseta rj45", "patch cord", "patch panel", "organizador de cables"], category: "Networking > Passive Components" },
  { terms: ["velcro"], category: "Networking > Cable Management" },
  { terms: ["tornillos", "tirafondos", "taco", "varilla roscada", "tuercas", "arandelas", "remaches", "grapas"], category: "Hardware > Fixings & Fasteners" },
  { terms: ["silicona", "adhesivo", "espuma de poliuretano"], category: "Consumables > Sealants & Adhesives" },
  { terms: ["lubricante", "alcohol isopropilico", "limpiador de contactos", "trapos de limpieza"], category: "Consumables > Maintenance & Cleaning" },
  { terms: ["multimetro", "pinza amperimetrica", "detector", "comprobador"], category: "Electrical > Test Equipment" },
  { terms: ["guantes", "gafas", "casco", "chaleco", "protectores auditivos", "mascarillas"], category: "Safety > PPE" },
  { terms: ["botiquin"], category: "Safety > First Aid" },
  { terms: ["escalera"], category: "Site Equipment > Access Equipment" },
  { terms: ["caja de herramientas", "organizador de tornilleria", "mochila de herramientas", "carro de transporte"], category: "Storage > Tool Storage & Transport" },
  { terms: ["bidon de agua"], category: "Site Equipment > Site Supplies" },
  { terms: ["rotulador", "etiquetas"], category: "Office & Identification > Marking & Labels" },
];

function assignHierarchicalCategory(name, description, flatCategory) {
  const combined = normalize(`${name} ${description}`);
  for (const rule of rules) {
    if (rule.terms.some((term) => combined.includes(normalize(term)))) {
      return rule.category;
    }
  }

  const fallbackMap = new Map([
    ["Power Tools", "Tools > Power Tools"],
    ["Cleaning Equipment", "Tools > Cleaning Equipment"],
    ["Lighting", "Electrical > Lighting"],
    ["Batteries & Chargers", "Electrical > Batteries & Chargers"],
    ["Precision Tools", "Tools > Precision Tools"],
    ["Hand Tools", "Tools > Hand Tools"],
    ["Measuring & Layout Tools", "Tools > Measuring & Layout"],
    ["Tool Accessories", "Tools > Tool Accessories"],
    ["Cables & Wiring", "Electrical > Cables & Wiring"],
    ["Electrical Consumables", "Electrical > Wiring Accessories"],
    ["Electrical Installation", "Electrical > Installation Devices"],
    ["Networking", "Networking > Passive Components"],
    ["Cable Management", "Networking > Cable Management"],
    ["Fixings & Fasteners", "Hardware > Fixings & Fasteners"],
    ["Chemicals & Consumables", "Consumables > Maintenance & Cleaning"],
    ["Electrical Testing", "Electrical > Test Equipment"],
    ["PPE & Safety", "Safety > PPE"],
    ["Access Equipment", "Site Equipment > Access Equipment"],
    ["Storage & Transport", "Storage > Tool Storage & Transport"],
    ["Site Supplies", "Site Equipment > Site Supplies"],
    ["Marking & Identification", "Office & Identification > Marking & Labels"],
    ["General Supplies", "General > Miscellaneous"],
  ]);

  return fallbackMap.get(flatCategory) ?? "General > Miscellaneous";
}

const raw = await fs.readFile(inputPath, "utf8");
const rows = parseCsv(raw);
const [header, ...dataRows] = rows;
const outputRows = [header];

for (const row of dataRows) {
  const cloned = [...row];
  while (cloned.length < 9) cloned.push("");
  cloned[6] = assignHierarchicalCategory(cloned[1], cloned[3], cloned[6]);
  outputRows.push(cloned);
}

const csvText = outputRows.map((row) => row.map(csvEscape).join(",")).join("\r\n");
await fs.writeFile(outputPath, csvText, "utf8");

console.log(JSON.stringify({ outputPath, rows: outputRows.length - 1 }, null, 2));
