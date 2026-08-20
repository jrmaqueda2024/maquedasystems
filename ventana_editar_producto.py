"""
ventana_editar_producto.py
Ventana modal "Editar Producto" / "Nuevo Producto" con 5 pestañas tipo Ribbon:
Datos, Datos Adicionales, Imágenes, Proveedor, Opciones.
Replica el diseño visual de MetaVentas.

IMPORTANTE: todas las variables (tk.StringVar / tk.BooleanVar) que respaldan
los campos del formulario se crean UNA SOLA VEZ en _inicializar_variables(),
llamado desde __init__. Los métodos _mostrar_pestana_* NUNCA recrean estas
variables — solo construyen los widgets que las muestran. Esto es lo que
permite que los datos se conserven al navegar entre pestañas.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import shutil
import os

from models_catalogo import (
    crear_producto, editar_producto, cambiar_codigo_producto,
    producto_tiene_movimientos, listar_marcas, listar_categorias,
    crear_marca, crear_categoria, listar_proveedores, listar_productos,
)
from utilidades_ui import forzar_mayusculas, ajustar_tamaño_ventana, obtener_carpeta_base

AZUL_RIBBON = "#1d5fd6"
GRIS_FONDO = "#e9eaee"
GRIS_CLARO = "#f4f5f7"

UNIDADES_MEDIDA = ["Unidad", "Kilogramo", "Litro", "Metro", "Caja", "Paquete", "Docena"]
TIPOS_IMPUESTO = ["IVA 10%", "IVA 5%", "Exento"]

UNIDADES_FRACCIONABLES = {"Kilogramo", "Litro", "Metro"}


class VentanaEditarProducto(tk.Toplevel):
    def __init__(self, parent, producto, on_guardado, usuario_actual=None):
        super().__init__(parent)
        self.producto = producto
        self.on_guardado = on_guardado
        self.usuario_actual = usuario_actual
        self.es_edicion = producto is not None
        self.ruta_imagen_nueva = None
        self.imagen_marcada_para_eliminar = False

        self.title("Editar Producto" if self.es_edicion else "Nuevo Producto")
        self.minsize(480, 560)
        self.resizable(True, True)
        self.configure(bg=GRIS_FONDO)
        self.grab_set()

        # Layout raíz responsive: fila 0 = barra de título (fija),
        # fila 1 = pestañas (fija), fila 2 = herramientas (fija),
        # fila 3 = cuerpo (se expande), fila 4 = botones (fija).
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._inicializar_variables()

        self._construir_barra_pestanas()
        self.frame_cuerpo = tk.Frame(self, bg=GRIS_CLARO)
        self.frame_cuerpo.grid(row=3, column=0, sticky="nsew")

        self._construir_botones_inferiores()

        self.pestana_actual = "Datos"
        self._mostrar_pestana_datos()

        # Enter guarda el producto sin importar en qué pestaña o campo esté
        # el foco (Código Secundario, precios, combos, radiobuttons, stock
        # en Opciones, etc.), no solo cuando el foco está en el botón
        # Guardar. La única excepción es el campo "Descripción" (multilínea):
        # ahí Enter sigue insertando un salto de línea como siempre — ver
        # _al_presionar_enter.
        self.bind("<Return>", self._al_presionar_enter)

        # Tamaño inicial calculado según el contenido real de la pestaña
        # "Datos" (la primera que se muestra). Las demás pestañas vuelven a
        # ajustar el tamaño al activarse, en _cambiar_pestana, para que
        # ninguna quede con campos cortados sin importar cuál tenga más
        # contenido (ej. 'Datos Adicionales' u 'Opciones').
        ajustar_tamaño_ventana(self, ancho_min=480, alto_min=560)

    def _inicializar_variables(self):
        p = self.producto if self.es_edicion else {}

        self.var_codigo = tk.StringVar(value=str(p.get("id")) if self.es_edicion else "(automático)")
        self.var_codigo_secundario = tk.StringVar(value=p.get("codigo_secundario", ""))
        self.var_codigo_barras = tk.StringVar(value=p.get("codigo_barras", ""))
        self.var_descripcion = tk.StringVar(value=p.get("nombre", ""))
        self.var_unidad = tk.StringVar(value=p.get("unidad_medida", "Unidad"))
        self.var_impuesto = tk.StringVar(value=p.get("tipo_impuesto", "IVA 10%"))
        self.var_precio_compra = tk.StringVar(value=self._formato_inicial_precio(p.get("precio_compra")))
        self.var_precio_venta = tk.StringVar(value=self._formato_inicial_precio(p.get("precio_venta")))
        self.var_precio_credito = tk.StringVar(value=self._formato_inicial_precio(p.get("precio_credito")))
        self.var_precio_mayorista = tk.StringVar(value=self._formato_inicial_precio(p.get("precio_mayorista")))

        marcas = listar_marcas()
        categorias = listar_categorias()
        marca_actual = next((m["nombre"] for m in marcas if m["id"] == p.get("marca_id")), "")
        categoria_actual = next((c["nombre"] for c in categorias if c["id"] == p.get("categoria_id")), "")
        self.var_marca = tk.StringVar(value=marca_actual)
        self.var_categoria = tk.StringVar(value=categoria_actual)

        proveedores = listar_proveedores()
        proveedor_actual = next((pr["nombre"] for pr in proveedores if pr["id"] == p.get("proveedor_id")), "")
        self.var_proveedor = tk.StringVar(value=proveedor_actual)
        self.proveedores_cache = {pr["nombre"]: pr for pr in proveedores}

        self.var_tipo_producto = tk.StringVar(value=p.get("tipo_producto", "Producto"))
        self.var_control_stock = tk.StringVar(value=p.get("control_stock", "Cantidad"))
        self.var_articulo_comun = tk.BooleanVar(value=p.get("es_articulo_comun", False))
        self.var_stock_inicial = tk.StringVar(value="0" if not self.es_edicion else self._formato_cantidad(p.get("stock", 0)))
        self.var_stock_minimo = tk.StringVar(value=self._formato_cantidad(p.get("stock_minimo", 0)))

        # Referencias a los widgets de Stock Inicial/Mínimo (se completan
        # al construir la pestaña "Opciones"). Cuando el control de stock
        # es "Ilimitado" esos campos no aplican, así que se inhabilitan.
        self._widgets_stock_inicial = None
        self._widgets_stock_minimo = None
        self.var_control_stock.trace_add("write", self._sync_control_stock)

    def _formato_inicial_precio(self, valor):
        if valor is None or valor == "":
            return ""
        return f"{valor:g}" if isinstance(valor, (int, float)) else str(valor)

    def _formato_cantidad(self, valor):
        try:
            valor = float(valor)
        except (TypeError, ValueError):
            return "0"
        return f"{valor:g}".replace(".", ",") if self._unidad_es_fraccionable() else str(int(valor))

    def _unidad_es_fraccionable(self):
        return self.var_unidad.get() in UNIDADES_FRACCIONABLES

    def _construir_barra_pestanas(self):
        barra_titulo = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra_titulo.grid(row=0, column=0, sticky="ew")
        barra_titulo.grid_propagate(False)
        tk.Label(barra_titulo, text=self.title(), font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(pady=7)

        self.frame_tabs = tk.Frame(self, bg=AZUL_RIBBON, height=28)
        self.frame_tabs.grid(row=1, column=0, sticky="ew")
        self.frame_tabs.grid_propagate(False)

        self.botones_tab = {}
        nombres_tabs = ["Datos", "Datos Adicionales", "Imágenes", "Proveedor", "Opciones"]
        for nombre in nombres_tabs:
            btn = tk.Label(self.frame_tabs, text=nombre, font=("Segoe UI", 9),
                           bg=AZUL_RIBBON, fg="white", cursor="hand2", padx=10)
            btn.pack(side="left", fill="y", pady=4)
            btn.bind("<Button-1>", lambda e, n=nombre: self._cambiar_pestana(n))
            self.botones_tab[nombre] = btn

        self.frame_ribbon_herramientas = tk.Frame(self, bg=GRIS_FONDO, height=18)
        self.frame_ribbon_herramientas.grid(row=2, column=0, sticky="ew")
        self.frame_ribbon_herramientas.grid_propagate(False)

    def _resaltar_pestana_activa(self):
        for nombre, btn in self.botones_tab.items():
            if nombre == self.pestana_actual:
                btn.config(bg=GRIS_CLARO, fg=AZUL_RIBBON, font=("Segoe UI", 9, "bold"))
            else:
                btn.config(bg=AZUL_RIBBON, fg="white", font=("Segoe UI", 9))

    def _limpiar_cuerpo(self):
        for widget in self.frame_cuerpo.winfo_children():
            widget.destroy()
        for widget in self.frame_ribbon_herramientas.winfo_children():
            widget.destroy()

    def _cambiar_pestana(self, nombre):
        self.pestana_actual = nombre
        self._resaltar_pestana_activa()
        self._limpiar_cuerpo()
        metodo = {
            "Datos": self._mostrar_pestana_datos,
            "Datos Adicionales": self._mostrar_pestana_datos_adicionales,
            "Imágenes": self._mostrar_pestana_imagenes,
            "Proveedor": self._mostrar_pestana_proveedor,
            "Opciones": self._mostrar_pestana_opciones,
        }[nombre]
        metodo()

        # Cada pestaña puede tener más o menos contenido que la anterior
        # (ej. 'Opciones' u 'Datos Adicionales' suelen ser más altas que
        # 'Proveedor'). Se usa el tamaño ACTUAL de la ventana como piso,
        # para que la ventana solo crezca si la nueva pestaña lo necesita
        # y nunca quede con campos cortados, sin achicarse molestamente al
        # volver a una pestaña más corta.
        ajustar_tamaño_ventana(
            self, ancho_min=self.winfo_width(), alto_min=self.winfo_height(),
            mantener_posicion=True,
        )

    def _mostrar_pestana_datos(self):
        self._resaltar_pestana_activa()

        if not self.es_edicion:
            btn_generar = tk.Label(self.frame_ribbon_herramientas, text="⚙ Generar Código",
                                   font=("Segoe UI", 7), bg=GRIS_FONDO, fg="#333", cursor="hand2")
            btn_generar.pack(side="left", padx=8)
            btn_generar.bind("<Button-1>", lambda e: self._generar_codigo_sugerido())

        campos = tk.Frame(self.frame_cuerpo, bg=GRIS_CLARO)
        campos.pack(fill="both", expand=True, padx=20, pady=15)

        tk.Label(campos, text="Código:", font=("Segoe UI", 9, "bold"), bg=GRIS_CLARO).grid(
            row=0, column=0, sticky="w", pady=4)
        entry_codigo = tk.Entry(campos, textvariable=self.var_codigo, font=("Segoe UI", 9),
                                 state="readonly", width=22)
        entry_codigo.grid(row=0, column=1, pady=4, sticky="w")
        if self.es_edicion:
            tk.Button(campos, text="Cambiar", font=("Segoe UI", 7),
                      command=self._cambiar_codigo).grid(row=0, column=2, padx=4)

        filas = [
            ("Código Secundario:", self.var_codigo_secundario, "entry_mayusculas"),
            ("Código de Barras:", self.var_codigo_barras, "entry_mayusculas"),
        ]

        for i, (etiqueta, var, tipo) in enumerate(filas, start=1):
            tk.Label(campos, text=etiqueta, font=("Segoe UI", 9, "bold"), bg=GRIS_CLARO).grid(
                row=i, column=0, sticky="w", pady=4)
            entry = tk.Entry(campos, textvariable=var, font=("Segoe UI", 9), width=22)
            entry.grid(row=i, column=1, pady=4, sticky="w")
            forzar_mayusculas(entry, var)
            if var is self.var_codigo_barras or var is self.var_codigo_secundario:
                # Un lector de código de barras "escribe" el código y termina
                # con un Enter automático, como si el usuario lo hubiera
                # tecleado — sin este freno, ese Enter dispara el guardado
                # general del formulario (self._al_presionar_enter) y cierra
                # la ventana a mitad de carga. Acá se consume ese Enter
                # puntual (con "break") para que solo complete el campo, sin
                # afectar el atajo de Enter en el resto del formulario.
                # Se aplica tanto a Código de Barras como a Código
                # Secundario, porque ambos se suelen cargar con la pistola
                # lectora en la práctica.
                entry.bind("<Return>", lambda e: "break")
                # Referencia guardada para la segunda barrera de seguridad
                # en _al_presionar_enter (ver ese método para el detalle).
                if var is self.var_codigo_barras:
                    self._entry_codigo_barras = entry
                else:
                    self._entry_codigo_secundario = entry

        # --- Descripción: campo de texto multilínea expandible, con scroll
        # y una esquina arrastrable para agrandarlo (igual al "resize handle"
        # de un <textarea>), para poder ver bien descripciones largas. ---
        fila_descripcion = len(filas) + 1
        tk.Label(campos, text="Descripción:", font=("Segoe UI", 9, "bold"), bg=GRIS_CLARO).grid(
            row=fila_descripcion, column=0, sticky="nw", pady=4)

        contenedor_descripcion = tk.Frame(campos, bg=GRIS_CLARO)
        contenedor_descripcion.grid(row=fila_descripcion, column=1, columnspan=2, pady=4, sticky="we")
        campos.grid_rowconfigure(fila_descripcion, weight=0)

        self.texto_descripcion = tk.Text(
            contenedor_descripcion, font=("Segoe UI", 9), width=34, height=3, wrap="word",
            relief="solid", bd=1, undo=True,
        )
        self.texto_descripcion.grid(row=0, column=0, sticky="nsew")
        scrollbar_descripcion = ttk.Scrollbar(contenedor_descripcion, orient="vertical",
                                               command=self.texto_descripcion.yview)
        scrollbar_descripcion.grid(row=0, column=1, sticky="ns")
        self.texto_descripcion.configure(yscrollcommand=scrollbar_descripcion.set)

        # Esquina inferior derecha arrastrable: redimensiona el alto del
        # cuadro de texto (en filas de texto), simulando el "resize handle"
        # de un <textarea> de navegador.
        agarradera = tk.Label(contenedor_descripcion, text="◢", font=("Segoe UI", 8), bg=GRIS_CLARO,
                              fg="#999", cursor="sizing")
        agarradera.grid(row=1, column=0, sticky="e")
        agarradera.bind("<B1-Motion>", self._al_arrastrar_agarradera_descripcion)
        self._y_inicial_arrastre = None

        self.texto_descripcion.insert("1.0", self.var_descripcion.get())
        self.texto_descripcion.bind("<KeyRelease>", self._al_escribir_descripcion)
        # Tab normalmente inserta una tabulación dentro de un tk.Text; lo
        # interceptamos para que en cambio mueva el foco al siguiente campo,
        # como en cualquier otro Entry del formulario.
        self.texto_descripcion.bind("<Tab>", self._tab_sale_de_descripcion)
        self.texto_descripcion.bind("<Shift-Tab>", self._shift_tab_sale_de_descripcion)

        filas_resto = [
            ("Unidad de Medida:", self.var_unidad, "combo_unidad"),
            ("Tipo de Impuesto:", self.var_impuesto, "combo_impuesto"),
            ("Precio Compra:", self.var_precio_compra, "entry"),
            ("Precio Venta:", self.var_precio_venta, "entry"),
            ("Precio Crédito:", self.var_precio_credito, "entry"),
            ("Precio Mayorista:", self.var_precio_mayorista, "entry"),
        ]

        # Bandera: se pone en True apenas el usuario escribe algo a mano en
        # Precio Crédito, para dejar de autocompletarlo desde Precio Venta.
        self._credito_editado_manualmente = bool(self.var_precio_credito.get().strip())

        # Referencias a los 4 Entry de precio: se usan tanto para el filtro
        # de tecla en tiempo real de abajo como para releer su valor real
        # (entry.get()) justo antes de guardar — ver _guardar_impl().
        self.entries_precio = {}

        for i, (etiqueta, var, tipo) in enumerate(filas_resto, start=fila_descripcion + 1):
            tk.Label(campos, text=etiqueta, font=("Segoe UI", 9, "bold"), bg=GRIS_CLARO).grid(
                row=i, column=0, sticky="w", pady=4)
            if tipo == "entry":
                entry = tk.Entry(campos, textvariable=var, font=("Segoe UI", 9), width=22)
                entry.grid(row=i, column=1, pady=4, sticky="w")
                self.entries_precio[etiqueta] = entry
                # Filtro en tiempo real: un precio en Guaraní es siempre un
                # entero, así que cualquier caracter que no sea dígito se
                # descarta apenas se escribe (mismo criterio que ya se usa
                # en Stock Inicial/Mínimo — ver _filtrar_tecla más abajo).
                # Esto evita que un caracter inesperado (por ejemplo, una
                # coma o un símbolo que se cuele por un problema de
                # distribución de teclado del lector de código de barras)
                # quede sin detectarse hasta el momento de guardar.
                entry.bind("<KeyRelease>", lambda e, _var=var, _entry=entry: self._filtrar_tecla_precio(_var, _entry))
                if etiqueta == "Precio Venta:":
                    self.entry_precio_venta = entry
                    var.trace_add("write", self._al_escribir_precio_venta)
                elif etiqueta == "Precio Crédito:":
                    self.entry_precio_credito = entry
                    entry.bind("<KeyRelease>", lambda e, _var=var, _entry=entry: (
                        self._filtrar_tecla_precio(_var, _entry),
                        self._al_escribir_precio_credito_manual(e),
                    ), add=False)
            elif tipo == "combo_unidad":
                combo = ttk.Combobox(campos, textvariable=var, values=UNIDADES_MEDIDA,
                                      font=("Segoe UI", 9), width=20, state="readonly")
                combo.grid(row=i, column=1, pady=4, sticky="w")
                combo.bind("<<ComboboxSelected>>", lambda e: self._al_cambiar_unidad_medida())
            elif tipo == "combo_impuesto":
                ttk.Combobox(campos, textvariable=var, values=TIPOS_IMPUESTO,
                             font=("Segoe UI", 9), width=20, state="readonly").grid(
                    row=i, column=1, pady=4, sticky="w")

    def _al_escribir_descripcion(self, event=None):
        """Sincroniza el contenido del Text con var_descripcion (en
        mayúsculas), para que _guardar() y la validación sigan funcionando
        igual que con cualquier otro campo de texto."""
        texto_actual = self.texto_descripcion.get("1.0", "end-1c")
        texto_mayusculas = texto_actual.upper()
        if texto_actual != texto_mayusculas:
            posicion_cursor = self.texto_descripcion.index(tk.INSERT)
            self.texto_descripcion.delete("1.0", "end")
            self.texto_descripcion.insert("1.0", texto_mayusculas)
            self.texto_descripcion.mark_set(tk.INSERT, posicion_cursor)
        self.var_descripcion.set(self.texto_descripcion.get("1.0", "end-1c"))

    def _al_escribir_precio_venta(self, *_args):
        """Mientras el usuario no haya escrito un valor propio en Precio
        Crédito, lo mantiene sincronizado con Precio Venta automáticamente."""
        if self._credito_editado_manualmente:
            return
        self.var_precio_credito.set(self.var_precio_venta.get())

    def _filtrar_tecla_precio(self, var, entry):
        """Descarta en tiempo real cualquier caracter que no sea un dígito
        en los 4 campos de precio (Compra/Venta/Crédito/Mayorista). El
        Guaraní no tiene decimales, así que un precio válido es siempre
        solo dígitos — no hace falta permitir coma ni punto acá (a
        diferencia de las cantidades de Stock, que sí pueden ser
        fraccionarias según la unidad de medida).

        Esto es una defensa adicional para que ningún caracter inesperado
        (por ejemplo, si un lector de código de barras deja el teclado en
        un estado raro y un símbolo se cuela en vez del dígito esperado)
        pueda arruinar el precio de forma silenciosa: se limpia al toque,
        en vez de recién detectarse (o no) al momento de guardar."""
        if not self.winfo_exists():
            return
        texto = var.get()
        limpio = "".join(c for c in texto if c.isdigit())
        if limpio != texto:
            pos = entry.index("insert")
            var.set(limpio)
            entry.icursor(max(0, pos - (len(texto) - len(limpio))))

    def _al_escribir_precio_credito_manual(self, event=None):
        """En cuanto el usuario toca Precio Crédito directamente, se
        considera 'editado a mano' y deja de copiarse desde Precio Venta."""
        self._credito_editado_manualmente = True

    def _tab_sale_de_descripcion(self, event):
        """Tab dentro de un tk.Text inserta una tabulación por defecto.
        Lo interceptamos para que en cambio mueva el foco al siguiente
        widget del formulario, igual que en los demás campos Entry."""
        event.widget.tk_focusNext().focus()
        return "break"  # evita que el Text inserte el carácter de tabulación

    def _shift_tab_sale_de_descripcion(self, event):
        """Shift+Tab: mueve el foco al campo anterior del formulario."""
        event.widget.tk_focusPrev().focus()
        return "break"

    def _al_arrastrar_agarradera_descripcion(self, event):
        """Permite agrandar/achicar el cuadro de Descripción arrastrando la
        esquina inferior derecha, igual al resize handle de un textarea."""
        altura_linea_aprox = 18  # píxeles aproximados por línea de texto a este tamaño de fuente
        nuevas_filas = max(2, min(12, event.y // altura_linea_aprox))
        self.texto_descripcion.configure(height=nuevas_filas)

    def _al_cambiar_unidad_medida(self):
        self._reformatear_campo_cantidad(self.var_stock_inicial)
        self._reformatear_campo_cantidad(self.var_stock_minimo)

    def _reformatear_campo_cantidad(self, var):
        valor = self._parsear_cantidad(var.get())
        var.set(self._formato_cantidad(valor))

    def _generar_codigo_sugerido(self):
        productos = listar_productos(solo_activos=False)
        siguiente = (max((p["id"] for p in productos), default=0)) + 1
        self.var_codigo.set(str(siguiente))

    def _cambiar_codigo(self):
        ventana = tk.Toplevel(self)
        ventana.title("Cambiar Código")
        ventana.grab_set()
        tk.Label(ventana, text="Nuevo código:", font=("Segoe UI", 10)).pack(pady=(15, 5))
        var_nuevo = tk.StringVar(value=str(self.producto["id"]))
        tk.Entry(ventana, textvariable=var_nuevo, font=("Segoe UI", 10)).pack()

        def confirmar():
            try:
                nuevo = int(var_nuevo.get())
            except ValueError:
                messagebox.showerror("Error", "El código debe ser un número entero.")
                return
            ok, msg = cambiar_codigo_producto(self.producto["id"], nuevo)
            if ok:
                self.producto["id"] = nuevo
                self.var_codigo.set(str(nuevo))
                messagebox.showinfo("Listo", msg)
                ventana.destroy()
            else:
                messagebox.showerror("Error", msg)

        tk.Button(ventana, text="Confirmar", bg="#16a34a", fg="white",
                  command=confirmar).pack(pady=15)

        ajustar_tamaño_ventana(ventana, ancho_min=260, alto_min=120)

    def _mostrar_pestana_datos_adicionales(self):
        nombres_marcas = [m["nombre"] for m in listar_marcas()]
        nombres_categorias = [c["nombre"] for c in listar_categorias()]

        contenedor = tk.Frame(self.frame_cuerpo, bg=GRIS_CLARO)
        contenedor.pack(fill="both", expand=True, padx=25, pady=40)

        tk.Label(contenedor, text="Marca:", font=("Segoe UI", 9, "bold"), bg=GRIS_CLARO).grid(
            row=0, column=0, sticky="w", pady=10)
        combo_marca = ttk.Combobox(contenedor, textvariable=self.var_marca, values=nombres_marcas,
                                    font=("Segoe UI", 9), width=24)
        combo_marca.grid(row=0, column=1, pady=10, sticky="w")
        forzar_mayusculas(combo_marca, self.var_marca)

        tk.Label(contenedor, text="Categoría:", font=("Segoe UI", 9, "bold"), bg=GRIS_CLARO).grid(
            row=1, column=0, sticky="w", pady=10)
        combo_categoria = ttk.Combobox(contenedor, textvariable=self.var_categoria, values=nombres_categorias,
                                        font=("Segoe UI", 9), width=24)
        combo_categoria.grid(row=1, column=1, pady=10, sticky="w")
        forzar_mayusculas(combo_categoria, self.var_categoria)

        tk.Label(contenedor, text="(Escribe un nombre nuevo para crearlo al guardar)",
                 font=("Segoe UI", 7), bg=GRIS_CLARO, fg="#777").grid(row=2, column=0, columnspan=2, pady=(5, 0))

    def _mostrar_pestana_imagenes(self):
        ruta_actual = self._ruta_imagen_efectiva()

        contenedor = tk.Frame(self.frame_cuerpo, bg=GRIS_CLARO)
        contenedor.pack(fill="both", expand=True, padx=20, pady=20)

        if ruta_actual and os.path.exists(ruta_actual):
            self._construir_vista_con_imagen(contenedor, ruta_actual)
        else:
            self._construir_vista_sin_imagen(contenedor)

    def _ruta_imagen_efectiva(self):
        """Determina qué imagen mostrar ahora mismo, respetando el orden:
        1) si el usuario marcó eliminar, no hay imagen;
        2) si eligió una imagen nueva, esa;
        3) si no, la que ya tenía el producto (en modo edición)."""
        if getattr(self, "imagen_marcada_para_eliminar", False):
            return None
        if self.ruta_imagen_nueva:
            return self.ruta_imagen_nueva
        return self.producto.get("imagen_ruta") if self.es_edicion else None

    def _construir_vista_sin_imagen(self, contenedor):
        label_drop = tk.Label(contenedor, text="Arrastre su imagen aquí\no click para buscar",
                               font=("Segoe UI", 10, "bold"), bg=GRIS_CLARO, fg="#888",
                               relief="solid", bd=1, cursor="hand2")
        label_drop.pack(fill="both", expand=True)
        label_drop.bind("<Button-1>", lambda e: self._seleccionar_imagen())

    def _construir_vista_con_imagen(self, contenedor, ruta_actual):
        # --- Vista previa real de la imagen (si Pillow está disponible) ---
        frame_preview = tk.Frame(contenedor, bg="white", relief="solid", bd=1)
        frame_preview.pack(fill="both", expand=True)

        label_preview = tk.Label(frame_preview, bg="white")
        label_preview.pack(fill="both", expand=True, padx=10, pady=10)
        self._cargar_vista_previa(label_preview, ruta_actual)

        # --- Información del archivo: nombre y peso ---
        frame_info = tk.Frame(contenedor, bg=GRIS_CLARO)
        frame_info.pack(fill="x", pady=(10, 10))

        nombre_archivo = os.path.basename(ruta_actual)
        try:
            tamano_bytes = os.path.getsize(ruta_actual)
            tamano_texto = self._formatear_tamano_archivo(tamano_bytes)
        except OSError:
            tamano_texto = "—"

        tk.Label(frame_info, text=f"📄 {nombre_archivo}", font=("Segoe UI", 9, "bold"),
                 bg=GRIS_CLARO, anchor="w").pack(anchor="w")
        tk.Label(frame_info, text=f"Peso: {tamano_texto}", font=("Segoe UI", 8),
                 bg=GRIS_CLARO, fg="#666", anchor="w").pack(anchor="w")

        # --- Botones: Cambiar imagen / Eliminar imagen ---
        frame_botones_imagen = tk.Frame(contenedor, bg=GRIS_CLARO)
        frame_botones_imagen.pack(fill="x")

        tk.Button(frame_botones_imagen, text="🔄 Cambiar Imagen", font=("Segoe UI", 9, "bold"),
                  bg="white", relief="solid", bd=1, padx=10, pady=6, cursor="hand2",
                  command=self._seleccionar_imagen).pack(side="left", padx=(0, 8))
        tk.Button(frame_botones_imagen, text="🗑 Eliminar Imagen", font=("Segoe UI", 9, "bold"),
                  bg="white", fg="#dc2626", relief="solid", bd=1, padx=10, pady=6, cursor="hand2",
                  command=self._eliminar_imagen).pack(side="left")

    def _cargar_vista_previa(self, label_widget, ruta_imagen):
        try:
            from PIL import Image, ImageTk
        except ImportError:
            label_widget.config(
                text="(Instala 'Pillow' para ver la vista previa: pip install Pillow)",
                font=("Segoe UI", 8), fg="#999",
            )
            return

        try:
            imagen = Image.open(ruta_imagen)
        except Exception:
            label_widget.config(text="No se pudo cargar la imagen.", font=("Segoe UI", 9), fg="#c00")
            return

        ancho_max, alto_max = 320, 280
        ancho_original, alto_original = imagen.size
        factor = min(ancho_max / ancho_original, alto_max / alto_original, 1)
        nuevo_tam = (max(1, int(ancho_original * factor)), max(1, int(alto_original * factor)))

        imagen_redimensionada = imagen.resize(nuevo_tam, Image.LANCZOS)
        self.imagen_preview_tk = ImageTk.PhotoImage(imagen_redimensionada)
        label_widget.config(image=self.imagen_preview_tk, text="")

    def _formatear_tamano_archivo(self, tamano_bytes: int) -> str:
        if tamano_bytes < 1024:
            return f"{tamano_bytes} B"
        if tamano_bytes < 1024 * 1024:
            return f"{tamano_bytes / 1024:.1f} KB"
        return f"{tamano_bytes / (1024 * 1024):.2f} MB"

    def _seleccionar_imagen(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar imagen del producto",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if ruta:
            self.ruta_imagen_nueva = ruta
            self.imagen_marcada_para_eliminar = False
            self._cambiar_pestana("Imágenes")

    def _eliminar_imagen(self):
        if not messagebox.askyesno("Eliminar imagen", "¿Seguro que quieres quitar la imagen de este producto?"):
            return
        self.ruta_imagen_nueva = None
        self.imagen_marcada_para_eliminar = True
        self._cambiar_pestana("Imágenes")

    def _mostrar_pestana_proveedor(self):
        nombres_proveedores = list(self.proveedores_cache.keys())

        contenedor = tk.Frame(self.frame_cuerpo, bg=GRIS_CLARO)
        contenedor.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(contenedor, text="Proveedor", font=("Segoe UI", 9, "bold"), bg=GRIS_CLARO).grid(
            row=0, column=0, sticky="w", pady=6)
        combo = ttk.Combobox(contenedor, textvariable=self.var_proveedor, values=nombres_proveedores,
                              font=("Segoe UI", 9), width=24, state="readonly")
        combo.grid(row=0, column=1, pady=6, sticky="w")
        combo.bind("<<ComboboxSelected>>", lambda e: self._actualizar_datos_proveedor())

        self.label_nombre_prov = tk.Label(contenedor, text="", font=("Segoe UI", 9), bg=GRIS_CLARO)
        self.label_ruc_prov = tk.Label(contenedor, text="", font=("Segoe UI", 9), bg=GRIS_CLARO)
        self.label_dir_prov = tk.Label(contenedor, text="", font=("Segoe UI", 9), bg=GRIS_CLARO)
        self.label_tel_prov = tk.Label(contenedor, text="", font=("Segoe UI", 9), bg=GRIS_CLARO)
        self.label_contacto_prov = tk.Label(contenedor, text="", font=("Segoe UI", 9), bg=GRIS_CLARO)

        etiquetas = ["Nombre:", "RUC:", "Dirección:", "Teléfono:", "Contacto:"]
        for i, texto in enumerate(etiquetas, start=1):
            tk.Label(contenedor, text=texto, font=("Segoe UI", 9, "bold"), bg=GRIS_CLARO).grid(
                row=i, column=0, sticky="e", pady=6)

        self.label_nombre_prov.grid(row=1, column=1, sticky="w")
        self.label_ruc_prov.grid(row=2, column=1, sticky="w")
        self.label_dir_prov.grid(row=3, column=1, sticky="w")
        self.label_tel_prov.grid(row=4, column=1, sticky="w")
        self.label_contacto_prov.grid(row=5, column=1, sticky="w")

        if self.var_proveedor.get():
            self._actualizar_datos_proveedor()

    def _actualizar_datos_proveedor(self):
        prov = self.proveedores_cache.get(self.var_proveedor.get())
        if prov:
            self.label_nombre_prov.config(text=prov["nombre"])
            self.label_ruc_prov.config(text=prov.get("ruc", "") or "")
            self.label_dir_prov.config(text=prov.get("direccion", "") or "")
            self.label_tel_prov.config(text=prov.get("telefono", "") or "")
            self.label_contacto_prov.config(text=prov.get("contacto", "") or "")

    def _mostrar_pestana_opciones(self):
        if self.es_edicion and producto_tiene_movimientos(self.producto["id"]):
            tk.Label(self.frame_cuerpo, text="⚠ Este producto ya tiene movimientos registrados.",
                     font=("Segoe UI", 8), bg="#fef3c7", fg="#92400e").pack(fill="x", pady=(2, 0))

        seccion_tipo = tk.Frame(self.frame_cuerpo, bg=AZUL_RIBBON)
        seccion_tipo.pack(fill="x", padx=15, pady=(15, 0))
        tk.Label(seccion_tipo, text="TIPO DE PRODUCTO", font=("Segoe UI", 8, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(anchor="w", padx=5, pady=2)

        frame_radios_tipo = tk.Frame(self.frame_cuerpo, bg=GRIS_CLARO)
        frame_radios_tipo.pack(fill="x", padx=15, pady=5)
        tk.Radiobutton(frame_radios_tipo, text="Producto", variable=self.var_tipo_producto, value="Producto",
                       font=("Segoe UI", 9), bg=GRIS_CLARO).pack(anchor="w")
        tk.Radiobutton(frame_radios_tipo, text="Servicio", variable=self.var_tipo_producto, value="Servicio",
                       font=("Segoe UI", 9), bg=GRIS_CLARO).pack(anchor="w")

        seccion_stock = tk.Frame(self.frame_cuerpo, bg=AZUL_RIBBON)
        seccion_stock.pack(fill="x", padx=15, pady=(15, 0))
        tk.Label(seccion_stock, text="STOCK", font=("Segoe UI", 8, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(anchor="w", padx=5, pady=2)

        frame_stock = tk.Frame(self.frame_cuerpo, bg=GRIS_CLARO)
        frame_stock.pack(fill="x", padx=15, pady=5)

        tk.Radiobutton(frame_stock, text="Cantidad", variable=self.var_control_stock, value="Cantidad",
                       font=("Segoe UI", 9), bg=GRIS_CLARO).grid(row=0, column=0, sticky="w", pady=3)
        tk.Radiobutton(frame_stock, text="Ilimitado", variable=self.var_control_stock, value="Ilimitado",
                       font=("Segoe UI", 9), bg=GRIS_CLARO).grid(row=1, column=0, sticky="w", pady=3)

        etiqueta_inicial = "Stock Inicial:" if not self.es_edicion else "Stock Actual:"
        tk.Label(frame_stock, text=etiqueta_inicial, font=("Segoe UI", 9), bg=GRIS_CLARO).grid(
            row=0, column=1, sticky="e", padx=(20, 6))
        self._widgets_stock_inicial = self._control_cantidad_con_botones(
            frame_stock, self.var_stock_inicial, row=0, column=2, solo_lectura=self.es_edicion)

        tk.Label(frame_stock, text="Stock Mínimo:", font=("Segoe UI", 9), bg=GRIS_CLARO).grid(
            row=1, column=1, sticky="e", padx=(20, 6))
        self._widgets_stock_minimo = self._control_cantidad_con_botones(
            frame_stock, self.var_stock_minimo, row=1, column=2)

        # Aplica de inmediato el estado habilitado/inhabilitado según el
        # control de stock actual (por ejemplo, al editar un producto que
        # ya estaba marcado como "Ilimitado").
        self._sync_control_stock()

        if self.es_edicion:
            tk.Label(self.frame_cuerpo,
                     text="El stock actual se modifica desde el módulo Inventario (Entrada/Salida).",
                     font=("Segoe UI", 7), bg=GRIS_CLARO, fg="#777", wraplength=340,
                     justify="left").pack(anchor="w", padx=18, pady=(2, 0))

        seccion_ventas = tk.Frame(self.frame_cuerpo, bg=AZUL_RIBBON)
        seccion_ventas.pack(fill="x", padx=15, pady=(15, 0))
        tk.Label(seccion_ventas, text="VENTAS", font=("Segoe UI", 8, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(anchor="w", padx=5, pady=2)

        frame_comun = tk.Frame(self.frame_cuerpo, bg=GRIS_CLARO)
        frame_comun.pack(fill="x", padx=15, pady=5)
        tk.Checkbutton(frame_comun, text="Marcar como Artículo Común (acceso rápido con Ctrl+P en Ventas)",
                       variable=self.var_articulo_comun, font=("Segoe UI", 9), bg=GRIS_CLARO,
                       wraplength=320, justify="left").pack(anchor="w")

    def _sync_control_stock(self, *_):
        """Inhabilita Stock Inicial/Actual y Stock Mínimo cuando el control
        de stock está en 'Ilimitado', ya que en ese caso esos valores no
        se usan. Se vuelve a habilitar (respetando el modo solo lectura de
        'Stock Actual' al editar) al elegir 'Cantidad'."""
        ilimitado = self.var_control_stock.get() == "Ilimitado"
        for widgets in (self._widgets_stock_inicial, self._widgets_stock_minimo):
            if not widgets:
                continue
            entry = widgets["entry"]
            if not entry.winfo_exists():
                continue
            if ilimitado:
                entry.config(state="disabled")
            else:
                entry.config(state="readonly" if widgets["solo_lectura"] else "normal")
            for btn in widgets["botones"]:
                if btn.winfo_exists():
                    btn.config(state="disabled" if ilimitado else "normal")

    def _control_cantidad_con_botones(self, parent, var, row, column, solo_lectura=False):
        frame = tk.Frame(parent, bg=GRIS_CLARO)
        frame.grid(row=row, column=column, sticky="w")

        entry = tk.Entry(frame, textvariable=var, font=("Segoe UI", 9), width=8,
                          justify="center", state="readonly" if solo_lectura else "normal")
        entry.pack(side="left")

        # Referencias devueltas para poder inhabilitar/habilitar este
        # control desde afuera (ej. al elegir stock "Ilimitado").
        widgets = {"entry": entry, "solo_lectura": solo_lectura, "botones": []}

        if not solo_lectura:
            def _filtrar_tecla(e, _var=var, _entry=entry):
                """Filtra caracteres inválidos después de cada tecla pulsada."""
                if not self.winfo_exists():
                    return
                texto = _var.get()
                if self._unidad_es_fraccionable():
                    # Solo dígitos y una coma
                    limpio = ""
                    comas = 0
                    for c in texto:
                        if c.isdigit():
                            limpio += c
                        elif c == "," and comas == 0:
                            limpio += c
                            comas += 1
                else:
                    # Solo dígitos enteros
                    limpio = "".join(c for c in texto if c.isdigit())
                if limpio != texto:
                    pos = _entry.index("insert")
                    _var.set(limpio)
                    _entry.icursor(max(0, pos - (len(texto) - len(limpio))))

            entry.bind("<KeyRelease>", _filtrar_tecla)
            entry.bind("<FocusOut>", lambda e, _var=var: (
                self.winfo_exists() and self._reformatear_campo_cantidad(_var)
            ))

            def incrementar():
                actual = self._parsear_cantidad(var.get())
                paso = 0.1 if self._unidad_es_fraccionable() else 1
                var.set(self._formato_cantidad(round(actual + paso, 3)))

            def decrementar():
                actual = self._parsear_cantidad(var.get())
                paso = 0.1 if self._unidad_es_fraccionable() else 1
                var.set(self._formato_cantidad(max(0, round(actual - paso, 3))))

            btn_mas = tk.Button(frame, text="＋", width=2, command=incrementar)
            btn_mas.pack(side="left", padx=(4, 0))
            btn_menos = tk.Button(frame, text="－", width=2, command=decrementar)
            btn_menos.pack(side="left", padx=(2, 0))
            widgets["botones"] = [btn_mas, btn_menos]

        return widgets

    def _validar_caracter_cantidad(self, valor_propuesto: str) -> bool:
        """Mantenido por compatibilidad — la validación real se hace en _filtrar_tecla."""
        return True

    def _parsear_cantidad(self, texto):
        """Convierte texto a número aceptando coma como decimal (guaraní paraguayo).
        Si la unidad es entera, devuelve siempre un entero (trunca decimales)."""
        try:
            valor = float(str(texto).replace(",", "."))
        except (TypeError, ValueError):
            return 0.0
        if not self._unidad_es_fraccionable():
            return float(int(round(valor)))
        return valor

    def _construir_botones_inferiores(self):
        frame_botones = tk.Frame(self, bg=GRIS_FONDO, height=58)
        frame_botones.grid(row=4, column=0, sticky="ew")
        frame_botones.grid_propagate(False)

        contenedor = tk.Frame(frame_botones, bg=GRIS_FONDO)
        contenedor.pack(pady=10)

        self._btn_guardar = tk.Button(contenedor, text="💾 Guardar", font=("Segoe UI", 10, "bold"),
                  bg=AZUL_RIBBON, fg="white", relief="flat", bd=0, padx=18, pady=8,
                  cursor="hand2", activebackground="#1747ad", activeforeground="white",
                  command=self._guardar)
        self._btn_guardar.pack(side="left", padx=10)
        self._btn_guardar.bind("<Return>", lambda e: self._guardar())

        self._btn_cancelar = tk.Button(contenedor, text="❌ Cancelar", font=("Segoe UI", 10, "bold"),
                  bg="white", fg="#333", relief="solid", bd=1, padx=18, pady=8,
                  cursor="hand2", activebackground="#f1f5f9",
                  command=self.destroy)
        self._btn_cancelar.pack(side="left", padx=10)

        def _cancelar_por_enter(event):
            # Enter con el foco en "Cancelar" cierra la ventana (como se
            # espera de ese botón), en vez de guardar — "break" corta la
            # propagación hacia el bind global de la ventana.
            self.destroy()
            return "break"
        self._btn_cancelar.bind("<Return>", _cancelar_por_enter)

    def _al_presionar_enter(self, event=None):
        """Permite guardar el producto con Enter desde cualquier pestaña y
        cualquier campo (Código Secundario, Código de Barras, precios,
        combos, radiobuttons, checkbox de Artículo Común, stock en la
        pestaña Opciones, etc.), no solo cuando el foco está en el botón
        Guardar.

        Excepciones:
        - Dentro del campo 'Descripción' (multilínea), Enter debe seguir
          insertando un salto de línea como siempre.
        - Desde Código Secundario o Código de Barras, un lector de código
          de barras termina la lectura con un Enter automático; esos
          campos ya cortan la propagación de ese Enter con 'break' (ver
          _mostrar_pestana_datos), pero se vuelve a chequear acá por las
          dudas, como segunda barrera, para que bajo ningún escenario ese
          Enter automático dispare un guardado a mitad de carga.
        """
        widget_enfocado = event.widget if event is not None else None
        if widget_enfocado is getattr(self, "texto_descripcion", None):
            return
        widgets_codigo_barras = [
            w for w in (getattr(self, "_entry_codigo_barras", None),
                        getattr(self, "_entry_codigo_secundario", None))
            if w is not None
        ]
        if widget_enfocado is not None and widget_enfocado in widgets_codigo_barras:
            return
        self._guardar()

    def _validar_numero(self, texto, nombre_campo):
        """Parsea un precio ingresado por el usuario, aceptando tanto el
        formato paraguayo (2.000 con punto de miles) como el anglosajón.
        El guaraní no tiene decimales, así que siempre devuelve int."""
        try:
            from utilidades_ui import parsear_cantidad
            valor = parsear_cantidad(str(texto).strip() or "0")
            return int(round(valor))
        except ValueError:
            messagebox.showerror("Dato inválido", f"'{nombre_campo}' debe ser un número.")
            return None

    def _resolver_marca_categoria(self):
        marca_id = None
        nombre_marca = self.var_marca.get().strip()
        if nombre_marca:
            existentes = {m["nombre"]: m["id"] for m in listar_marcas()}
            if nombre_marca not in existentes:
                crear_marca(nombre_marca)
                existentes = {m["nombre"]: m["id"] for m in listar_marcas()}
            marca_id = existentes.get(nombre_marca)

        categoria_id = None
        nombre_categoria = self.var_categoria.get().strip()
        if nombre_categoria:
            existentes = {c["nombre"]: c["id"] for c in listar_categorias()}
            if nombre_categoria not in existentes:
                crear_categoria(nombre_categoria)
                existentes = {c["nombre"]: c["id"] for c in listar_categorias()}
            categoria_id = existentes.get(nombre_categoria)

        return marca_id, categoria_id

    def _resolver_proveedor(self):
        nombre_proveedor = self.var_proveedor.get().strip()
        if not nombre_proveedor:
            return None
        prov = self.proveedores_cache.get(nombre_proveedor)
        return prov["id"] if prov else None

    def _guardar_imagen_si_corresponde(self, producto_id):
        """Devuelve:
        - la ruta del archivo nuevo, si el usuario eligió una imagen distinta;
        - "" (cadena vacía), si el usuario marcó eliminar la imagen actual
          (esto se guarda como 'sin imagen' en la base de datos);
        - None, si no hubo ningún cambio (se conserva lo que ya había)."""
        if self.imagen_marcada_para_eliminar:
            ruta_anterior = self.producto.get("imagen_ruta") if self.es_edicion else None
            if ruta_anterior and os.path.exists(ruta_anterior):
                try:
                    os.remove(ruta_anterior)
                except OSError:
                    pass  # si no se puede borrar el archivo físico, igual desvinculamos la referencia
            return ""

        if not self.ruta_imagen_nueva:
            return None

        carpeta_destino = os.path.join(obtener_carpeta_base(), "imagenes_productos")
        os.makedirs(carpeta_destino, exist_ok=True)
        extension = os.path.splitext(self.ruta_imagen_nueva)[1]
        destino = os.path.join(carpeta_destino, f"producto_{producto_id}{extension}")
        shutil.copyfile(self.ruta_imagen_nueva, destino)
        return destino

    def _guardar(self):
        """Guarda el producto. Usa un flag simple para evitar doble ejecución
        sin depender de deshabilitar/habilitar el botón (lo que causaba que
        el botón quedara deshabilitado permanentemente ante cualquier error)."""
        if getattr(self, "_en_guardado", False):
            return
        self._en_guardado = True
        try:
            self._guardar_impl()
        except Exception as e:
            messagebox.showerror("Error inesperado",
                                 f"Ocurrió un error al guardar:\n{e}")
        finally:
            self._en_guardado = False

    def _guardar_impl(self):
        # Si el widget de Descripción (Text multilínea) está actualmente
        # construido (pestaña Datos visible o ya visitada), sincronizamos su
        # contenido real con var_descripcion antes de validar/guardar, para
        # no depender únicamente del evento <KeyRelease>.
        if hasattr(self, "texto_descripcion") and self.texto_descripcion.winfo_exists():
            self.var_descripcion.set(self.texto_descripcion.get("1.0", "end-1c").strip())

        # Defensa adicional: releemos el valor REAL mostrado en cada Entry
        # de precio (entry.get()) y lo volvemos a poner en su StringVar
        # justo antes de validar. En el uso normal esto es un no-op (la
        # variable ya está sincronizada con lo que se ve en pantalla),
        # pero cubre cualquier caso raro en el que ambos hayan quedado
        # desincronizados (por ejemplo, tras una carga muy rápida con
        # lector de código de barras), garantizando que lo que se guarda
        # sea exactamente lo que el usuario ve escrito en el campo.
        mapa_var_precio = {
            "Precio Compra:": self.var_precio_compra,
            "Precio Venta:": self.var_precio_venta,
            "Precio Crédito:": self.var_precio_credito,
            "Precio Mayorista:": self.var_precio_mayorista,
        }
        for etiqueta, entry in getattr(self, "entries_precio", {}).items():
            if entry.winfo_exists() and etiqueta in mapa_var_precio:
                mapa_var_precio[etiqueta].set(entry.get())

        descripcion = self.var_descripcion.get().strip()
        if not descripcion:
            messagebox.showerror("Dato requerido", "La descripción es obligatoria.")
            self._cambiar_pestana("Datos")
            return

        precio_compra = self._validar_numero(self.var_precio_compra.get(), "Precio Compra")
        precio_venta = self._validar_numero(self.var_precio_venta.get(), "Precio Venta")
        precio_credito = self._validar_numero(self.var_precio_credito.get(), "Precio Crédito")
        precio_mayorista = self._validar_numero(self.var_precio_mayorista.get(), "Precio Mayorista")
        if None in (precio_compra, precio_venta, precio_credito, precio_mayorista):
            self._cambiar_pestana("Datos")
            return

        marca_id, categoria_id = self._resolver_marca_categoria()
        proveedor_id = self._resolver_proveedor()
        tipo_producto = self.var_tipo_producto.get()
        control_stock = self.var_control_stock.get()
        es_articulo_comun = self.var_articulo_comun.get()
        stock_minimo = self._parsear_cantidad(self.var_stock_minimo.get())

        if self.es_edicion:
            imagen_ruta = self._guardar_imagen_si_corresponde(self.producto["id"])
            uid = self.usuario_actual.get("id") if self.usuario_actual else None
            ok, msg = editar_producto(
                self.producto["id"], descripcion, precio_compra, precio_venta,
                precio_credito, precio_mayorista, self.producto.get("stock", 0),
                stock_minimo=stock_minimo,
                marca_id=marca_id, categoria_id=categoria_id, proveedor_id=proveedor_id,
                codigo_secundario=self.var_codigo_secundario.get(),
                codigo_barras=self.var_codigo_barras.get(),
                unidad_medida=self.var_unidad.get(), tipo_impuesto=self.var_impuesto.get(),
                tipo_producto=tipo_producto, control_stock=control_stock,
                imagen_ruta=imagen_ruta, es_articulo_comun=es_articulo_comun,
                usuario_id=uid,
            )
        else:
            stock_inicial = self._parsear_cantidad(self.var_stock_inicial.get())
            uid = self.usuario_actual.get("id") if self.usuario_actual else None
            ok, msg, nuevo_id = crear_producto(
                descripcion, precio_compra, precio_venta, precio_credito, precio_mayorista,
                stock=stock_inicial, stock_minimo=stock_minimo,
                marca_id=marca_id, categoria_id=categoria_id, proveedor_id=proveedor_id,
                codigo_secundario=self.var_codigo_secundario.get(),
                codigo_barras=self.var_codigo_barras.get(),
                unidad_medida=self.var_unidad.get(), tipo_impuesto=self.var_impuesto.get(),
                tipo_producto=tipo_producto, control_stock=control_stock,
                es_articulo_comun=es_articulo_comun, usuario_id=uid,
            )
            # Si el usuario adjuntó una imagen al crear el producto, recién
            # ahora existe el id necesario para guardarla con su nombre
            # definitivo y enlazarla al registro.
            if ok and nuevo_id and self.ruta_imagen_nueva:
                ruta_guardada = self._guardar_imagen_si_corresponde(nuevo_id)
                if ruta_guardada:
                    editar_producto(
                        nuevo_id, descripcion, precio_compra, precio_venta,
                        precio_credito, precio_mayorista, stock_inicial,
                        stock_minimo=stock_minimo, marca_id=marca_id, categoria_id=categoria_id,
                        proveedor_id=proveedor_id, codigo_secundario=self.var_codigo_secundario.get(),
                        codigo_barras=self.var_codigo_barras.get(), unidad_medida=self.var_unidad.get(),
                        tipo_impuesto=self.var_impuesto.get(), tipo_producto=tipo_producto,
                        control_stock=control_stock, imagen_ruta=ruta_guardada,
                        es_articulo_comun=es_articulo_comun, usuario_id=uid,
                    )

        if ok:
            self.on_guardado()
            self.destroy()
            messagebox.showinfo("Listo", msg)
        else:
            messagebox.showerror("Error al guardar", msg)