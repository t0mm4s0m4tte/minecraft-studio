"""
Script di validazione per texture LabPBR 1.3 - Aetheria LabPBR 32x.
Verifica:
1. Dimensioni: esattamente 32x32 pixel (o multiplo di animazione 32x32N)
2. Normal map (_n.png): RGBA (R=NormalX, G=NormalY, B=AO, A=Height)
3. Specular map (_s.png): RGBA (R=Smoothness, G=Metalness/F0, B=Porosity/SSS, A=Emissive <= 254)
4. Assenza di canali non conformi o deviazioni LabPBR 1.3
5. Supporto flag --strict (exit code 1 se errori) e --subset <lista_o_file>
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
    
    for fpath, map_type in [(base_file, "Albedo"), (normal_file, "Normal (_n)"), (spec_file, "Specular (_s)")]:
        if not os.path.exists(fpath):
            errors.append(f"Manca file {map_type}: {os.path.basename(fpath)}")
            continue
            
        meta, err = read_png_dimensions_and_mode(fpath)
        if err:
            errors.append(f"Errore lettura {fpath}: {err}")
            continue
            
        if meta["width"] != 32:
            errors.append(f"Larghezza non conforme per {os.path.basename(fpath)}: {meta['width']}px (atteso 32px)")
            
        if meta["height"] % 32 != 0:
            errors.append(f"Altezza non conforme per {os.path.basename(fpath)}: {meta['height']}px (atteso multiplo di 32px)")
            
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

def main():
    parser = argparse.ArgumentParser(description="Aetheria LabPBR 1.3 Texture Validator")
    parser.add_argument("--strict", action="store_true", help="Fallisce con exit code 1 se una texture del subset manca o non è conforme")
    parser.add_argument("--subset", type=str, default=None, help="Lista di blocchi separati da virgola o percorso file con la lista dei blocchi")
    args = parser.parse_args()

    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    manifest_path = os.path.join(root_dir, "mvp-60-blocks.json")
    textures_dir = os.path.join(root_dir, "assets", "minecraft", "textures", "block")
    
    if args.subset:
        if os.path.exists(args.subset):
            with open(args.subset, "r", encoding="utf-8") as f:
                target_blocks = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        else:
            target_blocks = [b.strip() for b in args.subset.split(",") if b.strip()]
    else:
        if not os.path.exists(manifest_path):
            print(f"[FATAL] Manifest non trovato: {manifest_path}")
            sys.exit(1)
            
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            
        target_blocks = []
        for cat, blocks in manifest["categories"].items():
            target_blocks.extend(blocks)
        
    print(f"==================================================")
    print(f" AETHERIA LABPBR 1.3 VALIDATOR - MC 1.21.1        ")
    print(f" Modalità Strict: {'ATTIVA' if args.strict else 'DISATTIVATA'}")
    print(f" Totale blocchi in esame: {len(target_blocks)}")
    print(f" Directory texture: {textures_dir}")
    print(f"==================================================")
    
    failed_count = 0
    valid_count = 0
    
    for block in target_blocks:
        errs, warns = validate_texture_set(block, textures_dir, strict_labpbr=args.strict)
        if errs:
            failed_count += 1
            print(f" [FAIL] {block}: {'; '.join(errs)}")
        else:
            valid_count += 1
            print(f" [PASS] {block} (Albedo, _n, _s OK)")
            
    print(f"\nEsito Validazione:")
    print(f"- Conclusi e conformi: {valid_count}/{len(target_blocks)}")
    print(f"- Non conformi / Mancanti: {failed_count}/{len(target_blocks)}")
    
    if args.strict and failed_count > 0:
        print("\n[STRICT CHECK FAILED] Alcune texture non rispettano i requisiti LabPBR 1.3.")
        sys.exit(1)
        
    sys.exit(0)

if __name__ == "__main__":
    main()
