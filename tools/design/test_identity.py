"""Check selected-asset rejection and proportion-preserving print preparation."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

spec = importlib.util.spec_from_file_location("prepare_book", Path(__file__).with_name("prepare_book.py"))
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class CoverContract(unittest.TestCase):
    def test_changed_asset_is_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            asset = directory / "art.png"
            asset.write_bytes(b"reviewed pixels")
            (directory / "selected-artwork.json").write_text(json.dumps({
                "file": "art.png", "sha256": hashlib.sha256(asset.read_bytes()).hexdigest()}))
            prepare.verify_artwork(directory)
            asset.write_bytes(b"changed pixels")
            with self.assertRaisesRegex(ValueError, "reviewed identity"):
                prepare.verify_artwork(directory)

    def test_print_canvas_preserves_original_geometry_and_image(self):
        original = prepare.ROOT / "design/identity/front.svg"
        with tempfile.TemporaryDirectory() as name:
            destination = Path(name) / "cover.svg"
            prepare.print_cover(original, destination, "#000000", 210, 297)
            before = ET.parse(original).getroot()
            after = ET.parse(destination).getroot()
            self.assertEqual(after.get("width"), "210mm")
            self.assertEqual(after.get("height"), "297mm")
            x,y,w,h=map(float,after.get("viewBox").split())
            self.assertLessEqual(x,0)
            self.assertLessEqual(y,0)
            self.assertGreaterEqual(x+w,800)
            self.assertGreaterEqual(y+h,1100)
            self.assertAlmostEqual(w/h,210/297,places=5)
            # Only a background extension may precede the unmodified composition.
            self.assertEqual(len(after), len(before) + 1)
            for a, b in zip(before, list(after)[1:]):
                self.assertEqual(ET.tostring(a), ET.tostring(b))

    def test_back_footer_extends_without_moving_its_text(self):
        with tempfile.TemporaryDirectory() as name:
            destination = Path(name) / "back.svg"
            prepare.print_cover(prepare.ROOT / "design/identity/back.svg", destination, "#F5F2EB", 210, 297)
            after = ET.parse(destination).getroot()
            self.assertEqual(float(after[1].get("width")),800)
            self.assertGreater(float(after[1].get("height")),133)
            x,y,w,h=map(float,after.get("viewBox").split())
            self.assertAlmostEqual(float(after[1].get("y")) + float(after[1].get("height")),y+h,places=2)
            self.assertEqual(after[1].get("y"), "967")
            before = ET.parse(prepare.ROOT / "design/identity/back.svg").getroot()
            for a,b in zip(before,list(after)[2:]):
                self.assertEqual(ET.tostring(a),ET.tostring(b))


if __name__ == "__main__":
    unittest.main()
