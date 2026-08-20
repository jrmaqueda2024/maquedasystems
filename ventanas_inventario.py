"""
ventanas_inventario.py
Ventanas modales del módulo Inventario: Agregar Inventario (Entrada),
Salida Inventario, Editar Stock Mínimo, e Historial de Movimientos.

Todas usan layout responsive (grid en la raíz + pack en el contenido),
por lo que se pueden maximizar o redimensionar sin que ningún campo o
botón quede oculto fuera del área visible.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from models_inventario import (
    registrar_entrada, registrar_salida, editar_stock_minimo, historial_movimientos,
    MOTIVOS_ENTRADA, MOTIVOS_SALIDA,
)
from utilidades_ui import (
    forzar_mayusculas, ajustar_tamaño_ventana, formatear_gs,
    habilitar_deseleccion_treeview, formatear_cantidad,
)

AZUL_RIBBON = "#1d5fd6"
GRIS_FONDO = "#e9eaee"
VERDE = "#16a34a"
ROJO = "#dc2626"


class _VentanaBaseMovimiento(tk.Toplevel):
    """Base compartida por Entrada y Salida: mismo layout, distinto comportamiento."""

    def __init__(self, parent, producto, usuario_actual, on_guardado):
        super().__init__(parent)
        self.producto = producto
        self.usuario_actual = usuario_actual
        self.on_guardado = on_guardado

        self.resizable(True, True)
        self.configure(bg=GRIS_FONDO)
        self.grab_set()

        # Layout raíz responsive: fila 0 = título (fija), fila 1 = cuerpo
        # (se expande), fila 2 = botones (fija).
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def _construir_titulo(self, texto):
        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text=texto, font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)
        cerrar = tk.Label(barra, text="✕", font=("Segoe UI", 11), bg=AZUL_RIBBON, fg="white", cursor="hand2")
        cerrar.pack(side="right", padx=15, pady=6)
        cerrar.bind("<Button-1>", lambda e: self.destroy())

    def _fila_solo_lectura(self, parent, fila, etiqueta, valor):
        tk.Label(parent, text=etiqueta, font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=fila, column=0, sticky="e", pady=6, padx=(0, 8))
        tk.Label(parent, text=valor, font=("Segoe UI", 9), bg="white").grid(
            row=fila, column=1, sticky="w", pady=6)

    def _control_cantidad(self, parent, fila, etiqueta):
        tk.Label(parent, text=etiqueta, font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=fila, column=0, sticky="e", pady=6, padx=(0, 8))
        frame_cant = tk.Frame(parent, bg="white")
        frame_cant.grid(row=fila, column=1, sticky="w", pady=6)

        var_cantidad = tk.StringVar(value="1")
        entry = tk.Entry(frame_cant, textvariable=var_cantidad, font=("Segoe UI", 9), width=8, justify="center")
        entry.pack(side="left")

        def incrementar():
            try:
                var_cantidad.set(str(float(var_cantidad.get() or 0) + 1))
            except ValueError:
                var_cantidad.set("1")

        def decrementar():
            try:
                actual = float(var_cantidad.get() or 0)
                var_cantidad.set(str(max(0, actual - 1)))
            except ValueError:
                var_cantidad.set("1")

        tk.Button(frame_cant, text="＋", width=2, command=incrementar).pack(side="left", padx=(4, 0))
        tk.Button(frame_cant, text="－", width=2, command=decrementar).pack(side="left", padx=(2, 0))
        return var_cantidad

    def _combo_motivo(self, parent, fila, motivos):
        tk.Label(parent, text="Motivo:", font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=fila, column=0, sticky="e", pady=6, padx=(0, 8))
        var_motivo = tk.StringVar(value=motivos[0])
        ttk.Combobox(parent, textvariable=var_motivo, values=motivos, font=("Segoe UI", 9),
                     width=22, state="readonly").grid(row=fila, column=1, sticky="w", pady=6)
        return var_motivo

    def _entry_texto(self, parent, fila, etiqueta, ancho=24):
        tk.Label(parent, text=etiqueta, font=("Segoe UI", 9, "bold"), bg="white").grid(
            row=fila, column=0, sticky="e", pady=6, padx=(0, 8))
        var = tk.StringVar()
        entry = tk.Entry(parent, textvariable=var, font=("Segoe UI", 9), width=ancho)
        entry.grid(row=fila, column=1, sticky="w", pady=6)
        forzar_mayusculas(entry, var)
        return var

    def _validar_cantidad(self, texto):
        try:
            valor = float(texto.replace(",", "."))
            if valor <= 0:
                raise ValueError
            return valor
        except ValueError:
            messagebox.showerror("Cantidad inválida", "Ingresa una cantidad numérica mayor a cero.")
            return None

    def _construir_botones(self, etiqueta_accion, comando_accion):
        frame_botones = tk.Frame(self, bg=GRIS_FONDO, height=58)
        frame_botones.grid(row=2, column=0, sticky="ew")
        frame_botones.grid_propagate(False)

        contenedor = tk.Frame(frame_botones, bg=GRIS_FONDO)
        contenedor.pack(pady=10)

        tk.Button(contenedor, text=etiqueta_accion, font=("Segoe UI", 10, "bold"), bg="white",
                  relief="solid", bd=1, width=14, command=comando_accion).pack(side="left", padx=8)
        tk.Button(contenedor, text="❌ Cancelar", font=("Segoe UI", 10, "bold"), bg="white",
                  relief="solid", bd=1, width=14, command=self.destroy).pack(side="left", padx=8)


class VentanaAgregarInventario(_VentanaBaseMovimiento):
    """Diálogo 'Agregar Inventario' (Entrada)."""

    def __init__(self, parent, producto, usuario_actual, on_guardado):
        super().__init__(parent, producto, usuario_actual, on_guardado)
        self.title("Agregar Inventario")
        self.minsize(400, 460)
        self._construir_titulo("Agregar Inventario")
        self._construir_formulario()
        self._construir_botones("➕ Agregar", self._confirmar)
        ajustar_tamaño_ventana(self, ancho_min=400, alto_min=460)

    def _construir_formulario(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=1, column=0, sticky="nsew")
        campos = tk.Frame(contenedor, bg="white")
        campos.pack(pady=15, padx=15)

        self._fila_solo_lectura(campos, 0, "Producto:", self.producto["nombre"])
        self._fila_solo_lectura(campos, 1, "Descripción:", self.producto["nombre"])
        self._fila_solo_lectura(campos, 2, "Stock Actual:", f"{self.producto['stock']:,.3f}")

        self.var_agregar = self._control_cantidad(campos, 3, "Agregar:")
        self.var_motivo = self._combo_motivo(campos, 4, MOTIVOS_ENTRADA)
        self.var_comprobante = self._entry_texto(campos, 5, "N° Comprobante:")
        self.var_observaciones = self._entry_texto(campos, 6, "Observaciones:")

        self.var_precio_compra = self._entry_texto(campos, 7, "Precio de Compra:")
        self.var_precio_compra.set(f"{self.producto['precio_compra']:,.0f}")
        self.var_precio_venta = self._entry_texto(campos, 8, "Precio de Venta:")
        self.var_precio_venta.set(f"{self.producto['precio_venta']:,.0f}")
        self.var_precio_mayorista = self._entry_texto(campos, 9, "Precio Mayorista:")
        self.var_precio_mayorista.set(f"{self.producto['precio_mayorista']:,.0f}")

    def _parse_precio(self, texto):
        texto = texto.replace("Gs.", "").replace(",", "").strip()
        if not texto:
            return None
        try:
            return float(texto)
        except ValueError:
            return None

    def _confirmar(self):
        cantidad = self._validar_cantidad(self.var_agregar.get())
        if cantidad is None:
            return

        ok, msg = registrar_entrada(
            self.producto["id"], cantidad, self.var_motivo.get(), self.usuario_actual["id"],
            nro_comprobante=self.var_comprobante.get(), observaciones=self.var_observaciones.get(),
            precio_compra=self._parse_precio(self.var_precio_compra.get()),
            precio_venta=self._parse_precio(self.var_precio_venta.get()),
            precio_mayorista=self._parse_precio(self.var_precio_mayorista.get()),
        )
        if ok:
            self.on_guardado()
            self.destroy()
        else:
            messagebox.showerror("Error", msg)


class VentanaSalidaInventario(_VentanaBaseMovimiento):
    """Diálogo 'Salida Inventario'."""

    def __init__(self, parent, producto, usuario_actual, on_guardado):
        super().__init__(parent, producto, usuario_actual, on_guardado)
        self.title("Salida Inventario")
        self.minsize(400, 340)
        self._construir_titulo("Salida Inventario")
        self._construir_formulario()
        self._construir_botones("➖ Descontar", self._confirmar)
        ajustar_tamaño_ventana(self, ancho_min=400, alto_min=340)

    def _construir_formulario(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=1, column=0, sticky="nsew")
        campos = tk.Frame(contenedor, bg="white")
        campos.pack(pady=15, padx=15)

        self._fila_solo_lectura(campos, 0, "Producto:", self.producto["nombre"])
        self._fila_solo_lectura(campos, 1, "Descripción:", self.producto["nombre"])
        self._fila_solo_lectura(campos, 2, "Stock Actual:", f"{self.producto['stock']:,.3f}")

        self.var_descontar = self._control_cantidad(campos, 3, "Descontar:")
        self.var_motivo = self._combo_motivo(campos, 4, MOTIVOS_SALIDA)
        self.var_comprobante = self._entry_texto(campos, 5, "N° Comprobante:")
        self.var_observaciones = self._entry_texto(campos, 6, "Observaciones:")

    def _confirmar(self):
        cantidad = self._validar_cantidad(self.var_descontar.get())
        if cantidad is None:
            return

        ok, msg = registrar_salida(
            self.producto["id"], cantidad, self.var_motivo.get(), self.usuario_actual["id"],
            nro_comprobante=self.var_comprobante.get(), observaciones=self.var_observaciones.get(),
        )
        if ok:
            self.on_guardado()
            self.destroy()
        else:
            messagebox.showerror("Error", msg)


class VentanaEditarStockMinimo(tk.Toplevel):
    def __init__(self, parent, producto, on_guardado):
        super().__init__(parent)
        self.producto = producto
        self.on_guardado = on_guardado

        self.title("Editar Stock Mínimo")
        self.minsize(340, 260)
        self.resizable(True, True)
        self.configure(bg="white")
        self.grab_set()

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text="Editar Stock Mínimo", font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

        cuerpo = tk.Frame(self, bg="white")
        cuerpo.grid(row=1, column=0, sticky="nsew")

        contenido = tk.Frame(cuerpo, bg="white")
        contenido.pack(expand=True, pady=15)

        tk.Label(contenido, text=producto["nombre"], font=("Segoe UI", 12, "bold"),
                 bg="white").pack(pady=(0, 15))

        fila1 = tk.Frame(contenido, bg="white")
        fila1.pack(pady=5)
        tk.Label(fila1, text="Stock Mínimo Actual:", font=("Segoe UI", 9, "bold"), bg="white").pack(side="left")
        tk.Label(fila1, text=f"{producto['stock_minimo']:,.3f}", font=("Segoe UI", 9), bg="white").pack(
            side="left", padx=(8, 0))

        fila2 = tk.Frame(contenido, bg="white")
        fila2.pack(pady=5)
        tk.Label(fila2, text="Stock Mínimo:", font=("Segoe UI", 9, "bold"), bg="white").pack(side="left")
        self.var_nuevo = tk.StringVar(value=str(int(producto["stock_minimo"])))
        tk.Spinbox(fila2, textvariable=self.var_nuevo, from_=0, to=999999, font=("Segoe UI", 10),
                   width=12).pack(side="left", padx=(8, 0))

        frame_botones = tk.Frame(contenido, bg="white")
        frame_botones.pack(pady=(15, 0))
        btn_inv = tk.Button(frame_botones, text="✔ Guardar Cambios", font=("Segoe UI", 9, "bold"), bg="white",
                  fg=VERDE, relief="solid", bd=1, width=16, command=self._guardar)
        btn_inv.pack(side="left", padx=6)
        btn_inv.bind("<Return>", lambda e: self())
        tk.Button(frame_botones, text="❌ Cancelar", font=("Segoe UI", 9, "bold"), bg="white",
                  fg=ROJO, relief="solid", bd=1, width=12, command=self.destroy).pack(side="left", padx=6)

        ajustar_tamaño_ventana(self, ancho_min=340, alto_min=260)

    def _guardar(self):
        try:
            nuevo = float(self.var_nuevo.get())
            if nuevo < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Dato inválido", "El stock mínimo debe ser un número mayor o igual a cero.")
            return

        ok, msg = editar_stock_minimo(self.producto["id"], nuevo)
        if ok:
            self.on_guardado()
            self.destroy()
        else:
            messagebox.showerror("Error", msg)


class VentanaHistorialMovimientos(tk.Toplevel):
    """Historial de movimientos de inventario para un producto.
    Muestra entradas y salidas con filtro de cantidad, colores por tipo,
    totales y columna de observaciones — similar al historial de MetaVentas."""

    LIMITE_OPCIONES = [25, 50, 100, 250, 500, 1000, 10000, 100000, "Todos"]

    def __init__(self, parent, producto):
        super().__init__(parent)
        self.producto = producto
        self._todos_movimientos: list[dict] = []
        # Unidad de medida del producto (Unidad, Kilogramo, Litro, Metro,
        # Caja, Paquete, Docena), usada para formatear cada cantidad con
        # su abreviatura correspondiente (Kg, Lt, Mt, Unid., etc.), igual
        # que en el resto del sistema.
        self._unidad_medida = producto.get("unidad_medida", "Unidad")

        self.title("Historial Movimientos")
        self.geometry("900x520")
        self.minsize(700, 380)
        self.resizable(True, True)
        self.configure(bg="white")
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)

        self._construir_barra_titulo()
        self._construir_filtros()
        self._construir_tabla()
        self._construir_pie()
        self._cargar_movimientos()

    # ── Barra de título ────────────────────────────────────────
    def _construir_barra_titulo(self):
        barra = tk.Frame(self, bg=AZUL_RIBBON, height=36)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra,
                 text=f"🕑  Historial de Movimientos — {self.producto['nombre']}",
                 font=("Segoe UI", 10, "bold"), bg=AZUL_RIBBON, fg="white"
                 ).pack(side="left", padx=15, pady=7)

    # ── Barra de filtros ───────────────────────────────────────
    def _opciones_limite_formateadas(self) -> list[str]:
        """Las opciones numéricas se muestran con punto separador de miles
        (ej. '10.000', '100.000') para que se lean de un vistazo; 'Todos'
        queda tal cual."""
        return [
            f"{x:,}".replace(",", ".") if isinstance(x, int) else x
            for x in self.LIMITE_OPCIONES
        ]

    def _construir_filtros(self):
        barra = tk.Frame(self, bg="#f8f9fa", height=38)
        barra.grid(row=1, column=0, sticky="ew")
        barra.grid_propagate(False)

        interior = tk.Frame(barra, bg="#f8f9fa")
        interior.pack(side="left", padx=12, pady=6)

        tk.Label(interior, text="Mostrar los últimos movimientos:",
                 font=("Segoe UI", 9), bg="#f8f9fa").pack(side="left")

        self.var_limite = tk.StringVar(value="1.000")
        combo = ttk.Combobox(interior, textvariable=self.var_limite,
                             values=self._opciones_limite_formateadas(),
                             state="readonly", width=8, font=("Segoe UI", 9))
        combo.pack(side="left", padx=(6, 20))
        combo.bind("<<ComboboxSelected>>", lambda e: self._aplicar_filtro())

        # Filtro por tipo
        tk.Label(interior, text="Tipo:", font=("Segoe UI", 9),
                 bg="#f8f9fa").pack(side="left")
        self.var_tipo = tk.StringVar(value="Todos")
        ttk.Combobox(interior, textvariable=self.var_tipo,
                     values=["Todos", "Entrada", "Salida"],
                     state="readonly", width=9,
                     font=("Segoe UI", 9)).pack(side="left", padx=(4, 0))
        self.var_tipo.trace_add("write", lambda *_: self._aplicar_filtro())

    # ── Tabla principal ────────────────────────────────────────
    def _construir_tabla(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=2, column=0, sticky="nsew", padx=8, pady=(4, 0))
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        cols   = ("fecha",  "comprobante", "cantidad", "motivo", "obs", "stock_res", "usuario")
        encabs = ("Fecha y Hora", "N° Comp.", "Cantidad", "Motivo", "Obs", "Stock Result.", "Usuario")
        # "cantidad" se ensanchó (antes 80px) porque ahora puede mostrar
        # texto más largo como "− Ilimitado (2,75 Mt)" en vez de solo un
        # número corto.
        anchos = (135, 80, 150, 200, 160, 95, 120)

        style = ttk.Style()
        style.configure("Historial.Treeview", font=("Segoe UI", 9), rowheight=22)
        style.configure("Historial.Treeview.Heading",
                        font=("Segoe UI", 9, "bold"))

        self.tabla = ttk.Treeview(contenedor, columns=cols, show="headings",
                                   style="Historial.Treeview", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, ancho in zip(cols, encabs, anchos):
            self.tabla.heading(col, text=enc,
                               command=lambda c=col: self._ordenar(c))
            self.tabla.column(col, width=ancho,
                              anchor="w" if col in ("motivo", "obs") else "center",
                              minwidth=50)

        # Tags de color por tipo de movimiento
        self.tabla.tag_configure("entrada",
                                  background="#f0fdf4", foreground="#166534")
        self.tabla.tag_configure("salida",
                                  background="#fef2f2", foreground="#991b1b")
        self.tabla.tag_configure("entrada_sel",
                                  background="#bbf7d0", foreground="#14532d")
        self.tabla.tag_configure("salida_sel",
                                  background="#fecaca", foreground="#7f1d1d")

        sb_y = ttk.Scrollbar(contenedor, orient="vertical",
                             command=self.tabla.yview)
        sb_x = ttk.Scrollbar(contenedor, orient="horizontal",
                             command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=sb_y.set,
                             xscrollcommand=sb_x.set)

        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x.grid(row=1, column=0, sticky="ew")

        self._orden_col = None
        self._orden_asc = False  # más reciente primero por defecto

    # ── Pie: totales + botones ─────────────────────────────────
    def _construir_pie(self):
        pie = tk.Frame(self, bg="#f8f9fa", height=46)
        pie.grid(row=3, column=0, sticky="ew")
        pie.grid_propagate(False)

        # Totales
        self.lbl_registros = tk.Label(pie, text="",
                                       font=("Segoe UI", 9), bg="#f8f9fa",
                                       fg="#374151")
        self.lbl_registros.pack(side="left", padx=14, pady=12)

        sep = tk.Frame(pie, bg="#d1d5db", width=1)
        sep.pack(side="left", fill="y", pady=8)

        self.lbl_total_entradas = tk.Label(pie, text="",
                                            font=("Segoe UI", 9, "bold"),
                                            bg="#f8f9fa", fg="#166534")
        self.lbl_total_entradas.pack(side="left", padx=14)

        sep2 = tk.Frame(pie, bg="#d1d5db", width=1)
        sep2.pack(side="left", fill="y", pady=8)

        self.lbl_total_salidas = tk.Label(pie, text="",
                                           font=("Segoe UI", 9, "bold"),
                                           bg="#f8f9fa", fg="#991b1b")
        self.lbl_total_salidas.pack(side="left", padx=14)

        # Total vendido de un producto "Ilimitado" (suma histórica, de
        # TODAS las ventas/salidas registradas para ese producto, sin
        # importar el filtro de tipo ni el límite de "últimos
        # movimientos" elegido arriba). Solo se muestra si el producto
        # tiene al menos una salida marcada como Ilimitado; para
        # productos con stock normal (Cantidad) queda oculto.
        self._sep3 = tk.Frame(pie, bg="#d1d5db", width=1)
        self.lbl_total_vendido_ilimitado = tk.Label(
            pie, text="", font=("Segoe UI", 9, "bold"),
            bg="#f8f9fa", fg=AZUL_RIBBON)

        # Botones
        tk.Button(pie, text="Cerrar",
                  font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, padx=14, pady=4,
                  cursor="hand2", command=self.destroy
                  ).pack(side="right", padx=12, pady=8)

    # ── Carga y filtrado ───────────────────────────────────────
    def _cargar_movimientos(self):
        self._todos_movimientos = historial_movimientos(self.producto["id"])

        # Total histórico vendido/salido de este producto como
        # "Ilimitado" (independiente del filtro de tipo y del límite de
        # registros a mostrar — es un acumulado GLOBAL de toda su
        # trazabilidad, no solo de lo que se ve en la grilla).
        total_ilimitado = sum(
            m["cantidad"] for m in self._todos_movimientos
            if m["tipo"] == "salida" and m.get("es_ilimitado")
        )
        if total_ilimitado > 0:
            texto = f'🧮 Total vendido: {formatear_cantidad(total_ilimitado, self._unidad_medida)}'
            self.lbl_total_vendido_ilimitado.configure(text=texto)
            if not self._sep3.winfo_ismapped():
                self._sep3.pack(side="left", fill="y", pady=8)
                self.lbl_total_vendido_ilimitado.pack(side="left", padx=14)
        else:
            if self._sep3.winfo_ismapped():
                self._sep3.pack_forget()
                self.lbl_total_vendido_ilimitado.pack_forget()

        self._aplicar_filtro()

    def _aplicar_filtro(self):
        movs = self._todos_movimientos

        # Filtro tipo
        tipo_sel = self.var_tipo.get()
        if tipo_sel == "Entrada":
            movs = [m for m in movs if m["tipo"] == "entrada"]
        elif tipo_sel == "Salida":
            movs = [m for m in movs if m["tipo"] == "salida"]

        # Límite de registros
        lim_str = self.var_limite.get()
        if lim_str != "Todos":
            try:
                movs = movs[:int(lim_str.replace(".", ""))]
            except ValueError:
                pass

        self._poblar_tabla(movs)

    def _poblar_tabla(self, movs: list[dict]):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        total_ent = total_sal = 0.0

        for m in movs:
            es_entrada = m["tipo"] == "entrada"
            es_ilimitado = m.get("es_ilimitado", False)

            # Los movimientos de productos con stock "Ilimitado" no suman
            # a los totales de Entradas/Salidas (esos totales representan
            # unidades reales de inventario, y acá no hay ninguna real que
            # contar) ni muestran una cantidad o stock resultante numérico:
            # se identifican con la etiqueta "Ilimitado" en ambas columnas.
            if not es_ilimitado:
                total_ent += m["cantidad"] if es_entrada else 0
                total_sal += m["cantidad"] if not es_entrada else 0

            signo  = "+"  if es_entrada else "−"
            tag    = "entrada" if es_entrada else "salida"

            if es_ilimitado:
                if es_entrada:
                    # "Stock Inicial" de un producto Ilimitado: no hay una
                    # cantidad real que mostrar (ese producto no tiene un
                    # stock inicial numérico), así que se deja solo la
                    # etiqueta "Ilimitado".
                    cant = f"{signo} Ilimitado"
                else:
                    # Venta/salida real de un producto Ilimitado: sí hay
                    # una cantidad real vendida/descontada, se muestra
                    # entre paréntesis junto a "Ilimitado", con su unidad
                    # de medida (Kg, Lt, Mt, Unid., etc.) igual que en el
                    # resto del sistema.
                    cantidad_fmt = formatear_cantidad(m["cantidad"], self._unidad_medida)
                    cant = f"{signo} Ilimitado ({cantidad_fmt})"
                stock_res = "Ilimitado"
            else:
                cant = f'{signo} {m["cantidad"]:,.2f}'.rstrip("0").rstrip(".")
                stock_res = (f'{m["stock_resultante"]:,.2f}'.rstrip("0").rstrip(".")
                             if m["stock_resultante"] is not None else "—")

            self.tabla.insert("", "end", values=(
                m["fecha"], m["nro_comprobante"] or "—",
                cant, m["motivo"], m["observaciones"],
                stock_res, m["usuario"],
            ), tags=(tag,))

        # Actualizar pie
        n = len(movs)
        self.lbl_registros.config(
            text=f"{n} movimiento{'s' if n != 1 else ''}")
        self.lbl_total_entradas.config(
            text=f"⬆ Entradas: {total_ent:,.2f}".rstrip("0").rstrip("."))
        self.lbl_total_salidas.config(
            text=f"⬇ Salidas: {total_sal:,.2f}".rstrip("0").rstrip("."))

        # Mensaje vacío
        if not movs:
            for w in self.tabla.winfo_children():
                w.destroy()
            tk.Label(self, text="No hay movimientos registrados para este producto.",
                     font=("Segoe UI", 10), bg="white", fg="#9ca3af"
                     ).place(relx=0.5, rely=0.5, anchor="center")

    # ── Ordenamiento por columna ───────────────────────────────
    def _ordenar(self, col):
        if self._orden_col == col:
            self._orden_asc = not self._orden_asc
        else:
            self._orden_col = col
            self._orden_asc = True

        col_map = {
            "fecha": "fecha", "comprobante": "nro_comprobante",
            "cantidad": "cantidad", "motivo": "motivo",
            "obs": "observaciones", "stock_res": "stock_resultante",
            "usuario": "usuario",
        }
        clave = col_map.get(col, "fecha")
        reverse = not self._orden_asc

        movs = self._todos_movimientos[:]
        try:
            movs.sort(
                key=lambda m: (m.get(clave) or 0)
                              if clave in ("cantidad", "stock_resultante")
                              else str(m.get(clave) or "").lower(),
                reverse=reverse,
            )
        except Exception:
            pass

        # Re-aplicar límite y tipo sobre la lista reordenada
        tipo_sel = self.var_tipo.get()
        if tipo_sel == "Entrada":
            movs = [m for m in movs if m["tipo"] == "entrada"]
        elif tipo_sel == "Salida":
            movs = [m for m in movs if m["tipo"] == "salida"]

        lim_str = self.var_limite.get()
        if lim_str != "Todos":
            try:
                movs = movs[:int(lim_str.replace(".", ""))]
            except ValueError:
                pass

        self._poblar_tabla(movs)
