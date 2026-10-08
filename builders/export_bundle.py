"""
export_bundle.py - Empaquetador automatizado de distribución para AutoCAD Plant 3D 2027.

Empaqueta en un archivo ZIP autocontenido:
1. CustomScripts/: Scripts Python aplanados (modelos y librerías) + ScriptGroup.xml.
2. Catalogs/: Catálogos generados de tuberías (.pcat) y de soportes (.acat).
3. instalar.bat: Instalador desatendido en 1 clic para Windows.
4. LEEME_INSTALACION.txt: Guía paso a paso, uso en Spec Editor y resolución de problemas.

Uso:
    python builders/export_bundle.py
    python builders/export_bundle.py --output dist/Plant3D_Distribution_Bundle.zip
    python builders/export_bundle.py --catalog ITECO_B3S
"""

import os
import sys
import zipfile
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTENT_DIR = Path(r"C:\AutoCAD Plant 3D 2027 Content")
DEFAULT_SCRIPTS_DIR = DEFAULT_CONTENT_DIR / "CPak Common" / "CustomScripts"
DEFAULT_DIST_DIR = REPO_ROOT / "dist"
DEFAULT_ZIP_NAME = "Plant3D_Distribution_Bundle.zip"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from builders.build import iter_components, get_lib_files, output_path, flatten


INSTALL_BAT_CONTENT = """@echo off
chcp 65001 >nul
color 0b
title Instalador Automatizado - CustomScripts y Catalogos Plant 3D

echo ========================================================================
echo   INSTALADOR DE SCRIPTS Y CATALOGOS PARA AUTOCAD PLANT 3D
echo ========================================================================
echo.

REM 1. Detectar carpeta de contenido compartido de Plant 3D
set "CONTENT_DIR="
if exist "C:\\AutoCAD Plant 3D 2027 Content" set "CONTENT_DIR=C:\\AutoCAD Plant 3D 2027 Content"
if not defined CONTENT_DIR if exist "C:\\AutoCAD Plant 3D 2026 Content" set "CONTENT_DIR=C:\\AutoCAD Plant 3D 2026 Content"
if not defined CONTENT_DIR if exist "C:\\AutoCAD Plant 3D 2025 Content" set "CONTENT_DIR=C:\\AutoCAD Plant 3D 2025 Content"

if not defined CONTENT_DIR (
    echo [!] No se detecto automaticamente la ruta estandar de contenido compartido.
    echo Por favor introduce la ruta de tu carpeta de contenido
    echo ejemplo: C:\\AutoCAD Plant 3D 2027 Content
    set /p "CONTENT_DIR=Ruta: "
)

if not exist "%CONTENT_DIR%" (
    color 0c
    echo [ERROR] La carpeta especificada no existe: "%CONTENT_DIR%"
    echo Instalacion cancelada.
    pause
    exit /b 1
)

echo [+] Carpeta de Contenido Compartido detectada:
echo     "%CONTENT_DIR%"
echo.

REM 2. Crear carpetas de destino si no existen
if not exist "%CONTENT_DIR%\\CPak Common\\CustomScripts" mkdir "%CONTENT_DIR%\\CPak Common\\CustomScripts"
if not exist "%CONTENT_DIR%\\CPak Common" mkdir "%CONTENT_DIR%\\CPak Common"

REM 3. Copiar CustomScripts
echo [1/2] Instalando scripts Python y grupos en CustomScripts...
if exist "%~dp0CustomScripts" (
    xcopy /Y /Q "%~dp0CustomScripts\\*.*" "%CONTENT_DIR%\\CPak Common\\CustomScripts\\" >nul
    echo       - [OK] Scripts copiados a CPak Common\\CustomScripts\\
) else (
    echo       - [AVISO] Carpeta CustomScripts no encontrada.
)

REM 4. Copiar Catalogos (.pcat y .acat)
echo [2/2] Instalando catalogos SQLite (.pcat / .acat)...
if exist "%~dp0Catalogs" (
    xcopy /Y /Q "%~dp0Catalogs\\*.*" "%CONTENT_DIR%\\CPak Common\\" >nul
    xcopy /Y /Q "%~dp0Catalogs\\*.*" "%CONTENT_DIR%\\CPak Common\\CustomScripts\\" >nul
    echo       - [OK] Catalogos copiados a CPak Common\\
) else (
    echo       - [AVISO] Carpeta Catalogs no encontrada.
)

echo.
color 0a
echo ========================================================================
echo   ¡ARCHIVOS INSTALADOS CON EXITO!
echo ========================================================================
echo.
echo PASOS PARA ACTIVAR Y USAR EN AUTOCAD PLANT 3D:
echo.
echo 1. REGISTRAR SCRIPTS [En la linea de comandos de Plant 3D]:
echo      (arxload "PnP3dACPAdapter")
echo      PLANTREGISTERCUSTOMSCRIPTS
echo.
echo 2. INCORPORAR CATALOGOS A TU ESPECIFICACION [Spec Editor]:
echo    a. Abre 'AutoCAD Plant 3D Spec Editor'.
echo    b. Abre tu especificacion [File - Open Spec - tu .pspc de proyecto].
echo    c. Abre el catalogo [File - Open Catalog - selecciona el .pcat o .acat].
echo    d. Selecciona la familia de valvulas o soportes en el catalogo.
echo    e. Haz clic en el boton 'Add to Spec' [Anadir a la especificacion].
echo    f. Guarda la especificacion [Ctrl+S].
echo    g. En AutoCAD Plant 3D, ejecuta el comando: PLANTSPECUPDATECHECK
echo ========================================================================
echo.
pause
"""


README_CONTENT = """========================================================================
GUIA RAPIDA DE INSTALACION - AUTOCAD PLANT 3D
========================================================================

PASO 1: INSTALAR ARCHIVOS
- Ejecuta "instalar.bat" haciendo doble clic.
  (O copia manualmente CustomScripts/ y Catalogs/ a
   C:\\AutoCAD Plant 3D 2027 Content\\CPak Common\\).

PASO 2: REGISTRAR SCRIPTS EN PLANT 3D (OBLIGATORIO)
Abre AutoCAD Plant 3D y en la barra de comandos ejecuta estas 2 lineas:

   (arxload "PnP3dACPAdapter")
   PLANTREGISTERCUSTOMSCRIPTS

* NOTA: Debes incluir los parentesis "( )" en arxload.

PASO 3: AGREGAR A TU ESPECIFICACION (SPEC EDITOR)
1. Abre AutoCAD Plant 3D Spec Editor.
2. Abre tu especificacion de proyecto (File -> Open Spec).
3. Abre el catalogo deseado (File -> Open Catalog).
4. Selecciona la familia de valvulas o soportes y haz clic en "Add to Spec".
5. Guarda con Ctrl+S.
6. En Plant 3D, ejecuta: PLANTSPECUPDATECHECK
========================================================================
"""


def get_flattened_scripts(repo_root: Path, custom_scripts_dir: Path) -> dict:
    """
    Obtiene el mapeo {nombre_archivo: contenido_bytes} de los scripts aplanados.
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

    # 2. Si faltaba alguno de los componentes esperados del repo, aplanar dinámicamente
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


STOCK_AUTODESK_CATALOGS = {
    "Actuator Catalog.acat",
    "NOZZLE Catalog.acat",
    "Structural Catalog.acat",
    "SUPPORTS Catalog.acat",
    "SUPPORTS Catalog metric.acat",
    "CustomParts Imperial Catalog.pcat",
    "CustomParts Imperial.pcat",
    "CustomParts Metric Catalog.pcat",
    "Instrumentation Imperial.pcat",
    "Instrumentation Metric.pcat",
}


def get_catalog_files(catalogs_dir: Path, catalog_filter: str = None) -> dict:
    """
    Obtiene los archivos .pcat y .acat disponibles, excluyendo los catálogos base de Autodesk.
    """
    catalogs = {}
    search_dirs = [catalogs_dir]
    if catalogs_dir != DEFAULT_SCRIPTS_DIR and DEFAULT_SCRIPTS_DIR.exists():
        search_dirs.append(DEFAULT_SCRIPTS_DIR)
    cpak_common = DEFAULT_CONTENT_DIR / "CPak Common"
    if cpak_common.exists() and cpak_common not in search_dirs:
        search_dirs.append(cpak_common)

    patterns = ["*.pcat", "*.acat"]
    for s_dir in search_dirs:
        if not s_dir.exists():
            continue
        for pattern in patterns:
            for cat_file in s_dir.glob(pattern):
                if cat_file.name in catalogs:
                    continue
                if cat_file.name in STOCK_AUTODESK_CATALOGS:
                    continue
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
    Crea el archivo ZIP con solo catálogos y scripts necesarios para distribución.
    """
    output_zip = Path(output_zip).resolve()
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    scripts = get_flattened_scripts(repo_root, scripts_dir)
    catalogs = get_catalog_files(catalogs_dir, catalog_filter)

    with zipfile.ZipFile(output_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # 1. CustomScripts/
        for name, data in sorted(scripts.items()):
            zf.writestr(f"CustomScripts/{name}", data)

        # 2. Catalogs/
        for name, data in sorted(catalogs.items()):
            zf.writestr(f"Catalogs/{name}", data)

        # 3. Raíz: instalador y documentación
        bat_crlf = INSTALL_BAT_CONTENT.replace("\r\n", "\n").replace("\n", "\r\n")
        zf.writestr("instalar.bat", bat_crlf.encode("utf-8"))
        readme_crlf = README_CONTENT.replace("\r\n", "\n").replace("\n", "\r\n")
        zf.writestr("LEEME_INSTALACION.txt", readme_crlf.encode("utf-8"))

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
        root_files = [it for it in items if "/" not in it]

        print(f"\n[OK] Paquete ZIP generado con éxito: {created}")
        print(f"  - Tamaño: {created.stat().st_size / 1024:.1f} KB")
        print(f"  - Archivos raíz ({len(root_files)}):")
        for rf in sorted(root_files):
            print(f"      * {rf}")
        print(f"  - Scripts aplanados ({len(custom_scripts)}):")
        for cs in sorted(custom_scripts):
            print(f"      * {cs}")
        print(f"  - Catálogos ({len(cats)}):")
        for ct in sorted(cats):
            print(f"      * {ct}")


if __name__ == "__main__":
    main()
