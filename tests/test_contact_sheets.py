import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

# Load generate_contact_sheets.py dynamically from packs/aetheria-labpbr-32x/scripts/
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT_PATH = _REPO_ROOT / "packs" / "aetheria-labpbr-32x" / "scripts" / "generate_contact_sheets.py"

spec = importlib.util.spec_from_file_location("generate_contact_sheets", _SCRIPT_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules["generate_contact_sheets"] = module
spec.loader.exec_module(module)
generate_sheets = module.generate_sheets

class TestContactSheets(unittest.TestCase):
    def test_generate_sheets_real_repo(self):
        pack_dir = _REPO_ROOT / "packs" / "aetheria-labpbr-32x"

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir)
            p1, p2 = generate_sheets(pack_dir, out_dir)

            self.assertTrue(p1.exists(), f"File {p1} does not exist")
            self.assertTrue(p2.exists(), f"File {p2} does not exist")

            self.assertGreater(p1.stat().st_size, 1000, f"File {p1} too small ({p1.stat().st_size} bytes)")
            self.assertGreater(p2.stat().st_size, 1000, f"File {p2} too small ({p2.stat().st_size} bytes)")

if __name__ == "__main__":
    unittest.main()
