"""
ventana_ventas.py
Pantalla principal de Ventas: campo de código + Enter para agregar,
grilla de la venta actual, atajos de teclado (F1 Asignar Cliente,
Ctrl+P Artículo Común, F2 Buscar, F11 Mayoreo,
F7 Entrada de Efectivo (ingreso de caja), F8 Salida de Efectivo (retiro de caja),
DEL Borrar Artículo, F12 Procesar).
"""
import tkinter as tk
from tkinter import ttk, messagebox

from models_catalogo import buscar_producto_por_codigo
from ventanas_auxiliares_venta import VentanaBuscarProducto, VentanaAsignarCliente, VentanaArticulosComunes
from utilidades_ui import (
    habilitar_deseleccion_treeview,
    ajustar_tamaño_ventana, formatear_gs, formatear_cantidad,
    unidad_es_fraccionable, parsear_cantidad,
)
from traducciones import t

AZUL_RIBBON = "#1d5fd6"
VERDE_IMPORTE = "#dcfce7"
GRIS_FONDO = "#f4f5f7"


class PanelVentas(tk.Frame):
    def __init__(self, parent, usuario_actual, on_venta_finalizada=None,
                 on_caja_actualizada=None):
        super().__init__(parent, bg="white")
        self.usuario_actual = usuario_actual
        # Callback opcional que el contenedor de pestañas usa para cerrar
        # esta pestaña automáticamente cuando la venta se cobra con éxito.
        self.on_venta_finalizada = on_venta_finalizada
        # Callback opcional que el contenedor de pestañas usa para refrescar
        # el panel de Resumen (Ventas en Efectivo, Entradas, Salidas, etc.)
        # cada vez que se registra una Entrada/Salida de efectivo (F7/F8).
        self.on_caja_actualizada = on_caja_actualizada

        self.items_venta = []  # cada item: {producto, cantidad, precio_unitario, es_mayoreo}
        self.cliente_seleccionado = None  # None = Ocasional
        # Recuerda la última sesión de "Armar Venta por Locales" armada
        # desde ESTA pestaña de venta (locales, sus productos, y qué se
        # cargó en la venta), para poder reabrirla y seguir editándola en
        # vez de tener que empezar de cero cada vez.
        self.sesion_armar_locales = None
        # Si "Armar Venta por Locales" está abierta en este momento para
        # esta pestaña, esta es la referencia viva a esa ventana: permite
        # sincronizar cambios en ambos sentidos mientras esté abierta.
        self.ventana_locales_activa = None
        # Bandera anti-loop: evita que una sincronización Locales->Venta
        # dispare, a su vez, una sincronización Venta->Locales (y viceversa).
        self._sync_en_progreso = False

        self._construir_barra_codigo()
        self._construir_barra_atajos()
        self._construir_grilla()
        self._construir_pie()
        self._registrar_atajos_teclado()

        self._actualizar_vista()

    # ---------------- BARRA SUPERIOR: CÓDIGO DE BARRA / CÓDIGO SECUNDARIO ----------------
    def _construir_barra_codigo(self):
        barra = tk.Frame(self, bg="white")
        barra.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(barra, text=t("ventas_codigo_barra"), font=("Segoe UI", 10, "bold"),
                 bg="white").pack(side="left", padx=(0, 8))
        self.var_codigo = tk.StringVar()
        self.entry_codigo = tk.Entry(barra, textvariable=self.var_codigo, font=("Segoe UI", 11), width=22)
        self.entry_codigo.pack(side="left", padx=(0, 15))
        self.entry_codigo.bind("<Return>", lambda e: self._agregar_por_codigo())

        tk.Label(barra, text=t("ventas_codigo_secundario"), font=("Segoe UI", 10, "bold"),
                 bg="white").pack(side="left", padx=(0, 8))
        self.var_codigo_secundario = tk.StringVar()
        self.entry_codigo_secundario = tk.Entry(barra, textvariable=self.var_codigo_secundario,
                                                 font=("Segoe UI", 11), width=22)
        self.entry_codigo_secundario.pack(side="left", padx=(0, 8))
        self.entry_codigo_secundario.bind("<Return>", lambda e: self._agregar_por_codigo_secundario())

        self.entry_codigo.focus()

        tk.Button(barra, text=t("ventas_agregar_producto"), font=("Segoe UI", 9, "bold"),
                  bg=AZUL_RIBBON, fg="white", command=self._agregar_por_codigo).pack(side="left")

    # ---------------- BARRA DE ATAJOS ----------------
    def _construir_barra_atajos(self):
        barra = tk.Frame(self, bg="white")
        barra.pack(fill="x", padx=10, pady=(0, 8))

        atajos = [
            ("F1 - Asignar Cliente",  self._abrir_asignar_cliente,        "#2563eb"),
            ("Ctrl+P Art. Común",     self._abrir_articulos_comunes,       "#7c3aed"),
            ("F2 Buscar",             self._abrir_buscar_producto,         "#0891b2"),
            ("F3 Stock",              self._abrir_consultar_stock,         "#0e7490"),
            ("F11 Mayoreo",           self._toggle_mayoreo,                "#ca8a04"),
            ("F7 Entradas",           self._abrir_entrada_rapida,          "#16a34a"),
            ("F8 Salidas",            self._abrir_salida_rapida,           "#dc2626"),
            ("DEL Borrar Artículo",   self._borrar_articulo_seleccionado,  "#6b7280"),
            ("🗑 Limpiar Todo",        self._limpiar_venta,                 "#374151"),
            ("🏬 Armar Venta por Locales", self._abrir_armar_venta_locales, "#0f766e"),
        ]
        for texto, comando, color in atajos:
            tk.Button(barra, text=texto, font=("Segoe UI", 8, "bold"),
                      bg=color, fg="white", relief="flat", padx=10, pady=6,
                      cursor="hand2", command=comando).pack(side="left", padx=(0, 6))

    # ---------------- GRILLA DE LA VENTA ACTUAL ----------------
    def _construir_grilla(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        columnas = ("codigo", "descripcion", "precio_venta", "cantidad", "importe", "existencia")
        encabezados = (t("col_codigo"), t("col_descripcion"), t("col_precio_venta"),
                       t("col_cantidad"), t("col_importe"), t("col_existencia"))

        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc in zip(columnas, encabezados):
            self.tabla.heading(col, text=enc)
            ancho = 260 if col == "descripcion" else 100
            self.tabla.column(col, width=ancho, anchor="w" if col == "descripcion" else "center")

        self.tabla.tag_configure("importe", background=VERDE_IMPORTE)

        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        scrollbar_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=scrollbar.set, xscrollcommand=scrollbar_h.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        scrollbar_h.grid(row=1, column=0, sticky="ew")

        # Doble click en cantidad permite editarla rápido escribiendo el número
        self.tabla.bind("<Double-1>", lambda e: self._editar_cantidad_seleccionada())
        self.tabla.bind("<<TreeviewSelect>>", lambda e: self._actualizar_barra_cantidad())

        # Click izquierdo en una zona VACÍA de la grilla (fuera de cualquier
        # fila, por ejemplo debajo del último artículo) deselecciona el
        # registro actual, igual que "click afuera" en cualquier lista.
        self.tabla.bind("<Button-1>", self._al_click_en_grilla, add="+")

        self._construir_barra_control_cantidad()

    def _al_click_en_grilla(self, event):
        """Si el click cae fuera de cualquier fila (espacio vacío de la
        tabla), deselecciona el artículo actualmente seleccionado."""
        fila_id = self.tabla.identify_row(event.y)
        if not fila_id:
            self.tabla.selection_remove(*self.tabla.selection())

    def _deseleccionar_articulo(self, event=None):
        """Tecla Escape: quita la selección de la grilla de la venta actual,
        sin importar qué widget tenga el foco en ese momento."""
        if self.tabla.selection():
            self.tabla.selection_remove(*self.tabla.selection())

    def _texto_cantidad_editable(self, valor, unidad: str) -> str:
        """Texto para mostrar en un campo editable de cantidad: coma decimal
        sin ceros finales si la unidad es fraccionable (Kg/Lt/Mt), o entero
        sin decimales si es una unidad entera (Unidad/Caja/Paquete/Docena)."""
        if unidad_es_fraccionable(unidad):
            s = f"{valor:.10f}".rstrip("0").rstrip(".")
            return s.replace(".", ",")
        return str(int(round(valor)))

    def _construir_barra_control_cantidad(self):
        """Barra con botones ➕/➖ para sumar o restar de uno en uno la
        cantidad del producto seleccionado en la grilla de la venta."""
        barra = tk.Frame(self, bg=GRIS_FONDO, relief="solid", bd=1, highlightbackground="#e2e8f0")
        barra.pack(fill="x", padx=10, pady=(0, 10))

        self.label_producto_control = tk.Label(barra, text=t("ventas_selecciona_producto"),
                                                font=("Segoe UI", 9), bg=GRIS_FONDO, fg="#555")
        self.label_producto_control.pack(side="left", padx=(12, 15), pady=10)

        self.btn_disminuir = tk.Button(
            barra, text="－", font=("Segoe UI", 12, "bold"), width=3, bg="#fee2e2", fg="#dc2626",
            relief="flat", cursor="hand2", state="disabled", disabledforeground="#dc2626",
            command=self._disminuir_cantidad_seleccionada)
        self.btn_disminuir.pack(side="left", pady=10)

        # Campo editable: además de los botones +/-, el usuario puede
        # escribir la cantidad directamente con el teclado y confirmarla
        # con Enter o haciendo click fuera del campo.
        self.var_cantidad_actual = tk.StringVar(value="0")
        self.entry_cantidad_actual = tk.Entry(
            barra, textvariable=self.var_cantidad_actual, font=("Segoe UI", 12, "bold"),
            width=6, justify="center", relief="solid", bd=1,
        )
        self.entry_cantidad_actual.pack(side="left", padx=8, pady=10)
        self.entry_cantidad_actual.bind("<Return>", lambda e: self._confirmar_cantidad_escrita(quitar_foco=True))
        self.entry_cantidad_actual.bind("<FocusOut>", lambda e: self._confirmar_cantidad_escrita(quitar_foco=False))

        self.btn_aumentar = tk.Button(
            barra, text="＋", font=("Segoe UI", 12, "bold"), width=3, bg="#dcfce7", fg="#16a34a",
            relief="flat", cursor="hand2", state="disabled", disabledforeground="#16a34a",
            command=self._aumentar_cantidad_seleccionada)
        self.btn_aumentar.pack(side="left", padx=(0, 12), pady=10)

        # Bloque opcional "cargar por monto": solo se muestra cuando el
        # producto seleccionado se vende por Kilogramo/Litro/Metro. Permite
        # escribir cuánto dinero (Gs.) va a gastar el cliente y calcula
        # automáticamente cuántos Kg/Lt/Mt corresponden a ese monto, en vez
        # de tener que calcularlo a mano y escribir la cantidad exacta.
        self.frame_por_monto = tk.Frame(barra, bg=GRIS_FONDO)
        self._abrev_unidad_monto = ""

        tk.Label(self.frame_por_monto, text="│", font=("Segoe UI", 12), bg=GRIS_FONDO,
                 fg="#cbd5e1").pack(side="left", padx=(0, 10))
        tk.Label(self.frame_por_monto, text="💰 Cargar por monto:", font=("Segoe UI", 9),
                 bg=GRIS_FONDO, fg="#555").pack(side="left")

        self.var_monto_cantidad = tk.StringVar(value="")
        self.entry_monto_cantidad = tk.Entry(
            self.frame_por_monto, textvariable=self.var_monto_cantidad, font=("Segoe UI", 10, "bold"),
            width=10, justify="center", relief="solid", bd=1)
        self.entry_monto_cantidad.pack(side="left", padx=6)
        self.entry_monto_cantidad.bind("<KeyRelease>", lambda e: self._previsualizar_cantidad_por_monto())
        self.entry_monto_cantidad.bind("<Return>", lambda e: self._confirmar_cantidad_por_monto(quitar_foco=True))
        self.entry_monto_cantidad.bind("<FocusOut>", lambda e: self._confirmar_cantidad_por_monto(quitar_foco=False))

        self.label_preview_monto = tk.Label(self.frame_por_monto, text="", font=("Segoe UI", 9, "bold"),
                                             bg=GRIS_FONDO, fg="#166534", width=28, anchor="w")
        self.label_preview_monto.pack(side="left", padx=(6, 12))

        # Arranca oculto: solo se muestra cuando corresponde (ver
        # _actualizar_barra_cantidad / _mostrar_control_por_monto).

    def _producto_id_seleccionado_en_grilla(self):
        seleccion = self.tabla.selection()
        return int(seleccion[0]) if seleccion else None

    def _item_seleccionado(self):
        producto_id = self._producto_id_seleccionado_en_grilla()
        if producto_id is None:
            return None
        return next((i for i in self.items_venta if i["producto"]["id"] == producto_id), None)

    def _actualizar_barra_cantidad(self):
        item = self._item_seleccionado()
        if item is None:
            self._producto_id_en_edicion = None
            self.label_producto_control.config(text=t("ventas_selecciona_producto"))
            self.var_cantidad_actual.set("0")
            self.btn_disminuir.config(state="disabled")
            self.btn_aumentar.config(state="disabled")
            self.entry_cantidad_actual.config(state="disabled")
            self._ocultar_control_por_monto()
        else:
            self._producto_id_en_edicion = item["producto"]["id"]
            self.label_producto_control.config(text=item["producto"]["nombre"])
            unidad = item["producto"].get("unidad_medida", "Unidad")
            self.var_cantidad_actual.set(self._texto_cantidad_editable(item["cantidad"], unidad))
            self.btn_disminuir.config(state="normal")
            self.btn_aumentar.config(state="normal")
            self.entry_cantidad_actual.config(state="normal")
            if unidad_es_fraccionable(unidad):
                self._mostrar_control_por_monto(unidad)
            else:
                self._ocultar_control_por_monto()

    def _mostrar_control_por_monto(self, unidad: str):
        """Muestra el bloque 'Cargar por monto' (solo aplica a productos que
        se venden por Kg/Lt/Mt, donde tiene sentido decir 'quiero Gs. 20.000
        de esto' en vez de calcular a mano cuántos kilos/litros/metros son)."""
        abrev = {"Kilogramo": "Kg", "Litro": "Lt", "Metro": "Mt"}.get(unidad, unidad)
        self._abrev_unidad_monto = abrev
        self.var_monto_cantidad.set("")
        self.label_preview_monto.config(text="")
        if not self.frame_por_monto.winfo_ismapped():
            self.frame_por_monto.pack(side="left", pady=10)

    def _ocultar_control_por_monto(self):
        self.var_monto_cantidad.set("")
        self.label_preview_monto.config(text="")
        self.frame_por_monto.pack_forget()

    def _previsualizar_cantidad_por_monto(self):
        """Mientras el usuario escribe el monto en guaraníes, muestra en
        vivo a cuántos Kg/Lt/Mt equivale, sin todavía aplicarlo a la venta."""
        item = self._item_seleccionado()
        if item is None:
            return
        texto = self.var_monto_cantidad.get().strip()
        if not texto:
            self.label_preview_monto.config(text="")
            return
        try:
            monto = parsear_cantidad(texto)
        except ValueError:
            self.label_preview_monto.config(text="⚠ monto inválido")
            return
        precio = item["precio_unitario"]
        if not precio or precio <= 0:
            self.label_preview_monto.config(text="⚠ sin precio")
            return
        cantidad = round(monto / precio, 3)
        monto_real = cantidad * precio
        texto_cantidad = f"{cantidad:.10f}".rstrip("0").rstrip(".").replace(".", ",")
        if round(monto_real) != round(monto):
            self.label_preview_monto.config(
                text=f"≈ {texto_cantidad} {self._abrev_unidad_monto}  →  {formatear_gs(monto_real)}")
        else:
            self.label_preview_monto.config(text=f"≈ {texto_cantidad} {self._abrev_unidad_monto}")

    def _confirmar_cantidad_por_monto(self, quitar_foco: bool = False):
        """Al confirmar (Enter o click afuera), calcula la cantidad exacta
        de Kg/Lt/Mt que corresponde al monto ingresado y la aplica como la
        cantidad del artículo, igual que si se hubiera escrito a mano."""
        if getattr(self, "_procesando_monto", False):
            return
        self._procesando_monto = True
        try:
            producto_id = getattr(self, "_producto_id_en_edicion", None)
            if producto_id is None:
                return
            item = next((i for i in self.items_venta if i["producto"]["id"] == producto_id), None)
            if item is None:
                return

            texto = self.var_monto_cantidad.get().strip()
            if not texto:
                return  # nada escrito: no hay nada que aplicar

            try:
                monto = parsear_cantidad(texto)
                if monto < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Monto inválido", "Ingresa un monto en guaraníes válido (0 o mayor).")
                self.var_monto_cantidad.set("")
                self.label_preview_monto.config(text="")
                return

            precio = item["precio_unitario"]
            if not precio or precio <= 0:
                messagebox.showerror(
                    "Precio no disponible",
                    f"'{item['producto']['nombre']}' no tiene un precio unitario válido "
                    "para calcular la cantidad a partir del monto.")
                self.var_monto_cantidad.set("")
                self.label_preview_monto.config(text="")
                return

            cantidad = round(monto / precio, 3)

            if cantidad <= 0:
                self.items_venta = [i for i in self.items_venta if i["producto"]["id"] != producto_id]
                self._actualizar_vista()
                self._actualizar_barra_cantidad()
                self._notificar_cambio_a_locales(producto_id, 0)
                return

            item["cantidad"] = cantidad
            self._actualizar_vista()
            self._reseleccionar_y_refrescar_barra(producto_id)
            self._notificar_cambio_a_locales(producto_id, cantidad)

            if quitar_foco:
                self.entry_codigo.focus_set()
        finally:
            self._procesando_monto = False

    def _confirmar_cantidad_escrita(self, quitar_foco: bool = False):
        # Protección anti-doble-disparo: al presionar Enter, Tkinter también
        # puede emitir <FocusOut> casi al mismo tiempo (por ejemplo al mover
        # el foco con focus_set más abajo). Sin esta bandera, el método se
        # ejecutaba dos veces seguidas y, si la tabla todavía no había
        # terminado de reconstruirse tras el primer llamado, la segunda
        # ejecución podía no encontrar la fila seleccionada y producía el
        # efecto de "el producto desaparece de la grilla".
        if getattr(self, "_procesando_cantidad", False):
            return
        self._procesando_cantidad = True
        try:
            # IMPORTANTE: usamos el producto que estaba siendo editado
            # cuando se habilitó el campo (guardado en _actualizar_barra_
            # cantidad), NO la selección "en vivo" de la grilla en este
            # instante. Si el usuario hace clic en OTRA fila mientras el
            # campo de cantidad todavía tenía foco, el <FocusOut> puede
            # dispararse cuando la grilla YA cambió su selección a esa
            # otra fila, pero el texto del campo todavía es el viejo (por
            # ejemplo "0" de un estado "sin selección" anterior). Si en ese
            # caso volviéramos a leer la selección actual, terminaríamos
            # aplicando ese "0" al producto EQUIVOCADO y lo borraríamos de
            # la grilla sin que el usuario lo pidiera.
            producto_id = getattr(self, "_producto_id_en_edicion", None)
            if producto_id is None:
                return
            item = next((i for i in self.items_venta if i["producto"]["id"] == producto_id), None)
            if item is None:
                return

            texto = self.var_cantidad_actual.get().strip()
            unidad = item["producto"].get("unidad_medida", "Unidad")
            try:
                nueva_cantidad = parsear_cantidad(texto)
                if nueva_cantidad < 0:
                    raise ValueError
                if not unidad_es_fraccionable(unidad) and nueva_cantidad != int(nueva_cantidad):
                    messagebox.showerror(
                        "Cantidad inválida",
                        f"'{item['producto']['nombre']}' se vende por {unidad.lower()} "
                        "y no admite cantidades con decimales. Ingresa un número entero.")
                    self.var_cantidad_actual.set(self._texto_cantidad_editable(item["cantidad"], unidad))
                    return
            except ValueError:
                messagebox.showerror("Cantidad inválida", "Ingresa un número válido (0 o mayor).")
                self.var_cantidad_actual.set(self._texto_cantidad_editable(item["cantidad"], unidad))
                return

            if nueva_cantidad <= 0:
                # Igual que el botón "－" al llegar a 0: se quita la línea de la venta.
                self.items_venta = [i for i in self.items_venta if i["producto"]["id"] != producto_id]
                self._actualizar_vista()
                self._actualizar_barra_cantidad()
                self._notificar_cambio_a_locales(producto_id, 0)
                return

            # Si la cantidad no cambió en realidad, no hace falta refrescar
            # nada (evita el "titileo" de reconstruir la tabla sin necesidad
            # cuando el usuario solo confirma el mismo valor que ya tenía).
            if nueva_cantidad == item["cantidad"]:
                if quitar_foco:
                    self.entry_codigo.focus_set()
                return

            item["cantidad"] = nueva_cantidad
            self._actualizar_vista()
            self._reseleccionar_y_refrescar_barra(producto_id)
            self._notificar_cambio_a_locales(producto_id, nueva_cantidad)

            if quitar_foco:
                # Mueve el foco al campo de Código del Producto (el lugar
                # natural para seguir trabajando) en vez de dejarlo en el
                # campo de cantidad, que es lo que producía el parpadeo
                # visual al quedar seleccionado/resaltado sin necesidad.
                self.entry_codigo.focus_set()
        finally:
            self._procesando_cantidad = False

    def _aumentar_cantidad_seleccionada(self):
        item = self._item_seleccionado()
        if item is None:
            messagebox.showinfo("Selecciona un producto", "Primero selecciona un producto de la lista de la venta.")
            return
        item["cantidad"] += 1
        self._actualizar_vista()
        self._reseleccionar_y_refrescar_barra(item["producto"]["id"])
        self._notificar_cambio_a_locales(item["producto"]["id"], item["cantidad"])

    def _disminuir_cantidad_seleccionada(self):
        item = self._item_seleccionado()
        if item is None:
            messagebox.showinfo("Selecciona un producto", "Primero selecciona un producto de la lista de la venta.")
            return
        if item["cantidad"] <= 1:
            # Si llega a 0, se quita la línea de la venta (igual que Borrar Artículo)
            producto_id = item["producto"]["id"]
            self.items_venta = [i for i in self.items_venta if i["producto"]["id"] != producto_id]
            self._actualizar_vista()
            self._actualizar_barra_cantidad()
            self._notificar_cambio_a_locales(producto_id, 0)
            return
        item["cantidad"] -= 1
        self._actualizar_vista()
        self._reseleccionar_y_refrescar_barra(item["producto"]["id"])
        self._notificar_cambio_a_locales(item["producto"]["id"], item["cantidad"])

    def _reseleccionar_y_refrescar_barra(self, producto_id):
        """Tras refrescar la grilla, recupera la selección visual de la fila
        para que la barra de +/- siga apuntando al mismo producto."""
        str_id = str(producto_id)
        if str_id in self.tabla.get_children():
            self.tabla.selection_set(str_id)
        self._actualizar_barra_cantidad()

    # ---------------- PIE: TOTAL, CONDICIÓN DE VENTA, F12 ----------------
    def _construir_pie(self):
        pie = tk.Frame(self, bg=GRIS_FONDO)
        pie.pack(fill="x", padx=10, pady=(0, 10))

        fila_superior = tk.Frame(pie, bg=GRIS_FONDO)
        fila_superior.pack(fill="x", pady=8, padx=10)

        self.label_contador = tk.Label(fila_superior, text=t("ventas_productos_en_venta").format(n=0),
                                        font=("Segoe UI", 10), bg=GRIS_FONDO)
        self.label_contador.pack(side="left")

        tk.Button(fila_superior, text=t("ventas_f12_procesar"), font=("Segoe UI", 10, "bold"),
                  bg=AZUL_RIBBON, fg="white", relief="flat", bd=0, padx=16, pady=8,
                  cursor="hand2", activebackground="#163d8c", activeforeground="white",
                  command=self._procesar_venta).pack(side="right", padx=(20, 0))

        self.label_total = tk.Label(fila_superior, text="Gs. 0", font=("Segoe UI", 20, "bold"),
                                     bg=GRIS_FONDO, fg="#1d4ed8")
        self.label_total.pack(side="right", padx=20)

        fila_inferior = tk.Frame(pie, bg=GRIS_FONDO)
        fila_inferior.pack(fill="x", pady=(0, 8), padx=10)

        self.label_cliente = tk.Label(fila_inferior, text=f"{t('cliente_label')} {t('ocasional')}",
                                       font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO)
        self.label_cliente.pack(side="left")
        self.label_cliente_doc = tk.Label(fila_inferior, text=t("ventas_ci_ruc"),
                                           font=("Segoe UI", 9), bg=GRIS_FONDO, fg="#555")
        self.label_cliente_doc.pack(side="left", padx=(15, 0))

        frame_condicion = tk.Frame(fila_inferior, bg=GRIS_FONDO)
        frame_condicion.pack(side="right")
        tk.Label(frame_condicion, text=t("ventas_condicion_venta"), font=("Segoe UI", 9, "bold"),
                 bg=GRIS_FONDO).pack(side="left", padx=(0, 8))
        self.var_condicion = tk.StringVar(value="contado")
        tk.Radiobutton(frame_condicion, text=t("contado"), variable=self.var_condicion, value="contado",
                       bg=GRIS_FONDO, font=("Segoe UI", 9)).pack(side="left")
        tk.Radiobutton(frame_condicion, text=t("credito_label"), variable=self.var_condicion, value="credito",
                       bg=GRIS_FONDO, font=("Segoe UI", 9)).pack(side="left")

    # ---------------- ATAJOS DE TECLADO GLOBALES ----------------
    def _registrar_atajos_teclado(self):
        self._atajos_activos = True

        def manejar(callback):
            def wrapper(event):
                if self._atajos_activos:
                    callback()
            return wrapper

        self.bind_all("<F1>", manejar(self._abrir_asignar_cliente))
        self.bind_all("<Control-p>", manejar(self._abrir_articulos_comunes))
        self.bind_all("<F2>", manejar(self._abrir_buscar_producto))
        self.bind_all("<F3>", manejar(self._abrir_consultar_stock))
        self.bind_all("<F11>", manejar(self._toggle_mayoreo))
        self.bind_all("<F7>", manejar(self._abrir_entrada_rapida))
        self.bind_all("<F8>", manejar(self._abrir_salida_rapida))
        self.bind_all("<Delete>", manejar(self._borrar_articulo_seleccionado))
        self.bind_all("<F12>", manejar(self._procesar_venta))
        self.bind_all("<Escape>", manejar(self._deseleccionar_articulo))

    def _desactivar_atajos(self):
        """Se llama mientras una ventana modal (como Cobrar) está abierta,
        para que sus propios atajos F11/F12/F8 no choquen con los de Ventas."""
        self._atajos_activos = False

    def _reactivar_atajos(self):
        self._atajos_activos = True

    # ---------------- AGREGAR PRODUCTO POR CÓDIGO ----------------
    def _agregar_por_codigo(self):
        codigo = self.var_codigo.get().strip()
        if not codigo:
            return
        producto = buscar_producto_por_codigo(codigo)
        if producto is None or not producto["activo"]:
            messagebox.showerror("No encontrado", f"No existe un producto activo con el código de barra '{codigo}'.")
            self.var_codigo.set("")
            return
        self._agregar_item(producto)
        self.var_codigo.set("")
        self.entry_codigo.focus()

    def _agregar_por_codigo_secundario(self):
        codigo = self.var_codigo_secundario.get().strip()
        if not codigo:
            return
        producto = buscar_producto_por_codigo(codigo)
        if producto is None or not producto["activo"]:
            messagebox.showerror("No encontrado", f"No existe un producto activo con el código secundario '{codigo}'.")
            self.var_codigo_secundario.set("")
            return
        self._agregar_item(producto)
        self.var_codigo_secundario.set("")
        self.entry_codigo_secundario.focus()

    def _agregar_item(self, producto, cantidad=1):
        es_libre = producto.get("es_libre", False)

        if es_libre:
            # Los productos libres con la misma descripción se acumulan
            for item in self.items_venta:
                if item["producto"].get("es_libre") and item["producto"]["nombre"] == producto["nombre"]:
                    item["cantidad"] += cantidad
                    self._actualizar_vista()
                    return
        else:
            # Producto de catálogo: acumular por ID
            for item in self.items_venta:
                if not item["producto"].get("es_libre") and item["producto"]["id"] == producto["id"]:
                    item["cantidad"] += cantidad
                    self._actualizar_vista()
                    return

        self.items_venta.append({
            "producto": producto, "cantidad": cantidad,
            "precio_unitario": producto["precio_venta"], "es_mayoreo": False,
        })
        self._actualizar_vista()

    def _agregar_item_con_precio(self, producto, cantidad, precio_unitario, es_mayoreo=False):
        """Igual que _agregar_item, pero conservando un precio unitario ya
        definido (por ejemplo, el precio Mayoreo elegido en 'Armar Venta
        por Locales'), en vez de tomar siempre el precio normal del
        catálogo. Si el producto ya está en la venta, se suma la cantidad
        y se adopta este precio para la línea."""
        es_libre = producto.get("es_libre", False)

        if es_libre:
            for item in self.items_venta:
                if item["producto"].get("es_libre") and item["producto"]["nombre"] == producto["nombre"]:
                    item["cantidad"] += cantidad
                    item["precio_unitario"] = precio_unitario
                    item["es_mayoreo"] = es_mayoreo
                    self._actualizar_vista()
                    return
        else:
            for item in self.items_venta:
                if not item["producto"].get("es_libre") and item["producto"]["id"] == producto["id"]:
                    item["cantidad"] += cantidad
                    item["precio_unitario"] = precio_unitario
                    item["es_mayoreo"] = es_mayoreo
                    self._actualizar_vista()
                    return

        self.items_venta.append({
            "producto": producto, "cantidad": cantidad,
            "precio_unitario": precio_unitario, "es_mayoreo": es_mayoreo,
        })
        self._actualizar_vista()

    def _restar_cantidad_producto(self, producto_id, cantidad):
        """Resta una cantidad de la línea de un producto ya cargado en la
        venta (quitando la línea por completo si llega a 0 o menos). Se usa
        para 'deshacer' lo que 'Armar Venta por Locales' había cargado
        antes, y así poder actualizar la venta sin duplicar cantidades si
        el usuario corrige algo y vuelve a presionar 'Cargar en Venta'."""
        for item in self.items_venta:
            if not item["producto"].get("es_libre") and item["producto"]["id"] == producto_id:
                item["cantidad"] -= cantidad
                if item["cantidad"] <= 0:
                    self.items_venta.remove(item)
                self._actualizar_vista()
                return

    def _quitar_producto_completamente(self, producto_id):
        """Quita por completo la línea de un producto de la venta, sin
        importar la cantidad que tuviera. A diferencia de restar una
        cantidad puntual, esto no depende de que ningún registro anterior
        sea exacto: garantiza un estado limpio antes de volver a cargar los
        totales actuales desde 'Armar Venta por Locales', sin arrastrar
        ninguna diferencia acumulada de sincronizaciones anteriores."""
        nueva_lista = [
            item for item in self.items_venta
            if item["producto"].get("es_libre") or item["producto"]["id"] != producto_id
        ]
        if len(nueva_lista) != len(self.items_venta):
            self.items_venta = nueva_lista
            self._actualizar_vista()

    def _notificar_cambio_a_locales(self, producto_id, nueva_cantidad_total):
        """Si el usuario cambió a mano (en esta grilla) la cantidad de un
        producto que había sido cargado desde 'Armar Venta por Locales',
        y esa ventana sigue abierta, le avisamos para que reparta el
        cambio entre los locales correspondientes y ambas pantallas
        queden sincronizadas."""
        if self._sync_en_progreso:
            return
        ventana = self.ventana_locales_activa
        if ventana is None or not ventana.winfo_exists():
            return
        ventana.actualizar_cantidad_desde_venta(producto_id, nueva_cantidad_total)

    # ---------------- ACTUALIZAR GRILLA Y TOTALES ----------------
    def _actualizar_vista(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        total = 0
        for item in self.items_venta:
            p = item["producto"]
            importe = item["cantidad"] * item["precio_unitario"]
            total += importe
            unidad = p.get("unidad_medida", "Unidad")
            existencia = p["disponible"] if isinstance(p["disponible"], str) else formatear_cantidad(p['disponible'], unidad)
            cantidad_txt = formatear_cantidad(item["cantidad"], unidad)
            if item.get("es_mayoreo"):
                descripcion = f"{p['nombre']}  🏷 Mayoreo"
            elif p.get("es_libre"):
                descripcion = f"{p['nombre']}  ✏ Libre"
            else:
                descripcion = p["nombre"]
            self.tabla.insert("", "end", iid=str(p["id"]), values=(
                "—" if p.get("es_libre") else p["id"],
                descripcion, formatear_gs(item['precio_unitario']),
                cantidad_txt, formatear_gs(importe), existencia
            ), tags=("importe",))

        self.label_contador.config(text=t("ventas_productos_en_venta").format(n=len(self.items_venta)))
        self.label_total.config(text=formatear_gs(total))

        # Si la fila que estaba seleccionada ya no existe (se borró el
        # artículo o se limpió la venta), la barra +/- queda sin selección;
        # lo forzamos explícitamente para no depender únicamente del evento
        # <<TreeviewSelect>>, que puede no dispararse en todos los casos
        # (por ejemplo al vaciar la tabla por completo).
        self._actualizar_barra_cantidad()

        if self.cliente_seleccionado:
            self.label_cliente.config(text=f"{t('cliente_label')} {self.cliente_seleccionado['nombre']}")
            self.label_cliente_doc.config(text=f"{t('ventas_ci_ruc')} {self.cliente_seleccionado.get('nro_documento', '')}")
        else:
            self.label_cliente.config(text=f"{t('cliente_label')} {t('ocasional')}")
            self.label_cliente_doc.config(text=t("ventas_ci_ruc"))

    # ---------------- ATAJOS: ACCIONES ----------------
    def _abrir_asignar_cliente(self):
        def al_seleccionar(cliente):
            self.cliente_seleccionado = cliente
            self._actualizar_vista()
        VentanaAsignarCliente(self, on_seleccionado=al_seleccionar)

    def _abrir_articulos_comunes(self):
        """Ctrl+P: abre 'Producto Común', donde se puede cargar libremente
        una descripción, cantidad y precio unitario. Se registra como un
        producto real en la base de datos (servicio, stock ilimitado) y se
        agrega de inmediato a la venta actual."""
        def al_seleccionar(producto, cantidad):
            self._agregar_item(producto, cantidad)
        VentanaArticulosComunes(self, on_seleccionado=al_seleccionar)

    def _abrir_buscar_producto(self):
        def al_seleccionar(producto):
            self._agregar_item(producto)
        VentanaBuscarProducto(self, on_seleccionado=al_seleccionar)

    def _abrir_armar_venta_locales(self):
        if self.ventana_locales_activa is not None and self.ventana_locales_activa.winfo_exists():
            # Ya está abierta para esta pestaña: la traemos al frente en
            # vez de abrir una segunda (evita confusiones de sincronización).
            self.ventana_locales_activa.lift()
            self.ventana_locales_activa.focus_force()
            return
        from ventana_armar_venta_locales import VentanaArmarVentaPorLocales
        VentanaArmarVentaPorLocales(self, panel_ventas=self, usuario_actual=self.usuario_actual,
                                    sesion_previa=self.sesion_armar_locales)

    def _abrir_consultar_stock(self):
        """Abre la consulta de stock: tabla completa de todos los productos
        con sus precios, stock actual, comprometido y disponible.
        Solo consulta, no agrega nada a la venta."""
        from ventanas_auxiliares_venta import VentanaConsultarStock
        VentanaConsultarStock(self)

    def _toggle_mayoreo(self):
        """F11: alterna el precio Mayorista/Normal SOLO en la línea
        actualmente seleccionada en la grilla. Si no hay ninguna línea
        seleccionada, avisa que hay que elegir un producto primero."""
        item = self._item_seleccionado()
        if item is None:
            messagebox.showinfo(
                "Selecciona un producto",
                "Primero selecciona el producto de la venta al que quieres aplicar el precio Mayoreo."
            )
            return

        p = item["producto"]
        item["es_mayoreo"] = not item.get("es_mayoreo", False)
        item["precio_unitario"] = p["precio_mayorista"] if item["es_mayoreo"] else p["precio_venta"]
        self._actualizar_vista()
        self._reseleccionar_y_refrescar_barra(p["id"])

        estado = "activado" if item["es_mayoreo"] else "desactivado"
        self.label_contador.config(
            text=f"Mayoreo {estado} para '{p['nombre']}'. {len(self.items_venta)} productos en la venta."
        )

    def _abrir_entrada_rapida(self):
        """F7: abre 'Entrada de Efectivo'. Al guardar, refresca el panel de
        Resumen (Entradas / Dinero en Caja) y muestra el detalle del día."""
        from ventana_entrada_efectivo import VentanaEntradaEfectivo
        def al_guardar():
            if self.on_caja_actualizada:
                self.on_caja_actualizada()
            _VentanaDetalleMovimientoCaja(self, tipo="entrada")
        VentanaEntradaEfectivo(self, self.usuario_actual, on_guardado=al_guardar)

    def _abrir_salida_rapida(self):
        """F8: abre 'Salida de Efectivo'. Al guardar, refresca el panel de
        Resumen (Salidas / Dinero en Caja) y muestra el detalle del día."""
        from ventana_salida_efectivo import VentanaSalidaEfectivo
        def al_guardar():
            if self.on_caja_actualizada:
                self.on_caja_actualizada()
            _VentanaDetalleMovimientoCaja(self, tipo="salida")
        VentanaSalidaEfectivo(self, self.usuario_actual, on_guardado=al_guardar)

    def _limpiar_venta(self):
        """Limpia todos los artículos de la venta actual sin procesarla."""
        if not self.items_venta:
            return
        if not messagebox.askyesno(
            "Limpiar venta",
            f"¿Eliminar todos los {len(self.items_venta)} artículo(s) de esta venta?\n\n"
            "La venta NO se procesará ni se guardará.",
            parent=self,
        ):
            return
        self.items_venta        = []
        self.cliente_seleccionado = None
        self.var_condicion.set("contado")
        self._actualizar_vista()
        self.entry_codigo.focus()
        # Si "Armar Venta por Locales" está abierta para esta pestaña,
        # vaciamos también todos los locales: la venta a la que estaban
        # sincronizados quedó vacía. Y si no está abierta pero había una
        # sesión recordada (de una vez anterior que se cerró con
        # productos cargados), también la descartamos: ya no corresponde
        # a la venta actual, que se acaba de vaciar.
        if self.ventana_locales_activa is not None and self.ventana_locales_activa.winfo_exists():
            self.ventana_locales_activa.limpiar_todos_los_locales()
        self.sesion_armar_locales = None

    def _borrar_articulo_seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        try:
            producto_id = int(seleccion[0])
        except (ValueError, TypeError):
            return
        self.items_venta = [item for item in self.items_venta if item["producto"]["id"] != producto_id]
        self._actualizar_vista()
        self._notificar_cambio_a_locales(producto_id, 0)

    def _editar_cantidad_seleccionada(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        try:
            producto_id = int(seleccion[0])
        except (ValueError, TypeError):
            return
        item = next((i for i in self.items_venta if i["producto"]["id"] == producto_id), None)
        if item is None:
            return

        ventana = tk.Toplevel(self)
        ventana.title("Editar Cantidad")
        ventana.grab_set()
        unidad = item["producto"].get("unidad_medida", "Unidad")
        tk.Label(ventana, text=item["producto"]["nombre"], font=("Segoe UI", 9, "bold"),
                 wraplength=240).pack(pady=(10, 5))
        var_cant = tk.StringVar(value=self._texto_cantidad_editable(item["cantidad"], unidad))
        entry = tk.Entry(ventana, textvariable=var_cant, font=("Segoe UI", 11), justify="center")
        entry.pack(pady=5)
        entry.focus()
        entry.select_range(0, tk.END)

        def confirmar():
            try:
                nueva_cantidad = parsear_cantidad(var_cant.get())
                if nueva_cantidad <= 0:
                    raise ValueError
                if not unidad_es_fraccionable(unidad) and nueva_cantidad != int(nueva_cantidad):
                    messagebox.showerror(
                        "Cantidad inválida",
                        f"'{item['producto']['nombre']}' se vende por {unidad.lower()} "
                        "y no admite cantidades con decimales. Ingresa un número entero.")
                    return
            except ValueError:
                messagebox.showerror("Cantidad inválida", "Ingresa un número mayor a cero.")
                return
            item["cantidad"] = nueva_cantidad
            ventana.destroy()
            self._actualizar_vista()

        entry.bind("<Return>", lambda e: confirmar())
        tk.Button(ventana, text=t("confirmar"), bg=AZUL_RIBBON, fg="white",
                  command=confirmar).pack(pady=10)

        ajustar_tamaño_ventana(ventana, ancho_min=260, alto_min=130)

    # ---------------- PROCESAR VENTA (F12) → ABRE VENTANA COBRAR ----------------
    def _procesar_venta(self):
        if not self.items_venta:
            messagebox.showwarning("Venta vacía", "Agrega al menos un producto antes de procesar la venta.")
            return

        from ventana_cobrar import VentanaCobrar
        self._desactivar_atajos()
        ventana = VentanaCobrar(
            self, items_venta=self.items_venta, cliente=self.cliente_seleccionado,
            usuario_actual=self.usuario_actual, condicion_inicial=self.var_condicion.get(),
            on_venta_procesada=self._reiniciar_venta,
        )
        ventana.bind("<Destroy>", lambda e: self._reactivar_atajos())

    def _reiniciar_venta(self):
        self.items_venta = []
        self.cliente_seleccionado = None
        self.var_condicion.set("contado")
        self._actualizar_vista()
        self.entry_codigo.focus()
        # La venta se cobró con éxito: si "Armar Venta por Locales" tenía
        # una sesión con productos para esta pestaña (abierta en este
        # momento, o simplemente recordada para reabrir más tarde), le
        # pertenecía a la venta que ya se cobró y quedó guardada. La
        # reiniciamos por completo para que la próxima vez que se abra
        # "Armar Venta por Locales" en esta misma pestaña empiece desde
        # cero, en vez de arrastrar los locales de una venta ya cerrada.
        if self.ventana_locales_activa is not None and self.ventana_locales_activa.winfo_exists():
            self.ventana_locales_activa.limpiar_todos_los_locales()
        self.sesion_armar_locales = None
        # Si este panel vive dentro de un contenedor de pestañas múltiples,
        # le avisamos que la venta terminó para que decida cerrar la pestaña.
        if self.on_venta_finalizada:
            self.on_venta_finalizada()


class PanelVentasConPestanas(tk.Frame):
    """Contenedor del módulo Ventas con una barra de pestañas propia (no
    ttk.Notebook, para poder tener botón '➕ Nueva Venta' y una '✕' de
    cierre individual en cada pestaña de venta, como las pestañas de un
    navegador). Siempre hay una pestaña fija 'Resumen' y al menos una
    pestaña de venta activa; el sistema arranca mostrando la primera
    pestaña de venta, no el Resumen."""

    COLOR_FONDO_BARRA = "#dbe4f0"
    COLOR_TAB_ACTIVA = "white"
    COLOR_TAB_INACTIVA = "#c7d3e6"
    COLOR_AZUL = "#1d5fd6"

    def __init__(self, parent, usuario_actual):
        super().__init__(parent, bg="white")
        self.usuario_actual = usuario_actual

        self.contador_ventas_creadas = 0  # para numerar "Nueva Venta N" de forma creciente
        self.pestanas_venta = {}  # id_pestaña -> {"panel":, "boton_frame":, "label":}
        self.pestana_actual = None  # "resumen" o el id de una pestaña de venta

        self._construir_barra_pestanas()
        self._construir_area_contenido()

        from ventana_resumen_ventas import PanelResumenVentas
        self.panel_resumen = PanelResumenVentas(self.area_contenido, usuario_actual)

        # Arranca con una pestaña de venta abierta y activa (no en Resumen).
        primera_pestana_id = self._agregar_pestana_venta()
        self._activar_pestana(primera_pestana_id)

    # ---------------- BARRA DE PESTAÑAS ----------------
    def _construir_barra_pestanas(self):
        self.barra_pestanas = tk.Frame(self, bg=self.COLOR_FONDO_BARRA, height=36)
        self.barra_pestanas.pack(fill="x")
        self.barra_pestanas.pack_propagate(False)

        # Pestaña fija "Resumen", siempre la primera y nunca se cierra.
        self.tab_resumen_frame = tk.Frame(self.barra_pestanas, bg=self.COLOR_TAB_INACTIVA)
        self.tab_resumen_frame.pack(side="left", fill="y", padx=(6, 2), pady=4)
        self.label_tab_resumen = tk.Label(self.tab_resumen_frame, text=t("ventas_tab_resumen"), font=("Segoe UI", 9, "bold"),
                                          bg=self.COLOR_TAB_INACTIVA, fg="#334155", padx=14, pady=6, cursor="hand2")
        self.label_tab_resumen.pack()
        self.label_tab_resumen.bind("<Button-1>", lambda e: self._activar_pestana("resumen"))

        # Contenedor donde se van agregando las pestañas de venta dinámicas.
        self.frame_tabs_venta = tk.Frame(self.barra_pestanas, bg=self.COLOR_FONDO_BARRA)
        self.frame_tabs_venta.pack(side="left", fill="y")

        # Botón "➕" para agregar una nueva venta en paralelo.
        btn_agregar = tk.Label(self.barra_pestanas, text="➕", font=("Segoe UI", 11, "bold"),
                               bg=self.COLOR_FONDO_BARRA, fg=self.COLOR_AZUL, cursor="hand2", padx=10)
        btn_agregar.pack(side="left", pady=4)
        btn_agregar.bind("<Button-1>", lambda e: self._activar_pestana(self._agregar_pestana_venta()))

    def _construir_area_contenido(self):
        self.area_contenido = tk.Frame(self, bg="white")
        self.area_contenido.pack(fill="both", expand=True)

    # ---------------- GESTIÓN DE PESTAÑAS DE VENTA ----------------
    def _agregar_pestana_venta(self) -> str:
        self.contador_ventas_creadas += 1
        numero = self.contador_ventas_creadas
        pestana_id = f"venta_{numero}"

        panel = PanelVentas(
            self.area_contenido, self.usuario_actual,
            on_venta_finalizada=lambda pid=pestana_id: self._al_finalizar_venta(pid),
            on_caja_actualizada=self._refrescar_resumen_si_visible,
        )

        tab_frame = tk.Frame(self.frame_tabs_venta, bg=self.COLOR_TAB_INACTIVA)
        tab_frame.pack(side="left", fill="y", padx=2, pady=4)

        label = tk.Label(tab_frame, text=f"{t('ventas_nueva_venta')} {numero}", font=("Segoe UI", 9, "bold"),
                         bg=self.COLOR_TAB_INACTIVA, fg="#334155", padx=10, pady=6, cursor="hand2")
        label.pack(side="left")
        label.bind("<Button-1>", lambda e, pid=pestana_id: self._activar_pestana(pid))

        btn_cerrar = tk.Label(tab_frame, text="✕", font=("Segoe UI", 8), bg=self.COLOR_TAB_INACTIVA,
                              fg="#64748b", cursor="hand2")
        btn_cerrar.pack(side="left", padx=(0, 8))
        btn_cerrar.bind("<Button-1>", lambda e, pid=pestana_id: self._cerrar_pestana_venta(pid))

        self.pestanas_venta[pestana_id] = {
            "panel": panel, "tab_frame": tab_frame, "label": label, "btn_cerrar": btn_cerrar, "numero": numero,
        }
        return pestana_id

    def _cerrar_pestana_venta(self, pestana_id: str):
        if len(self.pestanas_venta) <= 1:
            messagebox.showinfo(
                "No se puede cerrar",
                "Debe quedar al menos una pestaña de venta abierta."
            )
            return

        info = self.pestanas_venta[pestana_id]
        if info["panel"].items_venta:
            if not messagebox.askyesno(
                "Cerrar venta en curso",
                "Esta pestaña tiene productos cargados que no se procesaron.\n\n"
                "¿Seguro que quieres cerrarla? Se perderá esa venta en curso."
            ):
                return

        era_la_activa = (self.pestana_actual == pestana_id)

        info["tab_frame"].destroy()
        info["panel"].destroy()
        del self.pestanas_venta[pestana_id]

        if era_la_activa:
            # Activar la pestaña de venta más reciente que quede disponible.
            siguiente_id = list(self.pestanas_venta.keys())[-1]
            self._activar_pestana(siguiente_id)

    def _al_finalizar_venta(self, pestana_id: str):
        """Se llama cuando una venta se cobra con éxito. Navega al Resumen
        para mostrar la venta recién registrada. La pestaña de venta NO se
        cierra sola: se queda abierta (ya reiniciada/vacía por
        _reiniciar_venta) lista para la próxima venta, y solo se cierra si
        el usuario hace clic en su botón '✕' manualmente."""
        self._activar_pestana("resumen")  # ya llama _cargar_datos internamente

    def _refrescar_resumen_si_visible(self):
        """Se llama tras registrar una Entrada (F7) o Salida (F8) de efectivo
        desde cualquier pestaña de venta. Recarga siempre los datos del panel
        de Resumen (Ventas en Efectivo, Entradas, Salidas, Dinero en Caja),
        esté o no visible en este momento, para que al volver a esa pestaña
        ya estén actualizados."""
        self.panel_resumen._cargar_datos()

    # ---------------- ACTIVAR / CAMBIAR DE PESTAÑA ----------------
    def _activar_pestana(self, pestana_id: str):
        self.pestana_actual = pestana_id

        # Ocultar todo
        self.panel_resumen.pack_forget()
        for info in self.pestanas_venta.values():
            info["panel"].pack_forget()

        # Restaurar colores de todas las pestañas a "inactiva"
        self.tab_resumen_frame.config(bg=self.COLOR_TAB_INACTIVA)
        self.label_tab_resumen.config(bg=self.COLOR_TAB_INACTIVA)
        for info in self.pestanas_venta.values():
            info["tab_frame"].config(bg=self.COLOR_TAB_INACTIVA)
            info["label"].config(bg=self.COLOR_TAB_INACTIVA)
            info["btn_cerrar"].config(bg=self.COLOR_TAB_INACTIVA)

        if pestana_id == "resumen":
            self.panel_resumen.pack(fill="both", expand=True)
            self.tab_resumen_frame.config(bg=self.COLOR_TAB_ACTIVA)
            self.label_tab_resumen.config(bg=self.COLOR_TAB_ACTIVA)
            self.panel_resumen._cargar_datos()
        else:
            info = self.pestanas_venta[pestana_id]
            info["panel"].pack(fill="both", expand=True)
            info["tab_frame"].config(bg=self.COLOR_TAB_ACTIVA)
            info["label"].config(bg=self.COLOR_TAB_ACTIVA)
            info["btn_cerrar"].config(bg=self.COLOR_TAB_ACTIVA)
            # Devuelve el foco al campo "Código del Producto" de ESTA
            # pestaña. Es clave para que un lector de código de barras
            # (que solo tipea donde está el cursor) siempre cargue el
            # producto en la pestaña que se está viendo, sin importar en
            # cuál se haya usado el lector la última vez. El 'after' es
            # necesario porque el foco recién se puede tomar una vez que
            # Tkinter terminó de mostrar (pack) el widget.
            self.after(10, info["panel"].entry_codigo.focus_set)

# ─────────────────────────────────────────────────────────────
#  VENTANA DE DETALLE DE ENTRADAS / SALIDAS DE CAJA (F7 / F8)
# ─────────────────────────────────────────────────────────────
class _VentanaDetalleMovimientoCaja(tk.Toplevel):
    """Se abre automáticamente tras registrar una Entrada (F7) o Salida (F8)
    de efectivo, mostrando todos los movimientos del tipo registrado en el
    día actual. Mismo diseño que la ventana de detalle del Resumen de Ventas."""

    def __init__(self, parent, tipo: str):
        super().__init__(parent)
        import datetime
        from models_ventas import listar_movimientos_caja

        self._tipo      = tipo
        es_entrada      = tipo == "entrada"
        hoy             = datetime.date.today()
        fecha_str       = hoy.isoformat()
        fecha_fmt       = hoy.strftime("%d/%m/%Y")
        self._movs      = [m for m in listar_movimientos_caja(fecha_str, fecha_str)
                           if m["tipo"] == tipo]

        titulo     = "Detalle de Entradas" if es_entrada else "Detalle de Salidas"
        color_hdr  = "#16a34a"             if es_entrada else "#dc2626"
        icono      = "📥"                  if es_entrada else "📤"
        fg_color   = "#166534"             if es_entrada else "#991b1b"
        bg_row     = "#f0fdf4"             if es_entrada else "#fef2f2"

        self.title(titulo)
        self.geometry("560x380")
        self.minsize(480, 300)
        self.resizable(True, True)
        self.configure(bg="white")
        self.grab_set()

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Barra de título ─────────────────────────────────
        barra = tk.Frame(self, bg=color_hdr, height=36)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra,
                 text=f"{icono}  {titulo} — {fecha_fmt}",
                 font=("Segoe UI", 10, "bold"),
                 bg=color_hdr, fg="white"
                 ).pack(side="left", padx=15, pady=7)

        # ── Tabla ───────────────────────────────────────────
        cont = tk.Frame(self, bg="white")
        cont.grid(row=1, column=0, sticky="nsew", padx=8, pady=(6, 0))
        cont.grid_rowconfigure(0, weight=1)
        cont.grid_columnconfigure(0, weight=1)

        cols   = ("hora", "monto", "motivo", "usuario")
        encabs = ("Hora", "Monto", "Motivo", "Registrado por")
        anchos = (70, 110, 230, 130)

        tabla = ttk.Treeview(cont, columns=cols, show="headings",
                             selectmode="browse")
        habilitar_deseleccion_treeview(tabla)
        for col, enc, ancho in zip(cols, encabs, anchos):
            tabla.heading(col, text=enc)
            tabla.column(col, width=ancho,
                         anchor="center" if col in ("hora", "monto") else "w",
                         minwidth=50)
        tabla.tag_configure("mov", background=bg_row, foreground=fg_color)

        sb_y = ttk.Scrollbar(cont, orient="vertical",   command=tabla.yview)
        sb_x = ttk.Scrollbar(cont, orient="horizontal", command=tabla.xview)
        tabla.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        tabla.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x.grid(row=1, column=0, sticky="ew")

        total = 0.0
        for m in self._movs:
            hora   = m["fecha"].split(" ")[1][:5] if " " in m["fecha"] else "—"
            total += m["monto"]
            tabla.insert("", "end", tags=("mov",), values=(
                hora,
                formatear_gs(m['monto']),
                m["descripcion"],
                m["usuario"],
            ))

        if not self._movs:
            tk.Label(cont,
                     text=f"No hay {titulo.lower()} registradas hoy.",
                     font=("Segoe UI", 9), bg="white", fg="#9ca3af"
                     ).grid(row=0, column=0, pady=50)

        # ── Pie: total + cerrar ──────────────────────────────
        pie = tk.Frame(self, bg="#f8f9fa", height=40)
        pie.grid(row=2, column=0, sticky="ew")
        pie.grid_propagate(False)

        signo = "+" if es_entrada else "−"
        tk.Label(pie,
                 text=t("ventas_total_del_dia").format(signo=signo, total=f"{total:,.0f}"),
                 font=("Segoe UI", 10, "bold"),
                 bg="#f8f9fa", fg=fg_color
                 ).pack(side="left", padx=14, pady=9)

        tk.Button(pie, text=t("cerrar"),
                  font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, padx=12, pady=3,
                  cursor="hand2", command=self.destroy
                  ).pack(side="right", padx=12, pady=7)
