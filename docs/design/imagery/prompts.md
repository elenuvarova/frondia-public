# Frondia · фото для сайта — промпты

27.09.2026. Состояние: промпты «шелеста» A–D готовы, не прогонялись; «кольцо» и «бирка» — черновики.

## Правило

Сгенерированная картинка не изображает данные (спутник, до/после) и реальные места (Droogdokkenpark, Ninove и
т. п.): обещание сайта — «измерено, а не на глаз». Генерируем только метафору: **шелест** (шум), **кольцо**
(факт), **бирка** (документ), плюс og-картинку и обложку кейса. Для реальных мест — настоящие фото (Wikimedia
Commons с указанием автора).

## Что не сработало (первый прогон)

- «Overcast, Portra +1, pale sage, no saturated green» → выцветшие серо-оливковые деревья во всех моделях.
  Цвет не тот, сирени нет.
- Полоска палитры как референс и слово «palette» в промпте → Higgsfield Soul рисует плашки цветов прямо в
  кадре, добавляет плёночную рамку и небоскрёбы. Soul — модель под людей, для деревьев не брать.
- Seedream держит описание лучше Soul.

## Как держать палитру

- Зелень CADRO: контровое низкое солнце — просвеченные листья кислотно-лаймовые, тень кроны — глубокая
  бутылочная зелень с бирюзой. Плёнка сочная: Ektar 100 или Velvia 50.
- Сирень приходит **содержимым или светом**, как в Satoyama (лиловые цветы в кадре) и CADRO (свечение в
  расфокусе): цветущая сирень, сиреневое небо после заката, либо Aerochrome.
- В промпте — никаких hex-кодов и слова «palette». Референс — только вырезанный градиент CADRO
  (`refs/ref-cadro-gradient.jpg`) с подписью «use this image only for colour, not content».
- Формат 3:2 (og-картинку потом обрезать до 1200×630, webp).

## Шелест (шум) — четыре варианта

**A. Сирень на переднем плане**
```
A mature linden tree in a small city park moving in a strong wind, photographed through a flowering common lilac bush (Syringa vulgaris) in the foreground. The lilac blossoms nearest the lens are large soft out-of-focus clouds of lavender and pale violet across the lower third; behind them the linden's trunk and main branches are sharp while its leaves are smeared into directional streaks by a 1/4-second exposure. Late afternoon sun low behind the tree: backlit leaves glow acid lime-yellow, the shade inside the crown is deep bottle green with a hint of teal. Mamiya RZ67, 110mm lens wide open at f/2.8, tripod, Kodak Ektar 100: saturated, fine grain, clean colour. Tree slightly off-centre.
```

**B. Сиреневый закат** — градиент CADRO: лайм у горизонта → сирень вверху
```
A single wind-bent tree at the edge of a city park against the sky ten minutes after sunset. The sky is a soft gradient: pale acid lime-yellow at the horizon on the left, turning lavender and lilac-pink higher up on the right. The trunk and branches are crisp and dark bottle green; the leaves blur into streaks in the wind during a 1-second exposure, the moving crown catching lilac light at its edges. Low camera, Hasselblad 500C/M with an 80mm lens, f/8, tripod, Fuji Velvia 50: saturated deep greens, the magenta-lilac cast slide film gives a dusk sky. Tree in the left third, open sky on the right.
```

**C. Aerochrome** — инфракрасная плёнка: живые листья сиреневые (то же свойство листа, на котором стоит NDVI).
Риск: розовое близко к шкале потерь `#EB7F7F` — держать подальше от карт и графиков.
```
Colour-infrared photograph on Kodak Aerochrome III 1443 with a yellow filter: the living leaves of a large park tree render lavender, lilac and soft pink, the trunk and branches dark aubergine, the sky clear teal-cyan, the grass below pale pink. The crown moves in the wind; leaves smeared by a 1/8-second exposure while the trunk stays sharp. Bright sunny day, Pentax 67 with a 105mm lens, f/8, tripod, fine even film grain.
```

**D. Сквозь листву** — расфокус как у CADRO
```
Looking into the crown of a linden tree on a windy summer evening through a veil of out-of-focus leaves and lilac blossoms right in front of the lens. Most of the frame is soft colour: glowing acid-lime backlit leaves, deep bottle-green and teal shade, a soft lavender-pink bloom where the low sun flares through lilac petals. Only one branch in the middle distance is sharp; the leaves around it streak with motion. 135mm lens wide open at f/2, 1/15 second, Kodak Ektar 100, gentle lens flare. It reads almost like an abstract colour field, but it is a real photograph.
```

**Хвост — к каждому из A–D и к «кольцу»** (с 27.09 — только утвердительно, см. раунд 2):
```
One continuous photograph that fills the frame edge to edge.
```
~~Full-bleed photograph: no borders, no film rebate or edge markings, no colour swatches or palette chips, no text, no buildings, no people.~~
У Soul (и у Flux-подобных моделей) нет негативного поля: названное «no X» модель скорее нарисует. Каждое
исключение — описанием того, что должно быть.

## Раунд 2 — как фон лендинга

Цель (Елена, 27.09): картинки должны походить на фон героя — «поле» NDVI Брюсселя, лето 2024, размазанное
по горизонтали (направление лет) и дрожащее, как листва; справа — розово-сиреневое свечение. Референс —
`refs/ref-hero-field.png` (снят с прода без карточки, 3:2).

Замер: CIE Lab, 6 кластеров; A и D — по скриншоту сайта Higgsfield, приблизительно.

| | фон героя | A, раунд 1 | D, раунд 1 |
|---|---|---|---|
| средняя светлота | **L 73** | ~57 | ~65 |
| самое тёмное | `#59A54D`, L 62 | `#314B86`, L 33 | `#41614C`, L 38 |
| зелень | `#59A54D` 31 %, `#95C96A` 20 %, мята `#BDDDA3` 15 %, бирюзово-зелёный `#6FB192` 13 % | горчица `#A6A448`, олива `#586A29` | травяная `#578643` |
| светлое | `#DAE1D0` 11 % | `#D5BD8B` | `#CAD2B8` 23 % |
| сирень | `#DCBBF1` 9 %, одно пятно | нет, тёмно-синий | серо-лиловая `#A4969F` |

Вывод: у фона нет теней вовсе — «deep bottle green» из раунда 1 для этой цели не годится; смаз горизонтальный,
а не диагональный; сирень — одно большое светлое пятно, а не россыпь соцветий. Halation Vintage уводит в
тепло и дымку — брать другой объектив или без него. **Enhance Prompt выключить.** 3:2, 2k.

**F1. Проводка вдоль листвы** (без референса)
```
Intentional camera movement photograph: the camera pans sideways during a one-second exposure across a sunlit wall of fresh summer leaves, so the whole frame turns into soft horizontal streaks with a gentle wavy ripple, like leaves shivering in the wind. Bright and airy, overexposed by a stop: fresh leaf green, light lime and pale mint, a few cooler teal-green bands, and washes of almost-white light where the sun breaks through. Even the darkest areas are a mid leaf green. Right of centre floats one large soft round glow of pink-lilac light, pink at its core and lavender at its rim, an out-of-focus lilac blossom pressed against the lens. Fuji Pro 400H, soft, clean, pastel. One continuous photograph that fills the frame edge to edge.
```

**F2. По референсу** — Soul Cinema, в Reference — `refs/ref-hero-field.png`
```
A real photograph with the same colours, lightness and horizontal motion as the reference: fresh summer foliage in bright sun, blurred into soft horizontal streaks by a sideways camera pan during a long exposure, with a gentle ripple like leaves in the wind. Light greens, pale mint and a few teal-green bands, washes of near-white sunlight, and one large soft pink-lilac glow right of centre from a lilac blossom right against the lens. Soft film grain, clean pastel colour. One continuous photograph that fills the frame edge to edge.
```

**F3. Фото из фона** — Nano Banana Pro или Seedream 4.5, тот же референс как исходник
```
Turn this image into a real photograph while keeping its composition, colours and lightness exactly: it becomes fresh summer foliage in bright sun, photographed with a sideways camera pan during a long exposure, so the leaves turn into soft horizontal streaks. The pink-lilac spot stays where it is and becomes an out-of-focus lilac blossom glowing right in front of the lens. Add fine film grain and the small irregularities of real leaves and light.
```

**G1. Луг с проводкой** — референс Елены: Figma `256:3916` (луг с космеей, ICM, плёнка); «такое, но цветов
сирени поменьше и побольше зелени». Soul Cinema, 3:2. **Мимо:** вышел ровный зелёный луг, цветы
пропали (сирени 0 %). И главное — у нас не луг: сюжет — городская крона.
```
Intentional camera movement photograph of a summer meadow at the edge of a city park: the camera sweeps sideways during a half-second exposure, so the tall grass and leaves smear into soft horizontal streaks. The frame is almost all green: fresh leaf green, light lime, pale mint and a few cool teal-green shadows. Only a handful of small lilac and lavender flowers are scattered through the grass, smeared into soft pastel dashes, most of them towards the right side. Soft daylight, gentle haze, muted pastel film colour, fine visible grain, Kodak Portra 400. One continuous photograph that fills the frame edge to edge.
```

**H1. Крона и сирень, проводка дугой** — приём с референсов (ICM, крупный смазанный цвет у объектива,
зерно), сюжет — городское дерево. Soul Cinema, 3:2.
```
Intentional camera movement photograph taken close up inside the crown of a linden street tree, with a flowering lilac bush growing beside it: the camera swings sideways in a quick arc during a half-second exposure, so the leaves smear into dense curved streaks of deep green, fresh leaf green and bright lime where the sun comes through. Two or three lilac flower clusters close to the lens become large soft blobs of lavender and pale violet, dragged along the same arc; all the rest of the frame is foliage. Soft daylight, gentle haze, rich but soft film colour, fine visible grain, 35mm film. Dense and close, one continuous photograph filling the frame edge to edge.
```

Итог H1: «arc» → закрутка по кругу (spin), кадры темнее фона; ближе всего H1-3 (диагональ, крупные пятна).
Елена: «у нас должен быть куст сирени».

**J1. Куст сирени, проводка вбок** — Soul Cinema, 3:2.
```
Intentional camera movement photograph of a large flowering common lilac bush (Syringa vulgaris) in a city park, photographed from close up: the camera pans straight sideways during a half-second exposure, so the bush's heart-shaped leaves smear into soft horizontal streaks of fresh leaf green, light lime and a little teal-green in the shade. A few lilac flower clusters near the lens become soft elongated blobs of lavender and pale violet, dragged along the same horizontal motion; leaves fill most of the frame. Bright soft daylight, airy and light, gentle haze, soft film colour, fine visible grain, 35mm film. One continuous photograph filling the frame edge to edge.
```

Итог J1: куст есть, ближе всего J1-2 (горизонталь 2,51, ΔE 10,8); все темнее фона (L 58–65).

**K1. Куст сирени по рефу Unfold Academy** — Figma `257:3927`, копия `refs/ref-unfold-academy.png` (в модель не
подавать: на нём надпись). Один быстрый смаз по пологой диагонали вверх, крупные формы без деталей, клин бледного
неба, глубокая тень, зерно; замер рефа — L 40, темнее нашего фона. Soul Cinema, 3:2.
```
Cinematic intentional camera movement photograph of a tall flowering lilac bush at the edge of a city park against a pale blue-grey sky: the camera sweeps fast along a shallow rising diagonal during the exposure, so the whole bush melts into long soft streaks with almost no detail. A wedge of pale sky fills the upper left; the rest of the frame is the bush: deep green shadow, fresh leaf green and lime where the light catches the leaves, with scattered lilac clusters smeared into soft lavender and violet strokes. Large calm shapes, soft focus, muted cinematic colour, fine film grain, 35mm film. One continuous photograph filling the frame edge to edge.
```

Итог K1: строй и светлота как у рефа (L 36–39 против 40), но серо (насыщенность 10–21 против 29) — виноваты «muted» и «pale».

**K2–K5. Вариации** (27.09, Soul Cinema по 2 кадра; K2 ещё на Soul 2.0 со стилями Nature light и Warm vivid film). Лист — `round2/sheet-K2-K5.jpg`.

K2 — как K1, сочная зелень:
```
Cinematic intentional camera movement photograph of a tall flowering lilac bush at the edge of a city park against a pale blue-grey sky: the camera sweeps fast along a shallow rising diagonal during the exposure, so the whole bush melts into long soft streaks with almost no detail. A wedge of pale sky fills the upper left; the rest of the frame is the bush in rich, saturated greens: deep bottle-green shadow, juicy fresh leaf green and glowing lime where the light catches the leaves, with scattered lilac clusters smeared into clear lavender and violet strokes. Large calm shapes, soft focus, rich cinematic colour. Fine film grain, 35mm film. One continuous photograph filling the frame edge to edge.
```

K3 — проводка горизонтальная, как фон:
```
Cinematic intentional camera movement photograph of a tall flowering lilac bush in a city park: the camera pans fast and perfectly level from left to right during the exposure, so the bush melts into long soft horizontal streaks with almost no detail. A thin band of pale blue-grey sky runs along the top edge; below it the bush in rich greens: deep green shadow, fresh leaf green and bright lime where the light catches, with scattered lilac clusters stretched into soft horizontal lavender and violet strokes. Large calm shapes, soft focus, rich cinematic colour. Fine film grain, 35mm film. One continuous photograph filling the frame edge to edge.
```

K4 — без неба, куст на весь кадр:
```
Cinematic intentional camera movement photograph taken right up against a flowering lilac bush in a city park, the bush filling the whole frame: the camera sweeps fast along a shallow rising diagonal during the exposure, so leaves and flowers melt into long soft streaks with almost no detail. Rich greens dominate: deep green shadow, fresh leaf green, glowing lime highlights; a few lilac clusters close to the lens smear into large soft lavender and violet strokes. Large calm shapes, soft focus, rich cinematic colour. Fine film grain, 35mm film. One continuous photograph filling the frame edge to edge.
```

K5 — контровое вечернее солнце:
```
Cinematic intentional camera movement photograph of a tall flowering lilac bush in a city park at golden hour, backlit by a low sun: the camera sweeps fast along a shallow rising diagonal during the exposure, so the bush melts into long soft streaks with almost no detail. Sunlight glows through the leaves in acid lime and warm yellow-green, the shade inside the bush is deep green with a hint of teal, a soft pale sky glows in the upper left, and scattered lilac clusters smear into luminous lavender and violet strokes. Large calm shapes, soft focus, rich cinematic colour. Fine film grain, 35mm film. One continuous photograph filling the frame edge to edge.
```

Итог: ближе всего к рефу **K2-cinema-2** (диагональ, клин неба, L 43, насыщенность 34); под текст — **K4-cinema-1/2**
(куст на весь кадр); **K3-cinema-1** — горизонталь как у фона; **K5-cinema-1** — живой контровой свет. Плёночная рамка
по углам у K3-2 и K5-2 — брак. **Soul 2.0 со стилями проводку не делает**: вышли резкие статичные кусты (у Warm vivid
film — ещё и дома). HEX-цвет в CLI не принимается (ни `color`, ни `hex`) — только на сайте.

## Выбрано — `gpt/` (27.09)

Елена: «и так збс». Четыре кадра Higgsfield, модель **GPT Image 2.5 Sunburst**, качество High, 3840×2160 (16:9), в `docs/design/imagery/gpt/` — куст
сирени с горизонтальной проводкой. Замер против фона героя: L 64–68 (фон 74), насыщенность 43–44 (41), смаз
горизонтальный 2,2–2,6 (2,70), сирень 11–15 % кадра (8 %) цвета `#C59AE6`–`#CEA3E9`, ΔE 13–15 — ближе всего из всех
прогонов. Промпт — J1 (выше, без изменений). Лучший по композиции — `…52c0ffbd` (зелень слева, сирень справа, как свечение на фоне).

## Вариации для сайта (из выбранных `gpt/`)

GPT Image 2.5, вариант Sunburst, качество High, 4K; референсы — все четыре кадра из `gpt/`. Через CLI —
4,25 кредита за кадр (`gpt_image_2_5 --variant sunburst --quality high --resolution 4k`); на сайте — Unlimited.
Начало у всех общее, меняется только последнее предложение — компоновка под место на странице.

**V1. Полоса с цифрами** — 21:9; секция «The city rustles every summer»: свет на полосе стоит слева, за первой цифрой (landing.css `.rustle-band`).
```
Same scene, light and style as the reference images: a large flowering common lilac bush in a city park, photographed from close up while the camera pans straight sideways during a half-second exposure, so the heart-shaped leaves smear into soft horizontal streaks of fresh leaf green, light lime and a little teal-green in the shade, and lilac clusters become soft elongated blobs of lavender and pale violet. Bright soft daylight, airy and light, gentle haze, soft film colour, fine visible grain, 35mm film. Wide panoramic frame. The lilac clusters gather in the left third of the frame; the middle and the right two thirds are only leaves, evenly smeared, calm and bright.
```

**V2. Телефон** — 9:16; герой на телефоне: карточка закрывает середину, свечение уходит наверх (`@media (max-width: 720px)`).
```
Same scene, light and style as the reference images: a large flowering common lilac bush in a city park, photographed from close up while the camera pans straight sideways during a half-second exposure, so the heart-shaped leaves smear into soft horizontal streaks of fresh leaf green, light lime and a little teal-green in the shade, and lilac clusters become soft elongated blobs of lavender and pale violet. Bright soft daylight, airy and light, gentle haze, soft film colour, fine visible grain, 35mm film. Tall vertical frame. The lilac clusters sit in the upper third; the middle and lower two thirds are leaves only, smooth and even, with no strong detail.
```

**V3. Тихий фон** — 16:9; под плитками и текстом, где сирень отвлекает.
```
Same scene, light and style as the reference images: a large flowering common lilac bush in a city park, photographed from close up while the camera pans straight sideways during a half-second exposure, so the heart-shaped leaves smear into soft horizontal streaks of fresh leaf green, light lime and a little teal-green in the shade, and lilac clusters become soft elongated blobs of lavender and pale violet. Bright soft daylight, airy and light, gentle haze, soft film colour, fine visible grain, 35mm film. Almost the whole frame is leaves; only two or three small lilac blobs near the right edge. Very even, light and calm, large soft shapes.
```

**V4. Обложка и og** — 16:9 (потом обрезать до 1200×630); обложка кейса и превью ссылки: слева спокойное место под заголовок.
```
Same scene, light and style as the reference images: a large flowering common lilac bush in a city park, photographed from close up while the camera pans straight sideways during a half-second exposure, so the heart-shaped leaves smear into soft horizontal streaks of fresh leaf green, light lime and a little teal-green in the shade, and lilac clusters become soft elongated blobs of lavender and pale violet. Bright soft daylight, airy and light, gentle haze, soft film colour, fine visible grain, 35mm film. The left half is calm, bright, evenly smeared leaves; the lilac clusters gather in the right half, a little larger and closer to the lens than elsewhere.
```

Итог (27.09, CLI, 4 × 4,25 кр.): `gpt/site/V1–V4.png`. Компоновка у всех по заданию. Светлота L 71–73 — почти как
у фона (74), светлее исходных `gpt/`. Насыщенность выше фона: 51–54, у V3 — 62 (кислотный лайм, против 41). Сирень:
V1 16 %, V2 15 %, V3 3 %, V4 21 % кадра.

В Figma (27.09, страница Hi-fi `220:11`): герой 1440 — `gpt/…52c0ffbd`, полоса с цифрами 1440 — V1, герой 390 — V2;
на слоях картинки зерно — эффект Noise (monotone, чёрный 14 %, размер 1,2, плотность 0,6). Исходники — секция
«Imagery · lilac bush» (`266:3742`) под экранами атласа. V3 и V4 пока без места.

## Кольцо (факт) — черновик

Большой формат 4×5, задник параллелен срезу: кольца считаются, перспектива не искажена. 1:1 или 3:2.
```
Top-down photograph of a freshly cut cross-section of a tree trunk, about 60 cm across, lying on bright spring moss. The growth rings are sharp and countable, one per year, a few narrow rings of dry summers, a fine radial crack, pale fresh sapwood around a darker heartwood core. Fallen lilac florets, small lavender and violet stars, are scattered across the moss around it. Late afternoon sun low from the left rakes across the cut and lifts the relief of the rings; the moss glows acid lime where the light hits it and falls to deep bottle green in the shade. 4x5 large-format view camera, 150mm lens, camera back parallel to the cut so there is no perspective distortion, f/22, Kodak Ektar 100, fine grain.
```

## Бирка (документ) — черновик

Планшетный сканер (сканография): резко только то, что касается стекла. Гербарий = документ.
```
Flatbed-scanner image (scanography) of a herbarium specimen: a pressed sprig of common lilac (Syringa vulgaris) with two leaves and a small cluster of lilac-violet flowers, and a small cream paper tag tied to its stem with fine string. Everything touching the scanner glass is razor sharp; the parts that rise off the glass fall into soft shadow within a centimetre. Flat frontal scanner light, deep bottle-green leaves with lime veins, warm cream paper background filling the frame edge to edge. The tag carries a short handwritten number in pencil and nothing else.
```

## Прогон

- Модель: Seedream (Higgsfield `seedream_v4_5`, `--quality high`) или Nano Banana Pro (`nano_banana_2`; есть и в
  Figma Weave, ~11 кредитов за кадр, до 14 референсов). По 2 штуки на вариант + те же с референсом.
- 27.09 Елена прогнала A–D, «кольцо» и «бирку» на сайте Higgsfield.
- Higgsfield CLI 1.1.26 залогинен 27.09, выбрано пространство Private (`hf workspace set`, иначе «No workspace
  selected»), тариф creator. CLI списывает кредиты, Unlimited работает только на сайте. Скрипты бота из
  `~/git projects/higgsfield-bot/` пропали (остались промпты и старая выдача).
- Результаты — в Figma рядом с секциями, сравнение бок о бок.
