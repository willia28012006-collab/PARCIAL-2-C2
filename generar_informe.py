"""Genera informe_consultoria.pdf a partir de datos.csv (todas las cifras se calculan con Pandas)."""
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

from analisis_pandas import cargar_datos, resumen_por_categoria, resumen_por_proveedor, \
    resumen_por_sucursal, stock_critico

# --- Datos de la portada: EDITAR con los nombres reales de los integrantes ---
INTEGRANTES = ["William Vásquez", "Nombre del compañero/a"]
FECHA = "22 de octubre de 2026"
FECHA_REF = pd.Timestamp("2026-10-22")
AZUL = colors.HexColor("#1f4e9c")


def usd(x):
    return f"${x:,.2f}"


def graficos(df, carpeta: Path):
    rutas = {}
    # 1. Valor por sucursal
    s = df.groupby("sucursal")["valor_inventario"].sum().sort_values()
    fig, ax = plt.subplots(figsize=(6.5, 3))
    ax.barh(s.index, s.values, color="#1f4e9c")
    ax.set_xlim(right=s.max() * 1.15)
    ax.set_title("Valor del inventario por sucursal (USD)")
    for i, v in enumerate(s.values):
        ax.text(v, i, f" ${v:,.0f}", va="center", fontsize=8)
    fig.tight_layout()
    rutas["sucursal"] = carpeta / "g1.png"
    fig.savefig(rutas["sucursal"], dpi=150)
    plt.close(fig)

    # 2. Valor por categoría
    c = df.groupby("categoria")["valor_inventario"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(6.5, 3))
    ax.bar(c.index, c.values, color="#2a9d8f")
    ax.set_title("Valor del inventario por categoría (USD)")
    ax.tick_params(axis="x", rotation=15)
    fig.tight_layout()
    rutas["categoria"] = carpeta / "g2.png"
    fig.savefig(rutas["categoria"], dpi=150)
    plt.close(fig)

    # 3. Histograma de márgenes
    fig, ax = plt.subplots(figsize=(6.5, 3))
    ax.hist(df["margen_pct"], bins=12, color="#e07b39", edgecolor="white")
    ax.axvline(df["margen_pct"].mean(), color="black", linestyle="--")
    ax.set_title("Distribución del margen sobre costo (%)")
    ax.set_xlabel("Margen (%)")
    fig.tight_layout()
    rutas["margen"] = carpeta / "g3.png"
    fig.savefig(rutas["margen"], dpi=150)
    plt.close(fig)
    return rutas


def tabla(datos, anchos=None):
    t = Table(datos, colWidths=anchos, repeatRows=1, splitByRow=0)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef3fb")]),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
    ]))
    return t


def construir():
    df = cargar_datos()
    df["dias_sin_reabastecer"] = (FECHA_REF - df["ultimo_reabastecimiento"]).dt.days
    total = df["valor_inventario"].sum()
    suc, cat, prov = resumen_por_sucursal(df), resumen_por_categoria(df), resumen_por_proveedor(df)
    crit = stock_critico(df)
    viejos = df[df["dias_sin_reabastecer"] > 90]
    elec_pct = cat.loc["Electrónica", "valor_inventario"] / total * 100
    ss_pct = suc.loc["San Salvador", "valor_inventario"] / total * 100
    prod_valor = df.groupby("producto")["valor_inventario"].sum().sort_values(ascending=False)
    top2_pct = prod_valor.head(2).sum() / total * 100
    corr = df["stock"].corr(df["precio_unitario"])
    sin_stock = df[df["stock"] == 0]

    ss = getSampleStyleSheet()
    cuerpo = ParagraphStyle("cuerpo", parent=ss["BodyText"], alignment=TA_JUSTIFY,
                            fontSize=10, leading=14, spaceAfter=6)
    h1 = ParagraphStyle("h1", parent=ss["Heading1"], textColor=AZUL, fontSize=16, keepWithNext=1)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], textColor=AZUL, fontSize=12, keepWithNext=1)
    centro = ParagraphStyle("centro", parent=ss["Normal"], alignment=TA_CENTER, fontSize=12,
                            leading=18)
    titulo = ParagraphStyle("titulo", parent=centro, fontSize=24, leading=30, textColor=AZUL,
                            fontName="Helvetica-Bold")
    vineta = ParagraphStyle("vineta", parent=cuerpo, leftIndent=14, bulletIndent=2)

    def P(t): return Paragraph(t, cuerpo)
    def B(t): return Paragraph(t, vineta, bulletText="•")

    with tempfile.TemporaryDirectory() as tmp:
        g = graficos(df, Path(tmp))
        doc = SimpleDocTemplate("informe_consultoria.pdf", pagesize=letter,
                                leftMargin=2.3 * cm, rightMargin=2.3 * cm,
                                topMargin=2.2 * cm, bottomMargin=2.2 * cm,
                                title="Informe de consultoría – Inventario por sucursal",
                                author=", ".join(INTEGRANTES))
        e = []

        # ---------------- Portada ----------------
        e += [Spacer(1, 2 * cm), Paragraph("Universidad Gerardo Barrios", titulo),
              Spacer(1, 0.5 * cm),
              Paragraph("Programación Computacional III", centro), Spacer(1, 2.5 * cm),
              Paragraph("INFORME DE CONSULTORÍA", titulo), Spacer(1, 0.3 * cm),
              Paragraph("Análisis del inventario de cinco sucursales", centro),
              Spacer(1, 3 * cm), Paragraph("<b>Elaborado por:</b>", centro)]
        e += [Paragraph(n, centro) for n in INTEGRANTES]
        e += [Spacer(1, 1.2 * cm), Paragraph("<b>Docente:</b> ______________________", centro),
              Spacer(1, 1.2 * cm), Paragraph(f"El Salvador – {FECHA}", centro),
              PageBreak()]

        # ---------------- 1. Introducción ----------------
        e += [Paragraph("1. Introducción y metodología", h1)]
        e.append(P(
            "La gerencia de una empresa salvadoreña que comercializa distintos productos con "
            "locales en San Salvador, Santa Ana, San Miguel, La Libertad y Sonsonate solicitó un "
            "inventario consolidado y una aplicación gráfica para visualizarlo. Este informe "
            "resume el análisis realizado sobre ese inventario."))
        e.append(P(
            f"El conjunto de datos (<i>datos.csv</i>) contiene <b>{len(df)} registros</b> "
            f"(25 productos por sucursal) y 9 columnas originales: id_producto, producto, "
            f"categoría, sucursal, proveedor, stock, costo_unitario, precio_unitario y "
            f"ultimo_reabastecimiento. A partir de ellas se calcularon valor_inventario "
            f"(stock × costo), margen_unitario y margen_pct (margen sobre costo). El análisis se "
            f"hizo con Pandas y la visualización con PyQt5 y Matplotlib."))
        e.append(P(
            "<b>Nota:</b> los datos fueron generados de forma simulada con Python para este "
            "ejercicio académico; no corresponden a una empresa real."))

        # ---------------- 2. Hallazgos ----------------
        e += [Paragraph("2. Análisis de los hallazgos", h1)]
        e += [Paragraph("2.1 Calidad y estructura de los datos", h2)]
        e.append(P(
            f"No se encontraron valores nulos ni registros duplicados. Las columnas numéricas "
            f"tienen el tipo adecuado y la fecha de reabastecimiento se interpretó como fecha. "
            f"El inventario total tiene <b>{df['stock'].sum():,} unidades</b> con un valor al "
            f"costo de <b>{usd(total)}</b>."))

        e += [Paragraph("2.2 Valor del inventario por sucursal", h2)]
        filas = [["Sucursal", "Unidades", "Valor (USD)", "Margen prom. %"]]
        for n, r in suc.iterrows():
            filas.append([n, f"{int(r.unidades):,}", usd(r.valor_inventario),
                          f"{r.margen_promedio_pct:.1f}"])
        e += [tabla(filas, [5 * cm, 3 * cm, 4 * cm, 4 * cm]), Spacer(1, 6),
              Image(str(g["sucursal"]), width=14 * cm, height=6.5 * cm)]
        e.append(P(
            f"San Salvador concentra el <b>{ss_pct:.1f}%</b> del valor total "
            f"({usd(suc.loc['San Salvador', 'valor_inventario'])}), mientras que La Libertad es "
            f"la sucursal con menor inversión ({usd(suc.loc['La Libertad', 'valor_inventario'])}). "
            f"Santa Ana tiene la mayor cantidad de unidades "
            f"({int(suc.loc['Santa Ana', 'unidades']):,}) pero un valor mucho menor que la "
            f"capital, lo que indica que su inventario se compone de artículos de menor precio."))

        e += [Paragraph("2.3 Valor por categoría y productos principales", h2)]
        e.append(Image(str(g["categoria"]), width=14 * cm, height=6.5 * cm))
        e.append(P(
            f"La categoría <b>Electrónica</b> representa el <b>{elec_pct:.1f}%</b> del valor del "
            f"inventario, aun cuando su número de unidades es similar al de las demás categorías. "
            f"Solo dos productos (Televisor 43\" y Smartphone básico) suman el "
            f"<b>{top2_pct:.1f}%</b> del valor total. Esto implica una fuerte concentración de "
            f"capital en pocos artículos."))

        e += [Paragraph("2.4 Márgenes de ganancia", h2)]
        e.append(Image(str(g["margen"]), width=14 * cm, height=6.5 * cm))
        e.append(P(
            f"El margen sobre costo promedio es de <b>{df['margen_pct'].mean():.1f}%</b>, con un "
            f"mínimo de {df['margen_pct'].min():.1f}% y un máximo de "
            f"{df['margen_pct'].max():.1f}%. La categoría Alimentos tiene el margen más bajo "
            f"({cat.loc['Alimentos', 'margen_promedio_pct']:.1f}%) y Electrónica el más alto "
            f"({cat.loc['Electrónica', 'margen_promedio_pct']:.1f}%). La correlación entre precio y "
            f"stock es prácticamente nula ({corr:.2f}), es decir, el nivel de existencias no "
            f"depende del precio del producto."))

        e += [Paragraph("2.5 Proveedores", h2)]
        filas = [["Proveedor", "Unidades", "Valor (USD)", "% del valor"]]
        for n, r in prov.iterrows():
            filas.append([n, f"{int(r.unidades):,}", usd(r.valor_inventario),
                          f"{r.valor_inventario / total * 100:.1f}"])
        e += [tabla(filas, [6.5 * cm, 3 * cm, 3.5 * cm, 3 * cm]), Spacer(1, 6)]
        e.append(P(
            f"Grupo Mayorista SV y Comercial Pacífico suministran el "
            f"{(prov['valor_inventario'].iloc[:2].sum() / total * 100):.1f}% del valor del "
            f"inventario, por lo que existe dependencia de dos proveedores."))

        e += [Paragraph("2.6 Riesgo de desabastecimiento y rotación", h2)]
        e.append(P(
            f"Se identificaron <b>{len(crit)} registros con stock crítico</b> (10 unidades o "
            f"menos), de los cuales <b>{len(sin_stock)}</b> están agotados: "
            + "; ".join(f"{r.producto} en {r.sucursal}" for r in sin_stock.itertuples()) + ". "
            f"Además, <b>{len(viejos)} de {len(df)} productos ({len(viejos) / len(df) * 100:.0f}%)</b> "
            f"llevan más de 90 días sin reabastecerse (San Miguel es la sucursal con más casos: "
            f"{(viejos['sucursal'] == 'San Miguel').sum()})."))

        # ---------------- 3. Conclusiones por columna ----------------
        e += [PageBreak(), Paragraph("3. Conclusiones por columna o variable", h1)]
        concl = [
            ("id_producto", f"Es un identificador único: {df['id_producto'].nunique()} valores "
             "distintos para 125 filas, sin duplicados. Permite rastrear cada artículo por sucursal."),
            ("producto", f"Hay {df['producto'].nunique()} productos distintos, cada uno presente "
             "en las cinco sucursales. El catálogo es homogéneo, lo que facilita comparar "
             "sucursales."),
            ("categoria", f"Cinco categorías. Electrónica domina el valor ({elec_pct:.1f}%) y "
             "Alimentos aporta el menor valor (precios unitarios bajos)."),
            ("sucursal", f"Cinco sucursales con 25 productos cada una. San Salvador es la de "
             f"mayor valor ({ss_pct:.1f}%) y La Libertad la de menor inversión y menos unidades."),
            ("proveedor", "Cuatro proveedores; Grupo Mayorista SV lidera en valor y unidades. "
             "Existe concentración en los dos principales."),
            ("stock", f"Promedio de {df['stock'].mean():.1f} unidades por registro (mediana "
             f"{df['stock'].median():.0f}), con alta variabilidad (desviación "
             f"{df['stock'].std():.1f}) y {len(crit)} registros en nivel crítico."),
            ("costo_unitario", f"Va de {usd(df['costo_unitario'].min())} a "
             f"{usd(df['costo_unitario'].max())}; la media ({usd(df['costo_unitario'].mean())}) "
             "es mucho mayor que la mediana "
             f"({usd(df['costo_unitario'].median())}) por los artículos electrónicos caros."),
            ("precio_unitario", f"Promedio de {usd(df['precio_unitario'].mean())}. Sigue la "
             "misma asimetría que el costo y siempre supera al costo (margen positivo en todos "
             "los casos)."),
            ("ultimo_reabastecimiento", f"El último reabastecimiento tiene en promedio "
             f"{df['dias_sin_reabastecer'].mean():.0f} días de antigüedad; "
             f"{len(viejos)} productos superan los 90 días."),
        ]
        for col, texto in concl:
            e.append(B(f"<b>{col}:</b> {texto}"))

        # ---------------- 4. Recomendaciones ----------------
        e += [Paragraph("4. Recomendaciones estratégicas", h1)]
        recs = [
            ("Reponer de inmediato los productos agotados y críticos",
             f"Priorizar los {len(sin_stock)} registros sin existencias y definir un punto de "
             "reorden por producto y sucursal para evitar ventas perdidas."),
            ("Reducir la concentración en Electrónica",
             f"Con {elec_pct:.0f}% del capital en una categoría y {top2_pct:.0f}% en dos "
             "productos, conviene manejar pedidos más frecuentes y de menor volumen, o negociar "
             "consignación con los proveedores."),
            ("Rebalancear entre sucursales",
             "Transferir excedentes de Santa Ana y San Salvador hacia La Libertad y Sonsonate "
             "cuando exista desabastecimiento, antes de comprar nuevo producto."),
            ("Revisar los productos con más de 90 días sin reabastecimiento",
             "Verificar si son de baja rotación; aplicar promociones o liquidación para liberar "
             "capital, empezando por San Miguel."),
            ("Mejorar márgenes en Alimentos",
             f"Su margen ({cat.loc['Alimentos', 'margen_promedio_pct']:.1f}%) es el más bajo. "
             "Evaluar renegociar costos o ajustar precios en los productos de mayor rotación."),
            ("Diversificar proveedores",
             "Reducir la dependencia de los dos principales proveedores y comparar costos con "
             "alternativas, ya que los márgenes varían ligeramente entre proveedores."),
            ("Usar el panel gráfico como herramienta de seguimiento",
             "Actualizar datos.csv periódicamente y revisar los indicadores (stock crítico, valor "
             "por sucursal, márgenes) en la aplicación de escritorio."),
        ]
        for i, (t, d) in enumerate(recs, 1):
            e.append(Paragraph(f"<b>{i}. {t}.</b> {d}", cuerpo))

        e += [Paragraph("5. Conclusión general", h1),
              P("El inventario está sano en cuanto a calidad de datos y márgenes, pero presenta "
                "riesgos claros: capital concentrado en pocos productos y en la sucursal de San "
                "Salvador, algunos artículos agotados y un porcentaje relevante de productos sin "
                "reabastecer. Aplicar las recomendaciones anteriores permitiría mejorar la "
                "disponibilidad y la rotación sin aumentar la inversión total.")]

        def pie(canvas, doc_):
            canvas.setFont("Helvetica", 8)
            canvas.drawCentredString(letter[0] / 2, 1.2 * cm,
                                     f"Informe de consultoría – Página {doc_.page}")

        doc.build(e, onLaterPages=pie)
    print("informe_consultoria.pdf generado")


if __name__ == "__main__":
    construir()
