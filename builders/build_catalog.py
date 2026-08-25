"""
build_catalog.py - Generador automatizado y DESACOPLADO de catálogo .pcat (SQLite3) para Plant 3D 2027.

Escanea dinámicamente todos los archivos .csv en src/families/ para construir el catálogo
sin tener datos de dimensiones hardcodeados en el código Python.

Uso:
    python builders/build_catalog.py
    python builders/build_catalog.py --output-pcat <path>
"""
import os
import sys
import csv
import json
import uuid

import argparse
try:
    import sqlite3
except ImportError:
    sqlite3 = None
import shutil
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FAMILIES_DIR = REPO_ROOT / "src" / "families"
DEFAULT_TARGET_DIR = Path(r"C:\AutoCAD Plant 3D 2027 Content\CPak Common\CustomScripts")
TEMPLATE_PCAT = Path(r"C:\AutoCAD Plant 3D 2027 Content\CPak Common\CustomParts Imperial Catalog.pcat")
DEFAULT_OUTPUT_PCAT = DEFAULT_TARGET_DIR / "Swagelok_Catalog.pcat"

# Incluir REPO_ROOT en sys.path por si se ejecuta directamente
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from builders.build import find_registration_name
except ImportError:
    from build import find_registration_name

# Tablas del sistema SQLite / Plant3D que NO deben vaciarse al limpiar el catálogo
SYSTEM_TABLES = {
    "PnPDatabase", "PnPTables", "PnPProperties", "PnPRelationshipTypes", "PnPRoleTypes", 
    "PnPRelationshipProperties", "PnPTableAttributes", "PnPColumnAttributes", 
    "sqlite_sequence", "RepositoryDescriptor", "PnPSys_RelationshipSystem_PnPID"
}


def guid_to_bytes(guid_str=None):
    """Genera un GUID binario de 16 bytes compatible con SQLite de Plant 3D."""
    if not guid_str:
        u = uuid.uuid4()
    else:
        u = uuid.UUID(guid_str)
    return u.bytes


def get_current_win_filetime():
    """Devuelve la marca de tiempo en ticks de Windows (100-ns desde 1601)."""
    return int(time.time() * 10000000) + 116444736000000000


def get_next_pnp_id(cursor):
    """Devuelve el siguiente PnPID único usando la secuencia autoincremental."""
    cursor.execute("INSERT INTO PnPSys_PnPBase_PnPID(d) VALUES ('a');")
    return cursor.lastrowid


def prepare_base_catalog(output_pcat=DEFAULT_OUTPUT_PCAT, template_pcat=TEMPLATE_PCAT, catalog_title="Custom"):
    """Copia la plantilla base de catálogo .pcat limpia y asigna un GUID único de catálogo."""
    output_pcat.parent.mkdir(parents=True, exist_ok=True)
    if output_pcat.exists():
        try:
            output_pcat.unlink()
        except PermissionError:
            print(f"AVISO: {output_pcat.name} está bloqueado (probablemente abierto en Spec Editor). Omitiendo...")
            return False

    shutil.copy2(template_pcat, output_pcat)

    conn = sqlite3.connect(output_pcat)
    cursor = conn.cursor()

    # 1. Asignar un RepositoryID GUID 100% ÚNICO para evitar colisión de catálogos en Spec Editor
    new_repo_guid = f"{{{uuid.uuid4()}}}"
    new_db_guid = guid_to_bytes()

    cursor.execute("""
        UPDATE RepositoryDescriptor
        SET RepositoryID = ?, Name = ?, Description = ?
        WHERE PnPID = 1;
    """, (new_repo_guid, f"{catalog_title} Catalog", f"{catalog_title} Custom Component Catalog"))

    cursor.execute("""
        UPDATE PnPDatabase
        SET DBID = ?;
    """, (new_db_guid,))

    conn.commit()
    conn.close()

    print(f"Catálogo base asignado con nuevo RepositoryID {new_repo_guid} en: {output_pcat}")


def clean_all_data_tables(conn):
    """Limpia TODAS las tablas de datos para eliminar registros huérfanos y evitar corrupción."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    all_tables = [r[0] for r in cursor.fetchall()]

    for table in all_tables:
        if table not in SYSTEM_TABLES:
            cursor.execute(f"DELETE FROM `{table}`;")

    cursor.execute("DELETE FROM PnPSys_PnPBase_PnPID;")
    
    # Re-insertar entrada base de RepositoryDescriptor en PnPBase con PnPID=1
    repo_guid = guid_to_bytes()
    cursor.execute("""
        INSERT INTO PnPBase (PnPID, PnPClassName, PnPStatus, PnPRevision, PnPGuid, PnPTimestamp)
        VALUES (1, 'RepositoryDescriptor', 0, 4, ?, ?);
    """, (repo_guid, get_current_win_filetime()))

    conn.commit()


def add_catalog_family(conn, template_dict, family_desc, short_desc, script_name, sizes_list, end_type="SWAGELOK", skey="UN", pnp_class="Coupling", category="Fittings"):
    """
    Clona la fila de una plantilla oficial y aplica la estructura exacta de puertos de Plant 3D.
    """
    cursor = conn.cursor()
    family_guid = guid_to_bytes()
    win_filetime = get_current_win_filetime()

    print(f"\n[+] Añadiendo Familia: {family_desc} ({len(sizes_list)} tallas desde CSV)")

    for item in sizes_list:
        nd = item["nd"]
        part_num = item.get("part_num", "")
        size_desc = f"{family_desc} ND {nd}\" ({part_num})" if part_num else f"{family_desc} ND {nd}\""
        size_record_guid = guid_to_bytes()
        ports_count = item.get("ports_count", 2)

        # A. Crear PnPBase para la Parte
        part_pnp_id = get_next_pnp_id(cursor)
        part_guid = guid_to_bytes()
        cursor.execute("""
            INSERT INTO PnPBase (PnPID, PnPClassName, PnPStatus, PnPRevision, PnPGuid, PnPTimestamp)
            VALUES (?, ?, 0, 0, ?, ?);
        """, (part_pnp_id, pnp_class, part_guid, win_filetime))

        # B. Formatear la cadena de parámetros geométricos
        params = item.get("params", {})
        param_def = ",".join([f"{k}={v:.6f}" if isinstance(v, float) else f"{k}={v}" for k, v in params.items()])
        iso_def = f"TYPE={pnp_class.upper()},SKEY={skey}"

        # C. Rellenar diccionario de EngineeringItems (Incluye Puerto 1: S1)
        row_data = dict(template_dict)
        row_data["PnPID"] = part_pnp_id
        row_data["PartFamilyId"] = family_guid
        row_data["CatalogPartFamilyId"] = family_guid
        row_data["PartFamilyLongDesc"] = family_desc
        row_data["PartSizeLongDesc"] = size_desc
        row_data["ShortDescription"] = short_desc
        row_data["ItemCode"] = part_num or size_desc
        row_data["Manufacturer"] = "Swagelok"
        row_data["Material"] = "SS 316"
        row_data["MaterialCode"] = "316"
        row_data["NominalDiameter"] = nd
        row_data["NominalUnit"] = "in"
        row_data["MatchingPipeOd"] = item.get("OD", nd)
        row_data["EndType"] = end_type
        row_data["ContentGeometryParamDefinition"] = param_def
        row_data["ContentIsoSymbolDefinition"] = iso_def
        row_data["ContentGeometryTemplate"] = script_name
        row_data["SizeRecordId"] = size_record_guid
        row_data["ConnectionPortCount"] = ports_count
        
        row_data["PortName"] = "S1"
        row_data["LengthUnit"] = "in"
        row_data["PartCategory"] = category
        row_data["ContentDomain"] = "P3D"
        row_data["PartVersion"] = "5_0"
        row_data["WeightUnit"] = "LB"

        fields = list(row_data.keys())
        placeholders = ",".join(["?"] * len(fields))
        values = [row_data[k] for k in fields]

        query = f"INSERT INTO EngineeringItems ({','.join(fields)}) VALUES ({placeholders});"
        cursor.execute(query, values)

        cursor.execute("INSERT INTO PipeRunComponent (PnPID) VALUES (?);", (part_pnp_id,))
        try:
            cursor.execute(f"INSERT INTO `{pnp_class}` (PnPID) VALUES (?);", (part_pnp_id,))
        except Exception:
            pass

        # D. Registrar Puertos adicionales (S2, S3... SN)
        for p_idx in range(2, ports_count + 1):
            port_pnp_id = get_next_pnp_id(cursor)
            port_guid = guid_to_bytes()
            port_size_record_guid = guid_to_bytes()
            port_name = f"S{p_idx}"

            cursor.execute("""
                INSERT INTO PnPBase (PnPID, PnPClassName, PnPStatus, PnPRevision, PnPGuid, PnPTimestamp)
                VALUES (?, 'Port', 0, 0, ?, ?);
            """, (port_pnp_id, port_guid, win_filetime))

            cursor.execute("""
                INSERT INTO Port (
                    PnPID, SizeRecordId, PortName, NominalDiameter, NominalUnit,
                    MatchingPipeOd, EndType, LengthUnit
                ) VALUES (?, ?, ?, ?, 'in', ?, ?, 'in');
            """, (port_pnp_id, port_size_record_guid, port_name, nd, item.get("OD", nd), end_type))

            partport_pnp_id = get_next_pnp_id(cursor)
            partport_guid = guid_to_bytes()
            cursor.execute("""
                INSERT INTO PnPBase (PnPID, PnPClassName, PnPStatus, PnPRevision, PnPGuid, PnPTimestamp)
                VALUES (?, 'PartPort', 0, 0, ?, ?);
            """, (partport_pnp_id, partport_guid, win_filetime))

            cursor.execute("""
                INSERT INTO PartPort (PnPID, PnPGuid, PnPTimestamp, Part, Port, Name)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (partport_pnp_id, partport_guid, win_filetime, part_pnp_id, port_pnp_id, port_name))

            cursor.execute("""
                INSERT INTO PnPRowRelations (ROWID, RELID, RelationshipTypeName)
                VALUES (?, ?, 'PartPort');
            """, (part_pnp_id, partport_pnp_id))

        print(f"  - Talla PnPID {part_pnp_id}: ND {nd}\" ({part_num}) | {ports_count} Puertos | Script: {script_name}")

    conn.commit()


def remove_redundant_catalogs(target_dir=DEFAULT_TARGET_DIR):
    """Elimina archivos .pcat secundarios para asegurar limpieza."""
    redundant_files = [
        target_dir / "Swagelok_Custom_Catalog.pcat",
        target_dir / "Swagelok_Cloned_Catalog.pcat",
        REPO_ROOT / "Swagelok_Custom_Catalog.pcat",
        REPO_ROOT / "Swagelok_Cloned_Catalog.pcat",
    ]
    for f in redundant_files:
        if f.exists():
            try:
                f.unlink()
                print(f"Eliminado catálogo redundante: {f.name}")
            except Exception as e:
                print(f"No se pudo eliminar {f.name}: {e}")


def load_families_from_json_manifest(conn, templates_dict, manifest_path: Path):
    """
    Carga familias de componentes directamente desde un archivo manifest.json y modelos JSON
    generados por catalog-scrap, eliminando totalmente la necesidad de archivos .csv.
    """
    if not manifest_path.exists():
        print(f"ERROR: No existe el archivo manifest.json en {manifest_path}")
        return

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    catalog_dir = manifest_path.parent
    models = manifest.get("models", [])
    print(f"\n[+] Cargando {len(models)} modelos desde JSON manifest ({manifest_path.name}):\n")

    for model_meta in models:
        model_file = model_meta.get("file")
        if not model_file:
            continue

        model_json_path = catalog_dir / model_file
        if not model_json_path.exists():
            print(f"AVISO: No se encontró el archivo de modelo {model_json_path}")
            continue

        with open(model_json_path, "r", encoding="utf-8") as mf:
            model_data = json.load(mf)

        model_name = model_data.get("model", model_meta.get("model"))
        family_desc = f"{model_data.get('manufacturer', '')} {model_name} {model_data.get('valve_type', '')}".strip()
        short_desc = f"{model_name} {model_data.get('valve_type', '')}".strip()
        script_name = model_data.get("geometry_template", "BALL_VALVE_2PC_FLANGED")

        items = model_data.get("items", [])
        sizes_list = []

        for it in items:
            dn_mm = it.get("DN_mm", 15)
            # Convert DN/NPS to inches (nd)
            nd = round(dn_mm / 25.4, 4) if dn_mm else 0.5

            l_in = round(it.get("L_mm", 0.0) / 25.4, 4)
            d_in = round(it.get("D_mm", 0.0) / 25.4, 4)
            h_in = round(it.get("H_mm", 0.0) / 25.4, 4)
            l1_in = round(it.get("L1_mm", 0.0) / 25.4, 4)
            e_in = round(it.get("E_mm", 0.0) / 25.4, 4)

            # End type: FL if flanged (D_mm > 0), PL if tubing
            end_type = "FL" if d_in > 0 else "PL"

            params = {
                "OD": nd,
                "L": l_in,
                "H": h_in
            }
            if d_in > 0:
                params["D"] = d_in
            if l1_in > 0:
                params["L1"] = l1_in
            if e_in > 0:
                params["E"] = e_in

            sizes_list.append({
                "nd": nd,
                "part_num": it.get("Part_Number", f"{model_name}-{nd}"),
                "OD": nd,
                "ports_count": 2,
                "params": params
            })

        pnp_class_name = "ValveBody"
        template_dict = templates_dict.get(pnp_class_name, templates_dict["Coupling"])

        add_catalog_family(
            conn,
            template_dict=template_dict,
            family_desc=family_desc,
            short_desc=short_desc,
            script_name=script_name,
            skey="VB",
            end_type="FL",
            pnp_class=pnp_class_name,
            category="Valves",
            sizes_list=sizes_list
        )


def load_families_from_csv(conn, templates_dict, source_dir):
    """
    Escanea dinámicamente la carpeta fuente en busca de archivos .csv
    y procesa cada familia de componentes de forma 100% desacoplada.
    """
    if not source_dir.exists():
        print(f"ERROR: No existe la carpeta {source_dir}")
        return

    csv_files = sorted(source_dir.rglob("*.csv"))
    print(f"\n[+] Se encontraron {len(csv_files)} archivos CSV de familias en {source_dir.name}/:\n")

    for csv_path in csv_files:
        py_path = csv_path.with_suffix(".py")
        if py_path.exists():
            script_name = find_registration_name(py_path)
        else:
            rel_path = csv_path.relative_to(source_dir)
            family_folder = rel_path.parts[0] if len(rel_path.parts) > 1 else csv_path.stem
            component_stem = csv_path.stem
            script_name = f"{family_folder}.{component_stem}"

        families_in_csv = {}  # family_desc -> {meta, sizes_list}

        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                family_desc = row["family_desc"]
                nd = float(row["nd"])
                part_num = row["part_num"]
                od = float(row["OD"])
                ports_count = int(row.get("ports_count", 2))
                end_type = row.get("end_type", "SWAGELOK")
                skey = row.get("skey", "UN")
                pnp_class = row.get("pnp_class", "Coupling")
                category = row.get("category", "Fittings")
                short_desc = row["short_desc"]

                if family_desc not in families_in_csv:
                    families_in_csv[family_desc] = {
                        "meta": {
                            "family_desc": family_desc,
                            "short_desc": short_desc,
                            "end_type": end_type,
                            "skey": skey,
                            "pnp_class": pnp_class,
                            "category": category,
                            "script_name": script_name
                        },
                        "sizes_list": []
                    }

                # Extraer parámetros geométricos no vacíos
                params = {}
                for k in ["OD", "D", "L", "A", "H", "E", "T", "F", "NL", "DX", "OD1", "RO", "RI", "W", "B", "C", "G", "L1"]:
                    val = row.get(k, "").strip() if row.get(k) else ""
                    if val:
                        params[k] = float(val)

                families_in_csv[family_desc]["sizes_list"].append({
                    "nd": nd,
                    "part_num": part_num,
                    "OD": od,
                    "ports_count": ports_count,
                    "params": params
                })

        for family_desc, fam_data in families_in_csv.items():
            family_meta = fam_data["meta"]
            sizes_list = fam_data["sizes_list"]
            pnp_class_name = family_meta["pnp_class"]
            template_dict = templates_dict.get(pnp_class_name, templates_dict["Coupling"])

            add_catalog_family(
                conn,
                template_dict=template_dict,
                family_desc=family_meta["family_desc"],
                short_desc=family_meta["short_desc"],
                script_name=family_meta["script_name"],
                skey=family_meta["skey"],
                end_type=family_meta["end_type"],
                pnp_class=family_meta["pnp_class"],
                category=family_meta["category"],
                sizes_list=sizes_list
            )


def build_single_catalog(catalog_dir, output_pcat=None, target_dir=DEFAULT_TARGET_DIR, json_manifest=None):
    if json_manifest:
        manifest_path = Path(json_manifest)
        catalog_title = manifest_path.parent.name.replace("_", " ").title()
        if output_pcat is None:
            output_pcat = target_dir / f"{catalog_title.replace(' ', '_')}_Catalog.pcat"
        output_pcat = Path(output_pcat)

        print(f"\n=== CONSTRUYENDO CATÁLOGO JSON-DRIVEN: {catalog_title} ({output_pcat.name}) ===\n")
        if prepare_base_catalog(output_pcat, TEMPLATE_PCAT, catalog_title) is False:
            return None

        conn = sqlite3.connect(output_pcat)
        cursor = conn.cursor()

        def load_template(pnp_id):
            cursor.execute("SELECT * FROM EngineeringItems WHERE PnPID = ?;", (pnp_id,))
            row = cursor.fetchone()
            cols = [c[0] for c in cursor.description]
            return dict(zip(cols, row))

        templates_dict = {
            "Coupling": load_template(2252),
            "Elbow": load_template(88),
            "Tee": load_template(1682),
            "Cross": load_template(573),
            "Reducer": load_template(3771),
            "Cap": load_template(807),
            "Plug": load_template(1413),
            "ValveBody": load_template(1916)
        }

        clean_all_data_tables(conn)
        load_families_from_json_manifest(conn, templates_dict, manifest_path)

        conn.close()
        remove_redundant_catalogs(output_pcat.parent)
        print(f"\n[OK] Catálogo JSON-Driven {catalog_title} generado con éxito en: {output_pcat.resolve()}")
        return output_pcat

    catalog_key = catalog_dir.name
    catalog_title = catalog_key.replace("_", " ").title()
    if output_pcat is None:
        output_pcat = target_dir / f"{catalog_title.replace(' ', '_')}_Catalog.pcat"
    output_pcat = Path(output_pcat)

    print(f"\n=== CONSTRUYENDO CATÁLOGO DESACOPLADO: {catalog_title} ({output_pcat.name}) ===\n")
    if prepare_base_catalog(output_pcat, TEMPLATE_PCAT, catalog_title) is False:
        return None

    conn = sqlite3.connect(output_pcat)
    cursor = conn.cursor()

    # Cargar diccionarios plantilla para cada clase PnP
    def load_template(pnp_id):
        cursor.execute("SELECT * FROM EngineeringItems WHERE PnPID = ?;", (pnp_id,))
        row = cursor.fetchone()
        cols = [c[0] for c in cursor.description]
        return dict(zip(cols, row))

    templates_dict = {
        "Coupling": load_template(2252),
        "Elbow": load_template(88),
        "Tee": load_template(1682),
        "Cross": load_template(573),
        "Reducer": load_template(3771),
        "Cap": load_template(807),
        "Plug": load_template(1413),
        "ValveBody": load_template(1916)
    }

    # Limpieza exhaustiva de TODAS las tablas de datos para eliminar huérfanos
    clean_all_data_tables(conn)

    # Cargar dinámicamente todas las familias desde la carpeta fuente (CSV legacy)
    load_families_from_csv(conn, templates_dict, catalog_dir)

    conn.close()

    # Eliminar copias redundantes anteriores
    remove_redundant_catalogs(output_pcat.parent)

    print(f"\n[OK] Catálogo {catalog_title} generado con éxito en: {output_pcat.resolve()}")
    return output_pcat


def build_all_catalogs(target_dir=DEFAULT_TARGET_DIR, selected_catalog=None, output_pcat_override=None, json_manifest=None):
    if json_manifest:
        out_p = Path(output_pcat_override) if output_pcat_override else None
        return [build_single_catalog(Path("."), out_p, target_dir, json_manifest=json_manifest)]

    catalogs_dir = REPO_ROOT / "src" / "catalogs"
    built = []

    if selected_catalog:
        cat_dir = catalogs_dir / selected_catalog
        if not cat_dir.is_dir():
            cat_dir = REPO_ROOT / "src" / "families"
        out_p = Path(output_pcat_override) if output_pcat_override else None
        built.append(build_single_catalog(cat_dir, out_p, target_dir))
    else:
        if catalogs_dir.is_dir():
            for sub_dir in sorted(catalogs_dir.iterdir()):
                if sub_dir.is_dir() and not sub_dir.name.startswith("_"):
                    built.append(build_single_catalog(sub_dir, None, target_dir))
        if not built and (REPO_ROOT / "src" / "families").is_dir():
            built.append(build_single_catalog(REPO_ROOT / "src" / "families", None, target_dir))

    return built


def main():
    parser = argparse.ArgumentParser(description="Generador de Catálogos SQLite .pcat para Plant 3D")
    parser.add_argument(
        "--output-pcat",
        type=str,
        default=None,
        help="Ruta personalizada de salida para el archivo .pcat generado"
    )
    parser.add_argument(
        "--catalog",
        type=str,
        default=None,
        help="Nombre del catálogo a compilar (ej: swagelok, klinger_intec)"
    )
    parser.add_argument(
        "--json-manifest",
        type=str,
        default=None,
        help="Ruta al archivo manifest.json generado por catalog-scrap para construcción JSON-Driven"
    )
    parser.add_argument(
        "--target-dir",
        type=str,
        default=str(DEFAULT_TARGET_DIR),
        help="Carpeta destino para guardar los catálogos .pcat"
    )

    args = parser.parse_args()
    target_dir = Path(args.target_dir)

    build_all_catalogs(target_dir, selected_catalog=args.catalog, output_pcat_override=args.output_pcat, json_manifest=args.json_manifest)


if __name__ == "__main__":
    main()
