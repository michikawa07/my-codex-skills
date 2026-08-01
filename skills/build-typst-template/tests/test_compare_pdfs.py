from pathlib import Path
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import compare_pdfs


class CompareContractTests(unittest.TestCase):
    def test_layer_selection_is_closed(self):
        self.assertEqual(compare_pdfs.parse_layers(None), set(compare_pdfs.DEFAULT_LAYERS))
        self.assertEqual(compare_pdfs.parse_layers("content,geometry"), {"content", "geometry"})
        with self.assertRaises(compare_pdfs.InputError):
            compare_pdfs.parse_layers("content,ocr")

    def test_gate_contract_rejects_unknown_fields(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "contract.json"
            path.write_text('{"mode":"zero","regions":[],"unknown":true}', encoding="utf-8")
            with self.assertRaises(compare_pdfs.InputError):
                compare_pdfs.parse_contract(path)

    def test_local_rule_bands_capture_dense_rows_and_columns(self):
        width, height = 6, 4
        values = bytearray(width * height)
        for column in range(width):
            values[1 * width + column] = 255
        for row in range(height):
            values[row * width + 4] = 255
        horizontal = compare_pdfs.local_rule_bands(
            bytes(values), width, (0, 0, width, height), horizontal=True,
        )
        vertical = compare_pdfs.local_rule_bands(
            bytes(values), width, (0, 0, width, height), horizontal=False,
        )
        self.assertEqual([(item["start"], item["end"]) for item in horizontal], [(1, 2)])
        self.assertEqual([(item["start"], item["end"]) for item in vertical], [(4, 5)])


if __name__ == "__main__":
    unittest.main()
