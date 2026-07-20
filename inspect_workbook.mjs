import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = "C:/Users/Lenovo/Downloads/Base de Datos de Materiales y Herramientas.xlsx";

const input = await FileBlob.load(inputPath);
const workbook = await SpreadsheetFile.importXlsx(input);

const sheet = workbook.worksheets.getItemAt(0);
const usedRange = sheet.getUsedRange();
const values = usedRange.values;

await fs.writeFile(
  path.join(process.cwd(), "inspect_values.json"),
  JSON.stringify(values, null, 2),
  "utf8",
);

console.log(JSON.stringify(values, null, 2));
