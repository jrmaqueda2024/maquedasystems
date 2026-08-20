"""
ventana_compras.py
Pantalla del módulo Compras:
- PanelCompras: grilla con el historial de compras (Código, Fecha y Hora,
  Fecha Compra, Nro. Comprobante, Proveedor, Importe) + botón "Nueva Compra".
- VentanaNuevaCompra: carga de una compra nueva (código de producto + Enter,
  F2 Buscar, DEL Borrar Artículo), igual al flujo de Ventas, pero sumando
  stock en vez de restarlo.
- VentanaBuscarProductoCompra: buscador de productos (Código, Descripción,
  Precio Venta, Existencia), igual a la captura de referencia.
- VentanaPrecioCompra: popup que pide el precio de compra del producto
  elegido antes de agregarlo a la grilla.
"""
import datetime
import tkinter as tk
from tkinter import ttk, messagebox

from models_catalogo import listar_productos, buscar_producto_por_codigo, listar_proveedores, crear_proveedor
from models_compras import listar_compras, crear_compra, obtener_detalle_compra
from utilidades_ui import (
    habilitar_deseleccion_treeview,
    ajustar_tamaño_ventana, formatear_gs, formatear_cantidad,
    unidad_es_fraccionable, parsear_cantidad, forzar_mayusculas,
)
from traducciones import t
from widget_calendario import abrir_selector_fecha

AZUL_RIBBON = "#1d5fd6"
VERDE_IMPORTE = "#dcfce7"
GRIS_FONDO = "#f4f5f7"


# ============================================================
# PANEL PRINCIPAL: LISTADO DE COMPRAS
# ============================================================
class PanelCompras(tk.Frame):
    def __init__(self, parent, usuario_actual):
        super().__init__(parent, bg="white")
        self.usuario_actual = usuario_actual

        self._construir_barra_superior()
        self._construir_grilla()
        self._cargar_datos()

    # ---------------- BARRA SUPERIOR ----------------
    def _construir_barra_superior(self):
        barra = tk.Frame(self, bg="white")
        barra.pack(fill="x", padx=10, pady=(10, 5))

        tk.Button(barra, text=t("compras_nueva"), font=("Segoe UI", 9, "bold"),
                  bg=AZUL_RIBBON, fg="white", relief="flat", padx=12, pady=6,
                  cursor="hand2", command=self._abrir_nueva_compra).pack(side="left")

        tk.Label(barra, text=t("buscar") + ":", font=("Segoe UI", 9), bg="white").pack(side="right", padx=(0, 5))
        self.var_busqueda = tk.StringVar()
        entry = tk.Entry(barra, textvariable=self.var_busqueda, font=("Segoe UI", 9), width=25)
        entry.pack(side="right")
        entry.bind("<KeyRelease>", lambda e: self._cargar_datos())

    # ---------------- GRILLA ----------------
    def _construir_grilla(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        columnas = ("codigo", "fecha_hora", "fecha_compra", "nro_comprobante", "proveedor", "importe")
        encabezados = (t("col_codigo_mayus"), t("col_fecha_hora"), t("compras_fecha_compra"), t("compras_nro_comprobante"), t("col_proveedor_mayus"), t("col_importe_mayus"))
        anchos = (80, 150, 120, 160, 220, 120)

        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho,
                              anchor="w" if col == "proveedor" else "center")

        sb_y = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb_y.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_y_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_y_h.set)
        sb_y_h.grid(row=1, column=0, sticky="ew")

        self.tabla.bind("<Double-1>", lambda e: self._ver_detalle_seleccionado())

    def _cargar_datos(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        compras = listar_compras(texto_busqueda=self.var_busqueda.get())
        for c in compras:
            fecha_hora_fmt = _formatear_fecha_hora_iso(c["fecha_y_hora"])
            fecha_compra_fmt = _formatear_fecha_iso(c["fecha_compra"])
            self.tabla.insert("", "end", iid=str(c["id"]), values=(
                c["id"], fecha_hora_fmt, fecha_compra_fmt,
                c["nro_comprobante"] or "—", c["proveedor"], formatear_gs(c["importe"]),
            ))

    def _ver_detalle_seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        VentanaDetalleCompra(self, int(seleccion[0]))

    def _abrir_nueva_compra(self):
        VentanaNuevaCompra(self, self.usuario_actual, on_guardado=self._cargar_datos)


def _formatear_fecha_iso(fecha_iso: str) -> str:
    if not fecha_iso:
        return "—"
    try:
        return datetime.date.fromisoformat(fecha_iso[:10]).strftime("%d/%m/%Y")
    except ValueError:
        return fecha_iso


def _formatear_fecha_hora_iso(fecha_hora: str) -> str:
    if not fecha_hora:
        return "—"
    try:
        dt = datetime.datetime.fromisoformat(fecha_hora)
        return dt.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return fecha_hora


# ============================================================
# VER DETALLE DE UNA COMPRA (solo lectura)
# ============================================================
class VentanaDetalleCompra(tk.Toplevel):
    def __init__(self, parent, compra_id: int):
        super().__init__(parent)
        self.title(f"Compra Nro. {compra_id}")
        self.configure(bg="white")
        self.grab_set()
        self.resizable(True, True)
        self.minsize(560, 420)

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        detalle = obtener_detalle_compra(compra_id)
        if detalle is None:
            self.destroy()
            return

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text=f"Compra Nro. {compra_id}", font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

        info = tk.Frame(self, bg="white")
        info.grid(row=1, column=0, sticky="ew", padx=15, pady=10)
        datos = [
            ("Fecha y Hora:", _formatear_fecha_hora_iso(detalle["fecha_y_hora"])),
            ("Fecha Compra:", _formatear_fecha_iso(detalle["fecha_compra"])),
            ("Nro. Comprobante:", detalle["nro_comprobante"] or "—"),
            ("Proveedor:", detalle["proveedor"]),
        ]
        for i, (etq, val) in enumerate(datos):
            fila, col = divmod(i, 2)
            tk.Label(info, text=etq, font=("Segoe UI", 9, "bold"), bg="white").grid(
                row=fila, column=col * 2, sticky="w", padx=(0, 6), pady=3)
            tk.Label(info, text=val, font=("Segoe UI", 9), bg="white").grid(
                row=fila, column=col * 2 + 1, sticky="w", padx=(0, 20), pady=3)

        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=2, column=0, sticky="nsew", padx=15)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        columnas = ("codigo", "descripcion", "cantidad", "precio_unitario", "importe")
        encabezados = (t("col_codigo"), t("col_descripcion"), t("col_cantidad_cap"), t("col_precio_unit"), t("col_importe_cap"))
        tabla = ttk.Treeview(contenedor, columns=columnas, show="headings")
        habilitar_deseleccion_treeview(tabla)
        for col, enc in zip(columnas, encabezados):
            tabla.heading(col, text=enc)
            ancho = 240 if col == "descripcion" else 100
            tabla.column(col, width=ancho, anchor="w" if col == "descripcion" else "center")
        sb = ttk.Scrollbar(contenedor, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=sb.set)
        tabla.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        sb_h = ttk.Scrollbar(contenedor, orient="horizontal", command=tabla.xview)
        tabla.configure(xscrollcommand=sb_h.set)
        sb_h.grid(row=1, column=0, sticky="ew")

        for item in detalle["items"]:
            cantidad_txt = f"{item['cantidad']:g}"
            tabla.insert("", "end", values=(
                item["producto_id"] or "—", item["nombre"], cantidad_txt,
                formatear_gs(item["precio_unitario"]), formatear_gs(item["importe"]),
            ))

        pie = tk.Frame(self, bg=GRIS_FONDO)
        pie.grid(row=3, column=0, sticky="ew")
        tk.Label(pie, text=t("total_label"), font=("Segoe UI", 11, "bold"), bg=GRIS_FONDO).pack(
            side="left", padx=(15, 4), pady=10)
        tk.Label(pie, text=formatear_gs(detalle["importe"]), font=("Segoe UI", 14, "bold"),
                 bg=GRIS_FONDO, fg="#1d4ed8").pack(side="left", pady=10)
        tk.Button(pie, text=t("cerrar"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="right", padx=15, pady=10)

        ajustar_tamaño_ventana(self, ancho_min=560, alto_min=420)


# ============================================================
# NUEVA COMPRA
# ============================================================
class VentanaNuevaCompra(tk.Toplevel):
    def __init__(self, parent, usuario_actual, on_guardado=None):
        super().__init__(parent)
        self.usuario_actual = usuario_actual
        self.on_guardado = on_guardado
        self.items_compra = []  # cada item: {producto, cantidad, precio_unitario}
        self.proveedores = []
        self.proveedor_id_seleccionado = None
        self.fecha_compra = datetime.date.today()

        self.title("Compras")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()
        # Sin self.transient(parent): en Windows, una ventana
        # "transient" se trata como diálogo y pierde minimizar/
        # maximizar sin importar resizable().
        self.lift()
        self.focus_force()

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_titulo()
        self._construir_barra_codigo()
        self._construir_grilla()
        self._construir_pie()
        self._registrar_atajos()

        self.minsize(760, 560)
        ajustar_tamaño_ventana(self, ancho_min=760, alto_min=560)
        self.entry_codigo.focus()

    # ---------------- TÍTULO ----------------
    def _construir_titulo(self):
        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text=t("compras_titulo_barra"), font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

    # ---------------- CÓDIGO DEL PRODUCTO ----------------
    def _construir_barra_codigo(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=1, column=0, sticky="ew", padx=10, pady=(10, 5))

        barra = tk.Frame(contenedor, bg="white")
        barra.pack(fill="x")
        tk.Label(barra, text=t("compras_codigo_producto"), font=("Segoe UI", 10, "bold"),
                 bg="white").pack(side="left", padx=(0, 8))
        self.var_codigo = tk.StringVar()
        self.entry_codigo = tk.Entry(barra, textvariable=self.var_codigo, font=("Segoe UI", 11), width=26)
        self.entry_codigo.pack(side="left", padx=(0, 8))
        self.entry_codigo.bind("<Return>", lambda e: self._agregar_por_codigo())
        tk.Button(barra, text=t("ventas_agregar_producto"), font=("Segoe UI", 9, "bold"),
                  bg=AZUL_RIBBON, fg="white", command=self._agregar_por_codigo).pack(side="left")

        atajos = tk.Frame(contenedor, bg="white")
        atajos.pack(fill="x", pady=(8, 0))
        tk.Button(atajos, text=t("atajo_f2_buscar"), font=("Segoe UI", 8, "bold"),
                  bg="#0891b2", fg="white", relief="flat", padx=10, pady=6,
                  cursor="hand2", command=self._abrir_buscar_producto).pack(side="left", padx=(0, 6))
        tk.Button(atajos, text=t("atajo_del_borrar"), font=("Segoe UI", 8, "bold"),
                  bg="#6b7280", fg="white", relief="flat", padx=10, pady=6,
                  cursor="hand2", command=self._borrar_articulo_seleccionado).pack(side="left", padx=(0, 6))

    # ---------------- GRILLA DE ITEMS ----------------
    def _construir_grilla(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 5))
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        columnas = ("codigo", "descripcion", "cantidad", "precio_unitario", "importe")
        encabezados = ("Código", "Descripción", "Cant.", "Precio Compra", "Importe")

        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc in zip(columnas, encabezados):
            self.tabla.heading(col, text=enc)
            ancho = 260 if col == "descripcion" else 110
            self.tabla.column(col, width=ancho, anchor="w" if col == "descripcion" else "center")
        self.tabla.tag_configure("importe", background=VERDE_IMPORTE)

        sb_y = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb_y.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_y_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_y_h.set)
        sb_y_h.grid(row=1, column=0, sticky="ew")

        self.tabla.bind("<Double-1>", lambda e: self._editar_item_seleccionado())

    # ---------------- PIE: FECHA / COMPROBANTE / PROVEEDOR / TOTAL ----------------
    def _construir_pie(self):
        pie = tk.Frame(self, bg=GRIS_FONDO)
        pie.grid(row=3, column=0, sticky="ew")

        # IMPORTANTE: el Total, los botones y el contador de productos se
        # arman y empaquetan PRIMERO (antes que los campos de fecha/
        # comprobante/proveedor), para que siempre tengan garantizado su
        # espacio completo. Así el monto total NUNCA queda cortado o
        # invisible, sin importar cuántos dígitos tenga ni qué tan angosta
        # esté la ventana — el único bloque que cede espacio si hace falta
        # es "izquierda" (fecha/comprobante/proveedor), que se empaqueta
        # al final con expand=True.
        botones = tk.Frame(pie, bg=GRIS_FONDO)
        botones.pack(side="right", padx=15, pady=10)
        tk.Button(botones, text=t("compras_guardar_compra"), font=("Segoe UI", 10, "bold"), bg="white",
                  relief="solid", bd=1, command=self._guardar_compra).pack(side="right", padx=(8, 0))
        tk.Button(botones, text=t("cancelar_x"), font=("Segoe UI", 10, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="right")

        self.label_total = tk.Label(pie, text="Gs. 0", font=("Segoe UI", 20, "bold"),
                                     bg=GRIS_FONDO, fg="#1d4ed8")
        self.label_total.pack(side="right", padx=20, pady=10)

        self.label_contador = tk.Label(pie, text=t("compras_productos_en_compra").format(n=0),
                                        font=("Segoe UI", 9), bg=GRIS_FONDO, fg="#555")
        self.label_contador.pack(side="left", padx=(15, 15), pady=10)

        izquierda = tk.Frame(pie, bg=GRIS_FONDO)
        izquierda.pack(side="left", padx=(0, 15), pady=10, fill="x", expand=True)

        # Fecha (de hoy, informativa)
        tk.Label(izquierda, text=t("compras_fecha_label"), font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).grid(
            row=0, column=0, sticky="w", pady=3)
        tk.Label(izquierda, text=datetime.date.today().strftime("%d/%m/%Y"),
                 font=("Segoe UI", 9), bg=GRIS_FONDO).grid(row=0, column=1, sticky="w", padx=(6, 25), pady=3)

        # Fecha Compra (editable con calendario)
        tk.Label(izquierda, text=t("compras_fecha_compra_label"), font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).grid(
            row=0, column=2, sticky="w", pady=3)
        self.lbl_fecha_compra = tk.Label(izquierda, text=self.fecha_compra.strftime("%d/%m/%Y"),
                                          font=("Segoe UI", 9), bg="white", relief="solid", bd=1,
                                          width=12, cursor="hand2")
        self.lbl_fecha_compra.grid(row=0, column=3, sticky="w", padx=(6, 0), pady=3)
        self.lbl_fecha_compra.bind("<Button-1>", lambda e: self._elegir_fecha_compra())

        # N° Comprobante
        tk.Label(izquierda, text=t("compras_nro_comprobante_label"), font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).grid(
            row=1, column=0, sticky="w", pady=3)
        self.var_comprobante = tk.StringVar()
        entry_comp = tk.Entry(izquierda, textvariable=self.var_comprobante, font=("Segoe UI", 9), width=18)
        entry_comp.grid(row=1, column=1, sticky="w", padx=(6, 25), pady=3)
        forzar_mayusculas(entry_comp, self.var_comprobante)

        # Proveedor
        tk.Label(izquierda, text=t("compras_proveedor_label"), font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).grid(
            row=1, column=2, sticky="w", pady=3)
        frame_prov = tk.Frame(izquierda, bg=GRIS_FONDO)
        frame_prov.grid(row=1, column=3, sticky="w", padx=(6, 0), pady=3)
        self.var_proveedor = tk.StringVar()
        self.combo_proveedor = ttk.Combobox(frame_prov, textvariable=self.var_proveedor,
                                             font=("Segoe UI", 9), width=22, state="readonly")
        self.combo_proveedor.pack(side="left")
        self.combo_proveedor.bind("<<ComboboxSelected>>", lambda e: self._al_elegir_proveedor())
        tk.Button(frame_prov, text=t("compras_nuevo_proveedor"), font=("Segoe UI", 8, "bold"), bg="white",
                  relief="solid", bd=1, cursor="hand2",
                  command=self._abrir_nuevo_proveedor).pack(side="left", padx=(6, 0))
        self._cargar_proveedores()

    def _cargar_proveedores(self):
        self.proveedores = listar_proveedores()
        valores = ["(Sin proveedor)"] + [p["nombre"] for p in self.proveedores]
        self.combo_proveedor["values"] = valores
        self.combo_proveedor.current(0)
        self.proveedor_id_seleccionado = None

    def _al_elegir_proveedor(self):
        texto = self.var_proveedor.get()
        if texto == "(Sin proveedor)":
            self.proveedor_id_seleccionado = None
            return
        for p in self.proveedores:
            if p["nombre"] == texto:
                self.proveedor_id_seleccionado = p["id"]
                return
        self.proveedor_id_seleccionado = None

    def _abrir_nuevo_proveedor(self):
        VentanaProveedorRapido(self, on_creado=self._al_crear_proveedor)

    def _al_crear_proveedor(self, nombre_creado):
        self._cargar_proveedores()
        valores = list(self.combo_proveedor["values"])
        if nombre_creado in valores:
            self.combo_proveedor.set(nombre_creado)
            self._al_elegir_proveedor()

    def _elegir_fecha_compra(self):
        def al_elegir(fecha):
            self.fecha_compra = fecha
            self.lbl_fecha_compra.config(text=fecha.strftime("%d/%m/%Y"))
        abrir_selector_fecha(self, self.fecha_compra, al_elegir)

    # ---------------- ATAJOS ----------------
    def _registrar_atajos(self):
        self.bind("<F2>", lambda e: self._abrir_buscar_producto())
        self.bind("<Delete>", lambda e: self._borrar_articulo_seleccionado())

    # ---------------- AGREGAR PRODUCTO POR CÓDIGO ----------------
    def _agregar_por_codigo(self):
        codigo = self.var_codigo.get().strip()
        if not codigo:
            return
        producto = buscar_producto_por_codigo(codigo)
        if producto is None or not producto["activo"]:
            messagebox.showerror("No encontrado", f"No existe un producto activo con el código '{codigo}'.",
                                 parent=self)
            self.var_codigo.set("")
            return
        self.var_codigo.set("")
        self._pedir_precio_y_agregar(producto)

    def _abrir_buscar_producto(self):
        VentanaBuscarProductoCompra(self, on_seleccionado=self._pedir_precio_y_agregar)

    def _pedir_precio_y_agregar(self, producto):
        VentanaPrecioCompra(self, producto, on_confirmado=self._agregar_item)
        self.entry_codigo.focus()

    def _agregar_item(self, producto, precio_compra, cantidad=1):
        for item in self.items_compra:
            if item["producto"]["id"] == producto["id"]:
                item["cantidad"] += cantidad
                item["precio_unitario"] = precio_compra
                self._actualizar_vista()
                return
        self.items_compra.append({
            "producto": producto, "cantidad": cantidad, "precio_unitario": precio_compra,
        })
        self._actualizar_vista()

    def _borrar_articulo_seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        producto_id = int(seleccion[0])
        self.items_compra = [i for i in self.items_compra if i["producto"]["id"] != producto_id]
        self._actualizar_vista()

    def _editar_item_seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        producto_id = int(seleccion[0])
        item = next((i for i in self.items_compra if i["producto"]["id"] == producto_id), None)
        if item is None:
            return
        VentanaEditarItemCompra(self, item, on_confirmado=self._actualizar_vista)

    # ---------------- ACTUALIZAR GRILLA Y TOTALES ----------------
    def _actualizar_vista(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        total = 0
        for item in self.items_compra:
            p = item["producto"]
            importe = item["cantidad"] * item["precio_unitario"]
            total += importe
            unidad = p.get("unidad_medida", "Unidad")
            cantidad_txt = formatear_cantidad(item["cantidad"], unidad)
            self.tabla.insert("", "end", iid=str(p["id"]), values=(
                p["id"], p["nombre"], cantidad_txt,
                formatear_gs(item["precio_unitario"]), formatear_gs(importe),
            ), tags=("importe",))

        self.label_contador.config(text=f"{len(self.items_compra)} productos en la compra.")
        self.label_total.config(text=formatear_gs(total))

    # ---------------- GUARDAR ----------------
    def _guardar_compra(self):
        if not self.items_compra:
            messagebox.showwarning("Compra vacía", "Agrega al menos un producto antes de guardar.",
                                   parent=self)
            return

        items = [
            {
                "producto_id": item["producto"]["id"],
                "cantidad": item["cantidad"],
                "precio_unitario": item["precio_unitario"],
            }
            for item in self.items_compra
        ]

        exito, mensaje, compra_id = crear_compra(
            items=items,
            fecha_compra=self.fecha_compra.isoformat(),
            usuario_id=self.usuario_actual.get("id"),
            proveedor_id=self.proveedor_id_seleccionado,
            nro_comprobante=self.var_comprobante.get(),
        )
        if not exito:
            messagebox.showerror("No se pudo guardar", mensaje, parent=self)
            return

        messagebox.showinfo("Compra registrada", mensaje, parent=self)
        if self.on_guardado:
            self.on_guardado()
        self.destroy()


# ============================================================
# EDITAR CANTIDAD / PRECIO DE UN ITEM YA AGREGADO
# ============================================================
class VentanaEditarItemCompra(tk.Toplevel):
    def __init__(self, parent, item, on_confirmado):
        super().__init__(parent)
        self.item = item
        self.on_confirmado = on_confirmado
        producto = item["producto"]

        self.title("Editar Artículo")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()
        # Sin self.transient(parent): en Windows, una ventana
        # "transient" se trata como diálogo y pierde minimizar/
        # maximizar sin importar resizable().
        self.lift()
        self.focus_force()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=0, column=0, sticky="nsew")

        tk.Label(contenedor, text=producto["nombre"], font=("Segoe UI", 10, "bold"),
                 bg="white", wraplength=280).pack(padx=16, pady=(16, 10))

        cuerpo = tk.Frame(contenedor, bg="white")
        cuerpo.pack(padx=16, expand=True)

        unidad = producto.get("unidad_medida", "Unidad")
        texto_cant = self._texto_editable(item["cantidad"], unidad)

        tk.Label(cuerpo, text=t("cantidad_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=0, column=0, sticky="e", pady=6, padx=(0, 8))
        self.var_cantidad = tk.StringVar(value=texto_cant)
        entry_cant = tk.Entry(cuerpo, textvariable=self.var_cantidad, font=("Segoe UI", 10), width=14)
        entry_cant.grid(row=0, column=1, sticky="w", pady=6)

        tk.Label(cuerpo, text=t("compras_precio_de_compra"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=1, column=0, sticky="e", pady=6, padx=(0, 8))
        self.var_precio = tk.StringVar(value=str(int(round(item["precio_unitario"]))))
        entry_precio = tk.Entry(cuerpo, textvariable=self.var_precio, font=("Segoe UI", 10), width=14)
        entry_precio.grid(row=1, column=1, sticky="w", pady=6)

        botones = tk.Frame(contenedor, bg="white")
        botones.pack(pady=16)
        tk.Button(botones, text=t("aceptar_icono"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON, fg="white",
                  relief="flat", padx=14, pady=6, cursor="hand2", command=self._confirmar).pack(
                      side="left", padx=6)
        tk.Button(botones, text=t("cancelar_x"), font=("Segoe UI", 9, "bold"), bg="#f3f4f6",
                  relief="flat", padx=14, pady=6, cursor="hand2", command=self.destroy).pack(
                      side="left", padx=6)

        entry_cant.focus()
        entry_cant.selection_range(0, "end")
        self.bind("<Return>", lambda e: self._confirmar())
        self.bind("<Escape>", lambda e: self.destroy())
        self.minsize(320, 200)
        ajustar_tamaño_ventana(self, ancho_min=320, alto_min=200)

    def _texto_editable(self, valor, unidad):
        if unidad_es_fraccionable(unidad):
            s = f"{valor:.10f}".rstrip("0").rstrip(".")
            return s.replace(".", ",")
        return str(int(round(valor)))

    def _confirmar(self):
        try:
            cantidad = parsear_cantidad(self.var_cantidad.get())
            if cantidad <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Cantidad inválida", "Ingresa una cantidad numérica mayor a cero.",
                                 parent=self)
            return
        try:
            precio = parsear_cantidad(self.var_precio.get())
            if precio < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Precio inválido", "Ingresa un precio de compra numérico válido.",
                                 parent=self)
            return

        self.item["cantidad"] = cantidad
        self.item["precio_unitario"] = precio
        self.destroy()
        self.on_confirmado()


# ============================================================
# BUSCAR PRODUCTO (F2) — Código, Descripción, Precio Venta, Existencia
# ============================================================
class VentanaBuscarProductoCompra(tk.Toplevel):
    def __init__(self, parent, on_seleccionado):
        super().__init__(parent)
        self.on_seleccionado = on_seleccionado

        self.title("Buscar Producto")
        self.geometry("640x460")
        self.minsize(500, 360)
        self.resizable(True, True)
        self.configure(bg="white")
        self.grab_set()
        # Sin self.transient(parent): en Windows, una ventana
        # "transient" se trata como diálogo y pierde minimizar/
        # maximizar sin importar resizable().
        self.lift()
        self.focus_force()

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text=t("compras_buscar_producto_titulo"), font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

        frame_busqueda = tk.Frame(self, bg="white")
        frame_busqueda.grid(row=1, column=0, sticky="ew", padx=10, pady=8)
        tk.Label(frame_busqueda, text=t("buscar") + ":", font=("Segoe UI", 9), bg="white").pack(side="left")
        self.var_busqueda = tk.StringVar()
        entry = tk.Entry(frame_busqueda, textvariable=self.var_busqueda, font=("Segoe UI", 10), width=40)
        entry.pack(side="left", padx=8, fill="x", expand=True)
        entry.bind("<KeyRelease>", lambda e: self._buscar())
        entry.focus()

        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=2, column=0, sticky="nsew", padx=10)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        columnas = ("codigo", "descripcion", "precio_venta", "existencia")
        encabezados = ("CÓDIGO", "DESCRIPCIÓN", "PRECIO VENTA", "EXISTENCIA")
        anchos = (80, 300, 120, 120)

        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho, anchor="w" if col == "descripcion" else "center")

        sb_y = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb_y.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_y_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_y_h.set)
        sb_y_h.grid(row=1, column=0, sticky="ew")

        self.tabla.bind("<Double-1>", lambda e: self._confirmar_seleccion())
        self.bind("<Return>", lambda e: self._confirmar_seleccion())
        self.bind("<Escape>", lambda e: self.destroy())

        frame_botones = tk.Frame(self, bg="white", height=46)
        frame_botones.grid(row=3, column=0, sticky="ew")
        frame_botones.grid_propagate(False)
        tk.Button(frame_botones, text=t("compras_enter_agregar"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, width=16, command=self._confirmar_seleccion).pack(side="left",
                                                                                            padx=(10, 4), pady=8)
        tk.Button(frame_botones, text=t("compras_esc_cancelar"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, width=16, command=self.destroy).pack(side="left", pady=8)

        self.productos_por_id = {}
        self._buscar()

    def _buscar(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        productos = listar_productos(solo_activos=True, texto_busqueda=self.var_busqueda.get())
        self.productos_por_id = {}
        for p in productos:
            unidad = p.get("unidad_medida", "Unidad")
            stock = p.get("stock", 0)
            existencia_txt = formatear_cantidad(stock, unidad)
            self.tabla.insert("", "end", iid=str(p["id"]), values=(
                p["id"], p["nombre"], formatear_gs(p["precio_venta"]), existencia_txt,
            ))
            self.productos_por_id[str(p["id"])] = p

    def _confirmar_seleccion(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Selecciona un producto", "Elige un producto de la lista.", parent=self)
            return
        producto = self.productos_por_id[seleccion[0]]
        self.destroy()
        self.on_seleccionado(producto)


# ============================================================
# POPUP: PRECIO DE COMPRA
# ============================================================
class VentanaPrecioCompra(tk.Toplevel):
    def __init__(self, parent, producto, on_confirmado):
        super().__init__(parent)
        self.producto = producto
        self.on_confirmado = on_confirmado

        self.title(producto["nombre"])
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()
        # Sin self.transient(parent): en Windows, una ventana
        # "transient" se trata como diálogo y pierde minimizar/
        # maximizar sin importar resizable().
        self.lift()
        self.focus_force()

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=30)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text=producto["nombre"], font=("Segoe UI", 10, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=12, pady=5)

        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=1, column=0, sticky="nsew")
        cuerpo = tk.Frame(contenedor, bg="white")
        cuerpo.pack(padx=18, pady=16, expand=True)

        unidad = producto.get("unidad_medida", "Unidad")
        tk.Label(cuerpo, text=t("cantidad_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=0, column=0, sticky="w", pady=(0, 4))
        self.var_cantidad = tk.StringVar(value=self._texto_editable(1, unidad))
        self.entry_cantidad = tk.Entry(cuerpo, textvariable=self.var_cantidad,
                                        font=("Segoe UI", 12), width=20)
        self.entry_cantidad.grid(row=1, column=0, sticky="ew", pady=(0, 14), ipady=3)

        tk.Label(cuerpo, text=t("compras_precio_de_compra"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=2, column=0, sticky="w", pady=(0, 4))
        precio_sugerido = producto.get("precio_compra") or 0
        self.var_precio = tk.StringVar(value=str(int(round(precio_sugerido))) if precio_sugerido else "")
        self.entry_precio = tk.Entry(cuerpo, textvariable=self.var_precio, font=("Segoe UI", 12), width=20)
        self.entry_precio.grid(row=3, column=0, sticky="ew", pady=(0, 14), ipady=3)

        botones = tk.Frame(cuerpo, bg="white")
        botones.grid(row=4, column=0, sticky="ew")
        tk.Button(botones, text=t("aceptar_boton"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, cursor="hand2", command=self._confirmar).pack(
                      side="left", expand=True, fill="x", padx=(0, 4), ipady=4)
        tk.Button(botones, text=t("cancelar_x"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, cursor="hand2", command=self.destroy).pack(
                      side="left", expand=True, fill="x", padx=(4, 0), ipady=4)

        self.entry_cantidad.focus()
        self.entry_cantidad.selection_range(0, "end")
        self.bind("<Return>", lambda e: self._confirmar())
        self.bind("<Escape>", lambda e: self.destroy())
        self.minsize(300, 220)
        ajustar_tamaño_ventana(self, ancho_min=300, alto_min=220)

    def _texto_editable(self, valor, unidad):
        if unidad_es_fraccionable(unidad):
            s = f"{valor:.10f}".rstrip("0").rstrip(".")
            return s.replace(".", ",")
        return str(int(round(valor)))

    def _confirmar(self):
        try:
            cantidad = parsear_cantidad(self.var_cantidad.get())
            if cantidad <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Cantidad inválida", "Ingresa una cantidad numérica mayor a cero.",
                                 parent=self)
            return
        try:
            precio = parsear_cantidad(self.var_precio.get())
            if precio < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Precio inválido", "Ingresa un precio de compra numérico válido.",
                                 parent=self)
            return
        self.destroy()
        self.on_confirmado(self.producto, precio, cantidad)


# ============================================================
# ALTA RÁPIDA DE PROVEEDOR
# ============================================================
class VentanaProveedorRapido(tk.Toplevel):
    def __init__(self, parent, on_creado):
        super().__init__(parent)
        self.on_creado = on_creado

        self.title("Nuevo Proveedor")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()
        # Sin self.transient(parent): en Windows, una ventana
        # "transient" se trata como diálogo y pierde minimizar/
        # maximizar sin importar resizable().
        self.lift()
        self.focus_force()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=0, column=0, sticky="nsew")

        cuerpo = tk.Frame(contenedor, bg="white")
        cuerpo.pack(padx=18, pady=16, expand=True)

        self.var_nombre = tk.StringVar()
        self.var_telefono = tk.StringVar()
        self.var_ruc = tk.StringVar()

        campos = [("Nombre:", self.var_nombre, True), ("Teléfono:", self.var_telefono, False),
                  ("RUC:", self.var_ruc, False)]
        for i, (etq, var, mayus) in enumerate(campos):
            tk.Label(cuerpo, text=etq, font=("Segoe UI", 9, "bold"), bg="white").grid(
                row=i, column=0, sticky="e", pady=6, padx=(0, 8))
            entry = tk.Entry(cuerpo, textvariable=var, font=("Segoe UI", 9), width=24)
            entry.grid(row=i, column=1, sticky="w", pady=6)
            if mayus:
                forzar_mayusculas(entry, var)
                entry.focus()

        botones = tk.Frame(contenedor, bg="white")
        botones.pack(pady=(0, 16))
        tk.Button(botones, text=t("guardar_icono"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON, fg="white",
                  relief="flat", padx=14, pady=6, cursor="hand2", command=self._guardar).pack(
                      side="left", padx=6)
        tk.Button(botones, text=t("cancelar_x"), font=("Segoe UI", 9, "bold"), bg="#f3f4f6",
                  relief="flat", padx=14, pady=6, cursor="hand2", command=self.destroy).pack(
                      side="left", padx=6)

        self.bind("<Return>", lambda e: self._guardar())
        self.bind("<Escape>", lambda e: self.destroy())
        self.minsize(320, 200)
        ajustar_tamaño_ventana(self, ancho_min=320, alto_min=200)

    def _guardar(self):
        nombre = self.var_nombre.get().strip()
        if not nombre:
            messagebox.showerror("Falta el nombre", "El nombre del proveedor es obligatorio.", parent=self)
            return
        exito, mensaje = crear_proveedor(nombre, telefono=self.var_telefono.get(), ruc=self.var_ruc.get())
        if not exito:
            messagebox.showerror("No se pudo guardar", mensaje, parent=self)
            return
        self.destroy()
        self.on_creado(nombre)
