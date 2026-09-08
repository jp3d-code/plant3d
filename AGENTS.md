# AGENTS.md — Guía para agentes de IA en este repositorio

Repositorio de scripts Python paramétricos y catálogos `.pcat` para **AutoCAD Plant 3D 2027** (módulo `varmain`). Este archivo resume la arquitectura del proyecto, el estado actual y los aprendizajes verificados.

---

## 📌 Estado Actual del Proyecto (Completado)

El desarrollo del paquete de componentes Swagelok se encuentra **finalizado y 100% operativo**:

- **11 Familias Completadas**: Uniones, codos, tes, conectores macho/hembra, pasamuros, reductores, tapones, tapas, válvulas de bola/retención.
- **Auto-Snapping Activado**: Todos los archivos CSV usan `end_type = PL` (Plain End / Tubing), el estándar nativo de Plant 3D.
- **Estabilidad C++ Garantizada**: Se purgó la llamada `erase()` posterior a booleanos para prevenir `FATAL ERROR`.
- **Codos 3D Corregidos**: Se emplea `ARC3D2` con tipos flotantes explícitos.
- **Catálogo SQLite Actualizado**: `Swagelok_Catalog.pcat` generado con mapeo a funciones `@activate`.

---

## Flujo de trabajo

1. **Editar geometrías paramétricas 3D dentro de `src/models/`**:
   - `src/models/generic/`: Modelos esbeltos gobernados por `L` y `D` para catálogos comerciales generales (e.g. Saidi RK 2016).
   - `src/models/specific/`: Modelos de precisión y alta fidelidad de ingeniería (e.g. `klinger_intec/intec_k200_ball_valve.py` con taladrado adaptativo de 4/8 pernos, buje, ISO pad y estabilidad C++ `.erase()`).
2. **Aplanar componentes directamente a CustomScripts de Plant 3D** (`C:\AutoCAD Plant 3D 2027 Content\CPak Common\CustomScripts`):
   ```powershell
   python builders/build.py
   ```
3. **Generar catálogos `.pcat` (Dual-Engine desde catalog-scrap)**:
   ```powershell
   # A. Catálogo Comercial General (modelos gobernados por L y D)
   python builders/build_catalog.py --catalog-manifest ..\catalog-scrap\output\catalogs\CATALOGO_VAL_BOLA_2016-44\manifest.json

   # B. Ficha Técnica Específica de Alta Fidelidad (100% parámetros de ingeniería y plantilla específica)
   python builders/build_catalog.py --spec-json ..\catalog-scrap\output\specifications\INTEC_K200.json

   # C. Detección Inteligente Automática
   python builders/build_catalog.py --input ..\catalog-scrap\output\specifications\INTEC_K200.json
   ```

4. **Verificar sincronización y tests unitarios**:
   ```powershell
   python builders/build.py --check
   python -m unittest discover -s tests -v
   ```
5. **En AutoCAD Plant 3D (registrar y probar en pantalla)**:
   ```text
   (arxload "PnP3dACPAdapter")
   PLANTREGISTERCUSTOMSCRIPTS
   (testacpscript "SIMPLE_ELBOW_90")
   (testacpscript "SIMPLE_ELBOW_45")
   ```

---

## API `varmain` — Aprendizajes Verificados (Plant 3D 2027)

### 1. Primitiva de Codos 3D: `ARC3D2`
- **`TORUS(s, R1, R2)`**: Dibuja un toroide completo de 360° (dona) y no corta limpiamente por ángulo `A`.
- **`ARC3D2(s, D=float(OD), D2=float(OD), R=R1, A=90)`**: Primitiva nativa de curva de tubería.
  - Usar siempre valores flotantes explícitos (`float(OD)`, `float(L)`).
  - Posicionar puertos con `s.setPoint(elbow.pointAt(0), elbow.directionAt(0), 0)` y `s.setPoint(elbow.pointAt(1), elbow.directionAt(1), 0)`.

### 2. Primitivas y Manejo de Memoria C++ (`.erase()`)
- **Registro con `s`**: En `varmain`, todas las primitivas deben crearse pasándoles `s` como primer argumento (ej. `body = SPHERE(s, ...)`, `cyl = CYLINDER(s, ...)`). Esto agrega la primitiva a la lista interna `s.m_Primitives`.
- **Limpieza con `.erase()` tras CSG**: Después de unir (`body.uniteWith(operando)`) o restar (`body.subtractFrom(operando)`), se debe llamar **SIEMPRE** a `operando.erase()`.
- **¿Por qué es obligatorio `.erase()`?**: Al unir o restar, la geometría C++ del operando se consume dentro de `body`. Llamar a `operando.erase()` quita la referencia del operando de la lista `s.m_Primitives`. Si no se llama `.erase()`, `s` mantiene un puntero en desuso (*dangling pointer*). Al presionar **ESCAPE** o finalizar el comando de inserción en Plant 3D, el destructor C++ de `s` intenta liberar la lista de primitivas, causando un colapso instantáneo por doble liberación de memoria (`FATAL ERROR: Unhandled Access Violation Reading 0x0000`).


### 3. Conexiones e Inserción (`end_type = PL`)
- Para tubos e instrumentación Swagelok, el tipo de extremo nativo es **`PL`**.
- La declaración de `PL` en los CSVs permite arrastrar y soltar piezas desde la Tool Palette / Spec Viewer y conectarlas a tubos sin errores de compatibilidad de extremos.

### 4. Generación de Catálogo `.pcat`
- El campo `ContentGeometryTemplate` de la base de datos SQLite `.pcat` debe coincidir exactamente con el nombre registrado en `@activate(name)` (ej: `SIMPLE_UNION`, `SIMPLE_ELBOW_90`), resuelto dinámicamente por `build_catalog.py`.
- Mantener la importación de `sqlite3` protegida con `try...except ImportError` en scripts que puedan ser escaneados por el intérprete embebido de Plant 3D.

---

## Reglas Estructurales

- Función registrable: `def NOMBRE(s, ...)` en MAYÚSCULAS, única en todo el repo.
- Todo componente necesita `@activate(..., Ports="N")` y `@param(...)` con tipos `LENGTH` / `ANGLE`.
- Todo componente define puertos con `s.setPoint(...)`.
- Los builders se encuentran en la carpeta `builders/` y compilan directamente a `C:\AutoCAD Plant 3D 2027 Content\CPak Common\CustomScripts`.
