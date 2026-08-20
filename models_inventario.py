"""
models_inventario.py
Lógica de negocio del módulo Inventario: registrar entradas y salidas de
stock, editar el stock mínimo, y consultar el historial de movimientos
de un producto.
"""
from database import conectar

MOTIVOS_ENTRADA = ["Compra de Productos", "Ajuste de Inventario", "Devolución de Cliente", "Otro"]
MOTIVOS_SALIDA = ["Devolución de Producto", "Ajuste de Inventario", "Producto Dañado/Perdido", "Uso Interno", "Otro"]


def _insertar_movimiento(cursor, producto_id: int, tipo: str, cantidad: float,
                          motivo: str, usuario_id, stock_resultante: float,
                          nro_comprobante: str = "", observaciones: str = "",
                          es_ilimitado: bool = False):
    """Inserta una fila en movimientos_inventario. Pensado para reutilizarse
    dentro de la MISMA transacción/cursor de quien ya está modificando el
    stock (ventas, devoluciones, alta y edición de productos), para que el
    historial de movimientos quede siempre completo y consistente con el
    stock real, sin duplicar la lógica de INSERT en cada módulo.

    es_ilimitado=True marca el movimiento como perteneciente a un producto
    con control de stock "Ilimitado": la cantidad no representa unidades
    reales descontadas/sumadas del inventario (ese producto no lleva stock
    numérico), sino que el movimiento se guarda solo para trazabilidad. La
    UI del historial usa este flag para mostrar "Ilimitado" en vez de un
    número en las columnas de Cantidad y Stock Resultante."""
    cursor.execute("""
        INSERT INTO movimientos_inventario
            (producto_id, tipo, cantidad, motivo, usuario_id, nro_comprobante,
             observaciones, stock_resultante, es_ilimitado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (producto_id, tipo, cantidad, motivo, usuario_id,
          (nro_comprobante or "").strip(), (observaciones or "").strip(),
          stock_resultante, 1 if es_ilimitado else 0))


def registrar_entrada(producto_id: int, cantidad: float, motivo: str, usuario_id: int,
                       nro_comprobante: str = "", observaciones: str = "",
                       precio_compra: float = None, precio_venta: float = None,
                       precio_mayorista: float = None) -> tuple[bool, str]:
    """Registra una entrada de inventario: suma stock y, si se indicaron precios
    nuevos, actualiza los precios del producto para ventas/compras futuras."""
    if cantidad is None or cantidad <= 0:
        return False, "La cantidad a agregar debe ser mayor a cero."

    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT stock, nombre FROM productos WHERE id = ?", (producto_id,))
        fila = cursor.fetchone()
        if fila is None:
            return False, "El producto no existe."
        stock_actual, nombre = fila
        nuevo_stock = (stock_actual or 0) + cantidad

        cursor.execute("UPDATE productos SET stock = ? WHERE id = ?", (nuevo_stock, producto_id))

        # Actualizar precios del producto si se ingresaron (afecta ventas futuras)
        sets, valores = [], []
        if precio_compra is not None:
            sets.append("precio_compra = ?")
            valores.append(precio_compra)
        if precio_venta is not None:
            sets.append("precio = ?")
            valores.append(precio_venta)
        if precio_mayorista is not None:
            sets.append("precio_mayorista = ?")
            valores.append(precio_mayorista)
        if sets:
            valores.append(producto_id)
            cursor.execute(f"UPDATE productos SET {', '.join(sets)} WHERE id = ?", valores)

        _insertar_movimiento(cursor, producto_id, "entrada", cantidad, motivo,
                             usuario_id, nuevo_stock, nro_comprobante, observaciones)

        conn.commit()
        return True, f"Se agregaron {cantidad:g} unidades a '{nombre}'. Nuevo stock: {nuevo_stock:g}."
    except Exception as e:
        conn.rollback()
        return False, f"Error al registrar la entrada: {e}"
    finally:
        conn.close()


def registrar_salida(producto_id: int, cantidad: float, motivo: str, usuario_id: int,
                      nro_comprobante: str = "", observaciones: str = "") -> tuple[bool, str]:
    """Registra una salida manual de inventario (no por venta). Valida que no
    se descuente más de lo disponible."""
    if cantidad is None or cantidad <= 0:
        return False, "La cantidad a descontar debe ser mayor a cero."

    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT stock, comprometido, nombre FROM productos WHERE id = ?", (producto_id,))
        fila = cursor.fetchone()
        if fila is None:
            return False, "El producto no existe."
        stock_actual, comprometido, nombre = fila
        disponible = (stock_actual or 0) - (comprometido or 0)

        if cantidad > disponible:
            return False, f"No se puede descontar {cantidad:g}: solo hay {disponible:g} disponible(s)."

        nuevo_stock = (stock_actual or 0) - cantidad
        cursor.execute("UPDATE productos SET stock = ? WHERE id = ?", (nuevo_stock, producto_id))

        _insertar_movimiento(cursor, producto_id, "salida", cantidad, motivo,
                             usuario_id, nuevo_stock, nro_comprobante, observaciones)

        conn.commit()
        return True, f"Se descontaron {cantidad:g} unidades de '{nombre}'. Nuevo stock: {nuevo_stock:g}."
    except Exception as e:
        conn.rollback()
        return False, f"Error al registrar la salida: {e}"
    finally:
        conn.close()


def editar_stock_minimo(producto_id: int, nuevo_stock_minimo: float) -> tuple[bool, str]:
    if nuevo_stock_minimo is None or nuevo_stock_minimo < 0:
        return False, "El stock mínimo no puede ser negativo."

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE productos SET stock_minimo = ? WHERE id = ?", (nuevo_stock_minimo, producto_id))
    conn.commit()
    conn.close()
    return True, "Stock mínimo actualizado."


def registrar_movimiento_externo(cursor, producto_id: int, tipo: str, cantidad: float,
                                  motivo: str, usuario_id, stock_resultante: float,
                                  nro_comprobante: str = "", observaciones: str = "",
                                  es_ilimitado: bool = False):
    """Punto de entrada público para que OTROS módulos (alta/edición de
    productos en models_catalogo.py, ventas y devoluciones en
    models_ventas.py) registren un movimiento de inventario usando su
    propio cursor, dentro de la misma transacción donde ya están
    modificando el stock del producto. Así el historial de movimientos
    queda completo: desde el stock inicial al crear el producto, hasta
    cada entrada, salida, venta y devolución.

    es_ilimitado=True indica que el producto tiene control de stock
    "Ilimitado": el movimiento se registra igual (para dejar constancia
    de la carga inicial y de cada salida/venta posterior) pero sin que
    represente un descuento real de inventario."""
    _insertar_movimiento(cursor, producto_id, tipo, cantidad, motivo,
                         usuario_id, stock_resultante, nro_comprobante,
                         observaciones, es_ilimitado)


def historial_movimientos(producto_id: int) -> list[dict]:
    """Devuelve el historial de movimientos manuales (entradas/salidas) de un
    producto, más recientes primero."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.id, m.tipo, m.cantidad, m.motivo, m.fecha, m.nro_comprobante,
               m.observaciones, m.stock_resultante, u.nombre_completo, m.es_ilimitado
        FROM movimientos_inventario m
        LEFT JOIN usuarios u ON m.usuario_id = u.id
        WHERE m.producto_id = ?
        ORDER BY m.fecha DESC, m.id DESC
    """, (producto_id,))
    filas = cursor.fetchall()
    conn.close()
    return [
        {
            "id": f[0], "tipo": f[1], "cantidad": f[2], "motivo": f[3] or "",
            "fecha": f[4], "nro_comprobante": f[5] or "", "observaciones": f[6] or "",
            "stock_resultante": f[7], "usuario": f[8] or "", "es_ilimitado": bool(f[9]),
        }
        for f in filas
    ]
