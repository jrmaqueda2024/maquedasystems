"""
ventana_juegos.py
Módulo "Juegos y Entretenimiento": un mini arcade con 6 juegos clásicos
(Solitario, Buscaminas, Tetris, Snake, Pong y Pac-Man), con puntajes
guardados por usuario y un ranking general de todos los usuarios del
sistema. Pensado como una pausa recreativa dentro de MaquedaSystems.

Estructura del archivo:
  - PanelJuegos:  panel principal (lanzador con las 6 tarjetas + ranking)
  - PanelRanking: tabla de puntajes acumulados por usuario
  - _crear_encabezado_juego: barra superior reutilizable de cada juego
  - JuegoSnake, JuegoPong, JuegoBuscaminas, JuegoTetris, JuegoPacman,
    JuegoSolitario: un tk.Frame por juego, cada uno autocontenido.
"""
import random
import time
import tkinter as tk
from tkinter import ttk, messagebox

import models_juegos as mj

# ───────────────────────────── Paleta general ─────────────────────────
AZUL_RIBBON = "#1d5fd6"
BLANCO = "#ffffff"
GRIS_FONDO = "#f4f5f7"
GRIS_BORDE = "#e2e8f0"
GRIS_TEXTO = "#374151"
NEGRO_TABLERO = "#0f172a"
VERDE = "#16a34a"
ROJO = "#dc2626"
AMARILLO = "#f59e0b"

# Color de acento de cada juego (para las tarjetas del lanzador y el
# encabezado dentro de cada juego).
COLOR_JUEGO = {
    "solitario":  "#166534",
    "buscaminas": "#475569",
    "tetris":     "#7c3aed",
    "snake":      "#15803d",
    "pong":       "#0f172a",
    "pacman":     "#eab308",
}
ICONO_JUEGO = {
    "solitario": "🃏", "buscaminas": "💣", "tetris": "🧱",
    "snake": "🐍", "pong": "🏓", "pacman": "👻",
}
DESCRIPCION_JUEGO = {
    "solitario": "El clásico Klondike con cartas de verdad.",
    "buscaminas": "Descubrí el tablero sin pisar una mina.",
    "tetris": "Encajá las piezas y completá líneas.",
    "snake": "Comé manzanas sin chocar contra vos mismo.",
    "pong": "El ping-pong original, contra la máquina.",
    "pacman": "Comé todos los puntos escapando de los fantasmas.",
}


# ════════════════════════════════════════════════════════════════════
#  PANEL PRINCIPAL (lanzador)
# ════════════════════════════════════════════════════════════════════
class PanelJuegos(tk.Frame):
    def __init__(self, parent, usuario_actual):
        super().__init__(parent, bg=GRIS_FONDO)
        self.usuario_actual = usuario_actual or {}
        self._mostrar_lanzador()

    # ---------------------------------------------------------- utils --
    def _limpiar(self):
        for w in self.winfo_children():
            w.destroy()

    def _nombre_usuario(self) -> str:
        return (self.usuario_actual.get("nombre_completo")
                or self.usuario_actual.get("usuario") or "Invitado")

    def guardar_puntaje(self, juego: str, puntaje: int, detalle: str = ""):
        """Los juegos llaman a esto al finalizar la partida."""
        mj.registrar_puntaje(
            self.usuario_actual.get("id"), self._nombre_usuario(), juego, puntaje, detalle)

    # ------------------------------------------------------- lanzador --
    def _mostrar_lanzador(self):
        self._limpiar()

        encabezado = tk.Frame(self, bg=AZUL_RIBBON, height=54)
        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)
        tk.Label(encabezado, text="🎮 Juegos y Entretenimiento",
                 font=("Segoe UI", 15, "bold"), bg=AZUL_RIBBON, fg=BLANCO
                 ).pack(side="left", padx=20, pady=12)
        tk.Button(encabezado, text="🏆 Ver ranking de usuarios", font=("Segoe UI", 9, "bold"),
                  bg=BLANCO, fg=AZUL_RIBBON, relief="flat", cursor="hand2", padx=12,
                  command=self._mostrar_ranking).pack(side="right", padx=20)

        contenedor = tk.Frame(self, bg=GRIS_FONDO)
        contenedor.pack(fill="both", expand=True, padx=30, pady=24)

        tk.Label(contenedor, text=f"¡Hola, {self._nombre_usuario()}! Elegí un juego:",
                 font=("Segoe UI", 12, "bold"), bg=GRIS_FONDO, fg=GRIS_TEXTO
                 ).pack(anchor="w", pady=(0, 16))

        grilla = tk.Frame(contenedor, bg=GRIS_FONDO)
        grilla.pack(fill="both", expand=True)
        COLUMNAS = 3
        for c in range(COLUMNAS):
            grilla.grid_columnconfigure(c, weight=1, uniform="tarjeta")

        for i, (clave, etiqueta) in enumerate(mj.JUEGOS_DISPONIBLES):
            fila, columna = divmod(i, COLUMNAS)
            self._tarjeta_juego(grilla, clave, fila, columna)

    def _tarjeta_juego(self, parent, clave: str, fila: int, columna: int):
        color = COLOR_JUEGO[clave]
        mejor = mj.obtener_mejor_puntaje_usuario(self.usuario_actual.get("id"), clave)

        card = tk.Frame(parent, bg=BLANCO, relief="solid", bd=1,
                         highlightbackground=GRIS_BORDE, cursor="hand2")
        card.grid(row=fila, column=columna, sticky="nsew", padx=10, pady=10, ipady=6)

        franja = tk.Frame(card, bg=color, height=6)
        franja.pack(fill="x")

        tk.Label(card, text=ICONO_JUEGO[clave], font=("Segoe UI", 34), bg=BLANCO
                 ).pack(pady=(16, 4))
        tk.Label(card, text=mj.NOMBRES_JUEGOS[clave].split(" ", 1)[1], font=("Segoe UI", 13, "bold"),
                 bg=BLANCO, fg=GRIS_TEXTO).pack()
        tk.Label(card, text=DESCRIPCION_JUEGO[clave], font=("Segoe UI", 8), bg=BLANCO,
                 fg="#6b7280", wraplength=190, justify="center").pack(pady=(4, 10))
        tk.Label(card, text=f"🏅 Tu mejor puntaje: {mejor}", font=("Segoe UI", 8, "bold"),
                 bg=BLANCO, fg=color).pack(pady=(0, 12))

        def _abrir(event=None, c=clave):
            self._abrir_juego(c)

        for widget in (card, franja, *card.winfo_children()):
            widget.bind("<Button-1>", _abrir)
            if isinstance(widget, tk.Label):
                widget.configure(cursor="hand2")

    # --------------------------------------------------------- juegos --
    def _abrir_juego(self, clave: str):
        self._limpiar()
        clases = {
            "snake": JuegoSnake,
            "pong": JuegoPong,
            "buscaminas": JuegoBuscaminas,
            "tetris": JuegoTetris,
            "pacman": JuegoPacman,
            "solitario": JuegoSolitario,
        }
        clase = clases[clave]
        instancia = clase(self, on_volver=self._mostrar_lanzador,
                           on_fin_partida=lambda pts, det="": self.guardar_puntaje(clave, pts, det))
        instancia.pack(fill="both", expand=True)

    def _mostrar_ranking(self):
        self._limpiar()
        panel = PanelRanking(self, on_volver=self._mostrar_lanzador)
        panel.pack(fill="both", expand=True)


# ════════════════════════════════════════════════════════════════════
#  RANKING GENERAL DE USUARIOS
# ════════════════════════════════════════════════════════════════════
class PanelRanking(tk.Frame):
    def __init__(self, parent, on_volver):
        super().__init__(parent, bg=GRIS_FONDO)
        self.on_volver = on_volver
        self._construir_ui()

    def _construir_ui(self):
        encabezado = tk.Frame(self, bg=AZUL_RIBBON, height=54)
        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)
        tk.Button(encabezado, text="⬅ Volver", font=("Segoe UI", 9, "bold"),
                  bg=BLANCO, fg=AZUL_RIBBON, relief="flat", cursor="hand2", padx=12,
                  command=self.on_volver).pack(side="left", padx=20, pady=12)
        tk.Label(encabezado, text="🏆 Ranking de Usuarios", font=("Segoe UI", 15, "bold"),
                 bg=AZUL_RIBBON, fg=BLANCO).pack(side="left", padx=10)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=16)

        tab_general = tk.Frame(nb, bg=BLANCO)
        nb.add(tab_general, text="🏅 Ranking general")
        self._tabla_ranking_general(tab_general)

        for clave, etiqueta in mj.JUEGOS_DISPONIBLES:
            tab = tk.Frame(nb, bg=BLANCO)
            nb.add(tab, text=etiqueta)
            self._tabla_top_juego(tab, clave)

    def _tabla_ranking_general(self, parent):
        tk.Label(parent, text="Suma del mejor puntaje de cada usuario en cada juego que jugó.",
                 font=("Segoe UI", 9, "italic"), bg=BLANCO, fg="#6b7280"
                 ).pack(anchor="w", padx=14, pady=(10, 6))

        columnas = ("puesto", "usuario", "total") + tuple(c for c, _ in mj.JUEGOS_DISPONIBLES)
        etiquetas = {"puesto": "#", "usuario": "Usuario", "total": "Total"}
        etiquetas.update({c: e.split(" ", 1)[1] if " " in e else e for c, e in mj.JUEGOS_DISPONIBLES})

        tabla = ttk.Treeview(parent, columns=columnas, show="headings", height=14)
        for c in columnas:
            tabla.heading(c, text=etiquetas.get(c, c))
            tabla.column(c, width=90 if c != "usuario" else 180,
                         anchor="center" if c != "usuario" else "w")
        tabla.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        ranking = mj.obtener_ranking_usuarios()
        for i, registro in enumerate(ranking, start=1):
            fila = [i, registro["usuario"], registro["total"]]
            for clave, _ in mj.JUEGOS_DISPONIBLES:
                fila.append(registro["por_juego"].get(clave, "—"))
            etiqueta_medalla = ""
            if i == 1:
                etiqueta_medalla = "oro"
            elif i == 2:
                etiqueta_medalla = "plata"
            elif i == 3:
                etiqueta_medalla = "bronce"
            tabla.insert("", "end", values=fila, tags=(etiqueta_medalla,))
        tabla.tag_configure("oro", background="#fef9c3")
        tabla.tag_configure("plata", background="#f1f5f9")
        tabla.tag_configure("bronce", background="#fde7d0")

        if not ranking:
            tk.Label(parent, text="Todavía nadie registró un puntaje. ¡Jugá algo!",
                     font=("Segoe UI", 10, "italic"), bg=BLANCO, fg="#6b7280").pack(pady=20)

    def _tabla_top_juego(self, parent, clave: str):
        tabla = ttk.Treeview(parent, columns=("puesto", "usuario", "puntaje", "fecha"),
                              show="headings", height=14)
        tabla.heading("puesto", text="#")
        tabla.heading("usuario", text="Usuario")
        tabla.heading("puntaje", text="Mejor puntaje")
        tabla.heading("fecha", text="Fecha")
        tabla.column("puesto", width=50, anchor="center")
        tabla.column("usuario", width=200)
        tabla.column("puntaje", width=120, anchor="center")
        tabla.column("fecha", width=160, anchor="center")
        tabla.pack(fill="both", expand=True, padx=14, pady=14)

        top = mj.obtener_top_puntajes(clave, limite=20)
        for i, r in enumerate(top, start=1):
            tabla.insert("", "end", values=(i, r["usuario"], r["puntaje"], r["fecha"]))
        if not top:
            tk.Label(parent, text="Todavía no hay puntajes registrados en este juego.",
                     font=("Segoe UI", 10, "italic"), bg=BLANCO, fg="#6b7280").pack(pady=20)


# ════════════════════════════════════════════════════════════════════
#  Encabezado reutilizable dentro de cada juego
# ════════════════════════════════════════════════════════════════════
def _crear_encabezado_juego(parent, titulo: str, color: str, on_volver):
    """Crea la barra superior estándar de un juego: volver + título +
    devuelve un Frame vacío a la derecha donde el juego puede poner sus
    propias etiquetas (puntaje, nivel, vidas, etc.)."""
    encabezado = tk.Frame(parent, bg=color, height=54)
    encabezado.pack(fill="x")
    encabezado.pack_propagate(False)
    tk.Button(encabezado, text="⬅ Volver", font=("Segoe UI", 9, "bold"),
              bg=BLANCO, fg=color, relief="flat", cursor="hand2", padx=12,
              command=on_volver).pack(side="left", padx=16, pady=12)
    tk.Label(encabezado, text=titulo, font=("Segoe UI", 14, "bold"),
             bg=color, fg=BLANCO).pack(side="left", padx=10)
    marcador = tk.Frame(encabezado, bg=color)
    marcador.pack(side="right", padx=20)
    return marcador


# ════════════════════════════════════════════════════════════════════
#  SNAKE
# ════════════════════════════════════════════════════════════════════
class JuegoSnake(tk.Frame):
    TAM_CELDA = 22
    COLUMNAS = 20
    FILAS = 20

    def __init__(self, parent, on_volver, on_fin_partida):
        super().__init__(parent, bg=GRIS_FONDO)
        self.on_volver = on_volver
        self.on_fin_partida = on_fin_partida
        self.color = COLOR_JUEGO["snake"]
        self._job = None
        self._construir_ui()
        self._nueva_partida()

    def _construir_ui(self):
        marcador = _crear_encabezado_juego(self, "🐍 Snake", self.color, self._salir)
        self.lbl_puntaje = tk.Label(marcador, text="Puntaje: 0", font=("Segoe UI", 12, "bold"),
                                     bg=self.color, fg=BLANCO)
        self.lbl_puntaje.pack(side="left", padx=10)

        cuerpo = tk.Frame(self, bg=GRIS_FONDO)
        cuerpo.pack(fill="both", expand=True, padx=16, pady=16)

        ancho = self.COLUMNAS * self.TAM_CELDA
        alto = self.FILAS * self.TAM_CELDA
        self.canvas = tk.Canvas(cuerpo, width=ancho, height=alto, bg=NEGRO_TABLERO,
                                 highlightthickness=2, highlightbackground=self.color)
        self.canvas.pack(side="left")

        panel = tk.Frame(cuerpo, bg=GRIS_FONDO, padx=20)
        panel.pack(side="left", fill="y")
        tk.Label(panel, text="Controles", font=("Segoe UI", 11, "bold"), bg=GRIS_FONDO,
                 fg=GRIS_TEXTO).pack(anchor="w", pady=(0, 6))
        tk.Label(panel,
                 text="Flechas o W A S D para\nmoverte. Comé las manzanas 🍎\ny evitá chocar contra las\nparedes o contra vos mismo.",
                 font=("Segoe UI", 9), bg=GRIS_FONDO, fg="#6b7280", justify="left").pack(anchor="w")
        self.btn_pausa = tk.Button(panel, text="⏸ Pausar", font=("Segoe UI", 10, "bold"),
                                    bg=self.color, fg=BLANCO, relief="flat", cursor="hand2",
                                    command=self._alternar_pausa)
        self.btn_pausa.pack(anchor="w", pady=(16, 6), fill="x")
        tk.Button(panel, text="🔁 Nueva partida", font=("Segoe UI", 10, "bold"),
                  bg="#e2e8f0", fg=GRIS_TEXTO, relief="flat", cursor="hand2",
                  command=self._nueva_partida).pack(anchor="w", fill="x")

        self.bind("<KeyPress-Up>", lambda e: self._cambiar_direccion("Up"))
        self.bind("<KeyPress-Down>", lambda e: self._cambiar_direccion("Down"))
        self.bind("<KeyPress-Left>", lambda e: self._cambiar_direccion("Left"))
        self.bind("<KeyPress-Right>", lambda e: self._cambiar_direccion("Right"))
        self.bind("<KeyPress-w>", lambda e: self._cambiar_direccion("Up"))
        self.bind("<KeyPress-s>", lambda e: self._cambiar_direccion("Down"))
        self.bind("<KeyPress-a>", lambda e: self._cambiar_direccion("Left"))
        self.bind("<KeyPress-d>", lambda e: self._cambiar_direccion("Right"))
        self.bind("<KeyPress-space>", lambda e: self._alternar_pausa())
        self.focus_set()

    def destroy(self):
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
        super().destroy()

    def _salir(self):
        self.on_volver()

    def _nueva_partida(self):
        if self._job:
            self.after_cancel(self._job)
        self.puntaje = 0
        self.velocidad_ms = 140
        self.direccion = "Right"
        self.direccion_pendiente = "Right"
        self.terminado = False
        self.pausado = False
        self.btn_pausa.config(text="⏸ Pausar")
        centro_x, centro_y = self.COLUMNAS // 2, self.FILAS // 2
        self.serpiente = [(centro_x - 1, centro_y), (centro_x - 2, centro_y), (centro_x - 3, centro_y)]
        self._colocar_manzana()
        self.lbl_puntaje.config(text="Puntaje: 0")
        self._dibujar()
        self._job = self.after(self.velocidad_ms, self._tick)

    def _colocar_manzana(self):
        libres = [(x, y) for x in range(self.COLUMNAS) for y in range(self.FILAS)
                  if (x, y) not in self.serpiente]
        self.manzana = random.choice(libres)

    def _cambiar_direccion(self, nueva):
        opuestos = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}
        if opuestos.get(nueva) != self.direccion:
            self.direccion_pendiente = nueva

    def _alternar_pausa(self):
        if self.terminado:
            return
        self.pausado = not self.pausado
        self.btn_pausa.config(text="▶ Continuar" if self.pausado else "⏸ Pausar")

    def _tick(self):
        if self.terminado:
            return
        if not self.pausado:
            self._mover()
        if not self.terminado:
            self._job = self.after(self.velocidad_ms, self._tick)

    def _mover(self):
        self.direccion = self.direccion_pendiente
        cabeza_x, cabeza_y = self.serpiente[0]
        dx, dy = {"Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0)}[self.direccion]
        nueva_cabeza = (cabeza_x + dx, cabeza_y + dy)

        choco_pared = not (0 <= nueva_cabeza[0] < self.COLUMNAS and 0 <= nueva_cabeza[1] < self.FILAS)
        if choco_pared or nueva_cabeza in self.serpiente:
            self._fin_partida()
            return

        self.serpiente.insert(0, nueva_cabeza)
        if nueva_cabeza == self.manzana:
            self.puntaje += 10
            self.lbl_puntaje.config(text=f"Puntaje: {self.puntaje}")
            self.velocidad_ms = max(60, self.velocidad_ms - 3)
            self._colocar_manzana()
        else:
            self.serpiente.pop()

        self._dibujar()

    def _dibujar(self):
        c = self.canvas
        c.delete("all")
        t = self.TAM_CELDA
        for x in range(0, self.COLUMNAS * t, t):
            c.create_line(x, 0, x, self.FILAS * t, fill="#1e293b")
        for y in range(0, self.FILAS * t, t):
            c.create_line(0, y, self.COLUMNAS * t, y, fill="#1e293b")

        mx, my = self.manzana
        c.create_oval(mx * t + 3, my * t + 3, mx * t + t - 3, my * t + t - 3,
                      fill="#ef4444", outline="#991b1b", width=2)

        for i, (x, y) in enumerate(self.serpiente):
            color = "#4ade80" if i == 0 else "#22c55e"
            c.create_rectangle(x * t + 1, y * t + 1, x * t + t - 1, y * t + t - 1,
                                fill=color, outline="#166534", width=1)

        if self.terminado:
            c.create_rectangle(0, 0, self.COLUMNAS * t, self.FILAS * t, fill="#000000", stipple="gray50")
            c.create_text(self.COLUMNAS * t // 2, self.FILAS * t // 2,
                          text="GAME OVER", font=("Segoe UI", 22, "bold"), fill="white")

    def _fin_partida(self):
        self.terminado = True
        self._dibujar()
        self.on_fin_partida(self.puntaje, f"largo {len(self.serpiente)}")
        messagebox.showinfo("Snake", f"¡Juego terminado!\nPuntaje: {self.puntaje}", parent=self)


# ════════════════════════════════════════════════════════════════════
#  PONG
# ════════════════════════════════════════════════════════════════════
class JuegoPong(tk.Frame):
    ANCHO = 600
    ALTO = 400
    ALTO_PALA = 70
    ANCHO_PALA = 10
    RADIO_BOLA = 8
    PUNTOS_PARA_GANAR = 5

    def __init__(self, parent, on_volver, on_fin_partida):
        super().__init__(parent, bg=GRIS_FONDO)
        self.on_volver = on_volver
        self.on_fin_partida = on_fin_partida
        self.color = COLOR_JUEGO["pong"]
        self._job = None
        self._construir_ui()
        self._nueva_partida()

    def _construir_ui(self):
        marcador = _crear_encabezado_juego(self, "🏓 Pong", self.color, self._salir)
        self.lbl_marcador = tk.Label(marcador, text="Vos 0 — 0 Máquina", font=("Segoe UI", 12, "bold"),
                                      bg=self.color, fg=BLANCO)
        self.lbl_marcador.pack(side="left", padx=10)

        cuerpo = tk.Frame(self, bg=GRIS_FONDO)
        cuerpo.pack(fill="both", expand=True, padx=16, pady=16)
        self.canvas = tk.Canvas(cuerpo, width=self.ANCHO, height=self.ALTO, bg=NEGRO_TABLERO,
                                 highlightthickness=2, highlightbackground=self.color)
        self.canvas.pack(side="left")

        panel = tk.Frame(cuerpo, bg=GRIS_FONDO, padx=20)
        panel.pack(side="left", fill="y")
        tk.Label(panel, text="Controles", font=("Segoe UI", 11, "bold"), bg=GRIS_FONDO,
                 fg=GRIS_TEXTO).pack(anchor="w", pady=(0, 6))
        tk.Label(panel, text="Flechas ↑ ↓ o W/S para\nmover tu paleta celeste.\nGana quien llegue a 5 puntos.",
                 font=("Segoe UI", 9), bg=GRIS_FONDO, fg="#6b7280", justify="left").pack(anchor="w")
        tk.Button(panel, text="🔁 Nueva partida", font=("Segoe UI", 10, "bold"),
                  bg=self.color, fg=BLANCO, relief="flat", cursor="hand2",
                  command=self._nueva_partida).pack(anchor="w", pady=(16, 6), fill="x")

        self.bind("<KeyPress-Up>", lambda e: self._mover_jugador(-1))
        self.bind("<KeyPress-Down>", lambda e: self._mover_jugador(1))
        self.bind("<KeyPress-w>", lambda e: self._mover_jugador(-1))
        self.bind("<KeyPress-s>", lambda e: self._mover_jugador(1))
        self.focus_set()

    def destroy(self):
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
        super().destroy()

    def _salir(self):
        self.on_volver()

    def _nueva_partida(self):
        if self._job:
            self.after_cancel(self._job)
        self.puntaje_jugador = 0
        self.puntaje_maquina = 0
        self.y_jugador = self.ALTO / 2 - self.ALTO_PALA / 2
        self.y_maquina = self.ALTO / 2 - self.ALTO_PALA / 2
        self.terminado = False
        self._resetear_bola()
        self._actualizar_marcador()
        self._loop()

    def _resetear_bola(self):
        self.bola_x = self.ANCHO / 2
        self.bola_y = self.ALTO / 2
        self.bola_vx = random.choice([-4.0, 4.0])
        self.bola_vy = random.uniform(-3.0, 3.0)

    def _mover_jugador(self, delta):
        paso = 26
        self.y_jugador = max(0, min(self.ALTO - self.ALTO_PALA, self.y_jugador + delta * paso))

    def _loop(self):
        if self.terminado:
            return
        self._actualizar_fisica()
        self._dibujar()
        if not self.terminado:
            self._job = self.after(16, self._loop)

    def _actualizar_fisica(self):
        self.bola_x += self.bola_vx
        self.bola_y += self.bola_vy

        if self.bola_y - self.RADIO_BOLA <= 0 or self.bola_y + self.RADIO_BOLA >= self.ALTO:
            self.bola_vy *= -1

        centro_maquina = self.y_maquina + self.ALTO_PALA / 2
        if self.bola_y > centro_maquina + 8:
            self.y_maquina = min(self.ALTO - self.ALTO_PALA, self.y_maquina + 3.4)
        elif self.bola_y < centro_maquina - 8:
            self.y_maquina = max(0, self.y_maquina - 3.4)

        if (self.bola_x - self.RADIO_BOLA <= 20 + self.ANCHO_PALA
                and self.y_jugador <= self.bola_y <= self.y_jugador + self.ALTO_PALA
                and self.bola_vx < 0):
            self.bola_vx = abs(self.bola_vx) * 1.05
            self.bola_vy += random.uniform(-1.5, 1.5)

        if (self.bola_x + self.RADIO_BOLA >= self.ANCHO - 20 - self.ANCHO_PALA
                and self.y_maquina <= self.bola_y <= self.y_maquina + self.ALTO_PALA
                and self.bola_vx > 0):
            self.bola_vx = -abs(self.bola_vx) * 1.05
            self.bola_vy += random.uniform(-1.5, 1.5)

        if self.bola_x < 0:
            self.puntaje_maquina += 1
            self._actualizar_marcador()
            self._resetear_bola()
        elif self.bola_x > self.ANCHO:
            self.puntaje_jugador += 1
            self._actualizar_marcador()
            self._resetear_bola()

        if self.puntaje_jugador >= self.PUNTOS_PARA_GANAR or self.puntaje_maquina >= self.PUNTOS_PARA_GANAR:
            self._fin_partida()

    def _actualizar_marcador(self):
        self.lbl_marcador.config(text=f"Vos {self.puntaje_jugador} — {self.puntaje_maquina} Máquina")

    def _dibujar(self):
        c = self.canvas
        c.delete("all")
        for y in range(0, self.ALTO, 20):
            c.create_line(self.ANCHO / 2, y, self.ANCHO / 2, y + 10, fill="#334155")
        c.create_rectangle(20, self.y_jugador, 20 + self.ANCHO_PALA, self.y_jugador + self.ALTO_PALA,
                            fill="#38bdf8", outline="")
        c.create_rectangle(self.ANCHO - 20 - self.ANCHO_PALA, self.y_maquina,
                            self.ANCHO - 20, self.y_maquina + self.ALTO_PALA,
                            fill="#f87171", outline="")
        c.create_oval(self.bola_x - self.RADIO_BOLA, self.bola_y - self.RADIO_BOLA,
                      self.bola_x + self.RADIO_BOLA, self.bola_y + self.RADIO_BOLA,
                      fill="#facc15", outline="")

    def _fin_partida(self):
        self.terminado = True
        gano = self.puntaje_jugador > self.puntaje_maquina
        puntaje_final = max(0, self.puntaje_jugador * 100 - self.puntaje_maquina * 20
                             + (200 if gano else 0))
        self.on_fin_partida(puntaje_final, f"{self.puntaje_jugador}-{self.puntaje_maquina}")
        mensaje = "¡Ganaste! 🎉" if gano else "Ganó la máquina."
        messagebox.showinfo("Pong", f"{mensaje}\nPuntaje final: {puntaje_final}", parent=self)


# ════════════════════════════════════════════════════════════════════
#  BUSCAMINAS
# ════════════════════════════════════════════════════════════════════
class JuegoBuscaminas(tk.Frame):
    TAM_CELDA = 26
    DIFICULTADES = {
        "Fácil (9x9, 10 minas)": (9, 9, 10),
        "Medio (14x14, 30 minas)": (14, 14, 30),
        "Difícil (18x14, 50 minas)": (18, 14, 50),
    }

    def __init__(self, parent, on_volver, on_fin_partida):
        super().__init__(parent, bg=GRIS_FONDO)
        self.on_volver = on_volver
        self.on_fin_partida = on_fin_partida
        self.color = COLOR_JUEGO["buscaminas"]
        self._job_reloj = None
        self._construir_ui()
        self._nueva_partida()

    def _construir_ui(self):
        marcador = _crear_encabezado_juego(self, "💣 Buscaminas", self.color, self._salir)
        self.lbl_minas = tk.Label(marcador, text="💣 0", font=("Segoe UI", 12, "bold"),
                                   bg=self.color, fg=BLANCO)
        self.lbl_minas.pack(side="left", padx=10)
        self.lbl_tiempo = tk.Label(marcador, text="⏱ 0s", font=("Segoe UI", 12, "bold"),
                                    bg=self.color, fg=BLANCO)
        self.lbl_tiempo.pack(side="left", padx=10)

        barra = tk.Frame(self, bg=GRIS_FONDO)
        barra.pack(fill="x", padx=16, pady=(12, 0))
        tk.Label(barra, text="Dificultad:", font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO,
                 fg=GRIS_TEXTO).pack(side="left")
        self.var_dificultad = tk.StringVar(value=list(self.DIFICULTADES.keys())[0])
        combo = ttk.Combobox(barra, textvariable=self.var_dificultad, state="readonly",
                              values=list(self.DIFICULTADES.keys()), width=26, font=("Segoe UI", 9))
        combo.pack(side="left", padx=8)
        combo.bind("<<ComboboxSelected>>", lambda e: self._nueva_partida())
        tk.Button(barra, text="🙂 Nueva partida", font=("Segoe UI", 9, "bold"), bg=self.color,
                  fg=BLANCO, relief="flat", cursor="hand2", command=self._nueva_partida
                  ).pack(side="left", padx=10)
        tk.Label(barra, text="Click izquierdo: descubrir  ·  Click derecho: bandera 🚩",
                 font=("Segoe UI", 8, "italic"), bg=GRIS_FONDO, fg="#6b7280").pack(side="left", padx=16)

        marco_canvas = tk.Frame(self, bg=GRIS_FONDO)
        marco_canvas.pack(fill="both", expand=True, padx=16, pady=16)
        self.canvas = tk.Canvas(marco_canvas, bg="#94a3b8", highlightthickness=2,
                                 highlightbackground=self.color)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._clic_izquierdo)
        self.canvas.bind("<Button-3>", self._clic_derecho)

    def destroy(self):
        if self._job_reloj:
            try:
                self.after_cancel(self._job_reloj)
            except Exception:
                pass
        super().destroy()

    def _salir(self):
        self.on_volver()

    def _nueva_partida(self):
        if self._job_reloj:
            self.after_cancel(self._job_reloj)
        self.columnas, self.filas, self.total_minas = self.DIFICULTADES[self.var_dificultad.get()]
        self.canvas.config(width=self.columnas * self.TAM_CELDA, height=self.filas * self.TAM_CELDA)
        self.tablero = [[{"mina": False, "revelada": False, "bandera": False, "adyacentes": 0}
                          for _ in range(self.columnas)] for _ in range(self.filas)]
        self.minas_colocadas = False
        self.terminado = False
        self.celdas_reveladas = 0
        self.banderas = 0
        self.tiempo_transcurrido = 0
        self.lbl_minas.config(text=f"💣 {self.total_minas}")
        self.lbl_tiempo.config(text="⏱ 0s")
        self._dibujar()
        self._tick_reloj()

    def _tick_reloj(self):
        if not self.terminado:
            self.tiempo_transcurrido += 1
            self.lbl_tiempo.config(text=f"⏱ {self.tiempo_transcurrido}s")
            self._job_reloj = self.after(1000, self._tick_reloj)

    def _colocar_minas(self, evitar_x, evitar_y):
        posiciones = [(x, y) for y in range(self.filas) for x in range(self.columnas)
                      if abs(x - evitar_x) > 1 or abs(y - evitar_y) > 1]
        for x, y in random.sample(posiciones, min(self.total_minas, len(posiciones))):
            self.tablero[y][x]["mina"] = True
        for y in range(self.filas):
            for x in range(self.columnas):
                if not self.tablero[y][x]["mina"]:
                    self.tablero[y][x]["adyacentes"] = self._contar_minas_vecinas(x, y)
        self.minas_colocadas = True

    def _contar_minas_vecinas(self, x, y):
        total = 0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.columnas and 0 <= ny < self.filas and self.tablero[ny][nx]["mina"]:
                    total += 1
        return total

    def _celda_en(self, event):
        x = event.x // self.TAM_CELDA
        y = event.y // self.TAM_CELDA
        if 0 <= x < self.columnas and 0 <= y < self.filas:
            return x, y
        return None

    def _clic_izquierdo(self, event):
        if self.terminado:
            return
        pos = self._celda_en(event)
        if not pos:
            return
        x, y = pos
        if self.tablero[y][x]["bandera"]:
            return
        if not self.minas_colocadas:
            self._colocar_minas(x, y)
        self._revelar(x, y)
        self._dibujar()
        self._revisar_estado()

    def _clic_derecho(self, event):
        if self.terminado:
            return
        pos = self._celda_en(event)
        if not pos:
            return
        x, y = pos
        celda = self.tablero[y][x]
        if celda["revelada"]:
            return
        celda["bandera"] = not celda["bandera"]
        self.banderas += 1 if celda["bandera"] else -1
        self.lbl_minas.config(text=f"💣 {self.total_minas - self.banderas}")
        self._dibujar()

    def _revelar(self, x, y):
        celda = self.tablero[y][x]
        if celda["revelada"] or celda["bandera"]:
            return
        celda["revelada"] = True
        self.celdas_reveladas += 1
        if celda["mina"]:
            self._perder()
            return
        if celda["adyacentes"] == 0:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.columnas and 0 <= ny < self.filas:
                        if not self.tablero[ny][nx]["revelada"]:
                            self._revelar(nx, ny)

    def _revisar_estado(self):
        total_celdas = self.columnas * self.filas
        if not self.terminado and self.celdas_reveladas >= total_celdas - self.total_minas:
            self._ganar()

    def _perder(self):
        self.terminado = True
        for fila in self.tablero:
            for celda in fila:
                if celda["mina"]:
                    celda["revelada"] = True
        self._dibujar()
        puntaje = self.celdas_reveladas * 2
        self.on_fin_partida(puntaje, f"perdió en {self.tiempo_transcurrido}s")
        messagebox.showinfo("Buscaminas", f"💥 ¡Pisaste una mina!\nPuntaje: {puntaje}", parent=self)

    def _ganar(self):
        self.terminado = True
        multiplicador = {81: 1, 196: 2, 252: 3}.get(self.columnas * self.filas, 2)
        puntaje = max(100, multiplicador * 1000 - self.tiempo_transcurrido * 5)
        self.on_fin_partida(puntaje, f"ganó en {self.tiempo_transcurrido}s")
        messagebox.showinfo("Buscaminas",
                             f"🎉 ¡Ganaste!\nTiempo: {self.tiempo_transcurrido}s\nPuntaje: {puntaje}",
                             parent=self)

    def _dibujar(self):
        c = self.canvas
        c.delete("all")
        t = self.TAM_CELDA
        colores_numeros = {1: "#2563eb", 2: "#16a34a", 3: "#dc2626", 4: "#7c3aed",
                            5: "#92400e", 6: "#0891b2", 7: "#111827", 8: "#6b7280"}
        for y in range(self.filas):
            for x in range(self.columnas):
                celda = self.tablero[y][x]
                x0, y0 = x * t, y * t
                x1, y1 = x0 + t, y0 + t
                if celda["revelada"]:
                    color_fondo = "#fecaca" if celda["mina"] else "#e2e8f0"
                    c.create_rectangle(x0, y0, x1, y1, fill=color_fondo, outline="#cbd5e1")
                    if celda["mina"]:
                        c.create_text((x0 + x1) / 2, (y0 + y1) / 2, text="💣", font=("Segoe UI", 12))
                    elif celda["adyacentes"] > 0:
                        c.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=str(celda["adyacentes"]),
                                      font=("Segoe UI", 11, "bold"),
                                      fill=colores_numeros.get(celda["adyacentes"], "#111827"))
                else:
                    c.create_rectangle(x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill="#94a3b8", outline="#64748b")
                    c.create_line(x0 + 1, y0 + 1, x1 - 1, y0 + 1, fill="#cbd5e1")
                    c.create_line(x0 + 1, y0 + 1, x0 + 1, y1 - 1, fill="#cbd5e1")
                    if celda["bandera"]:
                        c.create_text((x0 + x1) / 2, (y0 + y1) / 2, text="🚩", font=("Segoe UI", 12))


# ════════════════════════════════════════════════════════════════════
#  TETRIS
# ════════════════════════════════════════════════════════════════════
class JuegoTetris(tk.Frame):
    COLUMNAS = 10
    FILAS = 20
    TAM_CELDA = 24

    PIEZAS = {
        "I": {"color": "#22d3ee", "celdas": [(0, 1), (1, 1), (2, 1), (3, 1)], "n": 4},
        "O": {"color": "#facc15", "celdas": [(0, 0), (1, 0), (0, 1), (1, 1)], "n": 2},
        "T": {"color": "#a855f7", "celdas": [(0, 1), (1, 1), (2, 1), (1, 0)], "n": 3},
        "S": {"color": "#22c55e", "celdas": [(1, 0), (2, 0), (0, 1), (1, 1)], "n": 3},
        "Z": {"color": "#ef4444", "celdas": [(0, 0), (1, 0), (1, 1), (2, 1)], "n": 3},
        "J": {"color": "#3b82f6", "celdas": [(0, 0), (0, 1), (1, 1), (2, 1)], "n": 3},
        "L": {"color": "#f97316", "celdas": [(2, 0), (0, 1), (1, 1), (2, 1)], "n": 3},
    }

    def __init__(self, parent, on_volver, on_fin_partida):
        super().__init__(parent, bg=GRIS_FONDO)
        self.on_volver = on_volver
        self.on_fin_partida = on_fin_partida
        self.color = COLOR_JUEGO["tetris"]
        self._job = None
        self._construir_ui()
        self._nueva_partida()

    def _construir_ui(self):
        marcador = _crear_encabezado_juego(self, "🧱 Tetris", self.color, self._salir)
        self.lbl_puntaje = tk.Label(marcador, text="Puntaje: 0", font=("Segoe UI", 12, "bold"),
                                     bg=self.color, fg=BLANCO)
        self.lbl_puntaje.pack(side="left", padx=10)
        self.lbl_nivel = tk.Label(marcador, text="Nivel: 1", font=("Segoe UI", 12, "bold"),
                                   bg=self.color, fg=BLANCO)
        self.lbl_nivel.pack(side="left", padx=10)

        cuerpo = tk.Frame(self, bg=GRIS_FONDO)
        cuerpo.pack(fill="both", expand=True, padx=16, pady=16)
        ancho = self.COLUMNAS * self.TAM_CELDA
        alto = self.FILAS * self.TAM_CELDA
        self.canvas = tk.Canvas(cuerpo, width=ancho, height=alto, bg=NEGRO_TABLERO,
                                 highlightthickness=2, highlightbackground=self.color)
        self.canvas.pack(side="left")

        panel = tk.Frame(cuerpo, bg=GRIS_FONDO, padx=20)
        panel.pack(side="left", fill="y")
        tk.Label(panel, text="Siguiente pieza", font=("Segoe UI", 11, "bold"), bg=GRIS_FONDO,
                 fg=GRIS_TEXTO).pack(anchor="w")
        self.canvas_siguiente = tk.Canvas(panel, width=110, height=90, bg=NEGRO_TABLERO,
                                           highlightthickness=1, highlightbackground=GRIS_BORDE)
        self.canvas_siguiente.pack(anchor="w", pady=(4, 16))
        tk.Label(panel, text="Controles", font=("Segoe UI", 11, "bold"), bg=GRIS_FONDO,
                 fg=GRIS_TEXTO).pack(anchor="w")
        tk.Label(panel, text="← → mover · ↓ bajar\n↑ rotar · Espacio caída rápida",
                 font=("Segoe UI", 9), bg=GRIS_FONDO, fg="#6b7280", justify="left").pack(anchor="w")
        tk.Button(panel, text="🔁 Nueva partida", font=("Segoe UI", 10, "bold"),
                  bg=self.color, fg=BLANCO, relief="flat", cursor="hand2",
                  command=self._nueva_partida).pack(anchor="w", pady=(16, 6), fill="x")

        self.bind("<KeyPress-Left>", lambda e: self._mover(-1, 0))
        self.bind("<KeyPress-Right>", lambda e: self._mover(1, 0))
        self.bind("<KeyPress-Down>", lambda e: self._mover(0, 1, es_soft_drop=True))
        self.bind("<KeyPress-Up>", lambda e: self._rotar())
        self.bind("<KeyPress-space>", lambda e: self._caida_rapida())
        self.focus_set()

    def destroy(self):
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
        super().destroy()

    def _salir(self):
        self.on_volver()

    def _nueva_partida(self):
        if self._job:
            self.after_cancel(self._job)
        self.grilla = [[None for _ in range(self.COLUMNAS)] for _ in range(self.FILAS)]
        self.puntaje = 0
        self.lineas_totales = 0
        self.nivel = 1
        self.terminado = False
        self.tipo_siguiente = random.choice(list(self.PIEZAS.keys()))
        self._generar_pieza()
        self._actualizar_labels()
        self._dibujar()
        self._tick()

    def _generar_pieza(self):
        self.tipo_actual = self.tipo_siguiente
        self.tipo_siguiente = random.choice(list(self.PIEZAS.keys()))
        info = self.PIEZAS[self.tipo_actual]
        self.celdas_actual = list(info["celdas"])
        self.n_actual = info["n"]
        self.color_actual = info["color"]
        self.px = self.COLUMNAS // 2 - self.n_actual // 2
        self.py = 0
        if self._colisiona(self.celdas_actual, self.px, self.py):
            self._fin_partida()
        self._dibujar_siguiente()

    def _colisiona(self, celdas, px, py):
        for cx, cy in celdas:
            x, y = px + cx, py + cy
            if x < 0 or x >= self.COLUMNAS or y >= self.FILAS:
                return True
            if y >= 0 and self.grilla[y][x] is not None:
                return True
        return False

    def _mover(self, dx, dy, es_soft_drop=False):
        if self.terminado:
            return
        if not self._colisiona(self.celdas_actual, self.px + dx, self.py + dy):
            self.px += dx
            self.py += dy
            if es_soft_drop:
                self.puntaje += 1
                self._actualizar_labels()
            self._dibujar()
        elif dy > 0:
            self._fijar_pieza()

    def _rotar(self):
        if self.terminado or self.tipo_actual == "O":
            return
        n = self.n_actual
        nuevas = [(n - 1 - cy, cx) for cx, cy in self.celdas_actual]
        for dx in (0, -1, 1, -2, 2):
            if not self._colisiona(nuevas, self.px + dx, self.py):
                self.celdas_actual = nuevas
                self.px += dx
                self._dibujar()
                return

    def _caida_rapida(self):
        if self.terminado:
            return
        distancia = 0
        while not self._colisiona(self.celdas_actual, self.px, self.py + 1):
            self.py += 1
            distancia += 1
        self.puntaje += distancia * 2
        self._actualizar_labels()
        self._fijar_pieza()

    def _fijar_pieza(self):
        for cx, cy in self.celdas_actual:
            x, y = self.px + cx, self.py + cy
            if 0 <= y < self.FILAS and 0 <= x < self.COLUMNAS:
                self.grilla[y][x] = self.color_actual
        self._limpiar_lineas()
        if not self.terminado:
            self._generar_pieza()
        self._dibujar()

    def _limpiar_lineas(self):
        filas_completas = [y for y in range(self.FILAS) if all(c is not None for c in self.grilla[y])]
        if not filas_completas:
            return
        for y in filas_completas:
            del self.grilla[y]
            self.grilla.insert(0, [None] * self.COLUMNAS)
        cantidad = len(filas_completas)
        puntos_por_lineas = {1: 100, 2: 300, 3: 500, 4: 800}
        self.puntaje += puntos_por_lineas.get(cantidad, 800) * self.nivel
        self.lineas_totales += cantidad
        self.nivel = self.lineas_totales // 10 + 1
        self._actualizar_labels()

    def _actualizar_labels(self):
        self.lbl_puntaje.config(text=f"Puntaje: {self.puntaje}")
        self.lbl_nivel.config(text=f"Nivel: {self.nivel}")

    def _tick(self):
        if self.terminado:
            return
        self._mover(0, 1)
        if not self.terminado:
            intervalo = max(100, 500 - (self.nivel - 1) * 40)
            self._job = self.after(intervalo, self._tick)

    def _dibujar(self):
        c = self.canvas
        c.delete("all")
        t = self.TAM_CELDA
        for y in range(self.FILAS):
            for x in range(self.COLUMNAS):
                color = self.grilla[y][x]
                if color:
                    c.create_rectangle(x * t, y * t, x * t + t, y * t + t, fill=color, outline="#0f172a")
        for cx, cy in self.celdas_actual:
            x, y = self.px + cx, self.py + cy
            if y >= 0:
                c.create_rectangle(x * t, y * t, x * t + t, y * t + t,
                                    fill=self.color_actual, outline="#0f172a")
        for x in range(0, self.COLUMNAS * t, t):
            c.create_line(x, 0, x, self.FILAS * t, fill="#1e293b")
        for y in range(0, self.FILAS * t, t):
            c.create_line(0, y, self.COLUMNAS * t, y, fill="#1e293b")

        if self.terminado:
            c.create_rectangle(0, 0, self.COLUMNAS * t, self.FILAS * t, fill="#000000", stipple="gray50")
            c.create_text(self.COLUMNAS * t // 2, self.FILAS * t // 2,
                          text="GAME OVER", font=("Segoe UI", 18, "bold"), fill="white")

    def _dibujar_siguiente(self):
        c = self.canvas_siguiente
        c.delete("all")
        info = self.PIEZAS[self.tipo_siguiente]
        t = 20
        for cx, cy in info["celdas"]:
            c.create_rectangle(10 + cx * t, 10 + cy * t, 10 + cx * t + t, 10 + cy * t + t,
                                fill=info["color"], outline="#0f172a")

    def _fin_partida(self):
        self.terminado = True
        self._dibujar()
        self.on_fin_partida(self.puntaje, f"nivel {self.nivel}, {self.lineas_totales} líneas")
        messagebox.showinfo("Tetris", f"¡Juego terminado!\nPuntaje: {self.puntaje}\nNivel: {self.nivel}",
                             parent=self)


# ════════════════════════════════════════════════════════════════════
#  PAC-MAN (versión simplificada)
# ════════════════════════════════════════════════════════════════════
class JuegoPacman(tk.Frame):
    TAM_CELDA = 24
    COLUMNAS = 21
    FILAS = 17
    INTERVALO_MS = 160
    DURACION_ASUSTADO = 38

    def __init__(self, parent, on_volver, on_fin_partida):
        super().__init__(parent, bg=GRIS_FONDO)
        self.on_volver = on_volver
        self.on_fin_partida = on_fin_partida
        self.color = COLOR_JUEGO["pacman"]
        self._job = None
        self._construir_ui()
        self._nueva_partida()

    def _construir_ui(self):
        marcador = _crear_encabezado_juego(self, "👻 Pac-Man", self.color, self._salir)
        self.lbl_puntaje = tk.Label(marcador, text="Puntaje: 0", font=("Segoe UI", 12, "bold"),
                                     bg=self.color, fg="#111827")
        self.lbl_puntaje.pack(side="left", padx=10)
        self.lbl_vidas = tk.Label(marcador, text="Vidas: ❤❤❤", font=("Segoe UI", 12, "bold"),
                                   bg=self.color, fg="#111827")
        self.lbl_vidas.pack(side="left", padx=10)

        cuerpo = tk.Frame(self, bg=GRIS_FONDO)
        cuerpo.pack(fill="both", expand=True, padx=16, pady=16)
        ancho = self.COLUMNAS * self.TAM_CELDA
        alto = self.FILAS * self.TAM_CELDA
        self.canvas = tk.Canvas(cuerpo, width=ancho, height=alto, bg=NEGRO_TABLERO,
                                 highlightthickness=2, highlightbackground=self.color)
        self.canvas.pack(side="left")

        panel = tk.Frame(cuerpo, bg=GRIS_FONDO, padx=20)
        panel.pack(side="left", fill="y")
        tk.Label(panel, text="Controles", font=("Segoe UI", 11, "bold"), bg=GRIS_FONDO,
                 fg=GRIS_TEXTO).pack(anchor="w")
        tk.Label(panel,
                 text="Flechas para moverte.\nComé todos los puntos\nevitando a los fantasmas.\n"
                      "Las bolitas grandes 🟡 te dejan\ncomer fantasmas por un rato.",
                 font=("Segoe UI", 9), bg=GRIS_FONDO, fg="#6b7280", justify="left").pack(anchor="w")
        tk.Button(panel, text="🔁 Nueva partida", font=("Segoe UI", 10, "bold"),
                  bg=self.color, fg="#111827", relief="flat", cursor="hand2",
                  command=self._nueva_partida).pack(anchor="w", pady=(16, 6), fill="x")

        self.bind("<KeyPress-Up>", lambda e: self._cambiar_direccion("Up"))
        self.bind("<KeyPress-Down>", lambda e: self._cambiar_direccion("Down"))
        self.bind("<KeyPress-Left>", lambda e: self._cambiar_direccion("Left"))
        self.bind("<KeyPress-Right>", lambda e: self._cambiar_direccion("Right"))
        self.bind("<KeyPress-w>", lambda e: self._cambiar_direccion("Up"))
        self.bind("<KeyPress-s>", lambda e: self._cambiar_direccion("Down"))
        self.bind("<KeyPress-a>", lambda e: self._cambiar_direccion("Left"))
        self.bind("<KeyPress-d>", lambda e: self._cambiar_direccion("Right"))
        self.focus_set()

    def destroy(self):
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
        super().destroy()

    def _salir(self):
        self.on_volver()

    def _generar_mapa(self):
        columnas, filas = self.COLUMNAS, self.FILAS
        mapa = [["." for _ in range(columnas)] for _ in range(filas)]
        for x in range(columnas):
            mapa[0][x] = "#"
            mapa[filas - 1][x] = "#"
        for y in range(filas):
            mapa[y][0] = "#"
            mapa[y][columnas - 1] = "#"

        bloques = [
            (2, 2, 4, 2), (columnas - 6, 2, 4, 2),
            (2, filas - 4, 4, 2), (columnas - 6, filas - 4, 4, 2),
            (columnas // 2 - 3, filas // 2 - 2, 6, 2),
            (columnas // 2 - 3, filas // 2 + 1, 6, 2),
            (2, filas // 2 - 1, 3, 2), (columnas - 5, filas // 2 - 1, 3, 2),
            (columnas // 2 - 1, 2, 2, 2), (columnas // 2 - 1, filas - 4, 2, 2),
        ]
        for bx, by, bw, bh in bloques:
            for y in range(by, by + bh):
                for x in range(bx, bx + bw):
                    if 0 < x < columnas - 1 and 0 < y < filas - 1:
                        mapa[y][x] = "#"

        for (x, y) in [(1, 1), (columnas - 2, 1), (1, filas - 2), (columnas - 2, filas - 2)]:
            mapa[y][x] = "o"

        fila_tunel = filas // 2
        mapa[fila_tunel][0] = " "
        mapa[fila_tunel][columnas - 1] = " "
        self.fila_tunel = fila_tunel
        return mapa

    def _es_pared(self, x, y):
        if y == self.fila_tunel and (x < 0 or x >= self.COLUMNAS):
            return False
        if x < 0 or x >= self.COLUMNAS or y < 0 or y >= self.FILAS:
            return True
        return self.mapa[y][x] == "#"

    def _nueva_partida(self):
        if self._job:
            self.after_cancel(self._job)
        self.mapa = self._generar_mapa()
        self.total_puntos = sum(row.count(".") + row.count("o") for row in self.mapa)
        self.puntaje = 0
        self.vidas = 3
        self.terminado = False
        self.pacman_x, self.pacman_y = self.COLUMNAS // 2, self.FILAS - 2
        self.mapa[self.pacman_y][self.pacman_x] = " "
        self.direccion = "Left"
        self.direccion_deseada = "Left"
        self.boca_abierta = True
        self.asustado_ticks = 0
        self.combo_fantasmas = 0

        centro_x, centro_y = self.COLUMNAS // 2, self.FILAS // 2
        colores_fantasmas = ["#ef4444", "#f472b6", "#22d3ee"]
        posiciones = [(centro_x - 2, centro_y), (centro_x, centro_y), (centro_x + 2, centro_y)]
        self.fantasmas = []
        for (fx, fy), color in zip(posiciones, colores_fantasmas):
            self.mapa[fy][fx] = " "
            self.fantasmas.append({"x": fx, "y": fy, "color": color, "dir": "Up"})

        self._actualizar_labels()
        self._dibujar()
        self._tick()

    def _cambiar_direccion(self, direccion):
        self.direccion_deseada = direccion

    def _celdas_libres(self, x, y):
        return [d for d, (dx, dy) in
                {"Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0)}.items()
                if not self._es_pared(x + dx, y + dy)]

    def _tick(self):
        if self.terminado:
            return
        self._mover_pacman()
        if not self.terminado:
            self._mover_fantasmas()
        if not self.terminado:
            self.boca_abierta = not self.boca_abierta
            self._dibujar()
            self._job = self.after(self.INTERVALO_MS, self._tick)

    def _mover_pacman(self):
        dxdy = {"Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0)}
        dx, dy = dxdy[self.direccion_deseada]
        if not self._es_pared(self.pacman_x + dx, self.pacman_y + dy):
            self.direccion = self.direccion_deseada
        dx, dy = dxdy[self.direccion]
        nx, ny = self.pacman_x + dx, self.pacman_y + dy
        if self._es_pared(nx, ny):
            return
        nx %= self.COLUMNAS
        ny %= self.FILAS
        self.pacman_x, self.pacman_y = nx, ny

        celda = self.mapa[ny][nx]
        if celda == ".":
            self.mapa[ny][nx] = " "
            self.puntaje += 10
            self.total_puntos -= 1
        elif celda == "o":
            self.mapa[ny][nx] = " "
            self.puntaje += 50
            self.total_puntos -= 1
            self.asustado_ticks = self.DURACION_ASUSTADO
            self.combo_fantasmas = 0

        self._revisar_colisiones_fantasmas()
        if not self.terminado and self.total_puntos <= 0:
            self._ganar()
        self._actualizar_labels()

    def _mover_fantasmas(self):
        if self.asustado_ticks > 0:
            self.asustado_ticks -= 1
        dxdy = {"Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0)}
        for f in self.fantasmas:
            direcciones = self._celdas_libres(f["x"], f["y"])
            if not direcciones:
                continue
            opuesta = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}[f["dir"]]
            candidatas = [d for d in direcciones if d != opuesta] or direcciones

            if random.random() < 0.65:
                if self.asustado_ticks > 0:
                    candidatas.sort(key=lambda d: -(abs((f["x"] + dxdy[d][0]) - self.pacman_x)
                                                     + abs((f["y"] + dxdy[d][1]) - self.pacman_y)))
                else:
                    candidatas.sort(key=lambda d: abs((f["x"] + dxdy[d][0]) - self.pacman_x)
                                                  + abs((f["y"] + dxdy[d][1]) - self.pacman_y))
                elegida = candidatas[0]
            else:
                elegida = random.choice(candidatas)

            dx, dy = dxdy[elegida]
            f["x"] = (f["x"] + dx) % self.COLUMNAS
            f["y"] = (f["y"] + dy) % self.FILAS
            f["dir"] = elegida

        self._revisar_colisiones_fantasmas()

    def _revisar_colisiones_fantasmas(self):
        for f in self.fantasmas:
            if f["x"] == self.pacman_x and f["y"] == self.pacman_y:
                if self.asustado_ticks > 0:
                    self.combo_fantasmas += 1
                    self.puntaje += 200 * self.combo_fantasmas
                    centro_x, centro_y = self.COLUMNAS // 2, self.FILAS // 2
                    f["x"], f["y"] = centro_x, centro_y
                else:
                    self._perder_vida()
                    return

    def _perder_vida(self):
        self.vidas -= 1
        self._actualizar_labels()
        if self.vidas <= 0:
            self._fin_partida()
        else:
            self.pacman_x, self.pacman_y = self.COLUMNAS // 2, self.FILAS - 2
            self.direccion = "Left"
            self.direccion_deseada = "Left"
            centro_x, centro_y = self.COLUMNAS // 2, self.FILAS // 2
            posiciones = [(centro_x - 2, centro_y), (centro_x, centro_y), (centro_x + 2, centro_y)]
            for f, (fx, fy) in zip(self.fantasmas, posiciones):
                f["x"], f["y"] = fx, fy

    def _actualizar_labels(self):
        self.lbl_puntaje.config(text=f"Puntaje: {self.puntaje}")
        self.lbl_vidas.config(text="Vidas: " + "❤" * max(0, self.vidas))

    def _ganar(self):
        self.terminado = True
        self.puntaje += 1000
        self._actualizar_labels()
        self._dibujar()
        self.on_fin_partida(self.puntaje, "¡mapa completo!")
        messagebox.showinfo("Pac-Man", f"🎉 ¡Comiste todos los puntos!\nPuntaje final: {self.puntaje}",
                             parent=self)

    def _fin_partida(self):
        self.terminado = True
        self._dibujar()
        self.on_fin_partida(self.puntaje, "sin vidas")
        messagebox.showinfo("Pac-Man", f"💀 ¡Te atraparon!\nPuntaje final: {self.puntaje}", parent=self)

    def _dibujar(self):
        c = self.canvas
        c.delete("all")
        t = self.TAM_CELDA
        for y in range(self.FILAS):
            for x in range(self.COLUMNAS):
                celda = self.mapa[y][x]
                cx0, cy0 = x * t, y * t
                if celda == "#":
                    c.create_rectangle(cx0, cy0, cx0 + t, cy0 + t, fill="#1e3a8a", outline="#1e40af")
                elif celda == ".":
                    c.create_oval(cx0 + t / 2 - 2, cy0 + t / 2 - 2, cx0 + t / 2 + 2, cy0 + t / 2 + 2,
                                  fill="#fde68a", outline="")
                elif celda == "o":
                    c.create_oval(cx0 + t / 2 - 6, cy0 + t / 2 - 6, cx0 + t / 2 + 6, cy0 + t / 2 + 6,
                                  fill="#fde68a", outline="")

        px0, py0 = self.pacman_x * t, self.pacman_y * t
        angulo_inicio = {"Right": 30, "Left": 210, "Up": 120, "Down": 300}[self.direccion]
        extension = 300 if self.boca_abierta else 359
        c.create_arc(px0 + 2, py0 + 2, px0 + t - 2, py0 + t - 2, start=angulo_inicio,
                     extent=extension, fill="#facc15", outline="")

        for f in self.fantasmas:
            fx0, fy0 = f["x"] * t, f["y"] * t
            color = "#3b82f6" if self.asustado_ticks > 0 else f["color"]
            c.create_oval(fx0 + 2, fy0 + 2, fx0 + t - 2, fy0 + t - 2, fill=color, outline="")
            c.create_oval(fx0 + 6, fy0 + 6, fx0 + 10, fy0 + 10, fill="white", outline="")
            c.create_oval(fx0 + t - 10, fy0 + 6, fx0 + t - 6, fy0 + 10, fill="white", outline="")

        if self.terminado:
            c.create_rectangle(0, 0, self.COLUMNAS * t, self.FILAS * t, fill="#000000", stipple="gray50")


# ════════════════════════════════════════════════════════════════════
#  SOLITARIO (Klondike)
# ════════════════════════════════════════════════════════════════════
class JuegoSolitario(tk.Frame):
    CARD_W = 64
    CARD_H = 92
    OFFSET_TABLEAU = 24
    Y_TOP = 20
    Y_TABLEAU = 134
    X_STOCK = 20
    X_WASTE = 104
    X_FUND_START = 300
    SEP_FUND = 80
    ORDEN_PALOS = ["♠", "♥", "♦", "♣"]

    def __init__(self, parent, on_volver, on_fin_partida):
        super().__init__(parent, bg=GRIS_FONDO)
        self.on_volver = on_volver
        self.on_fin_partida = on_fin_partida
        self.color = COLOR_JUEGO["solitario"]
        self._construir_ui()
        self._nueva_partida()

    def _construir_ui(self):
        marcador = _crear_encabezado_juego(self, "🃏 Solitario", self.color, self._salir)
        self.lbl_puntaje = tk.Label(marcador, text="Puntaje: 0", font=("Segoe UI", 12, "bold"),
                                     bg=self.color, fg=BLANCO)
        self.lbl_puntaje.pack(side="left", padx=10)

        barra = tk.Frame(self, bg=GRIS_FONDO)
        barra.pack(fill="x", padx=16, pady=(12, 0))
        tk.Button(barra, text="🔁 Nueva partida", font=("Segoe UI", 9, "bold"), bg=self.color, fg=BLANCO,
                  relief="flat", cursor="hand2", command=self._nueva_partida).pack(side="left")
        tk.Button(barra, text="🤖 Auto-mover a fundaciones", font=("Segoe UI", 9, "bold"),
                  bg="#e2e8f0", fg=GRIS_TEXTO, relief="flat", cursor="hand2",
                  command=self._auto_mover_fundaciones).pack(side="left", padx=8)
        tk.Button(barra, text="🏳 Terminar y guardar puntaje", font=("Segoe UI", 9, "bold"),
                  bg="#e2e8f0", fg=GRIS_TEXTO, relief="flat", cursor="hand2",
                  command=self._rendirse).pack(side="left", padx=8)
        tk.Label(barra, text="Click en una carta para elegirla, luego click en el destino. Click en el mazo para robar.",
                 font=("Segoe UI", 8, "italic"), bg=GRIS_FONDO, fg="#6b7280").pack(side="left", padx=16)

        marco_canvas = tk.Frame(self, bg=GRIS_FONDO)
        marco_canvas.pack(fill="both", expand=True, padx=16, pady=16)
        self.canvas = tk.Canvas(marco_canvas, width=680, height=560, bg="#0b4a1f",
                                 highlightthickness=2, highlightbackground=self.color)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._clic_canvas)

    def _salir(self):
        self.on_volver()

    def _x_columna(self, idx):
        return 20 + idx * 88

    def _nueva_partida(self):
        self._repartir()
        self.puntaje = 0
        self.terminado = False
        self.seleccion = None
        self._actualizar_labels()
        self._dibujar()

    def _repartir(self):
        mazo = [{"palo": p, "valor": v, "boca_arriba": False}
                for p in self.ORDEN_PALOS for v in range(1, 14)]
        random.shuffle(mazo)
        self.tableau = [[] for _ in range(7)]
        for c in range(7):
            for i in range(c + 1):
                carta = mazo.pop()
                carta["boca_arriba"] = (i == c)
                self.tableau[c].append(carta)
        self.stock = mazo
        self.waste = []
        self.fundaciones = {p: [] for p in self.ORDEN_PALOS}

    def _actualizar_labels(self):
        self.lbl_puntaje.config(text=f"Puntaje: {max(0, self.puntaje)}")

    @staticmethod
    def _es_rojo(palo):
        return palo in ("♥", "♦")

    def _validar_destino_tablero(self, run, col_idx):
        columna = self.tableau[col_idx]
        primera = run[0]
        if not columna:
            return primera["valor"] == 13
        tope = columna[-1]
        return (tope["boca_arriba"] and primera["valor"] == tope["valor"] - 1
                and self._es_rojo(primera["palo"]) != self._es_rojo(tope["palo"]))

    def _validar_destino_fundacion(self, run, palo):
        if len(run) != 1:
            return False
        carta = run[0]
        if carta["palo"] != palo:
            return False
        pila = self.fundaciones[palo]
        if not pila:
            return carta["valor"] == 1
        return carta["valor"] == pila[-1]["valor"] + 1

    def _obtener_run(self, origen):
        if origen[0] == "waste":
            return [self.waste[-1]]
        columna = self.tableau[origen[1]]
        return columna[origen[2]:]

    def _quitar_run(self, origen, cantidad):
        if origen[0] == "waste":
            self.waste.pop()
        else:
            columna = self.tableau[origen[1]]
            del columna[-cantidad:]
            if columna and not columna[-1]["boca_arriba"]:
                columna[-1]["boca_arriba"] = True
                self.puntaje += 5

    def _ejecutar_movimiento(self, origen, destino):
        run = self._obtener_run(origen)
        if destino[0] == "fundacion":
            if not self._validar_destino_fundacion(run, destino[1]):
                return False
            self._quitar_run(origen, len(run))
            self.fundaciones[destino[1]].append(run[0])
            self.puntaje += 10
        else:
            if not self._validar_destino_tablero(run, destino[1]):
                return False
            self._quitar_run(origen, len(run))
            self.tableau[destino[1]].extend(run)
            if origen[0] == "waste":
                self.puntaje += 5
        self._revisar_victoria()
        return True

    def _auto_mover_fundaciones(self):
        movido = True
        while movido:
            movido = False
            if self.waste and self._validar_destino_fundacion([self.waste[-1]], self.waste[-1]["palo"]):
                carta = self.waste.pop()
                self.fundaciones[carta["palo"]].append(carta)
                self.puntaje += 10
                movido = True
            for columna in self.tableau:
                if columna and columna[-1]["boca_arriba"]:
                    carta = columna[-1]
                    if self._validar_destino_fundacion([carta], carta["palo"]):
                        columna.pop()
                        self.fundaciones[carta["palo"]].append(carta)
                        self.puntaje += 10
                        if columna and not columna[-1]["boca_arriba"]:
                            columna[-1]["boca_arriba"] = True
                            self.puntaje += 5
                        movido = True
        self._revisar_victoria()
        self._actualizar_labels()
        self._dibujar()

    def _revisar_victoria(self):
        if not self.terminado and all(len(p) == 13 for p in self.fundaciones.values()):
            self.terminado = True
            self.puntaje += 700
            self._actualizar_labels()
            self.on_fin_partida(self.puntaje, "ganó la partida")
            messagebox.showinfo("Solitario", f"🎉 ¡Ganaste! Puntaje final: {self.puntaje}", parent=self)

    def _rendirse(self):
        if messagebox.askyesno("Solitario", "¿Terminar la partida actual y guardar el puntaje?", parent=self):
            self.on_fin_partida(max(0, self.puntaje), "partida terminada por el usuario")
            self._nueva_partida()

    def _click_stock(self):
        if self.stock:
            carta = self.stock.pop()
            carta["boca_arriba"] = True
            self.waste.append(carta)
        elif self.waste:
            self.stock = list(reversed(self.waste))
            for c in self.stock:
                c["boca_arriba"] = False
            self.waste = []
        self.seleccion = None
        self._dibujar()

    def _click_waste(self):
        if not self.waste:
            return
        self.seleccion = None if self.seleccion == ("waste", None, 0) else ("waste", None, 0)
        self._dibujar()

    def _click_fundacion(self, palo):
        if self.seleccion is not None:
            self._ejecutar_movimiento(self.seleccion, ("fundacion", palo))
        self.seleccion = None
        self._actualizar_labels()
        self._dibujar()

    def _click_tableau(self, col_idx, idx):
        columna = self.tableau[col_idx]
        if self.seleccion is None:
            if idx is None or not columna:
                return
            if idx == len(columna) - 1 and not columna[idx]["boca_arriba"]:
                columna[idx]["boca_arriba"] = True
                self.puntaje += 5
                self._actualizar_labels()
                self._dibujar()
                return
            if columna[idx]["boca_arriba"]:
                self.seleccion = ("tableau", col_idx, idx)
                self._dibujar()
            return

        if self.seleccion == ("tableau", col_idx, idx):
            self.seleccion = None
            self._dibujar()
            return

        self._ejecutar_movimiento(self.seleccion, ("tableau", col_idx))
        self.seleccion = None
        self._actualizar_labels()
        self._dibujar()

    def _tarjeta_en_columna(self, col_idx, x, y):
        columna = self.tableau[col_idx]
        if not columna:
            return None
        for i in range(len(columna) - 1, -1, -1):
            y_i = self.Y_TABLEAU + i * self.OFFSET_TABLEAU
            y_fin = y_i + (self.CARD_H if i == len(columna) - 1 else self.OFFSET_TABLEAU)
            if y_i <= y <= y_fin:
                return i
        return None

    def _clic_canvas(self, event):
        if self.terminado:
            return
        x, y = event.x, event.y
        if self.X_STOCK <= x <= self.X_STOCK + self.CARD_W and self.Y_TOP <= y <= self.Y_TOP + self.CARD_H:
            self._click_stock()
            return
        if self.X_WASTE <= x <= self.X_WASTE + self.CARD_W and self.Y_TOP <= y <= self.Y_TOP + self.CARD_H:
            self._click_waste()
            return
        for i, palo in enumerate(self.ORDEN_PALOS):
            fx = self.X_FUND_START + i * self.SEP_FUND
            if fx <= x <= fx + self.CARD_W and self.Y_TOP <= y <= self.Y_TOP + self.CARD_H:
                self._click_fundacion(palo)
                return
        for col_idx in range(7):
            cx = self._x_columna(col_idx)
            if cx <= x <= cx + self.CARD_W and y >= self.Y_TABLEAU:
                idx = self._tarjeta_en_columna(col_idx, x, y)
                self._click_tableau(col_idx, idx)
                return

    def _dibujar_carta(self, x, y, carta):
        c = self.canvas
        if not carta["boca_arriba"]:
            c.create_rectangle(x, y, x + self.CARD_W, y + self.CARD_H, fill="#1d4ed8",
                                outline="#0f172a", width=2)
            for i in range(8, self.CARD_H, 14):
                c.create_line(x + 4, y + i, x + self.CARD_W - 4, y + i, fill="#3b82f6")
            return
        rojo = self._es_rojo(carta["palo"])
        color_texto = "#dc2626" if rojo else "#111827"
        c.create_rectangle(x, y, x + self.CARD_W, y + self.CARD_H, fill="#ffffff",
                            outline="#0f172a", width=2)
        texto_valor = {1: "A", 11: "J", 12: "Q", 13: "K"}.get(carta["valor"], str(carta["valor"]))
        c.create_text(x + 9, y + 13, text=texto_valor, font=("Segoe UI", 10, "bold"),
                      fill=color_texto, anchor="w")
        c.create_text(x + 9, y + 29, text=carta["palo"], font=("Segoe UI", 11), fill=color_texto, anchor="w")
        c.create_text(x + self.CARD_W / 2, y + self.CARD_H / 2 + 6, text=carta["palo"],
                      font=("Segoe UI", 22), fill=color_texto)

    def _dibujar(self):
        c = self.canvas
        c.delete("all")

        if self.stock:
            self._dibujar_carta(self.X_STOCK, self.Y_TOP, {"boca_arriba": False})
        else:
            c.create_rectangle(self.X_STOCK, self.Y_TOP, self.X_STOCK + self.CARD_W,
                                self.Y_TOP + self.CARD_H, outline="#86efac", dash=(4, 2))
            c.create_text(self.X_STOCK + self.CARD_W / 2, self.Y_TOP + self.CARD_H / 2,
                          text="↺", font=("Segoe UI", 20), fill="#86efac")

        if self.waste:
            self._dibujar_carta(self.X_WASTE, self.Y_TOP, self.waste[-1])
            if self.seleccion == ("waste", None, 0):
                c.create_rectangle(self.X_WASTE - 2, self.Y_TOP - 2, self.X_WASTE + self.CARD_W + 2,
                                    self.Y_TOP + self.CARD_H + 2, outline="#facc15", width=3)
        else:
            c.create_rectangle(self.X_WASTE, self.Y_TOP, self.X_WASTE + self.CARD_W,
                                self.Y_TOP + self.CARD_H, outline="#86efac", dash=(4, 2))

        for i, palo in enumerate(self.ORDEN_PALOS):
            x = self.X_FUND_START + i * self.SEP_FUND
            pila = self.fundaciones[palo]
            if pila:
                self._dibujar_carta(x, self.Y_TOP, pila[-1])
            else:
                c.create_rectangle(x, self.Y_TOP, x + self.CARD_W, self.Y_TOP + self.CARD_H,
                                    outline="#86efac", dash=(3, 2))
                c.create_text(x + self.CARD_W / 2, self.Y_TOP + self.CARD_H / 2, text=palo,
                              font=("Segoe UI", 18),
                              fill="#dc2626" if palo in ("♥", "♦") else "#111827")

        for col_idx, columna in enumerate(self.tableau):
            x = self._x_columna(col_idx)
            if not columna:
                c.create_rectangle(x, self.Y_TABLEAU, x + self.CARD_W, self.Y_TABLEAU + self.CARD_H,
                                    outline="#86efac", dash=(3, 2))
                continue
            for i, carta in enumerate(columna):
                y = self.Y_TABLEAU + i * self.OFFSET_TABLEAU
                self._dibujar_carta(x, y, carta)
            if self.seleccion and self.seleccion[0] == "tableau" and self.seleccion[1] == col_idx:
                idx_sel = self.seleccion[2]
                y_ini = self.Y_TABLEAU + idx_sel * self.OFFSET_TABLEAU
                y_fin = self.Y_TABLEAU + (len(columna) - 1) * self.OFFSET_TABLEAU + self.CARD_H
                c.create_rectangle(x - 2, y_ini - 2, x + self.CARD_W + 2, y_fin + 2,
                                    outline="#facc15", width=3)
