# Plant3D — Componentes Paramétricos y Catálogos `.pcat` para AutoCAD Plant 3D 2027

Repositorio de modelado 3D paramétrico (`varmain`) y generación de catálogos SQLite (`.pcat`) para **AutoCAD Plant 3D 2027**.

Integra una **arquitectura de doble motor (Dual-Engine)** para soportar tanto catálogos comerciales basados en longitudes globales como hojas técnicas de alta fidelidad de ingeniería.

---

## 📌 Arquitectura Dual-Engine

1. **Modelos Genéricos Comerciales (`src/models/generic/`)**:
   - Para catálogos estándar (ej. Saidi RK 2016) donde solo se dispone de longitud cara a cara ($L$), diámetro de cuerpo ($D$) y diámetro nominal ($OD$).
   - Cuello, vástago, palanca y volante se calculan de manera proporcional en Python sin requerir parámetros que las tablas comerciales no proveen.
   - Componentes disponibles:
     - `BALL_VALVE_1PC_COMPACT`: Válvula monobloque con palanca.
     - `BALL_VALVE_2PC_FLANGED`: Válvula de 2 piezas bridada con palanca.
     - `BALL_VALVE_3PC_THREADED`: Válvula de 3 piezas con cuerpo central simétrico.
     - `BALL_VALVE_HANDWHEEL`: Válvula bridada con volante para diámetros mayores.

2. **Modelos Específicos de Alta Fidelidad (`src/models/specific/`)**:
   - Para componentes de precisión con ficha técnica completa de fabricante.
   - `INTEC_K200_BALL_VALVE` (`src/models/specific/klinger_intec/`):
     - Gobierna cotas exactas: $L, D, H, L_1, E, OD$.
     - Plato ISO 5211, buje y prensaestopas.
     - **Taladrado adaptativo de pernos**: 4 orificios para tamaños $\le 3"$, 8 orificios para $4"$.

---

## 📂 Estructura del Repositorio

```text
plant3d/
├── builders/
│   ├── build.py              # Aplana y despliega scripts a CPak Common\CustomScripts\
│   └── build_catalog.py      # Generador dual-engine de catálogos SQLite (.pcat)
├── src/
│   ├── lib/
│   │   └── utils.py          # Utilidades matemáticas y de validación
│   └── models/               # Modelos paramétricos 3D
│       ├── generic/          # Modelos comerciales L / D
│       └── specific/         # Modelos de precisión por fabricante
├── tests/                    # Suite de pruebas unitarias
├── AGENTS.md                 # Guía y reglas críticas para agentes de IA
└── README.md
```

---

## 🚀 Flujo de Trabajo

### 1. Desplegar Scripts al Entorno de Plant 3D
Plant 3D 2027 requiere que los scripts se ubiquen de forma aplanada en `C:\AutoCAD Plant 3D 2027 Content\CPak Common\CustomScripts\`.
```powershell
python builders/build.py
```

### 2. Generar Catálogos `.pcat`
El builder detecta automáticamente el tipo de archivo de entrada generado por `catalog-scrap`:
```powershell
# Detección inteligente (especificación de fabricante o catálogo comercial):
python builders/build_catalog.py --input ..\catalog-scrap\output\specifications\INTEC_K200.json
python builders/build_catalog.py --input ..\catalog-scrap\output\catalogs\CATALOGO_VAL_BOLA_2016-44\manifest.json

# O usando banderas específicas:
python builders/build_catalog.py --spec-json ..\catalog-scrap\output\specifications\INTEC_K200.json
python builders/build_catalog.py --catalog-manifest ..\catalog-scrap\output\catalogs\CATALOGO_VAL_BOLA_2016-44\manifest.json
```

### 3. Validar con Tests Unitarios
```powershell
python builders/build.py --check
python -m unittest discover -s tests -v
```

### 4. Probar en AutoCAD Plant 3D
En la línea de comandos de AutoCAD Plant 3D:
```lisp
(arxload "PnP3dACPAdapter")
PLANTREGISTERCUSTOMSCRIPTS
(testacpscript "BALL_VALVE_2PC_FLANGED")
(testacpscript "BALL_VALVE_3PC_THREADED")
(testacpscript "BALL_VALVE_1PC_COMPACT")
(testacpscript "BALL_VALVE_HANDWHEEL")
(testacpscript "INTEC_K200_BALL_VALVE")
```

---

## 🧠 Reglas de Oro de la API `varmain`

1. **Estabilidad C++ (`.erase()`)**:
   Tras unir (`body.uniteWith(op)`) o restar (`body.subtractFrom(op)`), se debe llamar **SIEMPRE** a `op.erase()`. De lo contrario, `s` mantiene punteros colgantes en `s.m_Primitives` que provocan `FATAL ERROR: Unhandled Access Violation` al pulsar ESC.
2. **Origen de Primitivas**:
   - `BOX(s, L, W, H)`: Nace ya centrada en `(0, 0, 0)`. **No trasladas por $(-L/2, -W/2)$**.
   - `CYLINDER(s, R, H)`: Nace con la base en $Z=0$ y crece hacia $+Z$. Se centra con `.translate((0, 0, -H/2))`.
   - `ARC3D2`: Primitiva oficial para codos y curvas de tubería.
3. **Conexiones**:
   - `end_type = PL` (Plain End / Tubing) para instrumentación y auto-snapping sin accesorios.
   - `end_type = FL` para bridas con clase de presión.
