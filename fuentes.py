"""
fuentes.py
Sistema centralizado de fuentes de la aplicación.

En vez de escribir tuplas fijas como ("Segoe UI", 10, "bold") en cada
pantalla, todo el sistema pide sus fuentes a través de las funciones
`f()` (variable, familia configurable) y `mono()` (fija en Consolas,
para el cronómetro) de este módulo.

¿Por qué esto permite cambiar el tamaño/tipografía de TODO el sistema
en caliente, sin reiniciar? Porque tkinter.font.Font son objetos
"vivos": cualquier widget que use uno de estos objetos como su `font`
se redibuja automáticamente en pantalla en el instante en que alguien
llama a `fuente.configure(...)` sobre ese mismo objeto — no hace falta
recrear el widget. Este módulo mantiene un registro de todas las
fuentes que se van pidiendo (una por cada combinación de tamaño base +
estilo realmente usada en el sistema) y, cuando se aplica una nueva
configuración de Apariencia, reconfigura TODAS de una sola vez.

Ver también: models_configuracion.py (persistencia en la base de
datos) y ventana_ajustes.py (pantalla "Ajustes del Sistema" donde el
administrador cambia esta configuración).
"""
import tkinter.font as tkfont

FAMILIA_PREDETERMINADA = "Segoe UI"
ESCALA_PREDETERMINADA = 100  # 100% = tamaño original de diseño de cada pantalla

_familia_actual = FAMILIA_PREDETERMINADA
_escala_actual = ESCALA_PREDETERMINADA

# (tamaño_base, peso, inclinacion, subrayado) -> tkinter.font.Font ya creado
_fuentes_registradas: dict = {}

# Funciones a avisar cuando cambia la configuración (para que, por ejemplo,
# la ventana de Ajustes pueda refrescar su propia vista previa).
_callbacks_cambio: list = []


def f(tamaño_base: int, *estilos: str) -> tkfont.Font:
    """Devuelve el objeto Font "vivo" para un tamaño base de diseño y
    estilos opcionales ('bold', 'italic', 'underline'). Reemplaza a las
    tuplas ('Segoe UI', tamaño, estilo) que se usaban antes en todo el
    código de las pantallas."""
    peso = "bold" if "bold" in estilos else "normal"
    inclinacion = "italic" if "italic" in estilos else "roman"
    subrayado = 1 if "underline" in estilos else 0
    clave = (tamaño_base, peso, inclinacion, subrayado)

    fuente = _fuentes_registradas.get(clave)
    if fuente is None:
        fuente = tkfont.Font(
            family=_familia_actual,
            size=_escalar(tamaño_base),
            weight=peso,
            slant=inclinacion,
            underline=subrayado,
        )
        _fuentes_registradas[clave] = fuente
    return fuente


def mono(tamaño_base: int, *estilos: str) -> tkfont.Font:
    """Igual que f(), pero siempre en una tipografía monoespaciada
    (Consolas), sin importar la familia elegida en Ajustes. Se usa para
    el cronómetro de sesión, donde los dígitos no deben "bailar" al
    cambiar de número. El TAMAÑO sí respeta la escala configurada."""
    peso = "bold" if "bold" in estilos else "normal"
    inclinacion = "italic" if "italic" in estilos else "roman"
    clave = ("mono", tamaño_base, peso, inclinacion)

    fuente = _fuentes_registradas.get(clave)
    if fuente is None:
        fuente = tkfont.Font(
            family="Consolas",
            size=_escalar(tamaño_base),
            weight=peso,
            slant=inclinacion,
        )
        _fuentes_registradas[clave] = fuente
    return fuente


def _escalar(tamaño_base: int) -> int:
    return max(6, round(tamaño_base * _escala_actual / 100))


def familia_actual() -> str:
    return _familia_actual


def escala_actual() -> int:
    return _escala_actual


def aplicar_configuracion(familia: str = None, escala: int = None, guardar: bool = True):
    """Cambia la familia y/o la escala de TODAS las fuentes registradas
    hasta ahora, en caliente (se ve el cambio al instante en cualquier
    ventana ya abierta), y guarda la preferencia en la base de datos."""
    global _familia_actual, _escala_actual
    if familia:
        _familia_actual = familia
    if escala:
        _escala_actual = escala

    for clave, fuente in _fuentes_registradas.items():
        if clave[0] == "mono":
            _, tamaño_base, peso, inclinacion = clave
            fuente.configure(size=_escalar(tamaño_base))  # Consolas: no cambia de familia
        else:
            tamaño_base, peso, inclinacion, subrayado = clave
            fuente.configure(family=_familia_actual, size=_escalar(tamaño_base),
                              weight=peso, slant=inclinacion, underline=subrayado)

    if guardar:
        from models_configuracion import guardar_configuracion_apariencia
        guardar_configuracion_apariencia(_familia_actual, _escala_actual)

    for callback in _callbacks_cambio:
        try:
            callback()
        except Exception:
            pass


def restablecer_configuracion():
    """Vuelve la fuente y el tamaño a los valores de fábrica."""
    aplicar_configuracion(FAMILIA_PREDETERMINADA, ESCALA_PREDETERMINADA)


def cargar_configuracion_guardada():
    """Se llama una sola vez, al iniciar el sistema (antes de construir
    la ventana principal), para aplicar la preferencia guardada por el
    usuario en una sesión anterior."""
    from models_configuracion import obtener_configuracion_apariencia
    familia, escala = obtener_configuracion_apariencia()
    aplicar_configuracion(familia, escala, guardar=False)


def registrar_callback_cambio(callback):
    """Permite que una pantalla (ej.: la vista previa de Ajustes) se
    entere cuando cambia la configuración, para refrescarse."""
    _callbacks_cambio.append(callback)
