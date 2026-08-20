"""
ventana_calculadora.py
Calculadora integrada al sistema, inspirada en la app "Calculadora" de
Windows 11: un panel lateral (con scroll) permite elegir el tipo de
calculadora / conversor, y el panel derecho muestra la calculadora
elegida.

Incluye:
  - Estándar
  - Científica
  - Programador
  - Cálculo de fecha
  - Convertidor: Moneda, Volumen, Longitud, Peso y masa, Temperatura,
    Energía, Área, Velocidad, Tiempo, Potencia, Datos, Presión, Ángulo

No depende de librerías externas (solo Tkinter + math + urllib, que ya
se usan en el resto del sistema).
"""
import tkinter as tk
from tkinter import ttk
import math
import datetime
import threading

try:
    from urllib.request import urlopen
    import json
except ImportError:
    urlopen = None

AZUL        = "#1d5fd6"
AZUL_OSC    = "#163d8c"
FONDO       = "#f4f5f7"
FONDO_MENU  = "#ffffff"
BORDE       = "#e2e8f0"
NEGRO       = "#1e293b"
GRIS_TEXT   = "#6b7280"
BLANCO      = "#ffffff"
HOVER       = "#eef2ff"
SELECCION   = "#e0e7ff"


# ───────────────────────── Definición de menú ──────────────────────────
# Cada item: (clave, etiqueta, icono)
MENU_CALCULADORA = [
    ("estandar",    "Estándar",         "🧮"),
    ("cientifica",  "Científica",       "🔬"),
    ("grafica",     "Gráfica",          "📈"),
    ("programador", "Programador",      "💻"),
    ("fecha",       "Cálculo de fecha", "📅"),
]

MENU_CONVERTIDOR = [
    ("moneda",      "Moneda",           "💱"),
    ("volumen",     "Volumen",          "🧪"),
    ("longitud",    "Longitud",         "📏"),
    ("peso",        "Peso y masa",      "⚖"),
    ("temperatura", "Temperatura",      "🌡"),
    ("energia",     "Energía",          "🔋"),
    ("area",        "Área",             "▦"),
    ("velocidad",   "Velocidad",        "🚀"),
    ("tiempo",      "Tiempo",           "⏰"),
    ("potencia",    "Potencia",         "⚡"),
    ("datos",       "Datos",            "💾"),
    ("presion",     "Presión",          "🧭"),
    ("angulo",      "Ángulo",           "📐"),
]

# ───────────────────── Tablas de conversión (a unidad base) ─────────────
UNIDADES = {
    "volumen": {
        "base": "ml",
        "unidades": {
            "Mililitros": 1, "Litros": 1000, "Cucharaditas (EE. UU.)": 4.92892,
            "Cucharadas (EE. UU.)": 14.7868, "Tazas (EE. UU.)": 236.588,
            "Pintas (EE. UU.)": 473.176, "Galones (EE. UU.)": 3785.41,
            "Mililitros³": 1, "Metros cúbicos": 1_000_000,
        },
    },
    "longitud": {
        "base": "cm",
        "unidades": {
            "Milímetros": 0.1, "Centímetros": 1, "Metros": 100,
            "Kilómetros": 100000, "Pulgadas": 2.54, "Pies": 30.48,
            "Yardas": 91.44, "Millas": 160934,
        },
    },
    "peso": {
        "base": "g",
        "unidades": {
            "Miligramos": 0.001, "Gramos": 1, "Kilogramos": 1000,
            "Libras": 453.592, "Onzas": 28.3495, "Toneladas métricas": 1_000_000,
        },
    },
    "area": {
        "base": "m2",
        "unidades": {
            "Metros cuadrados": 1, "Kilómetros cuadrados": 1_000_000,
            "Pies cuadrados": 0.092903, "Yardas cuadradas": 0.836127,
            "Acres": 4046.86, "Hectáreas": 10000,
        },
    },
    "velocidad": {
        "base": "kmh",
        "unidades": {
            "Kilómetros por hora": 1, "Millas por hora": 1.60934,
            "Metros por segundo": 3.6, "Nudos": 1.852,
        },
    },
    "tiempo": {
        "base": "s",
        "unidades": {
            "Segundos": 1, "Minutos": 60, "Horas": 3600,
            "Días": 86400, "Semanas": 604800,
        },
    },
    "potencia": {
        "base": "w",
        "unidades": {
            "Vatios": 1, "Kilovatios": 1000,
            "Caballos de fuerza (EE. UU.)": 745.7,
            "BTU por minuto": 17.5843,
            "Pies-libra por minuto": 0.0225970,
        },
    },
    "datos": {
        "base": "byte",
        "unidades": {
            "Bytes": 1, "Kilobytes": 1024, "Megabytes": 1024 ** 2,
            "Gigabytes": 1024 ** 3, "Terabytes": 1024 ** 4,
        },
    },
    "presion": {
        "base": "pa",
        "unidades": {
            "Pascales": 1, "Kilopascales": 1000, "Bar": 100000,
            "Atmósferas": 101325, "PSI": 6894.76,
        },
    },
    "angulo": {
        "base": "grados",
        "unidades": {
            "Grados": 1, "Radianes": 57.29578, "Gradianes": 0.9,
        },
    },
    "energia": {
        "base": "j",
        "unidades": {
            "Julios": 1, "Kilojulios": 1000, "Calorías": 4.184,
            "Calorías alimentarias": 4184, "Vatios-hora": 3600,
        },
    },
}

MONEDAS_COMUNES = ["PYG", "USD", "EUR", "ARS", "BRL"]
# Categorías que además muestran una línea "Prácticamente igual que..."
# con la conversión a las demás unidades de la categoría, igual que en
# la calculadora de Windows.
CATEGORIAS_CON_REFERENCIA = {"temperatura", "potencia", "angulo"}

# Etiqueta a mostrar en el encabezado según la vista seleccionada
ETIQUETAS_VISTA = {clave: etiqueta for clave, etiqueta, _icono
                    in MENU_CALCULADORA + MENU_CONVERTIDOR}

# Nombres abreviados para la línea "Prácticamente igual que", ya que el
# panel es angosto y los nombres completos no entran en una sola línea.
NOMBRES_CORTOS = {
    "Caballos de fuerza (EE. UU.)": "hp",
    "BTU por minuto": "BTU/min",
    "Pies-libra por minuto": "ft·lb/min",
    "Kilovatios": "kW",
    "Vatios": "W",
    "Kelvin": "K",
    "Gradianes": "gradianes",
    "Radianes": "radianes",
    "Grados": "grados",
}
NOMBRES_MONEDA = {
    "PYG": "Paraguay - Guaraní", "USD": "Estados Unidos - Dólar",
    "EUR": "Europa - Euro", "ARS": "Argentina - Peso", "BRL": "Brasil - Real",
}


_MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
    "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _formatear_fecha_larga(fecha: datetime.date) -> str:
    """Formatea como '12 de julio de 2026', sin depender del locale
    del sistema operativo (que puede estar en inglés)."""
    return f"{fecha.day} de {_MESES_ES[fecha.month - 1]} de {fecha.year}"


def _formatear_numero(valor: float) -> str:
    """Formatea un número al estilo de la calculadora de Windows
    (sin ceros de más, coma como separador decimal)."""
    if valor == int(valor) and abs(valor) < 1e15:
        texto = f"{int(valor)}"
    else:
        texto = f"{valor:.6f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",")


def _texto_a_float(texto: str) -> float:
    if not texto:
        return 0.0
    try:
        return float(texto.replace(".", "").replace(",", "."))
    except ValueError:
        return 0.0


class VentanaCalculadora(tk.Toplevel):
    """Ventana de calculadora con panel lateral desplazable para elegir
    el tipo de calculadora / conversor, similar a la app nativa de
    Windows 11."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Calculadora")
        self.configure(bg=FONDO)
        # Tamaño inicial más compacto (antes 640x680, demasiado grande
        # para una calculadora): se busca una proporción similar a la
        # calculadora nativa de Windows, que sigue siendo redimensionable
        # si el usuario la quiere más grande.
        self.geometry("360x560")
        self.minsize(320, 480)
        # NOTA: deliberadamente NO se usa self.transient(parent) aquí.
        # En Windows, transient() suprime los botones de minimizar/
        # maximizar de la ventana (bug conocido de Tkinter), y queremos
        # que la calculadora se comporte como una ventana independiente
        # con controles completos, igual que la calculadora nativa.

        self._vista_actual = None
        self._panel_derecho = None
        self._botones_menu = {}
        self._memoria = None            # registro único de memoria (MC/MR/M+/M-/MS)
        self._grupos_memoria = []       # botones de memoria de la vista activa
        self._historial = []            # lista de (expresion, resultado)
        self._overlay_menu_visible = False
        self._overlay_historial_visible = False
        self._siempre_encima = False
        self._accion_convertidor_actual = None  # closure de teclado del convertidor activo

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_encabezado()
        self._construir_area_contenido()
        self._construir_overlay_menu()
        self._construir_overlay_historial()

        self._seleccionar("estandar")

        self.bind("<Configure>", self._al_redimensionar)
        # Soporte de teclado: números, operadores, Enter, Backspace, etc.
        # (antes la calculadora solo se podía usar con el mouse).
        self.bind("<Key>", self._on_key)
        self.lift()
        self.focus_set()

    def _al_redimensionar(self, event):
        if event.widget is not self:
            return
        if self._overlay_menu_visible:
            alto = max(self.winfo_height() - 47, 100)
            self._overlay_menu.place_configure(height=alto)
        if self._overlay_historial_visible:
            alto = max(self.winfo_height() - 47, 100)
            ancho = min(280, self.winfo_width())
            self._overlay_historial.place_configure(height=alto, width=ancho,
                                                      x=self.winfo_width() - ancho)

    # ─────────────────────── Entrada por teclado ────────────────────────
    def _on_key(self, event):
        """Permite operar la calculadora por teclado además de con el
        mouse: dígitos, operadores básicos, Enter para '=', Backspace
        para borrar el último carácter, Supr para CE y Escape para C.
        Los campos de texto reales (ej. 'f(x)=' en Gráfica) y los combos
        desplegables manejan su propio tecleo con normalidad; acá no se
        intercepta nada en esos casos."""
        widget = event.widget
        if isinstance(widget, (tk.Entry, ttk.Combobox)):
            return None

        vista = self._vista_actual
        tecla = event.keysym
        car = event.char

        if vista == "estandar":
            if car.isdigit():
                self._accion_estandar(f"d{car}")
                return "break"
            if car in (",", "."):
                self._accion_estandar("coma")
                return "break"
            if car == "+":
                self._accion_estandar("op_sum")
                return "break"
            if car == "-":
                self._accion_estandar("op_sub")
                return "break"
            if car in ("*", "x", "X"):
                self._accion_estandar("op_mul")
                return "break"
            if car == "/":
                self._accion_estandar("op_div")
                return "break"
            if car == "%":
                self._accion_estandar("op_pct")
                return "break"
            if tecla in ("Return", "KP_Enter", "equal"):
                self._accion_estandar("igual")
                return "break"
            if tecla == "BackSpace":
                self._accion_estandar("borrar")
                return "break"
            if tecla == "Delete":
                self._accion_estandar("ce")
                return "break"
            if tecla == "Escape":
                self._accion_estandar("c")
                return "break"
            return None

        if vista == "cientifica":
            if car and car in "0123456789+-*/()":
                self._accion_cientifica(car)
                return "break"
            if car in (",", "."):
                self._accion_cientifica(".")
                return "break"
            if tecla in ("Return", "KP_Enter", "equal"):
                self._accion_cientifica("igual")
                return "break"
            if tecla == "BackSpace":
                self._accion_cientifica("borrar")
                return "break"
            if tecla == "Escape":
                self._accion_cientifica("c")
                return "break"
            return None

        if vista == "programador":
            # El botón "C" de Limpiar y el dígito hexadecimal "C" comparten
            # letra en pantalla; por teclado la tecla "c" no se asigna a
            # ninguno de los dos para no generar ambigüedad (ambos siguen
            # disponibles con el mouse).
            if car.isdigit():
                self._accion_programador(car)
                return "break"
            if car.lower() in ("a", "b", "d", "e", "f"):
                self._accion_programador(car.upper())
                return "break"
            if car == "/":
                self._accion_programador("/")
                return "break"
            if tecla in ("Return", "KP_Enter", "equal"):
                self._accion_programador("igual")
                return "break"
            if tecla == "BackSpace":
                self._accion_programador("borrar")
                return "break"
            if tecla == "Escape":
                self._accion_programador("c")
                return "break"
            return None

        if vista == "moneda":
            if car.isdigit():
                self._accion_moneda(car)
                return "break"
            if car in (",", "."):
                self._accion_moneda(",")
                return "break"
            if tecla == "BackSpace":
                self._accion_moneda("borrar")
                return "break"
            if tecla in ("Delete", "Escape"):
                self._accion_moneda("ce")
                return "break"
            return None

        if vista in UNIDADES and self._accion_convertidor_actual:
            accion_fn = self._accion_convertidor_actual
            if car.isdigit():
                accion_fn(car)
                return "break"
            if car in (",", "."):
                accion_fn(",")
                return "break"
            if tecla == "BackSpace":
                accion_fn("borrar")
                return "break"
            if tecla in ("Delete", "Escape"):
                accion_fn("ce")
                return "break"
            return None

        return None

    # ───────────────────────── Encabezado ───────────────────────────
    def _construir_encabezado(self):
        ALTO = 46
        self._encabezado = tk.Frame(self, bg=FONDO_MENU, height=ALTO)
        self._encabezado.grid(row=0, column=0, sticky="ew")
        self._encabezado.grid_propagate(False)

        borde_inferior = tk.Frame(self, bg=BORDE, height=1)
        borde_inferior.grid(row=0, column=0, sticky="sew")

        self._lbl_hamburguesa = tk.Label(
            self._encabezado, text="☰", font=("Segoe UI", 15),
            bg=FONDO_MENU, fg=NEGRO, cursor="hand2", padx=14)
        self._lbl_hamburguesa.pack(side="left", fill="y")
        self._lbl_hamburguesa.bind("<Button-1>", lambda e: self._alternar_menu())

        self._titulo_var = tk.StringVar(value="Estándar")
        tk.Label(self._encabezado, textvariable=self._titulo_var,
                 font=("Segoe UI", 13, "bold"), bg=FONDO_MENU, fg=NEGRO).pack(
            side="left", padx=(2, 0))

        self._lbl_historial = tk.Label(
            self._encabezado, text="🕐", font=("Segoe UI", 13),
            bg=FONDO_MENU, fg=NEGRO, cursor="hand2", padx=12)
        self._lbl_historial.pack(side="right", fill="y")
        self._lbl_historial.bind("<Button-1>", lambda e: self._alternar_historial())

        self._lbl_expandir = tk.Label(
            self._encabezado, text="⤢", font=("Segoe UI", 12),
            bg=FONDO_MENU, fg=NEGRO, cursor="hand2", padx=10)
        self._lbl_expandir.pack(side="right", fill="y")
        self._lbl_expandir.bind("<Button-1>", lambda e: self._alternar_siempre_encima())

        for w in (self._lbl_hamburguesa, self._lbl_historial, self._lbl_expandir):
            w.bind("<Enter>", lambda e, w=w: w.configure(bg=HOVER))
            w.bind("<Leave>", lambda e, w=w: w.configure(
                bg=HOVER if (w is self._lbl_expandir and self._siempre_encima) else FONDO_MENU))

    def _alternar_siempre_encima(self):
        self._siempre_encima = not self._siempre_encima
        try:
            self.attributes("-topmost", self._siempre_encima)
        except Exception:
            pass
        self._lbl_expandir.configure(
            bg=HOVER if self._siempre_encima else FONDO_MENU,
            fg=AZUL if self._siempre_encima else NEGRO)

    # ─────────────────── Menú lateral (overlay desplegable) ──────────────
    def _construir_overlay_menu(self):
        self._overlay_menu = tk.Frame(self, bg=FONDO_MENU, bd=0,
                                       highlightthickness=1, highlightbackground=BORDE)

        contenedor = tk.Frame(self._overlay_menu, bg=FONDO_MENU)
        contenedor.pack(fill="both", expand=True)

        canvas = tk.Canvas(contenedor, bg=FONDO_MENU, highlightthickness=0)
        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=canvas.yview)
        self._frame_scroll = tk.Frame(canvas, bg=FONDO_MENU)

        self._frame_scroll.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=self._frame_scroll, anchor="nw",
                              width=228)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Scroll con la rueda del mouse (Windows / Linux)
        def _en_rueda(event):
            if not self._overlay_menu_visible:
                return
            delta = -1 if event.num == 5 or event.delta < 0 else 1
            canvas.yview_scroll(-delta, "units")
        canvas.bind_all("<MouseWheel>", _en_rueda)
        canvas.bind_all("<Button-4>", _en_rueda)
        canvas.bind_all("<Button-5>", _en_rueda)

        self._agregar_seccion_menu("Calculadora", MENU_CALCULADORA)
        self._agregar_seccion_menu("Convertidor", MENU_CONVERTIDOR)

    def _agregar_seccion_menu(self, titulo, items):
        tk.Label(self._frame_scroll, text=titulo, bg=FONDO_MENU, fg=GRIS_TEXT,
                 font=("Segoe UI", 9, "bold"), anchor="w").pack(
            fill="x", padx=14, pady=(12, 4))
        for clave, etiqueta, icono in items:
            self._crear_boton_menu(clave, etiqueta, icono)

    def _crear_boton_menu(self, clave, etiqueta, icono):
        marco = tk.Frame(self._frame_scroll, bg=FONDO_MENU, cursor="hand2")
        marco.pack(fill="x", padx=6, pady=1)
        lbl = tk.Label(marco, text=f"{icono}   {etiqueta}", bg=FONDO_MENU,
                        fg=NEGRO, font=("Segoe UI", 10), anchor="w",
                        cursor="hand2", padx=10, pady=7)
        lbl.pack(fill="x")

        def _entrar(_e):
            if self._vista_actual != clave:
                marco.configure(bg=HOVER)
                lbl.configure(bg=HOVER)

        def _salir(_e):
            if self._vista_actual != clave:
                marco.configure(bg=FONDO_MENU)
                lbl.configure(bg=FONDO_MENU)

        marco.bind("<Enter>", _entrar)
        marco.bind("<Leave>", _salir)
        lbl.bind("<Enter>", _entrar)
        lbl.bind("<Leave>", _salir)
        marco.bind("<Button-1>", lambda e: self._seleccionar(clave))
        lbl.bind("<Button-1>", lambda e: self._seleccionar(clave))

        self._botones_menu[clave] = (marco, lbl)

    def _marcar_seleccion(self, clave):
        for k, (marco, lbl) in self._botones_menu.items():
            color = SELECCION if k == clave else FONDO_MENU
            marco.configure(bg=color)
            lbl.configure(bg=color)

    def _alternar_menu(self):
        if self._overlay_menu_visible:
            self._ocultar_menu()
        else:
            self._ocultar_historial()
            self.update_idletasks()
            alto = max(self.winfo_height() - 47, 100)
            self._overlay_menu.place(x=0, y=47, width=250, height=alto)
            self._overlay_menu.lift()
            self._overlay_menu_visible = True

    def _ocultar_menu(self):
        self._overlay_menu.place_forget()
        self._overlay_menu_visible = False

    # ─────────────────── Historial (overlay desplegable) ────────────────
    def _construir_overlay_historial(self):
        self._overlay_historial = tk.Frame(self, bg=FONDO_MENU, bd=0,
                                            highlightthickness=1, highlightbackground=BORDE)
        tk.Label(self._overlay_historial, text="Historial", bg=FONDO_MENU,
                 fg=NEGRO, font=("Segoe UI", 11, "bold"), anchor="w").pack(
            fill="x", padx=14, pady=(12, 6))
        self._frame_historial_items = tk.Frame(self._overlay_historial, bg=FONDO_MENU)
        self._frame_historial_items.pack(fill="both", expand=True, padx=6)

    def _alternar_historial(self):
        if self._vista_actual not in ("estandar", "cientifica"):
            return
        if self._overlay_historial_visible:
            self._ocultar_historial()
        else:
            self._ocultar_menu()
            self._refrescar_historial_ui()
            self.update_idletasks()
            alto = max(self.winfo_height() - 47, 100)
            ancho = min(280, self.winfo_width())
            self._overlay_historial.place(x=self.winfo_width() - ancho, y=47,
                                           width=ancho, height=alto)
            self._overlay_historial.lift()
            self._overlay_historial_visible = True

    def _ocultar_historial(self):
        self._overlay_historial.place_forget()
        self._overlay_historial_visible = False

    def _refrescar_historial_ui(self):
        for w in self._frame_historial_items.winfo_children():
            w.destroy()
        if not self._historial:
            tk.Label(self._frame_historial_items, text="No hay historial todavía",
                     bg=FONDO_MENU, fg=GRIS_TEXT, font=("Segoe UI", 9),
                     wraplength=220, justify="left").pack(anchor="w", pady=10)
            return
        for expresion, resultado in reversed(self._historial[-30:]):
            item = tk.Frame(self._frame_historial_items, bg=FONDO_MENU, cursor="hand2")
            item.pack(fill="x", pady=4)
            tk.Label(item, text=expresion, bg=FONDO_MENU, fg=GRIS_TEXT,
                     font=("Segoe UI", 8), anchor="e", justify="right").pack(fill="x")
            lbl_res = tk.Label(item, text=resultado, bg=FONDO_MENU, fg=NEGRO,
                                font=("Segoe UI", 12, "bold"), anchor="e")
            lbl_res.pack(fill="x")
            for w in (item, lbl_res):
                w.bind("<Button-1>", lambda e, r=resultado: self._usar_resultado_historial(r))

    def _usar_resultado_historial(self, resultado):
        if self._vista_actual == "estandar" and hasattr(self, "_pantalla_var"):
            self._pantalla_var.set(resultado)
            self._acumulado = None
            self._operador_pendiente = None
            self._reiniciar_en_proximo_digito = True
        elif self._vista_actual == "cientifica" and hasattr(self, "_pantalla_cien"):
            self._expresion = resultado.replace(",", ".")
            self._pantalla_cien.set(resultado)
        self._ocultar_historial()

    def _agregar_historial(self, expresion, resultado):
        self._historial.append((expresion, resultado))

    # ───────────────────────── Fila de memoria ──────────────────────────
    def _fila_memoria(self, parent, obtener_valor, establecer_valor):
        """Crea la fila MC / MR / M+ / M- / MS / M∨, igual que en la
        calculadora de Windows. `obtener_valor` debe devolver el número
        actual en pantalla (float); `establecer_valor` recibe el texto
        formateado a mostrar cuando se recupera la memoria."""
        fila = tk.Frame(parent, bg=FONDO)
        fila.pack(fill="x", pady=(2, 12))
        for i in range(6):
            fila.grid_columnconfigure(i, weight=1)

        especificaciones = [("MC", "mc"), ("MR", "mr"), ("M+", "mmas"),
                            ("M-", "mmenos"), ("MS", "ms"), ("M∨", "mver")]
        botones = {}
        for i, (texto, clave) in enumerate(especificaciones):
            lbl = tk.Label(fila, text=texto, bg=FONDO, fg=GRIS_TEXT,
                           font=("Segoe UI", 10), cursor="hand2")
            lbl.grid(row=0, column=i, sticky="nsew", ipady=4)
            lbl.bind("<Button-1>", lambda e, c=clave: self._accion_memoria(
                c, obtener_valor, establecer_valor))
            botones[clave] = lbl

        self._grupos_memoria.append(botones)
        self._actualizar_estado_memoria()
        return botones

    def _accion_memoria(self, clave, obtener_valor, establecer_valor):
        if clave == "mc":
            self._memoria = None
        elif clave == "mr" or clave == "mver":
            if self._memoria is not None:
                establecer_valor(_formatear_numero(self._memoria))
        elif clave == "mmas":
            self._memoria = (self._memoria or 0) + obtener_valor()
        elif clave == "mmenos":
            self._memoria = (self._memoria or 0) - obtener_valor()
        elif clave == "ms":
            self._memoria = obtener_valor()
        self._actualizar_estado_memoria()

    def _actualizar_estado_memoria(self):
        activo = self._memoria is not None
        color = NEGRO if activo else "#c7ccd4"
        for botones in self._grupos_memoria:
            for clave, lbl in botones.items():
                if not lbl.winfo_exists():
                    continue
                if clave in ("ms", "mmas", "mmenos"):
                    lbl.configure(fg=NEGRO)
                else:
                    lbl.configure(fg=color)

    # ───────────────────────── Panel de contenido ───────────────────────
    def _construir_area_contenido(self):
        self._panel_derecho = tk.Frame(self, bg=FONDO)
        self._panel_derecho.grid(row=1, column=0, sticky="nsew")

    def _limpiar_panel(self):
        for w in self._panel_derecho.winfo_children():
            w.destroy()
        self._grupos_memoria = []
        self._accion_convertidor_actual = None

    def _seleccionar(self, clave):
        self._vista_actual = clave
        self._marcar_seleccion(clave)
        self._limpiar_panel()
        self._ocultar_menu()
        self._ocultar_historial()
        self._titulo_var.set(ETIQUETAS_VISTA.get(clave, clave.capitalize()))
        self._lbl_historial.configure(
            fg=NEGRO if clave in ("estandar", "cientifica") else "#c7ccd4",
            cursor="hand2" if clave in ("estandar", "cientifica") else "arrow")

        constructores = {
            "estandar": self._vista_estandar,
            "cientifica": self._vista_cientifica,
            "grafica": self._vista_grafica,
            "programador": self._vista_programador,
            "fecha": self._vista_fecha,
            "moneda": self._vista_moneda,
        }
        if clave in constructores:
            constructores[clave]()
        elif clave in UNIDADES:
            self._vista_convertidor_generico(clave)

        # Devuelve el foco de teclado a la ventana (y no a un widget
        # puntual) para que los atajos numéricos sigan funcionando apenas
        # se cambia de calculadora/conversor, sin necesidad de hacer clic.
        self.after_idle(self.focus_set)

    # ═══════════════════════ ESTÁNDAR ═══════════════════════
    def _vista_estandar(self):
        marco = tk.Frame(self._panel_derecho, bg=FONDO)
        marco.pack(fill="both", expand=True, padx=14, pady=10)

        self._pantalla_var = tk.StringVar(value="0")
        tk.Label(marco, textvariable=self._pantalla_var, bg=FONDO, fg=NEGRO,
                 font=("Segoe UI", 34), anchor="e").pack(fill="x", pady=(10, 6))

        self._fila_memoria(
            marco,
            obtener_valor=lambda: _texto_a_float(self._pantalla_var.get()),
            establecer_valor=lambda t: (self._pantalla_var.set(t),
                                         setattr(self, "_reiniciar_en_proximo_digito", True)))

        botones_frame = tk.Frame(marco, bg=FONDO)
        botones_frame.pack(fill="both", expand=True)
        for i in range(6):
            botones_frame.grid_rowconfigure(i, weight=1)
        for i in range(4):
            botones_frame.grid_columnconfigure(i, weight=1)

        self._acumulado = None
        self._operador_pendiente = None
        self._reiniciar_en_proximo_digito = False

        filas = [
            [("%", "op_pct"), ("CE", "ce"), ("C", "c"), ("⌫", "borrar")],
            [("1/x", "inv"), ("x²", "cuad"), ("²√x", "raiz"), ("÷", "op_div")],
            [("7", "d7"), ("8", "d8"), ("9", "d9"), ("×", "op_mul")],
            [("4", "d4"), ("5", "d5"), ("6", "d6"), ("−", "op_sub")],
            [("1", "d1"), ("2", "d2"), ("3", "d3"), ("+", "op_sum")],
            [("+/-", "signo"), ("0", "d0"), (",", "coma"), ("=", "igual")],
        ]
        for r, fila in enumerate(filas):
            for c, (texto, accion) in enumerate(fila):
                self._boton_calc(botones_frame, texto, accion,
                                  self._accion_estandar).grid(
                    row=r, column=c, sticky="nsew", padx=3, pady=3)

    def _boton_calc(self, parent, texto, accion, manejador, destacado=False):
        bg = AZUL if destacado else BLANCO
        fg = BLANCO if destacado else NEGRO
        btn = tk.Button(parent, text=texto, font=("Segoe UI", 13),
                         bg=bg, fg=fg, relief="flat", bd=0,
                         activebackground=HOVER if not destacado else AZUL_OSC,
                         cursor="hand2", takefocus=0,
                         command=lambda: manejador(accion))
        return btn

    def _accion_estandar(self, accion):
        actual = self._pantalla_var.get()

        def num_actual():
            return _texto_a_float(actual)

        if accion.startswith("d"):
            digito = accion[1]
            if actual == "0" or self._reiniciar_en_proximo_digito:
                actual = digito
                self._reiniciar_en_proximo_digito = False
            else:
                actual += digito
            self._pantalla_var.set(actual)
            return

        if accion == "coma":
            if self._reiniciar_en_proximo_digito:
                actual = "0"
                self._reiniciar_en_proximo_digito = False
            if "," not in actual:
                self._pantalla_var.set(actual + ",")
            return

        if accion == "c":
            self._pantalla_var.set("0")
            self._acumulado = None
            self._operador_pendiente = None
            return

        if accion == "ce":
            self._pantalla_var.set("0")
            return

        if accion == "borrar":
            nuevo = actual[:-1] or "0"
            self._pantalla_var.set(nuevo)
            return

        if accion == "signo":
            valor = num_actual() * -1
            self._pantalla_var.set(_formatear_numero(valor))
            return

        if accion == "cuad":
            self._pantalla_var.set(_formatear_numero(num_actual() ** 2))
            self._reiniciar_en_proximo_digito = True
            return

        if accion == "raiz":
            try:
                self._pantalla_var.set(_formatear_numero(math.sqrt(num_actual())))
            except ValueError:
                self._pantalla_var.set("Error")
            self._reiniciar_en_proximo_digito = True
            return

        if accion == "inv":
            try:
                self._pantalla_var.set(_formatear_numero(1 / num_actual()))
            except ZeroDivisionError:
                self._pantalla_var.set("Error")
            self._reiniciar_en_proximo_digito = True
            return

        if accion == "op_pct":
            if self._acumulado is not None:
                valor = self._acumulado * (num_actual() / 100)
                self._pantalla_var.set(_formatear_numero(valor))
            return

        operadores = {"op_div": "÷", "op_mul": "×", "op_sub": "−", "op_sum": "+"}
        if accion in operadores:
            if self._acumulado is not None and not self._reiniciar_en_proximo_digito:
                self._aplicar_operacion(num_actual())
            else:
                self._acumulado = num_actual()
            self._operador_pendiente = operadores[accion]
            self._reiniciar_en_proximo_digito = True
            return

        if accion == "igual":
            expr = f"{_formatear_numero(self._acumulado)} {self._operador_pendiente} {_formatear_numero(num_actual())}" \
                if self._acumulado is not None and self._operador_pendiente else ""
            self._aplicar_operacion(num_actual())
            self._operador_pendiente = None
            self._reiniciar_en_proximo_digito = True
            if expr:
                self._agregar_historial(expr, self._pantalla_var.get())
            return

    def _aplicar_operacion(self, valor_actual):
        if self._acumulado is None or self._operador_pendiente is None:
            self._acumulado = valor_actual
            self._pantalla_var.set(_formatear_numero(valor_actual))
            return
        a, b, op = self._acumulado, valor_actual, self._operador_pendiente
        try:
            if op == "÷":
                resultado = a / b
            elif op == "×":
                resultado = a * b
            elif op == "−":
                resultado = a - b
            else:
                resultado = a + b
        except ZeroDivisionError:
            self._pantalla_var.set("Error")
            self._acumulado = None
            return
        self._pantalla_var.set(_formatear_numero(resultado))
        self._acumulado = resultado

    # ═══════════════════════ CIENTÍFICA ═══════════════════════
    def _vista_cientifica(self):
        marco = tk.Frame(self._panel_derecho, bg=FONDO)
        marco.pack(fill="both", expand=True, padx=14, pady=10)

        cabecera = tk.Frame(marco, bg=FONDO)
        cabecera.pack(fill="x")

        self._modo_grados = tk.BooleanVar(value=True)
        tk.Checkbutton(cabecera, text="DEG", variable=self._modo_grados,
                        bg=FONDO, onvalue=True, offvalue=False,
                        font=("Segoe UI", 9)).pack(side="right")

        self._expresion = ""
        self._pantalla_cien = tk.StringVar(value="0")
        tk.Label(marco, textvariable=self._pantalla_cien, bg=FONDO, fg=NEGRO,
                 font=("Segoe UI", 26), anchor="e", wraplength=480).pack(
            fill="x", pady=(10, 6))

        self._fila_memoria(
            marco,
            obtener_valor=lambda: _texto_a_float(self._pantalla_cien.get()),
            establecer_valor=lambda t: (setattr(self, "_expresion", t.replace(",", ".")),
                                         self._pantalla_cien.set(t)))

        botones_frame = tk.Frame(marco, bg=FONDO)
        botones_frame.pack(fill="both", expand=True)
        for i in range(7):
            botones_frame.grid_rowconfigure(i, weight=1)
        for i in range(5):
            botones_frame.grid_columnconfigure(i, weight=1)

        filas = [
            [("sin", "sin("), ("cos", "cos("), ("tan", "tan("), ("C", "c"), ("⌫", "borrar")],
            [("log", "log10("), ("ln", "log("), ("(", "("), (")", ")"), ("÷", "/")],
            [("x²", "**2_post"), ("√x", "sqrt("), ("7", "7"), ("8", "8"), ("9", "9")],
            [("xʸ", "**"), ("π", "pi"), ("4", "4"), ("5", "5"), ("6", "6")],
            [("mod", "%"), ("e", "e"), ("1", "1"), ("2", "2"), ("3", "3")],
            [("n!", "fact_post"), ("exp", "exp("), ("+/-", "signo"), ("0", "0"), (",", ".")],
            [("×", "*"), ("−", "-"), ("+", "+"), ("=", "igual"), ("", "")],
        ]
        for r, fila in enumerate(filas):
            for c, (texto, accion) in enumerate(fila):
                if not texto:
                    continue
                self._boton_calc(botones_frame, texto, accion,
                                  self._accion_cientifica).grid(
                    row=r, column=c, sticky="nsew", padx=3, pady=3)

    def _accion_cientifica(self, accion):
        if accion == "c":
            self._expresion = ""
            self._pantalla_cien.set("0")
            return
        if accion == "borrar":
            self._expresion = self._expresion[:-1]
            self._pantalla_cien.set(self._expresion or "0")
            return
        if accion == "signo":
            self._expresion = f"(-1*({self._expresion}))" if self._expresion else "-"
            self._pantalla_cien.set(self._expresion)
            return
        if accion == "**2_post":
            self._expresion += "**2"
            self._pantalla_cien.set(self._expresion)
            return
        if accion == "fact_post":
            self._expresion += "!"
            self._pantalla_cien.set(self._expresion)
            return
        if accion == "igual":
            self._evaluar_cientifica()
            return
        self._expresion += accion
        self._pantalla_cien.set(self._expresion)

    def _evaluar_cientifica(self):
        expr = self._expresion
        try:
            # Factorial: reemplaza "N!" por math.factorial(N)
            while "!" in expr:
                idx = expr.index("!")
                j = idx - 1
                while j >= 0 and (expr[j].isdigit() or expr[j] == "."):
                    j -= 1
                num = expr[j + 1:idx]
                expr = expr[:j + 1] + f"math.factorial(int({num}))" + expr[idx + 1:]

            grados = self._modo_grados.get()
            entorno = {
                "sin": (lambda x: math.sin(math.radians(x))) if grados else math.sin,
                "cos": (lambda x: math.cos(math.radians(x))) if grados else math.cos,
                "tan": (lambda x: math.tan(math.radians(x))) if grados else math.tan,
                "sqrt": math.sqrt, "log10": math.log10, "log": math.log,
                "exp": math.exp, "pi": math.pi, "e": math.e, "math": math,
            }
            resultado = eval(expr, {"__builtins__": {}}, entorno)
            expr_original = self._expresion
            self._expresion = _formatear_numero(float(resultado))
            self._pantalla_cien.set(self._expresion)
            self._agregar_historial(expr_original, self._expresion)
        except Exception:
            self._pantalla_cien.set("Error")
            self._expresion = ""

    # ═══════════════════════ PROGRAMADOR ═══════════════════════
    def _vista_programador(self):
        marco = tk.Frame(self._panel_derecho, bg=FONDO)
        marco.pack(fill="both", expand=True, padx=14, pady=10)

        self._valor_prog = 0
        marco_bases = tk.Frame(marco, bg=FONDO)
        marco_bases.pack(fill="x", pady=(14, 10))
        self._lbl_bases = {}
        for base in ("HEX", "DEC", "OCT", "BIN"):
            fila = tk.Frame(marco_bases, bg=FONDO)
            fila.pack(fill="x", pady=1)
            tk.Label(fila, text=base, width=5, anchor="w", bg=FONDO,
                     fg=GRIS_TEXT, font=("Segoe UI", 9)).pack(side="left")
            lbl = tk.Label(fila, text="0", anchor="e", bg=FONDO, fg=NEGRO,
                            font=("Consolas", 13))
            lbl.pack(side="right", fill="x", expand=True)
            self._lbl_bases[base] = lbl

        botones_frame = tk.Frame(marco, bg=FONDO)
        botones_frame.pack(fill="both", expand=True)
        for i in range(5):
            botones_frame.grid_rowconfigure(i, weight=1)
        for i in range(5):
            botones_frame.grid_columnconfigure(i, weight=1)

        filas = [
            [("<<", "shl"), (">>", "shr"), ("C", "c"), ("⌫", "borrar"), ("÷", "/")],
            [("A", "A"), ("B", "B"), ("7", "7"), ("8", "8"), ("9", "9")],
            [("C", "Chex"), ("D", "D"), ("4", "4"), ("5", "5"), ("6", "6")],
            [("E", "E"), ("F", "F"), ("1", "1"), ("2", "2"), ("3", "3")],
            [("AND", "and"), ("OR", "or"), ("XOR", "xor"), ("0", "0"), ("=", "igual")],
        ]
        self._prog_expr = ""
        for r, fila in enumerate(filas):
            for c, (texto, accion) in enumerate(fila):
                self._boton_calc(botones_frame, texto, accion,
                                  self._accion_programador).grid(
                    row=r, column=c, sticky="nsew", padx=3, pady=3)

    def _accion_programador(self, accion):
        if accion == "c":
            self._prog_expr = ""
        elif accion == "borrar":
            self._prog_expr = self._prog_expr[:-1]
        elif accion == "shl":
            self._prog_expr += "<<1"
        elif accion == "shr":
            self._prog_expr += ">>1"
        elif accion == "and":
            self._prog_expr += "&"
        elif accion == "or":
            self._prog_expr += "|"
        elif accion == "xor":
            self._prog_expr += "^"
        elif accion == "Chex":
            self._prog_expr += "C"
        elif accion == "igual":
            try:
                self._valor_prog = eval(self._prog_expr, {"__builtins__": {}}, {})
                self._prog_expr = str(self._valor_prog)
            except Exception:
                self._prog_expr = ""
                self._valor_prog = 0
        else:
            self._prog_expr += accion

        try:
            valor = eval(self._prog_expr, {"__builtins__": {}}, {}) if self._prog_expr else 0
            valor = int(valor)
        except Exception:
            valor = self._valor_prog

        self._valor_prog = valor
        self._lbl_bases["HEX"].configure(text=hex(valor)[2:].upper() if valor >= 0 else hex(valor).upper())
        self._lbl_bases["DEC"].configure(text=str(valor))
        self._lbl_bases["OCT"].configure(text=oct(valor)[2:] if valor >= 0 else oct(valor))
        self._lbl_bases["BIN"].configure(text=bin(valor)[2:] if valor >= 0 else bin(valor))

    # ═══════════════════════ CÁLCULO DE FECHA ═══════════════════════
    def _vista_fecha(self):
        marco = tk.Frame(self._panel_derecho, bg=FONDO)
        marco.pack(fill="both", expand=True, padx=14, pady=10)

        tk.Label(marco, text="Diferencia entre días", bg=FONDO, fg=GRIS_TEXT,
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(6, 6))

        hoy = datetime.date.today()
        self._fecha_desde = hoy
        self._fecha_hasta = hoy

        tk.Label(marco, text="Desde", bg=FONDO, fg=GRIS_TEXT,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(10, 2))
        self._lbl_desde = tk.Label(marco, text=_formatear_fecha_larga(hoy),
                                    bg=FONDO, fg=NEGRO, cursor="hand2",
                                    font=("Segoe UI", 12))
        self._lbl_desde.pack(anchor="w")
        self._lbl_desde.bind("<Button-1>", lambda e: self._elegir_fecha("desde"))

        tk.Label(marco, text="Hasta", bg=FONDO, fg=GRIS_TEXT,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(16, 2))
        self._lbl_hasta = tk.Label(marco, text=_formatear_fecha_larga(hoy),
                                    bg=FONDO, fg=NEGRO, cursor="hand2",
                                    font=("Segoe UI", 12))
        self._lbl_hasta.pack(anchor="w")
        self._lbl_hasta.bind("<Button-1>", lambda e: self._elegir_fecha("hasta"))

        tk.Label(marco, text="Diferencia", bg=FONDO, fg=GRIS_TEXT,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(20, 2))
        self._lbl_diferencia = tk.Label(marco, text="Mismas fechas", bg=FONDO,
                                         fg=NEGRO, font=("Segoe UI", 13, "bold"))
        self._lbl_diferencia.pack(anchor="w")

    def _elegir_fecha(self, cual):
        try:
            from widget_calendario import abrir_selector_fecha
        except Exception:
            return
        actual = self._fecha_desde if cual == "desde" else self._fecha_hasta

        def _al_elegir(fecha):
            if cual == "desde":
                self._fecha_desde = fecha
                self._lbl_desde.configure(text=_formatear_fecha_larga(fecha))
            else:
                self._fecha_hasta = fecha
                self._lbl_hasta.configure(text=_formatear_fecha_larga(fecha))
            self._actualizar_diferencia_fecha()

        abrir_selector_fecha(self, actual, _al_elegir)

    def _actualizar_diferencia_fecha(self):
        dias = (self._fecha_hasta - self._fecha_desde).days
        if dias == 0:
            texto = "Mismas fechas"
        else:
            texto = f"{abs(dias)} días"
        self._lbl_diferencia.configure(text=texto)

    # ═══════════════════════ GRÁFICA ═══════════════════════
    def _vista_grafica(self):
        marco = tk.Frame(self._panel_derecho, bg=FONDO)
        marco.pack(fill="both", expand=True, padx=14, pady=10)

        entrada_frame = tk.Frame(marco, bg=FONDO)
        entrada_frame.pack(fill="x", pady=(4, 8))
        tk.Label(entrada_frame, text="f(x) =", bg=FONDO, fg=NEGRO,
                 font=("Segoe UI", 11)).pack(side="left")
        self._entrada_funcion = tk.Entry(entrada_frame, font=("Segoe UI", 11))
        self._entrada_funcion.pack(side="left", fill="x", expand=True, padx=8)
        self._entrada_funcion.insert(0, "sin(x)")
        tk.Button(entrada_frame, text="Graficar", bg=AZUL, fg=BLANCO,
                  relief="flat", cursor="hand2",
                  command=self._graficar_funcion).pack(side="left")

        self._canvas_grafica = tk.Canvas(marco, bg=BLANCO, highlightthickness=1,
                                          highlightbackground=BORDE)
        self._canvas_grafica.pack(fill="both", expand=True, pady=(6, 0))
        self._canvas_grafica.bind("<Configure>", lambda e: self._graficar_funcion())
        self.after(80, self._graficar_funcion)

    def _graficar_funcion(self):
        cv = self._canvas_grafica
        if not cv.winfo_exists():
            return
        cv.delete("all")
        w = cv.winfo_width() or 400
        h = cv.winfo_height() or 300
        if w < 20 or h < 20:
            return

        rango = 10  # eje de -10 a 10
        margen = 30

        def px(x):
            return margen + (x + rango) / (2 * rango) * (w - 2 * margen)

        def py(y):
            return h - margen - (y + rango) / (2 * rango) * (h - 2 * margen)

        # Ejes
        cv.create_line(margen, h / 2, w - margen, h / 2, fill="#9ca3af")
        cv.create_line(w / 2, margen, w / 2, h - margen, fill="#9ca3af")
        cv.create_text(w - margen + 10, h / 2, text="x", fill="#6b7280")
        cv.create_text(w / 2, margen - 10, text="y", fill="#6b7280")

        expr = self._entrada_funcion.get() or "x"
        entorno = {
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "sqrt": math.sqrt, "log": math.log, "exp": math.exp,
            "pi": math.pi, "e": math.e, "abs": abs,
        }

        puntos = []
        pasos = 300
        for i in range(pasos + 1):
            x = -rango + (2 * rango) * i / pasos
            try:
                y = eval(expr, {"__builtins__": {}}, {**entorno, "x": x})
                if isinstance(y, complex) or abs(y) > rango * 3:
                    puntos.append(None)
                else:
                    puntos.append((px(x), py(y)))
            except Exception:
                puntos.append(None)

        segmento = []
        for p in puntos:
            if p is None:
                if len(segmento) > 1:
                    cv.create_line(*sum(segmento, ()), fill=AZUL, width=2, smooth=True)
                segmento = []
            else:
                segmento.append(p)
        if len(segmento) > 1:
            cv.create_line(*sum(segmento, ()), fill=AZUL, width=2, smooth=True)

    # ═══════════════════════ MONEDA ═══════════════════════
    def _vista_moneda(self):
        marco = tk.Frame(self._panel_derecho, bg=FONDO)
        marco.pack(fill="both", expand=True, padx=14, pady=10)

        self._tasa_moneda = None  # 1 origen = tasa * destino
        self._moneda_origen = tk.StringVar(value="USD")
        self._moneda_destino = tk.StringVar(value="PYG")
        self._monto_origen = tk.StringVar(value="0")
        self._monto_destino = tk.StringVar(value="0")

        etiquetas_moneda = [f"{c} - {NOMBRES_MONEDA[c].split(' - ')[-1]}" for c in MONEDAS_COMUNES]
        display_origen = tk.StringVar(value=etiquetas_moneda[MONEDAS_COMUNES.index(self._moneda_origen.get())])
        display_destino = tk.StringVar(value=etiquetas_moneda[MONEDAS_COMUNES.index(self._moneda_destino.get())])

        f1 = tk.Frame(marco, bg=FONDO)
        f1.pack(fill="x", pady=(16, 4))
        tk.Label(f1, textvariable=self._monto_origen, bg=FONDO, fg=NEGRO,
                 font=("Segoe UI", 22)).pack(side="left")
        combo1 = ttk.Combobox(f1, textvariable=display_origen,
                               values=etiquetas_moneda,
                               state="readonly", width=26)
        combo1.pack(side="right")

        f2 = tk.Frame(marco, bg=FONDO)
        f2.pack(fill="x", pady=(10, 4))
        tk.Label(f2, textvariable=self._monto_destino, bg=FONDO, fg=NEGRO,
                 font=("Segoe UI", 22)).pack(side="left")
        combo2 = ttk.Combobox(f2, textvariable=display_destino,
                               values=etiquetas_moneda,
                               state="readonly", width=26)
        combo2.pack(side="right")

        self._lbl_estado_moneda = tk.Label(marco, text="Obteniendo tipo de cambio...",
                                            bg=FONDO, fg=GRIS_TEXT, font=("Segoe UI", 9))
        self._lbl_estado_moneda.pack(anchor="w", pady=(10, 4))

        lbl_actualizar = tk.Label(marco, text="Actualizar tipos", bg=FONDO, fg=AZUL,
                                   font=("Segoe UI", 9, "underline"), cursor="hand2")
        lbl_actualizar.pack(anchor="w")
        lbl_actualizar.bind("<Button-1>", lambda e: self._obtener_tasa_moneda())

        teclado = tk.Frame(marco, bg=FONDO)
        teclado.pack(fill="both", expand=True, pady=(14, 0))
        for i in range(5):
            teclado.grid_rowconfigure(i, weight=1)
        for i in range(3):
            teclado.grid_columnconfigure(i, weight=1)

        self._boton_calc(teclado, "CE", "ce", self._accion_moneda).grid(
            row=0, column=0, columnspan=2, sticky="nsew", padx=3, pady=3)
        self._boton_calc(teclado, "⌫", "borrar", self._accion_moneda).grid(
            row=0, column=2, sticky="nsew", padx=3, pady=3)

        filas = [
            [("7", "7"), ("8", "8"), ("9", "9")],
            [("4", "4"), ("5", "5"), ("6", "6")],
            [("1", "1"), ("2", "2"), ("3", "3")],
            [("", ""), ("0", "0"), (",", ",")],
        ]
        for r, fila in enumerate(filas):
            for c, (texto, accion) in enumerate(fila):
                if not texto:
                    continue
                self._boton_calc(teclado, texto, accion,
                                  self._accion_moneda).grid(
                    row=r + 1, column=c, sticky="nsew", padx=3, pady=3)

        def _combo_cambiado(_e=None):
            self._moneda_origen.set(display_origen.get().split(" - ")[0])
            self._moneda_destino.set(display_destino.get().split(" - ")[0])
            self._obtener_tasa_moneda()
            self.after_idle(self.focus_set)
        combo1.bind("<<ComboboxSelected>>", _combo_cambiado)
        combo2.bind("<<ComboboxSelected>>", _combo_cambiado)

        self._obtener_tasa_moneda()

    def _accion_moneda(self, accion):
        actual = self._monto_origen.get()
        if accion == "ce":
            actual = "0"
        elif accion == "borrar":
            actual = actual[:-1] or "0"
        elif accion == ",":
            if "," not in actual:
                actual += ","
        else:
            actual = accion if actual == "0" else actual + accion
        self._monto_origen.set(actual)
        self._recalcular_moneda()

    def _obtener_tasa_moneda(self):
        origen = self._moneda_origen.get()
        destino = self._moneda_destino.get()
        self._lbl_estado_moneda.configure(text="Obteniendo tipo de cambio...")

        def _tarea():
            tasa = None
            try:
                if urlopen:
                    url = f"https://api.frankfurter.dev/v1/latest?base={origen}&symbols={destino}"
                    with urlopen(url, timeout=6) as resp:
                        datos = json.loads(resp.read().decode())
                        tasa = datos.get("rates", {}).get(destino)
            except Exception:
                tasa = None

            if tasa is None:
                # Tasas de referencia aproximadas de respaldo (offline)
                referencia_usd = {"USD": 1, "EUR": 0.87, "ARS": 1280, "BRL": 5.4, "PYG": 7300}
                if origen in referencia_usd and destino in referencia_usd:
                    tasa = referencia_usd[destino] / referencia_usd[origen]

            def _actualizar():
                if not self._lbl_estado_moneda.winfo_exists():
                    return
                if tasa is not None:
                    self._tasa_moneda = tasa
                    ahora = datetime.datetime.now().strftime("%d/%m/%Y a las %H:%M")
                    self._lbl_estado_moneda.configure(
                        text=f"1 {origen} = {_formatear_numero(tasa)} {destino}  ·  {ahora}")
                else:
                    self._lbl_estado_moneda.configure(text="No se pudo obtener el tipo de cambio")
                self._recalcular_moneda()

            self.after(0, _actualizar)

        threading.Thread(target=_tarea, daemon=True).start()

    def _recalcular_moneda(self):
        if self._tasa_moneda is None:
            return
        valor = _texto_a_float(self._monto_origen.get())
        self._monto_destino.set(_formatear_numero(valor * self._tasa_moneda))

    # ═══════════════════════ CONVERTIDOR GENÉRICO ═══════════════════════
    def _vista_convertidor_generico(self, clave):
        info = UNIDADES[clave]
        unidades = info["unidades"]
        nombres = list(unidades.keys())

        marco = tk.Frame(self._panel_derecho, bg=FONDO)
        marco.pack(fill="both", expand=True, padx=14, pady=10)

        origen_var = tk.StringVar(value=nombres[0])
        destino_var = tk.StringVar(value=nombres[1] if len(nombres) > 1 else nombres[0])
        monto_var = tk.StringVar(value="0")
        resultado_var = tk.StringVar(value="0")

        f1 = tk.Frame(marco, bg=FONDO)
        f1.pack(fill="x", pady=(6, 4))
        tk.Label(f1, textvariable=monto_var, bg=FONDO, fg=NEGRO,
                 font=("Segoe UI", 22)).pack(side="left")
        combo1 = ttk.Combobox(f1, textvariable=origen_var, values=nombres,
                               state="readonly", width=22)
        combo1.pack(side="right")

        f2 = tk.Frame(marco, bg=FONDO)
        f2.pack(fill="x", pady=(10, 4))
        tk.Label(f2, textvariable=resultado_var, bg=FONDO, fg=NEGRO,
                 font=("Segoe UI", 22)).pack(side="left")
        combo2 = ttk.Combobox(f2, textvariable=destino_var, values=nombres,
                               state="readonly", width=22)
        combo2.pack(side="right")

        lbl_referencia = None
        if clave in CATEGORIAS_CON_REFERENCIA:
            tk.Label(marco, text="Prácticamente igual que", bg=FONDO, fg=GRIS_TEXT,
                      font=("Segoe UI", 9)).pack(anchor="w", pady=(12, 0))
            lbl_referencia = tk.Label(marco, text="", bg=FONDO, fg=NEGRO,
                                       font=("Segoe UI", 11, "bold"),
                                       anchor="w", justify="left", wraplength=190)
            lbl_referencia.pack(anchor="w")

        teclado = tk.Frame(marco, bg=FONDO)
        teclado.pack(fill="both", expand=True, pady=(20, 0))
        for i in range(5):
            teclado.grid_rowconfigure(i, weight=1)
        for i in range(3):
            teclado.grid_columnconfigure(i, weight=1)

        def _convertir(*_):
            valor = _texto_a_float(monto_var.get())
            if clave == "temperatura":
                resultado = self._convertir_temperatura(valor, origen_var.get(), destino_var.get())
            else:
                base_origen = unidades[origen_var.get()]
                base_destino = unidades[destino_var.get()]
                resultado = valor * base_origen / base_destino
            resultado_var.set(_formatear_numero(resultado))

            if lbl_referencia is not None:
                otras = [u for u in nombres if u not in (origen_var.get(), destino_var.get())]
                partes = []
                for u in otras:
                    if clave == "temperatura":
                        conv = self._convertir_temperatura(valor, origen_var.get(), u)
                    else:
                        base_origen = unidades[origen_var.get()]
                        conv = valor * base_origen / unidades[u]
                    partes.append(f"{_formatear_numero(conv)} {NOMBRES_CORTOS.get(u, u)}")
                lbl_referencia.configure(text="\n".join(partes))

        def _accion(accion):
            actual = monto_var.get()
            if accion == "ce":
                actual = "0"
            elif accion == "borrar":
                actual = actual[:-1] or "0"
            elif accion == ",":
                if "," not in actual:
                    actual += ","
            else:
                actual = accion if actual == "0" else actual + accion
            monto_var.set(actual)
            _convertir()

        # Se guarda la referencia para que el manejador de teclado
        # (_on_key) pueda reutilizar esta misma lógica de este conversor.
        self._accion_convertidor_actual = _accion

        self._boton_calc(teclado, "CE", "ce", _accion).grid(
            row=0, column=0, columnspan=2, sticky="nsew", padx=3, pady=3)
        self._boton_calc(teclado, "⌫", "borrar", _accion).grid(
            row=0, column=2, sticky="nsew", padx=3, pady=3)

        filas = [
            [("7", "7"), ("8", "8"), ("9", "9")],
            [("4", "4"), ("5", "5"), ("6", "6")],
            [("1", "1"), ("2", "2"), ("3", "3")],
            [("", ""), ("0", "0"), (",", ",")],
        ]
        for r, fila in enumerate(filas):
            for c, (texto, accion) in enumerate(fila):
                if not texto:
                    continue
                self._boton_calc(teclado, texto, accion, _accion).grid(
                    row=r + 1, column=c, sticky="nsew", padx=3, pady=3)

        combo1.bind("<<ComboboxSelected>>", lambda e: (_convertir(), self.after_idle(self.focus_set)))
        combo2.bind("<<ComboboxSelected>>", lambda e: (_convertir(), self.after_idle(self.focus_set)))

        _convertir()

    def _convertir_temperatura(self, valor, origen, destino):
        # Primero a Celsius
        if origen == "Celsius":
            c = valor
        elif origen == "Fahrenheit":
            c = (valor - 32) * 5 / 9
        else:  # Kelvin
            c = valor - 273.15
        # Luego de Celsius a destino
        if destino == "Celsius":
            return c
        elif destino == "Fahrenheit":
            return c * 9 / 5 + 32
        else:
            return c + 273.15


# El diccionario de temperatura usa nombres especiales, se agrega aparte
UNIDADES["temperatura"] = {
    "base": "c",
    "unidades": {"Celsius": 1, "Fahrenheit": 1, "Kelvin": 1},  # factores no aplican, ver método especial
}


def abrir_calculadora(parent):
    """Punto de entrada: abre la ventana de la calculadora."""
    VentanaCalculadora(parent)
