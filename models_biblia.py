"""
models_biblia.py
Módulo "Biblia": permite leer el Antiguo Testamento, el Nuevo Testamento
y la Santa Biblia completa (66 libros), descargando el texto de cada
libro desde Internet y guardándolo en caché local (en la base de datos)
para poder seguir leyendo sin conexión luego de la primera descarga.

Fuente de los textos: repositorio público "aruljohn/Reina-Valera"
(Biblia Reina-Valera, en español, de dominio público), publicado en
formato JSON bajo licencia MIT y servido a través de
raw.githubusercontent.com. Cada libro es un archivo JSON independiente
con la forma:
    {"book": "Génesis", "chapters": [{"chapter": 1, "verses": [
        {"verse": 1, "text": "..."}, ...]}, ...]}
"""
import json
import urllib.request
import urllib.error
import urllib.parse

from database import conectar

BASE_URL = "https://raw.githubusercontent.com/aruljohn/Reina-Valera/main/"

# Orden y nombres EXACTOS de los 66 libros, tal cual el nombre de archivo
# en el repositorio fuente (con tildes y mayúsculas incluidas).
LIBROS_ANTIGUO_TESTAMENTO = [
    "Génesis", "Éxodo", "Levítico", "Números", "Deuteronomio", "Josué", "Jueces",
    "Rut", "1 Samuel", "2 Samuel", "1 Reyes", "2 Reyes", "1 Crónicas", "2 Crónicas",
    "Ésdras", "Nehemías", "Ester", "Job", "Salmos", "Proverbios", "Eclesiástes",
    "Cantares", "Isaías", "Jeremías", "Lamentaciones", "Ezequiel", "Daniel",
    "Oséas", "Joel", "Amós", "Abdías", "Jonás", "Miquéas", "Nahum", "Habacuc",
    "Sofonías", "Aggeo", "Zacarías", "Malaquías",
]
LIBROS_NUEVO_TESTAMENTO = [
    "San Mateo", "San Márcos", "San Lúcas", "San Juan", "Los Actos", "Romanos",
    "1 Corintios", "2 Corintios", "Gálatas", "Efesios", "Filipenses", "Colosenses",
    "1 Tesalonicenses", "2 Tesalonicenses", "1 Timoteo", "2 Timoteo", "Tito",
    "Filemón", "Hebreos", "Santiago", "1 San Pedro", "2 San Pedro", "1 San Juan",
    "2 San Juan", "3 San Juan", "San Júdas", "Revelación",
]
LIBROS_BIBLIA_COMPLETA = LIBROS_ANTIGUO_TESTAMENTO + LIBROS_NUEVO_TESTAMENTO


def _nombre_archivo(libro: str) -> str:
    return urllib.parse.quote(f"{libro}.json")


def libro_en_cache(libro: str) -> bool:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM biblia_cache WHERE libro = ?", (libro,))
    existe = cursor.fetchone() is not None
    conn.close()
    return existe


def cantidad_libros_en_cache(lista_libros: list[str]) -> int:
    conn = conectar()
    cursor = conn.cursor()
    marcadores = ",".join("?" * len(lista_libros))
    cursor.execute(f"SELECT COUNT(*) FROM biblia_cache WHERE libro IN ({marcadores})", lista_libros)
    total = cursor.fetchone()[0]
    conn.close()
    return total


def _guardar_en_cache(libro: str, contenido: dict):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO biblia_cache (libro, contenido, fecha_descarga)
        VALUES (?, ?, datetime('now', 'localtime'))
        ON CONFLICT(libro) DO UPDATE SET
            contenido = excluded.contenido,
            fecha_descarga = excluded.fecha_descarga
    """, (libro, json.dumps(contenido, ensure_ascii=False)))
    conn.commit()
    conn.close()


def _leer_de_cache(libro: str):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT contenido FROM biblia_cache WHERE libro = ?", (libro,))
    fila = cursor.fetchone()
    conn.close()
    if not fila:
        return None
    return json.loads(fila[0])


def descargar_libro(libro: str, timeout: int = 12) -> tuple[bool, str]:
    """Descarga un libro desde Internet y lo guarda en caché local.
    Devuelve (ok, mensaje)."""
    url = BASE_URL + _nombre_archivo(libro)
    try:
        peticion = urllib.request.Request(url, headers={"User-Agent": "MaquedaSystems/1.0"})
        with urllib.request.urlopen(peticion, timeout=timeout) as respuesta:
            datos = json.loads(respuesta.read().decode("utf-8"))
        _guardar_en_cache(libro, datos)
        return True, f"'{libro}' descargado correctamente."
    except urllib.error.URLError as e:
        return False, f"No se pudo descargar '{libro}'. Verificá tu conexión a Internet.\n({e})"
    except Exception as e:
        return False, f"Error al procesar '{libro}': {e}"


def obtener_libro(libro: str, forzar_descarga: bool = False):
    """Devuelve (contenido, origen) de un libro: desde caché si ya existe
    (y no se pidió forzar), o descargándolo desde Internet si no. Si la
    descarga falla pero había una versión vieja en caché, se devuelve esa
    versión igual (mejor mostrar algo que nada)."""
    if not forzar_descarga:
        en_cache = _leer_de_cache(libro)
        if en_cache is not None:
            return en_cache, "cache"

    ok, mensaje = descargar_libro(libro)
    if not ok:
        respaldo = _leer_de_cache(libro)
        if respaldo is not None:
            return respaldo, f"Sin conexión a Internet: se muestra la última versión ya descargada.\n({mensaje})"
        return None, mensaje
    return _leer_de_cache(libro), "descargado"


def libros_faltantes(lista_libros: list[str]) -> list[str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT libro FROM biblia_cache")
    en_cache = {f[0] for f in cursor.fetchall()}
    conn.close()
    return [libro for libro in lista_libros if libro not in en_cache]


def descargar_todos(lista_libros: list[str], progreso_callback=None) -> tuple[int, int, list[str]]:
    """Descarga (solo) los libros de la lista indicada que todavía no
    están en caché. progreso_callback(i, total, libro) se llama antes de
    cada descarga individual, para poder actualizar una barra de
    progreso en la interfaz. Devuelve (exitosos, fallidos, errores)."""
    faltantes = libros_faltantes(lista_libros)
    exitosos, fallidos = 0, 0
    errores: list[str] = []
    total = len(faltantes)
    for i, libro in enumerate(faltantes, start=1):
        if progreso_callback:
            progreso_callback(i, total, libro)
        ok, msg = descargar_libro(libro)
        if ok:
            exitosos += 1
        else:
            fallidos += 1
            errores.append(f"{libro}: {msg}")
    return exitosos, fallidos, errores


def buscar_texto(termino: str, lista_libros: list[str], limite: int = 150) -> list[dict]:
    """Busca un término dentro de los libros YA DESCARGADOS (caché) de la
    lista indicada (Antiguo Testamento, Nuevo Testamento o Biblia
    Completa). No busca en libros que el usuario todavía no descargó."""
    termino_low = termino.strip().lower()
    if not termino_low or not lista_libros:
        return []
    resultados = []
    conn = conectar()
    cursor = conn.cursor()
    marcadores = ",".join("?" * len(lista_libros))
    cursor.execute(
        f"SELECT libro, contenido FROM biblia_cache WHERE libro IN ({marcadores})",
        lista_libros,
    )
    filas = cursor.fetchall()
    conn.close()
    # Recorremos respetando el orden bíblico de lista_libros, no el orden
    # (arbitrario) en que SQLite devolvió las filas.
    contenidos = {libro: json.loads(contenido) for libro, contenido in filas}
    for libro in lista_libros:
        datos = contenidos.get(libro)
        if not datos:
            continue
        for cap in datos.get("chapters", []):
            for v in cap.get("verses", []):
                texto = v.get("text", "")
                if termino_low in texto.lower():
                    resultados.append({
                        "libro": libro,
                        "capitulo": cap.get("chapter"),
                        "versiculo": v.get("verse"),
                        "texto": texto,
                    })
                    if len(resultados) >= limite:
                        return resultados
    return resultados
