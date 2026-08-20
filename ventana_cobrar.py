"""
ventana_cobrar.py
Ventana modal "Cobrar" que se abre al presionar F12 desde la pantalla de
Ventas. Muestra los datos del cliente, las formas de pago disponibles, el
total a cobrar, el campo de efectivo con cálculo automático de vuelto,
observaciones, y las acciones: Cobrar e Imprimir, Cobrar sin Imprimir,
Generar Preventa, y Cancelar.

Layout responsive: usa grid/pack con pesos de expansión, por lo que la
ventana se puede maximizar o redimensionar sin que ningún campo quede
oculto fuera del área visible.
"""
import tkinter as tk
from tkinter import messagebox

from models_ventas import procesar_venta
from utilidades_ui import forzar_mayusculas, ajustar_tamaño_ventana, formatear_gs

AZUL_RIBBON = "#1d5fd6"
AZUL_OSCURO = "#163d8c"
GRIS_FONDO = "#f4f5f7"
VERDE = "#16a34a"
VERDE_OSCURO = "#15803d"
NARANJA = "#d97706"
ROJO = "#dc2626"

FORMAS_DE_PAGO = ["Efectivo", "Crédito", "Tarjeta/QR", "Transferencia Bancaria", "Criptomonedas"]


class VentanaCobrar(tk.Toplevel):
    def __init__(self, parent, items_venta, cliente, usuario_actual, condicion_inicial, on_venta_procesada):
        super().__init__(parent)
        self.items_venta = items_venta
        self.cliente = cliente
        self.usuario_actual = usuario_actual
        self.on_venta_procesada = on_venta_procesada

        self.total = sum(i["cantidad"] * i["precio_unitario"] for i in items_venta)

        self.title("Cobrar")
        self.minsize(700, 420)
        self.resizable(True, True)
        self.configure(bg="white")
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._cancelar)
        # En Windows, mantener un grab modal activo (grab_set) mientras se
        # hace click en "Minimizar" hace que el botón no responda: el
        # gestor de ventanas no puede minimizar una ventana que retiene el
        # grab. Se libera el grab justo antes de minimizar y se vuelve a
        # tomar al restaurar la ventana, para que "Minimizar" funcione sin
        # perder el comportamiento modal el resto del tiempo.
        self.bind("<Unmap>", self._al_cambiar_visibilidad)
        self.bind("<Map>", self._al_cambiar_visibilidad)

        # Layout raíz responsive: fila 0 = barra de título (fija),
        # fila 1 = cuerpo (se expande en ambos ejes).
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_barra_titulo()
        self._construir_cuerpo()

        if condicion_inicial == "credito":
            self.var_forma_pago.set("Crédito")
            self._al_cambiar_forma_pago()

        self._registrar_atajos()
        self.entry_efectivo.focus()

        # El tamaño se calcula DESPUÉS de construir todo el contenido, para
        # garantizar que Cliente, Formas de Pago, Total, Efectivo, Vuelto y
        # Observaciones siempre se vean completos sin recortarse.
        ajustar_tamaño_ventana(self, ancho_min=700, alto_min=420)

    def _al_cambiar_visibilidad(self, event=None):
        """Libera el grab modal cuando la ventana se minimiza (<Unmap>) y lo
        retoma cuando se restaura (<Map>). Ver comentario en __init__: sin
        esto, el botón nativo de Minimizar no responde en Windows mientras
        el grab está activo."""
        if event is not None and event.widget is not self:
            return
        if not self.winfo_exists():
            return
        try:
            if self.state() == "iconic":
                self.grab_release()
            else:
                self.grab_set()
        except tk.TclError:
            pass

    # ---------------- BARRA DE TÍTULO ----------------
    def _construir_barra_titulo(self):
        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text="Cobrar", font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

    # ---------------- CUERPO: dos columnas (izquierda expande, derecha fija) ----------------
    def _construir_cuerpo(self):
        cuerpo = tk.Frame(self, bg="white")
        cuerpo.grid(row=1, column=0, sticky="nsew")
        cuerpo.grid_columnconfigure(0, weight=1)  # panel izquierdo se expande
        cuerpo.grid_columnconfigure(1, weight=0)  # panel de botones, ancho fijo
        cuerpo.grid_rowconfigure(0, weight=1)

        self._construir_panel_cliente_y_pago(cuerpo)
        self._construir_panel_botones(cuerpo)

    # ---------------- PANEL IZQUIERDO: CLIENTE, FORMAS DE PAGO, TOTAL/EFECTIVO ----------------
    def _construir_panel_cliente_y_pago(self, cuerpo):
        panel_izq = tk.Frame(cuerpo, bg="white")
        panel_izq.grid(row=0, column=0, sticky="nsew", padx=15, pady=10)

        # --- Sección CLIENTE ---
        seccion_cliente = tk.Frame(panel_izq, bg=AZUL_RIBBON)
        seccion_cliente.pack(fill="x")
        tk.Label(seccion_cliente, text="CLIENTE", font=("Segoe UI", 9, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(anchor="w", padx=8, pady=3)

        datos_cliente = tk.Frame(panel_izq, bg=GRIS_FONDO)
        datos_cliente.pack(fill="x", pady=(0, 10))

        nombre_cliente = self.cliente["nombre"] if self.cliente else "Ocasional"
        documento = (self.cliente.get("ruc") or self.cliente.get("nro_documento", "")) if self.cliente else ""
        direccion = self.cliente.get("direccion", "") if self.cliente else ""
        telefono = self.cliente.get("telefono", "") if self.cliente else ""

        filas_cliente = [
            ("Cliente:", nombre_cliente, "RUC:", documento),
            ("Dirección:", direccion, "", ""),
            ("Teléfono:", telefono, "", ""),
        ]
        for fila, (et1, val1, et2, val2) in enumerate(filas_cliente):
            tk.Label(datos_cliente, text=et1, font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).grid(
                row=fila, column=0, sticky="w", padx=8, pady=3)
            tk.Label(datos_cliente, text=val1, font=("Segoe UI", 9), bg=GRIS_FONDO).grid(
                row=fila, column=1, sticky="w", pady=3)
            if et2:
                tk.Label(datos_cliente, text=et2, font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).grid(
                    row=fila, column=2, sticky="w", padx=8, pady=3)
                tk.Label(datos_cliente, text=val2, font=("Segoe UI", 9), bg=GRIS_FONDO).grid(
                    row=fila, column=3, sticky="w", pady=3)

        # --- Sección FORMAS DE PAGO ---
        seccion_pago = tk.Frame(panel_izq, bg=AZUL_RIBBON)
        seccion_pago.pack(fill="x")
        tk.Label(seccion_pago, text="FORMAS DE PAGO", font=("Segoe UI", 9, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(anchor="w", padx=8, pady=3)

        frame_radios = tk.Frame(panel_izq, bg="white")
        frame_radios.pack(fill="x", pady=(5, 10))

        self.var_forma_pago = tk.StringVar(value="Efectivo")
        self.radios_forma_pago = []
        # Grilla de 2 columnas en vez de lista vertical: reduce bastante el
        # alto de esta sección sin perder legibilidad (4 opciones = 2 filas
        # en vez de 4).
        for i, forma in enumerate(FORMAS_DE_PAGO):
            fila, columna = divmod(i, 2)
            r = tk.Radiobutton(frame_radios, text=forma, variable=self.var_forma_pago, value=forma,
                               font=("Segoe UI", 9), bg="white", selectcolor="white",
                               activebackground="white", command=self._al_cambiar_forma_pago)
            r.grid(row=fila, column=columna, sticky="w", padx=8, pady=2)
            self.radios_forma_pago.append(r)

        # --- Sección PAGO (Total / Efectivo / Vuelto / Observaciones) ---
        seccion_pago2 = tk.Frame(panel_izq, bg=AZUL_RIBBON)
        seccion_pago2.pack(fill="x")
        tk.Label(seccion_pago2, text="PAGO", font=("Segoe UI", 9, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(anchor="w", padx=8, pady=3)

        frame_pago = tk.Frame(panel_izq, bg="white")
        frame_pago.pack(fill="x", pady=(8, 0))
        frame_pago.grid_columnconfigure(1, weight=1)

        tk.Label(frame_pago, text="TOTAL:", font=("Segoe UI", 13, "bold"), bg="white").grid(
            row=0, column=0, sticky="e", pady=4, padx=(0, 10))
        tk.Label(frame_pago, text=formatear_gs(self.total), font=("Segoe UI", 16, "bold"),
                 bg=AZUL_OSCURO, fg="white", padx=10, pady=2).grid(row=0, column=1, sticky="w", pady=4)

        tk.Label(frame_pago, text="Efectivo:", font=("Segoe UI", 11, "bold"), bg="white").grid(
            row=1, column=0, sticky="e", pady=6, padx=(0, 10))
        self.var_efectivo = tk.StringVar()
        self.entry_efectivo = tk.Entry(frame_pago, textvariable=self.var_efectivo, font=("Segoe UI", 12), width=16)
        self.entry_efectivo.grid(row=1, column=1, sticky="w", pady=6)
        self.var_efectivo.trace_add("write", lambda *a: self._recalcular_vuelto())
        # Doble click en el campo Efectivo autocompleta con el monto exacto del Total
        # (atajo de "pago exacto", evita tener que tipear el número).
        self.entry_efectivo.bind("<Double-Button-1>", lambda e: self._autocompletar_efectivo_con_total())
        # Enter en el campo Efectivo cobra directo (F12, con impresión), sin
        # necesidad de tocar el mouse: si se deja vacío, se interpreta como
        # pago exacto (completa el Total automáticamente) y cobra en el
        # mismo paso — para agilizar el caso más común de pago en efectivo.
        self.entry_efectivo.bind("<Return>", self._al_enter_efectivo)

        tk.Label(frame_pago, text="(doble click en Efectivo para completar el Total exacto)",
                 font=("Segoe UI", 7), bg="white", fg="#888").grid(row=1, column=2, sticky="w", padx=(8, 0))

        tk.Label(frame_pago, text="Vuelto:", font=("Segoe UI", 11, "bold"), bg="white").grid(
            row=2, column=0, sticky="e", pady=3, padx=(0, 10))
        self.label_vuelto = tk.Label(frame_pago, text="-", font=("Segoe UI", 11, "bold"), bg="white")
        self.label_vuelto.grid(row=2, column=1, sticky="w", pady=3)

        tk.Label(frame_pago, text="Observaciones:", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=3, column=0, sticky="e", pady=6, padx=(0, 10))
        self.var_observaciones = tk.StringVar()
        entry_observaciones = tk.Entry(frame_pago, textvariable=self.var_observaciones, font=("Segoe UI", 9), width=30)
        entry_observaciones.grid(row=3, column=1, sticky="w", pady=6)
        forzar_mayusculas(entry_observaciones, self.var_observaciones)

        # --- Sección TIPO DE DOCUMENTO ---
        seccion_doc = tk.Frame(panel_izq, bg=AZUL_RIBBON)
        seccion_doc.pack(fill="x", pady=(10, 0))
        tk.Label(seccion_doc, text="TIPO DE DOCUMENTO A EMITIR",
                 font=("Segoe UI", 9, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(anchor="w", padx=8, pady=3)

        frame_doc = tk.Frame(panel_izq, bg="#fef3c7", relief="solid", bd=1)
        frame_doc.pack(fill="x", pady=(0, 8))

        tk.Label(frame_doc,
                 text="⚠  Debe elegir el tipo de documento ANTES de cobrar.",
                 font=("Segoe UI", 8, "bold"), bg="#fef3c7", fg="#92400e"
                 ).pack(anchor="w", padx=8, pady=(6, 2))

        self.var_tipo_doc = tk.StringVar(value="")

        r_comp = tk.Radiobutton(
            frame_doc, text="🧾  Comprobante de Venta  (sin datos fiscales)",
            variable=self.var_tipo_doc, value="comprobante",
            font=("Segoe UI", 9), bg="#fef3c7", selectcolor="#fef3c7", activebackground="#fef3c7",
            command=self._al_cambiar_tipo_doc)
        r_comp.pack(anchor="w", padx=8, pady=2)

        r_fac = tk.Radiobutton(
            frame_doc, text="📄  Factura Legal  (con RUC, Timbrado e IVA)",
            variable=self.var_tipo_doc, value="factura",
            font=("Segoe UI", 9), bg="#fef3c7", selectcolor="#fef3c7", activebackground="#fef3c7",
            command=self._al_cambiar_tipo_doc)
        r_fac.pack(anchor="w", padx=8, pady=2)

        # Datos del comprador para la factura (se muestran solo si elige Factura)
        self._frame_datos_factura = tk.Frame(frame_doc, bg="#fef3c7")
        self._frame_datos_factura.pack(fill="x", padx=8, pady=(4, 6))
        self._frame_datos_factura.pack_forget()  # oculto por defecto

        tk.Label(self._frame_datos_factura, text="RUC/CI comprador:",
                 font=("Segoe UI", 8, "bold"), bg="#fef3c7").grid(
                     row=0, column=0, sticky="w", pady=2)
        self.var_ruc_comprador = tk.StringVar(
            value=(self.cliente.get("ruc") or self.cliente.get("nro_documento", "")) if self.cliente else "")
        tk.Entry(self._frame_datos_factura, textvariable=self.var_ruc_comprador,
                 font=("Segoe UI", 9), width=18).grid(
                     row=0, column=1, sticky="w", padx=(6, 0), pady=2)

        tk.Label(self._frame_datos_factura, text="Razón social:",
                 font=("Segoe UI", 8, "bold"), bg="#fef3c7").grid(
                     row=1, column=0, sticky="w", pady=2)
        self.var_razon_social_comp = tk.StringVar(
            value=(self.cliente.get("razon_social") or self.cliente.get("nombre", "")) if self.cliente else "")
        tk.Entry(self._frame_datos_factura, textvariable=self.var_razon_social_comp,
                 font=("Segoe UI", 9), width=28).grid(
                     row=1, column=1, sticky="w", padx=(6, 0), pady=2)

        self.lbl_doc_seleccionado = tk.Label(
            frame_doc, text="", font=("Segoe UI", 8, "italic"),
            bg="#fef3c7", fg="#374151")
        self.lbl_doc_seleccionado.pack(anchor="w", padx=8, pady=(0, 6))

    def _autocompletar_efectivo_con_total(self):
        """Doble click en el campo Efectivo: lo llena automáticamente con el
        monto exacto del Total, para agilizar el caso de pago exacto."""
        self.var_efectivo.set(f"{self.total:.0f}")
        self.entry_efectivo.icursor(tk.END)
        self.entry_efectivo.selection_range(0, tk.END)

    def _al_enter_efectivo(self, event=None):
        """Enter en el campo Efectivo: si se dejó vacío y la forma de pago
        es Efectivo, se asume pago exacto (se completa el Total solo) y se
        cobra e imprime en el mismo paso — el atajo más rápido para el caso
        más común (pago justo, sin vuelto)."""
        if self.var_forma_pago.get() == "Efectivo" and not self.var_efectivo.get().strip():
            self._autocompletar_efectivo_con_total()
        self._cobrar(imprimir=True)

    def _al_cambiar_tipo_doc(self):
        tipo = self.var_tipo_doc.get()
        if tipo == "factura":
            self._frame_datos_factura.pack(fill="x", padx=8, pady=(4, 6))
            self.lbl_doc_seleccionado.config(
                text="✔ Se generará Factura Legal con IVA al cobrar.",
                fg="#16a34a")
        else:
            self._frame_datos_factura.pack_forget()
            self.lbl_doc_seleccionado.config(
                text="✔ Se generará Comprobante de Venta al cobrar.",
                fg="#16a34a")

    def _al_cambiar_forma_pago(self):
        # Si la forma de pago no es Efectivo, el campo Efectivo/Vuelto no aplica directamente.
        if self.var_forma_pago.get() != "Efectivo":
            self.var_efectivo.set("")
            self.label_vuelto.config(text="-", fg="black")
        self._recalcular_vuelto()

    def _recalcular_vuelto(self):
        forma = self.var_forma_pago.get()
        if forma != "Efectivo":
            self.label_vuelto.config(text="-", fg="black")
            return
        texto = self.var_efectivo.get().replace(",", "").replace("Gs.", "").strip()
        if not texto:
            self.label_vuelto.config(text="-", fg="black")
            return
        try:
            efectivo = float(texto)
        except ValueError:
            self.label_vuelto.config(text="Monto inválido", fg="#dc2626")
            return
        vuelto = efectivo - self.total
        if vuelto < 0:
            self.label_vuelto.config(text=f"Falta " + formatear_gs(abs(vuelto)), fg="#dc2626")
        else:
            self.label_vuelto.config(text=formatear_gs(vuelto), fg="#16a34a")

    def _validar_pago_suficiente(self):
        """Para Efectivo, exige que el monto ingresado cubra el total.
        Para otras formas de pago, no se exige un monto específico aquí."""
        forma = self.var_forma_pago.get()
        if forma != "Efectivo":
            return True
        texto = self.var_efectivo.get().replace(",", "").replace("Gs.", "").strip()
        if not texto:
            messagebox.showwarning("Falta el efectivo", "Ingresa el monto recibido en efectivo.", parent=self)
            return False
        try:
            efectivo = float(texto)
        except ValueError:
            messagebox.showerror("Monto inválido", "El efectivo ingresado no es un número válido.", parent=self)
            return False
        if efectivo < self.total:
            messagebox.showwarning(
                "Efectivo insuficiente",
                f"El efectivo ingresado (Gs. " + formatear_gs(efectivo) + ") es menor al total (Gs. " + formatear_gs(self.total) + ")."
            )
            return False
        return True

    # ---------------- PANEL DERECHO: BOTONES DE ACCIÓN ----------------
    def _construir_panel_botones(self, cuerpo):
        panel_der = tk.Frame(cuerpo, bg="white", width=230)
        panel_der.grid(row=0, column=1, sticky="ns", padx=(0, 15), pady=10)
        panel_der.grid_propagate(False)

        tk.Button(panel_der, text="🖶 F12 - Cobrar e Imprimir", font=("Segoe UI", 9, "bold"),
                  bg=AZUL_RIBBON, fg="white", relief="flat", bd=0, anchor="w", padx=10, pady=8,
                  cursor="hand2", activebackground=AZUL_OSCURO, activeforeground="white",
                  command=lambda: self._cobrar(imprimir=True)).pack(fill="x", pady=4)
        tk.Button(panel_der, text="🖶 F11 - Cobrar sin Imprimir", font=("Segoe UI", 9, "bold"),
                  bg=VERDE, fg="white", relief="flat", bd=0, anchor="w", padx=10, pady=8,
                  cursor="hand2", activebackground=VERDE_OSCURO, activeforeground="white",
                  command=lambda: self._cobrar(imprimir=False)).pack(fill="x", pady=4)
        tk.Button(panel_der, text="🕑 F8 - Generar Preventa", font=("Segoe UI", 9, "bold"),
                  bg=NARANJA, fg="white", relief="flat", bd=0, anchor="w", padx=10, pady=8,
                  cursor="hand2", activebackground="#b45309", activeforeground="white",
                  command=self._generar_preventa).pack(fill="x", pady=4)
        tk.Button(panel_der, text="✕ ESC - Cancelar", font=("Segoe UI", 9, "bold"),
                  bg="white", fg=ROJO, relief="solid", bd=1, anchor="w", padx=10, pady=8,
                  cursor="hand2", activebackground="#fef2f2",
                  command=self._cancelar).pack(fill="x", pady=4)

    def _registrar_atajos(self):
        self.bind("<F12>", lambda e: self._cobrar(imprimir=True))
        self.bind("<F11>", lambda e: self._cobrar(imprimir=False))
        self.bind("<F8>", lambda e: self._generar_preventa())
        self.bind("<Escape>", lambda e: self._cancelar())

    # ---------------- ACCIONES ----------------
    def _cobrar(self, imprimir: bool):
        if not self._validar_pago_suficiente():
            return

        # Validar que se haya elegido un tipo de documento
        tipo_doc = self.var_tipo_doc.get()
        if not tipo_doc:
            messagebox.showwarning(
                "Tipo de documento requerido",
                "Debe elegir el tipo de documento antes de cobrar:\n\n"
                "  🧾  Comprobante de Venta\n"
                "  📄  Factura Legal\n\n"
                "Seleccione una opción en la sección 'TIPO DE DOCUMENTO'.",
                parent=self)
            return

        forma_pago = self.var_forma_pago.get()
        condicion = "credito" if forma_pago == "Crédito" else "contado"
        cliente_id = self.cliente["id"] if self.cliente else None

        if condicion == "credito" and cliente_id is None:
            messagebox.showwarning(
                "Cliente requerido",
                "Una venta a crédito necesita un cliente asignado (F1 - Asignar Cliente)."
            )
            return

        if condicion == "credito":
            from models_clientes import cliente_tiene_credito_permitido
            if not cliente_tiene_credito_permitido(cliente_id):
                messagebox.showwarning(
                    "Crédito no permitido",
                    f"'{self.cliente['nombre']}' no tiene el crédito habilitado.\n\n"
                    "Puedes activarlo desde Clientes → Editar Cliente → pestaña Créditos."
                )
                return

        items_para_guardar = []
        for item in self.items_venta:
            p = item["producto"]
            if p.get("es_libre"):
                items_para_guardar.append({
                    "producto_id": None,
                    "descripcion_libre": p["nombre"],
                    "cantidad": item["cantidad"],
                    "precio_unitario": item["precio_unitario"],
                })
            else:
                items_para_guardar.append({
                    "producto_id": p["id"],
                    "cantidad": item["cantidad"],
                    "precio_unitario": item["precio_unitario"],
                })

        ok, msg, venta_id = procesar_venta(
            items_para_guardar, usuario_id=self.usuario_actual["id"], cliente_id=cliente_id,
            condicion=condicion, forma_pago=forma_pago, tipo_documento=tipo_doc,
        )

        if not ok:
            messagebox.showerror("No se pudo procesar la venta", msg, parent=self)
            return

        # Guardar el tipo de documento en la venta (para el resumen)
        self._tipo_doc_emitido = tipo_doc
        self._venta_id_emitida = venta_id

        if imprimir:
            self._generar_e_imprimir_documento(tipo_doc, venta_id, msg)
        else:
            messagebox.showinfo("Venta cobrada", msg, parent=self)

        self.on_venta_procesada()
        self.destroy()

    def _generar_e_imprimir_documento(self, tipo_doc: str, venta_id: int, msg: str):
        """Genera e imprime el documento elegido usando el driver de
        impresoras: ticketera → texto directo (RAW/ESC-POS, sin PDF);
        Hoja A4 → PDF. Usa la impresora configurada para cada tipo de
        documento en Config. Local (o la predeterminada del sistema)."""
        import driver_impresora
        try:
            import os, tempfile
            from models_comprobante import obtener_config_local
            cfg = obtener_config_local()

            if tipo_doc == "factura":
                from models_ventas import obtener_detalle_venta
                from ventana_configuracion_local import (
                    generar_texto_factura_desde_detalle, generar_factura_pdf_desde_detalle,
                )

                # Para la factura legal se usan los datos de comprador
                # ingresados en este formulario (RUC/Razón Social), ya que
                # una "Factura Legal" siempre necesita esos datos, aunque
                # el cliente de la venta sea "Ocasional". Se arma un
                # detalle "manual" con esos datos en vez de los del cliente
                # guardado, para no tener que re-grabar la venta.
                detalle_venta = obtener_detalle_venta(venta_id)
                detalle_venta["cliente_nombre"] = self.var_razon_social_comp.get() or "Ocasional"
                detalle_venta["cliente_documento"] = self.var_ruc_comprador.get() or "-"
                if self.cliente:
                    detalle_venta["cliente_direccion"] = self.cliente.get("direccion", "-")

                formato = cfg.get("formato_factura", "a4") or "a4"
                impresora = cfg.get("impresora_factura", "") or None
                if formato == "a4":
                    ruta = os.path.join(tempfile.gettempdir(), f"factura_{venta_id}.pdf")
                    resultado = driver_impresora.imprimir_documento(
                        formato, impresora,
                        ruta_pdf_callback=lambda: (
                            generar_factura_pdf_desde_detalle(ruta, detalle_venta, formato=formato), ruta)[1],
                        nombre_trabajo=f"Factura venta {venta_id}",
                    )
                else:
                    texto = generar_texto_factura_desde_detalle(detalle_venta)
                    resultado = driver_impresora.imprimir_documento(
                        formato, impresora, texto=texto, nombre_trabajo=f"Factura venta {venta_id}",
                    )
            else:
                # Comprobante de Venta (sin datos fiscales), con el tamaño
                # de papel e impresora configurados en Config. Local →
                # pestaña Comprobante de Venta.
                from models_comprobante import generar_texto_comprobante, generar_comprobante_desde_venta
                from models_ventas import obtener_detalle_venta

                formato = cfg.get("formato_comprobante", "a4") or "a4"
                impresora = cfg.get("impresora_comprobante", "") or None
                if formato == "a4":
                    ruta = generar_comprobante_desde_venta(venta_id, formato=formato)
                    resultado = driver_impresora.imprimir_documento(
                        formato, impresora, ruta_pdf_callback=lambda: ruta,
                        nombre_trabajo=f"Comprobante venta {venta_id}",
                    )
                else:
                    detalle_venta = obtener_detalle_venta(venta_id)
                    texto = generar_texto_comprobante(detalle_venta)
                    resultado = driver_impresora.imprimir_documento(
                        formato, impresora, texto=texto, nombre_trabajo=f"Comprobante venta {venta_id}",
                    )

            tipo_txt = "Factura Legal" if tipo_doc == "factura" else "Comprobante de Venta"
            messagebox.showinfo("Venta cobrada",
                                f"{msg}\n\n📄 {tipo_txt}: {resultado}",
                                parent=self)
        except driver_impresora.ErrorImpresora as e:
            messagebox.showinfo("Venta cobrada",
                                f"{msg}\n\n⚠ No se pudo imprimir:\n{e}",
                                parent=self)
        except Exception as e:
            messagebox.showinfo("Venta cobrada",
                                f"{msg}\n\n⚠ No se pudo generar el documento:\n{e}\n"
                                "(Instalá reportlab: pip install reportlab)",
                                parent=self)

    def _generar_preventa(self):
        items_para_guardar = []
        for item in self.items_venta:
            p = item["producto"]
            if p.get("es_libre"):
                items_para_guardar.append({
                    "producto_id": None,
                    "descripcion_libre": p["nombre"],
                    "cantidad": item["cantidad"],
                    "precio_unitario": item["precio_unitario"],
                })
            else:
                items_para_guardar.append({
                    "producto_id": p["id"],
                    "cantidad": item["cantidad"],
                    "precio_unitario": item["precio_unitario"],
                })

        cliente_id = self.cliente["id"] if self.cliente else None

        from models_ventas import crear_preventa
        ok, msg, preventa_id = crear_preventa(
            items_para_guardar, usuario_id=self.usuario_actual["id"], cliente_id=cliente_id,
        )
        if not ok:
            messagebox.showerror("No se pudo generar la pre-venta", msg, parent=self)
            return

        messagebox.showinfo(
            "Pre-Venta generada",
            f"{msg}\n\nNo se descontó stock ni se generó ningún comprobante. "
            "Podés retomarla luego desde el módulo Pre-Venta.",
            parent=self,
        )
        self.on_venta_procesada()
        self.destroy()

    def _cancelar(self):
        self.destroy()