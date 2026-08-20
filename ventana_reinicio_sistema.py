"""
ventana_reinicio_sistema.py
Módulo "Reinicio del Sistema": permite borrar de forma persistente y
definitiva los datos del negocio, liberando el espacio de la base de
datos para reutilizarlo, como si el sistema arrancara desde cero.

Dos modalidades, cada una con su propia tarjeta y flujo de confirmación
reforzado (escribir una palabra exacta + contraseña del administrador):
  1. Reiniciar datos del negocio   → borra ventas, productos, clientes,
                                      inventario, caja, compras, créditos,
                                      devoluciones, presupuestos, préstamos,
                                      asistencia técnica, veterinaria,
                                      restaurante, streaming e importaciones.
                                      Conserva usuarios y la licencia activa.
  2. Reinicio total de fábrica     → borra TODO lo anterior Y TAMBIÉN los
                                      usuarios. El sistema vuelve a pedir
                                      crear el primer administrador al
                                      reiniciar.

Solo accesible para administradores.
"""
import tkinter as tk
from tkinter import messagebox, ttk

from models_reset import (
    obtener_resumen_antes_de_reset,
    reiniciar_datos_de_negocio,
    reinicio_total_de_fabrica,
    tablas_sin_categoria,
)
from auth import login
from utilidades_ui import ajustar_tamaño_ventana
from traducciones import t

AZUL_RIBBON = "#1d5fd6"
AZUL_OSCURO = "#163d8c"
GRIS_FONDO  = "#f4f5f7"
GRIS_BORDE  = "#e2e8f0"
BLANCO      = "#ffffff"
VERDE       = "#16a34a"
ROJO        = "#dc2626"
ROJO_OSCURO = "#991b1b"
NARANJA     = "#d97706"
GRIS_TEXTO  = "#6b7280"


# ─────────────────────────────────────────────────────────────
#  PANEL PRINCIPAL
# ─────────────────────────────────────────────────────────────
class PanelReinicioSistema(tk.Frame):
    def __init__(self, parent, usuario_actual, on_reinicio_total=None):
        super().__init__(parent, bg=GRIS_FONDO)
        self.usuario_actual = usuario_actual
        # Callback que el contenedor (main.py) usa para cerrar la sesión
        # actual y volver al login tras un reinicio total de fábrica
        # (los usuarios, incluido el que está logueado, ya no existen).
        self.on_reinicio_total = on_reinicio_total
        self._construir_ui()

    def _construir_ui(self):
        # ── Encabezado ──────────────────────────────────────────
        encabezado = tk.Frame(self, bg=ROJO, height=54)
        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)
        tk.Label(encabezado, text=t("reinicio_titulo"),
                 font=("Segoe UI", 15, "bold"), bg=ROJO, fg=BLANCO
                 ).pack(side="left", padx=20, pady=12)

        canvas = tk.Canvas(self, bg=GRIS_FONDO, highlightthickness=0)
        scroll = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        contenedor = tk.Frame(canvas, bg=GRIS_FONDO)
        canvas.create_window((0, 0), window=contenedor, anchor="nw")
        contenedor.bind("<Configure>",
                        lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        def _scroll(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
            else:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_scroll(widget):
            widget.bind("<MouseWheel>", _scroll)
            widget.bind("<Button-4>", _scroll)
            widget.bind("<Button-5>", _scroll)
            for h in widget.winfo_children():
                _bind_scroll(h)

        _bind_scroll(canvas)
        contenedor.bind("<Configure>",
                        lambda e: (_bind_scroll(contenedor),
                                   canvas.configure(scrollregion=canvas.bbox("all"))))

        # ── Advertencia general ──────────────────────────────────
        nota = tk.Frame(contenedor, bg="#fef2f2")
        nota.pack(fill="x", padx=30, pady=(20, 10))
        tk.Frame(nota, bg=ROJO, width=4).pack(side="left", fill="y")
        tk.Label(nota,
                 text="⚠  Las acciones de esta sección son PERMANENTES y no se pueden deshacer.\n"
                      "Antes de continuar, te recomendamos exportar una copia de seguridad desde\n"
                      "'Gestión de Datos' por si necesitás los datos más adelante.",
                 font=("Segoe UI", 9), bg="#fef2f2", fg=ROJO_OSCURO,
                 justify="left", padx=14, pady=10).pack(side="left", anchor="w")

        # ── Resumen actual de la BD ──────────────────────────────
        self.frame_resumen = tk.Frame(contenedor, bg=BLANCO,
                                       highlightthickness=1, highlightbackground=GRIS_BORDE)
        self.frame_resumen.pack(fill="x", padx=30, pady=(0, 20))
        self._construir_resumen()

        # ── Sección: Reinicio parcial ────────────────────────────
        self._seccion(contenedor, "🔄  Reiniciar datos del negocio")
        fila1 = tk.Frame(contenedor, bg=GRIS_FONDO)
        fila1.pack(fill="x", padx=30, pady=(0, 10))
        self._tarjeta(
            fila1,
            icono="🧹", titulo="Reiniciar datos del negocio",
            descripcion=(
                "Borra de forma persistente: productos, ventas, clientes, "
                "inventario, caja, compras, créditos, devoluciones, presupuestos, "
                "préstamos (incluidas sus cuotas y pagos), asistencia técnica, "
                "veterinaria (mascotas, consultas, vacunas), restaurante/comedor "
                "(comandas, platos, mesas) y alquiler de streaming (cuentas, "
                "perfiles, suscripciones).\n\n"
                "✓ Conserva los usuarios y sus contraseñas.\n"
                "✓ Conserva la licencia activa (no hace falta reactivar).\n"
                "✓ Conserva tus puntajes de Juegos y la Biblia ya descargada."
            ),
            color_boton=NARANJA, texto_boton="Reiniciar datos del negocio",
            comando=self._abrir_confirmacion_parcial,
        )

        # ── Sección: Reinicio total ──────────────────────────────
        self._seccion(contenedor, "💥  Reinicio total de fábrica")
        fila2 = tk.Frame(contenedor, bg=GRIS_FONDO)
        fila2.pack(fill="x", padx=30, pady=(0, 30))
        self._tarjeta(
            fila2,
            icono="☢", titulo="Reinicio total de fábrica",
            descripcion=(
                "Borra ABSOLUTAMENTE TODO: todos los datos del negocio (incluidos "
                "préstamos, presupuestos, asistencia técnica, veterinaria, "
                "restaurante y streaming), tus puntajes de Juegos, Y TAMBIÉN los "
                "usuarios (incluida tu propia cuenta).\n\n"
                "El sistema quedará exactamente como recién instalado: al "
                "reiniciar la app, pedirá crear el primer administrador.\n\n"
                "✓ La licencia activa se conserva.\n"
                "✓ La Biblia ya descargada se conserva (no hace falta bajarla de nuevo)."
            ),
            color_boton=ROJO, texto_boton="Reinicio total de fábrica",
            comando=self._abrir_confirmacion_total,
        )

    # ── Resumen de impacto ───────────────────────────────────────
    def _construir_resumen(self):
        for w in self.frame_resumen.winfo_children():
            w.destroy()

        tk.Label(self.frame_resumen, text=t("reinicio_estado_bd"),
                 font=("Segoe UI", 11, "bold"), bg=BLANCO
                 ).pack(anchor="w", padx=16, pady=(14, 8))

        r = obtener_resumen_antes_de_reset()

        # La cantidad de bloques crece con cada módulo nuevo que se agrega
        # al sistema, así que en pantallas angostas (o con muchos módulos)
        # ya no entran todos en una sola fila. Para no cortar ni achicar
        # los números, la fila va dentro de un canvas horizontal con su
        # propia barra de desplazamiento lateral en vez de un Frame fijo.
        contenedor_h = tk.Frame(self.frame_resumen, bg=BLANCO)
        contenedor_h.pack(fill="x", padx=16, pady=(0, 16))

        canvas_h = tk.Canvas(contenedor_h, bg=BLANCO, highlightthickness=0, height=58)
        scroll_h = tk.Scrollbar(contenedor_h, orient="horizontal", command=canvas_h.xview)
        canvas_h.configure(xscrollcommand=scroll_h.set)
        canvas_h.pack(fill="x")
        scroll_h.pack(fill="x", pady=(4, 0))

        fila = tk.Frame(canvas_h, bg=BLANCO)
        ventana_fila = canvas_h.create_window((0, 0), window=fila, anchor="nw")

        def _actualizar_scroll_h(event=None):
            canvas_h.configure(scrollregion=canvas_h.bbox("all"))
            # Si todos los bloques entran en el ancho visible, no hace
            # falta mostrar la barra (evita una barra "decorativa" vacía).
            ancho_contenido = fila.winfo_reqwidth()
            ancho_visible = canvas_h.winfo_width()
            if ancho_contenido <= ancho_visible:
                scroll_h.pack_forget()
            else:
                scroll_h.pack(fill="x", pady=(4, 0))

        fila.bind("<Configure>", _actualizar_scroll_h)
        canvas_h.bind("<Configure>", _actualizar_scroll_h)

        def _scroll_horizontal(event):
            # Rueda del mouse + Shift, o touchpad con gesto lateral,
            # desplazan la fila sin afectar el scroll vertical de la
            # ventana (que sigue manejando el canvas exterior).
            if event.num == 4:
                canvas_h.xview_scroll(-1, "units")
            elif event.num == 5:
                canvas_h.xview_scroll(1, "units")
            else:
                canvas_h.xview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas_h.bind("<Shift-MouseWheel>", _scroll_horizontal)
        canvas_h.bind("<Shift-Button-4>", _scroll_horizontal)
        canvas_h.bind("<Shift-Button-5>", _scroll_horizontal)

        def bloque(etiqueta, valor):
            f = tk.Frame(fila, bg=BLANCO)
            f.pack(side="left", padx=(0, 36))
            tk.Label(f, text=str(valor), font=("Segoe UI", 16, "bold"),
                     bg=BLANCO, fg=AZUL_RIBBON).pack(anchor="w")
            tk.Label(f, text=etiqueta, font=("Segoe UI", 8),
                     bg=BLANCO, fg=GRIS_TEXTO).pack(anchor="w")

        bloque("Productos", r["productos"])
        bloque("Clientes", r["clientes"])
        bloque("Ventas", r["ventas"])
        bloque("Mov. de Inventario", r["movimientos_inventario"])
        bloque("Compras", r["compras"])
        bloque("Préstamos", r["prestamos"])
        bloque("Presupuestos", r["presupuestos"])
        bloque("Casos Técnicos", r["casos_tecnicos"])
        bloque("Mascotas (Vet.)", r["mascotas"])
        bloque("Comandas (Rest.)", r["rest_comandas"])
        bloque("Suscrip. Streaming", r["stream_suscripciones"])
        bloque("Compras Importación", r["import_compras"])
        bloque("Usuarios", r["usuarios"])

        fila2 = tk.Frame(self.frame_resumen, bg=BLANCO)
        fila2.pack(fill="x", padx=16, pady=(0, 14))
        faltantes = tablas_sin_categoria()
        if faltantes:
            tk.Label(fila2,
                     text=f"⚠ Hay {len(faltantes)} tabla(s) nueva(s) sin clasificar en el reinicio: "
                          + ", ".join(faltantes) + ". Avisale a soporte para que las agregue.",
                     font=("Segoe UI", 8, "bold"), bg=BLANCO, fg=ROJO_OSCURO,
                     wraplength=900, justify="left").pack(anchor="w")
        else:
            tk.Label(fila2,
                     text="✓ Verificado: todos los módulos del sistema (incluidos Préstamos, "
                          "Presupuestos, Asistencia Técnica, Veterinaria, Restaurante, Streaming "
                          "e Importaciones) están cubiertos por el reinicio.",
                     font=("Segoe UI", 8, "bold"), bg=BLANCO, fg=VERDE).pack(anchor="w")

        tk.Button(self.frame_resumen, text=t("actualizar"),
                  font=("Segoe UI", 8), bg=BLANCO, relief="solid", bd=1,
                  padx=8, pady=3, cursor="hand2",
                  command=self._construir_resumen
                  ).place(relx=1.0, rely=0, anchor="ne", x=-12, y=12)

    # ── Helpers de UI compartidos con ventana_datos.py ──────────
    def _seccion(self, parent, titulo):
        f = tk.Frame(parent, bg=GRIS_FONDO)
        f.pack(fill="x", padx=30, pady=(10, 8))
        tk.Label(f, text=titulo, font=("Segoe UI", 12, "bold"),
                 bg=GRIS_FONDO, fg="#1e293b").pack(side="left")
        tk.Frame(f, bg=GRIS_BORDE, height=1).pack(side="left", fill="x", expand=True, padx=(12, 0), pady=7)

    def _tarjeta(self, parent, icono, titulo, descripcion,
                 color_boton, texto_boton, comando):
        card = tk.Frame(parent, bg=BLANCO, relief="flat", bd=0,
                        highlightthickness=1, highlightbackground=GRIS_BORDE)
        card.pack(fill="x", ipadx=10, ipady=12)

        tk.Label(card, text=icono, font=("Segoe UI", 28),
                 bg=BLANCO).pack(anchor="w", padx=16, pady=(14, 4))
        tk.Label(card, text=titulo, font=("Segoe UI", 12, "bold"),
                 bg=BLANCO, fg="#1e293b").pack(anchor="w", padx=16)
        tk.Label(card, text=descripcion, font=("Segoe UI", 9),
                 bg=BLANCO, fg=GRIS_TEXTO, justify="left",
                 wraplength=640).pack(anchor="w", padx=16, pady=(4, 14))

        tk.Button(card, text=texto_boton, font=("Segoe UI", 10, "bold"),
                  bg=color_boton, fg=BLANCO, relief="flat", bd=0,
                  padx=18, pady=8, cursor="hand2",
                  activebackground=ROJO_OSCURO, activeforeground=BLANCO,
                  command=comando).pack(anchor="w", padx=16, pady=(0, 14))

    # ── Acciones ─────────────────────────────────────────────────
    def _abrir_confirmacion_parcial(self):
        _VentanaConfirmacionReset(
            self,
            usuario_actual=self.usuario_actual,
            titulo="Reiniciar datos del negocio",
            color=NARANJA,
            palabra_confirmacion="REINICIAR",
            descripcion=(
                "Vas a borrar de forma PERMANENTE todos los productos, ventas, "
                "clientes, inventario, caja, compras, créditos, devoluciones, "
                "presupuestos, préstamos, asistencia técnica, veterinaria, "
                "restaurante/comedor y alquiler de streaming.\n\n"
                "Los usuarios y la licencia activa NO se verán afectados."
            ),
            on_confirmado=self._ejecutar_reset_parcial,
        )

    def _abrir_confirmacion_total(self):
        _VentanaConfirmacionReset(
            self,
            usuario_actual=self.usuario_actual,
            titulo="Reinicio total de fábrica",
            color=ROJO,
            palabra_confirmacion="ELIMINAR TODO",
            descripcion=(
                "Vas a borrar de forma PERMANENTE absolutamente todo, incluyendo "
                "TODOS los usuarios (también tu propia cuenta).\n\n"
                "Al cerrar este diálogo se cerrará tu sesión automáticamente, y la "
                "próxima vez que se abra el sistema pedirá crear el primer "
                "administrador, como una instalación nueva."
            ),
            on_confirmado=self._ejecutar_reset_total,
        )

    def _ejecutar_reset_parcial(self):
        ok, msg = reiniciar_datos_de_negocio()
        if ok:
            messagebox.showinfo("Reinicio completado", msg, parent=self)
            self._construir_resumen()
        else:
            messagebox.showerror("Error", msg, parent=self)

    def _ejecutar_reset_total(self):
        ok, msg = reinicio_total_de_fabrica()
        if ok:
            messagebox.showinfo("Reinicio total completado", msg, parent=self)
            if self.on_reinicio_total:
                self.on_reinicio_total()
        else:
            messagebox.showerror("Error", msg, parent=self)


# ─────────────────────────────────────────────────────────────
#  VENTANA DE CONFIRMACIÓN REFORZADA
# ─────────────────────────────────────────────────────────────
class _VentanaConfirmacionReset(tk.Toplevel):
    """Exige dos pasos antes de ejecutar un reset destructivo:
      1. Escribir una palabra exacta de confirmación.
      2. Ingresar usuario y contraseña de un administrador.
    Ambos deben ser correctos para habilitar el botón final.

    Usa la barra de título NATIVA del sistema operativo (con sus botones
    reales de minimizar, maximizar y cerrar) y un layout responsive con
    grid + scroll, para que la ventana se pueda redimensionar o maximizar
    sin que ningún campo o botón quede cortado fuera del área visible."""

    def __init__(self, parent, usuario_actual, titulo, color,
                 palabra_confirmacion, descripcion, on_confirmado):
        super().__init__(parent)
        self.usuario_actual = usuario_actual
        self.palabra_confirmacion = palabra_confirmacion
        self.on_confirmado = on_confirmado

        self.title(titulo)
        self.resizable(True, True)
        self.configure(bg=BLANCO)
        self.grab_set()
        # NOTA: no usamos transient(parent) a propósito. En Windows, una
        # ventana Toplevel marcada como "transient" de su padre pierde los
        # botones nativos de minimizar y maximizar (queda solo con cerrar),
        # que es justo lo que no queremos en este diálogo.
        #
        # Además, forzamos explícitamente '-toolwindow' a False: en Windows,
        # cuando Tk decide automáticamente el estilo de la ventana, a veces
        # la clasifica como "tool window" (la usada para paletas/diálogos
        # flotantes), que SIEMPRE viene sin botones de minimizar/maximizar
        # sin importar resizable(). Forzarlo a False asegura una ventana
        # estándar con los tres botones completos. Se ignora en silencio en
        # sistemas no-Windows, donde este atributo no existe.
        try:
            self.attributes("-toolwindow", False)
        except tk.TclError:
            pass

        # Layout raíz responsive: fila 0 = barra de color (fija),
        # fila 1 = cuerpo con scroll (se expande), fila 2 = botones (fija).
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Barra de color (NO es la barra de título del SO; esa la pone
        # Windows/Linux automáticamente con sus botones nativos) ──────
        barra = tk.Frame(self, bg=color, height=40)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text=f"⚠  {titulo}", font=("Segoe UI", 11, "bold"),
                 bg=color, fg=BLANCO).pack(side="left", padx=16, pady=9)

        # ── Cuerpo scrolleable (por si la ventana queda muy chica) ────
        contenedor_scroll = tk.Frame(self, bg=BLANCO)
        contenedor_scroll.grid(row=1, column=0, sticky="nsew")
        contenedor_scroll.grid_rowconfigure(0, weight=1)
        contenedor_scroll.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(contenedor_scroll, bg=BLANCO, highlightthickness=0)
        scrollbar = ttk.Scrollbar(contenedor_scroll, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        cuerpo = tk.Frame(canvas, bg=BLANCO, padx=20, pady=16)
        ventana_canvas = canvas.create_window((0, 0), window=cuerpo, anchor="nw")

        def _actualizar_scrollregion(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _ajustar_ancho_cuerpo(event):
            # El frame interno siempre ocupa el ancho visible del canvas,
            # para que el wraplength de las etiquetas se recalcule bien
            # al redimensionar o maximizar la ventana.
            canvas.itemconfig(ventana_canvas, width=event.width)

        cuerpo.bind("<Configure>", _actualizar_scrollregion)
        canvas.bind("<Configure>", _ajustar_ancho_cuerpo)

        def _scroll(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
            else:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        for w in (canvas, cuerpo):
            w.bind("<MouseWheel>", _scroll)
            w.bind("<Button-4>", _scroll)
            w.bind("<Button-5>", _scroll)

        tk.Label(cuerpo, text=descripcion, font=("Segoe UI", 9),
                 bg=BLANCO, fg="#374151", justify="left",
                 wraplength=420).pack(anchor="w", pady=(0, 16), fill="x")

        tk.Frame(cuerpo, bg=GRIS_BORDE, height=1).pack(fill="x", pady=(0, 14))

        # Paso 1: palabra de confirmación
        tk.Label(cuerpo,
                 text=f"Para confirmar, escribí exactamente:  {palabra_confirmacion}",
                 font=("Segoe UI", 9, "bold"), bg=BLANCO, wraplength=420,
                 justify="left").pack(anchor="w", pady=(0, 4), fill="x")
        self.var_palabra = tk.StringVar()
        entry_palabra = tk.Entry(cuerpo, textvariable=self.var_palabra,
                                 font=("Segoe UI", 11))
        entry_palabra.pack(fill="x", pady=(0, 14))
        self.var_palabra.trace_add("write", lambda *_: self._validar())
        entry_palabra.bind("<Tab>", self._tab_siguiente)

        # Paso 2: usuario y contraseña de administrador
        tk.Label(cuerpo, text=t("reinicio_usuario_admin"),
                 font=("Segoe UI", 9, "bold"), bg=BLANCO
                 ).pack(anchor="w", pady=(0, 4))
        self.var_usuario = tk.StringVar()
        entry_usuario = tk.Entry(cuerpo, textvariable=self.var_usuario,
                                 font=("Segoe UI", 11))
        entry_usuario.pack(fill="x", pady=(0, 14))
        self.var_usuario.trace_add("write", lambda *_: self._validar())

        tk.Label(cuerpo, text=t("contrasena_label"),
                 font=("Segoe UI", 9, "bold"), bg=BLANCO
                 ).pack(anchor="w", pady=(0, 4))
        self.var_password = tk.StringVar()
        entry_password = tk.Entry(cuerpo, textvariable=self.var_password,
                                  font=("Segoe UI", 11), show="•")
        entry_password.pack(fill="x", pady=(0, 6))
        self.var_password.trace_add("write", lambda *_: self._validar())
        entry_password.bind("<Return>", lambda e: self._confirmar() if str(self.btn_confirmar["state"]) == "normal" else None)

        self.lbl_estado = tk.Label(cuerpo, text="", font=("Segoe UI", 8),
                                   bg=BLANCO, fg=ROJO_OSCURO, wraplength=420,
                                   justify="left")
        self.lbl_estado.pack(anchor="w", pady=(0, 10), fill="x")

        # ── Botones (siempre fijos al pie, fuera del área scrolleable) ─
        pie = tk.Frame(self, bg=BLANCO)
        pie.grid(row=2, column=0, sticky="ew")
        tk.Frame(pie, bg=GRIS_BORDE, height=1).pack(fill="x")
        f_bot = tk.Frame(pie, bg=BLANCO, padx=20, pady=14)
        f_bot.pack(fill="x")
        self.btn_confirmar = tk.Button(
            f_bot, text=t("reinicio_confirmar_ejecutar"),
            font=("Segoe UI", 10, "bold"), bg=color, fg=BLANCO,
            relief="flat", padx=16, pady=9, cursor="hand2",
            state="disabled", command=self._confirmar,
        )
        self.btn_confirmar.pack(side="left", padx=(0, 10))
        tk.Button(f_bot, text=t("cancelar"), font=("Segoe UI", 10),
                  bg=BLANCO, fg="#374151", relief="solid", bd=1,
                  padx=16, pady=8, cursor="hand2",
                  command=self.destroy).pack(side="left")

        entry_palabra.focus()

        # Tamaño calculado según el contenido real (evita que el botón
        # de confirmar quede cortado), con un piso razonable y tope al
        # tamaño de pantalla si el contenido fuera muy largo.
        ajustar_tamaño_ventana(self, ancho_min=480, alto_min=480,
                               margen_alto=30, ancho_max=560, alto_max=700)

    def _tab_siguiente(self, event):
        event.widget.tk_focusNext().focus()
        return "break"

    def _validar(self):
        palabra_ok = self.var_palabra.get().strip() == self.palabra_confirmacion
        usuario_ingresado = bool(self.var_usuario.get().strip())
        password_ingresada = bool(self.var_password.get().strip())
        if palabra_ok and usuario_ingresado and password_ingresada:
            self.btn_confirmar.config(state="normal")
            self.lbl_estado.config(text="")
        else:
            self.btn_confirmar.config(state="disabled")

    def _confirmar(self):
        # Verificamos las credenciales ingresadas (usuario + contraseña)
        # contra la base de datos real, y exigimos explícitamente que el
        # usuario tenga rol 'admin' — no alcanza con cualquier login válido,
        # ni con que coincida con el usuario actualmente logueado.
        usuario_ingresado = self.var_usuario.get().strip()
        exito, _msg, datos = login(usuario_ingresado, self.var_password.get())

        if not exito:
            self.lbl_estado.config(text=t("reinicio_error_credenciales"))
            self.btn_confirmar.config(state="disabled")
            return

        if datos.get("rol") != "admin":
            self.lbl_estado.config(text=t("reinicio_error_permisos"))
            self.btn_confirmar.config(state="disabled")
            return

        if not messagebox.askyesno(
            "Última confirmación",
            "Esta es tu ÚLTIMA oportunidad de cancelar.\n\n"
            "¿Confirmás que querés ejecutar esta acción de forma definitiva?",
            icon="warning", parent=self,
        ):
            return

        self.destroy()
        self.on_confirmado()
