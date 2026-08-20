"""
ventana_restaurante.py
Módulo Restaurante/Comedor: mapa de Mesas, Comandas (pedidos por mesa,
delivery, para llevar o mostrador), Platos con su Receta (costeo
automático a partir de los insumos del catálogo de Productos) y un
Dashboard con los reportes típicos de un restaurante (platos más
vendidos, margen por plato, costos vs ingresos, ventas por turno).

El personal y sus turnos de trabajo se administran en Rec. Humanos; acá
solo se registra qué usuario atendió cada comanda. La caja y la
facturación reutilizan el mismo motor de Ventas de siempre (cada
comanda cerrada genera una venta real, con su factura y su lugar en el
Resumen de Ventas y Reportes).
"""
import datetime
import tkinter as tk
from tkinter import ttk, messagebox

from models_restaurante import (
    CATEGORIAS_PLATO, TIPOS_COMANDA, ESTADOS_ITEM, TURNOS, ESTADOS_DELIVERY,
    listar_platos, obtener_plato, crear_plato, editar_plato, cambiar_estado_plato, eliminar_plato,
    listar_ingredientes_receta, agregar_ingrediente_receta, editar_cantidad_ingrediente,
    quitar_ingrediente_receta,
    listar_variantes_plato, agregar_variante_plato, editar_variante_plato, quitar_variante_plato,
    costo_receta_con_multiplicador,
    listar_mesas, crear_mesa, editar_mesa, cambiar_estado_mesa, eliminar_mesa,
    listar_repartidores, crear_repartidor, editar_repartidor, cambiar_estado_repartidor,
    abrir_comanda, obtener_comanda_activa_de_mesa, listar_comandas_activas, obtener_comanda_detalle,
    agregar_item_comanda, cambiar_cantidad_item, quitar_item_comanda, cambiar_estado_item,
    agregar_extra_item, quitar_extra_item,
    asignar_repartidor, cambiar_estado_delivery, listar_comandas_delivery_activas,
    verificar_insumos_suficientes, cerrar_comanda, cancelar_comanda,
    conteos_dashboard, platos_mas_vendidos, margen_por_plato, costos_vs_ingresos, ventas_por_turno,
)
from models_catalogo import listar_productos, crear_producto
from utilidades_ui import ajustar_tamaño_ventana, forzar_mayusculas, formatear_gs, formatear_cantidad, habilitar_deseleccion_treeview
from traducciones import t
from widget_calendario import abrir_selector_fecha

AZUL_RIBBON = "#1d5fd6"
GRIS_FONDO = "#f4f5f7"
VERDE = "#16a34a"
ROJO = "#dc2626"
NARANJA = "#d97706"
AMARILLO = "#ca8a04"
GRIS_TEXTO = "#6b7280"
GRIS_MEDIO = "#9ca3af"

COLOR_MESA = {
    "Libre": "#16a34a", "Ocupada": "#dc2626", "Reservada": "#ca8a04", "Para Limpiar": "#6b7280",
}
COLOR_ESTADO_ITEM = {
    "Pendiente": "#6b7280", "Preparando": "#d97706", "Listo": "#16a34a",
    "Entregado": "#1d5fd6", "Cancelado": "#dc2626",
}


def _campo_fecha(parent, variable: tk.StringVar):
    frame = tk.Frame(parent, bg=parent.cget("bg"))
    frame.pack(side="left", padx=(4, 0))
    tk.Entry(frame, textvariable=variable, font=("Segoe UI", 10), state="readonly", width=12).pack(side="left")
    tk.Button(frame, text="📅", font=("Segoe UI", 9), bg="white", relief="solid", bd=1, cursor="hand2",
              command=lambda: abrir_selector_fecha(
                  parent.winfo_toplevel(), datetime.date.today(),
                  lambda d: variable.set(d.isoformat()))).pack(side="left", padx=(4, 0))
    return frame


# ============================================================
# PANEL PRINCIPAL
# ============================================================
class PanelRestaurante(tk.Frame):
    def __init__(self, parent, usuario_actual):
        super().__init__(parent, bg="white")
        self.usuario_actual = usuario_actual

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_mesas = _TabMesas(self.notebook, self)
        self.tab_comandas = _TabComandasActivas(self.notebook, self)
        self.tab_delivery = _TabDelivery(self.notebook, self)
        self.tab_platos = _TabPlatos(self.notebook, self)
        self.tab_dashboard = _TabDashboard(self.notebook, self)

        self.notebook.add(self.tab_mesas, text=t("rest_tab_mesas"))
        self.notebook.add(self.tab_comandas, text=t("rest_tab_comandas"))
        self.notebook.add(self.tab_delivery, text=t("rest_tab_delivery"))
        self.notebook.add(self.tab_platos, text=t("rest_tab_platos"))
        self.notebook.add(self.tab_dashboard, text=t("rest_tab_dashboard"))

        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self.refrescar_todo())

    def refrescar_todo(self):
        self.tab_mesas.cargar()
        self.tab_comandas.cargar()
        self.tab_delivery.cargar()
        self.tab_dashboard.cargar()

    def abrir_comanda_ventana(self, comanda_id: int):
        VentanaComanda(self, self.usuario_actual, comanda_id, on_cambio=self.refrescar_todo)


# ============================================================
# PESTAÑA: MESAS
# ============================================================
class _TabMesas(tk.Frame):
    def __init__(self, parent, panel_padre: PanelRestaurante):
        super().__init__(parent, bg="white")
        self.panel_padre = panel_padre
        self._construir()
        self.cargar()

    def _construir(self):
        barra = tk.Frame(self, bg="white")
        barra.pack(fill="x", pady=(6, 10))
        tk.Button(barra, text=t("rest_nueva_mesa"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON, fg="white",
                  relief="flat", padx=12, pady=6, cursor="hand2", command=self._nueva_mesa).pack(side="left")
        tk.Button(barra, text=t("rest_nuevo_pedido"),
                  font=("Segoe UI", 9, "bold"), bg="#0891b2", fg="white", relief="flat",
                  padx=12, pady=6, cursor="hand2", command=self._nuevo_pedido_sin_mesa).pack(side="left", padx=(8, 0))

        leyenda = tk.Frame(barra, bg="white")
        leyenda.pack(side="right")
        for estado, color in COLOR_MESA.items():
            chip = tk.Frame(leyenda, bg=color, width=14, height=14)
            chip.pack(side="left", padx=(10, 3))
            chip.pack_propagate(False)
            tk.Label(leyenda, text=estado, font=("Segoe UI", 8), bg="white", fg=GRIS_TEXTO).pack(side="left")

        self.frame_mesas = tk.Frame(self, bg="white")
        self.frame_mesas.pack(fill="both", expand=True)

    def _nueva_mesa(self):
        VentanaFichaMesa(self, on_guardado=self.cargar)

    def _nuevo_pedido_sin_mesa(self):
        VentanaNuevoPedidoSinMesa(self, self.panel_padre.usuario_actual, on_creado=self._al_crear_pedido)

    def _al_crear_pedido(self, comanda_id):
        self.cargar()
        self.panel_padre.abrir_comanda_ventana(comanda_id)

    def _click_mesa(self, mesa: dict):
        if mesa["estado"] == "Libre":
            if not messagebox.askyesno("Abrir comanda", f"¿Abrir una comanda nueva para {mesa['numero']}?",
                                       parent=self):
                return
            ok, msg, comanda_id = abrir_comanda("Mesa", self.panel_padre.usuario_actual.get("id"),
                                                mesa_id=mesa["id"])
            if not ok:
                messagebox.showerror("No se pudo abrir", msg, parent=self)
                return
            self.cargar()
            self.panel_padre.abrir_comanda_ventana(comanda_id)
        elif mesa["estado"] == "Ocupada":
            comanda = obtener_comanda_activa_de_mesa(mesa["id"])
            if comanda is None:
                messagebox.showwarning("Sin comanda", "Esta mesa figura ocupada pero no tiene una comanda "
                                       "abierta. Marcala como Libre y volvé a intentar.", parent=self)
                return
            self.panel_padre.abrir_comanda_ventana(comanda["id"])
        elif mesa["estado"] == "Para Limpiar":
            if messagebox.askyesno("Mesa limpia", f"¿Marcar {mesa['numero']} como Libre?", parent=self):
                cambiar_estado_mesa(mesa["id"], "Libre")
                self.cargar()
        elif mesa["estado"] == "Reservada":
            opciones = ["Marcar Ocupada (abrir comanda)", "Liberar Reserva"]
            self._menu_mesa_reservada(mesa)

    def _menu_mesa_reservada(self, mesa):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Abrir comanda ahora", command=lambda: self._abrir_desde_reservada(mesa))
        menu.add_command(label="Liberar reserva", command=lambda: (cambiar_estado_mesa(mesa["id"], "Libre"),
                                                                    self.cargar()))
        try:
            menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        finally:
            menu.grab_release()

    def _abrir_desde_reservada(self, mesa):
        ok, msg, comanda_id = abrir_comanda("Mesa", self.panel_padre.usuario_actual.get("id"), mesa_id=mesa["id"])
        if not ok:
            messagebox.showerror("No se pudo abrir", msg, parent=self)
            return
        self.cargar()
        self.panel_padre.abrir_comanda_ventana(comanda_id)

    def _click_derecho_mesa(self, mesa):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="✏ Editar mesa", command=lambda: VentanaFichaMesa(self, mesa=mesa, on_guardado=self.cargar))
        if mesa["estado"] == "Libre":
            menu.add_command(label="🔖 Marcar Reservada", command=lambda: (cambiar_estado_mesa(mesa["id"], "Reservada"), self.cargar()))
            menu.add_command(label="🗑 Dar de baja", command=lambda: self._dar_de_baja(mesa))
        try:
            menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        finally:
            menu.grab_release()

    def _dar_de_baja(self, mesa):
        if messagebox.askyesno("Dar de baja", f"¿Dar de baja la mesa {mesa['numero']}?", parent=self):
            ok, msg = eliminar_mesa(mesa["id"])
            if not ok:
                messagebox.showerror("No se pudo", msg, parent=self)
            self.cargar()

    def cargar(self):
        for w in self.frame_mesas.winfo_children():
            w.destroy()
        mesas = listar_mesas()
        if not mesas:
            tk.Label(self.frame_mesas, text=t("rest_sin_mesas"),
                     font=("Segoe UI", 10), bg="white", fg=GRIS_TEXTO).pack(pady=30)
            return

        columnas = 5
        for i, mesa in enumerate(mesas):
            fila, col = divmod(i, columnas)
            color = COLOR_MESA.get(mesa["estado"], GRIS_MEDIO)
            tarjeta = tk.Frame(self.frame_mesas, bg=color, width=150, height=100, cursor="hand2")
            tarjeta.grid(row=fila, column=col, padx=8, pady=8)
            tarjeta.grid_propagate(False)
            tk.Label(tarjeta, text=mesa["numero"], font=("Segoe UI", 13, "bold"), bg=color, fg="white").pack(pady=(14, 2))
            tk.Label(tarjeta, text=mesa["estado"], font=("Segoe UI", 9), bg=color, fg="white").pack()
            tk.Label(tarjeta, text=f"👥 {mesa['capacidad']}", font=("Segoe UI", 8), bg=color, fg="white").pack(pady=(4, 0))
            for widget in (tarjeta, *tarjeta.winfo_children()):
                widget.bind("<Button-1>", lambda e, m=mesa: self._click_mesa(m))
                widget.bind("<Button-3>", lambda e, m=mesa: self._click_derecho_mesa(m))


# ============================================================
# PESTAÑA: COMANDAS ACTIVAS
# ============================================================
class _TabComandasActivas(tk.Frame):
    def __init__(self, parent, panel_padre: PanelRestaurante):
        super().__init__(parent, bg="white")
        self.panel_padre = panel_padre
        self._construir()
        self.cargar()

    def _construir(self):
        columnas = ("tipo", "mesa", "cliente", "mozo", "items", "total", "turno", "hora")
        encabezados = (t("rest_col_tipo"), t("col_mesa"), t("col_cliente_mayus2"), t("rest_col_mozo"), t("rest_col_items"), t("col_total_mayus2"), t("rest_col_turno"), t("rest_col_apertura"))
        anchos = (100, 90, 180, 150, 70, 110, 90, 130)
        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, pady=(6, 0))
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho, anchor="w" if col in ("mesa", "cliente", "mozo") else "center")
        sb = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        sb_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_h.set)
        sb_h.grid(row=1, column=0, sticky="ew")
        self.tabla.bind("<Double-1>", lambda e: self._abrir_seleccionada())

    def _abrir_seleccionada(self):
        seleccion = self.tabla.selection()
        if seleccion:
            self.panel_padre.abrir_comanda_ventana(int(seleccion[0]))

    def cargar(self):
        for f in self.tabla.get_children():
            self.tabla.delete(f)
        for c in listar_comandas_activas():
            hora = c["fecha_apertura"].split(" ")[-1][:5] if c["fecha_apertura"] else "—"
            self.tabla.insert("", "end", iid=str(c["id"]), values=(
                c["tipo"], c["mesa"], c["cliente"], c["mozo"], c["cantidad_items"],
                formatear_gs(c["total"]), c["turno"], hora,
            ))


# ============================================================
# PESTAÑA: DELIVERY
# ============================================================
class _TabDelivery(tk.Frame):
    def __init__(self, parent, panel_padre: PanelRestaurante):
        super().__init__(parent, bg="white")
        self.panel_padre = panel_padre
        self._construir()
        self.cargar()

    def _construir(self):
        barra = tk.Frame(self, bg="white")
        barra.pack(fill="x", pady=(6, 6))
        tk.Button(barra, text=t("rest_gestionar_repartidores"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                  fg="white", relief="flat", padx=12, pady=6, cursor="hand2",
                  command=self._gestionar_repartidores).pack(side="left")
        tk.Button(barra, text=t("rest_asignar_repartidor"), font=("Segoe UI", 9, "bold"), bg="#0891b2",
                  fg="white", relief="flat", padx=12, pady=6, cursor="hand2",
                  command=self._asignar_repartidor).pack(side="left", padx=(8, 0))
        tk.Button(barra, text=t("rest_cambiar_estado"), font=("Segoe UI", 9, "bold"), bg=NARANJA,
                  fg="white", relief="flat", padx=12, pady=6, cursor="hand2",
                  command=self._cambiar_estado).pack(side="left", padx=(8, 0))

        columnas = ("cliente", "direccion", "repartidor", "estado", "total", "hora")
        encabezados = (t("col_cliente_mayus2"), t("rest_col_direccion_entrega"), t("rest_col_repartidor"), t("col_estado_mayus"), t("col_total_mayus2"), t("rest_col_hora_pedido"))
        anchos = (160, 240, 150, 110, 110, 100)
        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho, anchor="w" if col in ("cliente", "direccion") else "center")
        sb = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        sb_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_h.set)
        sb_h.grid(row=1, column=0, sticky="ew")
        self.tabla.tag_configure("Preparando", foreground=NARANJA)
        self.tabla.tag_configure("En Camino", foreground="#0891b2")
        self.tabla.tag_configure("Entregado", foreground=VERDE)
        self.tabla.bind("<Double-1>", lambda e: self._abrir_comanda_seleccionada())

    def _abrir_comanda_seleccionada(self):
        seleccion = self.tabla.selection()
        if seleccion:
            self.panel_padre.abrir_comanda_ventana(int(seleccion[0]))

    def _gestionar_repartidores(self):
        VentanaGestionRepartidores(self)

    def _asignar_repartidor(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showinfo("Selecciona un pedido", "Elegí un pedido de delivery de la lista.", parent=self)
            return
        repartidores = listar_repartidores()
        if not repartidores:
            messagebox.showinfo("Sin repartidores", "Todavía no agregaste ningún repartidor. Usá "
                               "'Gestionar Repartidores' para crear uno.", parent=self)
            return
        VentanaElegirRepartidor(self, repartidores, on_elegido=self._al_elegir_repartidor,
                                comanda_id=int(seleccion[0]))

    def _al_elegir_repartidor(self, comanda_id, repartidor_id):
        asignar_repartidor(comanda_id, repartidor_id)
        self.cargar()

    def _cambiar_estado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showinfo("Selecciona un pedido", "Elegí un pedido de delivery de la lista.", parent=self)
            return
        comanda_id = int(seleccion[0])
        detalle = obtener_comanda_detalle(comanda_id)
        estado_actual = detalle.get("estado_delivery") or "Preparando"
        idx = ESTADOS_DELIVERY.index(estado_actual) if estado_actual in ESTADOS_DELIVERY else 0
        nuevo_estado = ESTADOS_DELIVERY[min(idx + 1, len(ESTADOS_DELIVERY) - 1)]
        cambiar_estado_delivery(comanda_id, nuevo_estado)
        self.cargar()

    def cargar(self):
        for f in self.tabla.get_children():
            self.tabla.delete(f)
        for d in listar_comandas_delivery_activas():
            hora = d["fecha_apertura"].split(" ")[-1][:5] if d["fecha_apertura"] else "—"
            self.tabla.insert("", "end", iid=str(d["id"]), tags=(d["estado_delivery"],), values=(
                d["cliente"], d["direccion_entrega"] or "—", d["repartidor"],
                d["estado_delivery"], formatear_gs(d["total"]), hora,
            ))


# ============================================================
# PESTAÑA: PLATOS
# ============================================================
class _TabPlatos(tk.Frame):
    def __init__(self, parent, panel_padre: PanelRestaurante):
        super().__init__(parent, bg="white")
        self.panel_padre = panel_padre
        self._construir()
        self.cargar()

    def _construir(self):
        barra = tk.Frame(self, bg="white")
        barra.pack(fill="x", pady=(6, 6))
        tk.Button(barra, text=t("rest_nuevo_plato"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON, fg="white",
                  relief="flat", padx=12, pady=6, cursor="hand2", command=self._nuevo_plato).pack(side="left")

        self.var_categoria = tk.StringVar(value="Todas")
        combo = ttk.Combobox(barra, textvariable=self.var_categoria, state="readonly",
                             values=["Todas"] + CATEGORIAS_PLATO, width=16)
        combo.pack(side="left", padx=(10, 0))
        combo.bind("<<ComboboxSelected>>", lambda e: self.cargar())

        self.var_incluir_inactivos = tk.BooleanVar(value=False)
        tk.Checkbutton(barra, text=t("rest_incluir_inactivos"), variable=self.var_incluir_inactivos,
                       bg="white", font=("Segoe UI", 9), command=self.cargar).pack(side="left", padx=(10, 0))

        self.var_busqueda = tk.StringVar()
        entry = tk.Entry(barra, textvariable=self.var_busqueda, font=("Segoe UI", 9), width=24)
        entry.pack(side="right")
        entry.bind("<KeyRelease>", lambda e: self.cargar())
        tk.Label(barra, text="🔍 " + t("buscar") + ":", font=("Segoe UI", 9), bg="white").pack(side="right", padx=(0, 6))

        columnas = ("nombre", "categoria", "precio", "costo", "margen", "margen_pct", "estado")
        encabezados = (t("rest_col_plato"), t("rest_col_categoria"), t("col_p_venta"), t("col_costo"), t("rest_col_margen"), t("rest_col_margen_pct"), t("col_estado_mayus"))
        anchos = (200, 130, 120, 110, 110, 90, 90)
        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho, anchor="w" if col in ("nombre", "categoria") else "center")
        sb = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        sb_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_h.set)
        sb_h.grid(row=1, column=0, sticky="ew")
        self.tabla.tag_configure("inactivo", foreground=GRIS_TEXTO)
        self.tabla.bind("<Double-1>", lambda e: self._abrir_seleccionado())

    def _nuevo_plato(self):
        VentanaFichaPlato(self, plato_id=None, on_cambio=self.cargar)

    def _abrir_seleccionado(self):
        seleccion = self.tabla.selection()
        if seleccion:
            VentanaFichaPlato(self, plato_id=int(seleccion[0]), on_cambio=self.cargar)

    def cargar(self):
        for f in self.tabla.get_children():
            self.tabla.delete(f)
        categoria = "" if self.var_categoria.get() == "Todas" else self.var_categoria.get()
        platos = listar_platos(solo_activos=not self.var_incluir_inactivos.get(),
                               categoria=categoria, busqueda=self.var_busqueda.get())
        for p in platos:
            tags = () if p["activo"] else ("inactivo",)
            self.tabla.insert("", "end", iid=str(p["id"]), tags=tags, values=(
                p["nombre"], p["categoria"], formatear_gs(p["precio_venta"]), formatear_gs(p["costo"]),
                formatear_gs(p["margen"]), f"{p['margen_pct']:.0f}%", "Activo" if p["activo"] else "Inactivo",
            ))


# ============================================================
# PESTAÑA: DASHBOARD
# ============================================================
class _TabDashboard(tk.Frame):
    def __init__(self, parent, panel_padre: PanelRestaurante):
        super().__init__(parent, bg="white")
        self.panel_padre = panel_padre
        self._construir()
        self.cargar()

    def _construir(self):
        self.frame_tarjetas = tk.Frame(self, bg="white")
        self.frame_tarjetas.pack(fill="x", pady=(6, 10))

        barra_filtro = tk.Frame(self, bg=GRIS_FONDO)
        barra_filtro.pack(fill="x", pady=(0, 10))
        interior = tk.Frame(barra_filtro, bg=GRIS_FONDO)
        interior.pack(fill="x", padx=10, pady=8)
        tk.Label(interior, text="Desde:", font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).pack(side="left")
        self.var_desde = tk.StringVar(value=datetime.date.today().replace(day=1).isoformat())
        _campo_fecha(interior, self.var_desde)
        tk.Label(interior, text="Hasta:", font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).pack(side="left", padx=(10, 0))
        self.var_hasta = tk.StringVar(value=datetime.date.today().isoformat())
        _campo_fecha(interior, self.var_hasta)
        tk.Button(interior, text="🔄 Actualizar", font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON, fg="white",
                  relief="flat", padx=10, pady=4, cursor="hand2", command=self.cargar).pack(side="left", padx=(10, 0))

        notebook_reportes = ttk.Notebook(self)
        notebook_reportes.pack(fill="both", expand=True)

        self.tab_mas_vendidos = self._crear_tabla_reporte(
            notebook_reportes, ("plato", "categoria", "cantidad", "ingreso"),
            ("PLATO", "CATEGORÍA", "CANT. VENDIDA", "INGRESO"))
        notebook_reportes.add(self.tab_mas_vendidos["frame"], text="Platos más vendidos")

        self.tab_margen = self._crear_tabla_reporte(
            notebook_reportes, ("plato", "cantidad", "ingreso", "costo", "margen", "margen_pct"),
            ("PLATO", "CANT.", "INGRESO", "COSTO", "MARGEN", "MARGEN %"))
        notebook_reportes.add(self.tab_margen["frame"], text="Margen por plato")

        self.tab_turno = self._crear_tabla_reporte(
            notebook_reportes, ("turno", "comandas", "ingreso"), ("TURNO", "COMANDAS", "INGRESO"))
        notebook_reportes.add(self.tab_turno["frame"], text="Ventas por turno")

    def _crear_tabla_reporte(self, parent, columnas, encabezados):
        frame = tk.Frame(parent, bg="white")
        contenedor = tk.Frame(frame, bg="white")
        contenedor.pack(fill="both", expand=True, padx=6, pady=6)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(tabla)
        for col, enc in zip(columnas, encabezados):
            tabla.heading(col, text=enc)
            tabla.column(col, width=130, anchor="center")
        sb = ttk.Scrollbar(contenedor, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=sb.set)
        tabla.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        sb_h = ttk.Scrollbar(contenedor, orient="horizontal", command=tabla.xview)
        tabla.configure(xscrollcommand=sb_h.set)
        sb_h.grid(row=1, column=0, sticky="ew")
        return {"frame": frame, "tabla": tabla}

    def _crear_tarjeta(self, titulo, valor, color):
        marco = tk.Frame(self.frame_tarjetas, bg=color, padx=16, pady=10)
        marco.pack(side="left", padx=(0, 10))
        tk.Label(marco, text=str(valor), font=("Segoe UI", 16, "bold"), bg=color, fg="white").pack(anchor="w")
        tk.Label(marco, text=titulo, font=("Segoe UI", 9), bg=color, fg="white").pack(anchor="w")

    def cargar(self):
        for w in self.frame_tarjetas.winfo_children():
            w.destroy()
        conteos = conteos_dashboard()
        self._crear_tarjeta("Mesas Libres", conteos["mesas_libres"], VERDE)
        self._crear_tarjeta("Mesas Ocupadas", conteos["mesas_ocupadas"], ROJO)
        self._crear_tarjeta("Comandas Abiertas", conteos["comandas_abiertas"], AZUL_RIBBON)
        self._crear_tarjeta("Comandas Cerradas Hoy", conteos["comandas_cerradas_hoy"], NARANJA)
        self._crear_tarjeta("Ingresos de Hoy", formatear_gs(conteos["ingresos_hoy"]), "#0f766e")

        desde, hasta = self.var_desde.get(), self.var_hasta.get()

        tabla = self.tab_mas_vendidos["tabla"]
        for f in tabla.get_children():
            tabla.delete(f)
        for p in platos_mas_vendidos(desde, hasta, limite=20):
            tabla.insert("", "end", values=(p["nombre"], p["categoria"], f"{p['cantidad_vendida']:g}",
                                            formatear_gs(p["ingreso"])))

        tabla = self.tab_margen["tabla"]
        for f in tabla.get_children():
            tabla.delete(f)
        for p in margen_por_plato(desde, hasta):
            tabla.insert("", "end", values=(p["nombre"], f"{p['cantidad_vendida']:g}", formatear_gs(p["ingreso"]),
                                            formatear_gs(p["costo"]), formatear_gs(p["margen"]),
                                            f"{p['margen_pct']:.0f}%"))

        tabla = self.tab_turno["tabla"]
        for f in tabla.get_children():
            tabla.delete(f)
        for t in ventas_por_turno(desde, hasta):
            tabla.insert("", "end", values=(t["turno"], t["cantidad_comandas"], formatear_gs(t["ingreso"])))


# ============================================================
# FICHA DE MESA (crear / editar)
# ============================================================
class VentanaFichaMesa(tk.Toplevel):
    def __init__(self, parent, mesa: dict = None, on_guardado=None):
        super().__init__(parent)
        self.mesa = mesa
        self.on_guardado = on_guardado

        self.title("Nueva Mesa" if mesa is None else "Editar Mesa")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        tk.Label(barra, text="🍽 " + (t("rest_nueva_mesa_titulo") if mesa is None else t("rest_editar_mesa_titulo")),
                 font=("Segoe UI", 11, "bold"), bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=16, pady=16)
        contenedor.grid_columnconfigure(1, weight=1)

        tk.Label(contenedor, text=t("rest_numero_nombre"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=0, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_numero = tk.StringVar(value=mesa["numero"] if mesa else "")
        entry_numero = tk.Entry(contenedor, textvariable=self.var_numero, font=("Segoe UI", 10))
        entry_numero.grid(row=0, column=1, sticky="ew", pady=4)
        forzar_mayusculas(entry_numero, self.var_numero)

        tk.Label(contenedor, text=t("rest_capacidad"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=1, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_capacidad = tk.StringVar(value=str(mesa["capacidad"]) if mesa else "4")
        tk.Entry(contenedor, textvariable=self.var_capacidad, font=("Segoe UI", 10), width=10).grid(
            row=1, column=1, sticky="w", pady=4)

        tk.Label(contenedor, text=t("rest_zona_sector"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=2, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_zona = tk.StringVar(value=mesa["zona"] if mesa else "")
        entry_zona = tk.Entry(contenedor, textvariable=self.var_zona, font=("Segoe UI", 10))
        entry_zona.grid(row=2, column=1, sticky="ew", pady=4)
        forzar_mayusculas(entry_zona, self.var_zona)

        botones = tk.Frame(self, bg="white")
        botones.pack(fill="x", padx=16, pady=(0, 16))
        tk.Button(botones, text=t("cancelar_x"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="left")
        tk.Button(botones, text=t("guardar_icono"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON, fg="white",
                  relief="flat", padx=14, cursor="hand2", command=self._guardar).pack(side="right")

        self.minsize(380, 260)
        ajustar_tamaño_ventana(self, ancho_min=380, alto_min=260)
        entry_numero.focus()

    def _guardar(self):
        try:
            capacidad = int(self.var_capacidad.get())
        except ValueError:
            messagebox.showwarning("Capacidad inválida", "Ingresa un número entero de personas.", parent=self)
            return
        if self.mesa is None:
            ok, msg = crear_mesa(self.var_numero.get(), capacidad, self.var_zona.get())
        else:
            ok, msg = editar_mesa(self.mesa["id"], self.var_numero.get(), capacidad, self.var_zona.get())
        if not ok:
            messagebox.showerror("No se pudo guardar", msg, parent=self)
            return
        if self.on_guardado:
            self.on_guardado()
        self.destroy()


# ============================================================
# NUEVO PEDIDO SIN MESA (Delivery / Para Llevar / Mostrador)
# ============================================================
class VentanaNuevoPedidoSinMesa(tk.Toplevel):
    def __init__(self, parent, usuario_actual, on_creado=None):
        super().__init__(parent)
        self.usuario_actual = usuario_actual
        self.on_creado = on_creado
        self.cliente_seleccionado = None

        self.title("Nuevo Pedido")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        tk.Label(barra, text=t("rest_titulo_nuevo_pedido"), font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=16, pady=16)
        contenedor.grid_columnconfigure(1, weight=1)

        tk.Label(contenedor, text=t("rest_tipo_pedido"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=0, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_tipo = tk.StringVar(value="Delivery")
        frame_tipo = tk.Frame(contenedor, bg="white")
        frame_tipo.grid(row=0, column=1, sticky="w", pady=4)
        for t in ("Delivery", "Para Llevar", "Mostrador"):
            tk.Radiobutton(frame_tipo, text=t, variable=self.var_tipo, value=t, bg="white",
                          font=("Segoe UI", 9), command=self._actualizar_visibilidad_direccion).pack(
                          side="left", padx=(0, 10))

        self.label_direccion = tk.Label(contenedor, text=t("rest_direccion_entrega_label"), font=("Segoe UI", 9, "bold"),
                                        bg="white")
        self.label_direccion.grid(row=1, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_direccion = tk.StringVar()
        self.entry_direccion = tk.Entry(contenedor, textvariable=self.var_direccion, font=("Segoe UI", 10))
        self.entry_direccion.grid(row=1, column=1, columnspan=2, sticky="ew", pady=4)

        tk.Label(contenedor, text=t("rest_cliente_opcional"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=2, column=0, sticky="e", pady=4, padx=(0, 8))
        self.label_cliente = tk.Label(contenedor, text=t("rest_consumidor_final"), font=("Segoe UI", 10),
                                      bg="white", fg=GRIS_TEXTO)
        self.label_cliente.grid(row=2, column=1, sticky="w", pady=4)
        tk.Button(contenedor, text=t("vet_buscar_cliente"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, cursor="hand2", command=self._buscar_cliente).grid(
                  row=2, column=2, padx=(8, 0))

        tk.Label(contenedor, text=t("observaciones_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=3, column=0, sticky="ne", pady=4, padx=(0, 8))
        self.texto_observaciones = tk.Text(contenedor, font=("Segoe UI", 9), height=3, relief="solid", bd=1)
        self.texto_observaciones.grid(row=3, column=1, columnspan=2, sticky="ew", pady=4)

        botones = tk.Frame(self, bg="white")
        botones.pack(fill="x", padx=16, pady=(0, 16))
        tk.Button(botones, text=t("cancelar_x"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="left")
        tk.Button(botones, text=t("rest_abrir_comanda"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON, fg="white",
                  relief="flat", padx=14, cursor="hand2", command=self._crear).pack(side="right")

        self.minsize(440, 300)
        ajustar_tamaño_ventana(self, ancho_min=440, alto_min=300)

    def _buscar_cliente(self):
        from ventanas_auxiliares_venta import VentanaAsignarCliente
        VentanaAsignarCliente(self, on_seleccionado=self._al_elegir_cliente)

    def _al_elegir_cliente(self, cliente):
        self.cliente_seleccionado = cliente
        self.label_cliente.config(text=cliente["nombre"] if cliente else "Consumidor Final")

    def _actualizar_visibilidad_direccion(self):
        if self.var_tipo.get() == "Delivery":
            self.label_direccion.grid()
            self.entry_direccion.grid()
        else:
            self.label_direccion.grid_remove()
            self.entry_direccion.grid_remove()

    def _crear(self):
        cliente_id = self.cliente_seleccionado["id"] if self.cliente_seleccionado else None
        ok, msg, comanda_id = abrir_comanda(
            self.var_tipo.get(), self.usuario_actual.get("id"), mesa_id=None, cliente_id=cliente_id,
            observaciones=self.texto_observaciones.get("1.0", "end").strip(),
            direccion_entrega=self.var_direccion.get() if self.var_tipo.get() == "Delivery" else "",
        )
        if not ok:
            messagebox.showerror("No se pudo abrir", msg, parent=self)
            return
        self.destroy()
        if self.on_creado:
            self.on_creado(comanda_id)



# ============================================================
# VENTANA DE LA COMANDA (agregar platos, estado de cocina, cobrar)
# ============================================================
class VentanaComanda(tk.Toplevel):
    def __init__(self, parent, usuario_actual, comanda_id: int, on_cambio=None):
        super().__init__(parent)
        self.usuario_actual = usuario_actual
        self.comanda_id = comanda_id
        self.on_cambio = on_cambio

        self.title("Comanda")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_titulo()
        self._construir_barra_agregar()
        self._construir_tabla()
        self._construir_pie()

        self.minsize(760, 560)
        ajustar_tamaño_ventana(self, ancho_min=760, alto_min=600,
                              alto_max=self.winfo_screenheight() - 60)
        self.cargar()

    def _construir_titulo(self):
        self.barra_titulo = tk.Frame(self, bg=AZUL_RIBBON, height=44)
        self.barra_titulo.grid(row=0, column=0, sticky="ew")
        self.barra_titulo.grid_propagate(False)
        self.label_titulo = tk.Label(self.barra_titulo, text="", font=("Segoe UI", 11, "bold"),
                                     bg=AZUL_RIBBON, fg="white", justify="left")
        self.label_titulo.pack(side="left", padx=15, pady=6, anchor="w")

    def _construir_barra_agregar(self):
        barra = tk.Frame(self, bg=GRIS_FONDO)
        barra.grid(row=1, column=0, sticky="ew")
        interior = tk.Frame(barra, bg=GRIS_FONDO)
        interior.pack(fill="x", padx=10, pady=8)
        tk.Button(interior, text=t("rest_agregar_plato"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                  fg="white", relief="flat", padx=10, pady=5, cursor="hand2",
                  command=self._agregar_plato).pack(side="left")
        tk.Button(interior, text=t("rest_cambiar_estado"), font=("Segoe UI", 9, "bold"), bg="#0891b2",
                  fg="white", relief="flat", padx=10, pady=5, cursor="hand2",
                  command=self._ciclar_estado_seleccionado).pack(side="left", padx=(8, 0))
        tk.Button(interior, text=t("rest_quitar"), font=("Segoe UI", 9, "bold"), bg="#6b7280",
                  fg="white", relief="flat", padx=10, pady=5, cursor="hand2",
                  command=self._quitar_item).pack(side="left", padx=(8, 0))
        tk.Button(interior, text=t("rest_personalizar"), font=("Segoe UI", 9, "bold"), bg="#7c3aed",
                  fg="white", relief="flat", padx=10, pady=5, cursor="hand2",
                  command=self._personalizar_item).pack(side="left", padx=(8, 0))

    def _construir_tabla(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=2, column=0, sticky="nsew", padx=10)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        columnas = ("plato", "tamaño", "cantidad", "precio", "importe", "estado", "tiempo", "obs")
        encabezados = (t("rest_col_plato"), t("rest_col_tamano"), t("col_cantidad"), t("rest_col_precio"), t("col_importe_mayus"), t("rest_col_estado_cocina"), t("rest_col_tiempo"), t("rest_col_observaciones"))
        anchos = (190, 90, 60, 100, 110, 130, 90, 170)
        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho, anchor="w" if col in ("plato", "obs") else "center")
        sb = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        sb_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_h.set)
        sb_h.grid(row=1, column=0, sticky="ew")
        self.tabla.bind("<Double-1>", lambda e: self._editar_cantidad_seleccionado())
        for estado, color in COLOR_ESTADO_ITEM.items():
            self.tabla.tag_configure(estado, foreground=color)
        self.tabla.tag_configure("excedido", background="#fef2f2")

    def _construir_pie(self):
        pie = tk.Frame(self, bg="white")
        pie.grid(row=3, column=0, sticky="ew", padx=16, pady=12)
        self.label_total = tk.Label(pie, text="Total: Gs. 0", font=("Segoe UI", 14, "bold"),
                                    bg="white", fg=AZUL_RIBBON)
        self.label_total.pack(side="left")

        frame_botones = tk.Frame(pie, bg="white")
        frame_botones.pack(side="right")
        tk.Button(frame_botones, text=t("rest_cancelar_comanda"), font=("Segoe UI", 9, "bold"), bg="white",
                  fg=ROJO, relief="solid", bd=1, padx=10, pady=6, cursor="hand2",
                  command=self._cancelar).pack(side="left", padx=(0, 8))
        tk.Button(frame_botones, text=t("cerrar_ventana"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, padx=10, pady=6, cursor="hand2",
                  command=self.destroy).pack(side="left", padx=(0, 8))
        self.boton_cobrar = tk.Button(frame_botones, text=t("rest_cerrar_cuenta_cobrar"),
                  font=("Segoe UI", 10, "bold"), bg=VERDE, fg="white", relief="flat",
                  padx=14, pady=8, cursor="hand2", command=self._cerrar_cuenta)
        self.boton_cobrar.pack(side="left")

    def _agregar_plato(self):
        VentanaSeleccionarPlato(self, on_seleccionado=self._al_elegir_plato)

    def _al_elegir_plato(self, plato, cantidad, observaciones, variante_id=None):
        ok, msg = agregar_item_comanda(self.comanda_id, plato["id"], cantidad, observaciones, variante_id)
        if not ok:
            messagebox.showerror("No se pudo agregar", msg, parent=self)
            return
        self.cargar()

    def _personalizar_item(self):
        item_id = self._item_seleccionado_id()
        if item_id is None:
            messagebox.showinfo("Selecciona un ítem", "Elegí un plato de la lista primero.", parent=self)
            return
        detalle = obtener_comanda_detalle(self.comanda_id)
        item = next((i for i in detalle["items"] if i["id"] == item_id), None)
        if item is None:
            return
        VentanaPersonalizarItem(self, item, on_cambio=self.cargar)

    def _item_seleccionado_id(self):
        seleccion = self.tabla.selection()
        return int(seleccion[0]) if seleccion else None

    def _ciclar_estado_seleccionado(self):
        item_id = self._item_seleccionado_id()
        if item_id is None:
            messagebox.showinfo("Selecciona un ítem", "Elegí un plato de la lista primero.", parent=self)
            return
        detalle = obtener_comanda_detalle(self.comanda_id)
        item = next((i for i in detalle["items"] if i["id"] == item_id), None)
        if item is None or item["estado_cocina"] == "Cancelado":
            return
        secuencia = ["Pendiente", "Preparando", "Listo", "Entregado"]
        idx = secuencia.index(item["estado_cocina"]) if item["estado_cocina"] in secuencia else 0
        nuevo_estado = secuencia[(idx + 1) % len(secuencia)]
        cambiar_estado_item(item_id, nuevo_estado)
        self.cargar()

    def _editar_cantidad_seleccionado(self):
        item_id = self._item_seleccionado_id()
        if item_id is None:
            return
        detalle = obtener_comanda_detalle(self.comanda_id)
        item = next((i for i in detalle["items"] if i["id"] == item_id), None)
        if item is None:
            return
        VentanaEditarCantidadItem(self, item, on_guardado=self.cargar)

    def _quitar_item(self):
        item_id = self._item_seleccionado_id()
        if item_id is None:
            messagebox.showinfo("Selecciona un ítem", "Elegí un plato de la lista primero.", parent=self)
            return
        if messagebox.askyesno("Quitar plato", "¿Quitar este plato de la comanda?", parent=self):
            quitar_item_comanda(item_id)
            self.cargar()

    def _cancelar(self):
        if not messagebox.askyesno("Cancelar comanda", "¿Cancelar por completo esta comanda? "
                                   "No se generará ninguna venta.", parent=self):
            return
        ok, msg = cancelar_comanda(self.comanda_id)
        if not ok:
            messagebox.showerror("No se pudo cancelar", msg, parent=self)
            return
        if self.on_cambio:
            self.on_cambio()
        self.destroy()

    def _cerrar_cuenta(self):
        detalle = obtener_comanda_detalle(self.comanda_id)
        if not detalle["items"] or detalle["total"] <= 0:
            messagebox.showinfo("Sin ítems", "Agregá al menos un plato antes de cobrar.", parent=self)
            return
        ok_stock, faltantes = verificar_insumos_suficientes(self.comanda_id)
        if not ok_stock:
            detalle_faltantes = "\n".join(
                f"• {f['nombre']}: faltan {f['necesario'] - f['disponible']:g} {f['unidad_medida'].lower()}"
                for f in faltantes
            )
            messagebox.showerror("Insumos insuficientes",
                                 f"No hay suficiente stock de insumos para preparar todo lo pedido:\n\n"
                                 f"{detalle_faltantes}", parent=self)
            return
        VentanaCobroComanda(self, self.usuario_actual, self.comanda_id, on_cobrado=self._al_cobrar)

    def _al_cobrar(self):
        if self.on_cambio:
            self.on_cambio()
        self.destroy()

    def cargar(self):
        detalle = obtener_comanda_detalle(self.comanda_id)
        if detalle is None:
            messagebox.showerror("No encontrada", "Esta comanda ya no existe.", parent=self)
            self.destroy()
            return
        if detalle["estado"] != "Abierta":
            messagebox.showinfo("Comanda cerrada", "Esta comanda ya fue cerrada o cancelada.", parent=self)
            self.destroy()
            return

        titulo = f"🧾 {detalle['tipo']}"
        if detalle["tipo"] == "Mesa":
            titulo += f" — {detalle['mesa']}"
        titulo += f"  |  Mozo/a: {detalle['mozo']}  |  Cliente: {detalle['cliente']}  |  Turno: {detalle['turno']}"
        self.label_titulo.config(text=titulo)
        self.title(f"Comanda — {detalle['tipo']}" + (f" {detalle['mesa']}" if detalle["tipo"] == "Mesa" else ""))

        for f in self.tabla.get_children():
            self.tabla.delete(f)
        for item in detalle["items"]:
            if item["minutos_preparando"] is not None:
                texto_tiempo = f"⏱ {item['minutos_preparando']:.0f} min"
                if item["excedido_tiempo"]:
                    texto_tiempo += " ⚠"
            else:
                texto_tiempo = "—"
            tags = [item["estado_cocina"]]
            if item["excedido_tiempo"]:
                tags.append("excedido")
            self.tabla.insert("", "end", iid=str(item["id"]), tags=tuple(tags), values=(
                item["plato"], item["variante_nombre"] or "—", f"{item['cantidad']:g}",
                formatear_gs(item["precio_unitario"]), formatear_gs(item["importe"]), item["estado_cocina"],
                texto_tiempo, item["observaciones"],
            ))
        self.label_total.config(text=f"Total: {formatear_gs(detalle['total'])}")


# ============================================================
# SELECCIONAR PLATO PARA AGREGAR A LA COMANDA
# ============================================================
class VentanaSeleccionarPlato(tk.Toplevel):
    def __init__(self, parent, on_seleccionado):
        super().__init__(parent)
        self.on_seleccionado = on_seleccionado
        self.plato_elegido = None

        self.title("Agregar Plato")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text=t("rest_agregar_plato_comanda"), font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

        barra_busqueda = tk.Frame(self, bg="white")
        barra_busqueda.grid(row=1, column=0, sticky="ew", padx=16, pady=(10, 6))
        self.var_busqueda = tk.StringVar()
        entry = tk.Entry(barra_busqueda, textvariable=self.var_busqueda, font=("Segoe UI", 10))
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<KeyRelease>", lambda e: self._cargar_lista())
        tk.Label(barra_busqueda, text="🔍", font=("Segoe UI", 11), bg="white").pack(side="left", padx=(6, 0))

        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=2, column=0, sticky="nsew", padx=16)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        columnas = ("nombre", "categoria", "precio")
        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc in zip(columnas, ("PLATO", "CATEGORÍA", "PRECIO")):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=180 if col == "nombre" else 120,
                              anchor="w" if col == "nombre" else "center")
        sb = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        sb_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_h.set)
        sb_h.grid(row=1, column=0, sticky="ew")
        self.tabla.bind("<Double-1>", lambda e: self._continuar())
        self.tabla.bind("<<TreeviewSelect>>", lambda e: self._actualizar_variantes())

        self.frame_variante = tk.Frame(self, bg="white")
        self.frame_variante.grid(row=3, column=0, sticky="ew", padx=16, pady=(6, 0))
        self.label_variante = tk.Label(self.frame_variante, text=t("rest_tamano_label"), font=("Segoe UI", 9, "bold"),
                                       bg="white")
        self.var_variante = tk.StringVar()
        self.combo_variante = ttk.Combobox(self.frame_variante, textvariable=self.var_variante,
                                           state="readonly", width=30)
        self.combo_variante.bind("<<ComboboxSelected>>", lambda e: self._actualizar_precio_mostrado())
        self.label_precio_variante = tk.Label(self.frame_variante, text="", font=("Segoe UI", 9, "bold"),
                                              bg="white", fg=AZUL_RIBBON)

        frame_cantidad = tk.Frame(self, bg="white")
        frame_cantidad.grid(row=4, column=0, sticky="ew", padx=16, pady=(10, 4))
        tk.Label(frame_cantidad, text=t("cantidad_label"), font=("Segoe UI", 9, "bold"), bg="white").pack(side="left")
        self.var_cantidad = tk.StringVar(value="1")
        tk.Entry(frame_cantidad, textvariable=self.var_cantidad, font=("Segoe UI", 10), width=8).pack(
            side="left", padx=(6, 16))
        tk.Label(frame_cantidad, text=t("observaciones_label"), font=("Segoe UI", 9, "bold"), bg="white").pack(side="left")
        self.var_observaciones = tk.StringVar()
        tk.Entry(frame_cantidad, textvariable=self.var_observaciones, font=("Segoe UI", 10)).pack(
            side="left", fill="x", expand=True, padx=(6, 0))

        botones = tk.Frame(self, bg="white")
        botones.grid(row=5, column=0, sticky="ew", padx=16, pady=(6, 16))
        tk.Button(botones, text=t("cancelar_x"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="left")
        tk.Button(botones, text=t("rest_agregar_boton"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON, fg="white",
                  relief="flat", padx=14, cursor="hand2", command=self._continuar).pack(side="right")

        self.minsize(480, 520)
        ajustar_tamaño_ventana(self, ancho_min=480, alto_min=560)
        entry.focus()
        self._cargar_lista()

    def _cargar_lista(self):
        for f in self.tabla.get_children():
            self.tabla.delete(f)
        self._platos = {p["id"]: p for p in listar_platos(solo_activos=True, busqueda=self.var_busqueda.get())}
        for p in self._platos.values():
            self.tabla.insert("", "end", iid=str(p["id"]), values=(p["nombre"], p["categoria"],
                                                                    formatear_gs(p["precio_venta"])))
        self._actualizar_variantes()

    def _actualizar_variantes(self):
        seleccion = self.tabla.selection()
        self._variantes_actuales = {}
        if not seleccion:
            self.label_variante.pack_forget()
            self.combo_variante.pack_forget()
            self.label_precio_variante.pack_forget()
            return
        plato = self._platos[int(seleccion[0])]
        variantes = listar_variantes_plato(plato["id"])
        if not variantes:
            self.label_variante.pack_forget()
            self.combo_variante.pack_forget()
            self.label_precio_variante.pack_forget()
            return
        self._variantes_actuales = {v["nombre"]: v for v in variantes}
        self.combo_variante["values"] = list(self._variantes_actuales.keys())
        self.label_variante.pack(side="left")
        self.combo_variante.pack(side="left", padx=(6, 10))
        self.label_precio_variante.pack(side="left")
        self.combo_variante.current(0)
        self._actualizar_precio_mostrado()

    def _actualizar_precio_mostrado(self):
        variante = self._variantes_actuales.get(self.var_variante.get())
        if variante:
            self.label_precio_variante.config(text=formatear_gs(variante["precio"]))

    def _continuar(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showinfo("Selecciona un plato", "Elegí un plato de la lista.", parent=self)
            return
        plato = self._platos[int(seleccion[0])]
        try:
            cantidad = float(self.var_cantidad.get().replace(",", "."))
            if cantidad <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Cantidad inválida", "Ingresa una cantidad mayor a 0.", parent=self)
            return
        variante_id = None
        if self._variantes_actuales:
            variante = self._variantes_actuales.get(self.var_variante.get())
            if variante is None:
                messagebox.showinfo("Elegí un tamaño", "Este plato tiene tamaños disponibles; elegí uno.",
                                   parent=self)
                return
            variante_id = variante["id"]
        self.destroy()
        self.on_seleccionado(plato, cantidad, self.var_observaciones.get(), variante_id)


# ============================================================
# EDITAR CANTIDAD DE UN ÍTEM DE LA COMANDA
# ============================================================
class VentanaEditarCantidadItem(tk.Toplevel):
    def __init__(self, parent, item: dict, on_guardado=None):
        super().__init__(parent)
        self.item = item
        self.on_guardado = on_guardado

        self.title("Editar Cantidad")
        self.configure(bg="white")
        self.grab_set()

        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(padx=20, pady=20)
        tk.Label(contenedor, text=item["plato"], font=("Segoe UI", 11, "bold"), bg="white").pack(anchor="w")
        fila = tk.Frame(contenedor, bg="white")
        fila.pack(pady=(10, 0))
        tk.Label(fila, text=t("cantidad_label"), font=("Segoe UI", 9, "bold"), bg="white").pack(side="left")
        self.var_cantidad = tk.StringVar(value=f"{item['cantidad']:g}")
        entry = tk.Entry(fila, textvariable=self.var_cantidad, font=("Segoe UI", 10), width=10)
        entry.pack(side="left", padx=(6, 0))
        entry.bind("<Return>", lambda e: self._guardar())

        botones = tk.Frame(contenedor, bg="white")
        botones.pack(pady=(16, 0), fill="x")
        tk.Button(botones, text=t("cancelar_x"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="left")
        tk.Button(botones, text=t("guardar_icono"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON, fg="white",
                  relief="flat", padx=14, cursor="hand2", command=self._guardar).pack(side="right")
        entry.focus()
        entry.select_range(0, "end")

    def _guardar(self):
        try:
            cantidad = float(self.var_cantidad.get().replace(",", "."))
        except ValueError:
            messagebox.showwarning("Cantidad inválida", "Ingresa un número.", parent=self)
            return
        cambiar_cantidad_item(self.item["id"], cantidad)
        if self.on_guardado:
            self.on_guardado()
        self.destroy()


# ============================================================
# COBRAR LA COMANDA (cierra cuenta y genera la venta real)
# ============================================================
class VentanaCobroComanda(tk.Toplevel):
    def __init__(self, parent, usuario_actual, comanda_id: int, on_cobrado=None):
        super().__init__(parent)
        self.usuario_actual = usuario_actual
        self.comanda_id = comanda_id
        self.on_cobrado = on_cobrado
        self.cliente_seleccionado = None

        detalle = obtener_comanda_detalle(comanda_id)
        self.detalle = detalle

        self.title("Cerrar Cuenta")
        self.configure(bg="white")
        self.grab_set()

        barra = tk.Frame(self, bg=VERDE, height=34)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        tk.Label(barra, text=t("rest_cerrar_cuenta_cobrar"), font=("Segoe UI", 11, "bold"),
                 bg=VERDE, fg="white").pack(side="left", padx=15, pady=6)

        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=18, pady=16)

        tk.Label(contenedor, text=f"Total a cobrar: {formatear_gs(detalle['total'])}",
                 font=("Segoe UI", 14, "bold"), bg="white", fg=AZUL_RIBBON).pack(anchor="w", pady=(0, 12))

        fila_cliente = tk.Frame(contenedor, bg="white")
        fila_cliente.pack(fill="x", pady=(0, 10))
        tk.Label(fila_cliente, text=t("rest_cliente_label"), font=("Segoe UI", 9, "bold"), bg="white").pack(side="left")
        self.label_cliente = tk.Label(fila_cliente, text=detalle["cliente"], font=("Segoe UI", 10),
                                      bg="white", fg=GRIS_TEXTO)
        self.label_cliente.pack(side="left", padx=(6, 10))
        tk.Button(fila_cliente, text=t("rest_cambiar_cliente"), font=("Segoe UI", 8, "bold"), bg="white",
                  relief="solid", bd=1, cursor="hand2", command=self._buscar_cliente).pack(side="left")

        tk.Label(contenedor, text=t("rest_condicion_venta"), font=("Segoe UI", 9, "bold"), bg="white").pack(
            anchor="w", pady=(6, 2))
        self.var_condicion = tk.StringVar(value="contado")
        frame_cond = tk.Frame(contenedor, bg="white")
        frame_cond.pack(anchor="w")
        tk.Radiobutton(frame_cond, text=t("contado"), variable=self.var_condicion, value="contado",
                      bg="white", font=("Segoe UI", 9)).pack(side="left", padx=(0, 10))
        tk.Radiobutton(frame_cond, text=t("credito_label"), variable=self.var_condicion, value="credito",
                      bg="white", font=("Segoe UI", 9)).pack(side="left")

        tk.Label(contenedor, text=t("rest_forma_pago_label"), font=("Segoe UI", 9, "bold"), bg="white").pack(
            anchor="w", pady=(10, 2))
        self.var_forma_pago = tk.StringVar(value="Efectivo")
        ttk.Combobox(contenedor, textvariable=self.var_forma_pago, state="readonly",
                    values=["Efectivo", "Transferencia Bancaria", "Tarjeta"], width=25).pack(anchor="w")

        botones = tk.Frame(self, bg="white")
        botones.pack(fill="x", padx=18, pady=(0, 16))
        tk.Button(botones, text=t("cancelar_x"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="left")
        self.boton_confirmar = tk.Button(botones, text=t("rest_confirmar_cobro"), font=("Segoe UI", 10, "bold"),
                  bg=VERDE, fg="white", relief="flat", padx=14, pady=8, cursor="hand2",
                  command=self._confirmar)
        self.boton_confirmar.pack(side="right")

        self.minsize(420, 380)
        ajustar_tamaño_ventana(self, ancho_min=420, alto_min=380)

    def _buscar_cliente(self):
        from ventanas_auxiliares_venta import VentanaAsignarCliente
        VentanaAsignarCliente(self, on_seleccionado=self._al_elegir_cliente)

    def _al_elegir_cliente(self, cliente):
        self.cliente_seleccionado = cliente
        self.label_cliente.config(text=cliente["nombre"] if cliente else "Consumidor Final")

    def _confirmar(self):
        self.boton_confirmar.config(state="disabled", text=t("rest_procesando"))
        self.update_idletasks()
        cliente_id = self.cliente_seleccionado["id"] if self.cliente_seleccionado else None
        ok, msg, venta_id = cerrar_comanda(
            self.comanda_id, self.usuario_actual.get("id"), condicion=self.var_condicion.get(),
            forma_pago=self.var_forma_pago.get(), cliente_id=cliente_id,
        )
        if not ok:
            messagebox.showerror("No se pudo cobrar", msg, parent=self)
            self.boton_confirmar.config(state="normal", text=t("rest_confirmar_cobro"))
            return
        messagebox.showinfo("Cobrado", msg, parent=self)
        self.destroy()
        if self.on_cobrado:
            self.on_cobrado()


# ============================================================
# FICHA DE PLATO (datos + receta con costeo automático)
# ============================================================
class VentanaFichaPlato(tk.Toplevel):
    def __init__(self, parent, plato_id: int = None, on_cambio=None):
        super().__init__(parent)
        self.plato_id = plato_id
        self.es_nuevo = plato_id is None
        self.on_cambio = on_cambio

        self.title("Nuevo Plato" if self.es_nuevo else "Ficha del Plato")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_titulo()
        self._construir_datos()
        if not self.es_nuevo:
            self._construir_receta()
            self._cargar_datos()

        self.minsize(680, 520)
        ajustar_tamaño_ventana(self, ancho_min=680, alto_min=560,
                              alto_max=self.winfo_screenheight() - 60)

    def _construir_titulo(self):
        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        titulo = "🍔 Nuevo Plato" if self.es_nuevo else "🍔 Ficha del Plato"
        tk.Label(barra, text=titulo, font=("Segoe UI", 11, "bold"), bg=AZUL_RIBBON, fg="white").pack(
            side="left", padx=15, pady=6)

    def _construir_datos(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=1, column=0, sticky="ew", padx=16, pady=(12, 6))
        contenedor.grid_columnconfigure(1, weight=1)
        contenedor.grid_columnconfigure(3, weight=1)

        tk.Label(contenedor, text=t("nombre_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=0, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_nombre = tk.StringVar()
        entry_nombre = tk.Entry(contenedor, textvariable=self.var_nombre, font=("Segoe UI", 10))
        entry_nombre.grid(row=0, column=1, sticky="ew", pady=4)
        forzar_mayusculas(entry_nombre, self.var_nombre)

        tk.Label(contenedor, text=t("rest_col_categoria").capitalize() + ":", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=0, column=2, sticky="e", pady=4, padx=(10, 8))
        self.var_categoria = tk.StringVar(value=CATEGORIAS_PLATO[1])
        ttk.Combobox(contenedor, textvariable=self.var_categoria, state="readonly",
                    values=CATEGORIAS_PLATO, width=16).grid(row=0, column=3, sticky="w", pady=4)

        tk.Label(contenedor, text=t("rest_precio_venta_gs"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=1, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_precio = tk.StringVar(value="0")
        tk.Entry(contenedor, textvariable=self.var_precio, font=("Segoe UI", 10), width=14).grid(
            row=1, column=1, sticky="w", pady=4)

        tk.Label(contenedor, text=t("rest_tiempo_prep"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=1, column=2, sticky="e", pady=4, padx=(10, 8))
        self.var_tiempo = tk.StringVar()
        tk.Entry(contenedor, textvariable=self.var_tiempo, font=("Segoe UI", 10), width=10).grid(
            row=1, column=3, sticky="w", pady=4)

        tk.Label(contenedor, text=t("descripcion_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=2, column=0, sticky="ne", pady=4, padx=(0, 8))
        self.texto_descripcion = tk.Text(contenedor, font=("Segoe UI", 9), height=2, relief="solid", bd=1)
        self.texto_descripcion.grid(row=2, column=1, columnspan=3, sticky="ew", pady=4)

        self.label_costeo = tk.Label(contenedor, text="", font=("Segoe UI", 9, "bold"), bg="white", fg=GRIS_TEXTO)
        self.label_costeo.grid(row=3, column=0, columnspan=4, sticky="w", pady=(6, 0))

        botones = tk.Frame(self, bg="white")
        botones.grid(row=1, column=0, sticky="se", padx=16)
        # (los botones reales van en una fila propia más abajo para no
        # pisar el label de costeo; se agregan al pie general)
        self.frame_botones = tk.Frame(self, bg="white")
        self.frame_botones.grid(row=1, column=0, sticky="ew", padx=16, pady=(48, 6))
        if self.es_nuevo:
            tk.Button(self.frame_botones, text=t("cancelar_x"), font=("Segoe UI", 9, "bold"), bg="white",
                      relief="solid", bd=1, command=self.destroy).pack(side="left")
            tk.Button(self.frame_botones, text=t("guardar_icono"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                      fg="white", relief="flat", padx=14, cursor="hand2", command=self._guardar).pack(side="right")
        else:
            self.boton_estado = tk.Button(self.frame_botones, text="", font=("Segoe UI", 9, "bold"), bg="white",
                      relief="solid", bd=1, cursor="hand2", command=self._alternar_estado)
            self.boton_estado.pack(side="left")
            tk.Button(self.frame_botones, text=t("guardar_cambios"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                      fg="white", relief="flat", padx=14, cursor="hand2", command=self._guardar).pack(side="right")

        entry_nombre.focus()

    def _construir_receta(self):
        self.sub_notebook = ttk.Notebook(self)
        self.sub_notebook.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))

        seccion = tk.Frame(self.sub_notebook, bg="white")
        self.sub_notebook.add(seccion, text=t("rest_receta_insumos"))
        seccion.grid_rowconfigure(1, weight=1)
        seccion.grid_columnconfigure(0, weight=1)

        barra = tk.Frame(seccion, bg="white")
        barra.grid(row=0, column=0, sticky="ew", pady=(6, 6), padx=6)
        tk.Label(barra, text=t("rest_insumos_consume"), font=("Segoe UI", 10, "bold"),
                 bg="white").pack(side="left")
        tk.Button(barra, text=t("rest_agregar_insumo"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON, fg="white",
                  relief="flat", padx=10, pady=4, cursor="hand2", command=self._agregar_ingrediente).pack(
                  side="right")

        contenedor = tk.Frame(seccion, bg="white")
        contenedor.grid(row=1, column=0, sticky="nsew", padx=6)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        columnas = ("insumo", "cantidad", "unidad", "costo_unit", "subtotal", "stock")
        encabezados = ("INSUMO", "CANTIDAD", "UNIDAD", "COSTO UNIT.", "SUBTOTAL", "STOCK DISP.")
        self.tabla_receta = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla_receta)
        for col, enc in zip(columnas, encabezados):
            self.tabla_receta.heading(col, text=enc)
            self.tabla_receta.column(col, width=140 if col == "insumo" else 100,
                                     anchor="w" if col == "insumo" else "center")
        sb = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla_receta.yview)
        self.tabla_receta.configure(yscrollcommand=sb.set)
        self.tabla_receta.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        sb_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla_receta.xview)
        self.tabla_receta.configure(xscrollcommand=sb_h.set)
        sb_h.grid(row=1, column=0, sticky="ew")
        self.tabla_receta.bind("<Double-1>", lambda e: self._editar_cantidad_ingrediente())

        barra_inferior = tk.Frame(seccion, bg="white")
        barra_inferior.grid(row=2, column=0, sticky="ew", pady=(6, 6), padx=6)
        tk.Button(barra_inferior, text=t("rest_quitar_insumo"), font=("Segoe UI", 9, "bold"), bg="#6b7280",
                  fg="white", relief="flat", padx=10, pady=4, cursor="hand2",
                  command=self._quitar_ingrediente).pack(side="left")

        self._construir_tab_variantes()

    def _construir_tab_variantes(self):
        seccion = tk.Frame(self.sub_notebook, bg="white")
        self.sub_notebook.add(seccion, text=t("rest_tamanos_variantes"))
        seccion.grid_rowconfigure(1, weight=1)
        seccion.grid_columnconfigure(0, weight=1)

        barra = tk.Frame(seccion, bg="white")
        barra.grid(row=0, column=0, sticky="ew", pady=(6, 6), padx=6)
        tk.Label(barra, text=t("rest_tamanos_disponibles"),
                 font=("Segoe UI", 9), bg="white", fg=GRIS_TEXTO, wraplength=420, justify="left").pack(
                 side="left", fill="x", expand=True)
        tk.Button(barra, text=t("rest_agregar_tamano"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON, fg="white",
                  relief="flat", padx=10, pady=4, cursor="hand2", command=self._agregar_variante).pack(
                  side="right")

        contenedor = tk.Frame(seccion, bg="white")
        contenedor.grid(row=1, column=0, sticky="nsew", padx=6)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        columnas = ("nombre", "precio", "multiplicador", "costo_estimado")
        self.tabla_variantes = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla_variantes)
        for col, enc in zip(columnas, ("TAMAÑO", "PRECIO", "MULTIPLICADOR RECETA", "COSTO ESTIMADO")):
            self.tabla_variantes.heading(col, text=enc)
            self.tabla_variantes.column(col, width=150 if col == "nombre" else 130,
                                        anchor="w" if col == "nombre" else "center")
        sb2 = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla_variantes.yview)
        self.tabla_variantes.configure(yscrollcommand=sb2.set)
        self.tabla_variantes.grid(row=0, column=0, sticky="nsew")
        sb2.grid(row=0, column=1, sticky="ns")
        sb2_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla_variantes.xview)
        self.tabla_variantes.configure(xscrollcommand=sb2_h.set)
        sb2_h.grid(row=1, column=0, sticky="ew")
        self.tabla_variantes.bind("<Double-1>", lambda e: self._editar_variante())

        barra_inferior = tk.Frame(seccion, bg="white")
        barra_inferior.grid(row=2, column=0, sticky="ew", pady=(6, 6), padx=6)
        tk.Button(barra_inferior, text=t("rest_quitar_tamano"), font=("Segoe UI", 9, "bold"), bg="#6b7280",
                  fg="white", relief="flat", padx=10, pady=4, cursor="hand2",
                  command=self._quitar_variante).pack(side="left")

    def _agregar_ingrediente(self):
        VentanaElegirInsumo(self, on_elegido=self._al_elegir_insumo)

    def _al_elegir_insumo(self, producto, cantidad):
        ok, msg = agregar_ingrediente_receta(self.plato_id, producto["id"], cantidad)
        if not ok:
            messagebox.showerror("No se pudo agregar", msg, parent=self)
            return
        self._cargar_receta()

    def _ingrediente_seleccionado(self):
        seleccion = self.tabla_receta.selection()
        return int(seleccion[0]) if seleccion else None

    def _editar_cantidad_ingrediente(self):
        ingrediente_id = self._ingrediente_seleccionado()
        if ingrediente_id is None:
            return
        self._abrir_editor_cantidad(ingrediente_id)

    def _abrir_editor_cantidad(self, ingrediente_id):
        ingredientes = {i["id"]: i for i in listar_ingredientes_receta(self.plato_id)}
        ing = ingredientes.get(ingrediente_id)
        if ing is None:
            return
        ventana = tk.Toplevel(self)
        ventana.title("Editar Cantidad")
        ventana.configure(bg="white")
        ventana.grab_set()
        cont = tk.Frame(ventana, bg="white")
        cont.pack(padx=20, pady=20)
        tk.Label(cont, text=f"{ing['nombre']} ({ing['unidad_medida']})", font=("Segoe UI", 10, "bold"),
                 bg="white").pack(anchor="w")
        var_cant = tk.StringVar(value=f"{ing['cantidad']:g}")
        entry = tk.Entry(cont, textvariable=var_cant, font=("Segoe UI", 10), width=10)
        entry.pack(pady=(10, 0))

        def guardar():
            try:
                nueva_cant = float(var_cant.get().replace(",", "."))
            except ValueError:
                messagebox.showwarning("Cantidad inválida", "Ingresa un número.", parent=ventana)
                return
            editar_cantidad_ingrediente(ingrediente_id, nueva_cant)
            ventana.destroy()
            self._cargar_receta()

        entry.bind("<Return>", lambda e: guardar())
        tk.Button(cont, text=t("guardar_icono"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON, fg="white",
                  relief="flat", padx=14, pady=6, cursor="hand2", command=guardar).pack(pady=(14, 0))
        entry.focus()
        entry.select_range(0, "end")

    def _quitar_ingrediente(self):
        ingrediente_id = self._ingrediente_seleccionado()
        if ingrediente_id is None:
            messagebox.showinfo("Selecciona un insumo", "Elegí un insumo de la receta primero.", parent=self)
            return
        quitar_ingrediente_receta(ingrediente_id)
        self._cargar_receta()

    def _cargar_receta(self):
        for f in self.tabla_receta.get_children():
            self.tabla_receta.delete(f)
        for ing in listar_ingredientes_receta(self.plato_id):
            self.tabla_receta.insert("", "end", iid=str(ing["id"]), values=(
                ing["nombre"], formatear_cantidad(ing["cantidad"], ing["unidad_medida"]),
                ing["unidad_medida"], formatear_gs(ing["precio_compra"]), formatear_gs(ing["subtotal"]),
                formatear_cantidad(ing["stock_disponible"], ing["unidad_medida"]),
            ))
        self._refrescar_costeo()
        self._cargar_variantes()

    # ---------------- Tamaños / Variantes ----------------
    def _variante_seleccionada(self):
        seleccion = self.tabla_variantes.selection()
        return int(seleccion[0]) if seleccion else None

    def _agregar_variante(self):
        VentanaFichaVariante(self, plato_id=self.plato_id, on_guardado=self._cargar_variantes)

    def _editar_variante(self):
        variante_id = self._variante_seleccionada()
        if variante_id is None:
            return
        variante = next((v for v in listar_variantes_plato(self.plato_id) if v["id"] == variante_id), None)
        if variante:
            VentanaFichaVariante(self, plato_id=self.plato_id, variante=variante,
                                 on_guardado=self._cargar_variantes)

    def _quitar_variante(self):
        variante_id = self._variante_seleccionada()
        if variante_id is None:
            messagebox.showinfo("Selecciona un tamaño", "Elegí un tamaño de la lista primero.", parent=self)
            return
        quitar_variante_plato(variante_id)
        self._cargar_variantes()

    def _cargar_variantes(self):
        if not hasattr(self, "tabla_variantes"):
            return
        for f in self.tabla_variantes.get_children():
            self.tabla_variantes.delete(f)
        for v in listar_variantes_plato(self.plato_id):
            costo_estimado = costo_receta_con_multiplicador(self.plato_id, v["multiplicador_receta"])
            self.tabla_variantes.insert("", "end", iid=str(v["id"]), values=(
                v["nombre"], formatear_gs(v["precio"]), f"{v['multiplicador_receta']:g}x",
                formatear_gs(costo_estimado),
            ))

    def _refrescar_costeo(self):
        try:
            precio_venta = float(self.var_precio.get().replace(",", ".") or 0)
        except ValueError:
            precio_venta = 0
        plato = obtener_plato(self.plato_id) if not self.es_nuevo else None
        if plato:
            costo, margen, margen_pct = plato["costo"], precio_venta - plato["costo"], 0
            margen_pct = (margen / precio_venta * 100) if precio_venta else 0
            color = VERDE if margen >= 0 else ROJO
            self.label_costeo.config(
                text=f"Costo de insumos: {formatear_gs(costo)}   |   "
                     f"Margen: {formatear_gs(margen)} ({margen_pct:.0f}%)", fg=color)

    def _cargar_datos(self):
        plato = obtener_plato(self.plato_id)
        if plato is None:
            messagebox.showerror("No encontrado", "Este plato ya no existe.", parent=self)
            self.destroy()
            return
        self.var_nombre.set(plato["nombre"])
        self.var_categoria.set(plato["categoria"])
        self.var_precio.set(str(plato["precio_venta"]))
        self.var_tiempo.set(str(plato["tiempo_preparacion_min"]) if plato["tiempo_preparacion_min"] else "")
        self.texto_descripcion.delete("1.0", "end")
        if plato["descripcion"]:
            self.texto_descripcion.insert("1.0", plato["descripcion"])
        self.boton_estado.config(text=t("rest_desactivar_plato") if plato["activo"] else t("rest_activar_plato"))
        self.title(f"Ficha de {plato['nombre']}" + ("" if plato["activo"] else " (Inactivo)"))
        self._cargar_receta()

    def _alternar_estado(self):
        plato = obtener_plato(self.plato_id)
        if plato is None:
            return
        cambiar_estado_plato(self.plato_id, not plato["activo"])
        self._cargar_datos()
        if self.on_cambio:
            self.on_cambio()

    def _guardar(self):
        try:
            precio = float(self.var_precio.get().replace(",", "."))
        except ValueError:
            messagebox.showwarning("Precio inválido", "Ingresa el precio de venta como un número.", parent=self)
            return
        tiempo = None
        if self.var_tiempo.get().strip():
            try:
                tiempo = int(self.var_tiempo.get())
            except ValueError:
                messagebox.showwarning("Tiempo inválido", "El tiempo de preparación debe ser un número entero.",
                                       parent=self)
                return
        descripcion = self.texto_descripcion.get("1.0", "end").strip()

        if self.es_nuevo:
            ok, msg, nuevo_id = crear_plato(self.var_nombre.get(), self.var_categoria.get(), precio,
                                            descripcion, tiempo)
            if not ok:
                messagebox.showerror("No se pudo guardar", msg, parent=self)
                return
            messagebox.showinfo("Plato creado", msg, parent=self)
            if self.on_cambio:
                self.on_cambio()
            # Transformamos la ventana en modo edición para poder cargar la receta enseguida
            self.plato_id = nuevo_id
            self.es_nuevo = False
            for w in self.frame_botones.winfo_children():
                w.destroy()
            self.boton_estado = tk.Button(self.frame_botones, text="", font=("Segoe UI", 9, "bold"), bg="white",
                      relief="solid", bd=1, cursor="hand2", command=self._alternar_estado)
            self.boton_estado.pack(side="left")
            tk.Button(self.frame_botones, text=t("guardar_cambios"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                      fg="white", relief="flat", padx=14, cursor="hand2", command=self._guardar).pack(side="right")
            self._construir_receta()
            self._cargar_datos()
            ajustar_tamaño_ventana(self, ancho_min=680, alto_min=560,
                                  alto_max=self.winfo_screenheight() - 60, mantener_posicion=True)
        else:
            ok, msg = editar_plato(self.plato_id, self.var_nombre.get(), self.var_categoria.get(), precio,
                                   descripcion, tiempo)
            if not ok:
                messagebox.showerror("No se pudo guardar", msg, parent=self)
                return
            self._cargar_datos()
            if self.on_cambio:
                self.on_cambio()


# ============================================================
# ELEGIR INSUMO (producto del catálogo) PARA LA RECETA
# ============================================================
class VentanaElegirInsumo(tk.Toplevel):
    def __init__(self, parent, on_elegido):
        super().__init__(parent)
        self.on_elegido = on_elegido

        self.title("Agregar Insumo a la Receta")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text=t("rest_elegir_insumo_titulo"), font=("Segoe UI", 11, "bold"), bg=AZUL_RIBBON,
                 fg="white").pack(side="left", padx=15, pady=6)

        barra_busqueda = tk.Frame(self, bg="white")
        barra_busqueda.grid(row=1, column=0, sticky="ew", padx=16, pady=(10, 6))
        self.var_busqueda = tk.StringVar()
        entry = tk.Entry(barra_busqueda, textvariable=self.var_busqueda, font=("Segoe UI", 10))
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<KeyRelease>", lambda e: self._cargar_lista())
        tk.Button(barra_busqueda, text=t("rest_crear_insumo_nuevo"), font=("Segoe UI", 9, "bold"), bg=VERDE,
                  fg="white", relief="flat", padx=10, pady=4, cursor="hand2",
                  command=self._crear_insumo_nuevo).pack(side="left", padx=(8, 0))

        self.label_vacio = tk.Label(
            self, text=t("rest_sin_insumos"),
            font=("Segoe UI", 9), bg="white", fg=GRIS_TEXTO, justify="center")

        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=2, column=0, sticky="nsew", padx=16)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        columnas = ("nombre", "unidad", "precio_compra", "stock")
        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc in zip(columnas, (t("col_insumo_mayus"), t("col_unidad_mayus"), t("col_costo_unit"), t("col_stock_mayus2"))):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=170 if col == "nombre" else 110,
                              anchor="w" if col == "nombre" else "center")
        sb = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        sb_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_h.set)
        sb_h.grid(row=1, column=0, sticky="ew")
        self.tabla.bind("<Double-1>", lambda e: self._continuar())

        frame_cantidad = tk.Frame(self, bg="white")
        frame_cantidad.grid(row=3, column=0, sticky="ew", padx=16, pady=(10, 4))
        tk.Label(frame_cantidad, text=t("rest_cantidad_que_usa"), font=("Segoe UI", 9, "bold"),
                 bg="white").pack(side="left")
        self.var_cantidad = tk.StringVar(value="1")
        tk.Entry(frame_cantidad, textvariable=self.var_cantidad, font=("Segoe UI", 10), width=10).pack(
            side="left", padx=(6, 0))

        botones = tk.Frame(self, bg="white")
        botones.grid(row=4, column=0, sticky="ew", padx=16, pady=(6, 16))
        tk.Button(botones, text=t("cancelar_x"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="left")
        tk.Button(botones, text=t("rest_agregar_boton"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON, fg="white",
                  relief="flat", padx=14, cursor="hand2", command=self._continuar).pack(side="right")

        self.minsize(480, 480)
        ajustar_tamaño_ventana(self, ancho_min=480, alto_min=520)
        entry.focus()
        self._cargar_lista()

    def _cargar_lista(self):
        for f in self.tabla.get_children():
            self.tabla.delete(f)
        self._productos = {p["id"]: p for p in listar_productos(solo_activos=True,
                                                                 texto_busqueda=self.var_busqueda.get())}
        for p in self._productos.values():
            self.tabla.insert("", "end", iid=str(p["id"]), values=(
                p["nombre"], p["unidad_medida"], formatear_gs(p["precio_compra"]),
                formatear_cantidad(p["stock"], p["unidad_medida"]),
            ))
        if not self._productos:
            self.label_vacio.grid(row=2, column=0, sticky="n", pady=40)
        else:
            self.label_vacio.grid_remove()

    def _crear_insumo_nuevo(self):
        VentanaCrearInsumoRapido(self, on_creado=self._al_crear_insumo)

    def _al_crear_insumo(self, producto_id):
        self.var_busqueda.set("")
        self._cargar_lista()
        if str(producto_id) in self.tabla.get_children():
            self.tabla.selection_set(str(producto_id))
            self.tabla.see(str(producto_id))

    def _continuar(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showinfo("Selecciona un insumo", "Elegí un producto de la lista.", parent=self)
            return
        producto = self._productos[int(seleccion[0])]
        try:
            cantidad = float(self.var_cantidad.get().replace(",", "."))
            if cantidad <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Cantidad inválida", "Ingresa una cantidad mayor a 0.", parent=self)
            return
        self.destroy()
        self.on_elegido(producto, cantidad)


# ============================================================
# GESTIONAR REPARTIDORES (CRUD simple)
# ============================================================
class VentanaGestionRepartidores(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Repartidores")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text=t("rest_repartidores_titulo"), font=("Segoe UI", 11, "bold"), bg=AZUL_RIBBON,
                 fg="white").pack(side="left", padx=15, pady=6)

        formulario = tk.Frame(self, bg="white")
        formulario.grid(row=1, column=0, sticky="ew", padx=16, pady=(12, 6))
        formulario.grid_columnconfigure(1, weight=1)
        tk.Label(formulario, text=t("nombre_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=0, column=0, sticky="e", padx=(0, 6))
        self.var_nombre = tk.StringVar()
        entry_nombre = tk.Entry(formulario, textvariable=self.var_nombre, font=("Segoe UI", 10))
        entry_nombre.grid(row=0, column=1, sticky="ew")
        forzar_mayusculas(entry_nombre, self.var_nombre)

        tk.Label(formulario, text=t("telefono_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=1, column=0, sticky="e", padx=(0, 6), pady=(4, 0))
        self.var_telefono = tk.StringVar()
        tk.Entry(formulario, textvariable=self.var_telefono, font=("Segoe UI", 10)).grid(
            row=1, column=1, sticky="ew", pady=(4, 0))

        tk.Label(formulario, text=t("vehiculo_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=2, column=0, sticky="e", padx=(0, 6), pady=(4, 0))
        self.var_vehiculo = tk.StringVar()
        entry_vehiculo = tk.Entry(formulario, textvariable=self.var_vehiculo, font=("Segoe UI", 10))
        entry_vehiculo.grid(row=2, column=1, sticky="ew", pady=(4, 0))
        forzar_mayusculas(entry_vehiculo, self.var_vehiculo)

        tk.Button(formulario, text=t("rest_agregar_boton"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON, fg="white",
                  relief="flat", padx=12, pady=5, cursor="hand2", command=self._agregar).grid(
                  row=3, column=1, sticky="e", pady=(8, 0))

        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=2, column=0, sticky="nsew", padx=16, pady=(6, 6))
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        columnas = ("nombre", "telefono", "vehiculo", "estado")
        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc in zip(columnas, (t("col_nombre_mayus"), t("col_telefono").upper(), t("col_vehiculo_mayus"), t("col_estado_mayus"))):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=140, anchor="w" if col == "nombre" else "center")
        sb = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        sb_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_h.set)
        sb_h.grid(row=1, column=0, sticky="ew")
        self.tabla.tag_configure("inactivo", foreground=GRIS_TEXTO)

        botones = tk.Frame(self, bg="white")
        botones.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 16))
        tk.Button(botones, text=t("rest_activar_desactivar_sel"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, cursor="hand2", command=self._alternar_estado).pack(side="left")
        tk.Button(botones, text=t("cerrar"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="right")

        self.minsize(460, 460)
        ajustar_tamaño_ventana(self, ancho_min=460, alto_min=480)
        entry_nombre.focus()
        self.cargar()

    def _agregar(self):
        ok, msg = crear_repartidor(self.var_nombre.get(), self.var_telefono.get(), self.var_vehiculo.get())
        if not ok:
            messagebox.showerror("No se pudo agregar", msg, parent=self)
            return
        self.var_nombre.set("")
        self.var_telefono.set("")
        self.var_vehiculo.set("")
        self.cargar()

    def _alternar_estado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showinfo("Selecciona un repartidor", "Elegí un repartidor de la lista.", parent=self)
            return
        repartidor_id = int(seleccion[0])
        repartidor = next((r for r in listar_repartidores(solo_activos=False) if r["id"] == repartidor_id), None)
        if repartidor:
            cambiar_estado_repartidor(repartidor_id, not repartidor["activo"])
            self.cargar()

    def cargar(self):
        for f in self.tabla.get_children():
            self.tabla.delete(f)
        for r in listar_repartidores(solo_activos=False):
            tags = () if r["activo"] else ("inactivo",)
            self.tabla.insert("", "end", iid=str(r["id"]), tags=tags, values=(
                r["nombre"], r["telefono"] or "—", r["vehiculo"] or "—", "Activo" if r["activo"] else "Inactivo",
            ))


# ============================================================
# ELEGIR REPARTIDOR PARA UN PEDIDO
# ============================================================
class VentanaElegirRepartidor(tk.Toplevel):
    def __init__(self, parent, repartidores: list, on_elegido, comanda_id: int):
        super().__init__(parent)
        self.on_elegido = on_elegido
        self.comanda_id = comanda_id

        self.title("Asignar Repartidor")
        self.configure(bg="white")
        self.grab_set()

        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(padx=20, pady=20)
        tk.Label(contenedor, text=t("rest_elegir_quien_entrega"), font=("Segoe UI", 10, "bold"),
                 bg="white").pack(anchor="w", pady=(0, 8))

        self.var_repartidor = tk.StringVar()
        self._mapa = {r["nombre"]: r["id"] for r in repartidores}
        combo = ttk.Combobox(contenedor, textvariable=self.var_repartidor, state="readonly",
                             values=list(self._mapa.keys()), width=30)
        combo.pack()
        if repartidores:
            combo.current(0)

        botones = tk.Frame(contenedor, bg="white")
        botones.pack(pady=(16, 0), fill="x")
        tk.Button(botones, text=t("cancelar_x"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="left")
        tk.Button(botones, text=t("rest_asignar"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON, fg="white",
                  relief="flat", padx=14, cursor="hand2", command=self._confirmar).pack(side="right")

    def _confirmar(self):
        nombre = self.var_repartidor.get()
        if not nombre:
            messagebox.showinfo("Elegí un repartidor", "Seleccioná un repartidor de la lista.", parent=self)
            return
        self.destroy()
        self.on_elegido(self.comanda_id, self._mapa[nombre])


# ============================================================
# FICHA DE TAMAÑO/VARIANTE (crear / editar)
# ============================================================
class VentanaFichaVariante(tk.Toplevel):
    def __init__(self, parent, plato_id: int, variante: dict = None, on_guardado=None):
        super().__init__(parent)
        self.plato_id = plato_id
        self.variante = variante
        self.on_guardado = on_guardado

        self.title("Nuevo Tamaño" if variante is None else "Editar Tamaño")
        self.configure(bg="white")
        self.grab_set()

        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(padx=20, pady=20)
        contenedor.grid_columnconfigure(1, weight=1)

        tk.Label(contenedor, text=t("rest_nombre_ej_tamano"), font=("Segoe UI", 9, "bold"),
                 bg="white").grid(row=0, column=0, sticky="e", padx=(0, 8), pady=4)
        self.var_nombre = tk.StringVar(value=variante["nombre"] if variante else "")
        entry_nombre = tk.Entry(contenedor, textvariable=self.var_nombre, font=("Segoe UI", 10))
        entry_nombre.grid(row=0, column=1, sticky="ew", pady=4)
        forzar_mayusculas(entry_nombre, self.var_nombre)

        tk.Label(contenedor, text=t("rest_precio_venta_gs2"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=1, column=0, sticky="e", padx=(0, 8), pady=4)
        self.var_precio = tk.StringVar(value=str(variante["precio"]) if variante else "0")
        tk.Entry(contenedor, textvariable=self.var_precio, font=("Segoe UI", 10), width=14).grid(
            row=1, column=1, sticky="w", pady=4)

        tk.Label(contenedor, text=t("rest_multiplicador_receta"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=2, column=0, sticky="e", padx=(0, 8), pady=4)
        self.var_multiplicador = tk.StringVar(value=str(variante["multiplicador_receta"]) if variante else "1")
        tk.Entry(contenedor, textvariable=self.var_multiplicador, font=("Segoe UI", 10), width=14).grid(
            row=2, column=1, sticky="w", pady=4)
        tk.Label(contenedor, text=t("rest_multiplicador_ayuda"),
                 font=("Segoe UI", 8), bg="white", fg=GRIS_TEXTO, wraplength=280, justify="left").grid(
                 row=3, column=1, sticky="w")

        botones = tk.Frame(contenedor, bg="white")
        botones.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        tk.Button(botones, text=t("cancelar_x"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="left")
        tk.Button(botones, text=t("guardar_icono"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON, fg="white",
                  relief="flat", padx=14, cursor="hand2", command=self._guardar).pack(side="right")
        entry_nombre.focus()

    def _guardar(self):
        if self.variante is None:
            ok, msg = agregar_variante_plato(self.plato_id, self.var_nombre.get(), self.var_precio.get(),
                                             self.var_multiplicador.get())
        else:
            ok, msg = editar_variante_plato(self.variante["id"], self.var_nombre.get(), self.var_precio.get(),
                                            self.var_multiplicador.get())
        if not ok:
            messagebox.showerror("No se pudo guardar", msg, parent=self)
            return
        if self.on_guardado:
            self.on_guardado()
        self.destroy()


# ============================================================
# PERSONALIZAR UN ÍTEM DE LA COMANDA (agregar/quitar ingredientes)
# ============================================================
class VentanaPersonalizarItem(tk.Toplevel):
    def __init__(self, parent, item: dict, on_cambio=None):
        super().__init__(parent)
        self.item = item
        self.on_cambio = on_cambio

        self.title("Personalizar")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        barra = tk.Frame(self, bg="#7c3aed", height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text=f"🎨 Personalizar: {item['plato']}", font=("Segoe UI", 11, "bold"),
                 bg="#7c3aed", fg="white").pack(side="left", padx=15, pady=6)

        botones_arriba = tk.Frame(self, bg="white")
        botones_arriba.grid(row=1, column=0, sticky="ew", padx=16, pady=(10, 6))
        tk.Button(botones_arriba, text=t("rest_agregar_ingrediente_extra"), font=("Segoe UI", 9, "bold"),
                  bg=VERDE, fg="white", relief="flat", padx=10, pady=5, cursor="hand2",
                  command=self._agregar_ingrediente).pack(side="left")
        tk.Button(botones_arriba, text=t("rest_quitar_ingrediente_receta"), font=("Segoe UI", 9, "bold"),
                  bg=NARANJA, fg="white", relief="flat", padx=10, pady=5, cursor="hand2",
                  command=self._quitar_ingrediente_base).pack(side="left", padx=(8, 0))

        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=2, column=0, sticky="nsew", padx=16)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        columnas = ("tipo", "ingrediente", "cantidad", "recargo")
        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc in zip(columnas, (t("rest_col_tipo2"), t("col_ingrediente_mayus"), t("col_cantidad"), t("rest_col_recargo"))):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=140, anchor="center")
        sb = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        sb_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_h.set)
        sb_h.grid(row=1, column=0, sticky="ew")
        self.tabla.tag_configure("Agregado", foreground=VERDE)
        self.tabla.tag_configure("Quitado", foreground=NARANJA)

        botones = tk.Frame(self, bg="white")
        botones.grid(row=3, column=0, sticky="ew", padx=16, pady=(10, 16))
        tk.Button(botones, text=t("rest_quitar_personalizacion"), font=("Segoe UI", 9, "bold"), bg="#6b7280",
                  fg="white", relief="flat", padx=10, pady=5, cursor="hand2",
                  command=self._quitar_extra).pack(side="left")
        tk.Button(botones, text=t("cerrar"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self._cerrar).pack(side="right")

        self.minsize(500, 420)
        ajustar_tamaño_ventana(self, ancho_min=500, alto_min=460)
        self.cargar()

    def _agregar_ingrediente(self):
        VentanaElegirInsumo(self, on_elegido=self._al_agregar_extra)

    def _al_agregar_extra(self, producto, cantidad):
        costo_sugerido = round(producto["precio_compra"] * cantidad * 2, -2)  # sugerencia: 2x el costo
        VentanaConfirmarRecargo(self, producto, cantidad, costo_sugerido, on_confirmado=self._guardar_agregado)

    def _guardar_agregado(self, producto, cantidad, costo_extra):
        ok, msg = agregar_extra_item(self.item["id"], producto["id"], "Agregado", cantidad, costo_extra)
        if not ok:
            messagebox.showerror("No se pudo agregar", msg, parent=self)
            return
        self.cargar()

    def _quitar_ingrediente_base(self):
        ingredientes = listar_ingredientes_receta(self.item["plato_id"])
        if not ingredientes:
            messagebox.showinfo("Sin receta", "Este plato no tiene ingredientes base cargados en su receta.",
                               parent=self)
            return
        VentanaElegirIngredienteBase(self, ingredientes, on_elegido=self._al_quitar_base)

    def _al_quitar_base(self, ingrediente):
        ok, msg = agregar_extra_item(self.item["id"], ingrediente["producto_id"], "Quitado",
                                     ingrediente["cantidad"], 0)
        if not ok:
            messagebox.showerror("No se pudo quitar", msg, parent=self)
            return
        self.cargar()

    def _extra_seleccionado(self):
        seleccion = self.tabla.selection()
        return int(seleccion[0]) if seleccion else None

    def _quitar_extra(self):
        extra_id = self._extra_seleccionado()
        if extra_id is None:
            messagebox.showinfo("Selecciona una fila", "Elegí una personalización de la lista.", parent=self)
            return
        quitar_extra_item(extra_id)
        self.cargar()

    def cargar(self):
        for f in self.tabla.get_children():
            self.tabla.delete(f)
        extras = _obtener_extras_item(self.item["id"])
        for ex in extras:
            self.tabla.insert("", "end", iid=str(ex["id"]), tags=(ex["tipo"],), values=(
                ex["tipo"], ex["nombre"], f"{ex['cantidad']:g}",
                formatear_gs(ex["costo_extra"]) if ex["tipo"] == "Agregado" else "—",
            ))

    def _cerrar(self):
        self.destroy()
        if self.on_cambio:
            self.on_cambio()


def _obtener_extras_item(comanda_item_id: int) -> list[dict]:
    """Pequeño helper local: lee directamente los extras de un ítem sin
    necesitar el comanda_id (la ficha de personalización solo tiene el
    item a mano)."""
    from database import conectar
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id, e.producto_id, p.nombre, e.tipo, e.cantidad, e.costo_extra
        FROM rest_comanda_item_extras e JOIN productos p ON e.producto_id = p.id
        WHERE e.comanda_item_id = ?
    """, (comanda_item_id,))
    filas = cursor.fetchall()
    conn.close()
    return [{"id": f[0], "producto_id": f[1], "nombre": f[2], "tipo": f[3], "cantidad": f[4], "costo_extra": f[5]}
            for f in filas]


# ============================================================
# ELEGIR UN INGREDIENTE DE LA RECETA BASE (para "Quitar")
# ============================================================
class VentanaElegirIngredienteBase(tk.Toplevel):
    def __init__(self, parent, ingredientes: list, on_elegido):
        super().__init__(parent)
        self.on_elegido = on_elegido
        self.title("Quitar Ingrediente")
        self.configure(bg="white")
        self.grab_set()

        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(padx=20, pady=20)
        tk.Label(contenedor, text=t("rest_que_ingrediente_quitar"),
                 font=("Segoe UI", 10, "bold"), bg="white", wraplength=320, justify="left").pack(anchor="w")

        self._mapa = {i["nombre"]: i for i in ingredientes}
        self.var_ingrediente = tk.StringVar()
        combo = ttk.Combobox(contenedor, textvariable=self.var_ingrediente, state="readonly",
                             values=list(self._mapa.keys()), width=30)
        combo.pack(pady=(10, 0))
        if ingredientes:
            combo.current(0)

        botones = tk.Frame(contenedor, bg="white")
        botones.pack(pady=(16, 0), fill="x")
        tk.Button(botones, text=t("cancelar_x"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="left")
        tk.Button(botones, text=t("rest_quitar_confirmar"), font=("Segoe UI", 9, "bold"), bg=NARANJA, fg="white",
                  relief="flat", padx=14, cursor="hand2", command=self._confirmar).pack(side="right")

    def _confirmar(self):
        nombre = self.var_ingrediente.get()
        if not nombre:
            return
        self.destroy()
        self.on_elegido(self._mapa[nombre])


# ============================================================
# CONFIRMAR EL RECARGO DE UN INGREDIENTE AGREGADO
# ============================================================
class VentanaConfirmarRecargo(tk.Toplevel):
    def __init__(self, parent, producto: dict, cantidad: float, costo_sugerido: float, on_confirmado):
        super().__init__(parent)
        self.producto = producto
        self.cantidad = cantidad
        self.on_confirmado = on_confirmado

        self.title("Recargo por Ingrediente Extra")
        self.configure(bg="white")
        self.grab_set()

        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(padx=20, pady=20)
        tk.Label(contenedor, text=f"Agregar {formatear_cantidad(cantidad, producto['unidad_medida'])} de "
                                  f"{producto['nombre']}", font=("Segoe UI", 10, "bold"), bg="white",
                 wraplength=320, justify="left").pack(anchor="w")

        fila = tk.Frame(contenedor, bg="white")
        fila.pack(pady=(10, 0), fill="x")
        tk.Label(fila, text=t("rest_recargo_a_cobrar"), font=("Segoe UI", 9, "bold"), bg="white").pack(side="left")
        self.var_recargo = tk.StringVar(value=str(int(costo_sugerido)))
        entry = tk.Entry(fila, textvariable=self.var_recargo, font=("Segoe UI", 10), width=12)
        entry.pack(side="left", padx=(6, 0))

        botones = tk.Frame(contenedor, bg="white")
        botones.pack(pady=(16, 0), fill="x")
        tk.Button(botones, text=t("cancelar_x"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="left")
        tk.Button(botones, text=t("confirmar_icono"), font=("Segoe UI", 9, "bold"), bg=VERDE, fg="white",
                  relief="flat", padx=14, cursor="hand2", command=self._confirmar).pack(side="right")
        entry.focus()
        entry.select_range(0, "end")

    def _confirmar(self):
        try:
            recargo = float(self.var_recargo.get().replace(",", "."))
            if recargo < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Recargo inválido", "Ingresa un número (0 o mayor).", parent=self)
            return
        self.destroy()
        self.on_confirmado(self.producto, self.cantidad, recargo)


# ============================================================
# CREAR INSUMO RÁPIDO (sin salir del módulo Restaurante)
# ============================================================
class VentanaCrearInsumoRapido(tk.Toplevel):
    """Da de alta un producto nuevo en el catálogo (Productos/Inventario)
    directamente desde 'Elegir Insumo', para no tener que salir del
    módulo Restaurante cada vez que hace falta cargar algo nuevo (una
    bebida, un jugo, una verdura que todavía no estaba cargada, etc.).
    Usa los mismos datos mínimos que models_catalogo.crear_producto; si
    más adelante hace falta afinar precio de venta, código de barras,
    proveedor, etc., se puede completar desde el módulo Productos."""

    UNIDADES = ["Unidad", "Kilogramo", "Litro", "Metro", "Caja", "Paquete", "Docena"]

    def __init__(self, parent, on_creado=None):
        super().__init__(parent)
        self.on_creado = on_creado

        self.title("Crear Insumo Nuevo")
        self.configure(bg="white")
        self.grab_set()

        barra = tk.Frame(self, bg=VERDE, height=34)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        tk.Label(barra, text=t("rest_crear_insumo_titulo"), font=("Segoe UI", 11, "bold"),
                 bg=VERDE, fg="white").pack(side="left", padx=15, pady=6)

        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=18, pady=16)
        contenedor.grid_columnconfigure(1, weight=1)

        tk.Label(contenedor, text=t("rest_nombre_ej_insumo"),
                 font=("Segoe UI", 9, "bold"), bg="white").grid(row=0, column=0, columnspan=2, sticky="w")
        self.var_nombre = tk.StringVar()
        entry_nombre = tk.Entry(contenedor, textvariable=self.var_nombre, font=("Segoe UI", 10))
        entry_nombre.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 10))
        forzar_mayusculas(entry_nombre, self.var_nombre)

        tk.Label(contenedor, text=t("rest_se_mide_por"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=2, column=0, sticky="e", padx=(0, 8), pady=4)
        self.var_unidad = tk.StringVar(value="Unidad")
        ttk.Combobox(contenedor, textvariable=self.var_unidad, state="readonly",
                    values=self.UNIDADES, width=14).grid(row=2, column=1, sticky="w", pady=4)
        tk.Label(contenedor, text=t("rest_se_mide_por_ayuda"),
                 font=("Segoe UI", 8), bg="white", fg=GRIS_TEXTO, wraplength=320, justify="left").grid(
                 row=3, column=0, columnspan=2, sticky="w")

        tk.Label(contenedor, text=t("rest_costo_compra"), font=("Segoe UI", 9, "bold"),
                 bg="white").grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.var_costo = tk.StringVar(value="0")
        tk.Entry(contenedor, textvariable=self.var_costo, font=("Segoe UI", 10), width=16).grid(
            row=5, column=0, sticky="w", pady=(2, 10))

        tk.Label(contenedor, text=t("rest_stock_inicial"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=6, column=0, columnspan=2, sticky="w")
        self.var_stock = tk.StringVar(value="0")
        tk.Entry(contenedor, textvariable=self.var_stock, font=("Segoe UI", 10), width=16).grid(
            row=7, column=0, sticky="w", pady=(2, 4))

        botones = tk.Frame(self, bg="white")
        botones.pack(fill="x", padx=18, pady=(0, 16))
        tk.Button(botones, text=t("cancelar_x"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="left")
        tk.Button(botones, text=t("rest_crear_insumo_boton"), font=("Segoe UI", 9, "bold"), bg=VERDE, fg="white",
                  relief="flat", padx=14, pady=6, cursor="hand2", command=self._guardar).pack(side="right")

        self.minsize(400, 380)
        ajustar_tamaño_ventana(self, ancho_min=400, alto_min=400)
        entry_nombre.focus()

    def _guardar(self):
        try:
            costo = float(self.var_costo.get().replace(",", "."))
            stock = float(self.var_stock.get().replace(",", "."))
            if costo < 0 or stock < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Datos inválidos", "El costo y el stock deben ser números (0 o mayor).",
                                   parent=self)
            return
        # precio_venta/credito/mayorista quedan en 0: este producto se usa como
        # insumo interno, no se vende suelto directamente al público. Si en algún
        # momento también se vende tal cual (ej. una gaseosa de lata), se le puede
        # cargar el precio de venta después desde el módulo Productos.
        ok, msg, nuevo_id = crear_producto(
            self.var_nombre.get(), costo, 0, 0, 0, stock, unidad_medida=self.var_unidad.get(),
        )
        if not ok:
            messagebox.showerror("No se pudo crear", msg, parent=self)
            return
        self.destroy()
        if self.on_creado:
            self.on_creado(nuevo_id)
