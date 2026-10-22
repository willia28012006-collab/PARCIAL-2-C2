# Inventario por sucursal – Parcial Segundo Cómputo

Proyecto de **Programación Computacional III** – Universidad Gerardo Barrios.

Análisis y visualización del inventario de una empresa salvadoreña con cinco sucursales
(San Salvador, Santa Ana, San Miguel, La Libertad y Sonsonate) usando Pandas, PyQt5 y Matplotlib.

## Integrantes

- William Edgardo Vásquez Lopez
- Melvin Lizandro Castro Sorto

## Contenido del repositorio

| Archivo | Descripción |
|---|---|
| `generar_datos.py` | Genera el inventario simulado con Pandas y lo guarda en `datos.csv` |
| `datos.csv` | Inventario (125 registros, 9 columnas, incluye la columna `sucursal`) |
| `analisis_pandas.py` | Inspección de datos (head, info, dtypes, describe, nulos) y resúmenes por sucursal, categoría y proveedor |
| `app_inventario.py` | Aplicación gráfica PyQt5 con gráficos de Matplotlib, filtros y tabla de datos |
| `generar_informe.py` | Genera el informe de consultoría en PDF |
| `informe_consultoria.pdf` | Informe de consultoría (portada, hallazgos, conclusiones y recomendaciones) |
| `requirements.txt` | Dependencias |

## Instalación y ejecución

```bash
python3 -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate
pip install -r requirements.txt

python3 generar_datos.py        # (opcional) regenera datos.csv
python3 analisis_pandas.py      # imprime la inspección y los resúmenes en consola
python3 app_inventario.py       # abre la aplicación gráfica
python3 generar_informe.py      # (opcional) regenera el PDF
```

## Aplicación gráfica

- Filtros por sucursal y categoría.
- Indicadores: productos, unidades, valor del inventario, margen promedio y stock crítico.
- Gráficos: valor por sucursal, stock por categoría, distribución de márgenes,
  stock vs. precio y participación de proveedores.
- Pestaña con la tabla de datos filtrada.

## Columnas del inventario

`id_producto`, `producto`, `categoria`, `sucursal`, `proveedor`, `stock`,
`costo_unitario`, `precio_unitario`, `ultimo_reabastecimiento`.

> Los datos son simulados con fines académicos.
