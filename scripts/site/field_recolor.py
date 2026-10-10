#!/usr/bin/env python3
"""
Перекраска готового кадра поля в другую палитру из field.py — без Earth Engine.

Earth Engine красит NDVI линейной интерполяцией между ступенями палитры в sRGB, поэтому
пиксель кадра light лежит на ломаной из девяти ступеней (плюс размытие и шум JPEG).
Для каждого пикселя скрипт находит ближайшую точку ломаной (отрезок и долю на нём), берёт
ту же точку на ломаной новой палитры и прибавляет остаток — зерно и сглаживание остаются.
Порядок ступеней тот же, поэтому светлое по-прежнему значит «мало зелени», тёмное — лес.
Остаток печатается: если он велик, кадр рисовали не этой палитрой и перекраска неверна.

Палитры читаются из field.py как литерал (без импорта Earth Engine).

Запуск:
    python3 scripts/site/field_recolor.py --src site/public/field/brussels-wide-2024-light.jpg --palette cadro
    → site/public/field/brussels-wide-2024-cadro.jpg
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

import numpy as np
from PIL import Image

FIELD = Path(__file__).with_name("field.py")


def palettes() -> dict[str, list[str]]:
    tree = ast.parse(FIELD.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "PALETTES" for t in node.targets):
            return ast.literal_eval(node.value)
    raise SystemExit("PALETTES не найден в field.py")


def rgb(stops: list[str]) -> np.ndarray:
    return np.array([[int(s[i:i + 2], 16) for i in (0, 2, 4)] for s in stops], dtype=np.float32)


def recolor(px: np.ndarray, old: np.ndarray, new: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """px — (N, 3). Возвращает перекрашенные пиксели и расстояние до ломаной old."""
    a, d = old[:-1], old[1:] - old[:-1]                        # (S, 3)
    rel = px[:, None, :] - a[None]                             # (N, S, 3)
    t = np.clip((rel * d[None]).sum(-1) / (d * d).sum(-1)[None], 0, 1)   # (N, S)
    proj = a[None] + t[..., None] * d[None]
    dist = np.linalg.norm(px[:, None, :] - proj, axis=-1)      # (N, S)
    k = dist.argmin(1)
    n = np.arange(len(px))
    tk = t[n, k][:, None]
    resid = px - proj[n, k]
    out = new[:-1][k] + tk * (new[1:] - new[:-1])[k] + resid
    return np.clip(out, 0, 255), dist[n, k]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--src", required=True, help="кадр в палитре light")
    ap.add_argument("--palette", required=True, help="ключ PALETTES в field.py")
    ap.add_argument("--from-palette", default="light")
    args = ap.parse_args()
    pals = palettes()
    old, new = rgb(pals[args.from_palette]), rgb(pals[args.palette])
    src = Path(args.src)
    im = np.asarray(Image.open(src).convert("RGB"), dtype=np.float32)
    h, w, _ = im.shape
    out, dist = recolor(im.reshape(-1, 3), old, new)
    dst = src.with_name(src.name.replace(f"-{args.from_palette}.", f"-{args.palette}."))
    if dst == src:
        raise SystemExit(f"в имени {src.name} нет «-{args.from_palette}.»")
    Image.fromarray(out.reshape(h, w, 3).round().astype(np.uint8)).save(dst, quality=88, optimize=True)
    q = np.quantile(dist, [0.5, 0.95, 0.99])
    print(f"{dst}  {w}×{h}  остаток до ломаной, ед. sRGB: медиана {q[0]:.1f} · 95 % {q[1]:.1f} · 99 % {q[2]:.1f}")


if __name__ == "__main__":
    main()
