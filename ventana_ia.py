"""
ventana_ia.py
Módulo "Asistente IA": chat con un proveedor de IA real (OpenAI,
Anthropic, u otro compatible) integrado en MaquedaSystems, para:
  - Responder preguntas sobre cómo usar el sistema.
  - Analizar ventas del negocio y sugerir recomendaciones (botón
    'Analizar mis ventas', que arma el resumen automáticamente).
  - Generar descripciones de productos.
  - Chat libre para cualquier otra consulta.

Requiere que un Administrador configure antes un proveedor de IA (ver
ventana_configurar_ia.py) con su propia clave de API. Sin esa
configuración, el módulo muestra una pantalla explicando qué falta en
vez de un chat vacío.

El uso de este módulo tiene un costo real cobrado por el proveedor de
IA elegido (no por MaquedaSystems), y necesita conexión a internet.
"""
import tkinter as tk
from tkinter import messagebox
import datetime
import threading

from models_ia import obtener_configuracion_ia, enviar_mensaje_ia
from utilidades_ui import formatear_gs
from traducciones import t

AZUL_RIBBON = "#1d5fd6"
AZUL_OSCURO = "#163d8c"
GRIS_FONDO  = "#f4f5f7"
GRIS_BORDE  = "#e2e8f0"
BLANCO      = "#ffffff"
VERDE       = "#16a34a"
ROJO        = "#dc2626"
GRIS_TEXTO  = "#6b7280"
NEGRO       = "#1e293b"
BURBUJA_USUARIO   = "#1d5fd6"
BURBUJA_ASISTENTE = "#eef2f7"

MENSAJE_SISTEMA = (
    "Sos el Asistente IA integrado dentro de MaquedaSystems, un sistema de gestión de "
    "ventas, inventario, clientes y otros módulos de negocio (Créditos, Préstamos, "
    "Presupuestos, Compras, Asistencia Técnica, Veterinaria, Restaurante/Comedor, "
    "Alquiler de Streaming, Reportes, RRHH, Cotizaciones) usado por comercios pequeños "
    "y medianos, principalmente en Paraguay. Los montos del sistema están en Guaraníes "
    "(Gs.).\n\n"
    "Tus tareas principales:\n"
    "1. Ayudar a usar el sistema: explicar cómo hacer algo en MaquedaSystems de forma "
    "clara y con pasos concretos. Si no estás seguro de un detalle específico de esta "
    "versión del sistema, decilo en vez de inventar botones o pantallas que no sabés "
    "si existen.\n"
    "2. Analizar datos de ventas/negocio que el usuario te comparta, y dar "
    "recomendaciones prácticas y específicas, no genéricas.\n"
    "3. Ayudar a redactar descripciones de productos: claras, breves y orientadas a "
    "venta, en español, listas para pegar en el campo 'Descripción' del sistema.\n"
    "4. Cualquier otra consulta general que el usuario tenga.\n\n"
    "Respondé siempre en español, de forma directa y concisa, sin relleno innecesario. "
    "Usá listas o pasos numerados cuando ayude a la claridad."
)


class PanelAsistenteIA(tk.Frame):
    def __init__(self, parent, usuario_actual):
        super().__init__(parent, bg=GRIS_FONDO)
        self.usuario_actual = usuario_actual
        self.es_admin = bool(usuario_actual) and usuario_actual.get("rol") == "admin"
        self.config_ia = obtener_configuracion_ia()
        self.mensajes = [{"role": "system", "content": MENSAJE_SISTEMA}]
        self.esperando_respuesta = False

        self._construir_encabezado()
        if self.config_ia:
            self._construir_chat()
        else:
            self._construir_estado_sin_configurar()

    # ── Encabezado ───────────────────────────────────────────
    def _construir_encabezado(self):
        encabezado = tk.Frame(self, bg=AZUL_RIBBON, height=54)
        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)
        tk.Label(encabezado, text=t("ia_titulo"),
                 font=("Segoe UI", 15, "bold"), bg=AZUL_RIBBON, fg=BLANCO
                 ).pack(side="left", padx=20, pady=12)

        if self.es_admin:
            tk.Button(encabezado, text=t("ia_configurar"), font=("Segoe UI", 9, "bold"),
                      bg=AZUL_OSCURO, fg=BLANCO, relief="flat", padx=12, pady=5,
                      cursor="hand2", command=self._abrir_configuracion
                      ).pack(side="right", padx=16, pady=12)

    def _abrir_configuracion(self):
        from ventana_configurar_ia import VentanaConfigurarIA
        VentanaConfigurarIA(self, on_guardado=self._recargar_tras_configurar)

    def _recargar_tras_configurar(self):
        self.config_ia = obtener_configuracion_ia()
        # Se destruye todo lo que no sea el encabezado (primer hijo empaquetado)
        # y se reconstruye el cuerpo según si ya quedó configurado o no.
        for w in list(self.pack_slaves())[1:]:
            w.destroy()
        self.mensajes = [{"role": "system", "content": MENSAJE_SISTEMA}]
        if self.config_ia:
            self._construir_chat()
        else:
            self._construir_estado_sin_configurar()

    # ── Estado sin configurar ────────────────────────────────
    def _construir_estado_sin_configurar(self):
        centro = tk.Frame(self, bg=GRIS_FONDO)
        centro.pack(fill="both", expand=True)
        contenido = tk.Frame(centro, bg=GRIS_FONDO)
        contenido.place(relx=0.5, rely=0.4, anchor="center")

        tk.Label(contenido, text="🤖", font=("Segoe UI", 48), bg=GRIS_FONDO).pack()
        tk.Label(contenido, text=t("ia_no_configurado"),
                 font=("Segoe UI", 13, "bold"), bg=GRIS_FONDO, fg=NEGRO).pack(pady=(8, 4))

        if self.es_admin:
            tk.Label(contenido,
                     text="Conectá una cuenta de OpenAI, Anthropic u otro proveedor compatible\n"
                          "para activar el chat, el análisis de ventas y la generación de\n"
                          "descripciones de productos con IA real.",
                     font=("Segoe UI", 9), bg=GRIS_FONDO, fg=GRIS_TEXTO,
                     justify="center").pack(pady=(0, 16))
            tk.Button(contenido, text=t("ia_configurar_asistente"), font=("Segoe UI", 10, "bold"),
                      bg=AZUL_RIBBON, fg=BLANCO, relief="flat", padx=18, pady=10, cursor="hand2",
                      command=self._abrir_configuracion).pack()
        else:
            tk.Label(contenido,
                     text="Pedile a un Administrador que configure el Asistente IA\n"
                          "desde este mismo módulo, con la clave de API de un proveedor\n"
                          "como OpenAI o Anthropic.",
                     font=("Segoe UI", 9), bg=GRIS_FONDO, fg=GRIS_TEXTO,
                     justify="center").pack()

    # ── Chat ─────────────────────────────────────────────────
    def _construir_chat(self):
        barra_acciones = tk.Frame(self, bg=BLANCO, height=44)
        barra_acciones.pack(fill="x")
        barra_acciones.pack_propagate(False)
        tk.Button(barra_acciones, text=t("ia_analizar_ventas"), font=("Segoe UI", 9, "bold"),
                  bg=BLANCO, fg="#333", relief="solid", bd=1, padx=10, pady=4, cursor="hand2",
                  command=self._analizar_ventas).pack(side="left", padx=(12, 6), pady=7)
        tk.Button(barra_acciones, text=t("ia_generar_descripcion"), font=("Segoe UI", 9, "bold"),
                  bg=BLANCO, fg="#333", relief="solid", bd=1, padx=10, pady=4, cursor="hand2",
                  command=self._generar_descripcion_producto).pack(side="left", padx=6, pady=7)
        tk.Button(barra_acciones, text=t("ia_traducir_texto"), font=("Segoe UI", 9, "bold"),
                  bg=BLANCO, fg="#333", relief="solid", bd=1, padx=10, pady=4, cursor="hand2",
                  command=self._traducir_texto).pack(side="left", padx=6, pady=7)
        tk.Button(barra_acciones, text=t("ia_nueva_conversacion"), font=("Segoe UI", 9), bg=BLANCO,
                  fg="#333", relief="solid", bd=1, padx=10, pady=4, cursor="hand2",
                  command=self._nueva_conversacion).pack(side="right", padx=12, pady=7)

        cuerpo = tk.Frame(self, bg=GRIS_FONDO)
        cuerpo.pack(fill="both", expand=True)
        cuerpo.grid_rowconfigure(0, weight=1)
        cuerpo.grid_columnconfigure(0, weight=1)

        self.canvas_chat = tk.Canvas(cuerpo, bg=GRIS_FONDO, highlightthickness=0)
        self.canvas_chat.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        sb_chat = tk.Scrollbar(cuerpo, orient="vertical", command=self.canvas_chat.yview)
        self.canvas_chat.configure(yscrollcommand=sb_chat.set)
        sb_chat.grid(row=0, column=1, sticky="ns", pady=10)

        self.frame_mensajes = tk.Frame(self.canvas_chat, bg=GRIS_FONDO)
        self._id_ventana_canvas = self.canvas_chat.create_window((0, 0), window=self.frame_mensajes, anchor="nw")
        self.frame_mensajes.bind("<Configure>", lambda e: self.canvas_chat.configure(
            scrollregion=self.canvas_chat.bbox("all")))
        self.canvas_chat.bind("<Configure>", lambda e: self.canvas_chat.itemconfig(
            self._id_ventana_canvas, width=e.width))

        def _rueda(event):
            if event.num == 4:
                self.canvas_chat.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas_chat.yview_scroll(1, "units")
            else:
                self.canvas_chat.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.canvas_chat.bind("<MouseWheel>", _rueda)
        self.canvas_chat.bind("<Button-4>", _rueda)
        self.canvas_chat.bind("<Button-5>", _rueda)

        self._agregar_burbuja(
            "assistant",
            "¡Hola! Soy el Asistente IA de MaquedaSystems. Puedo ayudarte a usar el sistema, "
            "analizar tus ventas, redactar descripciones de productos, o charlar sobre lo que "
            "necesites. ¿En qué te ayudo?",
        )

        # Barra de entrada
        barra_entrada = tk.Frame(self, bg=BLANCO, height=90)
        barra_entrada.pack(fill="x")
        barra_entrada.pack_propagate(False)

        self.texto_entrada = tk.Text(barra_entrada, font=("Segoe UI", 10), height=3,
                                     wrap="word", relief="solid", bd=1, padx=8, pady=6)
        self.texto_entrada.pack(side="left", fill="both", expand=True, padx=(12, 8), pady=12)
        self.texto_entrada.bind("<Return>", self._al_presionar_enter_entrada)
        self.texto_entrada.focus_set()

        self.btn_enviar = tk.Button(barra_entrada, text=t("ia_enviar"), font=("Segoe UI", 9, "bold"),
                                    bg=AZUL_RIBBON, fg=BLANCO, relief="flat", padx=14,
                                    cursor="hand2", command=self._enviar_mensaje)
        self.btn_enviar.pack(side="left", padx=(0, 12), pady=12, fill="y")

        self.label_estado = tk.Label(self, text="", font=("Segoe UI", 8, "italic"),
                                     bg=GRIS_FONDO, fg=GRIS_TEXTO, anchor="w")
        self.label_estado.pack(fill="x", padx=12, pady=(0, 4))

    def _al_presionar_enter_entrada(self, event):
        if event.state & 0x0001:  # Shift+Enter → salto de línea normal
            return
        self._enviar_mensaje()
        return "break"

    def _nueva_conversacion(self):
        if self.esperando_respuesta:
            return
        self.mensajes = [{"role": "system", "content": MENSAJE_SISTEMA}]
        for w in self.frame_mensajes.winfo_children():
            w.destroy()
        self._agregar_burbuja("assistant", "Conversación reiniciada. ¿En qué te ayudo?")

    # ── Burbujas de chat ─────────────────────────────────────
    def _agregar_burbuja(self, rol: str, texto: str):
        es_usuario = (rol == "user")
        fila = tk.Frame(self.frame_mensajes, bg=GRIS_FONDO)
        fila.pack(fill="x", pady=4, anchor="e" if es_usuario else "w")

        color_fondo = BURBUJA_USUARIO if es_usuario else BURBUJA_ASISTENTE
        color_texto = BLANCO if es_usuario else NEGRO
        burbuja = tk.Frame(fila, bg=color_fondo)
        burbuja.pack(side="right" if es_usuario else "left", padx=10)
        tk.Label(burbuja, text=texto, font=("Segoe UI", 10), bg=color_fondo, fg=color_texto,
                 justify="left", wraplength=560, padx=12, pady=8).pack()

        self.after(10, lambda: self.canvas_chat.yview_moveto(1.0))

    # ── Envío de mensajes ────────────────────────────────────
    def _enviar_mensaje(self):
        if self.esperando_respuesta:
            return
        texto = self.texto_entrada.get("1.0", "end").strip()
        if not texto:
            return
        self.texto_entrada.delete("1.0", "end")
        self._agregar_burbuja("user", texto)
        self.mensajes.append({"role": "user", "content": texto})
        self._pedir_respuesta_ia()

    def _pedir_respuesta_ia(self):
        self.esperando_respuesta = True
        self.btn_enviar.config(state="disabled")
        self.label_estado.config(text=t("ia_pensando"))

        config = self.config_ia
        mensajes_a_enviar = list(self.mensajes)

        def _tarea():
            ok, respuesta = enviar_mensaje_ia(mensajes_a_enviar, config)
            self.after(0, lambda: self._al_recibir_respuesta(ok, respuesta))

        threading.Thread(target=_tarea, daemon=True).start()

    def _al_recibir_respuesta(self, ok: bool, respuesta: str):
        if not self.winfo_exists():
            return
        self.esperando_respuesta = False
        self.btn_enviar.config(state="normal")
        self.label_estado.config(text="")
        if ok:
            self.mensajes.append({"role": "assistant", "content": respuesta})
            self._agregar_burbuja("assistant", respuesta)
        else:
            self._agregar_burbuja("assistant", f"⚠ No se pudo obtener una respuesta:\n{respuesta}")

    # ── Acción rápida: analizar ventas ───────────────────────
    def _analizar_ventas(self):
        if self.esperando_respuesta:
            return
        from models_ventas import resumen_financiero_en_rango, productos_mas_vendidos_en_rango
        from auth import filtro_usuario_ventas

        hoy = datetime.date.today()
        desde = (hoy - datetime.timedelta(days=30)).isoformat()
        hasta = hoy.isoformat()
        usuario_id = filtro_usuario_ventas(self.usuario_actual)

        resumen = resumen_financiero_en_rango(desde, hasta, usuario_id=usuario_id)
        top_productos = productos_mas_vendidos_en_rango(desde, hasta, limite=10, usuario_id=usuario_id)

        lineas_productos = "\n".join(
            f"  - {p['nombre']}: {p['cantidad']:g} unidades, {formatear_gs(p['importe'])}"
            for p in top_productos
        ) or "  (sin ventas de productos en el período)"

        prompt = (
            f"Analizá el desempeño de ventas de los últimos 30 días ({desde} a {hasta}) y dame "
            "3 a 5 recomendaciones concretas y accionables para el negocio. Datos:\n\n"
            f"- Cantidad de ventas: {len(resumen['ventas'])}\n"
            f"- Total vendido: {formatear_gs(resumen['ventas_totales'])}\n"
            f"- Ganancia estimada: {formatear_gs(resumen['ganancia'])}\n"
            f"- Ventas en efectivo: {formatear_gs(resumen['ventas_efectivo'])}\n"
            f"- Ventas por transferencia: {formatear_gs(resumen['ventas_transferencia'])}\n\n"
            f"Productos más vendidos:\n{lineas_productos}"
        )
        self._agregar_burbuja("user", "📊 Analizar mis ventas de los últimos 30 días")
        self.mensajes.append({"role": "user", "content": prompt})
        self._pedir_respuesta_ia()

    # ── Acción rápida: generar descripción de producto ───────
    def _generar_descripcion_producto(self):
        if self.esperando_respuesta:
            return
        ventana = tk.Toplevel(self)
        ventana.title("Generar descripción con IA")
        ventana.configure(bg=BLANCO)
        ventana.grab_set()
        ventana.resizable(True, False)

        tk.Label(ventana, text="Contale al Asistente qué producto es\n(nombre, categoría, características, para quién es, etc.):",
                 font=("Segoe UI", 9, "bold"), bg=BLANCO, justify="left").pack(anchor="w", padx=14, pady=(14, 6))
        texto = tk.Text(ventana, font=("Segoe UI", 10), height=4, width=48, wrap="word",
                        relief="solid", bd=1)
        texto.pack(padx=14, fill="x")
        texto.focus_set()

        def _confirmar():
            descripcion_pedido = texto.get("1.0", "end").strip()
            if not descripcion_pedido:
                return
            ventana.destroy()
            prompt = (
                "Redactá una descripción de producto breve (1 a 2 líneas), clara y orientada a "
                "venta, en español, lista para pegar en el campo 'Descripción' del sistema (sin "
                f"comillas ni explicaciones extra alrededor). Datos del producto: {descripcion_pedido}"
            )
            self._agregar_burbuja("user", f"✨ Generar descripción: {descripcion_pedido}")
            self.mensajes.append({"role": "user", "content": prompt})
            self._pedir_respuesta_ia()

        frame_botones = tk.Frame(ventana, bg=BLANCO)
        frame_botones.pack(fill="x", padx=14, pady=12)
        tk.Button(frame_botones, text="✨ Generar", font=("Segoe UI", 9, "bold"),
                  bg=AZUL_RIBBON, fg=BLANCO, relief="flat", padx=14, pady=6, cursor="hand2",
                  command=_confirmar).pack(side="left")
        tk.Button(frame_botones, text=t("cancelar_simple"), font=("Segoe UI", 9), bg=BLANCO,
                  relief="solid", bd=1, padx=14, pady=6, command=ventana.destroy).pack(side="left", padx=8)

    # ── Acción rápida: traducir un texto puntual ─────────────
    def _traducir_texto(self):
        if self.esperando_respuesta:
            return
        idiomas_destino = ["Inglés", "Portugués", "Guaraní", "Francés", "Italiano", "Alemán",
                           "Chino (mandarín)", "Japonés", "Otro (lo escribo yo)"]

        ventana = tk.Toplevel(self)
        ventana.title("Traducir texto con IA")
        ventana.configure(bg=BLANCO)
        ventana.grab_set()
        ventana.resizable(True, False)

        tk.Label(ventana, text="Pegá o escribí el texto a traducir\n"
                               "(por ejemplo, la descripción de un producto, una observación, etc.):",
                 font=("Segoe UI", 9, "bold"), bg=BLANCO, justify="left").pack(anchor="w", padx=14, pady=(14, 6))
        texto = tk.Text(ventana, font=("Segoe UI", 10), height=4, width=48, wrap="word",
                        relief="solid", bd=1)
        texto.pack(padx=14, fill="x")
        texto.focus_set()

        tk.Label(ventana, text="Traducir a:", font=("Segoe UI", 9, "bold"), bg=BLANCO
                 ).pack(anchor="w", padx=14, pady=(12, 2))
        var_idioma = tk.StringVar(value=idiomas_destino[0])
        from tkinter import ttk as _ttk
        combo_idioma = _ttk.Combobox(ventana, textvariable=var_idioma, state="readonly",
                                     values=idiomas_destino, font=("Segoe UI", 9), width=25)
        combo_idioma.pack(anchor="w", padx=14)

        var_idioma_libre = tk.StringVar()
        entry_libre = tk.Entry(ventana, textvariable=var_idioma_libre, font=("Segoe UI", 9), state="disabled")
        entry_libre.pack(anchor="w", padx=14, pady=(6, 0), fill="x")

        def _al_cambiar_idioma(event=None):
            entry_libre.config(state="normal" if var_idioma.get() == "Otro (lo escribo yo)" else "disabled")
        combo_idioma.bind("<<ComboboxSelected>>", _al_cambiar_idioma)

        def _confirmar():
            texto_a_traducir = texto.get("1.0", "end").strip()
            if not texto_a_traducir:
                return
            idioma_destino = (var_idioma_libre.get().strip()
                              if var_idioma.get() == "Otro (lo escribo yo)" else var_idioma.get())
            if not idioma_destino:
                return
            ventana.destroy()
            prompt = (
                f"Traducí el siguiente texto al {idioma_destino}. Respondé ÚNICAMENTE con la "
                "traducción, sin comillas ni explicaciones alrededor, conservando el sentido "
                f"original tal como se usaría en un sistema de gestión de negocio:\n\n{texto_a_traducir}"
            )
            self._agregar_burbuja("user", f"🌐 Traducir a {idioma_destino}: {texto_a_traducir}")
            self.mensajes.append({"role": "user", "content": prompt})
            self._pedir_respuesta_ia()

        frame_botones2 = tk.Frame(ventana, bg=BLANCO)
        frame_botones2.pack(fill="x", padx=14, pady=12)
        tk.Button(frame_botones2, text="🌐 Traducir", font=("Segoe UI", 9, "bold"),
                  bg=AZUL_RIBBON, fg=BLANCO, relief="flat", padx=14, pady=6, cursor="hand2",
                  command=_confirmar).pack(side="left")
        tk.Button(frame_botones2, text=t("cancelar_simple"), font=("Segoe UI", 9), bg=BLANCO,
                  relief="solid", bd=1, padx=14, pady=6, command=ventana.destroy).pack(side="left", padx=8)
