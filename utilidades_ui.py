"""
utilidades_ui.py
Utilidades reutilizables de interfaz. Por ahora contiene la función que
fuerza mayúsculas automáticas en campos de texto (tk.Entry), usada en
Productos, Clientes, Proveedores, Marcas, Categorías, etc. en todo el
sistema, para mantener consistencia en los datos guardados.
"""
import tkinter as tk
import sys
import os


def obtener_carpeta_base() -> str:
    """Devuelve la carpeta donde deben vivir los archivos persistentes del
    programa (base de datos, fotos de perfil, backups, etc.).

    - En desarrollo normal (corriendo los .py directamente), es la carpeta
      donde está este archivo.
    - Cuando el programa se empaquetó con PyInstaller (--onefile o
      --onedir), sys.frozen es True y sys.executable apunta al .exe real;
      __file__ en cambio apuntaría a una carpeta temporal de extracción
      (_MEIxxxxxx) que se borra al cerrar el programa, así que NO se debe
      usar para archivos que necesitan persistir entre ejecuciones (la
      base de datos se perdería cada vez que se cierra la aplicación).
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def obtener_carpeta_assets() -> str:
    """Devuelve la carpeta donde están los assets de SOLO LECTURA que se
    empaquetan junto con el programa (logo.jpg, íconos, plantillas, etc.),
    a diferencia de obtener_carpeta_base() que es para archivos que el
    programa necesita escribir y que deben persistir (BD, fotos subidas).

    - En desarrollo, es la misma carpeta del proyecto.
    - Empaquetado con PyInstaller, los assets viven dentro de la carpeta
      temporal de extracción sys._MEIPASS (solo existe mientras el programa
      corre), que es donde PyInstaller coloca los archivos agregados con
      --add-data. Esto es intencional: estos archivos no se modifican en
      tiempo de ejecución, por lo que no importa que vivan en una carpeta
      temporal de solo lectura.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def forzar_mayusculas(entry: tk.Entry, variable: tk.StringVar):
    """Convierte automáticamente a mayúsculas lo que el usuario escribe en
    un Entry, en tiempo real, sin mover el cursor de su posición.

    Uso:
        var_nombre = tk.StringVar()
        entry_nombre = tk.Entry(parent, textvariable=var_nombre)
        forzar_mayusculas(entry_nombre, var_nombre)
    """
    def _al_escribir(*_args):
        texto_actual = variable.get()
        texto_mayusculas = texto_actual.upper()
        if texto_actual != texto_mayusculas:
            posicion_cursor = entry.index(tk.INSERT)
            variable.set(texto_mayusculas)
            entry.icursor(posicion_cursor)

    variable.trace_add("write", _al_escribir)


def entry_mayusculas(parent, variable: tk.StringVar = None, **kwargs) -> tk.Entry:
    """Crea un tk.Entry con mayúsculas automáticas ya conectadas. Si no se
    pasa una variable, crea una StringVar nueva y la deja accesible como
    entry.variable_asociada."""
    if variable is None:
        variable = tk.StringVar()
    entry = tk.Entry(parent, textvariable=variable, **kwargs)
    forzar_mayusculas(entry, variable)
    entry.variable_asociada = variable
    return entry


def ajustar_tamaño_ventana(ventana: tk.Toplevel, ancho_min: int = 0, alto_min: int = 0,
                            margen_ancho: int = 0, margen_alto: int = 0,
                            ancho_max: int = None, alto_max: int = None,
                            mantener_posicion: bool = False) -> None:
    """Hace que una ventana Toplevel quede SIEMPRE del tamaño real que su
    contenido necesita, en vez de un geometry() fijo "adivinado" que puede
    quedar chico y cortar campos (ej. 'Vuelto' u 'Observaciones' en Cobrar).

    Debe llamarse DESPUÉS de construir todo el contenido de la ventana
    (todos los widgets ya empacados/grideados), y reemplaza al uso manual
    de self.geometry("WxH").

    - Calcula el tamaño real requerido por el contenido (winfo_reqwidth/height).
    - Respeta ancho_min/alto_min como piso (igual que minsize).
    - Si el contenido requerido es mayor a la pantalla disponible, lo limita
      al tamaño de la pantalla (con un margen) para que no quede más grande
      que el monitor del usuario.
    - Si mantener_posicion=False (default), centra la ventana en la pantalla.
    - Si mantener_posicion=True, conserva la posición x,y actual de la
      ventana y solo ajusta el tamaño. Útil para ventanas con pestañas que
      reconstruyen su contenido (ej. Editar Producto): al cambiar de pestaña
      se recalcula el tamaño sin que la ventana "salte" de lugar en pantalla.
    - Sigue dejando la ventana redimensionable manualmente (resizable sigue
      configurable por separado; esta función no lo toca).

    Uso típico, al final de __init__ tras construir todo el contenido:
        self.minsize(480, 360)
        ajustar_tamaño_ventana(self, ancho_min=480, alto_min=360)
    """
    ventana.update_idletasks()  # fuerza a Tkinter a calcular el tamaño real del contenido

    ancho_requerido = ventana.winfo_reqwidth() + margen_ancho
    alto_requerido = ventana.winfo_reqheight() + margen_alto

    ancho_final = max(ancho_requerido, ancho_min)
    alto_final = max(alto_requerido, alto_min)

    pantalla_ancho = ventana.winfo_screenwidth()
    pantalla_alto = ventana.winfo_screenheight()
    tope_ancho = ancho_max if ancho_max is not None else int(pantalla_ancho * 0.95)
    tope_alto = alto_max if alto_max is not None else int(pantalla_alto * 0.90)

    ancho_final = min(ancho_final, tope_ancho)
    alto_final = min(alto_final, tope_alto)

    if mantener_posicion:
        pos_x = ventana.winfo_x()
        pos_y = ventana.winfo_y()
        # Si la ventana creció, evita que se salga de la pantalla por abajo/derecha.
        pos_x = max(0, min(pos_x, pantalla_ancho - ancho_final))
        pos_y = max(0, min(pos_y, pantalla_alto - alto_final))
    else:
        pos_x = max(0, (pantalla_ancho - ancho_final) // 2)
        pos_y = max(0, (pantalla_alto - alto_final) // 2)

    ventana.geometry(f"{ancho_final}x{alto_final}+{pos_x}+{pos_y}")


# ─────────────────────────────────────────────────────────────────────────────
#  FORMATO GUARANÍ PARAGUAYO
#  Separador de miles: PUNTO  (2.000)
#  Separador decimal: COMA   (15,36)
# ─────────────────────────────────────────────────────────────────────────────

UNIDADES_CONTINUAS = {"Kilogramo": "Kg", "Litro": "Lt", "Metro": "Mt"}
UNIDADES_ENTERAS   = {"Unidad": "Unid.", "Caja": "Cja.", "Paquete": "Paq.", "Docena": "Doc."}


def formatear_gs(valor) -> str:
    """Formatea un valor monetario en guaraníes paraguayos.
    Separador de miles: punto.  Sin decimales (el guaraní no tiene centavos).
    Ej: 2000 → 'Gs. 2.000'   1234567 → 'Gs. 1.234.567'
    """
    try:
        # Python usa coma para miles en :, — intercambiamos . y ,
        en = f"{int(round(valor)):,}"          # "2,000"  /  "1,234,567"
        return "Gs. " + en.replace(",", ".")   # "Gs. 2.000"  /  "Gs. 1.234.567"
    except (TypeError, ValueError):
        return "Gs. 0"


def formatear_cantidad(valor, unidad: str) -> str:
    """Formatea una cantidad de stock con su unidad de medida.
    - Continuas (Kg, Lt, Mt): coma decimal, sin ceros finales → '15,36 Kg'
    - Enteras (Unid., etc.):  sin decimales                   → '20 Unid.'
    """
    if valor is None:
        return "—"
    abrev = UNIDADES_CONTINUAS.get(unidad)
    if abrev:
        s = f"{valor:.10f}".rstrip("0").rstrip(".")
        return f"{s.replace('.', ',')} {abrev}"
    abrev = UNIDADES_ENTERAS.get(unidad, "Unid.")
    return f"{int(round(valor))} {abrev}"


def unidad_es_fraccionable(unidad: str) -> bool:
    """True si la unidad de medida admite cantidades decimales (Kg, Lt, Mt)."""
    return unidad in UNIDADES_CONTINUAS


def parsear_cantidad(texto: str) -> float:
    """Convierte texto ingresado por el usuario a float, aceptando tanto
    punto como coma como separador decimal.
    Ej: '15,36' → 15.36   '15.36' → 15.36   '20' → 20.0
    """
    texto = texto.strip().replace(" ", "")
    # Si tiene coma Y punto, el que viene último es el decimal
    if "," in texto and "." in texto:
        if texto.rfind(",") > texto.rfind("."):
            # coma es el decimal: '1.234,56' → '1234.56'
            texto = texto.replace(".", "").replace(",", ".")
        else:
            # punto es el decimal: '1,234.56' → '1234.56'
            texto = texto.replace(",", "")
    else:
        texto = texto.replace(",", ".")
    return float(texto)


def habilitar_deseleccion_treeview(tree) -> None:
    """Permite deseleccionar una fila de una grilla (ttk.Treeview) haciendo
    click en un espacio en blanco (fuera de cualquier fila), o presionando
    Escape con el foco en la grilla.

    Si al presionar Escape NO hay ninguna fila seleccionada, no se hace
    nada acá y el evento sigue su curso normal — así no interfiere con
    atajos de Escape que ya existan en cada pantalla (por ejemplo, cerrar
    una ventana o cancelar una acción), que solo entran a jugar cuando ya
    no queda nada para deseleccionar.
    """
    def _al_click_en_blanco(event):
        widget = event.widget
        if not widget.identify_row(event.y):
            widget.selection_remove(widget.selection())

    def _al_escape(event):
        widget = event.widget
        if widget.selection():
            widget.selection_remove(widget.selection())
            return "break"
        return None

    tree.bind("<Button-1>", _al_click_en_blanco, add="+")
    tree.bind("<Escape>", _al_escape, add="+")

