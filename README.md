# Plant3D - Custom Scripts para Racores y Componentes

Repositorio oficial de scripts Python para **AutoCAD Plant 3D 2027** que definen geometrías paramétricas y puertos de conexión 3D para componentes y racores personalizados.

---

## 📍 Ubicación Oficial de Trabajo

En **AutoCAD Plant 3D 2027**, la ruta oficial de ejecución para scripts personalizados se define en `ContentConfig.xml` (`<NativeContentCustomScriptsPath>`):

```text
C:\AutoCAD Plant 3D 2027 Content\CPak Common\CustomScripts\
```

Este repositorio Git está configurado e inicializado **directamente en esa ruta**, por lo que cualquier cambio en los archivos `.py` se aplicará en AutoCAD Plant 3D inmediatamente al ejecutar el comando de registro.

---

## 📂 Estructura del Repositorio

> **Importante**: Para que el compilador de Plant 3D (`varmain`) registre los scripts automáticamente, cada componente `.py` debe estar colocado directamente en la raíz de `CustomScripts/`.

```text
C:\AutoCAD Plant 3D 2027 Content\CPak Common\CustomScripts\
├── .git/                      # Control de versiones Git
├── .gitignore                 # Filtros de archivos temporales/XML
├── README.md                  # Documentación principal
│
├── simple_cylinder.py         # Cilindro sólido paramétrico
├── simple_box.py              # Caja sólida paramétrica
├── simple_sphere.py           # Esfera sólida paramétrica
├── hollow_cylinder.py         # Cilindro hueco (tubo) con corte
├── simple_elbow_90.py         # Codo 90° curvo con TORUS y 2 puertos
├── simple_tee.py              # T con derivación (branch) y 3 puertos
├── simple_union.py            # Unión recta para tubo con 2 puertos
├── utils.py                   # Funciones de validación y conversión
└── __init__.py                # Inicializador del paquete (sin imports relativos)
```

---

## 🚀 Instalación y Registro en AutoCAD Plant 3D

### 1. Agregar la Ruta a Support Paths (Solo la primera vez)
1. En AutoCAD Plant 3D, escribe el comando `OP` (Options) y presiona Enter.
2. Ve a la pestaña **Files** $\rightarrow$ **Support File Search Path**.
3. Haz clic en **Add** $\rightarrow$ **Browse** y selecciona:
   `C:\AutoCAD Plant 3D 2027 Content\CPak Common\CustomScripts`
4. Haz clic en **Apply** y **OK**.

### 2. Registrar los Scripts
En la línea de comandos de AutoCAD Plant 3D, ejecuta:
```text
PLANTREGISTERCUSTOMSCRIPTS
```

### 3. Probar un Componente en Pantalla
Para probar y renderizar una entidad 3D en la consola de AutoCAD:
```lisp
(TESTACPSCRIPT "SIMPLE_CYLINDER")
(TESTACPSCRIPT "SIMPLE_ELBOW_90")
(TESTACPSCRIPT "SIMPLE_TEE")
(TESTACPSCRIPT "SIMPLE_UNION")
```

---

## 💻 Flujo de Trabajo en Git

Para subir tus avances a GitHub ([`jp3d-code/plant3d`](https://github.com/jp3d-code/plant3d.git)):

Abre la terminal de comandos o PowerShell en `C:\AutoCAD Plant 3D 2027 Content\CPak Common\CustomScripts`:

```bash
# 1. Verificar archivos modificados o nuevos
git status

# 2. Agregar cambios al área de preparación (stage)
git add .

# 3. Guardar el commit con mensaje descriptivo
git commit -m "feat: agregar componente racor XYZ con puertos 3D"

# 4. Enviar a GitHub
git push origin main
```

---

## 📐 Estructura del Código y Puertos 3D

Cada script de componente debe seguir esta estructura base usando `varmain.custom` y `varmain.primitiv`:

```python
from varmain.primitiv import *
from varmain.custom import *
from math import *

@activate(
    Group="Elbows",
    TooltipShort="Codo 90",
    TooltipLong="Codo de 90 grados con 2 puertos",
    LengthUnit="in"  # "in" o "mm"
)
@group("MainDimensions")
@param(OD=LENGTH, TooltipShort="Diámetro exterior")
@param(L=LENGTH, TooltipShort="Centro a extremo")
@param(T=LENGTH, TooltipShort="Espesor de pared")
def MI_COMPONENTE(s, OD=1, L=2, T=0.1, **kw):
    R1 = L
    R2 = OD / 2
    
    # 1. Dibujar Geometría
    s = TORUS(s, R1=R1, R2=R2, A=90)
    
    # 2. Definir Puertos (Puntos y Vectores de Conexión)
    s.setPoint(1, (-R1, 0, 0))
    s.setVector(1, (-1, 0, 0))
    
    s.setPoint(2, (0, R1, 0))
    s.setVector(2, (0, 1, 0))
    
    return s
```

---

## 📝 Notas de Depuración

- **Sin importaciones relativas**: Los archivos `__init__.py` dentro del repositorio deben estar vacíos o sin expresiones como `from .module import *` para evitar errores de `exec_module` durante la compilación de `varmain`.
- **Filtro de archivos temporales**: El archivo `.gitignore` ignora automáticamente los archivos `.xml` y `.map` generados durante la compilación de `PLANTREGISTERCUSTOMSCRIPTS`.
