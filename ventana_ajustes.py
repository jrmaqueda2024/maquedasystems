"""
ventana_ajustes.py
Módulo "Ajustes del Sistema": permite al administrador cambiar la
tipografía y el tamaño de letra de TODO el sistema, con vista previa en
vivo y un botón para restablecer los valores de fábrica.

Solo accesible para administradores (ver MODULOS_SOLO_ADMIN en auth.py).
"""
import tkinter as tk
from tkinter import ttk, messagebox

import fuentes
import temas
from models_configuracion import FAMILIAS_DE_FUENTE_DISPONIBLES

AZUL       = "#1d5fd6"
AZUL_OSC   = "#163d8c"
GRIS_FONDO = "#f4f5f7"
GRIS_BORDE = "#e2e8f0"
BLANCO     = "#ffffff"
VERDE      = "#16a34a"
ROJO       = "#dc2626"
GRIS_TEXT  = "#6b7280"
NEGRO      = "#1e293b"

PASO_ESCALA = 5
ESCALA_MIN = 60
ESCALA_MAX = 200


class PanelAjustes(tk.Frame):
    def __init__(self, parent, usuario_actual):
        super().__init__(parent, bg=temas.c(BLANCO))
        self.usuario_actual = usuario_actual
        self._construir_ui()

    # ── UI raíz ──────────────────────────────────────────────────
    def _construir_ui(self):
        encabezado = tk.Frame(self, bg=temas.c(AZUL), height=54)
        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)
        tk.Label(encabezado, text="🔤  Ajustes del Sistema",
                 font=fuentes.f(15, "bold"), bg=temas.c(AZUL), fg=temas.c(BLANCO)
                 ).pack(side="left", padx=20, pady=12)

        cuerpo = tk.Frame(self, bg=temas.c(BLANCO), padx=24, pady=20)
        cuerpo.pack(fill="both", expand=True)

        tk.Label(cuerpo, text="Apariencia: fuente y tamaño de letra",
                 font=fuentes.f(13, "bold"), bg=temas.c(BLANCO), fg=temas.c(NEGRO)
                 ).pack(anchor="w")
        tk.Label(cuerpo,
                 text="Este cambio se aplica a TODO el sistema, al instante, "
                      "para cualquier usuario que esté usando el programa.",
                 font=fuentes.f(9), bg=temas.c(BLANCO), fg=temas.c(GRIS_TEXT),
                 wraplength=560, justify="left").pack(anchor="w", pady=(2, 16))

        panel_ctrl = tk.Frame(cuerpo, bg=temas.c(GRIS_FONDO), padx=18, pady=16)
        panel_ctrl.pack(fill="x")

        # --- Tema (Claro / Oscuro) ---
        fila_tema = tk.Frame(panel_ctrl, bg=temas.c(GRIS_FONDO))
        fila_tema.pack(fill="x", pady=(0, 14))
        tk.Label(fila_tema, text="Tema del sistema:", font=fuentes.f(10, "bold"),
                 bg=temas.c(GRIS_FONDO), width=20, anchor="w").pack(side="left")
        self.btn_tema_claro = tk.Button(fila_tema, text="☀ Claro", font=fuentes.f(10, "bold"),
                                         relief="solid", bd=1, padx=14, pady=5, cursor="hand2",
                                         command=lambda: self._cambiar_tema("claro"))
        self.btn_tema_claro.pack(side="left", padx=(0, 8))
        self.btn_tema_oscuro = tk.Button(fila_tema, text="🌙 Oscuro", font=fuentes.f(10, "bold"),
                                          relief="solid", bd=1, padx=14, pady=5, cursor="hand2",
                                          command=lambda: self._cambiar_tema("oscuro"))
        self.btn_tema_oscuro.pack(side="left")

        # --- Fuente ---
        fila_fuente = tk.Frame(panel_ctrl, bg=temas.c(GRIS_FONDO))
        fila_fuente.pack(fill="x", pady=(0, 14))
        tk.Label(fila_fuente, text="Fuente del sistema:", font=fuentes.f(10, "bold"),
                 bg=temas.c(GRIS_FONDO), width=20, anchor="w").pack(side="left")
        self.var_fuente = tk.StringVar(value=fuentes.familia_actual())
        combo = ttk.Combobox(fila_fuente, textvariable=self.var_fuente,
                              values=FAMILIAS_DE_FUENTE_DISPONIBLES,
                              state="readonly", font=fuentes.f(10), width=22)
        combo.pack(side="left")
        combo.bind("<<ComboboxSelected>>", lambda e: self._aplicar())

        # --- Tamaño (escala %) ---
        fila_tam = tk.Frame(panel_ctrl, bg=temas.c(GRIS_FONDO))
        fila_tam.pack(fill="x")
        tk.Label(fila_tam, text="Tamaño de letra:", font=fuentes.f(10, "bold"),
                 bg=temas.c(GRIS_FONDO), width=20, anchor="w").pack(side="left")

        tk.Button(fila_tam, text="－", font=fuentes.f(11, "bold"), width=3,
                  cursor="hand2", command=self._disminuir).pack(side="left")
        self.lbl_escala = tk.Label(fila_tam, text="100%", font=fuentes.f(11, "bold"),
                                    bg=temas.c(GRIS_FONDO), fg=temas.c(AZUL), width=6)
        self.lbl_escala.pack(side="left", padx=6)
        tk.Button(fila_tam, text="＋", font=fuentes.f(11, "bold"), width=3,
                  cursor="hand2", command=self._aumentar).pack(side="left")
        tk.Label(fila_tam, text="(100% = tamaño original de diseño)",
                 font=fuentes.f(8, "italic"), bg=temas.c(GRIS_FONDO), fg=temas.c(GRIS_TEXT)
                 ).pack(side="left", padx=(12, 0))

        # --- Vista previa en vivo ---
        tk.Label(cuerpo, text="Vista previa:", font=fuentes.f(10, "bold"),
                 bg=temas.c(BLANCO), fg=temas.c(NEGRO)).pack(anchor="w", pady=(20, 4))
        marco_preview = tk.Frame(cuerpo, bg=temas.c(BLANCO), highlightbackground=temas.c(GRIS_BORDE),
                                  highlightthickness=1, padx=16, pady=14)
        marco_preview.pack(fill="x")
        self.lbl_preview_titulo = tk.Label(marco_preview, text="Título de ejemplo",
                                            font=fuentes.f(16, "bold"), bg=temas.c(BLANCO), fg=temas.c(AZUL_OSC))
        self.lbl_preview_titulo.pack(anchor="w")
        self.lbl_preview_texto = tk.Label(
            marco_preview,
            text="Este es un texto de ejemplo para ver cómo se ve la letra "
                 "en las pantallas del sistema (Ventas, Productos, Reportes, etc.).",
            font=fuentes.f(10), bg=temas.c(BLANCO), fg=temas.c("#374151"), justify="left", wraplength=560)
        self.lbl_preview_texto.pack(anchor="w", pady=(6, 0))

        # --- Botones ---
        fila_botones = tk.Frame(cuerpo, bg=temas.c(BLANCO))
        fila_botones.pack(fill="x", pady=(20, 0))
        tk.Button(fila_botones, text="↺ Restablecer valores predeterminados",
                  font=fuentes.f(10, "bold"), bg=temas.c(BLANCO), fg=temas.c(ROJO),
                  relief="solid", bd=1, padx=14, pady=7, cursor="hand2",
                  command=self._restablecer).pack(side="left")

        self.lbl_estado = tk.Label(cuerpo, text="", font=fuentes.f(9, "italic"),
                                    bg=temas.c(BLANCO), fg=temas.c(VERDE))
        self.lbl_estado.pack(anchor="w", pady=(10, 0))

        self._refrescar_controles()

    # ── Acciones ───────────────────────────────────────────────
    def _cambiar_tema(self, modo):
        if modo == temas.modo_actual():
            return
        temas.aplicar_tema(modo)
        # Nota: temas.aplicar_tema() dispara el callback registrado en
        # main.py, que reconstruye esta misma pantalla (entre otras
        # cosas) para reflejar el tema nuevo — por eso no hace falta
        # tocar más widgets acá; este método probablemente ni termine
        # de ejecutarse sobre el widget viejo.

    def _aumentar(self):
        nueva = min(ESCALA_MAX, fuentes.escala_actual() + PASO_ESCALA)
        self._aplicar(escala=nueva)

    def _disminuir(self):
        nueva = max(ESCALA_MIN, fuentes.escala_actual() - PASO_ESCALA)
        self._aplicar(escala=nueva)

    def _aplicar(self, escala=None):
        familia = self.var_fuente.get()
        ok, msg = self._guardar_y_aplicar(familia, escala if escala is not None else fuentes.escala_actual())
        if ok:
            self._refrescar_controles()
            self.lbl_estado.config(text="✓ Apariencia actualizada en todo el sistema.", fg=temas.c(VERDE))
        else:
            self.lbl_estado.config(text=f"✗ {msg}", fg=temas.c(ROJO))

    def _guardar_y_aplicar(self, familia, escala):
        from models_configuracion import guardar_configuracion_apariencia
        ok, msg = guardar_configuracion_apariencia(familia, escala)
        if ok:
            fuentes.aplicar_configuracion(familia, escala, guardar=False)
        return ok, msg

    def _restablecer(self):
        if not messagebox.askyesno(
            "Restablecer apariencia",
            "¿Volver la fuente, el tamaño de letra y el tema a los valores "
            f"originales del sistema ({fuentes.FAMILIA_PREDETERMINADA}, 100%, Claro)?",
            parent=self,
        ):
            return
        # Importante: primero la fuente (no destruye widgets, solo
        # reconfigura los objetos Font en vivo) y recién AL FINAL el
        # tema, porque cambiar el tema reconstruye esta misma pantalla
        # (ver _al_cambiar_tema en main.py) — cualquier código nuestro
        # después de esa línea correría sobre widgets ya destruidos.
        fuentes.restablecer_configuracion()
        self.var_fuente.set(fuentes.familia_actual())
        self._refrescar_controles()
        self.lbl_estado.config(text="✓ Apariencia restablecida a los valores predeterminados.", fg=temas.c(VERDE))
        if temas.modo_actual() != temas.MODO_PREDETERMINADO:
            temas.aplicar_tema(temas.MODO_PREDETERMINADO)

    def _refrescar_controles(self):
        self.lbl_escala.config(text=f"{fuentes.escala_actual()}%")
        es_oscuro = temas.modo_actual() == "oscuro"
        self.btn_tema_claro.config(
            bg=temas.c(AZUL) if not es_oscuro else temas.c(BLANCO),
            fg=temas.c(BLANCO) if not es_oscuro else temas.c(NEGRO),
        )
        self.btn_tema_oscuro.config(
            bg=temas.c(AZUL) if es_oscuro else temas.c(BLANCO),
            fg=temas.c(BLANCO) if es_oscuro else temas.c(NEGRO),
        )
