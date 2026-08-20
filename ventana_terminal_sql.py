"""
ventana_terminal_sql.py
Módulo "Terminal SQL": acceso avanzado y directo a la base de datos
SQLite del sistema, para ejecutar consultas SQL manuales (SELECT,
INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, etc.) sobre cualquier
tabla, sin pasar por las pantallas normales del sistema.

Pensado como una herramienta de administrador para casos que las
pantallas comunes no cubren (correcciones puntuales, consultas de
diagnóstico, limpiezas específicas). Solo accesible para
Administradores (ver auth.MODULOS_SOLO_ADMIN).

Medidas de seguridad incluidas:
  - "Modo solo lectura" activado por defecto: solo permite SELECT /
    PRAGMA / EXPLAIN / WITH. Para poder escribir (INSERT, UPDATE,
    DELETE, CREATE, ALTER, DROP, etc.) hay que desactivarlo a
    propósito con el candado.
  - Antes de ejecutar cualquier sentencia que modifique datos o el
    esquema, se pide una confirmación explícita mostrando la consulta
    completa, y el sistema genera automáticamente un backup completo
    de la base de datos (igual que en Gestión de Datos) ANTES de
    ejecutarla, para poder deshacer el cambio si algo sale mal.
  - Alerta reforzada si un UPDATE o DELETE no tiene cláusula WHERE
    (afectaría TODAS las filas de la tabla).
  - Solo se ejecuta UNA sentencia SQL por vez (no se admite encadenar
    varias separadas por ';'), para evitar efectos en cadena
    inesperados de una sola pasada.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import os
import re
import shutil
import sqlite3

from database import conectar, obtener_ruta_bd
from utilidades_ui import habilitar_deseleccion_treeview
from traducciones import t

AZUL_RIBBON = "#1d5fd6"
AZUL_OSCURO = "#163d8c"
GRIS_FONDO  = "#f4f5f7"
GRIS_BORDE  = "#e2e8f0"
BLANCO      = "#ffffff"
VERDE       = "#16a34a"
ROJO        = "#dc2626"
NARANJA     = "#d97706"
GRIS_TEXTO  = "#6b7280"
NEGRO       = "#1e293b"

# Sentencias que nunca modifican datos ni esquema: siempre permitidas,
# incluso con "Modo solo lectura" activado.
PALABRAS_SOLO_LECTURA = ("select", "pragma", "explain", "with")

MAX_FILAS_HISTORIAL = 50
LIMITE_FILAS_RESULTADO = 500  # tope de filas que se muestran en la grilla


def _tipo_sentencia(sql: str) -> str:
    """Primera palabra clave de la sentencia (en minúsculas), para decidir
    si es de solo lectura o no. Ignora paréntesis/espacios iniciales."""
    texto = sql.strip().lstrip("(")
    m = re.match(r"([a-zA-Z]+)", texto)
    return m.group(1).lower() if m else ""


def _quitar_comentarios_y_strings(sql: str) -> str:
    """Versión simplificada de la consulta sin literales de texto ni
    comentarios, usada solo para detectar heurísticamente cosas como
    '¿tiene WHERE?' o '¿hay más de una sentencia?' sin confundirse con
    un ';' o la palabra 'where' dentro de un string."""
    sin_comentarios = re.sub(r"--[^\n]*", " ", sql)
    sin_comentarios = re.sub(r"/\*.*?\*/", " ", sin_comentarios, flags=re.S)
    return re.sub(r"'(?:[^']|'')*'", "''", sin_comentarios)


def _es_multisentencia(sql: str) -> bool:
    """True si hay contenido real después de un ';' (más de una sentencia)."""
    limpio = _quitar_comentarios_y_strings(sql).strip()
    if limpio.endswith(";"):
        limpio = limpio[:-1]
    return ";" in limpio


def _tiene_where(sql: str) -> bool:
    limpio = _quitar_comentarios_y_strings(sql)
    return re.search(r"\bwhere\b", limpio, flags=re.IGNORECASE) is not None


class PanelTerminalSQL(tk.Frame):
    def __init__(self, parent, usuario_actual):
        super().__init__(parent, bg=GRIS_FONDO)
        self.usuario_actual = usuario_actual
        self.var_solo_lectura = tk.BooleanVar(value=True)
        self.historial = []  # lista de strings, más reciente primero

        self._construir_ui()
        self._cargar_tablas()

    # ── UI ─────────────────────────────────────────────────────
    def _construir_ui(self):
        encabezado = tk.Frame(self, bg=AZUL_RIBBON, height=54)
        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)
        tk.Label(encabezado, text=t("sql_titulo"),
                 font=("Segoe UI", 15, "bold"), bg=AZUL_RIBBON, fg=BLANCO
                 ).pack(side="left", padx=20, pady=12)

        aviso = tk.Frame(self, bg="#fefce8")
        aviso.pack(fill="x")
        tk.Frame(aviso, bg="#fbbf24", width=4).pack(side="left", fill="y")
        tk.Label(aviso,
                 text="⚠  Herramienta avanzada: ejecuta sentencias directamente sobre la base de "
                      "datos, sin las validaciones de las pantallas normales. Una consulta mal "
                      "escrita puede dañar información real. Usala con cuidado.",
                 font=("Segoe UI", 8, "italic"), bg="#fefce8", fg="#92400e",
                 justify="left", wraplength=900, padx=10, pady=6).pack(side="left", fill="x", expand=True)

        cuerpo = tk.Frame(self, bg=GRIS_FONDO)
        cuerpo.pack(fill="both", expand=True)
        cuerpo.grid_rowconfigure(0, weight=1)
        cuerpo.grid_columnconfigure(1, weight=1)

        self._construir_panel_izquierdo(cuerpo)
        self._construir_panel_derecho(cuerpo)

    # ── Panel izquierdo: Tablas + Historial ─────────────────────
    def _construir_panel_izquierdo(self, parent):
        panel = tk.Frame(parent, bg=BLANCO, width=230,
                         highlightthickness=1, highlightbackground=GRIS_BORDE)
        panel.grid(row=0, column=0, sticky="nsew", padx=(10, 6), pady=10)
        panel.grid_propagate(False)
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_rowconfigure(3, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        tk.Label(panel, text=t("sql_tablas"), font=("Segoe UI", 10, "bold"),
                 bg=BLANCO, fg=NEGRO).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 4))

        frame_tablas = tk.Frame(panel, bg=BLANCO)
        frame_tablas.grid(row=1, column=0, sticky="nsew", padx=10)
        frame_tablas.grid_rowconfigure(0, weight=1)
        frame_tablas.grid_columnconfigure(0, weight=1)
        self.lista_tablas = tk.Listbox(frame_tablas, font=("Consolas", 9),
                                       relief="solid", bd=1, activestyle="none",
                                       selectbackground=AZUL_RIBBON, selectforeground=BLANCO)
        self.lista_tablas.grid(row=0, column=0, sticky="nsew")
        sb_tablas = ttk.Scrollbar(frame_tablas, orient="vertical", command=self.lista_tablas.yview)
        self.lista_tablas.configure(yscrollcommand=sb_tablas.set)
        sb_tablas.grid(row=0, column=1, sticky="ns")
        self.lista_tablas.bind("<Double-Button-1>", self._al_elegir_tabla)
        tk.Label(panel, text=t("sql_doble_clic"),
                 font=("Segoe UI", 7, "italic"), bg=BLANCO, fg=GRIS_TEXTO
                 ).grid(row=2, column=0, sticky="w", padx=10, pady=(2, 10))

        tk.Label(panel, text=t("sql_historial"), font=("Segoe UI", 10, "bold"),
                 bg=BLANCO, fg=NEGRO).grid(row=2, column=0, sticky="w", padx=10, pady=(4, 4))

        frame_hist = tk.Frame(panel, bg=BLANCO)
        frame_hist.grid(row=3, column=0, sticky="nsew", padx=10, pady=(4, 10))
        frame_hist.grid_rowconfigure(0, weight=1)
        frame_hist.grid_columnconfigure(0, weight=1)
        self.lista_historial = tk.Listbox(frame_hist, font=("Consolas", 8),
                                          relief="solid", bd=1, activestyle="none",
                                          selectbackground=AZUL_RIBBON, selectforeground=BLANCO)
        self.lista_historial.grid(row=0, column=0, sticky="nsew")
        sb_hist = ttk.Scrollbar(frame_hist, orient="vertical", command=self.lista_historial.yview)
        self.lista_historial.configure(yscrollcommand=sb_hist.set)
        sb_hist.grid(row=0, column=1, sticky="ns")
        self.lista_historial.bind("<Double-Button-1>", self._al_elegir_historial)

    # ── Panel derecho: editor + resultados ──────────────────────
    def _construir_panel_derecho(self, parent):
        panel = tk.Frame(parent, bg=GRIS_FONDO)
        panel.grid(row=0, column=1, sticky="nsew", padx=(4, 10), pady=10)
        panel.grid_rowconfigure(2, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # Editor SQL
        frame_editor = tk.Frame(panel, bg=BLANCO, highlightthickness=1,
                                highlightbackground=GRIS_BORDE)
        frame_editor.grid(row=0, column=0, sticky="ew")
        frame_editor.grid_columnconfigure(0, weight=1)

        self.texto_sql = tk.Text(frame_editor, font=("Consolas", 10), height=6,
                                 wrap="word", relief="flat", bd=0, padx=8, pady=8,
                                 undo=True)
        self.texto_sql.grid(row=0, column=0, sticky="ew", padx=(2, 0), pady=2)
        sb_editor = ttk.Scrollbar(frame_editor, orient="vertical", command=self.texto_sql.yview)
        self.texto_sql.configure(yscrollcommand=sb_editor.set)
        sb_editor.grid(row=0, column=1, sticky="ns", pady=2)
        self.texto_sql.insert("1.0", "SELECT * FROM productos LIMIT 100;")
        self.texto_sql.bind("<Control-Return>", lambda e: (self._ejecutar(), "break")[1])
        self.texto_sql.bind("<F5>", lambda e: (self._ejecutar(), "break")[1])

        # Barra de acciones
        barra = tk.Frame(panel, bg=GRIS_FONDO)
        barra.grid(row=1, column=0, sticky="ew", pady=(8, 8))

        tk.Button(barra, text=t("sql_ejecutar"), font=("Segoe UI", 9, "bold"),
                  bg=AZUL_RIBBON, fg=BLANCO, relief="flat", padx=14, pady=6, cursor="hand2",
                  activebackground=AZUL_OSCURO, activeforeground=BLANCO,
                  command=self._ejecutar).pack(side="left")
        tk.Button(barra, text=t("sql_limpiar"), font=("Segoe UI", 9, "bold"),
                  bg=BLANCO, fg="#333", relief="solid", bd=1, padx=12, pady=6, cursor="hand2",
                  command=self._limpiar_editor).pack(side="left", padx=(8, 0))

        chk = tk.Checkbutton(barra, text=t("sql_modo_lectura"),
                             variable=self.var_solo_lectura, font=("Segoe UI", 9, "bold"),
                             bg=GRIS_FONDO, fg=NEGRO, activebackground=GRIS_FONDO,
                             command=self._al_cambiar_solo_lectura)
        chk.pack(side="left", padx=(20, 0))

        self.label_estado = tk.Label(barra, text="", font=("Segoe UI", 9, "bold"),
                                     bg=GRIS_FONDO, fg=GRIS_TEXTO, anchor="e")
        self.label_estado.pack(side="right", padx=(0, 4))

        # Resultados
        frame_resultados = tk.Frame(panel, bg=BLANCO, highlightthickness=1,
                                    highlightbackground=GRIS_BORDE)
        frame_resultados.grid(row=2, column=0, sticky="nsew")
        frame_resultados.grid_rowconfigure(0, weight=1)
        frame_resultados.grid_columnconfigure(0, weight=1)

        self.tabla_resultados = ttk.Treeview(frame_resultados, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla_resultados)
        self.tabla_resultados.grid(row=0, column=0, sticky="nsew")
        sb_res_y = ttk.Scrollbar(frame_resultados, orient="vertical", command=self.tabla_resultados.yview)
        self.tabla_resultados.configure(yscrollcommand=sb_res_y.set)
        sb_res_y.grid(row=0, column=1, sticky="ns")
        sb_res_x = ttk.Scrollbar(frame_resultados, orient="horizontal", command=self.tabla_resultados.xview)
        self.tabla_resultados.configure(xscrollcommand=sb_res_x.set)
        sb_res_x.grid(row=1, column=0, sticky="ew")

    # ── Carga inicial de tablas ──────────────────────────────────
    def _cargar_tablas(self):
        self.lista_tablas.delete(0, tk.END)
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            nombres = [f[0] for f in cur.fetchall()]
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Error al leer tablas", str(e), parent=self)
            return
        for nombre in nombres:
            self.lista_tablas.insert(tk.END, nombre)

    def _al_elegir_tabla(self, event=None):
        sel = self.lista_tablas.curselection()
        if not sel:
            return
        tabla = self.lista_tablas.get(sel[0])
        self.texto_sql.delete("1.0", "end")
        self.texto_sql.insert("1.0", f"SELECT * FROM {tabla} LIMIT 100;")
        self._ejecutar()

    def _al_elegir_historial(self, event=None):
        sel = self.lista_historial.curselection()
        if not sel:
            return
        consulta = self.historial[sel[0]]
        self.texto_sql.delete("1.0", "end")
        self.texto_sql.insert("1.0", consulta)
        self.texto_sql.focus_set()

    def _al_cambiar_solo_lectura(self):
        if not self.var_solo_lectura.get():
            messagebox.showwarning(
                "Modo escritura activado",
                "Desactivaste 'Modo solo lectura'.\n\n"
                "Ahora se pueden ejecutar sentencias que MODIFICAN datos o el "
                "esquema (INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, etc.).\n\n"
                "Antes de cada una se pedirá confirmación y se hará un backup "
                "automático de la base de datos, pero igual conviene revisar bien "
                "la consulta antes de ejecutarla.",
                parent=self,
            )

    def _limpiar_editor(self):
        self.texto_sql.delete("1.0", "end")
        self.texto_sql.focus_set()

    # ── Historial ────────────────────────────────────────────────
    def _agregar_al_historial(self, sql: str):
        sql = sql.strip()
        if self.historial and self.historial[0] == sql:
            return
        self.historial.insert(0, sql)
        del self.historial[MAX_FILAS_HISTORIAL:]
        self.lista_historial.delete(0, tk.END)
        for consulta in self.historial:
            resumen = " ".join(consulta.split())
            if len(resumen) > 60:
                resumen = resumen[:57] + "..."
            self.lista_historial.insert(tk.END, resumen)

    # ── Backup automático antes de escribir ─────────────────────
    def _crear_backup_automatico(self) -> str | None:
        try:
            ruta_bd = obtener_ruta_bd()
            carpeta = os.path.dirname(ruta_bd)
            ahora = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            destino = os.path.join(carpeta, f"backup_auto_terminal_sql_{ahora}.db")
            shutil.copy2(ruta_bd, destino)
            return destino
        except OSError as e:
            messagebox.showerror(
                "No se pudo crear el backup",
                f"No se ejecutó la consulta porque no se pudo generar el backup "
                f"automático previo:\n{e}",
                parent=self,
            )
            return None

    # ── Ejecutar ─────────────────────────────────────────────────
    def _ejecutar(self):
        sql = self.texto_sql.get("1.0", "end").strip()
        if not sql:
            return

        if _es_multisentencia(sql):
            messagebox.showwarning(
                "Una sentencia por vez",
                "Solo se puede ejecutar UNA sentencia SQL a la vez.\n\n"
                "Se detectó contenido después de un ';'. Separá las consultas "
                "y ejecutalas una por una.",
                parent=self,
            )
            return

        tipo = _tipo_sentencia(sql)
        es_lectura = tipo in PALABRAS_SOLO_LECTURA

        if not es_lectura:
            if self.var_solo_lectura.get():
                messagebox.showwarning(
                    "Modo solo lectura activado",
                    f"Esta consulta ({tipo.upper()}) modifica datos o el esquema, "
                    "y 'Modo solo lectura' está activado.\n\n"
                    "Destildá el candado '🔒 Modo solo lectura' si realmente "
                    "querés ejecutarla.",
                    parent=self,
                )
                return

            advertencia_extra = ""
            if tipo in ("update", "delete") and not _tiene_where(sql):
                advertencia_extra = (
                    "\n\n⚠⚠ ESTA CONSULTA NO TIENE 'WHERE' ⚠⚠\n"
                    f"Va a afectar TODAS las filas de la tabla con {tipo.upper()}."
                )

            confirmar = messagebox.askyesno(
                "Confirmar ejecución",
                f"Estás por ejecutar esta sentencia {tipo.upper()}:\n\n{sql}\n\n"
                "Antes de ejecutarla se hará un backup automático completo de la "
                "base de datos, para poder restaurarla desde Gestión de Datos si "
                f"algo sale mal.{advertencia_extra}\n\n¿Continuar?",
                icon="warning", parent=self,
            )
            if not confirmar:
                return

            ruta_backup = self._crear_backup_automatico()
            if not ruta_backup:
                return

        try:
            conn = conectar()
            cursor = conn.cursor()
            inicio = datetime.datetime.now()
            cursor.execute(sql)
            duracion_ms = (datetime.datetime.now() - inicio).total_seconds() * 1000

            if es_lectura:
                columnas = [d[0] for d in (cursor.description or [])]
                filas = cursor.fetchmany(LIMITE_FILAS_RESULTADO + 1)
                truncado = len(filas) > LIMITE_FILAS_RESULTADO
                filas = filas[:LIMITE_FILAS_RESULTADO]
                conn.close()
                self._mostrar_resultados(columnas, filas)
                texto_estado = f"✔ {len(filas)} fila(s) devuelta(s) en {duracion_ms:.0f} ms"
                if truncado:
                    texto_estado += f" (mostrando las primeras {LIMITE_FILAS_RESULTADO})"
                self.label_estado.config(text=texto_estado, fg=VERDE)
            else:
                conn.commit()
                filas_afectadas = cursor.rowcount
                conn.close()
                self._limpiar_resultados()
                self.label_estado.config(
                    text=f"✔ {tipo.upper()} ejecutado — "
                         f"{filas_afectadas if filas_afectadas >= 0 else 0} fila(s) afectada(s) "
                         f"en {duracion_ms:.0f} ms",
                    fg=VERDE,
                )
                self._cargar_tablas()  # por si se creó/eliminó una tabla

            self._agregar_al_historial(sql)

        except sqlite3.Error as e:
            try:
                conn.close()
            except Exception:
                pass
            self.label_estado.config(text=t("sql_error_consulta"), fg=ROJO)
            messagebox.showerror("Error de SQL", str(e), parent=self)

    # ── Resultados ───────────────────────────────────────────────
    def _limpiar_resultados(self):
        self.tabla_resultados.delete(*self.tabla_resultados.get_children())
        self.tabla_resultados["columns"] = ()

    def _mostrar_resultados(self, columnas, filas):
        self.tabla_resultados.delete(*self.tabla_resultados.get_children())
        self.tabla_resultados["columns"] = columnas
        for col in columnas:
            self.tabla_resultados.heading(col, text=col)
            self.tabla_resultados.column(col, width=120, anchor="w")
        for i, fila in enumerate(filas):
            valores = ["" if v is None else str(v) for v in fila]
            self.tabla_resultados.insert("", "end", iid=str(i), values=valores)


class VentanaTerminalSQL(tk.Toplevel):
    """Envoltorio en ventana flotante de PanelTerminalSQL, para poder
    abrir la herramienta desde otras pantallas (ej. el botón 'Terminal
    SQL' de Gestión de Datos) sin salir de donde se esté."""

    def __init__(self, parent, usuario_actual):
        super().__init__(parent)
        self.title("Terminal SQL")
        self.configure(bg=GRIS_FONDO)
        self.resizable(True, True)
        self.grab_set()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        panel = PanelTerminalSQL(self, usuario_actual)
        panel.grid(row=0, column=0, sticky="nsew")

        self.minsize(880, 560)
        self.geometry("1000x650")
