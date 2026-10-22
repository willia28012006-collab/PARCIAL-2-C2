"""Genera el inventario de la empresa (datos simulados) y lo guarda en datos.csv."""
import numpy as np
import pandas as pd

SUCURSALES = ["San Salvador", "Santa Ana", "San Miguel", "La Libertad", "Sonsonate"]

# categoria -> {producto: (costo_base, margen_aprox)}
CATALOGO = {
    "Electrónica": {"Televisor 43\"": 260, "Audífonos Bluetooth": 18, "Parlante portátil": 30,
                    "Cargador USB-C": 6, "Smartphone básico": 120},
    "Hogar": {"Licuadora": 22, "Plancha": 15, "Olla de presión": 28,
              "Juego de sábanas": 14, "Ventilador": 20},
    "Ferretería": {"Taladro eléctrico": 45, "Juego de destornilladores": 9,
                   "Cinta métrica": 4, "Pintura galón": 17, "Candado": 5},
    "Papelería": {"Cuaderno universitario": 1.2, "Caja de lapiceros": 3,
                  "Resma de papel": 4.5, "Mochila escolar": 11, "Calculadora": 8},
    "Alimentos": {"Aceite 1L": 2.4, "Arroz 5 lb": 2.8, "Frijoles 5 lb": 4.2,
                  "Azúcar 5 lb": 2.6, "Café molido 1 lb": 3.9},
}
PROVEEDORES = ["Distribuidora Cuscatlán", "Importadora Centroamericana",
               "Comercial Pacífico", "Grupo Mayorista SV"]

# Factor de demanda por sucursal (San Salvador vende más)
FACTOR_SUCURSAL = {"San Salvador": 1.6, "Santa Ana": 1.2, "San Miguel": 1.1,
                   "La Libertad": 1.0, "Sonsonate": 0.8}


def generar(semilla: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(semilla)
    filas = []
    id_prod = 1
    for sucursal in SUCURSALES:
        for categoria, productos in CATALOGO.items():
            for producto, costo_base in productos.items():
                costo = round(costo_base * rng.uniform(0.95, 1.08), 2)
                precio = round(costo * rng.uniform(1.15, 1.55), 2)
                stock = int(rng.gamma(shape=3, scale=18) * FACTOR_SUCURSAL[sucursal])
                if rng.random() < 0.06:          # algunos productos casi agotados
                    stock = int(rng.integers(0, 4))
                fecha = pd.Timestamp("2026-10-15") - pd.Timedelta(days=int(rng.integers(1, 120)))
                filas.append({
                    "id_producto": f"P{id_prod:04d}",
                    "producto": producto,
                    "categoria": categoria,
                    "sucursal": sucursal,
                    "proveedor": rng.choice(PROVEEDORES),
                    "stock": stock,
                    "costo_unitario": costo,
                    "precio_unitario": precio,
                    "ultimo_reabastecimiento": fecha.date().isoformat(),
                })
                id_prod += 1
    return pd.DataFrame(filas)


if __name__ == "__main__":
    df = generar()
    df.to_csv("datos.csv", index=False, encoding="utf-8")
    print(f"datos.csv generado: {df.shape[0]} filas x {df.shape[1]} columnas")
