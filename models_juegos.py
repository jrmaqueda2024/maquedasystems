"""
models_juegos.py
Lógica de persistencia del módulo "Juegos y Entretenimiento". Guarda cada
puntaje obtenido por un usuario en cualquiera de los 6 juegos disponibles
(Solitario, Buscaminas, Tetris, Snake, Pong, Pac-Man) y ofrece las
consultas para armar el ranking general de usuarios y las mejores
puntuaciones por juego.
"""
from database import conectar

# Clave interna -> etiqueta visible (con ícono) de cada juego.
JUEGOS_DISPONIBLES = [
    ("solitario",  "🃏 Solitario"),
    ("buscaminas", "💣 Buscaminas"),
    ("tetris",     "🧱 Tetris"),
    ("snake",      "🐍 Snake"),
    ("pong",       "🏓 Pong"),
    ("pacman",     "👻 Pac-Man"),
]
NOMBRES_JUEGOS = dict(JUEGOS_DISPONIBLES)


def registrar_puntaje(usuario_id, usuario_nombre: str, juego: str, puntaje: int, detalle: str = ""):
    """Guarda un puntaje obtenido al finalizar una partida."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO juegos_puntajes (usuario_id, usuario_nombre, juego, puntaje, detalle)
        VALUES (?, ?, ?, ?, ?)
    """, (usuario_id, usuario_nombre, juego, int(puntaje), detalle))
    conn.commit()
    conn.close()


def obtener_mejor_puntaje_usuario(usuario_id, juego: str) -> int:
    """Devuelve el mejor (más alto) puntaje histórico del usuario en un juego."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT MAX(puntaje) FROM juegos_puntajes WHERE usuario_id = ? AND juego = ?
    """, (usuario_id, juego))
    fila = cursor.fetchone()
    conn.close()
    return fila[0] or 0 if fila else 0


def obtener_top_puntajes(juego: str, limite: int = 10) -> list[dict]:
    """Devuelve el mejor puntaje de cada usuario para un juego puntual,
    ordenado de mayor a menor (tabla de líderes de ESE juego)."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT usuario_nombre, MAX(puntaje) AS mejor, MAX(fecha)
        FROM juegos_puntajes WHERE juego = ?
        GROUP BY usuario_nombre
        ORDER BY mejor DESC
        LIMIT ?
    """, (juego, limite))
    filas = cursor.fetchall()
    conn.close()
    return [{"usuario": f[0], "puntaje": f[1], "fecha": f[2]} for f in filas]


def obtener_ranking_usuarios() -> list[dict]:
    """Ranking general: por cada usuario, suma de sus MEJORES puntajes en
    cada uno de los juegos que jugó (para no premiar solo por jugar mucho
    un único juego), más el detalle desglosado por juego."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT usuario_nombre, juego, MAX(puntaje)
        FROM juegos_puntajes
        GROUP BY usuario_nombre, juego
    """)
    filas = cursor.fetchall()
    conn.close()

    resumen: dict[str, dict] = {}
    for nombre, juego, mejor in filas:
        registro = resumen.setdefault(nombre, {"usuario": nombre, "total": 0, "por_juego": {}})
        registro["por_juego"][juego] = mejor or 0
        registro["total"] += mejor or 0

    lista = list(resumen.values())
    lista.sort(key=lambda r: r["total"], reverse=True)
    return lista


def obtener_historial_usuario(usuario_id, limite: int = 50) -> list[dict]:
    """Últimas partidas jugadas por un usuario en particular, con detalle."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT juego, puntaje, detalle, fecha FROM juegos_puntajes
        WHERE usuario_id = ? ORDER BY fecha DESC LIMIT ?
    """, (usuario_id, limite))
    filas = cursor.fetchall()
    conn.close()
    return [{"juego": f[0], "puntaje": f[1], "detalle": f[2] or "", "fecha": f[3]} for f in filas]
