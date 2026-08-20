"""
models_streaming.py
Lógica de negocio del módulo Alquiler de Cuentas de Streaming (Netflix,
HBO Max, Disney+, YouTube Premium, Spotify, etc.):

- Plataformas: catálogo de servicios que se alquilan.
- Cuentas: cada cuenta que el negocio compra (con su costo mensual real
  pagado al proveedor), con sus "cupos" (Perfiles) — un perfil puede ser
  un perfil real de Netflix, o el cupo único de una cuenta vendida como
  'Acceso Completo' a un solo cliente.
- Combos: paquetes de varias plataformas a precio combinado (ej.
  "Netflix + Disney+"), que al contratarse ocupan un perfil libre en
  cada una de las plataformas incluidas.
- Suscripciones: qué cliente tiene alquilado qué perfil(es), desde
  cuándo y hasta cuándo, con su tarifa y forma de pago.
- Pagos/Renovaciones: cada cobro genera una venta real (reutilizando
  models_ventas.procesar_venta, igual que en Veterinaria y Restaurante),
  para que todo aparezca en la misma Caja y Reportes de siempre.
- Seguridad: control de rotación de contraseñas y de dispositivos
  conectados simultáneos por suscripción.

Los clientes se administran con el módulo Clientes ya existente; acá
solo se referencia al cliente que alquila cada perfil.
"""
import datetime

from database import conectar
from models_ventas import procesar_venta

MODALIDADES = ["Perfil Individual", "Acceso Completo", "Combo"]
ESTADOS_CUENTA = ["Activa", "Vencida", "Suspendida"]
ESTADOS_SUSCRIPCION = ["Activa", "Vencida", "Cancelada"]
FORMAS_PAGO = ["Efectivo", "Transferencia Bancaria", "Tarjeta"]


# ============================================================
# PLATAFORMAS
# ============================================================
def listar_plataformas(solo_activas: bool = True) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    where = "WHERE activa = 1" if solo_activas else ""
    cursor.execute(f"SELECT id, nombre, activa FROM stream_plataformas {where} ORDER BY nombre")
    filas = cursor.fetchall()
    conn.close()
    return [{"id": f[0], "nombre": f[1], "activa": bool(f[2])} for f in filas]


def crear_plataforma(nombre: str) -> tuple[bool, str]:
    if not nombre.strip():
        return False, "El nombre de la plataforma es obligatorio."
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO stream_plataformas (nombre) VALUES (?)", (nombre.strip(),))
        conn.commit()
        return True, f"Plataforma '{nombre.strip()}' agregada."
    except Exception:
        return False, "Ya existe una plataforma con ese nombre."
    finally:
        conn.close()


def cambiar_estado_plataforma(plataforma_id: int, activa: bool) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE stream_plataformas SET activa = ? WHERE id = ?", (1 if activa else 0, plataforma_id))
    conn.commit()
    conn.close()
    return True, "Plataforma activada." if activa else "Plataforma desactivada."


# ============================================================
# CUENTAS Y PERFILES
# ============================================================
def listar_cuentas(plataforma_id: int = None, incluir_inactivas: bool = True) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    condiciones, parametros = [], []
    if plataforma_id is not None:
        condiciones.append("c.plataforma_id = ?")
        parametros.append(plataforma_id)
    if not incluir_inactivas:
        condiciones.append("c.estado = 'Activa'")
    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    cursor.execute(f"""
        SELECT c.id, c.plataforma_id, p.nombre, c.email, c.plan_nombre, c.max_perfiles,
               c.costo_mensual, c.fecha_compra, c.fecha_proximo_pago_proveedor,
               c.fecha_ultimo_cambio_password, c.estado, c.notas
        FROM stream_cuentas c JOIN stream_plataformas p ON c.plataforma_id = p.id
        {where}
        ORDER BY p.nombre, c.email
    """, parametros)
    filas = cursor.fetchall()

    resultado = []
    for f in filas:
        cursor.execute("SELECT COUNT(*) FROM stream_perfiles WHERE cuenta_id = ? AND estado = 'Ocupado'", (f[0],))
        ocupados = cursor.fetchone()[0]
        resultado.append({
            "id": f[0], "plataforma_id": f[1], "plataforma": f[2], "email": f[3],
            "plan_nombre": f[4] or "", "max_perfiles": f[5], "costo_mensual": f[6],
            "fecha_compra": f[7], "fecha_proximo_pago_proveedor": f[8] or "",
            "fecha_ultimo_cambio_password": f[9], "estado": f[10], "notas": f[11] or "",
            "perfiles_ocupados": ocupados, "perfiles_libres": f[5] - ocupados,
        })
    conn.close()
    return resultado


def obtener_cuenta(cuenta_id: int) -> dict | None:
    cuentas = listar_cuentas()
    return next((c for c in cuentas if c["id"] == cuenta_id), None)


def crear_cuenta(plataforma_id: int, email: str, contrasena: str, plan_nombre: str,
                  max_perfiles: int, costo_mensual: float,
                  fecha_proximo_pago_proveedor: str = None) -> tuple[bool, str, int | None]:
    if not email.strip():
        return False, "El email/usuario de la cuenta es obligatorio.", None
    try:
        max_perfiles = int(max_perfiles)
        costo_mensual = float(costo_mensual)
        if max_perfiles < 1 or costo_mensual < 0:
            raise ValueError
    except (TypeError, ValueError):
        return False, "La cantidad de perfiles y el costo mensual deben ser números válidos.", None

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO stream_cuentas (plataforma_id, email, contrasena, plan_nombre, max_perfiles,
                                     costo_mensual, fecha_proximo_pago_proveedor)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (plataforma_id, email.strip(), contrasena.strip(), plan_nombre.strip(), max_perfiles,
          costo_mensual, fecha_proximo_pago_proveedor or None))
    cuenta_id = cursor.lastrowid

    # Se crean automáticamente los N perfiles (cupos) de la cuenta
    for i in range(1, max_perfiles + 1):
        nombre_perfil = "Cuenta Completa" if max_perfiles == 1 else f"Perfil {i}"
        cursor.execute("INSERT INTO stream_perfiles (cuenta_id, nombre_perfil) VALUES (?, ?)",
                       (cuenta_id, nombre_perfil))

    conn.commit()
    conn.close()
    return True, "Cuenta creada correctamente.", cuenta_id


def editar_cuenta(cuenta_id: int, email: str, contrasena: str, plan_nombre: str,
                   costo_mensual: float, fecha_proximo_pago_proveedor: str = None,
                   notas: str = "") -> tuple[bool, str]:
    if not email.strip():
        return False, "El email/usuario de la cuenta es obligatorio."
    try:
        costo_mensual = float(costo_mensual)
        if costo_mensual < 0:
            raise ValueError
    except (TypeError, ValueError):
        return False, "El costo mensual debe ser un número válido."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE stream_cuentas
        SET email = ?, contrasena = ?, plan_nombre = ?, costo_mensual = ?,
            fecha_proximo_pago_proveedor = ?, notas = ?
        WHERE id = ?
    """, (email.strip(), contrasena.strip(), plan_nombre.strip(), costo_mensual,
          fecha_proximo_pago_proveedor or None, notas.strip(), cuenta_id))
    conn.commit()
    conn.close()
    return True, "Cuenta actualizada correctamente."


def cambiar_estado_cuenta(cuenta_id: int, estado: str) -> tuple[bool, str]:
    if estado not in ESTADOS_CUENTA:
        return False, "Estado de cuenta inválido."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE stream_cuentas SET estado = ? WHERE id = ?", (estado, cuenta_id))
    conn.commit()
    conn.close()
    return True, f"Cuenta marcada como {estado}."


def rotar_password_cuenta(cuenta_id: int, nueva_contrasena: str) -> tuple[bool, str]:
    if not nueva_contrasena.strip():
        return False, "Ingresa la nueva contraseña."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE stream_cuentas SET contrasena = ?, fecha_ultimo_cambio_password = date('now', 'localtime')
        WHERE id = ?
    """, (nueva_contrasena.strip(), cuenta_id))
    conn.commit()
    conn.close()
    return True, "Contraseña actualizada. Recordá avisarle a los clientes con acceso a esta cuenta."


def eliminar_cuenta(cuenta_id: int) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM stream_perfiles WHERE cuenta_id = ? AND estado = 'Ocupado'", (cuenta_id,))
    if cursor.fetchone()[0] > 0:
        conn.close()
        return False, "Esta cuenta tiene perfiles ocupados por clientes; no se puede eliminar."
    cursor.execute("DELETE FROM stream_perfiles WHERE cuenta_id = ?", (cuenta_id,))
    cursor.execute("DELETE FROM stream_cuentas WHERE id = ?", (cuenta_id,))
    conn.commit()
    conn.close()
    return True, "Cuenta eliminada correctamente."


def cuentas_necesitan_rotacion_password(dias: int = 60) -> list[dict]:
    """Cuentas cuya contraseña no se cambia hace más de N días (política
    de rotación periódica, para evitar abuso de accesos compartidos)."""
    conn = conectar()
    cursor = conn.cursor()
    limite = (datetime.date.today() - datetime.timedelta(days=dias)).isoformat()
    cursor.execute("""
        SELECT c.id, p.nombre, c.email, c.fecha_ultimo_cambio_password
        FROM stream_cuentas c JOIN stream_plataformas p ON c.plataforma_id = p.id
        WHERE c.estado = 'Activa' AND c.fecha_ultimo_cambio_password <= ?
        ORDER BY c.fecha_ultimo_cambio_password
    """, (limite,))
    filas = cursor.fetchall()
    conn.close()
    return [{"id": f[0], "plataforma": f[1], "email": f[2], "fecha_ultimo_cambio_password": f[3]} for f in filas]


# ---------------- Perfiles ----------------
def listar_perfiles_cuenta(cuenta_id: int) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sp.id, sp.nombre_perfil, sp.pin, sp.estado, s.id, cl.nombre, s.fecha_vencimiento
        FROM stream_perfiles sp
        LEFT JOIN stream_suscripcion_perfiles ssp ON ssp.perfil_id = sp.id
        LEFT JOIN stream_suscripciones s ON ssp.suscripcion_id = s.id AND s.estado = 'Activa'
        LEFT JOIN clientes cl ON s.cliente_id = cl.id
        WHERE sp.cuenta_id = ?
        ORDER BY sp.nombre_perfil
    """, (cuenta_id,))
    filas = cursor.fetchall()
    conn.close()
    return [
        {"id": f[0], "nombre_perfil": f[1], "pin": f[2] or "", "estado": f[3],
         "suscripcion_id": f[4], "cliente": f[5] or "", "fecha_vencimiento": f[6] or ""}
        for f in filas
    ]


def editar_perfil(perfil_id: int, nombre_perfil: str, pin: str = "") -> tuple[bool, str]:
    if not nombre_perfil.strip():
        return False, "El nombre del perfil es obligatorio."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE stream_perfiles SET nombre_perfil = ?, pin = ? WHERE id = ?",
                   (nombre_perfil.strip(), pin.strip(), perfil_id))
    conn.commit()
    conn.close()
    return True, "Perfil actualizado."


def _perfiles_libres_de_plataforma(cursor, plataforma_id: int) -> list[tuple]:
    cursor.execute("""
        SELECT sp.id, sp.cuenta_id, c.email FROM stream_perfiles sp
        JOIN stream_cuentas c ON sp.cuenta_id = c.id
        WHERE c.plataforma_id = ? AND c.estado = 'Activa' AND sp.estado = 'Libre'
        ORDER BY sp.id
    """, (plataforma_id,))
    return cursor.fetchall()


def listar_perfiles_libres(plataforma_id: int) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    filas = _perfiles_libres_de_plataforma(cursor, plataforma_id)
    conn.close()
    return [{"id": f[0], "cuenta_id": f[1], "email": f[2]} for f in filas]


# ============================================================
# COMBOS
# ============================================================
def listar_combos(solo_activos: bool = True) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    where = "WHERE activo = 1" if solo_activos else ""
    cursor.execute(f"SELECT id, nombre, precio_mensual, activo FROM stream_combos {where} ORDER BY nombre")
    filas = cursor.fetchall()
    resultado = []
    for f in filas:
        cursor.execute("""
            SELECT p.nombre FROM stream_combo_plataformas cp JOIN stream_plataformas p ON cp.plataforma_id = p.id
            WHERE cp.combo_id = ?
        """, (f[0],))
        plataformas = [r[0] for r in cursor.fetchall()]
        resultado.append({"id": f[0], "nombre": f[1], "precio_mensual": f[2], "activo": bool(f[3]),
                          "plataformas": plataformas})
    conn.close()
    return resultado


def crear_combo(nombre: str, precio_mensual: float, plataforma_ids: list[int]) -> tuple[bool, str, int | None]:
    if not nombre.strip():
        return False, "El nombre del combo es obligatorio.", None
    if len(plataforma_ids) < 2:
        return False, "Un combo necesita al menos 2 plataformas.", None
    try:
        precio_mensual = float(precio_mensual)
        if precio_mensual < 0:
            raise ValueError
    except (TypeError, ValueError):
        return False, "El precio mensual debe ser un número válido.", None

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO stream_combos (nombre, precio_mensual) VALUES (?, ?)",
                   (nombre.strip(), precio_mensual))
    combo_id = cursor.lastrowid
    for pid in plataforma_ids:
        cursor.execute("INSERT INTO stream_combo_plataformas (combo_id, plataforma_id) VALUES (?, ?)",
                       (combo_id, pid))
    conn.commit()
    conn.close()
    return True, f"Combo '{nombre.strip()}' creado.", combo_id


def cambiar_estado_combo(combo_id: int, activo: bool) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE stream_combos SET activo = ? WHERE id = ?", (1 if activo else 0, combo_id))
    conn.commit()
    conn.close()
    return True, "Combo activado." if activo else "Combo desactivado."


def eliminar_combo(combo_id: int) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM stream_suscripciones WHERE combo_id = ? AND estado = 'Activa'",
                   (combo_id,))
    if cursor.fetchone()[0] > 0:
        conn.close()
        return False, "Este combo tiene suscripciones activas; no se puede eliminar."
    cursor.execute("DELETE FROM stream_combo_plataformas WHERE combo_id = ?", (combo_id,))
    cursor.execute("DELETE FROM stream_combos WHERE id = ?", (combo_id,))
    conn.commit()
    conn.close()
    return True, "Combo eliminado."


# ============================================================
# SUSCRIPCIONES (alquileres de perfil/cuenta/combo a un cliente)
# ============================================================
def _marcar_vencidas():
    """Pasa a estado 'Vencida' cualquier suscripción activa cuya fecha de
    vencimiento ya pasó (no libera los perfiles: eso se hace explícitamente
    al cancelar, para no perder el historial de a quién pertenecían)."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE stream_suscripciones SET estado = 'Vencida'
        WHERE estado = 'Activa' AND fecha_vencimiento < date('now', 'localtime')
    """)
    conn.commit()
    conn.close()


def crear_suscripcion(cliente_id: int, modalidad: str, precio_mensual: float, duracion_dias: int,
                       forma_pago: str = "Efectivo", max_dispositivos: int = 1,
                       perfil_id: int = None, cuenta_id: int = None, combo_id: int = None,
                       notas: str = "") -> tuple[bool, str, int | None]:
    """Crea la suscripción y ocupa el/los perfil(es) correspondientes:
    - Perfil Individual: se pasa 'perfil_id' (un perfil puntual ya elegido).
    - Acceso Completo: se pasa 'cuenta_id' (usa el único perfil de esa cuenta).
    - Combo: se pasa 'combo_id' (busca automáticamente un perfil libre en
      una cuenta activa de cada plataforma incluida en el combo)."""
    if modalidad not in MODALIDADES:
        return False, "Modalidad inválida.", None
    try:
        precio_mensual = float(precio_mensual)
        duracion_dias = int(duracion_dias)
        max_dispositivos = int(max_dispositivos)
        if precio_mensual < 0 or duracion_dias <= 0 or max_dispositivos < 1:
            raise ValueError
    except (TypeError, ValueError):
        return False, "El precio, la duración y los dispositivos deben ser números válidos.", None

    conn = conectar()
    cursor = conn.cursor()

    perfiles_a_ocupar = []

    if modalidad == "Perfil Individual":
        if perfil_id is None:
            conn.close()
            return False, "Elegí un perfil libre para asignar.", None
        cursor.execute("SELECT estado FROM stream_perfiles WHERE id = ?", (perfil_id,))
        fila = cursor.fetchone()
        if fila is None or fila[0] != "Libre":
            conn.close()
            return False, "Ese perfil ya no está libre.", None
        perfiles_a_ocupar = [perfil_id]

    elif modalidad == "Acceso Completo":
        if cuenta_id is None:
            conn.close()
            return False, "Elegí la cuenta a alquilar completa.", None
        cursor.execute("SELECT id, estado FROM stream_perfiles WHERE cuenta_id = ? AND estado = 'Libre'",
                       (cuenta_id,))
        libres = cursor.fetchall()
        if not libres:
            conn.close()
            return False, "Esa cuenta no tiene ningún cupo libre en este momento.", None
        perfiles_a_ocupar = [libres[0][0]]

    elif modalidad == "Combo":
        if combo_id is None:
            conn.close()
            return False, "Elegí el combo a contratar.", None
        cursor.execute("SELECT plataforma_id FROM stream_combo_plataformas WHERE combo_id = ?", (combo_id,))
        plataformas_combo = [r[0] for r in cursor.fetchall()]
        if not plataformas_combo:
            conn.close()
            return False, "Este combo no tiene plataformas configuradas.", None
        for plataforma_id in plataformas_combo:
            libres = _perfiles_libres_de_plataforma(cursor, plataforma_id)
            if not libres:
                cursor.execute("SELECT nombre FROM stream_plataformas WHERE id = ?", (plataforma_id,))
                fila_nombre = cursor.fetchone()
                nombre_plataforma = fila_nombre[0] if fila_nombre else "una de las plataformas"
                conn.close()
                return False, f"No hay ningún cupo libre en '{nombre_plataforma}' para armar este combo.", None
            perfiles_a_ocupar.append(libres[0][0])

    fecha_inicio = datetime.date.today().isoformat()
    fecha_vencimiento = (datetime.date.today() + datetime.timedelta(days=duracion_dias)).isoformat()

    cursor.execute("""
        INSERT INTO stream_suscripciones
            (cliente_id, combo_id, modalidad, fecha_inicio, fecha_vencimiento, precio_mensual,
             forma_pago, max_dispositivos, notas)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (cliente_id, combo_id, modalidad, fecha_inicio, fecha_vencimiento, precio_mensual,
          forma_pago, max_dispositivos, notas.strip()))
    suscripcion_id = cursor.lastrowid

    for pid in perfiles_a_ocupar:
        cursor.execute("INSERT INTO stream_suscripcion_perfiles (suscripcion_id, perfil_id) VALUES (?, ?)",
                       (suscripcion_id, pid))
        cursor.execute("UPDATE stream_perfiles SET estado = 'Ocupado' WHERE id = ?", (pid,))

    conn.commit()
    conn.close()
    return True, "Suscripción creada correctamente.", suscripcion_id


def obtener_suscripcion_detalle(suscripcion_id: int) -> dict | None:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id, s.cliente_id, cl.nombre, cl.telefono, s.combo_id, co.nombre,
               s.modalidad, s.fecha_inicio, s.fecha_vencimiento, s.precio_mensual, s.estado,
               s.forma_pago, s.max_dispositivos, s.notas
        FROM stream_suscripciones s
        JOIN clientes cl ON s.cliente_id = cl.id
        LEFT JOIN stream_combos co ON s.combo_id = co.id
        WHERE s.id = ?
    """, (suscripcion_id,))
    f = cursor.fetchone()
    if f is None:
        conn.close()
        return None

    cursor.execute("""
        SELECT sp.id, sp.nombre_perfil, sp.pin, c.email, p.nombre, sp.cuenta_id
        FROM stream_suscripcion_perfiles ssp
        JOIN stream_perfiles sp ON ssp.perfil_id = sp.id
        JOIN stream_cuentas c ON sp.cuenta_id = c.id
        JOIN stream_plataformas p ON c.plataforma_id = p.id
        WHERE ssp.suscripcion_id = ?
    """, (suscripcion_id,))
    perfiles = [
        {"perfil_id": r[0], "nombre_perfil": r[1], "pin": r[2] or "", "email_cuenta": r[3],
         "plataforma": r[4], "cuenta_id": r[5]}
        for r in cursor.fetchall()
    ]
    conn.close()

    dias_restantes = (datetime.date.fromisoformat(f[8]) - datetime.date.today()).days
    return {
        "id": f[0], "cliente_id": f[1], "cliente": f[2], "cliente_telefono": f[3] or "",
        "combo_id": f[4], "combo_nombre": f[5], "modalidad": f[6], "fecha_inicio": f[7],
        "fecha_vencimiento": f[8], "precio_mensual": f[9], "estado": f[10], "forma_pago": f[11],
        "max_dispositivos": f[12], "notas": f[13] or "", "perfiles": perfiles,
        "dias_restantes": dias_restantes,
    }


def listar_suscripciones(busqueda: str = "", solo_activas: bool = True) -> list[dict]:
    _marcar_vencidas()
    conn = conectar()
    cursor = conn.cursor()
    condiciones, parametros = [], []
    if solo_activas:
        condiciones.append("s.estado = 'Activa'")
    if busqueda.strip():
        condiciones.append("cl.nombre LIKE ?")
        parametros.append(f"%{busqueda.strip()}%")
    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    cursor.execute(f"""
        SELECT s.id, cl.nombre, s.modalidad, s.combo_id, co.nombre, s.fecha_vencimiento,
               s.precio_mensual, s.estado, s.forma_pago
        FROM stream_suscripciones s
        JOIN clientes cl ON s.cliente_id = cl.id
        LEFT JOIN stream_combos co ON s.combo_id = co.id
        {where}
        ORDER BY s.fecha_vencimiento
    """, parametros)
    filas = cursor.fetchall()

    resultado = []
    for f in filas:
        cursor.execute("""
            SELECT p.nombre FROM stream_suscripcion_perfiles ssp
            JOIN stream_perfiles sp ON ssp.perfil_id = sp.id
            JOIN stream_cuentas c ON sp.cuenta_id = c.id
            JOIN stream_plataformas p ON c.plataforma_id = p.id
            WHERE ssp.suscripcion_id = ?
        """, (f[0],))
        plataformas = [r[0] for r in cursor.fetchall()]
        dias_restantes = (datetime.date.fromisoformat(f[5]) - datetime.date.today()).days
        resultado.append({
            "id": f[0], "cliente": f[1], "modalidad": f[2], "combo_id": f[3],
            "combo_nombre": f[4], "plataformas": ", ".join(plataformas) or (f[4] or ""),
            "fecha_vencimiento": f[5], "precio_mensual": f[6], "estado": f[7],
            "forma_pago": f[8], "dias_restantes": dias_restantes,
        })
    conn.close()
    return resultado


def suscripciones_por_vencer(dias: int = 5) -> list[dict]:
    todas = listar_suscripciones(solo_activas=True)
    return [s for s in todas if 0 <= s["dias_restantes"] <= dias]


def registrar_pago_renovacion(suscripcion_id: int, usuario_id: int, dias_extension: int = 30,
                               monto: float = None, forma_pago: str = None,
                               cliente_id: int = None) -> tuple[bool, str, int | None]:
    """Cobra un período (genera una venta real, igual que en los otros
    módulos) y extiende la fecha de vencimiento de la suscripción."""
    detalle = obtener_suscripcion_detalle(suscripcion_id)
    if detalle is None:
        return False, "La suscripción no existe.", None
    if detalle["estado"] == "Cancelada":
        return False, "Esta suscripción está cancelada; no se le puede cobrar.", None

    monto = monto if monto is not None else detalle["precio_mensual"]
    try:
        monto = float(monto)
        dias_extension = int(dias_extension)
        if monto < 0 or dias_extension <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return False, "El monto y la duración deben ser números válidos.", None

    descripcion = f"Alquiler {detalle['modalidad']}"
    if detalle["combo_nombre"]:
        descripcion += f" - Combo {detalle['combo_nombre']}"
    elif detalle["perfiles"]:
        descripcion += " - " + ", ".join(sorted({p["plataforma"] for p in detalle["perfiles"]}))

    items_venta = [{"producto_id": None, "descripcion_libre": descripcion, "cantidad": 1,
                    "precio_unitario": monto}]
    ok, msg, venta_id = procesar_venta(
        items_venta, usuario_id, cliente_id or detalle["cliente_id"], condicion="contado",
        forma_pago=forma_pago or detalle["forma_pago"],
    )
    if not ok:
        return False, msg, None

    conn = conectar()
    cursor = conn.cursor()

    # La base para la extensión es el vencimiento actual si todavía no
    # venció (renovación anticipada), o la fecha de hoy si ya venció.
    fecha_actual_vto = datetime.date.fromisoformat(detalle["fecha_vencimiento"])
    base = max(fecha_actual_vto, datetime.date.today())
    nueva_fecha_vencimiento = (base + datetime.timedelta(days=dias_extension)).isoformat()
    periodo_desde = detalle["fecha_vencimiento"]

    cursor.execute("""
        UPDATE stream_suscripciones SET fecha_vencimiento = ?, estado = 'Activa' WHERE id = ?
    """, (nueva_fecha_vencimiento, suscripcion_id))
    cursor.execute("""
        INSERT INTO stream_pagos (suscripcion_id, periodo_desde, periodo_hasta, monto, venta_id, usuario_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (suscripcion_id, periodo_desde, nueva_fecha_vencimiento, monto, venta_id, usuario_id))
    conn.commit()
    conn.close()
    return True, f"Pago registrado. Nuevo vencimiento: {nueva_fecha_vencimiento}.", venta_id


def cancelar_suscripcion(suscripcion_id: int) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT estado FROM stream_suscripciones WHERE id = ?", (suscripcion_id,))
    fila = cursor.fetchone()
    if fila is None:
        conn.close()
        return False, "La suscripción no existe."
    if fila[0] == "Cancelada":
        conn.close()
        return False, "Esta suscripción ya estaba cancelada."

    cursor.execute("SELECT perfil_id FROM stream_suscripcion_perfiles WHERE suscripcion_id = ?",
                   (suscripcion_id,))
    for (perfil_id,) in cursor.fetchall():
        cursor.execute("UPDATE stream_perfiles SET estado = 'Libre' WHERE id = ?", (perfil_id,))

    cursor.execute("UPDATE stream_suscripciones SET estado = 'Cancelada' WHERE id = ?", (suscripcion_id,))
    conn.commit()
    conn.close()
    return True, "Suscripción cancelada. Los perfiles quedaron libres para volver a alquilarlos."


def listar_historial_pagos(suscripcion_id: int) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT fecha_pago, periodo_desde, periodo_hasta, monto, venta_id
        FROM stream_pagos WHERE suscripcion_id = ? ORDER BY fecha_pago DESC
    """, (suscripcion_id,))
    filas = cursor.fetchall()
    conn.close()
    return [{"fecha_pago": f[0], "periodo_desde": f[1], "periodo_hasta": f[2], "monto": f[3], "venta_id": f[4]}
            for f in filas]


# ============================================================
# DASHBOARD Y REPORTES
# ============================================================
def conteos_dashboard() -> dict:
    _marcar_vencidas()
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM stream_cuentas WHERE estado = 'Activa'")
    cuentas_activas = cursor.fetchone()[0]
    cursor.execute("""
        SELECT COUNT(*) FROM stream_perfiles sp JOIN stream_cuentas c ON sp.cuenta_id = c.id
        WHERE c.estado = 'Activa' AND sp.estado = 'Libre'
    """)
    perfiles_libres = cursor.fetchone()[0]
    cursor.execute("""
        SELECT COUNT(*) FROM stream_perfiles sp JOIN stream_cuentas c ON sp.cuenta_id = c.id
        WHERE c.estado = 'Activa' AND sp.estado = 'Ocupado'
    """)
    perfiles_ocupados = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM stream_suscripciones WHERE estado = 'Activa'")
    suscripciones_activas = cursor.fetchone()[0]
    cursor.execute("SELECT COALESCE(SUM(costo_mensual), 0) FROM stream_cuentas WHERE estado = 'Activa'")
    costo_mensual_total = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COALESCE(SUM(precio_mensual), 0) FROM stream_suscripciones WHERE estado = 'Activa'")
    ingreso_mensual_estimado = cursor.fetchone()[0] or 0
    conn.close()
    return {
        "cuentas_activas": cuentas_activas, "perfiles_libres": perfiles_libres,
        "perfiles_ocupados": perfiles_ocupados, "suscripciones_activas": suscripciones_activas,
        "costo_mensual_total": costo_mensual_total, "ingreso_mensual_estimado": ingreso_mensual_estimado,
        "margen_mensual_estimado": ingreso_mensual_estimado - costo_mensual_total,
        "cuentas_por_rotar_password": len(cuentas_necesitan_rotacion_password()),
        "suscripciones_por_vencer": len(suscripciones_por_vencer()),
    }


def rentabilidad_por_plataforma() -> list[dict]:
    """Ingreso (suma de precio_mensual de suscripciones activas que usan
    perfiles de esa plataforma, prorrateado si es un combo) vs costo
    (suma de costo_mensual de las cuentas activas) por plataforma."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM stream_plataformas WHERE activa = 1 ORDER BY nombre")
    plataformas = cursor.fetchall()

    resultado = []
    for plataforma_id, nombre in plataformas:
        cursor.execute("SELECT COALESCE(SUM(costo_mensual), 0) FROM stream_cuentas "
                       "WHERE plataforma_id = ? AND estado = 'Activa'", (plataforma_id,))
        costo = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT s.id, s.precio_mensual, s.combo_id
            FROM stream_suscripciones s
            JOIN stream_suscripcion_perfiles ssp ON ssp.suscripcion_id = s.id
            JOIN stream_perfiles sp ON ssp.perfil_id = sp.id
            JOIN stream_cuentas c ON sp.cuenta_id = c.id
            WHERE c.plataforma_id = ? AND s.estado = 'Activa'
        """, (plataforma_id,))
        ingreso = 0
        for _sid, precio, combo_id in cursor.fetchall():
            if combo_id:
                cursor.execute("SELECT COUNT(*) FROM stream_combo_plataformas WHERE combo_id = ?", (combo_id,))
                cant_plataformas_combo = cursor.fetchone()[0] or 1
                ingreso += precio / cant_plataformas_combo
            else:
                ingreso += precio

        resultado.append({
            "plataforma": nombre, "costo_mensual": costo, "ingreso_mensual": ingreso,
            "margen": ingreso - costo,
        })
    conn.close()
    return resultado
