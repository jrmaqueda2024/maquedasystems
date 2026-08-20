"""
ventana_armar_venta_locales.py
Herramienta "Armar Venta por Locales": permite cargar productos en
grillas independientes, una por cada local/comercio al que se le
distribuye, y al finalizar generar un PDF consolidado y/o cargar todo
lo pedido en la venta actual (sumando cantidades de productos repetidos
entre locales).
"""
import tkinter as tk
from tkinter import ttk, messagebox

from models_catalogo import buscar_producto_por_codigo
from ventanas_auxiliares_venta import VentanaBuscarProducto, VentanaAsignarCliente
from utilidades_ui import (
    habilitar_deseleccion_treeview,
    ajustar_tamaño_ventana, formatear_gs, formatear_cantidad,
    unidad_es_fraccionable, parsear_cantidad, forzar_mayusculas,
)

AZUL_RIBBON = "#1d5fd6"
VERDE_IMPORTE = "#dcfce7"
GRIS_FONDO = "#f4f5f7"
GRIS_BORDE = "#e2e8f0"

COLOR_FONDO_BARRA = "#dbe4f0"
COLOR_TAB_ACTIVA = "white"
COLOR_TAB_INACTIVA = "#c7d3e6"


class VentanaArmarVentaPorLocales(tk.Toplevel):
    """Ventana principal: barra para agregar locales, pestañas (una por
    local) con su propia grilla de productos, y acciones finales de
    Generar PDF / Cargar en Venta."""

    def __init__(self, parent, panel_ventas, usuario_actual, sesion_previa: dict = None):
        super().__init__(parent)
        self.panel_ventas = panel_ventas   # instancia de PanelVentas donde se cargará el pedido final
        self.usuario_actual = usuario_actual
        self.cliente_para_nuevo_local = None

        self.locales = {}   # local_id -> {"nombre":, "panel":, "tab_frame":, "label":, "btn_cerrar":}
        self.contador_locales = 0
        self.local_actual_id = None
        # Recuerda qué se cargó la última vez en la venta (producto_id ->
        # cantidad), para poder "deshacerlo" antes de recalcular si el
        # usuario corrige algo y vuelve a presionar "Cargar en Venta".
        self._snapshot_cargado_en_venta = dict((sesion_previa or {}).get("snapshot_cargado_en_venta", {}))
        self._lista_para_autosync = False

        self.title("Armar Venta por Locales")
        self.configure(bg="white")
        self.resizable(True, True)
        self.grab_set()
        # Sin transient(): así el gestor de ventanas no le quita los
        # botones de minimizar/maximizar a esta ventana.
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)

        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_titulo()
        self._construir_barra_agregar_local()
        self._construir_barra_pestanas()
        self._construir_area_contenido()
        self._construir_pie()

        self.minsize(820, 560)
        ajustar_tamaño_ventana(self, ancho_min=820, alto_min=600,
                              alto_max=self.winfo_screenheight() - 60)

        # Si esta pestaña de venta ya tenía una sesión armada anteriormente
        # (locales con sus productos), la restauramos tal cual quedó, en
        # vez de empezar de cero.
        locales_previos = (sesion_previa or {}).get("locales", [])
        for datos_local in locales_previos:
            self._crear_tab_local(datos_local["nombre"], datos_local.get("cliente_id"),
                                  datos_local.get("items", []))
        if locales_previos:
            self._activar_local("local_1")
            self._actualizar_total_general()

        # A partir de este punto, cualquier cambio en un local (agregar,
        # quitar, cambiar cantidad, mayoreo) se refleja al instante en la
        # grilla de la venta, y viceversa. Se activa recién ahora para no
        # disparar sincronizaciones de más mientras se restauraba la sesión.
        self._lista_para_autosync = True
        self.panel_ventas.ventana_locales_activa = self

    # ---------------- TÍTULO ----------------
    def _construir_titulo(self):
        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text="🏬 Armar Venta por Locales", font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

    # ---------------- BARRA PARA AGREGAR UN NUEVO LOCAL ----------------
    def _construir_barra_agregar_local(self):
        barra = tk.Frame(self, bg=GRIS_FONDO)
        barra.grid(row=1, column=0, sticky="ew")
        interior = tk.Frame(barra, bg=GRIS_FONDO)
        interior.pack(fill="x", padx=10, pady=8)

        tk.Label(interior, text="Nombre del Local:", font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).pack(
            side="left", padx=(0, 6))
        self.var_nombre_local = tk.StringVar()
        entry_nombre = tk.Entry(interior, textvariable=self.var_nombre_local, font=("Segoe UI", 10), width=28)
        entry_nombre.pack(side="left", padx=(0, 8))
        forzar_mayusculas(entry_nombre, self.var_nombre_local)
        entry_nombre.bind("<Return>", lambda e: self._agregar_local())

        tk.Button(interior, text="🔍 Buscar Cliente", font=("Segoe UI", 9, "bold"), bg="white",
                  relief="solid", bd=1, cursor="hand2",
                  command=self._abrir_buscar_cliente).pack(side="left", padx=(0, 8))
        tk.Button(interior, text="➕ Agregar Local", font=("Segoe UI", 9, "bold"), bg=AZUL_RIBBON,
                  fg="white", relief="flat", padx=12, cursor="hand2",
                  command=self._agregar_local).pack(side="left")

        self._entry_nombre_local = entry_nombre
        entry_nombre.focus()

    def _abrir_buscar_cliente(self):
        def al_elegir(cliente):
            if cliente:
                self.cliente_para_nuevo_local = cliente
                self.var_nombre_local.set(cliente["nombre"])
        VentanaAsignarCliente(self, on_seleccionado=al_elegir)

    # ---------------- BARRA DE PESTAÑAS (una por local) ----------------
    def _construir_barra_pestanas(self):
        self.barra_pestanas = tk.Frame(self, bg=COLOR_FONDO_BARRA, height=36)
        self.barra_pestanas.grid(row=2, column=0, sticky="ew")
        self.barra_pestanas.grid_propagate(False)

        self.frame_tabs_locales = tk.Frame(self.barra_pestanas, bg=COLOR_FONDO_BARRA)
        self.frame_tabs_locales.pack(side="left", fill="y")

        self.label_sin_locales = tk.Label(
            self.barra_pestanas, text="  Agregá un local arriba para empezar a cargar productos.",
            font=("Segoe UI", 9, "italic"), bg=COLOR_FONDO_BARRA, fg="#64748b")
        self.label_sin_locales.pack(side="left", pady=8)

    def _construir_area_contenido(self):
        self.area_contenido = tk.Frame(self, bg="white")
        self.area_contenido.grid(row=3, column=0, sticky="nsew")

    # ---------------- PIE: TOTAL GENERAL + ACCIONES FINALES ----------------
    def _construir_pie(self):
        pie = tk.Frame(self, bg=GRIS_FONDO)
        pie.grid(row=4, column=0, sticky="ew")
        interior = tk.Frame(pie, bg=GRIS_FONDO)
        interior.pack(fill="x", padx=10, pady=10)

        tk.Button(interior, text="📄 Generar PDF", font=("Segoe UI", 10, "bold"), bg="white",
                  relief="solid", bd=1, padx=12, pady=6, cursor="hand2",
                  command=self._generar_pdf).pack(side="left")
        tk.Button(interior, text="📥 Cargar en Venta", font=("Segoe UI", 10, "bold"), bg=AZUL_RIBBON,
                  fg="white", relief="flat", padx=12, pady=6, cursor="hand2",
                  command=self._cargar_en_venta).pack(side="left", padx=(8, 0))
        tk.Button(interior, text="✕ Cerrar", font=("Segoe UI", 10, "bold"), bg="white",
                  relief="solid", bd=1, padx=12, pady=6, cursor="hand2",
                  command=self._al_cerrar).pack(side="left", padx=(8, 0))

        self.label_total_general = tk.Label(interior, text="Total General: Gs. 0",
                                            font=("Segoe UI", 14, "bold"), bg=GRIS_FONDO, fg="#1d4ed8")
        self.label_total_general.pack(side="right")

    # ============================================================
    # GESTIÓN DE LOCALES (pestañas)
    # ============================================================
    def _agregar_local(self):
        nombre = self.var_nombre_local.get().strip()
        if not nombre:
            messagebox.showwarning("Falta el nombre", "Ingresa el nombre del local antes de agregarlo.",
                                   parent=self)
            return
        if any(info["nombre"] == nombre for info in self.locales.values()):
            messagebox.showwarning("Local repetido", f"Ya agregaste un local llamado '{nombre}'.",
                                   parent=self)
            return

        cliente_id = (self.cliente_para_nuevo_local or {}).get("id")
        local_id = self._crear_tab_local(nombre, cliente_id)

        self.var_nombre_local.set("")
        self.cliente_para_nuevo_local = None
        self._activar_local(local_id)

    def _crear_tab_local(self, nombre: str, cliente_id, items: list = None) -> str:
        """Crea la pestaña y la grilla de un local, opcionalmente
        precargada con productos (usado al restaurar una sesión anterior).
        Devuelve el local_id creado."""
        self.contador_locales += 1
        local_id = f"local_{self.contador_locales}"

        panel = _PanelLocal(self.area_contenido, self)
        if items:
            panel.items = list(items)
            panel._actualizar_vista()

        tab_frame = tk.Frame(self.frame_tabs_locales, bg=COLOR_TAB_INACTIVA)
        tab_frame.pack(side="left", fill="y", padx=2, pady=4)
        label = tk.Label(tab_frame, text=f"🏬 {nombre}", font=("Segoe UI", 9, "bold"),
                         bg=COLOR_TAB_INACTIVA, fg="#334155", padx=10, pady=6, cursor="hand2")
        label.pack(side="left")
        label.bind("<Button-1>", lambda e, lid=local_id: self._activar_local(lid))
        label.bind("<Double-Button-1>", lambda e, lid=local_id: self._iniciar_renombrar_local(lid))
        btn_editar = tk.Label(tab_frame, text="✏", font=("Segoe UI", 8), bg=COLOR_TAB_INACTIVA,
                              fg="#64748b", cursor="hand2")
        btn_editar.pack(side="left", padx=(0, 4))
        btn_editar.bind("<Button-1>", lambda e, lid=local_id: self._iniciar_renombrar_local(lid))
        btn_cerrar = tk.Label(tab_frame, text="✕", font=("Segoe UI", 8), bg=COLOR_TAB_INACTIVA,
                              fg="#64748b", cursor="hand2")
        btn_cerrar.pack(side="left", padx=(0, 8))
        btn_cerrar.bind("<Button-1>", lambda e, lid=local_id: self._cerrar_local(lid))

        self.locales[local_id] = {
            "nombre": nombre, "cliente_id": cliente_id,
            "panel": panel, "tab_frame": tab_frame, "label": label,
            "btn_editar": btn_editar, "btn_cerrar": btn_cerrar, "entry_renombrar": None,
        }
        self.label_sin_locales.pack_forget()
        return local_id

    def _iniciar_renombrar_local(self, local_id: str):
        """Reemplaza momentáneamente el nombre del local (en su pestaña)
        por un campo editable, para poder corregirlo sin tener que
        cerrarlo y volver a crearlo desde cero."""
        info = self.locales.get(local_id)
        if info is None or info["entry_renombrar"] is not None:
            return  # ya se está renombrando este local

        label = info["label"]
        var_nuevo_nombre = tk.StringVar(value=info["nombre"])
        entry = tk.Entry(info["tab_frame"], textvariable=var_nuevo_nombre, font=("Segoe UI", 9, "bold"),
                         width=16)
        label.pack_forget()
        entry.pack(side="left", padx=(8, 4), before=info["btn_editar"])
        entry.focus()
        entry.select_range(0, "end")
        info["entry_renombrar"] = entry

        def confirmar(_e=None):
            if info["entry_renombrar"] is None:
                return  # ya se confirmó/canceló (evita doble disparo Enter + FocusOut)
            nuevo_nombre = var_nuevo_nombre.get().strip()
            if not nuevo_nombre:
                messagebox.showwarning("Nombre vacío", "El nombre del local no puede quedar vacío.", parent=self)
                nuevo_nombre = info["nombre"]
            elif any(lid != local_id and otro["nombre"] == nuevo_nombre for lid, otro in self.locales.items()):
                messagebox.showwarning("Nombre repetido", f"Ya hay otro local llamado '{nuevo_nombre}'.",
                                       parent=self)
                nuevo_nombre = info["nombre"]
            info["nombre"] = nuevo_nombre
            label.config(text=f"🏬 {nuevo_nombre}")
            entry.destroy()
            info["entry_renombrar"] = None
            label.pack(side="left", before=info["btn_editar"])

        def cancelar(_e=None):
            if info["entry_renombrar"] is None:
                return
            entry.destroy()
            info["entry_renombrar"] = None
            label.pack(side="left", before=info["btn_editar"])

        entry.bind("<Return>", confirmar)
        entry.bind("<FocusOut>", confirmar)
        entry.bind("<Escape>", cancelar)

    def _activar_local(self, local_id: str):
        if local_id not in self.locales:
            return
        for lid, info in self.locales.items():
            info["panel"].pack_forget()
            color = COLOR_TAB_ACTIVA if lid == local_id else COLOR_TAB_INACTIVA
            info["tab_frame"].config(bg=color)
            info["label"].config(bg=color, font=("Segoe UI", 9, "bold" if lid == local_id else "normal"))
            info["btn_editar"].config(bg=color)
            info["btn_cerrar"].config(bg=color)
        self.locales[local_id]["panel"].pack(in_=self.area_contenido, fill="both", expand=True)
        self.local_actual_id = local_id

    def _cerrar_local(self, local_id: str):
        info = self.locales.get(local_id)
        if info is None:
            return
        if info["panel"].items:
            aviso_venta = (
                " y se quitarán de la venta actual" if self._lista_para_autosync else ""
            )
            if not messagebox.askyesno(
                "Cerrar local",
                f"El local '{info['nombre']}' tiene productos cargados que se perderán{aviso_venta}.\n\n"
                "¿Seguro que querés cerrarlo?", parent=self,
            ):
                return

        era_el_activo = (self.local_actual_id == local_id)
        info["tab_frame"].destroy()
        info["panel"].destroy()
        del self.locales[local_id]

        if not self.locales:
            self.label_sin_locales.pack(side="left", pady=8)
            self.local_actual_id = None
        elif era_el_activo:
            self._activar_local(list(self.locales.keys())[-1])

        self._actualizar_total_general()
        self._sincronizar_automaticamente()

    # ============================================================
    # TOTAL GENERAL (suma de subtotales de todos los locales)
    # ============================================================
    def _actualizar_total_general(self):
        total = sum(info["panel"].calcular_subtotal() for info in self.locales.values())
        self.label_total_general.config(text=f"Total General: {formatear_gs(total)}")

    # ============================================================
    # GENERAR PDF
    # ============================================================
    def _generar_pdf(self):
        if not self.locales or all(not info["panel"].items for info in self.locales.values()):
            messagebox.showinfo("Nada para generar",
                               "Agregá al menos un local con productos antes de generar el PDF.",
                               parent=self)
            return

        from tkinter import filedialog
        try:
            from reporte_venta_locales_pdf import generar_pdf_venta_por_locales
        except ImportError:
            messagebox.showerror("Falta una librería",
                                 "Para generar el PDF se necesita instalar 'reportlab'.\n\n"
                                 "Abre una terminal y ejecutá:\n\npip install reportlab",
                                 parent=self)
            return

        import datetime
        # Sugerimos un nombre con hora incluida (no siempre "pedido_por_
        # locales.pdf") para que generar el PDF de nuevo no choque con el
        # archivo anterior si todavía lo tenés abierto en un lector de PDF.
        nombre_sugerido = f"pedido_por_locales_{datetime.datetime.now().strftime('%H%M%S')}.pdf"
        ruta = filedialog.asksaveasfilename(
            title="Guardar Pedido por Locales", initialfile=nombre_sugerido,
            defaultextension=".pdf", filetypes=[("Archivo PDF", "*.pdf")], parent=self,
        )
        if not ruta:
            return

        datos_locales = [
            {"nombre": info["nombre"], "items": info["panel"].items}
            for info in self.locales.values()
        ]
        try:
            generar_pdf_venta_por_locales(ruta, datos_locales,
                                          generado_por=self.usuario_actual.get("nombre_completo", ""))
        except PermissionError:
            messagebox.showerror(
                "No se pudo guardar el archivo",
                f"Windows no dejó guardar en:\n{ruta}\n\n"
                "Esto casi siempre pasa porque el archivo ya está abierto en un lector de PDF "
                "(o en otro programa). Cerralo e intentá de nuevo, o elegí otro nombre de archivo.",
                parent=self)
            return
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n{e}", parent=self)
            return

        if messagebox.askyesno("PDF generado", f"El pedido se guardó en:\n{ruta}\n\n"
                                               "¿Querés abrirlo ahora?", parent=self):
            import os, sys, subprocess
            try:
                if sys.platform == "win32":
                    os.startfile(ruta)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", ruta], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    subprocess.Popen(["xdg-open", ruta], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

    # ============================================================
    # CARGAR EN VENTA (fusiona todos los locales en la venta actual)
    # ============================================================
    def _cargar_en_venta(self):
        todos_los_items = []
        for info in self.locales.values():
            todos_los_items.extend(info["panel"].items)

        if not todos_los_items:
            messagebox.showinfo("Nada para cargar",
                               "Agregá al menos un local con productos antes de cargarlo en la venta.",
                               parent=self)
            return

        cantidad_productos = len(todos_los_items)
        cantidad_locales = len(self.locales)
        ya_habia_cargado_antes = bool(self._snapshot_cargado_en_venta)
        texto_repeticion = (
            "\n\nComo ya habías cargado esto antes, primero se actualiza lo anterior "
            "(no se va a duplicar)." if ya_habia_cargado_antes else ""
        )
        if not messagebox.askyesno(
            "Cargar en la venta actual",
            f"Se van a cargar {cantidad_productos} línea(s) de producto de {cantidad_locales} local(es) "
            "en la venta actual. Si un producto se repite entre locales, se sumarán las cantidades."
            f"{texto_repeticion}\n\n¿Continuar?", parent=self,
        ):
            return

        self._ejecutar_sincronizacion(todos_los_items)

        mensaje = (f"Se actualizaron {cantidad_productos} línea(s) de producto en la venta actual."
                  if ya_habia_cargado_antes else
                  f"Se cargaron {cantidad_productos} línea(s) de producto en la venta actual.")
        messagebox.showinfo(
            "Cargado", f"{mensaje}\n\n"
            "De ahora en más, cualquier cambio que hagas acá (o en la grilla de la venta) "
            "se va a reflejar automáticamente en ambos lados mientras esta ventana esté abierta.",
            parent=self,
        )

    def _ejecutar_sincronizacion(self, todos_los_items):
        """Aplica el estado actual de todos los locales a la venta: primero
        QUITA POR COMPLETO (sin importar la cantidad que tuvieran) todas las
        líneas de productos que esta ventana venía manejando, y después las
        vuelve a cargar desde cero con los totales actuales (sumando
        cantidades repetidas entre locales). Al no basarse en restar una
        cantidad anterior, cada sincronización queda exacta aunque alguna
        sincronización previa hubiera quedado desactualizada por cualquier
        motivo. Sin diálogos: la usan tanto el botón 'Cargar en Venta' como
        la sincronización automática en tiempo real."""
        self.panel_ventas._sync_en_progreso = True
        try:
            # Solo "limpiamos por completo" los productos que esta ventana
            # YA venía gestionando (evita arrastrar cualquier diferencia
            # acumulada de sincronizaciones anteriores). Un producto que
            # recién ahora empieza a venir de un local, y que el usuario ya
            # tenía cargado a mano en la venta por otro motivo, se sigue
            # sumando en vez de pisarse.
            for producto_id in list(self._snapshot_cargado_en_venta.keys()):
                self.panel_ventas._quitar_producto_completamente(producto_id)

            nuevo_snapshot = {}
            for item in todos_los_items:
                self.panel_ventas._agregar_item_con_precio(
                    item["producto"], item["cantidad"], item["precio_unitario"], item.get("es_mayoreo", False),
                )
                producto_id = item["producto"]["id"]
                nuevo_snapshot[producto_id] = nuevo_snapshot.get(producto_id, 0) + item["cantidad"]
            self._snapshot_cargado_en_venta = nuevo_snapshot
        finally:
            self.panel_ventas._sync_en_progreso = False

    def _sincronizar_automaticamente(self):
        """Se llama cada vez que cambia algo en cualquier local (agregar,
        quitar, cambiar cantidad, Mayoreo) mientras esta ventana está
        abierta: refleja el cambio en la grilla de la venta al instante,
        sin pedir confirmación ni mostrar mensajes."""
        if not self._lista_para_autosync or self.panel_ventas._sync_en_progreso:
            return
        todos_los_items = []
        for info in self.locales.values():
            todos_los_items.extend(info["panel"].items)
        self._ejecutar_sincronizacion(todos_los_items)

    def actualizar_cantidad_desde_venta(self, producto_id, nueva_cantidad_total):
        """Cuando el usuario cambia a mano, en la grilla de la venta, la
        cantidad de un producto que había sido cargado desde acá, repartimos
        ese cambio entre el/los local(es) que lo habían aportado (proporcional
        si estaba repartido entre varios), para que ambas pantallas queden
        sincronizadas en tiempo real."""
        cantidad_anterior_total = self._snapshot_cargado_en_venta.get(producto_id)
        if cantidad_anterior_total is None:
            return  # este producto no vino de acá; no lo tocamos

        contribuciones = []  # [(panel_local, item), ...]
        for info in self.locales.values():
            for item in info["panel"].items:
                if item["producto"]["id"] == producto_id:
                    contribuciones.append((info["panel"], item))
        if not contribuciones:
            return

        self.panel_ventas._sync_en_progreso = True
        try:
            if nueva_cantidad_total <= 0:
                for panel_local, _item in contribuciones:
                    panel_local.items = [i for i in panel_local.items if i["producto"]["id"] != producto_id]
                    panel_local._actualizar_vista()
                del self._snapshot_cargado_en_venta[producto_id]
            elif len(contribuciones) == 1:
                panel_local, item = contribuciones[0]
                item["cantidad"] = nueva_cantidad_total
                panel_local._actualizar_vista()
                self._snapshot_cargado_en_venta[producto_id] = nueva_cantidad_total
            else:
                # Estaba repartido entre varios locales: mantenemos la misma
                # proporción que tenían entre sí, aplicada al nuevo total.
                total_anterior = sum(item["cantidad"] for _, item in contribuciones) or 1
                acumulado = 0
                for i, (panel_local, item) in enumerate(contribuciones):
                    if i == len(contribuciones) - 1:
                        nueva_cant_local = max(nueva_cantidad_total - acumulado, 0)
                    else:
                        proporcion = item["cantidad"] / total_anterior
                        nueva_cant_local = round(nueva_cantidad_total * proporcion, 3)
                        acumulado += nueva_cant_local
                    if nueva_cant_local <= 0:
                        panel_local.items = [i for i in panel_local.items if i["producto"]["id"] != producto_id]
                    else:
                        item["cantidad"] = nueva_cant_local
                    panel_local._actualizar_vista()
                self._snapshot_cargado_en_venta[producto_id] = nueva_cantidad_total
            self._actualizar_total_general()
        finally:
            self.panel_ventas._sync_en_progreso = False

    def limpiar_todos_los_locales(self):
        """Se llama cuando el usuario presiona 'Limpiar Todo' en la venta:
        vacía también todos los locales de esta ventana, ya que la venta a
        la que estaban sincronizados quedó vacía."""
        for info in list(self.locales.values()):
            info["tab_frame"].destroy()
            info["panel"].destroy()
        self.locales.clear()
        self.local_actual_id = None
        self._snapshot_cargado_en_venta = {}
        self.label_sin_locales.pack(side="left", pady=8)
        self._actualizar_total_general()

    # ============================================================
    # RECORDAR LA SESIÓN (para poder reabrir y seguir editando)
    # ============================================================
    def _obtener_snapshot_sesion(self) -> dict:
        return {
            "locales": [
                {"nombre": info["nombre"], "cliente_id": info["cliente_id"], "items": list(info["panel"].items)}
                for info in self.locales.values()
            ],
            "snapshot_cargado_en_venta": dict(self._snapshot_cargado_en_venta),
        }

    def _al_cerrar(self):
        """Al cerrar esta ventana (con el botón "✕ Cerrar" o la X de la
        ventana), guardamos todo lo armado en esta pestaña de venta para
        poder reabrir "Armar Venta por Locales" más tarde y seguir
        editando exactamente donde se quedó, en vez de empezar de cero."""
        if self.locales:
            self.panel_ventas.sesion_armar_locales = self._obtener_snapshot_sesion()
        else:
            self.panel_ventas.sesion_armar_locales = None
        if self.panel_ventas.ventana_locales_activa is self:
            self.panel_ventas.ventana_locales_activa = None
        self.destroy()


# ============================================================
# PANEL DE UN LOCAL: grilla de productos independiente
# ============================================================
class _PanelLocal(tk.Frame):
    def __init__(self, parent, ventana_padre: VentanaArmarVentaPorLocales):
        super().__init__(parent, bg="white")
        self.ventana_padre = ventana_padre
        self.items = []   # {"producto": {...}, "cantidad": float, "precio_unitario": float}

        self._construir_barra_codigo()
        self._construir_grilla()
        self._construir_barra_cantidad()
        self._construir_pie_subtotal()

    # ---------------- BARRA DE CÓDIGO ----------------
    def _construir_barra_codigo(self):
        barra = tk.Frame(self, bg="white")
        barra.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(barra, text="Código de Barra:", font=("Segoe UI", 9, "bold"), bg="white").pack(
            side="left", padx=(0, 8))
        self.var_codigo = tk.StringVar()
        self.entry_codigo = tk.Entry(barra, textvariable=self.var_codigo, font=("Segoe UI", 10), width=20)
        self.entry_codigo.pack(side="left", padx=(0, 10))
        self.entry_codigo.bind("<Return>", lambda e: self._agregar_por_codigo())

        tk.Button(barra, text="🔍 Buscar Producto", font=("Segoe UI", 9, "bold"), bg="#0891b2",
                  fg="white", relief="flat", padx=10, pady=5, cursor="hand2",
                  command=self._abrir_buscar_producto).pack(side="left", padx=(0, 6))
        tk.Button(barra, text="🏷 Mayoreo", font=("Segoe UI", 9, "bold"), bg="#ca8a04",
                  fg="white", relief="flat", padx=10, pady=5, cursor="hand2",
                  command=self._toggle_mayoreo).pack(side="left", padx=(0, 6))
        tk.Button(barra, text="🗑 Quitar Seleccionado", font=("Segoe UI", 9, "bold"), bg="#6b7280",
                  fg="white", relief="flat", padx=10, pady=5, cursor="hand2",
                  command=self._quitar_seleccionado).pack(side="left")

    # ---------------- GRILLA ----------------
    def _construir_grilla(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        columnas = ("codigo", "descripcion", "precio_venta", "cantidad", "importe")
        encabezados = ("Código", "Descripción", "Precio Venta", "Cant.", "Importe")

        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc in zip(columnas, encabezados):
            self.tabla.heading(col, text=enc)
            ancho = 280 if col == "descripcion" else 100
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

        self.tabla.bind("<<TreeviewSelect>>", lambda e: self._actualizar_barra_cantidad())
        self.tabla.bind("<Delete>", lambda e: self._quitar_seleccionado())

    # ---------------- BARRA +/- CANTIDAD ----------------
    def _construir_barra_cantidad(self):
        barra = tk.Frame(self, bg=GRIS_FONDO)
        barra.pack(fill="x", padx=10, pady=(0, 5))
        interior = tk.Frame(barra, bg=GRIS_FONDO)
        interior.pack(fill="x", padx=10, pady=6)

        self.label_producto_control = tk.Label(
            interior, text="Selecciona un producto de la lista para ajustar su cantidad",
            font=("Segoe UI", 9), bg=GRIS_FONDO)
        self.label_producto_control.pack(side="left")

        frame_cant = tk.Frame(interior, bg=GRIS_FONDO)
        frame_cant.pack(side="right")
        self.btn_disminuir = tk.Button(frame_cant, text="－", font=("Segoe UI", 10, "bold"), width=3,
                                       bg="#fecaca", relief="flat", state="disabled", cursor="hand2",
                                       command=self._disminuir_cantidad)
        self.btn_disminuir.pack(side="left", padx=(0, 4))
        self.var_cantidad_actual = tk.StringVar(value="0")
        self.entry_cantidad_actual = tk.Entry(frame_cant, textvariable=self.var_cantidad_actual,
                                              font=("Segoe UI", 10), width=8, justify="center", state="disabled")
        self.entry_cantidad_actual.pack(side="left", padx=4)
        self.entry_cantidad_actual.bind("<Return>", lambda e: self._confirmar_cantidad_escrita(quitar_foco=True))
        self.entry_cantidad_actual.bind("<FocusOut>", lambda e: self._confirmar_cantidad_escrita(quitar_foco=False))
        self.btn_aumentar = tk.Button(frame_cant, text="＋", font=("Segoe UI", 10, "bold"), width=3,
                                      bg="#bbf7d0", relief="flat", state="disabled", cursor="hand2",
                                      command=self._aumentar_cantidad)
        self.btn_aumentar.pack(side="left", padx=(4, 0))

        # Bloque opcional "cargar por monto": solo se muestra cuando el
        # producto seleccionado se vende por Kilogramo/Litro/Metro. Permite
        # escribir cuánto dinero (Gs.) va a llevar de este local y calcula
        # automáticamente cuántos Kg/Lt/Mt corresponden a ese monto.
        self.frame_por_monto = tk.Frame(interior, bg=GRIS_FONDO)
        self._abrev_unidad_monto = ""

        tk.Label(self.frame_por_monto, text="│", font=("Segoe UI", 12), bg=GRIS_FONDO,
                 fg="#cbd5e1").pack(side="left", padx=(0, 8))
        tk.Label(self.frame_por_monto, text="💰 Por monto:", font=("Segoe UI", 9),
                 bg=GRIS_FONDO, fg="#555").pack(side="left")

        self.var_monto_cantidad = tk.StringVar(value="")
        self.entry_monto_cantidad = tk.Entry(
            self.frame_por_monto, textvariable=self.var_monto_cantidad, font=("Segoe UI", 10, "bold"),
            width=9, justify="center", relief="solid", bd=1)
        self.entry_monto_cantidad.pack(side="left", padx=6)
        self.entry_monto_cantidad.bind("<KeyRelease>", lambda e: self._previsualizar_cantidad_por_monto())
        self.entry_monto_cantidad.bind("<Return>", lambda e: self._confirmar_cantidad_por_monto(quitar_foco=True))
        self.entry_monto_cantidad.bind("<FocusOut>", lambda e: self._confirmar_cantidad_por_monto(quitar_foco=False))

        self.label_preview_monto = tk.Label(self.frame_por_monto, text="", font=("Segoe UI", 9, "bold"),
                                             bg=GRIS_FONDO, fg="#166534", width=26, anchor="w")
        self.label_preview_monto.pack(side="left", padx=(6, 0))

        # Arranca oculto: solo se muestra cuando corresponde (ver
        # _actualizar_barra_cantidad / _mostrar_control_por_monto).

    def _construir_pie_subtotal(self):
        pie = tk.Frame(self, bg="white")
        pie.pack(fill="x", padx=10, pady=(0, 10))
        self.label_contador_local = tk.Label(pie, text="0 productos en este local.",
                                             font=("Segoe UI", 9), bg="white", fg="#6b7280")
        self.label_contador_local.pack(side="left")
        self.label_subtotal_local = tk.Label(pie, text="Subtotal: Gs. 0",
                                             font=("Segoe UI", 12, "bold"), bg="white", fg="#1d4ed8")
        self.label_subtotal_local.pack(side="right")

    # ---------------- AGREGAR PRODUCTOS ----------------
    def _agregar_por_codigo(self):
        codigo = self.var_codigo.get().strip()
        if not codigo:
            return
        producto = buscar_producto_por_codigo(codigo)
        if producto is None or not producto["activo"]:
            messagebox.showerror("No encontrado",
                                 f"No existe un producto activo con el código '{codigo}'.", parent=self)
            self.var_codigo.set("")
            return
        self._agregar_item(producto)
        self.var_codigo.set("")
        self.entry_codigo.focus()

    def _abrir_buscar_producto(self):
        VentanaBuscarProducto(self, on_seleccionado=self._agregar_item)

    def _agregar_item(self, producto, cantidad=1):
        for item in self.items:
            if item["producto"]["id"] == producto["id"]:
                item["cantidad"] += cantidad
                self._actualizar_vista()
                return
        self.items.append({
            "producto": producto, "cantidad": cantidad,
            "precio_unitario": producto["precio_venta"], "es_mayoreo": False,
        })
        self._actualizar_vista()

    # ---------------- ACTUALIZAR GRILLA Y SUBTOTAL ----------------
    def calcular_subtotal(self) -> float:
        return sum(it["cantidad"] * it["precio_unitario"] for it in self.items)

    def _actualizar_vista(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        for item in self.items:
            p = item["producto"]
            importe = item["cantidad"] * item["precio_unitario"]
            unidad = p.get("unidad_medida", "Unidad")
            cantidad_txt = formatear_cantidad(item["cantidad"], unidad)
            descripcion = f"{p['nombre']}  🏷 Mayoreo" if item.get("es_mayoreo") else p["nombre"]
            self.tabla.insert("", "end", iid=str(p["id"]), values=(
                p["id"], descripcion, formatear_gs(item["precio_unitario"]),
                cantidad_txt, formatear_gs(importe),
            ), tags=("importe",))

        subtotal = self.calcular_subtotal()
        self.label_contador_local.config(text=f"{len(self.items)} producto(s) en este local.")
        self.label_subtotal_local.config(text=f"Subtotal: {formatear_gs(subtotal)}")
        self._actualizar_barra_cantidad()
        self.ventana_padre._actualizar_total_general()
        self.ventana_padre._sincronizar_automaticamente()

    # ---------------- SELECCIÓN Y AJUSTE DE CANTIDAD ----------------
    def _item_seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return None
        producto_id = int(seleccion[0])
        return next((i for i in self.items if i["producto"]["id"] == producto_id), None)

    def _actualizar_barra_cantidad(self):
        item = self._item_seleccionado()
        if item is None:
            self._producto_id_en_edicion = None
            self.label_producto_control.config(text="Selecciona un producto de la lista para ajustar su cantidad")
            self.var_cantidad_actual.set("0")
            self.btn_disminuir.config(state="disabled")
            self.btn_aumentar.config(state="disabled")
            self.entry_cantidad_actual.config(state="disabled")
            self._ocultar_control_por_monto()
        else:
            self._producto_id_en_edicion = item["producto"]["id"]
            self.label_producto_control.config(text=item["producto"]["nombre"])
            unidad = item["producto"].get("unidad_medida", "Unidad")
            valor = item["cantidad"]
            texto = f"{valor:g}" if unidad_es_fraccionable(unidad) else str(int(valor))
            self.var_cantidad_actual.set(texto)
            self.btn_disminuir.config(state="normal")
            self.btn_aumentar.config(state="normal")
            self.entry_cantidad_actual.config(state="normal")
            if unidad_es_fraccionable(unidad):
                self._mostrar_control_por_monto(unidad)
            else:
                self._ocultar_control_por_monto()

    def _mostrar_control_por_monto(self, unidad: str):
        """Muestra el bloque 'Cargar por monto' (solo aplica a productos que
        se venden por Kg/Lt/Mt)."""
        abrev = {"Kilogramo": "Kg", "Litro": "Lt", "Metro": "Mt"}.get(unidad, unidad)
        self._abrev_unidad_monto = abrev
        self.var_monto_cantidad.set("")
        self.label_preview_monto.config(text="")
        if not self.frame_por_monto.winfo_ismapped():
            self.frame_por_monto.pack(side="right", padx=(0, 10))

    def _ocultar_control_por_monto(self):
        self.var_monto_cantidad.set("")
        self.label_preview_monto.config(text="")
        self.frame_por_monto.pack_forget()

    def _previsualizar_cantidad_por_monto(self):
        """Mientras se escribe el monto en guaraníes, muestra en vivo a
        cuántos Kg/Lt/Mt equivale, sin todavía aplicarlo."""
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
        """Calcula la cantidad exacta de Kg/Lt/Mt que corresponde al monto
        ingresado y la aplica como la cantidad del artículo en este local."""
        if getattr(self, "_procesando_monto", False):
            return
        self._procesando_monto = True
        try:
            producto_id = getattr(self, "_producto_id_en_edicion", None)
            if producto_id is None:
                return
            item = next((i for i in self.items if i["producto"]["id"] == producto_id), None)
            if item is None:
                return

            texto = self.var_monto_cantidad.get().strip()
            if not texto:
                return

            try:
                monto = parsear_cantidad(texto)
                if monto < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Monto inválido", "Ingresa un monto en guaraníes válido (0 o mayor).",
                                     parent=self)
                self.var_monto_cantidad.set("")
                self.label_preview_monto.config(text="")
                return

            precio = item["precio_unitario"]
            if not precio or precio <= 0:
                messagebox.showerror(
                    "Precio no disponible",
                    f"'{item['producto']['nombre']}' no tiene un precio unitario válido "
                    "para calcular la cantidad a partir del monto.", parent=self)
                self.var_monto_cantidad.set("")
                self.label_preview_monto.config(text="")
                return

            cantidad = round(monto / precio, 3)

            if cantidad <= 0:
                self.items = [i for i in self.items if i["producto"]["id"] != producto_id]
                self._actualizar_vista()
                self._actualizar_barra_cantidad()
                return

            item["cantidad"] = cantidad
            self._actualizar_vista()
            self._reseleccionar_y_refrescar_barra(producto_id)

            if quitar_foco:
                self.entry_codigo.focus_set()
        finally:
            self._procesando_monto = False

    def _confirmar_cantidad_escrita(self, quitar_foco: bool = False):
        # Protección anti-doble-disparo (Enter dispara focus_set() al final,
        # lo que genera un <FocusOut> que volvería a llamar a este mismo
        # método mientras el primero todavía se está ejecutando).
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
            # otra fila, pero el texto del campo todavía es el viejo
            # (por ejemplo "0" de un estado "sin selección" anterior).
            # Si en ese caso volviéramos a leer la selección actual,
            # terminaríamos aplicando ese "0" al producto EQUIVOCADO y
            # lo borraríamos de la grilla sin que el usuario lo pidiera.
            producto_id = getattr(self, "_producto_id_en_edicion", None)
            if producto_id is None:
                return
            item = next((i for i in self.items if i["producto"]["id"] == producto_id), None)
            if item is None:
                return

            texto = self.var_cantidad_actual.get().strip()
            unidad = item["producto"].get("unidad_medida", "Unidad")
            try:
                nueva_cantidad = parsear_cantidad(texto)
                if nueva_cantidad < 0:
                    raise ValueError
                if not unidad_es_fraccionable(unidad) and nueva_cantidad != int(nueva_cantidad):
                    messagebox.showerror("Cantidad inválida",
                                         f"'{item['producto']['nombre']}' se vende por {unidad.lower()} "
                                         "y no admite cantidades con decimales.", parent=self)
                    self._actualizar_barra_cantidad()
                    return
            except ValueError:
                messagebox.showerror("Cantidad inválida", "Ingresa un número válido (0 o mayor).", parent=self)
                self._actualizar_barra_cantidad()
                return

            if nueva_cantidad <= 0:
                self.items = [i for i in self.items if i["producto"]["id"] != producto_id]
                self._actualizar_vista()
                self._actualizar_barra_cantidad()
                return

            # Si el valor no cambió, no hace falta reconstruir la grilla.
            if nueva_cantidad == item["cantidad"]:
                if quitar_foco:
                    self.entry_codigo.focus_set()
                return

            item["cantidad"] = nueva_cantidad
            self._actualizar_vista()
            self._reseleccionar_y_refrescar_barra(producto_id)

            if quitar_foco:
                self.entry_codigo.focus_set()
        finally:
            self._procesando_cantidad = False

    def _aumentar_cantidad(self):
        item = self._item_seleccionado()
        if item is None:
            return
        item["cantidad"] += 1
        self._actualizar_vista()
        self._reseleccionar_y_refrescar_barra(item["producto"]["id"])

    def _disminuir_cantidad(self):
        item = self._item_seleccionado()
        if item is None:
            return
        if item["cantidad"] <= 1:
            producto_id = item["producto"]["id"]
            self.items = [i for i in self.items if i["producto"]["id"] != producto_id]
            self._actualizar_vista()
            self._actualizar_barra_cantidad()
            return
        item["cantidad"] -= 1
        self._actualizar_vista()
        self._reseleccionar_y_refrescar_barra(item["producto"]["id"])

    def _quitar_seleccionado(self):
        item = self._item_seleccionado()
        if item is None:
            messagebox.showinfo("Selecciona un producto", "Primero selecciona un producto de la lista.",
                               parent=self)
            return
        producto_id = item["producto"]["id"]
        self.items = [i for i in self.items if i["producto"]["id"] != producto_id]
        self._actualizar_vista()

    def _toggle_mayoreo(self):
        """Alterna el precio Mayorista/Normal solo en la línea seleccionada
        de este local, igual que F11 en la pantalla principal de Ventas."""
        item = self._item_seleccionado()
        if item is None:
            messagebox.showinfo("Selecciona un producto",
                               "Primero selecciona el producto de este local al que quieras "
                               "aplicar el precio Mayoreo.", parent=self)
            return
        p = item["producto"]
        item["es_mayoreo"] = not item.get("es_mayoreo", False)
        item["precio_unitario"] = p["precio_mayorista"] if item["es_mayoreo"] else p["precio_venta"]
        self._actualizar_vista()
        self._reseleccionar_y_refrescar_barra(p["id"])

    def _reseleccionar_y_refrescar_barra(self, producto_id):
        str_id = str(producto_id)
        if str_id in self.tabla.get_children():
            self.tabla.selection_set(str_id)
        self._actualizar_barra_cantidad()
