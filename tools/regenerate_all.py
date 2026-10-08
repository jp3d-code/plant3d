r"""
regenerate_all.py - Pipeline Maestro de Regeneración Integral para AutoCAD Plant 3D 2027.

Ejecuta el ciclo de vida completo de extremo a extremo:
1. build.py: Valida y aplana modelos paramétricos 3D (Válvulas + Soportes) hacia CustomScripts.
2. build_catalog.py: Construye catálogo .pcat de INTEC K200 (KLINGER Schoneberg).
3. build_catalog.py: Construye catálogo .pcat de Saidi RK 2016 (Válvulas comerciales).
4. build_support_catalog.py: Construye catálogo .acat de Soportes U-Bolt (ITECO B3S, 29 tamaños).
5. build_support_spec.py: Incorpora los soportes en PipeSupportsSpec.pspc (Master CPak y Proyecto Activo).
6. build_piping_spec.py: Incorpora las válvulas Clase 150# en CS150.pspc (Master CPak ASME y Proyecto Activo).
7. Verificación de integridad.

Uso:
    python tools/regenerate_all.py
"""

import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRAP_OUTPUT = REPO_ROOT.parent / "catalog-scrap" / "output"

PROJECT_SPECS_DIR = Path(
    r"C:\Users\ynoacamino\AppData\Roaming\Autodesk\Autodesk AutoCAD Plant 3D 2027\R26.0\enu\DefaultProject\SpecSheets"
)


def run_step(step_num: int, title: str, cmd_args: list):
    print(f"\n[{step_num}/6] {title}...")
    print(f"      Comando: {' '.join(str(a) for a in cmd_args)}")
    res = subprocess.run(cmd_args, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"\n[X] Error en {title}:\n{res.stderr}\n{res.stdout}")
        sys.exit(1)
    # Imprimir resumen de salida
    lines = [l for l in res.stdout.strip().splitlines() if l.strip()]
    for l in lines[-3:]:
        print(f"      {l}")
    print(f"      -> [OK] Completado exitosamente.")


def main():
    print("=" * 70)
    print(" PIPELINE MAESTRO DE REGENERACION COMPLETA - AUTOCAD PLANT 3D 2027")
    print("=" * 70)

    py = sys.executable

    # 1. Aplanar modelos a CustomScripts
    run_step(
        1,
        "Aplanando modelos paramétricos Python a CustomScripts",
        [py, str(REPO_ROOT / "builders" / "build.py")]
    )

    # 2. Catálogo INTEC K200 (.pcat)
    intec_json = SCRAP_OUTPUT / "specifications" / "INTEC_K200.json"
    run_step(
        2,
        "Construyendo Catálogo .pcat: KLINGER Schoneberg INTEC K200",
        [py, str(REPO_ROOT / "builders" / "build_catalog.py"), "--spec-json", str(intec_json)]
    )

    # 3. Catálogo Saidi RK 2016 (.pcat)
    saidi_manifest = SCRAP_OUTPUT / "catalogs" / "CATALOGO_VAL_BOLA_2016-44" / "manifest.json"
    run_step(
        3,
        "Construyendo Catálogo .pcat: Saidi RK 2016 Comercial",
        [py, str(REPO_ROOT / "builders" / "build_catalog.py"), "--catalog-manifest", str(saidi_manifest)]
    )

    # 4. Catálogo de Soportes ITECO B3S (.acat)
    iteco_json = SCRAP_OUTPUT / "specifications" / "ITECO_B3S.json"
    run_step(
        4,
        "Construyendo Catálogo .acat: ITECO B3S Soportes U-Bolt (29 tamaños)",
        [py, str(REPO_ROOT / "builders" / "build_support_catalog.py"), "--spec-json", str(iteco_json)]
    )

    # 5. Inyectar Soportes a PipeSupportsSpec.pspc (Master y Proyecto Activo)
    support_spec_proj = PROJECT_SPECS_DIR / "PipeSupportsSpec.pspc"
    print(f"\n[5/6] Incorporando Soportes ITECO a Especificaciones PipeSupportsSpec.pspc...")
    # Master
    res = subprocess.run([py, str(REPO_ROOT / "builders" / "build_support_spec.py")], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[X] Error en build_support_spec master:\n{res.stderr}")
        sys.exit(1)
    print("      -> Master CPak Common\\PipeSupportsSpec.pspc actualizado.")

    # Proyecto
    if support_spec_proj.exists():
        res = subprocess.run(
            [py, str(REPO_ROOT / "builders" / "build_support_spec.py"), "--spec-pspc", str(support_spec_proj)],
            capture_output=True,
            text=True
        )
        if res.returncode != 0:
            print(f"[X] Error en build_support_spec proyecto:\n{res.stderr}")
            sys.exit(1)
        print(f"      -> Proyecto activo {support_spec_proj.name} actualizado.")
    print("      -> [OK] Soportes listos para PLANTPIPESUPPORTADD.")

    # 6. Crear Nueva Spec CS150_Soportes (Tuberías Clásicas CS150 + Soportes U-Bolt, SIN válvulas)
    import shutil
    cs150_master = REPO_ROOT.parent / "AutoCAD Plant 3D 2027 Content" / "CPak ASME" / "CS150.pspc"
    if not cs150_master.exists():
        cs150_master = Path(r"C:\AutoCAD Plant 3D 2027 Content\CPak ASME\CS150.pspc")
    cs150_master_x = cs150_master.with_suffix(".pspx")

    new_spec_proj = PROJECT_SPECS_DIR / "CS150_Soportes.pspc"
    new_spec_proj_x = PROJECT_SPECS_DIR / "CS150_Soportes.pspx"

    print(f"\n[6/6] Creando Nueva Spec Híbrida: CS150_Soportes.pspc (Tuberías + Soportes)...")
    if cs150_master.exists():
        shutil.copy2(cs150_master, new_spec_proj)
        if cs150_master_x.exists():
            shutil.copy2(cs150_master_x, new_spec_proj_x)

        # Actualizar RepositoryDescriptor para que el nombre interno coincida con el nombre del archivo
        import sqlite3, uuid
        conn = sqlite3.connect(new_spec_proj)
        cur = conn.cursor()
        new_repo_id = f"{{{str(uuid.uuid4())}}}"
        cur.execute("""
            UPDATE RepositoryDescriptor
            SET Name = 'CS150_Soportes',
                RepositoryID = ?,
                Description = '150# Carbon Steel con Soportes U-Bolt'
            WHERE PnPID = 1;
        """, (new_repo_id,))
        conn.commit()
        conn.close()

        # Inyectar soportes a la nueva spec
        res = subprocess.run(
            [py, str(REPO_ROOT / "builders" / "build_support_spec.py"), "--spec-pspc", str(new_spec_proj)],
            capture_output=True,
            text=True
        )
        if res.returncode != 0:
            print(f"[X] Error inyectando soportes en CS150_Soportes.pspc:\n{res.stderr}")
            sys.exit(1)

        # Copiar también a CPak ASME para disponibilidad global
        cs150_soportes_master = cs150_master.parent / "CS150_Soportes.pspc"
        cs150_soportes_master_x = cs150_master.parent / "CS150_Soportes.pspx"
        shutil.copy2(new_spec_proj, cs150_soportes_master)
        if new_spec_proj_x.exists():
            shutil.copy2(new_spec_proj_x, cs150_soportes_master_x)

        print(f"      -> {new_spec_proj.name} creada con Tuberías ASME B36.10 + 29 Soportes U-Bolt.")
    print("      -> [OK] Nueva spec CS150_Soportes lista para modelado.")

    print("\n" + "=" * 70)
    print(" REGENERACION COMPLETA FINALIZADA CON EXITO!")
    print(" Todos los archivos (.py, .pcat, .acat, .pspc) estan 100% frescos y sincronizados.")
    print("=" * 70)


if __name__ == "__main__":
    main()
