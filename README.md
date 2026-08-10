# Plant3D - Custom Scripts para Racores Swagelok

Scripts de Python para AutoCAD Plant 3D que definen componentes personalizados de racores para tubo.

## Requisitos

- AutoCAD Plant 3D 2026 o superior
- Python (version incluida en Plant3D, verificar con `python "import sys; print(sys.version)"`)

## Estructura

```
plant3d/
├── custom_scripts/          # Scripts Python
│   ├── primitives/          # Formas basicas
│   ├── straight/            # Uniones rectas
│   ├── elbows/              # Codos
│   ├── tees/                # Tes
│   ├── crosses/             # Cruces
│   ├── plugs/               # Tapones
│   ├── adapters/            # Adaptadores
│   └── utils.py             # Funciones comunes
├── equipment_packages/      # Paquetes .peqx
├── images/                  # Imagenes de referencia
├── config/                  # Configuracion
└── docs/                    # Documentacion
```

## Instalacion

1. Copiar la carpeta `custom_scripts/` a:
   ```
   C:\ProgramData\Autodesk\Plant 3D 20XX\CustomScripts\
   ```

2. Abrir AutoCAD Plant 3D

3. Cargar el adapter de pruebas:
   ```
   arxload "PnP3DACPAdapter.arx"
   ```

4. Registrar los scripts:
   ```
   PLANTREGISTERCUSTOMSCRIPTS
   ```

5. Reiniciar Plant3D para liberar scripts de memoria

## Pruebas

Para probar un script especifico:

```
TESTACPSCRIPT "SIMPLE_CYLINDER"
TESTACPSCRIPT "SIMPLE_BOX"
TESTACPSCRIPT "SIMPLE_UNION"
```

## Desarrollo

### Entorno de desarrollo (recomendado)

Crear botones en Tool Palette con estos macros:

| Accion | Macro |
|--------|-------|
| Cargar adapter | `^C^C(arxload "PnP3dACPAdapter.arx");` |
| Registrar scripts | `^C^C(arxload "PnP3DAcpadapter.arx");PLANTREGISTERCUSTOMSCRIPTS;` |
| Registrar y reiniciar | `^C^CPLANTREGISTERCUSTOMSCRIPTS;(startapp "C:/Program Files/Autodesk/AutoCAD Plant 3D 20XX/acad.exe");QUIT` |
| Probar script | `^C^C(TESTACPSCRIPT "NOMBRE_SCRIPT")` |

### Validar sintaxis

```bash
python3 -c "
import ast
with open('custom_scripts/primitives/simple_cylinder.py') as f:
    ast.parse(f.read())
print('OK')
"
```

### Tipos de parametros

| Tipo | Descripcion | Ejemplo |
|------|-------------|---------|
| `LENGTH` | Longitud, debe ser > 0 | `D=LENGTH` |
| `d0` | Longitud, puede ser 0 | `OF=d0` |
| `d-` | Offset, puede ser negativo | `X=d-` |
| `a` | Angulo en grados | `ANGLE` |
| `r` | Numero sin dimension | `N=r` |
| `b` | Booleano true/false | `FLAG=b` |

### Decoradores

```python
@activate(
    Group="Primitives",
    TooltipShort="Nombre corto",
    TooltipLong="Descripcion larga",
    LengthUnit="in"  # o "mm"
)
@group("Categoria")
@param(D=LENGTH, TooltipShort="Parametro D")
def MI_SCRIPT(s, D=48, **kw):
    # Codigo aqui
    return s
```

## Scripts disponibles

### Primitivos
- `simple_cylinder.py` - Cilindro solido
- `simple_box.py` - Caja solida
- `simple_sphere.py` - Esfera solida
- `hollow_cylinder.py` - Cilindro hueco (tubo)

### Racores
- `simple_union.py` - Union recta
- `simple_elbow_90.py` - Codo 90°
- `simple_tee.py` - T simple

## Notas importantes

- Plant3D no libera scripts de memoria. Reiniciar para actualizar cambios.
- El nombre de la funcion debe coincidir con el nombre del archivo en mayusculas.
- Usar `s` como primer parametro y retorno del script.
- Los scripts importan de `varmain.primitiv` y `varmain.custom` (solo disponibles en Plant3D).

## Referencias

- [AU Class PD1746: Scripting Components for AutoCAD Plant 3D](https://www.autodesk.com/autodesk-university/class/Scripting-Components-for-AutoCAD-Plant-3D)
- [Custom Python Scripting for AutoCAD Plant 3D (Parts 1-4)](https://www.autodesk.com/autodesk-university/)
- Catálogo Swagelok MS-01-23ES
