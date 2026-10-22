"""Análisis del inventario con Pandas: inspección, limpieza y métricas derivadas."""
import pandas as pd

RUTA_CSV = "datos.csv"


def cargar_datos(ruta: str = RUTA_CSV) -> pd.DataFrame:
    """Carga el CSV y agrega columnas calculadas."""
    df = pd.read_csv(ruta, parse_dates=["ultimo_reabastecimiento"])
    df["valor_inventario"] = df["stock"] * df["costo_unitario"]
    df["margen_unitario"] = df["precio_unitario"] - df["costo_unitario"]
    df["margen_pct"] = df["margen_unitario"] / df["costo_unitario"] * 100
    return df


def inspeccionar(df: pd.DataFrame) -> None:
    """Funciones de inspección: estructura, tipos y estadísticas básicas."""
    print("=" * 60)
    print("1. PRIMERAS FILAS (head)")
    print(df.head())

    print("\n2. DIMENSIONES (shape):", df.shape)
    print("   Columnas:", list(df.columns))

    print("\n3. INFORMACIÓN GENERAL (info)")
    df.info()

    print("\n4. TIPOS DE DATOS (dtypes)")
    print(df.dtypes)

    print("\n5. VALORES NULOS (isnull().sum())")
    print(df.isnull().sum())

    print("\n6. DUPLICADOS:", df.duplicated().sum())

    print("\n7. ESTADÍSTICAS NUMÉRICAS (describe)")
    print(df.describe().round(2))

    print("\n8. ESTADÍSTICAS CATEGÓRICAS (columnas no numéricas)")
    print(df.select_dtypes(exclude="number").describe())

    print("\n9. VALORES ÚNICOS POR COLUMNA (nunique)")
    print(df.nunique())


def resumen_por_sucursal(df: pd.DataFrame) -> pd.DataFrame:
    return (df.groupby("sucursal")
              .agg(productos=("id_producto", "count"),
                   unidades=("stock", "sum"),
                   valor_inventario=("valor_inventario", "sum"),
                   margen_promedio_pct=("margen_pct", "mean"))
              .sort_values("valor_inventario", ascending=False)
              .round(2))


def resumen_por_categoria(df: pd.DataFrame) -> pd.DataFrame:
    return (df.groupby("categoria")
              .agg(unidades=("stock", "sum"),
                   valor_inventario=("valor_inventario", "sum"),
                   margen_promedio_pct=("margen_pct", "mean"))
              .sort_values("valor_inventario", ascending=False)
              .round(2))


def resumen_por_proveedor(df: pd.DataFrame) -> pd.DataFrame:
    return (df.groupby("proveedor")
              .agg(unidades=("stock", "sum"), valor_inventario=("valor_inventario", "sum"))
              .sort_values("valor_inventario", ascending=False)
              .round(2))


def stock_critico(df: pd.DataFrame, umbral: int = 10) -> pd.DataFrame:
    return df[df["stock"] <= umbral].sort_values("stock")[
        ["id_producto", "producto", "categoria", "sucursal", "stock"]]


def top_margen(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    return (df.groupby("producto")["margen_pct"].mean()
              .sort_values(ascending=False).head(n).round(2).to_frame())


if __name__ == "__main__":
    datos = cargar_datos()
    inspeccionar(datos)
    print("\n" + "=" * 60)
    print("RESUMEN POR SUCURSAL\n", resumen_por_sucursal(datos))
    print("\nRESUMEN POR CATEGORÍA\n", resumen_por_categoria(datos))
    print("\nRESUMEN POR PROVEEDOR\n", resumen_por_proveedor(datos))
    print("\nPRODUCTOS CON STOCK CRÍTICO (<= 10)\n", stock_critico(datos))
    print("\nTOP 5 PRODUCTOS POR MARGEN %\n", top_margen(datos))
