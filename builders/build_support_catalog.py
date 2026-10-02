r"""
build_support_catalog.py - Generador automatizado de Catálogos de Soportes (.acat)
para AutoCAD Plant 3D 2027 según el estándar ASME / MSS-SP-58.

Lee un archivo JSON de especificación canónica (ej: ITECO_B3S.json) y genera el archivo
SQLite3 (.acat) de catálogo de soportes para abrir directamente en el Spec Editor de Plant 3D.

Uso:
    python builders/build_support_catalog.py --spec-json ..\catalog-scrap\output\specifications\ITECO_B3S.json
"""

import os
import sys
import json
import uuid
import shutil
import argparse
from pathlib import Path

try:
    import sqlite3
except ImportError:
    sqlite3 = None

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTENT_DIR = Path(r"C:\AutoCAD Plant 3D 2027 Content\CPak Common")
DEFAULT_TEMPLATE_ACAT = DEFAULT_CONTENT_DIR / "SUPPORTS Catalog.acat"
DEFAULT_TARGET_DIR = DEFAULT_CONTENT_DIR / "CustomScripts"

# Asegurar REPO_ROOT en sys.path
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from builders.build_catalog import get_matching_pipe_od, DN_TO_INCH_MAP
except ImportError:
    from build_catalog import get_matching_pipe_od, DN_TO_INCH_MAP


def parse_nps_to_inch(nps_str: str, dn_mm: float = None) -> float:
    """Convierte una cadena de NPS (ej: '1/4\"', '1 1/2\"', '2\"') a float en pulgadas decimales."""
    if nps_str:
        s = str(nps_str).replace('"', '').replace("'", '').strip()
        parts = s.split()
        total = 0.0
        for p in parts:
            if "/" in p:
                try:
                    num, den = p.split("/")
                    total += float(num) / float(den)
                except ValueError:
                    pass
            else:
                try:
                    total += float(p)
                except ValueError:
                    pass
        if total > 0:
            return round(total, 3)
    if dn_mm:
        try:
            dn_int = int(round(float(dn_mm)))
            if dn_int in DN_TO_INCH_MAP:
                return DN_TO_INCH_MAP[dn_int]
        except (ValueError, TypeError):
            pass
        return round(float(dn_mm) / 25.4, 3)
    return 1.0


def build_support_catalog(
    spec_json_path: Path,
    output_dir: Path = DEFAULT_TARGET_DIR,
    catalog_name: str = None,
    template_acat: Path = DEFAULT_TEMPLATE_ACAT,
    clear_existing: bool = True
):
    """
    Construye un catálogo oficial (.acat) de soportes para abrir en Plant 3D Spec Editor.
    """
    if sqlite3 is None:
        raise RuntimeError("El módulo sqlite3 no está disponible en este entorno Python.")

    if not spec_json_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo JSON de especificación: {spec_json_path}")

    if not template_acat.exists():
        raise FileNotFoundError(f"No se encontró la plantilla de catálogo .acat: {template_acat}")

    with open(spec_json_path, "r", encoding="utf-8") as f:
        spec_data = json.load(f)

    meta = spec_data.get("metadata", {})
    records = spec_data.get("plant3d_records", [])
    if not records:
        raise ValueError(f"El archivo {spec_json_path} no contiene 'plant3d_records'.")

    model = spec_data.get("model") or meta.get("model", "SUPPORT")
    model_code = model.replace(" ", "_")
    if not catalog_name:
        catalog_name = f"{model_code}_Supports_Catalog"

    output_dir.mkdir(parents=True, exist_ok=True)
    out_acat = output_dir / f"{catalog_name}.acat"

    # Copiar plantilla base oficial de soportes (.acat)
    shutil.copy2(template_acat, out_acat)

    conn = sqlite3.connect(out_acat)
    cur = conn.cursor()

    manufacturer = spec_data.get("manufacturer") or meta.get("manufacturer", "Generic")
    desc = spec_data.get("valve_type") or spec_data.get("description") or meta.get("description", "Pipe Support")

    if clear_existing:
        cur.execute("DELETE FROM EngineeringItems;")
        cur.execute("DELETE FROM PipeRunComponent;")
        cur.execute("DELETE FROM Support;")
        cur.execute("DELETE FROM PnPBase WHERE PnPClassName != 'RepositoryDescriptor';")
        cur.execute("UPDATE RepositoryDescriptor SET Name = ?, Description = ? WHERE PnPID = 1;",
                    (catalog_name, f"{manufacturer} {model} Support Catalog"))
        conn.commit()
        start_pnp_id = 2
    else:
        cur.execute("SELECT MAX(PnPID) FROM PnPBase;")
        row = cur.fetchone()
        start_pnp_id = (row[0] + 1) if row and row[0] is not None else 2

    family_guid = uuid.uuid4().bytes
    family_desc = f"{manufacturer} {model} {desc}".strip()
    short_desc = f"{model}"
    design_std = (spec_data.get("standards", {}).get("manufacturing") or
                  meta.get("standards", {}).get("manufacturing") or
                  meta.get("design_standard", "MSS-SP-58"))
    geom_template = spec_data.get("plant3d_template") or meta.get("plant3d_template", "UBOLT_STANDARD")

    pnp_id = start_pnp_id
    items_count = 0

    for it in records:
        dn_mm = it.get("DN_mm", 15)
        nps_str = it.get("NPS_inch", "")
        nd = parse_nps_to_inch(nps_str, dn_mm)
        pipe_od_in = get_matching_pipe_od(nd)

        a_in = round(it.get("Rod_Diameter_mm", 0.0) / 25.4, 4)
        b_in = round(it.get("B_Inside_Width_mm", 0.0) / 25.4, 4)
        c_in = round(it.get("C_Center_Distance_mm", 0.0) / 25.4, 4)
        d_in = round(it.get("D_Total_Height_mm", 0.0) / 25.4, 4)
        e_in = round(it.get("E_Leg_Height_mm", 0.0) / 25.4, 4)
        f_in = round(it.get("F_Thread_Length_mm", 0.0) / 25.4, 4)

        size_desc = f"{family_desc}, {nps_str}".strip(", ")
        param_def = f"OD={pipe_od_in:.6f},A={a_in:.6f},B={b_in:.6f},C={c_in:.6f},D={d_in:.6f},E={e_in:.6f},F={f_in:.6f}"

        guid = uuid.uuid4().bytes
        size_guid = uuid.uuid4().bytes
        timestamp = 638000000000000000

        cur.execute("""
            INSERT INTO PnPBase (PnPID, PnPClassName, PnPStatus, PnPRevision, PnPGuid, PnPTimestamp)
            VALUES (?, 'Support', 0, 0, ?, ?);
        """, (pnp_id, guid, timestamp))

        cur.execute("INSERT INTO PipeRunComponent (PnPID) VALUES (?);", (pnp_id,))
        cur.execute("INSERT INTO Support (PnPID, PartSubType) VALUES (?, 'Support');", (pnp_id,))

        weight_kg = it.get("Weight_kg", 0.0)
        weight_lb = round(weight_kg * 2.20462, 2) if weight_kg else None

        cur.execute("""
            INSERT INTO EngineeringItems (
                PnPID, PartFamilyId, CatalogPartFamilyId, PartFamilyLongDesc,
                PartSizeLongDesc, ShortDescription, Manufacturer, Material,
                MaterialCode, DesignStd, CompatibleStandard, Weight, WeightUnit,
                ConnectionPortCount, SizeRecordId, PortName, NominalDiameter,
                NominalUnit, MatchingPipeOd, EndType, LengthUnit, PartCategory,
                ContentDomain, ContentGeometryParamDefinition, ContentIsoSymbolDefinition,
                ContentGeometryTemplate, PartVersion
            ) VALUES (
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?
            );
        """, (
            pnp_id, family_guid, family_guid, family_desc,
            size_desc, short_desc, manufacturer, it.get("Material", "Carbon Steel"),
            "CS", design_std, design_std, weight_lb, "LB" if weight_lb else None,
            1, size_guid, "S1", nd,
            "in", pipe_od_in, "Undefined_ET", "in", "Default",
            "P3D", param_def, "TYPE=SUPPORT,SKEY=ANCH",
            geom_template, "4_0"
        ))

        pnp_id += 1
        items_count += 1

    conn.commit()
    conn.close()

    return {
        "acat_path": str(out_acat),
        "items_count": items_count,
        "catalog_name": catalog_name
    }


def main():
    parser = argparse.ArgumentParser(description="Construir Catálogo de Soporte (.acat) para Plant 3D 2027")
    parser.add_argument("--spec-json", required=True, type=Path, help="Ruta al JSON de especificación")
    parser.add_argument("--output-dir", default=DEFAULT_TARGET_DIR, type=Path, help="Directorio destino")
    parser.add_argument("--catalog-name", default=None, type=str, help="Nombre del archivo de catálogo")
    parser.add_argument("--template-acat", default=DEFAULT_TEMPLATE_ACAT, type=Path, help="Plantilla base .acat")

    args = parser.parse_args()
    res = build_support_catalog(
        spec_json_path=args.spec_json,
        output_dir=args.output_dir,
        catalog_name=args.catalog_name,
        template_acat=args.template_acat
    )
    print(f"[+] Catálogo de Soporte creado con éxito: {res['catalog_name']}")
    print(f"    ACAT: {res['acat_path']}")
    print(f"    Total items: {res['items_count']}")


if __name__ == "__main__":
    main()
