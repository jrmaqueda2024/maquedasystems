"""
ventana_ver_imagen.py
Ventana simple que muestra la imagen adjunta de un producto, ajustada
(estirada) al tamaño de la ventana sin deformarse, con opción de
redimensionar la ventana para ver la imagen más grande.
"""
import tkinter as tk
import os

try:
    from PIL import Image, ImageTk
    PIL_DISPONIBLE = True
except ImportError:
    PIL_DISPONIBLE = False

AZUL_RIBBON = "#1d5fd6"


class VentanaVerImagen(tk.Toplevel):
    def __init__(self, parent, ruta_imagen: str, nombre_producto: str = ""):
        super().__init__(parent)
        self.ruta_imagen = ruta_imagen
        self.imagen_tk = None  # referencia viva, necesaria para que Tkinter no la recolecte

        self.title(f"Imagen — {nombre_producto}" if nombre_producto else "Imagen del producto")
        self.geometry("520x560")
        self.minsize(300, 340)
        self.configure(bg="white")
        self.grab_set()

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_barra_titulo(nombre_producto)
        self._construir_area_imagen()

        self.bind("<Configure>", self._al_redimensionar)
        self._mostrar_imagen()

    def _construir_barra_titulo(self, nombre_producto):
        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        texto = f"📎 {nombre_producto}" if nombre_producto else "📎 Imagen del producto"
        tk.Label(barra, text=texto, font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

    def _construir_area_imagen(self):
        self.label_imagen = tk.Label(self, bg="#f4f5f7")
        self.label_imagen.grid(row=1, column=0, sticky="nsew")

    def _al_redimensionar(self, event):
        # Vuelve a escalar la imagen cada vez que el usuario cambia el
        # tamaño de la ventana, para que siempre se "estire" ocupando el
        # espacio disponible sin deformarse.
        if event.widget is self:
            self._mostrar_imagen()

    def _mostrar_imagen(self):
        if not self.ruta_imagen or not os.path.exists(self.ruta_imagen):
            self.label_imagen.config(
                image="", text="No se encontró el archivo de imagen.\n\n" + (self.ruta_imagen or ""),
                font=("Segoe UI", 9), fg="#888", compound="none",
            )
            return

        if not PIL_DISPONIBLE:
            self.label_imagen.config(
                image="",
                text="Para previsualizar imágenes se necesita instalar 'Pillow'.\n\n"
                     "Ejecuta: pip install Pillow\n\n"
                     f"Archivo: {self.ruta_imagen}",
                font=("Segoe UI", 9), fg="#888",
            )
            return

        ancho_disponible = max(self.label_imagen.winfo_width(), 300)
        alto_disponible = max(self.label_imagen.winfo_height(), 300)

        try:
            imagen = Image.open(self.ruta_imagen)
        except Exception as e:
            self.label_imagen.config(image="", text=f"No se pudo abrir la imagen:\n{e}",
                                     font=("Segoe UI", 9), fg="#c00")
            return

        # Escala manteniendo proporción (no deforma), ocupando el máximo
        # espacio posible dentro del área disponible ("estirar" sin recortar).
        ancho_original, alto_original = imagen.size
        factor = min(ancho_disponible / ancho_original, alto_disponible / alto_original)
        nuevo_ancho = max(1, int(ancho_original * factor))
        nuevo_alto = max(1, int(alto_original * factor))

        imagen_redimensionada = imagen.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)
        self.imagen_tk = ImageTk.PhotoImage(imagen_redimensionada)
        self.label_imagen.config(image=self.imagen_tk, text="")
