r"""
build_piping_spec.py - Incorporador automatizado de Catálogos de Válvulas (.pcat)
a Especificaciones de Tubería ASME (.pspc) para AutoCAD Plant 3D 2027.

Permite incorporar familias completas de válvulas comerciales y de alta fidelidad
(INTEC K200, Saidi RK 2016, etc.) directamente en especificaciones de tubería:
1. La especificación de tubería del proyecto activo:
   <Proyecto>\SpecSheets\CS150.pspc
2. La especificación maestra global de CPak ASME:
   CPak ASME\CS150.pspc

Garantiza:
- Conservación íntegra de todos los componentes nativos ASME (Pipe, Flange, Elbow, Tee, etc.).
- Idempotencia total: reemplaza limpiamente versiones previas sin duplicar registros.
- Puertos duales (S1 en EngineeringItems y S2 en Port/PartPort) conectados a ASME B16.5 RF.
- Compatibilidad nativa con enrutamiento de tubería PLANTPIPEADD y colocación de válvulas.
"""

import sys
import shutil
import sqlite3
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTENT_DIR = Path(r"C:\AutoCAD Plant 3D 2027 Content")
DEFAULT_PROJECT_DIR = Path(r"C:\Users\ynoacamino\AppData\Roaming\Autodesk\Autodesk AutoCAD Plant 3D 2027\R26.0\enu\DefaultProject")

DEFAULT_MASTER_CS150 = DEFAULT_CONTENT_DIR / "CPak ASME" / "CS150.pspc"
DEFAULT_PROJECT_CS150 = DEFAULT_PROJECT_DIR / "SpecSheets" / "CS150.pspc"

DEFAULT_INTEC_PCAT = DEFAULT_CONTENT_DIR / "CPak Common" / "CustomScripts" / "KLINGER_Schoneberg_INTEC_K200_Catalog.pcat"
DEFAULT_SAIDI_PCAT = DEFAULT_CONTENT_DIR / "CPak Common" / "CustomScripts" / "Catalogo_Val_Bola_2016-44_Catalog.pcat"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from builders.build_catalog import (
        guid_to_bytes,
        get_current_win_filetime,
        sanitize_ascii,
        normalize_pressure_class
    )
except ImportError:
    from build_catalog import (
        guid_to_bytes,
        get_current_win_filetime,
        sanitize_ascii,
        normalize_pressure_class
    )


def parse_geometry_params(param_str: Optional[str]) -> Dict[str, float]:
    """Extrae parámetros numéricos de la cadena ContentGeometryParamDefinition."""
    res = {}
    if not param_str:
        return res
    for token in param_str.split(","):
        if "=" in token:
            k, v = token.split("=", 1)
            k = k.strip().upper()
            try:
                res[k] = float(v.strip())
            except ValueError:
                pass
    return res


def add_valves_to_piping_spec(
    pcat_paths: List[Path],
    spec_pspc_path: Path = DEFAULT_PROJECT_CS150,
    target_pressure_class: str = "150",
    backup: bool = True
) -> Dict[str, Any]:
    """
    Incorpora válvulas de clase 150 desde catálogos .pcat dentro de una especificación .pspc.
    Preserva intactos todos los tubos, codos, bridas y accesorios existentes.
    """
    if not spec_pspc_path.exists():
        raise FileNotFoundError(f"No se encontró la especificación de tubería .pspc: {spec_pspc_path}")

    # 1. Crear backup de seguridad antes de modificar
    backup_path = None
    if backup:
        backup_path = spec_pspc_path.with_suffix(".pspc.bak")
        shutil.copy2(spec_pspc_path, backup_path)

    # 2. Conectar a la especificación .pspc destino
    spec_conn = sqlite3.connect(spec_pspc_path)
    spec_cur = spec_conn.cursor()

    # Inspeccionar columnas destino
    spec_cur.execute("PRAGMA table_info(EngineeringItems);")
    dest_eng_cols = {r[1] for r in spec_cur.fetchall()}

    spec_cur.execute("PRAGMA table_info(Valve);")
    dest_valve_cols = {r[1] for r in spec_cur.fetchall()}

    # 3. Identificar familias a procesar desde los catálogos fuente
    catalogs_data = []
    templates_to_replace = set()
    catalogs_to_replace = set()

    for pcat_path in pcat_paths:
        if not pcat_path.exists():
            print(f"[!] Aviso: Catálogo no encontrado, omitiendo: {pcat_path}")
            continue

        cat_conn = sqlite3.connect(pcat_path)
        cat_conn.row_factory = sqlite3.Row
        cat_cur = cat_conn.cursor()

        # Filtrar solo ítems de la clase de presión especificada (ej. 150)
        cat_cur.execute("""
            SELECT * FROM EngineeringItems
            WHERE PartCategory = 'Valves'
            ORDER BY NominalDiameter ASC;
        """)
        all_items = cat_cur.fetchall()

        matched_items = []
        for it in all_items:
            norm_class = normalize_pressure_class(it["PressureClass"])
            if norm_class == target_pressure_class:
                matched_items.append(it)
                templates_to_replace.add(it["ContentGeometryTemplate"])

        cat_name = sanitize_ascii(pcat_path.stem.replace("_Catalog", " Catalog").replace("_", " "))
        catalogs_to_replace.add(cat_name)

        # Leer puertos S2 desde PartPort y Port
        ports_map = {}
        for it in matched_items:
            pnpid = it["PnPID"]
            cat_cur.execute("SELECT Port FROM PartPort WHERE Part = ? AND Name = 'S2';", (pnpid,))
            port_row = cat_cur.fetchone()
            if port_row:
                port_id = port_row[0]
                cat_cur.execute("SELECT * FROM Port WHERE PnPID = ?;", (port_id,))
                p_data = cat_cur.fetchone()
                if p_data:
                    ports_map[pnpid] = dict(p_data)

        cat_conn.close()
        catalogs_data.append({
            "path": pcat_path,
            "catalog_id": cat_name,
            "items": matched_items,
            "ports_map": ports_map
        })

    # 4. Limpieza idempotente: eliminar versiones previas de las mismas familias/templates
    for tmpl in templates_to_replace:
        spec_cur.execute("""
            SELECT PnPID FROM EngineeringItems
            WHERE ContentGeometryTemplate = ?;
        """, (tmpl,))
        old_ids = [r[0] for r in spec_cur.fetchall()]

        for old_id in old_ids:
            # Obtener puerto S2 asociado
            spec_cur.execute("SELECT Port FROM PartPort WHERE Part = ?;", (old_id,))
            s2_ports = [r[0] for r in spec_cur.fetchall()]
            for p_id in s2_ports:
                spec_cur.execute("DELETE FROM Port WHERE PnPID = ?;", (p_id,))
                spec_cur.execute("DELETE FROM PnPBase WHERE PnPID = ?;", (p_id,))

            spec_cur.execute("DELETE FROM PartPort WHERE Part = ?;", (old_id,))
            spec_cur.execute("DELETE FROM Valve WHERE PnPID = ?;", (old_id,))
            spec_cur.execute("DELETE FROM PipeRunComponent WHERE PnPID = ?;", (old_id,))
            spec_cur.execute("DELETE FROM EngineeringItems WHERE PnPID = ?;", (old_id,))
            spec_cur.execute("DELETE FROM PnPBase WHERE PnPID = ?;", (old_id,))

    spec_conn.commit()

    # 5. Obtener secuencia máxima de PnPID
    spec_cur.execute("SELECT MAX(PnPID) FROM PnPBase;")
    max_pnp = spec_cur.fetchone()[0]
    next_pnp_id = (max_pnp + 1) if max_pnp is not None else 10000

    spec_cur.execute("SELECT MAX(PnPID) FROM PartPort;")
    max_pp = spec_cur.fetchone()[0]
    next_partport_id = (max_pp + 1) if max_pp is not None else 1000

    total_added = 0
    families_added = {}

    for cat in catalogs_data:
        catalog_id = cat["catalog_id"]
        for it in cat["items"]:
            valve_pnp_id = next_pnp_id
            next_pnp_id += 1

            guid = guid_to_bytes()
            timestamp = get_current_win_filetime()

            # A. Insertar en PnPBase
            spec_cur.execute("""
                INSERT INTO PnPBase (PnPID, PnPClassName, PnPStatus, PnPRevision, PnPGuid, PnPTimestamp)
                VALUES (?, 'Valve', 0, 0, ?, ?);
            """, (valve_pnp_id, guid, timestamp))

            # B. Insertar en PipeRunComponent
            spec_cur.execute("INSERT INTO PipeRunComponent (PnPID) VALUES (?);", (valve_pnp_id,))

            # C. Preparar e Insertar en EngineeringItems
            row_dict = dict(it)
            cols = ["PnPID"]
            vals = [valve_pnp_id]

            for col in dest_eng_cols:
                if col in ("PnPID",):
                    continue
                if col == "CatalogId":
                    cols.append("CatalogId")
                    vals.append(catalog_id)
                elif col == "CatalogPartId":
                    cols.append("CatalogPartId")
                    vals.append(None)
                elif col in row_dict:
                    val = row_dict[col]
                    if isinstance(val, str):
                        val = sanitize_ascii(val)
                    cols.append(col)
                    vals.append(val)

            placeholders = ", ".join(["?"] * len(vals))
            cols_str = ", ".join(cols)
            spec_cur.execute(f"INSERT INTO EngineeringItems ({cols_str}) VALUES ({placeholders});", vals)

            # D. Extraer cotas y parámetros para la tabla Valve
            geom_params = parse_geometry_params(row_dict.get("ContentGeometryParamDefinition", ""))
            length_val = geom_params.get("L", float(row_dict.get("NominalDiameter", 2.0)) * 3.5)
            d_flange = geom_params.get("D", float(row_dict.get("MatchingPipeOd", 2.375)) * 2.0)
            nd_val = float(row_dict.get("NominalDiameter", 2.0))

            h_act = geom_params.get("H", round(d_flange * 0.85, 2))
            l1_act = geom_params.get("L1", round(length_val * 1.5, 2))

            if nd_val >= 6.0:
                act_type = "HandWheel"
                act_family = "Hand Wheel"
            else:
                act_type = "HandLever"
                act_family = "Hand Lever"

            spec_cur.execute("""
                INSERT INTO Valve (
                    PnPID, Length, ValveAlignment, ValveDetail, ValveBodyType,
                    FlowDependent, ValveBodyFamilyId, ValveBodyPartSizeId,
                    ActuatorFamilyName, OperatorType, ActuatorType,
                    ActuatorHeight, ActuatorWidth
                ) VALUES (?, ?, 'Inline', 'Continuous', 'Ball', 0, ?, ?, ?, 'Manual', ?, ?, ?);
            """, (
                valve_pnp_id,
                length_val,
                row_dict.get("PartFamilyId"),
                row_dict.get("SizeRecordId"),
                act_family,
                act_type,
                h_act,
                l1_act
            ))

            # E. Configurar Puerto S2 en Port y PartPort
            port_s2_data = cat["ports_map"].get(it["PnPID"])
            port_pnp_id = next_pnp_id
            next_pnp_id += 1

            spec_cur.execute("""
                INSERT INTO PnPBase (PnPID, PnPClassName, PnPStatus, PnPRevision, PnPGuid, PnPTimestamp)
                VALUES (?, 'Port', 0, 0, ?, ?);
            """, (port_pnp_id, guid_to_bytes(), timestamp))

            if port_s2_data:
                matching_od = port_s2_data.get("MatchingPipeOd", row_dict.get("MatchingPipeOd"))
                flange_thk = port_s2_data.get("FlangeThickness", row_dict.get("FlangeThickness"))
                facing = port_s2_data.get("Facing", row_dict.get("Facing", "RF"))
                end_type = port_s2_data.get("EndType", row_dict.get("EndType", "FL"))
            else:
                matching_od = row_dict.get("MatchingPipeOd")
                flange_thk = row_dict.get("FlangeThickness")
                facing = row_dict.get("Facing", "RF")
                end_type = row_dict.get("EndType", "FL")

            spec_cur.execute("""
                INSERT INTO Port (
                    PnPID, SizeRecordId, PortName, NominalDiameter, NominalUnit,
                    MatchingPipeOd, EndType, Facing, FlangeThickness, PressureClass, LengthUnit
                ) VALUES (?, ?, 'S2', ?, 'in', ?, ?, ?, ?, '150', 'in');
            """, (
                port_pnp_id,
                row_dict.get("SizeRecordId"),
                nd_val,
                matching_od,
                end_type,
                facing,
                flange_thk
            ))

            # F. Mapeo en PartPort
            partport_pnp_id = next_partport_id
            next_partport_id += 1

            spec_cur.execute("""
                INSERT INTO PartPort (PnPID, PnPGuid, PnPTimestamp, Part, Port, Name)
                VALUES (?, ?, ?, ?, ?, 'S2');
            """, (partport_pnp_id, guid_to_bytes(), timestamp, valve_pnp_id, port_pnp_id))

            total_added += 1
            f_key = row_dict.get("ContentGeometryTemplate", "VALVE")
            families_added[f_key] = families_added.get(f_key, 0) + 1

    spec_conn.commit()
    spec_conn.close()

    return {
        "spec_path": str(spec_pspc_path),
        "backup_path": str(backup_path) if backup_path else None,
        "items_added": total_added,
        "families": families_added
    }


def main():
    parser = argparse.ArgumentParser(description="Incorporar Válvulas Clase 150 (.pcat) a Spec CS150 (.pspc)")
    parser.add_argument("--spec-pspc", default=DEFAULT_PROJECT_CS150, type=Path, help="Ruta a la spec CS150 .pspc destino")
    parser.add_argument("--also-master", action="store_true", help="Actualizar también la spec maestra en CPak ASME")
    parser.add_argument("--no-backup", action="store_true", help="No crear copia de respaldo .pspc.bak")

    args = parser.parse_args()

    pcats = [DEFAULT_INTEC_PCAT, DEFAULT_SAIDI_PCAT]

    print(f"\n[+] Incorporando Válvulas Clase 150 a Spec de Tubería:")
    print(f"    Destino Principal: {args.spec_pspc}")

    res = add_valves_to_piping_spec(
        pcat_paths=pcats,
        spec_pspc_path=args.spec_pspc,
        target_pressure_class="150",
        backup=not args.no_backup
    )

    print(f"    [OK] {res['items_added']} válvulas Clase 150 incorporadas:")
    for f_name, count in res["families"].items():
        print(f"         - {f_name}: {count} tamaños")

    if args.also_master and DEFAULT_MASTER_CS150.exists() and DEFAULT_MASTER_CS150 != args.spec_pspc:
        print(f"\n[+] Actualizando también spec maestra: {DEFAULT_MASTER_CS150}")
        res_master = add_valves_to_piping_spec(
            pcat_paths=pcats,
            spec_pspc_path=DEFAULT_MASTER_CS150,
            target_pressure_class="150",
            backup=not args.no_backup
        )
        print(f"    [OK] {res_master['items_added']} válvulas incorporadas a spec maestra.")


if __name__ == "__main__":
    main()
