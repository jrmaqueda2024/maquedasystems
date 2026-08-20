"""
ventana_gestion_catalogo.py
Ventanas de gestión de las listas auxiliares de Productos: Proveedores,
Marcas y Categorías. Replican el diseño visto en MetaVentas: una ventana
con un listado (Treeview), una barra de herramientas con Nuevo/Editar/
Eliminar, y un sub-diálogo modal para dar de alta o modificar cada
registro.

Se exponen tres clases, pensadas para abrirse como Toplevel desde el
panel de Productos:
    - VentanaProveedores
    - VentanaMarcas
    - VentanaCategorias

Todas aceptan un callback opcional `on_cambio` que se invoca cada vez
que se crea, edita o elimina un registro, para que la pantalla que las
abrió (ej. PanelProductos) pueda refrescar sus combos/caché si hace falta.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from models_catalogo import (
    listar_marcas, crear_marca, editar_marca, eliminar_marca,
    listar_categorias, crear_categoria, editar_categoria, eliminar_categoria,
    listar_proveedores, crear_proveedor, editar_proveedor, eliminar_proveedor,
)
from utilidades_ui import forzar_mayusculas, ajustar_tamaño_ventana, habilitar_deseleccion_treeview

AZUL_RIBBON = "#1d5fd6"
AZUL_OSCURO = "#163d8c"
GRIS_FONDO  = "#f4f5f7"
GRIS_BORDE  = "#e2e8f0"
BLANCO      = "#ffffff"
ROJO        = "#dc2626"
GRIS_TEXTO  = "#6b7280"


# ─────────────────────────────────────────────────────────────────────────
#  BASE GENÉRICA: listado + toolbar Nuevo/Editar/Eliminar
# ─────────────────────────────────────────────────────────────────────────
class _VentanaListaGestion(tk.Toplevel):
    """Clase base para las ventanas de listas simples (Marcas, Categorías).
    Las subclases solo necesitan definir título, funciones del modelo y,
    opcionalmente, personalizar el diálogo de alta/edición."""

    titulo_ventana = "Gestión"
    etiqueta_nueva = "Nuevo"
    columnas = ("nombre",)
    encabezados = ("NOMBRE",)

    def __init__(self, parent, on_cambio=None):
        super().__init__(parent)
        self.on_cambio = on_cambio
        self.item_sel_id = None

        self.title(self.titulo_ventana)
        self.configure(bg=GRIS_FONDO)
        self.grab_set()
        self.transient(parent)

        self._construir_barra_titulo()
        self._construir_toolbar()
        self._construir_grilla()
        self._cargar_datos()

        self.minsize(560, 380)
        ajustar_tamaño_ventana(self, ancho_min=560, alto_min=380)

    # ---------------- UI ----------------
    def _construir_barra_titulo(self):
        barra = tk.Frame(self, bg=AZUL_RIBBON, height=44)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        tk.Label(barra, text=self.titulo_ventana, font=("Segoe UI", 12, "bold"),
                  bg=AZUL_RIBBON, fg=BLANCO).pack(side="left", padx=16)

    def _construir_toolbar(self):
        barra = tk.Frame(self, bg=BLANCO, height=44)
        barra.pack(fill="x")
        barra.pack_propagate(False)

        tk.Button(barra, text=f"＋ {self.etiqueta_nueva}", font=("Segoe UI", 9, "bold"),
                   bg=AZUL_RIBBON, fg=BLANCO, relief="flat", bd=0, padx=12, pady=5,
                   cursor="hand2", command=self._nuevo).pack(side="left", padx=(12, 6), pady=7)
        tk.Button(barra, text="✏  Editar", font=("Segoe UI", 9), bg=BLANCO, fg="#1e293b",
                   relief="solid", bd=1, padx=12, pady=4, cursor="hand2",
                   command=self._editar).pack(side="left", padx=6, pady=7)
        tk.Button(barra, text="🗑  Eliminar", font=("Segoe UI", 9), bg=BLANCO, fg=ROJO,
                   relief="solid", bd=1, padx=12, pady=4, cursor="hand2",
                   command=self._eliminar).pack(side="left", padx=6, pady=7)

        tk.Label(barra, text="Buscar:", font=("Segoe UI", 9), bg=BLANCO).pack(side="left", padx=(20, 4))
        self.var_busqueda = tk.StringVar()
        entry_busqueda = tk.Entry(barra, textvariable=self.var_busqueda, font=("Segoe UI", 9), width=24)
        entry_busqueda.pack(side="left")
        entry_busqueda.bind("<KeyRelease>", lambda e: self._cargar_datos())

    def _construir_grilla(self):
        contenedor = tk.Frame(self, bg=BLANCO)
        contenedor.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        self.tabla = ttk.Treeview(contenedor, columns=self.columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, encabezado in zip(self.columnas, self.encabezados):
            self.tabla.heading(col, text=encabezado)
            self.tabla.column(col, width=140, anchor="w")

        sb_y = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb_y.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_y_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_y_h.set)
        sb_y_h.grid(row=1, column=0, sticky="ew")

        self.tabla.bind("<Double-1>", lambda e: self._editar())

    # ---------------- DATOS ----------------
    def _obtener_lista(self):
        raise NotImplementedError

    def _fila_de(self, item):
        raise NotImplementedError

    def _cargar_datos(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        self.items_por_id = {}

        texto = self.var_busqueda.get().strip().lower()
        for item in self._obtener_lista():
            if texto and texto not in item["nombre"].lower():
                continue
            self.tabla.insert("", "end", iid=str(item["id"]), values=self._fila_de(item))
            self.items_por_id[str(item["id"])] = item

    def _item_seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return None
        return self.items_por_id.get(seleccion[0])

    def _notificar_cambio(self):
        if self.on_cambio:
            self.on_cambio()

    # ---------------- ACCIONES ----------------
    def _nuevo(self):
        raise NotImplementedError

    def _editar(self):
        raise NotImplementedError

    def _eliminar(self):
        raise NotImplementedError


# ─────────────────────────────────────────────────────────────────────────
#  DIÁLOGO GENÉRICO "NOMBRE ÚNICO" (Marca / Categoría)
# ─────────────────────────────────────────────────────────────────────────
class _DialogoNombreUnico(tk.Toplevel):
    def __init__(self, parent, titulo, nombre_inicial="", on_guardar=None):
        super().__init__(parent)
        self.on_guardar = on_guardar
        self.title(titulo)
        self.configure(bg=GRIS_FONDO)
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=40)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        tk.Label(barra, text=titulo, font=("Segoe UI", 11, "bold"), bg=AZUL_RIBBON,
                  fg=BLANCO).pack(side="left", padx=14)

        cuerpo = tk.Frame(self, bg=GRIS_FONDO)
        cuerpo.pack(fill="both", expand=True, padx=20, pady=18)

        tk.Label(cuerpo, text="Nombre:", font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).grid(
            row=0, column=0, sticky="w", pady=(0, 6))
        self.var_nombre = tk.StringVar(value=nombre_inicial)
        entry = tk.Entry(cuerpo, textvariable=self.var_nombre, font=("Segoe UI", 10), width=32)
        entry.grid(row=1, column=0, sticky="ew")
        forzar_mayusculas(entry, self.var_nombre)
        entry.focus_set()
        entry.icursor("end")

        botones = tk.Frame(self, bg=GRIS_FONDO)
        botones.pack(fill="x", padx=20, pady=(0, 16))
        tk.Button(botones, text="💾  Guardar", font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                   fg=BLANCO, relief="flat", padx=14, pady=6, cursor="hand2",
                   command=self._guardar).pack(side="left")
        tk.Button(botones, text="✖  Cancelar", font=("Segoe UI", 9), bg=BLANCO, fg="#1e293b",
                   relief="solid", bd=1, padx=14, pady=5, cursor="hand2",
                   command=self.destroy).pack(side="left", padx=8)

        self.bind("<Return>", lambda e: self._guardar())
        self.bind("<Escape>", lambda e: self.destroy())

        ajustar_tamaño_ventana(self, ancho_min=340, alto_min=170)

    def _guardar(self):
        nombre = self.var_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Falta el nombre", "El nombre no puede estar vacío.", parent=self)
            return
        ok, mensaje = self.on_guardar(nombre)
        if ok:
            self.destroy()
        else:
            messagebox.showerror("No se pudo guardar", mensaje, parent=self)


# ─────────────────────────────────────────────────────────────────────────
#  MARCAS
# ─────────────────────────────────────────────────────────────────────────
class VentanaMarcas(_VentanaListaGestion):
    titulo_ventana = "Marcas"
    etiqueta_nueva = "Nueva Marca"
    columnas = ("codigo", "nombre")
    encabezados = ("CÓDIGO", "NOMBRE")

    def _obtener_lista(self):
        return listar_marcas()

    def _fila_de(self, item):
        return (item["id"], item["nombre"])

    def _nuevo(self):
        def guardar(nombre):
            ok, msg = crear_marca(nombre)
            if ok:
                self._cargar_datos()
                self._notificar_cambio()
            return ok, msg
        _DialogoNombreUnico(self, "Nueva Marca", on_guardar=guardar)

    def _editar(self):
        item = self._item_seleccionado()
        if item is None:
            messagebox.showwarning("Selecciona una marca", "Primero selecciona una marca de la lista.", parent=self)
            return

        def guardar(nombre):
            ok, msg = editar_marca(item["id"], nombre)
            if ok:
                self._cargar_datos()
                self._notificar_cambio()
            return ok, msg
        _DialogoNombreUnico(self, "Editar Marca", nombre_inicial=item["nombre"], on_guardar=guardar)

    def _eliminar(self):
        item = self._item_seleccionado()
        if item is None:
            messagebox.showwarning("Selecciona una marca", "Primero selecciona una marca de la lista.", parent=self)
            return
        if not messagebox.askyesno("Confirmar eliminación",
                                    f"¿Eliminar la marca '{item['nombre']}'?", parent=self):
            return
        ok, msg = eliminar_marca(item["id"])
        if ok:
            self._cargar_datos()
            self._notificar_cambio()
        else:
            messagebox.showerror("No se pudo eliminar", msg, parent=self)


# ─────────────────────────────────────────────────────────────────────────
#  CATEGORÍAS
# ─────────────────────────────────────────────────────────────────────────
class VentanaCategorias(_VentanaListaGestion):
    titulo_ventana = "Categorías"
    etiqueta_nueva = "Nueva Categoría"
    columnas = ("nombre",)
    encabezados = ("NOMBRE",)

    def _obtener_lista(self):
        return listar_categorias()

    def _fila_de(self, item):
        return (item["nombre"],)

    def _nuevo(self):
        def guardar(nombre):
            ok, msg = crear_categoria(nombre)
            if ok:
                self._cargar_datos()
                self._notificar_cambio()
            return ok, msg
        _DialogoNombreUnico(self, "Nueva Categoría", on_guardar=guardar)

    def _editar(self):
        item = self._item_seleccionado()
        if item is None:
            messagebox.showwarning("Selecciona una categoría", "Primero selecciona una categoría de la lista.", parent=self)
            return

        def guardar(nombre):
            ok, msg = editar_categoria(item["id"], nombre)
            if ok:
                self._cargar_datos()
                self._notificar_cambio()
            return ok, msg
        _DialogoNombreUnico(self, "Editar Categoría", nombre_inicial=item["nombre"], on_guardar=guardar)

    def _eliminar(self):
        item = self._item_seleccionado()
        if item is None:
            messagebox.showwarning("Selecciona una categoría", "Primero selecciona una categoría de la lista.", parent=self)
            return
        if not messagebox.askyesno("Confirmar eliminación",
                                    f"¿Eliminar la categoría '{item['nombre']}'?", parent=self):
            return
        ok, msg = eliminar_categoria(item["id"])
        if ok:
            self._cargar_datos()
            self._notificar_cambio()
        else:
            messagebox.showerror("No se pudo eliminar", msg, parent=self)


# ─────────────────────────────────────────────────────────────────────────
#  PROVEEDORES (formulario más completo: RUC, Dirección, Teléfono, Contacto)
# ─────────────────────────────────────────────────────────────────────────
class _DialogoProveedor(tk.Toplevel):
    def __init__(self, parent, titulo, proveedor=None, on_guardar=None):
        super().__init__(parent)
        self.on_guardar = on_guardar
        self.title(titulo)
        self.configure(bg=GRIS_FONDO)
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)
        p = proveedor or {}

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=40)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        tk.Label(barra, text=titulo, font=("Segoe UI", 11, "bold"), bg=AZUL_RIBBON,
                  fg=BLANCO).pack(side="left", padx=14)

        cuerpo = tk.Frame(self, bg=GRIS_FONDO)
        cuerpo.pack(fill="both", expand=True, padx=20, pady=18)
        cuerpo.grid_columnconfigure(0, weight=1)

        self.var_nombre = tk.StringVar(value=p.get("nombre", ""))
        self.var_ruc = tk.StringVar(value=p.get("ruc", ""))
        self.var_direccion = tk.StringVar(value=p.get("direccion", ""))
        self.var_telefono = tk.StringVar(value=p.get("telefono", ""))
        self.var_contacto = tk.StringVar(value=p.get("contacto", ""))

        campos = (
            ("Nombre:", self.var_nombre),
            ("RUC:", self.var_ruc),
            ("Dirección:", self.var_direccion),
            ("Teléfono:", self.var_telefono),
            ("Persona Contacto:", self.var_contacto),
        )
        primer_entry = None
        for i, (etiqueta, variable) in enumerate(campos):
            tk.Label(cuerpo, text=etiqueta, font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).grid(
                row=i * 2, column=0, sticky="w", pady=(8 if i else 0, 4))
            entry = tk.Entry(cuerpo, textvariable=variable, font=("Segoe UI", 10), width=36)
            entry.grid(row=i * 2 + 1, column=0, sticky="ew")
            # El teléfono no se fuerza a mayúsculas (puede llevar signo '+').
            if etiqueta != "Teléfono:":
                forzar_mayusculas(entry, variable)
            if primer_entry is None:
                primer_entry = entry

        primer_entry.focus_set()
        primer_entry.icursor("end")

        botones = tk.Frame(self, bg=GRIS_FONDO)
        botones.pack(fill="x", padx=20, pady=(4, 16))
        tk.Button(botones, text="💾  Guardar", font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                   fg=BLANCO, relief="flat", padx=14, pady=6, cursor="hand2",
                   command=self._guardar).pack(side="left")
        tk.Button(botones, text="✖  Cancelar", font=("Segoe UI", 9), bg=BLANCO, fg="#1e293b",
                   relief="solid", bd=1, padx=14, pady=5, cursor="hand2",
                   command=self.destroy).pack(side="left", padx=8)

        self.bind("<Return>", lambda e: self._guardar())
        self.bind("<Escape>", lambda e: self.destroy())

        ajustar_tamaño_ventana(self, ancho_min=380, alto_min=360)

    def _guardar(self):
        nombre = self.var_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Falta el nombre", "El nombre del proveedor es obligatorio.", parent=self)
            return
        ok, mensaje = self.on_guardar(
            nombre, self.var_telefono.get(), self.var_direccion.get(),
            self.var_ruc.get(), self.var_contacto.get(),
        )
        if ok:
            self.destroy()
        else:
            messagebox.showerror("No se pudo guardar", mensaje, parent=self)


class VentanaProveedores(_VentanaListaGestion):
    titulo_ventana = "Proveedores"
    etiqueta_nueva = "Nuevo Proveedor"
    columnas = ("nombre", "ruc", "direccion", "telefono", "contacto")
    encabezados = ("NOMBRE", "RUC", "DIRECCIÓN", "TELÉFONO", "CONTACTO")

    def _construir_grilla(self):
        super()._construir_grilla()
        self.tabla.column("nombre", width=180)
        self.tabla.column("ruc", width=100)
        self.tabla.column("direccion", width=180)
        self.tabla.column("telefono", width=110)
        self.tabla.column("contacto", width=140)

    def _obtener_lista(self):
        return listar_proveedores(texto_busqueda=self.var_busqueda.get())

    def _cargar_datos(self):
        # Proveedores filtra directamente en el modelo (incluye RUC y
        # contacto en la búsqueda), así que no repetimos el filtro por
        # nombre acá como hace la clase base.
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        self.items_por_id = {}
        for item in self._obtener_lista():
            self.tabla.insert("", "end", iid=str(item["id"]), values=self._fila_de(item))
            self.items_por_id[str(item["id"])] = item

    def _fila_de(self, item):
        return (item["nombre"], item.get("ruc", ""), item.get("direccion", ""),
                item.get("telefono", ""), item.get("contacto", ""))

    def _nuevo(self):
        def guardar(nombre, telefono, direccion, ruc, contacto):
            ok, msg = crear_proveedor(nombre, telefono, direccion, ruc, contacto)
            if ok:
                self._cargar_datos()
                self._notificar_cambio()
            return ok, msg
        _DialogoProveedor(self, "Nuevo Proveedor", on_guardar=guardar)

    def _editar(self):
        item = self._item_seleccionado()
        if item is None:
            messagebox.showwarning("Selecciona un proveedor", "Primero selecciona un proveedor de la lista.", parent=self)
            return

        def guardar(nombre, telefono, direccion, ruc, contacto):
            ok, msg = editar_proveedor(item["id"], nombre, telefono, direccion, ruc, contacto)
            if ok:
                self._cargar_datos()
                self._notificar_cambio()
            return ok, msg
        _DialogoProveedor(self, "Editar Proveedor", proveedor=item, on_guardar=guardar)

    def _eliminar(self):
        item = self._item_seleccionado()
        if item is None:
            messagebox.showwarning("Selecciona un proveedor", "Primero selecciona un proveedor de la lista.", parent=self)
            return
        if not messagebox.askyesno("Confirmar eliminación",
                                    f"¿Eliminar el proveedor '{item['nombre']}'?", parent=self):
            return
        ok, msg = eliminar_proveedor(item["id"])
        if ok:
            self._cargar_datos()
            self._notificar_cambio()
        else:
            messagebox.showerror("No se pudo eliminar", msg, parent=self)
