from utilidades_ui import formatear_gs, formatear_cantidad, habilitar_deseleccion_treeview
from traducciones import t
"""
ventana_inventario.py
Pantalla del módulo Inventario: grilla con columnas de inventario
(proveedor, stock mínimo, stock, comprometido, disponible), menú
contextual con Entrada, Salida, Editar Stock Mínimo, Historial e
Editar Producto, panel de Resumen de Inventario (toggleable), y
Reporte General exportable a Excel/PDF.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from models_catalogo import listar_productos, productos_bajo_stock_minimo, resumen_inventario
from ventana_editar_producto import VentanaEditarProducto
from ventanas_inventario import (
    VentanaAgregarInventario, VentanaSalidaInventario,
    VentanaEditarStockMinimo, VentanaHistorialMovimientos,
)
from menu_reporte_general import BotonReporteGeneral
from widgets_filtro_catalogo import BarraFiltrosCatalogo

AZUL_RIBBON = "#1d5fd6"
GRIS_FONDO = "#f4f5f7"


class PanelInventario(tk.Frame):
    def __init__(self, parent, usuario_actual):
        super().__init__(parent, bg="white")
        self.usuario_actual = usuario_actual
        self.filtro_actual = "todos"  # 'todos' | 'bajo_stock' | 'con_stock'
        self.resumen_visible = True

        self._construir_barra_superior()
        self._construir_grilla()
        self._construir_panel_resumen()
        self._cargar_datos()
        self._registrar_atajo_escape()

    def _registrar_atajo_escape(self):
        """Escape deselecciona el producto seleccionado en la grilla. Se
        registra con bind_all (para que funcione sin importar qué widget
        tenga el foco) pero verificando que este panel siga existiendo,
        ya que bind_all queda activo a nivel de toda la aplicación."""
        def _manejar_escape(event):
            if self.winfo_exists():
                self._deseleccionar_producto()
        self.bind_all("<Escape>", _manejar_escape)
        # Si el panel se destruye (se navega a otro módulo), liberamos el
        # binding global para no dejarlo "colgado" apuntando a un widget
        # que ya no existe.
        self.bind("<Destroy>", lambda e: self.unbind_all("<Escape>"))

    def _deseleccionar_producto(self):
        if self.tabla.selection():
            self.tabla.selection_remove(*self.tabla.selection())

    # ---------------- BARRA SUPERIOR ----------------
    def _construir_barra_superior(self):
        barra = tk.Frame(self, bg="white")
        barra.pack(fill="x", padx=10, pady=(10, 5))

        estilo_boton = dict(font=("Segoe UI", 9, "bold"), relief="flat", bd=0,
                            padx=12, pady=7, cursor="hand2")

        self.boton_bajo_stock = tk.Button(
            barra, text=t("inv_mostrar_bajo_stock"), bg="#fef3c7", fg="#92400e",
            activebackground="#fde68a", activeforeground="#92400e",
            command=self._toggle_bajo_stock, **estilo_boton)
        self.boton_bajo_stock.pack(side="left", padx=(0, 8))

        self.boton_con_stock = tk.Button(
            barra, text=t("inv_mostrar_con_stock"), bg="#dbeafe", fg="#1e40af",
            activebackground="#bfdbfe", activeforeground="#1e40af",
            command=self._toggle_con_stock, **estilo_boton)
        self.boton_con_stock.pack(side="left", padx=(0, 8))

        self.boton_inactivos = tk.Button(
            barra, text=t("inv_mostrar_inactivos"), bg="#fee2e2", fg="#991b1b",
            activebackground="#fecaca", activeforeground="#991b1b",
            command=self._toggle_inactivos, **estilo_boton)
        self.boton_inactivos.pack(side="left", padx=(0, 8))

        self.boton_resumen = tk.Button(
            barra, text=t("inv_ocultar_resumen"), bg="#e0e7ff", fg="#3730a3",
            activebackground="#c7d2fe", activeforeground="#3730a3",
            command=self._toggle_resumen, **estilo_boton)
        self.boton_resumen.pack(side="left", padx=(0, 8))

        self.boton_reporte = BotonReporteGeneral(
            barra, obtener_datos_callback=self._obtener_datos_reporte, nombre_archivo_base="Reporte_Inventario",
        )
        self.boton_reporte.generador_pdf_dashboard = self._generar_pdf_dashboard
        self.boton_reporte.generador_excel = self._generar_excel
        self.boton_reporte.pack(side="left", padx=(0, 8))

        # Fila aparte para la búsqueda, así siempre queda visible con buen
        # tamaño sin importar cuánto espacio ocupen los botones de arriba.
        barra_busqueda = tk.Frame(self, bg="white")
        barra_busqueda.pack(fill="x", padx=10, pady=(0, 5))

        tk.Label(barra_busqueda, text=t("inv_buscar_ctrl_b"), font=("Segoe UI", 9, "bold"),
                 bg="white", fg="#1e293b").pack(side="left", padx=(0, 8))
        self.var_busqueda = tk.StringVar()
        entry = tk.Entry(barra_busqueda, textvariable=self.var_busqueda, font=("Segoe UI", 10),
                          relief="solid", bd=1)
        entry.pack(side="left", fill="x", expand=True, ipady=3)
        entry.bind("<KeyRelease>", lambda e: self._cargar_datos())

        # Fila aparte para los filtros por Proveedor/Marca/Categoría,
        # debajo de la búsqueda por texto (se pueden combinar ambas).
        barra_filtros = tk.Frame(self, bg="white")
        barra_filtros.pack(fill="x", padx=10, pady=(0, 5))
        self.filtros = BarraFiltrosCatalogo(barra_filtros, on_cambio=self._cargar_datos)
        self.filtros.pack(side="left")

    def _estilo_boton_filtro(self, boton, activo: bool, color_pastel: str, color_texto_pastel: str,
                             color_solido: str = None):
        """Aplica el estilo 'chip' consistente: color pastel cuando el
        filtro está disponible, color sólido con texto blanco cuando el
        filtro está aplicado (para que se note claramente cuál está activo)."""
        if activo and color_solido:
            boton.config(bg=color_solido, fg="white", relief="flat")
        else:
            boton.config(bg=color_pastel, fg=color_texto_pastel, relief="flat")

    def _toggle_bajo_stock(self):
        self.filtro_actual = "todos" if self.filtro_actual == "bajo_stock" else "bajo_stock"
        activo = self.filtro_actual == "bajo_stock"
        self.boton_bajo_stock.config(
            text=t("inv_volver_todos") if activo else t("inv_mostrar_bajo_stock"))
        self._estilo_boton_filtro(self.boton_bajo_stock, activo, "#fef3c7", "#92400e", "#d97706")
        self._cargar_datos()

    def _toggle_con_stock(self):
        self.filtro_actual = "todos" if self.filtro_actual == "con_stock" else "con_stock"
        activo = self.filtro_actual == "con_stock"
        self.boton_con_stock.config(
            text=t("inv_volver_todos") if activo else t("inv_mostrar_con_stock"))
        self._estilo_boton_filtro(self.boton_con_stock, activo, "#dbeafe", "#1e40af", "#2563eb")
        self._cargar_datos()

    def _toggle_inactivos(self):
        self.filtro_actual = "todos" if self.filtro_actual == "inactivos" else "inactivos"
        activo = self.filtro_actual == "inactivos"
        self.boton_inactivos.config(
            text=t("inv_volver_activos") if activo else t("inv_mostrar_inactivos"))
        self._estilo_boton_filtro(self.boton_inactivos, activo, "#fee2e2", "#991b1b", "#dc2626")
        self._cargar_datos()

    def _toggle_resumen(self):
        self.resumen_visible = not self.resumen_visible
        if self.resumen_visible:
            self.contenedor_resumen.pack(fill="both", padx=10, pady=(0, 10))
            self.boton_resumen.config(text=t("inv_ocultar_resumen"), bg="#e0e7ff", fg="#3730a3", relief="flat")
            self._actualizar_resumen()
        else:
            self.contenedor_resumen.pack_forget()
            self.boton_resumen.config(text=t("inv_mostrar_resumen"), bg="#e0e7ff", fg="#3730a3", relief="flat")

    # ---------------- REPORTE GENERAL: puentes hacia el controlador genérico ----------------
    def _obtener_datos_reporte(self) -> dict:
        from reportes_datos import preparar_datos_reporte_inventario
        nombre_usuario = self.usuario_actual.get("nombre_completo", "")
        return preparar_datos_reporte_inventario(generado_por=nombre_usuario)

    def _generar_pdf_dashboard(self, ruta: str):
        from reporte_inventario_pdf import generar_reporte_inventario_pdf
        nombre_usuario = self.usuario_actual.get("nombre_completo", "")
        generar_reporte_inventario_pdf(ruta, generado_por=nombre_usuario)

    def _generar_excel(self, ruta: str):
        from reporte_inventario_excel import generar_reporte_inventario_excel
        nombre_usuario = self.usuario_actual.get("nombre_completo", "")
        generar_reporte_inventario_excel(ruta, generado_por=nombre_usuario)

    # ---------------- GRILLA ----------------
    def _construir_grilla(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        columnas = ("codigo", "descripcion", "proveedor", "p_compra", "p_venta",
                    "p_mayorista", "stock_minimo", "stock", "comprometido", "disponible", "adjunto")
        encabezados = (t("col_codigo_mayus"), t("col_descripcion_mayus"), t("col_proveedor"),
                       t("col_precio_compra_mayus"), t("col_precio_venta_mayus"),
                       t("col_precio_mayorista_mayus"), t("col_stock_minimo"), t("col_stock_mayus"),
                       t("col_comprometido"), t("col_disponible"), t("col_adjunto"))

        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc in zip(columnas, encabezados):
            self.tabla.heading(col, text=enc)
            ancho = 220 if col == "descripcion" else (80 if col == "adjunto" else 100)
            self.tabla.column(col, width=ancho, anchor="w" if col == "descripcion" else "center")

        # Resaltar en rojo claro las filas bajo stock mínimo
        self.tabla.tag_configure("bajo_stock", background="#fde8e8")
        # Productos desactivados: fondo gris y texto atenuado
        self.tabla.tag_configure("inactivo", background="#f3f4f6", foreground="#9ca3af")
        # La columna "Adjunto" se muestra en azul cuando hay imagen (link "Ver")
        self.tabla.tag_configure("con_imagen", foreground=AZUL_RIBBON)

        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        sb_y = ttk.Scrollbar(contenedor, orient="vertical",   command=self.tabla.yview)
        sb_x = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x.grid(row=1, column=0, sticky="ew")

        self.tabla.bind("<Button-3>", self._mostrar_menu_contextual)
        self.tabla.bind("<Button-1>", self._al_click_izquierdo)
        self._construir_menu_contextual()

    def _construir_menu_contextual(self):
        # El menú se reconstruye en cada click derecho (ver
        # _mostrar_menu_contextual) porque sus opciones dependen del
        # estado del producto seleccionado (activo/inactivo, stock, etc.).
        self.menu_contextual = tk.Menu(self, tearoff=0)

    def _mostrar_menu_contextual(self, event):
        fila_id = self.tabla.identify_row(event.y)
        if not fila_id:
            return
        self.tabla.selection_set(fila_id)
        producto = self.productos_por_id.get(fila_id)
        if producto is None:
            return

        self.menu_contextual.delete(0, "end")
        self.menu_contextual.add_command(label="📥  Entrada", command=self._abrir_entrada)
        self.menu_contextual.add_command(label="📤  Salida", command=self._abrir_salida)
        self.menu_contextual.add_command(label="🔧  Editar Stock Mínimo", command=self._abrir_editar_stock_minimo)
        self.menu_contextual.add_command(label="🕑  Historial Movimientos", command=self._abrir_historial)
        self.menu_contextual.add_separator()
        self.menu_contextual.add_command(label="✏  Editar Producto", command=self._abrir_editar_producto)
        self.menu_contextual.add_separator()

        if producto.get("activo", True):
            self.menu_contextual.add_command(
                label="🚫  Desactivar Producto", command=self._desactivar_producto)
        else:
            self.menu_contextual.add_command(
                label="✅  Activar Producto", command=self._activar_producto)

        from models_catalogo import puede_eliminarse_producto
        puede, _motivo = puede_eliminarse_producto(producto["id"])
        # El ítem se mantiene siempre HABILITADO (aunque no se pueda eliminar
        # todavía) para que el click dispare _eliminar_producto_definitivo,
        # que explica con un mensaje claro qué falta hacer primero. Si lo
        # deshabilitáramos con state='disabled', Tkinter ignora el click por
        # completo y el usuario nunca vería el motivo.
        color_texto = None if puede else "#9ca3af"
        self.menu_contextual.add_command(
            label="🗑  Eliminar Producto Definitivamente",
            command=self._eliminar_producto_definitivo,
            foreground=color_texto,
        )

        self.menu_contextual.tk_popup(event.x_root, event.y_root)

    def _al_click_izquierdo(self, event):
        """Si el click cae exactamente sobre la columna 'Adjunto' de una
        fila con imagen, abre el visor en vez de solo seleccionar la fila.
        Si el click cae fuera de cualquier fila (zona vacía de la grilla),
        deselecciona el producto actualmente seleccionado."""
        fila_id = self.tabla.identify_row(event.y)
        if not fila_id:
            self.tabla.selection_remove(*self.tabla.selection())
            return

        region = self.tabla.identify_region(event.x, event.y)
        if region != "cell":
            return
        columna = self.tabla.identify_column(event.x)

        indice_columna_adjunto = self.tabla["columns"].index("adjunto")
        if columna != f"#{indice_columna_adjunto + 1}":
            return

        producto = self.productos_por_id.get(fila_id)
        if producto and producto.get("imagen_ruta"):
            from ventana_ver_imagen import VentanaVerImagen
            VentanaVerImagen(self, producto["imagen_ruta"], nombre_producto=producto["nombre"])

    # ---------------- PANEL RESUMEN DE INVENTARIO (toggleable) ----------------
    def _construir_panel_resumen(self):
        # Contenedor con altura fija y scroll propio: como ahora cada
        # unidad de medida se muestra por separado (pueden ser 7 o más),
        # este panel podría crecer mucho más que antes. Con una altura
        # tope + scrollbar, el resumen nunca empuja el resto de la
        # pantalla ni queda cortado sin poder verse completo.
        self.contenedor_resumen = tk.Frame(self, bg=GRIS_FONDO, height=220)
        self.contenedor_resumen.pack(fill="both", padx=10, pady=(0, 10))
        self.contenedor_resumen.pack_propagate(False)

        canvas = tk.Canvas(self.contenedor_resumen, bg=GRIS_FONDO, highlightthickness=0,
                           bd=0, width=1, height=1)
        scrollbar = ttk.Scrollbar(self.contenedor_resumen, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)

        self.frame_resumen = tk.Frame(canvas, bg=GRIS_FONDO)
        id_ventana = canvas.create_window((0, 0), window=self.frame_resumen, anchor="nw")

        def _actualizar_scroll(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(id_ventana, width=canvas.winfo_width())
            if self.frame_resumen.winfo_reqheight() > canvas.winfo_height():
                if not scrollbar.winfo_ismapped():
                    scrollbar.pack(side="right", fill="y")
            else:
                if scrollbar.winfo_ismapped():
                    scrollbar.pack_forget()

        self.frame_resumen.bind("<Configure>", _actualizar_scroll)
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

        self.contenedor_resumen.bind("<Enter>", _activar_scroll)
        self.contenedor_resumen.bind("<Leave>", _desactivar_scroll)

        tk.Label(self.frame_resumen, text=t("inv_resumen_titulo"),
                 font=("Segoe UI", 12, "bold"), bg=GRIS_FONDO
                 ).pack(anchor="w", padx=12, pady=(8, 6))

        # Íconos y colores por unidad, para diferenciarlas de un vistazo
        self._iconos_unidad = {
            "Unidad": "🔷", "Caja": "📦", "Paquete": "🎁", "Docena": "🔢",
            "Kilogramo": "⚖️", "Litro": "🧴", "Metro": "📏",
        }

        self.frame_secciones_unidad = tk.Frame(self.frame_resumen, bg=GRIS_FONDO)
        self.frame_secciones_unidad.pack(fill="x", padx=12, pady=(0, 8))
        # Las secciones (una por unidad) se arman dinámicamente en
        # _actualizar_resumen(), porque el conjunto de unidades usadas
        # puede variar según los productos cargados.
        self.labels_por_unidad: dict[str, dict] = {}

    def _construir_seccion_unidad(self, padre, unidad: str, es_primera: bool):
        if not es_primera:
            tk.Frame(padre, bg="#d1d5db", height=1).pack(fill="x", pady=4)

        seccion = tk.Frame(padre, bg=GRIS_FONDO)
        seccion.pack(fill="x", pady=(0, 2))

        icono = self._iconos_unidad.get(unidad, "🔷")
        tk.Label(seccion, text=f"{icono} {unidad}", font=("Segoe UI", 9, "bold"),
                 bg=GRIS_FONDO, fg=AZUL_RIBBON).pack(anchor="w", pady=(0, 4))

        fila = tk.Frame(seccion, bg=GRIS_FONDO)
        fila.pack(fill="x")

        def _col(padre_col, etiqueta):
            bloque = tk.Frame(padre_col, bg=GRIS_FONDO)
            bloque.pack(side="left", padx=(0, 50))
            tk.Label(bloque, text=etiqueta, font=("Segoe UI", 9),
                     bg=GRIS_FONDO, fg="#555").pack(anchor="w")
            lbl = tk.Label(bloque, text="—", font=("Segoe UI", 13, "bold"), bg=GRIS_FONDO)
            lbl.pack(anchor="w")
            return lbl

        lbl_cant   = _col(fila, "Cantidad en Inventario")
        lbl_compra = _col(fila, "Valor Total (a Precio de Compra)")
        lbl_venta  = _col(fila, "Valor Total (a Precio de Venta)")
        self.labels_por_unidad[unidad] = {"cantidad": lbl_cant, "compra": lbl_compra, "venta": lbl_venta}

    def _actualizar_resumen(self):
        if not self.resumen_visible:
            return
        r = resumen_inventario()

        # Reconstruir las secciones si cambió el conjunto de unidades
        # (por ejemplo, la primera vez que se usa una unidad nueva).
        # Se muestran SIEMPRE todas las unidades de medida (Unidad, Caja,
        # Paquete, Docena, Kilogramo, Litro, Metro, y cualquier otra que
        # se llegue a usar), tengan o no productos cargados todavía, para
        # que se puedan visualizar todas de entrada.
        unidades_actuales = list(r["orden_unidades"])
        if not unidades_actuales:
            unidades_actuales = ["Unidad"]
        if set(unidades_actuales) != set(self.labels_por_unidad.keys()):
            for w in self.frame_secciones_unidad.winfo_children():
                w.destroy()
            self.labels_por_unidad = {}
            for i, unidad in enumerate(unidades_actuales):
                self._construir_seccion_unidad(self.frame_secciones_unidad, unidad, es_primera=(i == 0))

        for unidad, datos in r["por_unidad"].items():
            if unidad not in self.labels_por_unidad:
                continue
            labels = self.labels_por_unidad[unidad]
            if unidad in ("Kilogramo", "Litro", "Metro"):
                s = f"{datos['cantidad']:.10f}".rstrip("0").rstrip(".")
                cant_txt = s.replace(".", ",")
            else:
                cant_txt = str(int(round(datos["cantidad"])))
            labels["cantidad"].config(text=cant_txt)
            labels["compra"].config(text=formatear_gs(datos["valor_compra"]))
            labels["venta"].config(text=formatear_gs(datos["valor_venta"]))

    # ---------------- CARGA DE DATOS ----------------
    def _cargar_datos(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        texto = self.var_busqueda.get()
        proveedor_id, marca_id, categoria_id = self.filtros.obtener_ids()

        if self.filtro_actual == "inactivos":
            productos = listar_productos(solo_activos=False, texto_busqueda=texto,
                                          proveedor_id=proveedor_id, marca_id=marca_id,
                                          categoria_id=categoria_id)
            productos = [p for p in productos if not p.get("activo", True)]
        else:
            productos = listar_productos(solo_activos=True, texto_busqueda=texto,
                                          proveedor_id=proveedor_id, marca_id=marca_id,
                                          categoria_id=categoria_id)
            if self.filtro_actual == "bajo_stock":
                ids_bajo_stock = {p["id"] for p in productos_bajo_stock_minimo()}
                productos = [p for p in productos if p["id"] in ids_bajo_stock]
            elif self.filtro_actual == "con_stock":
                productos = [p for p in productos if p["stock"] > 0]

        # Abreviaturas por unidad de medida
        UNIDADES_CONTINUAS = {"Kilogramo": "Kg", "Litro": "Lt", "Metro": "Mt"}
        UNIDADES_ENTERAS   = {"Unidad": "Unid.", "Caja": "Cja.", "Paquete": "Paq.", "Docena": "Doc."}

        def formatear_cantidad(valor, unidad):
            if valor is None:
                return "—"
            abrev = UNIDADES_CONTINUAS.get(unidad)
            if abrev:
                s = f"{valor:.10f}".rstrip("0").rstrip(".")
                return f"{s.replace('.', ',')} {abrev}"
            abrev = UNIDADES_ENTERAS.get(unidad, "Unid.")
            return f"{int(round(valor))} {abrev}"

        self.productos_por_id = {}
        for p in productos:
            unidad       = p.get("unidad_medida", "Unidad")
            es_servicio  = p.get("tipo_producto") == "Servicio"
            es_inactivo  = not p.get("activo", True)
            tiene_imagen = bool(p.get("imagen_ruta"))
            texto_adjunto = "📎 Ver" if tiene_imagen else "—"

            stock        = p.get("stock", 0) or 0
            comprometido = p.get("comprometido", 0) or 0
            disponible   = p.get("disponible", stock - comprometido)
            stock_min    = p.get("stock_minimo", 0) or 0

            es_bajo_stock = (not isinstance(disponible, str)) and stock <= stock_min

            tags = []
            if es_inactivo:
                tags.append("inactivo")
            elif es_bajo_stock:
                tags.append("bajo_stock")
            if tiene_imagen:
                tags.append("con_imagen")

            nombre_mostrado = f"🚫 {p['nombre']}" if es_inactivo else p["nombre"]

            if es_servicio:
                stock_txt = comp_txt = disp_txt = smin_txt = "—"
            else:
                stock_txt = formatear_cantidad(stock, unidad)
                comp_txt  = formatear_cantidad(comprometido, unidad)
                disp_txt  = disponible if isinstance(disponible, str) else formatear_cantidad(disponible, unidad)
                smin_txt  = formatear_cantidad(stock_min, unidad)

            self.tabla.insert("", "end", iid=str(p["id"]), values=(
                p["id"], nombre_mostrado, p["proveedor"],
                formatear_gs(p['precio_compra']), formatear_gs(p['precio_venta']),
                formatear_gs(p['precio_mayorista']), smin_txt,
                stock_txt, comp_txt, disp_txt, texto_adjunto,
            ), tags=tuple(tags))
            self.productos_por_id[str(p["id"])] = p

        self._actualizar_resumen()

    def _producto_seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return None
        return self.productos_por_id.get(seleccion[0])

    # ---------------- ACCIONES DEL MENÚ CONTEXTUAL ----------------
    def _abrir_entrada(self):
        producto = self._producto_seleccionado()
        if producto is None:
            messagebox.showwarning("Selecciona un producto", "Primero selecciona un producto de la lista.")
            return
        VentanaAgregarInventario(self, producto, self.usuario_actual, on_guardado=self._cargar_datos)

    def _abrir_salida(self):
        producto = self._producto_seleccionado()
        if producto is None:
            messagebox.showwarning("Selecciona un producto", "Primero selecciona un producto de la lista.")
            return
        VentanaSalidaInventario(self, producto, self.usuario_actual, on_guardado=self._cargar_datos)

    def _abrir_editar_stock_minimo(self):
        producto = self._producto_seleccionado()
        if producto is None:
            messagebox.showwarning("Selecciona un producto", "Primero selecciona un producto de la lista.")
            return
        VentanaEditarStockMinimo(self, producto, on_guardado=self._cargar_datos)

    def _abrir_historial(self):
        producto = self._producto_seleccionado()
        if producto is None:
            messagebox.showwarning("Selecciona un producto", "Primero selecciona un producto de la lista.")
            return
        VentanaHistorialMovimientos(self, producto)

    def _abrir_editar_producto(self):
        producto = self._producto_seleccionado()
        if producto is None:
            messagebox.showwarning("Selecciona un producto", "Primero selecciona un producto de la lista.")
            return
        VentanaEditarProducto(self, producto=producto, on_guardado=self._refrescar_tras_editar_producto, usuario_actual=self.usuario_actual)

    def _refrescar_tras_editar_producto(self):
        """Al editar un producto se puede haber creado una marca o
        categoría nueva desde el propio formulario, así que además de
        recargar la grilla hay que repoblar las opciones de los combos
        de filtro."""
        self.filtros.actualizar_opciones()
        self._cargar_datos()

    def _desactivar_producto(self):
        producto = self._producto_seleccionado()
        if producto is None:
            return

        stock = producto.get("stock", 0) or 0
        comprometido = producto.get("comprometido", 0) or 0
        if not isinstance(stock, str) and stock != 0:
            messagebox.showwarning(
                "No se puede desactivar",
                f"No se puede desactivar '{producto['nombre']}': todavía tiene "
                f"{stock:g} unidad(es) en stock.\n\n"
                "Primero registra una Salida de Inventario hasta dejar el "
                "stock en cero, y luego podrás desactivarlo.",
            )
            return
        if not isinstance(comprometido, str) and comprometido != 0:
            messagebox.showwarning(
                "No se puede desactivar",
                f"No se puede desactivar '{producto['nombre']}': tiene "
                f"{comprometido:g} unidad(es) comprometidas en ventas pendientes.",
            )
            return

        if not messagebox.askyesno(
            "Desactivar producto",
            f"¿Desactivar '{producto['nombre']}'?\n\n"
            "Dejará de aparecer en Ventas y en el listado normal de "
            "Inventario, pero podrás reactivarlo en cualquier momento.",
        ):
            return
        from models_catalogo import cambiar_estado_producto
        ok, msg = cambiar_estado_producto(producto["id"], False)
        if ok:
            self._cargar_datos()
        else:
            messagebox.showwarning("No se puede desactivar", msg)

    def _activar_producto(self):
        producto = self._producto_seleccionado()
        if producto is None:
            return
        from models_catalogo import cambiar_estado_producto
        ok, msg = cambiar_estado_producto(producto["id"], True)
        if ok:
            self._cargar_datos()
        else:
            messagebox.showerror("Error", msg)

    def _eliminar_producto_definitivo(self):
        producto = self._producto_seleccionado()
        if producto is None:
            return

        from models_catalogo import puede_eliminarse_producto, eliminar_producto
        puede, motivo = puede_eliminarse_producto(producto["id"])
        if not puede:
            messagebox.showwarning("No se puede eliminar", motivo)
            return

        if not messagebox.askyesno(
            "⚠ Eliminar producto definitivamente",
            f"Esta acción eliminará '{producto['nombre']}' de forma PERMANENTE "
            "y no se puede deshacer.\n\n"
            "El historial de ventas y movimientos de inventario que ya tuvo "
            "este producto se conservará, mostrando su nombre como referencia.\n\n"
            "¿Confirmás la eliminación definitiva?",
            icon="warning",
        ):
            return

        ok, msg = eliminar_producto(producto["id"])
        if ok:
            messagebox.showinfo("Producto eliminado", msg)
            self._cargar_datos()
        else:
            messagebox.showerror("Error", msg)
