"""
ventana_creditos.py
Módulo Créditos: listado de ventas a crédito (generadas automáticamente
por models_ventas.procesar_venta cuando la condición de venta es
"crédito"), con vista de Resumen por cliente, vista de Pendientes/Todos
(individual o agrupada por cliente), registro de pagos parciales, y
Estado de Cuenta imprimible por cliente.
"""
import datetime
import tkinter as tk
from tkinter import ttk, messagebox

from models_creditos import (
    listar_creditos, resumen_por_cliente, obtener_detalle_credito,
    registrar_pago_credito, estado_cuenta_cliente, totales_creditos_pendientes,
)
from utilidades_ui import ajustar_tamaño_ventana, formatear_gs, habilitar_deseleccion_treeview
from traducciones import t

AZUL_RIBBON = "#1d5fd6"
GRIS_FONDO = "#f4f5f7"
GRIS_BORDE = "#e2e8f0"
VERDE = "#16a34a"
ROJO = "#dc2626"
GRIS_TEXTO = "#6b7280"


def _formatear_fecha(fecha: str) -> str:
    if not fecha:
        return "—"
    try:
        return datetime.date.fromisoformat(fecha[:10]).strftime("%d/%m/%Y")
    except ValueError:
        return fecha


# ============================================================
# PANEL PRINCIPAL
# ============================================================
class PanelCreditos(tk.Frame):
    def __init__(self, parent, usuario_actual):
        super().__init__(parent, bg="white")
        self.usuario_actual = usuario_actual
        self.var_vista = tk.StringVar(value="pendientes")
        self.var_agrupado = tk.BooleanVar(value=False)
        self.var_resumen_visible = tk.BooleanVar(value=False)
        self.var_busqueda = tk.StringVar()
        # Guarda cliente_id de cada fila de la tabla (créditos o clientes agrupados)
        self._cliente_por_fila = {}

        self._construir_barra_superior()
        self._construir_tabla()
        self._construir_panel_resumen()
        self._cargar()

    # ---------------- BARRA SUPERIOR (ribbon) ----------------
    def _construir_barra_superior(self):
        barra = tk.Frame(self, bg="white")
        barra.pack(fill="x", padx=10, pady=(10, 5))

        self.btn_estado_cuenta = tk.Button(
            barra, text=t("creditos_estado_cuenta"), font=("Segoe UI", 9, "bold"),
            bg="#f3f4f6", fg="#9ca3af", relief="flat", padx=12, pady=6, justify="left",
            state="disabled", command=self._abrir_estado_cuenta,
        )
        self.btn_estado_cuenta.pack(side="left", padx=(0, 6))

        self.btn_agrupar = tk.Button(
            barra, text=t("creditos_agrupar_cliente"), font=("Segoe UI", 9, "bold"),
            bg="white", fg="#1e293b", relief="flat", padx=12, pady=6, justify="left",
            cursor="hand2", command=self._alternar_agrupar,
        )
        self.btn_agrupar.pack(side="left", padx=(0, 12))

        tk.Frame(barra, bg=GRIS_BORDE, width=1).pack(side="left", fill="y", padx=(0, 12))

        # "Vista": arriba el toggle de Resumen (ojo), abajo los radios de filtro
        frame_vista = tk.Frame(barra, bg="white")
        frame_vista.pack(side="left")
        self.lbl_toggle_resumen = tk.Label(
            frame_vista, text=t("creditos_mostrar_resumen"), font=("Segoe UI", 9),
            bg="white", fg=AZUL_RIBBON, cursor="hand2")
        self.lbl_toggle_resumen.pack(anchor="w")
        self.lbl_toggle_resumen.bind("<Button-1>", lambda e: self._alternar_resumen())

        frame_radios = tk.Frame(frame_vista, bg="white")
        frame_radios.pack(anchor="w")
        tk.Radiobutton(frame_radios, text=t("creditos_mostrar_pendientes"), variable=self.var_vista,
                      value="pendientes", bg="white", font=("Segoe UI", 9),
                      command=self._cargar).pack(side="left", padx=(0, 10))
        tk.Radiobutton(frame_radios, text=t("creditos_mostrar_todos"), variable=self.var_vista,
                      value="todos", bg="white", font=("Segoe UI", 9),
                      command=self._cargar).pack(side="left")

        entry = tk.Entry(barra, textvariable=self.var_busqueda, font=("Segoe UI", 9), width=28)
        entry.pack(side="right")
        entry.bind("<KeyRelease>", lambda e: self._cargar())
        tk.Label(barra, text="🔍", font=("Segoe UI", 10), bg="white").pack(side="right", padx=(0, 4))

        tk.Button(barra, text="🔄", font=("Segoe UI", 10), bg="white", relief="flat",
                  cursor="hand2", command=self._cargar).pack(side="right", padx=(0, 10))

    def _alternar_agrupar(self):
        self.var_agrupado.set(not self.var_agrupado.get())
        if self.var_agrupado.get():
            self.btn_agrupar.config(text=t("creditos_agrupar_venta"))
        else:
            self.btn_agrupar.config(text=t("creditos_agrupar_cliente"))
        self._reconstruir_columnas()
        self._cargar()

    def _alternar_resumen(self):
        self.var_resumen_visible.set(not self.var_resumen_visible.get())
        if self.var_resumen_visible.get():
            self.lbl_toggle_resumen.config(text=t("creditos_ocultar_resumen"))
            self.frame_resumen.pack(fill="x", side="bottom")
            self._actualizar_resumen()
        else:
            self.lbl_toggle_resumen.config(text=t("creditos_mostrar_resumen"))
            self.frame_resumen.pack_forget()

    # ---------------- TABLA ----------------
    def _construir_tabla(self):
        self.contenedor = tk.Frame(self, bg="white")
        self.contenedor.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        self.contenedor.grid_rowconfigure(0, weight=1)
        self.contenedor.grid_columnconfigure(0, weight=1)

        self.tabla = None
        self._reconstruir_columnas()

    def _reconstruir_columnas(self):
        """Recrea la tabla con las columnas correspondientes al modo
        actual: detalle de créditos (por venta) o agrupado por cliente."""
        if self.tabla is not None:
            self.tabla.destroy()
            self.sb_y.destroy()

        if self.var_agrupado.get():
            columnas = ("cod_cliente", "nombre_cliente", "deuda_total", "pagado", "saldo")
            encabezados = (t("col_cod_cliente"), t("col_nombre_cliente"), t("creditos_deuda_total"), t("creditos_pagado"), t("creditos_saldo"))
            anchos = (100, 260, 130, 130, 130)
        else:
            columnas = ("credito", "fecha", "cliente", "fecha_venc", "descripcion",
                       "factura", "deuda_total", "pagado", "saldo")
            encabezados = (t("creditos_credito_num"), t("col_fecha_mayus"), t("col_cliente_mayus"), t("creditos_fecha_venc"), t("col_descripcion_mayus2"),
                          "NRO. FACTURA", "DEUDA TOTAL", "PAGADO", "SALDO")
            anchos = (80, 100, 200, 100, 200, 120, 110, 110, 110)

        self.tabla = ttk.Treeview(self.contenedor, columns=columnas, show="headings",
                                  selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho,
                              anchor="w" if col in ("cliente", "descripcion", "nombre_cliente")
                              else "center")
        self.tabla.tag_configure("saldado", foreground="#9ca3af")

        self.sb_y = ttk.Scrollbar(self.contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=self.sb_y.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        self.sb_y.grid(row=0, column=1, sticky="ns")
        self_sb_y_h = ttk.Scrollbar(self.contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=self_sb_y_h.set)
        self_sb_y_h.grid(row=1, column=0, sticky="ew")

        self.tabla.bind("<<TreeviewSelect>>", self._al_seleccionar)
        self.tabla.bind("<Double-1>", lambda e: self._abrir_detalle_seleccionado())

    # ---------------- PANEL "RESUMEN DE CRÉDITOS" (pie, oculto por defecto) ----------------
    def _construir_panel_resumen(self):
        self.frame_resumen = tk.Frame(self, bg=GRIS_FONDO, relief="solid", bd=1)
        # No se empaqueta todavía: arranca oculto hasta tocar "Mostrar Resumen"

        tk.Label(self.frame_resumen, text=t("creditos_resumen_titulo"), font=("Segoe UI", 11, "bold"),
                bg=GRIS_FONDO, fg="#1e293b").pack(anchor="w", padx=15, pady=(10, 6))

        fila = tk.Frame(self.frame_resumen, bg=GRIS_FONDO)
        fila.pack(fill="x", padx=15, pady=(0, 12))

        col1 = tk.Frame(fila, bg=GRIS_FONDO)
        col1.pack(side="left", padx=(0, 60))
        tk.Label(col1, text=t("creditos_total_pendientes"), font=("Segoe UI", 9, "bold"),
                bg=GRIS_FONDO, fg=AZUL_RIBBON).pack(anchor="w")
        self.lbl_cant_pendientes = tk.Label(col1, text="0", font=("Segoe UI", 13),
                                            bg=GRIS_FONDO, fg="#1e293b")
        self.lbl_cant_pendientes.pack(anchor="w")

        col2 = tk.Frame(fila, bg=GRIS_FONDO)
        col2.pack(side="left")
        tk.Label(col2, text=t("creditos_total_pendiente_pago"), font=("Segoe UI", 9, "bold"),
                bg=GRIS_FONDO, fg=AZUL_RIBBON).pack(anchor="w")
        self.lbl_total_pendiente = tk.Label(col2, text="Gs. 0", font=("Segoe UI", 13),
                                            bg=GRIS_FONDO, fg=ROJO)
        self.lbl_total_pendiente.pack(anchor="w")

    def _actualizar_resumen(self):
        totales = totales_creditos_pendientes()
        self.lbl_cant_pendientes.config(text=str(totales["cantidad_pendientes"]))
        self.lbl_total_pendiente.config(text=formatear_gs(totales["total_pendiente"]))

    # ---------------- CARGA DE DATOS ----------------
    def _cargar(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        self._cliente_por_fila = {}

        busqueda = self.var_busqueda.get()
        vista = self.var_vista.get()

        if self.var_agrupado.get():
            for c in resumen_por_cliente(vista=vista, texto_busqueda=busqueda):
                iid = f"cli_{c['cliente_id']}"
                self.tabla.insert("", "end", iid=iid, values=(
                    c["cliente_id"] if c["cliente_id"] is not None else "—", c["cliente"],
                    formatear_gs(c["deuda_total"]), formatear_gs(c["pagado"]),
                    formatear_gs(c["saldo"]),
                ))
                self._cliente_por_fila[iid] = c["cliente_id"]
        else:
            for c in listar_creditos(vista=vista, texto_busqueda=busqueda):
                iid = str(c["id"])
                tags = ("saldado",) if c["saldo"] <= 0.009 else ()
                self.tabla.insert("", "end", iid=iid, values=(
                    c["id"], _formatear_fecha(c["fecha"]), c["cliente"],
                    _formatear_fecha(c["fecha_vencimiento"]), c["descripcion"] or "—",
                    c["nro_factura"] or "—", formatear_gs(c["deuda_total"]),
                    formatear_gs(c["pagado"]), formatear_gs(c["saldo"]),
                ), tags=tags)
                self._cliente_por_fila[iid] = c["cliente_id"]

        if self.var_resumen_visible.get():
            self._actualizar_resumen()
        self._al_seleccionar()

    def _al_seleccionar(self, event=None):
        seleccion = self.tabla.selection()
        hay_cliente = bool(seleccion) and self._cliente_por_fila.get(seleccion[0]) is not None
        self.btn_estado_cuenta.config(
            state="normal" if hay_cliente else "disabled",
            bg="white" if hay_cliente else "#f3f4f6",
            fg="#1e293b" if hay_cliente else "#9ca3af",
        )

    def _abrir_detalle_seleccionado(self):
        if self.var_agrupado.get():
            return  # en la vista agrupada, doble click no abre un crédito individual
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        credito_id = int(seleccion[0])
        VentanaDetalleCredito(self, credito_id, self.usuario_actual, on_cambio=self._cargar)

    def _abrir_estado_cuenta(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        cliente_id = self._cliente_por_fila.get(seleccion[0])
        if cliente_id is None:
            messagebox.showinfo("Sin cliente", "Este renglón no tiene un cliente registrado asociado.",
                                parent=self)
            return
        VentanaEstadoCuenta(self, cliente_id)


# ============================================================
# DETALLE DE UN CRÉDITO + REGISTRAR PAGO
# ============================================================
class VentanaDetalleCredito(tk.Toplevel):
    def __init__(self, parent, credito_id: int, usuario_actual, on_cambio=None):
        super().__init__(parent)
        self.credito_id = credito_id
        self.usuario_actual = usuario_actual
        self.on_cambio = on_cambio

        self.credito = obtener_detalle_credito(credito_id)
        if self.credito is None:
            self.destroy()
            return

        self.title(f"Crédito Nro. {credito_id}")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()
        self.transient(parent)

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_titulo()
        self._construir_info()
        self._construir_pagos()
        self._construir_pie()

        self.minsize(480, 480)
        ajustar_tamaño_ventana(self, ancho_min=480, alto_min=480)

    def _construir_titulo(self):
        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text=f"Crédito Nro. {self.credito_id}", font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

    def _construir_info(self):
        c = self.credito
        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=1, column=0, sticky="ew", padx=16, pady=(14, 6))
        contenedor.grid_columnconfigure(1, weight=1)

        def fila(r, etiqueta, valor, color="#1e293b"):
            tk.Label(contenedor, text=etiqueta, font=("Segoe UI", 9, "bold"), bg="white").grid(
                row=r, column=0, sticky="e", pady=3, padx=(0, 10))
            tk.Label(contenedor, text=valor, font=("Segoe UI", 9), bg="white", fg=color,
                    wraplength=300, justify="left", anchor="w").grid(row=r, column=1, sticky="w", pady=3)

        fila(0, "Cliente:", c["cliente"])
        fila(1, "Fecha:", _formatear_fecha(c["fecha"]))
        fila(2, "Vencimiento:", _formatear_fecha(c["fecha_vencimiento"]))
        fila(3, "Factura:", c["nro_factura"] or "—")
        fila(4, "Descripción:", c["descripcion"] or "—")

        tk.Frame(contenedor, bg=GRIS_BORDE, height=1).grid(row=5, column=0, columnspan=2,
                                                            sticky="ew", pady=8)

        fila(6, "Deuda Total:", formatear_gs(c["deuda_total"]))
        fila(7, "Pagado:", formatear_gs(c["pagado"]), color=VERDE)
        color_saldo = ROJO if c["saldo"] > 0.009 else VERDE
        fila(8, "Saldo:", formatear_gs(c["saldo"]), color=color_saldo)

    def _construir_pagos(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=2, column=0, sticky="nsew", padx=16, pady=(6, 6))
        contenedor.grid_rowconfigure(1, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        tk.Label(contenedor, text=t("creditos_historial_pagos"), font=("Segoe UI", 9, "bold"),
                bg="white").grid(row=0, column=0, sticky="w")

        cols = ("fecha", "monto")
        tabla = ttk.Treeview(contenedor, columns=cols, show="headings", height=6)
        habilitar_deseleccion_treeview(tabla)
        tabla.heading("fecha", text=t("col_fecha"))
        tabla.heading("monto", text=t("col_monto"))
        tabla.column("fecha", width=180, anchor="center")
        tabla.column("monto", width=150, anchor="center")
        tabla.grid(row=1, column=0, sticky="nsew")
        sb = ttk.Scrollbar(contenedor, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=sb.set)
        sb.grid(row=1, column=1, sticky="ns")
        sb_h = ttk.Scrollbar(contenedor, orient="horizontal", command=tabla.xview)
        tabla.configure(xscrollcommand=sb_h.set)
        sb_h.grid(row=2, column=0, sticky="ew")

        if not self.credito["pagos"]:
            tk.Label(contenedor, text=t("creditos_sin_pagos"),
                    font=("Segoe UI", 8, "italic"), bg="white", fg=GRIS_TEXTO).grid(
                        row=2, column=0, sticky="w", pady=(4, 0))
        for p in self.credito["pagos"]:
            tabla.insert("", "end", values=(_formatear_fecha(p["fecha"]), formatear_gs(p["monto"])))

    def _construir_pie(self):
        pie = tk.Frame(self, bg=GRIS_FONDO)
        pie.grid(row=3, column=0, sticky="ew")

        saldado = self.credito["saldo"] <= 0.009

        if not saldado:
            tk.Label(pie, text=t("creditos_monto_a_pagar"), font=("Segoe UI", 9, "bold"),
                    bg=GRIS_FONDO).pack(side="left", padx=(15, 6), pady=12)
            self.var_monto = tk.StringVar(value=str(int(round(self.credito["saldo"]))))
            entry = tk.Entry(pie, textvariable=self.var_monto, font=("Segoe UI", 10), width=14)
            entry.pack(side="left", pady=12)
            entry.focus()
            entry.selection_range(0, "end")
            tk.Button(pie, text=t("creditos_pagar_saldo_total"), font=("Segoe UI", 8), bg="white",
                     relief="solid", bd=1, cursor="hand2",
                     command=lambda: self.var_monto.set(str(int(round(self.credito["saldo"]))))
                     ).pack(side="left", padx=(8, 0), pady=12)
            tk.Button(pie, text=t("creditos_registrar_pago"), font=("Segoe UI", 9, "bold"), bg=VERDE,
                     fg="white", relief="flat", padx=14, pady=6, cursor="hand2",
                     command=self._registrar_pago).pack(side="right", padx=(0, 15), pady=12)
        else:
            tk.Label(pie, text=t("creditos_ya_saldado"),
                    font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO, fg=VERDE).pack(
                        side="left", padx=15, pady=12)

        tk.Button(pie, text=t("cerrar"), font=("Segoe UI", 9, "bold"), bg="white",
                 relief="solid", bd=1, command=self.destroy).pack(side="right", padx=(0, 8), pady=12)

    def _registrar_pago(self):
        try:
            monto = float(self.var_monto.get().replace(",", "."))
            if monto <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Monto inválido", "Ingresa un monto numérico mayor a cero.",
                                 parent=self)
            return

        ok, msg = registrar_pago_credito(self.credito_id, monto,
                                         usuario_id=self.usuario_actual.get("id"))
        if not ok:
            messagebox.showerror("No se pudo registrar el pago", msg, parent=self)
            return

        messagebox.showinfo("Pago registrado", msg, parent=self)
        if self.on_cambio:
            self.on_cambio()
        self.destroy()


# ============================================================
# ESTADO DE CUENTA DE UN CLIENTE
# ============================================================
class VentanaEstadoCuenta(tk.Toplevel):
    def __init__(self, parent, cliente_id: int):
        super().__init__(parent)
        self.cliente_id = cliente_id

        self.estado = estado_cuenta_cliente(cliente_id)
        if self.estado is None:
            self.destroy()
            return

        self.title(f"Estado de Cuenta — {self.estado['nombre']}")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()
        self.transient(parent)

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_titulo()
        self._construir_datos_cliente()
        self._construir_tabla_creditos()
        self._construir_pie()

        self.minsize(760, 560)
        ajustar_tamaño_ventana(self, ancho_min=760, alto_min=560)

    def _construir_titulo(self):
        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text=f"Estado de Cuenta — {self.estado['nombre']}",
                font=("Segoe UI", 11, "bold"), bg=AZUL_RIBBON, fg="white"
                ).pack(side="left", padx=15, pady=6)

    def _construir_datos_cliente(self):
        e = self.estado
        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=1, column=0, sticky="ew", padx=16, pady=(12, 6))

        tk.Label(contenedor, text=f"CI/RUC: {e['nro_documento'] or '—'}    "
                                  f"Dirección: {e['direccion'] or '—'}    "
                                  f"Teléfono: {e['telefono'] or '—'}",
                font=("Segoe UI", 9), bg="white", fg=GRIS_TEXTO
                ).pack(anchor="w")

        tk.Label(contenedor, text=f"Fecha del reporte: {datetime.date.today().strftime('%d/%m/%Y')}",
                font=("Segoe UI", 8), bg="white", fg=GRIS_TEXTO).pack(anchor="w", pady=(2, 0))

    def _construir_tabla_creditos(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=2, column=0, sticky="nsew", padx=16)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        cols = ("credito", "fecha", "vencimiento", "descripcion", "factura",
               "deuda_total", "pagado", "saldo")
        encs = (t("numero_simbolo"), t("col_fecha"), t("vencimiento_label"), t("col_descripcion"), t("factura_label"),
               t("deuda_label"), t("pagado_cap"), t("saldo_cap"))
        anchos = (50, 100, 100, 200, 120, 110, 110, 110)

        tabla = ttk.Treeview(contenedor, columns=cols, show="headings")
        habilitar_deseleccion_treeview(tabla)
        for col, enc, ancho in zip(cols, encs, anchos):
            tabla.heading(col, text=enc)
            tabla.column(col, width=ancho, anchor="w" if col == "descripcion" else "center")
        tabla.tag_configure("saldado", foreground="#9ca3af")
        tabla.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(contenedor, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")
        sb_h = ttk.Scrollbar(contenedor, orient="horizontal", command=tabla.xview)
        tabla.configure(xscrollcommand=sb_h.set)
        sb_h.grid(row=1, column=0, sticky="ew")

        for c in self.estado["creditos"]:
            tags = ("saldado",) if c["saldo"] <= 0.009 else ()
            tabla.insert("", "end", values=(
                c["id"], _formatear_fecha(c["fecha"]), _formatear_fecha(c["fecha_vencimiento"]),
                c["descripcion"] or "—", c["nro_factura"] or "—",
                formatear_gs(c["deuda_total"]), formatear_gs(c["pagado"]), formatear_gs(c["saldo"]),
            ), tags=tags)

        if not self.estado["creditos"]:
            tk.Label(contenedor, text=t("creditos_sin_creditos_cliente"),
                    font=("Segoe UI", 9, "italic"), bg="white", fg=GRIS_TEXTO).grid(
                        row=1, column=0, sticky="w", pady=8)

    def _construir_pie(self):
        e = self.estado
        pie = tk.Frame(self, bg=GRIS_FONDO)
        pie.grid(row=3, column=0, sticky="ew")

        totales = tk.Frame(pie, bg=GRIS_FONDO)
        totales.pack(side="left", padx=15, pady=10)
        tk.Label(totales, text=f"Deuda Total: {formatear_gs(e['deuda_total'])}   "
                              f"Pagado: {formatear_gs(e['pagado'])}",
                font=("Segoe UI", 9), bg=GRIS_FONDO).pack(anchor="w")
        color_saldo = ROJO if e["saldo"] > 0.009 else VERDE
        tk.Label(totales, text=f"Saldo Total: {formatear_gs(e['saldo'])}",
                font=("Segoe UI", 12, "bold"), bg=GRIS_FONDO, fg=color_saldo).pack(anchor="w")

        tk.Button(pie, text=t("presup_generar_pdf_boton"), font=("Segoe UI", 9, "bold"), bg="white",
                 relief="solid", bd=1, cursor="hand2",
                 command=self._generar_pdf).pack(side="right", padx=(0, 8), pady=10)
        tk.Button(pie, text=t("cerrar"), font=("Segoe UI", 9, "bold"), bg="white",
                 relief="solid", bd=1, command=self.destroy).pack(side="right", padx=(0, 8), pady=10)

    def _generar_pdf(self):
        from tkinter import filedialog
        try:
            from reporte_estado_cuenta_pdf import generar_estado_cuenta_pdf
        except ImportError:
            messagebox.showerror("Falta una librería",
                                 "Para generar el PDF se necesita instalar 'reportlab'.\n\n"
                                 "Abre una terminal y ejecutá:\n\npip install reportlab",
                                 parent=self)
            return
        ruta = filedialog.asksaveasfilename(
            title="Guardar Estado de Cuenta",
            initialfile=f"estado_cuenta_{self.estado['nombre'].replace(' ', '_')}.pdf",
            defaultextension=".pdf", filetypes=[("Archivo PDF", "*.pdf")],
        )
        if not ruta:
            return
        try:
            generar_estado_cuenta_pdf(ruta, self.estado)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n{e}", parent=self)
            return
        if messagebox.askyesno("PDF generado", f"El estado de cuenta se guardó en:\n{ruta}\n\n"
                                               "¿Querés abrirlo ahora?", parent=self):
            import os, sys, subprocess
            try:
                if sys.platform == "win32":
                    os.startfile(ruta)
                elif sys.platform == "darwin":
                    subprocess.run(["open", ruta])
                else:
                    subprocess.run(["xdg-open", ruta])
            except Exception:
                pass
