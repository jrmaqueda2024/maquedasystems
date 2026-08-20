from utilidades_ui import formatear_gs, habilitar_deseleccion_treeview
"""
ventana_reporte_rango.py
Ventana para generar un reporte de ventas en un rango de fechas (desde-hasta),
cada extremo seleccionable con calendario. Muestra todas las ventas del
período en una sola lista, más los totales acumulados.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import datetime

from models_ventas import resumen_financiero_en_rango
from widget_calendario import abrir_selector_fecha
from menu_reporte_general import BotonReporteGeneral
from auth import filtro_usuario_ventas

AZUL_RIBBON = "#1d5fd6"
GRIS_FONDO = "#f4f5f7"


class VentanaReporteRango(tk.Toplevel):
    def __init__(self, parent, usuario_actual=None):
        super().__init__(parent)
        self.usuario_actual = usuario_actual
        self.title("Reporte por Rango de Fechas")
        self.geometry("820x560")
        self.minsize(700, 480)
        self.configure(bg="white")
        self.grab_set()

        hoy = datetime.date.today()
        self.fecha_desde = hoy - datetime.timedelta(days=7)
        self.fecha_hasta = hoy

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_barra_titulo()
        self._construir_selector_rango()
        self._construir_grilla()
        self._construir_panel_totales()

        self._actualizar_reporte()

    def _construir_barra_titulo(self):
        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text="Reporte por Rango de Fechas", font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

    def _construir_selector_rango(self):
        barra = tk.Frame(self, bg=GRIS_FONDO)
        barra.grid(row=1, column=0, sticky="ew")

        contenido = tk.Frame(barra, bg=GRIS_FONDO)
        contenido.pack(pady=10, padx=15, anchor="w")

        tk.Label(contenido, text="Desde:", font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).pack(side="left")
        self.label_desde = tk.Label(contenido, text=self._fecha_corta(self.fecha_desde),
                                     font=("Segoe UI", 9, "bold"), bg="white", fg=AZUL_RIBBON,
                                     relief="solid", bd=1, padx=10, pady=4, cursor="hand2")
        self.label_desde.pack(side="left", padx=(6, 15))
        self.label_desde.bind("<Button-1>", lambda e: self._elegir_fecha_desde())

        tk.Label(contenido, text="Hasta:", font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).pack(side="left")
        self.label_hasta = tk.Label(contenido, text=self._fecha_corta(self.fecha_hasta),
                                     font=("Segoe UI", 9, "bold"), bg="white", fg=AZUL_RIBBON,
                                     relief="solid", bd=1, padx=10, pady=4, cursor="hand2")
        self.label_hasta.pack(side="left", padx=(6, 15))
        self.label_hasta.bind("<Button-1>", lambda e: self._elegir_fecha_hasta())

        self.boton_reporte = BotonReporteGeneral(
            contenido, obtener_datos_callback=self._obtener_datos_reporte,
            nombre_archivo_base=f"Reporte_Ventas_{self.fecha_desde.isoformat()}_a_{self.fecha_hasta.isoformat()}",
        )
        self.boton_reporte.generador_pdf_dashboard = self._generar_pdf_dashboard
        self.boton_reporte.pack(side="left", padx=(10, 0))

    def _fecha_corta(self, fecha: datetime.date) -> str:
        return fecha.strftime("%d/%m/%Y")

    def _elegir_fecha_desde(self):
        abrir_selector_fecha(self, self.fecha_desde, self._al_elegir_desde)

    def _elegir_fecha_hasta(self):
        abrir_selector_fecha(self, self.fecha_hasta, self._al_elegir_hasta)

    def _al_elegir_desde(self, fecha: datetime.date):
        if fecha > self.fecha_hasta:
            messagebox.showwarning("Rango inválido", "La fecha 'Desde' no puede ser posterior a 'Hasta'.")
            return
        self.fecha_desde = fecha
        self.label_desde.config(text=self._fecha_corta(fecha))
        self._actualizar_reporte()

    def _al_elegir_hasta(self, fecha: datetime.date):
        if fecha < self.fecha_desde:
            messagebox.showwarning("Rango inválido", "La fecha 'Hasta' no puede ser anterior a 'Desde'.")
            return
        self.fecha_hasta = fecha
        self.label_hasta.config(text=self._fecha_corta(fecha))
        self._actualizar_reporte()

    def _construir_grilla(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=2, column=0, sticky="nsew", padx=10, pady=(10, 5))

        columnas = ("codigo", "fecha_hora", "cliente", "importe", "estado", "forma_pago", "factura")
        encabezados = ("Código", "Fecha y Hora", "Cliente", "Importe", "Estado Cuenta", "Forma de Pago", "Factura")

        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc in zip(columnas, encabezados):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=110, anchor="center")
        self.tabla.column("cliente", width=160, anchor="w")

        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        scrollbar_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=scrollbar.set, xscrollcommand=scrollbar_h.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        scrollbar_h.grid(row=1, column=0, sticky="ew")

        self.tabla.tag_configure("cancelado", foreground="#9ca3af")

    def _construir_panel_totales(self):
        panel = tk.Frame(self, bg=GRIS_FONDO, height=70)
        panel.grid(row=3, column=0, sticky="ew")
        panel.grid_propagate(False)

        contenido = tk.Frame(panel, bg=GRIS_FONDO)
        contenido.pack(fill="x", padx=15, pady=12)

        tk.Label(contenido, text="Cantidad de Ventas:", font=("Segoe UI", 9), bg=GRIS_FONDO).pack(side="left")
        self.label_cantidad = tk.Label(contenido, text="0", font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO)
        self.label_cantidad.pack(side="left", padx=(4, 20))

        tk.Label(contenido, text="Ventas Totales:", font=("Segoe UI", 11), bg=GRIS_FONDO).pack(side="left")
        self.label_total_periodo = tk.Label(contenido, text="Gs. 0", font=("Segoe UI", 13, "bold"),
                                             bg=GRIS_FONDO, fg=AZUL_RIBBON)
        self.label_total_periodo.pack(side="left", padx=(4, 20))

        tk.Label(contenido, text="Ganancia Estimada:", font=("Segoe UI", 11), bg=GRIS_FONDO).pack(side="left")
        self.label_ganancia_periodo = tk.Label(contenido, text="Gs. 0", font=("Segoe UI", 13, "bold"),
                                                bg=GRIS_FONDO, fg="#16a34a")
        self.label_ganancia_periodo.pack(side="left", padx=(4, 0))

    def _actualizar_reporte(self):
        resumen = resumen_financiero_en_rango(
            self.fecha_desde.isoformat(), self.fecha_hasta.isoformat(),
            usuario_id=filtro_usuario_ventas(self.usuario_actual))

        # Mantiene el nombre de archivo sugerido sincronizado con el rango actual.
        self.boton_reporte.nombre_archivo_base = (
            f"Reporte_Ventas_{self.fecha_desde.isoformat()}_a_{self.fecha_hasta.isoformat()}"
        )

        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        for v in resumen["ventas"]:
            etiqueta_tags = ("cancelado",) if v["estado"] == "Cancelado" else ()
            self.tabla.insert("", "end", iid=str(v["id"]), values=(
                v["id"], v["fecha"], v["cliente"], formatear_gs(v['importe']),
                v["estado"], v["forma_pago"], v["factura"],
            ), tags=etiqueta_tags)

        self.label_cantidad.config(text=str(len(resumen["ventas"])))
        self.label_total_periodo.config(text=formatear_gs(resumen['ventas_totales']))
        self.label_ganancia_periodo.config(text=formatear_gs(resumen['ganancia']))

    # ---------------- REPORTE GENERAL: puentes hacia el controlador genérico ----------------
    def _obtener_datos_reporte(self) -> dict:
        from reportes_datos import preparar_datos_reporte_ventas
        nombre_usuario = self.usuario_actual.get("nombre_completo", "") if self.usuario_actual else ""
        return preparar_datos_reporte_ventas(
            self.fecha_desde.isoformat(), self.fecha_hasta.isoformat(), generado_por=nombre_usuario,
            usuario_id=filtro_usuario_ventas(self.usuario_actual),
        )

    def _generar_pdf_dashboard(self, ruta: str):
        from reporte_pdf import generar_reporte_pdf
        nombre_usuario = self.usuario_actual.get("nombre_completo", "") if self.usuario_actual else ""
        generar_reporte_pdf(
            ruta, self.fecha_desde.isoformat(), self.fecha_hasta.isoformat(), generado_por=nombre_usuario,
            usuario_id=filtro_usuario_ventas(self.usuario_actual),
        )
