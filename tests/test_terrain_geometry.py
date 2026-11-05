import json
import math
import unittest

from robust_bipedal.terrain_geometry import (
    BASE_HEIGHT_M, SCHEMA_VERSION, SAMPLES, START_PAD, TerrainProfile,
    WORLD_STEP_M, from_normalized_stroke,
)


class TerrainGeometryTests(unittest.TestCase):
    def setUp(self):
        self.flat = TerrainProfile((0.0,) * SAMPLES)

    def test_flat_has_200_samples(self):
        self.assertEqual(len(self.flat.world_points()), SAMPLES)

    def test_origin_and_spacing(self):
        w = self.flat.world_points()
        self.assertEqual(w[0], (0.0, BASE_HEIGHT_M))
        self.assertAlmostEqual(w[-1][0], (SAMPLES - 1) * WORLD_STEP_M)

    def test_flat_stroke_roundtrips(self):
        p = from_normalized_stroke([(0, 0.5), (1, 0.5)])
        self.assertEqual(p, self.flat)

    def test_initial_pad_forced_flat(self):
        p = from_normalized_stroke([(0, 0.5), (0.1, 0.5), (1, 0.45)])
        self.assertTrue(all(x == 0 for x in p.height_offsets_m[:START_PAD]))

    def test_hash_stable_under_round_trip(self):
        self.assertEqual(self.flat.terrain_sha256,
                         TerrainProfile.from_data(json.loads(self.flat.canonical_json())).terrain_sha256)

    def test_non_finite_rejected(self):
        v = list(self.flat.height_offsets_m)
        v[30] = math.nan
        with self.assertRaises(ValueError):
            TerrainProfile(tuple(v))

    def test_boolean_rejected(self):
        v = list(self.flat.height_offsets_m)
        v[30] = True
        with self.assertRaises(ValueError):
            TerrainProfile(tuple(v))

    def test_wrong_count_rejected(self):
        with self.assertRaises(ValueError):
            TerrainProfile((0.0,) * (SAMPLES-1))

    def test_initial_pad_change_rejected(self):
        v = list(self.flat.height_offsets_m)
        v[5] = 0.1
        with self.assertRaises(ValueError):
            TerrainProfile(tuple(v))

    def test_large_step_rejected(self):
        v = list(self.flat.height_offsets_m)
        v[30] = 1.5
        with self.assertRaises(ValueError):
            TerrainProfile(tuple(v))

    def test_large_height_rejected(self):
        v = list(self.flat.height_offsets_m)
        v[30] = 1.0
        v[31] = 2.1
        with self.assertRaises(ValueError):
            TerrainProfile(tuple(v))

    def test_backtracking_stroke_rejected(self):
        with self.assertRaises(ValueError):
            from_normalized_stroke([(0.0, 0.5), (0.6, 0.5), (0.4, 0.5), (1.0, 0.5)])

    def test_closed_shape_out_of_scope(self):
        with self.assertRaises(ValueError):
            from_normalized_stroke([(0.0, 0.5), (0.6, 0.3), (0.6, 0.8), (1.0, 0.5)])

    def test_schema_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            TerrainProfile.from_data({"schema_version":"v2", "height_offsets_m":[0]*SAMPLES})

    def test_schema_shape(self):
        self.assertEqual(self.flat.to_data()["schema_version"], SCHEMA_VERSION)

    def test_nonzero_terrain_is_distinct(self):
        w = list(self.flat.height_offsets_m)
        w[60] = 0.1
        p = TerrainProfile(tuple(w))
        self.assertNotEqual(self.flat.terrain_sha256, p.terrain_sha256)


if __name__ == "__main__":
    unittest.main()
