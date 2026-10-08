"""
pipeline_support.py - Pipeline automatizado de extremo a extremo para Soportes en Plant 3D 2027.

Ejecuta en un solo paso:
1. build.py: Aplana iteco_b3s_standard_ubolt.py hacia CPak Common\\CustomScripts.
2. build_support_catalog.py: Construye ITECO_B3S_Supports_Catalog.acat (29 tamaños).
3. build_support_spec.py: Inyecta los 29 tamaños en PipeSupportsSpec.pspc.
"""
import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def main():
    print("=" * 65)
    print(" PIPELINE COMPLETO DE SOPORTES CUSTOM: CATALOG -> SPEC")
    print("=" * 65)

    # 1. Aplanar scripts Python a CustomScripts
    print("\n[Paso 1/3] Aplanando modelos hacia CPak Common\\CustomScripts...")
    res = subprocess.run([sys.executable, str(REPO_ROOT / "builders" / "build.py")], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[X] Fallo en build.py:\n{res.stderr}")
        sys.exit(1)
    print("    [OK] Modelos aplanados y sincronizados.")

    # 2. Generar Catálogo .acat
    print("\n[Paso 2/3] Generando Catálogo de Soportes (.acat)...")
    spec_json = REPO_ROOT.parent / "catalog-scrap" / "output" / "specifications" / "ITECO_B3S.json"
    cat_script = REPO_ROOT / "builders" / "build_support_catalog.py"
    res = subprocess.run([sys.executable, str(cat_script), "--spec-json", str(spec_json)], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[X] Fallo en build_support_catalog.py:\n{res.stderr}")
        sys.exit(1)
    print("    [OK] ITECO_B3S_Supports_Catalog.acat generado con 29 tamaños.")

    # 3. Generar / Inyectar en Spec .pspc
    print("\n[Paso 3/3] Incorporando tamaños a la Spec de Soportes (.pspc)...")
    spec_script = REPO_ROOT / "builders" / "build_support_spec.py"
    res = subprocess.run([sys.executable, str(spec_script)], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[X] Fallo en build_support_spec.py:\n{res.stderr}")
        sys.exit(1)
    print("    [OK] 29 tamaños incorporados a PipeSupportsSpec.pspc.")

    print("\n" + "=" * 65)
    print(" [LISTO] El Catálogo y la Spec están 100% operativos en Plant 3D!")
    print("=" * 65)

if __name__ == "__main__":
    main()
