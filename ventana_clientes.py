"""
ventana_clientes.py
Pantalla del módulo Clientes: grilla con lista, búsqueda, alta/edición/
eliminación, y panel de detalle con resumen de compras e historial al
seleccionar un cliente.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from models_clientes import (
    listar_clientes, crear_cliente, editar_cliente, eliminar_cliente,
    resumen_cliente, historial_compras_cliente,
)
from utilidades_ui import forzar_mayusculas, ajustar_tamaño_ventana, formatear_gs, habilitar_deseleccion_treeview
from traducciones import t

AZUL_RIBBON = "#1d5fd6"
GRIS_FONDO = "#f4f5f7"


class PanelClientes(tk.Frame):
    def __init__(self, parent, usuario_actual):
        super().__init__(parent, bg="white")
        self.usuario_actual = usuario_actual
        self.cliente_seleccionado_id = None

        self._construir_barra_superior()
        self._construir_cuerpo()
        self._cargar_datos()

    # ---------------- BARRA SUPERIOR ----------------
    def _construir_barra_superior(self):
        barra = tk.Frame(self, bg="white")
        barra.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(barra, text=t("buscar") + ":", font=("Segoe UI", 9), bg="white").pack(side="left")
        self.var_busqueda = tk.StringVar()
        entry_busqueda = tk.Entry(barra, textvariable=self.var_busqueda, font=("Segoe UI", 9), width=30)
        entry_busqueda.pack(side="left", padx=(5, 15))
        entry_busqueda.bind("<KeyRelease>", lambda e: self._cargar_datos())

        tk.Button(barra, text=t("clientes_nuevo"), font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                  fg="white", relief="flat", padx=12, pady=6, cursor="hand2",
                  activebackground="#1547ab", activeforeground="white",
                  command=self._nuevo_cliente).pack(side="right")
        tk.Button(barra, text=t("editar_boton"), font=("Segoe UI", 9, "bold"), bg="#dbeafe", fg="#1e40af",
                  relief="flat", padx=12, pady=6, cursor="hand2",
                  activebackground="#bfdbfe", activeforeground="#1e40af",
                  command=self._editar_cliente_seleccionado).pack(side="right", padx=(0, 8))
        tk.Button(barra, text=t("eliminar_boton"), font=("Segoe UI", 9, "bold"), bg="#fee2e2", fg="#991b1b",
                  relief="flat", padx=12, pady=6, cursor="hand2",
                  activebackground="#fecaca", activeforeground="#991b1b",
                  command=self._eliminar_cliente_seleccionado).pack(side="right", padx=(0, 8))

    # ---------------- CUERPO: GRILLA (izquierda) + DETALLE (derecha) ----------------
    def _construir_cuerpo(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        contenedor.grid_columnconfigure(0, weight=1)
        contenedor.grid_columnconfigure(1, weight=0)
        contenedor.grid_rowconfigure(0, weight=1)

        self._construir_grilla(contenedor)
        self._construir_panel_detalle(contenedor)

    def _construir_grilla(self, padre):
        frame_grilla = tk.Frame(padre, bg="white")
        frame_grilla.grid(row=0, column=0, sticky="nsew")

        columnas = ("codigo", "nombre", "razon_social", "documento", "direccion", "telefono")
        encabezados = (t("col_codigo_cap"), t("col_nombre"), t("col_razon_social"), t("col_documento"), t("col_direccion"), t("col_telefono"))

        self.tabla = ttk.Treeview(frame_grilla, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc in zip(columnas, encabezados):
            self.tabla.heading(col, text=enc)
            ancho = 180 if col in ("nombre", "razon_social", "direccion") else 100
            self.tabla.column(col, width=ancho, anchor="w" if col != "codigo" else "center")

        frame_grilla.grid_rowconfigure(0, weight=1)
        frame_grilla.grid_columnconfigure(0, weight=1)
        scrollbar = ttk.Scrollbar(frame_grilla, orient="vertical", command=self.tabla.yview)
        scrollbar_h = ttk.Scrollbar(frame_grilla, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=scrollbar.set, xscrollcommand=scrollbar_h.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        scrollbar_h.grid(row=1, column=0, sticky="ew")

        self.tabla.bind("<<TreeviewSelect>>", lambda e: self._al_seleccionar_cliente())
        self.tabla.bind("<Double-1>", lambda e: self._editar_cliente_seleccionado())

    def _construir_panel_detalle(self, padre):
        self.frame_detalle = tk.Frame(padre, bg=GRIS_FONDO, width=320)
        self.frame_detalle.grid(row=0, column=1, sticky="ns", padx=(10, 0))
        self.frame_detalle.grid_propagate(False)
        self._mostrar_detalle_vacio()

    def _mostrar_detalle_vacio(self):
        for widget in self.frame_detalle.winfo_children():
            widget.destroy()
        tk.Label(self.frame_detalle, text=t("clientes_seleccion_detalle"),
                 font=("Segoe UI", 10), bg=GRIS_FONDO, fg="#888", justify="center").pack(
            expand=True, pady=40)

    # ---------------- CARGA DE DATOS ----------------
    def _cargar_datos(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        texto = self.var_busqueda.get()
        clientes = listar_clientes(texto_busqueda=texto)

        self.clientes_por_id = {}
        for c in clientes:
            self.tabla.insert("", "end", iid=str(c["id"]), values=(
                c["id"], c["nombre"], c["razon_social"], c["nro_documento"],
                c["direccion"], c["telefono"],
            ))
            self.clientes_por_id[str(c["id"])] = c

    def _cliente_seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return None
        return self.clientes_por_id.get(seleccion[0])

    # ---------------- DETALLE DEL CLIENTE SELECCIONADO ----------------
    def _al_seleccionar_cliente(self):
        cliente = self._cliente_seleccionado()
        if cliente is None:
            self._mostrar_detalle_vacio()
            return
        self.cliente_seleccionado_id = cliente["id"]
        self._mostrar_detalle_cliente(cliente)

    def _mostrar_detalle_cliente(self, cliente):
        for widget in self.frame_detalle.winfo_children():
            widget.destroy()

        tk.Label(self.frame_detalle, text=cliente["nombre"], font=("Segoe UI", 13, "bold"),
                 bg=GRIS_FONDO, wraplength=290, justify="left").pack(anchor="w", padx=15, pady=(15, 2))
        if cliente["razon_social"] and cliente["razon_social"] != cliente["nombre"]:
            tk.Label(self.frame_detalle, text=cliente["razon_social"], font=("Segoe UI", 9),
                     bg=GRIS_FONDO, fg="#666").pack(anchor="w", padx=15)

        datos = [
            ("N° Documento:", cliente["nro_documento"] or "—"),
            ("Teléfono:", cliente["telefono"] or "—"),
            ("Dirección:", cliente["direccion"] or "—"),
        ]
        frame_datos = tk.Frame(self.frame_detalle, bg=GRIS_FONDO)
        frame_datos.pack(fill="x", padx=15, pady=(10, 10))
        for etiqueta, valor in datos:
            fila = tk.Frame(frame_datos, bg=GRIS_FONDO)
            fila.pack(fill="x", pady=2)
            tk.Label(fila, text=etiqueta, font=("Segoe UI", 8, "bold"), bg=GRIS_FONDO,
                     width=13, anchor="w").pack(side="left")
            tk.Label(fila, text=valor, font=("Segoe UI", 8), bg=GRIS_FONDO, fg="#444",
                     wraplength=170, justify="left", anchor="w").pack(side="left", fill="x", expand=True)

        # --- Resumen de compras ---
        resumen = resumen_cliente(cliente["id"])
        seccion_resumen = tk.Frame(self.frame_detalle, bg=AZUL_RIBBON)
        seccion_resumen.pack(fill="x", padx=15)
        tk.Label(seccion_resumen, text=t("clientes_resumen"), font=("Segoe UI", 8, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(anchor="w", padx=6, pady=2)

        frame_resumen = tk.Frame(self.frame_detalle, bg=GRIS_FONDO)
        frame_resumen.pack(fill="x", padx=15, pady=(5, 10))
        filas_resumen = [
            ("Compras realizadas:", str(resumen["cantidad_compras"])),
            ("Total comprado:", formatear_gs(resumen['total_comprado'])),
            ("Saldo pendiente:", formatear_gs(resumen['saldo_pendiente'])),
        ]
        for i, (etiqueta, valor) in enumerate(filas_resumen):
            tk.Label(frame_resumen, text=etiqueta, font=("Segoe UI", 8), bg=GRIS_FONDO).grid(
                row=i, column=0, sticky="w", pady=2)
            color = "#dc2626" if "pendiente" in etiqueta.lower() and resumen["saldo_pendiente"] > 0 else "black"
            tk.Label(frame_resumen, text=valor, font=("Segoe UI", 8, "bold"), bg=GRIS_FONDO,
                     fg=color).grid(row=i, column=1, sticky="e", padx=(20, 0), pady=2)
        frame_resumen.grid_columnconfigure(1, weight=1)

        # --- Historial de compras ---
        seccion_historial = tk.Frame(self.frame_detalle, bg=AZUL_RIBBON)
        seccion_historial.pack(fill="x", padx=15)
        tk.Label(seccion_historial, text=t("clientes_historial_compras"), font=("Segoe UI", 8, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(anchor="w", padx=6, pady=2)

        contenedor_historial = tk.Frame(self.frame_detalle, bg="white")
        contenedor_historial.pack(fill="both", expand=True, padx=15, pady=(5, 15))
        contenedor_historial.grid_rowconfigure(0, weight=1)
        contenedor_historial.grid_columnconfigure(0, weight=1)

        columnas = ("fecha", "total", "estado")
        tabla_historial = ttk.Treeview(contenedor_historial, columns=columnas, show="headings", height=8)
        habilitar_deseleccion_treeview(tabla_historial)
        tabla_historial.heading("fecha", text=t("col_fecha"))
        tabla_historial.heading("total", text=t("col_total"))
        tabla_historial.heading("estado", text=t("col_estado"))
        tabla_historial.column("fecha", width=100, anchor="center")
        tabla_historial.column("total", width=90, anchor="e")
        tabla_historial.column("estado", width=80, anchor="center")
        sb_historial = ttk.Scrollbar(contenedor_historial, orient="vertical", command=tabla_historial.yview)
        sb_historial_h = ttk.Scrollbar(contenedor_historial, orient="horizontal", command=tabla_historial.xview)
        tabla_historial.configure(yscrollcommand=sb_historial.set, xscrollcommand=sb_historial_h.set)
        tabla_historial.grid(row=0, column=0, sticky="nsew")
        sb_historial.grid(row=0, column=1, sticky="ns")
        sb_historial_h.grid(row=1, column=0, sticky="ew")
        tabla_historial.tag_configure("cancelado", foreground="#9ca3af")

        historial = historial_compras_cliente(cliente["id"])
        for h in historial:
            fecha_corta = h["fecha"].split(" ")[0] if " " in h["fecha"] else h["fecha"]
            tags = ("cancelado",) if h["estado"] == "Cancelado" else ()
            tabla_historial.insert("", "end", values=(
                fecha_corta, formatear_gs(h['total']), h["estado"],
            ), tags=tags)

        if not historial:
            tk.Label(contenedor_historial, text=t("clientes_sin_compras"),
                     font=("Segoe UI", 8), bg="white", fg="#999").pack(pady=10)

    # ---------------- ACCIONES: NUEVO / EDITAR / ELIMINAR ----------------
    def _nuevo_cliente(self):
        VentanaFormularioCliente(self, cliente=None, on_guardado=self._cargar_datos)

    def _editar_cliente_seleccionado(self):
        cliente = self._cliente_seleccionado()
        if cliente is None:
            messagebox.showwarning("Selecciona un cliente", "Primero selecciona un cliente de la lista.", parent=self)
            return
        VentanaFormularioCliente(self, cliente=cliente, on_guardado=self._cargar_datos)

    def _eliminar_cliente_seleccionado(self):
        cliente = self._cliente_seleccionado()
        if cliente is None:
            messagebox.showwarning("Selecciona un cliente", "Primero selecciona un cliente de la lista.", parent=self)
            return
        if not messagebox.askyesno("Confirmar eliminación", f"¿Seguro que quieres eliminar a '{cliente['nombre']}'?"):
            return
        ok, msg = eliminar_cliente(cliente["id"])
        if ok:
            self._cargar_datos()
            self._mostrar_detalle_vacio()
        else:
            messagebox.showerror("No se pudo eliminar", msg, parent=self)


class VentanaFormularioCliente(tk.Toplevel):
    """Ventana de alta/edición de cliente con 3 pestañas: Datos, Créditos y
    Pagos, replicando el formulario completo de gestión de clientes."""

    def __init__(self, parent, cliente, on_guardado):
        super().__init__(parent)
        self.cliente = cliente
        self.es_edicion = cliente is not None
        self.on_guardado = on_guardado

        self.title("Editar Cliente" if self.es_edicion else "Nuevo Cliente")
        self.minsize(440, 600)
        self.configure(bg="white")
        self.grab_set()

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._inicializar_variables()
        self._construir_barra_titulo()
        self._construir_barra_pestanas()
        self._construir_cuerpo_scrollable()
        self._construir_botones_inferiores()

        self.pestana_actual = "Datos"
        self._mostrar_pestana_datos()
        ajustar_tamaño_ventana(self, ancho_min=440, alto_min=600)

    def _construir_cuerpo_scrollable(self):
        """El contenido de cada pestaña vive dentro de un canvas con
        scroll (rueda del mouse/touchpad + scrollbar fina, que solo
        aparece si hace falta), para que los campos y los botones
        Guardar/Cancelar nunca queden cortados sin importar el tamaño de
        la ventana ni cuántos campos tenga la pestaña activa."""
        contenedor = tk.Frame(self, bg=GRIS_FONDO)
        contenedor.grid(row=2, column=0, sticky="nsew")

        canvas = tk.Canvas(contenedor, bg=GRIS_FONDO, highlightthickness=0, bd=0, width=1, height=1)
        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)

        # frame_cuerpo sigue siendo donde cada _mostrar_pestana_* agrega su
        # contenido, sin cambiar esos métodos.
        self.frame_cuerpo = tk.Frame(canvas, bg=GRIS_FONDO)
        id_ventana = canvas.create_window((0, 0), window=self.frame_cuerpo, anchor="nw")

        def _actualizar_scroll(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(id_ventana, width=canvas.winfo_width())
            if self.frame_cuerpo.winfo_reqheight() > canvas.winfo_height():
                if not scrollbar.winfo_ismapped():
                    scrollbar.pack(side="right", fill="y")
            else:
                if scrollbar.winfo_ismapped():
                    scrollbar.pack_forget()

        self.frame_cuerpo.bind("<Configure>", _actualizar_scroll)
        canvas.bind("<Configure>", _actualizar_scroll)

        def _con_scroll_del_mouse(event):
            delta = event.delta
            if delta == 0:
                delta = -1 if getattr(event, "num", None) == 5 else 1
            else:
                delta = int(-1 * (delta / 120)) if abs(delta) >= 120 else -1 * delta
            canvas.yview_scroll(delta, "units")

        def _activar_scroll(event=None):
            canvas.bind_all("<MouseWheel>", _con_scroll_del_mouse)
            canvas.bind_all("<Button-4>", _con_scroll_del_mouse)
            canvas.bind_all("<Button-5>", _con_scroll_del_mouse)

        def _desactivar_scroll(event=None):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        contenedor.bind("<Enter>", _activar_scroll)
        contenedor.bind("<Leave>", _desactivar_scroll)

    # ---------------- VARIABLES (se crean una sola vez) ----------------
    def _inicializar_variables(self):
        from models_clientes import listar_zonas, listar_cobradores
        c = self.cliente or {}

        self.var_tipo_persona = tk.StringVar(value=c.get("tipo_persona", "Física"))
        self.var_nacionalidad = tk.StringVar(value=c.get("nacionalidad", "Paraguaya"))
        self.var_nombre = tk.StringVar(value=c.get("nombre", ""))
        self.var_razon_social = tk.StringVar(
            value=c.get("razon_social", "") if c.get("razon_social") != c.get("nombre") else "")
        self.var_documento = tk.StringVar(value=c.get("nro_documento", ""))
        self.var_ruc = tk.StringVar(value=c.get("ruc", ""))
        self.var_fecha_nacimiento = tk.StringVar(value=c.get("fecha_nacimiento", ""))
        self.var_direccion = tk.StringVar(value=c.get("direccion", ""))
        self.var_telefono = tk.StringVar(value=c.get("telefono", ""))
        self.var_email = tk.StringVar(value=c.get("email", ""))

        self.var_credito_permitido = tk.BooleanVar(value=c.get("credito_permitido", False))
        self.var_dia_cobro = tk.StringVar(value=c.get("dia_cobro", "Sin Asignar"))

        zonas = listar_zonas()
        cobradores = listar_cobradores()
        self.zonas_cache = {z["nombre"]: z["id"] for z in zonas}
        self.cobradores_cache = {co["nombre"]: co["id"] for co in cobradores}
        zona_actual = next((nombre for nombre, zid in self.zonas_cache.items() if zid == c.get("zona_id")), "")
        cobrador_actual = next((nombre for nombre, cid in self.cobradores_cache.items() if cid == c.get("cobrador_id")), "")
        self.var_zona = tk.StringVar(value=zona_actual)
        self.var_cobrador = tk.StringVar(value=cobrador_actual)

        # Las Observaciones van en un Text multilínea, no en StringVar.
        self.texto_observaciones_valor_inicial = c.get("observaciones", "")

    # ---------------- BARRA DE TÍTULO Y PESTAÑAS ----------------
    def _construir_barra_titulo(self):
        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text=self.title(), font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

    def _construir_barra_pestanas(self):
        self.frame_tabs = tk.Frame(self, bg=AZUL_RIBBON, height=28)
        self.frame_tabs.grid(row=1, column=0, sticky="ew")
        self.frame_tabs.grid_propagate(False)

        self.botones_tab = {}
        for nombre in ["Datos", "Créditos", "Pagos"]:
            btn = tk.Label(self.frame_tabs, text=nombre, font=("Segoe UI", 9),
                           bg=AZUL_RIBBON, fg="white", cursor="hand2", padx=14)
            btn.pack(side="left", fill="y", pady=4)
            btn.bind("<Button-1>", lambda e, n=nombre: self._cambiar_pestana(n))
            self.botones_tab[nombre] = btn

    def _resaltar_pestana_activa(self):
        for nombre, btn in self.botones_tab.items():
            if nombre == self.pestana_actual:
                btn.config(bg=GRIS_FONDO, fg=AZUL_RIBBON, font=("Segoe UI", 9, "bold"))
            else:
                btn.config(bg=AZUL_RIBBON, fg="white", font=("Segoe UI", 9))

    def _limpiar_cuerpo(self):
        for widget in self.frame_cuerpo.winfo_children():
            widget.destroy()

    def _cambiar_pestana(self, nombre):
        # Antes de cambiar, sincronizamos observaciones si esa pestaña estaba activa.
        self._sincronizar_observaciones_si_corresponde()
        self.pestana_actual = nombre
        self._resaltar_pestana_activa()
        self._limpiar_cuerpo()
        {"Datos": self._mostrar_pestana_datos,
         "Créditos": self._mostrar_pestana_creditos,
         "Pagos": self._mostrar_pestana_pagos}[nombre]()

        # Cada pestaña puede requerir más o menos alto; se usa el tamaño
        # actual como piso para que la ventana solo crezca si hace falta,
        # sin achicarse al volver a una pestaña más corta, ni cortar campos
        # en pestañas con más contenido.
        ajustar_tamaño_ventana(
            self, ancho_min=self.winfo_width(), alto_min=self.winfo_height(),
            mantener_posicion=True,
        )

    def _sincronizar_observaciones_si_corresponde(self):
        if hasattr(self, "texto_observaciones") and self.texto_observaciones.winfo_exists():
            self.texto_observaciones_valor_inicial = self.texto_observaciones.get("1.0", "end-1c").strip()

    # ---------------- PESTAÑA: DATOS ----------------
    def _mostrar_pestana_datos(self):
        self._resaltar_pestana_activa()
        contenedor = tk.Frame(self.frame_cuerpo, bg=GRIS_FONDO)
        contenedor.pack(fill="both", expand=True, padx=20, pady=15)

        # --- Tipo de persona + Nacionalidad ---
        fila_tipo = tk.Frame(contenedor, bg=GRIS_FONDO)
        fila_tipo.pack(fill="x", pady=(0, 12))
        tk.Radiobutton(fila_tipo, text="Física", variable=self.var_tipo_persona, value="Física",
                       font=("Segoe UI", 9), bg=GRIS_FONDO).pack(side="left")
        tk.Radiobutton(fila_tipo, text="Jurídica", variable=self.var_tipo_persona, value="Jurídica",
                       font=("Segoe UI", 9), bg=GRIS_FONDO).pack(side="left", padx=(8, 20))
        tk.Label(fila_tipo, text="Nacionalidad:", font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).pack(side="left")
        ttk.Combobox(fila_tipo, textvariable=self.var_nacionalidad, values=["Paraguaya", "Extranjera"],
                     font=("Segoe UI", 9), width=14, state="readonly").pack(side="left", padx=(6, 0))

        tk.Label(contenedor, text="Nombre Cliente:", font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).pack(
            anchor="w", pady=(4, 2))
        entry_nombre = tk.Entry(contenedor, textvariable=self.var_nombre, font=("Segoe UI", 10))
        entry_nombre.pack(fill="x")
        forzar_mayusculas(entry_nombre, self.var_nombre)

        tk.Label(contenedor, text="Datos de Facturación", font=("Segoe UI", 10, "bold"),
                 bg=GRIS_FONDO).pack(anchor="w", pady=(14, 6))

        self._campo_texto(contenedor, "Razón Social:", self.var_razon_social, mayusculas=True)
        self._campo_texto(contenedor, "N° Documento:", self.var_documento, mayusculas=False)
        self._campo_texto(contenedor, "RUC:", self.var_ruc, mayusculas=False)

        tk.Label(contenedor, text="Fecha Nac.:", font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).pack(
            anchor="w", pady=(8, 2))
        frame_fecha = tk.Frame(contenedor, bg=GRIS_FONDO)
        frame_fecha.pack(fill="x")
        self.label_fecha_nac = tk.Label(
            frame_fecha, text=self.var_fecha_nacimiento.get() or "Seleccione una fecha",
            font=("Segoe UI", 9), bg="white", relief="solid", bd=1, anchor="w", padx=8, pady=5,
            cursor="hand2",
        )
        self.label_fecha_nac.pack(side="left", fill="x", expand=True)
        self.label_fecha_nac.bind("<Button-1>", lambda e: self._elegir_fecha_nacimiento())
        icono_cal = tk.Label(frame_fecha, text="📅", font=("Segoe UI", 9), bg=GRIS_FONDO, cursor="hand2")
        icono_cal.pack(side="left", padx=(6, 0))
        icono_cal.bind("<Button-1>", lambda e: self._elegir_fecha_nacimiento())

        self._campo_texto(contenedor, "Dirección:", self.var_direccion, mayusculas=True, alto_extra=True)
        self._campo_texto(contenedor, "Teléfono:", self.var_telefono, mayusculas=False)
        self._campo_texto(contenedor, "Email:", self.var_email, mayusculas=False)

        tk.Label(contenedor, text="Obs:", font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).pack(
            anchor="w", pady=(8, 2))
        self.texto_observaciones = tk.Text(contenedor, font=("Segoe UI", 9), height=3, wrap="word",
                                            relief="solid", bd=1)
        self.texto_observaciones.pack(fill="x")
        self.texto_observaciones.insert("1.0", self.texto_observaciones_valor_inicial)

    def _campo_texto(self, parent, etiqueta, var, mayusculas=False, alto_extra=False):
        tk.Label(parent, text=etiqueta, font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).pack(
            anchor="w", pady=(8, 2))
        entry = tk.Entry(parent, textvariable=var, font=("Segoe UI", 9))
        entry.pack(fill="x", ipady=4 if alto_extra else 0)
        if mayusculas:
            forzar_mayusculas(entry, var)
        return entry

    def _elegir_fecha_nacimiento(self):
        from widget_calendario import abrir_selector_fecha
        import datetime
        fecha_actual = datetime.date.today()
        if self.var_fecha_nacimiento.get():
            try:
                fecha_actual = datetime.date.fromisoformat(self.var_fecha_nacimiento.get())
            except ValueError:
                pass

        def al_elegir(fecha):
            self.var_fecha_nacimiento.set(fecha.isoformat())
            self.label_fecha_nac.config(text=fecha.strftime("%d/%m/%Y"))

        abrir_selector_fecha(self, fecha_actual, al_elegir)

    # ---------------- PESTAÑA: CRÉDITOS ----------------
    def _mostrar_pestana_creditos(self):
        self._resaltar_pestana_activa()
        contenedor = tk.Frame(self.frame_cuerpo, bg=GRIS_FONDO)
        contenedor.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Checkbutton(contenedor, text="Crédito Permitido", variable=self.var_credito_permitido,
                       font=("Segoe UI", 10, "bold"), bg=GRIS_FONDO).pack(anchor="w")
        tk.Label(contenedor,
                 text="Si está desmarcado, este cliente no podrá registrar\nventas con la condición 'Crédito'.",
                 font=("Segoe UI", 8), bg=GRIS_FONDO, fg="#666", justify="left").pack(anchor="w", pady=(6, 0))

        if self.es_edicion:
            from models_clientes import resumen_cliente
            resumen = resumen_cliente(self.cliente["id"])
            if resumen["saldo_pendiente"] > 0:
                tk.Label(contenedor, text=f"⚠ Saldo pendiente actual: Gs. {resumen['saldo_pendiente']:,.0f}",
                         font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO, fg="#dc2626").pack(anchor="w", pady=(15, 0))

    # ---------------- PESTAÑA: PAGOS ----------------
    def _mostrar_pestana_pagos(self):
        from models_clientes import DIAS_COBRO
        self._resaltar_pestana_activa()
        contenedor = tk.Frame(self.frame_cuerpo, bg=GRIS_FONDO)
        contenedor.pack(fill="both", expand=True, padx=20, pady=15)

        tk.Label(contenedor, text="Día de Cobro", font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).pack(
            anchor="w", pady=(0, 6))
        for dia in DIAS_COBRO:
            tk.Radiobutton(contenedor, text=dia, variable=self.var_dia_cobro, value=dia,
                           font=("Segoe UI", 9), bg=GRIS_FONDO).pack(anchor="w")

        tk.Label(contenedor, text="Zona", font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).pack(
            anchor="w", pady=(16, 2))
        combo_zona = ttk.Combobox(contenedor, textvariable=self.var_zona,
                                   values=list(self.zonas_cache.keys()), font=("Segoe UI", 9))
        combo_zona.pack(fill="x")
        forzar_mayusculas(combo_zona, self.var_zona)

        tk.Label(contenedor, text="Cobrador", font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).pack(
            anchor="w", pady=(12, 2))
        combo_cobrador = ttk.Combobox(contenedor, textvariable=self.var_cobrador,
                                       values=list(self.cobradores_cache.keys()), font=("Segoe UI", 9))
        combo_cobrador.pack(fill="x")
        forzar_mayusculas(combo_cobrador, self.var_cobrador)

        tk.Label(contenedor, text="(Escribe un nombre nuevo para crearlo al guardar)",
                 font=("Segoe UI", 7), bg=GRIS_FONDO, fg="#777").pack(anchor="w", pady=(4, 0))

    # ---------------- BOTONES INFERIORES ----------------
    def _construir_botones_inferiores(self):
        frame_botones = tk.Frame(self, bg=GRIS_FONDO, height=58)
        frame_botones.grid(row=3, column=0, sticky="ew")
        frame_botones.grid_propagate(False)

        contenedor = tk.Frame(frame_botones, bg=GRIS_FONDO)
        contenedor.pack(pady=10)
        tk.Button(contenedor, text="✔ Guardar", font=("Segoe UI", 10, "bold"), bg="white", fg="#16a34a",
                  relief="solid", bd=1, padx=16, pady=8, cursor="hand2",
                  command=self._guardar).pack(side="left", padx=8)
        tk.Button(contenedor, text="✕ Cancelar", font=("Segoe UI", 10, "bold"), bg="white", fg="#dc2626",
                  relief="solid", bd=1, padx=16, pady=8, cursor="hand2",
                  command=self.destroy).pack(side="left", padx=8)

    # ---------------- RESOLVER ZONA / COBRADOR (crear si no existen) ----------------
    def _resolver_zona(self):
        from models_clientes import crear_zona, listar_zonas
        nombre = self.var_zona.get().strip()
        if not nombre:
            return None
        if nombre not in self.zonas_cache:
            crear_zona(nombre)
            self.zonas_cache = {z["nombre"]: z["id"] for z in listar_zonas()}
        return self.zonas_cache.get(nombre)

    def _resolver_cobrador(self):
        from models_clientes import crear_cobrador, listar_cobradores
        nombre = self.var_cobrador.get().strip()
        if not nombre:
            return None
        if nombre not in self.cobradores_cache:
            crear_cobrador(nombre)
            self.cobradores_cache = {co["nombre"]: co["id"] for co in listar_cobradores()}
        return self.cobradores_cache.get(nombre)

    def _guardar(self):
        self._sincronizar_observaciones_si_corresponde()

        nombre = self.var_nombre.get().strip()
        if not nombre:
            messagebox.showerror("Dato requerido", "El nombre del cliente es obligatorio.", parent=self)
            self._cambiar_pestana("Datos")
            return

        zona_id = self._resolver_zona()
        cobrador_id = self._resolver_cobrador()

        datos_comunes = dict(
            nombre=nombre, razon_social=self.var_razon_social.get(), nro_documento=self.var_documento.get(),
            direccion=self.var_direccion.get(), telefono=self.var_telefono.get(), email=self.var_email.get(),
            tipo_persona=self.var_tipo_persona.get(), nacionalidad=self.var_nacionalidad.get(),
            ruc=self.var_ruc.get(), fecha_nacimiento=self.var_fecha_nacimiento.get(),
            observaciones=self.texto_observaciones_valor_inicial,
            credito_permitido=self.var_credito_permitido.get(), dia_cobro=self.var_dia_cobro.get(),
            zona_id=zona_id, cobrador_id=cobrador_id,
        )

        if self.es_edicion:
            ok, msg = editar_cliente(self.cliente["id"], **datos_comunes)
        else:
            ok, msg = crear_cliente(**datos_comunes)

        if ok:
            self.on_guardado()
            self.destroy()
        else:
            messagebox.showerror("Error", msg, parent=self)