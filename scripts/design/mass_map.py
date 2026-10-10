#!/usr/bin/env python3
"""
Карта масс для дизайн-референсов: где лежит визуальный вес экрана — измерено, а не нарисовано.

Доски Figma «Landing · layout by section — masses» (108:5) и «Interface · layout — masses»
(115:2): каждая секция лендинга и каждое состояние атласа стоят рядом с референсом, у которого
массы совпадают, и у обоих посчитана карта масс.

Метод
    чернила  расстояние пикселя от цвета земли секции (максимум по каналам; земля — самый
             частый цвет на кромке картинки)
    линии    линейки и рамки карточек — структура, а не масса: длинные серии тонких чернил
             (чернила здесь, а в 3 px выше и ниже, или слева и справа, нет) убираются до подсчёта
    клетки   картинка режется на сетку ~ширина/150 px; клетка с покрытием больше 4 % — чернильная
    блоки    чернильные клетки расширяются на 2 клетки вбок и на 1 вниз, чтобы буквы сливались в
             строки, а строки в абзацы; каждая связная группа — один блок (его рамка)
    вес      среднее покрытие × (0,35 + средняя сила чернил) → один из четырёх серых, от лёгкого
             к тяжёлому
Фото во весь экран — один блок; первые экраны рисуются по замеренным рамкам. Для интерфейса
карта — одно поле, а у каждой плавающей карточки своя внутренняя карта масс (`--cards`).

Запуск
    python3 scripts/design/mass_map.py SECTION.jpg OUT.png [--mobbin] [--cells 150]
    python3 scripts/design/mass_map.py SCREEN.jpg OUT.png --bar 46 --cards x,y,w,h x,y,w,h [--scale 1.333]
Нужны Pillow и numpy.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque

import numpy as np
from PIL import Image, ImageDraw

GREYS = [(214, 211, 202), (163, 160, 150), (94, 93, 89), (20, 20, 19)]   # light -> heavy
GROUND = (246, 245, 241)
FIELD, BAR = (200, 198, 190), (232, 230, 222)


def strip_mobbin_band(im: Image.Image) -> Image.Image:
    """Mobbin previews end in a dark #2C2C2C credit band; the logo is too narrow to move the median."""
    a = np.asarray(im.convert("RGB")).astype(int)
    y = a.shape[0] - 1
    while y > a.shape[0] * 0.6 and np.abs(np.median(a[y], axis=0) - 44).max() < 14:
        y -= 1
    return im.crop((0, 0, im.width, y + 1)) if y < a.shape[0] - 1 else im


def ground(a: np.ndarray) -> np.ndarray:
    border = np.concatenate([a[:6].reshape(-1, 3), a[-6:].reshape(-1, 3),
                             a[:, :6].reshape(-1, 3), a[:, -6:].reshape(-1, 3)])
    q = [tuple((p // 8) * 8) for p in border]
    top = Counter(q).most_common(1)[0][0]
    return np.median(np.array([p for p, k in zip(border, q) if k == top]), axis=0)


def _long_runs(mask: np.ndarray, min_run: int) -> np.ndarray:
    out = np.zeros_like(mask)
    for i, row in enumerate(mask):
        if row.sum() < min_run:
            continue
        edges = np.flatnonzero(np.diff(np.concatenate(([0], row.astype(np.int8), [0]))))
        for s0, s1 in zip(edges[::2], edges[1::2]):
            if s1 - s0 >= min_run:
                out[i, s0:s1] = True
    return out


def mass_map(im: Image.Image, cells_across: int = 150) -> tuple[Image.Image, int]:
    a = np.asarray(im.convert("RGB")).astype(int)
    h, w, _ = a.shape
    ink = np.abs(a - ground(a)).max(axis=2)
    m, pad = ink > 24, 3
    shift = lambda arr, dy, dx: np.roll(np.roll(arr, dy, 0), dx, 1)
    thin_h = m & ~shift(m, pad, 0) & ~shift(m, -pad, 0)
    thin_v = m & ~shift(m, 0, pad) & ~shift(m, 0, -pad)
    min_run = max(40, w // 30)
    lines = _long_runs(thin_h, min_run) | _long_runs(thin_v.T, min_run).T
    grown = lines.copy()
    for k in (1, 2):
        grown |= shift(lines, k, 0) | shift(lines, -k, 0) | shift(lines, 0, k) | shift(lines, 0, -k)
    ink = np.where(grown, 0, ink)

    s = max(4, round(w / cells_across))
    gh, gw = h // s, w // s
    cells = ink[: gh * s, : gw * s].reshape(gh, s, gw, s)
    cov = (cells > 24).mean(axis=(1, 3))
    strength = cells.mean(axis=(1, 3)) / 255.0
    on = cov > 0.04
    d = on.copy()
    for dx in (1, 2):
        d[:, dx:] |= on[:, :-dx]
        d[:, :-dx] |= on[:, dx:]
    d2 = d.copy()
    d2[1:] |= d[:-1]
    d2[:-1] |= d[1:]

    seen = np.zeros_like(d2)
    blocks = []
    for y in range(gh):
        for x in range(gw):
            if not d2[y, x] or seen[y, x]:
                continue
            q, ys, xs = deque([(y, x)]), [], []
            seen[y, x] = True
            while q:
                cy, cx = q.popleft()
                ys.append(cy); xs.append(cx)
                for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                    if 0 <= ny < gh and 0 <= nx < gw and d2[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            y0, y1, x0, x1 = min(ys), max(ys) + 1, min(xs), max(xs) + 1
            if (y1 - y0) * (x1 - x0) < 3:
                continue
            inside = on[y0:y1, x0:x1]
            st = strength[y0:y1, x0:x1][inside].mean() if inside.any() else 0.0
            blocks.append((x0 * s, y0 * s, x1 * s, y1 * s, cov[y0:y1, x0:x1].mean() * (0.35 + st)))

    out = Image.new("RGB", (w, h), GROUND)
    dr = ImageDraw.Draw(out)
    for x0, y0, x1, y1, wt in sorted(blocks, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]), reverse=True):
        level = 0 if wt < 0.10 else 1 if wt < 0.22 else 2 if wt < 0.42 else 3
        dr.rectangle((x0, y0, x1 - 1, y1 - 1), fill=GREYS[level])
    return out, len(blocks)


def interface_mass(img: Image.Image, bar: float, cards: list[tuple[float, float, float, float]],
                   scale: float = 1.0) -> Image.Image:
    """A map screen: the map is one field, the bar a light band, each card its own inner masses."""
    out = Image.new("RGB", img.size, FIELD)
    d = ImageDraw.Draw(out)
    d.rectangle((0, 0, img.width, round(bar * scale)), fill=BAR)
    for x, y, w, h in cards:
        box = tuple(round(v * scale) for v in (x, y, x + w, y + h))
        inner, _ = mass_map(img.crop(box), cells_across=60)
        out.paste(inner, box[:2])
        d.rectangle(box, outline=GREYS[3], width=2)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("src"); ap.add_argument("dst")
    ap.add_argument("--mobbin", action="store_true", help="cut the Mobbin credit band first")
    ap.add_argument("--cells", type=int, default=150, help="grid cells across the width")
    ap.add_argument("--bar", type=float, help="interface mode: top bar height, in the screen's units")
    ap.add_argument("--cards", nargs="*", default=[], help="interface mode: floating cards as x,y,w,h")
    ap.add_argument("--scale", type=float, default=1.0, help="pixels per unit of --bar and --cards")
    args = ap.parse_args()
    im = Image.open(args.src).convert("RGB")
    if args.mobbin:
        im = strip_mobbin_band(im)
    if args.bar is not None:
        cards = [tuple(float(v) for v in c.split(",")) for c in args.cards]
        interface_mass(im, args.bar, cards, args.scale).save(args.dst)
        print(args.dst, im.size, f"{len(cards)} cards")
    else:
        out, n = mass_map(im, args.cells)
        out.save(args.dst)
        print(args.dst, im.size, f"{n} blocks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
