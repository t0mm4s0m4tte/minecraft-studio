"""
Script di validazione per texture LabPBR 1.3 - Aetheria LabPBR 32x.
Verifica:
1. Dimensioni: esattamente 32x32 pixel (o multiplo di animazione 32x32N, eccezione 64x per fluidi a scorrimento 32x vanilla)
2. Normal map (_n.png): RGBA (R=NormalX, G=NormalY, B=AO, A=Height)
3. Specular map (_s.png): RGBA (R=Smoothness, G=Metalness/F0, B=Porosity/SSS, A=Emissive <= 254)
4. Assenza di canali non conformi o deviazioni LabPBR 1.3
5. Supporto flag --strict, --subset e --all
"""

import os
import sys
import json
import struct
import zlib
import argparse

def read_png_dimensions_and_mode(filepath):
    """Legge header PNG nativo senza dipendenze esterne."""
    try:
        with open(filepath, "rb") as f:
            header = f.read(8)
            if header != b"\x89PNG\r\n\x1a\n":
                return None, "Not a valid PNG file"
            
            ihdr = f.read(25)
            length, chunk_type = struct.unpack(">I4s", ihdr[:8])
            if chunk_type != b"IHDR":
                return None, "Missing IHDR chunk"
                
            width, height, bit_depth, color_type = struct.unpack(">IIBB", ihdr[8:18])
            # Color type: 6 = RGBA, 2 = RGB, 4 = Gray+Alpha, 0 = Grayscale
            return {
                "width": width,
                "height": height,
                "bit_depth": bit_depth,
                "color_type": color_type,
                "is_rgba": (color_type == 6 and bit_depth == 8)
            }, None
    except Exception as e:
        return None, str(e)

def decode_png_pixels(filepath):
    """Decodifica i pixel RGBA di una PNG 8-bit non interlacciata per controlli LabPBR approfonditi."""
    try:
        with open(filepath, "rb") as f:
            header = f.read(8)
            if header != b"\x89PNG\r\n\x1a\n":
                return None, "Invalid PNG header"
            
            idat_data = bytearray()
            width, height = 0, 0
            
            while True:
                chunk_len_bytes = f.read(4)
                if not chunk_len_bytes or len(chunk_len_bytes) < 4:
                    break
                chunk_len = struct.unpack(">I", chunk_len_bytes)[0]
                chunk_type = f.read(4)
                chunk_data = f.read(chunk_len)
                f.read(4) # CRC
                
                if chunk_type == b"IHDR":
                    width, height, bit_depth, color_type = struct.unpack(">IIBB", chunk_data[:10])
                    if color_type != 6 or bit_depth != 8:
                        return None, f"Not 8-bit RGBA (color_type={color_type}, depth={bit_depth})"
                elif chunk_type == b"IDAT":
                    idat_data.extend(chunk_data)
                elif chunk_type == b"IEND":
                    break
            
            decompressed = zlib.decompress(bytes(idat_data))
            stride = width * 4
            pixels = []
            prev_row = bytearray(stride)
            offset = 0
            
            for y in range(height):
                filter_type = decompressed[offset]
                offset += 1
                row_raw = bytearray(decompressed[offset:offset+stride])
                offset += stride
                row = bytearray(stride)
                
                if filter_type == 0: # None
                    row = row_raw
                elif filter_type == 1: # Sub
                    for i in range(stride):
                        left = row[i - 4] if i >= 4 else 0
                        row[i] = (row_raw[i] + left) & 0xff
                elif filter_type == 2: # Up
                    for i in range(stride):
                        up = prev_row[i]
                        row[i] = (row_raw[i] + up) & 0xff
                elif filter_type == 3: # Average
                    for i in range(stride):
                        left = row[i - 4] if i >= 4 else 0
                        up = prev_row[i]
                        row[i] = (row_raw[i] + ((left + up) >> 1)) & 0xff
                elif filter_type == 4: # Paeth
                    for i in range(stride):
                        a = row[i - 4] if i >= 4 else 0
                        b = prev_row[i]
                        c = prev_row[i - 4] if i >= 4 else 0
                        p = a + b - c
                        pa = abs(p - a)
                        pb = abs(p - b)
                        pc = abs(p - c)
                        pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                        row[i] = (row_raw[i] + pr) & 0xff
                else:
                    return None, f"Unsupported filter type {filter_type}"
                
                prev_row = row
                for x in range(width):
                    px = (row[x*4], row[x*4+1], row[x*4+2], row[x*4+3])
                    pixels.append(px)
                    
            return pixels, None
    except Exception as e:
        return None, f"Decode error: {e}"

def validate_texture_set(block_name, textures_dir, strict_labpbr=False):
    errors = []
    warnings = []
    
    base_file = os.path.join(textures_dir, f"{block_name}.png")
    normal_file = os.path.join(textures_dir, f"{block_name}_n.png")
    spec_file = os.path.join(textures_dir, f"{block_name}_s.png")
    
    expected_width = 64 if block_name in ("lava_flow", "water_flow") else 32
    unit_height = 32

    for fpath, map_type in [(base_file, "Albedo"), (normal_file, "Normal (_n)"), (spec_file, "Specular (_s)")]:
        if not os.path.exists(fpath):
            errors.append(f"Manca file {map_type}: {os.path.basename(fpath)}")
            continue
            
        meta, err = read_png_dimensions_and_mode(fpath)
        if err:
            errors.append(f"Errore lettura {fpath}: {err}")
            continue
            
        if meta["width"] != expected_width:
            errors.append(f"Larghezza non conforme per {os.path.basename(fpath)}: {meta['width']}px (atteso {expected_width}px)")
            
        if meta["height"] % unit_height != 0:
            errors.append(f"Altezza non conforme per {os.path.basename(fpath)}: {meta['height']}px (atteso multiplo di {unit_height}px)")
            
        if not meta["is_rgba"]:
            errors.append(f"{os.path.basename(fpath)} deve essere salvato in formato RGBA a 8-bit (trovato color_type={meta['color_type']})")

    # Controlli specifici LabPBR 1.3 se strict_labpbr è attivo e i file esistono
    if strict_labpbr and os.path.exists(spec_file):
        pixels, err = decode_png_pixels(spec_file)
        if err:
            errors.append(f"Errore analisi pixel {os.path.basename(spec_file)}: {err}")
        else:
            # Controllo emissività: canale A <= 254 (255 è riservato/invalido in LabPBR 1.3)
            invalid_emissive = [p[3] for p in pixels if p[3] == 255]
            if invalid_emissive:
                errors.append(f"{os.path.basename(spec_file)}: canale Alpha (emissivo) ha valori 255 (LabPBR 1.3 richiede 0..254)")

    return errors, warnings

def check_texture_properties(root_dir):
    """Verifica presenza e contenuto di format=lab-pbr nei percorsi ufficiali."""
    errors = []
    candidates = [
        os.path.join(root_dir, "assets", "minecraft", "textures", "texture.properties"),
        os.path.join(root_dir, "assets", "minecraft", "textures", "block", "texture.properties"),
    ]
    for path in candidates:
        if not os.path.isfile(path):
            errors.append(f"File texture.properties mancante in {path}")
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if "format=lab-pbr" not in content.replace(" ", ""):
                errors.append(f"Contenuto 'format=lab-pbr' non trovato in {path}")
        except Exception as e:
            errors.append(f"Errore lettura {path}: {e}")
    return errors

def check_pack_json_files(root_dir):
    """Verifica pack.mcmeta e la sintassi JSON dei blockstates anti-tiling."""
    errors = []
    pack_mcmeta_path = os.path.join(root_dir, "pack.mcmeta")
    if not os.path.isfile(pack_mcmeta_path):
        errors.append("pack.mcmeta mancante")
    else:
        try:
            with open(pack_mcmeta_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            if not isinstance(data, dict) or "pack" not in data:
                errors.append("pack.mcmeta non contiene la chiave 'pack'")
        except Exception as e:
            errors.append(f"Errore parsing pack.mcmeta: {e}")

    blockstates_dir = os.path.join(root_dir, "assets", "minecraft", "blockstates")
    if os.path.isdir(blockstates_dir):
        for fname in sorted(os.listdir(blockstates_dir)):
            if fname.endswith(".json"):
                fpath = os.path.join(blockstates_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8-sig") as f:
                        bs_data = json.load(f)
                    if not isinstance(bs_data, dict) or ("variants" not in bs_data and "multipart" not in bs_data):
                        errors.append(f"Blockstate {fname} privo di 'variants' o 'multipart'")
                except Exception as e:
                    errors.append(f"Errore parsing blockstate {fname}: {e}")
    return errors

def collect_base_names(target_dir):
    if not os.path.isdir(target_dir):
        return []
    names = set()
    for fname in os.listdir(target_dir):
        if fname.endswith(".png") and not fname.endswith("_n.png") and not fname.endswith("_s.png"):
            names.add(fname[:-4])
    return sorted(names)

def main():
    parser = argparse.ArgumentParser(description="Aetheria LabPBR 1.3 Texture Validator")
    parser.add_argument("--strict", action="store_true", help="Fallisce con exit code 1 se una texture del subset manca o non è conforme")
    parser.add_argument("--subset", type=str, default=None, help="Lista di blocchi separati da virgola o percorso file con la lista dei blocchi")
    parser.add_argument("--all", action="store_true", help="Scansiona tutte le texture (blocchi e item) del resource pack")
    args = parser.parse_args()

    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    manifest_path = os.path.join(root_dir, "mvp-60-blocks.json")
    block_dir = os.path.join(root_dir, "assets", "minecraft", "textures", "block")
    item_dir = os.path.join(root_dir, "assets", "minecraft", "textures", "item")

    print(f"==================================================")
    print(f" AETHERIA LABPBR 1.3 VALIDATOR - MC 1.21.1        ")
    print(f" Modalità Strict: {'ATTIVA' if args.strict else 'DISATTIVATA'}")
    print(f" Modalità All Assets: {'ATTIVA' if args.all else 'DISATTIVATA'}")
    print(f" Directory root pack: {root_dir}")
    print(f"==================================================")

    # 1. Verifica texture.properties
    prop_errors = check_texture_properties(root_dir)
    for p_err in prop_errors:
        print(f" [FAIL-PROP] {p_err}")

    # 2. Verifica pack.mcmeta e blockstates JSON
    json_errors = check_pack_json_files(root_dir)
    for j_err in json_errors:
        print(f" [FAIL-JSON] {j_err}")

    targets = [] # Tuple di (nome, directory, categoria)
    if args.all:
        for b in collect_base_names(block_dir):
            targets.append((b, block_dir, "block"))
        for it in collect_base_names(item_dir):
            targets.append((it, item_dir, "item"))
    elif args.subset:
        if os.path.exists(args.subset):
            with open(args.subset, "r", encoding="utf-8") as f:
                target_blocks = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        else:
            target_blocks = [b.strip() for b in args.subset.split(",") if b.strip()]
        for b in target_blocks:
            targets.append((b, block_dir, "block"))
    else:
        if not os.path.exists(manifest_path):
            print(f"[FATAL] Manifest non trovato: {manifest_path}")
            sys.exit(1)
            
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            
        target_blocks = []
        for cat, blocks in manifest["categories"].items():
            target_blocks.extend(blocks)
        for b in target_blocks:
            targets.append((b, block_dir, "block"))
        
    print(f" Totale asset in esame: {len(targets)}")
    
    failed_count = 0
    valid_count = 0
    
    for name, directory, kind in targets:
        errs, warns = validate_texture_set(name, directory, strict_labpbr=args.strict)
        if errs:
            failed_count += 1
            print(f" [FAIL] [{kind}] {name}: {'; '.join(errs)}")
        else:
            valid_count += 1
            if not args.all:
                print(f" [PASS] {name} (Albedo, _n, _s OK)")
            
    if args.all:
        print(f" [PASS-ALL] Validate con successo {valid_count} texture set (blocchi + item).")

    total_failures = failed_count + len(prop_errors) + len(json_errors)
    print(f"\nEsito Validazione:")
    print(f"- Conclusi e conformi: {valid_count}/{len(targets)}")
    print(f"- Non conformi / Mancanti: {failed_count}/{len(targets)}")
    print(f"- Errori configurazione texture.properties: {len(prop_errors)}")
    print(f"- Errori JSON pack.mcmeta/blockstates: {len(json_errors)}")
    
    if args.strict and total_failures > 0:
        print("\n[STRICT CHECK FAILED] Alcune texture o configurazioni non rispettano i requisiti LabPBR 1.3.")
        sys.exit(1)
        
    sys.exit(0)

if __name__ == "__main__":
    main()
