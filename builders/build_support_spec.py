r"""
build_support_spec.py - Incorporador automatizado de Catálogos de Soporte (.acat)
a Especificaciones de Soporte (.pspc) para AutoCAD Plant 3D 2027.

Permite incorporar familias completas de soportes desde un archivo .acat a:
1. La especificación maestra global: CPak Common\PipeSupportsSpec.pspc
2. O la especificación de soporte de cualquier proyecto: <Proyecto>\Spec Sheets\PipeSupportsSpec.pspc

Uso:
    # A. Incorporar a la especificación maestra global por defecto:
    python builders/build_support_spec.py

    # B. Incorporar a la especificación de un proyecto específico:
    python builders/build_support_spec.py --acat "C:\...\ITECO_B3S_Supports_Catalog.acat" --spec-pspc "C:\...\MiProyecto\Spec Sheets\PipeSupportsSpec.pspc"
"""

import sys
import shutil
import sqlite3
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTENT_DIR = Path(r"C:\AutoCAD Plant 3D 2027 Content\CPak Common")
DEFAULT_MASTER_SPEC = DEFAULT_CONTENT_DIR / "PipeSupportsSpec.pspc"
DEFAULT_CATALOG_ACAT = DEFAULT_CONTENT_DIR / "CustomScripts" / "ITECO_B3S_Supports_Catalog.acat"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from builders.build_catalog import guid_to_bytes, get_current_win_filetime, sanitize_ascii
except ImportError:
    from build_catalog import guid_to_bytes, get_current_win_filetime, sanitize_ascii


def add_support_catalog_to_spec(
    acat_path: Path = DEFAULT_CATALOG_ACAT,
    spec_pspc_path: Path = DEFAULT_MASTER_SPEC,
    catalog_id: str = "SUPPORTS Catalog",
    backup: bool = True
):
    """
    Incorpora todos los registros de un catálogo .acat dentro de una especificación .pspc.
    Garantiza idempotencia: si la familia ya existe, la reemplaza limpiamente sin duplicados.
    """
    if not acat_path.exists():
        raise FileNotFoundError(f"No se encontró el catálogo de soporte .acat: {acat_path}")

    if not spec_pspc_path.exists():
        raise FileNotFoundError(f"No se encontró la especificación de soporte .pspc: {spec_pspc_path}")

    # 1. Crear backup de seguridad antes de modificar
    backup_path = None
    if backup:
        backup_path = spec_pspc_path.with_suffix(".pspc.bak")
        shutil.copy2(spec_pspc_path, backup_path)

    # 2. Leer registros y columnas desde el .acat fuente
    acat_conn = sqlite3.connect(acat_path)
    acat_conn.row_factory = sqlite3.Row
    acat_cur = acat_conn.cursor()

    acat_cur.execute("SELECT * FROM EngineeringItems ORDER BY NominalDiameter ASC;")
    acat_rows = acat_cur.fetchall()
    if not acat_rows:
        acat_conn.close()
        raise ValueError(f"El catálogo {acat_path} no contiene filas en EngineeringItems.")

    sample = acat_rows[0]
    family_desc = sample["PartFamilyLongDesc"]
    template_name = sample["ContentGeometryTemplate"]
    acat_conn.close()

    # 3. Conectar a la especificación .pspc destino
    spec_conn = sqlite3.connect(spec_pspc_path)
    spec_cur = spec_conn.cursor()

    # Asegurar que la tabla Support exista si es una spec nueva o derivada de piping
    spec_cur.execute("CREATE TABLE IF NOT EXISTS Support (PnPID INTEGER PRIMARY KEY, PartSubType TEXT);")

    # Inspeccionar columnas destino en EngineeringItems de la .pspc
    spec_cur.execute("PRAGMA table_info(EngineeringItems);")
    dest_cols = {r[1] for r in spec_cur.fetchall()}

    # 4. Eliminar versión previa de la misma familia si ya existía (Idempotencia)
    spec_cur.execute("""
        SELECT PnPID FROM EngineeringItems
        WHERE PartFamilyLongDesc = ? OR ContentGeometryTemplate = ?;
    """, (family_desc, template_name))
    old_pnpids = [r[0] for r in spec_cur.fetchall()]

    if old_pnpids:
        for old_id in old_pnpids:
            spec_cur.execute("DELETE FROM EngineeringItems WHERE PnPID = ?;", (old_id,))
            spec_cur.execute("DELETE FROM Support WHERE PnPID = ?;", (old_id,))
            spec_cur.execute("DELETE FROM PipeRunComponent WHERE PnPID = ?;", (old_id,))
            spec_cur.execute("DELETE FROM PnPBase WHERE PnPID = ?;", (old_id,))
        spec_conn.commit()

    # 5. Obtener el siguiente PnPID disponible
    spec_cur.execute("SELECT MAX(PnPID) FROM PnPBase;")
    max_pnp = spec_cur.fetchone()[0]
    next_pnp_id = (max_pnp + 1) if max_pnp is not None else 2

    # Detectar si la spec destino es una spec de piping (contiene tabla Pipe)
    spec_cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='Pipe';")
    is_piping_spec = (spec_cur.fetchone()[0] > 0)

    # Columnas comunes a transferir
    src_keys = [k for k in sample.keys() if k in dest_cols and k != "PnPID"]

    items_added = 0
    for row in acat_rows:
        pnp_id = next_pnp_id
        next_pnp_id += 1

        guid = guid_to_bytes()
        timestamp = get_current_win_filetime()

        # Insertar en PnPBase
        spec_cur.execute("""
            INSERT INTO PnPBase (PnPID, PnPClassName, PnPStatus, PnPRevision, PnPGuid, PnPTimestamp)
            VALUES (?, 'Support', 0, 0, ?, ?);
        """, (pnp_id, guid, timestamp))

        # Insertar en PipeRunComponent y Support
        spec_cur.execute("INSERT INTO PipeRunComponent (PnPID) VALUES (?);", (pnp_id,))
        spec_cur.execute("INSERT INTO Support (PnPID, PartSubType) VALUES (?, 'Support');", (pnp_id,))

        # Construir columnas y valores para EngineeringItems
        row_dict = dict(row)
        cols_to_insert = ["PnPID"]
        vals_to_insert = [pnp_id]

        for k in src_keys:
            cols_to_insert.append(k)
            if k == "PartCategory" and is_piping_spec:
                vals_to_insert.append("Miscellaneous")
            else:
                vals_to_insert.append(row_dict[k])

        # Asignar CatalogId si la columna existe en el destino
        if "CatalogId" in dest_cols and "CatalogId" not in cols_to_insert:
            cols_to_insert.append("CatalogId")
            vals_to_insert.append(catalog_id)

        if "CatalogPartId" in dest_cols and "CatalogPartId" not in cols_to_insert:
            cols_to_insert.append("CatalogPartId")
            vals_to_insert.append(None)

        placeholders = ", ".join(["?"] * len(vals_to_insert))
        cols_str = ", ".join(cols_to_insert)

        spec_cur.execute(f"""
            INSERT INTO EngineeringItems ({cols_str})
            VALUES ({placeholders});
        """, vals_to_insert)

        items_added += 1

    spec_conn.commit()
    spec_conn.close()

    return {
        "spec_path": str(spec_pspc_path),
        "backup_path": str(backup_path) if backup_path else None,
        "items_added": items_added,
        "family": family_desc,
        "template": template_name
    }


def main():
    parser = argparse.ArgumentParser(description="Incorporar Catálogo de Soporte (.acat) a Spec de Plant 3D (.pspc)")
    parser.add_argument("--acat", default=DEFAULT_CATALOG_ACAT, type=Path, help="Ruta al catálogo .acat fuente")
    parser.add_argument("--spec-pspc", default=DEFAULT_MASTER_SPEC, type=Path, help="Ruta a la spec .pspc destino")
    parser.add_argument("--catalog-id", default="SUPPORTS Catalog", type=str, help="Identificador del catálogo")
    parser.add_argument("--no-backup", action="store_true", help="No crear copia de respaldo .pspc.bak")

    args = parser.parse_args()

    res = add_support_catalog_to_spec(
        acat_path=args.acat,
        spec_pspc_path=args.spec_pspc,
        catalog_id=args.catalog_id,
        backup=not args.no_backup
    )

    print(f"\n[+] Incorporación completada exitosamente:")
    print(f"    Familia:       {res['family']}")
    print(f"    Template:      {res['template']}")
    print(f"    Items añadidos:{res['items_added']}")
    print(f"    Spec destino:  {res['spec_path']}")
    if res['backup_path']:
        print(f"    Backup previo: {res['backup_path']}")


if __name__ == "__main__":
    main()
