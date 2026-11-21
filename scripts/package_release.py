"""
Impacchettamento automatizzato del Trittico minecraft-studio per distribuzione
su Modrinth, CurseForge, GitHub Releases e installazione 1-click (.mrpack) in Minecraft 1.21.1.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


def _zip_selected(base_dir: Path, zip_path: Path, rel_paths):
    """Crea un archivio ZIP deterministico contenente i file/cartelle indicati."""
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel in rel_paths:
            target = base_dir / rel
            if not target.exists():
                raise FileNotFoundError(f"Percorso atteso mancante per archivio: {target}")
            if target.is_file():
                zf.write(target, arcname=Path(rel).as_posix())
            else:
                for file_path in sorted(p for p in target.rglob("*") if p.is_file()):
                    arcname = file_path.relative_to(base_dir).as_posix()
                    zf.write(file_path, arcname=arcname)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _build_mrpack(out_dir: Path, version: str, resource_zip: Path, shader_zip: Path, fabric_jar: Path | None) -> Path:
    """Genera il pacchetto Modrinth/Prism Launcher 1-click (.mrpack) con overrides completi."""
    mrpack_path = out_dir / f"Minecraft-Studio-Triptych-{version}.mrpack"
    index_data = {
        "formatVersion": 1,
        "game": "minecraft",
        "versionId": version,
        "name": "Minecraft Studio — Synergic Triptych",
        "summary": "Zero-click LabPBR 1.3 32x Resource Pack, Luminary Iris Shaders & Ambient Luminescence Dynamic Lights for MC 1.21.1.",
        "dependencies": {
            "minecraft": "1.21.1",
            "fabric-loader": ">=0.16.5",
        },
        "files": [],
    }
    with zipfile.ZipFile(mrpack_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.writestr("modrinth.index.json", json.dumps(index_data, indent=2) + "\n")
        zf.write(resource_zip, arcname=f"overrides/resourcepacks/{resource_zip.name}")
        zf.write(shader_zip, arcname=f"overrides/shaderpacks/{shader_zip.name}")
        if fabric_jar and fabric_jar.is_file():
            zf.write(fabric_jar, arcname=f"overrides/mods/{fabric_jar.name}")
    return mrpack_path


def _write_sha256sums(out_dir: Path) -> Path:
    """Scrive SHA256SUMS.txt per tutti gli artefatti binari presenti in out_dir."""
    checksum_path = out_dir / "SHA256SUMS.txt"
    targets = sorted(
        p for p in out_dir.iterdir()
        if p.is_file() and p.suffix in (".zip", ".jar", ".mrpack")
    )
    lines = [f"{_sha256_file(p)}  {p.name}" for p in targets]
    checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return checksum_path


def _find_java21_env():
    """Prepara env con JAVA_HOME su JDK 21 se disponibile localmente su Windows."""
    env = os.environ.copy()
    if env.get("JAVA_HOME") and "21" in env["JAVA_HOME"]:
        return env
    adoptium = Path(r"C:\Program Files\Eclipse Adoptium")
    if adoptium.is_dir():
        for jdk in sorted(adoptium.glob("jdk-21*"), reverse=True):
            if (jdk / "bin" / "java.exe").is_file():
                env["JAVA_HOME"] = str(jdk)
                env["PATH"] = f"{jdk / 'bin'}{os.pathsep}{env.get('PATH', '')}"
                break
    return env


def _run_step(cmd, cwd: Path, env=None):
    result = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Comando fallito ({result.returncode}): {' '.join(cmd)}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


def build_release(
    root_dir: Path,
    output_dir: Path,
    version: str = "2.2.0",
    skip_gradle: bool = False,
    skip_validate: bool = False,
) -> dict:
    """Valida asset, compila i loader (se richiesto) e genera i pacchetti release in output_dir."""
    root = Path(root_dir).resolve()
    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    for old_file in out.glob("*"):
        if old_file.is_file() and (
            (old_file.suffix in (".zip", ".jar", ".mrpack") and f"-{version}." not in old_file.name)
            or old_file.name == "SHA256SUMS.txt"
        ):
            old_file.unlink()

    pack_dir = root / "packs" / "aetheria-labpbr-32x"
    shader_dir = root / "shaders" / "luminary-shaders"
    mod_dir = root / "mods" / "ambient-luminescence"

    if not skip_validate:
        validator = pack_dir / "scripts" / "validate_labpbr.py"
        _run_step([sys.executable, str(validator), "--strict"], cwd=root)

    if not skip_gradle:
        gradle_exe = str(mod_dir / ("gradlew.bat" if os.name == "nt" else "gradlew"))
        _run_step([gradle_exe, "build", "--console=plain"], cwd=mod_dir, env=_find_java21_env())

    resource_zip = out / f"Aetheria-LabPBR-32x-{version}.zip"
    shader_zip = out / f"Luminary-Shaders-{version}.zip"

    pack_entries = ["pack.mcmeta", "assets"]
    if (pack_dir / "pack.png").is_file():
        pack_entries.insert(1, "pack.png")
    _zip_selected(pack_dir, resource_zip, pack_entries)
    _zip_selected(shader_dir, shader_zip, ["shaders"])

    artifacts = {
        "resource_pack": resource_zip,
        "shader_pack": shader_zip,
    }

    for loader in ("fabric", "neoforge"):
        libs_dir = mod_dir / loader / "build" / "libs"
        src_jar = libs_dir / f"{loader}-{version}.jar"
        if not src_jar.is_file() and skip_gradle and libs_dir.is_dir():
            candidates = sorted(libs_dir.glob(f"{loader}-*.jar"))
            if candidates:
                src_jar = candidates[-1]
        if src_jar.is_file():
            dst_jar = out / f"ambient_luminescence-{loader}-{version}.jar"
            shutil.copy2(src_jar, dst_jar)
            artifacts[f"mod_{loader}"] = dst_jar
        elif not skip_gradle:
            raise FileNotFoundError(f"JAR atteso non trovato dopo build Gradle: {src_jar}")

    mrpack_file = _build_mrpack(
        out_dir=out,
        version=version,
        resource_zip=resource_zip,
        shader_zip=shader_zip,
        fabric_jar=artifacts.get("mod_fabric"),
    )
    artifacts["mrpack_bundle"] = mrpack_file
    artifacts["sha256sums"] = _write_sha256sums(out)

    return artifacts


def main():
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Genera archivi release per minecraft-studio")
    parser.add_argument("--output-dir", default=str(repo_root / "dist"), help="Cartella output artefatti")
    parser.add_argument("--version", default="2.2.0", help="Versione pacchetti release")
    parser.add_argument("--skip-gradle", action="store_true", help="Salta la build Gradle e usa eventuali JAR gia presenti")
    parser.add_argument("--skip-validate", action="store_true", help="Salta validate_labpbr.py --strict")
    args = parser.parse_args()

    artifacts = build_release(
        root_dir=repo_root,
        output_dir=Path(args.output_dir),
        version=args.version,
        skip_gradle=args.skip_gradle,
        skip_validate=args.skip_validate,
    )
    for key, path in artifacts.items():
        print(f"[RELEASE] {key}: {path} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
