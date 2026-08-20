"""
ventana_configurar_email.py
Ventana para gestionar las cuentas de correo desde las que se envían los
reportes (botón 'Email' del Resumen de Ventas, y los reportes del módulo
Veterinaria). Admite cualquier proveedor: Gmail, Outlook/Hotmail, Yahoo,
ProtonMail (con Bridge) o un servidor SMTP personalizado.

A diferencia de versiones anteriores, se pueden guardar VARIAS cuentas a
la vez (no una sola): se listan todas las agregadas, se puede elegir cuál
es la "activa" (la que efectivamente se usa para enviar) con el botón
'Usar esta cuenta', editar los datos de cualquiera, o desvincularla
(quitarla) sin afectar a las demás.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from models_email import (
    listar_cuentas_email, agregar_cuenta_email, editar_cuenta_email,
    activar_cuenta_email, eliminar_cuenta_email, PROVEEDORES,
)
from utilidades_ui import forzar_mayusculas, ajustar_tamaño_ventana

AZUL_RIBBON = "#1d5fd6"
GRIS_FONDO = "#f4f5f7"
GRIS_BORDE = "#e2e8f0"
VERDE = "#16a34a"
ROJO = "#dc2626"

ORDEN_PROVEEDORES = ["gmail", "outlook", "yahoo", "protonmail", "personalizado"]


class VentanaConfigurarEmail(tk.Toplevel):
    def __init__(self, parent, on_guardado=None):
        super().__init__(parent)
        self.on_guardado = on_guardado
        self.modo_edicion_id = None  # None = agregando cuenta nueva; int = editando una existente

        self.title("Configurar Email")
        self.minsize(480, 620)
        self.configure(bg="white")
        self.grab_set()

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_barra_titulo()
        self._construir_ui()
        ajustar_tamaño_ventana(self, ancho_min=480, alto_min=620)

    def _construir_barra_titulo(self):
        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text="📧 Configurar Email", font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

    # ── Estructura general: lista de cuentas + formulario ──────
    def _construir_ui(self):
        self.contenedor = tk.Frame(self, bg="white")
        self.contenedor.grid(row=1, column=0, sticky="nsew", padx=20, pady=15)

        self.frame_lista = tk.Frame(self.contenedor, bg="white")
        self.frame_lista.pack(fill="x")

        self.frame_formulario = tk.Frame(self.contenedor, bg="white")
        # (se hace pack() más abajo, según corresponda, desde _refrescar_lista)

        self._refrescar_lista()

    # ── Lista de cuentas guardadas ──────────────────────────────
    def _refrescar_lista(self):
        for w in self.frame_lista.winfo_children():
            w.destroy()

        cuentas = listar_cuentas_email()

        if cuentas:
            tk.Label(self.frame_lista, text="Cuentas de correo guardadas:",
                     font=("Segoe UI", 9, "bold"), bg="white").pack(anchor="w", pady=(0, 6))
            for cuenta in cuentas:
                self._tarjeta_cuenta(self.frame_lista, cuenta)

            tk.Button(self.frame_lista, text="➕ Agregar otra cuenta de correo",
                      font=("Segoe UI", 9, "bold"), bg="white", fg=AZUL_RIBBON,
                      relief="solid", bd=1, padx=10, pady=6, cursor="hand2",
                      command=self._abrir_formulario_nueva_cuenta
                      ).pack(anchor="w", pady=(6, 10))

            tk.Frame(self.frame_lista, bg=GRIS_BORDE, height=1).pack(fill="x", pady=(0, 10))

            # Con al menos una cuenta ya guardada, el formulario para
            # agregar/editar arranca oculto hasta que se lo pida.
            self.frame_formulario.pack_forget()
        else:
            tk.Label(self.frame_lista,
                     text="Todavía no hay ninguna cuenta de correo configurada.",
                     font=("Segoe UI", 9), bg="white", fg="#6b7280"
                     ).pack(anchor="w", pady=(0, 10))
            # Sin ninguna cuenta, se muestra el formulario directamente.
            self._abrir_formulario_nueva_cuenta()

    def _tarjeta_cuenta(self, parent, cuenta: dict):
        es_activa = cuenta["activa"]
        card = tk.Frame(parent, bg="#e0f2fe" if es_activa else "#f8fafc",
                        relief="solid", bd=1,
                        highlightbackground=AZUL_RIBBON if es_activa else GRIS_BORDE)
        card.pack(fill="x", pady=4)

        info = tk.Frame(card, bg=card["bg"])
        info.pack(side="left", fill="both", expand=True, padx=10, pady=8)
        etiqueta_prov = PROVEEDORES.get(cuenta["proveedor"], {}).get("etiqueta", cuenta["proveedor"])
        texto_estado = "✔ En uso actualmente" if es_activa else etiqueta_prov
        tk.Label(info, text=cuenta["correo_remitente"], font=("Segoe UI", 9, "bold"),
                 bg=card["bg"], fg="#0f172a").pack(anchor="w")
        tk.Label(info, text=texto_estado, font=("Segoe UI", 8),
                 bg=card["bg"], fg=VERDE if es_activa else "#6b7280").pack(anchor="w")

        botones = tk.Frame(card, bg=card["bg"])
        botones.pack(side="right", padx=10, pady=8)

        if not es_activa:
            tk.Button(botones, text="Usar esta cuenta", font=("Segoe UI", 8, "bold"),
                      bg=AZUL_RIBBON, fg="white", relief="flat", padx=8, pady=4, cursor="hand2",
                      command=lambda cid=cuenta["id"]: self._usar_cuenta(cid)
                      ).pack(side="left", padx=(0, 6))
        tk.Button(botones, text="✎ Editar", font=("Segoe UI", 8), bg="white",
                  relief="solid", bd=1, padx=8, pady=4, cursor="hand2",
                  command=lambda c=cuenta: self._abrir_formulario_editar(c)
                  ).pack(side="left", padx=(0, 6))
        tk.Button(botones, text="✕ Desvincular", font=("Segoe UI", 8), bg="white", fg=ROJO,
                  relief="solid", bd=1, padx=8, pady=4, cursor="hand2",
                  command=lambda cid=cuenta["id"], correo=cuenta["correo_remitente"]:
                      self._desvincular_cuenta(cid, correo)
                  ).pack(side="left")

    def _usar_cuenta(self, cuenta_id: int):
        ok, msg = activar_cuenta_email(cuenta_id)
        if ok:
            self._refrescar_lista()
            if self.on_guardado:
                self.on_guardado()
        else:
            messagebox.showerror("Error", msg, parent=self)

    def _desvincular_cuenta(self, cuenta_id: int, correo: str):
        if not messagebox.askyesno(
            "Desvincular cuenta de correo",
            f"Esto va a quitar la cuenta '{correo}' de las cuentas guardadas.\n\n"
            "Las demás cuentas (si hay otras) no se ven afectadas. ¿Continuar?",
            parent=self,
        ):
            return
        ok, msg = eliminar_cuenta_email(cuenta_id)
        if ok:
            self._refrescar_lista()
            if self.on_guardado:
                self.on_guardado()
        else:
            messagebox.showerror("Error", msg, parent=self)

    # ── Formulario: agregar / editar una cuenta ─────────────────
    def _abrir_formulario_nueva_cuenta(self):
        self.modo_edicion_id = None
        self._construir_formulario()
        self.frame_formulario.pack(fill="x", pady=(4, 0))
        self.var_correo.set("")
        self.var_contrasena.set("")
        self.var_nombre.set("Sistema de Gestión de Ventas")
        self.combo_proveedor.current(0)
        self._al_cambiar_proveedor()
        ajustar_tamaño_ventana(self, ancho_min=480, alto_min=620, mantener_posicion=True)

    def _abrir_formulario_editar(self, cuenta: dict):
        self.modo_edicion_id = cuenta["id"]
        self._construir_formulario()
        self.frame_formulario.pack(fill="x", pady=(4, 0))
        clave = cuenta["proveedor"] if cuenta["proveedor"] in PROVEEDORES else "personalizado"
        self.combo_proveedor.set(PROVEEDORES[clave]["etiqueta"])
        self._al_cambiar_proveedor(forzar_valores=False)
        self.var_servidor.set(cuenta["servidor_smtp"])
        self.var_puerto.set(str(cuenta["puerto_smtp"]))
        self.var_seguridad.set(cuenta["seguridad"])
        self.var_correo.set(cuenta["correo_remitente"])
        self.var_contrasena.set(cuenta["contrasena_aplicacion"])
        self.var_nombre.set(cuenta["nombre_remitente"])
        ajustar_tamaño_ventana(self, ancho_min=480, alto_min=620, mantener_posicion=True)

    def _construir_formulario(self):
        for w in self.frame_formulario.winfo_children():
            w.destroy()
        contenedor = self.frame_formulario

        titulo = "Editar cuenta de correo" if self.modo_edicion_id else "Agregar cuenta de correo"
        tk.Label(contenedor, text=titulo, font=("Segoe UI", 10, "bold"), bg="white"
                 ).pack(anchor="w", pady=(4, 8))

        # --- Selector de proveedor ---
        tk.Label(contenedor, text="Proveedor de correo:", font=("Segoe UI", 9, "bold"), bg="white").pack(
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

        # --- Servidor / puerto / seguridad (solo editables si es 'Otro') ---
        fila_servidor = tk.Frame(contenedor, bg="white")
        fila_servidor.pack(fill="x", pady=(0, 4))
        tk.Label(fila_servidor, text="Servidor SMTP:", font=("Segoe UI", 8, "bold"), bg="white").pack(
            side="left")
        self.var_servidor = tk.StringVar()
        self.entry_servidor = tk.Entry(fila_servidor, textvariable=self.var_servidor, font=("Segoe UI", 9))
        self.entry_servidor.pack(side="left", fill="x", expand=True, padx=(6, 10))

        tk.Label(fila_servidor, text="Puerto:", font=("Segoe UI", 8, "bold"), bg="white").pack(side="left")
        self.var_puerto = tk.StringVar()
        self.entry_puerto = tk.Entry(fila_servidor, textvariable=self.var_puerto, font=("Segoe UI", 9), width=6)
        self.entry_puerto.pack(side="left", padx=(6, 0))

        fila_seguridad = tk.Frame(contenedor, bg="white")
        fila_seguridad.pack(fill="x", pady=(4, 12))
        tk.Label(fila_seguridad, text="Seguridad:", font=("Segoe UI", 8, "bold"), bg="white").pack(side="left")
        self.var_seguridad = tk.StringVar(value="ssl")
        self.radio_ssl = tk.Radiobutton(fila_seguridad, text="SSL", variable=self.var_seguridad, value="ssl",
                       bg="white", font=("Segoe UI", 8))
        self.radio_ssl.pack(side="left", padx=(6, 10))
        self.radio_starttls = tk.Radiobutton(fila_seguridad, text="STARTTLS", variable=self.var_seguridad,
                       value="starttls", bg="white", font=("Segoe UI", 8))
        self.radio_starttls.pack(side="left")

        # --- Campos de la cuenta ---
        tk.Label(contenedor, text="Tu correo:", font=("Segoe UI", 9, "bold"), bg="white").pack(
            anchor="w", pady=(5, 2))
        self.var_correo = tk.StringVar()
        tk.Entry(contenedor, textvariable=self.var_correo, font=("Segoe UI", 10), width=40).pack(
            anchor="w", fill="x")

        tk.Label(contenedor, text="Contraseña de aplicación:", font=("Segoe UI", 9, "bold"),
                 bg="white").pack(anchor="w", pady=(12, 2))
        self.var_contrasena = tk.StringVar()
        self.entry_contrasena = tk.Entry(contenedor, textvariable=self.var_contrasena,
                                          font=("Segoe UI", 10), width=40, show="•")
        self.entry_contrasena.pack(anchor="w", fill="x")

        self.var_mostrar = tk.BooleanVar(value=False)
        tk.Checkbutton(contenedor, text="Mostrar contraseña", variable=self.var_mostrar,
                       font=("Segoe UI", 8), bg="white", command=self._toggle_mostrar_contrasena
                       ).pack(anchor="w", pady=(4, 0))

        tk.Label(contenedor, text="Nombre que aparecerá como remitente:", font=("Segoe UI", 9, "bold"),
                 bg="white").pack(anchor="w", pady=(12, 2))
        self.var_nombre = tk.StringVar(value="Sistema de Gestión de Ventas")
        entry_nombre = tk.Entry(contenedor, textvariable=self.var_nombre, font=("Segoe UI", 10), width=40)
        entry_nombre.pack(anchor="w", fill="x")
        forzar_mayusculas(entry_nombre, self.var_nombre)

        frame_botones = tk.Frame(contenedor, bg="white")
        frame_botones.pack(fill="x", pady=(20, 0))
        texto_boton = "💾 Guardar Cambios" if self.modo_edicion_id else "💾 Guardar Cuenta"
        tk.Button(frame_botones, text=texto_boton, font=("Segoe UI", 10, "bold"),
                  bg=AZUL_RIBBON, fg="white", relief="flat", padx=14, pady=8, cursor="hand2",
                  command=self._guardar).pack(side="left")
        tk.Button(frame_botones, text="Cancelar", font=("Segoe UI", 10), bg="white",
                  relief="solid", bd=1, padx=14, pady=8, command=self._cancelar_formulario
                  ).pack(side="left", padx=8)

    def _cancelar_formulario(self):
        if listar_cuentas_email():
            # Ya hay al menos una cuenta guardada: se puede simplemente
            # ocultar el formulario y volver a la lista.
            self.frame_formulario.pack_forget()
            self.modo_edicion_id = None
            ajustar_tamaño_ventana(self, ancho_min=480, alto_min=620, mantener_posicion=True)
        else:
            # Sin ninguna cuenta guardada, no tiene sentido dejar la
            # ventana en un estado vacío sin formulario: se cierra.
            self.destroy()

    def _toggle_mostrar_contrasena(self):
        self.entry_contrasena.config(show="" if self.var_mostrar.get() else "•")

    def _al_cambiar_proveedor(self, forzar_valores: bool = True):
        clave = self._clave_proveedor_seleccionado()
        info = PROVEEDORES[clave]
        self.label_ayuda.config(text=info["ayuda"])
        if forzar_valores:
            self.var_servidor.set(info["servidor"])
            self.var_puerto.set(str(info["puerto"]))
            self.var_seguridad.set(info["seguridad"])

        # El servidor/puerto/seguridad solo son editables a mano cuando el
        # proveedor es "Otro"; para los conocidos, se autocompletan.
        editable = (clave == "personalizado")
        self.entry_servidor.config(state="normal" if editable else "disabled")
        self.entry_puerto.config(state="normal" if editable else "disabled")
        estado_radio = "normal" if editable else "disabled"
        self.radio_ssl.config(state=estado_radio)
        self.radio_starttls.config(state=estado_radio)

    def _clave_proveedor_seleccionado(self) -> str:
        etiqueta = self.var_proveedor.get()
        for clave in ORDEN_PROVEEDORES:
            if PROVEEDORES[clave]["etiqueta"] == etiqueta:
                return clave
        return "gmail"

    def _guardar(self):
        clave = self._clave_proveedor_seleccionado()
        if self.modo_edicion_id:
            ok, msg = editar_cuenta_email(
                self.modo_edicion_id, self.var_correo.get(), self.var_contrasena.get(), self.var_nombre.get(),
                proveedor=clave, servidor_smtp=self.var_servidor.get(),
                puerto_smtp=self.var_puerto.get(), seguridad=self.var_seguridad.get(),
            )
        else:
            ok, msg, _nuevo_id = agregar_cuenta_email(
                self.var_correo.get(), self.var_contrasena.get(), self.var_nombre.get(),
                proveedor=clave, servidor_smtp=self.var_servidor.get(),
                puerto_smtp=self.var_puerto.get(), seguridad=self.var_seguridad.get(),
            )
        if ok:
            messagebox.showinfo("Listo", msg, parent=self)
            self.modo_edicion_id = None
            self._refrescar_lista()
            if self.on_guardado:
                self.on_guardado()
        else:
            messagebox.showerror("Error", msg, parent=self)
