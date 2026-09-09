# AGENTS.md — Guía para agentes de IA en este repositorio

Repositorio de scripts Python paramétricos y catálogos `.pcat` para **AutoCAD Plant 3D 2027** (módulo `varmain`). Este archivo resume la arquitectura del proyecto, el estado actual, las reglas críticas y los flujos verificados.

---

## 📌 Estado Actual del Proyecto (Dual-Engine Activo)

El proyecto cuenta con una arquitectura de **doble motor** integrada con los datos extraídos de `catalog-scrap`:

1. **Modelos Genéricos Comerciales (`src/models/generic/`)**:
   - Validados visualmente en pantalla en Plant 3D 2027:
     - `BALL_VALVE_1PC_COMPACT`: Monobloque esbelto con cuello y palanca.
     - `BALL_VALVE_2PC_FLANGED`: Bipartida bridada con palanca.
     - `BALL_VALVE_3PC_THREADED`: Tripartita con bloque central simétrico centrado en el origen `(0, 0, 0)`.
     - `BALL_VALVE_HANDWHEEL`: Válvula bridada con volante toroidal para diámetros grandes.
   - Gobernados estrictamente por **`L`, `D`, y `OD`**. Todos los elementos visuales (vástago, manija/volante) se calculan proporcionalmente.

2. **Modelos Específicos de Alta Fidelidad (`src/models/specific/`)**:
   - `INTEC_K200_BALL_VALVE` (`klinger_intec/intec_k200_ball_valve.py`):
     - 100% cotas de ingeniería ($L, D, H, L_1, E, OD$).
     - Taladrado adaptativo de pernos (4 agujeros para $\le 3"$, 8 agujeros para $4"$).
     - ISO pad 5211, buje, prensaestopas y puertos de alta precisión.

3. **Catálogos SQLite (`.pcat`) Operativos**:
   - `KLINGER_Schoneberg_INTEC_K200_Catalog.pcat`: 18 ítems (Clases 150# y 300#).
   - `Catalogo_Val_Bola_2016-44_Catalog.pcat`: 73 ítems comerciales Saidi RK 2016 en 16 familias.

---

## 🔄 Flujo de Trabajo

### 1. Desarrollo de Geometrías 3D (`src/models/`)
- Modelos genéricos comerciales en `src/models/generic/`.
- Modelos de precisión por fabricante en `src/models/specific/{fabricante}/`.

### 2. Aplanar componentes a CustomScripts de Plant 3D
Despliega automáticamente a `C:\AutoCAD Plant 3D 2027 Content\CPak Common\CustomScripts\`:
```powershell
python builders/build.py
```

### 3. Generar Catálogos `.pcat` (Dual-Engine)
El builder detecta automáticamente si el JSON de entrada es una especificación detallada o un manifiesto comercial:
```powershell
# A. Detección automática inteligente
python builders/build_catalog.py --input ..\catalog-scrap\output\specifications\INTEC_K200.json
python builders/build_catalog.py --input ..\catalog-scrap\output\catalogs\CATALOGO_VAL_BOLA_2016-44\manifest.json

# B. Banderas explícitas
python builders/build_catalog.py --spec-json ..\catalog-scrap\output\specifications\INTEC_K200.json
python builders/build_catalog.py --catalog-manifest ..\catalog-scrap\output\catalogs\CATALOGO_VAL_BOLA_2016-44\manifest.json
```

### 4. Ejecutar Pruebas Unitarias
```powershell
python builders/build.py --check
python -m unittest discover -s tests -v
```

### 5. Registro y Prueba Interactiva en AutoCAD Plant 3D
En la línea de comandos de Plant 3D:
```text
(arxload "PnP3dACPAdapter")
PLANTREGISTERCUSTOMSCRIPTS
(testacpscript "BALL_VALVE_2PC_FLANGED")
(testacpscript "BALL_VALVE_3PC_THREADED")
(testacpscript "BALL_VALVE_1PC_COMPACT")
(testacpscript "BALL_VALVE_HANDWHEEL")
(testacpscript "INTEC_K200_BALL_VALVE")
```

---

## 🧠 API `varmain` — Reglas Críticas (Plant 3D 2027)

### 1. Limpieza con `.erase()` tras CSG (Prevención de Fatal Error)
- **OBLIGATORIO**: Tras unir (`body.uniteWith(operando)`) o restar (`body.subtractFrom(operando)`), se debe llamar **SIEMPRE** a `operando.erase()`.
- **Por qué**: Al unir o restar, la geometría C++ del operando se consume dentro de `body`. `.erase()` desvincula el operando de `s.m_Primitives`. Si no se llama `.erase()`, `s` retiene un puntero en desuso (*dangling pointer*). Al presionar **ESCAPE** o borrar la pieza en Plant 3D, el destructor C++ intenta liberar la memoria dos veces, provocando un colapso instantáneo: `FATAL ERROR: Unhandled Access Violation Reading 0x0000`.

### 2. Comportamiento y Origen de Primitivas
- **`BOX(s, L=..., W=..., H=...)`**:
  - **Nace ya centrada en el origen `(0, 0, 0)`** en los 3 ejes ($X \in [-L/2, L/2]$, $Y \in [-W/2, W/2]$, $Z \in [-H/2, H/2]$).
  - **NUNCA** trasladar con `(-L/2, -W/2)` a menos que se desee desplazar intencionalmente; hacerlo expulsará el bloque a un solo cuadrante.
- **`CYLINDER(s, R=..., H=...)`**:
  - La base circular nace centrada en $(0, 0)$ en el plano XY y la altura crece hacia $+Z$ ($Z \in [0, H]$).
  - Para centrarlo sobre el origen del eje de tubería: `body.translate((0, 0, -H/2))`.
- **`ARC3D2(s, D=float(OD), D2=float(OD), R=R1, A=90)`**:
  - Primitiva nativa oficial para codos y curvas de tubería. Usar siempre flotantes explícitos (`float(OD)`, `float(L)`).
  - Posicionar puertos con:
    ```python
    s.setPoint(elbow.pointAt(0), elbow.directionAt(0), 0)
    s.setPoint(elbow.pointAt(1), elbow.directionAt(1), 0)
    ```

### 3. Modelos Genéricos: Trampa de Parámetros Incompletos
- En catálogos comerciales (Saidi RK 2016, etc.), las tablas no proporcionan altura de vástago ($H$) ni longitud de palanca ($L_1$).
- Si un script genérico declara `@param(H=...)`, el generador `.pcat` le asignará `0.0`, provocando que en Plant 3D la válvula se dibuje sin cuello ni manija.
- **Regla**: Los modelos genéricos solo deben exponer `@param(L=...)`, `@param(D=...)` y `@param(OD=...)`. El resto se deriva en Python.

### 4. Conexiones e Inserción (`end_type`)
- Tubing / Racores / Roscado / SW: `end_type = PL` (Plain End / Tubing). Activa el auto-snapping nativo.
- Bridas: `end_type = FL` asociado a su `PressureClass` correspondiente (150#, 300#, PN16, PN40).

### 5. Generación de Catálogo `.pcat`
- El campo `ContentGeometryTemplate` de la base de datos SQLite `.pcat` debe coincidir exactamente con el nombre de la función en `@activate(name)` (ej: `BALL_VALVE_2PC_FLANGED`, `INTEC_K200_BALL_VALVE`).
- **Sanitización ASCII**: Nombres de catálogo y tablas deben normalizarse a ASCII puro (evitar caracteres con acentos o diacríticos como `Schöneberg` -> `Schoneberg`) para evitar corrupción al vincular bases de datos en Windows SQLite.
- Proteger la importación de `sqlite3` con `try...except ImportError` en scripts que puedan ser inspeccionados por el intérprete embebido de Plant 3D.

---

## 📐 Convenciones Estructurales y Git

- **Nombre de función registrable**: `def NOMBRE(s, ...)` en MAYÚSCULAS, única en todo el repo.
- **Decoradores obligatorios**: `@activate(..., Ports="N")` y `@param(...)` con tipos `LENGTH` / `ANGLE`.
- **Puertos**: Definidos explícitamente con `s.setPoint((x,y,z), (dx,dy,dz), index)`.
- **Estilo de Commits**: Commits atómicos tipo Conventional Commits (`<type>(<scope>): <subject>`) **con cero cuerpo/descripción**.
