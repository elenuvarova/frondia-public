/**
 * Ретро-аудит городского вмешательства по спутниковым снимкам
 * ============================================================
 * Google Earth Engine · Code Editor · JavaScript
 * Вставить целиком в https://code.earthengine.google.com и нажать Run.
 *
 * ЧТО ДЕЛАЕТ
 *   Считает, изменились ли растительность (NDVI) и температура поверхности (LST)
 *   внутри периметра вмешательства между «до» и «после» — и сравнивает это
 *   с контрольным кольцом вокруг, чтобы отделить эффект вмешательства от погоды.
 *
 * ГЛАВНЫЙ МЕТОДОЛОГИЧЕСКИЙ ПРИНЦИП
 *   Абсолютная температура скачет год от года из-за погоды. Поэтому меряем
 *   НЕ «стало на X градусов холоднее», а разность разностей (difference-in-differences):
 *
 *       эффект = (объект_после − объект_до) − (контроль_после − контроль_до)
 *
 *   Без этого мы измеряем лето, а не вмешательство. Это и есть та честность,
 *   которую продаём.
 *
 * ЧТО ЗАМЕНИТЬ ПЕРЕД ЗАПУСКОМ
 *   PERIMETER — координаты ниже ПРИБЛИЗИТЕЛЬНЫЕ, поставлены чтобы скрипт запускался.
 *   Настоящий периметр брать из contrat de quartier durable (GeoJSON/shapefile)
 *   и загружать как ассет: ee.FeatureCollection('projects/<проект>/assets/<имя>')
 */

// ─────────────────────────────────────────────────────────────────────────────
// 1. ПАРАМЕТРЫ
// ─────────────────────────────────────────────────────────────────────────────

// ⚠️ ПРИБЛИЗИТЕЛЬНЫЙ периметр: Parc de la Senne, фаза 2, квартал Masui–Reine.
// Заменить на настоящий из contrat de quartier.
var PERIMETER = ee.Geometry.Polygon([[
  [4.3505, 50.8695],
  [4.3585, 50.8695],
  [4.3585, 50.8745],
  [4.3505, 50.8745]
]]);

// Окна сравнения. «До» — заведомо до начала работ, «после» — когда посадки прижились.
// Парк сдан в 2020: даём зазор с обеих сторон.
var BEFORE = {start: '2017-01-01', end: '2019-12-31', label: 'до 2017–2019'};
var AFTER  = {start: '2021-01-01', end: '2024-12-31', label: 'после 2021–2024'};

// Только лето: зимние снимки не говорят ничего ни о кроне, ни о перегреве.
var SUMMER = [6, 8];  // июнь–август

// Контрольное кольцо вокруг объекта: тот же город, та же погода, без вмешательства.
var CONTROL_INNER_M = 300;   // отступ, чтобы не захватить край стройки
var CONTROL_OUTER_M = 1200;

var MAX_CLOUD = 30;          // % облачности для отбора сцен

// ─────────────────────────────────────────────────────────────────────────────
// 2. ГЕОМЕТРИИ
// ─────────────────────────────────────────────────────────────────────────────

var control = PERIMETER.buffer(CONTROL_OUTER_M)
                       .difference(PERIMETER.buffer(CONTROL_INNER_M), 1);

Map.centerObject(PERIMETER, 15);
Map.addLayer(control,   {color: 'FFFFFF'}, 'Контрольное кольцо', false);
Map.addLayer(PERIMETER, {color: '000000'}, 'Периметр вмешательства');

// ─────────────────────────────────────────────────────────────────────────────
// 3. NDVI — Sentinel-2, 10 м
// ─────────────────────────────────────────────────────────────────────────────

// Cloud Score+ — актуальный способ маскировать облака в S2.
var csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED');

function s2Summer(range) {
  return ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(PERIMETER)
    .filterDate(range.start, range.end)
    .filter(ee.Filter.calendarRange(SUMMER[0], SUMMER[1], 'month'))
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', MAX_CLOUD))
    .linkCollection(csPlus, ['cs_cdf'])
    .map(function (img) {
      var clear = img.select('cs_cdf').gte(0.6);          // 0.6 — рабочий порог
      var ndvi = img.normalizedDifference(['B8', 'B4']).rename('ndvi');
      return ndvi.updateMask(clear).copyProperties(img, ['system:time_start']);
    });
}

var ndviBefore = s2Summer(BEFORE).median().rename('ndvi_before');
var ndviAfter  = s2Summer(AFTER).median().rename('ndvi_after');
var ndviDelta  = ndviAfter.subtract(ndviBefore).rename('ndvi_delta');

// ─────────────────────────────────────────────────────────────────────────────
// 4. LST — Landsat 8/9 Collection 2 Level-2, готовый продукт ST_B10
// ─────────────────────────────────────────────────────────────────────────────

function lstSummer(range) {
  var l8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2');
  var l9 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2');
  return l8.merge(l9)
    .filterBounds(PERIMETER)
    .filterDate(range.start, range.end)
    .filter(ee.Filter.calendarRange(SUMMER[0], SUMMER[1], 'month'))
    .filter(ee.Filter.lt('CLOUD_COVER', MAX_CLOUD))
    .map(function (img) {
      // QA_PIXEL: бит 3 — облако, бит 4 — тень облака
      var qa = img.select('QA_PIXEL');
      var clear = qa.bitwiseAnd(1 << 3).eq(0)
              .and(qa.bitwiseAnd(1 << 4).eq(0));
      // Официальные коэффициенты Collection 2 L2 → Кельвины → Цельсий
      var lst = img.select('ST_B10')
                   .multiply(0.00341802).add(149.0).subtract(273.15)
                   .rename('lst');
      return lst.updateMask(clear).copyProperties(img, ['system:time_start']);
    });
}

var lstBefore = lstSummer(BEFORE).median().rename('lst_before');
var lstAfter  = lstSummer(AFTER).median().rename('lst_after');
var lstDelta  = lstAfter.subtract(lstBefore).rename('lst_delta');

// ─────────────────────────────────────────────────────────────────────────────
// 5. ЗОНАЛЬНАЯ СТАТИСТИКА + РАЗНОСТЬ РАЗНОСТЕЙ
// ─────────────────────────────────────────────────────────────────────────────

function zonal(img, band, geom, scale) {
  return ee.Number(
    img.select(band).reduceRegion({
      reducer: ee.Reducer.mean(),
      geometry: geom,
      scale: scale,
      maxPixels: 1e9,
      bestEffort: true
    }).get(band)
  );
}

function diffInDiff(deltaImg, band, scale, unit, title) {
  var onSite  = zonal(deltaImg, band, PERIMETER, scale);
  var onCtrl  = zonal(deltaImg, band, control,   scale);
  var effect  = onSite.subtract(onCtrl);

  print('──────── ' + title + ' ────────');
  print('  внутри периметра:      ', onSite, unit);
  print('  контрольное кольцо:    ', onCtrl, unit);
  print('  ЭФФЕКТ (разн. разностей):', effect, unit);
  return effect;
}

print('РЕТРО-АУДИТ · ' + BEFORE.label + '  →  ' + AFTER.label);
print('Полож. значения LST = стало теплее. Полож. NDVI = стало зеленее.');

var lstEffect  = diffInDiff(lstDelta,  'lst_delta',  100, '°C',      'Температура поверхности');
var ndviEffect = diffInDiff(ndviDelta, 'ndvi_delta',  10, 'ед. NDVI', 'Растительность (NDVI)');

// ─────────────────────────────────────────────────────────────────────────────
// 6. СКОЛЬКО СЦЕН ЛЕГЛО В ОСНОВУ — без этого результату верить нельзя
// ─────────────────────────────────────────────────────────────────────────────

print('──────── Обеспеченность снимками ────────');
print('Sentinel-2, до / после:', s2Summer(BEFORE).size(),  s2Summer(AFTER).size());
print('Landsat,    до / после:', lstSummer(BEFORE).size(), lstSummer(AFTER).size());
print('Если по любому окну меньше ~8 сцен — медиана шумная, результат не годится.');

// ─────────────────────────────────────────────────────────────────────────────
// 7. КАРТА
// ─────────────────────────────────────────────────────────────────────────────

// Расходящаяся рампа: бирюза = остыло, красный = нагрелось. Из валидированных.
var divergingLst = {
  min: -3, max: 3,
  palette: ['#0f6b63', '#22998d', '#5cc4b6', '#E8E8E4', '#f09a9a', '#e05f5f', '#c9302f']
};
// NDVI наоборот: рост зелени — хорошо, поэтому шкалу разворачиваем
var divergingNdvi = {
  min: -0.3, max: 0.3,
  palette: ['#c9302f', '#e05f5f', '#f09a9a', '#E8E8E4', '#5cc4b6', '#22998d', '#0f6b63']
};

Map.addLayer(lstDelta.clip(PERIMETER.buffer(CONTROL_OUTER_M)),  divergingLst,  'Δ температуры');
Map.addLayer(ndviDelta.clip(PERIMETER.buffer(CONTROL_OUTER_M)), divergingNdvi, 'Δ NDVI', false);

// Снимки «до» и «после» для картинки в заявку
var rgbVis = {bands: ['B4', 'B3', 'B2'], min: 0, max: 2500};
function s2Rgb(range) {
  return ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(PERIMETER).filterDate(range.start, range.end)
    .filter(ee.Filter.calendarRange(SUMMER[0], SUMMER[1], 'month'))
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))
    .median();
}
Map.addLayer(s2Rgb(BEFORE), rgbVis, 'Снимок ДО',    false);
Map.addLayer(s2Rgb(AFTER),  rgbVis, 'Снимок ПОСЛЕ', false);

// ─────────────────────────────────────────────────────────────────────────────
// 8. КАК ЧИТАТЬ РЕЗУЛЬТАТ
// ─────────────────────────────────────────────────────────────────────────────
//
//   Эффект LST около −1 °C и ниже, NDVI около +0,05 и выше,
//   при 8+ сценах в каждом окне  →  сигнал есть, идём по verification-first.
//
//   Эффект в пределах ±0,5 °C  →  на масштабе этого объекта не различаем.
//   Это НЕ провал: это честный результат, и он же — повод проверить объект
//   покрупнее (Tour & Taxis, 15 га) прежде чем делать выводы о продукте.
//
//   Landsat даёт тепловой канал с исходным разрешением ~100 м. Объект меньше
//   пары гектаров этим инструментом не измеряется в принципе — тогда NDVI
//   остаётся единственным честным показателем.
