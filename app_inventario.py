"""Aplicación gráfica (PyQt5 + Matplotlib) para visualizar el inventario por sucursal."""
import sys

import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QHeaderView, QLabel,
                             QMainWindow, QTableWidget, QTableWidgetItem, QTabWidget,
                             QVBoxLayout, QWidget)

from analisis_pandas import cargar_datos

COLORES = ["#1f4e9c", "#e07b39", "#2a9d8f", "#8e5ea2", "#c0392b"]
TODAS = "Todas"


class GraficoCanvas(FigureCanvas):
    """Lienzo de Matplotlib incrustado en un widget de Qt."""

    def __init__(self):
        self.fig = Figure(figsize=(6, 4), tight_layout=True)
        super().__init__(self.fig)
        self.ax = self.fig.add_subplot(111)

    def limpiar(self):
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)


class VentanaInventario(QMainWindow):
    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self.df = df
        self.setWindowTitle("Inventario por sucursal – Dashboard")
        self.resize(1100, 720)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # --- Filtros ---
        filtros = QHBoxLayout()
        self.cb_sucursal = QComboBox()
        self.cb_sucursal.addItems([TODAS] + sorted(df["sucursal"].unique()))
        self.cb_categoria = QComboBox()
        self.cb_categoria.addItems([TODAS] + sorted(df["categoria"].unique()))
        filtros.addWidget(QLabel("Sucursal:"))
        filtros.addWidget(self.cb_sucursal)
        filtros.addWidget(QLabel("Categoría:"))
        filtros.addWidget(self.cb_categoria)
        filtros.addStretch()
        layout.addLayout(filtros)

        # --- Indicadores (KPIs) ---
        self.lbl_kpi = QLabel()
        self.lbl_kpi.setStyleSheet(
            "font-size: 14px; padding: 8px; background: #eef3fb; border-radius: 6px;")
        layout.addWidget(self.lbl_kpi)

        # --- Pestañas con gráficos ---
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self.graficos = {}
        for nombre in ["Valor por sucursal", "Stock por categoría",
                       "Distribución de márgenes", "Stock vs. precio", "Proveedores"]:
            canvas = GraficoCanvas()
            pagina = QWidget()
            lay = QVBoxLayout(pagina)
            lay.addWidget(NavigationToolbar(canvas, self))
            lay.addWidget(canvas)
            self.tabs.addTab(pagina, nombre)
            self.graficos[nombre] = canvas

        # Pestaña de tabla
        self.tabla = QTableWidget()
        self.tabs.addTab(self.tabla, "Datos")

        self.cb_sucursal.currentTextChanged.connect(self.actualizar)
        self.cb_categoria.currentTextChanged.connect(self.actualizar)
        self.actualizar()

    # ------------------------------------------------------------------
    def filtrado(self) -> pd.DataFrame:
        d = self.df
        if self.cb_sucursal.currentText() != TODAS:
            d = d[d["sucursal"] == self.cb_sucursal.currentText()]
        if self.cb_categoria.currentText() != TODAS:
            d = d[d["categoria"] == self.cb_categoria.currentText()]
        return d

    def actualizar(self):
        d = self.filtrado()
        if d.empty:
            self.lbl_kpi.setText("Sin datos para el filtro seleccionado.")
            return
        self.lbl_kpi.setText(
            f"<b>Productos:</b> {len(d)} &nbsp;|&nbsp; "
            f"<b>Unidades en stock:</b> {d['stock'].sum():,} &nbsp;|&nbsp; "
            f"<b>Valor del inventario:</b> ${d['valor_inventario'].sum():,.2f} &nbsp;|&nbsp; "
            f"<b>Margen promedio:</b> {d['margen_pct'].mean():.1f}% &nbsp;|&nbsp; "
            f"<b>Stock crítico (≤10):</b> {(d['stock'] <= 10).sum()}")
        self.graf_valor_sucursal(d)
        self.graf_stock_categoria(d)
        self.graf_margenes(d)
        self.graf_dispersion(d)
        self.graf_proveedores(d)
        self.llenar_tabla(d)

    # ------------------------------------------------------------------
    def graf_valor_sucursal(self, d):
        c = self.graficos["Valor por sucursal"]
        c.limpiar()
        s = d.groupby("sucursal")["valor_inventario"].sum().sort_values()
        c.ax.barh(s.index, s.values, color=COLORES[0])
        c.ax.set_title("Valor del inventario por sucursal (USD)")
        c.ax.set_xlabel("USD")
        c.ax.set_xlim(right=s.max() * 1.15)
        for i, v in enumerate(s.values):
            c.ax.text(v, i, f" ${v:,.0f}", va="center", fontsize=9)
        c.draw()

    def graf_stock_categoria(self, d):
        c = self.graficos["Stock por categoría"]
        c.limpiar()
        s = d.groupby("categoria")["stock"].sum().sort_values(ascending=False)
        c.ax.bar(s.index, s.values, color=COLORES[2])
        c.ax.set_title("Unidades en stock por categoría")
        c.ax.set_ylabel("Unidades")
        c.ax.tick_params(axis="x", rotation=20)
        c.draw()

    def graf_margenes(self, d):
        c = self.graficos["Distribución de márgenes"]
        c.limpiar()
        c.ax.hist(d["margen_pct"], bins=12, color=COLORES[1], edgecolor="white")
        c.ax.axvline(d["margen_pct"].mean(), color="black", linestyle="--",
                     label=f"Promedio {d['margen_pct'].mean():.1f}%")
        c.ax.set_title("Distribución del margen de ganancia (%)")
        c.ax.set_xlabel("Margen sobre costo (%)")
        c.ax.set_ylabel("Cantidad de productos")
        c.ax.legend()
        c.draw()

    def graf_dispersion(self, d):
        c = self.graficos["Stock vs. precio"]
        c.limpiar()
        for i, (cat, g) in enumerate(d.groupby("categoria")):
            c.ax.scatter(g["precio_unitario"], g["stock"], label=cat,
                         color=COLORES[i % len(COLORES)], alpha=0.8)
        c.ax.set_xscale("log")
        c.ax.set_title("Relación entre precio unitario y stock")
        c.ax.set_xlabel("Precio unitario (USD, escala log)")
        c.ax.set_ylabel("Stock (unidades)")
        c.ax.legend(fontsize=8)
        c.draw()

    def graf_proveedores(self, d):
        c = self.graficos["Proveedores"]
        c.limpiar()
        s = d.groupby("proveedor")["valor_inventario"].sum()
        c.ax.pie(s.values, labels=s.index, autopct="%1.1f%%", colors=COLORES, startangle=90)
        c.ax.set_title("Participación de proveedores en el valor del inventario")
        c.draw()

    def llenar_tabla(self, d):
        cols = ["id_producto", "producto", "categoria", "sucursal", "proveedor",
                "stock", "costo_unitario", "precio_unitario", "ultimo_reabastecimiento"]
        self.tabla.setColumnCount(len(cols))
        self.tabla.setHorizontalHeaderLabels(cols)
        self.tabla.setRowCount(len(d))
        for r, (_, fila) in enumerate(d[cols].iterrows()):
            for k, col in enumerate(cols):
                v = fila[col]
                if isinstance(v, pd.Timestamp):
                    v = v.strftime("%Y-%m-%d")
                self.tabla.setItem(r, k, QTableWidgetItem(str(v)))
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)


def main():
    app = QApplication(sys.argv)
    ventana = VentanaInventario(cargar_datos())
    ventana.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
