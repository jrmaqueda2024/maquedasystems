"""
models_ventas.py
Lógica de negocio del proceso de ventas: registrar una venta nueva,
descontar stock, generar número de factura correlativo y, si la venta
es a crédito, crear automáticamente el registro en Créditos.

Todo el proceso de "procesar_venta" corre en una sola transacción:
si algo falla a mitad de camino, se revierte todo (no se descuenta stock
parcialmente ni se genera una factura sin venta real).
"""
from database import conectar


class ErrorDeVenta(Exception):
    """Excepción de negocio: stock insuficiente, datos inválidos, etc."""
    pass


def _siguiente_numero_con_cursor(cursor, tipo: str) -> str:
    """Igual que models_comprobante.siguiente_numero(), pero usando el
    cursor/transacción ya abiertos de procesar_venta, en vez de abrir una
    conexión nueva — abrir otra conexión de escritura mientras esta
    transacción todavía no se confirmó podría bloquear la base de datos
    (o directamente fallar) en SQLite.

    Importante: acá NO se debe llamar a
    models_comprobante.inicializar_tablas_comprobante(), porque esa
    función abre su PROPIA conexión nueva para crear las tablas — eso es
    exactamente la segunda conexión de escritura concurrente que este
    docstring dice que hay que evitar, y causaba 'database is locked' al
    procesar una venta. Por eso, la tabla se asegura acá mismo, con el
    cursor ya abierto de la transacción de la venta.
    """
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS numeracion_comprobante (
            tipo            TEXT PRIMARY KEY,
            establecimiento TEXT NOT NULL DEFAULT '001',
            punto_exp       TEXT NOT NULL DEFAULT '001',
            ultimo_numero   INTEGER NOT NULL DEFAULT 0
        )
    """)
    cursor.execute(
        "INSERT INTO numeracion_comprobante (tipo, establecimiento, punto_exp, ultimo_numero) "
        "VALUES (?, '001', '001', 1) "
        "ON CONFLICT(tipo) DO UPDATE SET ultimo_numero = ultimo_numero + 1",
        (tipo,),
    )
    cursor.execute(
        "SELECT establecimiento, punto_exp, ultimo_numero FROM numeracion_comprobante WHERE tipo = ?",
        (tipo,),
    )
    est, pto, num = cursor.fetchone()
    return f"{est}-{pto}-{num:07d}"


def procesar_venta(items: list[dict], usuario_id: int, cliente_id: int | None,
                    condicion: str = "contado", forma_pago: str = "Efectivo",
                    fecha_vencimiento_credito: str | None = None,
                    tipo_documento: str = "comprobante") -> tuple[bool, str, int | None]:
    """
    Procesa una venta completa.

    items: lista de dicts con {"producto_id": int, "cantidad": float, "precio_unitario": float}
    condicion: "contado" o "credito"
    tipo_documento: "comprobante" (sin datos fiscales) o "factura" (Factura
        Legal), según lo elegido en la ventana Cobrar. Se guarda con la
        venta para poder mostrarlo luego en el Resumen de Ventas.

    Devuelve (exito, mensaje, venta_id).
    """
    if not items:
        return False, "No hay productos en la venta.", None
    if condicion not in ("contado", "credito"):
        return False, "Condición de venta inválida.", None
    if tipo_documento not in ("comprobante", "factura"):
        tipo_documento = "comprobante"

    conn = conectar()
    cursor = conn.cursor()
    try:
        # 1. Verificar stock disponible de cada producto ANTES de modificar nada
        #    Los productos libres (producto_id=None) se saltan completamente.
        for item in items:
            if item.get("producto_id") is None:
                continue  # Venta libre: sin validación ni descuento de stock

            cursor.execute(
                "SELECT nombre, stock, comprometido, tipo_producto, control_stock FROM productos WHERE id = ? AND activo = 1",
                (item["producto_id"],),
            )
            fila = cursor.fetchone()
            if fila is None:
                raise ErrorDeVenta(f"El producto con código {item['producto_id']} no existe o está inactivo.")
            nombre, stock, comprometido, tipo_producto, control_stock = fila

            # Los servicios o productos con stock ilimitado no se validan ni descuentan
            if tipo_producto == "Servicio" or control_stock == "Ilimitado":
                continue

            disponible = (stock or 0) - (comprometido or 0)
            if item["cantidad"] > disponible:
                raise ErrorDeVenta(
                    f"Stock insuficiente para '{nombre}'. Disponible: {disponible}, solicitado: {item['cantidad']}."
                )

        # 2. Calcular el total de la venta
        total = sum(item["cantidad"] * item["precio_unitario"] for item in items)

        # 3. Insertar la cabecera de la venta
        cursor.execute("""
            INSERT INTO ventas (cliente_id, usuario_id, total, condicion, forma_pago, estado, tipo_documento)
            VALUES (?, ?, ?, ?, ?, 'Pagado', ?)
        """, (cliente_id, usuario_id, total, condicion, forma_pago, tipo_documento))
        venta_id = cursor.lastrowid

        # 4. Insertar el detalle y descontar stock de cada producto (salvo servicios/ilimitado/libres)
        for item in items:
            if item.get("producto_id") is None:
                # Producto libre: guarda solo descripción y precio, sin FK a productos
                cursor.execute("""
                    INSERT INTO detalle_ventas
                        (venta_id, producto_id, descripcion_libre, cantidad, precio_unitario)
                    VALUES (?, NULL, ?, ?, ?)
                """, (venta_id, item.get("descripcion_libre", ""), item["cantidad"], item["precio_unitario"]))
                continue

            cursor.execute("""
                INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario)
                VALUES (?, ?, ?, ?)
            """, (venta_id, item["producto_id"], item["cantidad"], item["precio_unitario"]))

            cursor.execute(
                "SELECT tipo_producto, control_stock FROM productos WHERE id = ?",
                (item["producto_id"],),
            )
            tipo_producto, control_stock = cursor.fetchone()
            if tipo_producto != "Servicio":
                from models_inventario import registrar_movimiento_externo
                if control_stock == "Ilimitado":
                    # No hay stock real que descontar, pero se deja
                    # constancia de la venta en el historial del artículo,
                    # marcada como "Ilimitado".
                    registrar_movimiento_externo(
                        cursor, item["producto_id"], "salida", item["cantidad"],
                        f"Venta según Nota Nro. {venta_id}", usuario_id, None,
                        nro_comprobante=str(venta_id), es_ilimitado=True,
                    )
                else:
                    cursor.execute(
                        "UPDATE productos SET stock = stock - ? WHERE id = ?",
                        (item["cantidad"], item["producto_id"]),
                    )
                    cursor.execute("SELECT stock FROM productos WHERE id = ?", (item["producto_id"],))
                    stock_resultante = cursor.fetchone()[0]
                    registrar_movimiento_externo(
                        cursor, item["producto_id"], "salida", item["cantidad"],
                        f"Venta según Nota Nro. {venta_id}", usuario_id, stock_resultante,
                        nro_comprobante=str(venta_id),
                    )

        # 5. Numeración: usa la configurada en Config. Local → Numeración
        #    (Establecimiento, Punto de Expedición y Último Número
        #    emitido), no un conteo improvisado — así lo que el usuario
        #    configura ahí queda realmente reflejado en el documento
        #    impreso. Se incrementa con el mismo cursor/transacción de la
        #    venta (no se abre una conexión aparte, para no bloquear la
        #    base de datos a mitad de una transacción sin confirmar). El
        #    número se fija una sola vez acá y no se recalcula al
        #    reimprimir o reabrir la venta después.
        nro_factura = _siguiente_numero_con_cursor(cursor, "factura")
        if tipo_documento == "comprobante":
            nro_comprobante = _siguiente_numero_con_cursor(cursor, "comprobante")
            cursor.execute("UPDATE ventas SET nro_comprobante = ? WHERE id = ?",
                           (nro_comprobante, venta_id))
        razon_social = "Ocasional"
        ruc = ""
        if cliente_id:
            cursor.execute("SELECT razon_social, nro_documento FROM clientes WHERE id = ?", (cliente_id,))
            fila_cliente = cursor.fetchone()
            if fila_cliente:
                razon_social = fila_cliente[0] or "Ocasional"
                ruc = fila_cliente[1] or ""

        cursor.execute("""
            INSERT INTO facturas (venta_id, nro_factura, razon_social, ruc, valor_total, estado)
            VALUES (?, ?, ?, ?, ?, 'Vigente')
        """, (venta_id, nro_factura, razon_social, ruc, total))

        # 6. Si la venta es a crédito, generar el registro de crédito con saldo pendiente
        if condicion == "credito":
            cursor.execute("""
                INSERT INTO creditos (venta_id, cliente_id, fecha_vencimiento, descripcion, deuda_total, pagado)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (venta_id, cliente_id, fecha_vencimiento_credito, f"Factura {nro_factura}", total))

        conn.commit()
        return True, f"Venta procesada correctamente. Factura {nro_factura}.", venta_id

    except ErrorDeVenta as e:
        conn.rollback()
        return False, str(e), None
    except Exception as e:
        conn.rollback()
        return False, f"Error inesperado al procesar la venta: {e}", None
    finally:
        conn.close()


def cancelar_venta(venta_id: int) -> tuple[bool, str]:
    """Cancela una venta: revierte el stock de los productos y marca la venta
    y su factura como canceladas. No elimina los registros (trazabilidad)."""
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT estado FROM ventas WHERE id = ?", (venta_id,))
        fila = cursor.fetchone()
        if fila is None:
            return False, "La venta no existe."
        if fila[0] == "Cancelado":
            return False, "Esta venta ya fue cancelada."

        cursor.execute("SELECT producto_id, cantidad FROM detalle_ventas WHERE venta_id = ?", (venta_id,))
        for producto_id, cantidad in cursor.fetchall():
            cursor.execute(
                "SELECT tipo_producto, control_stock FROM productos WHERE id = ?",
                (producto_id,),
            )
            fila_producto = cursor.fetchone()
            if fila_producto and fila_producto[0] != "Servicio" and fila_producto[1] != "Ilimitado":
                cursor.execute("UPDATE productos SET stock = stock + ? WHERE id = ?", (cantidad, producto_id))

        cursor.execute("UPDATE ventas SET estado = 'Cancelado' WHERE id = ?", (venta_id,))
        cursor.execute("UPDATE facturas SET estado = 'Cancelado' WHERE venta_id = ?", (venta_id,))
        conn.commit()
        return True, "Venta cancelada y stock revertido."
    except Exception as e:
        conn.rollback()
        return False, f"Error al cancelar la venta: {e}"
    finally:
        conn.close()


def listar_ventas_del_dia(fecha: str, usuario_id: int | None = None) -> list[dict]:
    """fecha en formato 'YYYY-MM-DD'. Devuelve las ventas de un único día.
    usuario_id: si se indica, solo devuelve las ventas generadas por ese
    usuario (ver auth.filtro_usuario_ventas)."""
    return listar_ventas_en_rango(fecha, fecha, usuario_id=usuario_id)


def listar_ventas_en_rango(fecha_desde: str, fecha_hasta: str,
                            usuario_id: int | None = None) -> list[dict]:
    """fecha_desde y fecha_hasta en formato 'YYYY-MM-DD' (ambas inclusive).
    Usado tanto en el Resumen diario (desde == hasta) como en el reporte por
    rango de fechas.

    usuario_id: si se indica (típicamente el ID de un usuario con rol
    'vendedor', ver auth.filtro_usuario_ventas), solo se devuelven las
    ventas generadas por ese usuario. Si es None, se devuelven las ventas
    de todos los usuarios (comportamiento para Gerente/Administrador)."""
    from models_comprobante import obtener_numeracion
    num_comp = obtener_numeracion("comprobante")

    conn = conectar()
    try:
        cursor = conn.cursor()
        sql = """
            SELECT v.id, v.fecha, COALESCE(c.nombre, 'Ocasional'), v.total, v.estado,
                   v.forma_pago, f.nro_factura, u.nombre_completo, v.tipo_documento
            FROM ventas v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            LEFT JOIN facturas f ON f.venta_id = v.id
            LEFT JOIN usuarios u ON v.usuario_id = u.id
            WHERE date(v.fecha) BETWEEN ? AND ?
        """
        params: list = [fecha_desde, fecha_hasta]
        if usuario_id is not None:
            sql += " AND v.usuario_id = ?"
            params.append(usuario_id)
        sql += " ORDER BY v.fecha DESC"
        cursor.execute(sql, params)
        filas = cursor.fetchall()
    finally:
        conn.close()

    def _nro_comprobante(venta_id: int) -> str:
        return f"{num_comp['establecimiento']}-{num_comp['punto_exp']}-{venta_id:07d}"

    return [
        {
            "id": f[0], "fecha": f[1], "cliente": f[2], "importe": f[3], "estado": f[4],
            "forma_pago": f[5], "factura": f[6] or "", "vendedor": f[7] or "",
            "tipo_documento": f[8] or "comprobante",
            # Etiqueta lista para mostrar en la grilla del Resumen: el
            # número de Factura sólo existe si el cliente pidió Factura
            # Legal al cobrar; en cualquier otro caso se muestra el número
            # correlativo propio del Comprobante de Venta.
            "factura_mostrar": (f"📄 Factura {f[6]}" if f[8] == "factura" and f[6]
                                else f"🧾 Comprobante {_nro_comprobante(f[0])}" if f[8] != "factura"
                                else (f[6] or "")),
        }
        for f in filas
    ]


def resumen_financiero_del_dia(fecha: str, usuario_id: int | None = None) -> dict:
    """Calcula ventas totales, ganancia, y desglose de caja para un día específico.
    usuario_id: ver resumen_financiero_en_rango."""
    return resumen_financiero_en_rango(fecha, fecha, usuario_id=usuario_id)


def resumen_financiero_en_rango(fecha_desde: str, fecha_hasta: str,
                                 usuario_id: int | None = None) -> dict:
    """Calcula ventas totales, ganancia, y desglose de caja para un rango de
    fechas (ambas inclusive). Si fecha_desde == fecha_hasta, es el resumen de
    un único día.

    usuario_id: si se indica, la lista de ventas y los totales derivados de
    ella (ventas_totales, ganancia, ventas_efectivo, ventas_transferencia)
    quedan limitados a las ventas de ese usuario — para que un Vendedor
    solo vea sus propias ventas. Gerente/Administrador pasan usuario_id=None
    y ven las de todos.

    El arqueo de caja (saldo_inicial, entradas, salidas, dinero_en_caja)
    NUNCA se filtra por usuario: la caja es física y compartida por todos
    los que operan el mismo día, así que 'Dinero en Caja' siempre debe
    cuadrar con el cajón real, sin importar quién vendió cada cosa.
    """
    ventas = listar_ventas_en_rango(fecha_desde, fecha_hasta, usuario_id=usuario_id)
    ventas_validas = [v for v in ventas if v["estado"] != "Cancelado"]

    ventas_totales = sum(v["importe"] for v in ventas_validas)
    ventas_efectivo = sum(v["importe"] for v in ventas_validas if v["forma_pago"] == "Efectivo")
    ventas_transferencia = sum(v["importe"] for v in ventas_validas if v["forma_pago"] == "Transferencia Bancaria")

    # Ganancia: suma de (precio_venta - precio_compra) * cantidad de cada
    # línea vendida en el rango (filtrada por usuario_id si corresponde).
    conn = conectar()
    try:
        cursor = conn.cursor()
        sql_ganancia = """
            SELECT dv.cantidad, dv.precio_unitario, p.precio_compra
            FROM detalle_ventas dv
            JOIN ventas v ON dv.venta_id = v.id
            JOIN productos p ON dv.producto_id = p.id
            WHERE date(v.fecha) BETWEEN ? AND ? AND v.estado != 'Cancelado'
        """
        params_ganancia = [fecha_desde, fecha_hasta]
        if usuario_id is not None:
            sql_ganancia += " AND v.usuario_id = ?"
            params_ganancia.append(usuario_id)
        cursor.execute(sql_ganancia, params_ganancia)
        ganancia = sum((precio_unit - (precio_compra or 0)) * cantidad
                       for cantidad, precio_unit, precio_compra in cursor.fetchall())
    finally:
        conn.close()

    cursor_caja = conectar()
    c = cursor_caja.cursor()
    c.execute("SELECT COALESCE(SUM(monto), 0) FROM caja_movimientos WHERE tipo='saldo_inicial' AND date(fecha) BETWEEN ? AND ?", (fecha_desde, fecha_hasta))
    saldo_inicial = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(monto), 0) FROM caja_movimientos WHERE tipo='entrada' AND date(fecha) BETWEEN ? AND ?", (fecha_desde, fecha_hasta))
    entradas = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(monto), 0) FROM caja_movimientos WHERE tipo='salida' AND date(fecha) BETWEEN ? AND ?", (fecha_desde, fecha_hasta))
    salidas = c.fetchone()[0]
    # Devoluciones de artículos: solo se informan en el panel si la venta
    # original fue pagada en Efectivo. NOTA: el total de la venta en la
    # tabla 'ventas' YA queda descontado al momento de devolver_articulo(),
    # así que 'ventas_efectivo' (calculado arriba a partir del total actual
    # de cada venta) ya refleja la devolución. Por eso 'devoluciones' es
    # solo informativo aquí y NO se vuelve a restar de dinero_en_caja
    # (evita una doble resta del mismo importe).
    c.execute("""
        SELECT COALESCE(SUM(d.importe), 0)
        FROM devoluciones d
        JOIN ventas v ON d.venta_id = v.id
        WHERE date(d.fecha) BETWEEN ? AND ? AND v.forma_pago = 'Efectivo'
    """, (fecha_desde, fecha_hasta))
    devoluciones = c.fetchone()[0]

    # 'Dinero en Caja' siempre se calcula con el efectivo vendido por
    # TODOS los usuarios (no solo el filtrado), para que el arqueo cuadre
    # con el cajón físico real aunque la tarjeta "Ventas en Efectivo" que
    # ve un Vendedor muestre únicamente lo que él vendió.
    if usuario_id is not None:
        c.execute("""
            SELECT COALESCE(SUM(v.total), 0) FROM ventas v
            WHERE date(v.fecha) BETWEEN ? AND ? AND v.estado != 'Cancelado' AND v.forma_pago = 'Efectivo'
        """, (fecha_desde, fecha_hasta))
        ventas_efectivo_caja = c.fetchone()[0]
    else:
        ventas_efectivo_caja = ventas_efectivo
    cursor_caja.close()

    dinero_en_caja = saldo_inicial + ventas_efectivo_caja + entradas - salidas

    return {
        "ventas": ventas,
        "ventas_totales": ventas_totales,
        "ganancia": ganancia,
        "saldo_inicial": saldo_inicial,
        "ventas_efectivo": ventas_efectivo,
        "ventas_transferencia": ventas_transferencia,
        "entradas": entradas,
        "salidas": salidas,
        "devoluciones": devoluciones,
        "dinero_en_caja": dinero_en_caja,
    }


def ventas_por_dia_en_rango(fecha_desde: str, fecha_hasta: str,
                             usuario_id: int | None = None) -> list[dict]:
    """Agrupa el total vendido por cada día dentro del rango (solo ventas no
    canceladas). Usado para el gráfico 'Ventas por día' del reporte PDF.
    Devuelve una lista ordenada por fecha ascendente: [{"fecha": "YYYY-MM-DD", "total": float}, ...]

    usuario_id: si se indica, solo considera las ventas de ese usuario."""
    conn = conectar()
    cursor = conn.cursor()
    sql = """
        SELECT date(fecha) AS dia, SUM(total)
        FROM ventas
        WHERE date(fecha) BETWEEN ? AND ? AND estado != 'Cancelado'
    """
    params: list = [fecha_desde, fecha_hasta]
    if usuario_id is not None:
        sql += " AND usuario_id = ?"
        params.append(usuario_id)
    sql += " GROUP BY date(fecha) ORDER BY date(fecha) ASC"
    cursor.execute(sql, params)
    filas = cursor.fetchall()
    conn.close()
    return [{"fecha": f[0], "total": f[1] or 0} for f in filas]


def productos_mas_vendidos_en_rango(fecha_desde: str, fecha_hasta: str, limite: int = 10,
                                     usuario_id: int | None = None) -> list[dict]:
    """Ranking de productos más vendidos (por cantidad) dentro del rango,
    con su cantidad total e importe total vendido. Usado en el reporte PDF.

    usuario_id: si se indica, solo considera lo vendido por ese usuario."""
    conn = conectar()
    cursor = conn.cursor()
    sql = """
        SELECT p.nombre, SUM(dv.cantidad) AS cantidad_total, SUM(dv.cantidad * dv.precio_unitario) AS importe_total
        FROM detalle_ventas dv
        JOIN ventas v ON dv.venta_id = v.id
        JOIN productos p ON dv.producto_id = p.id
        WHERE date(v.fecha) BETWEEN ? AND ? AND v.estado != 'Cancelado'
    """
    params: list = [fecha_desde, fecha_hasta]
    if usuario_id is not None:
        sql += " AND v.usuario_id = ?"
        params.append(usuario_id)
    sql += " GROUP BY dv.producto_id ORDER BY cantidad_total DESC LIMIT ?"
    params.append(limite)
    cursor.execute(sql, params)
    filas = cursor.fetchall()
    conn.close()
    return [{"nombre": f[0], "cantidad": f[1] or 0, "importe": f[2] or 0} for f in filas]


def obtener_detalle_venta(venta_id: int) -> dict | None:
    """Devuelve toda la información necesaria para mostrar el comprobante de
    una venta en el panel de detalle del Resumen: cabecera (cliente, fecha,
    condición, forma de pago, total) y líneas (producto, cantidad, importe,
    cuánto ya se devolvió de cada línea)."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.id, v.fecha, v.total, v.condicion, v.forma_pago, v.estado,
               COALESCE(NULLIF(c.razon_social, ''), c.nombre, 'Ocasional'),
               COALESCE(NULLIF(c.ruc, ''), c.nro_documento, ''),
               f.nro_factura, v.tipo_documento, COALESCE(c.direccion, ''),
               v.nro_comprobante
        FROM ventas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        LEFT JOIN facturas f ON f.venta_id = v.id
        WHERE v.id = ?
    """, (venta_id,))
    fila = cursor.fetchone()
    if fila is None:
        conn.close()
        return None

    cursor.execute("""
        SELECT dv.id, dv.producto_id,
               COALESCE(p.nombre, dv.descripcion_libre, '(Producto eliminado)') AS nombre_producto,
               dv.cantidad, dv.precio_unitario, dv.cantidad_devuelta
        FROM detalle_ventas dv
        LEFT JOIN productos p ON dv.producto_id = p.id
        WHERE dv.venta_id = ?
        ORDER BY dv.id
    """, (venta_id,))
    lineas = []
    for f in cursor.fetchall():
        cantidad_activa = f[3] - f[5]
        lineas.append({
            "detalle_id": f[0], "producto_id": f[1], "nombre_producto": f[2],
            "cantidad": f[3], "precio_unitario": f[4], "cantidad_devuelta": f[5],
            "cantidad_activa": cantidad_activa,
            "importe": cantidad_activa * f[4],
        })
    conn.close()

    return {
        "id": fila[0], "fecha": fila[1], "total": fila[2], "condicion": fila[3],
        "forma_pago": fila[4], "estado": fila[5], "cliente_nombre": fila[6],
        "cliente_documento": fila[7], "nro_factura": fila[8] or "",
        "tipo_documento": fila[9] or "comprobante", "cliente_direccion": fila[10] or "-",
        # Ventas de antes de esta corrección no tienen nro_comprobante
        # guardado (la columna es nueva) — para esas, se arma un número de
        # reserva con el ID de la venta, para no dejar el campo vacío.
        "nro_comprobante": fila[11] or f"001-001-{fila[0]:07d}",
        "lineas": lineas,
    }


def devolver_articulo(detalle_venta_id: int, cantidad_a_devolver: float, usuario_id: int) -> tuple[bool, str]:
    """Devuelve una cantidad específica de una línea de venta: repone el
    stock del producto, descuenta el importe del total de la venta y de la
    factura, registra la devolución para trazabilidad, y si ya no queda
    ninguna unidad activa en la venta, la marca como 'Cancelado'.

    Corre en una sola transacción: si algo falla, no se aplica nada."""
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT dv.venta_id, dv.producto_id, dv.cantidad, dv.cantidad_devuelta, dv.precio_unitario,
                   v.estado
            FROM detalle_ventas dv
            JOIN ventas v ON dv.venta_id = v.id
            WHERE dv.id = ?
        """, (detalle_venta_id,))
        fila = cursor.fetchone()
        if fila is None:
            return False, "La línea de venta no existe."

        venta_id, producto_id, cantidad, cantidad_devuelta, precio_unitario, estado_venta = fila

        if estado_venta == "Cancelado":
            return False, "Esta venta ya está cancelada; no se puede devolver nada más."

        cantidad_activa = cantidad - cantidad_devuelta
        if cantidad_a_devolver <= 0:
            return False, "La cantidad a devolver debe ser mayor a cero."
        if cantidad_a_devolver > cantidad_activa:
            return False, f"No se puede devolver {cantidad_a_devolver:g}: solo hay {cantidad_activa:g} unidad(es) activa(s) en esa línea."

        importe_devuelto = cantidad_a_devolver * precio_unitario

        # 1. Reponer stock del producto devuelto (solo si el producto sigue
        # existiendo; si ya fue eliminado definitivamente, no hay stock que
        # reponer pero la devolución igual se registra para trazabilidad).
        if producto_id is not None:
            cursor.execute("UPDATE productos SET stock = stock + ? WHERE id = ?", (cantidad_a_devolver, producto_id))

        # 2. Marcar la cantidad devuelta en la línea de venta
        cursor.execute(
            "UPDATE detalle_ventas SET cantidad_devuelta = cantidad_devuelta + ? WHERE id = ?",
            (cantidad_a_devolver, detalle_venta_id),
        )

        # 3. Descontar el importe del total de la venta y de la factura
        cursor.execute("UPDATE ventas SET total = total - ? WHERE id = ?", (importe_devuelto, venta_id))
        cursor.execute("UPDATE facturas SET valor_total = valor_total - ? WHERE venta_id = ?", (importe_devuelto, venta_id))

        # 4. Registrar la devolución para trazabilidad
        cursor.execute("""
            INSERT INTO devoluciones (venta_id, detalle_venta_id, producto_id, cantidad, importe, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (venta_id, detalle_venta_id, producto_id, cantidad_a_devolver, importe_devuelto, usuario_id))

        # 4b. Registrar también en el historial de movimientos de inventario,
        # como una entrada (la mercadería vuelve a stock), igual al
        # historial de MetaVentas que muestra "Devolución de Producto".
        if producto_id is not None:
            cursor.execute("SELECT stock FROM productos WHERE id = ?", (producto_id,))
            stock_resultante = cursor.fetchone()[0]
            from models_inventario import registrar_movimiento_externo
            registrar_movimiento_externo(
                cursor, producto_id, "entrada", cantidad_a_devolver,
                "Devolución de Producto", usuario_id, stock_resultante,
                nro_comprobante=str(venta_id),
                observaciones=f"Venta Nro. {venta_id}",
            )

        # 5. Si ya no queda ninguna unidad activa en toda la venta, cancelarla
        cursor.execute("""
            SELECT COALESCE(SUM(cantidad - cantidad_devuelta), 0) FROM detalle_ventas WHERE venta_id = ?
        """, (venta_id,))
        cantidad_activa_total = cursor.fetchone()[0]
        if cantidad_activa_total <= 0:
            cursor.execute("UPDATE ventas SET estado = 'Cancelado' WHERE id = ?", (venta_id,))
            cursor.execute("UPDATE facturas SET estado = 'Cancelado' WHERE venta_id = ?", (venta_id,))

        conn.commit()
        return True, f"Se devolvieron {cantidad_a_devolver:g} unidad(es). Stock actualizado."
    except Exception as e:
        conn.rollback()
        return False, f"Error al procesar la devolución: {e}"
    finally:
        conn.close()


def registrar_salida_efectivo(monto: float, motivo: str, usuario_id: int) -> tuple[bool, str]:
    """Registra una salida de efectivo de la caja (ej. un gasto o retiro),
    distinta de una salida de inventario. Se resta del 'Dinero en Caja' del
    día y queda reflejada en el Resumen de Ventas y en el Reporte General."""
    if monto is None or monto <= 0:
        return False, "El importe debe ser mayor a cero."
    if not motivo.strip():
        return False, "El motivo es obligatorio."

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO caja_movimientos (tipo, monto, descripcion, usuario_id)
        VALUES ('salida', ?, ?, ?)
    """, (monto, motivo.strip(), usuario_id))
    conn.commit()
    conn.close()
    return True, f"Salida de efectivo registrada: Gs. {monto:,.0f}."


def registrar_entrada_efectivo(monto: float, motivo: str, usuario_id: int) -> tuple[bool, str]:
    """Registra una entrada de efectivo manual a la caja (ej. un aporte o
    reposición), distinta de las ventas. Suma al 'Dinero en Caja' del día."""
    if monto is None or monto <= 0:
        return False, "El importe debe ser mayor a cero."
    if not motivo.strip():
        return False, "El motivo es obligatorio."

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO caja_movimientos (tipo, monto, descripcion, usuario_id)
        VALUES ('entrada', ?, ?, ?)
    """, (monto, motivo.strip(), usuario_id))
    conn.commit()
    conn.close()
    return True, f"Entrada de efectivo registrada: Gs. {monto:,.0f}."


def listar_movimientos_caja(fecha_desde: str, fecha_hasta: str) -> list[dict]:
    """Detalle de entradas/salidas manuales de caja en un rango de fechas
    (no incluye ventas, que se listan por separado). Usado en el Resumen
    de Ventas y en el Reporte General para mostrar el detalle de cada
    Salida/Entrada de Efectivo, con el motivo y quién la registró."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cm.id, cm.fecha, cm.tipo, cm.monto, cm.descripcion, u.nombre_completo
        FROM caja_movimientos cm
        LEFT JOIN usuarios u ON cm.usuario_id = u.id
        WHERE date(cm.fecha) BETWEEN ? AND ? AND cm.tipo IN ('entrada', 'salida')
        ORDER BY cm.fecha DESC
    """, (fecha_desde, fecha_hasta))
    filas = cursor.fetchall()
    conn.close()
    return [
        {
            "id": f[0], "fecha": f[1], "tipo": f[2], "monto": f[3],
            "descripcion": f[4] or "", "usuario": f[5] or "",
        }
        for f in filas
    ]


# ============================================================
# PRE-VENTA
# Se guarda en las mismas tablas 'ventas' / 'detalle_ventas' que una
# venta real, marcada con es_pre_venta=1 y estado='Pendiente'. NO
# descuenta stock, no genera movimientos de inventario, no crea crédito
# ni factura: es solo un "carrito guardado" para retomar más tarde.
# Al finalizarla (Cobrar) se procesa como una venta normal con
# procesar_venta() y luego se borra la fila de pre-venta.
# ============================================================
def crear_preventa(items: list[dict], usuario_id: int, cliente_id: int | None = None) -> tuple[bool, str, int | None]:
    """items: mismo formato que procesar_venta:
    [{"producto_id":.., "descripcion_libre":.., "cantidad":.., "precio_unitario":..}, ...]"""
    if not items:
        return False, "No hay productos cargados en la pre-venta.", None

    conn = conectar()
    cursor = conn.cursor()
    try:
        total = sum(i["cantidad"] * i["precio_unitario"] for i in items)
        cursor.execute("""
            INSERT INTO ventas (cliente_id, usuario_id, total, condicion, forma_pago,
                                 estado, es_pre_venta, tipo_documento)
            VALUES (?, ?, ?, 'contado', 'Efectivo', 'Pendiente', 1, 'comprobante')
        """, (cliente_id, usuario_id, total))
        preventa_id = cursor.lastrowid

        for item in items:
            cursor.execute("""
                INSERT INTO detalle_ventas
                    (venta_id, producto_id, descripcion_libre, cantidad, precio_unitario)
                VALUES (?, ?, ?, ?, ?)
            """, (preventa_id, item.get("producto_id"), item.get("descripcion_libre"),
                  item["cantidad"], item["precio_unitario"]))

        conn.commit()
        return True, f"Pre-Venta Nro. {preventa_id} generada correctamente.", preventa_id
    except Exception as e:
        conn.rollback()
        return False, f"Error al generar la pre-venta: {e}", None
    finally:
        conn.close()


def listar_preventas(busqueda: str = "") -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    condiciones = ["v.es_pre_venta = 1"]
    parametros: list = []
    if busqueda.strip():
        condiciones.append(
            "(COALESCE(cl.nombre,'') LIKE ? OR COALESCE(u.nombre_completo,'') LIKE ? OR CAST(v.id AS TEXT) LIKE ?)"
        )
        q = f"%{busqueda.strip()}%"
        parametros += [q, q, q]
    where = " AND ".join(condiciones)

    cursor.execute(f"""
        SELECT v.id, v.fecha, COALESCE(cl.nombre, 'Ocasional'), COALESCE(u.nombre_completo, ''),
               v.total, v.cliente_id
        FROM ventas v
        LEFT JOIN clientes cl ON v.cliente_id = cl.id
        LEFT JOIN usuarios u  ON v.usuario_id  = u.id
        WHERE {where}
        ORDER BY v.id DESC
    """, parametros)
    filas = cursor.fetchall()
    conn.close()
    return [
        {"id": f[0], "fecha": f[1], "cliente": f[2], "vendedor": f[3],
         "total": f[4] or 0, "cliente_id": f[5]}
        for f in filas
    ]


def obtener_detalle_preventa(preventa_id: int) -> dict | None:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.id, v.fecha, v.total, v.cliente_id,
               COALESCE(cl.nombre, 'Ocasional'), COALESCE(u.nombre_completo, '')
        FROM ventas v
        LEFT JOIN clientes cl ON v.cliente_id = cl.id
        LEFT JOIN usuarios u  ON v.usuario_id  = u.id
        WHERE v.id = ? AND v.es_pre_venta = 1
    """, (preventa_id,))
    fila = cursor.fetchone()
    if fila is None:
        conn.close()
        return None

    cursor.execute("""
        SELECT dv.id, dv.producto_id,
               COALESCE(p.nombre, dv.descripcion_libre, '(Artículo libre)'),
               dv.cantidad, dv.precio_unitario, p.unidad_medida
        FROM detalle_ventas dv
        LEFT JOIN productos p ON dv.producto_id = p.id
        WHERE dv.venta_id = ?
        ORDER BY dv.id
    """, (preventa_id,))
    items = []
    for f in cursor.fetchall():
        items.append({
            "detalle_id": f[0], "producto_id": f[1], "nombre": f[2],
            "cantidad": f[3], "precio_unitario": f[4], "importe": f[3] * f[4],
            "unidad_medida": f[5] or "Unidad", "es_libre": f[1] is None,
        })
    conn.close()

    return {
        "id": fila[0], "fecha": fila[1], "total": fila[2], "cliente_id": fila[3],
        "cliente": fila[4], "vendedor": fila[5], "items": items,
    }


def actualizar_preventa(preventa_id: int, items: list[dict], cliente_id: int | None) -> tuple[bool, str]:
    """Reemplaza las líneas y datos de una pre-venta existente (no la
    convierte en venta real; eso lo hace procesar_venta + eliminar_preventa
    al finalizarla desde 'Cobrar')."""
    if not items:
        return False, "No hay productos cargados en la pre-venta."

    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM ventas WHERE id = ? AND es_pre_venta = 1", (preventa_id,))
        if cursor.fetchone() is None:
            conn.close()
            return False, "La pre-venta no existe."

        total = sum(i["cantidad"] * i["precio_unitario"] for i in items)
        cursor.execute("UPDATE ventas SET cliente_id = ?, total = ? WHERE id = ?",
                       (cliente_id, total, preventa_id))
        cursor.execute("DELETE FROM detalle_ventas WHERE venta_id = ?", (preventa_id,))
        for item in items:
            cursor.execute("""
                INSERT INTO detalle_ventas
                    (venta_id, producto_id, descripcion_libre, cantidad, precio_unitario)
                VALUES (?, ?, ?, ?, ?)
            """, (preventa_id, item.get("producto_id"), item.get("descripcion_libre"),
                  item["cantidad"], item["precio_unitario"]))
        conn.commit()
        return True, "Pre-venta actualizada correctamente."
    except Exception as e:
        conn.rollback()
        return False, f"Error al actualizar la pre-venta: {e}"
    finally:
        conn.close()


def eliminar_preventa(preventa_id: int) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM ventas WHERE id = ? AND es_pre_venta = 1", (preventa_id,))
    if cursor.fetchone() is None:
        conn.close()
        return False, "La pre-venta no existe."
    cursor.execute("DELETE FROM ventas WHERE id = ?", (preventa_id,))
    conn.commit()
    conn.close()
    return True, "Pre-venta eliminada."
