"""
ventana_veterinaria.py
Módulo Veterinaria: ficha de Mascotas ligadas a un Cliente (dueño),
Historial Clínico (consultas), Vacunas y Tratamientos/desparasitaciones,
con pestañas Mascotas / Vacunas Próximas / Dashboard, siguiendo el mismo
patrón visual que el módulo de Asistencia Técnica.
"""
import datetime
import tkinter as tk
from tkinter import ttk, messagebox

from models_veterinaria import (
    SEXOS, TIPOS_TRATAMIENTO, listar_especies, crear_especie,
    crear_mascota, editar_mascota, listar_mascotas, listar_mascotas_por_cliente,
    obtener_mascota, marcar_fallecido, calcular_edad, obtener_ficha_completa,
    obtener_vacuna_detalle, obtener_consulta_detalle,
    crear_consulta, listar_consultas_por_mascota, listar_consultas_del_dia,
    crear_vacuna, listar_vacunas_por_mascota, listar_vacunas_proximas,
    crear_tratamiento, listar_tratamientos_por_mascota, finalizar_tratamiento,
    conteos_dashboard,
)
from utilidades_ui import ajustar_tamaño_ventana, forzar_mayusculas, habilitar_deseleccion_treeview
from traducciones import t
from widget_calendario import abrir_selector_fecha

AZUL_RIBBON = "#1d5fd6"
GRIS_FONDO = "#f4f5f7"
GRIS_BORDE = "#e2e8f0"
VERDE = "#16a34a"
ROJO = "#dc2626"
NARANJA = "#d97706"
GRIS_TEXTO = "#6b7280"


def _fecha_o_hoy(texto: str) -> datetime.date:
    try:
        return datetime.date.fromisoformat(texto)
    except (ValueError, TypeError):
        return datetime.date.today()


def _formatear_fecha(fecha_texto: str) -> str:
    if not fecha_texto:
        return "—"
    try:
        return datetime.date.fromisoformat(fecha_texto[:10]).strftime("%d/%m/%Y")
    except ValueError:
        return fecha_texto


def _formatear_fecha_hora(fecha_hora: str) -> str:
    if not fecha_hora:
        return "—"
    try:
        return datetime.datetime.fromisoformat(fecha_hora).strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return fecha_hora


def _campo_fecha(parent, variable: tk.StringVar, row: int, col: int):
    """Entry de solo lectura + botón calendario, siguiendo el patrón usado
    en RRHH y Créditos para elegir fechas con widget_calendario."""
    frame = tk.Frame(parent, bg="white")
    frame.grid(row=row, column=col, sticky="ew", pady=4)
    entry = tk.Entry(frame, textvariable=variable, font=("Segoe UI", 10), state="readonly", width=14)
    entry.pack(side="left")
    tk.Button(frame, text="📅", font=("Segoe UI", 9), bg="white", relief="solid", bd=1,
              cursor="hand2",
              command=lambda: abrir_selector_fecha(
                  parent.winfo_toplevel(), _fecha_o_hoy(variable.get()),
                  lambda d: variable.set(d.isoformat()))).pack(side="left", padx=(4, 0))
    tk.Button(frame, text="✕", font=("Segoe UI", 9), bg="white", relief="solid", bd=1,
              cursor="hand2", command=lambda: variable.set("")).pack(side="left", padx=(2, 0))
    return frame


def _abrir_archivo(ruta: str):
    import os, sys, subprocess
    try:
        if sys.platform == "win32":
            os.startfile(ruta)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", ruta], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(["xdg-open", ruta], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def _guardar_pdf_y_ofrecer_abrir(parent, nombre_archivo_sugerido: str, titulo_dialogo: str,
                                  generar_pdf_callable) -> str | None:
    """Pide dónde guardar el PDF, lo genera con generar_pdf_callable(ruta) y
    ofrece abrirlo. Devuelve la ruta generada (o None si se canceló/falló).
    Se usa desde los tres puntos de reporte (Mascota, Vacuna, Consulta)."""
    from tkinter import filedialog
    try:
        import reportlab  # noqa: F401
    except ImportError:
        messagebox.showerror("Falta una librería",
                             "Para generar el PDF se necesita instalar 'reportlab'.\n\n"
                             "Abre una terminal y ejecutá:\n\npip install reportlab",
                             parent=parent)
        return None

    ruta = filedialog.asksaveasfilename(
        title=titulo_dialogo, initialfile=nombre_archivo_sugerido,
        defaultextension=".pdf", filetypes=[("Archivo PDF", "*.pdf")], parent=parent,
    )
    if not ruta:
        return None
    try:
        generar_pdf_callable(ruta)
    except PermissionError:
        messagebox.showerror(
            "No se pudo guardar el archivo",
            f"Windows no dejó guardar en:\n{ruta}\n\n"
            "Esto casi siempre pasa porque el archivo ya está abierto en un lector de PDF "
            "(o en otro programa). Cerralo e intentá de nuevo, o elegí otro nombre de archivo.",
            parent=parent)
        return None
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo generar el PDF:\n{e}", parent=parent)
        return None

    if messagebox.askyesno("PDF generado", f"El reporte se guardó en:\n{ruta}\n\n"
                                           "¿Querés abrirlo ahora?", parent=parent):
        _abrir_archivo(ruta)
    return ruta


def _nombre_archivo_seguro(*partes) -> str:
    texto = "_".join(str(p).strip() for p in partes if p not in (None, ""))
    for caracter in " /\\:*?\"<>|":
        texto = texto.replace(caracter, "_")
    return texto + ".pdf"


# ---------------- Reporte de MASCOTA (ficha completa) ----------------
def _generar_reporte_pdf_mascota(parent, mascota_id: int):
    ficha = obtener_ficha_completa(mascota_id)
    if ficha is None:
        messagebox.showerror("No encontrada", "Esta mascota ya no existe.", parent=parent)
        return
    from reporte_veterinaria_pdf import generar_reporte_mascota_pdf
    nombre = _nombre_archivo_seguro("mascota", ficha["mascota"]["nombre"], mascota_id)
    _guardar_pdf_y_ofrecer_abrir(parent, nombre, "Guardar Reporte de la Mascota",
                                lambda ruta: generar_reporte_mascota_pdf(ruta, ficha))


def _enviar_reporte_mascota_email(parent, mascota_id: int, usuario_actual: dict):
    ficha = obtener_ficha_completa(mascota_id)
    if ficha is None:
        messagebox.showerror("No encontrada", "Esta mascota ya no existe.", parent=parent)
        return
    from reporte_veterinaria_pdf import generar_reporte_mascota_pdf
    m = ficha["mascota"]
    asunto = f"Reporte Veterinario - {m['nombre']}"
    cuerpo = (
        f"Hola,\n\nTe compartimos el reporte veterinario de {m['nombre']}, con su historial "
        f"clínico, vacunas y tratamientos registrados.\n\nSaludos,\n"
        f"{usuario_actual.get('nombre_completo', '')}"
    )
    nombre = _nombre_archivo_seguro("mascota", m["nombre"], mascota_id)
    VentanaEnviarReporteEmail(parent, "Enviar Reporte de la Mascota", asunto, cuerpo,
                              lambda ruta: generar_reporte_mascota_pdf(ruta, ficha), nombre)


# ---------------- Certificado de VACUNA ----------------
def _generar_certificado_vacuna(parent, vacuna_id: int):
    v = obtener_vacuna_detalle(vacuna_id)
    if v is None:
        messagebox.showerror("No encontrada", "Esta vacuna ya no existe.", parent=parent)
        return
    from reporte_veterinaria_pdf import generar_certificado_vacuna_pdf
    nombre = _nombre_archivo_seguro("vacuna", v["vacuna"], v["mascota"], vacuna_id)
    _guardar_pdf_y_ofrecer_abrir(parent, nombre, "Guardar Certificado de Vacunación",
                                lambda ruta: generar_certificado_vacuna_pdf(ruta, v))


def _enviar_certificado_vacuna_email(parent, vacuna_id: int, usuario_actual: dict):
    v = obtener_vacuna_detalle(vacuna_id)
    if v is None:
        messagebox.showerror("No encontrada", "Esta vacuna ya no existe.", parent=parent)
        return
    from reporte_veterinaria_pdf import generar_certificado_vacuna_pdf
    asunto = f"Certificado de Vacunación - {v['mascota']}"
    cuerpo = (
        f"Hola,\n\nTe compartimos el certificado de la vacuna '{v['vacuna']}' aplicada a "
        f"{v['mascota']}.\n\nSaludos,\n{usuario_actual.get('nombre_completo', '')}"
    )
    nombre = _nombre_archivo_seguro("vacuna", v["vacuna"], v["mascota"], vacuna_id)
    VentanaEnviarReporteEmail(parent, "Enviar Certificado de Vacunación", asunto, cuerpo,
                              lambda ruta: generar_certificado_vacuna_pdf(ruta, v), nombre)


# ---------------- Constancia de CONSULTA ----------------
def _generar_reporte_consulta(parent, consulta_id: int):
    c = obtener_consulta_detalle(consulta_id)
    if c is None:
        messagebox.showerror("No encontrada", "Esta consulta ya no existe.", parent=parent)
        return
    from reporte_veterinaria_pdf import generar_reporte_consulta_pdf
    nombre = _nombre_archivo_seguro("consulta", c["mascota"], consulta_id)
    _guardar_pdf_y_ofrecer_abrir(parent, nombre, "Guardar Constancia de Consulta",
                                lambda ruta: generar_reporte_consulta_pdf(ruta, c))


def _enviar_reporte_consulta_email(parent, consulta_id: int, usuario_actual: dict):
    c = obtener_consulta_detalle(consulta_id)
    if c is None:
        messagebox.showerror("No encontrada", "Esta consulta ya no existe.", parent=parent)
        return
    from reporte_veterinaria_pdf import generar_reporte_consulta_pdf
    asunto = f"Constancia de Consulta - {c['mascota']}"
    cuerpo = (
        f"Hola,\n\nTe compartimos la constancia de la consulta de {c['mascota']} "
        f"del {_formatear_fecha(c['fecha'])}.\n\nSaludos,\n{usuario_actual.get('nombre_completo', '')}"
    )
    nombre = _nombre_archivo_seguro("consulta", c["mascota"], consulta_id)
    VentanaEnviarReporteEmail(parent, "Enviar Constancia de Consulta", asunto, cuerpo,
                              lambda ruta: generar_reporte_consulta_pdf(ruta, c), nombre)


# ============================================================
# VENTANA GENÉRICA: ENVIAR CUALQUIER REPORTE DEL MÓDULO POR CORREO
# ============================================================
class VentanaEnviarReporteEmail(tk.Toplevel):
    """Reutilizada por los 3 tipos de reporte (Mascota, Vacuna, Consulta):
    pide el destinatario, genera el PDF a un archivo temporal y lo envía
    adjunto usando la cuenta de correo configurada (cualquier proveedor).
    Si todavía no hay ninguna cuenta configurada, ofrece abrir la
    configuración directamente, igual que en Resumen de Ventas."""

    def __init__(self, parent, titulo_ventana: str, asunto_default: str, cuerpo_texto: str,
                 generar_pdf_callable, nombre_adjunto: str):
        super().__init__(parent)
        self.titulo_ventana = titulo_ventana
        self.asunto_default = asunto_default
        self.cuerpo_texto = cuerpo_texto
        self.generar_pdf_callable = generar_pdf_callable
        self.nombre_adjunto = nombre_adjunto
        self.ruta_pdf_temporal = None

        self.title(titulo_ventana)
        self.minsize(420, 420)
        self.configure(bg="white")
        self.grab_set()
        self.transient(parent)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_barra_titulo()
        self._reconstruir_contenido()
        ajustar_tamaño_ventana(self, ancho_min=420, alto_min=420)

    def _construir_barra_titulo(self):
        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text=f"📧 {self.titulo_ventana}", font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

    def _reconstruir_contenido(self):
        for w in list(self.grid_slaves(row=1, column=0)):
            w.destroy()
        from models_email import obtener_configuracion_email
        config = obtener_configuracion_email()
        if config is None:
            self._mostrar_aviso_sin_configurar()
        else:
            self._construir_formulario(config)

    def _mostrar_aviso_sin_configurar(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)

        tk.Label(contenedor, text=t("vet_sin_cuenta_correo"),
                 font=("Segoe UI", 11, "bold"), bg="white", wraplength=400).pack(pady=(20, 10))
        tk.Label(contenedor, text="Necesitas configurar tu cuenta de correo (Gmail, Outlook, Yahoo, "
                                  "ProtonMail u otra) una sola vez antes de poder enviar reportes.",
                 font=("Segoe UI", 9), bg="white", fg="#555", wraplength=400, justify="center").pack(pady=(0, 20))

        tk.Button(contenedor, text=t("vet_configurar_email_ahora"), font=("Segoe UI", 10, "bold"),
                  bg=AZUL_RIBBON, fg="white", relief="flat", padx=14, pady=8, cursor="hand2",
                  command=self._abrir_configuracion).pack()

    def _abrir_configuracion(self):
        from ventana_configurar_email import VentanaConfigurarEmail
        VentanaConfigurarEmail(self, on_guardado=self._reconstruir_contenido)

    def _construir_formulario(self, config):
        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=1, column=0, sticky="nsew", padx=20, pady=15)

        barra_cuenta = tk.Frame(contenedor, bg="#e0f2fe", relief="solid", bd=1)
        barra_cuenta.pack(fill="x", pady=(0, 12))
        tk.Label(barra_cuenta, text=f"Enviando desde: {config['correo_remitente']}",
                 font=("Segoe UI", 8, "bold"), bg="#e0f2fe", fg="#075985").pack(
                 side="left", padx=10, pady=6)
        tk.Button(barra_cuenta, text=t("vet_cambiar_cuenta"), font=("Segoe UI", 8, "bold"),
                  bg="white", relief="solid", bd=1, cursor="hand2",
                  command=self._abrir_configuracion).pack(side="right", padx=10, pady=4)

        tk.Label(contenedor, text=t("vet_para_destinatario"), font=("Segoe UI", 9, "bold"), bg="white").pack(
            anchor="w", pady=(5, 2))
        self.var_destinatario = tk.StringVar(value=config.get("ultimo_destinatario", ""))
        entry_destinatario = tk.Entry(contenedor, textvariable=self.var_destinatario,
                                      font=("Segoe UI", 10), width=40)
        entry_destinatario.pack(anchor="w", fill="x")
        entry_destinatario.focus()

        tk.Label(contenedor, text=t("asunto_label"), font=("Segoe UI", 9, "bold"), bg="white").pack(
            anchor="w", pady=(12, 2))
        self.var_asunto = tk.StringVar(value=self.asunto_default)
        tk.Entry(contenedor, textvariable=self.var_asunto, font=("Segoe UI", 10), width=40).pack(
            anchor="w", fill="x")

        tk.Label(contenedor, text=t("mensaje_label"), font=("Segoe UI", 9, "bold"), bg="white").pack(
            anchor="w", pady=(12, 2))
        self.texto_cuerpo = tk.Text(contenedor, font=("Segoe UI", 9), height=7, relief="solid", bd=1)
        self.texto_cuerpo.insert("1.0", self.cuerpo_texto)
        self.texto_cuerpo.pack(fill="both", expand=True, pady=(0, 4))

        tk.Label(contenedor, text=t("vet_se_adjuntara_pdf"),
                 font=("Segoe UI", 8), bg="white", fg="#16a34a").pack(anchor="w", pady=(0, 10))

        frame_botones = tk.Frame(contenedor, bg="white")
        frame_botones.pack(fill="x")
        self.boton_enviar = tk.Button(frame_botones, text=t("enviar_avion"), font=("Segoe UI", 10, "bold"),
                                       bg=AZUL_RIBBON, fg="white", relief="flat", padx=16, pady=8,
                                       cursor="hand2", command=self._enviar)
        self.boton_enviar.pack(side="left")
        tk.Button(frame_botones, text=t("cancelar"), font=("Segoe UI", 10), bg="white",
                  relief="solid", bd=1, padx=14, pady=8, command=self.destroy).pack(side="left", padx=8)

    def _enviar(self):
        destinatario = self.var_destinatario.get().strip()
        if not destinatario or "@" not in destinatario:
            messagebox.showwarning("Destinatario requerido", "Ingresa un correo de destinatario válido.",
                                   parent=self)
            return

        self.boton_enviar.config(state="disabled", text=t("enviando"))
        self.update_idletasks()

        import tempfile, os
        ruta_temporal = os.path.join(tempfile.gettempdir(), f"veterinaria_temp_{self.nombre_adjunto}")
        try:
            self.generar_pdf_callable(ruta_temporal)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF del reporte:\n{e}", parent=self)
            self.boton_enviar.config(state="normal", text=t("enviar_avion"))
            return

        from models_email import enviar_correo
        ok, msg = enviar_correo(
            destinatario=destinatario, asunto=self.var_asunto.get().strip(),
            cuerpo_texto=self.texto_cuerpo.get("1.0", "end").strip(),
            ruta_adjunto=ruta_temporal, nombre_adjunto=self.nombre_adjunto,
        )

        if os.path.exists(ruta_temporal):
            try:
                os.remove(ruta_temporal)
            except OSError:
                pass

        if ok:
            messagebox.showinfo("Enviado", msg, parent=self)
            self.destroy()
        else:
            messagebox.showerror("No se pudo enviar", msg, parent=self)
            self.boton_enviar.config(state="normal", text=t("enviar_avion"))


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
class PanelVeterinaria(tk.Frame):
    def __init__(self, parent, usuario_actual):
        super().__init__(parent, bg="white")
        self.usuario_actual = usuario_actual

        self._construir_barra_superior()
        self._construir_notebook()

    def _construir_barra_superior(self):
        barra = tk.Frame(self, bg="white")
        barra.pack(fill="x", padx=10, pady=(10, 5))

        tk.Button(barra, text=t("vet_nueva_mascota"), font=("Segoe UI", 9, "bold"),
                  bg=AZUL_RIBBON, fg="white", relief="flat", padx=12, pady=6,
                  cursor="hand2", command=self._abrir_nueva_mascota).pack(side="left")

    def _construir_notebook(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tab_mascotas = _TabMascotas(self.notebook, self)
        self.tab_vacunas = _TabVacunasProximas(self.notebook, self)
        self.tab_dashboard = _TabDashboard(self.notebook, self)

        self.notebook.add(self.tab_mascotas, text=t("vet_tab_mascotas"))
        self.notebook.add(self.tab_vacunas, text=t("vet_tab_vacunas_proximas"))
        self.notebook.add(self.tab_dashboard, text=t("asist_tab_dashboard"))

        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self.refrescar_todo())

    def refrescar_todo(self):
        self.tab_mascotas.cargar()
        self.tab_vacunas.cargar()
        self.tab_dashboard.cargar()

    def _abrir_nueva_mascota(self):
        VentanaFichaMascota(self, self.usuario_actual, mascota_id=None,
                            on_cambio=self.refrescar_todo)

    def abrir_ficha(self, mascota_id: int):
        VentanaFichaMascota(self, self.usuario_actual, mascota_id=mascota_id,
                            on_cambio=self.refrescar_todo)


# ============================================================
# PESTAÑA: MASCOTAS
# ============================================================
class _TabMascotas(tk.Frame):
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

        self.var_incluir_fallecidos = tk.BooleanVar(value=False)
        tk.Checkbutton(interior, text=t("vet_incluir_fallecidos"), variable=self.var_incluir_fallecidos,
                       bg=GRIS_FONDO, font=("Segoe UI", 9),
                       command=self.cargar).pack(side="left")

        tk.Button(interior, text=t("vet_generar_pdf"), font=("Segoe UI", 9, "bold"), bg="white", fg=AZUL_RIBBON,
                  relief="solid", bd=1, cursor="hand2", activebackground="#eff6ff",
                  command=self._generar_pdf_seleccionado).pack(side="left", padx=(14, 0))
        tk.Button(interior, text=t("vet_enviar_correo"), font=("Segoe UI", 9, "bold"), bg="white", fg=VERDE,
                  relief="solid", bd=1, cursor="hand2", activebackground="#f0fdf4",
                  command=self._enviar_email_seleccionado).pack(side="left", padx=(8, 0))

        self.var_busqueda = tk.StringVar()
        entry = tk.Entry(interior, textvariable=self.var_busqueda, font=("Segoe UI", 9), width=28)
        entry.pack(side="right")
        entry.bind("<KeyRelease>", lambda e: self.cargar())
        tk.Label(interior, text="🔍", font=("Segoe UI", 10), bg=GRIS_FONDO).pack(side="right", padx=(0, 4))
        tk.Label(interior, text=t("vet_buscar_mascota"),
                 font=("Segoe UI", 9), bg=GRIS_FONDO).pack(side="right", padx=(0, 6))

    def _generar_pdf_seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showinfo("Selecciona una mascota",
                               "Primero hacé clic sobre una mascota de la lista y después "
                               "presioná \"Generar PDF\".", parent=self.panel_padre)
            return
        _generar_reporte_pdf_mascota(self.panel_padre, int(seleccion[0]))

    def _enviar_email_seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showinfo("Selecciona una mascota",
                               "Primero hacé clic sobre una mascota de la lista y después "
                               "presioná \"Enviar por Correo\".", parent=self.panel_padre)
            return
        _enviar_reporte_mascota_email(self.panel_padre, int(seleccion[0]), self.panel_padre.usuario_actual)

    def _construir_tabla(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=0, pady=(4, 0))
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        columnas = ("nombre", "especie", "raza", "sexo", "edad", "dueño", "telefono", "estado")
        encabezados = (t("col_mascota"), t("col_especie"), t("col_raza"), t("col_sexo"), t("col_edad"), t("col_dueno"), t("col_telefono").upper(), t("col_estado_mayus"))
        anchos = (140, 100, 130, 90, 110, 200, 120, 90)

        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho, anchor="w" if col in ("nombre", "dueño") else "center")

        sb_y = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb_y.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_y_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_y_h.set)
        sb_y_h.grid(row=1, column=0, sticky="ew")

        self.tabla.bind("<Double-1>", lambda e: self._abrir_seleccionado())
        self.tabla.tag_configure("fallecido", foreground=GRIS_TEXTO)

    def _abrir_seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        self.panel_padre.abrir_ficha(int(seleccion[0]))

    def cargar(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        mascotas = listar_mascotas(busqueda=self.var_busqueda.get(),
                                   incluir_fallecidos=self.var_incluir_fallecidos.get())
        for m in mascotas:
            estado = "Fallecido" if m["fallecido"] else "Activo"
            tags = ("fallecido",) if m["fallecido"] else ()
            self.tabla.insert("", "end", iid=str(m["id"]), tags=tags, values=(
                m["nombre"], m["especie"] or "—", m["raza"] or "—", m["sexo"],
                calcular_edad(m["fecha_nacimiento"]), m["dueño"], m["dueño_telefono"] or "—", estado,
            ))


# ============================================================
# PESTAÑA: VACUNAS PRÓXIMAS
# ============================================================
class _TabVacunasProximas(tk.Frame):
    def __init__(self, parent, panel_padre):
        super().__init__(parent, bg="white")
        self.panel_padre = panel_padre
        self._construir_tabla()
        self.cargar()

    def _construir_tabla(self):
        barra = tk.Frame(self, bg="white")
        barra.pack(fill="x", padx=10, pady=(10, 4))
        tk.Label(barra, text=t("vet_vacunas_vencidas"),
                 font=("Segoe UI", 10, "bold"), bg="white").pack(side="left")
        tk.Button(barra, text=t("vet_generar_pdf"), font=("Segoe UI", 9, "bold"), bg="white", fg=AZUL_RIBBON,
                  relief="solid", bd=1, cursor="hand2", activebackground="#eff6ff",
                  command=self._generar_pdf_seleccionado).pack(side="right", padx=(0, 0))
        tk.Button(barra, text=t("vet_enviar_correo"), font=("Segoe UI", 9, "bold"), bg="white", fg=VERDE,
                  relief="solid", bd=1, cursor="hand2", activebackground="#f0fdf4",
                  command=self._enviar_email_seleccionado).pack(side="right", padx=(0, 8))

        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        columnas = ("mascota", "dueño", "telefono", "vacuna", "vencimiento", "estado")
        encabezados = (t("col_mascota"), t("col_dueno"), t("col_telefono").upper(), t("col_vacuna"), t("col_vencimiento"), t("col_estado_mayus"))
        anchos = (140, 200, 120, 160, 110, 100)

        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho, anchor="w" if col in ("mascota", "dueño") else "center")

        sb_y = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb_y.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_y_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_y_h.set)
        sb_y_h.grid(row=1, column=0, sticky="ew")

        self.tabla.tag_configure("vencida", foreground=ROJO)
        self.tabla.tag_configure("proxima", foreground=NARANJA)
        self.tabla.bind("<Double-1>", lambda e: self._abrir_seleccionado())

    def _abrir_seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        idx = int(seleccion[0])
        if idx in self._mapa_mascota:
            self.panel_padre.abrir_ficha(self._mapa_mascota[idx])

    def _vacuna_id_seleccionada(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showinfo("Selecciona una vacuna",
                               "Primero hacé clic sobre una vacuna de la lista.", parent=self.panel_padre)
            return None
        idx = int(seleccion[0])
        return self._mapa_vacuna_id.get(idx)

    def _generar_pdf_seleccionado(self):
        vacuna_id = self._vacuna_id_seleccionada()
        if vacuna_id is not None:
            _generar_certificado_vacuna(self.panel_padre, vacuna_id)

    def _enviar_email_seleccionado(self):
        vacuna_id = self._vacuna_id_seleccionada()
        if vacuna_id is not None:
            _enviar_certificado_vacuna_email(self.panel_padre, vacuna_id, self.panel_padre.usuario_actual)

    def cargar(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        self._mapa_mascota = {}
        self._mapa_vacuna_id = {}
        for i, v in enumerate(listar_vacunas_proximas()):
            estado = "Vencida" if v["vencida"] else "Próxima"
            tag = "vencida" if v["vencida"] else "proxima"
            self.tabla.insert("", "end", iid=str(i), tags=(tag,), values=(
                v["mascota"], v["dueño"] or "—", v["dueño_telefono"] or "—",
                v["vacuna"], _formatear_fecha(v["proxima_dosis"]), estado,
            ))
            self._mapa_mascota[i] = v["mascota_id"]
            self._mapa_vacuna_id[i] = v["id"]


# ============================================================
# PESTAÑA: DASHBOARD
# ============================================================
class _TabDashboard(tk.Frame):
    def __init__(self, parent, panel_padre):
        super().__init__(parent, bg="white")
        self.panel_padre = panel_padre
        self._construir()
        self.cargar()

    def _construir(self):
        self.frame_tarjetas = tk.Frame(self, bg="white")
        self.frame_tarjetas.pack(fill="x", padx=10, pady=10)

        barra = tk.Frame(self, bg="white")
        barra.pack(fill="x", padx=10)
        tk.Label(barra, text=t("vet_consultas_hoy"), font=("Segoe UI", 10, "bold"), bg="white").pack(side="left")
        tk.Button(barra, text=t("vet_generar_pdf"), font=("Segoe UI", 9, "bold"), bg="white", fg=AZUL_RIBBON,
                  relief="solid", bd=1, cursor="hand2", activebackground="#eff6ff",
                  command=self._generar_pdf_seleccionado).pack(side="right")
        tk.Button(barra, text=t("vet_enviar_correo"), font=("Segoe UI", 9, "bold"), bg="white", fg=VERDE,
                  relief="solid", bd=1, cursor="hand2", activebackground="#f0fdf4",
                  command=self._enviar_email_seleccionado).pack(side="right", padx=(0, 8))

        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=10, pady=(4, 10))
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        columnas = ("hora", "mascota", "dueño", "motivo", "proxima")
        encabezados = (t("col_hora"), t("col_mascota"), t("col_dueno"), t("col_motivo"), t("col_prox_visita"))
        anchos = (100, 140, 200, 260, 110)
        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho, anchor="w" if col in ("mascota", "dueño", "motivo") else "center")
        sb_y = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb_y.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_y_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_y_h.set)
        sb_y_h.grid(row=1, column=0, sticky="ew")

    def _consulta_id_seleccionada(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showinfo("Selecciona una consulta",
                               "Primero hacé clic sobre una consulta de la lista.", parent=self.panel_padre)
            return None
        return int(seleccion[0])

    def _generar_pdf_seleccionado(self):
        consulta_id = self._consulta_id_seleccionada()
        if consulta_id is not None:
            _generar_reporte_consulta(self.panel_padre, consulta_id)

    def _enviar_email_seleccionado(self):
        consulta_id = self._consulta_id_seleccionada()
        if consulta_id is not None:
            _enviar_reporte_consulta_email(self.panel_padre, consulta_id, self.panel_padre.usuario_actual)

    def _crear_tarjeta(self, titulo: str, valor, color: str):
        marco = tk.Frame(self.frame_tarjetas, bg=color, padx=16, pady=10)
        marco.pack(side="left", padx=(0, 10))
        tk.Label(marco, text=str(valor), font=("Segoe UI", 16, "bold"), bg=color, fg="white").pack(anchor="w")
        tk.Label(marco, text=titulo, font=("Segoe UI", 9), bg=color, fg="white").pack(anchor="w")

    def cargar(self):
        for w in self.frame_tarjetas.winfo_children():
            w.destroy()
        conteos = conteos_dashboard()
        self._crear_tarjeta("Mascotas activas", conteos["total_mascotas"], AZUL_RIBBON)
        self._crear_tarjeta("Consultas hoy", conteos["consultas_hoy"], VERDE)
        self._crear_tarjeta("Tratamientos activos", conteos["tratamientos_activos"], NARANJA)
        self._crear_tarjeta("Vacunas próx./vencidas", conteos["vacunas_proximas"], ROJO)

        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        for c in listar_consultas_del_dia():
            hora = _formatear_fecha_hora(c["fecha"]).split(" ")[-1] if c["fecha"] else "—"
            self.tabla.insert("", "end", iid=str(c["id"]), values=(
                hora, c["mascota"], c["dueño"] or "—", c["motivo"], _formatear_fecha(c["proxima_visita"]),
            ))


# ============================================================
# FICHA DE MASCOTA (crear / editar + historial clínico, vacunas, tratamientos)
# ============================================================
class VentanaFichaMascota(tk.Toplevel):
    def __init__(self, parent, usuario_actual, mascota_id=None, on_cambio=None):
        super().__init__(parent)
        self.usuario_actual = usuario_actual
        self.mascota_id = mascota_id
        self.on_cambio = on_cambio
        self.cliente_seleccionado = None
        self.especie_id = None
        self.es_nueva = mascota_id is None

        self.title("Nueva Mascota" if self.es_nueva else "Ficha de la Mascota")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()
        # Nota: a propósito NO se usa self.transient(parent) aquí. En
        # algunos gestores de ventanas de Linux, transient() hace que la
        # ventana pierda los botones de minimizar/maximizar (se trata como
        # un diálogo secundario). grab_set() ya asegura que se comporte de
        # forma modal sin necesidad de transient().

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_titulo()
        self._construir_datos_mascota()
        self._construir_barra_botones()
        if not self.es_nueva:
            self._construir_sub_notebook()

        self.minsize(680, 560)
        ajustar_tamaño_ventana(self, ancho_min=680, alto_min=560, alto_max=self.winfo_screenheight() - 60)

        if not self.es_nueva:
            self._cargar_datos_mascota()

    def _construir_titulo(self):
        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        titulo = "🐾 Nueva Mascota" if self.es_nueva else "🐾 Ficha de la Mascota"
        tk.Label(barra, text=titulo, font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

    # ---------------- DATOS DE LA MASCOTA ----------------
    def _construir_datos_mascota(self):
        # Envolvemos el formulario (Dueño + Mascota) en una zona con scroll
        # propio, para que en pantallas chicas o con mucho contenido nunca
        # queden botones ni campos ocultos: siempre se puede desplazar.
        self.frame_datos, frame_scroll = _crear_seccion_scrollable(self)
        self.frame_datos.grid(row=1, column=0, sticky="nsew")
        contenedor = tk.Frame(frame_scroll, bg="white")
        contenedor.pack(fill="both", expand=True, padx=16, pady=(12, 6))

        # --- Sección Dueño ---
        seccion_dueño = tk.LabelFrame(contenedor, text=t("vet_seccion_dueno"), font=("Segoe UI", 9, "bold"),
                                      bg="white", padx=10, pady=10)
        seccion_dueño.pack(fill="x", pady=(0, 10))
        seccion_dueño.grid_columnconfigure(1, weight=1)

        tk.Label(seccion_dueño, text=t("nombre_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=0, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_dueño_nombre = tk.StringVar()
        entry_dueño = tk.Entry(seccion_dueño, textvariable=self.var_dueño_nombre, font=("Segoe UI", 10))
        entry_dueño.grid(row=0, column=1, sticky="ew", pady=4)
        forzar_mayusculas(entry_dueño, self.var_dueño_nombre)

        tk.Label(seccion_dueño, text=t("telefono_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=1, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_dueño_telefono = tk.StringVar()
        tk.Entry(seccion_dueño, textvariable=self.var_dueño_telefono, font=("Segoe UI", 10)).grid(
            row=1, column=1, sticky="ew", pady=4)

        tk.Button(seccion_dueño, text=t("vet_buscar_cliente"), font=("Segoe UI", 9, "bold"),
                  bg="white", relief="solid", bd=1, cursor="hand2",
                  command=self._abrir_buscar_cliente).grid(row=0, column=2, rowspan=2, padx=(10, 0))

        # --- Sección Mascota ---
        seccion_mascota = tk.LabelFrame(contenedor, text=t("vet_seccion_mascota"), font=("Segoe UI", 9, "bold"),
                                        bg="white", padx=10, pady=10)
        seccion_mascota.pack(fill="x")
        seccion_mascota.grid_columnconfigure(1, weight=1)
        seccion_mascota.grid_columnconfigure(3, weight=1)

        tk.Label(seccion_mascota, text=t("nombre_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=0, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_nombre = tk.StringVar()
        entry_nombre = tk.Entry(seccion_mascota, textvariable=self.var_nombre, font=("Segoe UI", 10))
        entry_nombre.grid(row=0, column=1, sticky="ew", pady=4)
        forzar_mayusculas(entry_nombre, self.var_nombre)

        tk.Label(seccion_mascota, text=t("especie_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=0, column=2, sticky="e", pady=4, padx=(10, 8))
        self.var_especie = tk.StringVar()
        self.combo_especie = ttk.Combobox(seccion_mascota, textvariable=self.var_especie, font=("Segoe UI", 10))
        self.combo_especie.grid(row=0, column=3, sticky="ew", pady=4)
        self._cargar_especies()

        tk.Label(seccion_mascota, text=t("raza_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=1, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_raza = tk.StringVar()
        entry_raza = tk.Entry(seccion_mascota, textvariable=self.var_raza, font=("Segoe UI", 10))
        entry_raza.grid(row=1, column=1, sticky="ew", pady=4)
        forzar_mayusculas(entry_raza, self.var_raza)

        tk.Label(seccion_mascota, text=t("color_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=1, column=2, sticky="e", pady=4, padx=(10, 8))
        self.var_color = tk.StringVar()
        entry_color = tk.Entry(seccion_mascota, textvariable=self.var_color, font=("Segoe UI", 10))
        entry_color.grid(row=1, column=3, sticky="ew", pady=4)
        forzar_mayusculas(entry_color, self.var_color)

        tk.Label(seccion_mascota, text=t("sexo_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=2, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_sexo = tk.StringVar(value="Desconocido")
        frame_sexo = tk.Frame(seccion_mascota, bg="white")
        frame_sexo.grid(row=2, column=1, sticky="w", pady=4)
        for s in SEXOS:
            tk.Radiobutton(frame_sexo, text=s, variable=self.var_sexo, value=s,
                          bg="white", font=("Segoe UI", 9)).pack(side="left", padx=(0, 10))

        tk.Label(seccion_mascota, text=t("vet_fecha_nacimiento"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=2, column=2, sticky="e", pady=4, padx=(10, 8))
        self.var_fecha_nacimiento = tk.StringVar()
        _campo_fecha(seccion_mascota, self.var_fecha_nacimiento, row=2, col=3)

        tk.Label(seccion_mascota, text=t("vet_peso_kg"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=3, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_peso = tk.StringVar()
        tk.Entry(seccion_mascota, textvariable=self.var_peso, font=("Segoe UI", 10), width=10).grid(
            row=3, column=1, sticky="w", pady=4)

        tk.Label(seccion_mascota, text=t("vet_microchip"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=3, column=2, sticky="e", pady=4, padx=(10, 8))
        self.var_microchip = tk.StringVar()
        entry_chip = tk.Entry(seccion_mascota, textvariable=self.var_microchip, font=("Segoe UI", 10))
        entry_chip.grid(row=3, column=3, sticky="ew", pady=4)
        forzar_mayusculas(entry_chip, self.var_microchip)

        self.var_esterilizado = tk.BooleanVar(value=False)
        tk.Checkbutton(seccion_mascota, text=t("vet_esterilizado"), variable=self.var_esterilizado,
                       bg="white", font=("Segoe UI", 9)).grid(row=4, column=1, sticky="w", pady=4)

        tk.Label(seccion_mascota, text=t("observaciones_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=5, column=0, sticky="ne", pady=4, padx=(0, 8))
        self.texto_observaciones = tk.Text(seccion_mascota, font=("Segoe UI", 9), height=3, relief="solid", bd=1)
        self.texto_observaciones.grid(row=5, column=1, columnspan=3, sticky="ew", pady=4)

        self._entry_nombre_para_foco = entry_nombre

    def _construir_barra_botones(self):
        self.frame_botones = tk.Frame(self, bg="white")
        self.frame_botones.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 10))
        self._reconstruir_botones()
        self._entry_nombre_para_foco.focus()

    def _reconstruir_botones(self):
        for w in self.frame_botones.winfo_children():
            w.destroy()
        botones = self.frame_botones
        if self.es_nueva:
            tk.Button(botones, text=t("cancelar_x"), font=("Segoe UI", 9, "bold"), bg="white",
                      relief="solid", bd=1, command=self.destroy).pack(side="left")
            tk.Button(botones, text=t("guardar_icono"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                      fg="white", relief="flat", padx=14, cursor="hand2",
                      command=self._guardar_mascota).pack(side="right")
        else:
            self.boton_fallecido = tk.Button(botones, text=t("vet_marcar_fallecido"), font=("Segoe UI", 9, "bold"),
                      bg="white", relief="solid", bd=1, cursor="hand2",
                      command=self._alternar_fallecido)
            self.boton_fallecido.pack(side="left")
            tk.Button(botones, text=t("vet_generar_pdf"), font=("Segoe UI", 9, "bold"), bg="white", fg=AZUL_RIBBON,
                      relief="solid", bd=1, cursor="hand2", activebackground="#eff6ff",
                      command=self._generar_reporte_pdf).pack(side="left", padx=(8, 0))
            tk.Button(botones, text=t("vet_enviar_correo"), font=("Segoe UI", 9, "bold"), bg="white", fg=VERDE,
                      relief="solid", bd=1, cursor="hand2", activebackground="#f0fdf4",
                      command=self._enviar_reporte_email).pack(side="left", padx=(8, 0))
            tk.Button(botones, text=t("guardar_cambios"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                      fg="white", relief="flat", padx=14, cursor="hand2",
                      command=self._guardar_mascota).pack(side="right")

    def _cargar_especies(self):
        self.especies = listar_especies()
        self.combo_especie["values"] = [e["nombre"] for e in self.especies]

    def _abrir_buscar_cliente(self):
        from ventanas_auxiliares_venta import VentanaAsignarCliente
        VentanaAsignarCliente(self, on_seleccionado=self._al_elegir_cliente)

    def _al_elegir_cliente(self, cliente):
        self.cliente_seleccionado = cliente
        if cliente:
            self.var_dueño_nombre.set(cliente["nombre"])
            self.var_dueño_telefono.set(cliente.get("telefono", ""))

    def _alternar_fallecido(self):
        datos = obtener_mascota(self.mascota_id)
        if datos is None:
            return
        nuevo_estado = not datos["fallecido"]
        marcar_fallecido(self.mascota_id, nuevo_estado)
        self._cargar_datos_mascota()
        if self.on_cambio:
            self.on_cambio()

    def _generar_reporte_pdf(self):
        _generar_reporte_pdf_mascota(self, self.mascota_id)

    def _enviar_reporte_email(self):
        _enviar_reporte_mascota_email(self, self.mascota_id, self.usuario_actual)

    def _cargar_datos_mascota(self):
        datos = obtener_mascota(self.mascota_id)
        if datos is None:
            messagebox.showerror("No encontrada", "Esta mascota ya no existe.", parent=self)
            self.destroy()
            return
        self.var_dueño_nombre.set(datos["dueño"] if datos["dueño"] != "Sin dueño registrado" else "")
        self.var_dueño_telefono.set(datos["dueño_telefono"])
        self.cliente_seleccionado = {"id": datos["cliente_id"]} if datos["cliente_id"] else None
        self.var_nombre.set(datos["nombre"])
        self.var_especie.set(datos["especie"])
        self.var_raza.set(datos["raza"])
        self.var_color.set(datos["color"])
        self.var_sexo.set(datos["sexo"])
        self.var_fecha_nacimiento.set(datos["fecha_nacimiento"])
        self.var_peso.set(str(datos["peso_kg"]) if datos["peso_kg"] else "")
        self.var_microchip.set(datos["microchip"])
        self.var_esterilizado.set(datos["esterilizado"])
        self.texto_observaciones.delete("1.0", "end")
        if datos["observaciones"]:
            self.texto_observaciones.insert("1.0", datos["observaciones"])
        self.boton_fallecido.config(
            text=t("vet_reactivar_ficha") if datos["fallecido"] else t("vet_marcar_fallecido"))
        self.title(f"Ficha de {datos['nombre']}" + (" (Fallecido)" if datos["fallecido"] else ""))

    def _resolver_especie(self):
        especie_texto = self.var_especie.get().strip()
        especie_id = None
        for e in self.especies:
            if e["nombre"] == especie_texto:
                especie_id = e["id"]
                break
        if especie_texto and especie_id is None:
            crear_especie(especie_texto)
            for e in listar_especies():
                if e["nombre"] == especie_texto:
                    especie_id = e["id"]
                    break
        return especie_id, especie_texto

    def _guardar_mascota(self):
        especie_id, especie_texto = self._resolver_especie()
        cliente_id = self.cliente_seleccionado["id"] if self.cliente_seleccionado else None
        try:
            peso = float(self.var_peso.get().replace(",", ".")) if self.var_peso.get().strip() else None
        except ValueError:
            messagebox.showwarning("Peso inválido", "Ingresa el peso como un número (ej. 4.5).", parent=self)
            return

        if self.es_nueva:
            ok, msg, nuevo_id = crear_mascota(
                nombre=self.var_nombre.get(), cliente_id=cliente_id,
                dueño_nombre=self.var_dueño_nombre.get(), dueño_telefono=self.var_dueño_telefono.get(),
                especie_id=especie_id, especie_texto=especie_texto, raza=self.var_raza.get(),
                sexo=self.var_sexo.get(), fecha_nacimiento=self.var_fecha_nacimiento.get(),
                color=self.var_color.get(), peso_kg=peso, microchip=self.var_microchip.get(),
                esterilizado=self.var_esterilizado.get(),
                observaciones=self.texto_observaciones.get("1.0", "end").strip(),
            )
            if not ok:
                messagebox.showerror("No se pudo guardar", msg, parent=self)
                return
            messagebox.showinfo("Mascota registrada", msg, parent=self)
            if self.on_cambio:
                self.on_cambio()
            self._transformar_a_modo_edicion(nuevo_id)
        else:
            ok, msg = editar_mascota(
                mascota_id=self.mascota_id, nombre=self.var_nombre.get(), cliente_id=cliente_id,
                dueño_nombre=self.var_dueño_nombre.get(), dueño_telefono=self.var_dueño_telefono.get(),
                especie_id=especie_id, especie_texto=especie_texto, raza=self.var_raza.get(),
                sexo=self.var_sexo.get(), fecha_nacimiento=self.var_fecha_nacimiento.get(),
                color=self.var_color.get(), peso_kg=peso, microchip=self.var_microchip.get(),
                esterilizado=self.var_esterilizado.get(),
                observaciones=self.texto_observaciones.get("1.0", "end").strip(),
            )
            if not ok:
                messagebox.showerror("No se pudo guardar", msg, parent=self)
                return
            self._cargar_datos_mascota()
            if self.on_cambio:
                self.on_cambio()
            ajustar_tamaño_ventana(self, ancho_min=680, alto_min=520, mantener_posicion=True)

    def _transformar_a_modo_edicion(self, mascota_id: int):
        """Al guardar una mascota nueva, en vez de cerrar la ventana la
        convertimos en la ficha completa (con Historial/Vacunas/Tratamientos
        y el botón Generar PDF), para que el usuario pueda seguir
        trabajando sobre ella sin tener que volver a abrirla."""
        self.mascota_id = mascota_id
        self.es_nueva = False
        self._reconstruir_botones()
        self._construir_sub_notebook()
        self._cargar_datos_mascota()
        ajustar_tamaño_ventana(self, ancho_min=680, alto_min=560,
                              alto_max=self.winfo_screenheight() - 60, mantener_posicion=True)

    # ---------------- SUB-NOTEBOOK: HISTORIAL / VACUNAS / TRATAMIENTOS ----------------
    def _construir_sub_notebook(self):
        self.sub_notebook = ttk.Notebook(self)
        self.sub_notebook.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.grid_rowconfigure(1, weight=1)   # formulario Dueño/Mascota (con scroll propio)
        self.grid_rowconfigure(3, weight=2)   # historial/vacunas/tratamientos (algo más de espacio)

        self.tab_historial = _TabHistorialClinico(self.sub_notebook, self)
        self.tab_vacunas = _TabVacunasMascota(self.sub_notebook, self)
        self.tab_tratamientos = _TabTratamientosMascota(self.sub_notebook, self)

        self.sub_notebook.add(self.tab_historial, text=t("vet_tab_historial_clinico"))
        self.sub_notebook.add(self.tab_vacunas, text=t("vet_tab_vacunas"))
        self.sub_notebook.add(self.tab_tratamientos, text=t("vet_tab_tratamientos"))


# ---------------- SUB-PESTAÑA: HISTORIAL CLÍNICO ----------------
class _TabHistorialClinico(tk.Frame):
    def __init__(self, parent, ficha: VentanaFichaMascota):
        super().__init__(parent, bg="white")
        self.ficha = ficha

        barra = tk.Frame(self, bg="white")
        barra.pack(fill="x", pady=(6, 4))
        tk.Button(barra, text=t("vet_nueva_consulta"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                  fg="white", relief="flat", padx=10, pady=4, cursor="hand2",
                  command=self._abrir_nueva_consulta).pack(side="left")

        columnas = ("fecha", "motivo", "diagnostico", "peso", "proxima", "costo")
        encabezados = (t("col_fecha_mayus"), t("col_motivo"), t("col_diagnostico"), t("col_peso"), t("col_prox_visita"), t("col_costo"))
        anchos = (100, 160, 200, 70, 100, 100)
        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho, anchor="w" if col in ("motivo", "diagnostico") else "center")
        sb_y = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb_y.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_y_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_y_h.set)
        sb_y_h.grid(row=1, column=0, sticky="ew")
        self.tabla.bind("<Double-1>", lambda e: self._ver_detalle())

        self.cargar()

    def _abrir_nueva_consulta(self):
        VentanaNuevaConsulta(self, self.ficha.usuario_actual, self.ficha.mascota_id,
                             on_guardado=self.cargar)

    def _ver_detalle(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        consultas = {c["id"]: c for c in listar_consultas_por_mascota(self.ficha.mascota_id)}
        c = consultas.get(int(seleccion[0]))
        if not c:
            return
        detalle = (
            f"Fecha: {_formatear_fecha_hora(c['fecha'])}\n"
            f"Motivo: {c['motivo']}\n"
            f"Diagnóstico: {c['diagnostico'] or '—'}\n"
            f"Tratamiento indicado: {c['tratamiento_indicado'] or '—'}\n"
            f"Peso: {c['peso_kg'] or '—'} Kg   Temperatura: {c['temperatura'] or '—'} °C\n"
            f"Observaciones: {c['observaciones'] or '—'}\n"
            f"Próxima visita: {_formatear_fecha(c['proxima_visita'])}\n"
            f"Atendido por: {c['atendido_por'] or '—'}"
        )
        messagebox.showinfo(f"Consulta #{c['id']}", detalle, parent=self.ficha)

    def cargar(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        for c in listar_consultas_por_mascota(self.ficha.mascota_id):
            self.tabla.insert("", "end", iid=str(c["id"]), values=(
                _formatear_fecha(c["fecha"]), c["motivo"], c["diagnostico"] or "—",
                f"{c['peso_kg']} Kg" if c["peso_kg"] else "—",
                _formatear_fecha(c["proxima_visita"]),
                f"Gs. {int(c['costo']):,}".replace(",", ".") if c["costo"] else "—",
            ))


# ---------------- SUB-PESTAÑA: VACUNAS ----------------
class _TabVacunasMascota(tk.Frame):
    def __init__(self, parent, ficha: VentanaFichaMascota):
        super().__init__(parent, bg="white")
        self.ficha = ficha

        barra = tk.Frame(self, bg="white")
        barra.pack(fill="x", pady=(6, 4))
        tk.Button(barra, text=t("vet_nueva_vacuna"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                  fg="white", relief="flat", padx=10, pady=4, cursor="hand2",
                  command=self._abrir_nueva_vacuna).pack(side="left")

        columnas = ("vacuna", "aplicacion", "proxima", "lote", "veterinario")
        encabezados = (t("col_vacuna"), t("col_fecha_aplicacion"), t("col_proxima_dosis"), t("col_lote"), t("col_veterinario"))
        anchos = (160, 130, 130, 100, 160)
        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho, anchor="w" if col in ("vacuna", "veterinario") else "center")
        sb_y = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb_y.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_y_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_y_h.set)
        sb_y_h.grid(row=1, column=0, sticky="ew")

        self.cargar()

    def _abrir_nueva_vacuna(self):
        VentanaNuevaVacuna(self, self.ficha.usuario_actual, self.ficha.mascota_id,
                           on_guardado=self.cargar)

    def cargar(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        for v in listar_vacunas_por_mascota(self.ficha.mascota_id):
            self.tabla.insert("", "end", iid=str(v["id"]), values=(
                v["vacuna"], _formatear_fecha(v["fecha_aplicacion"]),
                _formatear_fecha(v["proxima_dosis"]), v["lote"] or "—", v["veterinario"] or "—",
            ))


# ---------------- SUB-PESTAÑA: TRATAMIENTOS ----------------
class _TabTratamientosMascota(tk.Frame):
    def __init__(self, parent, ficha: VentanaFichaMascota):
        super().__init__(parent, bg="white")
        self.ficha = ficha

        barra = tk.Frame(self, bg="white")
        barra.pack(fill="x", pady=(6, 4))
        tk.Button(barra, text=t("vet_nuevo_tratamiento"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                  fg="white", relief="flat", padx=10, pady=4, cursor="hand2",
                  command=self._abrir_nuevo_tratamiento).pack(side="left")
        tk.Button(barra, text=t("vet_finalizar_seleccionado"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, cursor="hand2",
                  command=self._finalizar_seleccionado).pack(side="left", padx=(8, 0))

        columnas = ("tipo", "producto", "inicio", "fin", "dosis", "frecuencia", "estado")
        encabezados = (t("col_tipo"), t("col_producto_mayus"), t("col_inicio_mayus"), t("col_fin_mayus"), t("col_dosis"), t("col_frecuencia"), t("col_estado_mayus"))
        anchos = (110, 150, 100, 100, 100, 110, 90)
        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho, anchor="w" if col == "producto" else "center")
        sb_y = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb_y.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_y_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=sb_y_h.set)
        sb_y_h.grid(row=1, column=0, sticky="ew")

        self.tabla.tag_configure("activo", foreground=VERDE)
        self.cargar()

    def _abrir_nuevo_tratamiento(self):
        VentanaNuevoTratamiento(self, self.ficha.usuario_actual, self.ficha.mascota_id,
                                on_guardado=self.cargar)

    def _finalizar_seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showinfo("Selecciona un tratamiento", "Elige un tratamiento de la lista primero.",
                               parent=self.ficha)
            return
        finalizar_tratamiento(int(seleccion[0]))
        self.cargar()

    def cargar(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        for t in listar_tratamientos_por_mascota(self.ficha.mascota_id):
            tags = ("activo",) if t["estado"] == "Activo" else ()
            self.tabla.insert("", "end", iid=str(t["id"]), tags=tags, values=(
                t["tipo"], t["producto"], _formatear_fecha(t["fecha_inicio"]),
                _formatear_fecha(t["fecha_fin"]), t["dosis"] or "—", t["frecuencia"] or "—", t["estado"],
            ))


# ============================================================
# NUEVA CONSULTA
# ============================================================
class VentanaNuevaConsulta(tk.Toplevel):
    def __init__(self, parent, usuario_actual, mascota_id, on_guardado=None):
        super().__init__(parent)
        self.usuario_actual = usuario_actual
        self.mascota_id = mascota_id
        self.on_guardado = on_guardado

        self.title("Nueva Consulta")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()
        self.transient(parent)

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        tk.Label(barra, text=t("vet_titulo_nueva_consulta"), font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=16, pady=16)
        contenedor.grid_columnconfigure(1, weight=1)
        contenedor.grid_columnconfigure(3, weight=1)

        tk.Label(contenedor, text=t("motivo_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=0, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_motivo = tk.StringVar()
        entry_motivo = tk.Entry(contenedor, textvariable=self.var_motivo, font=("Segoe UI", 10))
        entry_motivo.grid(row=0, column=1, columnspan=3, sticky="ew", pady=4)
        forzar_mayusculas(entry_motivo, self.var_motivo)

        tk.Label(contenedor, text=t("vet_peso_kg"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=1, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_peso = tk.StringVar()
        tk.Entry(contenedor, textvariable=self.var_peso, font=("Segoe UI", 10), width=10).grid(
            row=1, column=1, sticky="w", pady=4)

        tk.Label(contenedor, text=t("vet_temperatura"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=1, column=2, sticky="e", pady=4, padx=(10, 8))
        self.var_temperatura = tk.StringVar()
        tk.Entry(contenedor, textvariable=self.var_temperatura, font=("Segoe UI", 10), width=10).grid(
            row=1, column=3, sticky="w", pady=4)

        tk.Label(contenedor, text=t("diagnostico_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=2, column=0, sticky="ne", pady=4, padx=(0, 8))
        self.texto_diagnostico = tk.Text(contenedor, font=("Segoe UI", 9), height=3, relief="solid", bd=1)
        self.texto_diagnostico.grid(row=2, column=1, columnspan=3, sticky="ew", pady=4)

        tk.Label(contenedor, text=t("vet_tratamiento_indicado"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=3, column=0, sticky="ne", pady=4, padx=(0, 8))
        self.texto_tratamiento = tk.Text(contenedor, font=("Segoe UI", 9), height=3, relief="solid", bd=1)
        self.texto_tratamiento.grid(row=3, column=1, columnspan=3, sticky="ew", pady=4)

        tk.Label(contenedor, text=t("observaciones_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=4, column=0, sticky="ne", pady=4, padx=(0, 8))
        self.texto_observaciones = tk.Text(contenedor, font=("Segoe UI", 9), height=3, relief="solid", bd=1)
        self.texto_observaciones.grid(row=4, column=1, columnspan=3, sticky="ew", pady=4)

        tk.Label(contenedor, text=t("vet_proxima_visita"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=5, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_proxima_visita = tk.StringVar()
        _campo_fecha(contenedor, self.var_proxima_visita, row=5, col=1)

        tk.Label(contenedor, text=t("vet_costo_gs"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=5, column=2, sticky="e", pady=4, padx=(10, 8))
        self.var_costo = tk.StringVar()
        tk.Entry(contenedor, textvariable=self.var_costo, font=("Segoe UI", 10), width=14).grid(
            row=5, column=3, sticky="w", pady=4)

        botones = tk.Frame(self, bg="white")
        botones.pack(fill="x", padx=16, pady=(0, 16))
        tk.Button(botones, text=t("cancelar_x"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="left")
        tk.Button(botones, text=t("guardar_icono"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                  fg="white", relief="flat", padx=14, cursor="hand2", command=self._guardar).pack(side="right")

        self.minsize(520, 460)
        ajustar_tamaño_ventana(self, ancho_min=520, alto_min=460)
        entry_motivo.focus()

    def _num_o_none(self, texto: str):
        texto = texto.strip().replace(",", ".")
        if not texto:
            return None
        try:
            return float(texto)
        except ValueError:
            return None

    def _guardar(self):
        peso = self._num_o_none(self.var_peso.get())
        temperatura = self._num_o_none(self.var_temperatura.get())
        costo = self._num_o_none(self.var_costo.get()) or 0

        ok, msg, _ = crear_consulta(
            mascota_id=self.mascota_id, motivo=self.var_motivo.get(),
            diagnostico=self.texto_diagnostico.get("1.0", "end").strip(),
            tratamiento_indicado=self.texto_tratamiento.get("1.0", "end").strip(),
            peso_kg=peso, temperatura=temperatura,
            observaciones=self.texto_observaciones.get("1.0", "end").strip(),
            proxima_visita=self.var_proxima_visita.get(), costo=costo,
            usuario_id=self.usuario_actual.get("id"),
        )
        if not ok:
            messagebox.showerror("No se pudo guardar", msg, parent=self)
            return
        messagebox.showinfo("Consulta registrada", msg, parent=self)
        if self.on_guardado:
            self.on_guardado()
        self.destroy()


# ============================================================
# NUEVA VACUNA
# ============================================================
class VentanaNuevaVacuna(tk.Toplevel):
    def __init__(self, parent, usuario_actual, mascota_id, on_guardado=None):
        super().__init__(parent)
        self.usuario_actual = usuario_actual
        self.mascota_id = mascota_id
        self.on_guardado = on_guardado

        self.title("Nueva Vacuna")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()
        self.transient(parent)

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        tk.Label(barra, text=t("vet_titulo_nueva_vacuna"), font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=16, pady=16)
        contenedor.grid_columnconfigure(1, weight=1)

        tk.Label(contenedor, text=t("vacuna_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=0, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_vacuna = tk.StringVar()
        entry_vacuna = tk.Entry(contenedor, textvariable=self.var_vacuna, font=("Segoe UI", 10))
        entry_vacuna.grid(row=0, column=1, sticky="ew", pady=4)
        forzar_mayusculas(entry_vacuna, self.var_vacuna)

        tk.Label(contenedor, text=t("vet_fecha_aplicacion_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=1, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_fecha_aplicacion = tk.StringVar(value=datetime.date.today().isoformat())
        _campo_fecha(contenedor, self.var_fecha_aplicacion, row=1, col=1)

        tk.Label(contenedor, text=t("vet_proxima_dosis_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=2, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_proxima_dosis = tk.StringVar()
        _campo_fecha(contenedor, self.var_proxima_dosis, row=2, col=1)

        tk.Label(contenedor, text=t("lote_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=3, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_lote = tk.StringVar()
        entry_lote = tk.Entry(contenedor, textvariable=self.var_lote, font=("Segoe UI", 10))
        entry_lote.grid(row=3, column=1, sticky="ew", pady=4)
        forzar_mayusculas(entry_lote, self.var_lote)

        tk.Label(contenedor, text=t("veterinario_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=4, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_veterinario = tk.StringVar(value=usuario_actual.get("nombre_completo", ""))
        entry_vet = tk.Entry(contenedor, textvariable=self.var_veterinario, font=("Segoe UI", 10))
        entry_vet.grid(row=4, column=1, sticky="ew", pady=4)
        forzar_mayusculas(entry_vet, self.var_veterinario)

        tk.Label(contenedor, text=t("observaciones_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=5, column=0, sticky="ne", pady=4, padx=(0, 8))
        self.texto_observaciones = tk.Text(contenedor, font=("Segoe UI", 9), height=3, relief="solid", bd=1)
        self.texto_observaciones.grid(row=5, column=1, sticky="ew", pady=4)

        botones = tk.Frame(self, bg="white")
        botones.pack(fill="x", padx=16, pady=(0, 16))
        tk.Button(botones, text=t("cancelar_x"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="left")
        tk.Button(botones, text=t("guardar_icono"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                  fg="white", relief="flat", padx=14, cursor="hand2", command=self._guardar).pack(side="right")

        self.minsize(440, 400)
        ajustar_tamaño_ventana(self, ancho_min=440, alto_min=400)
        entry_vacuna.focus()

    def _guardar(self):
        ok, msg = crear_vacuna(
            mascota_id=self.mascota_id, vacuna=self.var_vacuna.get(),
            proxima_dosis=self.var_proxima_dosis.get(), lote=self.var_lote.get(),
            veterinario=self.var_veterinario.get(),
            observaciones=self.texto_observaciones.get("1.0", "end").strip(),
            usuario_id=self.usuario_actual.get("id"),
            fecha_aplicacion=self.var_fecha_aplicacion.get() or None,
        )
        if not ok:
            messagebox.showerror("No se pudo guardar", msg, parent=self)
            return
        messagebox.showinfo("Vacuna registrada", msg, parent=self)
        if self.on_guardado:
            self.on_guardado()
        self.destroy()


# ============================================================
# NUEVO TRATAMIENTO
# ============================================================
class VentanaNuevoTratamiento(tk.Toplevel):
    def __init__(self, parent, usuario_actual, mascota_id, on_guardado=None):
        super().__init__(parent)
        self.usuario_actual = usuario_actual
        self.mascota_id = mascota_id
        self.on_guardado = on_guardado

        self.title("Nuevo Tratamiento")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()
        self.transient(parent)

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        tk.Label(barra, text=t("vet_titulo_nuevo_tratamiento"), font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=16, pady=16)
        contenedor.grid_columnconfigure(1, weight=1)

        tk.Label(contenedor, text=t("tipo_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=0, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_tipo = tk.StringVar(value=TIPOS_TRATAMIENTO[0])
        frame_tipo = tk.Frame(contenedor, bg="white")
        frame_tipo.grid(row=0, column=1, sticky="w", pady=4)
        for t in TIPOS_TRATAMIENTO:
            tk.Radiobutton(frame_tipo, text=t, variable=self.var_tipo, value=t,
                          bg="white", font=("Segoe UI", 9)).pack(side="left", padx=(0, 10))

        tk.Label(contenedor, text=t("vet_producto_medicamento"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=1, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_producto = tk.StringVar()
        entry_producto = tk.Entry(contenedor, textvariable=self.var_producto, font=("Segoe UI", 10))
        entry_producto.grid(row=1, column=1, sticky="ew", pady=4)
        forzar_mayusculas(entry_producto, self.var_producto)

        tk.Label(contenedor, text=t("dosis_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=2, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_dosis = tk.StringVar()
        tk.Entry(contenedor, textvariable=self.var_dosis, font=("Segoe UI", 10)).grid(
            row=2, column=1, sticky="ew", pady=4)

        tk.Label(contenedor, text=t("frecuencia_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=3, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_frecuencia = tk.StringVar()
        tk.Entry(contenedor, textvariable=self.var_frecuencia, font=("Segoe UI", 10)).grid(
            row=3, column=1, sticky="ew", pady=4)

        tk.Label(contenedor, text=t("vet_fecha_fin_estimada"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=4, column=0, sticky="e", pady=4, padx=(0, 8))
        self.var_fecha_fin = tk.StringVar()
        _campo_fecha(contenedor, self.var_fecha_fin, row=4, col=1)

        tk.Label(contenedor, text=t("observaciones_label"), font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=5, column=0, sticky="ne", pady=4, padx=(0, 8))
        self.texto_observaciones = tk.Text(contenedor, font=("Segoe UI", 9), height=3, relief="solid", bd=1)
        self.texto_observaciones.grid(row=5, column=1, sticky="ew", pady=4)

        botones = tk.Frame(self, bg="white")
        botones.pack(fill="x", padx=16, pady=(0, 16))
        tk.Button(botones, text=t("cancelar_x"), font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, command=self.destroy).pack(side="left")
        tk.Button(botones, text=t("guardar_icono"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                  fg="white", relief="flat", padx=14, cursor="hand2", command=self._guardar).pack(side="right")

        self.minsize(460, 420)
        ajustar_tamaño_ventana(self, ancho_min=460, alto_min=420)
        entry_producto.focus()

    def _guardar(self):
        ok, msg = crear_tratamiento(
            mascota_id=self.mascota_id, tipo=self.var_tipo.get(), producto=self.var_producto.get(),
            fecha_fin=self.var_fecha_fin.get(), dosis=self.var_dosis.get(),
            frecuencia=self.var_frecuencia.get(),
            observaciones=self.texto_observaciones.get("1.0", "end").strip(),
            usuario_id=self.usuario_actual.get("id"),
        )
        if not ok:
            messagebox.showerror("No se pudo guardar", msg, parent=self)
            return
        messagebox.showinfo("Tratamiento registrado", msg, parent=self)
        if self.on_guardado:
            self.on_guardado()
        self.destroy()
