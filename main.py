"""
main.py
Punto de entrada del sistema. Ejecuta este archivo para iniciar la app.

Flujo de inicio:
1. Inicializa la base de datos.
2. Verifica que exista una licencia vigente. Si no, pide activarla
   (obligatorio antes de poder iniciar sesión).
3. Una vez con licencia válida, muestra la ventana de login.
4. Tras el login, abre el dashboard con:
   - Cronómetro de uso en vivo (HH:MM:SS) en la barra superior.
   - Indicador de la licencia activa (días restantes).
   - Botón / atajo para abrir el generador de licencias (admin/admin).
"""
import tkinter as tk
from tkinter import messagebox, ttk
import os
from database import inicializar_bd
from ventana_login import VentanaLogin
from models_licencia import licencia_vigente, descripcion_licencia
from ventana_licencia import (
    VentanaActivarLicencia, VentanaEstadisticasUso,
    _solicitar_credenciales_y_abrir_generador,
)
from models_sesion import (
    iniciar_sesion, heartbeat_sesion, cerrar_sesion,
    tiempo_sesion_actual, formatear_duracion,
)

# Frecuencia (en milisegundos) con la que actualizamos el cronómetro y el heartbeat
INTERVALO_CRONOMETRO_MS = 1000          # refresca el HH:MM:SS cada segundo
INTERVALO_HEARTBEAT_MS = 30_000         # guarda la duración cada 30 segundos


class VentanaPrincipal(tk.Tk):
    """Ventana principal (Dashboard). Incluye el cronómetro en vivo y el
    estado de la licencia en la barra superior."""

    def __init__(self, usuario_actual: dict):
        super().__init__()
        self.usuario_actual = usuario_actual
        self.modulo_activo = None
        self.botones_menu = {}

        # --- Cronómetro y sesión de uso ---
        self.sesion_id = iniciar_sesion(
            usuario_actual.get("id"),
            usuario_actual.get("nombre_completo", usuario_actual.get("usuario", "")),
        )
        self._actualizando_cronometro = True

        from traducciones import t
        self.title(t("app_titulo"))
        self.configure(bg="#eef1f5")

        # ── Escala automática según la resolución de la pantalla ──────
        # Detectar la resolución real ANTES de construir cualquier widget
        self.update_idletasks()
        sh = self.winfo_screenheight()
        sw = self.winfo_screenwidth()

        # Calcular factor de escala: la UI fue diseñada para 768px de alto.
        # En pantallas más pequeñas todo se reduce proporcialmente.
        escala = min(sh / 768, sw / 1280, 1.0)   # nunca agrandar, solo achicar
        escala = max(escala, 0.65)                  # mínimo 65% para legibilidad

        # Tamaños base → ajustados por escala
        self._E = escala          # factor para usar en todo el sistema
        self._fs  = lambda s: max(7, int(s * escala))   # font size
        self._px  = lambda p: max(2, int(p * escala))   # padding/pixels

        # Tamaño de ventana proporcional a la pantalla
        win_w = min(int(1280 * escala), sw - 40)
        win_h = min(int(720  * escala), sh - 60)
        self.geometry(f"{win_w}x{win_h}")
        self.minsize(int(900 * escala), int(480 * escala))

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._construir_barra_superior()
        self._construir_menu_lateral()

        self.frame_contenido = tk.Frame(self, bg="white")
        self.frame_contenido.grid(row=1, column=1, sticky="nsew")

        # Arrancar en el primer módulo accesible para este usuario
        if self._botones_disponibles:
            clave, _, comando = self._botones_disponibles[0]
            self._seleccionar_modulo(clave, comando)
        else:
            self._mostrar_sin_permisos()

        # Iniciar bucles del cronómetro y verificación periódica de licencia
        self._tick_cronometro()
        self._tick_heartbeat()
        self._tick_verificar_licencia()

        # Atajos:
        # - Ctrl+Shift+L → generador de licencias (pide admin/admin)
        # - Ctrl+Shift+U → estadísticas de uso
        self.bind_all("<Control-Shift-L>", lambda e: self._abrir_generador_licencias())
        self.bind_all("<Control-Shift-U>", lambda e: self._abrir_estadisticas())

        # Guardar la sesión al cerrar
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)

    # ---------------- BARRA SUPERIOR ----------------
    def _construir_barra_superior(self):
        fs = self._fs
        px = self._px
        barra_h = px(58)
        self._barra = tk.Frame(self, bg="#1e293b", height=barra_h)
        self._barra.grid(row=0, column=0, columnspan=2, sticky="ew")
        self._barra.grid_propagate(False)

        tk.Label(self._barra, text="🧮", font=("Segoe UI", fs(16)),
                 bg="#1e293b", fg="#60a5fa").pack(
            side="left", padx=(px(20), px(8)), pady=px(12))
        from traducciones import t
        tk.Label(self._barra, text=t("app_titulo"),
                 font=("Segoe UI", fs(13), "bold"),
                 bg="#1e293b", fg="white").pack(side="left", pady=px(12))

        # Cronómetro (clickeable: abre estadísticas)
        marco_cron = tk.Frame(self._barra, bg="#0f172a", cursor="hand2")
        marco_cron.pack(side="left", padx=(px(25), 0), pady=px(12))
        tk.Label(marco_cron, text="⏱", font=("Segoe UI", fs(11)),
                 bg="#0f172a", fg="#60a5fa").pack(side="left", padx=(px(8), px(4)), pady=px(4))
        self.lbl_cronometro = tk.Label(marco_cron, text="00:00:00",
                                        font=("Consolas", fs(11), "bold"),
                                        bg="#0f172a", fg="white", cursor="hand2")
        self.lbl_cronometro.pack(side="left", padx=(0, px(8)), pady=px(4))
        for w in (marco_cron, self.lbl_cronometro):
            w.bind("<Button-1>", lambda e: self._abrir_estadisticas())

        # Etiqueta de licencia (clickeable)
        self.lbl_licencia = tk.Label(self._barra, text=descripcion_licencia(),
                                      font=("Segoe UI", fs(9)),
                                      bg="#1e293b", fg="#94a3b8", cursor="hand2")
        self.lbl_licencia.pack(side="left", padx=(px(15), 0), pady=px(14))
        self.lbl_licencia.bind("<Button-1>", lambda e: self._mostrar_info_licencia())

        # Icono de calculadora (clickeable) — abre la calculadora del sistema.
        # Usa el mismo estilo de "badge" oscuro que el cronómetro, para
        # mantener consistencia visual en la barra superior.
        marco_calc = tk.Frame(self._barra, bg="#0f172a", cursor="hand2")
        marco_calc.pack(side="left", padx=(px(12), 0), pady=px(12))
        lbl_calc_icono = tk.Label(marco_calc, text="🧮", font=("Segoe UI", fs(12)),
                                   bg="#0f172a", fg="#60a5fa", cursor="hand2")
        lbl_calc_icono.pack(side="left", padx=px(10), pady=px(6))

        def _calc_hover_on(_e=None):
            marco_calc.configure(bg="#1e3a5f")
            lbl_calc_icono.configure(bg="#1e3a5f")

        def _calc_hover_off(_e=None):
            marco_calc.configure(bg="#0f172a")
            lbl_calc_icono.configure(bg="#0f172a")

        for w in (marco_calc, lbl_calc_icono):
            w.bind("<Button-1>", lambda e: self._abrir_calculadora())
            w.bind("<Enter>", _calc_hover_on)
            w.bind("<Leave>", _calc_hover_off)

        from traducciones import t
        tk.Button(self._barra, text=t("cerrar_sesion"), font=("Segoe UI", fs(9)),
                  bg="#ef4444", fg="white", relief="flat",
                  padx=px(10), pady=px(4), activebackground="#dc2626",
                  cursor="hand2", command=self._cerrar_sesion).pack(
                      side="right", padx=px(20), pady=px(14))

        # ── Sección de perfil (clickeable → abre popup de perfil) ──
        # Con side="right", el último en packearse queda más a la DERECHA
        # visualmente. Queremos: [avatar] [nombre/rol]  → packeo nombre
        # primero, luego avatar, para que avatar quede más a la derecha.

        # 1) Nombre y rol (queda a la izquierda del avatar)
        self._frame_usuario_info = tk.Frame(self._barra, bg="#1e293b", cursor="hand2")
        self._frame_usuario_info.pack(side="right", padx=(0, 6), pady=10)
        self._lbl_nombre_usuario = tk.Label(
            self._frame_usuario_info,
            text=self.usuario_actual["nombre_completo"],
            font=("Segoe UI", 10, "bold"), bg="#1e293b", fg="white",
            cursor="hand2")
        self._lbl_nombre_usuario.pack(anchor="e")
        from traducciones import t as _t_rol
        self._lbl_rol_usuario = tk.Label(
            self._frame_usuario_info,
            text=_t_rol(self.usuario_actual["rol"]) if self.usuario_actual["rol"] in ("admin", "gerente", "vendedor")
                 else self.usuario_actual["rol"].capitalize(),
            font=("Segoe UI", 8), bg="#1e293b", fg="#94a3b8", cursor="hand2")
        self._lbl_rol_usuario.pack(anchor="e")

        # 2) Avatar (queda a la derecha del nombre, justo antes de "Cerrar sesión")
        self._frame_avatar = tk.Frame(self._barra, bg="#1e293b", cursor="hand2")
        self._frame_avatar.pack(side="right", padx=(0, 4), pady=10)

        # Bindings — se usan lambdas sin argumento para evitar que el
        # event de Tkinter tape el método (bug clásico con bind + lambda)
        self._frame_avatar.bind("<Button-1>",
                                lambda e: self._abrir_editar_perfil(pestana=2))
        self._frame_usuario_info.bind("<Button-1>",
                                      lambda e: self._abrir_editar_perfil(pestana=0))
        self._lbl_nombre_usuario.bind("<Button-1>",
                                      lambda e: self._abrir_editar_perfil(pestana=0))
        self._lbl_rol_usuario.bind("<Button-1>",
                                   lambda e: self._abrir_editar_perfil(pestana=0))

        self._actualizar_avatar()

    def _actualizar_avatar(self):
        """Destruye y recrea el widget de avatar con la foto actual del usuario."""
        for w in self._frame_avatar.winfo_children():
            w.destroy()

        foto_ruta = self.usuario_actual.get("foto_ruta", "")
        foto_tk   = None

        if foto_ruta:
            try:
                from PIL import Image, ImageTk, ImageDraw
                if os.path.exists(foto_ruta):
                    tam = 38
                    img = Image.open(foto_ruta).convert("RGBA")
                    w_i, h_i = img.size
                    lado = min(w_i, h_i)
                    img  = img.crop(((w_i - lado) // 2, (h_i - lado) // 2,
                                     (w_i + lado) // 2, (h_i + lado) // 2))
                    img  = img.resize((tam, tam), Image.LANCZOS)
                    mask = Image.new("L", (tam, tam), 0)
                    ImageDraw.Draw(mask).ellipse((0, 0, tam, tam), fill=255)
                    res  = Image.new("RGBA", (tam, tam), (0, 0, 0, 0))
                    res.paste(img, mask=mask)
                    foto_tk = ImageTk.PhotoImage(res)
            except Exception:
                foto_tk = None

        if foto_tk:
            lbl = tk.Label(self._frame_avatar, image=foto_tk,
                           bg="#1e293b", borderwidth=0, cursor="hand2")
            lbl.image = foto_tk   # evitar GC
            lbl.pack()
            lbl.bind("<Button-1>", lambda e: self._abrir_editar_perfil(pestana=2))
        else:
            iniciales = "".join(p[0].upper()
                                for p in self.usuario_actual["nombre_completo"].split()[:2])
            canvas = tk.Canvas(self._frame_avatar, width=38, height=38,
                               bg="#1e293b", highlightthickness=0, cursor="hand2")
            canvas.pack()
            canvas.create_oval(1, 1, 37, 37,
                               fill="#1d5fd6", outline="#3b82f6", width=2)
            canvas.create_text(19, 19, text=iniciales,
                               font=("Segoe UI", 13, "bold"), fill="white")
            canvas.bind("<Button-1>", lambda e: self._abrir_editar_perfil(pestana=2))


    def _abrir_editar_perfil(self, pestana=0):
        """Muestra un popup de perfil con opciones:
        - Click en nombre → popup con info + botones Editar y Cambiar foto
        - Click en avatar → abre directo la pestaña de foto"""
        if pestana == 2:
            # Click en el avatar → abrir directo pestaña foto
            self._abrir_formulario_perfil(pestana=2)
        else:
            # Click en el nombre → mostrar popup de información
            self._mostrar_popup_perfil()

    def _mostrar_popup_perfil(self):
        """Popup tipo card con la info del usuario y botones de acción."""
        # Si ya hay uno abierto, cerrarlo
        if hasattr(self, "_popup_win") and self._popup_win and \
                self._popup_win.winfo_exists():
            self._popup_win.destroy()
            return

        popup = tk.Toplevel(self)
        self._popup_win = popup
        popup.overrideredirect(True)   # sin borde del SO
        popup.configure(bg="white")
        popup.attributes("-topmost", True)

        # Posicionar debajo del avatar en la barra superior
        bx = self._frame_avatar.winfo_rootx()
        by = self._frame_avatar.winfo_rooty() + self._frame_avatar.winfo_height() + 4
        popup.geometry(f"250x{10}+{bx - 160}+{by}")

        # Borde con sombra simulada
        outer = tk.Frame(popup, bg="#e2e8f0", padx=1, pady=1)
        outer.pack(fill="both", expand=True)
        inner = tk.Frame(outer, bg="white", padx=16, pady=14)
        inner.pack(fill="both", expand=True)

        # Avatar grande
        foto_ruta = self.usuario_actual.get("foto_ruta", "")
        foto_tk = None
        try:
            from PIL import Image, ImageTk, ImageDraw
            if foto_ruta and os.path.exists(foto_ruta):
                tam = 64
                img = Image.open(foto_ruta).convert("RGBA")
                w_i, h_i = img.size
                lado = min(w_i, h_i)
                img  = img.crop(((w_i-lado)//2, (h_i-lado)//2,
                                  (w_i+lado)//2, (h_i+lado)//2))
                img  = img.resize((tam, tam), Image.LANCZOS)
                mask = Image.new("L", (tam, tam), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, tam, tam), fill=255)
                res  = Image.new("RGBA", (tam, tam), (0, 0, 0, 0))
                res.paste(img, mask=mask)
                foto_tk = ImageTk.PhotoImage(res)
        except Exception:
            foto_tk = None

        if foto_tk:
            lbl_av = tk.Label(inner, image=foto_tk, bg="white",
                              cursor="hand2")
            lbl_av.image = foto_tk
            lbl_av.pack(pady=(0, 6))
            lbl_av.bind("<Button-1>", lambda e: (
                popup.destroy(), self._abrir_formulario_perfil(pestana=2)))
        else:
            iniciales = "".join(p[0].upper() for p in
                                self.usuario_actual["nombre_completo"].split()[:2])
            cv = tk.Canvas(inner, width=64, height=64, bg="white",
                           highlightthickness=0, cursor="hand2")
            cv.pack(pady=(0, 6))
            cv.create_oval(2, 2, 62, 62, fill="#1d5fd6",
                           outline="#3b82f6", width=2)
            cv.create_text(32, 32, text=iniciales,
                           font=("Segoe UI", 20, "bold"), fill="white")
            cv.bind("<Button-1>", lambda e: (
                popup.destroy(), self._abrir_formulario_perfil(pestana=2)))

        # Info del usuario
        tk.Label(inner, text=self.usuario_actual["nombre_completo"],
                 font=("Segoe UI", 11, "bold"), bg="white",
                 fg="#1e293b").pack()
        tk.Label(inner, text=f"@{self.usuario_actual['usuario']}",
                 font=("Segoe UI", 9), bg="white",
                 fg="#6b7280").pack(pady=(0, 8))

        sep = tk.Frame(inner, bg="#e2e8f0", height=1)
        sep.pack(fill="x", pady=(0, 8))

        # Rol
        from traducciones import t as _t_rol2
        roles = {"admin": (_t_rol2("admin"), "#1d5fd6"),
                 "gerente": (_t_rol2("gerente"), "#7c3aed"),
                 "vendedor": (_t_rol2("vendedor"), "#16a34a")}
        rol_txt, rol_color = roles.get(
            self.usuario_actual.get("rol", "vendedor"),
            ("Usuario", "#6b7280"))
        tk.Label(inner, text=f"🔑  {rol_txt}",
                 font=("Segoe UI", 9), bg="white",
                 fg=rol_color).pack(anchor="w")
        tk.Label(inner, text="✔  Activo",
                 font=("Segoe UI", 9), bg="white",
                 fg="#16a34a").pack(anchor="w", pady=(2, 8))

        sep2 = tk.Frame(inner, bg="#e2e8f0", height=1)
        sep2.pack(fill="x", pady=(0, 8))

        # Botones en columna para que no se corten
        tk.Button(inner, text="✏  Editar perfil",
                  font=("Segoe UI", 9), bg="#1d5fd6", fg="white",
                  relief="flat", padx=10, pady=6, cursor="hand2",
                  command=lambda: (popup.destroy(),
                                   self._abrir_formulario_perfil(pestana=0))
                  ).pack(fill="x", pady=(0, 4))

        tk.Button(inner, text="📷  Cambiar foto de perfil",
                  font=("Segoe UI", 9), bg="#f3f4f6", fg="#1e293b",
                  relief="flat", padx=10, pady=6, cursor="hand2",
                  command=lambda: (popup.destroy(),
                                   self._abrir_formulario_perfil(pestana=2))
                  ).pack(fill="x")

        # Ajustar altura real después de construir el contenido
        popup.update_idletasks()
        h = inner.winfo_reqheight() + 30
        popup.geometry(f"250x{h}+{bx - 160}+{by}")

        # Cerrar al hacer click fuera
        popup.bind("<FocusOut>", lambda e: popup.destroy()
                   if popup.winfo_exists() else None)
        popup.focus_set()

    def _abrir_formulario_perfil(self, pestana=0):
        """Abre el formulario de edición del usuario logueado.

        Se abre en modo_autoedicion=True: un usuario editando su propio
        perfil NUNCA debe poder verse ni otorgarse a sí mismo un rol
        distinto ni permisos de módulos — eso es exclusivo de un
        Administrador desde el módulo Usuarios. Ver VentanaFormularioUsuario.
        """
        from auth import obtener_usuario
        from ventana_usuarios import VentanaFormularioUsuario
        datos = obtener_usuario(self.usuario_actual["id"]) or self.usuario_actual
        VentanaFormularioUsuario(
            self, datos,
            # on_guardado se llama SIEMPRE sin argumentos (uso genérico,
            # p. ej. refrescar una lista) — acá no hace falta nada extra,
            # así que va un no-op. El refresco real de la barra superior
            # (nombre, foto, rol) lo hace on_usuario_guardado, que sí
            # recibe el ID y se llama solo cuando corresponde.
            on_guardado=lambda: None,
            on_usuario_guardado=self._on_usuario_guardado,
            pestana_inicial=pestana,
            modo_autoedicion=True,
        )

    def _on_usuario_guardado(self, usuario_id: int):
        """Llamado desde PanelUsuarios cada vez que se guarda un usuario.
        Si el ID coincide con el usuario logueado, recarga su foto y nombre."""
        if usuario_id != self.usuario_actual.get("id"):
            return
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        from auth import obtener_usuario
        datos_frescos = obtener_usuario(usuario_id)
        if not datos_frescos:
            return
        # Actualizar el dict en memoria
        self.usuario_actual["foto_ruta"]        = datos_frescos.get("foto_ruta", "")
        self.usuario_actual["nombre_completo"]  = datos_frescos["nombre_completo"]
        self.usuario_actual["rol"]              = datos_frescos.get("rol", self.usuario_actual["rol"])
        # Refrescar widgets
        self._lbl_nombre_usuario.config(text=self.usuario_actual["nombre_completo"])
        from traducciones import t as _t_rol3
        _rol_actual = self.usuario_actual["rol"]
        self._lbl_rol_usuario.config(
            text=_t_rol3(_rol_actual) if _rol_actual in ("admin", "gerente", "vendedor") else _rol_actual.capitalize())
        self._actualizar_avatar()

    def _construir_menu_lateral(self):
        fs = self._fs   # función de escala de fuente
        px = self._px   # función de escala de pixels
        menu_w = px(185)

        menu_frame = tk.Frame(self, bg="#1e293b", width=menu_w)
        menu_frame.grid(row=1, column=0, sticky="ns")
        menu_frame.pack_propagate(False)

        tk.Frame(menu_frame, bg="#334155", height=1).pack(fill="x")

        # ── Contenedor con scroll: si la pantalla es baja o hay muchos
        # módulos asignados, el sidebar deja de "cortar" los últimos
        # botones y en cambio permite desplazarse para llegar a todos
        # ellos, con una barra fina que combina con el tema oscuro (en
        # vez de la barra gris gruesa por defecto). ──
        estilo = ttk.Style()
        estilo.theme_use(estilo.theme_use())  # conserva el theme activo
        estilo.configure("Sidebar.Vertical.TScrollbar", background="#475569",
                         troughcolor="#1e293b", bordercolor="#1e293b",
                         arrowcolor="#1e293b", relief="flat", arrowsize=1)
        estilo.map("Sidebar.Vertical.TScrollbar", background=[("active", "#64748b")])

        canvas_menu = tk.Canvas(menu_frame, bg="#1e293b", highlightthickness=0, bd=0, width=1)
        scrollbar_menu = ttk.Scrollbar(menu_frame, orient="vertical", command=canvas_menu.yview,
                                       style="Sidebar.Vertical.TScrollbar")
        canvas_menu.configure(yscrollcommand=scrollbar_menu.set)
        canvas_menu.pack(side="left", fill="both", expand=True)

        menu = tk.Frame(canvas_menu, bg="#1e293b")
        ventana_id = canvas_menu.create_window((0, 0), window=menu, anchor="nw")

        def _actualizar_scroll(event=None):
            # La scrollbar (fina, 6px) solo se muestra si el contenido no entra completo
            necesita_scroll = menu.winfo_reqheight() > canvas_menu.winfo_height()
            if necesita_scroll and not scrollbar_menu.winfo_ismapped():
                scrollbar_menu.pack(side="right", fill="y")
            elif not necesita_scroll and scrollbar_menu.winfo_ismapped():
                scrollbar_menu.pack_forget()

            # Mostrar/ocultar la scrollbar cambia el ancho disponible del
            # canvas; forzamos que Tk recalcule la geometría YA (en vez de
            # esperar al próximo <Configure>) para que el contenido interno
            # siempre ocupe el ancho real y no quede espacio muerto a la derecha.
            canvas_menu.update_idletasks()
            ancho_real = canvas_menu.winfo_width()
            canvas_menu.itemconfig(ventana_id, width=ancho_real)
            canvas_menu.configure(scrollregion=canvas_menu.bbox("all"))

        menu.bind("<Configure>", _actualizar_scroll)
        canvas_menu.bind("<Configure>", _actualizar_scroll)
        menu_frame.bind("<Configure>", _actualizar_scroll)

        # ---- Scroll con rueda de mouse / touchpad, en TODO el ancho del
        # sidebar (tanto sobre los botones a la izquierda como sobre la
        # franja derecha donde vive la scrollbar) ----
        def _con_scroll_del_mouse(event):
            delta = event.delta
            if delta == 0:
                delta = -1 if getattr(event, "num", None) == 5 else 1
            else:
                delta = int(-1 * (delta / 120)) if abs(delta) >= 120 else -1 * delta
            canvas_menu.yview_scroll(delta, "units")

        def _activar_scroll_mouse(event=None):
            canvas_menu.bind_all("<MouseWheel>", _con_scroll_del_mouse)
            canvas_menu.bind_all("<Button-4>", _con_scroll_del_mouse)
            canvas_menu.bind_all("<Button-5>", _con_scroll_del_mouse)

        def _desactivar_scroll_mouse(event=None):
            canvas_menu.unbind_all("<MouseWheel>")
            canvas_menu.unbind_all("<Button-4>")
            canvas_menu.unbind_all("<Button-5>")

        # Se activa/desactiva al entrar o salir de TODO el sidebar
        # (menu_frame), no solo del canvas, para que también funcione
        # sobre la franja de la scrollbar a la derecha.
        menu_frame.bind("<Enter>", _activar_scroll_mouse)
        menu_frame.bind("<Leave>", _desactivar_scroll_mouse)

        # ---- Arrastrar con el mouse/touchpad para desplazarse, igual que
        # en una pantalla táctil: click y arrastre vertical en cualquier
        # borde (izquierdo o derecho) de cada módulo ----
        self._arrastre_menu = {"y_inicial": None, "top_inicial": 0.0}

        def _iniciar_arrastre(event):
            self._arrastre_menu["y_inicial"] = event.y_root
            self._arrastre_menu["top_inicial"] = canvas_menu.yview()[0]

        def _arrastrar(event):
            if self._arrastre_menu["y_inicial"] is None:
                return
            total = menu.winfo_reqheight()
            visible = canvas_menu.winfo_height()
            if total <= visible:
                return
            delta_px = event.y_root - self._arrastre_menu["y_inicial"]
            delta_fraccion = -delta_px / total
            nuevo_top = max(0.0, min(1.0, self._arrastre_menu["top_inicial"] + delta_fraccion))
            canvas_menu.yview_moveto(nuevo_top)

        self._registrar_arrastre_sidebar = lambda widget: (
            widget.bind("<ButtonPress-1>", _iniciar_arrastre),
            widget.bind("<B1-Motion>", _arrastrar),
        )
        self._registrar_arrastre_sidebar(canvas_menu)

        from traducciones import t
        todos_los_botones = [
            ("ventas",       f"\U0001f9fe  {t('modulo_ventas')}",              self._mostrar_ventas),
            ("preventa",     f"\U0001f552  {t('modulo_preventa')}",           self._mostrar_preventa),
            ("creditos",     f"\U0001f4b3  {t('modulo_creditos')}",            self._mostrar_creditos),
            ("prestamos",    f"\U0001f3e6  {t('modulo_prestamos')}",           self._mostrar_prestamos),
            ("presupuestos", f"\U0001f4dd  {t('modulo_presupuestos')}",        self._mostrar_presupuestos),
            ("productos",    f"\U0001f4e6  {t('modulo_productos')}",           self._mostrar_productos),
            ("inventario",   f"\U0001f4cb  {t('modulo_inventario')}",          self._mostrar_inventario),
            ("compras",      f"\U0001f6d2  {t('modulo_compras')}",             self._mostrar_compras),
            ("importacion",  f"\U0001f4e6  {t('modulo_importacion')}",        self._mostrar_importacion),
            ("asistencia",   f"\U0001f5a5  {t('modulo_asistencia')}",  self._mostrar_asistencia),
            ("veterinaria",  f"\U0001f43e  {t('modulo_veterinaria')}",         self._mostrar_veterinaria),
            ("restaurante",  f"\U0001f37d  {t('modulo_restaurante')}",  self._mostrar_restaurante),
            ("streaming",    f"\U0001f4fa  {t('modulo_streaming')}", self._mostrar_streaming),
            ("clientes",     f"\U0001f465  {t('modulo_clientes')}",            self._mostrar_clientes),
            ("reportes",     f"\U0001f4ca  {t('modulo_reportes')}",            self._mostrar_reportes),
            ("cotizaciones", f"\U0001f4b1  {t('modulo_cotizaciones')}",        self._mostrar_cotizaciones),
            ("clima",        f"\u26c5  {t('modulo_clima')}",                   self._mostrar_clima),
            ("usuarios",     f"\u2699  {t('modulo_usuarios')}",                self._mostrar_usuarios),
            ("rrhh",         f"\U0001f9d1\u200d\U0001f4bc  {t('modulo_rrhh')}",   self._mostrar_rrhh),
            ("configlocal",  f"\U0001f3ea  {t('modulo_configlocal')}",       self._mostrar_config_local),
            ("licencia",     f"\U0001f511  {t('modulo_licencia')}",           self._abrir_generador_licencias),
            ("uso",          f"\u23f1  {t('modulo_uso')}",         self._abrir_estadisticas),
            ("datos",        f"\U0001f4be  {t('modulo_datos')}",    self._mostrar_datos),
            ("terminal",     f"\u2328  {t('modulo_terminal')}",             self._mostrar_terminal_sql),
            ("ia",           f"\U0001f916  {t('modulo_ia')}",         self._mostrar_ia),
            ("idioma",       f"\U0001f310  {t('modulo_idioma')}",         self._mostrar_idioma),
            ("juegos",       f"\U0001f3ae  {t('modulo_juegos')}",        self._mostrar_juegos),
            ("biblia",       f"\U0001f4d6  {t('modulo_biblia')}",        self._mostrar_biblia),
            ("novedades",    f"\U0001f195  {t('modulo_novedades')}",           self._mostrar_novedades),
            ("ayuda",        f"\u2753  {t('modulo_ayuda')}",                    self._mostrar_ayuda),
            ("reinicio",     f"\u267b  {t('modulo_reinicio')}",    self._mostrar_reinicio),
        ]

        from auth import usuario_tiene_acceso
        self._botones_disponibles = [
            (clave, texto, comando) for clave, texto, comando in todos_los_botones
            if usuario_tiene_acceso(self.usuario_actual, clave)
        ]

        for clave, texto, comando in self._botones_disponibles:
            self._crear_boton_menu(menu, clave, texto, comando)

        if not self._botones_disponibles:
            tk.Label(menu, text="Sin módulos\nasignados",
                     font=("Segoe UI", fs(10), "italic"),
                     bg="#1e293b", fg="#94a3b8", justify="center").pack(pady=20)

        # ── Ajustar el ancho del sidebar al texto real más largo entre los
        # módulos que este usuario en particular tiene asignados, en vez de
        # dejar un ancho fijo genérico que sobra cuando hay ítems cortos. ──
        if self.botones_menu:
            self.update_idletasks()
            ancho_maximo_texto = max(boton.winfo_reqwidth() for boton, _ in self.botones_menu.values())
            ancho_ideal = ancho_maximo_texto + px(4) + px(6) + 16  # + indicador + borde + margen scrollbar
            ancho_ideal = max(px(150), min(ancho_ideal, px(260)))
            menu_frame.config(width=ancho_ideal)
            _actualizar_scroll()

    def _crear_boton_menu(self, menu, clave, texto, comando):
        fs = self._fs
        px = self._px
        fila = tk.Frame(menu, bg="#1e293b")
        fila.pack(fill="x")
        indicador = tk.Frame(fila, bg="#1e293b", width=4)
        indicador.pack(side="left", fill="y")
        boton = tk.Button(fila, text=texto, font=("Segoe UI", fs(10)),
                          bg="#1e293b", fg="#cbd5e1", bd=0, anchor="w",
                          padx=px(14), pady=px(7), activebackground="#334155",
                          activeforeground="white", cursor="hand2",
                          command=lambda c=clave, cmd=comando:
                              self._seleccionar_modulo(c, cmd))
        boton.pack(side="left", fill="x", expand=True)
        borde_derecho = tk.Frame(fila, bg="#1e293b", width=6)
        borde_derecho.pack(side="right", fill="y")

        # Permite arrastrar con el mouse/touchpad para desplazar el menú,
        # tomando como "asa" los bordes izquierdo y derecho de cada fila
        # (sin interferir con el click normal sobre el botón).
        self._registrar_arrastre_sidebar(indicador)
        self._registrar_arrastre_sidebar(borde_derecho)
        self._registrar_arrastre_sidebar(fila)

        self.botones_menu[clave] = (boton, indicador)

    def _seleccionar_modulo(self, clave, comando):
        fs = self._fs
        self.modulo_activo = clave
        for k, (boton, indicador) in self.botones_menu.items():
            if k == clave:
                boton.config(bg="#334155", fg="white", font=("Segoe UI", fs(10), "bold"))
                indicador.config(bg="#3b82f6")
            else:
                boton.config(bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", fs(10)))
                indicador.config(bg="#1e293b")
        comando()

    def _limpiar_contenido(self):
        """Destruye todos los paneles del área de contenido, excepto el panel
        de Ventas que se preserva en memoria (solo se oculta) para no perder
        las pestañas y artículos cargados al navegar a otros módulos."""
        panel_ventas = getattr(self, "_panel_ventas", None)
        for widget in self.frame_contenido.winfo_children():
            if panel_ventas and widget is panel_ventas:
                widget.pack_forget()   # solo ocultar, no destruir
            else:
                widget.destroy()

    def _mostrar_bienvenida(self):
        self._limpiar_contenido()
        tk.Label(self.frame_contenido, text=f"¡Bienvenido, {self.usuario_actual['nombre_completo']}!",
                 font=("Segoe UI", 16, "bold"), bg="white").pack(pady=30)

    def _mostrar_productos(self):
        self._limpiar_contenido()
        from ventana_productos import PanelProductos
        panel = PanelProductos(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_inventario(self):
        self._limpiar_contenido()
        from ventana_inventario import PanelInventario
        panel = PanelInventario(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_clientes(self):
        self._limpiar_contenido()
        from ventana_clientes import PanelClientes
        panel = PanelClientes(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_compras(self):
        self._limpiar_contenido()
        from ventana_compras import PanelCompras
        panel = PanelCompras(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_importacion(self):
        self._limpiar_contenido()
        from ventana_importacion import PanelImportacion
        panel = PanelImportacion(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_asistencia(self):
        self._limpiar_contenido()
        from ventana_asistencia import PanelAsistenciaTecnica
        panel = PanelAsistenciaTecnica(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_veterinaria(self):
        self._limpiar_contenido()
        from ventana_veterinaria import PanelVeterinaria
        panel = PanelVeterinaria(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_restaurante(self):
        self._limpiar_contenido()
        from ventana_restaurante import PanelRestaurante
        panel = PanelRestaurante(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_streaming(self):
        self._limpiar_contenido()
        from ventana_streaming import PanelStreaming
        panel = PanelStreaming(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_preventa(self):
        self._limpiar_contenido()
        from ventana_preventa import PanelPreVenta
        panel = PanelPreVenta(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_creditos(self):
        self._limpiar_contenido()
        from ventana_creditos import PanelCreditos
        panel = PanelCreditos(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_prestamos(self):
        self._limpiar_contenido()
        from ventana_prestamos import PanelPrestamos
        panel = PanelPrestamos(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_presupuestos(self):
        self._limpiar_contenido()
        from ventana_presupuestos import PanelPresupuestos
        panel = PanelPresupuestos(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_ventas(self):
        """Muestra el panel de Ventas. Si ya fue creado antes, simplemente
        lo vuelve a mostrar (pack) sin recrearlo, preservando todas las
        pestañas abiertas y los artículos cargados en cada venta."""
        self._limpiar_contenido()
        from ventana_ventas import PanelVentasConPestanas
        if not hasattr(self, "_panel_ventas") or not self._panel_ventas.winfo_exists():
            self._panel_ventas = PanelVentasConPestanas(
                self.frame_contenido, self.usuario_actual)
        self._panel_ventas.pack(fill="both", expand=True)

    def _mostrar_reportes(self):
        self._limpiar_contenido()
        from ventana_reportes import PanelReportes
        panel = PanelReportes(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_rrhh(self):
        self._limpiar_contenido()
        from ventana_rrhh import PanelRRHH
        panel = PanelRRHH(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_config_local(self):
        self._limpiar_contenido()
        from ventana_configuracion_local import PanelConfigLocal
        panel = PanelConfigLocal(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_cotizaciones(self):
        self._limpiar_contenido()
        from ventana_cotizaciones import PanelCotizaciones
        panel = PanelCotizaciones(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_clima(self):
        self._limpiar_contenido()
        from ventana_clima import PanelClima
        panel = PanelClima(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_usuarios(self):
        self._limpiar_contenido()
        from ventana_usuarios import PanelUsuarios
        panel = PanelUsuarios(self.frame_contenido, self.usuario_actual,
                              on_usuario_guardado=self._on_usuario_guardado)
        panel.pack(fill="both", expand=True)

    def _mostrar_datos(self):
        self._limpiar_contenido()
        from ventana_datos import PanelDatos
        panel = PanelDatos(
            self.frame_contenido, self.usuario_actual,
            on_reiniciar_sesion=lambda: self._al_cerrar(volver_a_login=True),
        )
        panel.pack(fill="both", expand=True)

    def _mostrar_terminal_sql(self):
        self._limpiar_contenido()
        from ventana_terminal_sql import PanelTerminalSQL
        panel = PanelTerminalSQL(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_ia(self):
        self._limpiar_contenido()
        from ventana_ia import PanelAsistenteIA
        panel = PanelAsistenteIA(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_idioma(self):
        self._limpiar_contenido()
        from ventana_idioma import PanelIdioma
        panel = PanelIdioma(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_juegos(self):
        self._limpiar_contenido()
        from ventana_juegos import PanelJuegos
        panel = PanelJuegos(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_biblia(self):
        self._limpiar_contenido()
        from ventana_biblia import PanelBiblia
        panel = PanelBiblia(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_reinicio(self):
        self._limpiar_contenido()
        from ventana_reinicio_sistema import PanelReinicioSistema
        panel = PanelReinicioSistema(
            self.frame_contenido, self.usuario_actual,
            on_reinicio_total=lambda: self._al_cerrar(volver_a_login=True),
        )
        panel.pack(fill="both", expand=True)

    def _mostrar_ayuda(self):
        self._limpiar_contenido()
        from ventana_ayuda import PanelAyuda
        panel = PanelAyuda(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_novedades(self):
        self._limpiar_contenido()
        from ventana_novedades import PanelNovedades
        panel = PanelNovedades(self.frame_contenido, self.usuario_actual)
        panel.pack(fill="both", expand=True)

    def _mostrar_sin_permisos(self):
        self._limpiar_contenido()
        tk.Label(self.frame_contenido,
                 text="⚠ No tenés módulos asignados",
                 font=("Segoe UI", 16, "bold"), bg="white",
                 fg="#dc2626").pack(pady=(60, 10))
        tk.Label(self.frame_contenido,
                 text="Tu cuenta no tiene acceso a ningún módulo todavía.\n"
                      "Pedile a un administrador que te asigne permisos.",
                 font=("Segoe UI", 11), bg="white",
                 fg="#6b7280", justify="center").pack()

    # ---------------- LICENCIA ----------------
    def _abrir_generador_licencias(self):
        """Abre el generador, pidiendo siempre credenciales admin/admin."""
        _solicitar_credenciales_y_abrir_generador(self)

    def _mostrar_info_licencia(self):
        from models_licencia import obtener_licencia_activa, tiempo_restante_legible
        lic = obtener_licencia_activa()
        if not lic:
            messagebox.showinfo("Licencia", "No hay licencia activa.", parent=self)
            return
        if lic["duracion_unidad"] == "ilimitado":
            tiempo_info = "Tiempo restante: Permanente / Ilimitada ∞"
            venc_info = "Vence: Nunca"
        else:
            tiempo_info = f"Tiempo restante: {tiempo_restante_legible()}"
            venc_info = f"Vence: {lic['fecha_vencimiento']}"
        messagebox.showinfo(
            "Información de licencia",
            f"Duración: {lic['duracion_legible']}\n"
            f"Activada: {lic['fecha_activacion']}\n"
            f"{venc_info}\n"
            f"{tiempo_info}\n"
            f"Serial: {lic['serial']}",
            parent=self,
        )

    def _abrir_estadisticas(self):
        tiempo_actual = tiempo_sesion_actual(self.sesion_id)
        VentanaEstadisticasUso(self, self.usuario_actual, tiempo_actual)

    def _abrir_calculadora(self):
        from ventana_calculadora import abrir_calculadora
        abrir_calculadora(self)

    # ---------------- CRONÓMETRO ----------------
    def _tick_cronometro(self):
        if not self._actualizando_cronometro:
            return
        try:
            if not self.winfo_exists():
                return
            segundos = tiempo_sesion_actual(self.sesion_id)
            self.lbl_cronometro.config(text=formatear_duracion(segundos))
            self.after(INTERVALO_CRONOMETRO_MS, self._tick_cronometro)
        except tk.TclError:
            pass  # ventana destruida durante el tick

    def _tick_heartbeat(self):
        if not self._actualizando_cronometro or not self.winfo_exists():
            return
        heartbeat_sesion(self.sesion_id)
        self.after(INTERVALO_HEARTBEAT_MS, self._tick_heartbeat)

    def _tick_verificar_licencia(self):
        """Cada minuto verifica que la licencia siga vigente. Si venció,
        cierra la sesión y vuelve a pedir activación."""
        if not self.winfo_exists():
            return
        if not licencia_vigente():
            self._actualizando_cronometro = False
            cerrar_sesion(self.sesion_id)
            messagebox.showwarning(
                "Licencia vencida",
                "La licencia del sistema acaba de vencer.\n\n"
                "Tenés que activar una nueva licencia para seguir usando el sistema.",
                parent=self,
            )
            self.destroy()
            # Programamos el reinicio para que se ejecute después de que
            # esta Tk termine su mainloop. No llamamos a iniciar_app directamente
            # porque crearía un mainloop dentro de otro.
            import threading
            threading.Timer(0.5, iniciar_app).start()
            return
        try:
            self.lbl_licencia.config(text=descripcion_licencia())
        except tk.TclError:
            return
        self.after(60_000, self._tick_verificar_licencia)

    # ---------------- CIERRE ----------------
    def _cerrar_sesion(self):
        from traducciones import t
        if messagebox.askyesno(t("confirmar_cerrar_sesion_titulo"), t("confirmar_cerrar_sesion_texto")):
            self._al_cerrar(volver_a_login=True)

    def _al_cerrar(self, volver_a_login=False):
        self._actualizando_cronometro = False
        cerrar_sesion(self.sesion_id)
        self.destroy()
        if volver_a_login:
            iniciar_login()


# ============================================================
# ARRANQUE DEL SISTEMA
# ============================================================
def abrir_ventana_principal(usuario_actual: dict):
    app = VentanaPrincipal(usuario_actual)
    app.mainloop()


def iniciar_login():
    VentanaLogin(on_login_exitoso=abrir_ventana_principal).mainloop()


def iniciar_app():
    """Arranque completo: BD → check de licencia → login."""
    inicializar_bd()

    if licencia_vigente():
        iniciar_login()
        return

    # Sin licencia válida → ventana raíz obligatoria de activación.
    VentanaActivarLicencia(on_activada=iniciar_login).mainloop()


if __name__ == "__main__":
    iniciar_app()
