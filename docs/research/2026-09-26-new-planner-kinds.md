# Facta · City Planner: какие новые типы объектов и линзы добавить

Ресёрч от 26.09.2026. Репозиторий `/home/user/facta` только читался: ничего не изменено и не закоммичено.

**Коротко.** Проверено 28 кандидатов в типы (часть A) и 10 идей линз (часть B). Сильнейшие типы:

- **велобоксы:** у Брюсселя есть официальный набор и правило распределения 200 м;
- **районные площадки для подростков:** у Антверпена есть собственный слой дефицита, с которым можно сверить результат;
- **дефибриллятор, доступный ночью:** 97 % дефибрилляторов в Бельгии размечены признаком `indoor`;
- **прохладные места:** самая сильная история для кейса, но в OSM для них нет тега, и спрос у них другой.

Сильнейшие линзы (часть B) не требуют новых данных:

- нормы радиуса по типам и сверка с Антверпеном;
- устойчивость рекомендации к смене источника;
- «кому не хватает» по каждому типу.

---

## 0. Что нужно одному типу объектов (по коду движка)

| Что | Где в коде | Что это значит для нового типа |
|---|---|---|
| Теги существующих объектов | `ASSETS[kind]["osm_tags"]` → `ox.features_from_polygon(poly, tags=…)` в `adapters/base.py::_osm_assets` | Словарь тегов — это **ИЛИ**, а не И. Фильтра «pitch **и** sport=basketball» и исключений вроде `access=private` нет. Атрибуты отбрасываются: `accessible` всегда `None`. Для доступных туалетов, дефибрилляторов 24/7 и площадок по виду спорта нужен **постфильтр**. |
| Точки спроса | `ASSETS[kind]["demand_pois"]` → `compute_demand_score` | Считается **количество** POI из OSM в радиусе × 1,6. Веса вида «число жителей 65+» нет. Типы, где спрос — это жители (велобоксы, прохладные места), требуют режима спроса от жителей. |
| Радиус покрытия | `CITIES[city]["walk_radius_m"] = 500` и `--radius 500` в `run.py` | **Радиус одинаков для всех типов.** Нормы 150, 200 или 400 м сейчас не задать без правки. `candidate_min_dist_m = 300` больше радиуса 150 м. |
| Справедливость | `compute_equity_index(grid, ["deprivation_score", "demand_weight"])` | Только составной BIMD 2011. Файл BIMD содержит и **домены**: `income`, `employment`, `edu`, `hous`, `crime`, `health` (проверено по заголовку CSV). Возраст (`population_age.csv`), доход и жара есть в пакете Facta, но в движок не заходят. |
| Источник объектов | Адаптеры | Все 5 городов берут OSM. Исключение — туалеты Антверпена (`opendata.antwerpen.be`). Официальные наборы требуют адаптер, лучше один общий (Opendatasoft/ArcGIS + сопоставление полей в конфиге). |
| Ноль объектов | `compute_network_gap_score` → `ValueError` → евклидов запасной путь, GapScore = 1 везде | Если OSM не знает ни одного объекта, «покрытие 0 %» означает **«нет данных»**, а не «нет услуги». Для Шарлеруа это реальная угроза (см. §3). |

Прецедент из `CLAUDE.md` (04.09): дерево **намеренно не добавлено** в планировщик, потому что «спрос считается от точек притяжения, а деревья сажают там, где жарко… подменять её было бы враньём». Для прохладных мест действует то же правило: их нельзя добавлять с POI-спросом. Нужен спрос «жара × уязвимые жители».

## 1. Как проверялось

- **Покрытие OSM по Бельгии:** taginfo Geofabrik, `taginfo.geofabrik.de/europe:belgium/api/4/tag/stats`, данные на 25.09.2026 20:17 UTC. Один запрос на тег, пауза 1,5 с, 73 тега. Для долей атрибутов (wheelchair, fee, backrest, indoor, opening_hours) — `tag/combinations`. Мировой taginfo использован только для проверки, существует ли тег вообще.
- **Покрытие OSM по городам:** один Overpass-запрос `out count` на город.
  - `overpass-api.de` сбросил соединение (Connection reset by peer).
  - Зеркало VK Maps (`maps.mail.ru/osm/tools/overpass`) ответило для Брюсселя (регион, rel. 54094), Гента, Льежа и Шарлеруа.
  - По Антверпену лёгкие теги получены, тяжёлые (деревья, переходы, фонари, бордюры) — нет, 504 Gateway Timeout дважды.
- **Официальные наборы:** каждый каталог выгружен целиком одним запросом и прочитан локально:
  - data.stad.gent — 308 наборов;
  - opendata.brussels.be — 208;
  - opendata.liege.be — 101;
  - ODWB (Валлония, включая Шарлеруа) — 1281;
  - ArcGIS Hub Антверпена — 483.
  По ключевым наборам сняты фасеты (типы, статусы).
- Нормы радиуса и контекст взяты из открытых источников (ссылки в конце).

Сокращения городов: **BXL** — Брюссельский столичный регион, **ANT** — Антверпен, **GNT** — Гент, **LGE** — Льеж, **CRL** — Шарлеруа.

## 2. Нормы радиуса, на которые можно ссылаться

| Норма | Значение | Источник |
|---|---|---|
| Антверпен, «ruimteboekhouding» (бухгалтерия пространства) | Квартал (bouwblok) 150 м / 2 мин; соседство (buurt) 400 м / 5 мин; район (wijk) 800 м / 10 мин; часть города (stadsdeel) 1600 м / 20 мин. Сетевое расстояние с барьерами (вода, кольцо, железная дорога) и безопасными переходами. | Описания слоёв `bereik_*` на портале Антверпена (проверено) |
| Прохладное место (koelteplek), Антверпен | 150 м: зелень, площадь или природа без теплового стресса по карте жары; слой обновляется раз в 5 лет | `bereik_koelteplek_bouwblok`, `tekortzone_koelteplek_bouwblok` |
| Детская площадка, Антверпен | 150 м для малых (< 500 м², ≤ 5 снарядов), 400 м для остальных | `bereik_speelterrein_bouwblokbuurt` |
| Районная спортплощадка, Антверпен | 400 м | `bereik_buurtsportterrein_buurt` |
| Выгул собак, Антверпен | 800 м (планировщик сейчас берёт 500) | `bereik_hondenloopzone_wijk` |
| Общий огород / участок, Антверпен | 800 м / 1600 м | `bereik_samentuin_volkstuin_wijk_stadsdeel` |
| Fields in Trust (Великобритания) | Площадки для игр: LAP 100 м, LEAP 400 м, NEAP 1000 м (NEAP включает MUGA, скейт, баскетбол) | Fields in Trust, Guidance for Outdoor Sport and Play (2015) |
| Велобокс, Брюссель (Cycloparking) | Место ищется в радиусе 200 м от дома, затем 350 м, затем 500 м | FAQ parking.brussels (проверено) |
| Климатические убежища, Барселона | Цель к 2030 году — у каждого жителя убежище в 5 минутах ходьбы; сейчас 99,2 % жителей в пределах 10 минут | barcelona.cat |
| Скамейки (Inclusive Mobility, DfT) | В людных пешеходных зонах, на пересадках и станциях — сиденья не реже чем через 50 м | GOV.UK, Inclusive Mobility |
| Станции проката велосипедов (ITDP) | Шаг станций около 300 м (Vélib' около 10 станций на км²) | ITDP Bike-Share Planning Guide |
| Зарядки электромобилей, Брюссель | Решение для зарядки в пределах 250 м от дома, новый тендер — 150 м; план — 22 000 публичных точек к 2035 году | electrify.brussels, Sibelga |

## 3. Часть A — кандидаты в типы объектов

Число в колонке OSM: Бельгия всего, затем по городам (BXL · ANT · GNT · LGE · CRL).

Трудоёмкость:
- **S** — запись в конфиг плюс, может быть, постфильтр;
- **M** — постфильтр, свой радиус или официальный адаптер хотя бы для одного города;
- **L** — новый режим спроса или своя сборка набора из нескольких источников.

| # | Тип | OSM-тег(и) | OSM: BE / BXL·ANT·GNT·LGE·CRL | Официальный открытый набор | Спрос (точки или жители) | Радиус и основание | Трудо­ёмкость | Вердикт |
|---|---|---|---|---|---|---|---|---|
| 1 | **Прохладное место** (koelteplek, afkoelplek, îlot de fraîcheur, climate shelter) | Тега нет: `amenity=cooling_centre` 0, `social_facility=cooling_centre` 0; поиск по «cool/koel/fraich» по Бельгии пуст. Прокси — открытые прохладные здания (`amenity=library`, `community_centre`, `place_of_worship`, `townhall`, `museum`) плюс парки и затенённые площади | 0 (прокси из имеющихся тегов) | ANT: официальные слои [bereik_koelteplek_bouwblok](https://geodata.antwerpen.be/arcgissql/rest/services/P_Portal/portal_publiek12/MapServer/46) и [tekortzone_koelteplek_bouwblok](https://geodata.antwerpen.be/arcgissql/rest/services/P_Portal/portal_publiek12/MapServer/77) — готовый ответ для сверки. LGE: [ilots-de-fraicheur](https://opendata.liege.be/explore/dataset/ilots-de-fraicheur/), 33 места (19 парков и терриконов, 10 обсаженных набережных, 2 леса, 2 кладбища). BXL (только Ville de Bruxelles): [карта îlots de fraîcheur](https://www.bruxelles.be/carte-ilots-fraicheur) собрана из открытых наборов плюс [espaces publics de séjour](https://opendata.brussels.be/explore/dataset/espaces-publics-de-sejour-vbx/), 148 мест с тенью и скамейками. **Регионального перечня нет** (La Libre, 25.06.2026); региональный план на жару готовится (L'Avenir, 13.07.2026). GNT: интерактивная [карта afkoelplekken](https://stad.gent/nl/samenleven-welzijn-gezondheid/nieuws-evenementen/drinkwater-en-afkoelplekken-gent), открытость данных [не проверено]; [drinkwaterplekken-gent](https://data.stad.gent/explore/dataset/drinkwaterplekken-gent/) — 50 открытых зданий. CRL: нет | **Жители**, не POI: сектор × превышение LST (`heat_2022_2025`) × доля 65+ и 0–14 | 150 м (Антверпен, на улице); 5 мин ≈ 400 м (цель Барселоны) | L | **Да, флагман**, но как отдельная модель спроса (прецедент с деревом). Сверка с `tekortzone_koelteplek` Антверпена — known-answer тест |
| 2 | Водная игровая площадка / фонтан-брызгалка (splash pad) | `fountain=splash_pad`, `playground=splash_pad` | 255 + 19 / 178 · 11+6 · 2 · 3+1 · 0 | Нет. Карта Гента показывает «waterprikkels», открытость [не проверено] | Детские площадки, парки, школы; дети 0–14 в жарких секторах | 1000 м (NEAP, Fields in Trust) | M | Условно. **Риск:** 174 узла в BXL — все безымянные `amenity=fountain`, 16 с `level`. Похоже, размечены отдельные форсунки одной установки; кластеризация не выполнена, зеркало отвечало 504 [не проверено] |
| 3 | Навес от солнца | `shelter_type=sun_shelter` | 11 / 0 во всех пяти | Нет | — | — | — | **Нет.** Тень лучше мерить кроной, слой в Facta уже есть |
| 4 | Уличное дерево / приствольная лунка | `natural=tree` (`denotation=avenue` 4760) | 393 478 / 64 674 · — · 14 510 · 11 480 · 2 261 | GNT: [locaties-bomen-gent](https://data.stad.gent/explore/dataset/locaties-bomen-gent/), 68 240 (с годом посадки). BXL, Ville: [arbres-bomen-vbx-be-bm](https://opendata.brussels.be/explore/dataset/arbres-bomen-vbx-be-bm/), 31 674. LGE: [arbustum](https://opendata.liege.be/explore/dataset/arbustum/), 28 475 (2018). ANT: слой `boom` | — | — | — | **Нет** (решение 04.09: другая модель спроса). Остаётся в линии выполнения |
| 5 | **Доступный туалет** (для колясочников) | `amenity=toilets` + `wheelchair=yes` (или `toilets:wheelchair=yes`) | 674 из 2389 (28 % да, 15 % нет, 53 % без тега) / 51 из 188 · 30 из 93 · 26 из 144 · 14 из 52 · 5 из 12 | BXL, Ville: [toilettes-urinoirs-publics](https://opendata.brussels.be/explore/dataset/toilettes-urinoirs-publics-openbare-toiletten-urinoirs-vbx/), 156 (PMR 61, платных 22, 94 — сеть «Toilettes accueillantes» в магазинах и кафе). GNT: [publiek-sanitair-gent](https://data.stad.gent/explore/dataset/publiek-sanitair-gent/), 272, и [Toegankelijke plaatsen](https://data.stad.gent/explore/dataset/main-toegankelijkheid-widget/), 138 туалетов. LGE: [toilettes-pmr](https://opendata.liege.be/explore/dataset/toilettes-pmr/), 22 (2025). ANT: [openbaar_toilet](https://geodata.antwerpen.be/arcgissql/rest/services/P_Portal/portal_publiek1/MapServer/8) | Как у туалетов плюс больницы, аптеки, станции; 65+ и 80+ | 500 м, как туалеты | S | **Да.** Покрытие давать **диапазоном**: нижняя граница — только `yes`, верхняя — `yes` плюс неизвестные |
| 6 | Changing Places (туалет с подъёмником и столом для взрослых) | `changing_places=yes` | 0 (в мире 1) / 0 везде | Фландрия продвигает (Inter), открытого списка не найдено [не проверено] | — | Масштаб города, не пешей доступности | — | **Нет.** Объектов единицы; это задача «одна точка на город», а не пешее покрытие |
| 7 | Пеленальный столик | `changing_table=yes` | 519 / 29 · 24 · 50 · 6 · 5 (на туалетах BXL только 11) | Нет | Ясли, детсады, площадки, рынки; дети 0–14 (полосы 0–4 в слое нет) | 500 м | S | Условно. Мало данных, в основном в магазинах (`access=customers`). Лучше как атрибут туалета |
| 8 | Публичный душ | `amenity=shower` | 165 / 5 · 5 · 10 · 0 · 0 | [не проверено] (социальные: DoucheFLUX и др.) | Приюты, социальные службы | — | — | **Нет.** Мало объектов, это социальная услуга |
| 9 | Раздатчик менструальных средств | `vending=feminine_hygiene` / `vending=menstrual_products`, `toilets:menstrual_products=yes` | 0 / 0 (в мире 208 / 1 / 544) | Валлония раздаёт через школы и CPAS, адресов нет [не проверено] | — | — | — | **Нет данных** |
| 10 | Зарядка телефона или электровелосипеда | `amenity=device_charging_station` | 11 / 3 · 1 · 0 · 0 · 0 | Нет | — | — | — | **Нет** |
| 11 | Постамат (парсел-локер) | `amenity=parcel_locker` | 649 / 35 · 21 · 53 · 8 · 1 | Все почтовые точки публикует регулятор BIPT: [bipt-data.be](https://www.bipt-data.be/fr/opendata) (национальный охват [не проверено]). Выгрузка по Ville: [points-postaux0](https://opendata.brussels.be/explore/dataset/points-postaux0/), 16 постаматов. LGE: [armoires-colis](https://opendata.liege.be/explore/dataset/armoires-colis/), 9 городских «нейтральных» шкафов | Жители, станции | 500 м | M | Нет: коммерческая логистика, не общественное пространство |
| 12 | Почтовый ящик (красный bpost) | `amenity=post_box` | 4791 / 406 · 102 · 119 · 65 · 11 | BIPT (как выше); Ville: 103 ящика. Сеть bpost — около 13 000 ящиков; 20 % собирают меньше 6 писем в день, наименее загруженные убирают (уведомление коммуне Frasnes-lez-Anvaing) → OSM ≈ 37 % | Жители 65+ | 500 м [основания нет] | M | Условно. Интересно как измерение **изменения** (снимки BIPT во времени → кто теряет ящик), если BIPT хранит историю [не проверено] |
| 13 | Зарядка электромобиля | `amenity=charging_station` | 5857 / 704 · 197 · 547 · 11 · 10 | BXL, регион: [bornes-de-recharge-rbc](https://opendata.brussels.be/explore/dataset/bornes-de-recharge-pour-voitures-electriques-rbc/), 3516, CC BY 4.0. GNT: [laadpalen-gent](https://data.stad.gent/explore/dataset/laadpalen-gent/), 1112. ANT: `oplaadplaatsen`. Валлония: ORES, только счёт по коммунам | Дома без гаража (в открытых данных нет) | 250 → 150 м (electrify.brussels) | S | Как тип — нет: служит владельцам машин. **Как проверка обещания — да** (часть B7) |
| 14 | Станция проката велосипедов | `amenity=bicycle_rental` | 1124 / 365 · 324 · 19 · 1 · 1 | BXL: [stations-villo](https://opendata.brussels.be/explore/dataset/stations-villo-bruxelles-rbc/), 345. ANT: слой `velo`. GNT: [Donkey Republic](https://data.stad.gent/explore/dataset/donkey-republic-deelfietsen-stations-locaties/), 613 записей, и Bolt. LGE и CRL: практически нет | Станции ОТ, вузы, магазины | около 300 м (ITDP) | M | Нет: решение оператора; станционные системы есть только в BXL и ANT |
| 15 | Каршеринг (Cambio) | `amenity=car_sharing` | 574 / 186 · 14 · 109 · 10 · 2 | GNT: [autodeelplaatsen](https://data.stad.gent/explore/dataset/autodeelplaatsen-gent/), 867. [Cambio на ODWB](https://www.odwb.be/explore/dataset/cambio/), 1367 записей. BXL, Ville: Cambio 45 | — | — | M | **Нет** |
| 16 | **Велобокс / защищённая соседская велостоянка** (fietsbox, fietstrommel, vélobox) | `amenity=bicycle_parking` + `bicycle_parking=shed` / `lockers` / `building` | shed 1760, lockers 238, building 266 / BXL 1177 + 5 + 15 (из них 1042 с `operator=parking.brussels`, `charge=15 EUR/year`) · ANT 19 + 26 + 35 · GNT 55 + 18 + 10 · LGE 10 + 2 + 6 · CRL 0 | BXL, регион: [Cycloparking](https://opendata.brussels.be/explore/dataset/places-de-parking-boxes-securises-velos-et-velos-cargo-geres-par-cycloparking/), CC BY 4.0, 911 записей: 865 боксов, 26 соседских стоянок, 900 в работе; все коммуны (Иксель 173, Схарбек 159, Моленбек 149…). GNT: [fietsenstallingen-gent](https://data.stad.gent/explore/dataset/fietsenstallingen-gent/), `karakter` = Fietstrommel 19, Buurtfietsenstalling 18. ANT: [buurtfietsenstallingen](https://geodata.antwerpen.be/arcgissql/rest/services/P_Portal/portal_publiek4/MapServer/289). LGE: [velocite-box-velos](https://opendata.liege.be/explore/dataset/velocite-box-velos/), 74 (2020) | **Жители** плотной застройки. Прокси: плотность населения сектора и BIMD-домен `hous` | **200 → 350 → 500 м** (правило Cycloparking) | M | **Да.** Лучшие данные из всех новых типов. Боксы ставят постоянно, поэтому линия выполнения может проверить названные точки. Расхождение 865 против 1042 в OSM объяснить [не проверено] |
| 17 | Понижение бордюра / тактильная плитка | `kerb=lowered` / `flush`, `tactile_paving=yes` | 22 530 / 33 268; BXL 14 843 / 21 806 · ANT — · GNT 625 / 1069 · LGE 935 / 1685 · CRL 39 / 144 | Нет | — | — | — | **Нет как тип:** это элементы сети, и разница в 24 раза между BXL и GNT — артефакт разметки. Годится только для аудита доступности Брюсселя |
| 18 | Пешеходный переход | `highway=crossing`, `crossing:markings=zebra` | 120 062 / 22 726 · — · 4 652 · 2 507 · 2 419 | GNT: [schoolstraten](https://data.stad.gent/explore/dataset/schoolstraten-gent/), [schooltoegangen](https://data.stad.gent/explore/dataset/schooltoegangen-gent/) (270). BXL, Ville: [plans de déplacements scolaires](https://opendata.brussels.be/explore/dataset/plans-de-deplacements-scolaires-vbx/) (112). ANT: `schoolstraten` | — | — | L | **Нет как тип** (дорожная инженерия). См. B10 |
| 19 | Уличный фонарь | `highway=street_lamp` | 108 369 / 9 863 · — · 1 879 · 2 696 · 187 | Валлония: ORES, только число светильников по коммунам | — | — | — | **Нет:** разметка неполная, в CRL 187 фонарей |
| 20 | Бесплатный Wi-Fi | `internet_access=wlan` + `internet_access:fee=no` | 903 (fee=no) / 74 · 20 · 43 · 11 · 3 | BXL, Ville: [wifi.brussels](https://opendata.brussels.be/explore/dataset/points-acces-wifi-gratuit-wifibrussels-vbx/), 75. ANT: [wifi_openbaar](https://geodata.antwerpen.be/arcgissql/rest/services/P_Portal/portal_publiek1/MapServer/60) | — | — | S | **Нет** (низкая ценность) |
| 21 | Общий огород / участок | `garden:type=community`; `landuse=allotments` | 167 / 1313; BXL 25 / 138 · ANT 0 / 65 · GNT 7 / 27 · LGE 2 / 13 · CRL 2 / 3 | BXL, Ville: [potagers collectifs](https://opendata.brussels.be/explore/dataset/potagers-collectifs-collectieve-moestuinen/), 30. ANT: `samentuinen`, `volkstuinen_detail` и [bereik](https://geodata.antwerpen.be/arcgissql/rest/services/P_Portal/portal_publiek12/MapServer/52) | Жители без сада (плотная застройка), BIMD `hous` | 800 м / 1600 м (Антверпен) | M | Условно. Это участок земли, а не малый объект: «поставить N огородов» звучит неправдоподобно |
| 22 | Сад для опылителей / дождевой сад / отель для насекомых | Тега для дождевого сада нет; `man_made=insect_hotel` | 277 / — | Нет | — | — | — | **Нет** |
| 23 | Депейвинг (снятие покрытия) | Тега нет | — | Нет | — | — | — | **Нет как тип.** Место ему в линии «что изменилось» (класс застроенности у Dynamic World) |
| 24 | **Районная спортплощадка / место для подростков** (баскетбол, мини-футбол, пинг-понг, скейт, street workout) | `leisure=pitch` + `sport` ∈ {basketball, soccer, multi, table_tennis, skateboard} с `access` ∉ {private, customers} (+ `leisure=fitness_station`) | basketball 1325, table_tennis 450, skateboard 431 / баскетбол 118 · 97 · 50 · 15 · 12; пинг-понг 84 · 18 · 13 · 7 · 0; скейт 14 · 13 · 13 · 3 · 0 | GNT: [infrastructuur-buurtsport](https://data.stad.gent/explore/dataset/infrastructuur-buurtsport-gent/), 291 с полем `sport`: петанк 88, мини-футбол (buurtvoetbal) 86, баскетбол 48, фитнес 19, пинг-понг 14, скейт 10, street workout 10 — **совпадает с OSM** (баскетбол 48 против 50, пинг-понг 14 против 13, скейт 10 против 13). ANT: `buurtsportterrein` плюс [bereik](https://geodata.antwerpen.be/arcgissql/rest/services/P_Portal/portal_publiek12/MapServer/24) и `tekortzone_buurtsportterrein_buurt`. BXL, Ville: [espaces sportifs publics](https://opendata.brussels.be/explore/dataset/espaces-sportifs-publics-vbx/), 124 | Школы (особенно средние), молодёжные центры (`community_centre=youth_centre`: 24 · 5 · 8 · 2 · 0), парки; дети 0–14 (подростков 12–17 отдельно в слое нет) | **400 м** (Антверпен); NEAP / MUGA 1000 м | M | **Да.** Закрывает разрыв «площадки для малышей есть, для подростков нет». Сверка с `tekortzone` Антверпена — known-answer тест. «Место для подростков» входит сюда |
| 25 | Площадка для петанка | `sport=boules` (+ `access`) | 1899 / 122 · 43 · 116 · 25 · 7 | GNT: buurtsport «Petanque» 88. BXL, Ville: [lieux de sociabilité pour seniors](https://opendata.brussels.be/explore/dataset/lieux-de-sociabilite-pour-seniors-vbx/), 65, как точки спроса | 65+, дома престарелых, центры для пожилых, парки | 400–800 м | S–M | Условно. «Площадка для 65+» — симметричная пара детской. В OSM много клубных площадок, нужен постфильтр по `access` |
| 26 | Кафе или магазин с водой для бутылки (Refill) | `drinking_water:refill=yes` | 34 / — | BXL, Ville: [Réseau gourde](https://opendata.brussels.be/explore/dataset/water-bottle-network-of-the-city-of-brussels/), 113 заведений, CC0 | — | — | S | Не отдельный тип: **дополнение к питьевой воде** (для Ville de Bruxelles) |
| 27 | Уличные часы, шкафы обмена вещами, мангалы, лежаки | `amenity=clock` / `give_box` / `bbq` / `lounger` | 206 / 82 / 339 / 236 | Нет | — | — | — | **Нет** |
| 28 | Мобильный хаб (Hoppin) | `amenity=mobility_hub` | 357 / 0 · 5 · 3 · 0 · 0 | Фландрия: [Hoppinpunten](https://transportdata.be/dataset/overzicht-hoppinpunten-in-vlaanderen) (полон только для построенных) | — | — | M | **Нет** (только Фландрия; транспортное планирование) |
| 29 | **Дефибриллятор, доступный ночью** (вариант имеющегося типа) | `emergency=defibrillator` + (`indoor=no` или `opening_hours=24/7`) и `access` ∉ {private, customers} | 5672: 97 % с `indoor`; `indoor=no` 58,5 %, `24/7` 23 %, `customers` 7,5 %, `private` 3,8 % / всего 272 · 252 · 142 · 62 · 6 | BXL, Ville: [DEA](https://opendata.brussels.be/explore/dataset/defibrillateurs-installes-par-la-ville-de-bruxelles/), 99. LGE: [défibrillateurs](https://opendata.liege.be/explore/dataset/defibrillateurs/), 97 (2018; в OSM 62). ANT: слой `AED` на Hub | Как у дефибрилляторов | Как у имеющегося типа | S | **Да.** «Покрытие днём и в 3 часа ночи» — одна правка фильтра, теги почти полные |
| 30 | Скамейка со спинкой (для пожилых) | `amenity=bench` + `backrest=yes` (подлокотник `armrest=yes` — только 2,3 %) | 40 016 из 67 180 (60 %; 72 % имеют ключ) / 5419 из 7739 · 2001 из 3175 · 1561 из 2098 · 896 из 1373 · 62 из 167 | ANT: [meubilair_in_parken](https://geodata.antwerpen.be/arcgissql/rest/services/P_Portal/portal_publiek6/MapServer/680) (только парки) | Аптеки, врачи, супермаркеты, остановки; 65+ и 80+ | 50 м на людных маршрутах (Inclusive Mobility) — см. B5 | S | **Да, как основа для B5**. Как отдельный тип менее интересен |

### Что показали сами данные (за пределами таблицы)

- **Шарлеруа по OSM почти пуст:** 12 туалетов, 6 дефибрилляторов, 167 скамеек, 2 питьевых фонтанчика на город примерно в 200 тыс. жителей. Своих открытых наборов о малых объектах у Шарлеруа на ODWB нет (только велосеть 2022 года, дорожные работы, ассоциации). Результат планировщика там измеряет пробелы разметки, а не нехватку услуг (см. B1).
- **Туалет по OSM — не всегда публичный.** В Бельгии 12 % туалетов с `access=customers`, 9,6 % с `fee=yes`. В Брюсселе 28 из 188 имеют `access` = customers, private или no. Нынешний тип `toilets` засчитывает их в покрытие.
- **Официальный набор и OSM расходятся по-разному.** Туалеты: GNT 272 официальных против 144 в OSM, в OSM меньше. Велобоксы: BXL 865 официальных против 1042 в OSM, в OSM больше. Дефибрилляторы: LGE 97 официальных (2018) против 62 в OSM. Правильный вопрос — насколько сильно источник меняет рекомендацию (B1).
- **Брюссель: 174 «splash pad»** — все безымянные `amenity=fountain`. Вероятно, отдельные форсунки [не проверено].

## 4. Часть B — линзы и функции на существующих данных

| # | Идея | Что именно | Данные (есть) | Трудо­ёмкость |
|---|---|---|---|---|
| B1 | **Устойчивость к источнику и отказ по полноте карты** | 1) Для типа, у которого в городе есть официальный набор (туалеты BXL-Ville, GNT, ANT; дефибрилляторы BXL-Ville, LGE, ANT; велобоксы BXL; спортплощадки GNT), прогнать планировщик на двух источниках и опубликовать разницу покрытия «до» и пересечение первых 10 названных точек (доля общих). 2) Правило отказа: тип не ранжируется в городе, если плотность объектов в OSM на 10 тыс. жителей ниже названного порога относительно медианы других городов. Порог калибруется по парам с официальным набором. Первый кандидат на отказ — Шарлеруа | OSM, официальные наборы из таблицы, население секторов | M |
| B2 | **«Кому не хватает» по каждому из 14 (+) типов** | Из фазы 2 для линз нужды — на планировщик: покрытие «до» по третям дохода и доли детей и 65+ в худшей трети, по типу. Сейчас на сайте только строка «сколько из N стоит в беднейшей трети» | Сетка планировщика, `population_age.csv`, доход Statbel 2023 | S–M |
| B3 | **Нормы радиуса по типам + known-answer тест по Антверпену** | `walk_radius_m` и `candidate_min_dist_m` в `ASSETS` (150 / 200 / 400 / 800 м из §2), кривая чувствительности 300 / 500 / 800 м. Покрытие жителей Антверпена сравнить с официальными `bereik_*` (площадки, выгул собак, спортплощадки, прохладные места): совпадение в % жилой площади. Та же логика, что в сверках с VITO и WVL | Слои `bereik` и `tekortzone` Антверпена (MapServer), кэш сети | M |
| B4 | **«Набор на жаркий день»** | Доля жителей (все / дети / 65+), у которых в пределах 400 м есть одновременно тень (парк ≥ 1 га или крона в секторе ≥ порога), питьевая вода, туалет и скамейка. Разрез по жаре (`hot`) и доходу. Для Ville de Bruxelles добавить Réseau gourde и espaces publics de séjour | Точки 4 типов планировщика, `heat_2022_2025`, `rule_3_30_300`, возраст | M |
| B5 | **Цепочки скамеек для пожилых** | От центроида каждого сектора (лучше от адресов) к ближайшим аптеке, врачу и супермаркету по пешеходной сети: максимальный разрыв между скамейками со спинкой вдоль пути. Показатель — доля 65+ и 80+, у которых маршрут до аптеки имеет разрыв > 100 м (и > 50 м по Inclusive Mobility). Порог 100 м — наш, помечен как таковой | Скамейки OSM (в BXL 7739, 72 % с `backrest`), POI из Fit Score и SpotFinder, кэш сети | M–L |
| B6 | **Дефибриллятор днём и ночью** | Покрытие всеми дефибрилляторами против круглосуточных (`indoor=no` или `24/7`), по трети дохода: где ночью пусто | OSM (97 % с `indoor`) | S |
| B7 | **Проверка обещаний с названным порогом** | Пример: electrify.brussels пишет, что к 2025 году у каждого жителя решение для зарядки ≤ 150 м. Проверить по региональному набору (3516 точек) сетевым расстоянием от жилых секторов. Тот же формат для правила Cycloparking 200 м (доля жителей в 200 м от бокса) | Официальные наборы BXL, кэш сети | S |
| B8 | **Бюджет между типами** | 40 объектов на город на все типы сразу: где следующий объект даёт больше покрытия для 65+ или для детей. Ответ на вопрос «что купить первым», а не «где поставить» | Кривые `coverage_steps` уже есть по 14 типам | M |
| B9 | **Изменения малых объектов во времени** | История OSM (ohsome API) или снимки официальных наборов: сколько дефибрилляторов, боксов и фонтанчиков появилось с 2024 года в названных и контрольных точках. Чтобы отличить разметку от установки, нужен официальный набор с датой (у деревьев Гента есть `aanlegjaar`, у Cycloparking поле даты [не проверено]) | Линия выполнения уже есть | M |
| B10 | **Безопасный путь в школу** | Школьные улицы, переходы с разметкой в 300 м от входов в школу | GNT и ANT schoolstraten, BXL PDS, OSM crossings (неровно) | L |

## 5. Ранжирование: ценность для кейса × доступность данных

Ценность (1–3): связь с имеющейся историей (жара, «кому не хватает», «что изменилось»); измеримость с названным порогом или внешним ответом; публичное пространство и справедливость.

Данные (1–3): покрытие OSM во всех пяти городах плюс официальный набор хотя бы в одном.

**Часть A**

| Ранг | Тип | Ценность | Данные | Итог | Слой справедливости | Главный риск |
|---|---|---|---|---|---|---|
| 1 | Дефибриллятор ночью (№ 29) | 3 | 3 | 9 | BIMD `health` + доход | Время работы у 71 % без тега; `indoor=no` как прокси доступности |
| 2 | Велобокс (№ 16) | 3 | 3 | 9 | Плотность жителей, BIMD `hous`, доход | Спрос от жителей (новый режим); 865 против 1042 |
| 3 | Районная спортплощадка / подростки (№ 24) | 3 | 3 | 9 | Дети 0–14, доход | Постфильтр по `access`; в OSM есть клубные поля |
| 4 | Прохладное место (№ 1) | 3 | 2 | 6 | Жара × 65+ и 0–14 | Тега нет; собирать из прокси; спрос не от POI |
| 5 | Доступный туалет (№ 5) | 3 | 2 | 6 | 65+ и 80+, BIMD `health` | 53 % туалетов без тега → только диапазон |
| 6 | Скамейка со спинкой (№ 30) | 2 | 3 | 6 | 65+ и 80+ | Шарлеруа почти пуст |
| 7 | Петанк (№ 25) | 2 | 2 | 4 | 65+ | Клубные площадки |
| 8 | Почтовый ящик (№ 12) | 2 | 2 | 4 | 65+ | OSM ≈ 37 %; нужен BIPT |
| 9 | Общий огород (№ 21) | 1 | 2 | 2 | BIMD `hous` | Участок, а не объект |
| 10 | Водная игровая площадка (№ 2) | 2 | 1 | 2 | Дети × жара | Брюссельская аномалия 174 |
| 11 | Пеленальный столик (№ 7) | 2 | 1 | 2 | Дети | Почти всё в магазинах |
| 12 | Прокат велосипедов, постаматы, зарядки EV, каршеринг, Wi-Fi | 1 | 2–3 | ≤ 3 | — | Не общественное пространство или решение оператора |
| — | Changing Places, души, менструальные средства, навесы, деревья, бордюры, переходы, фонари, часы, шкафы обмена, мангалы, хабы | — | — | нет | — | Нет данных, другая модель спроса или сетевой элемент |

**Часть B**

| Ранг | Идея | Ценность | Данные | Итог |
|---|---|---|---|---|
| 1 | B3 Нормы радиуса + сверка с Антверпеном | 3 | 3 | 9 |
| 2 | B1 Устойчивость к источнику + отказ по полноте | 3 | 3 | 9 |
| 3 | B2 «Кому не хватает» по типам | 3 | 3 | 9 |
| 4 | B6 Дефибриллятор днём и ночью | 3 | 3 | 9 |
| 5 | B7 Проверка обещаний (зарядки 150 м, боксы 200 м) | 2 | 3 | 6 |
| 6 | B4 Набор на жаркий день | 3 | 2 | 6 |
| 7 | B5 Цепочки скамеек для пожилых | 3 | 2 | 6 |
| 8 | B9 Изменения малых объектов во времени | 3 | 2 | 6 |
| 9 | B8 Бюджет между типами | 2 | 3 | 6 |
| 10 | B10 Путь в школу | 2 | 1 | 2 |

## 6. Рекомендация: топ-8 (порядок работы)

1. **Нормы радиуса по типам и сверка с Антверпеном (B3).** Это предпосылка для всего остального: новые типы живут на 150, 200 и 400 м, а не на 500. Сверка с официальными слоями `bereik_*` Антверпена — такой же внешний ответ, как проверки с VITO и WVL в прошлом. Размер M.
2. **Дефибриллятор ночью (A 29 = B6).** Один постфильтр, теги заполнены на 97 %. Заголовок сам просится: «днём покрыто X %, в 3 часа ночи — Y %». Размер S.
3. **Велобоксы (A 16).** У Брюсселя официальный набор под CC BY и собственное правило 200 → 350 → 500 м. Боксы ставят постоянно, поэтому через год можно проверить, появились ли они в названных точках. Нужен спрос от жителей. Размер M.
4. **Районные спортплощадки для подростков (A 24).** Норма 400 м и слой дефицита Антверпена как известный ответ. Набор Гента по видам спорта совпадает с OSM, это отдельный довод в пользу OSM. Размер M.
5. **Устойчивость к источнику и отказ по полноте карты (B1).** Формулирует принцип проекта для планировщика: результат по Шарлеруа (12 туалетов на город) нельзя показывать как нехватку, это пробел карты. Размер M.
6. **«Кому не хватает» по каждому типу (B2).** Переносит готовый блок фазы 2 на планировщик. Размер S–M.
7. **Прохладные места + «набор на жаркий день» (A 1 + B4)** как одна функция. Самая сильная история: у Брюсселя нет регионального перечня, и план на жару только готовится. Делать честно: отдельная модель спроса (жара × дети и 65+), источник по каждому городу назван, для Шарлеруа отказ. Размер L.
8. **Доступные и по-настоящему публичные туалеты (A 5).** Покрытие давать диапазоном, а не точкой (53 % без тега); исключить `access=customers|private`. Размер S.

Следом стоят B5 (цепочки скамеек для пожилых) и B7 (проверка обещания electrify.brussels).

**Что понадобится в движке** (минимальный набор правок):

- в `ASSETS` добавить `walk_radius_m`, `candidate_min_dist_m`, `filters` (И, исключения по `access`) и `keep_tags` (wheelchair, opening_hours, indoor);
- общий загрузчик официальных наборов по конфигу (Opendatasoft `…/exports/geojson`, ArcGIS MapServer `…/query?f=geojson`);
- режим спроса «жители» с весами из `population_age.csv` вместо счёта POI;
- колонки справедливости по типу: домены BIMD, доля 65+ или 0–14, жара;
- явная пометка «нет данных» при нуле объектов, а не покрытие 0.

## 7. Ограничения этого ресёрча

- Счётчики OSM — это объекты с тегом, а не проверенные на месте. Счётчики по городам сняты одним запросом на город 26.09.2026; по Антверпену тяжёлые теги не получены (504).
- Площадки (`leisure=pitch`) и огороды — полигоны. Счёт в Overpass считает объекты, а не площадь.
- Карты afkoelplekken Гента, Changing Places во Фландрии и национальный набор BIPT на открытость не проверены до конца. Помечены [не проверено].
- Портал datastore.brussels (региональный) отрисовывается JavaScript, его содержимое по туалетам не прочитано [не проверено].
- Мой порог 100 м в B5 и все пороги отказа в B1 — наши и должны быть откалиброваны. Нормы в §2 взяты из источников.

## Источники

**Код и документы проекта**
- `pipelines/city_planner/engine/config.py`, `run.py`, `scoring.py`, `adapters/base.py`, `adapters/brussels.py`, `adapters/antwerp.py`, `adapters/ghent.py`; `docs/07-unified-facta.md`; `CLAUDE.md` (разделы «Типы объектов расширены…» 04.09, «Двенадцать прогонов планировщика…» 05.09, решение 25.09).
- BIMD 2011, заголовок файла доменов: https://raw.githubusercontent.com/bimd-project/bimd/main/FILE%202%20BIMD2011%20DOMAINS%20%28SCORES%2C%20RANKS%2C%20DECILES%29/BIMD2011_DOMAINS_STATISTICAL_SECTOR_ELLIS_WIDE.csv

**Покрытие OSM**
- taginfo Бельгия (Geofabrik), данные на 2026-09-25: https://taginfo.geofabrik.de/europe:belgium/ (API `/api/4/tag/stats`, `/api/4/tag/combinations`, `/api/4/search/by_value`)
- taginfo мир: https://taginfo.openstreetmap.org/
- Overpass, зеркало VK Maps: https://maps.mail.ru/osm/tools/overpass/api/interpreter (overpass-api.de сбрасывал соединение 26.09)

**Официальные открытые данные (каталоги)**
- Гент: https://data.stad.gent/ (наборы по ссылкам в таблице)
- Ville de Bruxelles и часть региональных наборов: https://opendata.brussels.be/
- Льеж: https://opendata.liege.be/
- Валлония (ODWB): https://www.odwb.be/
- Антверпен (ArcGIS Hub): https://portaal-stadantwerpen.opendata.arcgis.com/ ; слои `bereik_*` и `tekortzone_*`: https://geodata.antwerpen.be/arcgissql/rest/services/P_Portal/portal_publiek12/MapServer
- Регион Брюсселя, datastore: https://datastore.brussels/web/data/dataset/bruxelles_toilettes_publiques
- BIPT, почтовые точки: https://www.bipt-data.be/fr/opendata ; https://www.ibpt.be/consommateurs/services-postaux/operateurs-les-reseaux/point-postaux
- Hoppinpunten: https://transportdata.be/dataset/overzicht-hoppinpunten-in-vlaanderen

**Жара и прохладные места**
- Ville de Bruxelles, карта îlots de fraîcheur: https://www.bruxelles.be/carte-ilots-fraicheur
- Bruxelles Environnement, îlot de chaleur: https://environnement.brussels/citoyen/outils-et-donnees/etat-des-lieux-de-lenvironnement/ilot-de-chaleur
- La Libre, 25.06.2026, «refuges climatiques»: https://www.lalibre.be/planete/environnement/2026/06/25/bruxelles-se-transforme-en-cocotte-minute-face-a-la-canicule-les-villes-proposent-des-refuges-climatiques-XU3BRBV4ZFEEBPVXNE4JGB7VNM/
- RTBF, Ville de Bruxelles и другие коммуны: https://www.rtbf.be/article/ou-se-rafraichir-la-ville-de-bruxelles-propose-une-carte-de-ses-lieux-frais-les-autres-communes-francophones-a-la-traine-11755424
- L'Avenir, 13.07.2026, план на жару: https://www.lavenir.net/regions/bruxelles/2026/07/13/la-canicule-revele-les-failles-de-la-prise-en-charge-des-sans-abri-a-bruxelles-un-veritable-plan-est-desormais-en-preparation-SQQJSNGSUZCFHLKGCSHT55WTUI/
- Stad Gent, drinkwater- en afkoelplekken: https://stad.gent/nl/samenleven-welzijn-gezondheid/nieuws-evenementen/drinkwater-en-afkoelplekken-gent
- Барселона, климатические убежища (2026): https://www.barcelona.cat/infobarcelona/en/tema/climate-emergency/mes-de-500-refugis-climatics-per-combatre-la-calor-aquest-estiu-2026_1646096.html
- Доступность убежищ Барселоны для уязвимых (ScienceDirect): https://www.sciencedirect.com/science/article/pii/S0264275125007887

**Нормы радиуса**
- Cycloparking FAQ (200 / 350 / 500 м): https://parking.brussels/en/contact-and-support/faq-cycloparking ; очередь 8000 (2021): https://www.lavenir.net/regions/2021/01/05/8000-cyclistes-sur-liste-dattente-pour-un-parking-securise-a-bruxelles-il-faut-accepter-de-garer-son-velo-a-150m-du-domicile-K35P6FRNPRGIRLQS5EEKF5LM5E/
- Fields in Trust, Guidance for Outdoor Sport and Play (2015): https://www.dorsetcouncil.gov.uk/documents/35024/306859/Guidance+for+outdoor+sport+and+play+(Fields+In+Trust,+2015).pdf/7ff72c80-4370-4933-5c65-0b40af642508
- Inclusive Mobility (DfT): https://assets.publishing.service.gov.uk/media/61d32bb7d3bf7f1f72b5ffd2/inclusive-mobility-a-guide-to-best-practice-on-access-to-pedestrian-and-transport-infrastructure.pdf ; Active Travel England: https://activetravelengland.gov.uk/planning-active-places/benches-and-resting-points
- ITDP Bike-Share Planning Guide: https://nacto.org/wp-content/uploads/2014_ITDP_Bikeshare-Planning-Guide.pdf
- electrify.brussels / Sibelga (250 → 150 м; 22 000 к 2035): https://electrify.brussels/en/about/a-region-wide-vision ; https://www.sibelga.be/en/about-sibelga/projects-challenges/22000-charging-points-in-2035

**Прочее**
- bpost, сокращение сети ящиков (коммуна Frasnes-lez-Anvaing): https://www.frasnes-lez-anvaing.be/actualites/bpost-suppression-de-4-boites-aux-lettres-rouges
- Changing Places, Фландрия (Inter): https://www.vlaanderen.be/inter/mensen-met-een-handicap/changing-places ; первая в Де-Панне: https://www.depanne.be/nl/over-de-panne/communicatie/nieuws/primeur-de-panne-opent-eerste-changing-places-in-vlaanderen
- Менструальная бедность, Валлония: https://www.christiemorreale.be/precarite-menstruelle-la-wallonie-etend-la-distribution-de-protections-hygieniques-gratuites-sur-tout-son-territoire/

## Приложение: счётчики OSM по городам (Overpass, 26.09.2026)

| Тег | BXL | ANT | GNT | LGE | CRL |
|---|---|---|---|---|---|
| amenity=toilets | 188 | 93 | 144 | 52 | 12 |
| · wheelchair=yes | 51 | 30 | 26 | 14 | 5 |
| · access=customers/private/no | 28 | 11 | 23 | 12 | 1 |
| · changing_table=yes | 11 | 11 | 13 | 4 | 4 |
| changing_table=yes (всё) | 29 | 24 | 50 | 6 | 5 |
| fountain=splash_pad | 178 | 11 | 2 | 3 | 0 |
| playground=splash_pad | 0 | 6 | 0 | 1 | 0 |
| amenity=fountain | 443 | 53 | 24 | 39 | 4 |
| amenity=drinking_water | 180 | 97 | 27 | 31 | 2 |
| man_made=water_tap | 66 | 24 | 31 | 11 | 0 |
| amenity=shower | 5 | 5 | 10 | 0 | 0 |
| amenity=parcel_locker | 35 | 21 | 53 | 8 | 1 |
| amenity=post_box | 406 | 102 | 119 | 65 | 11 |
| amenity=bicycle_rental | 365 | 324 | 19 | 1 | 1 |
| amenity=car_sharing | 186 | 14 | 109 | 10 | 2 |
| amenity=mobility_hub | 0 | 5 | 3 | 0 | 0 |
| bicycle_parking=shed | 1177 | 19 | 55 | 10 | 0 |
| bicycle_parking=lockers | 5 | 26 | 18 | 2 | 0 |
| bicycle_parking=building | 15 | 35 | 10 | 6 | 0 |
| amenity=charging_station | 704 | 197 | 547 | 11 | 10 |
| amenity=device_charging_station | 3 | 1 | 0 | 0 | 0 |
| sport=table_tennis | 84 | 18 | 13 | 7 | 0 |
| sport=basketball | 118 | 97 | 50 | 15 | 12 |
| sport=skateboard | 14 | 13 | 13 | 3 | 0 |
| sport=boules | 122 | 43 | 116 | 25 | 7 |
| garden:type=community | 25 | 0 | 7 | 2 | 2 |
| landuse=allotments | 138 | 65 | 27 | 13 | 3 |
| community_centre=youth_centre | 24 | 5 | 8 | 2 | 0 |
| wlan + fee=no | 74 | 20 | 43 | 11 | 3 |
| highway=street_lamp | 9 863 | — | 1 879 | 2 696 | 187 |
| natural=tree | 64 674 | — | 14 510 | 11 480 | 2 261 |
| kerb=lowered | 14 843 | — | 625 | 935 | 39 |
| tactile_paving=yes | 21 806 | — | 1 069 | 1 685 | 144 |
| highway=crossing | 22 726 | — | 4 652 | 2 507 | 2 419 |
| amenity=give_box | 4 | 0 | 0 | 3 | 0 |
| amenity=clock | 50 | 5 | 9 | 0 | 2 |
| shelter_type=sun_shelter | 0 | 0 | 0 | 0 | 0 |
| amenity=bbq | 3 | 0 | 0 | 4 | 0 |
| amenity=bench | 7 739 | 3 175 | 2 098 | 1 373 | 167 |
| · backrest=yes | 5 419 | 2 001 | 1 561 | 896 | 62 |
| emergency=defibrillator | 272 | 252 | 142 | 62 | 6 |
| amenity=public_bookcase | 109 | 21 | 83 | 41 | 2 |

Для сравнения — 14 нынешних типов по Бельгии (taginfo): скамейки 67 180, урны 29 685, велопарковки 28 898, навесы 17 456, столы для пикника 11 319, контейнеры раздельного сбора 10 088, детские площадки 7 823, дефибрилляторы 5 672, туалеты 2 389, книжные шкафы 1 461, питьевая вода 1 082, уличные тренажёры 1 056, площадки для собак 708, велоремонтные станции 652.
