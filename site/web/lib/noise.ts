/* 3D simplex noise (Stefan Gustavson's algorithm, public domain), seeded.
   Used to draw ring outlines that wobble without a seam: sample it on a circle
   (cos θ, sin θ) and move the third axis for ring index and time. */

const GRAD: [number, number, number][] = [
  [1, 1, 0], [-1, 1, 0], [1, -1, 0], [-1, -1, 0], [1, 0, 1], [-1, 0, 1],
  [1, 0, -1], [-1, 0, -1], [0, 1, 1], [0, -1, 1], [0, 1, -1], [0, -1, -1],
]
const F3 = 1 / 3, G3 = 1 / 6

export function simplex3(seed = 1): (x: number, y: number, z: number) => number {
  // a permutation table shuffled by a small LCG, so the same seed draws the same wood
  const p = new Uint8Array(256)
  for (let i = 0; i < 256; i++) p[i] = i
  let s = seed >>> 0 || 1
  for (let i = 255; i > 0; i--) {
    s = (s * 1664525 + 1013904223) >>> 0
    const j = s % (i + 1)
    const t = p[i]!; p[i] = p[j]!; p[j] = t
  }
  const perm = new Uint8Array(512)
  for (let i = 0; i < 512; i++) perm[i] = p[i & 255]!

  return function noise(x: number, y: number, z: number): number {
    const sk = (x + y + z) * F3
    const i = Math.floor(x + sk), j = Math.floor(y + sk), k = Math.floor(z + sk)
    const t = (i + j + k) * G3
    const x0 = x - (i - t), y0 = y - (j - t), z0 = z - (k - t)
    let i1: number, j1: number, k1: number, i2: number, j2: number, k2: number
    if (x0 >= y0) {
      if (y0 >= z0) { i1 = 1; j1 = 0; k1 = 0; i2 = 1; j2 = 1; k2 = 0 }
      else if (x0 >= z0) { i1 = 1; j1 = 0; k1 = 0; i2 = 1; j2 = 0; k2 = 1 }
      else { i1 = 0; j1 = 0; k1 = 1; i2 = 1; j2 = 0; k2 = 1 }
    } else if (y0 < z0) { i1 = 0; j1 = 0; k1 = 1; i2 = 0; j2 = 1; k2 = 1 }
    else if (x0 < z0) { i1 = 0; j1 = 1; k1 = 0; i2 = 0; j2 = 1; k2 = 1 }
    else { i1 = 0; j1 = 1; k1 = 0; i2 = 1; j2 = 1; k2 = 0 }
    const x1 = x0 - i1 + G3, y1 = y0 - j1 + G3, z1 = z0 - k1 + G3
    const x2 = x0 - i2 + 2 * G3, y2 = y0 - j2 + 2 * G3, z2 = z0 - k2 + 2 * G3
    const x3 = x0 - 1 + 3 * G3, y3 = y0 - 1 + 3 * G3, z3 = z0 - 1 + 3 * G3
    const ii = i & 255, jj = j & 255, kk = k & 255
    const corner = (gi: number, cx: number, cy: number, cz: number): number => {
      let tt = 0.6 - cx * cx - cy * cy - cz * cz
      if (tt < 0) return 0
      const g = GRAD[gi % 12]!
      tt *= tt
      return tt * tt * (g[0] * cx + g[1] * cy + g[2] * cz)
    }
    const n0 = corner(perm[ii + perm[jj + perm[kk]!]!]!, x0, y0, z0)
    const n1 = corner(perm[ii + i1 + perm[jj + j1 + perm[kk + k1]!]!]!, x1, y1, z1)
    const n2 = corner(perm[ii + i2 + perm[jj + j2 + perm[kk + k2]!]!]!, x2, y2, z2)
    const n3 = corner(perm[ii + 1 + perm[jj + 1 + perm[kk + 1]!]!]!, x3, y3, z3)
    return 32 * (n0 + n1 + n2 + n3)   // ≈ −1…1
  }
}
