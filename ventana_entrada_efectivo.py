"""
ventana_entrada_efectivo.py
Ventana "Entrada de Efectivo" (atajo F7 desde la pantalla de Ventas):
permite registrar un ingreso de dinero a la caja (ej. un aporte o
reposición inicial), con Importe y Motivo. Se suma automáticamente al
'Dinero en Caja' del día y queda reflejado en el Resumen de Ventas y
en el Reporte General.
"""
import tkinter as tk
from tkinter import messagebox

from models_ventas import registrar_entrada_efectivo
from utilidades_ui import forzar_mayusculas, ajustar_tamaño_ventana

AZUL_RIBBON = "#1d5fd6"
GRIS_FONDO = "#f4f5f7"


class VentanaEntradaEfectivo(tk.Toplevel):
    def __init__(self, parent, usuario_actual, on_guardado=None):
        super().__init__(parent)
        self.usuario_actual = usuario_actual
        self.on_guardado = on_guardado

        self.title("Entrada de Efectivo")
        self.minsize(320, 280)
        self.configure(bg="white")
        self.grab_set()

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_barra_titulo()
        self._construir_formulario()
        ajustar_tamaño_ventana(self, ancho_min=320, alto_min=280)

    def _construir_barra_titulo(self):
        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text="Entrada de Efectivo", font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

    def _construir_formulario(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=1, column=0, sticky="nsew", padx=20, pady=15)

        tk.Label(contenedor, text="Importe:", font=("Segoe UI", 9, "bold"), bg="white").pack(
            anchor="w", pady=(0, 2))
        self.var_importe = tk.StringVar()
        entry_importe = tk.Entry(contenedor, textvariable=self.var_importe, font=("Segoe UI", 11))
        entry_importe.pack(fill="x")
        entry_importe.focus()

        tk.Label(contenedor, text="Motivo:", font=("Segoe UI", 9, "bold"), bg="white").pack(
            anchor="w", pady=(14, 2))
        self.var_motivo = tk.StringVar(value="Entrada de Efectivo")
        entry_motivo = tk.Entry(contenedor, textvariable=self.var_motivo, font=("Segoe UI", 10))
        entry_motivo.pack(fill="x")
        forzar_mayusculas(entry_motivo, self.var_motivo)

        frame_botones = tk.Frame(contenedor, bg="white")
        frame_botones.pack(fill="x", pady=(25, 0))
        tk.Button(frame_botones, text="✔ Aceptar", font=("Segoe UI", 10, "bold"), bg="white",
                  fg="#16a34a", relief="solid", bd=1, padx=14, pady=8, cursor="hand2",
                  command=self._aceptar).pack(side="left", padx=(0, 8))
        tk.Button(frame_botones, text="✕ Cancelar", font=("Segoe UI", 10, "bold"), bg="white",
                  fg="#dc2626", relief="solid", bd=1, padx=14, pady=8, cursor="hand2",
                  command=self.destroy).pack(side="left")

        entry_importe.bind("<Return>", lambda e: self._aceptar())
        entry_motivo.bind("<Return>", lambda e: self._aceptar())

    def _aceptar(self):
        texto_importe = self.var_importe.get().strip().replace(",", ".").replace("Gs.", "")
        try:
            importe = float(texto_importe)
        except ValueError:
            messagebox.showerror("Importe inválido", "Ingresa un monto numérico válido.")
            return

        ok, msg = registrar_entrada_efectivo(importe, self.var_motivo.get(), self.usuario_actual["id"])
        if ok:
            if self.on_guardado:
                self.on_guardado()
            self.destroy()
        else:
            messagebox.showerror("Error", msg)
