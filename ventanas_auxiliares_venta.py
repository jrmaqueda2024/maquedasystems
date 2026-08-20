"""
ventanas_auxiliares_venta.py
Ventanas modales auxiliares usadas desde la pantalla de Ventas:
- VentanaBuscarProducto (F2): buscador con grilla de resultados.
- VentanaAsignarCliente (F1): buscador de cliente + alta rápida si no existe.
- VentanaArticulosComunes (Ctrl+P): grilla de productos marcados como comunes.

Todas usan layout responsive (grid en la raíz + pack/grid en el contenido),
por lo que se pueden maximizar o redimensionar sin que ningún campo o
botón quede oculto fuera del área visible.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from models_catalogo import listar_productos
from models_clientes import listar_clientes
from utilidades_ui import forzar_mayusculas, ajustar_tamaño_ventana, formatear_gs, formatear_cantidad, habilitar_deseleccion_treeview
from traducciones import t
from widgets_filtro_catalogo import BarraFiltrosCatalogo

AZUL_RIBBON = "#1d5fd6"


class VentanaBuscarProducto(tk.Toplevel):
    """F2 - Buscar: permite buscar por nombre/código y elegir un producto
    haciendo doble click o con el botón Seleccionar."""

    def __init__(self, parent, on_seleccionado):
        super().__init__(parent)
        self.on_seleccionado = on_seleccionado

        self.title("Buscar Producto")
        self.geometry("680x500")
        self.minsize(500, 400)
        self.resizable(True, True)
        self.configure(bg="white")
        self.grab_set()

        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text=t("aux_buscar_producto_f2"), font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

        frame_busqueda = tk.Frame(self, bg="white")
        frame_busqueda.grid(row=1, column=0, sticky="ew", padx=10, pady=8)
        tk.Label(frame_busqueda, text=t("buscar") + ":", font=("Segoe UI", 9), bg="white").pack(side="left")
        self.var_busqueda = tk.StringVar()
        entry = tk.Entry(frame_busqueda, textvariable=self.var_busqueda, font=("Segoe UI", 10), width=40)
        entry.pack(side="left", padx=8, fill="x", expand=True)
        entry.bind("<KeyRelease>", lambda e: self._buscar())
        entry.focus()

        frame_filtros = tk.Frame(self, bg="white")
        frame_filtros.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))
        self.filtros = BarraFiltrosCatalogo(frame_filtros, on_cambio=self._buscar)
        self.filtros.pack(side="left")

        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=3, column=0, sticky="nsew", padx=10)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        columnas   = ("codigo", "descripcion", "precio_venta", "precio_mayorista", "precio_minorista", "disponible")
        encabezados = (t("col_codigo_mayus"), t("col_descripcion_mayus"), t("col_p_venta"), t("col_p_mayorista_mayus"), t("aux_p_minorista"), t("col_disponible"))
        anchos      = (70, 220, 105, 105, 105, 100)

        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho,
                              anchor="w" if col == "descripcion" else "center")

        sb_y = ttk.Scrollbar(contenedor, orient="vertical",   command=self.tabla.yview)
        sb_x = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x.grid(row=1, column=0, sticky="ew")

        self.tabla.bind("<Double-1>", lambda e: self._confirmar_seleccion())
        self.bind("<Return>", lambda e: self._confirmar_seleccion())

        frame_botones = tk.Frame(self, bg="white", height=46)
        frame_botones.grid(row=4, column=0, sticky="ew")
        frame_botones.grid_propagate(False)
        tk.Button(frame_botones, text=t("seleccionar_boton"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, width=14, command=self._confirmar_seleccion).pack(pady=8)

        self.productos_por_id = {}
        self._buscar()

    def _buscar(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        proveedor_id, marca_id, categoria_id = self.filtros.obtener_ids()
        productos = listar_productos(solo_activos=True, texto_busqueda=self.var_busqueda.get(),
                                      proveedor_id=proveedor_id, marca_id=marca_id,
                                      categoria_id=categoria_id)
        self.productos_por_id = {}
        for p in productos:
            unidad      = p.get("unidad_medida", "Unidad")
            es_servicio = p.get("tipo_producto") == "Servicio"
            disp = p["disponible"]
            if es_servicio:
                disp_txt = "—"
            elif isinstance(disp, str):
                disp_txt = disp
            else:
                disp_txt = formatear_cantidad(disp, unidad)
            unidad      = p.get("unidad_medida", "Unidad")
            es_servicio = p.get("tipo_producto") == "Servicio"
            disp = p.get("disponible", 0)
            if es_servicio:
                disp_txt = "—"
            elif isinstance(disp, str):
                disp_txt = disp
            else:
                disp_txt = formatear_cantidad(disp, unidad)

            self.tabla.insert("", "end", iid=str(p["id"]), values=(
                p["id"], p["nombre"],
                formatear_gs(p["precio_venta"]),
                formatear_gs(p.get("precio_mayorista", 0)),
                formatear_gs(p.get("precio_credito", p["precio_venta"])),
                disp_txt,
            ))
            self.productos_por_id[str(p["id"])] = p

    def _confirmar_seleccion(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Selecciona un producto", "Elige un producto de la lista.")
            return
        producto = self.productos_por_id[seleccion[0]]
        self.destroy()
        self.on_seleccionado(producto)


class VentanaArticulosComunes(tk.Toplevel):
    """Ctrl+P - Producto Común: permite cargar libremente la descripción,
    cantidad y precio unitario de un artículo que no necesita existir antes
    en el catálogo (ej. un producto vario o de mostrador). Al aceptar, se
    crea (o reutiliza, si ya existe uno con la misma descripción) un
    producto real en la base de datos con stock ilimitado, y se agrega de
    inmediato a la venta actual."""

    def __init__(self, parent, on_seleccionado):
        super().__init__(parent)
        self.on_seleccionado = on_seleccionado

        self.title("Producto Común")
        self.minsize(340, 280)
        self.resizable(True, True)
        self.configure(bg="white")
        self.grab_set()

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text=t("aux_producto_comun"), font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=1, column=0, sticky="nsew", padx=20, pady=15)
        contenedor.grid_columnconfigure(0, weight=1)
        contenedor.grid_columnconfigure(1, weight=0)
        contenedor.grid_columnconfigure(2, weight=1)

        tk.Label(contenedor, text=t("aux_descripcion_producto"), font=("Segoe UI", 9, "bold"),
                 bg="white").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 2))
        self.var_descripcion = tk.StringVar()
        entry_descripcion = tk.Entry(contenedor, textvariable=self.var_descripcion, font=("Segoe UI", 11))
        entry_descripcion.grid(row=1, column=0, columnspan=3, sticky="ew")
        entry_descripcion.focus()
        forzar_mayusculas(entry_descripcion, self.var_descripcion)

        tk.Label(contenedor, text=t("cantidad_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=2, column=0, sticky="w", pady=(14, 2))
        tk.Label(contenedor, text=t("precio_unitario_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=2, column=2, sticky="w", pady=(14, 2))

        self.var_cantidad = tk.StringVar(value="1")
        spin_cantidad = tk.Spinbox(contenedor, from_=1, to=999999, textvariable=self.var_cantidad,
                                    font=("Segoe UI", 10), width=8)
        spin_cantidad.grid(row=3, column=0, sticky="ew")

        tk.Label(contenedor, text="x", font=("Segoe UI", 10, "bold"), bg="white").grid(
            row=3, column=1, padx=6)

        self.var_precio = tk.StringVar(value="0")
        entry_precio = tk.Entry(contenedor, textvariable=self.var_precio, font=("Segoe UI", 10))
        entry_precio.grid(row=3, column=2, sticky="ew")

        frame_botones = tk.Frame(contenedor, bg="white")
        frame_botones.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(28, 0))
        tk.Button(frame_botones, text=t("aceptar_boton"), font=("Segoe UI", 10, "bold"), bg="white",
                  fg="#16a34a", relief="solid", bd=1, padx=14, pady=8, cursor="hand2",
                  command=self._aceptar).pack(side="left", padx=(0, 8))
        tk.Button(frame_botones, text=t("cancelar_x"), font=("Segoe UI", 10, "bold"), bg="white",
                  fg="#dc2626", relief="solid", bd=1, padx=14, pady=8, cursor="hand2",
                  command=self.destroy).pack(side="left")

        entry_descripcion.bind("<Return>", lambda e: self._aceptar())
        entry_precio.bind("<Return>", lambda e: self._aceptar())

        ajustar_tamaño_ventana(self, ancho_min=340, alto_min=280)

    def _aceptar(self):
        descripcion = self.var_descripcion.get().strip()
        if not descripcion:
            messagebox.showerror("Falta la descripción", "Ingresa la descripción del producto.")
            return

        try:
            cantidad = float(self.var_cantidad.get().strip().replace(",", "."))
            if cantidad <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Cantidad inválida", "Ingresa una cantidad numérica mayor a cero.")
            return

        texto_precio = self.var_precio.get().strip().replace(",", ".").replace("Gs.", "")
        try:
            precio_unitario = float(texto_precio) if texto_precio else 0.0
        except ValueError:
            messagebox.showerror("Precio inválido", "Ingresa un precio unitario numérico válido.")
            return

        # Producto virtual: NO se guarda en la BD ni en inventario.
        # Se usa un ID temporal negativo único para identificarlo en la grilla.
        import time
        id_temporal = -int(time.time() * 1000) % 10_000_000
        producto_virtual = {
            "id": id_temporal,
            "nombre": descripcion,
            "precio_venta": precio_unitario,
            "precio_mayorista": precio_unitario,
            "disponible": "Libre",
            "activo": True,
            "es_libre": True,          # bandera para distinguirlo en cobrar/reportes
        }

        self.destroy()
        self.on_seleccionado(producto_virtual, cantidad)


class VentanaAsignarCliente(tk.Toplevel):
    """F1 - Asignar Cliente: buscador de clientes existentes, con alta rápida
    si el cliente no aparece en la lista."""

    def __init__(self, parent, on_seleccionado):
        super().__init__(parent)
        self.on_seleccionado = on_seleccionado

        self.title("Asignar Cliente")
        self.geometry("640x460")
        self.minsize(480, 360)
        self.resizable(True, True)
        self.configure(bg="white")
        self.grab_set()

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text=t("aux_asignar_cliente_f1"), font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

        frame_busqueda = tk.Frame(self, bg="white")
        frame_busqueda.grid(row=1, column=0, sticky="ew", padx=10, pady=8)
        tk.Label(frame_busqueda, text=t("buscar") + ":", font=("Segoe UI", 9), bg="white").pack(side="left")
        self.var_busqueda = tk.StringVar()
        entry = tk.Entry(frame_busqueda, textvariable=self.var_busqueda, font=("Segoe UI", 10), width=35)
        entry.pack(side="left", padx=8, fill="x", expand=True)
        entry.bind("<KeyRelease>", lambda e: self._buscar())
        entry.focus()

        tk.Button(frame_busqueda, text=t("aux_cliente_nuevo"), font=("Segoe UI", 9), bg="white",
                  relief="solid", bd=1, command=self._abrir_alta_rapida).pack(side="right")

        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=2, column=0, sticky="nsew", padx=10)

        columnas = ("codigo", "nombre", "documento", "telefono")
        encabezados = (t("col_codigo_mayus"), t("col_nombre_mayus"), t("col_documento"), t("col_telefono").upper())
        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc in zip(columnas, encabezados):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=130, anchor="center")
        self.tabla.column("nombre", anchor="w", width=220)

        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        scrollbar_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=scrollbar.set, xscrollcommand=scrollbar_h.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        scrollbar_h.grid(row=1, column=0, sticky="ew")

        self.tabla.bind("<Double-1>", lambda e: self._confirmar_seleccion())

        frame_botones = tk.Frame(self, bg="white", height=46)
        frame_botones.grid(row=3, column=0, sticky="ew", pady=4)
        frame_botones.grid_propagate(False)
        contenido_botones = tk.Frame(frame_botones, bg="white")
        contenido_botones.pack()
        tk.Button(contenido_botones, text=t("seleccionar_boton"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self._confirmar_seleccion).pack(side="left", padx=(0, 8))
        tk.Button(contenido_botones, text=t("aux_cliente_ocasional_sin_registro"), font=("Segoe UI", 9), bg="white",
                  relief="solid", bd=1, command=self._usar_ocasional).pack(side="left")

        self.clientes_por_id = {}
        self._buscar()

    def _buscar(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        clientes = listar_clientes(texto_busqueda=self.var_busqueda.get())
        self.clientes_por_id = {}
        for c in clientes:
            self.tabla.insert("", "end", iid=str(c["id"]), values=(
                c["id"], c["nombre"], c["nro_documento"], c["telefono"]
            ))
            self.clientes_por_id[str(c["id"])] = c

    def _confirmar_seleccion(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Selecciona un cliente", "Elige un cliente de la lista, o usa 'Cliente Ocasional'.")
            return
        cliente = self.clientes_por_id[seleccion[0]]
        self.destroy()
        self.on_seleccionado(cliente)

    def _usar_ocasional(self):
        self.destroy()
        self.on_seleccionado(None)

    def _abrir_alta_rapida(self):
        """Abre el MISMO formulario completo del módulo Clientes
        (3 pestañas: Datos, Créditos, Pagos). Al guardar, queda cargado
        en clientes y refresca la búsqueda de esta ventana."""
        from ventana_clientes import VentanaFormularioCliente
        VentanaFormularioCliente(self, cliente=None, on_guardado=self._buscar)


class VentanaConsultarStock(tk.Toplevel):
    """Consulta rápida de stock disponible de todos los productos, accesible
    para cualquier usuario (incluyendo vendedores sin acceso a Inventario).
    Solo muestra información, no permite agregar a la venta ni editar nada."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Consultar Stock")
        self.resizable(True, True)
        self.configure(bg="white")
        self.grab_set()
        try:
            self.attributes("-toolwindow", False)
        except tk.TclError:
            pass

        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Barra de título ──────────────────────────────────
        barra = tk.Frame(self, bg=AZUL_RIBBON, height=40)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text=t("aux_consultar_stock"),
                 font=("Segoe UI", 11, "bold"), bg=AZUL_RIBBON, fg="white"
                 ).pack(side="left", padx=15, pady=9)

        # ── Barra de búsqueda y filtros ───────────────────────
        frame_busq = tk.Frame(self, bg="white")
        frame_busq.grid(row=1, column=0, sticky="ew", padx=12, pady=8)

        tk.Label(frame_busq, text="🔍 " + t("buscar") + ":", font=("Segoe UI", 9), bg="white").pack(side="left")
        self.var_busqueda = tk.StringVar()
        entry = tk.Entry(frame_busq, textvariable=self.var_busqueda,
                         font=("Segoe UI", 10), width=35)
        entry.pack(side="left", padx=(6, 16), fill="x", expand=True, ipady=3)
        entry.bind("<KeyRelease>", lambda e: self._buscar())
        entry.focus()

        self.var_solo_con_stock = tk.BooleanVar(value=False)
        tk.Checkbutton(frame_busq, text=t("aux_solo_con_stock"),
                       variable=self.var_solo_con_stock, bg="white",
                       font=("Segoe UI", 9), cursor="hand2",
                       command=self._buscar).pack(side="left")

        # ── Filtros por Proveedor/Marca/Categoría ──────────────
        frame_filtros = tk.Frame(self, bg="white")
        frame_filtros.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 8))
        self.filtros = BarraFiltrosCatalogo(frame_filtros, on_cambio=self._buscar)
        self.filtros.pack(side="left")

        # ── Tabla ─────────────────────────────────────────────
        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 4))
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        cols   = ("codigo", "descripcion", "categoria", "precio_venta",
                  "precio_mayorista", "stock", "comprometido", "disponible")
        encabs = (t("col_codigo_mayus"), t("col_descripcion_mayus"), t("col_categoria_mayus"), t("col_p_venta"),
                  t("col_precio_mayor"), t("col_stock_mayus"), t("col_comprometido"), t("col_disponible"))
        anchos = (70, 230, 120, 110, 110, 80, 100, 90)

        style = ttk.Style()
        style.configure("Stock.Treeview", font=("Segoe UI", 9), rowheight=24)
        style.configure("Stock.Treeview.Heading", font=("Segoe UI", 9, "bold"))

        self.tabla = ttk.Treeview(contenedor, columns=cols, show="headings",
                                   style="Stock.Treeview", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, ancho in zip(cols, encabs, anchos):
            self.tabla.heading(col, text=enc,
                               command=lambda c=col: self._ordenar(c))
            self.tabla.column(col, width=ancho,
                              anchor="w" if col == "descripcion" else "center",
                              minwidth=50)

        # Resaltar en rojo las filas con stock bajo
        self.tabla.tag_configure("bajo_stock", background="#fef2f2", foreground="#991b1b")
        self.tabla.tag_configure("sin_stock",  background="#f3f4f6", foreground="#9ca3af")

        sb_y = ttk.Scrollbar(contenedor, orient="vertical",   command=self.tabla.yview)
        sb_x = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x.grid(row=1, column=0, sticky="ew")

        self._orden_col = None
        self._orden_asc = True

        # ── Pie: total de registros + cerrar ─────────────────
        pie = tk.Frame(self, bg="#f8f9fa", height=44)
        pie.grid(row=4, column=0, sticky="ew")
        pie.grid_propagate(False)

        self.lbl_total = tk.Label(pie, text="", font=("Segoe UI", 9),
                                   bg="#f8f9fa", fg="#374151")
        self.lbl_total.pack(side="left", padx=14, pady=12)

        tk.Label(pie,
                 text=t("aux_bajo_stock_sin_stock"),
                 font=("Segoe UI", 8), bg="#f8f9fa", fg="#6b7280"
                 ).pack(side="left", padx=10)

        tk.Button(pie, text=t("cerrar"), font=("Segoe UI", 9, "bold"),
                  bg="white", relief="solid", bd=1, padx=14, pady=4,
                  cursor="hand2", command=self.destroy
                  ).pack(side="right", padx=12, pady=8)

        self._todos_productos = []
        self._buscar()
        ajustar_tamaño_ventana(self, ancho_min=780, alto_min=500,
                               margen_alto=20, ancho_max=1200, alto_max=880)

    # ── Carga de datos ────────────────────────────────────────
    def _buscar(self):
        texto = self.var_busqueda.get().strip()
        solo_con_stock = self.var_solo_con_stock.get()
        proveedor_id, marca_id, categoria_id = self.filtros.obtener_ids()
        productos = listar_productos(solo_activos=True, texto_busqueda=texto,
                                      proveedor_id=proveedor_id, marca_id=marca_id,
                                      categoria_id=categoria_id)
        if solo_con_stock:
            productos = [p for p in productos
                         if not isinstance(p.get("disponible"), str)
                         and (p.get("disponible") or 0) > 0]
        self._todos_productos = productos
        self._poblar_tabla(productos)

    def _poblar_tabla(self, productos):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        for p in productos:
            stock        = p.get("stock", 0) or 0
            comprometido = p.get("comprometido", 0) or 0
            disponible   = p.get("disponible", stock - comprometido)
            stock_min    = p.get("stock_minimo", 0) or 0
            unidad       = p.get("unidad_medida", "Unidad")
            es_servicio  = p.get("tipo_producto") == "Servicio"

            if isinstance(disponible, str):
                tag = ()
            elif disponible <= 0:
                tag = ("sin_stock",)
            elif stock <= stock_min:
                tag = ("bajo_stock",)
            else:
                tag = ()

            if es_servicio:
                stock_txt = comp_txt = disp_txt = "—"
            else:
                stock_txt = formatear_cantidad(stock, unidad)
                comp_txt  = formatear_cantidad(comprometido, unidad)
                disp_txt  = (disponible if isinstance(disponible, str)
                             else formatear_cantidad(disponible, unidad))

            self.tabla.insert("", "end", values=(
                p["id"],
                p["nombre"],
                p.get("categoria") or "—",
                formatear_gs(p['precio_venta']),
                formatear_gs(p.get('precio_mayorista', 0)),
                stock_txt,
                comp_txt,
                disp_txt,
            ), tags=tag)

        n = len(productos)
        self.lbl_total.config(text=f"{n} producto{'s' if n != 1 else ''} encontrado{'s' if n != 1 else ''}")

    # ── Ordenamiento por columna ──────────────────────────────
    def _ordenar(self, col):
        if self._orden_col == col:
            self._orden_asc = not self._orden_asc
        else:
            self._orden_col = col
            self._orden_asc = True

        col_map = {
            "codigo": "id", "descripcion": "nombre", "categoria": "categoria",
            "precio_venta": "precio_venta", "precio_mayorista": "precio_mayorista",
            "stock": "stock", "comprometido": "comprometido", "disponible": "disponible",
        }
        clave = col_map.get(col, "nombre")
        reverse = not self._orden_asc

        productos = self._todos_productos[:]
        try:
            productos.sort(
                key=lambda p: (p.get(clave) or 0)
                              if isinstance(p.get(clave, ""), (int, float))
                              else str(p.get(clave) or "").lower(),
                reverse=reverse,
            )
        except Exception:
            pass

        solo_con_stock = self.var_solo_con_stock.get()
        if solo_con_stock:
            productos = [p for p in productos
                         if not isinstance(p.get("disponible"), str)
                         and (p.get("disponible") or 0) > 0]

        self._poblar_tabla(productos)
