"""
models_clientes.py
Funciones de negocio para el módulo de Clientes: CRUD completo con todos
los campos del formulario (datos personales/de facturación, crédito,
día de cobro, zona y cobrador), más la gestión de Zonas y Cobradores
(listas editables, igual que Marca/Categoría en Productos).
"""
from database import conectar

DIAS_COBRO = ["Sin Asignar", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
TIPOS_PERSONA = ["Física", "Jurídica"]
NACIONALIDADES = ["Paraguaya", "Extranjera"]


# ---------------- ZONAS ----------------
def listar_zonas() -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM zonas ORDER BY nombre")
    filas = cursor.fetchall()
    conn.close()
    return [{"id": f[0], "nombre": f[1]} for f in filas]


def crear_zona(nombre: str) -> tuple[bool, str]:
    if not nombre.strip():
        return False, "El nombre de la zona no puede estar vacío."
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO zonas (nombre) VALUES (?)", (nombre.strip(),))
        conn.commit()
        return True, "Zona creada."
    except Exception:
        return False, "Esa zona ya existe."
    finally:
        conn.close()


# ---------------- COBRADORES ----------------
def listar_cobradores() -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM cobradores ORDER BY nombre")
    filas = cursor.fetchall()
    conn.close()
    return [{"id": f[0], "nombre": f[1]} for f in filas]


def crear_cobrador(nombre: str) -> tuple[bool, str]:
    if not nombre.strip():
        return False, "El nombre del cobrador no puede estar vacío."
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO cobradores (nombre) VALUES (?)", (nombre.strip(),))
        conn.commit()
        return True, "Cobrador creado."
    except Exception:
        return False, "Ese cobrador ya existe."
    finally:
        conn.close()


# ---------------- CLIENTES ----------------
def listar_clientes(texto_busqueda: str = "") -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()

    consulta_base = """
        SELECT c.id, c.nombre, c.razon_social, c.nro_documento, c.direccion, c.telefono,
               c.tipo_persona, c.nacionalidad, c.ruc, c.fecha_nacimiento, c.email,
               c.observaciones, c.credito_permitido, c.dia_cobro,
               c.zona_id, z.nombre, c.cobrador_id, co.nombre
        FROM clientes c
        LEFT JOIN zonas z ON c.zona_id = z.id
        LEFT JOIN cobradores co ON c.cobrador_id = co.id
    """

    if texto_busqueda.strip():
        comodin = f"%{texto_busqueda.strip()}%"
        cursor.execute(consulta_base + """
            WHERE c.nombre LIKE ? OR c.razon_social LIKE ? OR c.nro_documento LIKE ?
            ORDER BY c.nombre
        """, (comodin, comodin, comodin))
    else:
        cursor.execute(consulta_base + " ORDER BY c.nombre")

    filas = cursor.fetchall()
    conn.close()
    return [
        {
            "id": f[0], "nombre": f[1], "razon_social": f[2] or f[1],
            "nro_documento": f[3] or "", "direccion": f[4] or "", "telefono": f[5] or "",
            "tipo_persona": f[6] or "Física", "nacionalidad": f[7] or "Paraguaya",
            "ruc": f[8] or "", "fecha_nacimiento": f[9] or "", "email": f[10] or "",
            "observaciones": f[11] or "", "credito_permitido": bool(f[12]),
            "dia_cobro": f[13] or "Sin Asignar", "zona_id": f[14], "zona": f[15] or "",
            "cobrador_id": f[16], "cobrador": f[17] or "",
        }
        for f in filas
    ]


def obtener_cliente(cliente_id: int) -> dict | None:
    coincidencias = [c for c in listar_clientes() if c["id"] == cliente_id]
    return coincidencias[0] if coincidencias else None


def cliente_tiene_credito_permitido(cliente_id: int | None) -> bool:
    """Usado por el módulo de Ventas para bloquear la condición 'Crédito'
    si el cliente no tiene el crédito habilitado. Un cliente Ocasional
    (cliente_id=None) nunca tiene crédito permitido."""
    if cliente_id is None:
        return False
    cliente = obtener_cliente(cliente_id)
    return bool(cliente and cliente["credito_permitido"])


def crear_cliente(nombre: str, razon_social: str = "", nro_documento: str = "",
                   direccion: str = "", telefono: str = "", email: str = "",
                   tipo_persona: str = "Física", nacionalidad: str = "Paraguaya",
                   ruc: str = "", fecha_nacimiento: str = "", observaciones: str = "",
                   credito_permitido: bool = False, dia_cobro: str = "Sin Asignar",
                   zona_id: int = None, cobrador_id: int = None) -> tuple[bool, str]:
    if not nombre.strip():
        return False, "El nombre del cliente es obligatorio."

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clientes (nombre, razon_social, nro_documento, direccion, telefono, email,
                               tipo_persona, nacionalidad, ruc, fecha_nacimiento, observaciones,
                               credito_permitido, dia_cobro, zona_id, cobrador_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (nombre.strip(), razon_social.strip() or nombre.strip(), nro_documento.strip(),
          direccion.strip(), telefono.strip(), email.strip(), tipo_persona, nacionalidad,
          ruc.strip(), fecha_nacimiento, observaciones.strip(),
          1 if credito_permitido else 0, dia_cobro, zona_id, cobrador_id))
    conn.commit()
    conn.close()
    return True, "Cliente creado correctamente."


def editar_cliente(cliente_id: int, nombre: str, razon_social: str = "", nro_documento: str = "",
                    direccion: str = "", telefono: str = "", email: str = "",
                    tipo_persona: str = "Física", nacionalidad: str = "Paraguaya",
                    ruc: str = "", fecha_nacimiento: str = "", observaciones: str = "",
                    credito_permitido: bool = False, dia_cobro: str = "Sin Asignar",
                    zona_id: int = None, cobrador_id: int = None) -> tuple[bool, str]:
    if not nombre.strip():
        return False, "El nombre del cliente es obligatorio."

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE clientes
        SET nombre = ?, razon_social = ?, nro_documento = ?, direccion = ?, telefono = ?, email = ?,
            tipo_persona = ?, nacionalidad = ?, ruc = ?, fecha_nacimiento = ?, observaciones = ?,
            credito_permitido = ?, dia_cobro = ?, zona_id = ?, cobrador_id = ?
        WHERE id = ?
    """, (nombre.strip(), razon_social.strip() or nombre.strip(), nro_documento.strip(),
          direccion.strip(), telefono.strip(), email.strip(), tipo_persona, nacionalidad,
          ruc.strip(), fecha_nacimiento, observaciones.strip(),
          1 if credito_permitido else 0, dia_cobro, zona_id, cobrador_id, cliente_id))
    conn.commit()
    conn.close()
    return True, "Cliente actualizado."


def eliminar_cliente(cliente_id: int) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM ventas WHERE cliente_id = ?", (cliente_id,))
    tiene_ventas = cursor.fetchone()[0] > 0
    if tiene_ventas:
        conn.close()
        return False, "No se puede eliminar: el cliente ya tiene ventas registradas."
    cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
    conn.commit()
    conn.close()
    return True, "Cliente eliminado."


def historial_compras_cliente(cliente_id: int) -> list[dict]:
    """Ventas históricas de un cliente, más recientes primero. Usado en el
    panel de detalle del módulo Clientes."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.id, v.fecha, v.total, v.estado, v.forma_pago, f.nro_factura
        FROM ventas v
        LEFT JOIN facturas f ON f.venta_id = v.id
        WHERE v.cliente_id = ?
        ORDER BY v.fecha DESC
    """, (cliente_id,))
    filas = cursor.fetchall()
    conn.close()
    return [
        {
            "id": f[0], "fecha": f[1], "total": f[2], "estado": f[3],
            "forma_pago": f[4], "factura": f[5] or "",
        }
        for f in filas
    ]


def resumen_cliente(cliente_id: int) -> dict:
    """Totales rápidos de un cliente: cantidad de compras, total comprado,
    y saldo pendiente en créditos activos."""
    compras = historial_compras_cliente(cliente_id)
    compras_validas = [c for c in compras if c["estado"] != "Cancelado"]
    total_comprado = sum(c["total"] for c in compras_validas)

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(deuda_total - pagado), 0)
        FROM creditos WHERE cliente_id = ?
    """, (cliente_id,))
    saldo_pendiente = cursor.fetchone()[0]
    conn.close()

    return {
        "cantidad_compras": len(compras_validas),
        "total_comprado": total_comprado,
        "saldo_pendiente": saldo_pendiente,
    }
