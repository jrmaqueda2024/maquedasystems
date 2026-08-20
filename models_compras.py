"""
models_compras.py
Lógica de negocio del módulo Compras: registrar una compra a proveedor
(cabecera + detalle), lo que además:
- Suma stock a cada producto comprado.
- Actualiza el precio de compra del producto (para futuras referencias).
- Deja constancia en movimientos_inventario (motivo "Compra de Productos"),
  igual que hace una Entrada de Inventario manual, para que el historial
  de cada producto quede completo.

Sigue el mismo patrón transaccional que procesar_venta() en models_ventas.py:
todo se hace con un único cursor/conexión y se hace commit/rollback en bloque.
"""
from database import conectar


class ErrorDeCompra(Exception):
    pass


# ---------------- LISTADO ----------------
def listar_compras(texto_busqueda: str = "") -> list[dict]:
    """Devuelve las compras registradas (cabecera), más recientes primero.
    Permite filtrar por proveedor, número de comprobante o código (id)."""
    conn = conectar()
    cursor = conn.cursor()

    condiciones = []
    parametros = []
    if texto_busqueda.strip():
        condiciones.append(
            "(pr.nombre LIKE ? OR c.nro_comprobante LIKE ? OR CAST(c.id AS TEXT) LIKE ?)"
        )
        comodin = f"%{texto_busqueda.strip()}%"
        parametros.extend([comodin, comodin, comodin])
    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    cursor.execute(f"""
        SELECT c.id, c.fecha_y_hora, c.fecha_compra, c.nro_comprobante,
               c.importe, c.proveedor_id, pr.nombre
        FROM compras c
        LEFT JOIN proveedores pr ON c.proveedor_id = pr.id
        {where}
        ORDER BY c.id DESC
    """, parametros)
    filas = cursor.fetchall()
    conn.close()

    return [
        {
            "id": f[0],
            "fecha_y_hora": f[1],
            "fecha_compra": f[2],
            "nro_comprobante": f[3] or "",
            "importe": f[4] or 0,
            "proveedor_id": f[5],
            "proveedor": f[6] or "Sin proveedor",
        }
        for f in filas
    ]


def obtener_detalle_compra(compra_id: int) -> dict | None:
    """Devuelve la cabecera y las líneas de una compra, para verla en detalle."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.fecha_y_hora, c.fecha_compra, c.nro_comprobante,
               c.importe, c.proveedor_id, pr.nombre
        FROM compras c
        LEFT JOIN proveedores pr ON c.proveedor_id = pr.id
        WHERE c.id = ?
    """, (compra_id,))
    cabecera = cursor.fetchone()
    if cabecera is None:
        conn.close()
        return None

    cursor.execute("""
        SELECT dc.id, dc.producto_id, dc.producto_nombre_historico,
               dc.cantidad, dc.precio_unitario, p.nombre
        FROM detalle_compras dc
        LEFT JOIN productos p ON dc.producto_id = p.id
        WHERE dc.compra_id = ?
        ORDER BY dc.id
    """, (compra_id,))
    filas_detalle = cursor.fetchall()
    conn.close()

    items = [
        {
            "id": f[0],
            "producto_id": f[1],
            "nombre": f[5] or f[2] or "Producto eliminado",
            "cantidad": f[3],
            "precio_unitario": f[4],
            "importe": f[3] * f[4],
        }
        for f in filas_detalle
    ]

    return {
        "id": cabecera[0],
        "fecha_y_hora": cabecera[1],
        "fecha_compra": cabecera[2],
        "nro_comprobante": cabecera[3] or "",
        "importe": cabecera[4] or 0,
        "proveedor_id": cabecera[5],
        "proveedor": cabecera[6] or "Sin proveedor",
        "items": items,
    }


# ---------------- REGISTRAR NUEVA COMPRA ----------------
def crear_compra(items: list[dict], fecha_compra: str, usuario_id: int,
                  proveedor_id: int | None = None,
                  nro_comprobante: str = "") -> tuple[bool, str, int | None]:
    """
    Registra una compra completa.

    items: lista de dicts con {"producto_id": int, "cantidad": float, "precio_unitario": float}
    fecha_compra: fecha del comprobante en formato ISO ('YYYY-MM-DD').

    Por cada línea: suma el stock del producto, actualiza su precio de
    compra, y registra el movimiento de inventario correspondiente.

    Devuelve (exito, mensaje, compra_id).
    """
    if not items:
        return False, "No hay productos cargados en la compra.", None
    if not fecha_compra:
        return False, "La fecha de compra es obligatoria.", None

    conn = conectar()
    cursor = conn.cursor()
    try:
        # 1. Validar que todos los productos existan
        for item in items:
            cursor.execute("SELECT id FROM productos WHERE id = ?", (item["producto_id"],))
            if cursor.fetchone() is None:
                raise ErrorDeCompra(f"El producto con código {item['producto_id']} no existe.")
            if item["cantidad"] is None or item["cantidad"] <= 0:
                raise ErrorDeCompra("Todas las cantidades deben ser mayores a cero.")
            if item["precio_unitario"] is None or item["precio_unitario"] < 0:
                raise ErrorDeCompra("El precio de compra no puede ser negativo.")

        # 2. Calcular el importe total
        importe_total = sum(item["cantidad"] * item["precio_unitario"] for item in items)

        # 3. Insertar la cabecera de la compra
        cursor.execute("""
            INSERT INTO compras (proveedor_id, fecha_compra, nro_comprobante, importe)
            VALUES (?, ?, ?, ?)
        """, (proveedor_id, fecha_compra, (nro_comprobante or "").strip(), importe_total))
        compra_id = cursor.lastrowid

        # 4. Insertar el detalle, sumar stock y actualizar precio de compra
        from models_inventario import registrar_movimiento_externo
        for item in items:
            cursor.execute("SELECT nombre, stock FROM productos WHERE id = ?", (item["producto_id"],))
            nombre, stock_actual = cursor.fetchone()

            cursor.execute("""
                INSERT INTO detalle_compras
                    (compra_id, producto_id, producto_nombre_historico, cantidad, precio_unitario)
                VALUES (?, ?, ?, ?, ?)
            """, (compra_id, item["producto_id"], nombre, item["cantidad"], item["precio_unitario"]))

            nuevo_stock = (stock_actual or 0) + item["cantidad"]
            cursor.execute(
                "UPDATE productos SET stock = ?, precio_compra = ? WHERE id = ?",
                (nuevo_stock, item["precio_unitario"], item["producto_id"]),
            )

            registrar_movimiento_externo(
                cursor, item["producto_id"], "entrada", item["cantidad"],
                f"Compra de Productos - Comprobante Nro. {(nro_comprobante or compra_id)}",
                usuario_id, nuevo_stock,
                nro_comprobante=str(nro_comprobante or compra_id),
            )

        conn.commit()
        return True, f"Compra Nro. {compra_id} registrada correctamente.", compra_id

    except ErrorDeCompra as e:
        conn.rollback()
        return False, str(e), None
    except Exception as e:
        conn.rollback()
        return False, f"Error inesperado al registrar la compra: {e}", None
    finally:
        conn.close()


def eliminar_compra(compra_id: int) -> tuple[bool, str]:
    """Elimina una compra y su detalle. NO revierte el stock ni los
    movimientos de inventario ya generados, para no alterar el historial;
    solo se usa para corregir errores de carga evidentes."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM compras WHERE id = ?", (compra_id,))
    if cursor.fetchone() is None:
        conn.close()
        return False, "La compra no existe."
    cursor.execute("DELETE FROM compras WHERE id = ?", (compra_id,))
    conn.commit()
    conn.close()
    return True, "Compra eliminada."


# ============================================================
# CONSULTAS PARA EL MÓDULO REPORTES (filtros por rango de fechas)
# ============================================================
def listar_compras_en_rango(fecha_desde: str, fecha_hasta: str,
                             proveedor_id: int | None = None,
                             busqueda: str = "") -> list[dict]:
    """Igual que listar_compras(), pero filtrando por fecha_compra dentro
    de un rango, y opcionalmente por proveedor. Usado por el Reporte de
    Compras (módulo Reportes)."""
    conn = conectar()
    cursor = conn.cursor()

    condiciones = ["date(c.fecha_compra) BETWEEN ? AND ?"]
    parametros: list = [fecha_desde, fecha_hasta]
    if proveedor_id:
        condiciones.append("c.proveedor_id = ?")
        parametros.append(proveedor_id)
    if busqueda.strip():
        condiciones.append("(pr.nombre LIKE ? OR c.nro_comprobante LIKE ? OR CAST(c.id AS TEXT) LIKE ?)")
        comodin = f"%{busqueda.strip()}%"
        parametros.extend([comodin, comodin, comodin])
    where = f"WHERE {' AND '.join(condiciones)}"

    cursor.execute(f"""
        SELECT c.id, c.fecha_y_hora, c.fecha_compra, c.nro_comprobante,
               c.importe, c.proveedor_id, pr.nombre
        FROM compras c
        LEFT JOIN proveedores pr ON c.proveedor_id = pr.id
        {where}
        ORDER BY c.fecha_compra DESC, c.id DESC
    """, parametros)
    filas = cursor.fetchall()
    conn.close()

    return [
        {
            "id": f[0],
            "fecha_y_hora": f[1],
            "fecha_compra": f[2],
            "nro_comprobante": f[3] or "",
            "importe": f[4] or 0,
            "proveedor_id": f[5],
            "proveedor": f[6] or "Sin proveedor",
        }
        for f in filas
    ]


def resumen_compras_en_rango(fecha_desde: str, fecha_hasta: str,
                              proveedor_id: int | None = None,
                              busqueda: str = "") -> dict:
    """Indicadores generales del período (para las tarjetas del reporte)."""
    compras = listar_compras_en_rango(fecha_desde, fecha_hasta, proveedor_id, busqueda)
    total = sum(c["importe"] for c in compras)
    cantidad = len(compras)
    promedio = (total / cantidad) if cantidad else 0
    proveedores_distintos = len({c["proveedor_id"] for c in compras if c["proveedor_id"]})
    return {
        "compras": compras,
        "cantidad": cantidad,
        "total": total,
        "promedio": promedio,
        "proveedores_distintos": proveedores_distintos,
    }


def compras_por_dia_en_rango(fecha_desde: str, fecha_hasta: str) -> list[dict]:
    """Total comprado por día, para el gráfico de barras del PDF con dashboard."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT date(fecha_compra) AS dia, SUM(importe)
        FROM compras
        WHERE date(fecha_compra) BETWEEN ? AND ?
        GROUP BY dia
        ORDER BY dia
    """, (fecha_desde, fecha_hasta))
    filas = cursor.fetchall()
    conn.close()
    return [{"fecha": f[0], "total": f[1] or 0} for f in filas]


def productos_mas_comprados_en_rango(fecha_desde: str, fecha_hasta: str, limite: int = 10) -> list[dict]:
    """Ranking de productos por importe comprado en el período."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(p.nombre, dc.producto_nombre_historico, 'Producto eliminado') AS nombre,
               SUM(dc.cantidad) AS cantidad, SUM(dc.cantidad * dc.precio_unitario) AS importe
        FROM detalle_compras dc
        JOIN compras c ON dc.compra_id = c.id
        LEFT JOIN productos p ON dc.producto_id = p.id
        WHERE date(c.fecha_compra) BETWEEN ? AND ?
        GROUP BY nombre
        ORDER BY importe DESC
        LIMIT ?
    """, (fecha_desde, fecha_hasta, limite))
    filas = cursor.fetchall()
    conn.close()
    return [{"nombre": f[0], "cantidad": f[1] or 0, "importe": f[2] or 0} for f in filas]


def proveedores_en_rango(fecha_desde: str, fecha_hasta: str) -> list[dict]:
    """Total comprado a cada proveedor en el período, de mayor a menor."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(pr.nombre, 'Sin proveedor') AS proveedor, COUNT(*), SUM(c.importe)
        FROM compras c
        LEFT JOIN proveedores pr ON c.proveedor_id = pr.id
        WHERE date(c.fecha_compra) BETWEEN ? AND ?
        GROUP BY proveedor
        ORDER BY SUM(c.importe) DESC
    """, (fecha_desde, fecha_hasta))
    filas = cursor.fetchall()
    conn.close()
    return [{"proveedor": f[0], "cantidad": f[1] or 0, "total": f[2] or 0} for f in filas]
