"""
build_catalog.py - Generador automatizado y DESACOPLADO de catálogo .pcat (SQLite3) para Plant 3D 2027.

Escanea dinámicamente todos los archivos .csv en src/families/ para construir el catálogo
sin tener datos de dimensiones hardcodeados en el código Python.

Uso:
    python build_catalog.py
"""
import os
import sys
import csv
import uuid
try:
    import sqlite3
except ImportError:
    sqlite3 = None
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FAMILIES_DIR = ROOT / "src" / "families"
TEMPLATE_PCAT = Path(r"C:\AutoCAD Plant 3D 2027 Content\CPak Common\CustomParts Imperial Catalog.pcat")
OUTPUT_PCAT = ROOT / "Swagelok_Catalog.pcat"

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


def prepare_base_catalog():
    """Copia la plantilla base de catálogo .pcat limpia y asigna un GUID único de catálogo."""
    if OUTPUT_PCAT.exists():
        try:
            OUTPUT_PCAT.unlink()
        except PermissionError:
            print(f"ERROR: {OUTPUT_PCAT.name} está bloqueado por AutoCAD Plant 3D Spec Editor.")
            print("Por favor, cierra el catálogo en el Spec Editor e inténtalo de nuevo.")
            sys.exit(1)

    shutil.copy2(TEMPLATE_PCAT, OUTPUT_PCAT)

    conn = sqlite3.connect(OUTPUT_PCAT)
    cursor = conn.cursor()

    # 1. Asignar un RepositoryID GUID 100% ÚNICO para evitar colisión de catálogos en Spec Editor
    new_repo_guid = f"{{{uuid.uuid4()}}}"
    new_db_guid = guid_to_bytes()

    cursor.execute("""
        UPDATE RepositoryDescriptor
        SET RepositoryID = ?, Name = 'Swagelok Catalog', Description = 'Swagelok Custom Component Catalog'
        WHERE PnPID = 1;
    """, (new_repo_guid,))

    cursor.execute("""
        UPDATE PnPDatabase
        SET DBID = ?;
    """, (new_db_guid,))

    conn.commit()
    conn.close()

    print(f"Catálogo base asignado con nuevo RepositoryID {new_repo_guid} en: {OUTPUT_PCAT.name}")


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


def remove_redundant_catalogs():
    """Elimina archivos .pcat secundarios para asegurar que sólo exista un único catálogo."""
    redundant_files = [
        ROOT / "Swagelok_Custom_Catalog.pcat",
        ROOT / "Swagelok_Cloned_Catalog.pcat"
    ]
    for f in redundant_files:
        if f.exists():
            try:
                f.unlink()
                print(f"Eliminado catálogo redundante: {f.name}")
            except Exception as e:
                print(f"No se pudo eliminar {f.name}: {e}")


def load_families_from_csv(conn, templates_dict):
    """
    Escanea dinámicamente la carpeta src/families/ en busca de archivos .csv
    y procesa cada familia de componentes de forma 100% desacoplada.
    """
    if not FAMILIES_DIR.exists():
        print(f"ERROR: No existe la carpeta {FAMILIES_DIR}")
        return

    csv_files = sorted(FAMILIES_DIR.rglob("*.csv"))
    print(f"\n[+] Se encontraron {len(csv_files)} archivos CSV de familias en {FAMILIES_DIR.name}/:\n")

    for csv_path in csv_files:
        py_path = csv_path.with_suffix(".py")
        if py_path.exists():
            from build import find_registration_name
            script_name = find_registration_name(py_path)
        else:
            family_folder = rel_path.parts[0]
            component_stem = csv_path.stem
            script_name = f"{family_folder}.{component_stem}"

        sizes_list = []
        family_meta = {}

        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                nd = float(row["nd"])
                part_num = row["part_num"]
                od = float(row["OD"])
                ports_count = int(row.get("ports_count", 2))
                end_type = row.get("end_type", "SWAGELOK")
                skey = row.get("skey", "UN")
                pnp_class = row.get("pnp_class", "Coupling")
                category = row.get("category", "Fittings")
                family_desc = row["family_desc"]
                short_desc = row["short_desc"]

                # Extraer parámetros geométricos no vacíos (OD, L, H, T, OD1, etc.)
                params = {}
                for k in ["OD", "L", "H", "T", "OD1"]:
                    val = row.get(k, "").strip() if row.get(k) else ""
                    if val:
                        params[k] = float(val)

                sizes_list.append({
                    "nd": nd,
                    "part_num": part_num,
                    "OD": od,
                    "ports_count": ports_count,
                    "params": params
                })

                family_meta = {
                    "family_desc": family_desc,
                    "short_desc": short_desc,
                    "end_type": end_type,
                    "skey": skey,
                    "pnp_class": pnp_class,
                    "category": category,
                    "script_name": script_name
                }

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


def build_swagelok_catalog():
    print("=== CONSTRUYENDO CATÁLOGO DESACOPLADO DESDE ARCHIVOS CSV SWAGELOK .PCAT ===\n")
    prepare_base_catalog()

    conn = sqlite3.connect(OUTPUT_PCAT)
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

    # Cargar dinámicamente todas las familias desde src/families/**/*.csv
    load_families_from_csv(conn, templates_dict)

    conn.close()

    # Eliminar copias redundantes anteriores
    remove_redundant_catalogs()

    print(f"\n[OK] Catálogo desacoplado generado con éxito en: {OUTPUT_PCAT.resolve()}")


if __name__ == "__main__":
    build_swagelok_catalog()
