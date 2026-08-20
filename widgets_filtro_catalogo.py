"""
widgets_filtro_catalogo.py
Barra de filtros reutilizable por Proveedor, Marca y Categoría. Se usa en
las cuatro pantallas donde se busca un producto: Productos, Inventario,
Buscar Producto (F2 en Ventas) y Consultar Stock (F3 en Ventas).

Uso típico:

    self.filtros = BarraFiltrosCatalogo(parent, on_cambio=self._cargar_datos)
    self.filtros.pack(fill="x", padx=10, pady=(0, 5))
    ...
    proveedor_id, marca_id, categoria_id = self.filtros.obtener_ids()
    productos = listar_productos(texto_busqueda=texto, proveedor_id=proveedor_id,
                                  marca_id=marca_id, categoria_id=categoria_id)

on_cambio se dispara solo automáticamente cada vez que el usuario cambia
cualquiera de los tres combos o presiona "Limpiar filtros" — la pantalla
que use este widget es responsable de volver a leer obtener_ids() y
recargar su propia grilla en ese callback (igual que ya hace con la
búsqueda por texto).
"""
import tkinter as tk
from tkinter import ttk

from models_catalogo import listar_proveedores, listar_marcas, listar_categorias
from traducciones import t


class BarraFiltrosCatalogo(tk.Frame):
    def __init__(self, parent, on_cambio, bg="white"):
        super().__init__(parent, bg=bg)
        self.on_cambio = on_cambio
        self._bg = bg
        self._mapa_proveedores = {}
        self._mapa_marcas = {}
        self._mapa_categorias = {}
        self._construir()

    def _construir(self):
        opcion_todos = t("filtro_todos")

        tk.Label(self, text=t("filtro_proveedor"), font=("Segoe UI", 9),
                 bg=self._bg).pack(side="left", padx=(0, 4))
        self.var_proveedor = tk.StringVar(value=opcion_todos)
        self.combo_proveedor = ttk.Combobox(
            self, textvariable=self.var_proveedor, state="readonly",
            width=16, font=("Segoe UI", 9))
        self.combo_proveedor.pack(side="left", padx=(0, 14))
        self.combo_proveedor.bind("<<ComboboxSelected>>", lambda e: self.on_cambio())

        tk.Label(self, text=t("filtro_marca"), font=("Segoe UI", 9),
                 bg=self._bg).pack(side="left", padx=(0, 4))
        self.var_marca = tk.StringVar(value=opcion_todos)
        self.combo_marca = ttk.Combobox(
            self, textvariable=self.var_marca, state="readonly",
            width=14, font=("Segoe UI", 9))
        self.combo_marca.pack(side="left", padx=(0, 14))
        self.combo_marca.bind("<<ComboboxSelected>>", lambda e: self.on_cambio())

        tk.Label(self, text=t("filtro_categoria"), font=("Segoe UI", 9),
                 bg=self._bg).pack(side="left", padx=(0, 4))
        self.var_categoria = tk.StringVar(value=opcion_todos)
        self.combo_categoria = ttk.Combobox(
            self, textvariable=self.var_categoria, state="readonly",
            width=14, font=("Segoe UI", 9))
        self.combo_categoria.pack(side="left", padx=(0, 14))
        self.combo_categoria.bind("<<ComboboxSelected>>", lambda e: self.on_cambio())

        tk.Button(self, text=t("filtro_limpiar"), font=("Segoe UI", 8, "underline"),
                  bg=self._bg, fg="#6b7280", relief="flat", bd=0, cursor="hand2",
                  activebackground=self._bg, activeforeground="#374151",
                  command=self.limpiar).pack(side="left")

        self.actualizar_opciones()

    def actualizar_opciones(self):
        """Vuelve a leer proveedores/marcas/categorías de la base de
        datos (por si se agregó, editó o eliminó alguna desde que se
        abrió esta pantalla) y repuebla los tres combos, conservando la
        selección actual si el valor elegido todavía existe."""
        opcion_todos = t("filtro_todos")

        sel_prov = self.var_proveedor.get()
        self._mapa_proveedores = {p["nombre"]: p["id"] for p in listar_proveedores()}
        valores = [opcion_todos] + sorted(self._mapa_proveedores.keys())
        self.combo_proveedor["values"] = valores
        self.var_proveedor.set(sel_prov if sel_prov in valores else opcion_todos)

        sel_marca = self.var_marca.get()
        self._mapa_marcas = {m["nombre"]: m["id"] for m in listar_marcas()}
        valores = [opcion_todos] + sorted(self._mapa_marcas.keys())
        self.combo_marca["values"] = valores
        self.var_marca.set(sel_marca if sel_marca in valores else opcion_todos)

        sel_cat = self.var_categoria.get()
        self._mapa_categorias = {c["nombre"]: c["id"] for c in listar_categorias()}
        valores = [opcion_todos] + sorted(self._mapa_categorias.keys())
        self.combo_categoria["values"] = valores
        self.var_categoria.set(sel_cat if sel_cat in valores else opcion_todos)

    def obtener_ids(self):
        """Devuelve (proveedor_id, marca_id, categoria_id). Cada uno
        queda en None si el combo está en 'Todos' (o si la selección
        quedó obsoleta porque ese proveedor/marca/categoría se eliminó
        mientras la pantalla estaba abierta)."""
        proveedor_id = self._mapa_proveedores.get(self.var_proveedor.get())
        marca_id = self._mapa_marcas.get(self.var_marca.get())
        categoria_id = self._mapa_categorias.get(self.var_categoria.get())
        return proveedor_id, marca_id, categoria_id

    def hay_filtros_activos(self) -> bool:
        opcion_todos = t("filtro_todos")
        return (self.var_proveedor.get() != opcion_todos
                or self.var_marca.get() != opcion_todos
                or self.var_categoria.get() != opcion_todos)

    def limpiar(self):
        opcion_todos = t("filtro_todos")
        self.var_proveedor.set(opcion_todos)
        self.var_marca.set(opcion_todos)
        self.var_categoria.set(opcion_todos)
        self.on_cambio()
