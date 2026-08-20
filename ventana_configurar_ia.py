"""
ventana_configurar_ia.py
Ventana para configurar el proveedor de IA (OpenAI, Anthropic, u otro
compatible) que usa el módulo Asistente IA: proveedor, clave de API y
modelo. Incluye un botón "Probar conexión" para verificar que la clave
funciona antes de guardarla, sin tener que ir al chat a descubrirlo.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading

from models_ia import (
    obtener_configuracion_ia, guardar_configuracion_ia,
    eliminar_configuracion_ia, probar_conexion, PROVEEDORES,
)
from utilidades_ui import ajustar_tamaño_ventana

AZUL_RIBBON = "#1d5fd6"
GRIS_FONDO = "#f4f5f7"
VERDE = "#16a34a"
ROJO = "#dc2626"

ORDEN_PROVEEDORES = ["openai", "anthropic", "personalizado"]


class VentanaConfigurarIA(tk.Toplevel):
    def __init__(self, parent, on_guardado=None):
        super().__init__(parent)
        self.on_guardado = on_guardado
        self._hay_config_actual = obtener_configuracion_ia() is not None

        self.title("Configurar Asistente IA")
        self.minsize(480, 600)
        self.configure(bg="white")
        self.grab_set()

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_barra_titulo()
        self._construir_formulario()
        self._cargar_configuracion_actual()
        ajustar_tamaño_ventana(self, ancho_min=480, alto_min=600)

    def _construir_barra_titulo(self):
        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text="🤖 Configurar Asistente IA", font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

    def _construir_formulario(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=1, column=0, sticky="nsew", padx=20, pady=15)

        if self._hay_config_actual:
            barra_actual = tk.Frame(contenedor, bg="#e0f2fe", relief="solid", bd=1)
            barra_actual.pack(fill="x", pady=(0, 12))
            config_actual = obtener_configuracion_ia()
            etiqueta_prov = PROVEEDORES.get(config_actual["proveedor"], {}).get(
                "etiqueta", config_actual["proveedor"])
            tk.Label(barra_actual, text=f"✔ Configurado: {etiqueta_prov} ({config_actual['modelo']})",
                     font=("Segoe UI", 9, "bold"), bg="#e0f2fe", fg="#075985", wraplength=300,
                     justify="left").pack(side="left", padx=10, pady=8)
            tk.Button(barra_actual, text="✕ Quitar configuración", font=("Segoe UI", 8, "bold"),
                      bg="white", relief="solid", bd=1, cursor="hand2",
                      command=self._quitar_configuracion_actual).pack(side="right", padx=10, pady=6)

        aviso = tk.Frame(contenedor, bg="#fefce8", relief="solid", bd=1)
        aviso.pack(fill="x", pady=(0, 12))
        tk.Label(aviso,
                 text="⚠ El uso del Asistente IA tiene un costo real, cobrado por el proveedor "
                      "elegido según la cantidad de texto enviado/recibido. MaquedaSystems no "
                      "cobra nada por esto ni administra el pago — se gestiona directamente en "
                      "la cuenta que crees en el proveedor.",
                 font=("Segoe UI", 8), bg="#fefce8", fg="#92400e", justify="left",
                 wraplength=420, padx=10, pady=8).pack(anchor="w")

        # --- Selector de proveedor ---
        tk.Label(contenedor, text="Proveedor de IA:", font=("Segoe UI", 9, "bold"), bg="white").pack(
            anchor="w", pady=(5, 2))
        self.var_proveedor = tk.StringVar()
        self.combo_proveedor = ttk.Combobox(
            contenedor, textvariable=self.var_proveedor, state="readonly", font=("Segoe UI", 10),
            values=[PROVEEDORES[clave]["etiqueta"] for clave in ORDEN_PROVEEDORES],
        )
        self.combo_proveedor.pack(anchor="w", fill="x")
        self.combo_proveedor.bind("<<ComboboxSelected>>", lambda e: self._al_cambiar_proveedor())

        # --- Caja de ayuda (cambia según el proveedor elegido) ---
        self.caja_ayuda = tk.Frame(contenedor, bg="#fef3c7", relief="solid", bd=1)
        self.caja_ayuda.pack(fill="x", pady=(10, 15))
        self.label_ayuda = tk.Label(self.caja_ayuda, text="", font=("Segoe UI", 8), bg="#fef3c7",
                                    fg="#92400e", justify="left", wraplength=420)
        self.label_ayuda.pack(padx=10, pady=8, anchor="w")

        # --- URL base (solo para "personalizado") ---
        tk.Label(contenedor, text="URL base de la API (solo 'Otro proveedor'):",
                 font=("Segoe UI", 9, "bold"), bg="white").pack(anchor="w", pady=(0, 2))
        self.var_url_base = tk.StringVar()
        self.entry_url_base = tk.Entry(contenedor, textvariable=self.var_url_base,
                                       font=("Segoe UI", 9))
        self.entry_url_base.pack(anchor="w", fill="x")
        tk.Label(contenedor, text="Ej: https://api.deepseek.com/v1  (sin '/chat/completions' al final)",
                 font=("Segoe UI", 7, "italic"), bg="white", fg="#6b7280").pack(anchor="w", pady=(2, 10))

        # --- Clave de API ---
        tk.Label(contenedor, text="Clave de API:", font=("Segoe UI", 9, "bold"),
                 bg="white").pack(anchor="w", pady=(2, 2))
        self.var_api_key = tk.StringVar()
        self.entry_api_key = tk.Entry(contenedor, textvariable=self.var_api_key,
                                      font=("Segoe UI", 10), width=40, show="•")
        self.entry_api_key.pack(anchor="w", fill="x")

        self.var_mostrar = tk.BooleanVar(value=False)
        tk.Checkbutton(contenedor, text="Mostrar clave", variable=self.var_mostrar,
                       font=("Segoe UI", 8), bg="white", command=self._toggle_mostrar_clave
                       ).pack(anchor="w", pady=(4, 0))

        # --- Modelo ---
        tk.Label(contenedor, text="Modelo:", font=("Segoe UI", 9, "bold"),
                 bg="white").pack(anchor="w", pady=(12, 2))
        self.var_modelo = tk.StringVar()
        self.combo_modelo = ttk.Combobox(contenedor, textvariable=self.var_modelo,
                                         font=("Segoe UI", 10))
        self.combo_modelo.pack(anchor="w", fill="x")
        tk.Label(contenedor,
                 text="Los modelos '...-mini'/'haiku' son los más económicos y alcanzan de sobra "
                      "para este asistente.",
                 font=("Segoe UI", 7, "italic"), bg="white", fg="#6b7280",
                 wraplength=420, justify="left").pack(anchor="w", pady=(2, 0))

        # --- Probar conexión ---
        self.label_resultado_prueba = tk.Label(contenedor, text="", font=("Segoe UI", 8, "bold"),
                                               bg="white", wraplength=420, justify="left")
        self.label_resultado_prueba.pack(anchor="w", pady=(10, 0))

        frame_botones = tk.Frame(contenedor, bg="white")
        frame_botones.pack(fill="x", pady=(16, 0))
        tk.Button(frame_botones, text="🔌 Probar Conexión", font=("Segoe UI", 9, "bold"),
                  bg="white", fg="#333", relief="solid", bd=1, padx=12, pady=7, cursor="hand2",
                  command=self._probar_conexion).pack(side="left")
        tk.Button(frame_botones, text="💾 Guardar Configuración", font=("Segoe UI", 10, "bold"),
                  bg=AZUL_RIBBON, fg="white", relief="flat", padx=14, pady=8, cursor="hand2",
                  command=self._guardar).pack(side="left", padx=8)
        tk.Button(frame_botones, text="Cancelar", font=("Segoe UI", 10), bg="white",
                  relief="solid", bd=1, padx=14, pady=8, command=self.destroy).pack(side="left")

    def _toggle_mostrar_clave(self):
        self.entry_api_key.config(show="" if self.var_mostrar.get() else "•")

    def _al_cambiar_proveedor(self, forzar_valores: bool = True):
        clave = self._clave_proveedor_seleccionado()
        info = PROVEEDORES[clave]
        self.label_ayuda.config(text=info["ayuda"])
        self.combo_modelo["values"] = info["modelos"]
        if forzar_valores:
            self.var_modelo.set(info["modelo_sugerido"])
            self.var_url_base.set("")

        editable_url = (clave == "personalizado")
        self.entry_url_base.config(state="normal" if editable_url else "disabled")

    def _clave_proveedor_seleccionado(self) -> str:
        etiqueta = self.var_proveedor.get()
        for clave in ORDEN_PROVEEDORES:
            if PROVEEDORES[clave]["etiqueta"] == etiqueta:
                return clave
        return "openai"

    def _config_desde_formulario(self) -> dict:
        return {
            "proveedor": self._clave_proveedor_seleccionado(),
            "api_key": self.var_api_key.get().strip(),
            "modelo": self.var_modelo.get().strip(),
            "url_base_personalizada": self.var_url_base.get().strip(),
        }

    def _probar_conexion(self):
        config = self._config_desde_formulario()
        if not config["api_key"]:
            messagebox.showwarning("Falta la clave", "Ingresá la clave de API antes de probar.",
                                   parent=self)
            return
        if config["proveedor"] == "personalizado" and not config["url_base_personalizada"]:
            messagebox.showwarning("Falta la URL", "Ingresá la URL base de la API antes de probar.",
                                   parent=self)
            return
        if not config["modelo"]:
            messagebox.showwarning("Falta el modelo", "Indicá el modelo a usar antes de probar.",
                                   parent=self)
            return

        self.label_resultado_prueba.config(text="⏳ Probando conexión...", fg="#6b7280")
        self.update_idletasks()

        resultado = {}

        def _tarea():
            ok, msg = probar_conexion(config)
            resultado["ok"], resultado["msg"] = ok, msg
            self.after(0, _mostrar_resultado)

        def _mostrar_resultado():
            if not self.winfo_exists():
                return
            if resultado["ok"]:
                self.label_resultado_prueba.config(text="✔ Conexión exitosa. La clave y el modelo funcionan.",
                                                    fg=VERDE)
            else:
                self.label_resultado_prueba.config(text=f"✖ {resultado['msg']}", fg=ROJO)

        threading.Thread(target=_tarea, daemon=True).start()

    def _quitar_configuracion_actual(self):
        if not messagebox.askyesno(
            "Quitar configuración de IA",
            "Esto va a quitar la clave de API y la configuración actual del Asistente IA.\n\n"
            "Vas a poder configurar un proveedor distinto a continuación. ¿Continuar?",
            parent=self,
        ):
            return
        eliminar_configuracion_ia()
        self._hay_config_actual = False
        for w in list(self.grid_slaves(row=1, column=0)):
            w.destroy()
        self._construir_formulario()
        self.var_api_key.set("")
        self.var_url_base.set("")
        self.combo_proveedor.current(0)
        self._al_cambiar_proveedor()
        ajustar_tamaño_ventana(self, ancho_min=480, alto_min=600, mantener_posicion=True)

    def _cargar_configuracion_actual(self):
        config = obtener_configuracion_ia()
        if config:
            clave = config["proveedor"] if config["proveedor"] in PROVEEDORES else "personalizado"
            self.combo_proveedor.set(PROVEEDORES[clave]["etiqueta"])
            self._al_cambiar_proveedor(forzar_valores=False)
            self.combo_modelo["values"] = PROVEEDORES[clave]["modelos"]
            self.var_api_key.set(config["api_key"])
            self.var_modelo.set(config["modelo"])
            self.var_url_base.set(config["url_base_personalizada"])
            self.entry_url_base.config(state="normal" if clave == "personalizado" else "disabled")
        else:
            self.combo_proveedor.current(0)
            self._al_cambiar_proveedor()

    def _guardar(self):
        config = self._config_desde_formulario()
        ok, msg = guardar_configuracion_ia(
            config["proveedor"], config["api_key"], config["modelo"],
            url_base_personalizada=config["url_base_personalizada"],
        )
        if ok:
            messagebox.showinfo("Listo", msg, parent=self)
            if self.on_guardado:
                self.on_guardado()
            self.destroy()
        else:
            messagebox.showerror("Error", msg, parent=self)
