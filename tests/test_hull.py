"""Tests for the silhouette carver (needs numpy; skipped where numpy is unavailable)."""
import os
import sys
import unittest
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
try:
    import numpy as np
    import hull
except ImportError:  # CI's system python may lack numpy; Blender's python always has it
    np = None


def disc(n):
    yy, xx = np.mgrid[:n, :n]
    return (xx - (n - 1) / 2) ** 2 + (yy - (n - 1) / 2) ** 2 <= ((n - 1) / 2) ** 2


@unittest.skipIf(np is None, "numpy not installed")
class TestHull(unittest.TestCase):
    def test_disc_masks_carve_a_ball(self):
        occ, origin, _ = hull.carve(disc(60), disc(60), height_m=1.0, voxel=0.025)
        vol = occ.sum() * 0.025 ** 3
        self.assertAlmostEqual(vol, 4 / 3 * np.pi * 0.5 ** 3, delta=0.12)  # ~0.52 m3 ball

    def test_limb_depth_follows_its_thickness(self):
        # a thin horizontal bar in front, a deep body in side: the bar must stay thin in depth
        front = np.zeros((40, 80), bool)
        front[18:22, 5:75] = True
        front[0:40, 35:45] = True
        side = np.zeros((40, 40), bool)
        side[:, 5:35] = True
        occ, _, s = hull.carve(front, side, height_m=1.0, voxel=0.02)
        bar = occ[2:8].any(axis=(0, 2))           # depth extent near the bar's end
        body = occ[occ.shape[0] // 2].any(axis=1)
        self.assertLess(bar.sum(), body.sum() / 3)

    def test_boundary_is_closed(self):
        occ = np.zeros((4, 4, 4), bool)
        occ[1:3, 1:3, 1:3] = True
        occ[1, 1, 3] = True
        verts, quads = hull.boundary_quads(occ, np.zeros(3), 1.0)
        edges = Counter()
        for q in quads:
            for i in range(4):
                edges[tuple(sorted((q[i], q[(i + 1) % 4])))] += 1
        self.assertTrue(all(c == 2 for c in edges.values()))
        self.assertEqual(len(quads), 6 * 4 + 4)  # 2x2x2 cube faces + a bump adds 4 sides


if __name__ == "__main__":
    unittest.main()
