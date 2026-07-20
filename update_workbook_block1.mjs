import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = "C:/Users/Lenovo/Downloads/Base de Datos de Materiales y Herramientas.xlsx";
const outputDir = path.join(process.cwd(), "outputs", "block_001");
const outputPath = path.join(outputDir, "Base de Datos de Materiales y Herramientas - bloque 001.xlsx");
const previewPath = path.join(outputDir, "preview_block_001.png");

const input = await FileBlob.load(inputPath);
const workbook = await SpreadsheetFile.importXlsx(input);
const sheet = workbook.worksheets.getItemAt(0);

const updates = new Map([
  [8, {
    ficha: null,
    imagen: null,
    comment:
      "No se completan las URLs porque el fabricante FEIN y el Part Number 71292760000 no coinciden con la descripcion 'MultiMaster AMM 500 Plus'. Las referencias localizadas para AMM 500 Plus usan otra numeracion oficial.",
  }],
  [9, {
    ficha: "https://www.kaercher.com/es/home-garden/aspiradores-multifuncionales/aspiradores-multiuso/wd-3-16298210.html",
    imagen: "https://s1.kaercher-media.com/mam/16298210/mainproduct/50018/d1.jpg",
  }],
  [10, {
    ficha: "https://www.milwaukeetool.eu/en-eu/m18-led-torch/m18-tled/",
    imagen: "https://static.milwaukeetool.eu/remote.axd/milwaukee-media-images.s3.amazonaws.com/hi/M18_TLED-0--Hero_2.jpg",
  }],
  [11, {
    ficha: null,
    imagen: null,
    comment:
      "No se completan las URLs porque no se pudo validar con suficiente certeza que el Part Number 1171630 corresponda exactamente al foco Brennenstuhl JARO 30W; las referencias oficiales localizadas usan otra numeracion de articulo.",
  }],
  [12, {
    ficha: "https://www.bosch-professional.com/il/he/products/gba-18v-2-0ah-1600Z00036",
    imagen: "https://www.bosch-professional.com/es/es/ocsmedia/273728-82/product-image/full/bateria-o-pack-de-nimh-de-12-v-2867981.png",
  }],
  [13, {
    ficha: "https://makita.ae/product/battery-lxt-50-ah-li-ion-18-v-bl1850b-197280-8/",
    imagen: "https://fi.makitamedia.com/images/3_Makita/301_machines/3011_a_GS1/30120_JPG_zoom/BL1850B_C2L0.jpg",
  }],
  [14, {
    ficha: "https://www.dewalt.de/produkt/dcb118-qw/schnellladegeraet-fuer-54-bzw-18-v-8a-ladestrom",
    imagen: null,
    comment:
      "Se confirma la ficha oficial para DCB118-QW, pero no se pudo extraer con suficiente certeza una URL directa de imagen oficial o de distribuidor reconocido; por eso la URL de imagen queda vacia.",
  }],
  [15, {
    ficha: "https://makita-groupe.fr/makita/page.php?REF=DEAADP05&rub=fiche&s_rub=s_categories_1_3",
    imagen: "https://fi.makitamedia.com/images/3_Makita/301_machines/3011_a_GS1/30120_JPG_zoom/ADP05_C2L0.jpg",
  }],
  [16, {
    ficha: null,
    imagen: null,
    comment:
      "No se completan las URLs porque el Part Number 5051010001 no coincide con la descripcion 'Kraftform Plus VDE 7 piezas'. La referencia oficial localizada para 05051010001 corresponde a otro set de Wera.",
  }],
  [17, {
    ficha: null,
    imagen: null,
    comment:
      "No se completan las URLs porque no se pudo validar una coincidencia exacta entre el Part Number 526 y el comprobador Wiha SoftFinish 110-250 V. Las referencias oficiales localizadas usan otros numeros de pedido.",
  }],
]);

await workbook.comments.setSelf({ displayName: "User" });

for (const [row, data] of updates.entries()) {
  sheet.getRange(`E${row}`).values = [[data.ficha]];
  sheet.getRange(`F${row}`).values = [[data.imagen]];

  if (data.comment) {
    workbook.comments.addThread({ cell: sheet.getRange(`E${row}`) }, data.comment);
  }
}

await fs.mkdir(outputDir, { recursive: true });

const check = await workbook.inspect({
  kind: "table",
  sheetId: sheet.name,
  range: "A8:F17",
  include: "values",
  tableMaxRows: 10,
  tableMaxCols: 6,
});

await fs.writeFile(path.join(outputDir, "check_block_001.ndjson"), check.ndjson, "utf8");

const preview = await workbook.render({
  sheetName: sheet.name,
  range: "A1:F20",
  scale: 1,
  format: "png",
});
await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));

const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputPath);

console.log(JSON.stringify({ outputPath, previewPath }, null, 2));
console.log(check.ndjson);
