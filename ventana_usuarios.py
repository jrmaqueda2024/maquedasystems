"""
ventana_usuarios.py
Módulo de Gestión de Usuarios. Solo accesible para administradores.
Incluye foto de perfil, datos de contacto, fecha de nacimiento y más.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import shutil
import datetime

from auth import (
    listar_usuarios, obtener_usuario, crear_usuario, editar_usuario,
    eliminar_usuario, cambiar_estado_usuario, MODULOS_DISPONIBLES,
)
from utilidades_ui import forzar_mayusculas, ajustar_tamaño_ventana, obtener_carpeta_base, habilitar_deseleccion_treeview
from traducciones import t

try:
    from PIL import Image, ImageTk, ImageDraw
    PIL_OK = True
except ImportError:
    PIL_OK = False

AZUL       = "#1d5fd6"
AZUL_OSC   = "#163d8c"
GRIS_FONDO = "#f4f5f7"
GRIS_BORDE = "#e2e8f0"
BLANCO     = "#ffffff"
VERDE      = "#16a34a"
ROJO       = "#dc2626"
NARANJA    = "#d97706"
NEGRO      = "#1e293b"
GRIS_TEXT  = "#6b7280"

# Carpeta donde se guardan las fotos de perfil. Usa obtener_carpeta_base()
# (junto al .exe, NO la carpeta temporal de extracción) porque son archivos
# que el usuario sube en tiempo real y deben persistir entre ejecuciones.
_DIR_FOTOS = os.path.join(obtener_carpeta_base(), "fotos_perfil")


def _asegurar_dir_fotos():
    os.makedirs(_DIR_FOTOS, exist_ok=True)


def _calcular_edad(fecha_nac_str: str) -> str:
    """Devuelve la edad en años a partir de 'YYYY-MM-DD', o '' si es inválida."""
    if not fecha_nac_str:
        return ""
    try:
        nac = datetime.date.fromisoformat(fecha_nac_str)
        hoy = datetime.date.today()
        edad = hoy.year - nac.year - ((hoy.month, hoy.day) < (nac.month, nac.day))
        return f"{edad} años"
    except (ValueError, TypeError):
        return ""


def _cargar_foto_redonda(ruta: str, tam: int) -> "ImageTk.PhotoImage | None":
    """Carga una imagen, la recorta en círculo y la redimensiona a `tam`×`tam`."""
    if not PIL_OK or not ruta or not os.path.exists(ruta):
        return None
    try:
        img = Image.open(ruta).convert("RGBA")
        # Recorte cuadrado centrado
        w, h = img.size
        lado = min(w, h)
        left = (w - lado) // 2
        top  = (h - lado) // 2
        img  = img.crop((left, top, left + lado, top + lado))
        img  = img.resize((tam, tam), Image.LANCZOS)
        # Máscara circular
        mascara = Image.new("L", (tam, tam), 0)
        draw = ImageDraw.Draw(mascara)
        draw.ellipse((0, 0, tam, tam), fill=255)
        resultado = Image.new("RGBA", (tam, tam), (0, 0, 0, 0))
        resultado.paste(img, mask=mascara)
        return ImageTk.PhotoImage(resultado)
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
#  PANEL PRINCIPAL
# ─────────────────────────────────────────────────────────────
class PanelUsuarios(tk.Frame):
    def __init__(self, parent, usuario_actual, on_usuario_guardado=None):
        super().__init__(parent, bg=BLANCO)
        self.usuario_actual       = usuario_actual
        self.usuario_sel_id       = None
        self.on_usuario_guardado  = on_usuario_guardado  # callback hacia main.py

        self._construir_barra()
        self._construir_cuerpo()
        self._cargar_datos()

    def _construir_barra(self):
        barra = tk.Frame(self, bg=AZUL, height=46)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        tk.Label(barra, text=t("usuarios_titulo"),
                 font=("Segoe UI", 12, "bold"), bg=AZUL, fg=BLANCO
                 ).pack(side="left", padx=18, pady=10)
        tk.Button(barra, text=t("usuarios_nuevo"),
                  font=("Segoe UI", 9, "bold"), bg=AZUL, fg=BLANCO,
                  relief="solid", bd=1, padx=12, pady=4, cursor="hand2",
                  command=self._nuevo_usuario
                  ).pack(side="right", padx=14, pady=8)

    def _construir_cuerpo(self):
        cont = tk.Frame(self, bg=BLANCO)
        cont.pack(fill="both", expand=True, padx=14, pady=14)
        cont.grid_columnconfigure(0, weight=2)
        cont.grid_columnconfigure(1, weight=1)
        cont.grid_rowconfigure(0, weight=1)
        self._construir_grilla(cont)
        self._construir_panel_detalle(cont)

    def _construir_grilla(self, padre):
        marco = tk.Frame(padre, bg=BLANCO)
        marco.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        cols   = ("id", "usuario", "nombre", "rol", "activo", "permisos")
        nombres= (t("col_id"), t("col_usuario_mayus"), t("usuarios_nombre_completo"), t("usuarios_rol_mayus"), t("col_estado_mayus"), t("usuarios_permisos_mayus"))
        anchos = (50, 130, 220, 90, 90, 220)

        self.tabla = ttk.Treeview(marco, columns=cols, show="headings", height=18)
        habilitar_deseleccion_treeview(self.tabla)
        for c, n, a in zip(cols, nombres, anchos):
            self.tabla.heading(c, text=n)
            self.tabla.column(c, width=a, anchor="center")
        self.tabla.column("nombre",   anchor="w")
        self.tabla.column("permisos", anchor="w")
        marco.grid_rowconfigure(0, weight=1)
        marco.grid_columnconfigure(0, weight=1)
        sb = ttk.Scrollbar(marco, orient="vertical", command=self.tabla.yview)
        sb_h = ttk.Scrollbar(marco, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=sb.set, xscrollcommand=sb_h.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        sb_h.grid(row=1, column=0, sticky="ew")

        self.tabla.bind("<<TreeviewSelect>>", lambda e: self._al_seleccionar())
        self.tabla.bind("<Double-1>",          lambda e: self._editar_seleccionado())

    def _construir_panel_detalle(self, padre):
        # Contenedor con scroll: antes el panel de detalle (datos + lista de
        # permisos) se cortaba sin forma de desplazarse cuando un usuario
        # tenía muchos módulos asignados. Se envuelve en un Canvas con
        # scrollbar vertical (mismo patrón que la lista de permisos del
        # formulario) para que siempre se pueda ver todo el contenido.
        contenedor = tk.Frame(padre, bg=GRIS_FONDO)
        contenedor.grid(row=0, column=1, sticky="nsew")
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        canvas_detalle = tk.Canvas(contenedor, bg=GRIS_FONDO, highlightthickness=0, bd=0)
        sb_detalle = ttk.Scrollbar(contenedor, orient="vertical", command=canvas_detalle.yview)
        canvas_detalle.configure(yscrollcommand=sb_detalle.set)
        canvas_detalle.grid(row=0, column=0, sticky="nsew")
        self._canvas_detalle = canvas_detalle
        self._sb_detalle = sb_detalle

        self.panel = tk.Frame(canvas_detalle, bg=GRIS_FONDO, padx=15, pady=15)
        id_ventana_detalle = canvas_detalle.create_window((0, 0), window=self.panel, anchor="nw")

        def _actualizar_scroll_detalle(event=None):
            canvas_detalle.configure(scrollregion=canvas_detalle.bbox("all"))
            canvas_detalle.itemconfig(id_ventana_detalle, width=canvas_detalle.winfo_width())
            if self.panel.winfo_reqheight() > canvas_detalle.winfo_height():
                if not sb_detalle.winfo_ismapped():
                    sb_detalle.grid(row=0, column=1, sticky="ns")
            else:
                if sb_detalle.winfo_ismapped():
                    sb_detalle.grid_forget()

        self.panel.bind("<Configure>", _actualizar_scroll_detalle)
        canvas_detalle.bind("<Configure>", _actualizar_scroll_detalle)

        def _con_scroll_del_mouse(event):
            delta = event.delta
            if delta == 0:
                delta = -1 if getattr(event, "num", None) == 5 else 1
            else:
                delta = int(-1 * (delta / 120)) if abs(delta) >= 120 else -1 * delta
            canvas_detalle.yview_scroll(delta, "units")

        def _activar_scroll(event=None):
            canvas_detalle.bind_all("<MouseWheel>", _con_scroll_del_mouse)
            canvas_detalle.bind_all("<Button-4>", _con_scroll_del_mouse)
            canvas_detalle.bind_all("<Button-5>", _con_scroll_del_mouse)

        def _desactivar_scroll(event=None):
            canvas_detalle.unbind_all("<MouseWheel>")
            canvas_detalle.unbind_all("<Button-4>")
            canvas_detalle.unbind_all("<Button-5>")

        contenedor.bind("<Enter>", _activar_scroll)
        contenedor.bind("<Leave>", _desactivar_scroll)

        self._detalle_vacio()

    def _detalle_vacio(self):
        for w in self.panel.winfo_children():
            w.destroy()
        tk.Label(self.panel,
                 text=t("usuarios_seleccion_detalle"),
                 font=("Segoe UI", 10, "italic"), bg=GRIS_FONDO,
                 fg=GRIS_TEXT, justify="center").pack(pady=40)

    def _mostrar_detalle(self, u: dict):
        for w in self.panel.winfo_children():
            w.destroy()

        # ── Foto de perfil ──────────────────────────────────
        foto_frame = tk.Frame(self.panel, bg=GRIS_FONDO)
        foto_frame.pack(pady=(0, 10))

        foto_tk = _cargar_foto_redonda(u.get("foto_ruta", ""), 80)
        if foto_tk:
            lbl_foto = tk.Label(foto_frame, image=foto_tk, bg=GRIS_FONDO)
            lbl_foto.image = foto_tk   # evitar GC
            lbl_foto.pack()
        else:
            # Avatar placeholder con iniciales
            iniciales = "".join(p[0].upper() for p in u["nombre_completo"].split()[:2])
            canvas = tk.Canvas(foto_frame, width=80, height=80,
                               bg=AZUL, highlightthickness=0)
            canvas.pack()
            canvas.create_oval(2, 2, 78, 78, fill=AZUL, outline=AZUL_OSC, width=2)
            canvas.create_text(40, 40, text=iniciales,
                               font=("Segoe UI", 22, "bold"), fill=BLANCO)

        # ── Nombre y usuario ────────────────────────────────
        tk.Label(self.panel, text=u["nombre_completo"],
                 font=("Segoe UI", 12, "bold"), bg=GRIS_FONDO,
                 fg=AZUL_OSC, wraplength=220).pack(anchor="w")
        tk.Label(self.panel, text=f"@{u['usuario']}",
                 font=("Segoe UI", 9), bg=GRIS_FONDO, fg=GRIS_TEXT).pack(anchor="w")

        # ── Separador ───────────────────────────────────────
        tk.Frame(self.panel, bg=GRIS_BORDE, height=1).pack(fill="x", pady=10)

        # ── Datos de perfil ─────────────────────────────────
        info = tk.Frame(self.panel, bg=GRIS_FONDO)
        info.pack(fill="x")

        def fila(icono, valor, color=NEGRO):
            if not valor:
                return
            f = tk.Frame(info, bg=GRIS_FONDO)
            f.pack(fill="x", pady=2)
            tk.Label(f, text=icono, font=("Segoe UI", 10),
                     bg=GRIS_FONDO, width=3).pack(side="left")
            tk.Label(f, text=valor, font=("Segoe UI", 9),
                     bg=GRIS_FONDO, fg=color, anchor="w",
                     wraplength=190, justify="left").pack(side="left", fill="x", expand=True)

        rol_color = VERDE if u["rol"] == "admin" else AZUL
        fila("🎭", u["rol"].capitalize(), rol_color)
        fila("✅" if u["activo"] else "🚫",
             "Activo" if u["activo"] else "Deshabilitado",
             VERDE if u["activo"] else ROJO)

        # Edad calculada
        edad = _calcular_edad(u.get("fecha_nacimiento", ""))
        if u.get("fecha_nacimiento"):
            fila("🎂", f"{u['fecha_nacimiento']}  ({edad})" if edad else u["fecha_nacimiento"])

        fila("📧", u.get("email", ""))
        fila("📞", u.get("telefono", ""))
        fila("📍", u.get("direccion", ""))
        fila("📝", u.get("observaciones", ""))
        fila("📅", u.get("fecha_creacion", ""))

        # ── Permisos ─────────────────────────────────────────
        tk.Frame(self.panel, bg=GRIS_BORDE, height=1).pack(fill="x", pady=(10, 6))
        tk.Label(self.panel, text=t("usuarios_permisos_modulos"),
                 font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO).pack(anchor="w")

        if u["rol"] == "admin":
            tk.Label(self.panel,
                     text=t("usuarios_acceso_total"),
                     font=("Segoe UI", 9), bg=GRIS_FONDO, fg=VERDE,
                     justify="left").pack(anchor="w")
        elif not u["permisos"]:
            tk.Label(self.panel, text=t("usuarios_sin_modulos"),
                     font=("Segoe UI", 9), bg=GRIS_FONDO, fg=ROJO).pack(anchor="w")
        else:
            mapa = dict(MODULOS_DISPONIBLES)
            for clave in u["permisos"]:
                tk.Label(self.panel, text=f"  ✓ {mapa.get(clave, clave)}",
                         font=("Segoe UI", 9), bg=GRIS_FONDO, fg=NEGRO).pack(anchor="w")

        # ── Botones ──────────────────────────────────────────
        tk.Frame(self.panel, bg=GRIS_BORDE, height=1).pack(fill="x", pady=(10, 8))
        botones = tk.Frame(self.panel, bg=GRIS_FONDO)
        botones.pack(fill="x")

        tk.Button(botones, text=t("editar_boton"),
                  font=("Segoe UI", 9, "bold"), bg=BLANCO, fg=AZUL_OSC,
                  relief="solid", bd=1, padx=10, pady=5, cursor="hand2",
                  command=self._editar_seleccionado).pack(side="left", padx=(0, 5))

        txt_estado = "Deshabilitar" if u["activo"] else "Habilitar"
        tk.Button(botones, text=txt_estado,
                  font=("Segoe UI", 9), bg=BLANCO, relief="solid", bd=1,
                  padx=10, pady=5, cursor="hand2",
                  command=self._cambiar_estado).pack(side="left", padx=5)

        tk.Button(botones, text=t("eliminar_boton"),
                  font=("Segoe UI", 9), bg=BLANCO, fg=ROJO, relief="solid",
                  bd=1, padx=10, pady=5, cursor="hand2",
                  command=self._eliminar_seleccionado).pack(side="right")

    # ── Datos ──────────────────────────────────────────────
    def _cargar_datos(self):
        for f in self.tabla.get_children():
            self.tabla.delete(f)
        mapa = dict(MODULOS_DISPONIBLES)
        for u in listar_usuarios():
            if u["rol"] == "admin":
                perms = "(todos — admin)"
            elif not u["permisos"]:
                perms = "(sin permisos)"
            else:
                perms = ", ".join(mapa.get(p, p).split(" ", 1)[-1] for p in u["permisos"])
            self.tabla.insert("", "end", iid=str(u["id"]), values=(
                u["id"], u["usuario"], u["nombre_completo"],
                u["rol"].capitalize(),
                "Activo" if u["activo"] else "Deshabilitado", perms
            ))

    def _al_seleccionar(self):
        sel = self.tabla.selection()
        if not sel:
            self.usuario_sel_id = None
            self._detalle_vacio()
            return
        self.usuario_sel_id = int(sel[0])
        u = obtener_usuario(self.usuario_sel_id)
        if u:
            self._mostrar_detalle(u)

    # ── Acciones ───────────────────────────────────────────
    def _nuevo_usuario(self):
        VentanaFormularioUsuario(self, usuario=None,
                                 on_guardado=self._refrescar,
                                 on_usuario_guardado=self.on_usuario_guardado)

    def _editar_seleccionado(self):
        if not self.usuario_sel_id:
            return
        u = obtener_usuario(self.usuario_sel_id)
        VentanaFormularioUsuario(self, usuario=u,
                                 on_guardado=self._refrescar,
                                 on_usuario_guardado=self.on_usuario_guardado)

    def _eliminar_seleccionado(self):
        if not self.usuario_sel_id:
            return
        if self.usuario_sel_id == self.usuario_actual["id"]:
            messagebox.showwarning("No permitido",
                                   "No podés eliminarte mientras estás logueado.", parent=self)
            return
        u = obtener_usuario(self.usuario_sel_id)
        if not messagebox.askyesno("Confirmar",
                                   f"¿Eliminar al usuario '{u['usuario']}'?\n\n"
                                   "Esta acción no se puede deshacer.", parent=self):
            return
        ok, msg = eliminar_usuario(self.usuario_sel_id)
        if ok:
            self._refrescar()
        else:
            messagebox.showerror("Error", msg, parent=self)

    def _cambiar_estado(self):
        if not self.usuario_sel_id:
            return
        if self.usuario_sel_id == self.usuario_actual["id"]:
            messagebox.showwarning("No permitido",
                                   "No podés deshabilitarte a vos mismo.", parent=self)
            return
        u = obtener_usuario(self.usuario_sel_id)
        ok, msg = cambiar_estado_usuario(self.usuario_sel_id, not u["activo"])
        if ok:
            self._refrescar()

    def _refrescar(self):
        sel_id = self.usuario_sel_id
        self._cargar_datos()
        if sel_id is not None:
            try:
                self.tabla.selection_set(str(sel_id))
                u = obtener_usuario(sel_id)
                if u:
                    self._mostrar_detalle(u)
            except tk.TclError:
                self._detalle_vacio()


# ─────────────────────────────────────────────────────────────
#  FORMULARIO CON PESTAÑAS
# ─────────────────────────────────────────────────────────────
class VentanaFormularioUsuario(tk.Toplevel):
    def __init__(self, parent, usuario, on_guardado, on_usuario_guardado=None,
                 pestana_inicial=0, modo_autoedicion=False):
        super().__init__(parent)
        self.usuario              = usuario
        self.es_edicion           = usuario is not None
        self.on_guardado          = on_guardado
        self.on_usuario_guardado  = on_usuario_guardado
        self.foto_nueva           = ""
        self._pestana_inicial     = pestana_inicial
        # modo_autoedicion=True → el usuario está editando su PROPIO perfil
        # (abierto desde la barra superior, no desde el módulo Usuarios).
        # En ese caso jamás se muestran los controles de Rol, "Usuario
        # activo" ni la pestaña de Permisos: cambiar el propio rol o
        # autoasignarse módulos es una escalada de privilegios y debe ser
        # exclusivo de un Administrador editando a otra persona desde el
        # módulo Usuarios.
        self.modo_autoedicion     = modo_autoedicion

        titulo = "Mi Perfil" if self.modo_autoedicion else ("Editar Usuario" if self.es_edicion else "Nuevo Usuario")
        self.title(titulo)
        self.geometry("720x700")
        self.minsize(700, 600)
        self.resizable(True, True)
        self.configure(bg=BLANCO)
        self.grab_set()
        self.transient(parent)
        self.lift()

        self._inicializar_vars()
        self._construir_ui()
        ajustar_tamaño_ventana(self, ancho_min=700, alto_min=600, ancho_max=760, alto_max=760)

    # ── Variables ──────────────────────────────────────────
    def _inicializar_vars(self):
        u = self.usuario or {}
        self.var_nombre   = tk.StringVar(value=u.get("nombre_completo", ""))
        self.var_usuario  = tk.StringVar(value=u.get("usuario", ""))
        self.var_password = tk.StringVar(value="")
        self.var_rol      = tk.StringVar(value=u.get("rol", "vendedor"))
        self.var_activo   = tk.BooleanVar(value=u.get("activo", True))
        self.var_email    = tk.StringVar(value=u.get("email", ""))
        self.var_telefono = tk.StringVar(value=u.get("telefono", ""))
        self.var_fecha_nac= tk.StringVar(value=u.get("fecha_nacimiento", ""))
        self.var_direccion= tk.StringVar(value=u.get("direccion", ""))
        self.var_obs      = tk.StringVar(value=u.get("observaciones", ""))
        self.foto_actual  = u.get("foto_ruta", "")

        permisos_actuales = u.get("permisos", []) or []
        self.vars_permisos = {
            clave: tk.BooleanVar(value=clave in permisos_actuales)
            for clave, _ in MODULOS_DISPONIBLES
        }

    # ── UI ─────────────────────────────────────────────────
    def _construir_ui(self):
        # Barra de título
        barra = tk.Frame(self, bg=AZUL, height=38)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        tk.Label(barra, text=self.title(),
                 font=("Segoe UI", 11, "bold"), bg=AZUL, fg=BLANCO
                 ).pack(side="left", padx=18, pady=9)

        # Notebook de pestañas
        style = ttk.Style()
        style.configure("TNotebook.Tab", font=("Segoe UI", 9, "bold"), padding=[12, 6])

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=(8, 0))

        self._tab_basicos(self.nb)
        self._tab_perfil(self.nb)
        self._tab_foto(self.nb)
        if not self.modo_autoedicion:
            self._tab_permisos(self.nb)

        # Seleccionar la pestaña indicada al abrir (0=Datos, 1=Perfil, 2=Foto, 3=Permisos)
        # Si es autoedición no existe la pestaña 3 (Permisos): se acota al
        # último índice válido para evitar un error al seleccionarla.
        pestana_valida = min(self._pestana_inicial, len(self.nb.tabs()) - 1)
        if pestana_valida:
            self.nb.select(pestana_valida)

        # Botones inferiores
        pie = tk.Frame(self, bg=GRIS_FONDO, height=56)
        pie.pack(fill="x")
        pie.pack_propagate(False)
        cont = tk.Frame(pie, bg=GRIS_FONDO)
        cont.pack(pady=10)
        btn_guardar_usr = tk.Button(cont, text="✔ Guardar",
                  font=("Segoe UI", 10, "bold"), bg=VERDE, fg=BLANCO,
                  relief="flat", padx=20, pady=8, cursor="hand2",
                  command=self._guardar)
        btn_guardar_usr.pack(side="left", padx=6)
        btn_guardar_usr.bind("<Return>", lambda e: self._guardar())
        tk.Button(cont, text="✕ Cancelar",
                  font=("Segoe UI", 10, "bold"), bg=BLANCO, fg=ROJO,
                  relief="solid", bd=1, padx=20, pady=7, cursor="hand2",
                  command=self.destroy).pack(side="left", padx=6)

    # ── Pestaña 1: Datos básicos ───────────────────────────
    def _tab_basicos(self, nb):
        frame = tk.Frame(nb, bg=GRIS_FONDO, padx=20, pady=16)
        nb.add(frame, text="👤  Datos básicos")

        def campo(label, var, show=None, readonly=False):
            tk.Label(frame, text=label, font=("Segoe UI", 9, "bold"),
                     bg=GRIS_FONDO).pack(anchor="w", pady=(10, 2))
            e = tk.Entry(frame, textvariable=var, font=("Segoe UI", 10),
                         show=show or "",
                         state="readonly" if readonly else "normal")
            e.pack(fill="x")
            return e

        e_nombre = campo("Nombre completo:", self.var_nombre)
        forzar_mayusculas(e_nombre, self.var_nombre)

        campo("Usuario (login):", self.var_usuario)

        pwd_label = "Contraseña (vacío = no cambiar):" if self.es_edicion else "Contraseña:"
        campo(pwd_label, self.var_password, show="•")
        tk.Label(frame, text="(mínimo 4 caracteres)",
                 font=("Segoe UI", 8, "italic"), bg=GRIS_FONDO,
                 fg=GRIS_TEXT).pack(anchor="w")

        # Rol — en autoedición se muestra solo informativo, NUNCA editable:
        # otorgarse a uno mismo un rol o permisos distintos es exclusivo
        # de un Administrador desde el módulo Usuarios.
        tk.Label(frame, text="Rol:", font=("Segoe UI", 9, "bold"),
                 bg=GRIS_FONDO).pack(anchor="w", pady=(12, 2))
        if self.modo_autoedicion:
            nombres_rol = {"vendedor": "Vendedor", "gerente": "Gerente", "admin": "Administrador"}
            tk.Label(frame, text=nombres_rol.get(self.var_rol.get(), self.var_rol.get().capitalize()),
                     font=("Segoe UI", 10, "bold"), bg=GRIS_FONDO, fg=AZUL
                     ).pack(anchor="w")
            tk.Label(frame,
                     text="ℹ️  Solo un Administrador puede cambiar tu rol o tus permisos\n"
                          "    de acceso a módulos, desde el módulo Usuarios.",
                     font=("Segoe UI", 8), bg=GRIS_FONDO, fg="#6b7280",
                     justify="left").pack(anchor="w", pady=(4, 0))
        else:
            fila_rol = tk.Frame(frame, bg=GRIS_FONDO)
            fila_rol.pack(fill="x")
            tk.Radiobutton(fila_rol, text="Vendedor (permisos limitados)",
                           variable=self.var_rol, value="vendedor",
                           bg=GRIS_FONDO, font=("Segoe UI", 9),
                           command=self._sync_permisos).pack(side="left")
            tk.Radiobutton(fila_rol, text="Gerente (permisos configurables)",
                           variable=self.var_rol, value="gerente",
                           bg=GRIS_FONDO, font=("Segoe UI", 9),
                           command=self._sync_permisos).pack(side="left", padx=(12, 0))
            tk.Radiobutton(fila_rol, text="Administrador (acceso total)",
                           variable=self.var_rol, value="admin",
                           bg=GRIS_FONDO, font=("Segoe UI", 9),
                           command=self._sync_permisos).pack(side="left", padx=(12, 0))

            tk.Label(frame, text="ℹ️  El Gerente puede recibir acceso a cualquier módulo,\n"
                                 "    incluidos módulos administrativos. El Admin configura sus permisos.",
                     font=("Segoe UI", 8), bg=GRIS_FONDO, fg="#6b7280",
                     justify="left").pack(anchor="w", pady=(4, 0))

        if self.modo_autoedicion:
            # El propio usuario no puede desactivar su propia cuenta desde
            # acá tampoco — se muestra fijo, sin checkbox.
            pass
        else:
            tk.Checkbutton(frame, text="Usuario activo (puede iniciar sesión)",
                           variable=self.var_activo, bg=GRIS_FONDO,
                           font=("Segoe UI", 9)).pack(anchor="w", pady=(12, 0))

    # ── Pestaña 2: Perfil ──────────────────────────────────
    def _tab_perfil(self, nb):
        frame = tk.Frame(nb, bg=GRIS_FONDO, padx=20, pady=16)
        nb.add(frame, text="📋  Perfil")

        def campo(label, var):
            tk.Label(frame, text=label, font=("Segoe UI", 9, "bold"),
                     bg=GRIS_FONDO).pack(anchor="w", pady=(10, 2))
            tk.Entry(frame, textvariable=var,
                     font=("Segoe UI", 10)).pack(fill="x")

        campo("Correo electrónico:", self.var_email)
        campo("Teléfono / Celular:", self.var_telefono)

        # Fecha de nacimiento con selector
        tk.Label(frame, text="Fecha de nacimiento (YYYY-MM-DD):",
                 font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO
                 ).pack(anchor="w", pady=(10, 2))
        f_nac = tk.Frame(frame, bg=GRIS_FONDO)
        f_nac.pack(fill="x")
        entry_nac = tk.Entry(f_nac, textvariable=self.var_fecha_nac,
                             font=("Segoe UI", 10))
        entry_nac.pack(side="left", fill="x", expand=True)

        # Edad calculada en tiempo real
        self.lbl_edad = tk.Label(f_nac, text="", font=("Segoe UI", 9),
                                  bg=GRIS_FONDO, fg=AZUL, padx=8)
        self.lbl_edad.pack(side="left")
        self.var_fecha_nac.trace_add("write", self._actualizar_edad)
        self._actualizar_edad()

        campo("Dirección:", self.var_direccion)

        # Observaciones (multilinea simulada con Entry)
        tk.Label(frame, text="Observaciones:",
                 font=("Segoe UI", 9, "bold"), bg=GRIS_FONDO
                 ).pack(anchor="w", pady=(10, 2))
        tk.Entry(frame, textvariable=self.var_obs,
                 font=("Segoe UI", 10)).pack(fill="x")

    # ── Pestaña 3: Foto de perfil ──────────────────────────
    def _tab_foto(self, nb):
        frame = tk.Frame(nb, bg=GRIS_FONDO)
        nb.add(frame, text="📷  Foto")

        tk.Label(frame, text="Foto de perfil",
                 font=("Segoe UI", 11, "bold"), bg=GRIS_FONDO, fg=NEGRO
                 ).pack(pady=(20, 4))
        tk.Label(frame,
                 text="Se recomienda imagen cuadrada (JPG o PNG).\nSe recortará en círculo automáticamente.",
                 font=("Segoe UI", 8), bg=GRIS_FONDO, fg=GRIS_TEXT,
                 justify="center").pack()

        # Vista previa
        self.frame_preview = tk.Frame(frame, bg=GRIS_FONDO)
        self.frame_preview.pack(pady=20)
        self._refrescar_preview_foto()

        # Botones
        f_bot = tk.Frame(frame, bg=GRIS_FONDO)
        f_bot.pack()
        tk.Button(f_bot, text="📁 Elegir foto",
                  font=("Segoe UI", 10, "bold"), bg=AZUL, fg=BLANCO,
                  relief="flat", padx=16, pady=8, cursor="hand2",
                  command=self._elegir_foto).pack(side="left", padx=6)
        tk.Button(f_bot, text="🗑 Quitar foto",
                  font=("Segoe UI", 10), bg=BLANCO, fg=ROJO,
                  relief="solid", bd=1, padx=16, pady=7, cursor="hand2",
                  command=self._quitar_foto).pack(side="left", padx=6)

        if not PIL_OK:
            tk.Label(frame,
                     text="⚠ Instala 'Pillow' (pip install Pillow) para habilitar las fotos.",
                     font=("Segoe UI", 8), bg=GRIS_FONDO, fg=NARANJA,
                     wraplength=320, justify="center").pack(pady=12)

    # ── Pestaña 4: Permisos ────────────────────────────────
    def _tab_permisos(self, nb):
        frame = tk.Frame(nb, bg=GRIS_FONDO, padx=20, pady=16)
        nb.add(frame, text="🔒  Permisos")

        tk.Label(frame,
                 text="Módulos accesibles según el rol:\n"
                      "• Vendedor: solo módulos operativos\n"
                      "• Gerente: cualquier módulo, incluyendo los administrativos\n"
                      "• Administrador: acceso total automático (no configurable)",
                 font=("Segoe UI", 9), bg=GRIS_FONDO, fg="#374151",
                 justify="left").pack(anchor="w", pady=(0, 8))

        # ── Lista de módulos con scroll: como la cantidad de módulos del
        # sistema va creciendo, este contenedor SIEMPRE muestra todos los
        # checkboxes (con scroll si hace falta) en vez de cortarse cuando
        # la ventana no alcanza a mostrarlos todos de una. ──
        contenedor_lista = tk.Frame(frame, bg=BLANCO, relief="solid", bd=1)
        contenedor_lista.pack(fill="both", expand=True)

        canvas_permisos = tk.Canvas(contenedor_lista, bg=BLANCO, highlightthickness=0, bd=0, width=1, height=1)
        sb_permisos = ttk.Scrollbar(contenedor_lista, orient="vertical", command=canvas_permisos.yview)
        canvas_permisos.configure(yscrollcommand=sb_permisos.set)
        canvas_permisos.pack(side="left", fill="both", expand=True)

        self.frame_permisos = tk.Frame(canvas_permisos, bg=BLANCO)
        id_ventana_permisos = canvas_permisos.create_window((0, 0), window=self.frame_permisos, anchor="nw")

        def _actualizar_scroll_permisos(event=None):
            canvas_permisos.configure(scrollregion=canvas_permisos.bbox("all"))
            canvas_permisos.itemconfig(id_ventana_permisos, width=canvas_permisos.winfo_width())
            if self.frame_permisos.winfo_reqheight() > canvas_permisos.winfo_height():
                if not sb_permisos.winfo_ismapped():
                    sb_permisos.pack(side="right", fill="y")
            else:
                if sb_permisos.winfo_ismapped():
                    sb_permisos.pack_forget()

        self.frame_permisos.bind("<Configure>", _actualizar_scroll_permisos)
        canvas_permisos.bind("<Configure>", _actualizar_scroll_permisos)

        def _con_scroll_del_mouse(event):
            delta = event.delta
            if delta == 0:
                delta = -1 if getattr(event, "num", None) == 5 else 1
            else:
                delta = int(-1 * (delta / 120)) if abs(delta) >= 120 else -1 * delta
            canvas_permisos.yview_scroll(delta, "units")

        def _activar_scroll(event=None):
            canvas_permisos.bind_all("<MouseWheel>", _con_scroll_del_mouse)
            canvas_permisos.bind_all("<Button-4>", _con_scroll_del_mouse)
            canvas_permisos.bind_all("<Button-5>", _con_scroll_del_mouse)

        def _desactivar_scroll(event=None):
            canvas_permisos.unbind_all("<MouseWheel>")
            canvas_permisos.unbind_all("<Button-4>")
            canvas_permisos.unbind_all("<Button-5>")

        contenedor_lista.bind("<Enter>", _activar_scroll)
        contenedor_lista.bind("<Leave>", _desactivar_scroll)

        self.checks_permisos = {}
        for clave, etiqueta in MODULOS_DISPONIBLES:
            cb = tk.Checkbutton(
                self.frame_permisos, text=etiqueta,
                variable=self.vars_permisos[clave],
                bg=BLANCO, font=("Segoe UI", 10),
                anchor="w", padx=10, pady=5,
            )
            cb.pack(fill="x", anchor="w")
            self.checks_permisos[clave] = cb

        f_acc = tk.Frame(frame, bg=GRIS_FONDO)
        f_acc.pack(fill="x", pady=(8, 0))
        tk.Button(f_acc, text="Marcar todos", font=("Segoe UI", 8),
                  bg=BLANCO, relief="solid", bd=1, padx=10, pady=3,
                  cursor="hand2",
                  command=lambda: self._marcar_todos(True)).pack(side="left", padx=(0, 5))
        tk.Button(f_acc, text="Desmarcar todos", font=("Segoe UI", 8),
                  bg=BLANCO, relief="solid", bd=1, padx=10, pady=3,
                  cursor="hand2",
                  command=lambda: self._marcar_todos(False)).pack(side="left")

        self._sync_permisos()

    # ── Helpers ────────────────────────────────────────────
    def _actualizar_edad(self, *_):
        edad = _calcular_edad(self.var_fecha_nac.get().strip())
        self.lbl_edad.config(text=edad)

    def _marcar_todos(self, val: bool):
        for v in self.vars_permisos.values():
            v.set(val)

    def _sync_permisos(self):
        rol = self.var_rol.get()
        es_admin = rol == "admin"
        # Gerente y Vendedor tienen checkboxes habilitados
        estado = "disabled" if es_admin else "normal"
        bg = "#f3f4f6" if es_admin else BLANCO
        self.frame_permisos.config(bg=bg)
        for cb in self.checks_permisos.values():
            cb.config(state=estado, bg=bg)
        # Si es gerente, mostrar todos los módulos incluyendo los admin
        # Si es vendedor, solo los módulos operativos
        # (el filtro real está en auth.usuario_tiene_acceso)

    def _elegir_foto(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar foto de perfil",
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.bmp *.webp"),
                       ("Todos los archivos", "*.*")],
        )
        if ruta:
            self.foto_nueva = ruta
            self._refrescar_preview_foto()

    def _quitar_foto(self):
        self.foto_nueva = "__QUITAR__"
        self._refrescar_preview_foto()

    def _refrescar_preview_foto(self):
        for w in self.frame_preview.winfo_children():
            w.destroy()

        # Decidir qué ruta mostrar en la preview
        if self.foto_nueva == "__QUITAR__":
            ruta_preview = ""
        elif self.foto_nueva:
            ruta_preview = self.foto_nueva
        else:
            ruta_preview = self.foto_actual

        foto_tk = _cargar_foto_redonda(ruta_preview, 120)
        if foto_tk:
            lbl = tk.Label(self.frame_preview, image=foto_tk, bg=GRIS_FONDO)
            lbl.image = foto_tk
            lbl.pack()
            tk.Label(self.frame_preview,
                     text="✓ Foto cargada correctamente",
                     font=("Segoe UI", 9), bg=GRIS_FONDO, fg=VERDE).pack(pady=(6, 0))
        else:
            # Placeholder
            canvas = tk.Canvas(self.frame_preview, width=120, height=120,
                                bg=GRIS_FONDO, highlightthickness=0)
            canvas.pack()
            canvas.create_oval(5, 5, 115, 115, fill="#cbd5e1", outline="#94a3b8", width=2)
            canvas.create_text(60, 60, text="👤",
                               font=("Segoe UI", 36))
            tk.Label(self.frame_preview,
                     text="Sin foto asignada" if not ruta_preview else "No se pudo cargar la imagen",
                     font=("Segoe UI", 9), bg=GRIS_FONDO, fg=GRIS_TEXT).pack(pady=(6, 0))

    # ── Guardar ────────────────────────────────────────────
    def _guardar(self):
        nombre   = self.var_nombre.get().strip()
        usuario  = self.var_usuario.get().strip()
        password = self.var_password.get()
        rol      = self.var_rol.get()
        activo   = self.var_activo.get()
        email    = self.var_email.get().strip()
        telefono = self.var_telefono.get().strip()
        fecha_nac= self.var_fecha_nac.get().strip()
        direccion= self.var_direccion.get().strip()
        obs      = self.var_obs.get().strip()
        permisos = [k for k, v in self.vars_permisos.items() if v.get()]

        # Segunda barrera de seguridad (además de no mostrar los controles
        # en la UI): en autoedición, rol/activo/permisos SIEMPRE se
        # guardan tal cual estaban antes de abrir el formulario, sin
        # importar el valor que pudieran tener las variables en memoria.
        # Así un usuario nunca puede otorgarse a sí mismo un rol o
        # permisos distintos, ni desactivar su propia cuenta.
        if self.modo_autoedicion:
            u_original = self.usuario or {}
            rol      = u_original.get("rol", rol)
            activo   = u_original.get("activo", activo)
            permisos = u_original.get("permisos", permisos) or []

        if not nombre:
            messagebox.showerror("Dato requerido", "El nombre completo es obligatorio.", parent=self)
            return
        if not usuario:
            messagebox.showerror("Dato requerido", "El nombre de usuario es obligatorio.", parent=self)
            return
        if fecha_nac:
            try:
                datetime.date.fromisoformat(fecha_nac)
            except ValueError:
                messagebox.showerror("Fecha inválida",
                                     "La fecha de nacimiento debe tener el formato YYYY-MM-DD\n"
                                     "Ejemplo: 1990-05-15", parent=self)
                return
        # Módulos obligatorios: un Vendedor o Gerente sin ningún módulo
        # asignado no puede guardarse. Solo el Administrador (acceso total
        # automático) queda exento. En autoedición esta validación no
        # aplica porque los permisos ya vienen fijos del usuario original.
        if not self.modo_autoedicion and rol != "admin" and not permisos:
            messagebox.showerror(
                "Módulos requeridos",
                "Para crear o guardar este usuario primero debés asignarle "
                "al menos un módulo.\n\n"
                "Andá a la pestaña '🔒 Permisos' y marcá los módulos a los "
                "que este usuario podrá acceder.",
                parent=self,
            )
            try:
                self.nb.select(len(self.nb.tabs()) - 1)  # pestaña Permisos = última
            except tk.TclError:
                pass
            return

        # Procesar foto
        foto_ruta = self.foto_actual
        if self.foto_nueva == "__QUITAR__":
            foto_ruta = ""
        elif self.foto_nueva:
            _asegurar_dir_fotos()
            ext   = os.path.splitext(self.foto_nueva)[1].lower()
            fname = f"user_{usuario}{ext}"
            dest  = os.path.join(_DIR_FOTOS, fname)
            try:
                shutil.copy2(self.foto_nueva, dest)
                foto_ruta = dest
            except Exception as e:
                messagebox.showwarning("Foto no guardada",
                                       f"No se pudo copiar la foto:\n{e}", parent=self)

        kwargs = dict(
            email=email, telefono=telefono, fecha_nacimiento=fecha_nac,
            foto_ruta=foto_ruta, direccion=direccion, observaciones=obs,
        )

        if self.es_edicion:
            ok, msg = editar_usuario(
                self.usuario["id"], nombre, usuario, rol, activo, permisos,
                nueva_password=password, **kwargs,
            )
        else:
            if not password:
                messagebox.showerror("Dato requerido",
                                     "La contraseña es obligatoria para un usuario nuevo.",
                                     parent=self)
                return
            ok, msg = crear_usuario(nombre, usuario, password, rol, permisos, **kwargs)

        if ok:
            # Determinar el ID del usuario recién guardado
            if self.es_edicion:
                uid_guardado = self.usuario["id"]
            else:
                # Para usuario nuevo, buscar el ID por nombre de usuario
                from database import conectar as _conn
                c = _conn()
                cur = c.cursor()
                cur.execute("SELECT id FROM usuarios WHERE usuario=?", (usuario.strip().lower(),))
                fila = cur.fetchone()
                c.close()
                uid_guardado = fila[0] if fila else None

            self.on_guardado()
            if self.on_usuario_guardado and uid_guardado:
                self.on_usuario_guardado(uid_guardado)
            self.destroy()
        else:
            messagebox.showerror("Error", msg, parent=self)
