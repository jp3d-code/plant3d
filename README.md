# Plant3D - Custom Scripts para Racores y Componentes Swagelok

Repositorio oficial de scripts Python para **AutoCAD Plant 3D 2027** que definen geometrías paramétricas 3D, catálogos `.pcat` y puertos de conexión para componentes y racores personalizados Swagelok.

---

## 📌 Estado Actual del Proyecto

Actualmente, **el proyecto se encuentra 100% completado, integrado y verificado en AutoCAD Plant 3D 2027**:

- **11 Familias de Componentes Implementadas**: Uniones rectas, codos de 90° y 45°, conectores macho y hembra NPT, tes de unión y derivación, reductores, conectores de manómetros, tapones, tapas y válvulas de bola/retención.
- **Conexiones Nativas (`PL`)**: Todos los CSV están configurados con `end_type = PL` (Plain End / Tubing), lo que permite acoplamiento 3D automático e intuitivo en Plant 3D sin errores de conexión.
- **Catálogo SQLite (`Swagelok_Catalog.pcat`)**: Generado automáticamente y listo para importación en el **Spec Editor** o visor de especificaciones (`PLANTSPECVIEWER`).
- **Primitivas de Codos 3D Corregidas**: Codos de 90° y 45° utilizando la primitiva nativa `ARC3D2` con renderizado 3D perfecto.
- **Estabilidad C++**: Purga completa de llamadas `.erase()` duplicadas tras operaciones CSG, previniendo cuelgues `FATAL ERROR`.

---

## Ubicación Oficial de Trabajo

En **AutoCAD Plant 3D 2027**, la ruta oficial de ejecución para scripts personalizados se define en `ContentConfig.xml` (`<NativeContentCustomScriptsPath>`):

```text
C:\AutoCAD Plant 3D 2027 Content\CPak Common\CustomScripts\
```

---

## Estructura del Repositorio

> **Importante**: El compilador de Plant 3D (`varmain`) solo registra scripts `.py` colocados directamente en `CustomScripts/`. Por este motivo, las fuentes se mantienen organizadas por familia en `src/families/` y los builders en `builders/` los compilan y aplanan directamente a `C:\AutoCAD Plant 3D 2027 Content\CPak Common\CustomScripts/`.

```text
c:\Users\ynoacamino\dev\plant3d\
├── builders/
│   ├── build.py              # Aplana fuentes de src/families/ -> C:\AutoCAD Plant 3D 2027 Content\CPak Common\CustomScripts\
│   └── build_catalog.py      # Genera Swagelok_Catalog.pcat en CustomScripts\
├── src/                      # Código fuente organizado
│   ├── families/             # Componentes organizados por familias
│   │   ├── adapters/         # Adaptadores y conectores de puerto
│   │   ├── crosses/          # Cruces de unión
│   │   ├── elbows/           # Codos 90°, 45°, hembra, macho, orientables
│   │   ├── female/           # Conectores hembra NPT y pasamuros
   │   ├── male/             # Conectores macho NPT y pasamuros
│   │   ├── plugs/            # Tapones de tubo y racor
│   │   ├── primitives/       # Cilindro, caja, esfera, cilindro hueco
│   │   ├── special/          # Válvula de retención, conectores rápidos
│   │   ├── straight/         # Uniones rectas, reductores y pasamuros
│   │   ├── tees/             # Tes de unión y derivaciones macho/hembra
│   │   ├── valves/           # Válvulas de bola (2 vías, 3 vías) y aguja
│   │   └── vent_protectors/  # Protectores de venteo
│   └── lib/                  # Librería de utilidades compartidas
│       └── utils.py          # Funciones de validación y conversión
├── tests/                    # Tests unitarios
└── __init__.py               # Inicializador del paquete
```

---

## Flujo de Trabajo para Agregar o Modificar Componentes

1. **Editar o crear la fuente** en `src/families/{familia}/{componente}.py` y su correspondiente `.csv`.
2. **Aplanar fuentes a CustomScripts de Plant 3D**:
   ```bash
   python builders/build.py
   ```
3. **Regenerar el catálogo SQLite `.pcat`**:
   ```bash
   python builders/build_catalog.py
   ```
4. **Registrar en AutoCAD Plant 3D**:
   En la línea de comandos de AutoCAD Plant 3D:
   ```text
   PLANTREGISTERCUSTOMSCRIPTS
   ```
5. **Probar renderizado directo en Plant 3D**:
   ```lisp
   (arxload "PnP3dACPAdapter")
   (testacpscript "SIMPLE_ELBOW_90")
   (testacpscript "SIMPLE_ELBOW_45")
   ```

---

## 🧠 Aprendizajes Clave y Reglas de la API (`varmain`)

### 1. Primitiva de Codos: `ARC3D2`
- **`TORUS(s, R1, R2)`**: Genera siempre una dona completa (toroide de 360°) y no permite corte limpio por ángulo `A`.
- **`ARC3D2(s, D=float(OD), D2=float(OD), R=R1, A=90)`**: Es la primitiva oficial de Autodesk para codos 3D.
  - Parámetros clave: `D` y `D2` (diámetros exteriores en float), `R` (radio de curvatura centro-extremo), `A` (ángulo en grados: `90` o `45`).
  - Posicionamiento de puertos: Utilizar `s.setPoint(elbow.pointAt(0), elbow.directionAt(0), 0)` y `s.setPoint(elbow.pointAt(1), elbow.directionAt(1), 0)`.

### 2. Gestión de Memoria C++ en Operaciones CSG (`.erase()`)
- En el motor C++ de `varmain`, al llamar a `uniteWith(operando)` o `subtractFrom(operando)`, el motor **toma posesión del puntero y lo libera automáticamente**.
- **Jamás llamar a `operando.erase()` después de `uniteWith` o `subtractFrom`**, ya que provoca una doble liberación de memoria (`FATAL ERROR: unhandled access violation reading 0x0000`).

### 3. Conexiones e Inserción (`end_type = PL`)
- Para tuberías de instrumentación Swagelok, el `end_type` nativo en Plant 3D es **`PL`** (Plain End / Tubing).
- El uso de `PL` en los archivos CSV permite que las piezas se auto-conecten y ajusten en dibujos de proyecto 3D sin requerir reglas personalizadas en `DefaultConnectorsConfig.xml`.

### 4. Mapeo de Nombres en `build_catalog.py`
- En la base de datos `.pcat`, el campo `ContentGeometryTemplate` debe coincidir exactamente con el nombre decorado en `@activate(name)` (ejemplo: `SIMPLE_UNION`, `SIMPLE_ELBOW_90`), en lugar del nombre relativo del archivo.
- `build_catalog.py` incluye protección `try...except ImportError` en `sqlite3` para evitar conflictos en entornos Python recortados.

---

## 📋 Resumen de Comandos Útiles

```bash
# Aplanar scripts a CustomScripts
python builders/build.py

# Regenerar catálogo .pcat en CustomScripts
python builders/build_catalog.py

# Ejecutar tests unitarios
python -m unittest discover -s tests -v
```
