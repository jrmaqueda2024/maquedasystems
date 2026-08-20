"""
ventana_idioma.py
Módulo "Idioma": permite elegir el idioma de la interfaz del sistema
(menús, botones, títulos) entre los idiomas soportados. Es una
configuración del SISTEMA (una sola, no por usuario) y NO traduce los
datos ya cargados (nombres de clientes, productos, observaciones, etc.),
solo los textos fijos de la interfaz.

El cambio se aplica la próxima vez que se inicia sesión (para no tener
que reconstruir en caliente cada pantalla ya abierta).
"""
import tkinter as tk
from tkinter import messagebox

from models_idioma import obtener_idioma_actual, guardar_idioma
from traducciones import IDIOMAS, t

AZUL_RIBBON = "#1d5fd6"
GRIS_FONDO = "#f4f5f7"
GRIS_BORDE = "#e2e8f0"
VERDE = "#16a34a"
BLANCO = "#ffffff"

ORDEN_IDIOMAS = ["es", "gn", "pt", "en", "ru", "zh", "ko", "uk", "ar"]
BANDERAS = {
    "es": "🇵🇾", "gn": "🇵🇾", "pt": "🇧🇷", "en": "🇺🇸",
    "ru": "🇷🇺", "zh": "🇨🇳", "ko": "🇰🇷", "uk": "🇺🇦", "ar": "🇸🇦",
}


class PanelIdioma(tk.Frame):
    def __init__(self, parent, usuario_actual):
        super().__init__(parent, bg=GRIS_FONDO)
        self.usuario_actual = usuario_actual
        self.var_idioma = tk.StringVar(value=obtener_idioma_actual())
        self._construir_ui()

    def _construir_ui(self):
        encabezado = tk.Frame(self, bg=AZUL_RIBBON, height=54)
        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)
        tk.Label(encabezado, text=t("idioma_titulo"),
                 font=("Segoe UI", 15, "bold"), bg=AZUL_RIBBON, fg=BLANCO
                 ).pack(side="left", padx=20, pady=12)

        aviso = tk.Frame(self, bg="#fefce8")
        aviso.pack(fill="x")
        tk.Frame(aviso, bg="#fbbf24", width=4).pack(side="left", fill="y")
        tk.Label(aviso,
                 text="ℹ  Esto cambia el idioma de los menús, botones y títulos del sistema "
                      "para TODOS los usuarios. No traduce los datos que ya cargaste (nombres "
                      "de clientes, productos, observaciones, etc.) — para traducir un texto "
                      "puntual, usá el Asistente IA. El cambio se aplica la próxima vez que "
                      "se inicia sesión. Nota: en árabe (idioma de derecha a izquierda) el "
                      "texto se lee correctamente pero queda alineado a la izquierda, por una "
                      "limitación de la librería gráfica usada.",
                 font=("Segoe UI", 8, "italic"), bg="#fefce8", fg="#92400e",
                 justify="left", wraplength=900, padx=10, pady=8).pack(side="left", fill="x", expand=True)

        contenedor = tk.Frame(self, bg=GRIS_FONDO)
        contenedor.pack(fill="both", expand=True, padx=30, pady=20)

        tk.Label(contenedor, text=t("idioma_elegir"),
                 font=("Segoe UI", 11, "bold"), bg=GRIS_FONDO).pack(anchor="w", pady=(0, 12))

        self.tarjetas = {}
        COLUMNAS = 5
        fila_idiomas = tk.Frame(contenedor, bg=GRIS_FONDO)
        fila_idiomas.pack(fill="x")
        for col in range(COLUMNAS):
            fila_idiomas.grid_columnconfigure(col, weight=1)
        for i, clave in enumerate(ORDEN_IDIOMAS):
            fila, columna = divmod(i, COLUMNAS)
            self._tarjeta_idioma(fila_idiomas, clave, fila, columna)

        tk.Button(contenedor, text=t("idioma_aplicar"), font=("Segoe UI", 10, "bold"),
                  bg=AZUL_RIBBON, fg=BLANCO, relief="flat", padx=18, pady=10, cursor="hand2",
                  activebackground="#163d8c", activeforeground=BLANCO,
                  command=self._guardar).pack(anchor="w", pady=(24, 0))

    def _tarjeta_idioma(self, parent, clave: str, fila: int, columna: int):
        es_actual = (self.var_idioma.get() == clave)
        card = tk.Frame(parent, bg="#e0f2fe" if es_actual else BLANCO,
                        relief="solid", bd=2 if es_actual else 1,
                        highlightbackground=AZUL_RIBBON if es_actual else GRIS_BORDE,
                        cursor="hand2")
        card.grid(row=fila, column=columna, sticky="nsew", padx=6, pady=6, ipady=14)
        self.tarjetas[clave] = card

        def _elegir(event=None, c=clave):
            self.var_idioma.set(c)
            for k, w in self.tarjetas.items():
                activo = (k == c)
                w.configure(bg="#e0f2fe" if activo else BLANCO, bd=2 if activo else 1,
                           highlightbackground=AZUL_RIBBON if activo else GRIS_BORDE)
                for hijo in w.winfo_children():
                    hijo.configure(bg="#e0f2fe" if activo else BLANCO)

        card.bind("<Button-1>", _elegir)
        lbl_bandera = tk.Label(card, text=BANDERAS.get(clave, "🌐"), font=("Segoe UI", 28),
                               bg=card.cget("bg"))
        lbl_bandera.pack(pady=(4, 6))
        lbl_bandera.bind("<Button-1>", _elegir)
        lbl_nombre = tk.Label(card, text=IDIOMAS[clave], font=("Segoe UI", 10, "bold"),
                              bg=card.cget("bg"))
        lbl_nombre.pack()
        lbl_nombre.bind("<Button-1>", _elegir)
        if es_actual:
            lbl_check = tk.Label(card, text=t("idioma_actual_badge"), font=("Segoe UI", 8, "bold"),
                                 bg=card.cget("bg"), fg=VERDE)
            lbl_check.pack(pady=(4, 0))
            lbl_check.bind("<Button-1>", _elegir)

    def _guardar(self):
        ok, msg = guardar_idioma(self.var_idioma.get())
        if ok:
            messagebox.showinfo(
                "Idioma actualizado",
                f"{msg}\n\nCerrá sesión y volvé a entrar para ver la interfaz completa en "
                f"{IDIOMAS[self.var_idioma.get()]}.",
                parent=self,
            )
        else:
            messagebox.showerror("Error", msg, parent=self)
