import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "studio"))
import user_library


class TerrainStorageTests(unittest.TestCase):
    def test_saved_terrain_roundtrip_and_tampering(self):
        terrain = json.loads((ROOT / "examples/rolling_hills.heightfield.json").read_text())
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, BIPEDAL_DATA_ROOT=folder):
            entry = user_library.save_terrain("丘", terrain)
            self.assertEqual(user_library.read_terrain(entry["id"])["terrain"], terrain)
            path = Path(folder) / "terrains" / (entry["id"] + ".json")
            record = json.loads(path.read_text(encoding="utf-8"))
            record["terrain"]["height_offsets_m"][-1] += 0.01
            path.write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaises(ValueError):
                user_library.read_terrain(entry["id"])
