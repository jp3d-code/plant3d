"""
build_catalog.py - Generador automatizado de catálogo .pcat (SQLite3) completo para Swagelok en Plant 3D 2027.

Incluye todas las familias de componentes:
- Uniones Rectas, Reductoras y Pasamuros (Coupling)
- Codos de 90° y 45° (Elbow)
- Tees y Cruces (Tee, Cross)
- Conectores Macho y Hembra (Coupling / Nipple)
- Tapones y Racores (Cap, Plug)
- Válvulas de Bola y Aguja (ValveBody)

Utiliza la estructura de puertos exacta de Autodesk Plant 3D:
- S1 definido en EngineeringItems.
- S2..SN definidos individualmente en Port, PartPort y PnPRowRelations.

Uso:
    python build_catalog.py
"""
import os
import sys
import uuid
import sqlite3
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
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
    - S1 se define en las columnas de EngineeringItems.
    - S2..SN se definen individualmente en las tablas Port, PartPort y PnPRowRelations.
    """
    cursor = conn.cursor()
    family_guid = guid_to_bytes()  # GUID ÚNICO COMPARTIDO POR TODAS LAS TALLAS DE LA FAMILIA
    win_filetime = get_current_win_filetime()

    print(f"\n[+] Añadiendo Familia: {family_desc} ({len(sizes_list)} tallas)")

    for item in sizes_list:
        nd = item["nd"]
        part_num = item.get("part_num", "")
        size_desc = f"{family_desc} ND {nd}\" ({part_num})" if part_num else f"{family_desc} ND {nd}\""
        size_record_guid = guid_to_bytes()
        ports_count = item.get("ports_count", 2)

        # A. Crear PnPBase para la Parte (Coupling, Elbow, Tee, Cross, Cap, Plug, ValveBody, etc.)
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

        # C. Rellenar diccionario de EngineeringItems (Incluye la definición del Puerto 1: S1)
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
        
        # Atributos explícitos de Puerto 1 (S1) en EngineeringItems
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

        # D. Registrar Puertos adicionales (S2, S3... SN) en Port, PartPort y PnPRowRelations
        for p_idx in range(2, ports_count + 1):
            port_pnp_id = get_next_pnp_id(cursor)
            port_guid = guid_to_bytes()
            port_size_record_guid = guid_to_bytes()
            port_name = f"S{p_idx}"

            # 1. PnPBase para el Puerto
            cursor.execute("""
                INSERT INTO PnPBase (PnPID, PnPClassName, PnPStatus, PnPRevision, PnPGuid, PnPTimestamp)
                VALUES (?, 'Port', 0, 0, ?, ?);
            """, (port_pnp_id, port_guid, win_filetime))

            # 2. Fila en Port
            cursor.execute("""
                INSERT INTO Port (
                    PnPID, SizeRecordId, PortName, NominalDiameter, NominalUnit,
                    MatchingPipeOd, EndType, LengthUnit
                ) VALUES (?, ?, ?, ?, 'in', ?, ?, 'in');
            """, (port_pnp_id, port_size_record_guid, port_name, nd, item.get("OD", nd), end_type))

            # 3. PnPBase para PartPort
            partport_pnp_id = get_next_pnp_id(cursor)
            partport_guid = guid_to_bytes()
            cursor.execute("""
                INSERT INTO PnPBase (PnPID, PnPClassName, PnPStatus, PnPRevision, PnPGuid, PnPTimestamp)
                VALUES (?, 'PartPort', 0, 0, ?, ?);
            """, (partport_pnp_id, partport_guid, win_filetime))

            # 4. Fila en PartPort vinculando la Parte con el Puerto adicional
            cursor.execute("""
                INSERT INTO PartPort (PnPID, PnPGuid, PnPTimestamp, Part, Port, Name)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (partport_pnp_id, partport_guid, win_filetime, part_pnp_id, port_pnp_id, port_name))

            # 5. Relación en PnPRowRelations
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


def build_swagelok_catalog():
    print("=== CONSTRUYENDO CATÁLOGO COMPLETO SWAGELOK .PCAT ===\n")
    prepare_base_catalog()

    conn = sqlite3.connect(OUTPUT_PCAT)
    cursor = conn.cursor()

    # Cargar diccionarios plantilla para cada clase PnP
    def load_template(pnp_id):
        cursor.execute("SELECT * FROM EngineeringItems WHERE PnPID = ?;", (pnp_id,))
        row = cursor.fetchone()
        cols = [c[0] for c in cursor.description]
        return dict(zip(cols, row))

    tpl_coupling = load_template(2252) # Coupling
    tpl_elbow = load_template(88)      # Elbow
    tpl_tee = load_template(1682)      # Tee
    tpl_cross = load_template(573)     # Cross
    tpl_reducer = load_template(3771)  # Reducer
    tpl_cap = load_template(807)       # Cap
    tpl_plug = load_template(1413)     # Plug
    tpl_valve = load_template(1916)    # ValveBody

    # Limpieza exhaustiva de TODAS las tablas de datos para eliminar huérfanos
    clean_all_data_tables(conn)

    # 1. Uniones Rectas (straight.union)
    add_catalog_family(
        conn, template_dict=tpl_coupling,
        family_desc="Swagelok Straight Union", short_desc="Swagelok Union",
        script_name="straight.union", skey="UN", pnp_class="Coupling", category="Fittings",
        sizes_list=[
            {"nd": 0.0625, "part_num": "SS-100-6", "OD": 0.0625, "params": {"OD": 0.0625, "L": 0.99, "T": 0.010}},
            {"nd": 0.125,  "part_num": "SS-200-6", "OD": 0.125,  "params": {"OD": 0.125,  "L": 1.40, "T": 0.028}},
            {"nd": 0.1875, "part_num": "SS-300-6", "OD": 0.1875, "params": {"OD": 0.1875, "L": 1.47, "T": 0.030}},
            {"nd": 0.250,  "part_num": "SS-400-6", "OD": 0.250,  "params": {"OD": 0.250,  "L": 1.61, "T": 0.048}},
            {"nd": 0.3125, "part_num": "SS-500-6", "OD": 0.3125, "params": {"OD": 0.3125, "L": 1.69, "T": 0.055}},
            {"nd": 0.375,  "part_num": "SS-600-6", "OD": 0.375,  "params": {"OD": 0.375,  "L": 1.77, "T": 0.065}},
            {"nd": 0.500,  "part_num": "SS-810-6", "OD": 0.500,  "params": {"OD": 0.500,  "L": 2.02, "T": 0.065}},
            {"nd": 0.625,  "part_num": "SS-1010-6","OD": 0.625,  "params": {"OD": 0.625,  "L": 2.05, "T": 0.065}},
            {"nd": 0.750,  "part_num": "SS-1210-6","OD": 0.750,  "params": {"OD": 0.750,  "L": 2.11, "T": 0.075}},
            {"nd": 0.875,  "part_num": "SS-1410-6","OD": 0.875,  "params": {"OD": 0.875,  "L": 2.17, "T": 0.083}},
            {"nd": 1.000,  "part_num": "SS-1610-6","OD": 1.000,  "params": {"OD": 1.000,  "L": 2.55, "T": 0.095}},
        ]
    )

    # 2. Uniones Reductoras (straight.reducing_union)
    add_catalog_family(
        conn, template_dict=tpl_coupling,
        family_desc="Swagelok Reducing Union", short_desc="Swagelok Red. Union",
        script_name="straight.reducing_union", skey="UN", pnp_class="Coupling", category="Fittings",
        sizes_list=[
            {"nd": 0.250, "part_num": "SS-400-6-2", "OD": 0.250, "params": {"OD": 0.250, "OD1": 0.125, "L": 1.52, "T": 0.048}},
            {"nd": 0.375, "part_num": "SS-600-6-4", "OD": 0.375, "params": {"OD": 0.375, "OD1": 0.250, "L": 1.70, "T": 0.065}},
            {"nd": 0.500, "part_num": "SS-810-6-4", "OD": 0.500, "params": {"OD": 0.500, "OD1": 0.250, "L": 1.85, "T": 0.065}},
            {"nd": 0.500, "part_num": "SS-810-6-6", "OD": 0.500, "params": {"OD": 0.500, "OD1": 0.375, "L": 1.91, "T": 0.065}},
            {"nd": 0.750, "part_num": "SS-1210-6-8","OD": 0.750, "params": {"OD": 0.750, "OD1": 0.500, "L": 2.07, "T": 0.075}},
            {"nd": 1.000, "part_num": "SS-1610-6-12","OD": 1.000,"params": {"OD": 1.000, "OD1": 0.750, "L": 2.38, "T": 0.095}},
        ]
    )

    # 3. Uniones Pasamuros (straight.bulkhead_union)
    add_catalog_family(
        conn, template_dict=tpl_coupling,
        family_desc="Swagelok Bulkhead Union", short_desc="Swagelok Bulkhead Union",
        script_name="straight.bulkhead_union", skey="UN", pnp_class="Coupling", category="Fittings",
        sizes_list=[
            {"nd": 0.125, "part_num": "SS-200-61", "OD": 0.125, "params": {"OD": 0.125, "L": 2.02, "T": 0.028}},
            {"nd": 0.250, "part_num": "SS-400-61", "OD": 0.250, "params": {"OD": 0.250, "L": 2.27, "T": 0.048}},
            {"nd": 0.375, "part_num": "SS-600-61", "OD": 0.375, "params": {"OD": 0.375, "L": 2.45, "T": 0.065}},
            {"nd": 0.500, "part_num": "SS-810-61", "OD": 0.500, "params": {"OD": 0.500, "L": 2.80, "T": 0.065}},
            {"nd": 1.000, "part_num": "SS-1610-61","OD": 1.000, "params": {"OD": 1.000, "L": 3.69, "T": 0.095}},
        ]
    )

    # 4. Codos de 90° Unión (elbows.elbow_90)
    add_catalog_family(
        conn, template_dict=tpl_elbow,
        family_desc="Swagelok 90° Union Elbow", short_desc="Swagelok 90° Elbow",
        script_name="elbows.elbow_90", skey="EL", pnp_class="Elbow", category="Fittings",
        sizes_list=[
            {"nd": 0.0625, "part_num": "SS-100-9", "OD": 0.0625, "params": {"OD": 0.0625, "L": 0.70, "T": 0.010}},
            {"nd": 0.125,  "part_num": "SS-200-9", "OD": 0.125,  "params": {"OD": 0.125,  "L": 0.88, "T": 0.028}},
            {"nd": 0.1875, "part_num": "SS-300-9", "OD": 0.1875, "params": {"OD": 0.1875, "L": 1.00, "T": 0.030}},
            {"nd": 0.250,  "part_num": "SS-400-9", "OD": 0.250,  "params": {"OD": 0.250,  "L": 1.06, "T": 0.048}},
            {"nd": 0.3125, "part_num": "SS-500-9", "OD": 0.3125, "params": {"OD": 0.3125, "L": 1.13, "T": 0.055}},
            {"nd": 0.375,  "part_num": "SS-600-9", "OD": 0.375,  "params": {"OD": 0.375,  "L": 1.20, "T": 0.065}},
            {"nd": 0.500,  "part_num": "SS-810-9", "OD": 0.500,  "params": {"OD": 0.500,  "L": 1.42, "T": 0.065}},
            {"nd": 0.750,  "part_num": "SS-1210-9","OD": 0.750,  "params": {"OD": 0.750,  "L": 1.57, "T": 0.075}},
            {"nd": 1.000,  "part_num": "SS-1610-9","OD": 1.000,  "params": {"OD": 1.000,  "L": 1.93, "T": 0.095}},
        ]
    )

    # 5. Codos de 45° Unión (elbows.elbow_45)
    add_catalog_family(
        conn, template_dict=tpl_elbow,
        family_desc="Swagelok 45° Union Elbow", short_desc="Swagelok 45° Elbow",
        script_name="elbows.elbow_45", skey="EL", pnp_class="Elbow", category="Fittings",
        sizes_list=[
            {"nd": 0.125, "part_num": "SS-200-9-45", "OD": 0.125, "params": {"OD": 0.125, "L": 0.73, "T": 0.028}},
            {"nd": 0.250, "part_num": "SS-400-9-45", "OD": 0.250, "params": {"OD": 0.250, "L": 0.83, "T": 0.048}},
            {"nd": 0.375, "part_num": "SS-600-9-45", "OD": 0.375, "params": {"OD": 0.375, "L": 0.87, "T": 0.065}},
            {"nd": 0.500, "part_num": "SS-810-9-45", "OD": 0.500, "params": {"OD": 0.500, "L": 0.98, "T": 0.065}},
            {"nd": 1.000, "part_num": "SS-1610-9-45","OD": 1.000, "params": {"OD": 1.000, "L": 1.31, "T": 0.095}},
        ]
    )

    # 6. Codos de 90° Macho NPT (elbows.male_elbow_90)
    add_catalog_family(
        conn, template_dict=tpl_elbow,
        family_desc="Swagelok 90° Male NPT Elbow", short_desc="Swagelok Male Elbow",
        script_name="elbows.male_elbow_90", skey="EL", pnp_class="Elbow", category="Fittings",
        sizes_list=[
            {"nd": 0.125, "part_num": "SS-200-2-2", "OD": 0.125, "params": {"OD": 0.125, "L": 0.88, "H": 0.72, "T": 0.028}},
            {"nd": 0.250, "part_num": "SS-400-2-4", "OD": 0.250, "params": {"OD": 0.250, "L": 1.06, "H": 1.00, "T": 0.048}},
            {"nd": 0.375, "part_num": "SS-600-2-6", "OD": 0.375, "params": {"OD": 0.375, "L": 1.20, "H": 1.14, "T": 0.065}},
            {"nd": 0.500, "part_num": "SS-810-2-8", "OD": 0.500, "params": {"OD": 0.500, "L": 1.42, "H": 1.50, "T": 0.065}},
            {"nd": 1.000, "part_num": "SS-1610-2-16","OD": 1.000,"params": {"OD": 1.000, "L": 1.93, "H": 1.90, "T": 0.095}},
        ]
    )

    # 7. Tees Unión Igual (tees.union_tee)
    add_catalog_family(
        conn, template_dict=tpl_tee,
        family_desc="Swagelok Union Tee", short_desc="Swagelok Union Tee",
        script_name="tees.union_tee", skey="TE", pnp_class="Tee", category="Fittings",
        sizes_list=[
            {"nd": 0.0625, "part_num": "SS-100-3", "OD": 0.0625, "ports_count": 3, "params": {"OD": 0.0625, "L": 1.40, "H": 0.70, "T": 0.010}},
            {"nd": 0.125,  "part_num": "SS-200-3", "OD": 0.125,  "ports_count": 3, "params": {"OD": 0.125,  "L": 1.76, "H": 0.88, "T": 0.028}},
            {"nd": 0.1875, "part_num": "SS-300-3", "OD": 0.1875, "ports_count": 3, "params": {"OD": 0.1875, "L": 1.92, "H": 0.96, "T": 0.030}},
            {"nd": 0.250,  "part_num": "SS-400-3", "OD": 0.250,  "ports_count": 3, "params": {"OD": 0.250,  "L": 2.12, "H": 1.06, "T": 0.048}},
            {"nd": 0.3125, "part_num": "SS-500-3", "OD": 0.3125, "ports_count": 3, "params": {"OD": 0.3125, "L": 2.34, "H": 1.17, "T": 0.055}},
            {"nd": 0.375,  "part_num": "SS-600-3", "OD": 0.375,  "ports_count": 3, "params": {"OD": 0.375,  "L": 2.40, "H": 1.20, "T": 0.065}},
            {"nd": 0.500,  "part_num": "SS-810-3", "OD": 0.500,  "ports_count": 3, "params": {"OD": 0.500,  "L": 2.84, "H": 1.42, "T": 0.065}},
            {"nd": 0.750,  "part_num": "SS-1210-3","OD": 0.750,  "ports_count": 3, "params": {"OD": 0.750,  "L": 3.14, "H": 1.57, "T": 0.075}},
            {"nd": 1.000,  "part_num": "SS-1610-3","OD": 1.000,  "ports_count": 3, "params": {"OD": 1.000,  "L": 3.86, "H": 1.93, "T": 0.095}},
        ]
    )

    # 8. Cruces Unión Igual (crosses.union_cross)
    add_catalog_family(
        conn, template_dict=tpl_cross,
        family_desc="Swagelok Union Cross", short_desc="Swagelok Union Cross",
        script_name="crosses.union_cross", skey="CR", pnp_class="Cross", category="Fittings",
        sizes_list=[
            {"nd": 0.125, "part_num": "SS-200-4", "OD": 0.125, "ports_count": 4, "params": {"OD": 0.125, "L": 1.76, "H": 0.88, "T": 0.028}},
            {"nd": 0.250, "part_num": "SS-400-4", "OD": 0.250, "ports_count": 4, "params": {"OD": 0.250, "L": 2.12, "H": 1.06, "T": 0.048}},
            {"nd": 0.375, "part_num": "SS-600-4", "OD": 0.375, "ports_count": 4, "params": {"OD": 0.375, "L": 2.40, "H": 1.20, "T": 0.065}},
            {"nd": 0.500, "part_num": "SS-810-4", "OD": 0.500, "ports_count": 4, "params": {"OD": 0.500, "L": 2.84, "H": 1.42, "T": 0.065}},
            {"nd": 1.000, "part_num": "SS-1610-4","OD": 1.000, "ports_count": 4, "params": {"OD": 1.000, "L": 3.86, "H": 1.93, "T": 0.095}},
        ]
    )

    # 9. Conectores Macho NPT (male.male_connector)
    add_catalog_family(
        conn, template_dict=tpl_coupling,
        family_desc="Swagelok Male Connector NPT", short_desc="Swagelok Male Conn.",
        script_name="male.male_connector", skey="CN", pnp_class="Coupling", category="Fittings",
        sizes_list=[
            {"nd": 0.125, "part_num": "SS-200-1-2", "OD": 0.125, "params": {"OD": 0.125, "L": 1.20, "T": 0.028}},
            {"nd": 0.250, "part_num": "SS-400-1-4", "OD": 0.250, "params": {"OD": 0.250, "L": 1.49, "T": 0.048}},
            {"nd": 0.375, "part_num": "SS-600-1-6", "OD": 0.375, "params": {"OD": 0.375, "L": 1.57, "T": 0.065}},
            {"nd": 0.500, "part_num": "SS-810-1-8", "OD": 0.500, "params": {"OD": 0.500, "L": 1.86, "T": 0.065}},
            {"nd": 1.000, "part_num": "SS-1610-1-16","OD": 1.000,"params": {"OD": 1.000, "L": 2.26, "T": 0.095}},
        ]
    )

    # 10. Tapones de Tubo (plugs.tube_cap)
    add_catalog_family(
        conn, template_dict=tpl_cap,
        family_desc="Swagelok Tube Cap", short_desc="Swagelok Cap",
        script_name="plugs.tube_cap", skey="CP", pnp_class="Cap", category="Fittings",
        sizes_list=[
            {"nd": 0.125, "part_num": "SS-200-C", "OD": 0.125, "ports_count": 1, "params": {"OD": 0.125, "L": 0.60, "T": 0.028}},
            {"nd": 0.250, "part_num": "SS-400-C", "OD": 0.250, "ports_count": 1, "params": {"OD": 0.250, "L": 0.68, "T": 0.048}},
            {"nd": 0.375, "part_num": "SS-600-C", "OD": 0.375, "ports_count": 1, "params": {"OD": 0.375, "L": 0.72, "T": 0.065}},
            {"nd": 0.500, "part_num": "SS-810-C", "OD": 0.500, "ports_count": 1, "params": {"OD": 0.500, "L": 0.88, "T": 0.065}},
            {"nd": 1.000, "part_num": "SS-1610-C","OD": 1.000, "ports_count": 1, "params": {"OD": 1.000, "L": 1.13, "T": 0.095}},
        ]
    )

    # 11. Válvulas de Bola (valves.ball_valve_2way)
    add_catalog_family(
        conn, template_dict=tpl_valve,
        family_desc="Swagelok 40 Series 2-Way Ball Valve", short_desc="Swagelok Ball Valve",
        script_name="valves.ball_valve_2way", skey="VB", pnp_class="ValveBody", category="Valves",
        sizes_list=[
            {"nd": 0.125, "part_num": "SS-41S2", "OD": 0.125, "params": {"OD": 0.125, "L": 2.11, "H": 1.50, "T": 0.028}},
            {"nd": 0.250, "part_num": "SS-42S4", "OD": 0.250, "params": {"OD": 0.250, "L": 2.41, "H": 1.62, "T": 0.048}},
            {"nd": 0.375, "part_num": "SS-43S6", "OD": 0.375, "params": {"OD": 0.375, "L": 2.82, "H": 1.88, "T": 0.065}},
            {"nd": 0.500, "part_num": "SS-44S8", "OD": 0.500, "params": {"OD": 0.500, "L": 3.42, "H": 2.19, "T": 0.065}},
        ]
    )

    conn.close()

    # Eliminar copias redundantes anteriores
    remove_redundant_catalogs()

    print(f"\n[OK] Catálogo Swagelok completo generado con éxito en: {OUTPUT_PCAT.resolve()}")


if __name__ == "__main__":
    build_swagelok_catalog()
