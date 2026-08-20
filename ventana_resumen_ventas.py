"""
ventana_resumen_ventas.py
Panel "Resumen" del módulo Ventas: muestra las ventas de un día específico
(seleccionable con calendario), con el panel financiero (Ventas Totales,
Dinero en Caja), acceso al Reporte por Rango de Fechas, y un panel de
detalle de venta (comprobante) que aparece al hacer click en una venta,
con la opción de devolver un artículo específico (repone stock y
recalcula el total).
"""
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkfont
import datetime

from models_ventas import resumen_financiero_del_dia, cancelar_venta, obtener_detalle_venta, devolver_articulo
from widget_calendario import abrir_selector_fecha, formatear_fecha_es
from utilidades_ui import ajustar_tamaño_ventana, formatear_gs, habilitar_deseleccion_treeview
from models_comprobante import generar_texto_comprobante, ancho_texto_para_formato, obtener_config_local
from auth import filtro_usuario_ventas

AZUL_RIBBON = "#1d5fd6"
GRIS_FONDO = "#f4f5f7"
NARANJA = "#d97706"
ROJO = "#dc2626"


class PanelResumenVentas(tk.Frame):
    def __init__(self, parent, usuario_actual):
        super().__init__(parent, bg="white")
        self.usuario_actual = usuario_actual
        self.fecha_seleccionada = datetime.date.today()
        self.venta_seleccionada_id = None

        self._construir_barra_fecha()
        self._construir_cuerpo()
        self._cargar_datos()

    # ---------------- BARRA SUPERIOR: SELECTOR DE FECHA ----------------
    def _construir_barra_fecha(self):
        barra = tk.Frame(self, bg="white")
        barra.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(barra, text="Mostrar Resumen de:", font=("Segoe UI", 10), bg="white").pack(side="left")

        self.label_fecha = tk.Label(barra, text=formatear_fecha_es(self.fecha_seleccionada),
                                     font=("Segoe UI", 10, "bold"), bg="white", fg=AZUL_RIBBON,
                                     cursor="hand2")
        self.label_fecha.pack(side="left", padx=(8, 4))
        self.label_fecha.bind("<Button-1>", lambda e: self._abrir_calendario())

        icono_cal = tk.Label(barra, text="📅", font=("Segoe UI", 10), bg="white", cursor="hand2")
        icono_cal.pack(side="left")
        icono_cal.bind("<Button-1>", lambda e: self._abrir_calendario())

        tk.Button(barra, text="🔄 Actualizar", font=("Segoe UI", 9, "bold"),
                  bg="white", fg=AZUL_RIBBON, relief="solid", bd=1, padx=10, pady=5,
                  cursor="hand2", activebackground="#eff6ff",
                  command=self._cargar_datos).pack(side="left", padx=15)

        tk.Button(barra, text="📊 Reporte por Rango de Fechas", font=("Segoe UI", 9, "bold"),
                  bg=AZUL_RIBBON, fg="white", command=self._abrir_reporte_rango).pack(side="right")

    def _abrir_calendario(self):
        abrir_selector_fecha(self, self.fecha_seleccionada, self._al_elegir_fecha)

    def _al_elegir_fecha(self, fecha: datetime.date):
        self.fecha_seleccionada = fecha
        self.label_fecha.config(text=formatear_fecha_es(fecha))
        self._cerrar_detalle_venta()
        self._cargar_datos()

    # ---------------- CUERPO: GRILLA + FINANCIERO (izquierda) | DETALLE (derecha) ----------------
    def _construir_cuerpo(self):
        contenedor_general = tk.Frame(self, bg="white")
        contenedor_general.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        contenedor_general.grid_columnconfigure(0, weight=1)
        contenedor_general.grid_columnconfigure(1, weight=0)
        contenedor_general.grid_rowconfigure(0, weight=1)

        self._construir_columna_izquierda(contenedor_general)
        self._construir_panel_detalle(contenedor_general)

    def _construir_columna_izquierda(self, padre):
        contenedor = tk.Frame(padre, bg="white")
        contenedor.grid(row=0, column=0, sticky="nsew")

        # El bloque financiero (Ventas Totales + Dinero en Caja) se arma
        # PRIMERO y se ubica con side="bottom": así siempre se reserva su
        # espacio en la parte de abajo, sin importar cuántas filas tenga
        # la grilla de ventas. La grilla de arriba nunca se mueve junto
        # con este bloque; solo el bloque financiero tiene su propio
        # scroll interno (por si en una ventana muy chica no entrara).
        area_financiera = tk.Frame(contenedor, bg=GRIS_FONDO, height=260)
        area_financiera.pack(side="bottom", fill="x")
        area_financiera.pack_propagate(False)

        canvas = tk.Canvas(area_financiera, bg=GRIS_FONDO, highlightthickness=0, bd=0)
        scrollbar_col = ttk.Scrollbar(area_financiera, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar_col.set)
        canvas.pack(side="left", fill="both", expand=True)

        panel_financiero = tk.Frame(canvas, bg=GRIS_FONDO)
        id_ventana = canvas.create_window((0, 0), window=panel_financiero, anchor="nw")

        def _actualizar_scroll(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(id_ventana, width=canvas.winfo_width())
            if panel_financiero.winfo_reqheight() > canvas.winfo_height():
                if not scrollbar_col.winfo_ismapped():
                    scrollbar_col.pack(side="right", fill="y")
            else:
                if scrollbar_col.winfo_ismapped():
                    scrollbar_col.pack_forget()

        panel_financiero.bind("<Configure>", _actualizar_scroll)
        canvas.bind("<Configure>", _actualizar_scroll)

        def _con_scroll_del_mouse(event):
            delta = event.delta
            if delta == 0:
                delta = -1 if getattr(event, "num", None) == 5 else 1
            else:
                delta = int(-1 * (delta / 120)) if abs(delta) >= 120 else -1 * delta
            canvas.yview_scroll(delta, "units")

        def _activar_scroll(event=None):
            canvas.bind_all("<MouseWheel>", _con_scroll_del_mouse)
            canvas.bind_all("<Button-4>", _con_scroll_del_mouse)
            canvas.bind_all("<Button-5>", _con_scroll_del_mouse)

        def _desactivar_scroll(event=None):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        area_financiera.bind("<Enter>", _activar_scroll)
        area_financiera.bind("<Leave>", _desactivar_scroll)

        # --- Grilla de ventas del día (fija, no se mueve con el scroll
        # del bloque financiero; tiene su propio scroll de filas/columnas) ---
        frame_grilla = tk.Frame(contenedor, bg="white")
        frame_grilla.pack(side="top", fill="both", expand=True)

        columnas = ("codigo", "fecha_hora", "cliente", "importe", "estado", "forma_pago", "factura")
        encabezados = ("Código", "Fecha y Hora", "Cliente", "Importe", "Estado Cuenta", "Forma de Pago", "Documento")

        self.tabla = ttk.Treeview(frame_grilla, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc in zip(columnas, encabezados):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=110, anchor="center")
        self.tabla.column("cliente", width=160, anchor="w")
        self.tabla.column("factura", width=240, anchor="w")

        frame_grilla.grid_rowconfigure(0, weight=1)
        frame_grilla.grid_columnconfigure(0, weight=1)

        scrollbar_v = ttk.Scrollbar(frame_grilla, orient="vertical", command=self.tabla.yview)
        scrollbar_h = ttk.Scrollbar(frame_grilla, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        scrollbar_v.grid(row=0, column=1, sticky="ns")
        scrollbar_h.grid(row=1, column=0, sticky="ew")

        self.tabla.tag_configure("cancelado", foreground="#9ca3af")
        self.tabla.bind("<<TreeviewSelect>>", lambda e: self._al_seleccionar_venta())

        fila_totales = tk.Frame(panel_financiero, bg=GRIS_FONDO)
        fila_totales.pack(fill="x", padx=15, pady=10)

        tk.Label(fila_totales, text="₲ Ventas Totales", font=("Segoe UI", 13, "bold"),
                 bg=GRIS_FONDO).pack(side="left")
        self.label_ventas_totales = tk.Label(fila_totales, text="Gs. 0", font=("Segoe UI", 16, "bold"),
                                              bg=GRIS_FONDO, fg=AZUL_RIBBON)
        self.label_ventas_totales.pack(side="left", padx=15)

        tk.Button(fila_totales, text="🖶 Imprimir Resumen", font=("Segoe UI", 9, "bold"),
                  bg="white", fg=AZUL_RIBBON, relief="solid", bd=1, padx=10, pady=5,
                  cursor="hand2", activebackground="#eff6ff",
                  command=self._imprimir_resumen).pack(side="right")
        tk.Button(fila_totales, text="📧 Email", font=("Segoe UI", 9, "bold"),
                  bg="white", fg=AZUL_RIBBON, relief="solid", bd=1, padx=10, pady=5,
                  cursor="hand2", activebackground="#eff6ff",
                  command=self._abrir_enviar_email).pack(side="right", padx=(0, 8))

        frame_caja = tk.Frame(panel_financiero, bg=GRIS_FONDO)
        frame_caja.pack(fill="x", padx=15, pady=(0, 15))

        tk.Label(frame_caja, text="🏦 Dinero en Caja", font=("Segoe UI", 12, "bold"),
                 bg=GRIS_FONDO).grid(row=0, column=0, columnspan=2, sticky="w", pady=(5, 8))

        self.filas_caja = {}
        etiquetas_caja = [
            # (texto, clave_resumen, color, con_detalle, tipo_movimiento_bd)
            ("Saldo Inicial Caja", "saldo_inicial",   "black",    False, None),
            ("Ventas en Efectivo", "ventas_efectivo", "#16a34a",  False, None),
            ("Entradas",           "entradas",        "#16a34a",  True,  "entrada"),
            ("Salidas",            "salidas",         "#dc2626",  True,  "salida"),
            ("Devoluciones",       "devoluciones",    "#dc2626",  False, None),
        ]
        for i, (texto, clave, color, con_detalle, tipo_mov) in enumerate(etiquetas_caja, start=1):
            frame_etiqueta = tk.Frame(frame_caja, bg=GRIS_FONDO)
            frame_etiqueta.grid(row=i, column=0, sticky="w", padx=(15, 30), pady=2)
            tk.Label(frame_etiqueta, text=texto, font=("Segoe UI", 9), bg=GRIS_FONDO).pack(side="left")
            if con_detalle:
                link_detalle = tk.Label(frame_etiqueta, text=" (Ver detalle)", font=("Segoe UI", 8, "underline"),
                                        bg=GRIS_FONDO, fg=AZUL_RIBBON, cursor="hand2")
                link_detalle.pack(side="left")
                link_detalle.bind("<Button-1>", lambda e, t=tipo_mov: self._abrir_detalle_movimiento_caja(t))

            label_valor = tk.Label(frame_caja, text="Gs. 0", font=("Segoe UI", 9, "bold"),
                                    bg=GRIS_FONDO, fg=color)
            label_valor.grid(row=i, column=1, sticky="e", pady=2)
            self.filas_caja[clave] = label_valor

        tk.Frame(frame_caja, bg="#ccc", height=1).grid(row=6, column=0, columnspan=2, sticky="ew", pady=4)

        tk.Label(frame_caja, text="Total en Caja", font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).grid(
            row=7, column=0, sticky="w", padx=(15, 30))
        self.label_total_caja = tk.Label(frame_caja, text="Gs. 0", font=("Segoe UI", 10, "bold"), bg=GRIS_FONDO)
        self.label_total_caja.grid(row=7, column=1, sticky="e")

    # ---------------- PANEL DERECHO: DETALLE DE VENTA (COMPROBANTE) ----------------
    ANCHO_DETALLE_MIN = 320
    ANCHO_DETALLE_MAX = 480

    def _construir_panel_detalle(self, padre):
        self.frame_detalle = tk.Frame(padre, bg=GRIS_FONDO, width=self.ANCHO_DETALLE_MIN)
        self.frame_detalle.grid(row=0, column=1, sticky="ns", padx=(10, 0))
        self.frame_detalle.grid_propagate(False)
        # Arranca oculto hasta que se seleccione una venta
        self.frame_detalle.grid_remove()

        # --- Canvas + Scrollbars: si el comprobante y la lista de artículos
        # ocupan más alto (o más ancho, por ejemplo con formato A4) que el
        # panel, se puede desplazar en las dos direcciones para verlo
        # completo, y seguir viendo los botones (Cancelar, Reimprimir, etc.) ---
        self.frame_detalle.grid_rowconfigure(0, weight=1)
        self.frame_detalle.grid_columnconfigure(0, weight=1)

        self._canvas_detalle = tk.Canvas(self.frame_detalle, bg=GRIS_FONDO, highlightthickness=0)
        scroll_v_detalle = tk.Scrollbar(self.frame_detalle, orient="vertical",
                                        command=self._canvas_detalle.yview)
        scroll_h_detalle = tk.Scrollbar(self.frame_detalle, orient="horizontal",
                                        command=self._canvas_detalle.xview)
        self._canvas_detalle.configure(yscrollcommand=scroll_v_detalle.set,
                                       xscrollcommand=scroll_h_detalle.set)
        self._canvas_detalle.grid(row=0, column=0, sticky="nsew")
        scroll_v_detalle.grid(row=0, column=1, sticky="ns")
        scroll_h_detalle.grid(row=1, column=0, sticky="ew")

        self.frame_detalle_contenido = tk.Frame(self._canvas_detalle, bg=GRIS_FONDO)
        self._ventana_canvas_detalle = self._canvas_detalle.create_window(
            (0, 0), window=self.frame_detalle_contenido, anchor="nw")

        def _ajustar_ancho_canvas(event):
            # El contenido nunca se achica más allá de lo que necesita (así
            # no se corta ninguna letra del comprobante); si el panel es más
            # ancho que el contenido, éste se estira para ocupar todo el
            # espacio disponible.
            ancho_contenido = self.frame_detalle_contenido.winfo_reqwidth()
            nuevo_ancho = max(event.width, ancho_contenido)
            self._canvas_detalle.itemconfig(self._ventana_canvas_detalle, width=nuevo_ancho)

        self._canvas_detalle.bind("<Configure>", _ajustar_ancho_canvas)
        self.frame_detalle_contenido.bind(
            "<Configure>",
            lambda e: self._canvas_detalle.configure(scrollregion=self._canvas_detalle.bbox("all")))

        def _scroll_detalle_rueda(event):
            if event.num == 4:
                self._canvas_detalle.yview_scroll(-1, "units")
            elif event.num == 5:
                self._canvas_detalle.yview_scroll(1, "units")
            else:
                self._canvas_detalle.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _scroll_detalle_horizontal(event):
            # Shift + rueda del mouse (Windows/macOS) o Shift + Button-4/5 (Linux)
            if event.num == 4:
                self._canvas_detalle.xview_scroll(-1, "units")
            elif event.num == 5:
                self._canvas_detalle.xview_scroll(1, "units")
            else:
                self._canvas_detalle.xview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_scroll_recursivo(widget):
            widget.bind("<MouseWheel>", _scroll_detalle_rueda)
            widget.bind("<Button-4>", _scroll_detalle_rueda)
            widget.bind("<Button-5>", _scroll_detalle_rueda)
            widget.bind("<Shift-MouseWheel>", _scroll_detalle_horizontal)
            widget.bind("<Shift-Button-4>", _scroll_detalle_horizontal)
            widget.bind("<Shift-Button-5>", _scroll_detalle_horizontal)
            for hijo in widget.winfo_children():
                _bind_scroll_recursivo(hijo)

        self._bind_scroll_detalle = _bind_scroll_recursivo
        _bind_scroll_recursivo(self._canvas_detalle)

    def _al_seleccionar_venta(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            self._cerrar_detalle_venta()
            return
        try:
            venta_id = int(seleccion[0])
        except (ValueError, TypeError):
            return
        self.venta_seleccionada_id = venta_id
        self._mostrar_detalle_venta(venta_id)

    def _cerrar_detalle_venta(self):
        self.venta_seleccionada_id = None
        self.frame_detalle.grid_remove()

    def _mostrar_detalle_venta(self, venta_id: int):
        detalle = obtener_detalle_venta(venta_id)
        if detalle is None:
            self._cerrar_detalle_venta()
            return

        for widget in self.frame_detalle_contenido.winfo_children():
            widget.destroy()

        self.frame_detalle.grid()
        self.detalle_actual = detalle  # guardado para poder reimprimir

        # --- Comprobante completo como un solo bloque, igual de prolijo y
        # alineado que en el módulo Comprobante de Venta. Usa el mismo
        # tamaño de papel (A4 / Ticketera 80mm / 58mm) configurado en
        # Config. Local, para que este panel se vea siempre igual a esa
        # configuración. ---
        # --- Comprobante completo como un solo bloque, igual de prolijo y
        # alineado que en el módulo Config. Local. Si la venta se cobró
        # como "Factura Legal" se arma con el formato de Factura Legal (con
        # RUC, Timbrado e IVA discriminado); si se cobró como "Comprobante
        # de Venta" se arma con el formato simple. Cada uno usa el tamaño
        # de papel configurado en su propia pestaña de Config. Local. ---
        es_factura = detalle.get("tipo_documento") == "factura"
        if es_factura:
            from ventana_configuracion_local import generar_texto_factura_desde_detalle
            formato_actual = obtener_config_local().get("formato_factura", "a4") or "a4"
            ancho_ticket = ancho_texto_para_formato(formato_actual)
            texto_ticket = generar_texto_factura_desde_detalle(detalle, ancho=ancho_ticket)
        else:
            formato_actual = obtener_config_local().get("formato_comprobante", "a4") or "a4"
            ancho_ticket = ancho_texto_para_formato(formato_actual)
            texto_ticket = generar_texto_comprobante(detalle, ancho=ancho_ticket)
        self.texto_ticket_actual = texto_ticket

        # --- Panel autoajustable: el ancho se calcula según lo que
        # realmente ocupa el comprobante (letra Courier New 8) para que no
        # se corte ninguna letra, con un tope máximo razonable; si aun así
        # no entra completo (papel A4 en una ventana chica), queda la barra
        # de desplazamiento horizontal para poder verlo igual. ---
        fuente_medicion = tkfont.Font(family="Courier New", size=8)
        ancho_texto_px = fuente_medicion.measure("0" * ancho_ticket)
        ancho_ideal = ancho_texto_px + 60  # padding del Text + borde + margen + scrollbar
        nuevo_ancho_panel = max(self.ANCHO_DETALLE_MIN, min(ancho_ideal, self.ANCHO_DETALLE_MAX))
        self.frame_detalle.configure(width=nuevo_ancho_panel)

        # Si el comprobante tiene muchas líneas (venta con muchos artículos),
        # se limita la altura visible y aparece una barra de desplazamiento
        # en vez de estirar todo el panel indefinidamente.
        ALTO_MAX_TICKET = 34
        alto_contenido = texto_ticket.count("\n") + 1
        alto_visible = min(alto_contenido, ALTO_MAX_TICKET)
        necesita_scroll = alto_contenido > ALTO_MAX_TICKET

        fuente_ticket = ("Courier New", 8)
        frame_ticket = tk.Frame(self.frame_detalle_contenido, bg=GRIS_FONDO)
        # Alineado hacia el costado derecho del panel, en vez de estirado
        # de punta a punta, para que se vea como una boleta real.
        frame_ticket.pack(anchor="e", padx=15, pady=(12, 4))

        txt_ticket = tk.Text(frame_ticket, font=fuente_ticket,
                              width=ancho_ticket, height=alto_visible,
                              bg="#fffef7", fg="#1e293b", relief="solid", bd=1,
                              wrap="none", cursor="arrow", padx=6, pady=6)
        txt_ticket.grid(row=0, column=0, sticky="nsew")

        if necesita_scroll:
            scroll_ticket = tk.Scrollbar(frame_ticket, orient="vertical", command=txt_ticket.yview)
            scroll_ticket.grid(row=0, column=1, sticky="ns")
            txt_ticket.configure(yscrollcommand=scroll_ticket.set)

            def _scroll_ticket_rueda(event):
                if event.num == 4:
                    txt_ticket.yview_scroll(-1, "units")
                elif event.num == 5:
                    txt_ticket.yview_scroll(1, "units")
                else:
                    txt_ticket.yview_scroll(int(-1 * (event.delta / 120)), "units")

            txt_ticket.bind("<MouseWheel>", _scroll_ticket_rueda)
            txt_ticket.bind("<Button-4>", _scroll_ticket_rueda)
            txt_ticket.bind("<Button-5>", _scroll_ticket_rueda)

        txt_ticket.insert("1.0", texto_ticket)
        txt_ticket.config(state="disabled")

        # --- Sección aparte para devolver un artículo: va DEBAJO del
        # comprobante completo, para no partirlo en dos ---
        cantidad_activos = sum(1 for l in detalle["lineas"] if l["cantidad_activa"] > 0)
        if cantidad_activos:
            tk.Label(self.frame_detalle_contenido, text="Seleccioná un artículo para devolver:",
                     font=("Segoe UI", 8, "bold"), bg=GRIS_FONDO, fg="#555"
                     ).pack(anchor="w", padx=15, pady=(4, 2))

        estilo_lineas = ttk.Style()
        estilo_lineas.configure("Ticket.Treeview", font=("Segoe UI", 8), rowheight=18)
        estilo_lineas.configure("Ticket.Treeview.Heading", font=("Segoe UI", 8, "bold"))

        contenedor_lineas = tk.Frame(self.frame_detalle_contenido, bg=GRIS_FONDO)
        contenedor_lineas.pack(fill="x", padx=15, pady=(0, 4))
        contenedor_lineas.grid_rowconfigure(0, weight=1)
        contenedor_lineas.grid_columnconfigure(0, weight=1)

        columnas_lineas = ("cantidad", "descripcion", "importe")
        self.tabla_lineas = ttk.Treeview(contenedor_lineas, columns=columnas_lineas, show="headings",
                                          selectmode="browse", height=min(max(cantidad_activos, 1), 6),
                                          style="Ticket.Treeview")
        habilitar_deseleccion_treeview(self.tabla_lineas)
        self.tabla_lineas.heading("cantidad", text="Cant.")
        self.tabla_lineas.heading("descripcion", text="Descripción")
        self.tabla_lineas.heading("importe", text="Importe")
        self.tabla_lineas.column("cantidad", width=45, anchor="center")
        self.tabla_lineas.column("descripcion", width=140, anchor="w")
        self.tabla_lineas.column("importe", width=80, anchor="e")
        sb_lineas = ttk.Scrollbar(contenedor_lineas, orient="vertical", command=self.tabla_lineas.yview)
        sb_lineas_h = ttk.Scrollbar(contenedor_lineas, orient="horizontal", command=self.tabla_lineas.xview)
        self.tabla_lineas.configure(yscrollcommand=sb_lineas.set, xscrollcommand=sb_lineas_h.set)
        self.tabla_lineas.grid(row=0, column=0, sticky="nsew")
        sb_lineas.grid(row=0, column=1, sticky="ns")
        sb_lineas_h.grid(row=1, column=0, sticky="ew")
        self.tabla_lineas.tag_configure("sin_stock_activo", foreground="#9ca3af")

        self.lineas_por_id = {}
        for linea in detalle["lineas"]:
            if linea["cantidad_activa"] <= 0:
                continue  # ya devuelta por completo, no se muestra como activa
            self.tabla_lineas.insert("", "end", iid=str(linea["detalle_id"]), values=(
                f"{linea['cantidad_activa']:g}", linea["nombre_producto"], formatear_gs(linea['importe']),
            ))
            self.lineas_por_id[str(linea["detalle_id"])] = linea

        if not self.lineas_por_id:
            tk.Label(self.frame_detalle_contenido, text="(Todos los artículos fueron devueltos)",
                     font=("Segoe UI", 8), bg=GRIS_FONDO, fg="#777", wraplength=280,
                     justify="center").pack(fill="x", padx=15)

        # --- Botón Devolver artículo ---
        puede_devolver = detalle["estado"] != "Cancelado" and self.lineas_por_id
        btn_devolver = tk.Button(
            self.frame_detalle_contenido, text="↩ Devolver artículo seleccionado", font=("Segoe UI", 9, "bold"),
            bg="white", fg=NARANJA, relief="solid", bd=1, pady=6, cursor="hand2",
            activebackground="#fff7ed", disabledforeground="#b0b0b0",
            state="normal" if puede_devolver else "disabled",
            command=lambda: self._devolver_articulo_seleccionado(venta_id),
        )
        btn_devolver.pack(fill="x", padx=15, pady=(2, 10))

        # --- Botones inferiores ---
        frame_botones = tk.Frame(self.frame_detalle_contenido, bg=GRIS_FONDO)
        frame_botones.pack(fill="x", padx=15, pady=(0, 12))

        estado_cancelar = "normal" if detalle["estado"] != "Cancelado" else "disabled"
        tk.Button(frame_botones, text="✕ Cancelar Venta", font=("Segoe UI", 9, "bold"),
                  bg="white", fg=ROJO, relief="solid", bd=1, pady=6, cursor="hand2",
                  activebackground="#fef2f2", disabledforeground="#b0b0b0",
                  state=estado_cancelar, command=lambda: self._cancelar_venta_completa(venta_id)
                  ).pack(fill="x", pady=2)
        texto_btn_reimprimir = "🖶 Reimprimir Factura" if es_factura else "🖶 Reimprimir Comprobante"
        tk.Button(frame_botones, text=texto_btn_reimprimir, font=("Segoe UI", 9, "bold"),
                  bg="white", fg=AZUL_RIBBON, relief="solid", bd=1, pady=6, cursor="hand2",
                  activebackground="#eff6ff",
                  command=self._reimprimir_comprobante).pack(fill="x", pady=2)
        tk.Button(frame_botones, text="📄 Generar Factura PDF", font=("Segoe UI", 9, "bold"),
                  bg=AZUL_RIBBON, fg="white", relief="flat", pady=6, cursor="hand2",
                  activebackground="#163d8c", activeforeground="white",
                  command=self._generar_factura_pdf).pack(fill="x", pady=2)
        tk.Button(frame_botones, text="🖶 Imprimir Factura", font=("Segoe UI", 9, "bold"),
                  bg="white", fg=AZUL_RIBBON, relief="solid", bd=1, pady=6, cursor="hand2",
                  activebackground="#eff6ff",
                  command=self._imprimir_factura).pack(fill="x", pady=2)

        # Re-enganchar la rueda del mouse/touchpad a todo el contenido nuevo,
        # y volver al principio del panel cada vez que se elige una venta.
        self.frame_detalle_contenido.update_idletasks()
        self._canvas_detalle.configure(scrollregion=self._canvas_detalle.bbox("all"))
        self._bind_scroll_detalle(self.frame_detalle_contenido)
        self._canvas_detalle.yview_moveto(0)

    def _devolver_articulo_seleccionado(self, venta_id: int):
        seleccion = self.tabla_lineas.selection()
        if not seleccion:
            messagebox.showwarning("Selecciona un artículo", "Elige el artículo de la lista que quieres devolver.")
            return
        linea = self.lineas_por_id[seleccion[0]]

        ventana = tk.Toplevel(self)
        ventana.title("Devolver Artículo")
        ventana.grab_set()
        ventana.configure(bg="white")

        tk.Label(ventana, text=linea["nombre_producto"], font=("Segoe UI", 11, "bold"),
                 bg="white", wraplength=280).pack(pady=(15, 5))
        tk.Label(ventana, text=f"Cantidad activa en la venta: {linea['cantidad_activa']:g}",
                 font=("Segoe UI", 9), bg="white", fg="#555").pack()

        frame_cant = tk.Frame(ventana, bg="white")
        frame_cant.pack(pady=15)
        tk.Label(frame_cant, text="Cantidad a devolver:", font=("Segoe UI", 9, "bold"), bg="white").pack(side="left")
        var_cantidad = tk.StringVar(value=f"{linea['cantidad_activa']:g}")
        entry_cantidad = tk.Entry(frame_cant, textvariable=var_cantidad, font=("Segoe UI", 10), width=8, justify="center")
        entry_cantidad.pack(side="left", padx=8)

        def confirmar():
            try:
                cantidad = float(var_cantidad.get().replace(",", "."))
                if cantidad <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Cantidad inválida", "Ingresa un número mayor a cero.")
                return

            if not messagebox.askyesno(
                "Confirmar devolución",
                f"¿Confirmas devolver {cantidad:g} unidad(es) de '{linea['nombre_producto']}'?\n\n"
                "El stock se repondrá automáticamente y el total de la venta se recalculará."
            ):
                return

            ok, msg = devolver_articulo(linea["detalle_id"], cantidad, self.usuario_actual["id"])
            if ok:
                messagebox.showinfo("Listo", msg)
                ventana.destroy()
                self._cargar_datos()
                self._mostrar_detalle_venta(venta_id)
            else:
                messagebox.showerror("No se pudo devolver", msg)

        tk.Button(ventana, text="Confirmar Devolución", font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                  fg="white", command=confirmar).pack(pady=10)

        ajustar_tamaño_ventana(ventana, ancho_min=320, alto_min=220)

    def _cancelar_venta_completa(self, venta_id: int):
        if not messagebox.askyesno(
            "Cancelar venta",
            "¿Seguro que quieres cancelar esta venta completa?\n\n"
            "Todo el stock vendido se repondrá."
        ):
            return
        ok, msg = cancelar_venta(venta_id)
        if ok:
            messagebox.showinfo("Listo", msg)
            self._cargar_datos()
            self._mostrar_detalle_venta(venta_id)
        else:
            messagebox.showerror("No se pudo cancelar", msg)

    def _reimprimir_comprobante(self):
        if not getattr(self, "detalle_actual", None):
            messagebox.showinfo("Seleccionar venta", "Hacé click en una venta para seleccionarla.")
            return
        from models_comprobante import obtener_config_local
        es_factura = self.detalle_actual.get("tipo_documento") == "factura"
        cfg = obtener_config_local()
        if es_factura:
            formato_inicial = cfg.get("formato_factura", "a4") or "a4"
            config_key = "formato_factura"
            titulo = "Reimprimir Factura"
            nombre_archivo = f"factura_{self.detalle_actual['id']}"
        else:
            formato_inicial = cfg.get("formato_comprobante", "a4") or "a4"
            config_key = "formato_comprobante"
            titulo = "Reimprimir Comprobante"
            nombre_archivo = f"comprobante_{self.detalle_actual['id']}"
        self._abrir_vista_previa_impresion(
            titulo=titulo,
            detalle=self.detalle_actual,
            nombre_archivo=nombre_archivo,
            formato_inicial=formato_inicial,
            config_key=config_key,
            es_factura=es_factura,
        )

    def _abrir_vista_previa_impresion(self, titulo: str, detalle: dict, nombre_archivo: str,
                                       formato_inicial: str = "a4", config_key: str = "formato_comprobante",
                                       es_factura: bool = False):
        """Ventana de vista previa de impresión: muestra el ticket en
        formato monoespaciado (igual al de la pestaña Comprobante de Venta o
        Factura Legal de Configuración Local, según corresponda), permite
        elegir el tamaño de papel (Hoja A4 / Ticketera 80mm / Ticketera
        58mm) y la impresora de destino, y enviarlo a imprimir o guardarlo
        como PDF. Para ticketeras imprime el texto directo (RAW/ESC-POS,
        sin generar PDF); para Hoja A4 genera e imprime el PDF."""
        import driver_impresora
        from models_comprobante import (
            FORMATOS_IMPRESION, ancho_texto_para_formato, generar_texto_comprobante,
            generar_pdf_comprobante, guardar_config_local, obtener_config_local,
        )
        if es_factura:
            from ventana_configuracion_local import (
                generar_texto_factura_desde_detalle, generar_factura_pdf_desde_detalle,
            )

        clave_impresora = "impresora_factura" if es_factura else "impresora_comprobante"

        def _generar_texto(ancho):
            if es_factura:
                return generar_texto_factura_desde_detalle(detalle, ancho=ancho)
            return generar_texto_comprobante(detalle, ancho=ancho)

        def _generar_pdf(ruta, formato):
            if es_factura:
                return generar_factura_pdf_desde_detalle(ruta, detalle, formato=formato)
            return generar_pdf_comprobante(ruta, detalle, formato=formato)

        ventana = tk.Toplevel(self)
        ventana.title(titulo)
        ventana.configure(bg="#e5e7eb")
        ventana.grab_set()

        var_formato = tk.StringVar(value=formato_inicial)

        frame_formato = tk.Frame(ventana, bg="#e5e7eb")
        frame_formato.pack(fill="x", padx=16, pady=(14, 0))
        tk.Label(frame_formato, text="Tamaño de impresión:", font=("Segoe UI", 9, "bold"),
                 bg="#e5e7eb").pack(side="left")
        combo = ttk.Combobox(frame_formato, state="readonly", width=18,
                             values=[spec["etiqueta"] for spec in FORMATOS_IMPRESION.values()])
        claves_formato = list(FORMATOS_IMPRESION.keys())
        combo.current(claves_formato.index(formato_inicial) if formato_inicial in claves_formato else 0)
        combo.pack(side="left", padx=8)

        # --- Selector de impresora (cualquier impresora instalada en
        # Windows: normal o ticketera, de cualquier marca) ---
        frame_impresora = tk.Frame(ventana, bg="#e5e7eb")
        frame_impresora.pack(fill="x", padx=16, pady=(8, 0))
        tk.Label(frame_impresora, text="Impresora:", font=("Segoe UI", 9, "bold"),
                 bg="#e5e7eb").pack(side="left")

        PREDETERMINADA = "(Predeterminada del sistema)"
        impresoras_detectadas = driver_impresora.listar_impresoras()
        valores_combo_impresora = [PREDETERMINADA] + impresoras_detectadas
        combo_impresora = ttk.Combobox(frame_impresora, state="readonly", width=32,
                                       values=valores_combo_impresora)
        impresora_guardada = obtener_config_local().get(clave_impresora, "")
        if impresora_guardada and impresora_guardada in impresoras_detectadas:
            combo_impresora.current(valores_combo_impresora.index(impresora_guardada))
        else:
            combo_impresora.current(0)
        combo_impresora.pack(side="left", padx=8)
        if not impresoras_detectadas:
            tk.Label(frame_impresora, text="(no se detectaron impresoras instaladas)",
                     font=("Segoe UI", 8, "italic"), bg="#e5e7eb", fg="#888").pack(side="left")

        def _impresora_elegida() -> str:
            valor = combo_impresora.get()
            return "" if valor == PREDETERMINADA else valor

        def _guardar_impresora_elegida(*_):
            guardar_config_local({clave_impresora: _impresora_elegida()})

        combo_impresora.bind("<<ComboboxSelected>>", _guardar_impresora_elegida)

        cont = tk.Frame(ventana, bg="white", relief="solid", bd=1)
        cont.pack(padx=16, pady=16)

        txt = tk.Text(cont, font=("Courier New", 10), width=44, height=20,
                       bg="#fffef7", fg="#1e293b", relief="flat", bd=0, padx=12, pady=12,
                       wrap="none")
        txt.pack()

        def _texto_actual() -> str:
            return _generar_texto(ancho_texto_para_formato(var_formato.get()))

        def _refrescar_vista(*_):
            var_formato.set(claves_formato[combo.current()])
            guardar_config_local({config_key: var_formato.get()})
            texto = _texto_actual()
            txt.config(state="normal")
            txt.delete("1.0", "end")
            txt.insert("1.0", texto)
            txt.config(height=texto.count("\n") + 1)
            txt.config(state="disabled")

        combo.bind("<<ComboboxSelected>>", _refrescar_vista)
        _refrescar_vista()

        pie = tk.Frame(ventana, bg="#e5e7eb")
        pie.pack(fill="x", padx=16, pady=(0, 14))

        def _imprimir():
            import tempfile, os
            formato = var_formato.get()
            impresora = _impresora_elegida()
            try:
                if formato == "a4":
                    ruta = os.path.join(tempfile.gettempdir(), f"{nombre_archivo}.pdf")
                    resultado = driver_impresora.imprimir_documento(
                        formato, impresora, ruta_pdf_callback=lambda: (_generar_pdf(ruta, formato), ruta)[1],
                        nombre_trabajo=nombre_archivo,
                    )
                else:
                    texto = _texto_actual()
                    resultado = driver_impresora.imprimir_documento(
                        formato, impresora, texto=texto, nombre_trabajo=nombre_archivo,
                    )
                messagebox.showinfo("Enviado a impresora", resultado)
            except driver_impresora.ErrorImpresora as e:
                messagebox.showerror("No se pudo imprimir", str(e))
            except Exception as e:
                messagebox.showerror("No se pudo imprimir", f"Ocurrió un error inesperado:\n{e}")

        def _guardar_como():
            from tkinter import filedialog
            ruta_destino = filedialog.asksaveasfilename(
                defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
                initialfile=f"{nombre_archivo}.pdf")
            if not ruta_destino:
                return
            try:
                _generar_pdf(ruta_destino, var_formato.get())
                messagebox.showinfo("Guardado", f"Documento guardado en:\n{ruta_destino}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el documento:\n{e}")

        tk.Button(pie, text="🖶 Imprimir", font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                  fg="white", relief="flat", padx=14, pady=6, cursor="hand2",
                  command=_imprimir).pack(side="left")
        tk.Button(pie, text="💾 Guardar como PDF...", font=("Segoe UI", 9), padx=10, pady=6,
                  cursor="hand2", command=_guardar_como).pack(side="left", padx=8)
        tk.Button(pie, text="Cerrar", font=("Segoe UI", 9), padx=14, pady=6,
                  cursor="hand2", command=ventana.destroy).pack(side="right")

        ajustar_tamaño_ventana(ventana, ancho_min=460, alto_min=380)

    def _generar_factura_pdf(self):
        """Genera la factura legal paraguaya en PDF para la venta seleccionada."""
        if self.venta_seleccionada_id is None:
            messagebox.showinfo("Seleccionar venta",
                                "Hacé click en una venta para seleccionarla.")
            return

        try:
            import os, tempfile
            from models_ventas import obtener_detalle_venta
            from ventana_configuracion_local import (
                generar_factura_pdf_desde_detalle, obtener_config_local,
            )

            # Usa el mismo detalle (y el mismo número de factura, ya fijado
            # al procesar la venta) que usa "Imprimir Factura" — antes esta
            # función llamaba a generar_factura_desde_venta(), que volvía a
            # sacar un número NUEVO de la numeración configurada cada vez
            # que se tocaba este botón, en vez de reutilizar el que ya
            # tenía esa venta. Esto hacía que, aunque la numeración
            # configurada en Config. Local sí se guardara, cada click acá
            # "quemaba" un número distinto y la factura de una misma venta
            # cambiaba de número cada vez que se regeneraba el PDF.
            detalle_venta = obtener_detalle_venta(self.venta_seleccionada_id)
            cfg = obtener_config_local()
            formato = cfg.get("formato_factura", "a4") or "a4"

            ruta = os.path.join(tempfile.gettempdir(),
                                f"factura_{self.venta_seleccionada_id}.pdf")
            generar_factura_pdf_desde_detalle(ruta, detalle_venta, formato=formato)

            import subprocess, sys
            if sys.platform == "win32":
                os.startfile(ruta)
            elif sys.platform == "darwin":
                subprocess.run(["open", ruta])
            else:
                subprocess.run(["xdg-open", ruta])

            messagebox.showinfo("Factura generada",
                                f"Factura PDF generada y abierta.\nArchivo: {ruta}")
        except Exception as e:
            messagebox.showerror("Error al generar factura",
                                 f"Ocurrió un error:\n{e}\n\n"
                                 "Verificá que reportlab esté instalado:\n"
                                 "pip install reportlab")

    def _imprimir_factura(self):
        """Genera la factura legal y la envía a imprimir usando el driver de
        impresoras: si el tamaño configurado es Ticketera, manda el texto
        directo a la impresora (sin generar PDF); si es Hoja A4, genera e
        imprime el PDF. Usa la impresora elegida en Config. Local →
        Factura Legal (o la predeterminada del sistema si no se eligió
        ninguna en particular)."""
        if self.venta_seleccionada_id is None:
            messagebox.showinfo("Seleccionar venta", "Hacé click en una venta para seleccionarla.")
            return

        try:
            import driver_impresora
            import tempfile, os
            from models_ventas import obtener_detalle_venta
            from models_comprobante import obtener_config_local
            from ventana_configuracion_local import (
                generar_texto_factura_desde_detalle, generar_factura_pdf_desde_detalle,
            )

            detalle_venta = obtener_detalle_venta(self.venta_seleccionada_id)
            cfg = obtener_config_local()
            formato = cfg.get("formato_factura", "a4") or "a4"
            impresora = cfg.get("impresora_factura", "") or None
            nombre_trabajo = f"Factura venta {self.venta_seleccionada_id}"

            if formato == "a4":
                ruta = os.path.join(tempfile.gettempdir(), f"factura_{self.venta_seleccionada_id}.pdf")
                resultado = driver_impresora.imprimir_documento(
                    formato, impresora,
                    ruta_pdf_callback=lambda: (
                        generar_factura_pdf_desde_detalle(ruta, detalle_venta, formato=formato), ruta)[1],
                    nombre_trabajo=nombre_trabajo,
                )
            else:
                texto = generar_texto_factura_desde_detalle(detalle_venta)
                resultado = driver_impresora.imprimir_documento(
                    formato, impresora, texto=texto, nombre_trabajo=nombre_trabajo,
                )
            messagebox.showinfo("Enviado a impresora", resultado)
        except driver_impresora.ErrorImpresora as e:
            messagebox.showerror("No se pudo imprimir", str(e))
        except Exception as e:
            messagebox.showerror("Error al imprimir factura",
                                 f"Ocurrió un error:\n{e}\n\n"
                                 "Verificá que reportlab esté instalado:\n"
                                 "pip install reportlab")

    # ---------------- CARGA DE DATOS ----------------
    def _cargar_datos(self):
        fecha_str = self.fecha_seleccionada.isoformat()
        resumen = resumen_financiero_del_dia(fecha_str, usuario_id=filtro_usuario_ventas(self.usuario_actual))

        seleccion_previa = self.venta_seleccionada_id

        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        self.ventas_por_id = {}
        for v in resumen["ventas"]:
            etiqueta_tags = ("cancelado",) if v["estado"] == "Cancelado" else ()
            self.tabla.insert("", "end", iid=str(v["id"]), values=(
                v["id"], v["fecha"], v["cliente"], formatear_gs(v['importe']),
                v["estado"], v["forma_pago"], v["factura_mostrar"],
            ), tags=etiqueta_tags)
            self.ventas_por_id[str(v["id"])] = v

        self.label_ventas_totales.config(text=formatear_gs(resumen['ventas_totales']))
        self.filas_caja["saldo_inicial"].config(text=formatear_gs(resumen['saldo_inicial']))
        self.filas_caja["ventas_efectivo"].config(text="+ " + formatear_gs(resumen['ventas_efectivo']))
        self.filas_caja["entradas"].config(text=formatear_gs(resumen['entradas']))
        self.filas_caja["salidas"].config(text="- " + formatear_gs(resumen['salidas']))
        self.filas_caja["devoluciones"].config(text="- " + formatear_gs(resumen['devoluciones']))
        self.label_total_caja.config(text=formatear_gs(resumen['dinero_en_caja']))

        # Restaurar la selección visual si la venta seleccionada sigue en la lista
        if seleccion_previa is not None and str(seleccion_previa) in self.ventas_por_id:
            self.tabla.selection_set(str(seleccion_previa))

    # ---------------- ACCIONES ----------------
    def _abrir_detalle_movimiento_caja(self, tipo: str):
        """Muestra el detalle de las Entradas o Salidas de efectivo del día,
        con tabla estilizada igual a la imagen de referencia."""
        from models_ventas import listar_movimientos_caja

        fecha_str  = self.fecha_seleccionada.isoformat()
        fecha_fmt  = self.fecha_seleccionada.strftime("%d/%m/%Y")
        movimientos = [m for m in listar_movimientos_caja(fecha_str, fecha_str)
                       if m["tipo"] == tipo]

        es_entrada = tipo == "entrada"
        titulo     = "Detalle de Entradas" if es_entrada else "Detalle de Salidas"
        color_hdr  = "#16a34a" if es_entrada else "#dc2626"
        icono      = "📥" if es_entrada else "📤"

        ventana = tk.Toplevel(self)
        ventana.title(titulo)
        ventana.geometry("560x380")
        ventana.minsize(480, 300)
        ventana.resizable(True, True)
        ventana.configure(bg="white")
        ventana.grab_set()

        ventana.grid_rowconfigure(1, weight=1)
        ventana.grid_columnconfigure(0, weight=1)

        # ── Barra de título coloreada ─────────────────────────
        barra = tk.Frame(ventana, bg=color_hdr, height=36)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra,
                 text=f"{icono}  {titulo} — {fecha_fmt}",
                 font=("Segoe UI", 10, "bold"),
                 bg=color_hdr, fg="white"
                 ).pack(side="left", padx=15, pady=7)

        # ── Tabla ─────────────────────────────────────────────
        cont = tk.Frame(ventana, bg="white")
        cont.grid(row=1, column=0, sticky="nsew", padx=8, pady=(6, 0))
        cont.grid_rowconfigure(0, weight=1)
        cont.grid_columnconfigure(0, weight=1)

        cols   = ("hora", "monto", "motivo", "usuario")
        encabs = ("Hora", "Monto", "Motivo", "Registrado por")
        anchos = (70, 110, 230, 130)

        tabla = ttk.Treeview(cont, columns=cols, show="headings",
                             selectmode="browse")
        habilitar_deseleccion_treeview(tabla)
        for col, enc, ancho in zip(cols, encabs, anchos):
            tabla.heading(col, text=enc)
            tabla.column(col, width=ancho,
                         anchor="center" if col in ("hora", "monto") else "w",
                         minwidth=50)

        # color de fila según tipo
        tag_color = "#f0fdf4" if es_entrada else "#fef2f2"
        fg_color  = "#166534" if es_entrada else "#991b1b"
        tabla.tag_configure("mov", background=tag_color, foreground=fg_color)

        sb_y = ttk.Scrollbar(cont, orient="vertical",   command=tabla.yview)
        sb_x = ttk.Scrollbar(cont, orient="horizontal", command=tabla.xview)
        tabla.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        tabla.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x.grid(row=1, column=0, sticky="ew")

        total = 0.0
        for m in movimientos:
            hora  = m["fecha"].split(" ")[1][:5] if " " in m["fecha"] else "—"
            monto = m["monto"]
            total += monto
            tabla.insert("", "end", tags=("mov",), values=(
                hora,
                formatear_gs(monto),
                m["descripcion"],
                m["usuario"],
            ))

        if not movimientos:
            tk.Label(ventana,
                     text=f"No hay {titulo.lower()} registradas este día.",
                     font=("Segoe UI", 9), bg="white", fg="#9ca3af"
                     ).grid(row=1, column=0, pady=40)

        # ── Pie: total + cerrar ───────────────────────────────
        pie = tk.Frame(ventana, bg="#f8f9fa", height=40)
        pie.grid(row=2, column=0, sticky="ew")
        pie.grid_propagate(False)

        signo = "+" if es_entrada else "−"
        tk.Label(pie,
                 text=f"Total: {signo} Gs. {total:,.0f}",
                 font=("Segoe UI", 10, "bold"),
                 bg="#f8f9fa", fg=fg_color
                 ).pack(side="left", padx=14, pady=9)

        tk.Button(pie, text="Cerrar",
                  font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, padx=12, pady=3,
                  cursor="hand2", command=ventana.destroy
                  ).pack(side="right", padx=12, pady=7)

    def _imprimir_resumen(self):
        import tempfile, os
        import driver_impresora
        from reportes_datos import preparar_datos_reporte_ventas
        from reportes_formatos import generar_pdf_simple
        from models_comprobante import obtener_config_local, guardar_config_local

        fecha_iso = self.fecha_seleccionada.isoformat()
        nombre_usuario = self.usuario_actual.get("nombre_completo", "") if self.usuario_actual else ""
        nombre_archivo = f"Resumen_Ventas_{fecha_iso}"

        def _generar_pdf(ruta):
            datos = preparar_datos_reporte_ventas(
                fecha_iso, fecha_iso, generado_por=nombre_usuario,
                usuario_id=filtro_usuario_ventas(self.usuario_actual))
            generar_pdf_simple(ruta, datos)

        ventana = tk.Toplevel(self)
        ventana.title("Imprimir Resumen")
        ventana.configure(bg="#e5e7eb")
        ventana.grab_set()

        tk.Label(ventana, text=f"Resumen de Ventas — {formatear_fecha_es(self.fecha_seleccionada)}",
                 font=("Segoe UI", 10, "bold"), bg="#e5e7eb").pack(padx=16, pady=(14, 4), anchor="w")
        tk.Label(ventana, text="Se imprimirá en Hoja A4 (mismo formato que el PDF enviado por email).",
                 font=("Segoe UI", 9), bg="#e5e7eb", fg="#555").pack(padx=16, anchor="w")

        # --- Selector de impresora (cualquier impresora instalada) ---
        frame_impresora = tk.Frame(ventana, bg="#e5e7eb")
        frame_impresora.pack(fill="x", padx=16, pady=(12, 0))
        tk.Label(frame_impresora, text="Impresora:", font=("Segoe UI", 9, "bold"),
                 bg="#e5e7eb").pack(side="left")

        PREDETERMINADA = "(Predeterminada del sistema)"
        impresoras_detectadas = driver_impresora.listar_impresoras()
        valores_combo = [PREDETERMINADA] + impresoras_detectadas
        combo_impresora = ttk.Combobox(frame_impresora, state="readonly", width=32, values=valores_combo)
        impresora_guardada = obtener_config_local().get("impresora_resumen", "")
        if impresora_guardada and impresora_guardada in impresoras_detectadas:
            combo_impresora.current(valores_combo.index(impresora_guardada))
        else:
            combo_impresora.current(0)
        combo_impresora.pack(side="left", padx=8)
        if not impresoras_detectadas:
            tk.Label(frame_impresora, text="(no se detectaron impresoras instaladas)",
                     font=("Segoe UI", 8, "italic"), bg="#e5e7eb", fg="#888").pack(side="left")

        def _impresora_elegida() -> str:
            valor = combo_impresora.get()
            return "" if valor == PREDETERMINADA else valor

        combo_impresora.bind("<<ComboboxSelected>>",
                             lambda e: guardar_config_local({"impresora_resumen": _impresora_elegida()}))

        pie = tk.Frame(ventana, bg="#e5e7eb")
        pie.pack(fill="x", padx=16, pady=16)

        def _imprimir():
            impresora = _impresora_elegida()
            try:
                ruta = os.path.join(tempfile.gettempdir(), f"{nombre_archivo}.pdf")
                _generar_pdf(ruta)
                driver_impresora.imprimir_pdf(ruta, nombre_impresora=impresora)
                destino = impresora or driver_impresora.impresora_predeterminada() or "la impresora predeterminada"
                messagebox.showinfo("Enviado a impresora", f"Resumen enviado a '{destino}' (hoja A4).")
            except driver_impresora.ErrorImpresora as e:
                messagebox.showerror("No se pudo imprimir", str(e))
            except ImportError:
                messagebox.showerror(
                    "Falta una librería",
                    "Para generar el PDF del resumen se necesita instalar 'reportlab'.\n\n"
                    "Abre una terminal (CMD) y ejecuta:\n\npip install reportlab")
            except Exception as e:
                messagebox.showerror("No se pudo imprimir", f"Ocurrió un error inesperado:\n{e}")

        def _guardar_como():
            from tkinter import filedialog
            ruta_destino = filedialog.asksaveasfilename(
                defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
                initialfile=f"{nombre_archivo}.pdf")
            if not ruta_destino:
                return
            try:
                _generar_pdf(ruta_destino)
                messagebox.showinfo("Guardado", f"Resumen guardado en:\n{ruta_destino}")
            except ImportError:
                messagebox.showerror(
                    "Falta una librería",
                    "Para generar el PDF del resumen se necesita instalar 'reportlab'.\n\n"
                    "Abre una terminal (CMD) y ejecuta:\n\npip install reportlab")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el resumen:\n{e}")

        tk.Button(pie, text="🖶 Imprimir", font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                  fg="white", relief="flat", padx=14, pady=6, cursor="hand2",
                  command=_imprimir).pack(side="left")
        tk.Button(pie, text="💾 Guardar como PDF...", font=("Segoe UI", 9), padx=10, pady=6,
                  cursor="hand2", command=_guardar_como).pack(side="left", padx=8)
        tk.Button(pie, text="Cerrar", font=("Segoe UI", 9), padx=14, pady=6,
                  cursor="hand2", command=ventana.destroy).pack(side="right")

        ajustar_tamaño_ventana(ventana, ancho_min=420, alto_min=180)

    def _abrir_enviar_email(self):
        from ventana_enviar_email import VentanaEnviarEmail
        resumen_actual = resumen_financiero_del_dia(
            self.fecha_seleccionada.isoformat(), usuario_id=filtro_usuario_ventas(self.usuario_actual))
        VentanaEnviarEmail(self, fecha=self.fecha_seleccionada, resumen=resumen_actual,
                           usuario_actual=self.usuario_actual)

    def _abrir_reporte_rango(self):
        from ventana_reporte_rango import VentanaReporteRango
        VentanaReporteRango(self, self.usuario_actual)
