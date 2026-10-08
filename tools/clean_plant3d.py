"""
clean_plant3d.py - Limpieza integral de AutoCAD Plant 3D 2027.

Restaura el entorno oficial de Plant 3D a su estado original de fábrica (limpio):
1. Limpia válvulas personalizadas de CS150.pspc (en CPak ASME y en DefaultProject).
2. Limpia soportes U-Bolt de PipeSupportsSpec.pspc (en CPak Common y en DefaultProject).
3. Elimina especificaciones temporales (CS150_Soportes, ITECO_B3S_PipeSupports).
4. Vacía la carpeta CustomScripts (eliminando .py, .xml, .pcat, .acat, variants.*, __pycache__).
5. Elimina los catálogos del proyecto de CPak Common.
6. Elimina la carpeta extraída dist/Plant3D_Distribution_Bundle (manteniendo el ZIP).
7. Elimina dibujos de prueba en Plant_3D_Models.
"""

import shutil
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = Path(r"C:\AutoCAD Plant 3D 2027 Content")
PROJECT_DIR = Path(
    r"C:\Users\ynoacamino\AppData\Roaming\Autodesk\Autodesk AutoCAD Plant 3D 2027\R26.0\enu\DefaultProject"
)
PROJECT_SPECS_DIR = PROJECT_DIR / "SpecSheets"
PROJECT_MODELS_DIR = PROJECT_DIR / "Plant_3D_Models"

CUSTOM_SCRIPTS_DIR = CONTENT_DIR / "CPak Common" / "CustomScripts"
CPAK_COMMON_DIR = CONTENT_DIR / "CPak Common"
CPAK_ASME_DIR = CONTENT_DIR / "CPak ASME"
DIST_EXTRACTED_DIR = REPO_ROOT / "dist" / "Plant3D_Distribution_Bundle"


def clean_custom_valves_from_spec(spec_path: Path):
    if not spec_path.exists():
        return
    conn = sqlite3.connect(spec_path)
    cur = conn.cursor()
    templates = (
        "INTEC_K200_BALL_VALVE",
        "BALL_VALVE_2PC_FLANGED",
        "BALL_VALVE_1PC_COMPACT",
        "BALL_VALVE_3PC_THREADED",
        "BALL_VALVE_HANDWHEEL",
    )
    placeholders = ",".join("?" * len(templates))
    cur.execute(f"SELECT PnPID FROM EngineeringItems WHERE ContentGeometryTemplate IN ({placeholders})", templates)
    ids = [r[0] for r in cur.fetchall()]
    if ids:
        print(f"[LIMPIAR] Eliminando {len(ids)} valvulas de {spec_path.name}...")
        for vid in ids:
            cur.execute("SELECT Port FROM PartPort WHERE Part = ?", (vid,))
            ports = [r[0] for r in cur.fetchall()]
            for pid in ports:
                cur.execute("DELETE FROM Port WHERE PnPID = ?", (pid,))
                cur.execute("DELETE FROM PnPBase WHERE PnPID = ?", (pid,))
            cur.execute("DELETE FROM PartPort WHERE Part = ?", (vid,))
            cur.execute("DELETE FROM Valve WHERE PnPID = ?", (vid,))
            cur.execute("DELETE FROM PipeRunComponent WHERE PnPID = ?", (vid,))
            cur.execute("DELETE FROM EngineeringItems WHERE PnPID = ?", (vid,))
            cur.execute("DELETE FROM PnPBase WHERE PnPID = ?", (vid,))
        conn.commit()
    conn.close()


def clean_custom_supports_from_spec(spec_path: Path):
    if not spec_path.exists():
        return
    conn = sqlite3.connect(spec_path)
    cur = conn.cursor()
    cur.execute("SELECT PnPID FROM EngineeringItems WHERE ContentGeometryTemplate = 'UBOLT_STANDARD'")
    ids = [r[0] for r in cur.fetchall()]
    if ids:
        print(f"[LIMPIAR] Eliminando {len(ids)} soportes U-Bolt de {spec_path.name}...")
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in cur.fetchall()}
        for sid in ids:
            if "PartPort" in tables:
                cur.execute("SELECT Port FROM PartPort WHERE Part = ?", (sid,))
                ports = [r[0] for r in cur.fetchall()]
                for pid in ports:
                    if "Port" in tables:
                        cur.execute("DELETE FROM Port WHERE PnPID = ?", (pid,))
                    cur.execute("DELETE FROM PnPBase WHERE PnPID = ?", (pid,))
                cur.execute("DELETE FROM PartPort WHERE Part = ?", (sid,))
            for tbl in ["Support", "PipeSupport", "PipeRunComponent", "EngineeringItems", "PnPBase"]:
                if tbl in tables:
                    cur.execute(f"DELETE FROM {tbl} WHERE PnPID = ?", (sid,))
        conn.commit()
    conn.close()


def remove_file_or_pattern(directory: Path, pattern: str):
    if not directory.exists():
        return
    for item in directory.glob(pattern):
        if item.is_file():
            print(f"[ELIMINAR] Archivo: {item.name} de {directory.name}")
            item.unlink()
        elif item.is_dir():
            print(f"[ELIMINAR] Carpeta: {item.name} de {directory.name}")
            shutil.rmtree(item, ignore_errors=True)


def main():
    print("=" * 70)
    print(" LIMPIEZA INTEGRAL DE AUTOCAD PLANT 3D 2027")
    print("=" * 70)

    # 1. Limpiar válvulas y soportes de specs nativas
    print("\n1. Limpiando specs estandar (CS150 y PipeSupportsSpec)...")
    clean_custom_valves_from_spec(CPAK_ASME_DIR / "CS150.pspc")
    clean_custom_valves_from_spec(PROJECT_SPECS_DIR / "CS150.pspc")
    clean_custom_supports_from_spec(CPAK_COMMON_DIR / "PipeSupportsSpec.pspc")
    clean_custom_supports_from_spec(PROJECT_SPECS_DIR / "PipeSupportsSpec.pspc")

    # 2. Eliminar especificaciones personalizadas o temporales
    print("\n2. Eliminando especificaciones personalizadas (CS150_Soportes, ITECO)...")
    for d in [CPAK_ASME_DIR, CPAK_COMMON_DIR, PROJECT_SPECS_DIR]:
        remove_file_or_pattern(d, "CS150_Soportes.*")
        remove_file_or_pattern(d, "ITECO_B3S_PipeSupports.*")
        remove_file_or_pattern(d, "*.pspc.bak")

    # 3. Eliminar catálogos del proyecto en CPak Common
    print("\n3. Eliminando catalogos de proyecto en CPak Common...")
    for cat_name in [
        "KLINGER_Schoneberg_INTEC_K200_Catalog.pcat",
        "Catalogo_Val_Bola_2016-44_Catalog.pcat",
        "ITECO_B3S_Supports_Catalog.acat",
    ]:
        f = CPAK_COMMON_DIR / cat_name
        if f.exists():
            print(f"[ELIMINAR] Catalogo: {f.name}")
            f.unlink()

    # 4. Limpiar completamente CustomScripts
    print("\n4. Limpiando CustomScripts...")
    if CUSTOM_SCRIPTS_DIR.exists():
        for item in CUSTOM_SCRIPTS_DIR.iterdir():
            if item.name == "ErrorReports":
                continue  # Dejar la carpeta de error de Autodesk
            if item.is_file():
                print(f"[ELIMINAR] Script/Metadato: {item.name}")
                item.unlink()
            elif item.is_dir():
                print(f"[ELIMINAR] Subdirectorio: {item.name}")
                shutil.rmtree(item, ignore_errors=True)

    # 5. Eliminar carpeta extraída del bundle
    print("\n5. Limpiando carpeta extraida de distribucion (manteniendo ZIP)...")
    if DIST_EXTRACTED_DIR.exists():
        print(f"[ELIMINAR] Carpeta extraida: {DIST_EXTRACTED_DIR.name}")
        shutil.rmtree(DIST_EXTRACTED_DIR, ignore_errors=True)

    # 6. Limpiar dibujos de prueba
    print("\n6. Limpiando dibujos de prueba...")
    for dwg_name in ["Drawing1.dwg", "Drawing1.bak"]:
        dwg = PROJECT_MODELS_DIR / dwg_name
        if dwg.exists():
            print(f"[ELIMINAR] Dibujo: {dwg.name}")
            dwg.unlink()

    print("\n" + "=" * 70)
    print(" [OK] ENTORNO 100% LIMPIO Y LISTO PARA GRABAR EL VIDEO DESDE CERO.")
    print("=" * 70)


if __name__ == "__main__":
    main()
