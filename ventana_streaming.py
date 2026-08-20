"""
ventana_streaming.py
Módulo Alquiler de Cuentas de Streaming (Netflix, HBO Max, Disney+,
YouTube Premium, Spotify, etc.): Cuentas con sus perfiles/cupos,
Combos de varias plataformas, Suscripciones de clientes (con cobro y
renovación reutilizando el motor de Ventas de siempre) y un Dashboard
con alertas de seguridad (rotación de contraseñas, vencimientos).
"""
import datetime
import tkinter as tk
from tkinter import ttk, messagebox

from models_streaming import (
    MODALIDADES, ESTADOS_CUENTA, FORMAS_PAGO,
    listar_plataformas, crear_plataforma, cambiar_estado_plataforma,
    listar_cuentas, obtener_cuenta, crear_cuenta, editar_cuenta, cambiar_estado_cuenta,
    rotar_password_cuenta, eliminar_cuenta, cuentas_necesitan_rotacion_password,
    listar_perfiles_cuenta, editar_perfil, listar_perfiles_libres,
    listar_combos, crear_combo, cambiar_estado_combo, eliminar_combo,
    crear_suscripcion, obtener_suscripcion_detalle, listar_suscripciones, suscripciones_por_vencer,
    registrar_pago_renovacion, cancelar_suscripcion, listar_historial_pagos,
    conteos_dashboard, rentabilidad_por_plataforma,
)
from utilidades_ui import ajustar_tamaño_ventana, forzar_mayusculas, formatear_gs, habilitar_deseleccion_treeview
from traducciones import t

AZUL_RIBBON = "#1d5fd6"
GRIS_FONDO = "#f4f5f7"
VERDE = "#16a34a"
ROJO = "#dc2626"
NARANJA = "#d97706"
GRIS_TEXTO = "#6b7280"

COLOR_ESTADO_SUS = {"Activa": "#16a34a", "Vencida": "#d97706", "Cancelada": "#6b7280"}


def _crear_seccion_scrollable(parent):
    """Envuelve contenido en un Canvas + Scrollbar vertical, para que si el
    contenido no entra en el alto disponible de la ventana, se pueda
    desplazar en vez de quedar cortado/invisible. Devuelve
    (frame_exterior, frame_interior): frame_exterior se grid()-ea donde se
    necesite, y frame_interior es donde se agrega el contenido real."""
    frame_exterior = tk.Frame(parent, bg="white")
    canvas = tk.Canvas(frame_exterior, bg="white", highlightthickness=0)
    scrollbar = ttk.Scrollbar(frame_exterior, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    frame_interior = tk.Frame(canvas, bg="white")
    id_ventana_interior = canvas.create_window((0, 0), window=frame_interior, anchor="nw")

    def _actualizar_scrollregion(_e=None):
        canvas.configure(scrollregion=canvas.bbox("all"))
    frame_interior.bind("<Configure>", _actualizar_scrollregion)

    def _ajustar_ancho_interior(event):
        canvas.itemconfig(id_ventana_interior, width=event.width)
    canvas.bind("<Configure>", _ajustar_ancho_interior)

    def _rueda_mouse(event):
        if event.num == 5 or event.delta < 0:
            canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            canvas.yview_scroll(-1, "units")

    def _activar_scroll(_e=None):
        canvas.bind_all("<MouseWheel>", _rueda_mouse)
        canvas.bind_all("<Button-4>", _rueda_mouse)
        canvas.bind_all("<Button-5>", _rueda_mouse)

    def _desactivar_scroll(_e=None):
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    frame_exterior.bind("<Enter>", _activar_scroll)
    frame_exterior.bind("<Leave>", _desactivar_scroll)

    return frame_exterior, frame_interior


# ============================================================
# PANEL PRINCIPAL
# ============================================================
class PanelStreaming(tk.Frame):
    def __init__(self, parent, usuario_actual):
        super().__init__(parent, bg="white")
        self.usuario_actual = usuario_actual

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_suscripciones = _TabSuscripciones(self.notebook, self)
        self.tab_cuentas = _TabCuentas(self.notebook, self)
        self.tab_combos = _TabCombos(self.notebook, self)
        self.tab_dashboard = _TabDashboard(self.notebook, self)

        self.notebook.add(self.tab_suscripciones, text=t("stream_tab_suscripciones"))
        self.notebook.add(self.tab_cuentas, text=t("stream_tab_cuentas"))
        self.notebook.add(self.tab_combos, text=t("stream_tab_combos"))
        self.notebook.add(self.tab_dashboard, text=t("stream_tab_dashboard"))

        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self.refrescar_todo())

    def refrescar_todo(self):
        self.tab_suscripciones.cargar()
        self.tab_cuentas.cargar()
        self.tab_combos.cargar()
        self.tab_dashboard.cargar()


# ============================================================
# PESTAÑA: SUSCRIPCIONES (operación diaria con clientes)
# ============================================================
class _TabSuscripciones(tk.Frame):
    def __init__(self, parent, panel_padre: PanelStreaming):
        super().__init__(parent, bg="white")
        self.panel_padre = panel_padre
        self._construir()
        self.cargar()

    def _construir(self):
        barra = tk.Frame(self, bg="white")
        barra.pack(fill="x", pady=(6, 6))
        tk.Button(barra, text="➕ Nueva Suscripción", font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                  fg="white", relief="flat", padx=10, pady=5, cursor="hand2",
                  command=self._nueva_suscripcion).pack(side="left")
        tk.Button(barra, text="💳 Registrar Pago / Renovar", font=("Segoe UI", 9, "bold"), bg=VERDE,
                  fg="white", relief="flat", padx=10, pady=5, cursor="hand2",
                  command=self._registrar_pago).pack(side="left", padx=(8, 0))
        tk.Button(barra, text="🔑 Ver Credenciales", font=("Segoe UI", 9, "bold"), bg="#0891b2",
                  fg="white", relief="flat", padx=10, pady=5, cursor="hand2",
                  command=self._ver_credenciales).pack(side="left", padx=(8, 0))
        tk.Button(barra, text="✕ Cancelar Suscripción", font=("Segoe UI", 9, "bold"), bg="#6b7280",
                  fg="white", relief="flat", padx=10, pady=5, cursor="hand2",
                  command=self._cancelar).pack(side="left", padx=(8, 0))

        self.var_incluir_vencidas = tk.BooleanVar(value=False)
        tk.Checkbutton(barra, text="Incluir vencidas/canceladas", variable=self.var_incluir_vencidas,
                       bg="white", font=("Segoe UI", 9), command=self.cargar).pack(side="left", padx=(14, 0))

        self.var_busqueda = tk.StringVar()
        entry = tk.Entry(barra, textvariable=self.var_busqueda, font=("Segoe UI", 9), width=22)
        entry.pack(side="right")
        entry.bind("<KeyRelease>", lambda e: self.cargar())
        tk.Label(barra, text="🔍 Cliente:", font=("Segoe UI", 9), bg="white").pack(side="right", padx=(0, 6))

        columnas = ("cliente", "modalidad", "plataformas", "vencimiento", "dias", "precio", "estado", "pago")
        encabezados = ("CLIENTE", "MODALIDAD", "PLATAFORMA(S)", "VENCIMIENTO", "DÍAS REST.", "PRECIO", "ESTADO",
                      "FORMA DE PAGO")
        anchos = (150, 130, 200, 100, 90, 100, 90, 130)
        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho, anchor="w" if col in ("cliente", "plataformas") else "center")
        sb = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        sb_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_h.set)
        sb_h.grid(row=1, column=0, sticky="ew")
        self.tabla.tag_configure("por_vencer", foreground=NARANJA)
        self.tabla.tag_configure("vencida", foreground=ROJO)
        self.tabla.tag_configure("cancelada", foreground=GRIS_TEXTO)
        self.tabla.bind("<Double-1>", lambda e: self._ver_credenciales())

    def _suscripcion_seleccionada(self):
        seleccion = self.tabla.selection()
        return int(seleccion[0]) if seleccion else None

    def _nueva_suscripcion(self):
        VentanaNuevaSuscripcion(self, on_creado=self.cargar)

    def _registrar_pago(self):
        sid = self._suscripcion_seleccionada()
        if sid is None:
            messagebox.showinfo("Selecciona una suscripción", "Elegí un cliente de la lista primero.",
                               parent=self)
            return
        VentanaRegistrarPago(self, self.panel_padre.usuario_actual, sid, on_pagado=self.cargar)

    def _ver_credenciales(self):
        sid = self._suscripcion_seleccionada()
        if sid is None:
            return
        VentanaDetalleSuscripcion(self, sid, on_cambio=self.cargar)

    def _cancelar(self):
        sid = self._suscripcion_seleccionada()
        if sid is None:
            messagebox.showinfo("Selecciona una suscripción", "Elegí un cliente de la lista primero.",
                               parent=self)
            return
        if not messagebox.askyesno("Cancelar suscripción",
                                   "¿Cancelar esta suscripción? El/los perfil(es) quedarán libres "
                                   "para alquilarlos a otro cliente.", parent=self):
            return
        cancelar_suscripcion(sid)
        self.cargar()

    def cargar(self):
        for f in self.tabla.get_children():
            self.tabla.delete(f)
        for s in listar_suscripciones(busqueda=self.var_busqueda.get(),
                                      solo_activas=not self.var_incluir_vencidas.get()):
            if s["estado"] == "Cancelada":
                tag = "cancelada"
            elif s["estado"] == "Vencida":
                tag = "vencida"
            elif s["dias_restantes"] <= 5:
                tag = "por_vencer"
            else:
                tag = ""
            self.tabla.insert("", "end", iid=str(s["id"]), tags=(tag,), values=(
                s["cliente"], s["modalidad"], s["plataformas"], s["fecha_vencimiento"],
                s["dias_restantes"], formatear_gs(s["precio_mensual"]), s["estado"], s["forma_pago"],
            ))


# ============================================================
# PESTAÑA: CUENTAS
# ============================================================
class _TabCuentas(tk.Frame):
    def __init__(self, parent, panel_padre: PanelStreaming):
        super().__init__(parent, bg="white")
        self.panel_padre = panel_padre
        self._construir()
        self.cargar()

    def _construir(self):
        barra = tk.Frame(self, bg="white")
        barra.pack(fill="x", pady=(6, 6))
        tk.Button(barra, text="🔐➕ Nueva Cuenta", font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                  fg="white", relief="flat", padx=10, pady=5, cursor="hand2",
                  command=self._nueva_cuenta).pack(side="left")
        tk.Button(barra, text="⚙ Gestionar Plataformas", font=("Segoe UI", 9, "bold"), bg="#0891b2",
                  fg="white", relief="flat", padx=10, pady=5, cursor="hand2",
                  command=self._gestionar_plataformas).pack(side="left", padx=(8, 0))

        self.var_incluir_inactivas = tk.BooleanVar(value=True)
        tk.Checkbutton(barra, text="Incluir suspendidas/vencidas", variable=self.var_incluir_inactivas,
                       bg="white", font=("Segoe UI", 9), command=self.cargar).pack(side="left", padx=(14, 0))

        columnas = ("plataforma", "email", "plan", "perfiles", "costo", "prox_pago", "password", "estado")
        encabezados = ("PLATAFORMA", "EMAIL/USUARIO", "PLAN", "PERFILES", "COSTO MENSUAL",
                      "PRÓX. PAGO PROVEEDOR", "ÚLT. CAMBIO PASS.", "ESTADO")
        anchos = (110, 180, 150, 90, 110, 140, 130, 100)
        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho, anchor="w" if col in ("email", "plan") else "center")
        sb = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        sb_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_h.set)
        sb_h.grid(row=1, column=0, sticky="ew")
        self.tabla.tag_configure("inactiva", foreground=GRIS_TEXTO)
        self.tabla.bind("<Double-1>", lambda e: self._abrir_seleccionada())

    def _nueva_cuenta(self):
        VentanaFichaCuenta(self, on_guardado=self.cargar)

    def _gestionar_plataformas(self):
        VentanaGestionPlataformas(self, on_cambio=self.cargar)

    def _abrir_seleccionada(self):
        seleccion = self.tabla.selection()
        if seleccion:
            VentanaFichaCuenta(self, cuenta_id=int(seleccion[0]), on_guardado=self.cargar)

    def cargar(self):
        for f in self.tabla.get_children():
            self.tabla.delete(f)
        for c in listar_cuentas(incluir_inactivas=self.var_incluir_inactivas.get()):
            tags = () if c["estado"] == "Activa" else ("inactiva",)
            self.tabla.insert("", "end", iid=str(c["id"]), tags=tags, values=(
                c["plataforma"], c["email"], c["plan_nombre"] or "—",
                f"{c['perfiles_ocupados']}/{c['max_perfiles']}", formatear_gs(c["costo_mensual"]),
                c["fecha_proximo_pago_proveedor"] or "—", c["fecha_ultimo_cambio_password"], c["estado"],
            ))


# ============================================================
# PESTAÑA: COMBOS
# ============================================================
class _TabCombos(tk.Frame):
    def __init__(self, parent, panel_padre: PanelStreaming):
        super().__init__(parent, bg="white")
        self.panel_padre = panel_padre
        self._construir()
        self.cargar()

    def _construir(self):
        barra = tk.Frame(self, bg="white")
        barra.pack(fill="x", pady=(6, 6))
        tk.Button(barra, text="📦➕ Nuevo Combo", font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                  fg="white", relief="flat", padx=10, pady=5, cursor="hand2",
                  command=self._nuevo_combo).pack(side="left")
        tk.Button(barra, text="🚫 Activar/Desactivar", font=("Segoe UI", 9, "bold"), bg="#6b7280",
                  fg="white", relief="flat", padx=10, pady=5, cursor="hand2",
                  command=self._alternar_estado).pack(side="left", padx=(8, 0))
        tk.Button(barra, text="🗑 Eliminar", font=("Segoe UI", 9, "bold"), bg=ROJO,
                  fg="white", relief="flat", padx=10, pady=5, cursor="hand2",
                  command=self._eliminar).pack(side="left", padx=(8, 0))

        columnas = ("nombre", "plataformas", "precio", "estado")
        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc in zip(columnas, ("COMBO", "PLATAFORMAS INCLUIDAS", "PRECIO MENSUAL", "ESTADO")):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=200 if col in ("nombre", "plataformas") else 130,
                              anchor="w" if col in ("nombre", "plataformas") else "center")
        sb = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        sb_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_h.set)
        sb_h.grid(row=1, column=0, sticky="ew")
        self.tabla.tag_configure("inactivo", foreground=GRIS_TEXTO)

    def _nuevo_combo(self):
        VentanaFichaCombo(self, on_guardado=self.cargar)

    def _combo_seleccionado(self):
        seleccion = self.tabla.selection()
        return int(seleccion[0]) if seleccion else None

    def _alternar_estado(self):
        combo_id = self._combo_seleccionado()
        if combo_id is None:
            messagebox.showinfo("Selecciona un combo", "Elegí un combo de la lista.", parent=self)
            return
        combo = next((c for c in listar_combos(solo_activos=False) if c["id"] == combo_id), None)
        if combo:
            cambiar_estado_combo(combo_id, not combo["activo"])
            self.cargar()

    def _eliminar(self):
        combo_id = self._combo_seleccionado()
        if combo_id is None:
            messagebox.showinfo("Selecciona un combo", "Elegí un combo de la lista.", parent=self)
            return
        if not messagebox.askyesno("Eliminar combo", "¿Eliminar este combo?", parent=self):
            return
        ok, msg = eliminar_combo(combo_id)
        if not ok:
            messagebox.showerror("No se pudo eliminar", msg, parent=self)
        self.cargar()

    def cargar(self):
        for f in self.tabla.get_children():
            self.tabla.delete(f)
        for c in listar_combos(solo_activos=False):
            tags = () if c["activo"] else ("inactivo",)
            self.tabla.insert("", "end", iid=str(c["id"]), tags=tags, values=(
                c["nombre"], " + ".join(c["plataformas"]), formatear_gs(c["precio_mensual"]),
                "Activo" if c["activo"] else "Inactivo",
            ))


# ============================================================
# PESTAÑA: DASHBOARD
# ============================================================
class _TabDashboard(tk.Frame):
    def __init__(self, parent, panel_padre: PanelStreaming):
        super().__init__(parent, bg="white")
        self.panel_padre = panel_padre
        self._construir()
        self.cargar()

    def _construir(self):
        self.frame_tarjetas = tk.Frame(self, bg="white")
        self.frame_tarjetas.pack(fill="x", pady=(6, 6))

        self.frame_alertas = tk.Frame(self, bg="white")
        self.frame_alertas.pack(fill="x", pady=(0, 10))

        tk.Label(self, text="Rentabilidad por plataforma (ingresos de suscripciones activas vs "
                            "costo de las cuentas)", font=("Segoe UI", 10, "bold"), bg="white").pack(
                 anchor="w")
        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, pady=(4, 0))
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        columnas = ("plataforma", "costo", "ingreso", "margen")
        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc in zip(columnas, ("PLATAFORMA", "COSTO MENSUAL", "INGRESO MENSUAL", "MARGEN")):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=160, anchor="center" if col != "plataforma" else "w")
        sb = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        sb_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_h.set)
        sb_h.grid(row=1, column=0, sticky="ew")
        self.tabla.tag_configure("negativo", foreground=ROJO)
        self.tabla.tag_configure("positivo", foreground=VERDE)

    def _crear_tarjeta(self, titulo, valor, color):
        marco = tk.Frame(self.frame_tarjetas, bg=color, padx=14, pady=8)
        marco.pack(side="left", padx=(0, 10))
        tk.Label(marco, text=str(valor), font=("Segoe UI", 15, "bold"), bg=color, fg="white").pack(anchor="w")
        tk.Label(marco, text=titulo, font=("Segoe UI", 8), bg=color, fg="white").pack(anchor="w")

    def cargar(self):
        for w in self.frame_tarjetas.winfo_children():
            w.destroy()
        for w in self.frame_alertas.winfo_children():
            w.destroy()

        d = conteos_dashboard()
        self._crear_tarjeta("Cuentas Activas", d["cuentas_activas"], AZUL_RIBBON)
        self._crear_tarjeta("Perfiles Ocupados", d["perfiles_ocupados"], "#0f766e")
        self._crear_tarjeta("Perfiles Libres", d["perfiles_libres"], VERDE)
        self._crear_tarjeta("Suscripciones Activas", d["suscripciones_activas"], "#7c3aed")
        self._crear_tarjeta("Ingreso Mensual Est.", formatear_gs(d["ingreso_mensual_estimado"]), VERDE)
        self._crear_tarjeta("Costo Mensual Total", formatear_gs(d["costo_mensual_total"]), NARANJA)
        color_margen = VERDE if d["margen_mensual_estimado"] >= 0 else ROJO
        self._crear_tarjeta("Margen Mensual Est.", formatear_gs(d["margen_mensual_estimado"]), color_margen)

        if d["cuentas_por_rotar_password"] > 0:
            aviso = tk.Frame(self.frame_alertas, bg="#fef3c7", relief="solid", bd=1)
            aviso.pack(fill="x", pady=(0, 4))
            tk.Label(aviso, text=f"⚠ {d['cuentas_por_rotar_password']} cuenta(s) necesitan rotar la "
                                 "contraseña (política de seguridad).", font=("Segoe UI", 9, "bold"),
                     bg="#fef3c7", fg="#92400e").pack(anchor="w", padx=10, pady=6)
        if d["suscripciones_por_vencer"] > 0:
            aviso2 = tk.Frame(self.frame_alertas, bg="#fef3c7", relief="solid", bd=1)
            aviso2.pack(fill="x")
            tk.Label(aviso2, text=f"⏰ {d['suscripciones_por_vencer']} suscripción(es) vencen dentro de "
                                  "5 días. Contactá a esos clientes para renovar.",
                     font=("Segoe UI", 9, "bold"), bg="#fef3c7", fg="#92400e").pack(anchor="w", padx=10, pady=6)

        for f in self.tabla.get_children():
            self.tabla.delete(f)
        for r in rentabilidad_por_plataforma():
            tag = "positivo" if r["margen"] >= 0 else "negativo"
            self.tabla.insert("", "end", tags=(tag,), values=(
                r["plataforma"], formatear_gs(r["costo_mensual"]), formatear_gs(r["ingreso_mensual"]),
                formatear_gs(r["margen"]),
            ))


# ============================================================
# FICHA DE CUENTA (crear/editar + gestión de perfiles + rotar password)
# ============================================================
class VentanaFichaCuenta(tk.Toplevel):
    def __init__(self, parent, cuenta_id: int = None, on_guardado=None):
        super().__init__(parent)
        self.cuenta_id = cuenta_id
        self.es_nueva = cuenta_id is None
        self.on_guardado = on_guardado

        self.title("Nueva Cuenta" if self.es_nueva else "Ficha de la Cuenta")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()
        # Sin transient(): así el gestor de ventanas no le quita los
        # botones de minimizar/maximizar a esta ventana.

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_titulo()
        self._construir_datos()
        self._construir_barra_botones()
        if not self.es_nueva:
            self._construir_perfiles()
            self._cargar_datos()

        self.minsize(680, 460)
        ajustar_tamaño_ventana(self, ancho_min=680, alto_min=560,
                              alto_max=self.winfo_screenheight() - 60)

    def _construir_titulo(self):
        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        titulo = "🔐 Nueva Cuenta" if self.es_nueva else "🔐 Ficha de la Cuenta"
        tk.Label(barra, text=titulo, font=("Segoe UI", 11, "bold"), bg=AZUL_RIBBON, fg="white").pack(
            side="left", padx=15, pady=6)

    def _construir_datos(self):
        self.frame_datos, contenedor_scroll = _crear_seccion_scrollable(self)
        self.frame_datos.grid(row=1, column=0, sticky="nsew")
        contenedor = tk.Frame(contenedor_scroll, bg="white")
        contenedor.pack(fill="both", expand=True, padx=16, pady=(12, 6))
        contenedor.grid_columnconfigure(1, weight=1)
        contenedor.grid_columnconfigure(3, weight=1)

        tk.Label(contenedor, text="Plataforma:", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=0, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_plataforma = tk.StringVar()
        self._plataformas = {p["nombre"]: p["id"] for p in listar_plataformas()}
        self.combo_plataforma = ttk.Combobox(contenedor, textvariable=self.var_plataforma, state="readonly",
                                             values=list(self._plataformas.keys()), width=20)
        self.combo_plataforma.grid(row=0, column=1, sticky="w", pady=4)
        if not self.es_nueva:
            self.combo_plataforma.config(state="disabled")

        tk.Label(contenedor, text="Plan:", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=0, column=2, sticky="e", pady=4, padx=(10, 8))
        self.var_plan = tk.StringVar()
        entry_plan = tk.Entry(contenedor, textvariable=self.var_plan, font=("Segoe UI", 10))
        entry_plan.grid(row=0, column=3, sticky="ew", pady=4)
        forzar_mayusculas(entry_plan, self.var_plan)

        tk.Label(contenedor, text="Email/Usuario:", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=1, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_email = tk.StringVar()
        tk.Entry(contenedor, textvariable=self.var_email, font=("Segoe UI", 10)).grid(
            row=1, column=1, sticky="ew", pady=4)

        tk.Label(contenedor, text="Contraseña:", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=1, column=2, sticky="e", pady=4, padx=(10, 8))
        self.var_contrasena = tk.StringVar()
        tk.Entry(contenedor, textvariable=self.var_contrasena, font=("Segoe UI", 10)).grid(
            row=1, column=3, sticky="ew", pady=4)

        tk.Label(contenedor, text="Cantidad de Perfiles/Pantallas:", font=("Segoe UI", 9, "bold"),
                 bg="white").grid(row=2, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_max_perfiles = tk.StringVar(value="1")
        entry_perfiles = tk.Entry(contenedor, textvariable=self.var_max_perfiles, font=("Segoe UI", 10), width=8)
        entry_perfiles.grid(row=2, column=1, sticky="w", pady=4)
        if not self.es_nueva:
            entry_perfiles.config(state="disabled")

        tk.Label(contenedor, text="Costo mensual (Gs):", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=2, column=2, sticky="e", pady=4, padx=(10, 8))
        self.var_costo = tk.StringVar(value="0")
        tk.Entry(contenedor, textvariable=self.var_costo, font=("Segoe UI", 10), width=14).grid(
            row=2, column=3, sticky="w", pady=4)

        tk.Label(contenedor, text="Próx. pago al proveedor:", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=3, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_prox_pago = tk.StringVar()
        _campo_fecha_streaming(contenedor, self.var_prox_pago, row=3, col=1)

        if not self.es_nueva:
            tk.Label(contenedor, text="Notas:", font=("Segoe UI", 9, "bold"), bg="white").grid(
                row=4, column=0, sticky="ne", pady=4, padx=(0, 8))
            self.texto_notas = tk.Text(contenedor, font=("Segoe UI", 9), height=2, relief="solid", bd=1)
            self.texto_notas.grid(row=4, column=1, columnspan=3, sticky="ew", pady=4)

    def _construir_barra_botones(self):
        self.frame_botones = tk.Frame(self, bg="white")
        self.frame_botones.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 10))
        self._reconstruir_botones()

    def _reconstruir_botones(self):
        for w in self.frame_botones.winfo_children():
            w.destroy()
        if self.es_nueva:
            tk.Button(self.frame_botones, text="✕ Cancelar", font=("Segoe UI", 9, "bold"), bg="white",
                      relief="solid", bd=1, command=self.destroy).pack(side="left")
            tk.Button(self.frame_botones, text="💾 Guardar", font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                      fg="white", relief="flat", padx=14, cursor="hand2", command=self._guardar).pack(side="right")
        else:
            tk.Button(self.frame_botones, text="🔑 Rotar Contraseña", font=("Segoe UI", 9, "bold"), bg=NARANJA,
                      fg="white", relief="flat", padx=10, pady=4, cursor="hand2",
                      command=self._rotar_password).pack(side="left")
            self.boton_estado = ttk.Combobox(self.frame_botones, values=ESTADOS_CUENTA, state="readonly", width=12)
            self.boton_estado.pack(side="left", padx=(8, 0))
            self.boton_estado.bind("<<ComboboxSelected>>", lambda e: self._cambiar_estado())
            tk.Button(self.frame_botones, text="💾 Guardar Cambios", font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                      fg="white", relief="flat", padx=14, cursor="hand2", command=self._guardar).pack(side="right")

    def _construir_perfiles(self):
        self.grid_rowconfigure(1, weight=1)   # formulario (con scroll propio)
        self.grid_rowconfigure(3, weight=2)   # tabla de perfiles (algo más de espacio)

        seccion = tk.Frame(self, bg="white")
        seccion.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 16))
        seccion.grid_rowconfigure(1, weight=1)
        seccion.grid_columnconfigure(0, weight=1)

        tk.Label(seccion, text="Perfiles / Cupos de esta cuenta", font=("Segoe UI", 10, "bold"),
                 bg="white").grid(row=0, column=0, sticky="w", pady=(0, 6))

        contenedor = tk.Frame(seccion, bg="white")
        contenedor.grid(row=1, column=0, sticky="nsew")
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        columnas = ("perfil", "pin", "estado", "cliente", "vencimiento")
        self.tabla_perfiles = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla_perfiles)
        for col, enc in zip(columnas, ("PERFIL", "PIN", "ESTADO", "CLIENTE ASIGNADO", "VENCIMIENTO")):
            self.tabla_perfiles.heading(col, text=enc)
            self.tabla_perfiles.column(col, width=130, anchor="center")
        sb = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla_perfiles.yview)
        self.tabla_perfiles.configure(yscrollcommand=sb.set)
        self.tabla_perfiles.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        sb_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla_perfiles.xview)
        self.tabla_perfiles.configure(xscrollcommand=sb_h.set)
        sb_h.grid(row=1, column=0, sticky="ew")
        self.tabla_perfiles.tag_configure("Ocupado", foreground=ROJO)
        self.tabla_perfiles.tag_configure("Libre", foreground=VERDE)
        self.tabla_perfiles.bind("<Double-1>", lambda e: self._editar_perfil_seleccionado())

    def _editar_perfil_seleccionado(self):
        seleccion = self.tabla_perfiles.selection()
        if not seleccion:
            return
        perfil_id = int(seleccion[0])
        perfiles = listar_perfiles_cuenta(self.cuenta_id)
        perfil = next((p for p in perfiles if p["id"] == perfil_id), None)
        if perfil is None:
            return
        VentanaEditarPerfil(self, perfil, on_guardado=self._cargar_perfiles)

    def _cargar_perfiles(self):
        for f in self.tabla_perfiles.get_children():
            self.tabla_perfiles.delete(f)
        for p in listar_perfiles_cuenta(self.cuenta_id):
            self.tabla_perfiles.insert("", "end", iid=str(p["id"]), tags=(p["estado"],), values=(
                p["nombre_perfil"], p["pin"] or "—", p["estado"], p["cliente"] or "—",
                p["fecha_vencimiento"] or "—",
            ))

    def _rotar_password(self):
        VentanaRotarPassword(self, self.cuenta_id, on_guardado=self._cargar_datos)

    def _cambiar_estado(self):
        nuevo_estado = self.boton_estado.get()
        if nuevo_estado:
            cambiar_estado_cuenta(self.cuenta_id, nuevo_estado)
            if self.on_guardado:
                self.on_guardado()

    def _cargar_datos(self):
        cuenta = obtener_cuenta(self.cuenta_id)
        if cuenta is None:
            messagebox.showerror("No encontrada", "Esta cuenta ya no existe.", parent=self)
            self.destroy()
            return
        self.var_plataforma.set(cuenta["plataforma"])
        self.var_plan.set(cuenta["plan_nombre"])
        self.var_email.set(cuenta["email"])
        self.var_max_perfiles.set(str(cuenta["max_perfiles"]))
        self.var_costo.set(str(cuenta["costo_mensual"]))
        self.var_prox_pago.set(cuenta["fecha_proximo_pago_proveedor"])
        self.texto_notas.delete("1.0", "end")
        if cuenta["notas"]:
            self.texto_notas.insert("1.0", cuenta["notas"])
        self.boton_estado.set(cuenta["estado"])
        self.title(f"Ficha de {cuenta['plataforma']} — {cuenta['email']}")
        self._cargar_perfiles()

    def _guardar(self):
        try:
            costo = float(self.var_costo.get().replace(",", "."))
        except ValueError:
            messagebox.showwarning("Costo inválido", "El costo mensual debe ser un número.", parent=self)
            return

        if self.es_nueva:
            plataforma_id = self._plataformas.get(self.var_plataforma.get())
            if plataforma_id is None:
                messagebox.showwarning("Elegí una plataforma", "Seleccioná a qué plataforma pertenece "
                                       "esta cuenta.", parent=self)
                return
            try:
                max_perfiles = int(self.var_max_perfiles.get())
            except ValueError:
                messagebox.showwarning("Dato inválido", "La cantidad de perfiles debe ser un número entero.",
                                       parent=self)
                return
            ok, msg, nuevo_id = crear_cuenta(
                plataforma_id, self.var_email.get(), self.var_contrasena.get(), self.var_plan.get(),
                max_perfiles, costo, self.var_prox_pago.get() or None,
            )
            if not ok:
                messagebox.showerror("No se pudo guardar", msg, parent=self)
                return
            messagebox.showinfo("Cuenta creada", msg, parent=self)
            if self.on_guardado:
                self.on_guardado()
            self.destroy()
        else:
            ok, msg = editar_cuenta(
                self.cuenta_id, self.var_email.get(), self.var_contrasena.get(), self.var_plan.get(),
                costo, self.var_prox_pago.get() or None, self.texto_notas.get("1.0", "end").strip(),
            )
            if not ok:
                messagebox.showerror("No se pudo guardar", msg, parent=self)
                return
            self._cargar_datos()
            if self.on_guardado:
                self.on_guardado()


def _campo_fecha_streaming(parent, variable: tk.StringVar, row: int, col: int):
    from widget_calendario import abrir_selector_fecha
    frame = tk.Frame(parent, bg="white")
    frame.grid(row=row, column=col, sticky="ew", pady=4)
    tk.Entry(frame, textvariable=variable, font=("Segoe UI", 10), state="readonly", width=12).pack(side="left")
    tk.Button(frame, text="📅", font=("Segoe UI", 9), bg="white", relief="solid", bd=1, cursor="hand2",
              command=lambda: abrir_selector_fecha(
                  parent.winfo_toplevel(), datetime.date.today(),
                  lambda d: variable.set(d.isoformat()))).pack(side="left", padx=(4, 0))
    tk.Button(frame, text="✕", font=("Segoe UI", 9), bg="white", relief="solid", bd=1, cursor="hand2",
              command=lambda: variable.set("")).pack(side="left", padx=(2, 0))
    return frame


class VentanaEditarPerfil(tk.Toplevel):
    def __init__(self, parent, perfil: dict, on_guardado=None):
        super().__init__(parent)
        self.perfil = perfil
        self.on_guardado = on_guardado
        self.title("Editar Perfil")
        self.configure(bg="white")
        self.grab_set()

        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(padx=20, pady=20)
        tk.Label(contenedor, text="Nombre del perfil:", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=0, column=0, sticky="e", padx=(0, 8), pady=4)
        self.var_nombre = tk.StringVar(value=perfil["nombre_perfil"])
        tk.Entry(contenedor, textvariable=self.var_nombre, font=("Segoe UI", 10)).grid(
            row=0, column=1, sticky="ew", pady=4)

        tk.Label(contenedor, text="PIN (opcional):", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=1, column=0, sticky="e", padx=(0, 8), pady=4)
        self.var_pin = tk.StringVar(value=perfil["pin"])
        tk.Entry(contenedor, textvariable=self.var_pin, font=("Segoe UI", 10), width=10).grid(
            row=1, column=1, sticky="w", pady=4)

        botones = tk.Frame(contenedor, bg="white")
        botones.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        tk.Button(botones, text="✕ Cancelar", font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="left")
        tk.Button(botones, text="💾 Guardar", font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON, fg="white",
                  relief="flat", padx=14, cursor="hand2", command=self._guardar).pack(side="right")

    def _guardar(self):
        ok, msg = editar_perfil(self.perfil["id"], self.var_nombre.get(), self.var_pin.get())
        if not ok:
            messagebox.showerror("No se pudo guardar", msg, parent=self)
            return
        if self.on_guardado:
            self.on_guardado()
        self.destroy()


class VentanaRotarPassword(tk.Toplevel):
    def __init__(self, parent, cuenta_id: int, on_guardado=None):
        super().__init__(parent)
        self.cuenta_id = cuenta_id
        self.on_guardado = on_guardado
        self.title("Rotar Contraseña")
        self.configure(bg="white")
        self.grab_set()

        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(padx=20, pady=20)
        tk.Label(contenedor, text="Nueva contraseña para esta cuenta:", font=("Segoe UI", 9, "bold"),
                 bg="white").pack(anchor="w")
        self.var_password = tk.StringVar()
        entry = tk.Entry(contenedor, textvariable=self.var_password, font=("Segoe UI", 10), width=28)
        entry.pack(pady=(6, 0))
        tk.Label(contenedor, text="Recordá avisarle la nueva contraseña a todos los clientes\n"
                                  "que tengan un perfil activo en esta cuenta.",
                 font=("Segoe UI", 8), bg="white", fg=GRIS_TEXTO, justify="left").pack(anchor="w", pady=(8, 0))

        botones = tk.Frame(contenedor, bg="white")
        botones.pack(pady=(16, 0), fill="x")
        tk.Button(botones, text="✕ Cancelar", font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="left")
        tk.Button(botones, text="🔑 Confirmar", font=("Segoe UI", 9, "bold"), bg=NARANJA, fg="white",
                  relief="flat", padx=14, cursor="hand2", command=self._confirmar).pack(side="right")
        entry.focus()

    def _confirmar(self):
        ok, msg = rotar_password_cuenta(self.cuenta_id, self.var_password.get())
        if not ok:
            messagebox.showerror("No se pudo actualizar", msg, parent=self)
            return
        messagebox.showinfo("Listo", msg, parent=self)
        if self.on_guardado:
            self.on_guardado()
        self.destroy()


class VentanaGestionPlataformas(tk.Toplevel):
    def __init__(self, parent, on_cambio=None):
        super().__init__(parent)
        self.on_cambio = on_cambio
        self.title("Plataformas")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text="⚙ Plataformas", font=("Segoe UI", 11, "bold"), bg=AZUL_RIBBON,
                 fg="white").pack(side="left", padx=15, pady=6)

        formulario = tk.Frame(self, bg="white")
        formulario.grid(row=1, column=0, sticky="ew", padx=16, pady=(12, 6))
        self.var_nombre = tk.StringVar()
        entry = tk.Entry(formulario, textvariable=self.var_nombre, font=("Segoe UI", 10))
        entry.pack(side="left", fill="x", expand=True)
        forzar_mayusculas(entry, self.var_nombre)
        tk.Button(formulario, text="➕ Agregar", font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON, fg="white",
                  relief="flat", padx=10, pady=4, cursor="hand2", command=self._agregar).pack(side="left", padx=(8, 0))

        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=2, column=0, sticky="nsew", padx=16, pady=(6, 6))
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        columnas = ("nombre", "estado")
        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc in zip(columnas, ("PLATAFORMA", "ESTADO")):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=200 if col == "nombre" else 100)
        sb = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        sb_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_h.set)
        sb_h.grid(row=1, column=0, sticky="ew")
        self.tabla.tag_configure("inactiva", foreground=GRIS_TEXTO)

        botones = tk.Frame(self, bg="white")
        botones.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 16))
        tk.Button(botones, text="🚫 Activar/Desactivar", font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, cursor="hand2", command=self._alternar_estado).pack(side="left")
        tk.Button(botones, text="Cerrar", font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self._cerrar).pack(side="right")

        self.minsize(400, 440)
        ajustar_tamaño_ventana(self, ancho_min=400, alto_min=460)
        entry.focus()
        self.cargar()

    def _agregar(self):
        ok, msg = crear_plataforma(self.var_nombre.get())
        if not ok:
            messagebox.showerror("No se pudo agregar", msg, parent=self)
            return
        self.var_nombre.set("")
        self.cargar()

    def _alternar_estado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showinfo("Selecciona una plataforma", "Elegí una plataforma de la lista.", parent=self)
            return
        pid = int(seleccion[0])
        plataforma = next((p for p in listar_plataformas(solo_activas=False) if p["id"] == pid), None)
        if plataforma:
            cambiar_estado_plataforma(pid, not plataforma["activa"])
            self.cargar()

    def cargar(self):
        for f in self.tabla.get_children():
            self.tabla.delete(f)
        for p in listar_plataformas(solo_activas=False):
            tags = () if p["activa"] else ("inactiva",)
            self.tabla.insert("", "end", iid=str(p["id"]), tags=tags, values=(
                p["nombre"], "Activa" if p["activa"] else "Inactiva",
            ))

    def _cerrar(self):
        self.destroy()
        if self.on_cambio:
            self.on_cambio()


# ============================================================
# FICHA DE COMBO (crear)
# ============================================================
class VentanaFichaCombo(tk.Toplevel):
    def __init__(self, parent, on_guardado=None):
        super().__init__(parent)
        self.on_guardado = on_guardado
        self.title("Nuevo Combo")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text="📦 Nuevo Combo", font=("Segoe UI", 11, "bold"), bg=AZUL_RIBBON,
                 fg="white").pack(side="left", padx=15, pady=6)

        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=1, column=0, sticky="ew", padx=16, pady=(12, 6))
        contenedor.grid_columnconfigure(1, weight=1)
        tk.Label(contenedor, text="Nombre del combo:", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=0, column=0, sticky="e", padx=(0, 8), pady=4)
        self.var_nombre = tk.StringVar()
        entry_nombre = tk.Entry(contenedor, textvariable=self.var_nombre, font=("Segoe UI", 10))
        entry_nombre.grid(row=0, column=1, sticky="ew", pady=4)
        forzar_mayusculas(entry_nombre, self.var_nombre)

        tk.Label(contenedor, text="Precio mensual (Gs):", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=1, column=0, sticky="e", padx=(0, 8), pady=4)
        self.var_precio = tk.StringVar(value="0")
        tk.Entry(contenedor, textvariable=self.var_precio, font=("Segoe UI", 10), width=14).grid(
            row=1, column=1, sticky="w", pady=4)

        tk.Label(self, text="Elegí las plataformas que incluye este combo (2 o más):",
                 font=("Segoe UI", 9, "bold"), bg="white").grid(row=2, column=0, sticky="nw", padx=16)

        marco_lista = tk.Frame(self, bg="white")
        marco_lista.grid(row=3, column=0, sticky="nsew", padx=16, pady=(4, 6))
        self.grid_rowconfigure(3, weight=1)
        self.vars_plataformas = {}
        for p in listar_plataformas():
            var = tk.BooleanVar(value=False)
            tk.Checkbutton(marco_lista, text=p["nombre"], variable=var, bg="white",
                          font=("Segoe UI", 9)).pack(anchor="w")
            self.vars_plataformas[p["id"]] = var

        botones = tk.Frame(self, bg="white")
        botones.grid(row=4, column=0, sticky="ew", padx=16, pady=(6, 16))
        tk.Button(botones, text="✕ Cancelar", font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="left")
        tk.Button(botones, text="💾 Crear Combo", font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON, fg="white",
                  relief="flat", padx=14, cursor="hand2", command=self._guardar).pack(side="right")

        self.minsize(400, 480)
        ajustar_tamaño_ventana(self, ancho_min=400, alto_min=500)
        entry_nombre.focus()

    def _guardar(self):
        plataforma_ids = [pid for pid, var in self.vars_plataformas.items() if var.get()]
        ok, msg, nuevo_id = crear_combo(self.var_nombre.get(), self.var_precio.get(), plataforma_ids)
        if not ok:
            messagebox.showerror("No se pudo crear", msg, parent=self)
            return
        messagebox.showinfo("Combo creado", msg, parent=self)
        if self.on_guardado:
            self.on_guardado()
        self.destroy()


# ============================================================
# NUEVA SUSCRIPCIÓN (asignar un cliente a un perfil/cuenta/combo)
# ============================================================
class VentanaNuevaSuscripcion(tk.Toplevel):
    def __init__(self, parent, on_creado=None):
        super().__init__(parent)
        self.on_creado = on_creado
        self.cliente_seleccionado = None

        self.title("Nueva Suscripción")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        tk.Label(barra, text="👥 Nueva Suscripción", font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=18, pady=16)
        contenedor.grid_columnconfigure(1, weight=1)

        tk.Label(contenedor, text="Cliente:", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=0, column=0, sticky="e", padx=(0, 8), pady=4)
        self.label_cliente = tk.Label(contenedor, text="(ninguno elegido)", font=("Segoe UI", 10),
                                      bg="white", fg=GRIS_TEXTO)
        self.label_cliente.grid(row=0, column=1, sticky="w", pady=4)
        tk.Button(contenedor, text="🔍 Buscar Cliente", font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, cursor="hand2", command=self._buscar_cliente).grid(
                  row=0, column=2, padx=(8, 0))

        tk.Label(contenedor, text="Modalidad:", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=1, column=0, sticky="e", padx=(0, 8), pady=(10, 4))
        self.var_modalidad = tk.StringVar(value=MODALIDADES[0])
        frame_modalidad = tk.Frame(contenedor, bg="white")
        frame_modalidad.grid(row=1, column=1, columnspan=2, sticky="w", pady=(10, 4))
        for m in MODALIDADES:
            tk.Radiobutton(frame_modalidad, text=m, variable=self.var_modalidad, value=m, bg="white",
                          font=("Segoe UI", 9), command=self._actualizar_seccion_modalidad).pack(
                          side="left", padx=(0, 10))

        self.frame_dinamico = tk.Frame(contenedor, bg="white")
        self.frame_dinamico.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(4, 4))
        self.frame_dinamico.grid_columnconfigure(1, weight=1)

        tk.Label(contenedor, text="Precio mensual a cobrar (Gs):", font=("Segoe UI", 9, "bold"),
                 bg="white").grid(row=3, column=0, sticky="e", padx=(0, 8), pady=(10, 4))
        self.var_precio = tk.StringVar(value="0")
        tk.Entry(contenedor, textvariable=self.var_precio, font=("Segoe UI", 10), width=14).grid(
            row=3, column=1, sticky="w", pady=(10, 4))

        tk.Label(contenedor, text="Duración:", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=4, column=0, sticky="e", padx=(0, 8), pady=4)
        frame_duracion = tk.Frame(contenedor, bg="white")
        frame_duracion.grid(row=4, column=1, columnspan=2, sticky="w", pady=4)
        self.var_duracion_dias = tk.StringVar(value="30")
        tk.Entry(frame_duracion, textvariable=self.var_duracion_dias, font=("Segoe UI", 10), width=6).pack(
            side="left")
        tk.Label(frame_duracion, text="días  (7 = semanal, 30 = mensual)", font=("Segoe UI", 8), bg="white",
                 fg=GRIS_TEXTO).pack(side="left", padx=(6, 0))

        tk.Label(contenedor, text="Forma de pago:", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=5, column=0, sticky="e", padx=(0, 8), pady=4)
        self.var_forma_pago = tk.StringVar(value=FORMAS_PAGO[0])
        ttk.Combobox(contenedor, textvariable=self.var_forma_pago, state="readonly",
                    values=FORMAS_PAGO, width=20).grid(row=5, column=1, sticky="w", pady=4)

        tk.Label(contenedor, text="Máx. dispositivos simultáneos:", font=("Segoe UI", 9, "bold"),
                 bg="white").grid(row=6, column=0, sticky="e", padx=(0, 8), pady=4)
        self.var_max_dispositivos = tk.StringVar(value="1")
        tk.Entry(contenedor, textvariable=self.var_max_dispositivos, font=("Segoe UI", 10), width=6).grid(
            row=6, column=1, sticky="w", pady=4)

        botones = tk.Frame(self, bg="white")
        botones.pack(fill="x", padx=18, pady=(0, 16))
        tk.Button(botones, text="✕ Cancelar", font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="left")
        tk.Button(botones, text="✔ Crear Suscripción", font=("Segoe UI", 10, "bold"), bg=AZUL_RIBBON,
                  fg="white", relief="flat", padx=14, pady=6, cursor="hand2", command=self._crear).pack(
                  side="right")

        self.minsize(480, 440)
        ajustar_tamaño_ventana(self, ancho_min=480, alto_min=480)
        self._actualizar_seccion_modalidad()

    def _buscar_cliente(self):
        from ventanas_auxiliares_venta import VentanaAsignarCliente
        VentanaAsignarCliente(self, on_seleccionado=self._al_elegir_cliente)

    def _al_elegir_cliente(self, cliente):
        self.cliente_seleccionado = cliente
        self.label_cliente.config(text=cliente["nombre"] if cliente else "(ninguno elegido)")

    def _actualizar_seccion_modalidad(self):
        for w in self.frame_dinamico.winfo_children():
            w.destroy()
        modalidad = self.var_modalidad.get()

        if modalidad == "Perfil Individual":
            tk.Label(self.frame_dinamico, text="Plataforma:", font=("Segoe UI", 9, "bold"), bg="white").grid(
                row=0, column=0, sticky="e", padx=(0, 8))
            self.var_plataforma_sel = tk.StringVar()
            self._plataformas_disp = {p["nombre"]: p["id"] for p in listar_plataformas()}
            combo = ttk.Combobox(self.frame_dinamico, textvariable=self.var_plataforma_sel, state="readonly",
                                 values=list(self._plataformas_disp.keys()), width=20)
            combo.grid(row=0, column=1, sticky="w")
            combo.bind("<<ComboboxSelected>>", lambda e: self._actualizar_perfiles_libres())

            tk.Label(self.frame_dinamico, text="Perfil libre:", font=("Segoe UI", 9, "bold"), bg="white").grid(
                row=1, column=0, sticky="e", padx=(0, 8), pady=(4, 0))
            self.var_perfil_sel = tk.StringVar()
            self.combo_perfil = ttk.Combobox(self.frame_dinamico, textvariable=self.var_perfil_sel,
                                             state="readonly", width=30)
            self.combo_perfil.grid(row=1, column=1, sticky="w", pady=(4, 0))

        elif modalidad == "Acceso Completo":
            tk.Label(self.frame_dinamico, text="Cuenta disponible:", font=("Segoe UI", 9, "bold"),
                     bg="white").grid(row=0, column=0, sticky="e", padx=(0, 8))
            self.var_cuenta_sel = tk.StringVar()
            self._cuentas_disp = {
                f"{c['plataforma']} — {c['email']} ({c['perfiles_libres']} libre/s)": c["id"]
                for c in listar_cuentas(incluir_inactivas=False) if c["perfiles_libres"] > 0
            }
            combo = ttk.Combobox(self.frame_dinamico, textvariable=self.var_cuenta_sel, state="readonly",
                                 values=list(self._cuentas_disp.keys()), width=40)
            combo.grid(row=0, column=1, sticky="w")

        else:  # Combo
            tk.Label(self.frame_dinamico, text="Combo:", font=("Segoe UI", 9, "bold"), bg="white").grid(
                row=0, column=0, sticky="e", padx=(0, 8))
            self.var_combo_sel = tk.StringVar()
            self._combos_disp = {
                f"{c['nombre']} ({' + '.join(c['plataformas'])})": (c["id"], c["precio_mensual"])
                for c in listar_combos()
            }
            combo = ttk.Combobox(self.frame_dinamico, textvariable=self.var_combo_sel, state="readonly",
                                 values=list(self._combos_disp.keys()), width=40)
            combo.grid(row=0, column=1, sticky="w")
            combo.bind("<<ComboboxSelected>>", lambda e: self._autocompletar_precio_combo())

    def _actualizar_perfiles_libres(self):
        plataforma_id = self._plataformas_disp.get(self.var_plataforma_sel.get())
        if plataforma_id is None:
            return
        self._perfiles_disp = {f"{p['email']} — Perfil #{p['id']}": p["id"]
                               for p in listar_perfiles_libres(plataforma_id)}
        self.combo_perfil["values"] = list(self._perfiles_disp.keys())
        if self._perfiles_disp:
            self.combo_perfil.current(0)

    def _autocompletar_precio_combo(self):
        datos = self._combos_disp.get(self.var_combo_sel.get())
        if datos:
            self.var_precio.set(str(datos[1]))

    def _crear(self):
        if self.cliente_seleccionado is None:
            messagebox.showwarning("Falta el cliente", "Buscá y elegí el cliente que va a alquilar.",
                                   parent=self)
            return
        try:
            precio = float(self.var_precio.get().replace(",", "."))
            duracion = int(self.var_duracion_dias.get())
            max_disp = int(self.var_max_dispositivos.get())
        except ValueError:
            messagebox.showwarning("Datos inválidos", "Revisá el precio, la duración y los dispositivos.",
                                   parent=self)
            return

        modalidad = self.var_modalidad.get()
        kwargs = {}
        if modalidad == "Perfil Individual":
            perfil_id = self._perfiles_disp.get(self.var_perfil_sel.get()) if hasattr(self, "_perfiles_disp") else None
            if perfil_id is None:
                messagebox.showwarning("Elegí un perfil", "Seleccioná la plataforma y un perfil libre.",
                                       parent=self)
                return
            kwargs["perfil_id"] = perfil_id
        elif modalidad == "Acceso Completo":
            cuenta_id = self._cuentas_disp.get(self.var_cuenta_sel.get()) if hasattr(self, "_cuentas_disp") else None
            if cuenta_id is None:
                messagebox.showwarning("Elegí una cuenta", "Seleccioná qué cuenta alquilar completa.",
                                       parent=self)
                return
            kwargs["cuenta_id"] = cuenta_id
        else:
            datos = self._combos_disp.get(self.var_combo_sel.get()) if hasattr(self, "_combos_disp") else None
            if datos is None:
                messagebox.showwarning("Elegí un combo", "Seleccioná qué combo contratar.", parent=self)
                return
            kwargs["combo_id"] = datos[0]

        ok, msg, sid = crear_suscripcion(
            self.cliente_seleccionado["id"], modalidad, precio, duracion,
            forma_pago=self.var_forma_pago.get(), max_dispositivos=max_disp, **kwargs,
        )
        if not ok:
            messagebox.showerror("No se pudo crear", msg, parent=self)
            return
        messagebox.showinfo("Suscripción creada", msg, parent=self)
        self.destroy()
        if self.on_creado:
            self.on_creado()


# ============================================================
# REGISTRAR PAGO / RENOVACIÓN
# ============================================================
class VentanaRegistrarPago(tk.Toplevel):
    def __init__(self, parent, usuario_actual, suscripcion_id: int, on_pagado=None):
        super().__init__(parent)
        self.usuario_actual = usuario_actual
        self.suscripcion_id = suscripcion_id
        self.on_pagado = on_pagado

        detalle = obtener_suscripcion_detalle(suscripcion_id)
        self.detalle = detalle

        self.title("Registrar Pago")
        self.configure(bg="white")
        self.grab_set()

        barra = tk.Frame(self, bg=VERDE, height=34)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        tk.Label(barra, text="💳 Registrar Pago / Renovar", font=("Segoe UI", 11, "bold"),
                 bg=VERDE, fg="white").pack(side="left", padx=15, pady=6)

        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=18, pady=16)

        plataformas_txt = detalle["combo_nombre"] or ", ".join(sorted({p["plataforma"] for p in detalle["perfiles"]}))
        tk.Label(contenedor, text=f"{detalle['cliente']} — {plataformas_txt}",
                 font=("Segoe UI", 11, "bold"), bg="white").pack(anchor="w")
        tk.Label(contenedor, text=f"Vence: {detalle['fecha_vencimiento']} ({detalle['dias_restantes']} días)",
                 font=("Segoe UI", 9), bg="white", fg=GRIS_TEXTO).pack(anchor="w", pady=(0, 12))

        fila_monto = tk.Frame(contenedor, bg="white")
        fila_monto.pack(fill="x", pady=(0, 8))
        tk.Label(fila_monto, text="Monto a cobrar (Gs):", font=("Segoe UI", 9, "bold"), bg="white").pack(
            side="left")
        self.var_monto = tk.StringVar(value=str(detalle["precio_mensual"]))
        tk.Entry(fila_monto, textvariable=self.var_monto, font=("Segoe UI", 10), width=14).pack(
            side="left", padx=(6, 0))

        fila_dias = tk.Frame(contenedor, bg="white")
        fila_dias.pack(fill="x", pady=(0, 8))
        tk.Label(fila_dias, text="Extender por:", font=("Segoe UI", 9, "bold"), bg="white").pack(side="left")
        self.var_dias = tk.StringVar(value="30")
        tk.Entry(fila_dias, textvariable=self.var_dias, font=("Segoe UI", 10), width=6).pack(
            side="left", padx=(6, 6))
        tk.Label(fila_dias, text="días", font=("Segoe UI", 9), bg="white").pack(side="left")

        fila_pago = tk.Frame(contenedor, bg="white")
        fila_pago.pack(fill="x", pady=(0, 12))
        tk.Label(fila_pago, text="Forma de pago:", font=("Segoe UI", 9, "bold"), bg="white").pack(side="left")
        self.var_forma_pago = tk.StringVar(value=detalle["forma_pago"])
        ttk.Combobox(fila_pago, textvariable=self.var_forma_pago, state="readonly", values=FORMAS_PAGO,
                    width=20).pack(side="left", padx=(6, 0))

        botones = tk.Frame(self, bg="white")
        botones.pack(fill="x", padx=18, pady=(0, 16))
        tk.Button(botones, text="✕ Cancelar", font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="left")
        self.boton_confirmar = tk.Button(botones, text="✔ Confirmar Pago", font=("Segoe UI", 10, "bold"),
                  bg=VERDE, fg="white", relief="flat", padx=14, pady=6, cursor="hand2",
                  command=self._confirmar)
        self.boton_confirmar.pack(side="right")

        self.minsize(420, 340)
        ajustar_tamaño_ventana(self, ancho_min=420, alto_min=340)

    def _confirmar(self):
        try:
            monto = float(self.var_monto.get().replace(",", "."))
            dias = int(self.var_dias.get())
        except ValueError:
            messagebox.showwarning("Datos inválidos", "El monto y los días deben ser números.", parent=self)
            return
        self.boton_confirmar.config(state="disabled", text="Procesando...")
        self.update_idletasks()
        ok, msg, venta_id = registrar_pago_renovacion(
            self.suscripcion_id, self.usuario_actual.get("id"), dias_extension=dias, monto=monto,
            forma_pago=self.var_forma_pago.get(),
        )
        if not ok:
            messagebox.showerror("No se pudo registrar", msg, parent=self)
            self.boton_confirmar.config(state="normal", text="✔ Confirmar Pago")
            return
        messagebox.showinfo("Pago registrado", msg, parent=self)
        self.destroy()
        if self.on_pagado:
            self.on_pagado()


# ============================================================
# DETALLE DE SUSCRIPCIÓN (credenciales + historial de pagos)
# ============================================================
class VentanaDetalleSuscripcion(tk.Toplevel):
    def __init__(self, parent, suscripcion_id: int, on_cambio=None):
        super().__init__(parent)
        self.suscripcion_id = suscripcion_id
        self.on_cambio = on_cambio

        detalle = obtener_suscripcion_detalle(suscripcion_id)
        if detalle is None:
            self.destroy()
            return

        self.title(f"Suscripción — {detalle['cliente']}")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        tk.Label(barra, text=f"🔑 {detalle['cliente']} — {detalle['modalidad']}",
                 font=("Segoe UI", 11, "bold"), bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=18, pady=16)

        info = (f"Cliente: {detalle['cliente']}   Tel: {detalle['cliente_telefono'] or '—'}\n"
               f"Vigencia: {detalle['fecha_inicio']} → {detalle['fecha_vencimiento']} "
               f"({detalle['dias_restantes']} días restantes)\n"
               f"Precio mensual: {formatear_gs(detalle['precio_mensual'])}   "
               f"Forma de pago: {detalle['forma_pago']}   Estado: {detalle['estado']}\n"
               f"Máx. dispositivos: {detalle['max_dispositivos']}")
        tk.Label(contenedor, text=info, font=("Segoe UI", 9), bg="white", justify="left").pack(anchor="w")

        tk.Label(contenedor, text="Credenciales de acceso:", font=("Segoe UI", 10, "bold"), bg="white").pack(
            anchor="w", pady=(14, 4))
        for p in detalle["perfiles"]:
            texto_perfil = f"• {p['plataforma']} — {p['email_cuenta']}"
            if p["nombre_perfil"] and p["nombre_perfil"] != "Cuenta Completa":
                texto_perfil += f"  |  Perfil: {p['nombre_perfil']}"
                if p["pin"]:
                    texto_perfil += f"  |  PIN: {p['pin']}"
            tk.Label(contenedor, text=texto_perfil, font=("Segoe UI", 9), bg="white", fg="#075985").pack(
                anchor="w")

        tk.Label(contenedor, text="Historial de pagos:", font=("Segoe UI", 10, "bold"), bg="white").pack(
            anchor="w", pady=(14, 4))
        contenedor_tabla = tk.Frame(contenedor, bg="white")
        contenedor_tabla.pack(fill="both", expand=True)
        contenedor_tabla.grid_rowconfigure(0, weight=1)
        contenedor_tabla.grid_columnconfigure(0, weight=1)
        columnas = ("fecha", "periodo", "monto")
        tabla = ttk.Treeview(contenedor_tabla, columns=columnas, show="headings", selectmode="browse", height=5)
        habilitar_deseleccion_treeview(tabla)
        for col, enc in zip(columnas, ("FECHA DE PAGO", "PERÍODO CUBIERTO", "MONTO")):
            tabla.heading(col, text=enc)
            tabla.column(col, width=160, anchor="center")
        sb = ttk.Scrollbar(contenedor_tabla, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=sb.set)
        tabla.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        sb_h = ttk.Scrollbar(contenedor_tabla, orient="horizontal", command=tabla.xview)
        tabla.configure(xscrollcommand=sb_h.set)
        sb_h.grid(row=1, column=0, sticky="ew")
        for pago in listar_historial_pagos(suscripcion_id):
            tabla.insert("", "end", values=(
                pago["fecha_pago"].split(" ")[0], f"{pago['periodo_desde']} → {pago['periodo_hasta']}",
                formatear_gs(pago["monto"]),
            ))

        tk.Button(self, text="Cerrar", font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(pady=(0, 16))

        self.minsize(520, 480)
        ajustar_tamaño_ventana(self, ancho_min=520, alto_min=520)
