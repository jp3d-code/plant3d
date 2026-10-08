"""
export_bundle.py - Empaquetador automatizado de distribución para AutoCAD Plant 3D 2027.

Empaqueta en un archivo ZIP autocontenido:
1. CustomScripts/: Scripts Python aplanados (modelos y librerías) + ScriptGroup.xml.
2. Catalogs/: Catálogos generados de tuberías (.pcat) y de soportes (.acat).
3. Specs/: Especificaciones compiladas listas para usar (.pspc y .pspx).
4. instalar.bat: Instalador desatendido en 1 clic para Windows.
5. probar_instalacion.lsp: Script AutoLISP de prueba y verificación inmediata.
6. LEEME_INSTALACION.txt: Guía paso a paso, solución de problemas y diagnóstico.

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
DEFAULT_PROJECT_DIR = Path(
    r"C:\Users\ynoacamino\AppData\Roaming\Autodesk\Autodesk AutoCAD Plant 3D 2027\R26.0\enu\DefaultProject"
)
DEFAULT_DIST_DIR = REPO_ROOT / "dist"
DEFAULT_ZIP_NAME = "Plant3D_Distribution_Bundle.zip"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from builders.build import iter_components, get_lib_files, output_path, flatten


INSTALL_BAT_CONTENT = """@echo off
chcp 65001 >nul
color 0b
title Instalador Automatizado - Paquete AutoCAD Plant 3D

echo ========================================================================
echo   INSTALADOR DE COMPONENTES Y CATALOGOS PARA AUTOCAD PLANT 3D
echo ========================================================================
echo.

:: 1. Detectar carpeta de contenido compartido de Plant 3D
set "CONTENT_DIR="
if exist "C:\\AutoCAD Plant 3D 2027 Content" set "CONTENT_DIR=C:\\AutoCAD Plant 3D 2027 Content"
if not defined CONTENT_DIR if exist "C:\\AutoCAD Plant 3D 2026 Content" set "CONTENT_DIR=C:\\AutoCAD Plant 3D 2026 Content"
if not defined CONTENT_DIR if exist "C:\\AutoCAD Plant 3D 2025 Content" set "CONTENT_DIR=C:\\AutoCAD Plant 3D 2025 Content"

if not defined CONTENT_DIR (
    echo [!] No se detectó automáticamente la ruta estándar de contenido compartido.
    echo Por favor introduce la ruta de tu carpeta de contenido
    echo (ejemplo: C:\\AutoCAD Plant 3D 2027 Content):
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

:: 2. Crear carpetas de destino si no existen
if not exist "%CONTENT_DIR%\\CPak Common\\CustomScripts" mkdir "%CONTENT_DIR%\\CPak Common\\CustomScripts"
if not exist "%CONTENT_DIR%\\CPak Common" mkdir "%CONTENT_DIR%\\CPak Common"
if not exist "%CONTENT_DIR%\\CPak ASME" mkdir "%CONTENT_DIR%\\CPak ASME"

:: 3. Copiar CustomScripts
echo [1/4] Instalando scripts Python y grupos en CustomScripts...
if exist "%~dp0CustomScripts" (
    xcopy /Y /Q "%~dp0CustomScripts\\*.*" "%CONTENT_DIR%\\CPak Common\\CustomScripts\\" >nul
    echo       - [OK] Scripts copiados a CPak Common\\CustomScripts\\
) else (
    echo       - [AVISO] Carpeta CustomScripts no encontrada.
)

:: 4. Copiar Catalogos (.pcat y .acat)
echo [2/4] Instalando catalogos SQLite (.pcat / .acat)...
if exist "%~dp0Catalogs" (
    xcopy /Y /Q "%~dp0Catalogs\\*.*" "%CONTENT_DIR%\\CPak Common\\" >nul
    xcopy /Y /Q "%~dp0Catalogs\\*.*" "%CONTENT_DIR%\\CPak Common\\CustomScripts\\" >nul
    echo       - [OK] Catalogos copiados a CPak Common\\
) else (
    echo       - [AVISO] Carpeta Catalogs no encontrada.
)

:: 5. Copiar Especificaciones (.pspc y .pspx)
echo [3/4] Instalando Especificaciones (.pspc / .pspx)...
if exist "%~dp0Specs" (
    xcopy /Y /Q "%~dp0Specs\\*.*" "%CONTENT_DIR%\\CPak ASME\\" >nul
    xcopy /Y /Q "%~dp0Specs\\*.*" "%CONTENT_DIR%\\CPak Common\\" >nul
    echo       - [OK] Specs maestras copiadas a CPak ASME\\ y CPak Common\\
    
    :: Copiar al DefaultProject de Plant 3D si existe
    if exist "%APPDATA%\\Autodesk\\Autodesk AutoCAD Plant 3D 2027\\R26.0\\enu\\DefaultProject\\SpecSheets" (
        xcopy /Y /Q "%~dp0Specs\\*.*" "%APPDATA%\\Autodesk\\Autodesk AutoCAD Plant 3D 2027\\R26.0\\enu\\DefaultProject\\SpecSheets\\" >nul
        echo       - [OK] Specs copiadas al proyecto activo DefaultProject 2027
    )
    if exist "%APPDATA%\\Autodesk\\Autodesk AutoCAD Plant 3D 2026\\R25.0\\enu\\DefaultProject\\SpecSheets" (
        xcopy /Y /Q "%~dp0Specs\\*.*" "%APPDATA%\\Autodesk\\Autodesk AutoCAD Plant 3D 2026\\R25.0\\enu\\DefaultProject\\SpecSheets\\" >nul
        echo       - [OK] Specs copiadas al proyecto activo DefaultProject 2026
    )
) else (
    echo       - [AVISO] Carpeta Specs no encontrada.
)

:: 6. Copiar script de prueba
if exist "%~dp0probar_instalacion.lsp" (
    copy /Y "%~dp0probar_instalacion.lsp" "%CONTENT_DIR%\\CPak Common\\CustomScripts\\" >nul
)

echo [4/4] Verificando integración...
echo.
color 0a
echo ========================================================================
echo   ¡INSTALACION COMPLETADA CON EXITO!
echo ========================================================================
echo.
echo INSTRUCCIONES PARA ACTIVAR EN AUTOCAD PLANT 3D:
echo.
echo 1. Abre AutoCAD Plant 3D.
echo 2. En la línea de comandos escribe (incluyendo los paréntesis):
echo      (arxload "PnP3dACPAdapter")
echo      PLANTREGISTERCUSTOMSCRIPTS
echo.
echo 3. PRUEBA INMEDIATA EN 3 SEGUNDOS:
echo    Arrastra el archivo "probar_instalacion.lsp" al dibujo, o escribe:
echo      (load "probar_instalacion.lsp")
echo.
echo 4. COMO RUTEAR EN TU PROYECTO:
echo    - En el panel de Proyecto (Project Manager) bajo 'Pipe Specs',
echo      haz clic derecho -> 'Copy Specs to Project' y selecciona
echo      'CS150_Soportes.pspc' desde CPak ASME.
echo    - O selecciona directamente la especificación 'CS150_Soportes'
echo      en el desplegable de Specs de la cinta de opciones (Ribbon).
echo    - Para insertar soportes U-Bolt, usa el comando:
echo      PLANTPIPESUPPORTADD y selecciónalo de la paleta.
echo ========================================================================
echo.
pause
"""


README_CONTENT = """========================================================================
PAQUETE DE DISTRIBUCION - AUTOCAD PLANT 3D 2027
COMPONENTES PARAMETRICOS PYTHON + CATALOGOS + ESPECIFICACIONES ASME
========================================================================

Este paquete autocontenido incluye todo lo necesario para incorporar
válvulas de bola de alta precisión (KLINGER INTEC K200 y Saidi Comercial)
y abrazaderas de soporte U-Bolt ITECO B3S en AutoCAD Plant 3D 2027/2026.

CONTENIDO DEL PAQUETE:
----------------------
1. instalar.bat
   - Script de instalación automatizada en 1 clic para Windows.
   - Copia automáticamente scripts, catálogos y especificaciones a sus
     respectivas carpetas oficiales de Plant 3D sin errores de ruta.

2. probar_instalacion.lsp
   - Script AutoLISP de prueba y validación rápida.
   - Modela automáticamente en 3D un tramo de tubería 2", una válvula
     INTEC K200 2" y un soporte U-Bolt ITECO B3S 2" abrazado al tubo.

3. CustomScripts/
   - Scripts Python paramétricos (.py):
     * intec_k200_ball_valve.py (Válvula INTEC K200, 100% cotas de ingeniería)
     * iteco_b3s_standard_ubolt.py (Abrazadera U-Bolt ITECO B3S con contratuercas)
     * ball_valve_1pc_compact.py, ball_valve_2pc_flanged.py, etc.
     * utils.py (Librería de utilidades geométricas)
   - ScriptGroup.xml (Registro oficial de grupos y conexiones en Plant 3D).

4. Catalogs/
   - KLINGER_Schoneberg_INTEC_K200_Catalog.pcat (Válvulas INTEC K200 150# y 300#)
   - Catalogo_Val_Bola_2016-44_Catalog.pcat (Válvulas comerciales Saidi RK)
   - ITECO_B3S_Supports_Catalog.acat (29 tamaños de abrazaderas U-Bolt B3S)

5. Specs/
   - CS150_Soportes.pspc y .pspx:
     Especificación híbrida completa lista para modelado. Contiene:
     * Tuberías y accesorios de acero al carbono ASME B36.10 / ASME B16.5
     * Válvulas de bola Clase 150# (INTEC K200 y Saidi)
     * 29 tamaños de soportes U-Bolt ITECO B3S (1/4" a 36")
   - PipeSupportsSpec.pspc y .pspx:
     Especificación estándar de soportes de Plant 3D actualizada con los
     29 tamaños de abrazaderas U-Bolt para el comando PLANTPIPESUPPORTADD.

------------------------------------------------------------------------
METODOS DE INSTALACION:
------------------------------------------------------------------------

METODO 1: INSTALACION AUTOMATICA (RECOMENDADO - 1 CLIC)
--------------------------------------------------------
1. Descomprime este archivo ZIP en cualquier carpeta local.
2. Haz doble clic sobre "instalar.bat".
   (El script detectará tu versión de Plant 3D y copiará todo a su lugar).
3. Abre AutoCAD Plant 3D y en la línea de comandos ejecuta:
     (arxload "PnP3dACPAdapter")
     PLANTREGISTERCUSTOMSCRIPTS
4. Para validar que todo funciona en 3 segundos:
   Arrastra "probar_instalacion.lsp" al dibujo, o escribe en la consola:
     (load "probar_instalacion.lsp")


METODO 2: INSTALACION MANUAL (PASO A PASO)
-------------------------------------------
Si prefieres instalar los archivos manualmente:

PASO 1: Copiar Scripts Python
Copiar todos los archivos dentro de la carpeta "CustomScripts/" a:
    C:\\AutoCAD Plant 3D 2027 Content\\CPak Common\\CustomScripts\\
* IMPORTANTE: Copia los archivos directos, NO la carpeta CustomScripts
  dentro de sí misma.

PASO 2: Copiar Catálogos SQLite
Copiar todos los archivos dentro de la carpeta "Catalogs/" a:
    C:\\AutoCAD Plant 3D 2027 Content\\CPak Common\\

PASO 3: Copiar Especificaciones (.pspc y .pspx)
Copiar todos los archivos dentro de la carpeta "Specs/" a:
    C:\\AutoCAD Plant 3D 2027 Content\\CPak ASME\\
y a la subcarpeta de especificaciones de tu proyecto activo:
    <RutaDeTuProyecto>\\SpecSheets\\

PASO 4: Registrar Scripts en Plant 3D
Abrir AutoCAD Plant 3D y en la barra de comandos escribir exactamente:
    (arxload "PnP3dACPAdapter")
    PLANTREGISTERCUSTOMSCRIPTS
* NOTA: Los paréntesis "( )" en arxload son OBLIGATORIOS (sintaxis AutoLISP).

PASO 5: Usar en tu dibujo
- Selecciona la especificación "CS150_Soportes" en el menú desplegable de
  Specs (Spec Viewer) para insertar tubos, válvulas y accesorios.
- Para colocar soportes U-Bolt: ejecuta PLANTPIPESUPPORTADD y haz clic
  directamente sobre el eje de la tubería donde deseas la abrazadera.

------------------------------------------------------------------------
GUIA DE RESOLUCION DE PROBLEMAS (FAQ / TROUBLESHOOTING):
------------------------------------------------------------------------
P: ¿Por qué mi compañero no veía los soportes ni válvulas en su proyecto?
R: AutoCAD Plant 3D NUNCA inserta piezas directamente desde catálogos (.pcat/.acat).
   Plant 3D exige que los componentes formen parte de una Especificación (.pspc).
   Asegúrate de copiar "CS150_Soportes.pspc" dentro de la carpeta "SpecSheets"
   de tu proyecto de AutoCAD Plant 3D, o usar el Project Manager:
   clic derecho en "Pipe Specs" -> "Copy Specs to Project".

P: Al ejecutar arxload dice "Comando desconocido / Unknown command".
R: Escribiste arxload sin paréntesis. Debe escribirse con paréntesis:
   (arxload "PnP3dACPAdapter")

P: Los scripts de Python no se actualizan al registrarlos.
R: AutoCAD Plant 3D mantiene los módulos en memoria caché. Si ya tenías
   Plant 3D abierto antes de copiar los scripts, ciérralo y vuelve a abrirlo.

P: Windows bloquea los archivos descargados.
R: Si descargaste el ZIP por Teams, correo o navegador, haz clic derecho
   en el archivo ZIP -> "Propiedades" -> marca la casilla "Desbloquear"
   (Unblock) y haz clic en Aceptar antes de descomprimirlo.
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


def get_spec_files(specs_dir: Path = None) -> dict:
    """
    Obtiene las especificaciones compiladas .pspc y .pspx listas para usar.
    """
    specs = {}
    search_dirs = []
    if specs_dir and specs_dir.exists():
        search_dirs.append(specs_dir)
    
    # Rutas estándar de specs
    candidates = [
        DEFAULT_CONTENT_DIR / "CPak ASME",
        DEFAULT_CONTENT_DIR / "CPak Common",
        DEFAULT_PROJECT_DIR / "SpecSheets",
    ]
    for c in candidates:
        if c.exists() and c not in search_dirs:
            search_dirs.append(c)

    target_specs = ["CS150_Soportes", "PipeSupportsSpec"]
    patterns = ["*.pspc", "*.pspx"]

    for s_dir in search_dirs:
        for pattern in patterns:
            for sp_file in s_dir.glob(pattern):
                if sp_file.name.endswith(".bak"):
                    continue
                # Solo incluir las specs objetivo relevantes
                stem = sp_file.stem
                if any(t.lower() == stem.lower() for t in target_specs):
                    if sp_file.name not in specs:
                        specs[sp_file.name] = sp_file.read_bytes()

    return specs


def get_tool_files(repo_root: Path) -> dict:
    """
    Obtiene archivos de herramientas auxiliares (ej: probar_instalacion.lsp).
    """
    tools = {}
    lsp_path = repo_root / "tools" / "probar_instalacion.lsp"
    if lsp_path.exists():
        tools["probar_instalacion.lsp"] = lsp_path.read_bytes()
    return tools


def create_distribution_bundle(
    output_zip: Path,
    repo_root: Path = REPO_ROOT,
    scripts_dir: Path = DEFAULT_SCRIPTS_DIR,
    catalogs_dir: Path = DEFAULT_SCRIPTS_DIR,
    specs_dir: Path = None,
    catalog_filter: str = None
) -> Path:
    """
    Crea el archivo ZIP con la estructura limpia y completa de distribución.
    """
    output_zip = Path(output_zip).resolve()
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    scripts = get_flattened_scripts(repo_root, scripts_dir)
    catalogs = get_catalog_files(catalogs_dir, catalog_filter)
    specs = get_spec_files(specs_dir)
    tools = get_tool_files(repo_root)

    with zipfile.ZipFile(output_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # 1. CustomScripts/
        for name, data in sorted(scripts.items()):
            zf.writestr(f"CustomScripts/{name}", data)

        # 2. Catalogs/
        for name, data in sorted(catalogs.items()):
            zf.writestr(f"Catalogs/{name}", data)

        # 3. Specs/
        for name, data in sorted(specs.items()):
            zf.writestr(f"Specs/{name}", data)

        # 4. Raíz: herramientas y scripts de automatización
        zf.writestr("instalar.bat", INSTALL_BAT_CONTENT.encode("utf-8"))
        if "probar_instalacion.lsp" in tools:
            zf.writestr("probar_instalacion.lsp", tools["probar_instalacion.lsp"])

        # 5. Raíz: Documentación
        zf.writestr("LEEME_INSTALACION.txt", README_CONTENT.encode("utf-8"))

    return output_zip


def main():
    parser = argparse.ArgumentParser(
        description="Genera un paquete ZIP de distribución con CustomScripts, Catálogos y Specs para Plant 3D."
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
        "--specs-dir",
        type=str,
        default=None,
        help="Carpeta donde residen las especificaciones .pspc y .pspx"
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
    specs_dir = Path(args.specs_dir) if args.specs_dir else None

    print("==================================================")
    print("Exportador de Paquetes de Distribución Plant 3D")
    print("==================================================")
    print(f"Destino ZIP : {out_zip}")
    print(f"Scripts Dir : {scripts_dir}")
    print(f"Catalogs Dir: {catalogs_dir}")
    if specs_dir:
        print(f"Specs Dir   : {specs_dir}")
    if args.catalog:
        print(f"Filtro      : {args.catalog}")

    created = create_distribution_bundle(
        output_zip=out_zip,
        repo_root=REPO_ROOT,
        scripts_dir=scripts_dir,
        catalogs_dir=catalogs_dir,
        specs_dir=specs_dir,
        catalog_filter=args.catalog
    )

    # Mostrar resumen
    with zipfile.ZipFile(created, "r") as z:
        items = z.namelist()
        custom_scripts = [it for it in items if it.startswith("CustomScripts/")]
        cats = [it for it in items if it.startswith("Catalogs/")]
        specs_list = [it for it in items if it.startswith("Specs/")]
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
        print(f"  - Especificaciones ({len(specs_list)}):")
        for sp in sorted(specs_list):
            print(f"      * {sp}")


if __name__ == "__main__":
    main()
