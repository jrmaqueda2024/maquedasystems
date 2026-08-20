from utilidades_ui import formatear_gs, formatear_cantidad, habilitar_deseleccion_treeview
from traducciones import t
"""
ventana_productos.py
Pantalla del módulo Productos: muestra la grilla de productos (como en
MetaVentas) y permite, mediante click derecho sobre una fila, abrir el
menú contextual con "Editar Producto" y "Agrupaciones y Divisiones".

Incluye una columna "Adjunto" que muestra "Ver" (clickeable, en azul)
cuando el producto tiene una imagen asociada, o "—" si no tiene.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from models_catalogo import listar_productos
from ventana_editar_producto import VentanaEditarProducto
from ventana_gestion_catalogo import VentanaProveedores, VentanaMarcas, VentanaCategorias
from widgets_filtro_catalogo import BarraFiltrosCatalogo

AZUL_RIBBON = "#1d5fd6"
GRIS_FONDO = "#e9eaee"


class PanelProductos(tk.Frame):
    """Panel que se inserta dentro del frame de contenido de la ventana principal."""

    def __init__(self, parent, usuario_actual):
        super().__init__(parent, bg="white")
        self.usuario_actual = usuario_actual
        self.mostrar_activos = True

        self._construir_barra_superior()
        self._construir_grilla()
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

    # ---------------- BARRA SUPERIOR (búsqueda + filtro activos/inactivos) ----------------
    def _construir_barra_superior(self):
        barra = tk.Frame(self, bg="white")
        barra.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(barra, text=t("buscar") + ":", font=("Segoe UI", 9), bg="white").pack(side="left")
        self.var_busqueda = tk.StringVar()
        entry_busqueda = tk.Entry(barra, textvariable=self.var_busqueda, font=("Segoe UI", 9), width=30)
        entry_busqueda.pack(side="left", padx=(5, 15))
        entry_busqueda.bind("<KeyRelease>", lambda e: self._cargar_datos())

        self.var_activos = tk.BooleanVar(value=True)
        self.var_inactivos = tk.BooleanVar(value=False)
        tk.Checkbutton(barra, text=t("activos"), variable=self.var_activos, bg="white",
                       font=("Segoe UI", 9), command=self._cargar_datos).pack(side="left", padx=5)
        tk.Checkbutton(barra, text=t("inactivos"), variable=self.var_inactivos, bg="white",
                       font=("Segoe UI", 9), command=self._cargar_datos).pack(side="left", padx=5)

        tk.Button(barra, text=t("productos_nuevo"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                  fg="white", relief="flat", padx=14, pady=7, cursor="hand2",
                  activebackground="#163d8c", activeforeground="white",
                  command=self._nuevo_producto).pack(side="right")

        # Botones de gestión de listas auxiliares (Proveedores, Marcas,
        # Categorías): estilo "chip" con un color pastel propio por cada
        # uno, para diferenciarlos de un vistazo y que no se vean tan
        # planos como un simple botón blanco con borde.
        tk.Button(barra, text=t("productos_categorias"), font=("Segoe UI", 9, "bold"),
                  bg="#fef3c7", fg="#92400e", relief="flat", padx=12, pady=7, cursor="hand2",
                  activebackground="#fde68a", activeforeground="#92400e",
                  command=self._abrir_categorias).pack(side="right", padx=(0, 10))
        tk.Button(barra, text=t("productos_marcas"), font=("Segoe UI", 9, "bold"),
                  bg="#f3e8ff", fg="#6b21a8", relief="flat", padx=12, pady=7, cursor="hand2",
                  activebackground="#e9d5ff", activeforeground="#6b21a8",
                  command=self._abrir_marcas).pack(side="right", padx=(0, 6))
        tk.Button(barra, text=t("productos_proveedores"), font=("Segoe UI", 9, "bold"),
                  bg="#dbeafe", fg="#1e40af", relief="flat", padx=12, pady=7, cursor="hand2",
                  activebackground="#bfdbfe", activeforeground="#1e40af",
                  command=self._abrir_proveedores).pack(side="right", padx=(0, 6))

        # Fila aparte para los filtros por Proveedor/Marca/Categoría, así
        # siempre quedan visibles con buen tamaño sin importar cuánto
        # espacio ocupen los botones de arriba (mismo criterio que la
        # fila de búsqueda de Inventario).
        barra_filtros = tk.Frame(self, bg="white")
        barra_filtros.pack(fill="x", padx=10, pady=(0, 10))
        self.filtros = BarraFiltrosCatalogo(barra_filtros, on_cambio=self._cargar_datos)
        self.filtros.pack(side="left")

    # ---------------- GRILLA ----------------
    def _construir_grilla(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columnas = ("codigo", "descripcion", "marca", "p_compra", "p_venta",
                    "p_credito", "p_mayorista", "stock", "comprometido", "disponible", "adjunto")
        encabezados = (t("col_codigo_mayus"), t("col_descripcion_mayus"), t("col_marca"), t("col_p_compra"),
                       t("col_p_venta"), t("col_p_credito"), t("col_p_mayorista"), t("col_stock_mayus"),
                       t("col_comprometido"), t("col_disponible"), t("col_adjunto"))

        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, encabezado in zip(columnas, encabezados):
            self.tabla.heading(col, text=encabezado)
            ancho = 220 if col == "descripcion" else (80 if col == "adjunto" else 95)
            self.tabla.column(col, width=ancho, anchor="w" if col == "descripcion" else "center")

        # La columna "Adjunto" se muestra en azul cuando hay imagen, para
        # que se note que es clickeable (como un link "Ver").
        self.tabla.tag_configure("con_imagen", foreground=AZUL_RIBBON)

        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        sb_y = ttk.Scrollbar(contenedor, orient="vertical",   command=self.tabla.yview)
        sb_x = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x.grid(row=1, column=0, sticky="ew")

        # Click derecho abre el menú contextual
        self.tabla.bind("<Button-3>", self._mostrar_menu_contextual)
        # Click izquierdo: si cae sobre la columna "Adjunto" y el producto
        # tiene imagen, abre el visor; si no, comportamiento normal.
        self.tabla.bind("<Button-1>", self._al_click_izquierdo)
        # Doble click izquierdo también edita (atajo cómodo)
        self.tabla.bind("<Double-1>", lambda e: self._editar_producto_seleccionado())

        self._construir_menu_contextual()

    def _construir_menu_contextual(self):
        self.menu_contextual = tk.Menu(self, tearoff=0)
        self.menu_contextual.add_command(label="✏  Editar Producto", command=self._editar_producto_seleccionado)
        self.menu_contextual.add_command(label="🔗  Agrupaciones y Divisiones", command=self._agrupaciones_y_divisiones)

    def _mostrar_menu_contextual(self, event):
        fila_id = self.tabla.identify_row(event.y)
        if fila_id:
            self.tabla.selection_set(fila_id)
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
            self._abrir_visor_imagen(producto)

    def _abrir_visor_imagen(self, producto):
        from ventana_ver_imagen import VentanaVerImagen
        VentanaVerImagen(self, producto["imagen_ruta"], nombre_producto=producto["nombre"])

    # ---------------- CARGA DE DATOS ----------------
    def _cargar_datos(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        texto = self.var_busqueda.get()
        mostrar_activos = self.var_activos.get()
        mostrar_inactivos = self.var_inactivos.get()
        proveedor_id, marca_id, categoria_id = self.filtros.obtener_ids()

        productos = listar_productos(solo_activos=False, texto_busqueda=texto,
                                      proveedor_id=proveedor_id, marca_id=marca_id,
                                      categoria_id=categoria_id)
        self.productos_por_id = {}

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

        for p in productos:
            if p["activo"] and not mostrar_activos:
                continue
            if not p["activo"] and not mostrar_inactivos:
                continue

            unidad      = p.get("unidad_medida", "Unidad")
            es_servicio = p.get("tipo_producto") == "Servicio"
            tiene_imagen = bool(p.get("imagen_ruta"))
            texto_adjunto = "📎 Ver" if tiene_imagen else "—"

            if es_servicio:
                stock_txt = comp_txt = disp_txt = "—"
            else:
                stock_txt = formatear_cantidad(p.get("stock", 0) or 0, unidad)
                comp_txt  = formatear_cantidad(p.get("comprometido", 0) or 0, unidad)
                disp_txt  = (p["disponible"] if isinstance(p["disponible"], str)
                             else formatear_cantidad(p["disponible"], unidad))

            self.tabla.insert("", "end", iid=str(p["id"]), values=(
                p["id"], p["nombre"], p["marca"],
                formatear_gs(p['precio_compra']), formatear_gs(p['precio_venta']),
                formatear_gs(p['precio_credito']), formatear_gs(p['precio_mayorista']),
                stock_txt, comp_txt, disp_txt, texto_adjunto,
            ), tags=("con_imagen",) if tiene_imagen else ())
            self.productos_por_id[str(p["id"])] = p

    def _producto_seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return None
        return self.productos_por_id.get(seleccion[0])

    # ---------------- ACCIONES ----------------
    def _nuevo_producto(self):
        VentanaEditarProducto(self, producto=None, on_guardado=self._refrescar_tras_gestion_catalogo, usuario_actual=self.usuario_actual)

    def _editar_producto_seleccionado(self):
        producto = self._producto_seleccionado()
        if producto is None:
            messagebox.showwarning("Selecciona un producto", "Primero selecciona un producto de la lista.")
            return
        VentanaEditarProducto(self, producto=producto, on_guardado=self._refrescar_tras_gestion_catalogo, usuario_actual=self.usuario_actual)

    def _abrir_proveedores(self):
        VentanaProveedores(self, on_cambio=self._refrescar_tras_gestion_catalogo)

    def _abrir_marcas(self):
        VentanaMarcas(self, on_cambio=self._refrescar_tras_gestion_catalogo)

    def _abrir_categorias(self):
        VentanaCategorias(self, on_cambio=self._refrescar_tras_gestion_catalogo)

    def _refrescar_tras_gestion_catalogo(self):
        """Después de crear/editar/eliminar un proveedor, marca o
        categoría, hay que repoblar las opciones de los combos de
        filtro (por si se agregó uno nuevo o se renombró/eliminó el
        que estaba seleccionado) y recién después recargar la grilla."""
        self.filtros.actualizar_opciones()
        self._cargar_datos()

    def _agrupaciones_y_divisiones(self):
        producto = self._producto_seleccionado()
        nombre = producto["nombre"] if producto else ""
        messagebox.showinfo(
            "Agrupaciones y Divisiones",
            f"La funcionalidad de Agrupaciones y Divisiones para '{nombre}' "
            "estará disponible próximamente."
        )
