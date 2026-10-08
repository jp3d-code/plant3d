"""
generate_all_sizes_test.py - Genera el script AutoLISP tools/test_all_sizes.lsp
con los 29 tamaños exactos extraídos del catálogo ITECO_B3S_Supports_Catalog.acat.
"""
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ACAT_PATH = Path(r"C:\AutoCAD Plant 3D 2027 Content\CPak Common\CustomScripts\ITECO_B3S_Supports_Catalog.acat")
OUTPUT_LSP = REPO_ROOT / "tools" / "test_all_sizes.lsp"

def main():
    if not ACAT_PATH.exists():
        print(f"Error: No se encontró {ACAT_PATH}")
        return

    conn = sqlite3.connect(ACAT_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT NominalDiameter, MatchingPipeOd, PartSizeLongDesc, ContentGeometryParamDefinition
        FROM EngineeringItems
        ORDER BY NominalDiameter ASC;
    """)
    rows = cur.fetchall()
    conn.close()

    lines = [
        ";;; =========================================================================",
        ";;; AutoLISP Batch Runner: Instanciar TODOS los 29 tamaños de UBOLT_STANDARD",
        ";;; Arrastra este archivo al dibujo de AutoCAD o teclea: TESTALLSIZES",
        ";;; =========================================================================",
        "",
        "(defun c:TESTALLSIZES ( / ent xOffset spacing nd od)",
        "  (vl-load-com)",
        '  (princ "\\n[+] Cargando PnP3dACPAdapter...")',
        '  (arxload "PnP3dACPAdapter")',
        '  (princ "\\n[+] Registrando CustomScripts...")',
        '  (vl-cmdf "PLANTREGISTERCUSTOMSCRIPTS")',
        "  ",
        "  (setq xOffset 0.0)",
        '  (princ "\\n[+] Insertando 29 tamaños en fila ordenada...")',
        ""
    ]

    for nd, od, desc, pdef in rows:
        pdict = dict(item.split("=") for item in pdef.split(",") if "=" in item)
        # Espaciado proporcional al OD exterior de la tubería
        spacing = round(max(float(od) * 1.8 + 4.0, 8.0), 2)
        args_str = " ".join(f'"{k}" "{v}"' for k, v in pdict.items())

        lines.append(f'  ;; Talla ND {nd}" (OD={od}")')
        lines.append(f'  (testacpscript "UBOLT_STANDARD" {args_str})')
        lines.append("  (setq ent (entlast))")
        lines.append('  (if ent (vl-cmdf "_.move" ent "" \'(0 0 0) (list xOffset 0 0)))')
        lines.append(f"  (setq xOffset (+ xOffset {spacing}))")
        lines.append("")

    lines.extend([
        '  (princ "\\n[+] Configurando cámara y vista isométrica...")',
        '  (command "_.zoom" "_e")',
        '  (command "_.vscurrent" "_c")',
        '  (command "_.-view" "_swiso")',
        '  (command "_.zoom" "_e")',
        f'  (princ "\\n[OK] {len(rows)} abrazaderas UBOLT_STANDARD instanciadas exitosamente!\\n")',
        "  (princ)",
        ")",
        "",
        "(c:TESTALLSIZES)"
    ])

    OUTPUT_LSP.write_text("\n".join(lines), encoding="utf-8")
    print(f"[+] Generado exitosamente: {OUTPUT_LSP} con {len(rows)} tamaños.")

if __name__ == "__main__":
    main()
