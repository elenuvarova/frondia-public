"""Куда генераторы страниц пишут и откуда читают промежуточное.

Два разных места, и путать их нельзя:

  OUT      — готовые страницы перед публикацией. Временная папка: её можно
             стереть, всё в ней пересобирается командой. Переопределяется
             переменной окружения FRONDIA_OUT — так тест собирает все страницы
             в чистую папку и проверяет, что ни одна не зависит от старых файлов.

  DERIVED  — промежуточные данные МЕЖДУ генераторами: данные атласа, его
             гистограмма, SVG карты для лендинга. Лежат В ПРОЕКТЕ.

⚠️ Почему это разделение появилось. До 24.09.2026 промежуточное тоже лежало во
временной папке. Её очистили во время перерыва — и атлас перестал собираться,
а за ним лендинг, который берёт из атласа карту для героя. Правило «каждая
опубликованная страница пересобирается скриптом» три недели было ложным, и
заметить это можно было только после очистки. Тест `test_every_page_rebuilds_
from_a_clean_output_folder` теперь проверяет это при каждом прогоне.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# the finished pages: FRONDIA_OUT, or a folder in the system's temp dir (it used to be one session's scratchpad path)
OUT = Path(os.environ.get("FRONDIA_OUT") or Path(tempfile.gettempdir()) / "frondia-out")
OUT.mkdir(parents=True, exist_ok=True)

DERIVED = Path(os.environ.get("FRONDIA_DERIVED") or ROOT / "data" / "derived")   # тест подменяет на пустую папку
DERIVED.mkdir(parents=True, exist_ok=True)


MONTHS_RU = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа",
             "сентября", "октября", "ноября", "декабря"]


def today_ru() -> str:
    """Дата сборки страницы словами. Раньше дата была вписана в каждый генератор руками,
    и бюллетень сезона 2026 сообщал, что сформирован 3 сентября — до конца сезона."""
    from datetime import date
    d = date.today()
    return f"{d.day} {MONTHS_RU[d.month - 1]} {d.year}"
