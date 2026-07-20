import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = "C:/Users/Lenovo/Downloads/Base de Datos de Materiales y Herramientas_V2.xlsx";
const outputDir = path.join(process.cwd(), "outputs", "v2_completo");
const outputPath = path.join(outputDir, "Base de Datos de Materiales y Herramientas_V2 - alternativas_mejoradas.xlsx");
const previewPath = path.join(outputDir, "preview_v2_completo.png");

const input = await FileBlob.load(inputPath);
const workbook = await SpreadsheetFile.importXlsx(input);
const sheet = workbook.worksheets.getItemAt(0);
const rawAlt = JSON.parse(await fs.readFile(path.join(process.cwd(), "alternative_results_v2.json"), "utf8"));
const rawAltImages = JSON.parse(
  await fs.readFile(path.join(process.cwd(), "alternative_results_with_images_v2.json"), "utf8"),
);

const alternativeMap = new Map(rawAlt.map((item) => [item._row, item]));
const alternativeImageMap = new Map(rawAltImages.map((item) => [item._row, item]));

const exactUpdates = new Map([
  [21, {
    ficha: "https://www.bahco.com/at_de/rollgabelschlussel-mit-zentralmutter--phosphatiert--255--mm-8072.html",
    imagen: null,
    comment:
      "Se valida la ficha oficial de Bahco para la referencia 8072, pero no se pudo recuperar con suficiente certeza una URL directa y estable de imagen del producto.",
  }],
  [25, {
    ficha: "https://www.knipex.com/es-es/productos/alicates-universales-y-multifuncionales/alicates-universales/alicates-universales/0302180?sku=0307200&v=6702",
    imagen: null,
    comment:
      "Se valida la ficha oficial de Knipex para 03 02 180, pero no se pudo recuperar con suficiente certeza una URL directa y estable de imagen del producto.",
  }],
  [26, {
    ficha: "https://www.knipex.com/es-es/productos/alicates-cortantes/alicates-de-corte-diagonal/alicates-de-corte-diagonal/7002160",
    imagen: null,
    comment:
      "Se valida la ficha oficial de Knipex para 70 02 160, pero no se pudo recuperar con suficiente certeza una URL directa y estable de imagen del producto.",
  }],
  [27, {
    ficha: "https://www.knipex-tools.com/products/knipextend/long-nose-pliers/long-nose-pliers-cutter-and-awg-stripping-hole/2612200?source=share",
    imagen: null,
    comment:
      "Se valida la ficha oficial de Knipex para 26 12 200, pero no se pudo recuperar con suficiente certeza una URL directa y estable de imagen del producto.",
  }],
  [29, {
    ficha: "https://www.knipex.com/en-uk/products/crimping-pliers/crimping-pliers-for-western-plugs/crimping-pliers-western-plugs/975110?sku=975110&v=4851",
    imagen: null,
    comment:
      "Se valida la ficha oficial de Knipex para 97 51 10, pero no se pudo recuperar con suficiente certeza una URL directa y estable de imagen del producto.",
  }],
  [30, {
    ficha: "https://www.knipex-tools.com/products/crimping-pliers/knipex-preciforce/knipex-preciforce-crimping-pliers-insulated-terminals-plug-connectors-and-butt-connectors/975236",
    imagen: "https://web-assets.knipex.com/sites/default/files/975236-00-3.jpg",
  }],
  [31, {
    ficha: "https://www.manomano.es/p/cutter-interlock-m-plastico-stanley-010418-18-mm-38695136?model_id=2002917",
    imagen: null,
    comment:
      "Se valida una ficha de distribuidor reconocido para Stanley 0-10-418, pero no se pudo recuperar con suficiente certeza una URL directa y estable de imagen del producto.",
  }],
  [36, {
    ficha: "https://www.bosch-professional.com/gb/en/products/gll-2-15-g-0601063W02",
    imagen: null,
    comment:
      "No se localizo con suficiente certeza la referencia exacta 0601066B00. Se enlaza como alternativa oficial Bosch Professional de un nivel laser de lineas GLL 2-15 G.",
  }],
  [56, {
    ficha: "https://www.unex.net/es/brida-de-uso-interior-y-exterior-48x188-mm-en-u61x/2244-0",
    imagen: "https://files.unex.net/global/products/img/2244-0-R.png",
  }],
  [63, {
    ficha: "https://www.wago.com/global/installation-terminal-blocks-and-connectors/splicing-connector-with-levers/p/222-412",
    imagen: "https://www.wago.com/medias/200-11347030-DE.jpg?context=bWFzdGVyfGltYWdlc3wxNzI5OXxpbWFnZS9qcGVnfGFHWm1MMmd6Tnk4eE5qRTNOekF3TlRrMU16QTFOQzh5TURCZk1URXpORGN3TXpCZlJFVXVhbkJufDEwYmYzYzQyZDlmNjJhZmE0NTkzMjJmNTY2NmM4ZmM5NTcwMDBmMzlmM2ZlYjFkOGQxMjg4NWUyZmUyNDQ2MzM",
  }],
  [64, {
    ficha: "https://www.wago.com/global/installation-terminal-blocks-and-connectors/splicing-connector-with-levers/p/221-413",
    imagen: null,
    comment:
      "Se completa con la ficha oficial WAGO 221-413. No se pudo recuperar con suficiente certeza una URL directa y estable de imagen del producto.",
  }],
  [76, {
    ficha: "https://www.se.com/at/de/product/A9Z21240/fehlerstromschutzschalter-iid-2p-40a-30ma-typ-a/",
    imagen: null,
    comment:
      "No se localizo con suficiente certeza la referencia exacta A9R21240 en Schneider. Se enlaza como alternativa oficial un diferencial iID 2P 40A 30mA tipo A muy cercano.",
  }],
  [77, {
    ficha: "https://www.se.com/mx/es/product/A9F74116/acti9-interruptor-termomagnetico-ic60n-1x16a-curva-c/",
    imagen: "https://download.schneider-electric.com/files?default_image=DefaultProductImage.png&p_Doc_Ref=A9F74116_Image&p_File_Type=rendition_369_jpg",
  }],
  [105, {
    ficha: "https://www.fluke.com/es-us/producto/comprobacion-electrica/multimetros-digitales/fluke-115",
    imagen: "https://media.fluke.com/8a32f731-a3c4-446b-ad0f-b108002ad62f_original__size.jpg",
  }],
  [106, {
    ficha: "https://www.fluke.com/es-es/producto/comprobacion-electrica/pinzas-amperimetricas/fluke-323",
    imagen: "https://media.fluke.com/c0eacec0-218d-47a2-9ca4-b108002e0817_original__size.jpg",
  }],
  [107, {
    ficha: "https://www.fluke.com/es-es/producto/comprobacion-electrica/comprobadores-basicos/fluke-1ac-ii",
    imagen: "https://media.fluke.com/bb41f897-6aaa-4645-b42c-b1c4016bfa2d_original%20file.jpg",
  }],
  [108, {
    ficha: "https://www.boschtools.com/us/es/products/d-tect120-0601081311",
    imagen: null,
    comment:
      "No se localizo con suficiente certeza la referencia exacta 601081000. Se enlaza como alternativa oficial Bosch para el detector D-TECT120.",
  }],
  [110, {
    ficha: "https://www.fluke.com/en-us/product/network-cable-testers/copper/mt-8200-49a",
    imagen: null,
    comment:
      "La referencia MT-8200-49A corresponde en Fluke a MicroMapper, no a MicroScanner2. Se enlaza como alternativa del mismo tipo de comprobador de red.",
  }],
  [111, {
    ficha: "https://www.deltaplusbrasil.com.br/pt/p/ve702p",
    imagen: null,
    comment:
      "Se completa con la ficha oficial Delta Plus VE702P. No se pudo recuperar con suficiente certeza una URL directa y estable de imagen del producto.",
  }],
  [113, {
    ficha: "https://www.petzl.com/US/en/Professional/Helmets/VERTEX-VENT?trk=public_post_comment-text",
    imagen: null,
    comment:
      "No se localizo con suficiente certeza la referencia exacta A010AA00. Se enlaza como alternativa oficial Petzl VERTEX VENT del mismo tipo de casco.",
  }],
  [116, {
    ficha: "https://www.3m.com.es/3M/es_ES/p/d/v000125639/",
    imagen: null,
    comment:
      "Se completa con la ficha oficial 3M para la mascarilla 9320+. No se pudo recuperar con suficiente certeza una URL directa y estable de imagen del producto.",
  }],
  [119, {
    ficha: "https://www.stanleyworks.de/produkt/1-97-514/24-werkzeugtrage-mit-organizeraufsatz",
    imagen: null,
    comment:
      "Se completa con la ficha oficial STANLEY 1-97-514. No se pudo recuperar con suficiente certeza una URL directa y estable de imagen del producto.",
  }],
  [122, {
    ficha: "https://www.stanleytools.co.uk/product/sxwtd-ft580/70kg-folding-hand-truck",
    imagen: null,
    comment:
      "Se completa con la ficha oficial STANLEY SXWTD-FT580. No se pudo recuperar con suficiente certeza una URL directa y estable de imagen del producto.",
  }],
  [124, {
    ficha: "https://www.edding.com/es-es/productos/edding-3000-marcador-permanente/",
    imagen: "https://www.edding.com/fileadmin/products/29775/e-3000__light-green_4-3000011_4004764008063_02.jpg",
  }],
  [125, {
    ficha: "https://store.brother.es/supplies/ptouch/tapes/tze/tze231",
    imagen: null,
    comment:
      "Se valida la ficha oficial de Brother para TZe231, pero no se pudo recuperar con suficiente certeza una URL directa y estable de imagen del producto.",
  }],
]);

const specificComments = new Map([
  [50, "No se completan las URLs porque en esta fila las columnas de fabricante y Part Number parecen desplazadas; no se puede validar la referencia exacta con suficiente certeza."],
  [51, "No se completan las URLs porque en esta fila las columnas de fabricante y Part Number parecen desplazadas; no se puede validar la referencia exacta con suficiente certeza."],
  [52, "No se completan las URLs porque en esta fila las columnas de fabricante y Part Number parecen desplazadas; no se puede validar la referencia exacta con suficiente certeza."],
  [53, "No se completan las URLs porque en esta fila las columnas de fabricante y Part Number parecen desplazadas; no se puede validar la referencia exacta con suficiente certeza."],
  [72, "No se completan las URLs porque las coincidencias localizadas para 'Solera 520' no permitieron validar una ficha exacta del producto descrito."],
  [73, "No se completan las URLs porque las coincidencias localizadas para 'Solera 316' no permitieron validar una ficha exacta del producto descrito."],
  [108, "No se completan las URLs porque las referencias oficiales localizadas para D-tect 120 no coinciden exactamente con el Part Number indicado 601081000."],
  [110, "No se completan las URLs porque el Part Number MT-8200-49A localizado en Fluke Networks corresponde a MicroMapper, no a MicroScanner2 Cable Verifier."],
]);

const genericComment =
  "No se completan las URLs porque no se pudo validar con suficiente certeza una coincidencia exacta entre fabricante, Part Number y descripcion del producto.";

const genericToolImage =
  "https://bynder.sbdinc.com/m/3f4dcbe4c38e4f12/Drupal_Large-ST_stanley-category-fallbackat2x_GEB1.jpg";
const genericTapeImage =
  "https://multimedia.3m.com/mws/media/1140830J/3m-adhesive-transfer-tape-9471-305-mm-x-55-m-crop.jpg";
const genericElectricalImage =
  "https://www.wago.com/medias/200-11347030-DE.jpg?context=bWFzdGVyfGltYWdlc3wxNzI5OXxpbWFnZS9qcGVnfGFHWm1MMmd6Tnk4eE5qRTNOekF3TlRrMU16QTFOQzh5TURCZk1URXpORGN3TXpCZlJFVXVhbkJufDEwYmYzYzQyZDlmNjJhZmE0NTkzMjJmNTY2NmM4ZmM5NTcwMDBmMzlmM2ZlYjFkOGQxMjg4NWUyZmUyNDQ2MzM";
const genericPliersImage = "https://web-assets.knipex.com/sites/default/files/975236-00-3.jpg";
const genericMeasureImage = genericToolImage;
const genericTesterImage =
  "https://media.fluke.com/8a32f731-a3c4-446b-ad0f-b108002ad62f_original__size.jpg";
const genericPipeWrenchImage =
  "https://media.doitcenter.com.pa/media/catalog/product/1/6/165876241_hrkf5lfyfsn9ymgr.jpg?quality=85&fit=bounds";
const genericAdjustableWrenchImage = "http://www.m8w.co.uk/cdn/shop/files/wrench_0778.jpg?v=1780840492";
const genericMarkerImage =
  "https://www.edding.com/fileadmin/products/29775/e-3000__light-green_4-3000011_4004764008063_02.jpg";

function encodeQuery(text) {
  return encodeURIComponent(String(text || "").replace(/\s+/g, " ").trim());
}

function amazonSearchUrl(name, desc) {
  return `https://www.amazon.es/s?k=${encodeQuery(`${name} ${desc}`)}`;
}

function fallbackFicha(row, name, desc) {
  const manual = new Map([
    [22, "https://www.doitcenter.com.pa/productos/llaves-de-tubo-de-14-pulgadas-stanley-llaves-87-624-16587624"],
    [23, "https://www.amazon.es/s?k=juego+llaves+de+vaso"],
    [24, "https://www.amazon.es/s?k=juego+llaves+combinadas"],
    [35, "https://www.amazon.es/s?k=nivel+de+burbuja+60+cm"],
    [39, "https://www.amazon.es/s?k=punta+de+trazar+doble"],
    [44, "https://www.amazon.es/s?k=coronas+bimetalicas+electricista"],
    [45, "https://www.amazon.es/s?k=juego+puntas+atornillar"],
    [46, "https://www.amazon.es/s?k=vaso+magnetico+hexagonal+8mm"],
    [47, "https://www.amazon.es/s?k=disco+de+corte+metal"],
    [48, "https://www.amazon.es/s?k=disco+diamante+segmentado"],
    [49, "https://www.amazon.es/s?k=lija+orbital+grano+120"],
    [74, "https://www.leroymerlin.es/productos/electricidad-y-domotica/bases-multiples-y-enrollacables/regletas-de-enchufes/"],
    [78, "https://www.amazon.es/s?k=keystone+rj45+cat6"],
    [80, "https://www.amazon.es/s?k=patch+cord+cat6+1m"],
    [81, "https://www.amazon.es/s?k=patch+cord+cat6+2m"],
    [82, "https://www.amazon.es/s?k=patch+panel+cat6+24+puertos"],
    [83, "https://www.amazon.es/s?k=organizador+de+cables+rack"],
    [84, "https://www.amazon.es/s?k=velcro+para+cables"],
    [85, "https://www.amazon.es/s?k=tornillo+madera+4x40"],
    [86, "https://www.amazon.es/s?k=tornillo+rosca+chapa+4.2x13"],
    [87, "https://www.amazon.es/s?k=tirafondo+hexagonal+8x60"],
    [88, "https://www.amazon.es/s?k=taco+nylon+6x30"],
    [89, "https://www.amazon.es/s?k=taco+nylon+8x40"],
    [90, "https://www.amazon.es/s?k=taco+nylon+10x50"],
    [91, "https://www.amazon.es/s?k=taco+quimico+resina+inyeccion"],
    [97, "https://www.amazon.es/s?k=silicona+neutra+blanca"],
    [98, "https://www.amazon.es/s?k=silicona+sanitaria+antimoho"],
    [99, "https://www.amazon.es/s?k=adhesivo+de+montaje"],
    [100, "https://www.amazon.es/s?k=espuma+de+poliuretano+750ml"],
    [101, "https://www.amazon.es/s?k=lubricante+multiusos+spray"],
    [102, "https://www.amazon.es/s?k=alcohol+isopropilico"],
    [103, "https://www.amazon.es/s?k=limpiador+de+contactos"],
    [104, "https://www.amazon.es/s?k=panos+de+limpieza+rollo"],
    [109, "https://www.amazon.es/s?k=comprobador+de+enchufes"],
    [112, "https://www.amazon.es/s?k=gafas+de+proteccion+integrales"],
    [114, "https://www.amazon.es/s?k=chaleco+reflectante+alta+visibilidad"],
    [115, "https://www.amazon.es/s?k=orejeras+proteccion+acustica"],
    [117, "https://www.amazon.es/s?k=botiquin+primeros+auxilios"],
    [118, "https://www.amazon.es/s?k=escalera+telescopica+3.8m"],
    [120, "https://www.amazon.es/s?k=organizador+tornilleria"],
    [121, "https://www.amazon.es/s?k=mochila+herramientas"],
    [123, "https://www.amazon.es/s?k=bidon+agua+2+galones"],
  ]);

  if (manual.has(row)) {
    return manual.get(row);
  }

  const alt = alternativeMap.get(row)?.ficha;
  if (alt && !/britannica\.com|elcorteingles\.es\/musica|base\.com\/es-AR\/home/.test(alt)) {
    return alt;
  }

  return amazonSearchUrl(name, desc);
}

function fallbackImage(row, name, desc) {
  const exactAltImage = alternativeImageMap.get(row)?.imagen;
  if (exactAltImage && !/\/og\.png$/.test(exactAltImage)) {
    return exactAltImage;
  }

  const text = `${name} ${desc}`.toLowerCase();
  if (row === 21 || text.includes("llave inglesa")) return genericAdjustableWrenchImage;
  if (row === 22 || text.includes("llave grifa") || text.includes("llave de tubo")) return genericPipeWrenchImage;
  if (text.includes("alicate") || text.includes("crimpadora") || text.includes("pelacables")) return genericPliersImage;
  if (text.includes("cinta")) return genericTapeImage;
  if (
    text.includes("cable") ||
    text.includes("wago") ||
    text.includes("clema") ||
    text.includes("enchufe") ||
    text.includes("interruptor") ||
    text.includes("conmutador") ||
    text.includes("regleta") ||
    text.includes("canaleta") ||
    text.includes("tubo corrugado") ||
    text.includes("termorretráctil") ||
    text.includes("termorretractil") ||
    text.includes("keystone") ||
    text.includes("roseta")
  ) return genericElectricalImage;
  if (
    text.includes("multímetro") ||
    text.includes("multimetro") ||
    text.includes("pinza amperimétrica") ||
    text.includes("pinza amperimetrica") ||
    text.includes("detector") ||
    text.includes("comprobador")
  ) return genericTesterImage;
  if (text.includes("rotulador") || text.includes("etiqueta")) return genericMarkerImage;
  if (text.includes("flexómetro") || text.includes("flexometro") || text.includes("nivel") || text.includes("escuadra")) {
    return genericMeasureImage;
  }
  return genericToolImage;
}

await workbook.comments.setSelf({ displayName: "User" });

for (let row = 21; row <= 125; row += 1) {
  const name = sheet.getRange(`A${row}`).values?.[0]?.[0] ?? "";
  const desc = sheet.getRange(`D${row}`).values?.[0]?.[0] ?? "";
  const exact = exactUpdates.get(row);
  if (exact) {
    const resolvedFicha = exact.ficha ?? fallbackFicha(row, name, desc);
    const resolvedImage = exact.imagen ?? fallbackImage(row, name, desc);
    sheet.getRange(`E${row}`).values = [[resolvedFicha]];
    sheet.getRange(`F${row}`).values = [[resolvedImage]];
    const comment = exact.comment ?? (exact.imagen ? null : "Se mantiene la ficha localizada y se completa la imagen con una alternativa generica del mismo tipo de producto.");
    if (comment) {
      workbook.comments.addThread({ cell: sheet.getRange(`E${row}`) }, comment);
    }
    continue;
  }

  sheet.getRange(`E${row}`).values = [[fallbackFicha(row, name, desc)]];
  sheet.getRange(`F${row}`).values = [[fallbackImage(row, name, desc)]];
  const comment = specificComments.get(row)
    ? `${specificComments.get(row)} Se enlaza ademas una alternativa generica del mismo tipo de producto.`
    : "Se enlaza una alternativa generica del mismo tipo de producto porque no se confirmo la referencia exacta original.";
  workbook.comments.addThread({ cell: sheet.getRange(`E${row}`) }, comment);
}

await fs.mkdir(outputDir, { recursive: true });

const check = await workbook.inspect({
  kind: "table",
  sheetId: sheet.name,
  range: "A21:F125",
  include: "values",
  tableMaxRows: 105,
  tableMaxCols: 6,
});
await fs.writeFile(path.join(outputDir, "check_v2.ndjson"), check.ndjson, "utf8");

const preview = await workbook.render({
  sheetName: sheet.name,
  range: "A18:F30",
  scale: 1,
  format: "png",
});
await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));

const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputPath);

console.log(JSON.stringify({ outputPath, previewPath }, null, 2));
