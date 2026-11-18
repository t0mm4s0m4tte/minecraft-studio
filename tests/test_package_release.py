"""Unit test per scripts/package_release.py (TDD)."""

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))


class TestPackageRelease(unittest.TestCase):
    def test_packages_zips_and_copies_jars_from_fixture(self):
        from package_release import build_release

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            out = Path(tmp) / "dist"

            # Fixture resource pack
            pack_dir = root / "packs" / "aetheria-labpbr-32x"
            (pack_dir / "assets" / "minecraft" / "textures" / "block").mkdir(parents=True)
            (pack_dir / "scripts").mkdir(parents=True)
            (pack_dir / "pack.mcmeta").write_text('{"pack": {"pack_format": 34}}', encoding="utf-8")
            (pack_dir / "mvp-60-blocks.json").write_text(json.dumps({"categories": {}}), encoding="utf-8")
            (pack_dir / "scripts" / "validate_labpbr.py").write_text("print('ok')\n", encoding="utf-8")
            (pack_dir / "assets" / "minecraft" / "textures" / "block" / "stone.png").write_bytes(b"PNG")

            # Fixture shader pack
            shader_dir = root / "shaders" / "luminary-shaders" / "shaders"
            (shader_dir / "lib").mkdir(parents=True)
            (shader_dir / "shaders.properties").write_text("pbr.format = lab_pbr_1_3\n", encoding="utf-8")
            (shader_dir / "lib" / "settings.glsl").write_text("#define PBR_ENABLED\n", encoding="utf-8")

            # Fixture mod jars
            mod_dir = root / "mods" / "ambient-luminescence"
            (mod_dir / "fabric" / "build" / "libs").mkdir(parents=True)
            (mod_dir / "neoforge" / "build" / "libs").mkdir(parents=True)
            (mod_dir / "fabric" / "build" / "libs" / "fabric-1.0.0.jar").write_bytes(b"FABRIC")
            (mod_dir / "neoforge" / "build" / "libs" / "neoforge-1.0.0.jar").write_bytes(b"NEOFORGE")

            artifacts = build_release(
                root_dir=root,
                output_dir=out,
                version="1.0.0",
                skip_gradle=True,
                skip_validate=True,
            )

            pack_zip = out / "Aetheria-LabPBR-32x-1.0.0.zip"
            shader_zip = out / "Luminary-Shaders-1.0.0.zip"
            fabric_jar = out / "ambient_luminescence-fabric-1.0.0.jar"
            neoforge_jar = out / "ambient_luminescence-neoforge-1.0.0.jar"

            self.assertEqual(artifacts["resource_pack"], pack_zip)
            self.assertEqual(artifacts["shader_pack"], shader_zip)
            self.assertTrue(pack_zip.is_file())
            self.assertTrue(shader_zip.is_file())
            self.assertTrue(fabric_jar.is_file())
            self.assertTrue(neoforge_jar.is_file())

            with zipfile.ZipFile(pack_zip) as zf:
                names = set(zf.namelist())
                self.assertIn("pack.mcmeta", names)
                self.assertIn("assets/minecraft/textures/block/stone.png", names)
                self.assertFalse(any(n.startswith("scripts/") for n in names))
                self.assertNotIn("mvp-60-blocks.json", names)

            with zipfile.ZipFile(shader_zip) as zf:
                names = set(zf.namelist())
                self.assertIn("shaders/shaders.properties", names)
                self.assertIn("shaders/lib/settings.glsl", names)

    def test_real_repo_release_validation_and_zips(self):
        from package_release import build_release

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "dist"
            artifacts = build_release(
                root_dir=REPO_ROOT,
                output_dir=out,
                version="1.0.0",
                skip_gradle=True,
                skip_validate=False,
            )
            with zipfile.ZipFile(artifacts["resource_pack"]) as zf:
                pngs = [n for n in zf.namelist() if n.endswith(".png")]
                self.assertGreaterEqual(len(pngs), 180)
                self.assertIn("pack.mcmeta", zf.namelist())

            with zipfile.ZipFile(artifacts["shader_pack"]) as zf:
                names = set(zf.namelist())
                self.assertIn("shaders/shaders.properties", names)
                self.assertIn("shaders/gbuffers_terrain.fsh", names)
                self.assertIn("shaders/lib/settings.glsl", names)


if __name__ == "__main__":
    unittest.main()
