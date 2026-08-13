# Catálogo Swagelok — Racores para Tubo Galgables y Adaptadores

**Documento:** MS-01-140 (Rev AH, es-ES, julio 2023) — "Racores para Tubo Galgables y
Adaptadores".

Este directorio es una **reescritura estructurada en Markdown** del catálogo original
(`index.html`), organizada por **familias** (cada carpeta = una familia con forma única)
y **subfamilias** (cada archivo `.md` = una variante por rosca / extremo / tamaño).

> El objetivo es tener documentación legible y navegable para crear los scripts
> paramétricos de Plant 3D (`varmain`) de cada racor.

## Estructura

| Carpeta | Familia | Subfamilias |
|---|---|---|
| [`01-uniones/`](01-uniones/index.md) | Uniones rectas (2 extremos tubo) | Unión, reductora, pasamuros, reductora pasamuros |
| [`02-conectores-macho/`](02-conectores-macho/index.md) | Conectores macho (tubo + rosca/soldadura) | NPT, ISO cónica RT, ISO paralela RS/RP, SAE ST, OR, AN, roscas pequeñas, soldadura |
| [`03-conectores-hembra/`](03-conectores-hembra/index.md) | Conectores hembra | NPT, ISO RT/RJ/RP, RG manómetros, NPT pasamuros |
| [`04-reductores/`](04-reductores/index.md) | Reductores | Reductor, largo, pasamuros |
| [`05-tubos-manguito/`](05-tubos-manguito/index.md) | Tubos manguito conectores | Conector, conector reductor |
| [`06-tapones/`](06-tapones/index.md) | Tapones y protectores | Tapón tubo, tapón racor, protector de venteo |
| [`07-codos-90/`](07-codos-90/index.md) | Codos de 90° | Unión, macho NPT/RT, reductor, orientable, soldadura, hembra |
| [`08-codos-45/`](08-codos-45/index.md) | Codos de 45° | Macho NPT, orientable ST |
| [`09-tes/`](09-tes/index.md) | Tes | Unión, macho lateral/recta, orientables, hembra, adaptadoras |
| [`10-cruces/`](10-cruces/index.md) | Cruces | Unión |
| [`11-aplicaciones-especiales/`](11-aplicaciones-especiales/index.md) | Aplicaciones especiales | Brida Kwik, placa orificio, taladrados |
| [`12-adaptadores-tubo/`](12-adaptadores-tubo/index.md) | Adaptadores a tubo | Macho (NPT/RT/RS/RP/ST/OR/AN/W), hembra (NPT/RT/RP/RJ/RG/AN) |
| [`13-piezas-repuesto/`](13-piezas-repuesto/index.md) | Piezas de repuesto | Tuercas, férulas, juegos, juntas planas, juntas tóricas |
| [`14-herramientas/`](14-herramientas/index.md) | Herramientas y accesorios | Unidades de deformación, preensamblaje, llaves, galgas, etc. |
| [`15-instalacion/`](15-instalacion/index.md) | Instalación | Instrucciones, galgabilidad, reutilización |

## Cómo se lee una referencia Swagelok (pág. 55)

```
SS - 2 0 0 - 1 - 2 RT
│   │   │   │ │ │  └─ Rosca/2º extremo (RT=ISO cónica, RS/RP=ISO paralela,
│   │   │   │ │ │      ST=SAE/MS, OR=junta tórica, AN=37°, W=soldadura)
│   │   │   │ │ └─ Tamaño 2º extremo (2=1/8")
│   │   │   │ └─ Tipo de racor (1=conector macho, 6=unión, 7=hembra,
│   │   │   │      9=codo unión, 2=codo macho 90°, 8=codo hembra, 5=codo 45°,
│   │   │   │      3=te, 4=cruz, A=adaptador, R=reductor, C/P=tapones, etc.)
│   │   │   └─ Serie / Componente
│   │   └─ Tamaño Ø ext. tubo (200 = 1/8")
│   └─ Material (SS=inox 316, B=latón, S=acero carbono, ...)
└─ Prefijo estándar
```

- **Tamaño de tubo fraccional:** `100`=1/16, `200`=1/8, `300`=3/16, `400`=1/4,
  `500`=5/16, `600`=3/8, `810`=1/2, `1010`=5/8, `1210`=3/4, `1410`=7/8, `1610`=1,
  `2000`=1 1/4, `2400`=1 1/2, `3200`=2.
- **Tamaño de tubo métrico:** `2M0`=2 mm ... `50M0`=50 mm (el `M0` marca métrico).
- Para adaptadores a tubo el formato es `SS - 2 - TA - 1 - 4 RT` (`TA`/`MTA` =
  adaptador fraccional/métrico).

## Notas generales

- Dimensiones en **pulgadas** (fraccionales y decimales) y **mm**.
- `A` = longitud centro a extremo, `D` = Ø ext. tubo, `E` = paso mínimo,
  `F` = entre caras del hexágono, `T` = Ø ext. tubo, `Tx` = Ø ext. tubo del 2º extremo.
- La dimensión `E` es el **paso mínimo**: los racores pueden taladrarse a un diámetro
  interior mayor en la conexión roscada/soldada.
- Disponibles en medidas de 2 a 50 mm y de 1/16 a 2 pulg.

## Fuente

`index.html` (conversión del PDF original MS-01-140ES). Ver también la sección
"Información de pedido adicional" (págs. 55-56) para el desglose completo de las
referencias.
