"""
Impacchettamento automatizzato del Trittico minecraft-studio per distribuzione
su Modrinth, CurseForge e installazione manuale in Minecraft 1.21.1.
"""

import argparse
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
    version: str = "1.8.0",
    skip_gradle: bool = False,
    skip_validate: bool = False,
) -> dict:
    """Valida asset, compila i loader (se richiesto) e genera i pacchetti release in output_dir."""
    root = Path(root_dir).resolve()
    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

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

    return artifacts


def main():
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Genera archivi release per minecraft-studio")
    parser.add_argument("--output-dir", default=str(repo_root / "dist"), help="Cartella output artefatti")
    parser.add_argument("--version", default="1.8.0", help="Versione pacchetti release")
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
