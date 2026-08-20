"""
temas.py
Sistema centralizado de temas de color (Claro / Oscuro) de la aplicación.

Cómo funciona: cada pantalla, en vez de escribir un color fijo como
bg="#ffffff", llama a temas.c("#ffffff"). Esa función devuelve el mismo
color en modo Claro, o su equivalente pensado para modo Oscuro si el
tema activo es Oscuro. Como esta llamada se resuelve en el momento en
que se CONSTRUYE cada pantalla (no al importar el archivo), alcanza con
reconstruir la pantalla activa para que tome el tema nuevo — no hace
falta reiniciar el programa. Ver fuentes.py para la misma idea aplicada
al tamaño/tipografía de letra.

IMPORTANTE: la barra superior y el menú lateral de main.py, y el panel
de bienvenida de ventana_login.py, tienen su propio diseño oscuro de
marca (azules muy oscuros) que se ve bien en cualquier tema y no
depende de esta paleta — por eso esos dos archivos no llaman a
temas.c().

Ver también: models_configuracion.py (persistencia) y ventana_ajustes.py
(la pantalla "Ajustes del Sistema" donde se elige el tema).
"""

MODO_PREDETERMINADO = "claro"
_modo_actual = MODO_PREDETERMINADO
_callbacks_cambio: list = []

# Color CLARO (el que ya tenía diseñado cada pantalla) -> color pensado
# para modo OSCURO. Cubre todos los colores de diseño usados en las
# pantallas del sistema. Un color que no esté en este mapa se muestra
# igual en ambos temas (fallback seguro).
_MAPA_OSCURO = {
    # ── Fondos y superficies (claro -> oscuro) ──────────────────
    "#ffffff": "#20262f",
    "#f4f5f7": "#171b22",
    "#f8f9fa": "#20262f",
    "#f8fafc": "#20262f",
    "#e9eaee": "#171b22",
    "#eef1f5": "#171b22",
    "#f3f4f6": "#262c36",
    "#dbe4f0": "#232a34",
    # Fondos "pastel" de badges/avisos -> versión oscura del mismo matiz
    "#fefce8": "#332c14",
    "#fef3c7": "#3a2f14",
    "#fef2f2": "#331a1a",
    "#fee2e2": "#331a1a",
    "#fecaca": "#3d2020",
    "#f0fdf4": "#16281d",
    "#dcfce7": "#173b26",
    "#bbf7d0": "#1c4a2f",
    "#dbeafe": "#16283f",
    "#e0e7ff": "#1c2040",
    "#ede9fe": "#241c3d",
    "#d6e4fb": "#16283f",
    "#cfe0fb": "#16283f",

    # ── Bordes (sutiles, pero visibles sobre fondo oscuro) ──────
    "#e2e8f0": "#333b46",
    "#e5e7eb": "#333b46",
    "#dddddd": "#3a4250",
    "#d1d5db": "#3a4250",
    "#cbd5e1": "#3a4250",
    "#c7d3e6": "#333b46",

    # ── Textos (oscuro -> claro) ─────────────────────────────────
    "#1e293b": "#e8ebf0",
    "#374151": "#d7dbe3",
    "#6b7280": "#a3aab7",
    "#7a8aa3": "#a3aab7",
    "#555555": "#b3b9c4",
    "#334155": "#c7cdd8",
    "#64748b": "#a3aab7",
    "#475569": "#c7cdd8",
    "#9ca3af": "#8a93a3",
    "#94a3b8": "#8a93a3",

    # ── Azul (primario / acento) ─────────────────────────────────
    "#1d5fd6": "#5b8fef",
    "#163d8c": "#4472c4",
    "#2563eb": "#5b8fef",
    "#1d4ed8": "#5b8fef",
    "#3b82f6": "#6ea3f5",
    "#60a5fa": "#8fbdf7",
    "#93c5fd": "#a9d0fb",

    # ── Verde (éxito) ─────────────────────────────────────────────
    "#16a34a": "#3ecb70",
    "#166534": "#7fdba0",

    # ── Rojo (peligro) ────────────────────────────────────────────
    "#dc2626": "#f16f6f",
    "#991b1b": "#e88a8a",
    "#ef4444": "#f28e8e",
    "#7f1d1d": "#f4b8b8",

    # ── Naranja / amarillo (advertencia) ─────────────────────────
    "#d97706": "#f0a848",
    "#92400e": "#e8b98a",
    "#ca8a04": "#f2c14e",
    "#f59e0b": "#f5b85a",
    "#fbbf24": "#f7ca6e",

    # ── Morado ─────────────────────────────────────────────────────
    "#7c3aed": "#a988f2",

    # ── Grises abreviados (3 dígitos) usados como texto secundario ──
    "#333": "#d8dce2",
    "#444": "#cdd2da",
    "#555": "#c3c9d2",
    "#666": "#b9c0ca",
    "#777": "#aeb6c2",
    "#888": "#a4adba",
    "#999": "#9aa3b2",
    "#ccc": "#3a4250",  # usado como línea separadora (borde), no como texto

    # ── Otros acentos puntuales ──────────────────────────────────────
    "#c00": "#f1706f",       # rojo de error/advertencia
    "#0891b2": "#4fc6dc",    # celeste (atajo F2 Buscar en Ventas)
    "#0e7490": "#3aa9c2",    # celeste oscuro (atajo F3 Stock en Ventas)
    "#14532d": "#8fdba8",    # verde oscuro (texto de insignia "entrada")
    "#fde8e8": "#3a1d1d",    # fondo rojo pálido (fila bajo stock mínimo)
}


def modo_actual() -> str:
    return _modo_actual


def es_oscuro() -> bool:
    return _modo_actual == "oscuro"


def c(color_claro: str) -> str:
    """Devuelve el color que corresponde según el tema activo.
    En modo 'claro' (o si el color no tiene equivalente definido para
    modo oscuro) devuelve el mismo color original, sin cambios."""
    if _modo_actual == "oscuro" and isinstance(color_claro, str):
        return _MAPA_OSCURO.get(color_claro.lower(), color_claro)
    return color_claro


def aplicar_tema(modo: str, guardar: bool = True):
    """Cambia el tema activo, en caliente, y lo guarda en la base de
    datos (salvo que guardar=False, usado al cargar la preferencia
    guardada al iniciar el sistema)."""
    global _modo_actual
    if modo not in ("claro", "oscuro"):
        modo = "claro"
    _modo_actual = modo
    if guardar:
        from models_configuracion import guardar_tema
        guardar_tema(modo)
    for callback in _callbacks_cambio:
        try:
            callback()
        except Exception:
            pass


def alternar_tema():
    aplicar_tema("oscuro" if _modo_actual == "claro" else "claro")


def cargar_tema_guardado():
    """Se llama una sola vez, al iniciar el sistema, para aplicar el
    tema elegido en una sesión anterior."""
    from models_configuracion import obtener_tema
    aplicar_tema(obtener_tema(), guardar=False)


def registrar_callback_cambio(callback):
    """Permite que main.py se entere cuando cambia el tema, para
    reconstruir la pantalla activa y que tome los colores nuevos."""
    _callbacks_cambio.append(callback)


def aplicar_estilo_ttk():
    """Configura los estilos de los widgets ttk (Treeview, Combobox,
    Notebook, Scrollbar) según el tema activo. A diferencia de los
    widgets tk comunes, los estilos ttk SÍ se actualizan solos en
    cualquier widget ya visible en pantalla en el momento en que se
    llama a esta función — no hace falta reconstruir nada.

    Requiere que ya exista una ventana Tk creada (se llama desde
    VentanaLogin y VentanaPrincipal, nunca antes)."""
    import tkinter.ttk as ttk
    style = ttk.Style()
    try:
        # El tema nativo de Windows ('vista'/'winnative') ignora casi
        # todas las opciones de color al dibujar un Treeview. 'clam' es
        # multiplataforma y sí respeta los colores configurados abajo.
        style.theme_use("clam")
    except Exception:
        pass

    if es_oscuro():
        fondo, texto, borde = "#20262f", "#e8ebf0", "#333b46"
        cab_fondo, cab_texto = "#171b22", "#e8ebf0"
        seleccion, texto_sel = "#2c4a7c", "#ffffff"
    else:
        fondo, texto, borde = "#ffffff", "#1e293b", "#e2e8f0"
        cab_fondo, cab_texto = "#f4f5f7", "#1e293b"
        seleccion, texto_sel = "#dbeafe", "#1e293b"

    style.configure("Treeview", background=fondo, fieldbackground=fondo,
                     foreground=texto, borderwidth=0)
    style.map("Treeview",
              background=[("selected", seleccion)],
              foreground=[("selected", texto_sel)])
    style.configure("Treeview.Heading", background=cab_fondo, foreground=cab_texto,
                     relief="flat", borderwidth=1)
    style.map("Treeview.Heading", background=[("active", cab_fondo)])

    style.configure("TCombobox", fieldbackground=fondo, background=fondo, foreground=texto,
                     arrowcolor=texto)
    style.map("TCombobox",
              fieldbackground=[("readonly", fondo), ("disabled", cab_fondo)],
              foreground=[("readonly", texto), ("disabled", texto)])

    # La lista desplegable del Combobox (el "popdown") es en realidad un
    # Listbox interno de Tk que no se controla con ttk.Style, sino con
    # la base de datos de opciones de Tk (option_add).
    try:
        raiz = style.master
        raiz.option_add("*TCombobox*Listbox.background", fondo)
        raiz.option_add("*TCombobox*Listbox.foreground", texto)
        raiz.option_add("*TCombobox*Listbox.selectBackground", seleccion)
        raiz.option_add("*TCombobox*Listbox.selectForeground", texto_sel)
    except Exception:
        pass

    style.configure("TNotebook", background=fondo, borderwidth=0)
    style.configure("TNotebook.Tab", background=cab_fondo, foreground=cab_texto, padding=[10, 5])
    style.map("TNotebook.Tab",
              background=[("selected", fondo)],
              foreground=[("selected", texto)])

    style.configure("TScrollbar", background=cab_fondo, troughcolor=fondo,
                     bordercolor=borde, arrowcolor=texto)
