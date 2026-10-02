"""
export_bundle.py - Empaquetador automatizado de distribución para AutoCAD Plant 3D 2027.

Empaqueta en un archivo ZIP autocontenido:
1. CustomScripts/: Scripts Python aplanados (modelos y librerías) + ScriptGroup.xml.
2. Catalogs/: Catálogos generados de tuberías (.pcat) y de soportes (.acat).
3. LEEME_INSTALACION.txt: Guía paso a paso para instalación y uso en otra máquina.

Uso:
    python builders/export_bundle.py
    python builders/export_bundle.py --output dist/Plant3D_Bundle.zip
    python builders/export_bundle.py --catalog ITECO_B3S
"""

import os
import sys
import zipfile
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCRIPTS_DIR = Path(r"C:\AutoCAD Plant 3D 2027 Content\CPak Common\CustomScripts")
DEFAULT_DIST_DIR = REPO_ROOT / "dist"
DEFAULT_ZIP_NAME = "Plant3D_Distribution_Bundle.zip"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from builders.build import iter_components, get_lib_files, output_path, flatten


README_CONTENT = """========================================================================
PAQUETE DE DISTRIBUCION - COMPONENTES Y CATALOGOS AUTOCAD PLANT 3D 2027
========================================================================

Este paquete contiene los modelos paramétricos en Python y las bases de
datos de catálogos SQLite (.pcat y .acat) listos para su uso e importación.

CONTENIDO DEL PAQUETE:
----------------------
1. CustomScripts/
   - Scripts Python paramétricos (.py) de válvulas y soportes.
   - Librería utils.py con funciones geométricas auxiliares.
   - ScriptGroup.xml con el registro oficial de grupos y conexiones.

2. Catalogs/
   - Catálogos de tuberías / válvulas (.pcat):
     * KLINGER_Schoneberg_INTEC_K200_Catalog.pcat (Válvula INTEC K200 Clases 150# y 300#)
     * Catalogo_Val_Bola_2016-44_Catalog.pcat (Catálogo comercial de válvulas de bola)
   - Catálogos de soportes (.acat):
     * ITECO_B3S_Supports_Catalog.acat (Abrazadera U Standard con contratuercas)

------------------------------------------------------------------------
INSTRUCCIONES DE INSTALACION:
------------------------------------------------------------------------

PASO 1: INSTALAR SCRIPTS PYTHON
Copiar todos los archivos dentro de la carpeta "CustomScripts/" a la ruta
de contenido de AutoCAD Plant 3D 2027:
    C:\\AutoCAD Plant 3D 2027 Content\\CPak Common\\CustomScripts\\

PASO 2: REGISTRAR SCRIPTS EN PLANT 3D
Abrir AutoCAD Plant 3D 2027 y en la línea de comandos ejecutar:
    (arxload "PnP3dACPAdapter")
    PLANTREGISTERCUSTOMSCRIPTS

PASO 3: USO DE CATALOGOS (.pcat / .acat)
- Catálogos de Tubería (.pcat):
  Abrir con "AutoCAD Plant 3D Spec Editor" mediante:
  File -> Open Catalog -> Seleccionar archivo .pcat
  Desde allí puedes añadir las familias a tus specs de tubería (.pspc).

- Catálogos de Soporte (.acat):
  En el Spec Editor, abrir el catálogo de soportes (.acat) para
  incorporar las abrazaderas U a tu paleta y especificación de soportes.

NOTA TECNICA SOBRE SOPORTES:
Los soportes de tubería se colocan directamente sobre una tubería modelada.
Al engancharse al eje del tubo, el punto de conexión (S1) se valida y la gota
de desconexión ("Plant Connection Marker") desaparece automáticamente.
========================================================================
"""


def get_flattened_scripts(repo_root: Path, custom_scripts_dir: Path) -> dict:
    """
    Obtiene el mapeo {nombre_archivo: contenido_bytes_o_path} de los scripts aplanados.
    Si custom_scripts_dir existe con los archivos, los toma de allí;
    de lo contrario, aplana dinámicamente desde src/.
    """
    scripts = {}
    components = iter_components(repo_root)
    lib_files = get_lib_files(repo_root)

    expected_names = {output_path(custom_scripts_dir, src, repo_root).name for src in components.values()}
    expected_names.update(lib_src.name for lib_src in lib_files)

    # 1. Leer los archivos .py existentes en custom_scripts_dir
    if custom_scripts_dir.exists():
        for py_file in custom_scripts_dir.glob("*.py"):
            scripts[py_file.name] = py_file.read_bytes()

    # 2. Si faltaba alguno de los componentes esperados del repo, aplanar en memoria
    if not expected_names.issubset(scripts.keys()):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_p = Path(tmp_dir)
            flatten(repo_root, tmp_p)
            for f in tmp_p.glob("*.py"):
                if f.name not in scripts:
                    scripts[f.name] = f.read_bytes()

    # 3. Añadir ScriptGroup.xml si existe
    xml_path = custom_scripts_dir / "ScriptGroup.xml"
    if xml_path.exists():
        scripts["ScriptGroup.xml"] = xml_path.read_bytes()

    return scripts


def get_catalog_files(catalogs_dir: Path, catalog_filter: str = None) -> dict:
    """
    Obtiene los archivos .pcat y .acat disponibles.
    """
    catalogs = {}
    if not catalogs_dir.exists():
        return catalogs

    patterns = ["*.pcat", "*.acat"]
    for pattern in patterns:
        for cat_file in catalogs_dir.glob(pattern):
            if catalog_filter:
                if catalog_filter.lower() not in cat_file.name.lower():
                    continue
            catalogs[cat_file.name] = cat_file.read_bytes()

    return catalogs


def create_distribution_bundle(
    output_zip: Path,
    repo_root: Path = REPO_ROOT,
    scripts_dir: Path = DEFAULT_SCRIPTS_DIR,
    catalogs_dir: Path = DEFAULT_SCRIPTS_DIR,
    catalog_filter: str = None
) -> Path:
    """
    Crea el archivo ZIP con la estructura limpia de distribución.
    """
    output_zip = Path(output_zip).resolve()
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    scripts = get_flattened_scripts(repo_root, scripts_dir)
    catalogs = get_catalog_files(catalogs_dir, catalog_filter)

    if not catalogs:
        print(f"[Aviso] No se encontraron archivos de catálogo en {catalogs_dir}.")

    with zipfile.ZipFile(output_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # 1. CustomScripts/
        for name, data in sorted(scripts.items()):
            zf.writestr(f"CustomScripts/{name}", data)

        # 2. Catalogs/
        for name, data in sorted(catalogs.items()):
            zf.writestr(f"Catalogs/{name}", data)

        # 3. LEEME_INSTALACION.txt
        zf.writestr("LEEME_INSTALACION.txt", README_CONTENT.encode("utf-8"))

    return output_zip


def main():
    parser = argparse.ArgumentParser(
        description="Genera un paquete ZIP de distribución con CustomScripts y Catálogos para Plant 3D."
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=str(DEFAULT_DIST_DIR / DEFAULT_ZIP_NAME),
        help="Ruta de salida del archivo .zip"
    )
    parser.add_argument(
        "--scripts-dir",
        type=str,
        default=str(DEFAULT_SCRIPTS_DIR),
        help="Carpeta de origen de CustomScripts instalados"
    )
    parser.add_argument(
        "--catalogs-dir",
        type=str,
        default=str(DEFAULT_SCRIPTS_DIR),
        help="Carpeta donde residen los catálogos .pcat y .acat"
    )
    parser.add_argument(
        "--catalog", "-c",
        type=str,
        default=None,
        help="Filtro opcional para empaquetar un catálogo específico (ej: ITECO_B3S o INTEC_K200)"
    )

    args = parser.parse_args()
    out_zip = Path(args.output)
    scripts_dir = Path(args.scripts_dir)
    catalogs_dir = Path(args.catalogs_dir)

    print("==================================================")
    print("Exportador de Paquetes de Distribución Plant 3D")
    print("==================================================")
    print(f"Destino ZIP : {out_zip}")
    print(f"Scripts Dir : {scripts_dir}")
    print(f"Catalogs Dir: {catalogs_dir}")
    if args.catalog:
        print(f"Filtro      : {args.catalog}")

    created = create_distribution_bundle(
        output_zip=out_zip,
        repo_root=REPO_ROOT,
        scripts_dir=scripts_dir,
        catalogs_dir=catalogs_dir,
        catalog_filter=args.catalog
    )

    # Mostrar resumen
    with zipfile.ZipFile(created, "r") as z:
        items = z.namelist()
        custom_scripts = [it for it in items if it.startswith("CustomScripts/")]
        cats = [it for it in items if it.startswith("Catalogs/")]
        print(f"\n[OK] Paquete ZIP generado con éxito: {created}")
        print(f"  - Tamaño: {created.stat().st_size / 1024:.1f} KB")
        print(f"  - Scripts aplanados ({len(custom_scripts)}):")
        for cs in sorted(custom_scripts):
            print(f"      * {cs}")
        print(f"  - Catálogos ({len(cats)}):")
        for ct in sorted(cats):
            print(f"      * {ct}")
        print(f"  - Incluye: LEEME_INSTALACION.txt con pasos de instalación.")


if __name__ == "__main__":
    main()
