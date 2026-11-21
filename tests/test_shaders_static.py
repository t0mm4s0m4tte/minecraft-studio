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

    def test_fsh_rendertargets_match_layout_outputs(self):
        rt_pattern = re.compile(r"/\*\s*RENDERTARGETS:\s*([^*]+)\*/")
        layout_pattern = re.compile(r"layout\s*\(\s*location\s*=\s*\d+\s*\)\s*out\s+")
        for f in self.fsh_files:
            content = f.read_text(encoding="utf-8")
            rt_match = rt_pattern.search(content)
            self.assertIsNotNone(rt_match, f"{f.name} missing RENDERTARGETS directive")
            rt_count = len([x.strip() for x in rt_match.group(1).split(",") if x.strip()])
            layout_count = len(layout_pattern.findall(content))
            self.assertEqual(
                rt_count,
                layout_count,
                f"{f.name}: RENDERTARGETS count ({rt_count}) != layout outputs count ({layout_count})"
            )

    def test_shader_includes_exist(self):
        include_pattern = re.compile(r'#include\s+"([^"]+)"')
        for f in self.vsh_files + self.fsh_files:
            content = f.read_text(encoding="utf-8")
            for inc in include_pattern.findall(content):
                clean_inc = inc.lstrip("/\\")
                target = self.shaders_dir / clean_inc
                self.assertTrue(target.is_file(), f"{f.name} includes non-existent file: {inc} (resolved: {target})")

    def test_lang_files_key_parity(self):
        lang_dir = self.shaders_dir / "lang"
        en_lang = lang_dir / "en_us.lang"
        it_lang = lang_dir / "it_it.lang"
        self.assertTrue(en_lang.is_file(), "en_us.lang not found")
        self.assertTrue(it_lang.is_file(), "it_it.lang not found")

        def extract_keys(path):
            keys = set()
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    keys.add(line.split("=", 1)[0].strip())
            return keys

        en_keys = extract_keys(en_lang)
        it_keys = extract_keys(it_lang)
        self.assertEqual(en_keys, it_keys, f"Key mismatch between en_us and it_it: diff={en_keys ^ it_keys}")

    def test_no_unbounded_while_true_loops(self):
        while_pattern = re.compile(r"while\s*\(\s*true\s*\)")
        for f in self.vsh_files + self.fsh_files:
            content = f.read_text(encoding="utf-8")
            self.assertFalse(
                while_pattern.search(content),
                f"{f.name} contains unbounded while(true) loop"
            )

if __name__ == "__main__":
    unittest.main()
