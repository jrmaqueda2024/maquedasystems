"""
models_creditos.py
Lógica de negocio del módulo Créditos: cada venta procesada con
condición "crédito" (ver models_ventas.procesar_venta) genera
automáticamente una fila en la tabla 'creditos'. Este módulo se encarga
de listarlos (individualmente o agrupados/resumidos por cliente),
registrar pagos parciales, y armar el Estado de Cuenta de un cliente.
"""
from database import conectar


class ErrorDeCredito(Exception):
    pass


def _fila_a_dict(f) -> dict:
    deuda_total = f[6] or 0
    pagado = f[7] or 0
    return {
        "id": f[0], "fecha": f[1], "cliente_id": f[2],
        "cliente": f[3] or "Sin cliente", "fecha_vencimiento": f[4] or "",
        "descripcion": f[5] or "", "deuda_total": deuda_total, "pagado": pagado,
        "saldo": round(deuda_total - pagado, 2), "nro_factura": f[8] or "",
    }


_SELECT_BASE = """
    SELECT cr.id, cr.fecha, cr.cliente_id, cl.nombre, cr.fecha_vencimiento,
           cr.descripcion, cr.deuda_total, cr.pagado, f.nro_factura
    FROM creditos cr
    LEFT JOIN clientes cl ON cr.cliente_id = cl.id
    LEFT JOIN facturas f  ON f.venta_id = cr.venta_id
"""


def listar_creditos(vista: str = "pendientes", texto_busqueda: str = "") -> list[dict]:
    """vista: 'pendientes' (saldo > 0) o 'todos' (incluye ya saldados)."""
    conn = conectar()
    cursor = conn.cursor()

    condiciones = []
    parametros: list = []
    if vista == "pendientes":
        condiciones.append("(cr.deuda_total - cr.pagado) > 0.009")
    if texto_busqueda.strip():
        condiciones.append(
            "(COALESCE(cl.nombre,'') LIKE ? OR COALESCE(f.nro_factura,'') LIKE ? "
            "OR COALESCE(cr.descripcion,'') LIKE ? OR CAST(cr.id AS TEXT) LIKE ?)"
        )
        q = f"%{texto_busqueda.strip()}%"
        parametros += [q, q, q, q]
    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    cursor.execute(f"{_SELECT_BASE} {where} ORDER BY cr.fecha DESC", parametros)
    filas = cursor.fetchall()
    conn.close()
    return [_fila_a_dict(f) for f in filas]


def resumen_por_cliente(vista: str = "pendientes", texto_busqueda: str = "") -> list[dict]:
    """Vista 'Agrupar por Cliente': un renglón por cliente con sus totales
    de crédito acumulados (cantidad de créditos, deuda total, pagado,
    saldo), de mayor a menor saldo pendiente. Respeta el mismo filtro
    Pendientes/Todos que listar_creditos()."""
    conn = conectar()
    cursor = conn.cursor()
    condiciones = []
    parametros: list = []
    if vista == "pendientes":
        condiciones.append("(cr.deuda_total - cr.pagado) > 0.009")
    if texto_busqueda.strip():
        condiciones.append("COALESCE(cl.nombre,'') LIKE ?")
        parametros.append(f"%{texto_busqueda.strip()}%")
    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    cursor.execute(f"""
        SELECT cr.cliente_id, COALESCE(cl.nombre, 'Sin cliente'),
               COUNT(*), SUM(cr.deuda_total), SUM(cr.pagado)
        FROM creditos cr
        LEFT JOIN clientes cl ON cr.cliente_id = cl.id
        {where}
        GROUP BY cr.cliente_id
        ORDER BY (SUM(cr.deuda_total) - SUM(cr.pagado)) DESC
    """, parametros)
    filas = cursor.fetchall()
    conn.close()
    resultado = []
    for f in filas:
        deuda_total = f[3] or 0
        pagado = f[4] or 0
        resultado.append({
            "cliente_id": f[0], "cliente": f[1], "cantidad_creditos": f[2],
            "deuda_total": deuda_total, "pagado": pagado,
            "saldo": round(deuda_total - pagado, 2),
        })
    return resultado


def totales_creditos_pendientes() -> dict:
    """Para el panel 'Resumen de Créditos' (Mostrar/Ocultar Resumen):
    cantidad de ventas a crédito con saldo pendiente, y el total en
    guaraníes que todavía falta cobrar."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(deuda_total - pagado), 0)
        FROM creditos
        WHERE (deuda_total - pagado) > 0.009
    """)
    cantidad, total_pendiente = cursor.fetchone()
    conn.close()
    return {"cantidad_pendientes": cantidad or 0, "total_pendiente": total_pendiente or 0}


def obtener_detalle_credito(credito_id: int) -> dict | None:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(f"{_SELECT_BASE} WHERE cr.id = ?", (credito_id,))
    f = cursor.fetchone()
    if f is None:
        conn.close()
        return None
    credito = _fila_a_dict(f)

    cursor.execute("""
        SELECT id, fecha, monto FROM pagos_credito
        WHERE credito_id = ? ORDER BY fecha DESC
    """, (credito_id,))
    credito["pagos"] = [{"id": p[0], "fecha": p[1], "monto": p[2]} for p in cursor.fetchall()]
    conn.close()
    return credito


def registrar_pago_credito(credito_id: int, monto: float, usuario_id: int | None = None) -> tuple[bool, str]:
    if monto is None or monto <= 0:
        return False, "El monto a pagar debe ser mayor a cero."

    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT deuda_total, pagado FROM creditos WHERE id = ?", (credito_id,))
        fila = cursor.fetchone()
        if fila is None:
            conn.close()
            return False, "El crédito no existe."
        deuda_total, pagado = fila
        saldo = round(deuda_total - pagado, 2)
        if monto > saldo + 0.009:
            conn.close()
            return False, f"El monto ingresado supera el saldo pendiente (Gs. {saldo:,.0f})."

        cursor.execute("INSERT INTO pagos_credito (credito_id, monto) VALUES (?, ?)",
                       (credito_id, monto))
        nuevo_pagado = pagado + monto
        cursor.execute("UPDATE creditos SET pagado = ? WHERE id = ?", (nuevo_pagado, credito_id))
        conn.commit()

        nuevo_saldo = round(deuda_total - nuevo_pagado, 2)
        if nuevo_saldo <= 0.009:
            return True, f"Pago registrado. El crédito Nro. {credito_id} quedó saldado por completo."
        return True, f"Pago registrado. Saldo restante: Gs. {nuevo_saldo:,.0f}."
    except Exception as e:
        conn.rollback()
        return False, f"Error al registrar el pago: {e}"
    finally:
        conn.close()


def estado_cuenta_cliente(cliente_id: int) -> dict | None:
    """Todos los créditos de un cliente (con su historial de pagos cada
    uno) y los totales generales, para el 'Estado de Cuenta'."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, nro_documento, direccion, telefono FROM clientes WHERE id = ?",
                   (cliente_id,))
    fila_cliente = cursor.fetchone()
    if fila_cliente is None:
        conn.close()
        return None

    cursor.execute(f"{_SELECT_BASE} WHERE cr.cliente_id = ? ORDER BY cr.fecha", (cliente_id,))
    creditos = [_fila_a_dict(f) for f in cursor.fetchall()]
    for credito in creditos:
        cursor.execute("SELECT fecha, monto FROM pagos_credito WHERE credito_id = ? ORDER BY fecha",
                       (credito["id"],))
        credito["pagos"] = [{"fecha": p[0], "monto": p[1]} for p in cursor.fetchall()]
    conn.close()

    deuda_total = sum(c["deuda_total"] for c in creditos)
    pagado = sum(c["pagado"] for c in creditos)
    return {
        "cliente_id": cliente_id, "nombre": fila_cliente[0],
        "nro_documento": fila_cliente[1] or "", "direccion": fila_cliente[2] or "",
        "telefono": fila_cliente[3] or "", "creditos": creditos,
        "deuda_total": deuda_total, "pagado": pagado,
        "saldo": round(deuda_total - pagado, 2),
    }
