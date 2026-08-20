"""
ventana_configuracion_local.py
Módulo de configuración del local: datos que aparecen en los comprobantes
de venta y en las facturas legales paraguayas (SET/DNIT).
Incluye:
  - Pestaña "Datos del Local" — nombre, RUC, timbrado, dirección, etc.
  - Pestaña "Comprobante de Venta" — vista previa del ticket
  - Pestaña "Factura Legal" — factura según ley paraguaya, con IVA
  - Pestaña "Numeración" — secuencias de factura y comprobante
"""
import tkinter as tk
from tkinter import ttk, messagebox
import datetime

from models_comprobante import (
    obtener_config_local, guardar_config_local,
    obtener_numeracion, guardar_numeracion,
    siguiente_numero, calcular_iva, inicializar_tablas_comprobante,
    FORMATOS_IMPRESION, ancho_texto_para_formato,
)
from utilidades_ui import forzar_mayusculas, formatear_gs
from traducciones import t

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.units import cm, mm
    PDF_OK = True
except ImportError:
    PDF_OK = False

AZUL       = "#1d5fd6"
AZUL_OSC   = "#163d8c"
GRIS_FONDO = "#f4f5f7"
BLANCO     = "#ffffff"
VERDE      = "#16a34a"
ROJO       = "#dc2626"
NEGRO      = "#1e293b"
GRIS_TEXT  = "#6b7280"
GRIS_BORDE = "#e2e8f0"


# ══════════════════════════════════════════════════════════════
#  PANEL PRINCIPAL
# ══════════════════════════════════════════════════════════════
class PanelConfigLocal(tk.Frame):
    def __init__(self, parent, usuario_actual=None):
        super().__init__(parent, bg=BLANCO)
        self.usuario_actual = usuario_actual
        inicializar_tablas_comprobante()
        self.config_actual = obtener_config_local()
        self._construir_ui()

    def _construir_ui(self):
        # Encabezado
        enc = tk.Frame(self, bg=AZUL, height=54)
        enc.pack(fill="x")
        enc.pack_propagate(False)
        tk.Label(enc, text=t("configlocal_titulo"),
                 font=("Segoe UI", 15, "bold"), bg=AZUL, fg=BLANCO
                 ).pack(side="left", padx=20, pady=12)

        # Notebook
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=6)

        tab_datos  = tk.Frame(nb, bg=GRIS_FONDO)
        tab_comp   = tk.Frame(nb, bg=BLANCO)
        tab_fac    = tk.Frame(nb, bg=BLANCO)
        tab_num    = tk.Frame(nb, bg=GRIS_FONDO)

        nb.add(tab_datos, text=t("configlocal_tab_datos"))
        nb.add(tab_comp,  text=t("configlocal_tab_comprobante"))
        nb.add(tab_fac,   text=t("configlocal_tab_factura"))
        nb.add(tab_num,   text=t("configlocal_tab_numeracion"))

        self._tab_datos(tab_datos)
        self._tab_comprobante(tab_comp)
        self._tab_factura(tab_fac)
        self._tab_numeracion(tab_num)

    def _crear_panel_scrollable(self, parent, bg):
        """Crea un panel con scroll vertical (rueda del mouse/touchpad +
        scrollbar fina, que solo aparece si hace falta) y devuelve el
        frame interior donde se debe empacar el contenido. Se usa en
        columnas izquierdas largas (Comprobante de Venta, Factura Legal)
        que de otra forma quedarían cortadas si la ventana no es muy alta.
        """
        contenedor = tk.Frame(parent, bg=bg)
        canvas = tk.Canvas(contenedor, bg=bg, highlightthickness=0, bd=0, width=1, height=1)
        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)

        interior = tk.Frame(canvas, bg=bg)
        id_ventana = canvas.create_window((0, 0), window=interior, anchor="nw")

        def _actualizar(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(id_ventana, width=canvas.winfo_width())
            if interior.winfo_reqheight() > canvas.winfo_height():
                if not scrollbar.winfo_ismapped():
                    scrollbar.pack(side="right", fill="y")
            else:
                if scrollbar.winfo_ismapped():
                    scrollbar.pack_forget()

        interior.bind("<Configure>", _actualizar)
        canvas.bind("<Configure>", _actualizar)

        def _con_scroll_del_mouse(event):
            delta = event.delta
            if delta == 0:
                delta = -1 if getattr(event, "num", None) == 5 else 1
            else:
                delta = int(-1 * (delta / 120)) if abs(delta) >= 120 else -1 * delta
            canvas.yview_scroll(delta, "units")

        def _activar(event=None):
            canvas.bind_all("<MouseWheel>", _con_scroll_del_mouse)
            canvas.bind_all("<Button-4>", _con_scroll_del_mouse)
            canvas.bind_all("<Button-5>", _con_scroll_del_mouse)

        def _desactivar(event=None):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        contenedor.bind("<Enter>", _activar)
        contenedor.bind("<Leave>", _desactivar)

        return contenedor, interior

    # ══════════════════════════════════════════════════════════
    #  PESTAÑA 1: DATOS DEL LOCAL
    # ══════════════════════════════════════════════════════════
    def _tab_datos(self, parent):
        canvas_s = tk.Canvas(parent, bg=GRIS_FONDO, highlightthickness=0)
        sb = ttk.Scrollbar(parent, orient="vertical", command=canvas_s.yview)
        canvas_s.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas_s.pack(side="left", fill="both", expand=True)

        f = tk.Frame(canvas_s, bg=GRIS_FONDO)
        win = canvas_s.create_window((0, 0), window=f, anchor="nw")
        canvas_s.bind("<Configure>", lambda e: canvas_s.itemconfig(win, width=e.width))

        # ── Rueda del mouse / touchpad: sin esto, la única forma de
        # desplazarse era arrastrando la barra lateral con precisión. ──
        def _scroll_rueda(event):
            # Windows/macOS traen event.delta; Linux usa Button-4/5
            if event.num == 4:
                canvas_s.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas_s.yview_scroll(1, "units")
            else:
                canvas_s.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_scroll_recursivo(widget):
            widget.bind("<MouseWheel>", _scroll_rueda)
            widget.bind("<Button-4>", _scroll_rueda)
            widget.bind("<Button-5>", _scroll_rueda)
            for hijo in widget.winfo_children():
                _bind_scroll_recursivo(hijo)

        def _al_cambiar_contenido(e):
            canvas_s.configure(scrollregion=canvas_s.bbox("all"))
            # Los campos se crean después de este bind, así que cada vez
            # que cambia el contenido volvemos a "engancharles" la rueda.
            _bind_scroll_recursivo(f)

        f.bind("<Configure>", _al_cambiar_contenido)
        _bind_scroll_recursivo(canvas_s)

        vars_cfg = {}

        def _seccion(titulo):
            tk.Label(f, text=titulo, font=("Segoe UI", 10, "bold"),
                     bg=AZUL_OSC, fg=BLANCO, padx=12, pady=4
                     ).pack(fill="x", padx=20, pady=(12, 4))

        def _campo(label, clave, ancho=40, mayus=False):
            fila = tk.Frame(f, bg=GRIS_FONDO)
            fila.pack(fill="x", padx=24, pady=2)
            tk.Label(fila, text=label, font=("Segoe UI", 9, "bold"),
                     bg=GRIS_FONDO, width=22, anchor="w").pack(side="left")
            var = tk.StringVar(value=self.config_actual.get(clave, ""))
            entry = tk.Entry(fila, textvariable=var,
                             font=("Segoe UI", 9), width=ancho)
            entry.pack(side="left", padx=(4, 0))
            if mayus:
                forzar_mayusculas(entry, var)
            vars_cfg[clave] = var

        # ── Datos del Contribuyente ───────────────────────────
        _seccion("DATOS DEL CONTRIBUYENTE (Emisor de comprobantes)")
        _campo("Nombre / Razón Social:", "razon_social", 45, mayus=True)
        _campo("Nombre de Fantasía:",    "nombre_local",  45, mayus=True)
        _campo("RUC:",                   "ruc")
        _campo("Dirección:",             "direccion", 45, mayus=True)
        _campo("Ciudad:",                "ciudad", 30, mayus=True)
        _campo("Teléfono:",              "telefono")
        _campo("Email:",                 "email")
        _campo("Actividad Económica:",   "actividad_economica", 45, mayus=True)

        # ── Timbrado ─────────────────────────────────────────
        _seccion("TIMBRADO (Autorización SET/DNIT)")
        tk.Label(f,
                 text="ℹ  El Timbrado es la autorización del SET para emitir comprobantes.\n"
                      "    Se obtiene por el sistema Marangatu en www.set.gov.py",
                 font=("Segoe UI", 8), bg=GRIS_FONDO, fg=GRIS_TEXT,
                 justify="left").pack(anchor="w", padx=24, pady=(0, 4))
        _campo("Número de Timbrado:",    "timbrado_nro")
        _campo("Vigencia Desde (YYYY-MM-DD):", "timbrado_vigencia_desde")
        _campo("Vigencia Hasta (YYYY-MM-DD):", "timbrado_vigencia_hasta")

        # ── IVA ───────────────────────────────────────────────
        _seccion("CONFIGURACIÓN DE IVA")
        fila_iva = tk.Frame(f, bg=GRIS_FONDO)
        fila_iva.pack(fill="x", padx=24, pady=4)
        tk.Label(fila_iva, text="Tasa de IVA:", font=("Segoe UI", 9, "bold"),
                 bg=GRIS_FONDO, width=22, anchor="w").pack(side="left")
        vars_cfg["tipo_iva"] = tk.StringVar(
            value=self.config_actual.get("tipo_iva", "10"))
        for val, txt in [("10", "10% (Tasa General)"),
                          ("5",  "5%  (Bienes básicos)"),
                          ("0",  "Exento")]:
            tk.Radiobutton(fila_iva, text=txt, variable=vars_cfg["tipo_iva"],
                           value=val, bg=GRIS_FONDO,
                           font=("Segoe UI", 9)).pack(side="left", padx=8)

        fila_inc = tk.Frame(f, bg=GRIS_FONDO)
        fila_inc.pack(fill="x", padx=24, pady=2)
        tk.Label(fila_inc, text="Precios incluyen IVA:",
                 font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO,
                 width=22, anchor="w").pack(side="left")
        vars_cfg["incluye_iva"] = tk.BooleanVar(
            value=self.config_actual.get("incluye_iva", "1") == "1")
        tk.Checkbutton(fila_inc, variable=vars_cfg["incluye_iva"],
                       bg=GRIS_FONDO,
                       text="Sí, los precios ya incluyen el IVA"
                       ).pack(side="left")

        # ── Pie del comprobante ────────────────────────────────
        _seccion("MENSAJE EN EL PIE DEL COMPROBANTE")
        fila_pie = tk.Frame(f, bg=GRIS_FONDO)
        fila_pie.pack(fill="x", padx=24, pady=2)
        tk.Label(fila_pie, text="Mensaje de pie:", font=("Segoe UI", 9, "bold"),
                 bg=GRIS_FONDO, width=22, anchor="w").pack(side="left")
        vars_cfg["mensaje_pie"] = tk.StringVar(
            value=self.config_actual.get("mensaje_pie", ""))
        tk.Entry(fila_pie, textvariable=vars_cfg["mensaje_pie"],
                 font=("Segoe UI", 9), width=45).pack(side="left", padx=4)

        # ── Botón Guardar ─────────────────────────────────────
        pie = tk.Frame(f, bg=GRIS_FONDO)
        pie.pack(fill="x", padx=20, pady=16)

        def _guardar():
            datos = {}
            for clave, var in vars_cfg.items():
                if isinstance(var, tk.BooleanVar):
                    datos[clave] = "1" if var.get() else "0"
                else:
                    datos[clave] = var.get().strip()
            guardar_config_local(datos)
            self.config_actual = obtener_config_local()
            messagebox.showinfo("Guardado",
                                "Configuración guardada correctamente.")

        btn_g = tk.Button(pie, text="💾 Guardar Configuración",
                          font=("Segoe UI", 10, "bold"),
                          bg=VERDE, fg=BLANCO, relief="flat",
                          padx=20, pady=8, cursor="hand2",
                          command=_guardar)
        btn_g.pack(side="left")
        btn_g.bind("<Return>", lambda e: _guardar())

    # ══════════════════════════════════════════════════════════
    #  PESTAÑA 2: COMPROBANTE DE VENTA
    # ══════════════════════════════════════════════════════════
    def _tab_comprobante(self, parent):
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

        # Panel izquierdo: configuración (con scroll, para que nada quede
        # cortado sin importar cuántas líneas tenga la explicación ni el
        # tamaño de la ventana)
        contenedor_izq, izq = self._crear_panel_scrollable(parent, GRIS_FONDO)
        contenedor_izq.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)

        tk.Label(izq, text="Vista previa del comprobante",
                 font=("Segoe UI", 10, "bold"), bg=GRIS_FONDO
                 ).pack(anchor="w", pady=(0, 8))

        # --- Selector de tamaño de papel (A4 / Ticketera) ---
        cfg_actual = obtener_config_local()
        self._var_formato_comp = tk.StringVar(
            value=cfg_actual.get("formato_comprobante", "a4") or "a4")

        frame_formato = tk.LabelFrame(izq, text="Tamaño de impresión",
                                      font=("Segoe UI", 9, "bold"),
                                      bg=GRIS_FONDO, padx=10, pady=6)
        frame_formato.pack(fill="x", pady=(0, 10))
        for valor, spec in FORMATOS_IMPRESION.items():
            tk.Radiobutton(frame_formato, text=spec["etiqueta"],
                          variable=self._var_formato_comp, value=valor,
                          font=("Segoe UI", 9), bg=GRIS_FONDO,
                          command=self._cambiar_formato_comprobante,
                          ).pack(anchor="w")

        # --- Selector de impresora (cualquier impresora instalada: normal
        # o ticketera, de cualquier marca) ---
        import driver_impresora
        PREDETERMINADA = "(Predeterminada del sistema)"
        frame_impresora_comp = tk.LabelFrame(izq, text="Impresora para el Comprobante de Venta",
                                             font=("Segoe UI", 9, "bold"),
                                             bg=GRIS_FONDO, padx=10, pady=6)
        frame_impresora_comp.pack(fill="x", pady=(0, 10))
        impresoras_detectadas = driver_impresora.listar_impresoras()
        valores_imp = [PREDETERMINADA] + impresoras_detectadas
        combo_impresora_comp = ttk.Combobox(frame_impresora_comp, state="readonly",
                                            values=valores_imp, width=32)
        guardada_comp = cfg_actual.get("impresora_comprobante", "")
        combo_impresora_comp.current(
            valores_imp.index(guardada_comp) if guardada_comp in impresoras_detectadas else 0)
        combo_impresora_comp.pack(anchor="w")

        def _guardar_impresora_comp(event=None):
            valor = combo_impresora_comp.get()
            guardar_config_local({"impresora_comprobante": "" if valor == PREDETERMINADA else valor})

        combo_impresora_comp.bind("<<ComboboxSelected>>", _guardar_impresora_comp)
        if not impresoras_detectadas:
            tk.Label(frame_impresora_comp, text="No se detectaron impresoras instaladas en este equipo.",
                     font=("Segoe UI", 8, "italic"), bg=GRIS_FONDO, fg="#888").pack(anchor="w", pady=(4, 0))

        tk.Label(izq,
                 text="El comprobante de venta se genera automáticamente\n"
                      "con los datos configurados en la pestaña\n"
                      "'Datos del Local'.\n\n"
                      "Campos que aparecen:\n"
                      "• Nombre / Razón Social\n"
                      "• RUC\n"
                      "• Timbrado y vigencia\n"
                      "• Dirección y teléfono\n"
                      "• Número correlativo (001-001-XXXXXXX)\n"
                      "• Fecha y hora de emisión\n"
                      "• Cliente y CI/RUC\n"
                      "• Condición de venta (Contado/Crédito)\n"
                      "• Detalle de artículos con precio y subtotal\n"
                      "• Total en Gs.\n"
                      "• Liquidación del IVA (5% o 10%)\n"
                      "• Mensaje de pie configurado",
                 font=("Segoe UI", 9), bg=GRIS_FONDO, justify="left"
                 ).pack(anchor="w", padx=8)

        tk.Button(izq, text="📄 Generar Comprobante PDF de Ejemplo",
                  font=("Segoe UI", 9), bg=AZUL, fg=BLANCO,
                  relief="flat", padx=12, pady=6, cursor="hand2",
                  command=self._generar_comprobante_ejemplo
                  ).pack(anchor="w", padx=8, pady=8)

        if not PDF_OK:
            tk.Label(izq, text="⚠ Instalar reportlab para generar PDF",
                     font=("Segoe UI", 8), bg=GRIS_FONDO, fg=ROJO
                     ).pack(anchor="w", padx=8)

        # Panel derecho: vista previa
        der = tk.Frame(parent, bg=BLANCO, relief="solid", bd=1)
        der.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)

        self._vista_comprobante = tk.Text(
            der, font=("Courier New", 8), width=58, state="disabled",
            bg="#fffef7", relief="flat", padx=8, pady=8, wrap="none")
        self._vista_comprobante.pack(fill="both", expand=True)

        tk.Button(parent, text="🔄 Actualizar Vista Previa",
                  font=("Segoe UI", 9), bg=AZUL, fg=BLANCO,
                  relief="flat", padx=12, pady=4, cursor="hand2",
                  command=self._actualizar_vista_comprobante
                  ).grid(row=1, column=0, columnspan=2, pady=6)

        self._actualizar_vista_comprobante()

    def _cambiar_formato_comprobante(self):
        guardar_config_local({"formato_comprobante": self._var_formato_comp.get()})
        self._actualizar_vista_comprobante()

    def _actualizar_vista_comprobante(self):
        cfg = obtener_config_local()
        ahora = datetime.datetime.now()
        num = "001-001-0000001"
        ancho = ancho_texto_para_formato(self._var_formato_comp.get())

        def lim(texto: str) -> str:
            """Recorta una línea simple al ancho de papel para que nunca
            se salga del recuadro de vista previa."""
            return texto[:ancho]

        lineas = []
        lineas.append("=" * ancho)
        lineas.append(f"{cfg.get('razon_social','NOMBRE LOCAL')[:ancho]:^{ancho}}")
        if cfg.get("nombre_local"):
            lineas.append(f"{cfg['nombre_local'][:ancho]:^{ancho}}")
        lineas.append(lim(f"RUC: {cfg.get('ruc','-')}"))
        lineas.append(f"{cfg.get('direccion','Dirección')[:ancho]}")
        lineas.append(lim(f"Tel: {cfg.get('telefono','-')}"))
        lineas.append("-" * ancho)
        lineas.append(f"{'COMPROBANTE DE VENTA':^{ancho}}")
        lineas.append(f"{'** NO VÁLIDO PARA USO LEGAL **':^{ancho}}")
        lineas.append(lim(f"Timbrado Nº: {cfg.get('timbrado_nro','-')}"))
        lineas.append(lim(f"Vigencia: {cfg.get('timbrado_vigencia_desde','-')} al "
                      f"{cfg.get('timbrado_vigencia_hasta','-')}"))
        lineas.append("-" * ancho)
        lineas.append(lim(f"Comp. Nº: {num}"))
        lineas.append(lim(f"Fecha: {ahora.strftime('%d/%m/%Y %H:%M')}"))
        lineas.append(lim(f"Condición: CONTADO"))
        lineas.append(lim(f"Cliente: Ocasional"))
        lineas.append(lim(f"CI/RUC: -"))
        lineas.append("-" * ancho)
        ancho_desc = max(ancho - 19, 3)
        descripcion_ejemplo = "PRODUCTO EJEMPLO"[:ancho_desc]
        lineas.append(f"{'CANT':<5}{'DESCRIPCIÓN'[:ancho_desc]:<{ancho_desc}}{'IMPORTE':>14}")
        lineas.append(f"{'1':<5}{descripcion_ejemplo:<{ancho_desc}}{formatear_gs(2000):>14}")
        lineas.append("-" * ancho)
        tasa = int(cfg.get("tipo_iva", "10"))
        inc  = cfg.get("incluye_iva", "1") == "1"
        iva_d = calcular_iva(2000, tasa, inc)
        lineas.append(f"{'TOTAL':<{max(ancho-14, 5)}}{formatear_gs(2000):>14}")
        lineas.append(lim(f"Liquidación IVA ({tasa}%)"))
        lineas.append(lim(f"Base imponible: {formatear_gs(iva_d['base_imponible'])}"))
        lineas.append(lim(f"IVA ({tasa}%): {formatear_gs(iva_d['iva'])}"))
        lineas.append("-" * ancho)
        if cfg.get("mensaje_pie"):
            lineas.append(f"{cfg['mensaje_pie'][:ancho]:^{ancho}}")
        lineas.append("=" * ancho)

        txt = "\n".join(lineas)
        self._vista_comprobante.config(state="normal")
        self._vista_comprobante.delete("1.0", "end")
        self._vista_comprobante.insert("1.0", txt)
        self._vista_comprobante.config(state="disabled")

    def _generar_comprobante_ejemplo(self):
        if not PDF_OK:
            messagebox.showerror("Error",
                "Instalá reportlab para generar PDF:\n"
                "pip install reportlab")
            return
        from tkinter import filedialog
        from models_comprobante import generar_pdf_comprobante
        ruta = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="comprobante_ejemplo.pdf")
        if not ruta:
            return

        detalle_ejemplo = {
            "id": 1, "fecha": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
            "total": 2000, "condicion": "contado", "forma_pago": "Efectivo",
            "estado": "Activo", "cliente_nombre": "Ocasional", "cliente_documento": "",
            "lineas": [{
                "detalle_id": 1, "producto_id": 1, "nombre_producto": "PRODUCTO EJEMPLO",
                "cantidad": 1, "precio_unitario": 2000, "cantidad_devuelta": 0,
                "cantidad_activa": 1, "importe": 2000,
            }],
        }
        generar_pdf_comprobante(ruta, detalle_ejemplo, formato=self._var_formato_comp.get())
        messagebox.showinfo("PDF generado", f"Comprobante guardado en:\n{ruta}")

    # ══════════════════════════════════════════════════════════
    #  PESTAÑA 3: FACTURA LEGAL
    # ══════════════════════════════════════════════════════════
    def _tab_factura(self, parent):
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

        # Izquierda: explicación legal (con scroll, porque es una lista
        # larga de requisitos legales que no siempre entra completa)
        contenedor_izq, izq = self._crear_panel_scrollable(parent, GRIS_FONDO)
        contenedor_izq.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)

        tk.Label(izq, text="Factura Legal Paraguaya (SET/DNIT)",
                 font=("Segoe UI", 10, "bold"), bg=GRIS_FONDO
                 ).pack(anchor="w", pady=(0, 6))

        # --- Selector de tamaño de papel (A4 / Ticketera) ---
        cfg_actual = obtener_config_local()
        self._var_formato_fac = tk.StringVar(
            value=cfg_actual.get("formato_factura", "a4") or "a4")

        frame_formato_fac = tk.LabelFrame(izq, text="Tamaño de impresión",
                                          font=("Segoe UI", 9, "bold"),
                                          bg=GRIS_FONDO, padx=10, pady=6)
        frame_formato_fac.pack(fill="x", pady=(0, 10))
        for valor, spec in FORMATOS_IMPRESION.items():
            tk.Radiobutton(frame_formato_fac, text=spec["etiqueta"],
                          variable=self._var_formato_fac, value=valor,
                          font=("Segoe UI", 9), bg=GRIS_FONDO,
                          command=self._cambiar_formato_factura,
                          ).pack(anchor="w")
        tk.Label(frame_formato_fac,
                 text="Nota: en tamaño ticketera la factura se imprime\n"
                      "en formato condensado, en una sola columna.",
                 font=("Segoe UI", 7), bg=GRIS_FONDO, fg=GRIS_TEXT,
                 justify="left").pack(anchor="w", pady=(4, 0))

        # --- Selector de impresora (cualquier impresora instalada: normal
        # o ticketera, de cualquier marca) ---
        import driver_impresora
        PREDETERMINADA = "(Predeterminada del sistema)"
        frame_impresora_fac = tk.LabelFrame(izq, text="Impresora para la Factura Legal",
                                            font=("Segoe UI", 9, "bold"),
                                            bg=GRIS_FONDO, padx=10, pady=6)
        frame_impresora_fac.pack(fill="x", pady=(0, 10))
        impresoras_detectadas_fac = driver_impresora.listar_impresoras()
        valores_imp_fac = [PREDETERMINADA] + impresoras_detectadas_fac
        combo_impresora_fac = ttk.Combobox(frame_impresora_fac, state="readonly",
                                           values=valores_imp_fac, width=32)
        guardada_fac = cfg_actual.get("impresora_factura", "")
        combo_impresora_fac.current(
            valores_imp_fac.index(guardada_fac) if guardada_fac in impresoras_detectadas_fac else 0)
        combo_impresora_fac.pack(anchor="w")

        def _guardar_impresora_fac(event=None):
            valor = combo_impresora_fac.get()
            guardar_config_local({"impresora_factura": "" if valor == PREDETERMINADA else valor})

        combo_impresora_fac.bind("<<ComboboxSelected>>", _guardar_impresora_fac)
        if not impresoras_detectadas_fac:
            tk.Label(frame_impresora_fac, text="No se detectaron impresoras instaladas en este equipo.",
                     font=("Segoe UI", 8, "italic"), bg=GRIS_FONDO, fg="#888").pack(anchor="w", pady=(4, 0))

        info = (
            "Campos OBLIGATORIOS según Decreto 6.539/2005\n"
            "y Resolución General SET:\n\n"
            "DATOS PREIMPRESOS (en la imprenta):\n"
            "  ✓ Número de Timbrado\n"
            "  ✓ RUC del emisor\n"
            "  ✓ Razón Social del emisor\n"
            "  ✓ Dirección del establecimiento\n"
            "  ✓ Actividad económica\n"
            "  ✓ Vigencia del timbrado\n"
            "  ✓ Numeración: XXX-XXX-XXXXXXX\n"
            "  ✓ Datos de la imprenta habilitante\n\n"
            "DATOS AL EMITIR:\n"
            "  ✓ Fecha de emisión\n"
            "  ✓ RUC o CI del comprador\n"
            "  ✓ Nombre / Razón Social del comprador\n"
            "  ✓ Dirección del comprador\n"
            "  ✓ Condición de venta (Contado/Crédito)\n"
            "  ✓ Cantidad, descripción, precio unitario\n"
            "  ✓ Valor de venta\n"
            "  ✓ Subtotales Exentas / IVA 5% / IVA 10%\n"
            "  ✓ Total a pagar\n"
            "  ✓ Liquidación del IVA\n\n"
            "NOTA: La factura pre-impresa requiere\n"
            "timbrado vigente del SET. Sin timbrado\n"
            "el documento NO tiene validez legal.\n"
            "Obtener timbrado en: www.set.gov.py"
        )
        tk.Label(izq, text=info, font=("Segoe UI", 8),
                 bg=GRIS_FONDO, justify="left"
                 ).pack(anchor="w", padx=8)

        tk.Button(izq, text="📄 Generar Factura PDF de Ejemplo",
                  font=("Segoe UI", 9), bg=AZUL, fg=BLANCO,
                  relief="flat", padx=12, pady=6, cursor="hand2",
                  command=self._generar_factura_ejemplo
                  ).pack(anchor="w", padx=8, pady=8)

        if not PDF_OK:
            tk.Label(izq, text="⚠ Instalar reportlab para generar PDF",
                     font=("Segoe UI", 8), bg=GRIS_FONDO, fg=ROJO
                     ).pack(anchor="w", padx=8)

        # Derecha: vista previa de la factura
        der = tk.Frame(parent, bg=BLANCO, relief="solid", bd=1)
        der.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)

        self._vista_factura = tk.Text(
            der, font=("Courier New", 8), width=58, state="disabled",
            bg="#fffff8", relief="flat", padx=8, pady=8, wrap="none")
        self._vista_factura.pack(fill="both", expand=True)

        tk.Button(parent, text="🔄 Actualizar Vista Previa",
                  font=("Segoe UI", 9), bg=AZUL, fg=BLANCO,
                  relief="flat", padx=12, pady=4, cursor="hand2",
                  command=self._actualizar_vista_factura
                  ).grid(row=1, column=0, columnspan=2, pady=6)

        self._actualizar_vista_factura()

    def _cambiar_formato_factura(self):
        guardar_config_local({"formato_factura": self._var_formato_fac.get()})
        self._actualizar_vista_factura()

    def _actualizar_vista_factura(self):
        cfg = obtener_config_local()
        ahora = datetime.datetime.now()
        txt = generar_texto_factura(
            cfg=cfg, numero="001-001-0000001", fecha=ahora,
            cliente="JUAN PEREZ", ruc_cliente="12345678-9",
            direccion_cliente="ASUNCION", condicion="CONTADO",
            items=[{"cantidad": 1, "descripcion": "PRODUCTO EJEMPLO",
                    "precio_unitario": 18000, "total": 18000}],
            total=18000,
            ancho=ancho_texto_para_formato(self._var_formato_fac.get()),
        )
        self._vista_factura.config(state="normal")
        self._vista_factura.delete("1.0", "end")
        self._vista_factura.insert("1.0", txt)
        self._vista_factura.config(state="disabled")

    def _generar_factura_ejemplo(self):
        if not PDF_OK:
            messagebox.showerror("Error",
                "Instalá reportlab para generar PDF:\n"
                "pip install reportlab")
            return
        from tkinter import filedialog
        ruta = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="factura_ejemplo.pdf")
        if not ruta:
            return
        generar_factura_pdf(
            ruta=ruta,
            cfg=obtener_config_local(),
            numero="001-001-0000001",
            fecha=datetime.datetime.now(),
            cliente="JUAN PEREZ",
            ruc_cliente="12345678-9",
            direccion_cliente="ASUNCION",
            condicion="CONTADO",
            items=[{"cantidad": 1, "descripcion": "PRODUCTO EJEMPLO",
                    "precio_unitario": 18000, "total": 18000}],
            total=18000,
            formato=self._var_formato_fac.get(),
        )
        messagebox.showinfo("PDF generado", f"Factura guardada en:\n{ruta}")

    # ══════════════════════════════════════════════════════════
    #  PESTAÑA 4: NUMERACIÓN
    # ══════════════════════════════════════════════════════════
    def _tab_numeracion(self, parent):
        f = tk.Frame(parent, bg=GRIS_FONDO, padx=24, pady=16)
        f.pack(fill="both", expand=True)

        tk.Label(f,
                 text="Configuración de Numeración de Documentos",
                 font=("Segoe UI", 12, "bold"), bg=GRIS_FONDO
                 ).pack(anchor="w", pady=(0, 4))
        tk.Label(f,
                 text="El formato es: ESTABLECIMIENTO-PUNTO_EXP-NÚMERO\n"
                      "Ejemplo: 001-001-0000001\n"
                      "El número se incrementa automáticamente en cada documento emitido.",
                 font=("Segoe UI", 9), bg=GRIS_FONDO, fg=GRIS_TEXT
                 ).pack(anchor="w", pady=(0, 12))

        vars_num = {}
        for tipo, etiqueta in [("factura", "📄 Factura Legal"),
                                ("comprobante", "🧾 Comprobante de Venta")]:
            num = obtener_numeracion(tipo)

            frame_t = tk.LabelFrame(f, text=etiqueta,
                                    font=("Segoe UI", 9, "bold"),
                                    bg=GRIS_FONDO, padx=12, pady=8)
            frame_t.pack(fill="x", pady=6)

            vars_num[tipo] = {}
            for lbl, key, val in [
                ("Establecimiento (3 dígitos):", "establecimiento", num["establecimiento"]),
                ("Punto de Expedición (3 dígitos):", "punto_exp", num["punto_exp"]),
                ("Último número emitido:", "ultimo_numero", str(num["ultimo_numero"])),
            ]:
                fila = tk.Frame(frame_t, bg=GRIS_FONDO)
                fila.pack(fill="x", pady=2)
                tk.Label(fila, text=lbl, font=("Segoe UI", 9),
                         bg=GRIS_FONDO, width=30, anchor="w").pack(side="left")
                var = tk.StringVar(value=val)
                tk.Entry(fila, textvariable=var,
                         font=("Segoe UI", 9), width=12).pack(side="left")
                vars_num[tipo][key] = var

            prox = num["ultimo_numero"] + 1
            tk.Label(frame_t,
                     text=f"  Próximo número: {num['establecimiento']}-{num['punto_exp']}-{prox:07d}",
                     font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO, fg=AZUL
                     ).pack(anchor="w")

        def _guardar_num():
            for tipo in ("factura", "comprobante"):
                try:
                    guardar_numeracion(
                        tipo,
                        vars_num[tipo]["establecimiento"].get().strip().zfill(3),
                        vars_num[tipo]["punto_exp"].get().strip().zfill(3),
                        int(vars_num[tipo]["ultimo_numero"].get() or 0),
                    )
                except ValueError:
                    messagebox.showerror("Error",
                        f"El campo 'último número' de {tipo} debe ser un número.")
                    return
            messagebox.showinfo("Guardado", "Numeración guardada correctamente.")

        btn_n = tk.Button(f, text="💾 Guardar Numeración",
                          font=("Segoe UI", 10, "bold"),
                          bg=VERDE, fg=BLANCO, relief="flat",
                          padx=20, pady=8, cursor="hand2",
                          command=_guardar_num)
        btn_n.pack(anchor="w", pady=12)
        btn_n.bind("<Return>", lambda e: _guardar_num())


# ══════════════════════════════════════════════════════════════
#  TEXTO DE LA FACTURA (reutilizado por la vista previa y por el
#  PDF en tamaño ticketera)
# ══════════════════════════════════════════════════════════════
def generar_texto_factura(cfg: dict, numero: str, fecha: datetime.datetime,
                          cliente: str, ruc_cliente: str, direccion_cliente: str,
                          condicion: str, items: list, total: float,
                          ancho: int = 52) -> str:
    tasa = int(cfg.get("tipo_iva", "10") or "10")
    inc  = cfg.get("incluye_iva", "1") == "1"
    iva_d = calcular_iva(total, tasa, inc)
    interior = ancho - 4

    L = []
    borde = "═" * ancho
    L.append(borde)
    L.append(f"{cfg.get('razon_social','RAZÓN SOCIAL')[:interior]:^{interior}}")
    if cfg.get("nombre_local"):
        L.append(f"{cfg['nombre_local'][:interior]:^{interior}}")
    L.append(f"RUC: {cfg.get('ruc','-')}  Act.: {cfg.get('actividad_economica','')}"[:ancho])
    L.append(f"Dir: {cfg.get('direccion','')}"[:ancho])
    L.append(f"{cfg.get('ciudad','')} - Tel: {cfg.get('telefono','')}"[:ancho])
    L.append("-" * ancho)
    L.append(f"{'FACTURA':^{interior}}")
    L.append(f"Timbrado Nº: {cfg.get('timbrado_nro','-')}"[:ancho])
    L.append((f"Vigencia: {cfg.get('timbrado_vigencia_desde','-')} al "
              f"{cfg.get('timbrado_vigencia_hasta','-')}")[:ancho])
    L.append(f"Número: {numero}"[:ancho])
    L.append("-" * ancho)
    L.append(f"Fecha: {fecha.strftime('%d/%m/%Y %H:%M:%S')}"[:ancho])
    L.append(f"Condición: {condicion}"[:ancho])
    L.append(f"Señor(es): {cliente}"[:ancho])
    L.append(f"RUC/CI: {ruc_cliente}"[:ancho])
    L.append(f"Dirección: {direccion_cliente}"[:ancho])
    L.append("-" * ancho)

    # --- Tabla de ítems: el ancho de las columnas de precio se calcula
    # según el importe más largo, para que P.UNIT y TOTAL nunca se corten
    # ni se encimen entre sí, sea cual sea el monto. ---
    montos_items = []
    for item in items:
        montos_items.append(formatear_gs(item["precio_unitario"]))
        montos_items.append(formatear_gs(item["total"]))
    col_monto = max([len(m) for m in montos_items] + [len("P.UNIT"), len("TOTAL"), 8]) + 1
    ancho_desc = max(ancho - 5 - 2 * col_monto, 3)
    L.append(f"{'CANT':<5}{'DESCRIPCIÓN'[:ancho_desc]:<{ancho_desc}}{'P.UNIT':>{col_monto}}{'TOTAL':>{col_monto}}"[:ancho])
    for item in items:
        cant = str(item["cantidad"])
        desc = str(item["descripcion"])[:ancho_desc]
        p_unit = formatear_gs(item["precio_unitario"])
        subtotal = formatear_gs(item["total"])
        linea = f"{cant:<5}{desc:<{ancho_desc}}{p_unit:>{col_monto}}{subtotal:>{col_monto}}"
        if len(linea) <= ancho:
            L.append(linea)
        else:
            # Papel angosto: cada dato del ítem va en su propia línea para
            # que ningún importe se corte ni se pegue con el siguiente.
            L.append(f"{cant} x {desc}"[:ancho])
            L.append(f"  P.Unit: {p_unit}"[:ancho])
            L.append(f"  Total:  {subtotal}"[:ancho])
    L.append("-" * ancho)

    # --- Total y liquidación del IVA: ancho de columna de importe según
    # el monto más largo entre total e IVA, para que jamás se corte. ---
    col_total = max(10, len(formatear_gs(total)), len(formatear_gs(iva_d["iva"])),
                    len(formatear_gs(iva_d["base_imponible"]))) + 1
    L.append((f"{'TOTAL A PAGAR':<{max(ancho - col_total, 10)}}{formatear_gs(total):>{col_total}}")[:ancho])
    L.append("-" * ancho)
    L.append("LIQUIDACIÓN DEL IMPUESTO"[:ancho])
    L.append(f"{'Exentas:':<14}{formatear_gs(0):>{col_total}}"[:ancho])
    if tasa == 10:
        L.append(f"{'Gravadas 10%:':<14}{formatear_gs(iva_d['base_imponible']):>{col_total}}"[:ancho])
        L.append(f"{'IVA (10%):':<14}{formatear_gs(iva_d['iva']):>{col_total}}"[:ancho])
        L.append(f"{'Gravadas 5%:':<14}{formatear_gs(0):>{col_total}}"[:ancho])
        L.append(f"{'IVA (5%):':<14}{formatear_gs(0):>{col_total}}"[:ancho])
    else:
        L.append(f"{'Gravadas 5%:':<14}{formatear_gs(iva_d['base_imponible']):>{col_total}}"[:ancho])
        L.append(f"{'IVA (5%):':<14}{formatear_gs(iva_d['iva']):>{col_total}}"[:ancho])
        L.append(f"{'Gravadas 10%:':<14}{formatear_gs(0):>{col_total}}"[:ancho])
        L.append(f"{'IVA (10%):':<14}{formatear_gs(0):>{col_total}}"[:ancho])
    L.append(f"{'TOTAL IVA:':<14}{formatear_gs(iva_d['iva']):>{col_total}}"[:ancho])
    L.append("=" * ancho)
    if cfg.get("mensaje_pie"):
        L.append(f"{cfg['mensaje_pie'][:interior]:^{interior}}")
    L.append(borde)
    return "\n".join(L)


def generar_texto_factura_desde_detalle(detalle: dict, ancho: int = None) -> str:
    """Arma el texto de la Factura Legal (igual formato que se ve en la
    vista previa de Config. Local → Factura Legal) a partir del detalle de
    una venta ya registrada (dict devuelto por obtener_detalle_venta).
    Si no se indica 'ancho', usa el tamaño de papel configurado en la
    pestaña Factura Legal."""
    cfg = obtener_config_local()
    if ancho is None:
        formato = cfg.get("formato_factura", "a4") or "a4"
        ancho = ancho_texto_para_formato(formato)

    numero = detalle.get("nro_factura") or "001-001-0000000"
    try:
        fecha = datetime.datetime.strptime(detalle["fecha"], "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        fecha = datetime.datetime.now()

    items = [
        {
            "cantidad": l["cantidad_activa"],
            "descripcion": l["nombre_producto"],
            "precio_unitario": l["precio_unitario"],
            "total": l["importe"],
        }
        for l in detalle["lineas"] if l["cantidad_activa"] > 0
    ]

    return generar_texto_factura(
        cfg=cfg, numero=numero, fecha=fecha,
        cliente=detalle["cliente_nombre"], ruc_cliente=detalle["cliente_documento"] or "-",
        direccion_cliente=detalle.get("cliente_direccion", "-"),
        condicion=detalle["condicion"].upper(),
        items=items, total=detalle["total"], ancho=ancho,
    )


def generar_factura_pdf_desde_detalle(ruta: str, detalle: dict, formato: str = None) -> str:
    """Genera el PDF de la Factura Legal directamente a partir del detalle
    de una venta ya registrada (dict de obtener_detalle_venta), en la ruta
    indicada. Si no se pasa 'formato', usa el configurado en Config. Local
    → Factura Legal. Devuelve la ruta del PDF generado."""
    cfg = obtener_config_local()
    if formato is None:
        formato = cfg.get("formato_factura", "a4") or "a4"

    numero = detalle.get("nro_factura") or "001-001-0000000"
    try:
        fecha = datetime.datetime.strptime(detalle["fecha"], "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        fecha = datetime.datetime.now()

    items = [
        {
            "cantidad": l["cantidad_activa"],
            "descripcion": l["nombre_producto"],
            "precio_unitario": l["precio_unitario"],
            "total": l["importe"],
        }
        for l in detalle["lineas"] if l["cantidad_activa"] > 0
    ]

    generar_factura_pdf(
        ruta=ruta, cfg=cfg, numero=numero, fecha=fecha,
        cliente=detalle["cliente_nombre"], ruc_cliente=detalle["cliente_documento"] or "-",
        direccion_cliente=detalle.get("cliente_direccion", "-"),
        condicion=detalle["condicion"].upper(),
        items=items, total=detalle["total"], formato=formato,
    )
    return ruta


# ══════════════════════════════════════════════════════════════
#  GENERADOR DE FACTURA PDF (reportlab)
# ══════════════════════════════════════════════════════════════
def generar_factura_pdf(ruta: str, cfg: dict, numero: str,
                        fecha: datetime.datetime,
                        cliente: str, ruc_cliente: str,
                        direccion_cliente: str, condicion: str,
                        items: list, total: float, formato: str = "a4"):
    """Genera la factura legal paraguaya en PDF.
    'formato': 'a4' (hoja completa, diseño detallado) o
    'ticket80'/'ticket58' (impresora ticketera, formato condensado)."""
    if not PDF_OK:
        return

    if formato != "a4":
        _generar_factura_pdf_ticket(ruta, cfg, numero, fecha, cliente, ruc_cliente,
                                    direccion_cliente, condicion, items, total, formato)
        return

    c = rl_canvas.Canvas(ruta, pagesize=A4)
    ancho, alto = A4
    y = alto - 1.5*cm

    def txt(x_cm, y_pos, texto, size=9, bold=False):
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(x_cm * cm, y_pos, str(texto))

    def linea(y_pos, grosor=0.5):
        c.setLineWidth(grosor)
        c.line(1.5*cm, y_pos, ancho - 1.5*cm, y_pos)

    tasa     = int(cfg.get("tipo_iva", "10"))
    inc_iva  = cfg.get("incluye_iva", "1") == "1"
    iva_d    = calcular_iva(total, tasa, inc_iva)

    # ── Encabezado ────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(ancho/2, y, cfg.get("razon_social", "RAZÓN SOCIAL"))
    y -= 0.5*cm
    c.setFont("Helvetica", 10)
    if cfg.get("nombre_local"):
        c.drawCentredString(ancho/2, y, cfg["nombre_local"])
        y -= 0.4*cm
    c.drawCentredString(ancho/2, y,
        f"RUC: {cfg.get('ruc','-')}  -  Act.: {cfg.get('actividad_economica','')}")
    y -= 0.4*cm
    c.drawCentredString(ancho/2, y, cfg.get("direccion", ""))
    y -= 0.4*cm
    c.drawCentredString(ancho/2, y,
        f"{cfg.get('ciudad','')}  -  Tel.: {cfg.get('telefono','')}")

    # ── Cuadro de Factura (lado derecho) ─────────────────────
    y_box = alto - 1.5*cm
    c.setLineWidth(1)
    c.rect(ancho - 7*cm, y_box - 3*cm, 5.5*cm, 3*cm)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(ancho - 3.75*cm, y_box - 0.7*cm, "FACTURA")
    c.setFont("Helvetica", 8)
    c.drawString(ancho - 6.8*cm, y_box - 1.3*cm,
                 f"Timbrado Nº: {cfg.get('timbrado_nro','-')}")
    c.drawString(ancho - 6.8*cm, y_box - 1.7*cm,
                 f"Vigente: {cfg.get('timbrado_vigencia_desde','-')}")
    c.drawString(ancho - 6.8*cm, y_box - 2.1*cm,
                 f"   al: {cfg.get('timbrado_vigencia_hasta','-')}")
    c.drawString(ancho - 6.8*cm, y_box - 2.5*cm,
                 f"Nº: {numero}")

    # ── Datos del comprador ───────────────────────────────────
    y -= 0.6*cm
    linea(y)
    y -= 0.5*cm
    txt(1.5, y, f"Fecha: {fecha.strftime('%d/%m/%Y %H:%M')}  -  Condición: {condicion}", 9)
    y -= 0.5*cm
    txt(1.5, y, f"Señor(es): {cliente}", 9, bold=True)
    y -= 0.45*cm
    txt(1.5, y, f"RUC/CI: {ruc_cliente}  -  Dirección: {direccion_cliente}", 9)
    y -= 0.3*cm
    linea(y)

    # ── Cabecera de tabla ─────────────────────────────────────
    y -= 0.5*cm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(1.5*cm,   y, "CANT.")
    c.drawString(3.5*cm,   y, "DESCRIPCIÓN")
    c.drawRightString(14*cm, y, "P. UNIT.")
    c.drawRightString(17.5*cm, y, "TOTAL")
    y -= 0.2*cm
    linea(y)

    # ── Ítems ─────────────────────────────────────────────────
    c.setFont("Helvetica", 9)
    for item in items:
        y -= 0.45*cm
        c.drawString(1.5*cm, y, str(item["cantidad"]))
        c.drawString(3.5*cm, y, str(item["descripcion"])[:42])
        c.drawRightString(14*cm, y, formatear_gs(item["precio_unitario"]))
        c.drawRightString(17.5*cm, y, formatear_gs(item["total"]))

    # ── Total y liquidación IVA ───────────────────────────────
    y -= 0.4*cm
    linea(y)
    y -= 0.5*cm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(12*cm, y, "TOTAL A PAGAR:")
    c.drawRightString(17.5*cm, y, formatear_gs(total))

    y -= 0.6*cm
    linea(y)
    y -= 0.5*cm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(1.5*cm, y, "LIQUIDACIÓN DEL IMPUESTO")
    y -= 0.45*cm
    c.setFont("Helvetica", 8)
    c.drawString(1.5*cm, y, "Exentas:")
    c.drawRightString(8*cm, y, formatear_gs(0))
    y -= 0.4*cm
    lbl10 = "Gravadas 10%:" if tasa == 10 else "Gravadas 5%:"
    iva_lbl = f"IVA ({tasa}%):"
    c.drawString(1.5*cm, y, lbl10)
    c.drawRightString(8*cm, y, formatear_gs(iva_d["base_imponible"]))
    y -= 0.4*cm
    c.drawString(1.5*cm, y, iva_lbl)
    c.drawRightString(8*cm, y, formatear_gs(iva_d["iva"]))

    # ── Pie ───────────────────────────────────────────────────
    if cfg.get("mensaje_pie"):
        y -= 0.6*cm
        linea(y)
        y -= 0.4*cm
        c.setFont("Helvetica", 8)
        c.drawCentredString(ancho/2, y, cfg["mensaje_pie"])

    c.save()


def _generar_factura_pdf_ticket(ruta: str, cfg: dict, numero: str,
                                fecha: datetime.datetime,
                                cliente: str, ruc_cliente: str,
                                direccion_cliente: str, condicion: str,
                                items: list, total: float, formato: str):
    """Genera la factura legal en formato condensado, para imprimir en una
    ticketera de 80mm o 58mm (papel continuo, alto calculado según el
    contenido)."""
    spec = FORMATOS_IMPRESION.get(formato, FORMATOS_IMPRESION["ticket80"])
    texto = generar_texto_factura(cfg, numero, fecha, cliente, ruc_cliente,
                                  direccion_cliente, condicion, items, total,
                                  ancho=spec["ancho_txt"])
    lineas = texto.split("\n")
    interlineado = spec["fuente"] * 1.35
    ancho_pt = spec["ancho_mm"] * mm
    margen = spec["margen_mm"] * mm
    alto_pt = margen * 2 + len(lineas) * interlineado

    c = rl_canvas.Canvas(ruta, pagesize=(ancho_pt, alto_pt))
    c.setFont("Courier", spec["fuente"])
    x = margen
    y = alto_pt - margen
    for linea in lineas:
        c.drawString(x, y, linea)
        y -= interlineado
    c.save()


# ══════════════════════════════════════════════════════════════
#  FUNCIÓN PÚBLICA: generar factura desde una venta real
# ══════════════════════════════════════════════════════════════
def generar_factura_desde_venta(venta: dict, items: list,
                                 cliente: dict = None, formato: str = None) -> str:
    """Genera la factura PDF de una venta real y devuelve la ruta del PDF.
    Si no se indica 'formato', usa el tamaño de papel configurado en
    Configuración Local (pestaña Factura Legal)."""
    import os, tempfile
    cfg = obtener_config_local()
    if formato is None:
        formato = cfg.get("formato_factura", "a4") or "a4"
    numero, _ = siguiente_numero("factura")

    cliente_nombre = (cliente or {}).get("razon_social") or (cliente or {}).get("nombre", "Ocasional")
    cliente_ruc    = (cliente or {}).get("ruc") or (cliente or {}).get("nro_documento", "-")
    cliente_dir    = (cliente or {}).get("direccion", "-")

    ruta = os.path.join(tempfile.gettempdir(),
                        f"factura_{numero.replace('-','_')}.pdf")
    generar_factura_pdf(
        ruta=ruta, cfg=cfg, numero=numero,
        fecha=datetime.datetime.now(),
        cliente=cliente_nombre, ruc_cliente=cliente_ruc,
        direccion_cliente=cliente_dir,
        condicion=venta.get("condicion", "CONTADO").upper(),
        items=items,
        total=venta.get("total", 0),
        formato=formato,
    )
    return ruta
