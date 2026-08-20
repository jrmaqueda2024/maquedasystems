"""
ventana_asistencia.py
Módulo Asistencia Técnica: ingreso de equipos a reparación (casos
técnicos) con seguimiento de estado (Entrada → En Espera → En Revisión →
Disponible para Retiro → Retirado), pestañas Casos / Pendientes /
Dashboard / Equipos, y el asistente de 2 pasos "Entrada de Equipo".
"""
import datetime
import tkinter as tk
from tkinter import ttk, messagebox

from models_asistencia import (
    ESTADOS, PRIORIDADES, listar_tipos_equipo, crear_tipo_equipo,
    buscar_equipos, crear_caso, listar_casos, listar_pendientes,
    listar_casos_por_estado, listar_retirados_recientes, conteos_dashboard,
    obtener_caso, cambiar_estado_caso, actualizar_observaciones, anular_caso,
)
from utilidades_ui import ajustar_tamaño_ventana, forzar_mayusculas, habilitar_deseleccion_treeview
from traducciones import t

AZUL_RIBBON = "#1d5fd6"
GRIS_FONDO = "#f4f5f7"
GRIS_BORDE = "#e2e8f0"
VERDE = "#16a34a"
ROJO = "#dc2626"
NARANJA = "#d97706"
GRIS_TEXTO = "#6b7280"

COLOR_PRIORIDAD = {
    "Baja": "#6b7280", "Media": "#1d5fd6", "Alta": "#d97706", "Urgente": "#dc2626",
}
COLOR_ESTADO = {
    "Entrada": "#1d5fd6", "En Espera": "#d97706", "En Revisión": "#7c3aed",
    "Disponible para Retiro": "#16a34a", "Retirado": "#6b7280",
}


def _formatear_fecha_hora(fecha_hora: str) -> str:
    if not fecha_hora:
        return "—"
    try:
        return datetime.datetime.fromisoformat(fecha_hora).strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return fecha_hora


# ============================================================
# PANEL PRINCIPAL
# ============================================================
class PanelAsistenciaTecnica(tk.Frame):
    def __init__(self, parent, usuario_actual):
        super().__init__(parent, bg="white")
        self.usuario_actual = usuario_actual

        self._construir_barra_superior()
        self._construir_notebook()

    # ---------------- BARRA SUPERIOR (ribbon) ----------------
    def _construir_barra_superior(self):
        barra = tk.Frame(self, bg="white")
        barra.pack(fill="x", padx=10, pady=(10, 5))

        tk.Button(barra, text=t("asist_entrada_equipo"), font=("Segoe UI", 9, "bold"),
                  bg=AZUL_RIBBON, fg="white", relief="flat", padx=12, pady=6,
                  cursor="hand2", command=self._abrir_entrada_equipo).pack(side="left")

    # ---------------- SUB-PESTAÑAS ----------------
    def _construir_notebook(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tab_casos = _TabCasos(self.notebook, self)
        self.tab_pendientes = _TabPendientes(self.notebook, self)
        self.tab_dashboard = _TabDashboard(self.notebook, self)
        self.tab_equipos = _TabEquipos(self.notebook, self)

        self.notebook.add(self.tab_casos, text=t("asist_tab_casos"))
        self.notebook.add(self.tab_pendientes, text=t("asist_tab_pendientes"))
        self.notebook.add(self.tab_dashboard, text=t("asist_tab_dashboard"))
        self.notebook.add(self.tab_equipos, text=t("asist_tab_equipos"))

        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self.refrescar_todo())

    def refrescar_todo(self):
        self.tab_casos.cargar()
        self.tab_pendientes.cargar()
        self.tab_dashboard.cargar()
        self.tab_equipos.cargar()

    def _abrir_entrada_equipo(self):
        VentanaEntradaEquipo(self, self.usuario_actual, on_guardado=self.refrescar_todo)


# ============================================================
# PESTAÑA: CASOS
# ============================================================
class _TabCasos(tk.Frame):
    def __init__(self, parent, panel_padre):
        super().__init__(parent, bg="white")
        self.panel_padre = panel_padre
        self._construir_filtros()
        self._construir_tabla()
        self.cargar()

    def _construir_filtros(self):
        barra = tk.Frame(self, bg=GRIS_FONDO)
        barra.pack(fill="x")
        interior = tk.Frame(barra, bg=GRIS_FONDO)
        interior.pack(fill="x", padx=10, pady=8)

        tk.Label(interior, text="Mostrar:", font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).pack(side="left")
        self.var_mostrar = tk.StringVar(value="25")
        combo = ttk.Combobox(interior, textvariable=self.var_mostrar,
                             values=["25", "50", "100", "Todos"], state="readonly", width=8,
                             font=("Segoe UI", 9))
        combo.pack(side="left", padx=(6, 16))
        combo.bind("<<ComboboxSelected>>", lambda e: self.cargar())

        self.var_pendientes = tk.BooleanVar(value=True)
        self.var_anulados = tk.BooleanVar(value=True)
        self.var_retirados = tk.BooleanVar(value=True)
        for texto, var in [("Pendientes", self.var_pendientes), ("Anulados", self.var_anulados),
                           ("Retirados", self.var_retirados)]:
            tk.Checkbutton(interior, text=texto, variable=var, bg=GRIS_FONDO,
                           font=("Segoe UI", 9), command=self.cargar).pack(side="left", padx=(0, 10))

        self.var_busqueda = tk.StringVar()
        entry = tk.Entry(interior, textvariable=self.var_busqueda, font=("Segoe UI", 9), width=25)
        entry.pack(side="right")
        entry.bind("<KeyRelease>", lambda e: self.cargar())
        tk.Label(interior, text="🔍", font=("Segoe UI", 10), bg=GRIS_FONDO).pack(side="right", padx=(0, 4))

    def _construir_tabla(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=0, pady=(4, 0))
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        columnas = ("caso", "fecha_entrada", "tipo_equipo", "descripcion", "serie", "cliente", "estado", "fecha")
        encabezados = ("N° CASO", "FECHA ENTRADA", "TIPO EQUIPO", "DESCRIPCIÓN DEL EQUIPO",
                       "N° SERIE", "CLIENTE", "ESTADO", "FECHA")
        anchos = (70, 130, 110, 220, 100, 170, 150, 130)

        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho,
                              anchor="w" if col in ("descripcion", "cliente") else "center")
        self.tabla.tag_configure("anulado", foreground="#9ca3af")

        sb_y = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb_y.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_y_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_y_h.set)
        sb_y_h.grid(row=1, column=0, sticky="ew")

        self.tabla.bind("<Double-1>", lambda e: self._abrir_detalle_seleccionado())

    def cargar(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        casos = listar_casos(
            mostrar_ultimos=self.var_mostrar.get(),
            incluir_pendientes=self.var_pendientes.get(),
            incluir_anulados=self.var_anulados.get(),
            incluir_retirados=self.var_retirados.get(),
            busqueda=self.var_busqueda.get(),
        )
        for c in casos:
            tags = ("anulado",) if c["anulado"] else ()
            estado_txt = f"{c['estado']} (Anulado)" if c["anulado"] else c["estado"]
            self.tabla.insert("", "end", iid=str(c["id"]), values=(
                c["id"], _formatear_fecha_hora(c["fecha_entrada"]), c["tipo_equipo"] or "—",
                c["descripcion_equipo"], c["nro_serie"] or "—", c["cliente"],
                estado_txt, _formatear_fecha_hora(c["fecha_estado"]),
            ), tags=tags)

    def _abrir_detalle_seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        VentanaDetalleCaso(self, int(seleccion[0]), self.panel_padre.usuario_actual,
                          on_cambio=self.panel_padre.refrescar_todo)


# ============================================================
# PESTAÑA: PENDIENTES
# ============================================================
class _TabPendientes(tk.Frame):
    def __init__(self, parent, panel_padre):
        super().__init__(parent, bg="white")
        self.panel_padre = panel_padre
        self._construir_filtros()
        self._construir_tabla()
        self.cargar()

    def _construir_filtros(self):
        barra = tk.Frame(self, bg=GRIS_FONDO)
        barra.pack(fill="x")
        interior = tk.Frame(barra, bg=GRIS_FONDO)
        interior.pack(fill="x", padx=10, pady=8)
        self.var_busqueda = tk.StringVar()
        entry = tk.Entry(interior, textvariable=self.var_busqueda, font=("Segoe UI", 9), width=25)
        entry.pack(side="right")
        entry.bind("<KeyRelease>", lambda e: self.cargar())
        tk.Label(interior, text="🔍", font=("Segoe UI", 10), bg=GRIS_FONDO).pack(side="right", padx=(0, 4))

    def _construir_tabla(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=0, pady=(4, 0))
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        columnas = ("caso", "fecha_entrada", "prioridad", "tipo_equipo", "descripcion",
                    "serie", "cliente", "estado", "recibido_por")
        encabezados = ("N° CASO", "FECHA ENTRADA", "PRIORIDAD", "TIPO EQUIPO", "DESCRIPCIÓN DEL EQUIPO",
                       "N° SERIE", "CLIENTE", "ESTADO", "RECIBIDO POR:")
        anchos = (70, 130, 90, 110, 200, 100, 160, 150, 140)

        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho,
                              anchor="w" if col in ("descripcion", "cliente") else "center")

        sb_y = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb_y.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_y_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_y_h.set)
        sb_y_h.grid(row=1, column=0, sticky="ew")

        self.tabla.bind("<Double-1>", lambda e: self._abrir_detalle_seleccionado())

    def cargar(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        for c in listar_pendientes(busqueda=self.var_busqueda.get()):
            self.tabla.insert("", "end", iid=str(c["id"]), values=(
                c["id"], _formatear_fecha_hora(c["fecha_entrada"]), c["prioridad"],
                c["tipo_equipo"] or "—", c["descripcion_equipo"], c["nro_serie"] or "—",
                c["cliente"], c["estado"], c["recibido_por"] or "—",
            ), tags=(f"prioridad_{c['prioridad']}",))
            self.tabla.tag_configure(f"prioridad_{c['prioridad']}",
                                     foreground=COLOR_PRIORIDAD.get(c["prioridad"], "#1e293b"))

    def _abrir_detalle_seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        VentanaDetalleCaso(self, int(seleccion[0]), self.panel_padre.usuario_actual,
                          on_cambio=self.panel_padre.refrescar_todo)


# ============================================================
# PESTAÑA: DASHBOARD (acordeón por estado)
# ============================================================
class _TabDashboard(tk.Frame):
    def __init__(self, parent, panel_padre):
        super().__init__(parent, bg="white")
        self.panel_padre = panel_padre
        self.secciones: dict[str, dict] = {}

        barra = tk.Frame(self, bg=GRIS_FONDO)
        barra.pack(fill="x")
        interior = tk.Frame(barra, bg=GRIS_FONDO)
        interior.pack(fill="x", padx=10, pady=8)
        self.var_busqueda = tk.StringVar()
        entry = tk.Entry(interior, textvariable=self.var_busqueda, font=("Segoe UI", 9), width=25)
        entry.pack(side="right")
        tk.Label(interior, text="🔍", font=("Segoe UI", 10), bg=GRIS_FONDO).pack(side="right", padx=(0, 4))

        canvas = tk.Canvas(self, bg="white", highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.contenedor = tk.Frame(canvas, bg="white")
        canvas.create_window((0, 0), window=self.contenedor, anchor="nw")
        self.contenedor.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        titulos = ESTADOS[:-1] + ["Retirados recientemente"]
        for titulo in titulos:
            self._crear_seccion(titulo)

    def _crear_seccion(self, titulo: str):
        marco = tk.Frame(self.contenedor, bg="white")
        marco.pack(fill="x", padx=12, pady=(6, 0))

        encabezado = tk.Frame(marco, bg="white")
        encabezado.pack(fill="x")
        icono = tk.Label(encabezado, text="⌄", font=("Segoe UI", 11, "bold"), bg="white", cursor="hand2")
        icono.pack(side="left", padx=(0, 6))
        lbl = tk.Label(encabezado, text=titulo, font=("Segoe UI", 11, "bold"), bg="white", cursor="hand2")
        lbl.pack(side="left")
        contador = tk.Label(encabezado, text="(0)", font=("Segoe UI", 9), bg="white", fg=GRIS_TEXTO)
        contador.pack(side="left", padx=(6, 0))

        cuerpo = tk.Frame(marco, bg="white")
        # Colapsado por defecto (no se hace pack todavía)

        info = {"marco": marco, "cuerpo": cuerpo, "icono": icono, "contador": contador, "abierto": False}
        self.secciones[titulo] = info

        toggle = lambda e=None, t=titulo: self._alternar_seccion(t)
        icono.bind("<Button-1>", toggle)
        lbl.bind("<Button-1>", toggle)

        tk.Frame(marco, bg=GRIS_BORDE, height=1).pack(fill="x", pady=(6, 0))

    def _alternar_seccion(self, titulo: str):
        info = self.secciones[titulo]
        info["abierto"] = not info["abierto"]
        info["icono"].config(text="⌃" if info["abierto"] else "⌄")
        if info["abierto"]:
            info["cuerpo"].pack(fill="x", pady=(4, 8))
            self._poblar_seccion(titulo)
        else:
            info["cuerpo"].pack_forget()

    def _poblar_seccion(self, titulo: str):
        info = self.secciones[titulo]
        for w in info["cuerpo"].winfo_children():
            w.destroy()

        if titulo == "Retirados recientemente":
            casos = listar_retirados_recientes(limite=25)
        else:
            casos = listar_casos_por_estado(titulo)

        if not casos:
            tk.Label(info["cuerpo"], text="No hay casos en este estado.", font=("Segoe UI", 9),
                     bg="white", fg=GRIS_TEXTO).pack(anchor="w", padx=20)
            return

        for c in casos:
            fila = tk.Frame(info["cuerpo"], bg="white", highlightthickness=1,
                            highlightbackground=GRIS_BORDE, cursor="hand2")
            fila.pack(fill="x", padx=20, pady=2)
            texto = (f"Caso #{c['id']}  —  {c['cliente']}  —  {c['descripcion_equipo']}"
                    f"  ({_formatear_fecha_hora(c['fecha_estado'])})")
            lbl = tk.Label(fila, text=texto, font=("Segoe UI", 9), bg="white", anchor="w")
            lbl.pack(fill="x", padx=8, pady=4)
            for widget in (fila, lbl):
                widget.bind("<Button-1>", lambda e, cid=c["id"]: self._abrir_detalle(cid))

    def _abrir_detalle(self, caso_id: int):
        VentanaDetalleCaso(self, caso_id, self.panel_padre.usuario_actual,
                          on_cambio=self.panel_padre.refrescar_todo)

    def cargar(self):
        conteos = conteos_dashboard()
        conteos["Retirados recientemente"] = conteos.get("Retirado", 0)
        for titulo, info in self.secciones.items():
            info["contador"].config(text=f"({conteos.get(titulo, 0)})")
            if info["abierto"]:
                self._poblar_seccion(titulo)


# ============================================================
# PESTAÑA: EQUIPOS (catálogo)
# ============================================================
class _TabEquipos(tk.Frame):
    def __init__(self, parent, panel_padre):
        super().__init__(parent, bg="white")
        self.panel_padre = panel_padre
        self._construir_filtros()
        self._construir_tabla()
        self.cargar()

    def _construir_filtros(self):
        barra = tk.Frame(self, bg=GRIS_FONDO)
        barra.pack(fill="x")
        interior = tk.Frame(barra, bg=GRIS_FONDO)
        interior.pack(fill="x", padx=10, pady=8)
        self.var_busqueda = tk.StringVar()
        entry = tk.Entry(interior, textvariable=self.var_busqueda, font=("Segoe UI", 9), width=25)
        entry.pack(side="right")
        entry.bind("<KeyRelease>", lambda e: self.cargar())
        tk.Label(interior, text="🔍", font=("Segoe UI", 10), bg=GRIS_FONDO).pack(side="right", padx=(0, 4))

    def _construir_tabla(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=0, pady=(4, 0))
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        columnas = ("descripcion", "tipo_equipo", "serie", "cliente")
        encabezados = ("DESCRIPCIÓN DEL EQUIPO", "TIPO EQUIPO", "N° SERIE", "CLIENTE")
        anchos = (280, 150, 130, 220)

        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho, anchor="w" if col in ("descripcion", "cliente") else "center")

        sb_y = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb_y.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_y_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_y_h.set)
        sb_y_h.grid(row=1, column=0, sticky="ew")

    def cargar(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        for e in buscar_equipos(texto_busqueda=self.var_busqueda.get()):
            self.tabla.insert("", "end", iid=str(e["id"]), values=(
                e["descripcion"], e["tipo_equipo"] or "—", e["nro_serie"] or "—", e["cliente"],
            ))


# ============================================================
# ASISTENTE: ENTRADA DE EQUIPO (2 pasos)
# ============================================================
class VentanaEntradaEquipo(tk.Toplevel):
    def __init__(self, parent, usuario_actual, on_guardado=None):
        super().__init__(parent)
        self.usuario_actual = usuario_actual
        self.on_guardado = on_guardado
        self.cliente_seleccionado = None  # dict o None (walk-in / texto libre)
        self.tipo_equipo_id = None

        self.title("Entrada de Equipos")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()
        self.transient(parent)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_titulo()

        self.frame_paso1 = tk.Frame(self, bg="white")
        self.frame_paso2 = tk.Frame(self, bg="white")
        self.frame_paso1.grid(row=1, column=0, sticky="nsew")

        self._construir_paso1()
        self._construir_paso2()

        self.minsize(560, 480)
        ajustar_tamaño_ventana(self, ancho_min=560, alto_min=480)
        self.entry_nombre.focus()

    def _construir_titulo(self):
        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text="Entrada de Equipos", font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

    # ---------------- PASO 1: CLIENTE + EQUIPO ----------------
    def _construir_paso1(self):
        contenedor = tk.Frame(self.frame_paso1, bg="white")
        contenedor.pack(fill="both", expand=True, padx=16, pady=16)

        # --- Sección Cliente ---
        seccion_cliente = tk.LabelFrame(contenedor, text="Cliente", font=("Segoe UI", 9, "bold"),
                                        bg="white", padx=10, pady=10)
        seccion_cliente.pack(fill="x", pady=(0, 12))
        seccion_cliente.grid_columnconfigure(1, weight=1)

        tk.Label(seccion_cliente, text="Nombre:", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=0, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_nombre = tk.StringVar()
        self.entry_nombre = tk.Entry(seccion_cliente, textvariable=self.var_nombre, font=("Segoe UI", 10))
        self.entry_nombre.grid(row=0, column=1, sticky="ew", pady=4)
        forzar_mayusculas(self.entry_nombre, self.var_nombre)

        tk.Label(seccion_cliente, text="CI/RUC:", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=1, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_documento = tk.StringVar()
        tk.Entry(seccion_cliente, textvariable=self.var_documento, font=("Segoe UI", 10)).grid(
            row=1, column=1, sticky="ew", pady=4)

        tk.Label(seccion_cliente, text="Dirección:", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=2, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_direccion = tk.StringVar()
        entry_dir = tk.Entry(seccion_cliente, textvariable=self.var_direccion, font=("Segoe UI", 10))
        entry_dir.grid(row=2, column=1, sticky="ew", pady=4)
        forzar_mayusculas(entry_dir, self.var_direccion)

        tk.Label(seccion_cliente, text="Teléfono:", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=3, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_telefono = tk.StringVar()
        tk.Entry(seccion_cliente, textvariable=self.var_telefono, font=("Segoe UI", 10)).grid(
            row=3, column=1, sticky="ew", pady=4)

        tk.Button(seccion_cliente, text="🔍 F2 Buscar Cliente", font=("Segoe UI", 9, "bold"),
                  bg="white", relief="solid", bd=1, cursor="hand2",
                  command=self._abrir_buscar_cliente).grid(row=0, column=2, rowspan=2, padx=(10, 0))

        # --- Sección Equipo ---
        seccion_equipo = tk.LabelFrame(contenedor, text="Equipo", font=("Segoe UI", 9, "bold"),
                                       bg="white", padx=10, pady=10)
        seccion_equipo.pack(fill="x")
        seccion_equipo.grid_columnconfigure(1, weight=1)

        tk.Label(seccion_equipo, text="Tipo Equipo:", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=0, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_tipo_equipo = tk.StringVar()
        self.combo_tipo_equipo = ttk.Combobox(seccion_equipo, textvariable=self.var_tipo_equipo,
                                              font=("Segoe UI", 10))
        self.combo_tipo_equipo.grid(row=0, column=1, sticky="ew", pady=4)
        self._cargar_tipos_equipo()
        tk.Button(seccion_equipo, text="🔍 F3 Buscar Equipo", font=("Segoe UI", 9, "bold"),
                  bg="white", relief="solid", bd=1, cursor="hand2",
                  command=self._abrir_buscar_equipo).grid(row=0, column=2, padx=(10, 0))

        tk.Label(seccion_equipo, text="N° Serie/Identificación:", font=("Segoe UI", 9, "bold"),
                 bg="white").grid(row=1, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_serie = tk.StringVar()
        entry_serie = tk.Entry(seccion_equipo, textvariable=self.var_serie, font=("Segoe UI", 10))
        entry_serie.grid(row=1, column=1, sticky="ew", pady=4)
        forzar_mayusculas(entry_serie, self.var_serie)

        tk.Label(seccion_equipo, text="Descripción del Equipo:", font=("Segoe UI", 9, "bold"),
                 bg="white").grid(row=2, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_descripcion = tk.StringVar()
        entry_desc = tk.Entry(seccion_equipo, textvariable=self.var_descripcion, font=("Segoe UI", 10))
        entry_desc.grid(row=2, column=1, sticky="ew", pady=4, columnspan=2)
        forzar_mayusculas(entry_desc, self.var_descripcion)

        botones = tk.Frame(self.frame_paso1, bg="white")
        botones.pack(fill="x", padx=16, pady=(0, 16), side="bottom")
        tk.Button(botones, text="✕ ESC Cancelar", font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="left")
        tk.Button(botones, text="➕ F12 Siguiente", font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                  fg="white", relief="flat", padx=14, command=self._ir_a_paso2).pack(side="right")

        self.bind("<F12>", lambda e: self._ir_a_paso2())
        self.bind("<Escape>", lambda e: self.destroy())

    def _cargar_tipos_equipo(self):
        self.tipos_equipo = listar_tipos_equipo()
        self.combo_tipo_equipo["values"] = [t["nombre"] for t in self.tipos_equipo]

    def _abrir_buscar_cliente(self):
        from ventanas_auxiliares_venta import VentanaAsignarCliente
        VentanaAsignarCliente(self, on_seleccionado=self._al_elegir_cliente)

    def _al_elegir_cliente(self, cliente):
        self.cliente_seleccionado = cliente
        if cliente:
            self.var_nombre.set(cliente["nombre"])
            self.var_documento.set(cliente.get("nro_documento", ""))
            self.var_direccion.set(cliente.get("direccion", ""))
            self.var_telefono.set(cliente.get("telefono", ""))

    def _abrir_buscar_equipo(self):
        VentanaBuscarEquipo(self, on_seleccionado=self._al_elegir_equipo)

    def _al_elegir_equipo(self, equipo):
        self.var_tipo_equipo.set(equipo["tipo_equipo"] or "")
        self.var_serie.set(equipo["nro_serie"] or "")
        self.var_descripcion.set(equipo["descripcion"])

    def _ir_a_paso2(self):
        if not self.var_descripcion.get().strip():
            messagebox.showwarning("Falta la descripción", "Ingresa la descripción del equipo antes de continuar.",
                                   parent=self)
            return
        self.frame_paso1.grid_remove()
        self.frame_paso2.grid(row=1, column=0, sticky="nsew")

    # ---------------- PASO 2: PRIORIDAD + OBSERVACIONES ----------------
    def _construir_paso2(self):
        contenedor = tk.Frame(self.frame_paso2, bg="white")
        contenedor.pack(fill="both", expand=True, padx=16, pady=16)

        tk.Label(contenedor, text="Prioridad:", font=("Segoe UI", 9, "bold"), bg="white").pack(anchor="w")
        self.var_prioridad = tk.StringVar(value="Media")
        frame_prioridad = tk.Frame(contenedor, bg="white")
        frame_prioridad.pack(anchor="w", pady=(4, 14))
        for p in PRIORIDADES:
            tk.Radiobutton(frame_prioridad, text=p, variable=self.var_prioridad, value=p,
                          bg="white", font=("Segoe UI", 9),
                          fg=COLOR_PRIORIDAD.get(p, "#1e293b")).pack(side="left", padx=(0, 14))

        tk.Label(contenedor, text="Motivo de Ingreso / Observaciones:", font=("Segoe UI", 9, "bold"),
                bg="white").pack(anchor="w")
        self.texto_observaciones = tk.Text(contenedor, font=("Segoe UI", 10), height=8,
                                           relief="solid", bd=1)
        self.texto_observaciones.pack(fill="both", expand=True, pady=(4, 14))

        tk.Label(contenedor, text=f"Recibido por: {self.usuario_actual.get('nombre_completo', '')}",
                font=("Segoe UI", 9), bg="white", fg=GRIS_TEXTO).pack(anchor="w")

        botones = tk.Frame(self.frame_paso2, bg="white")
        botones.pack(fill="x", padx=16, pady=(0, 16), side="bottom")
        tk.Button(botones, text="◀ Atrás", font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self._volver_a_paso1).pack(side="left")
        tk.Button(botones, text="✕ ESC Cancelar", font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="left", padx=(8, 0))
        tk.Button(botones, text="💾 F12 Guardar", font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                  fg="white", relief="flat", padx=14, command=self._guardar).pack(side="right")

    def _volver_a_paso1(self):
        self.frame_paso2.grid_remove()
        self.frame_paso1.grid(row=1, column=0, sticky="nsew")

    def _guardar(self):
        tipo_equipo_texto = self.var_tipo_equipo.get().strip()
        tipo_equipo_id = None
        for t in self.tipos_equipo:
            if t["nombre"] == tipo_equipo_texto:
                tipo_equipo_id = t["id"]
                break
        if tipo_equipo_texto and tipo_equipo_id is None:
            # Tipo de equipo nuevo escrito a mano: lo agregamos al catálogo
            crear_tipo_equipo(tipo_equipo_texto)
            for t in listar_tipos_equipo():
                if t["nombre"] == tipo_equipo_texto:
                    tipo_equipo_id = t["id"]
                    break

        cliente_id = self.cliente_seleccionado["id"] if self.cliente_seleccionado else None

        ok, msg, caso_id = crear_caso(
            cliente_id=cliente_id,
            cliente_nombre=self.var_nombre.get(),
            cliente_documento=self.var_documento.get(),
            cliente_direccion=self.var_direccion.get(),
            cliente_telefono=self.var_telefono.get(),
            tipo_equipo_id=tipo_equipo_id,
            tipo_equipo_texto=tipo_equipo_texto,
            nro_serie=self.var_serie.get(),
            descripcion_equipo=self.var_descripcion.get(),
            prioridad=self.var_prioridad.get(),
            observaciones=self.texto_observaciones.get("1.0", "end").strip(),
            usuario_id=self.usuario_actual.get("id"),
        )
        if not ok:
            messagebox.showerror("No se pudo guardar", msg, parent=self)
            return

        messagebox.showinfo("Caso registrado", msg, parent=self)
        if self.on_guardado:
            self.on_guardado()
        self.destroy()


# ============================================================
# BUSCAR EQUIPO (F3)
# ============================================================
class VentanaBuscarEquipo(tk.Toplevel):
    def __init__(self, parent, on_seleccionado):
        super().__init__(parent)
        self.on_seleccionado = on_seleccionado

        self.title("Buscar Equipo")
        self.geometry("640x440")
        self.minsize(500, 340)
        self.resizable(True, True)
        self.configure(bg="white")
        self.grab_set()
        self.transient(parent)

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text="Buscar Equipo (F3)", font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

        frame_busqueda = tk.Frame(self, bg="white")
        frame_busqueda.grid(row=1, column=0, sticky="ew", padx=10, pady=8)
        tk.Label(frame_busqueda, text="Buscar:", font=("Segoe UI", 9), bg="white").pack(side="left")
        self.var_busqueda = tk.StringVar()
        entry = tk.Entry(frame_busqueda, textvariable=self.var_busqueda, font=("Segoe UI", 10), width=40)
        entry.pack(side="left", padx=8, fill="x", expand=True)
        entry.bind("<KeyRelease>", lambda e: self._buscar())
        entry.focus()

        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=2, column=0, sticky="nsew", padx=10)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        columnas = ("descripcion", "tipo_equipo", "serie", "cliente")
        encabezados = ("DESCRIPCIÓN DEL EQUIPO", "TIPO EQUIPO", "N° SERIE", "CLIENTE")
        anchos = (240, 120, 100, 160)

        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho, anchor="w" if col in ("descripcion", "cliente") else "center")

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
        tk.Button(frame_botones, text="Seleccionar", font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, width=14, command=self._confirmar_seleccion).pack(pady=8)

        self.equipos_por_id = {}
        self._buscar()

    def _buscar(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        self.equipos_por_id = {}
        for e in buscar_equipos(texto_busqueda=self.var_busqueda.get()):
            self.tabla.insert("", "end", iid=str(e["id"]), values=(
                e["descripcion"], e["tipo_equipo"] or "—", e["nro_serie"] or "—", e["cliente"],
            ))
            self.equipos_por_id[str(e["id"])] = e

    def _confirmar_seleccion(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Selecciona un equipo", "Elige un equipo de la lista.", parent=self)
            return
        equipo = self.equipos_por_id[seleccion[0]]
        self.destroy()
        self.on_seleccionado(equipo)


# ============================================================
# DETALLE / GESTIÓN DE UN CASO
# ============================================================
class VentanaDetalleCaso(tk.Toplevel):
    def __init__(self, parent, caso_id: int, usuario_actual, on_cambio=None):
        super().__init__(parent)
        self.caso_id = caso_id
        self.usuario_actual = usuario_actual
        self.on_cambio = on_cambio

        self.caso = obtener_caso(caso_id)
        if self.caso is None:
            self.destroy()
            return

        self.title(f"Caso Nro. {caso_id}")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()
        self.transient(parent)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_titulo()
        self._construir_cuerpo()

        self.minsize(560, 520)
        ajustar_tamaño_ventana(self, ancho_min=560, alto_min=520)

    def _construir_titulo(self):
        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text=f"Caso Nro. {self.caso_id}", font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)
        if self.caso["anulado"]:
            tk.Label(barra, text="ANULADO", font=("Segoe UI", 9, "bold"),
                    bg=ROJO, fg="white", padx=8).pack(side="right", padx=15, pady=6)

    def _construir_cuerpo(self):
        c = self.caso
        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=1, column=0, sticky="nsew", padx=16, pady=16)
        contenedor.grid_columnconfigure(1, weight=1)

        def fila(r, etiqueta, valor):
            tk.Label(contenedor, text=etiqueta, font=("Segoe UI", 9, "bold"), bg="white").grid(
                row=r, column=0, sticky="ne", pady=3, padx=(0, 10))
            tk.Label(contenedor, text=valor, font=("Segoe UI", 9), bg="white",
                    wraplength=360, justify="left", anchor="w").grid(row=r, column=1, sticky="w", pady=3)

        fila(0, "Cliente:", c["cliente_nombre"])
        fila(1, "CI/RUC:", c["cliente_documento"] or "—")
        fila(2, "Teléfono:", c["cliente_telefono"] or "—")
        fila(3, "Tipo Equipo:", c["tipo_equipo"] or "—")
        fila(4, "N° Serie:", c["nro_serie"] or "—")
        fila(5, "Descripción:", c["descripcion_equipo"])
        fila(6, "Fecha Entrada:", _formatear_fecha_hora(c["fecha_entrada"]))
        fila(7, "Recibido por:", c["recibido_por"] or "—")

        tk.Label(contenedor, text="Prioridad:", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=8, column=0, sticky="ne", pady=3, padx=(0, 10))
        tk.Label(contenedor, text=c["prioridad"], font=("Segoe UI", 9, "bold"), bg="white",
                fg=COLOR_PRIORIDAD.get(c["prioridad"], "#1e293b")).grid(row=8, column=1, sticky="w", pady=3)

        tk.Label(contenedor, text="Estado:", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=9, column=0, sticky="ne", pady=(3, 10), padx=(0, 10))
        frame_estado = tk.Frame(contenedor, bg="white")
        frame_estado.grid(row=9, column=1, sticky="w", pady=(3, 10))
        tk.Label(frame_estado, text=f"  {c['estado']}  ", font=("Segoe UI", 9, "bold"),
                bg=COLOR_ESTADO.get(c["estado"], "#1e293b"), fg="white").pack(side="left")

        if not c["anulado"] and c["estado"] != "Retirado":
            self.var_nuevo_estado = tk.StringVar(value=c["estado"])
            combo = ttk.Combobox(frame_estado, textvariable=self.var_nuevo_estado, values=ESTADOS,
                                 state="readonly", width=22, font=("Segoe UI", 9))
            combo.pack(side="left", padx=(10, 6))
            tk.Button(frame_estado, text="Actualizar Estado", font=("Segoe UI", 8, "bold"),
                     bg="white", relief="solid", bd=1, cursor="hand2",
                     command=self._cambiar_estado).pack(side="left")

        tk.Label(contenedor, text="Observaciones:", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=10, column=0, sticky="ne", pady=(3, 0), padx=(0, 10))
        self.texto_observaciones = tk.Text(contenedor, font=("Segoe UI", 9), height=6,
                                           relief="solid", bd=1)
        self.texto_observaciones.grid(row=10, column=1, sticky="ew", pady=(3, 0))
        self.texto_observaciones.insert("1.0", c["observaciones"])
        if c["anulado"]:
            self.texto_observaciones.config(state="disabled")

        botones = tk.Frame(self, bg="white")
        botones.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))
        if not c["anulado"]:
            tk.Button(botones, text="💾 Guardar Observaciones", font=("Segoe UI", 9, "bold"),
                     bg="white", relief="solid", bd=1, cursor="hand2",
                     command=self._guardar_observaciones).pack(side="left")
            tk.Button(botones, text="🚫 Anular Caso", font=("Segoe UI", 9, "bold"),
                     bg="white", fg=ROJO, relief="solid", bd=1, cursor="hand2",
                     command=self._anular).pack(side="left", padx=(8, 0))
        tk.Button(botones, text="Cerrar", font=("Segoe UI", 9, "bold"), bg="white",
                 relief="solid", bd=1, command=self.destroy).pack(side="right")

    def _cambiar_estado(self):
        nuevo_estado = self.var_nuevo_estado.get()
        if nuevo_estado == self.caso["estado"]:
            return
        if nuevo_estado == "Retirado":
            if not messagebox.askyesno("Confirmar retiro",
                                       f"¿Marcar el caso Nro. {self.caso_id} como Retirado?\n\n"
                                       "El cliente se está llevando el equipo.", parent=self):
                return
        ok, msg = cambiar_estado_caso(self.caso_id, nuevo_estado)
        if not ok:
            messagebox.showerror("No se pudo actualizar", msg, parent=self)
            return
        messagebox.showinfo("Estado actualizado", msg, parent=self)
        if self.on_cambio:
            self.on_cambio()
        self.destroy()

    def _guardar_observaciones(self):
        texto = self.texto_observaciones.get("1.0", "end").strip()
        ok, msg = actualizar_observaciones(self.caso_id, texto)
        if ok and self.on_cambio:
            self.on_cambio()
        messagebox.showinfo("Guardado", msg, parent=self)

    def _anular(self):
        if not messagebox.askyesno("Anular Caso",
                                   f"¿Anular el caso Nro. {self.caso_id}?\n\n"
                                   "Esta acción no se puede deshacer.", parent=self):
            return
        ok, msg = anular_caso(self.caso_id)
        if not ok:
            messagebox.showerror("No se pudo anular", msg, parent=self)
            return
        messagebox.showinfo("Caso anulado", msg, parent=self)
        if self.on_cambio:
            self.on_cambio()
        self.destroy()
