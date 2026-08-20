"""
ventana_login.py
Ventana de inicio de sesión con el estilo de marca MAQUEDASYSTEMS:
panel izquierdo blanco con logo, panel derecho azul con el formulario.
Si no existe ningún administrador todavía (primera vez que se usa el
sistema), obliga a crear el admin principal antes de poder ingresar.

Usa la barra de título NATIVA del sistema operativo (con sus botones de
minimizar, maximizar y cerrar reales) y un layout responsive con grid,
para que la ventana se pueda redimensionar o maximizar sin que el
contenido quede cortado o desproporcionado.
"""
import tkinter as tk
from tkinter import messagebox
import math
import os
from auth import login, crear_usuario, existe_algun_admin
from utilidades_ui import obtener_carpeta_assets

try:
    from PIL import Image, ImageTk
    PIL_DISPONIBLE = True
except ImportError:
    PIL_DISPONIBLE = False

# Paleta de colores de la marca
AZUL_PRINCIPAL = "#1d5fd6"
AZUL_OSCURO    = "#163d8c"
AZUL_BOTON     = "#16235c"
BLANCO         = "#ffffff"
GRIS_TEXTO     = "#7a8aa3"
GRIS_BARRA     = "#f4f5f7"


class VentanaLogin(tk.Tk):
    def __init__(self, on_login_exitoso):
        super().__init__()
        self.on_login_exitoso = on_login_exitoso

        self.title("MAQUEDASYSTEMS - Acceso")
        self.geometry("760x420")
        self.minsize(560, 360)
        self.resizable(True, True)
        self.configure(bg=BLANCO)
        self._centrar_ventana()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._construir_estructura_base()

        if not existe_algun_admin():
            self._construir_formulario_primer_admin()
        else:
            self._construir_formulario_login()

    def _centrar_ventana(self):
        self.update_idletasks()
        ancho, alto = 760, 420
        x = (self.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto // 2)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    # ---------- ESTRUCTURA BASE ----------
    def _construir_estructura_base(self):
        self.panel_izquierdo = tk.Frame(self, bg=BLANCO)
        self.panel_izquierdo.grid(row=0, column=0, sticky="nsew")

        self.panel_derecho = tk.Frame(self, bg=AZUL_PRINCIPAL)
        self.panel_derecho.grid(row=0, column=1, sticky="nsew")

        barra_inferior = tk.Frame(self, bg=GRIS_BARRA, height=30)
        barra_inferior.grid(row=1, column=0, columnspan=2, sticky="ew")
        barra_inferior.grid_propagate(False)
        tk.Label(barra_inferior, text="Desarrollado por MAQUEDASYSTEMS",
                 font=("Segoe UI", 8), bg=GRIS_BARRA, fg=GRIS_TEXTO).pack(side="left", padx=12, pady=7)
        tk.Label(barra_inferior, text=f"Versión: {self._version_actual()}",
                 font=("Segoe UI", 8), bg=GRIS_BARRA, fg=GRIS_TEXTO).pack(side="right", padx=12, pady=7)

        self._dibujar_logo()

    def _version_actual(self) -> str:
        """Lee la versión actual del sistema desde ventana_novedades.py
        (se calcula sola ahí a partir de la primera/más reciente entrada
        de NOVEDADES), para no tener el número de versión duplicado y
        desactualizado en dos lugares distintos. Si por algún motivo no
        se puede leer, cae a '1.0.0' sin romper la pantalla de login."""
        try:
            from ventana_novedades import VERSION_ACTUAL
            return VERSION_ACTUAL
        except Exception:
            return "1.0.0"

    # ---------- LOGO RESPONSIVO ----------
    def _dibujar_logo(self):
        """Carga el logotipo oficial y lo hace responsivo: se adapta al tamaño
        del panel izquierdo cada vez que la ventana cambia de tamaño."""
        if not PIL_DISPONIBLE:
            self._dibujar_logo_vectorial()
            return

        ruta_logo = os.path.join(obtener_carpeta_assets(), "logo.jpg")
        if not os.path.exists(ruta_logo):
            self._dibujar_logo_vectorial()
            return

        try:
            self._img_original_pil = Image.open(ruta_logo).convert("RGB")
        except Exception:
            self._dibujar_logo_vectorial()
            return

        # Contenedor centrado en el panel izquierdo
        self._contenedor_logo = tk.Frame(self.panel_izquierdo, bg=BLANCO)
        self._contenedor_logo.place(relx=0.5, rely=0.45, anchor="center")

        # Label que mostrará la imagen (se actualiza en cada resize)
        self._lbl_logo = tk.Label(self._contenedor_logo, bg=BLANCO, borderwidth=0)
        self._lbl_logo.pack(pady=(0, 4))

        self._lbl_slogan = tk.Label(self._contenedor_logo,
                                    text="Soluciones en la gestión de Ventas!",
                                    font=("Segoe UI", 9), bg=BLANCO, fg=GRIS_TEXTO)
        self._lbl_slogan.pack()

        self._ultimo_ancho_panel = 0
        self._resize_job = None
        self.panel_izquierdo.bind("<Configure>", self._on_panel_resize)

    def _on_panel_resize(self, event):
        """Redimensiona el logo con un pequeño debounce para no saturar la CPU."""
        ancho_panel = event.width
        if abs(ancho_panel - self._ultimo_ancho_panel) < 2:
            return
        # Cancelar el redibujado anterior si aún no se ejecutó
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(40, lambda: self._aplicar_resize(ancho_panel))

    def _aplicar_resize(self, ancho_panel):
        """Aplica el redimensionado real de la imagen."""
        self._ultimo_ancho_panel = ancho_panel
        # Ocupar el 90% del ancho del panel
        ancho_img = max(200, int(ancho_panel * 0.90))
        ratio = self._img_original_pil.height / self._img_original_pil.width
        alto_img = int(ancho_img * ratio)

        img_resized = self._img_original_pil.resize((ancho_img, alto_img), Image.LANCZOS)
        self._tk_logo = ImageTk.PhotoImage(img_resized)
        self._lbl_logo.config(image=self._tk_logo)

    def _dibujar_logo_vectorial(self):
        """Logo vectorial de respaldo si Pillow no está disponible o no existe logo.jpg."""
        contenedor_logo = tk.Frame(self.panel_izquierdo, bg=BLANCO)
        contenedor_logo.place(relx=0.5, rely=0.45, anchor="center")

        canvas = tk.Canvas(contenedor_logo, width=140, height=130,
                            bg=BLANCO, highlightthickness=0)
        canvas.pack()
        cx, cy, r = 70, 60, 55
        puntos_hex = []
        for i in range(6):
            angulo = math.radians(60 * i - 30)
            puntos_hex.append(cx + r * math.cos(angulo))
            puntos_hex.append(cy + r * math.sin(angulo))
        canvas.create_polygon(puntos_hex, outline=AZUL_PRINCIPAL, fill=BLANCO, width=5)
        canvas.create_polygon(
            cx, cy - 28, cx + 24, cy - 6, cx, cy + 16, cx - 24, cy - 6,
            fill=AZUL_PRINCIPAL, outline="",
        )
        canvas.create_rectangle(cx - 24, cy - 2, cx - 10, cy + 35,
                                 fill=AZUL_PRINCIPAL, outline="")
        canvas.create_rectangle(cx + 10, cy - 2, cx + 24, cy + 35,
                                 fill=AZUL_PRINCIPAL, outline="")
        canvas.create_polygon(
            cx - 24, cy + 35, cx - 10, cy + 35, cx, cy + 22, cx - 14, cy + 12,
            fill=AZUL_PRINCIPAL, outline="",
        )
        canvas.create_polygon(
            cx + 24, cy + 35, cx + 10, cy + 35, cx, cy + 22, cx + 14, cy + 12,
            fill=AZUL_PRINCIPAL, outline="",
        )
        tk.Label(contenedor_logo, text="MAQUEDASYSTEMS", font=("Segoe UI", 17, "bold"),
                 bg=BLANCO, fg=AZUL_PRINCIPAL).pack(pady=(10, 0))
        tk.Label(contenedor_logo, text="Soluciones en la gestión de Ventas!",
                 font=("Segoe UI", 9), bg=BLANCO, fg=GRIS_TEXTO).pack()

    def _limpiar_panel_derecho(self):
        for widget in self.panel_derecho.winfo_children():
            widget.destroy()

    # ---------- ESTILO DE CAMPO TIPO "UNDERLINE" ----------
    def _crear_campo(self, parent, placeholder, show=None, mayusculas=False):
        contenedor = tk.Frame(parent, bg=AZUL_PRINCIPAL)

        entry = tk.Entry(contenedor, font=("Segoe UI", 11), bg=AZUL_PRINCIPAL, fg="white",
                          insertbackground="white", relief="flat", show=show,
                          highlightthickness=0)
        entry.pack(fill="x")
        entry.insert(0, placeholder)
        entry.config(fg="#cfe0fb")

        def al_enfocar(event):
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
                entry.config(fg="white")

        def al_salir(event):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.config(fg="#cfe0fb")

        entry.bind("<FocusIn>", al_enfocar)
        entry.bind("<FocusOut>", al_salir)

        if mayusculas:
            # Convierte a mayúsculas en tiempo real lo que el usuario va
            # escribiendo, sin importar el estado del teclado físico (Caps
            # Lock, mayús/minús). Solo actúa mientras el texto NO es el
            # placeholder (es decir, mientras el usuario está escribiendo
            # contenido real), para no convertir el texto gris de ejemplo.
            def al_escribir_mayusculas(event):
                texto_actual = entry.get()
                if texto_actual == placeholder:
                    return
                texto_mayus = texto_actual.upper()
                if texto_actual != texto_mayus:
                    posicion_cursor = entry.index(tk.INSERT)
                    entry.delete(0, tk.END)
                    entry.insert(0, texto_mayus)
                    entry.icursor(posicion_cursor)
            entry.bind("<KeyRelease>", al_escribir_mayusculas)

        linea = tk.Frame(contenedor, bg="#7fa6ec", height=1)
        linea.pack(fill="x")

        contenedor.entry = entry
        return contenedor

    def _obtener_valor(self, contenedor_campo, placeholder):
        valor = contenedor_campo.entry.get()
        return "" if valor == placeholder else valor

    # ---------- LOGIN NORMAL ----------
    def _construir_formulario_login(self):
        self._limpiar_panel_derecho()
        panel = self.panel_derecho

        contenido = tk.Frame(panel, bg=AZUL_PRINCIPAL)
        contenido.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.75)

        tk.Label(contenido, text="Acceso", font=("Segoe UI", 20, "bold"),
                 bg=AZUL_PRINCIPAL, fg="white").pack(anchor="w", pady=(0, 4))
        tk.Label(contenido, text="Complete sus credenciales para acceder al Sistema!",
                 font=("Segoe UI", 9), bg=AZUL_PRINCIPAL, fg="#d6e4fb",
                 wraplength=320, justify="left").pack(anchor="w", pady=(0, 25))

        self.placeholder_usuario  = "Usuario"
        self.placeholder_password = "Contraseña"
        self.campo_usuario  = self._crear_campo(contenido, self.placeholder_usuario)
        self.campo_usuario.pack(fill="x", pady=(0, 22))
        self.campo_password = self._crear_campo(contenido, self.placeholder_password, show="*")
        self.campo_password.pack(fill="x", pady=(0, 30))

        self.entry_usuario  = self.campo_usuario.entry
        self.entry_password = self.campo_password.entry
        self.entry_password.bind("<Return>", lambda e: self._intentar_login())

        btn_ingresar = tk.Label(contenido, text="Ingresar", font=("Segoe UI", 10, "bold"),
                                 bg=AZUL_BOTON, fg="white", cursor="hand2", pady=10)
        btn_ingresar.pack(fill="x")
        btn_ingresar.bind("<Button-1>", lambda e: self._intentar_login())

        self.entry_usuario.focus()

    def _intentar_login(self):
        usuario  = self._obtener_valor(self.campo_usuario,  self.placeholder_usuario)
        password = self._obtener_valor(self.campo_password, self.placeholder_password)

        if not usuario or not password:
            messagebox.showwarning("Campos vacíos", "Ingresa usuario y contraseña.")
            return

        exito, mensaje, datos_usuario = login(usuario, password)
        if exito:
            self.destroy()
            self.on_login_exitoso(datos_usuario)
        else:
            messagebox.showerror("Error de acceso", mensaje)
            self.entry_password.delete(0, tk.END)
            self.entry_password.insert(0, self.placeholder_password)
            self.entry_password.config(fg="#cfe0fb")

    # ---------- PRIMER ARRANQUE: CREAR ADMIN ----------
    def _construir_formulario_primer_admin(self):
        self._limpiar_panel_derecho()
        panel = self.panel_derecho

        contenido = tk.Frame(panel, bg=AZUL_PRINCIPAL)
        contenido.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.75)

        tk.Label(contenido, text="Configuración inicial", font=("Segoe UI", 16, "bold"),
                 bg=AZUL_PRINCIPAL, fg="white").pack(anchor="w", pady=(0, 4))
        tk.Label(contenido, text="Crea el administrador principal del sistema",
                 font=("Segoe UI", 9), bg=AZUL_PRINCIPAL, fg="#d6e4fb",
                 wraplength=320, justify="left").pack(anchor="w", pady=(0, 18))

        self.ph_nombre         = "Nombre completo"
        self.ph_usuario_admin  = "Usuario"
        self.ph_password_admin = "Contraseña"
        self.ph_password_admin2= "Confirmar contraseña"

        self.campo_nombre          = self._crear_campo(contenido, self.ph_nombre, mayusculas=True)
        self.campo_nombre.pack(fill="x", pady=(0, 14))
        self.campo_usuario_admin   = self._crear_campo(contenido, self.ph_usuario_admin)
        self.campo_usuario_admin.pack(fill="x", pady=(0, 14))
        self.campo_password_admin  = self._crear_campo(contenido, self.ph_password_admin,  show="*")
        self.campo_password_admin.pack(fill="x", pady=(0, 14))
        self.campo_password_admin2 = self._crear_campo(contenido, self.ph_password_admin2, show="*")
        self.campo_password_admin2.pack(fill="x", pady=(0, 22))

        self.entry_nombre          = self.campo_nombre.entry
        self.entry_usuario_admin   = self.campo_usuario_admin.entry
        self.entry_password_admin  = self.campo_password_admin.entry
        self.entry_password_admin2 = self.campo_password_admin2.entry

        # Enter en cualquiera de los 4 campos confirma y crea el
        # administrador, igual que hacer click en "Crear administrador".
        self.entry_nombre.bind("<Return>", lambda e: self._crear_admin_principal())
        self.entry_usuario_admin.bind("<Return>", lambda e: self._crear_admin_principal())
        self.entry_password_admin.bind("<Return>", lambda e: self._crear_admin_principal())
        self.entry_password_admin2.bind("<Return>", lambda e: self._crear_admin_principal())

        btn_crear = tk.Label(contenido, text="Crear administrador", font=("Segoe UI", 10, "bold"),
                              bg=AZUL_BOTON, fg="white", cursor="hand2", pady=10)
        btn_crear.pack(fill="x")
        btn_crear.bind("<Button-1>", lambda e: self._crear_admin_principal())

        self.entry_nombre.focus()

    def _crear_admin_principal(self):
        nombre   = self._obtener_valor(self.campo_nombre,          self.ph_nombre)
        usuario  = self._obtener_valor(self.campo_usuario_admin,   self.ph_usuario_admin)
        password = self._obtener_valor(self.campo_password_admin,  self.ph_password_admin)
        password2= self._obtener_valor(self.campo_password_admin2, self.ph_password_admin2)

        if password != password2:
            messagebox.showerror("Error", "Las contraseñas no coinciden.")
            return

        exito, mensaje = crear_usuario(nombre, usuario, password, rol="admin")
        if exito:
            messagebox.showinfo("Listo", "Administrador creado. Ahora puedes iniciar sesión.")
            self._construir_formulario_login()
        else:
            messagebox.showerror("Error", mensaje)
