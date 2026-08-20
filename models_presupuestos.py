"""
models_presupuestos.py
Lógica de negocio del módulo Presupuestos: armar una cotización para un
cliente (existente o walk-in), con artículos, precios y fecha de validez,
sin afectar stock ni caja. Un presupuesto puede aprobarse, rechazarse, o
convertirse en una venta real (momento en el que sí se descuenta stock).
"""
import datetime
from database import conectar

ESTADOS = ["Pendiente", "Aprobado", "Rechazado", "Convertido"]


def _estado_efectivo(estado: str, fecha_validez: str) -> str:
    """Un presupuesto 'Pendiente' cuya fecha de validez ya pasó se muestra
    como 'Vencido' (estado calculado, no se persiste en la base)."""
    if estado == "Pendiente" and fecha_validez:
        try:
            if datetime.date.fromisoformat(fecha_validez[:10]) < datetime.date.today():
                return "Vencido"
        except ValueError:
            pass
    return estado


def _fila_a_dict(f) -> dict:
    return {
        "id": f[0], "fecha": f[1], "cliente_id": f[2], "cliente": f[3] or "Sin cliente",
        "fecha_validez": f[4] or "", "estado": f[5],
        "estado_efectivo": _estado_efectivo(f[5], f[4] or ""),
        "total": f[6] or 0, "vendedor": f[7] or "", "venta_id": f[8],
    }


_SELECT_BASE = """
    SELECT p.id, p.fecha, p.cliente_id,
           COALESCE(NULLIF(cl.nombre, ''), p.cliente_nombre, 'Sin datos'),
           p.fecha_validez, p.estado, p.total, u.nombre_completo, p.venta_id
    FROM presupuestos p
    LEFT JOIN clientes cl ON p.cliente_id = cl.id
    LEFT JOIN usuarios u  ON p.usuario_id  = u.id
"""


# ============================================================
# CREAR / EDITAR
# ============================================================
def crear_presupuesto(items: list[dict], usuario_id: int, cliente_id: int | None = None,
                       cliente_nombre: str = "", cliente_documento: str = "",
                       cliente_direccion: str = "", cliente_telefono: str = "",
                       fecha_validez: str = "", observaciones: str = "") -> tuple[bool, str, int | None]:
    """items: [{"producto_id":.., "descripcion_libre":.., "cantidad":.., "precio_unitario":..}, ...]"""
    if not items:
        return False, "No hay productos cargados en el presupuesto.", None

    conn = conectar()
    cursor = conn.cursor()
    try:
        total = sum(i["cantidad"] * i["precio_unitario"] for i in items)
        cursor.execute("""
            INSERT INTO presupuestos
                (cliente_id, cliente_nombre, cliente_documento, cliente_direccion,
                 cliente_telefono, fecha_validez, estado, observaciones, total, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?, 'Pendiente', ?, ?, ?)
        """, (cliente_id, cliente_nombre.strip(), cliente_documento.strip(),
              cliente_direccion.strip(), cliente_telefono.strip(), fecha_validez or None,
              observaciones.strip(), total, usuario_id))
        presupuesto_id = cursor.lastrowid

        for item in items:
            cursor.execute("""
                INSERT INTO detalle_presupuestos
                    (presupuesto_id, producto_id, descripcion_libre, cantidad, precio_unitario)
                VALUES (?, ?, ?, ?, ?)
            """, (presupuesto_id, item.get("producto_id"), item.get("descripcion_libre"),
                  item["cantidad"], item["precio_unitario"]))

        conn.commit()
        return True, f"Presupuesto Nro. {presupuesto_id} generado correctamente.", presupuesto_id
    except Exception as e:
        conn.rollback()
        return False, f"Error al generar el presupuesto: {e}", None
    finally:
        conn.close()


def actualizar_presupuesto(presupuesto_id: int, items: list[dict], cliente_id: int | None,
                            cliente_nombre: str, cliente_documento: str, cliente_direccion: str,
                            cliente_telefono: str, fecha_validez: str,
                            observaciones: str) -> tuple[bool, str]:
    if not items:
        return False, "No hay productos cargados en el presupuesto."

    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT estado FROM presupuestos WHERE id = ?", (presupuesto_id,))
        fila = cursor.fetchone()
        if fila is None:
            conn.close()
            return False, "El presupuesto no existe."
        if fila[0] != "Pendiente":
            conn.close()
            return False, f"No se puede modificar: el presupuesto ya está '{fila[0]}'."

        total = sum(i["cantidad"] * i["precio_unitario"] for i in items)
        cursor.execute("""
            UPDATE presupuestos
            SET cliente_id = ?, cliente_nombre = ?, cliente_documento = ?, cliente_direccion = ?,
                cliente_telefono = ?, fecha_validez = ?, observaciones = ?, total = ?
            WHERE id = ?
        """, (cliente_id, cliente_nombre.strip(), cliente_documento.strip(), cliente_direccion.strip(),
              cliente_telefono.strip(), fecha_validez or None, observaciones.strip(), total,
              presupuesto_id))
        cursor.execute("DELETE FROM detalle_presupuestos WHERE presupuesto_id = ?", (presupuesto_id,))
        for item in items:
            cursor.execute("""
                INSERT INTO detalle_presupuestos
                    (presupuesto_id, producto_id, descripcion_libre, cantidad, precio_unitario)
                VALUES (?, ?, ?, ?, ?)
            """, (presupuesto_id, item.get("producto_id"), item.get("descripcion_libre"),
                  item["cantidad"], item["precio_unitario"]))
        conn.commit()
        return True, "Presupuesto actualizado correctamente."
    except Exception as e:
        conn.rollback()
        return False, f"Error al actualizar el presupuesto: {e}"
    finally:
        conn.close()


# ============================================================
# LISTADOS Y DETALLE
# ============================================================
def listar_presupuestos(estado_filtro: str = "todos", busqueda: str = "") -> list[dict]:
    """estado_filtro: 'todos' o uno de ESTADOS + 'Vencido'."""
    conn = conectar()
    cursor = conn.cursor()
    condiciones = []
    parametros: list = []
    if busqueda.strip():
        condiciones.append(
            "(COALESCE(cl.nombre,'') LIKE ? OR p.cliente_nombre LIKE ? OR CAST(p.id AS TEXT) LIKE ?)"
        )
        q = f"%{busqueda.strip()}%"
        parametros += [q, q, q]
    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    cursor.execute(f"{_SELECT_BASE} {where} ORDER BY p.id DESC", parametros)
    filas = [_fila_a_dict(f) for f in cursor.fetchall()]
    conn.close()

    if estado_filtro != "todos":
        filas = [f for f in filas if f["estado_efectivo"] == estado_filtro]
    return filas


def obtener_presupuesto(presupuesto_id: int) -> dict | None:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT p.id, p.fecha, p.cliente_id, p.cliente_nombre, p.cliente_documento,
               p.cliente_direccion, p.cliente_telefono, p.fecha_validez, p.estado,
               p.observaciones, p.total, u.nombre_completo, p.venta_id,
               COALESCE(cl.nombre, '')
        FROM presupuestos p
        LEFT JOIN clientes cl ON p.cliente_id = cl.id
        LEFT JOIN usuarios u  ON p.usuario_id  = u.id
        WHERE p.id = ?
    """, (presupuesto_id,))
    f = cursor.fetchone()
    if f is None:
        conn.close()
        return None

    cursor.execute("""
        SELECT dp.id, dp.producto_id, COALESCE(p.nombre, dp.descripcion_libre, '(Artículo libre)'),
               dp.cantidad, dp.precio_unitario, p.unidad_medida
        FROM detalle_presupuestos dp
        LEFT JOIN productos p ON dp.producto_id = p.id
        WHERE dp.presupuesto_id = ?
        ORDER BY dp.id
    """, (presupuesto_id,))
    items = []
    for it in cursor.fetchall():
        items.append({
            "detalle_id": it[0], "producto_id": it[1], "nombre": it[2],
            "cantidad": it[3], "precio_unitario": it[4], "importe": it[3] * it[4],
            "unidad_medida": it[5] or "Unidad", "es_libre": it[1] is None,
        })
    conn.close()

    cliente_nombre_final = f[13] if f[13] else (f[3] or "Sin datos")
    return {
        "id": f[0], "fecha": f[1], "cliente_id": f[2], "cliente_nombre": cliente_nombre_final,
        "cliente_documento": f[4] or "", "cliente_direccion": f[5] or "",
        "cliente_telefono": f[6] or "", "fecha_validez": f[7] or "", "estado": f[8],
        "estado_efectivo": _estado_efectivo(f[8], f[7] or ""), "observaciones": f[9] or "",
        "total": f[10] or 0, "vendedor": f[11] or "", "venta_id": f[12], "items": items,
    }


# ============================================================
# CAMBIOS DE ESTADO / CONVERSIÓN / ELIMINACIÓN
# ============================================================
def cambiar_estado_presupuesto(presupuesto_id: int, nuevo_estado: str) -> tuple[bool, str]:
    if nuevo_estado not in ("Aprobado", "Rechazado", "Pendiente"):
        return False, "Estado inválido."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT estado FROM presupuestos WHERE id = ?", (presupuesto_id,))
    fila = cursor.fetchone()
    if fila is None:
        conn.close()
        return False, "El presupuesto no existe."
    if fila[0] == "Convertido":
        conn.close()
        return False, "Este presupuesto ya fue convertido en una venta; no se puede cambiar su estado."
    cursor.execute("UPDATE presupuestos SET estado = ? WHERE id = ?", (nuevo_estado, presupuesto_id))
    conn.commit()
    conn.close()
    return True, f"El presupuesto Nro. {presupuesto_id} ahora está '{nuevo_estado}'."


def marcar_convertido(presupuesto_id: int, venta_id: int) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE presupuestos SET estado = 'Convertido', venta_id = ? WHERE id = ?",
                   (venta_id, presupuesto_id))
    conn.commit()
    conn.close()
    return True, "Presupuesto marcado como convertido."


def eliminar_presupuesto(presupuesto_id: int) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT estado FROM presupuestos WHERE id = ?", (presupuesto_id,))
    fila = cursor.fetchone()
    if fila is None:
        conn.close()
        return False, "El presupuesto no existe."
    if fila[0] == "Convertido":
        conn.close()
        return False, "No se puede eliminar: este presupuesto ya fue convertido en una venta."
    cursor.execute("DELETE FROM presupuestos WHERE id = ?", (presupuesto_id,))
    conn.commit()
    conn.close()
    return True, "Presupuesto eliminado."


# ============================================================
# CONSULTAS PARA EL MÓDULO REPORTES
# ============================================================
def listar_presupuestos_en_rango(fecha_desde: str, fecha_hasta: str,
                                  estado: str | None = None, busqueda: str = "") -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    condiciones = ["date(p.fecha) BETWEEN ? AND ?"]
    parametros: list = [fecha_desde, fecha_hasta]
    if busqueda.strip():
        condiciones.append("(COALESCE(cl.nombre,'') LIKE ? OR p.cliente_nombre LIKE ?)")
        q = f"%{busqueda.strip()}%"
        parametros += [q, q]
    where = f"WHERE {' AND '.join(condiciones)}"
    cursor.execute(f"{_SELECT_BASE} {where} ORDER BY p.fecha DESC", parametros)
    filas = [_fila_a_dict(f) for f in cursor.fetchall()]
    conn.close()
    if estado:
        filas = [f for f in filas if f["estado_efectivo"] == estado]
    return filas


def resumen_presupuestos_en_rango(fecha_desde: str, fecha_hasta: str) -> dict:
    presupuestos = listar_presupuestos_en_rango(fecha_desde, fecha_hasta)
    cantidad = len(presupuestos)
    total_cotizado = sum(p["total"] for p in presupuestos)
    convertidos = [p for p in presupuestos if p["estado_efectivo"] == "Convertido"]
    aprobados = [p for p in presupuestos if p["estado_efectivo"] in ("Aprobado", "Convertido")]
    total_convertido = sum(p["total"] for p in convertidos)
    tasa_conversion = (len(convertidos) / cantidad * 100) if cantidad else 0
    return {
        "presupuestos": presupuestos, "cantidad": cantidad, "total_cotizado": total_cotizado,
        "cantidad_aprobados": len(aprobados), "cantidad_convertidos": len(convertidos),
        "total_convertido": total_convertido, "tasa_conversion": round(tasa_conversion, 1),
    }


def productos_mas_presupuestados_en_rango(fecha_desde: str, fecha_hasta: str, limite: int = 10) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(pr.nombre, dp.descripcion_libre, 'Producto eliminado') AS nombre,
               SUM(dp.cantidad) AS cantidad, SUM(dp.cantidad * dp.precio_unitario) AS importe
        FROM detalle_presupuestos dp
        JOIN presupuestos p ON dp.presupuesto_id = p.id
        LEFT JOIN productos pr ON dp.producto_id = pr.id
        WHERE date(p.fecha) BETWEEN ? AND ?
        GROUP BY nombre
        ORDER BY importe DESC
        LIMIT ?
    """, (fecha_desde, fecha_hasta, limite))
    filas = cursor.fetchall()
    conn.close()
    return [{"nombre": f[0], "cantidad": f[1] or 0, "importe": f[2] or 0} for f in filas]


def presupuestos_por_dia_en_rango(fecha_desde: str, fecha_hasta: str) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT date(fecha) AS dia, SUM(total)
        FROM presupuestos
        WHERE date(fecha) BETWEEN ? AND ?
        GROUP BY dia ORDER BY dia
    """, (fecha_desde, fecha_hasta))
    filas = cursor.fetchall()
    conn.close()
    return [{"fecha": f[0], "total": f[1] or 0} for f in filas]
