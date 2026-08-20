"""
ventana_clima.py
Módulo "Clima": muestra el clima actual de cualquier departamento/
distrito de Paraguay, con actualización automática cada 10 minutos (y
botón para forzarla manualmente), igual que el módulo Cotizaciones.

Incluye:
  - Clima actual: temperatura, sensación térmica, humedad, viento (con
    dirección), presión y precipitación.
  - Pronóstico de hoy por períodos (Tarde / Noche / Madrugada).
  - Pronóstico de los próximos 5 días.
  - Gráfico de evolución horaria de la temperatura (hora 0 a 23) del día
    que se elija entre los 5, dibujado con tk.Canvas (sin matplotlib ni
    otras librerías de gráficos, para no sumar dependencias pesadas).

Fuente de datos: Open-Meteo (ver models_clima.py para más detalle sobre
por qué se eligió esa API en vez de scrapear el sitio de la DINAC).

Los íconos del clima son formas vectoriales animadas dibujadas con
tk.Canvas y un bucle after() — no son imágenes ni GIFs.
"""
import tkinter as tk
from tkinter import ttk
import threading
import datetime
import math

from models_clima import (
    listar_departamentos, listar_distritos, obtener_coordenadas, obtener_pronostico_completo,
)
from traducciones import t

AZUL = "#1d5fd6"
AZUL_OSC = "#163d8c"
GRIS_FONDO = "#f4f5f7"
GRIS_BORDE = "#e2e8f0"
BLANCO = "#ffffff"
ROJO = "#dc2626"
GRIS_TEXTO = "#6b7280"

INTERVALO_MS = 10 * 60 * 1000  # 10 minutos, igual que Cotizaciones
FPS_ANIMACION_MS = 60  # ~16 cuadros por segundo


class IconoClimaAnimado(tk.Canvas):
    """Ícono del clima dibujado con formas vectoriales animadas (sin
    imágenes ni GIFs): un bucle after() redibuja el ícono varias veces
    por segundo, moviendo nubes, lluvia, rayos, o los rayos del sol,
    según la categoría de clima vigente."""

    def __init__(self, parent, size: int = 170):
        super().__init__(parent, width=size, height=size, bg=BLANCO, highlightthickness=0)
        self.size = size
        self.categoria = "despejado"
        self._t = 0
        self._job = None
        self.bind("<Destroy>", self._al_destruir)
        self._animar()

    def _al_destruir(self, event=None):
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None

    def establecer_categoria(self, categoria: str):
        self.categoria = categoria

    def _animar(self):
        if not self.winfo_exists():
            return
        self._t += 1
        self._dibujar()
        self._job = self.after(FPS_ANIMACION_MS, self._animar)

    def _dibujar(self):
        self.delete("all")
        s = self.size
        cx, cy = s / 2, s / 2

        if self.categoria == "despejado":
            self._sol(cx, cy, radio=s * 0.22, intensidad=1.0)
        elif self.categoria == "parcial":
            self._sol(cx - s * 0.14, cy - s * 0.08, radio=s * 0.16, intensidad=0.8)
            self._nube(cx + s * 0.06, cy + s * 0.10, ancho=s * 0.62, deriva=True)
        elif self.categoria == "nublado":
            self._nube(cx, cy - s * 0.02, ancho=s * 0.72, deriva=True, color="#cbd5e1")
            self._nube(cx - s * 0.12, cy + s * 0.14, ancho=s * 0.42, deriva=True, color="#94a3b8", fase=40)
        elif self.categoria == "niebla":
            self._nube(cx, cy - s * 0.16, ancho=s * 0.6, deriva=True, color="#cbd5e1")
            self._niebla(cx, cy + s * 0.12)
        elif self.categoria == "llovizna":
            self._nube(cx, cy - s * 0.14, ancho=s * 0.68, deriva=True, color="#94a3b8")
            self._lluvia(cx, cy + s * 0.05, cantidad=4, velocidad=0.5, largo=s * 0.05)
        elif self.categoria == "lluvia":
            self._nube(cx, cy - s * 0.16, ancho=s * 0.7, deriva=True, color="#64748b")
            self._lluvia(cx, cy + s * 0.05, cantidad=7, velocidad=1.1, largo=s * 0.09)
        elif self.categoria == "nieve":
            self._nube(cx, cy - s * 0.16, ancho=s * 0.7, deriva=True, color="#cbd5e1")
            self._nieve(cx, cy + s * 0.05)
        elif self.categoria == "tormenta":
            self._nube(cx, cy - s * 0.18, ancho=s * 0.72, deriva=True, color="#475569")
            self._lluvia(cx, cy + s * 0.08, cantidad=5, velocidad=1.3, largo=s * 0.08)
            self._rayo(cx, cy + s * 0.02)
        else:
            self._nube(cx, cy, ancho=s * 0.7, deriva=True)

    def _sol(self, cx, cy, radio, intensidad=1.0):
        angulo_base = (self._t * 2) % 360
        n_rayos = 10
        largo_rayo = radio * 1.5
        for i in range(n_rayos):
            ang = math.radians(angulo_base + i * (360 / n_rayos))
            x1 = cx + math.cos(ang) * radio * 1.15
            y1 = cy + math.sin(ang) * radio * 1.15
            x2 = cx + math.cos(ang) * (radio * 1.15 + largo_rayo * 0.35)
            y2 = cy + math.sin(ang) * (radio * 1.15 + largo_rayo * 0.35)
            self.create_line(x1, y1, x2, y2, fill="#f59e0b", width=3, capstyle="round")
        color_sol = "#fbbf24" if intensidad >= 1.0 else "#fcd34d"
        self.create_oval(cx - radio, cy - radio, cx + radio, cy + radio,
                         fill=color_sol, outline="#f59e0b", width=2)

    def _nube(self, cx, cy, ancho, deriva=True, color="#cbd5e1", fase=0):
        despl = math.sin((self._t + fase) / 40) * (ancho * 0.06) if deriva else 0
        cx += despl
        alto = ancho * 0.55
        self.create_oval(cx - ancho * 0.5, cy - alto * 0.15, cx - ancho * 0.10, cy + alto * 0.45,
                         fill=color, outline=color)
        self.create_oval(cx - ancho * 0.30, cy - alto * 0.50, cx + ancho * 0.15, cy + alto * 0.30,
                         fill=color, outline=color)
        self.create_oval(cx - ancho * 0.05, cy - alto * 0.35, cx + ancho * 0.45, cy + alto * 0.40,
                         fill=color, outline=color)
        self.create_oval(cx + ancho * 0.15, cy - alto * 0.05, cx + ancho * 0.50, cy + alto * 0.45,
                         fill=color, outline=color)
        self.create_rectangle(cx - ancho * 0.45, cy, cx + ancho * 0.45, cy + alto * 0.42,
                              fill=color, outline=color)

    def _lluvia(self, cx, cy_top, cantidad, velocidad, largo):
        ancho_zona = self.size * 0.55
        alto_zona = self.size * 0.42
        for i in range(cantidad):
            x0 = cx - ancho_zona / 2 + (i + 0.5) * (ancho_zona / cantidad)
            fase = (self._t * velocidad * 3 + i * 17) % 100
            y0 = cy_top + (fase / 100) * alto_zona
            self.create_line(x0, y0, x0 - largo * 0.3, y0 + largo, fill="#3b82f6", width=2, capstyle="round")

    def _nieve(self, cx, cy_top):
        ancho_zona = self.size * 0.55
        alto_zona = self.size * 0.42
        for i in range(6):
            fase = (self._t * 0.6 + i * 23) % 100
            x_deriva = math.sin((self._t + i * 10) / 15) * 6
            x0 = cx - ancho_zona / 2 + (i + 0.5) * (ancho_zona / 6) + x_deriva
            y0 = cy_top + (fase / 100) * alto_zona
            r = 2.5
            self.create_oval(x0 - r, y0 - r, x0 + r, y0 + r, fill="white", outline="#cbd5e1")

    def _niebla(self, cx, cy):
        ancho = self.size * 0.62
        for i, dy in enumerate((-10, 4, 18)):
            despl = math.sin((self._t + i * 15) / 25) * (ancho * 0.08)
            y = cy + dy
            self.create_line(cx - ancho / 2 + despl, y, cx + ancho / 2 + despl, y,
                             fill="#cbd5e1", width=4, capstyle="round")

    def _rayo(self, cx, cy):
        if (self._t // 12) % 3 != 0:
            return
        s = self.size
        puntos = [
            cx - s * 0.03, cy,
            cx + s * 0.05, cy,
            cx - s * 0.02, cy + s * 0.16,
            cx + s * 0.03, cy + s * 0.16,
            cx - s * 0.08, cy + s * 0.34,
            cx - s * 0.01, cy + s * 0.20,
            cx - s * 0.07, cy + s * 0.20,
        ]
        self.create_polygon(puntos, fill="#facc15", outline="#f59e0b")


class GraficoHorario(tk.Canvas):
    """Gráfico de línea de la temperatura hora a hora (0 a 23) de un día,
    dibujado con formas vectoriales (líneas, puntos y texto) sobre un
    tk.Canvas — sin matplotlib ni ninguna librería de gráficos externa."""

    def __init__(self, parent, width=760, height=220):
        super().__init__(parent, width=width, height=height, bg=BLANCO, highlightthickness=0)
        self._ancho, self._alto = width, height
        self.datos: list[tuple[int, float]] = []

    def establecer_datos(self, datos_hora_temp: list[tuple[int, float]]):
        self.datos = sorted(datos_hora_temp, key=lambda x: x[0])
        self._dibujar()

    def _dibujar(self):
        self.delete("all")
        if not self.datos:
            self.create_text(self._ancho / 2, self._alto / 2, text="Sin datos horarios disponibles.",
                             fill=GRIS_TEXTO, font=("Segoe UI", 9))
            return

        margen_izq, margen_der = 46, 20
        margen_arr, margen_abj = 16, 30
        ancho_grafico = self._ancho - margen_izq - margen_der
        alto_grafico = self._alto - margen_arr - margen_abj

        temps = [t for _, t in self.datos]
        t_min, t_max = min(temps), max(temps)
        if t_max == t_min:
            t_max += 1
        rango = t_max - t_min
        # Un poco de aire arriba/abajo para que la línea no toque los bordes.
        t_min -= rango * 0.15
        t_max += rango * 0.15
        rango = t_max - t_min

        def x_de(hora):
            return margen_izq + (hora / 23) * ancho_grafico

        def y_de(temp):
            return margen_arr + (1 - (temp - t_min) / rango) * alto_grafico

        # Líneas guía horizontales con la temperatura de referencia.
        for frac in (0, 0.5, 1.0):
            y = margen_arr + frac * alto_grafico
            temp_ref = t_max - frac * rango
            self.create_line(margen_izq, y, self._ancho - margen_der, y, fill="#e5e7eb", width=1)
            self.create_text(margen_izq - 8, y, text=f"{temp_ref:.0f}°", anchor="e",
                             font=("Segoe UI", 8), fill=GRIS_TEXTO)

        # Etiquetas de hora cada 3 horas.
        for hora in range(0, 24, 3):
            x = x_de(hora)
            self.create_text(x, self._alto - margen_abj + 14, text=f"{hora:02d}h",
                             font=("Segoe UI", 8), fill=GRIS_TEXTO)
            self.create_line(x, margen_arr, x, self._alto - margen_abj, fill="#f3f4f6", width=1)

        # Línea de temperatura + puntos, resaltando la hora actual si
        # corresponde al día de hoy.
        hora_actual = datetime.datetime.now().hour
        puntos_linea = []
        for hora, temp in self.datos:
            x, y = x_de(hora), y_de(temp)
            puntos_linea.extend([x, y])
        if len(puntos_linea) >= 4:
            self.create_line(*puntos_linea, fill=AZUL, width=2, smooth=True)
        for hora, temp in self.datos:
            x, y = x_de(hora), y_de(temp)
            es_actual = (hora == hora_actual)
            r = 4 if es_actual else 2.5
            color = "#f59e0b" if es_actual else AZUL
            self.create_oval(x - r, y - r, x + r, y + r, fill=color, outline=BLANCO, width=1)
            if hora % 3 == 0 or es_actual:
                self.create_text(x, y - 12, text=f"{temp:.0f}°", font=("Segoe UI", 7, "bold"), fill="#374151")


class PanelClima(tk.Frame):
    def __init__(self, parent, usuario_actual=None):
        super().__init__(parent, bg=BLANCO)
        self.usuario_actual = usuario_actual
        self._job_actualizacion = None
        self._iconos_secundarios: list[IconoClimaAnimado] = []
        self._dia_grafico_idx = 0
        self._ultimo_pronostico = None
        self._construir_ui()
        self.bind("<Destroy>", self._al_destruir)
        self._actualizar_clima()

    def _al_destruir(self, event=None):
        if event is not None and event.widget is not self:
            return
        if self._job_actualizacion:
            try:
                self.after_cancel(self._job_actualizacion)
            except Exception:
                pass
        # Por si el mouse quedó "adentro" del área con scroll justo cuando
        # se cambió de módulo (sin pasar por <Leave>), se desactiva el
        # bind_all igual acá para no dejarlo pegado afectando otras
        # pantallas.
        try:
            self.canvas_scroll.unbind_all("<MouseWheel>")
            self.canvas_scroll.unbind_all("<Button-4>")
            self.canvas_scroll.unbind_all("<Button-5>")
        except Exception:
            pass

    # ── UI general (con scroll, porque el contenido es largo) ───
    def _construir_ui(self):
        encabezado = tk.Frame(self, bg=AZUL, height=54)
        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)
        tk.Label(encabezado, text=t("clima_titulo"),
                 font=("Segoe UI", 15, "bold"), bg=AZUL, fg=BLANCO
                 ).pack(side="left", padx=20, pady=12)

        barra = tk.Frame(self, bg=BLANCO)
        barra.pack(fill="x", padx=20, pady=(14, 6))

        tk.Label(barra, text=t("clima_departamento"), font=("Segoe UI", 9, "bold"), bg=BLANCO).pack(side="left")
        self.var_depto = tk.StringVar(value="Distrito Capital")
        self.combo_depto = ttk.Combobox(barra, textvariable=self.var_depto, state="readonly",
                                        values=listar_departamentos(), width=22, font=("Segoe UI", 9))
        self.combo_depto.pack(side="left", padx=(6, 20))
        self.combo_depto.bind("<<ComboboxSelected>>", self._al_cambiar_departamento)

        tk.Label(barra, text=t("clima_ciudad_distrito"), font=("Segoe UI", 9, "bold"), bg=BLANCO).pack(side="left")
        self.var_distrito = tk.StringVar(value="Asunción")
        self.combo_distrito = ttk.Combobox(barra, textvariable=self.var_distrito, state="readonly",
                                           values=listar_distritos("Distrito Capital"),
                                           width=26, font=("Segoe UI", 9))
        self.combo_distrito.pack(side="left", padx=(6, 20))
        self.combo_distrito.bind("<<ComboboxSelected>>", lambda e: self._actualizar_clima())

        self.btn_refresh = tk.Button(barra, text=t("actualizar_icono"), font=("Segoe UI", 9, "bold"),
                                     bg=BLANCO, fg=AZUL, relief="solid", bd=1, padx=10, pady=5,
                                     cursor="hand2", activebackground="#eff6ff",
                                     command=self._actualizar_clima)
        self.btn_refresh.pack(side="left")

        self.lbl_update = tk.Label(barra, text="", font=("Segoe UI", 8, "italic"),
                                   bg=BLANCO, fg=GRIS_TEXTO)
        self.lbl_update.pack(side="right")

        # ── Área con scroll para todo el contenido (es largo) ──
        contenedor_scroll = tk.Frame(self, bg=BLANCO)
        contenedor_scroll.pack(fill="both", expand=True, padx=20, pady=(6, 20))
        self.canvas_scroll = tk.Canvas(contenedor_scroll, bg=BLANCO, highlightthickness=0)
        sb = ttk.Scrollbar(contenedor_scroll, orient="vertical", command=self.canvas_scroll.yview)
        self.canvas_scroll.configure(yscrollcommand=sb.set)
        self.canvas_scroll.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.frame_scroll = tk.Frame(self.canvas_scroll, bg=BLANCO)
        self._id_ventana = self.canvas_scroll.create_window((0, 0), window=self.frame_scroll, anchor="nw")
        self.frame_scroll.bind("<Configure>", lambda e: self.canvas_scroll.configure(
            scrollregion=self.canvas_scroll.bbox("all")))
        self.canvas_scroll.bind("<Configure>", lambda e: self.canvas_scroll.itemconfig(
            self._id_ventana, width=e.width))

        def _rueda(event):
            delta = event.delta
            if delta == 0:
                delta = -1 if getattr(event, "num", None) == 5 else 1
            else:
                delta = int(-1 * (delta / 120)) if abs(delta) >= 120 else -1 * delta
            self.canvas_scroll.yview_scroll(delta, "units")

        def _activar_scroll(event=None):
            # Se activa recién al entrar con el mouse/touchpad sobre esta
            # sección, y con bind_all (no solo sobre el canvas): así
            # también funciona cuando el cursor está sobre cualquiera de
            # los widgets de adentro (tarjetas, botones, íconos, etc.),
            # que es la mayor parte del área visible.
            self.canvas_scroll.bind_all("<MouseWheel>", _rueda)
            self.canvas_scroll.bind_all("<Button-4>", _rueda)
            self.canvas_scroll.bind_all("<Button-5>", _rueda)

        def _desactivar_scroll(event=None):
            self.canvas_scroll.unbind_all("<MouseWheel>")
            self.canvas_scroll.unbind_all("<Button-4>")
            self.canvas_scroll.unbind_all("<Button-5>")

        contenedor_scroll.bind("<Enter>", _activar_scroll)
        contenedor_scroll.bind("<Leave>", _desactivar_scroll)

        # ── Clima actual ──
        self.cuerpo_actual = tk.Frame(self.frame_scroll, bg=BLANCO, highlightthickness=1,
                                      highlightbackground=GRIS_BORDE)
        self.cuerpo_actual.pack(fill="x", pady=(0, 14))
        self._construir_seccion_actual()

        # ── Hoy por períodos ──
        tk.Label(self.frame_scroll, text=t("clima_hoy"), font=("Segoe UI", 12, "bold"), bg=BLANCO
                 ).pack(anchor="w", pady=(0, 6))
        self.frame_periodos = tk.Frame(self.frame_scroll, bg=BLANCO)
        self.frame_periodos.pack(fill="x", pady=(0, 16))

        # ── Pronóstico 5 días ──
        tk.Label(self.frame_scroll, text=t("clima_pronostico_5dias"), font=("Segoe UI", 12, "bold"), bg=BLANCO
                 ).pack(anchor="w", pady=(0, 6))
        self.frame_dias = tk.Frame(self.frame_scroll, bg=BLANCO)
        self.frame_dias.pack(fill="x", pady=(0, 16))

        # ── Gráfico horario ──
        self.lbl_titulo_grafico = tk.Label(self.frame_scroll, text=t("clima_evolucion_horaria"),
                                           font=("Segoe UI", 12, "bold"), bg=BLANCO)
        self.lbl_titulo_grafico.pack(anchor="w", pady=(0, 6))
        frame_grafico_cont = tk.Frame(self.frame_scroll, bg=BLANCO, highlightthickness=1,
                                      highlightbackground=GRIS_BORDE)
        frame_grafico_cont.pack(fill="x", pady=(0, 10))
        self.grafico = GraficoHorario(frame_grafico_cont, width=900, height=220)
        self.grafico.pack(padx=10, pady=10, fill="x")

        self.lbl_error = tk.Label(self.frame_scroll, text="", font=("Segoe UI", 9), bg=BLANCO, fg=ROJO,
                                  wraplength=800, justify="left")
        self.lbl_error.pack(pady=(0, 10))

    def _construir_seccion_actual(self):
        fila = tk.Frame(self.cuerpo_actual, bg=BLANCO)
        fila.pack(pady=24, padx=20, fill="x")

        self.icono = IconoClimaAnimado(fila, size=150)
        self.icono.pack(side="left", padx=(10, 30))

        info = tk.Frame(fila, bg=BLANCO)
        info.pack(side="left", fill="both", expand=True)

        self.lbl_ciudad = tk.Label(info, text="Asunción, Distrito Capital",
                                   font=("Segoe UI", 16, "bold"), bg=BLANCO)
        self.lbl_ciudad.pack(anchor="w")
        self.lbl_temp = tk.Label(info, text="—", font=("Segoe UI", 34, "bold"), bg=BLANCO, fg=AZUL)
        self.lbl_temp.pack(anchor="w")
        self.lbl_desc = tk.Label(info, text="", font=("Segoe UI", 12), bg=BLANCO, fg=GRIS_TEXTO)
        self.lbl_desc.pack(anchor="w", pady=(0, 10))

        grilla_datos = tk.Frame(info, bg=BLANCO)
        grilla_datos.pack(anchor="w", fill="x")
        grilla_datos.grid_columnconfigure(1, weight=1)
        grilla_datos.grid_columnconfigure(3, weight=1)
        self.lbl_presion = self._fila_dato(grilla_datos, 0, 0, "🌀 Presión:")
        self.lbl_sensacion = self._fila_dato(grilla_datos, 0, 2, "🌡 Sensación térmica:")
        self.lbl_humedad = self._fila_dato(grilla_datos, 1, 0, "💧 Humedad:")
        self.lbl_viento = self._fila_dato(grilla_datos, 1, 2, "💨 Viento:")
        self.lbl_precipitacion = self._fila_dato(grilla_datos, 2, 0, "🌧 Precipitación (última hora):")

    def _fila_dato(self, parent, fila, columna, etiqueta):
        tk.Label(parent, text=etiqueta, font=("Segoe UI", 9, "bold"), bg=BLANCO).grid(
            row=fila, column=columna, sticky="w", pady=3, padx=(0, 6))
        lbl_valor = tk.Label(parent, text="—", font=("Segoe UI", 9), bg=BLANCO)
        lbl_valor.grid(row=fila, column=columna + 1, sticky="w", pady=3, padx=(0, 20))
        return lbl_valor

    def _al_cambiar_departamento(self, event=None):
        depto = self.var_depto.get()
        distritos = listar_distritos(depto)
        self.combo_distrito["values"] = distritos
        if distritos:
            self.var_distrito.set(distritos[0])
        self._actualizar_clima()

    # ── Tarjetas de período / día (reutilizan la misma estructura) ──
    def _limpiar_iconos_secundarios(self):
        for icono in self._iconos_secundarios:
            icono.destroy()
        self._iconos_secundarios = []

    def _tarjeta_periodo(self, parent, periodo: dict):
        card = tk.Frame(parent, bg=BLANCO, highlightthickness=1, highlightbackground=GRIS_BORDE)
        card.pack(side="left", fill="both", expand=True, padx=(0, 10), ipady=8)
        tk.Label(card, text=periodo["nombre"].upper(), font=("Segoe UI", 9, "bold"),
                 bg=BLANCO, fg=GRIS_TEXTO).pack(pady=(8, 2))
        icono = IconoClimaAnimado(card, size=60)
        icono.establecer_categoria(periodo["categoria"])
        icono.pack()
        self._iconos_secundarios.append(icono)
        if periodo["temp_max"] is not None:
            tk.Label(card, text=f"{periodo['temp_max']} a {periodo['temp_min']} °C",
                     font=("Segoe UI", 11, "bold"), bg=BLANCO).pack(pady=(4, 2))
        tk.Label(card, text=periodo["texto"], font=("Segoe UI", 8), bg=BLANCO, fg=GRIS_TEXTO,
                 wraplength=180, justify="center").pack(padx=8, pady=(0, 8))

    def _tarjeta_dia(self, parent, dia: dict, idx: int):
        seleccionado = (idx == self._dia_grafico_idx)
        card = tk.Frame(parent, bg="#e0f2fe" if seleccionado else BLANCO, relief="solid",
                        bd=2 if seleccionado else 1,
                        highlightbackground=AZUL if seleccionado else GRIS_BORDE, cursor="hand2")
        card.pack(side="left", fill="both", expand=True, padx=(0, 8), ipady=8)

        def _elegir(event=None, i=idx):
            self._dia_grafico_idx = i
            self._refrescar_grafico()
            self._poblar_dias(self._ultimo_pronostico["dias"])

        card.bind("<Button-1>", _elegir)
        lbl_dia = tk.Label(card, text=f"{dia['nombre_dia'].upper()} {dia['dia_mes']}",
                           font=("Segoe UI", 9, "bold"), bg=card.cget("bg"))
        lbl_dia.pack(pady=(8, 2))
        lbl_dia.bind("<Button-1>", _elegir)
        icono = IconoClimaAnimado(card, size=50)
        icono.establecer_categoria(dia["categoria"])
        icono.pack()
        icono.bind("<Button-1>", _elegir)
        self._iconos_secundarios.append(icono)
        lbl_temp = tk.Label(card, text=f"{dia['temp_max']}° / {dia['temp_min']}°",
                            font=("Segoe UI", 10, "bold"), bg=card.cget("bg"))
        lbl_temp.pack(pady=(4, 2))
        lbl_temp.bind("<Button-1>", _elegir)
        lbl_txt = tk.Label(card, text=dia["texto"], font=("Segoe UI", 8), bg=card.cget("bg"),
                           fg=GRIS_TEXTO, wraplength=140, justify="center")
        lbl_txt.pack(padx=6, pady=(0, 8))
        lbl_txt.bind("<Button-1>", _elegir)

    def _poblar_periodos(self, periodos: list):
        for w in self.frame_periodos.winfo_children():
            w.destroy()
        for p in periodos:
            self._tarjeta_periodo(self.frame_periodos, p)

    def _poblar_dias(self, dias: list):
        for w in self.frame_dias.winfo_children():
            w.destroy()
        for i, d in enumerate(dias):
            self._tarjeta_dia(self.frame_dias, d, i)

    def _refrescar_grafico(self):
        if not self._ultimo_pronostico:
            return
        dias = self._ultimo_pronostico["dias"]
        if not dias or self._dia_grafico_idx >= len(dias):
            return
        dia = dias[self._dia_grafico_idx]
        self.lbl_titulo_grafico.config(
            text=f"Evolución horaria — {dia['nombre_dia']} {dia['dia_mes']}")
        datos_hora = self._ultimo_pronostico["horas_por_dia"].get(dia["fecha"], [])
        self.grafico.establecer_datos(datos_hora)

    # ── Actualización de datos (hilo secundario) ────────────────
    def _actualizar_clima(self):
        if self._job_actualizacion:
            try:
                self.after_cancel(self._job_actualizacion)
            except Exception:
                pass
        if not self.winfo_exists():
            return

        depto = self.var_depto.get()
        distrito = self.var_distrito.get()
        coords = obtener_coordenadas(depto, distrito)
        self.lbl_ciudad.config(text=f"{distrito}, {depto}")
        self.lbl_error.config(text="")

        if not coords:
            self.lbl_error.config(text=t("clima_sin_coordenadas"))
            return

        self.btn_refresh.config(state="disabled", text=t("clima_actualizando"))
        self.lbl_update.config(text=t("clima_descargando_datos"))
        lat, lon = coords
        self._dia_grafico_idx = 0

        def _tarea():
            try:
                pronostico = obtener_pronostico_completo(lat, lon)
                error = None
            except Exception as e:
                pronostico = None
                error = str(e)

            def _ui():
                if not self.winfo_exists():
                    return
                self.btn_refresh.config(state="normal", text=t("actualizar_icono"))
                if pronostico:
                    self._ultimo_pronostico = pronostico
                    clima = pronostico["actual"]
                    self.icono.establecer_categoria(clima["categoria"])
                    self.lbl_temp.config(text=f"{clima['temperatura']:.0f}°C")
                    self.lbl_desc.config(text=clima["descripcion"])
                    self.lbl_sensacion.config(text=f"{clima['sensacion_termica']:.0f}°C")
                    self.lbl_humedad.config(text=f"{clima['humedad']:.0f}%")
                    viento_txt = f"{clima['viento_kmh']:.0f} km/h"
                    if clima.get("direccion_viento"):
                        viento_txt += f" {clima['direccion_viento']}"
                    self.lbl_viento.config(text=viento_txt)
                    presion = clima.get("presion_hpa")
                    self.lbl_presion.config(text=f"{presion:.1f} hPa" if presion else "—")
                    self.lbl_precipitacion.config(text=f"{clima['precipitacion_mm']:.1f} mm")

                    self._limpiar_iconos_secundarios()
                    self._poblar_periodos(pronostico["periodos_hoy"])
                    self._poblar_dias(pronostico["dias"])
                    self._refrescar_grafico()

                    ahora = datetime.datetime.now().strftime("%H:%M:%S")
                    self.lbl_update.config(text=f"Última actualización: {ahora}")
                    self.lbl_error.config(text="")
                else:
                    self.lbl_update.config(text="")
                    self.lbl_error.config(
                        text=f"⚠ No se pudo obtener el clima. Verificá tu conexión a internet.\n({error})")
                self._job_actualizacion = self.after(INTERVALO_MS, self._actualizar_clima)

            self.after(0, _ui)

        threading.Thread(target=_tarea, daemon=True).start()
