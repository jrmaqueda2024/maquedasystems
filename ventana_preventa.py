"""
ventana_preventa.py
Módulo Pre-Venta: lista de ventas "guardadas para después" (generadas con
F8 - Generar Preventa desde la ventana Cobrar), con acciones Modificar
(retomar la carga de artículos y, si se desea, finalizar el cobro) y
Eliminar.

Una pre-venta se guarda en las mismas tablas 'ventas'/'detalle_ventas'
marcada con es_pre_venta=1: no descuenta stock ni genera ningún
comprobante hasta que se cobra de verdad.
"""
import datetime
import tkinter as tk
from tkinter import ttk, messagebox

from models_ventas import (
    listar_preventas, obtener_detalle_preventa, actualizar_preventa, eliminar_preventa,
)
from models_catalogo import buscar_producto_por_codigo
from utilidades_ui import (
    habilitar_deseleccion_treeview,
    ajustar_tamaño_ventana, formatear_gs, formatear_cantidad,
    unidad_es_fraccionable, parsear_cantidad,
)
from traducciones import t

AZUL_RIBBON = "#1d5fd6"
VERDE_IMPORTE = "#dcfce7"
GRIS_FONDO = "#f4f5f7"


# ============================================================
# PANEL PRINCIPAL: LISTADO DE PRE-VENTAS
# ============================================================
class PanelPreVenta(tk.Frame):
    def __init__(self, parent, usuario_actual):
        super().__init__(parent, bg="white")
        self.usuario_actual = usuario_actual

        self._construir_barra_superior()
        self._construir_grilla()
        self._cargar_datos()

    # ---------------- BARRA SUPERIOR (Acciones) ----------------
    def _construir_barra_superior(self):
        barra = tk.Frame(self, bg="white")
        barra.pack(fill="x", padx=10, pady=(10, 5))

        self.btn_modificar = tk.Button(
            barra, text=t("preventa_modificar"), font=("Segoe UI", 9, "bold"),
            bg="#dbeafe", fg="#1e40af", relief="flat", padx=12, pady=6,
            cursor="hand2", activebackground="#bfdbfe", activeforeground="#1e40af",
            command=self._modificar_seleccionada,
        )
        self.btn_modificar.pack(side="left", padx=(0, 6))

        self.btn_eliminar = tk.Button(
            barra, text=t("eliminar_boton"), font=("Segoe UI", 9, "bold"),
            bg="#fee2e2", fg="#991b1b", relief="flat", padx=12, pady=6,
            cursor="hand2", activebackground="#fecaca", activeforeground="#991b1b",
            command=self._eliminar_seleccionada,
        )
        self.btn_eliminar.pack(side="left", padx=(0, 6))

        tk.Label(barra, text=t("buscar") + ":", font=("Segoe UI", 9), bg="white").pack(side="right", padx=(0, 5))
        self.var_busqueda = tk.StringVar()
        entry = tk.Entry(barra, textvariable=self.var_busqueda, font=("Segoe UI", 9), width=25)
        entry.pack(side="right")
        entry.bind("<KeyRelease>", lambda e: self._cargar_datos())

        tk.Button(barra, text="🔄", font=("Segoe UI", 10), bg="white", relief="flat",
                  cursor="hand2", command=self._cargar_datos).pack(side="right", padx=(0, 10))

    # ---------------- GRILLA ----------------
    def _construir_grilla(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        columnas = ("codigo", "fecha_hora", "cliente", "importe", "vendedor")
        encabezados = (t("col_codigo_mayus"), t("col_fecha_hora"), t("col_cliente_mayus"), t("col_importe_mayus"), t("col_vendedor_mayus"))
        anchos = (80, 160, 240, 130, 180)

        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho,
                              anchor="w" if col in ("cliente", "vendedor") else "center")

        sb_y = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb_y.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_y_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_y_h.set)
        sb_y_h.grid(row=1, column=0, sticky="ew")

        self.tabla.bind("<<TreeviewSelect>>", self._al_seleccionar)
        self.tabla.bind("<Double-1>", lambda e: self._modificar_seleccionada())

    def _cargar_datos(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        preventas = listar_preventas(busqueda=self.var_busqueda.get())
        for p in preventas:
            self.tabla.insert("", "end", iid=str(p["id"]), values=(
                p["id"], _formatear_fecha_hora_iso(p["fecha"]),
                p["cliente"], formatear_gs(p["total"]), p["vendedor"] or "—",
            ))

    def _al_seleccionar(self, event=None):
        pass

    def _modificar_seleccionada(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showinfo("Seleccioná una Pre-Venta",
                                "Primero hacé clic sobre una pre-venta de la lista "
                                "y después presioná \"Modificar\".", parent=self)
            return
        VentanaEditarPreVenta(self, int(seleccion[0]), self.usuario_actual, on_cambio=self._cargar_datos)

    def _eliminar_seleccionada(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showinfo("Seleccioná una Pre-Venta",
                                "Primero hacé clic sobre una pre-venta de la lista "
                                "y después presioná \"Eliminar\".", parent=self)
            return
        preventa_id = int(seleccion[0])
        if not messagebox.askyesno("Eliminar Pre-Venta",
                                   f"¿Eliminar la Pre-Venta Nro. {preventa_id}?\n\n"
                                   "Esta acción no se puede deshacer.", parent=self):
            return
        ok, msg = eliminar_preventa(preventa_id)
        if not ok:
            messagebox.showerror("No se pudo eliminar", msg, parent=self)
            return
        self._cargar_datos()


def _formatear_fecha_hora_iso(fecha_hora: str) -> str:
    if not fecha_hora:
        return "—"
    try:
        dt = datetime.datetime.fromisoformat(fecha_hora)
        return dt.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return fecha_hora


# ============================================================
# EDITAR / RETOMAR UNA PRE-VENTA
# ============================================================
class VentanaEditarPreVenta(tk.Toplevel):
    def __init__(self, parent, preventa_id: int, usuario_actual, on_cambio=None):
        super().__init__(parent)
        self.preventa_id = preventa_id
        self.usuario_actual = usuario_actual
        self.on_cambio = on_cambio
        self.items_venta = []  # cada item: {"producto": {...}, "cantidad":, "precio_unitario":}
        self.cliente_seleccionado = None

        detalle = obtener_detalle_preventa(preventa_id)
        if detalle is None:
            self.destroy()
            return
        self._cargar_items_desde_detalle(detalle)
        if detalle["cliente_id"]:
            from models_clientes import obtener_cliente
            self.cliente_seleccionado = obtener_cliente(detalle["cliente_id"])

        self.title(f"Pre-Venta Nro. {preventa_id}")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()
        self.transient(parent)

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_titulo()
        self._construir_barra_codigo()
        self._construir_grilla()
        self._construir_pie()
        self._registrar_atajos()

        self.minsize(760, 560)
        ajustar_tamaño_ventana(self, ancho_min=760, alto_min=560)
        self._actualizar_vista()
        self.entry_codigo.focus()

    def _cargar_items_desde_detalle(self, detalle):
        for item in detalle["items"]:
            if item["es_libre"]:
                producto = {"id": None, "nombre": item["nombre"], "es_libre": True,
                            "unidad_medida": "Unidad"}
            else:
                producto = {"id": item["producto_id"], "nombre": item["nombre"],
                            "unidad_medida": item["unidad_medida"]}
            self.items_venta.append({
                "producto": producto, "cantidad": item["cantidad"],
                "precio_unitario": item["precio_unitario"],
            })

    # ---------------- TÍTULO ----------------
    def _construir_titulo(self):
        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text=f"Pre-Venta Nro. {self.preventa_id}", font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

    # ---------------- CÓDIGO DEL PRODUCTO ----------------
    def _construir_barra_codigo(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=1, column=0, sticky="ew", padx=10, pady=(10, 5))

        barra = tk.Frame(contenedor, bg="white")
        barra.pack(fill="x")
        tk.Label(barra, text=t("preventa_codigo_producto"), font=("Segoe UI", 10, "bold"),
                 bg="white").pack(side="left", padx=(0, 8))
        self.var_codigo = tk.StringVar()
        self.entry_codigo = tk.Entry(barra, textvariable=self.var_codigo, font=("Segoe UI", 11), width=26)
        self.entry_codigo.pack(side="left", padx=(0, 8))
        self.entry_codigo.bind("<Return>", lambda e: self._agregar_por_codigo())
        tk.Button(barra, text=t("ventas_agregar_producto"), font=("Segoe UI", 9, "bold"),
                  bg=AZUL_RIBBON, fg="white", command=self._agregar_por_codigo).pack(side="left")

        atajos = tk.Frame(contenedor, bg="white")
        atajos.pack(fill="x", pady=(8, 0))
        tk.Button(atajos, text=t("atajo_f1_cliente"), font=("Segoe UI", 8, "bold"),
                  bg="#7c3aed", fg="white", relief="flat", padx=10, pady=6,
                  cursor="hand2", command=self._abrir_asignar_cliente).pack(side="left", padx=(0, 6))
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
        encabezados = (t("col_codigo"), t("col_descripcion"), t("col_cantidad_cap"), t("col_precio_unit"), t("col_importe_cap"))

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

    # ---------------- PIE: CLIENTE / CONDICIÓN / TOTAL / ACCIONES ----------------
    def _construir_pie(self):
        pie = tk.Frame(self, bg=GRIS_FONDO)
        pie.grid(row=3, column=0, sticky="ew")

        fila_superior = tk.Frame(pie, bg=GRIS_FONDO)
        fila_superior.pack(fill="x", pady=8, padx=10)

        self.label_contador = tk.Label(fila_superior, text="", font=("Segoe UI", 10), bg=GRIS_FONDO)
        self.label_contador.pack(side="left")

        botones = tk.Frame(fila_superior, bg=GRIS_FONDO)
        botones.pack(side="right")
        tk.Button(botones, text=t("preventa_cobrar_finalizar"), font=("Segoe UI", 10, "bold"),
                  bg="white", relief="solid", bd=1, command=self._cobrar).pack(side="right", padx=(8, 0))
        tk.Button(botones, text=t("guardar_cambios"), font=("Segoe UI", 10, "bold"),
                  bg="white", relief="solid", bd=1, command=self._guardar_cambios).pack(side="right", padx=(8, 0))
        tk.Button(botones, text=t("cancelar_x"), font=("Segoe UI", 10, "bold"),
                  bg="white", relief="solid", bd=1, command=self.destroy).pack(side="right")

        self.label_total = tk.Label(fila_superior, text="Gs. 0", font=("Segoe UI", 20, "bold"),
                                     bg=GRIS_FONDO, fg="#1d4ed8")
        self.label_total.pack(side="right", padx=20)

        fila_inferior = tk.Frame(pie, bg=GRIS_FONDO)
        fila_inferior.pack(fill="x", pady=(0, 8), padx=10)

        self.label_cliente = tk.Label(fila_inferior, text=f"{t('cliente_label')} {t('ocasional')}",
                                       font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO)
        self.label_cliente.pack(side="left")

    # ---------------- ATAJOS ----------------
    def _registrar_atajos(self):
        self.bind("<F1>", lambda e: self._abrir_asignar_cliente())
        self.bind("<F2>", lambda e: self._abrir_buscar_producto())
        self.bind("<Delete>", lambda e: self._borrar_articulo_seleccionado())

    # ---------------- CLIENTE ----------------
    def _abrir_asignar_cliente(self):
        from ventanas_auxiliares_venta import VentanaAsignarCliente
        VentanaAsignarCliente(self, on_seleccionado=self._al_asignar_cliente)

    def _al_asignar_cliente(self, cliente):
        self.cliente_seleccionado = cliente
        self._actualizar_vista()

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
        self._agregar_item(producto, 1)

    def _abrir_buscar_producto(self):
        from ventanas_auxiliares_venta import VentanaBuscarProducto
        VentanaBuscarProducto(self, on_seleccionado=lambda p: self._agregar_item(p, 1))

    def _agregar_item(self, producto, cantidad):
        for item in self.items_venta:
            if item["producto"].get("id") == producto.get("id") and producto.get("id") is not None:
                item["cantidad"] += cantidad
                self._actualizar_vista()
                return
        precio = producto.get("precio_venta", producto.get("precio_unitario", 0))
        self.items_venta.append({"producto": producto, "cantidad": cantidad, "precio_unitario": precio})
        self._actualizar_vista()
        self.entry_codigo.focus()

    def _borrar_articulo_seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        indice = int(seleccion[0])
        del self.items_venta[indice]
        self._actualizar_vista()

    def _editar_item_seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        indice = int(seleccion[0])
        item = self.items_venta[indice]
        VentanaEditarItemPreVenta(self, item, on_confirmado=self._actualizar_vista)

    # ---------------- ACTUALIZAR GRILLA Y TOTALES ----------------
    def _actualizar_vista(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        total = 0
        for i, item in enumerate(self.items_venta):
            p = item["producto"]
            importe = item["cantidad"] * item["precio_unitario"]
            total += importe
            unidad = p.get("unidad_medida", "Unidad")
            cantidad_txt = formatear_cantidad(item["cantidad"], unidad)
            codigo_txt = p.get("id") if p.get("id") else "Libre"
            self.tabla.insert("", "end", iid=str(i), values=(
                codigo_txt, p["nombre"], cantidad_txt,
                formatear_gs(item["precio_unitario"]), formatear_gs(importe),
            ), tags=("importe",))

        self.label_contador.config(text=f"{len(self.items_venta)} Productos en esta pre-venta.")
        self.label_total.config(text=formatear_gs(total))

        if self.cliente_seleccionado:
            self.label_cliente.config(text=f"Cliente: {self.cliente_seleccionado['nombre']}")
        else:
            self.label_cliente.config(text=f"{t('cliente_label')} {t('ocasional')}")

    # ---------------- ITEMS PARA GUARDAR / COBRAR ----------------
    def _items_para_guardar(self):
        items = []
        for item in self.items_venta:
            p = item["producto"]
            if p.get("es_libre") or p.get("id") is None:
                items.append({
                    "producto_id": None, "descripcion_libre": p["nombre"],
                    "cantidad": item["cantidad"], "precio_unitario": item["precio_unitario"],
                })
            else:
                items.append({
                    "producto_id": p["id"], "cantidad": item["cantidad"],
                    "precio_unitario": item["precio_unitario"],
                })
        return items

    # ---------------- GUARDAR CAMBIOS (sigue siendo pre-venta) ----------------
    def _guardar_cambios(self):
        if not self.items_venta:
            messagebox.showwarning("Pre-venta vacía", "Agrega al menos un producto antes de guardar.",
                                   parent=self)
            return
        cliente_id = self.cliente_seleccionado["id"] if self.cliente_seleccionado else None
        ok, msg = actualizar_preventa(self.preventa_id, self._items_para_guardar(), cliente_id)
        if not ok:
            messagebox.showerror("No se pudo guardar", msg, parent=self)
            return
        messagebox.showinfo("Pre-Venta actualizada", msg, parent=self)
        if self.on_cambio:
            self.on_cambio()
        self.destroy()

    # ---------------- COBRAR (finaliza como venta real) ----------------
    def _cobrar(self):
        if not self.items_venta:
            messagebox.showwarning("Pre-venta vacía", "Agrega al menos un producto antes de cobrar.",
                                   parent=self)
            return

        # Persistimos primero los cambios pendientes, para no perder
        # ediciones si el usuario cancela la ventana Cobrar.
        cliente_id = self.cliente_seleccionado["id"] if self.cliente_seleccionado else None
        ok, msg = actualizar_preventa(self.preventa_id, self._items_para_guardar(), cliente_id)
        if not ok:
            messagebox.showerror("No se pudo continuar", msg, parent=self)
            return

        from ventana_cobrar import VentanaCobrar
        ventana = VentanaCobrar(
            self, items_venta=self.items_venta, cliente=self.cliente_seleccionado,
            usuario_actual=self.usuario_actual, condicion_inicial="contado",
            on_venta_procesada=self._al_finalizar_venta,
        )
        ventana.bind("<Destroy>", lambda e: None)

    def _al_finalizar_venta(self):
        """Se llama luego de que VentanaCobrar procesó la venta con éxito:
        la pre-venta ya cumplió su función y se elimina (la venta real ya
        quedó registrada aparte, con su propio número)."""
        eliminar_preventa(self.preventa_id)
        if self.on_cambio:
            self.on_cambio()
        self.destroy()


# ============================================================
# EDITAR CANTIDAD / PRECIO DE UN ITEM YA AGREGADO
# ============================================================
class VentanaEditarItemPreVenta(tk.Toplevel):
    def __init__(self, parent, item, on_confirmado):
        super().__init__(parent)
        self.item = item
        self.on_confirmado = on_confirmado
        producto = item["producto"]

        self.title("Editar Artículo")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()
        self.transient(parent)

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

        tk.Label(cuerpo, text="Cantidad:", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=0, column=0, sticky="e", pady=6, padx=(0, 8))
        self.var_cantidad = tk.StringVar(value=texto_cant)
        entry_cant = tk.Entry(cuerpo, textvariable=self.var_cantidad, font=("Segoe UI", 10), width=14)
        entry_cant.grid(row=0, column=1, sticky="w", pady=6)

        tk.Label(cuerpo, text="Precio Unitario:", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=1, column=0, sticky="e", pady=6, padx=(0, 8))
        self.var_precio = tk.StringVar(value=str(int(round(item["precio_unitario"]))))
        entry_precio = tk.Entry(cuerpo, textvariable=self.var_precio, font=("Segoe UI", 10), width=14)
        entry_precio.grid(row=1, column=1, sticky="w", pady=6)

        botones = tk.Frame(contenedor, bg="white")
        botones.pack(pady=16)
        tk.Button(botones, text="✔ Aceptar", font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON, fg="white",
                  relief="flat", padx=14, pady=6, cursor="hand2", command=self._confirmar).pack(
                      side="left", padx=6)
        tk.Button(botones, text="✕ Cancelar", font=("Segoe UI", 9, "bold"), bg="#f3f4f6",
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
            messagebox.showerror("Precio inválido", "Ingresa un precio unitario numérico válido.",
                                 parent=self)
            return

        self.item["cantidad"] = cantidad
        self.item["precio_unitario"] = precio
        self.destroy()
        self.on_confirmado()
