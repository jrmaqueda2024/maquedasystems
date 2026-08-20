"""
auth.py
Maneja todo lo relacionado a usuarios: login, creación/edición/borrado de
cuentas, verificación de contraseñas y PERMISOS por módulo. Las contraseñas
NUNCA se guardan en texto plano: se guardan con hash + sal usando hashlib
(pbkdf2_hmac).
"""
import hashlib
import os
import binascii
from database import conectar


# Módulos del sistema que se pueden asignar a un usuario "vendedor".
# (Los módulos administrativos -Usuarios, Licencias, Uso del sistema- siempre
# son exclusivos del rol "admin" y no se asignan por permisos.)
MODULOS_DISPONIBLES = [
    ("ventas",         "🧾 Ventas"),
    ("preventa",       "🕑 Pre-Venta"),
    ("creditos",       "💳 Créditos"),
    ("prestamos",      "🏦 Préstamos"),
    ("presupuestos",   "📝 Presupuestos"),
    ("productos",      "📦 Productos"),
    ("inventario",     "📋 Inventario"),
    ("compras",        "🛒 Compras"),
    ("importacion",    "📦 Importaciones"),
    ("asistencia",     "🖥 Asistencia Técnica"),
    ("veterinaria",    "🐾 Veterinaria"),
    ("restaurante",    "🍽 Restaurante/Comedor"),
    ("streaming",      "📺 Alquiler de Streaming"),
    ("clientes",       "👥 Clientes"),
    ("reportes",       "📊 Reportes"),
    ("cotizaciones",   "💱 Cotizaciones"),
    ("clima",          "⛅ Clima"),
    ("usuarios",       "⚙ Usuarios"),
    ("rrhh",           "🧑‍💼 Recursos Humanos"),
    ("licencia",       "🔑 Licencias"),
    ("uso",            "⏱ Uso del sistema"),
    ("datos",          "💾 Gestión de Datos"),
    ("terminal",       "🖥 Terminal SQL"),
    ("ia",             "🤖 Asistente IA"),
    ("idioma",         "🌐 Idioma"),
    ("juegos",         "🎮 Juegos"),
    ("biblia",         "📖 Biblia"),
    ("reinicio",       "♻ Reinicio del Sistema"),
]
CLAVES_MODULOS = [k for k, _ in MODULOS_DISPONIBLES]

# Módulos restringidos solo al rol "admin"
MODULOS_SOLO_ADMIN = {"usuarios", "licencia", "uso", "datos", "terminal", "ia", "idioma", "reinicio", "rrhh", "configlocal"}


def _generar_hash(password: str, sal: bytes = None):
    if sal is None:
        sal = os.urandom(16)
    hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), sal, 100_000)
    return f"{binascii.hexlify(sal).decode()}${binascii.hexlify(hash_bytes).decode()}"


def _verificar_password(password: str, password_guardado: str) -> bool:
    try:
        sal_hex, _ = password_guardado.split("$")
        sal = binascii.unhexlify(sal_hex)
    except (ValueError, binascii.Error):
        return False
    return _generar_hash(password, sal) == password_guardado


def _permisos_a_csv(permisos) -> str:
    """Convierte una lista de claves de módulo a CSV. Filtra solo válidas."""
    if not permisos:
        return ""
    if isinstance(permisos, str):
        items = [p.strip() for p in permisos.split(",")]
    else:
        items = list(permisos)
    return ",".join(p for p in items if p in CLAVES_MODULOS)


def _csv_a_permisos(csv: str) -> list[str]:
    if not csv:
        return []
    return [p.strip() for p in csv.split(",") if p.strip() in CLAVES_MODULOS]


# ============================================================
# CONSULTAS
# ============================================================
def existe_algun_admin() -> bool:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 'admin'")
    total = cursor.fetchone()[0]
    conn.close()
    return total > 0


def listar_usuarios() -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nombre_completo, usuario, rol, activo, fecha_creacion, permisos,
               email, telefono, fecha_nacimiento, foto_ruta, direccion, observaciones
        FROM usuarios ORDER BY id
    """)
    filas = cursor.fetchall()
    conn.close()
    return [
        {
            "id": f[0],
            "nombre_completo": f[1],
            "usuario": f[2],
            "rol": f[3],
            "activo": bool(f[4]),
            "fecha_creacion": f[5],
            "permisos": _csv_a_permisos(f[6] or ""),
            "email": f[7] or "",
            "telefono": f[8] or "",
            "fecha_nacimiento": f[9] or "",
            "foto_ruta": f[10] or "",
            "direccion": f[11] or "",
            "observaciones": f[12] or "",
        }
        for f in filas
    ]


def obtener_usuario(usuario_id: int) -> dict | None:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nombre_completo, usuario, rol, activo, fecha_creacion, permisos,
               email, telefono, fecha_nacimiento, foto_ruta, direccion, observaciones
        FROM usuarios WHERE id = ?
    """, (usuario_id,))
    f = cursor.fetchone()
    conn.close()
    if not f:
        return None
    return {
        "id": f[0],
        "nombre_completo": f[1],
        "usuario": f[2],
        "rol": f[3],
        "activo": bool(f[4]),
        "fecha_creacion": f[5],
        "permisos": _csv_a_permisos(f[6] or ""),
        "email": f[7] or "",
        "telefono": f[8] or "",
        "fecha_nacimiento": f[9] or "",
        "foto_ruta": f[10] or "",
        "direccion": f[11] or "",
        "observaciones": f[12] or "",
    }


# ============================================================
# ALTAS, EDICIONES Y BAJAS
# ============================================================
def crear_usuario(nombre_completo: str, usuario: str, password: str,
                   rol: str = "vendedor", permisos=None,
                   email: str = "", telefono: str = "",
                   fecha_nacimiento: str = "", foto_ruta: str = "",
                   direccion: str = "", observaciones: str = "") -> tuple[bool, str]:
    """Crea un nuevo usuario en el sistema."""
    if not nombre_completo.strip() or not usuario.strip() or not password:
        return False, "Todos los campos son obligatorios."
    if rol not in ("admin", "gerente", "vendedor"):
        return False, "Rol inválido."
    if len(password) < 4:
        return False, "La contraseña debe tener al menos 4 caracteres."

    permisos_csv = "" if rol == "admin" else _permisos_a_csv(permisos)
    password_hash = _generar_hash(password)
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO usuarios (nombre_completo, usuario, password_hash, rol, permisos, "
            "email, telefono, fecha_nacimiento, foto_ruta, direccion, observaciones) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (nombre_completo.strip(), usuario.strip().lower(), password_hash, rol, permisos_csv,
             email.strip(), telefono.strip(), fecha_nacimiento.strip(),
             foto_ruta.strip(), direccion.strip(), observaciones.strip()),
        )
        conn.commit()
        return True, "Usuario creado correctamente."
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            return False, "Ese nombre de usuario ya existe."
        return False, f"Error al crear usuario: {e}"
    finally:
        conn.close()


def editar_usuario(usuario_id: int, nombre_completo: str, usuario: str,
                    rol: str, activo: bool, permisos=None,
                    nueva_password: str = "",
                    email: str = "", telefono: str = "",
                    fecha_nacimiento: str = "", foto_ruta: str = "",
                    direccion: str = "", observaciones: str = "") -> tuple[bool, str]:
    """Edita los datos de un usuario. Si nueva_password está vacía, no la cambia."""
    if not nombre_completo.strip() or not usuario.strip():
        return False, "Nombre y usuario son obligatorios."
    if rol not in ("admin", "gerente", "vendedor"):
        return False, "Rol inválido."
    permisos_csv = "" if rol == "admin" else _permisos_a_csv(permisos)

    conn = conectar()
    cursor = conn.cursor()
    try:
        campos_perfil = (email.strip(), telefono.strip(), fecha_nacimiento.strip(),
                         foto_ruta.strip(), direccion.strip(), observaciones.strip())
        if nueva_password:
            if len(nueva_password) < 4:
                return False, "La contraseña debe tener al menos 4 caracteres."
            cursor.execute("""
                UPDATE usuarios
                SET nombre_completo=?, usuario=?, rol=?, activo=?, permisos=?,
                    password_hash=?,
                    email=?, telefono=?, fecha_nacimiento=?,
                    foto_ruta=?, direccion=?, observaciones=?
                WHERE id=?
            """, (nombre_completo.strip(), usuario.strip().lower(), rol,
                  1 if activo else 0, permisos_csv,
                  _generar_hash(nueva_password),
                  *campos_perfil, usuario_id))
        else:
            cursor.execute("""
                UPDATE usuarios
                SET nombre_completo=?, usuario=?, rol=?, activo=?, permisos=?,
                    email=?, telefono=?, fecha_nacimiento=?,
                    foto_ruta=?, direccion=?, observaciones=?
                WHERE id=?
            """, (nombre_completo.strip(), usuario.strip().lower(), rol,
                  1 if activo else 0, permisos_csv,
                  *campos_perfil, usuario_id))
        conn.commit()
        return True, "Usuario actualizado correctamente."
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            return False, "Ese nombre de usuario ya existe."
        return False, f"Error al editar usuario: {e}"
    finally:
        conn.close()


def eliminar_usuario(usuario_id: int) -> tuple[bool, str]:
    """Elimina un usuario. No se permite si es el último admin activo."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT rol, activo FROM usuarios WHERE id=?", (usuario_id,))
    fila = cursor.fetchone()
    if not fila:
        conn.close()
        return False, "Usuario no encontrado."
    rol, activo = fila
    if rol == "admin":
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol='admin' AND activo=1 AND id<>?",
                       (usuario_id,))
        otros_admins = cursor.fetchone()[0]
        if otros_admins == 0:
            conn.close()
            return False, "No podés eliminar al último administrador activo."

    try:
        cursor.execute("DELETE FROM usuarios WHERE id=?", (usuario_id,))
        conn.commit()
        return True, "Usuario eliminado."
    except Exception as e:
        return False, f"Error al eliminar usuario: {e}"
    finally:
        conn.close()


def cambiar_estado_usuario(usuario_id: int, activo: bool) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET activo = ? WHERE id = ?", (1 if activo else 0, usuario_id))
    conn.commit()
    conn.close()
    return True, "Estado actualizado."


def cambiar_password(usuario_id: int, nueva_password: str) -> tuple[bool, str]:
    if len(nueva_password) < 4:
        return False, "La contraseña debe tener al menos 4 caracteres."
    password_hash = _generar_hash(nueva_password)
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET password_hash = ? WHERE id = ?", (password_hash, usuario_id))
    conn.commit()
    conn.close()
    return True, "Contraseña actualizada."


# ============================================================
# LOGIN
# ============================================================
def login(usuario: str, password: str) -> tuple[bool, str, dict | None]:
    """Intenta iniciar sesión. Devuelve (exito, mensaje, datos_usuario).
    Los datos del usuario incluyen el rol y la lista de permisos."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nombre_completo, usuario, password_hash, rol, activo, permisos,
               foto_ruta
        FROM usuarios WHERE usuario = ?
    """, (usuario.strip().lower(),))
    fila = cursor.fetchone()
    conn.close()

    if fila is None:
        return False, "Usuario o contraseña incorrectos.", None

    user_id, nombre_completo, user_db, password_hash, rol, activo, permisos_csv, foto_ruta = fila

    if not activo:
        return False, "Este usuario está deshabilitado. Contacta al administrador.", None

    if not _verificar_password(password, password_hash):
        return False, "Usuario o contraseña incorrectos.", None

    datos_usuario = {
        "id": user_id,
        "nombre_completo": nombre_completo,
        "usuario": user_db,
        "rol": rol,
        "permisos": _csv_a_permisos(permisos_csv or ""),
        "foto_ruta": foto_ruta or "",
    }
    return True, "Bienvenido", datos_usuario


# ============================================================
# PERMISOS
# ============================================================
def filtro_usuario_ventas(usuario: dict | None) -> int | None:
    """Determina si las ventas visibles para este usuario deben limitarse
    a las que él mismo generó.

    - Vendedor: devuelve su propio ID → las pantallas de Resumen y
      Reportes deben filtrar 'WHERE usuario_id = <ese ID>', para que solo
      vea sus propias ventas.
    - Gerente y Administrador: devuelve None → sin filtro, ven las ventas
      de TODOS los usuarios (incluida la propia).

    Se usa como única fuente de verdad para esta regla, para no repetir
    "if rol == 'vendedor'" suelto en cada pantalla.
    """
    if not usuario:
        return None
    if usuario.get("rol") == "vendedor":
        return usuario.get("id")
    return None


def usuario_tiene_acceso(usuario: dict, modulo: str) -> bool:
    """Devuelve True si el usuario puede acceder al módulo dado.
    - Admin: tiene acceso a todo.
    - Vendedor: solo a los módulos en su lista de permisos.
    - Módulos administrativos (usuarios/licencia/uso/datos/reinicio) solo
      para admin.
    - 'ayuda' y 'novedades' son excepciones: siempre visibles para
      cualquier usuario logueado, sin importar su rol o permisos, ya que
      son documentación de referencia y no exponen ni modifican datos.
    """
    if not usuario:
        return False
    if modulo in ("ayuda", "cotizaciones", "clima", "novedades"):
        return True
    rol = usuario.get("rol", "")
    if rol == "admin":
        return True
    # Gerente: accede solo a los módulos que el admin le habilitó
    # (puede tener acceso a TODO si el admin se lo asigna, incluyendo
    # módulos administrativos como Usuarios, RRHH, Datos, etc.)
    permisos = usuario.get("permisos") or []
    if isinstance(permisos, str):
        permisos = _csv_a_permisos(permisos)
    if rol == "gerente":
        return modulo in permisos
    # Vendedor: nunca accede a módulos solo-admin
    if modulo in MODULOS_SOLO_ADMIN:
        return False
    return modulo in permisos
