import re
import unittest
from pathlib import Path

class TestShadersStatic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path(__file__).resolve().parent.parent
        cls.shaders_dir = cls.repo_root / "shaders" / "luminary-shaders" / "shaders"
        cls.vsh_files = sorted(cls.shaders_dir.glob("*.vsh"))
        cls.fsh_files = sorted(cls.shaders_dir.glob("*.fsh"))

    def test_shaders_version_directive(self):
        self.assertTrue(len(self.vsh_files) > 0, "No .vsh files found")
        self.assertTrue(len(self.fsh_files) > 0, "No .fsh files found")

        for f in self.vsh_files + self.fsh_files:
            content = f.read_text(encoding="utf-8")
            lines = [l.strip() for l in content.splitlines() if l.strip()]
            self.assertTrue(len(lines) > 0, f"File {f.name} is empty")
            self.assertEqual(
                lines[0],
                "#version 330 compatibility",
                f"{f.name} does not start with '#version 330 compatibility'"
            )

    def test_fsh_rendertargets_directive(self):
        rt_pattern = re.compile(r"/\*\s*RENDERTARGETS:\s*[^*]+\*/")
        for f in self.fsh_files:
            content = f.read_text(encoding="utf-8")
            self.assertRegex(
                content,
                rt_pattern,
                f"{f.name} does not contain directive /* RENDERTARGETS: ... */"
            )

    def test_gbuffers_fsh_srgb_to_linear(self):
        gbuffers_fsh = sorted(self.shaders_dir.glob("gbuffers_*.fsh"))
        self.assertTrue(len(gbuffers_fsh) > 0, "No gbuffers_*.fsh files found")

        for f in gbuffers_fsh:
            content = f.read_text(encoding="utf-8")
            self.assertIn(
                "srgbToLinear",
                content,
                f"{f.name} does not contain 'srgbToLinear' transform"
            )

    def test_block_properties_no_duplicate_assignments(self):
        bp_path = self.shaders_dir / "block.properties"
        self.assertTrue(bp_path.exists(), "block.properties not found")

        assigned_blocks = {}
        for line_num, raw_line in enumerate(bp_path.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            self.assertIn("=", line, f"Invalid format in block.properties line {line_num}: {line}")
            left, right = line.split("=", 1)
            block_id = left.strip()
            names = right.strip().split()
            for name in names:
                self.assertNotIn(
                    name,
                    assigned_blocks,
                    f"Block '{name}' in block.properties is assigned to multiple IDs: '{assigned_blocks.get(name)}' and '{block_id}'"
                )
                assigned_blocks[name] = block_id

if __name__ == "__main__":
    unittest.main()
