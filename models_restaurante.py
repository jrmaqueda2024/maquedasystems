"""
models_restaurante.py
Lógica de negocio del módulo Restaurante/Comedor:

- Platos y Recetas: cada plato define qué insumos consume y en qué
  cantidad (los insumos SON los productos ya existentes en el catálogo
  de Productos/Inventario — no se duplica esa gestión: se reutiliza el
  control de stock, alertas de reposición e integración con Compras/
  Proveedores que el sistema ya tiene). El costo y el margen de cada
  plato se calculan automáticamente a partir del precio de compra de
  sus insumos.
- Mesas: el estado del salón (Libre/Ocupada/Reservada/Para Limpiar).
- Comandas: el pedido de una mesa, delivery, para llevar o mostrador,
  con sus platos y el estado de preparación de cada uno. Al cerrar la
  comanda se genera una venta real (reutilizando
  models_ventas.procesar_venta, con la misma numeración de factura,
  caja y reportes de siempre) y se descuentan automáticamente los
  insumos de cada plato vendido, según su receta.
- Reportes: platos más vendidos, margen por plato, costos operativos
  (insumos consumidos) vs ingresos, y ventas por turno.

El personal (mozos, cocineros, cajeros) y sus pagos/turnos de trabajo
se administran con el módulo Rec. Humanos ya existente; acá solo se
referencia al usuario que atendió cada comanda.
"""
import datetime

from database import conectar
from models_ventas import procesar_venta

CATEGORIAS_PLATO = ["Entrada", "Plato Principal", "Pizza", "Combo", "Guarnición", "Postre", "Bebida", "Otro"]
TIPOS_COMANDA = ["Mesa", "Delivery", "Para Llevar", "Mostrador"]
ESTADOS_ITEM = ["Pendiente", "Preparando", "Listo", "Entregado", "Cancelado"]
TURNOS = ["Mañana", "Tarde", "Noche"]
ESTADOS_DELIVERY = ["Preparando", "En Camino", "Entregado"]


def calcular_turno_actual() -> str:
    hora = datetime.datetime.now().hour
    if 6 <= hora < 14:
        return "Mañana"
    if 14 <= hora < 20:
        return "Tarde"
    return "Noche"


# ============================================================
# PLATOS Y RECETAS
# ============================================================
def _costo_y_margen_plato(cursor, plato_id: int, precio_venta: float) -> dict:
    cursor.execute("""
        SELECT COALESCE(SUM(ri.cantidad * p.precio_compra), 0)
        FROM rest_receta_ingredientes ri
        JOIN productos p ON ri.producto_id = p.id
        WHERE ri.plato_id = ?
    """, (plato_id,))
    costo = cursor.fetchone()[0] or 0
    margen = precio_venta - costo
    margen_pct = (margen / precio_venta * 100) if precio_venta else 0
    return {"costo": costo, "margen": margen, "margen_pct": margen_pct}


def listar_platos(solo_activos: bool = True, categoria: str = "", busqueda: str = "") -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    condiciones, parametros = [], []
    if solo_activos:
        condiciones.append("activo = 1")
    if categoria:
        condiciones.append("categoria = ?")
        parametros.append(categoria)
    if busqueda.strip():
        condiciones.append("nombre LIKE ?")
        parametros.append(f"%{busqueda.strip()}%")
    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    cursor.execute(f"""
        SELECT id, nombre, categoria, precio_venta, descripcion,
               tiempo_preparacion_min, activo
        FROM rest_platos {where} ORDER BY categoria, nombre
    """, parametros)
    filas = cursor.fetchall()

    resultado = []
    for f in filas:
        plato_id, precio_venta = f[0], f[3] or 0
        costeo = _costo_y_margen_plato(cursor, plato_id, precio_venta)
        resultado.append({
            "id": plato_id, "nombre": f[1], "categoria": f[2], "precio_venta": precio_venta,
            "descripcion": f[4] or "", "tiempo_preparacion_min": f[5], "activo": bool(f[6]),
            **costeo,
        })
    conn.close()
    return resultado


def obtener_plato(plato_id: int) -> dict | None:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nombre, categoria, precio_venta, descripcion,
               tiempo_preparacion_min, activo
        FROM rest_platos WHERE id = ?
    """, (plato_id,))
    f = cursor.fetchone()
    if f is None:
        conn.close()
        return None
    costeo = _costo_y_margen_plato(cursor, plato_id, f[3] or 0)
    conn.close()
    return {
        "id": f[0], "nombre": f[1], "categoria": f[2], "precio_venta": f[3] or 0,
        "descripcion": f[4] or "", "tiempo_preparacion_min": f[5], "activo": bool(f[6]),
        **costeo,
    }


def crear_plato(nombre: str, categoria: str, precio_venta: float, descripcion: str = "",
                 tiempo_preparacion_min=None) -> tuple[bool, str, int | None]:
    if not nombre.strip():
        return False, "El nombre del plato es obligatorio.", None
    if categoria not in CATEGORIAS_PLATO:
        categoria = "Otro"
    try:
        precio_venta = float(precio_venta)
        if precio_venta < 0:
            raise ValueError
    except (TypeError, ValueError):
        return False, "El precio de venta debe ser un número válido.", None

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO rest_platos (nombre, categoria, precio_venta, descripcion, tiempo_preparacion_min)
        VALUES (?, ?, ?, ?, ?)
    """, (nombre.strip(), categoria, precio_venta, descripcion.strip(), tiempo_preparacion_min or None))
    plato_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return True, f"Plato '{nombre.strip()}' creado correctamente.", plato_id


def editar_plato(plato_id: int, nombre: str, categoria: str, precio_venta: float,
                  descripcion: str = "", tiempo_preparacion_min=None) -> tuple[bool, str]:
    if not nombre.strip():
        return False, "El nombre del plato es obligatorio."
    if categoria not in CATEGORIAS_PLATO:
        categoria = "Otro"
    try:
        precio_venta = float(precio_venta)
        if precio_venta < 0:
            raise ValueError
    except (TypeError, ValueError):
        return False, "El precio de venta debe ser un número válido."

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE rest_platos
        SET nombre = ?, categoria = ?, precio_venta = ?, descripcion = ?, tiempo_preparacion_min = ?
        WHERE id = ?
    """, (nombre.strip(), categoria, precio_venta, descripcion.strip(),
          tiempo_preparacion_min or None, plato_id))
    conn.commit()
    conn.close()
    return True, "Plato actualizado correctamente."


def cambiar_estado_plato(plato_id: int, activo: bool) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE rest_platos SET activo = ? WHERE id = ?", (1 if activo else 0, plato_id))
    conn.commit()
    conn.close()
    return True, "Plato activado." if activo else "Plato desactivado."


def eliminar_plato(plato_id: int) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM rest_comanda_items WHERE plato_id = ?", (plato_id,))
    if cursor.fetchone()[0] > 0:
        conn.close()
        return False, "Este plato ya fue pedido alguna vez; no se puede eliminar. Podés desactivarlo."
    cursor.execute("DELETE FROM rest_receta_ingredientes WHERE plato_id = ?", (plato_id,))
    cursor.execute("DELETE FROM rest_platos WHERE id = ?", (plato_id,))
    conn.commit()
    conn.close()
    return True, "Plato eliminado correctamente."


# ---------------- Receta (ingredientes de un plato) ----------------
def listar_ingredientes_receta(plato_id: int) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ri.id, ri.producto_id, p.nombre, p.unidad_medida, ri.cantidad,
               p.precio_compra, p.stock
        FROM rest_receta_ingredientes ri
        JOIN productos p ON ri.producto_id = p.id
        WHERE ri.plato_id = ?
        ORDER BY p.nombre
    """, (plato_id,))
    filas = cursor.fetchall()
    conn.close()
    return [
        {"id": f[0], "producto_id": f[1], "nombre": f[2], "unidad_medida": f[3] or "Unidad",
         "cantidad": f[4], "precio_compra": f[5] or 0, "subtotal": f[4] * (f[5] or 0),
         "stock_disponible": f[6] or 0}
        for f in filas
    ]


def agregar_ingrediente_receta(plato_id: int, producto_id: int, cantidad: float) -> tuple[bool, str]:
    try:
        cantidad = float(cantidad)
        if cantidad <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return False, "La cantidad debe ser un número mayor a 0."

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, cantidad FROM rest_receta_ingredientes WHERE plato_id = ? AND producto_id = ?",
                   (plato_id, producto_id))
    existente = cursor.fetchone()
    if existente:
        cursor.execute("UPDATE rest_receta_ingredientes SET cantidad = ? WHERE id = ?",
                       (existente[1] + cantidad, existente[0]))
    else:
        cursor.execute("INSERT INTO rest_receta_ingredientes (plato_id, producto_id, cantidad) VALUES (?, ?, ?)",
                       (plato_id, producto_id, cantidad))
    conn.commit()
    conn.close()
    return True, "Ingrediente agregado a la receta."


def editar_cantidad_ingrediente(ingrediente_id: int, cantidad: float) -> tuple[bool, str]:
    try:
        cantidad = float(cantidad)
        if cantidad <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return False, "La cantidad debe ser un número mayor a 0."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE rest_receta_ingredientes SET cantidad = ? WHERE id = ?", (cantidad, ingrediente_id))
    conn.commit()
    conn.close()
    return True, "Cantidad actualizada."


def quitar_ingrediente_receta(ingrediente_id: int) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rest_receta_ingredientes WHERE id = ?", (ingrediente_id,))
    conn.commit()
    conn.close()
    return True, "Ingrediente quitado de la receta."


# ---------------- Variantes / Tamaños (Individual, Mediana, Familiar...) ----------------
def listar_variantes_plato(plato_id: int) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nombre, precio, multiplicador_receta, orden
        FROM rest_variantes_plato WHERE plato_id = ? ORDER BY orden, precio
    """, (plato_id,))
    filas = cursor.fetchall()
    conn.close()
    return [{"id": f[0], "nombre": f[1], "precio": f[2], "multiplicador_receta": f[3], "orden": f[4]}
            for f in filas]


def agregar_variante_plato(plato_id: int, nombre: str, precio: float,
                            multiplicador_receta: float = 1) -> tuple[bool, str]:
    if not nombre.strip():
        return False, "El nombre del tamaño/variante es obligatorio."
    try:
        precio = float(precio)
        multiplicador_receta = float(multiplicador_receta)
        if precio < 0 or multiplicador_receta <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return False, "El precio y el multiplicador de receta deben ser números válidos."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(MAX(orden), -1) + 1 FROM rest_variantes_plato WHERE plato_id = ?", (plato_id,))
    siguiente_orden = cursor.fetchone()[0]
    cursor.execute("""
        INSERT INTO rest_variantes_plato (plato_id, nombre, precio, multiplicador_receta, orden)
        VALUES (?, ?, ?, ?, ?)
    """, (plato_id, nombre.strip(), precio, multiplicador_receta, siguiente_orden))
    conn.commit()
    conn.close()
    return True, f"Tamaño '{nombre.strip()}' agregado."


def editar_variante_plato(variante_id: int, nombre: str, precio: float,
                           multiplicador_receta: float = 1) -> tuple[bool, str]:
    if not nombre.strip():
        return False, "El nombre del tamaño/variante es obligatorio."
    try:
        precio = float(precio)
        multiplicador_receta = float(multiplicador_receta)
        if precio < 0 or multiplicador_receta <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return False, "El precio y el multiplicador de receta deben ser números válidos."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE rest_variantes_plato SET nombre = ?, precio = ?, multiplicador_receta = ? WHERE id = ?
    """, (nombre.strip(), precio, multiplicador_receta, variante_id))
    conn.commit()
    conn.close()
    return True, "Tamaño actualizado."


def quitar_variante_plato(variante_id: int) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rest_variantes_plato WHERE id = ?", (variante_id,))
    conn.commit()
    conn.close()
    return True, "Tamaño quitado."


def costo_receta_con_multiplicador(plato_id: int, multiplicador: float = 1) -> float:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(ri.cantidad * p.precio_compra), 0)
        FROM rest_receta_ingredientes ri JOIN productos p ON ri.producto_id = p.id
        WHERE ri.plato_id = ?
    """, (plato_id,))
    costo_base = cursor.fetchone()[0] or 0
    conn.close()
    return costo_base * multiplicador


# ============================================================
# MESAS
# ============================================================
def listar_mesas(solo_activas: bool = True) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    where = "WHERE activa = 1" if solo_activas else ""
    cursor.execute(f"SELECT id, numero, capacidad, zona, estado, activa FROM rest_mesas {where} ORDER BY numero")
    filas = cursor.fetchall()
    conn.close()
    return [
        {"id": f[0], "numero": f[1], "capacidad": f[2], "zona": f[3] or "", "estado": f[4], "activa": bool(f[5])}
        for f in filas
    ]


def crear_mesa(numero: str, capacidad: int, zona: str = "") -> tuple[bool, str]:
    if not numero.strip():
        return False, "El número/nombre de la mesa es obligatorio."
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO rest_mesas (numero, capacidad, zona) VALUES (?, ?, ?)",
                       (numero.strip(), int(capacidad) if capacidad else 4, zona.strip()))
        conn.commit()
        return True, f"Mesa '{numero.strip()}' creada correctamente."
    except Exception:
        return False, f"Ya existe una mesa llamada '{numero.strip()}'."
    finally:
        conn.close()


def editar_mesa(mesa_id: int, numero: str, capacidad: int, zona: str = "") -> tuple[bool, str]:
    if not numero.strip():
        return False, "El número/nombre de la mesa es obligatorio."
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE rest_mesas SET numero = ?, capacidad = ?, zona = ? WHERE id = ?",
                       (numero.strip(), int(capacidad) if capacidad else 4, zona.strip(), mesa_id))
        conn.commit()
        return True, "Mesa actualizada correctamente."
    except Exception:
        return False, f"Ya existe otra mesa llamada '{numero.strip()}'."
    finally:
        conn.close()


def cambiar_estado_mesa(mesa_id: int, estado: str) -> tuple[bool, str]:
    if estado not in ("Libre", "Ocupada", "Reservada", "Para Limpiar"):
        return False, "Estado de mesa inválido."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE rest_mesas SET estado = ? WHERE id = ?", (estado, mesa_id))
    conn.commit()
    conn.close()
    return True, f"Mesa marcada como {estado}."


def eliminar_mesa(mesa_id: int) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM rest_comandas WHERE mesa_id = ? AND estado = 'Abierta'", (mesa_id,))
    if cursor.fetchone()[0] > 0:
        conn.close()
        return False, "Esta mesa tiene una comanda abierta; no se puede eliminar."
    cursor.execute("UPDATE rest_mesas SET activa = 0 WHERE id = ?", (mesa_id,))
    conn.commit()
    conn.close()
    return True, "Mesa dada de baja."


# ============================================================
# REPARTIDORES (Delivery)
# ============================================================
def listar_repartidores(solo_activos: bool = True) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    where = "WHERE activo = 1" if solo_activos else ""
    cursor.execute(f"SELECT id, nombre, telefono, vehiculo, activo FROM rest_repartidores {where} ORDER BY nombre")
    filas = cursor.fetchall()
    conn.close()
    return [{"id": f[0], "nombre": f[1], "telefono": f[2] or "", "vehiculo": f[3] or "", "activo": bool(f[4])}
            for f in filas]


def crear_repartidor(nombre: str, telefono: str = "", vehiculo: str = "") -> tuple[bool, str]:
    if not nombre.strip():
        return False, "El nombre del repartidor es obligatorio."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO rest_repartidores (nombre, telefono, vehiculo) VALUES (?, ?, ?)",
                   (nombre.strip(), telefono.strip(), vehiculo.strip()))
    conn.commit()
    conn.close()
    return True, f"Repartidor '{nombre.strip()}' agregado."


def editar_repartidor(repartidor_id: int, nombre: str, telefono: str = "", vehiculo: str = "") -> tuple[bool, str]:
    if not nombre.strip():
        return False, "El nombre del repartidor es obligatorio."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE rest_repartidores SET nombre = ?, telefono = ?, vehiculo = ? WHERE id = ?",
                   (nombre.strip(), telefono.strip(), vehiculo.strip(), repartidor_id))
    conn.commit()
    conn.close()
    return True, "Repartidor actualizado."


def cambiar_estado_repartidor(repartidor_id: int, activo: bool) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE rest_repartidores SET activo = ? WHERE id = ?", (1 if activo else 0, repartidor_id))
    conn.commit()
    conn.close()
    return True, "Repartidor activado." if activo else "Repartidor desactivado."


# ============================================================
# COMANDAS
# ============================================================
def abrir_comanda(tipo: str, mozo_usuario_id: int, mesa_id: int = None, cliente_id: int = None,
                   observaciones: str = "", direccion_entrega: str = "") -> tuple[bool, str, int | None]:
    if tipo not in TIPOS_COMANDA:
        tipo = "Mostrador"
    conn = conectar()
    cursor = conn.cursor()

    if tipo == "Mesa":
        if mesa_id is None:
            conn.close()
            return False, "Elegí una mesa para abrir la comanda.", None
        cursor.execute("SELECT estado FROM rest_mesas WHERE id = ?", (mesa_id,))
        fila = cursor.fetchone()
        if fila is None:
            conn.close()
            return False, "La mesa no existe.", None
        if fila[0] == "Ocupada":
            conn.close()
            return False, "Esa mesa ya tiene una comanda abierta.", None

    estado_delivery = "Preparando" if tipo == "Delivery" else None

    cursor.execute("""
        INSERT INTO rest_comandas (mesa_id, tipo, cliente_id, mozo_usuario_id, turno, observaciones,
                                    direccion_entrega, estado_delivery)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (mesa_id if tipo == "Mesa" else None, tipo, cliente_id, mozo_usuario_id,
          calcular_turno_actual(), observaciones.strip(), direccion_entrega.strip(), estado_delivery))
    comanda_id = cursor.lastrowid

    if tipo == "Mesa":
        cursor.execute("UPDATE rest_mesas SET estado = 'Ocupada' WHERE id = ?", (mesa_id,))

    conn.commit()
    conn.close()
    return True, "Comanda abierta correctamente.", comanda_id


def asignar_repartidor(comanda_id: int, repartidor_id: int) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT tipo FROM rest_comandas WHERE id = ?", (comanda_id,))
    fila = cursor.fetchone()
    if fila is None:
        conn.close()
        return False, "La comanda no existe."
    if fila[0] != "Delivery":
        conn.close()
        return False, "Solo se puede asignar repartidor a pedidos de tipo Delivery."
    cursor.execute("UPDATE rest_comandas SET repartidor_id = ? WHERE id = ?", (repartidor_id, comanda_id))
    conn.commit()
    conn.close()
    return True, "Repartidor asignado."


def cambiar_estado_delivery(comanda_id: int, nuevo_estado: str) -> tuple[bool, str]:
    if nuevo_estado not in ESTADOS_DELIVERY:
        return False, "Estado de entrega inválido."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE rest_comandas SET estado_delivery = ? WHERE id = ?", (nuevo_estado, comanda_id))
    conn.commit()
    conn.close()
    return True, f"Pedido marcado como {nuevo_estado}."


def listar_comandas_delivery_activas() -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, COALESCE(cl.nombre, ''), c.direccion_entrega, c.estado_delivery,
               c.repartidor_id, COALESCE(r.nombre, ''), c.fecha_apertura
        FROM rest_comandas c
        LEFT JOIN clientes cl ON c.cliente_id = cl.id
        LEFT JOIN rest_repartidores r ON c.repartidor_id = r.id
        WHERE c.tipo = 'Delivery' AND c.estado = 'Abierta'
        ORDER BY c.fecha_apertura
    """)
    filas = cursor.fetchall()
    resultado = []
    for f in filas:
        cursor.execute("""
            SELECT COALESCE(SUM(cantidad * precio_unitario), 0) FROM rest_comanda_items
            WHERE comanda_id = ? AND estado_cocina != 'Cancelado'
        """, (f[0],))
        total = cursor.fetchone()[0] or 0
        resultado.append({
            "id": f[0], "cliente": f[1] or "Consumidor Final", "direccion_entrega": f[2] or "",
            "estado_delivery": f[3] or "Preparando", "repartidor_id": f[4],
            "repartidor": f[5] or "Sin asignar", "fecha_apertura": f[6], "total": total,
        })
    conn.close()
    return resultado


def obtener_comanda_activa_de_mesa(mesa_id: int) -> dict | None:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM rest_comandas WHERE mesa_id = ? AND estado = 'Abierta'", (mesa_id,))
    fila = cursor.fetchone()
    conn.close()
    return obtener_comanda_detalle(fila[0]) if fila else None


def listar_comandas_activas() -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.tipo, m.numero, c.cliente_id,
               COALESCE(cl.nombre, ''), u.nombre_completo, c.fecha_apertura, c.turno
        FROM rest_comandas c
        LEFT JOIN rest_mesas m ON c.mesa_id = m.id
        LEFT JOIN clientes cl ON c.cliente_id = cl.id
        LEFT JOIN usuarios u ON c.mozo_usuario_id = u.id
        WHERE c.estado = 'Abierta'
        ORDER BY c.fecha_apertura
    """)
    filas = cursor.fetchall()
    resultado = []
    for f in filas:
        cursor.execute("""
            SELECT COALESCE(SUM(cantidad * precio_unitario), 0) FROM rest_comanda_items
            WHERE comanda_id = ? AND estado_cocina != 'Cancelado'
        """, (f[0],))
        total = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM rest_comanda_items WHERE comanda_id = ? AND estado_cocina != 'Cancelado'",
                       (f[0],))
        cant_items = cursor.fetchone()[0]
        resultado.append({
            "id": f[0], "tipo": f[1], "mesa": f[2] or "—", "cliente_id": f[3],
            "cliente": f[4] or "Consumidor Final", "mozo": f[5] or "—",
            "fecha_apertura": f[6], "turno": f[7], "total": total, "cantidad_items": cant_items,
        })
    conn.close()
    return resultado


def obtener_comanda_detalle(comanda_id: int) -> dict | None:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.tipo, c.mesa_id, m.numero, c.cliente_id, COALESCE(cl.nombre, ''),
               c.mozo_usuario_id, u.nombre_completo, c.estado, c.turno, c.fecha_apertura,
               c.fecha_cierre, c.venta_id, c.observaciones,
               c.repartidor_id, COALESCE(r.nombre, ''), c.direccion_entrega, c.estado_delivery
        FROM rest_comandas c
        LEFT JOIN rest_mesas m ON c.mesa_id = m.id
        LEFT JOIN clientes cl ON c.cliente_id = cl.id
        LEFT JOIN usuarios u ON c.mozo_usuario_id = u.id
        LEFT JOIN rest_repartidores r ON c.repartidor_id = r.id
        WHERE c.id = ?
    """, (comanda_id,))
    f = cursor.fetchone()
    if f is None:
        conn.close()
        return None

    cursor.execute("""
        SELECT ci.id, ci.plato_id, p.nombre, ci.cantidad, ci.precio_unitario,
               ci.estado_cocina, ci.observaciones, ci.variante_id, ci.variante_nombre,
               ci.hora_inicio_preparacion, p.tiempo_preparacion_min
        FROM rest_comanda_items ci
        JOIN rest_platos p ON ci.plato_id = p.id
        WHERE ci.comanda_id = ?
        ORDER BY ci.fecha_agregado
    """, (comanda_id,))
    filas_items = cursor.fetchall()

    items = []
    ahora = datetime.datetime.now()
    for r in filas_items:
        item_id = r[0]
        cursor.execute("""
            SELECT e.id, e.producto_id, p.nombre, e.tipo, e.cantidad, e.costo_extra
            FROM rest_comanda_item_extras e JOIN productos p ON e.producto_id = p.id
            WHERE e.comanda_item_id = ?
        """, (item_id,))
        extras = [
            {"id": ex[0], "producto_id": ex[1], "nombre": ex[2], "tipo": ex[3],
             "cantidad": ex[4], "costo_extra": ex[5]}
            for ex in cursor.fetchall()
        ]
        recargo_extras = sum(e["costo_extra"] for e in extras if e["tipo"] == "Agregado")
        precio_final = r[4] + recargo_extras

        minutos_preparando = None
        excedido = False
        if r[9]:  # hora_inicio_preparacion
            try:
                inicio = datetime.datetime.fromisoformat(r[9])
                minutos_preparando = (ahora - inicio).total_seconds() / 60
                if r[10] and minutos_preparando > r[10]:
                    excedido = True
            except ValueError:
                pass

        items.append({
            "id": item_id, "plato_id": r[1], "plato": r[2], "cantidad": r[3],
            "precio_unitario": precio_final, "importe": r[3] * precio_final,
            "estado_cocina": r[5], "observaciones": r[6] or "", "variante_id": r[7],
            "variante_nombre": r[8] or "", "extras": extras,
            "tiempo_preparacion_min": r[10], "minutos_preparando": minutos_preparando,
            "excedido_tiempo": excedido,
        })
    conn.close()

    total = sum(i["importe"] for i in items if i["estado_cocina"] != "Cancelado")
    return {
        "id": f[0], "tipo": f[1], "mesa_id": f[2], "mesa": f[3] or "—", "cliente_id": f[4],
        "cliente": f[5] or "Consumidor Final", "mozo_usuario_id": f[6], "mozo": f[7] or "—",
        "estado": f[8], "turno": f[9], "fecha_apertura": f[10], "fecha_cierre": f[11],
        "venta_id": f[12], "observaciones": f[13] or "", "items": items, "total": total,
        "repartidor_id": f[14], "repartidor": f[15] or "Sin asignar",
        "direccion_entrega": f[16] or "", "estado_delivery": f[17],
    }


def agregar_item_comanda(comanda_id: int, plato_id: int, cantidad: float,
                          observaciones: str = "", variante_id: int = None) -> tuple[bool, str]:
    try:
        cantidad = float(cantidad)
        if cantidad <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return False, "La cantidad debe ser un número mayor a 0."

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT estado FROM rest_comandas WHERE id = ?", (comanda_id,))
    fila = cursor.fetchone()
    if fila is None or fila[0] != "Abierta":
        conn.close()
        return False, "Esta comanda ya no está abierta."

    cursor.execute("SELECT nombre, precio_venta, activo FROM rest_platos WHERE id = ?", (plato_id,))
    plato = cursor.fetchone()
    if plato is None or not plato[2]:
        conn.close()
        return False, "Ese plato no existe o está inactivo."

    precio_unitario = plato[1] or 0
    variante_nombre = None
    if variante_id is not None:
        cursor.execute("SELECT nombre, precio FROM rest_variantes_plato WHERE id = ?", (variante_id,))
        variante = cursor.fetchone()
        if variante is None:
            conn.close()
            return False, "El tamaño/variante elegido no existe."
        variante_nombre, precio_unitario = variante[0], variante[1]

    # Si ya está el mismo plato+variante sin observaciones propias, se suma la cantidad
    if not observaciones.strip():
        cursor.execute("""
            SELECT id, cantidad FROM rest_comanda_items
            WHERE comanda_id = ? AND plato_id = ? AND (observaciones IS NULL OR observaciones = '')
                  AND estado_cocina = 'Pendiente'
                  AND ((variante_id IS NULL AND ? IS NULL) OR variante_id = ?)
        """, (comanda_id, plato_id, variante_id, variante_id))
        existente = cursor.fetchone()
        if existente:
            cursor.execute("UPDATE rest_comanda_items SET cantidad = ? WHERE id = ?",
                           (existente[1] + cantidad, existente[0]))
            conn.commit()
            conn.close()
            return True, f"Se sumó '{plato[0]}' a la comanda."

    cursor.execute("""
        INSERT INTO rest_comanda_items
            (comanda_id, plato_id, cantidad, precio_unitario, observaciones, variante_id, variante_nombre)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (comanda_id, plato_id, cantidad, precio_unitario, observaciones.strip(), variante_id, variante_nombre))
    conn.commit()
    conn.close()
    return True, f"'{plato[0]}' agregado a la comanda."


def cambiar_cantidad_item(item_id: int, nueva_cantidad: float) -> tuple[bool, str]:
    try:
        nueva_cantidad = float(nueva_cantidad)
    except (TypeError, ValueError):
        return False, "La cantidad debe ser un número."
    conn = conectar()
    cursor = conn.cursor()
    if nueva_cantidad <= 0:
        cursor.execute("DELETE FROM rest_comanda_items WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
        return True, "Ítem quitado de la comanda."
    cursor.execute("UPDATE rest_comanda_items SET cantidad = ? WHERE id = ?", (nueva_cantidad, item_id))
    conn.commit()
    conn.close()
    return True, "Cantidad actualizada."


def quitar_item_comanda(item_id: int) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rest_comanda_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return True, "Ítem quitado de la comanda."


def cambiar_estado_item(item_id: int, nuevo_estado: str) -> tuple[bool, str]:
    if nuevo_estado not in ESTADOS_ITEM:
        return False, "Estado inválido."
    conn = conectar()
    cursor = conn.cursor()
    if nuevo_estado == "Preparando":
        # Arranca el control de tiempo de horneado/preparación
        cursor.execute("""
            UPDATE rest_comanda_items SET estado_cocina = ?, hora_inicio_preparacion = datetime('now', 'localtime')
            WHERE id = ?
        """, (nuevo_estado, item_id))
    else:
        cursor.execute("UPDATE rest_comanda_items SET estado_cocina = ? WHERE id = ?", (nuevo_estado, item_id))
    conn.commit()
    conn.close()
    return True, f"Ítem marcado como {nuevo_estado}."


# ---------------- Personalización (extras agregados/quitados por pedido) ----------------
def agregar_extra_item(comanda_item_id: int, producto_id: int, tipo: str, cantidad: float,
                        costo_extra: float = 0) -> tuple[bool, str]:
    if tipo not in ("Agregado", "Quitado"):
        return False, "Tipo de personalización inválido."
    try:
        cantidad = float(cantidad)
        costo_extra = float(costo_extra)
        if cantidad <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return False, "La cantidad debe ser un número mayor a 0."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO rest_comanda_item_extras (comanda_item_id, producto_id, tipo, cantidad, costo_extra)
        VALUES (?, ?, ?, ?, ?)
    """, (comanda_item_id, producto_id, tipo, cantidad, costo_extra if tipo == "Agregado" else 0))
    conn.commit()
    conn.close()
    verbo = "agregado" if tipo == "Agregado" else "quitado"
    return True, f"Ingrediente {verbo} correctamente."


def quitar_extra_item(extra_id: int) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rest_comanda_item_extras WHERE id = ?", (extra_id,))
    conn.commit()
    conn.close()
    return True, "Personalización quitada."


def _calcular_consumo_insumos_comanda(cursor, comanda_id: int) -> dict:
    """Calcula cuánto de cada insumo hace falta para preparar todo lo
    pedido en una comanda, contemplando: el multiplicador de la variante/
    tamaño elegido (una pizza Familiar consume más que una Individual) y
    la personalización de cada ítem (ingredientes agregados suman
    consumo extra; los quitados lo restan, hasta un mínimo de 0)."""
    cursor.execute("""
        SELECT ci.id, ci.plato_id, ci.cantidad, ci.variante_id
        FROM rest_comanda_items ci
        WHERE ci.comanda_id = ? AND ci.estado_cocina != 'Cancelado'
    """, (comanda_id,))
    items = cursor.fetchall()

    consumo_por_insumo = {}
    for item_id, plato_id, cantidad_plato, variante_id in items:
        multiplicador = 1.0
        if variante_id is not None:
            cursor.execute("SELECT multiplicador_receta FROM rest_variantes_plato WHERE id = ?", (variante_id,))
            fila_var = cursor.fetchone()
            if fila_var:
                multiplicador = fila_var[0] or 1.0

        consumo_item = {}
        cursor.execute("SELECT producto_id, cantidad FROM rest_receta_ingredientes WHERE plato_id = ?",
                       (plato_id,))
        for producto_id, cantidad_receta in cursor.fetchall():
            consumo_item[producto_id] = cantidad_receta * multiplicador

        cursor.execute("SELECT producto_id, tipo, cantidad FROM rest_comanda_item_extras WHERE comanda_item_id = ?",
                       (item_id,))
        for producto_id, tipo, cantidad_extra in cursor.fetchall():
            if tipo == "Agregado":
                consumo_item[producto_id] = consumo_item.get(producto_id, 0) + cantidad_extra
            else:  # Quitado
                consumo_item[producto_id] = max(consumo_item.get(producto_id, 0) - cantidad_extra, 0)

        for producto_id, cantidad_unitaria in consumo_item.items():
            consumo_por_insumo[producto_id] = (
                consumo_por_insumo.get(producto_id, 0) + cantidad_unitaria * cantidad_plato
            )
    return consumo_por_insumo


def verificar_insumos_suficientes(comanda_id: int) -> tuple[bool, list[dict]]:
    """Antes de cerrar la comanda, confirma que haya stock suficiente de
    cada insumo necesario para preparar todos los platos pedidos (ya
    contemplando tamaños/variantes y personalización)."""
    conn = conectar()
    cursor = conn.cursor()
    consumo_por_insumo = _calcular_consumo_insumos_comanda(cursor, comanda_id)

    faltantes = []
    for producto_id, cantidad_necesaria in consumo_por_insumo.items():
        cursor.execute("SELECT nombre, stock, control_stock, unidad_medida FROM productos WHERE id = ?",
                       (producto_id,))
        fila = cursor.fetchone()
        if fila is None:
            continue
        nombre, stock, control_stock, unidad = fila
        if control_stock == "Ilimitado":
            continue
        if (stock or 0) < cantidad_necesaria:
            faltantes.append({
                "producto_id": producto_id, "nombre": nombre, "necesario": cantidad_necesaria,
                "disponible": stock or 0, "unidad_medida": unidad or "Unidad",
            })
    conn.close()
    return (len(faltantes) == 0), faltantes


def cerrar_comanda(comanda_id: int, usuario_id: int, condicion: str = "contado",
                    forma_pago: str = "Efectivo", cliente_id: int = None,
                    fecha_vencimiento_credito: str = None) -> tuple[bool, str, int | None]:
    """Cobra la comanda: valida insumos, genera la venta real (misma
    numeración de factura y caja que el resto del sistema) y descuenta
    los insumos de cada plato según su receta."""
    detalle = obtener_comanda_detalle(comanda_id)
    if detalle is None:
        return False, "La comanda no existe.", None
    if detalle["estado"] != "Abierta":
        return False, "Esta comanda ya fue cerrada o cancelada.", None

    items_validos = [i for i in detalle["items"] if i["estado_cocina"] != "Cancelado"]
    if not items_validos:
        return False, "La comanda no tiene ningún ítem para cobrar.", None

    ok_stock, faltantes = verificar_insumos_suficientes(comanda_id)
    if not ok_stock:
        detalle_faltantes = "\n".join(
            f"- {f['nombre']}: necesita {f['necesario']:g} {f['unidad_medida'].lower()}, "
            f"disponible {f['disponible']:g}" for f in faltantes
        )
        return False, f"No hay insumos suficientes para cerrar esta comanda:\n{detalle_faltantes}", None

    items_venta = []
    for i in items_validos:
        descripcion = i["plato"]
        if i.get("variante_nombre"):
            descripcion += f" ({i['variante_nombre']})"
        agregados = [e["nombre"] for e in i.get("extras", []) if e["tipo"] == "Agregado"]
        if agregados:
            descripcion += " +" + "+".join(agregados)
        items_venta.append({
            "producto_id": None, "descripcion_libre": descripcion, "cantidad": i["cantidad"],
            "precio_unitario": i["precio_unitario"],
        })
    cliente_final = cliente_id if cliente_id is not None else detalle["cliente_id"]
    ok, msg, venta_id = procesar_venta(
        items_venta, usuario_id, cliente_final, condicion=condicion, forma_pago=forma_pago,
        fecha_vencimiento_credito=fecha_vencimiento_credito,
    )
    if not ok:
        return False, msg, None

    # Descontar los insumos de cada plato vendido, según su receta
    # (contemplando el tamaño/variante elegido y la personalización de cada ítem)
    conn = conectar()
    cursor = conn.cursor()
    consumo_por_insumo = _calcular_consumo_insumos_comanda(cursor, comanda_id)

    from models_inventario import registrar_movimiento_externo
    for producto_id, cantidad_consumida in consumo_por_insumo.items():
        cursor.execute("SELECT control_stock, stock FROM productos WHERE id = ?", (producto_id,))
        fila = cursor.fetchone()
        if fila is None:
            continue
        if fila[0] == "Ilimitado":
            # No hay stock real que descontar, pero se deja constancia del
            # consumo del insumo en su historial, marcada como "Ilimitado".
            registrar_movimiento_externo(
                cursor, producto_id, "salida", cantidad_consumida,
                f"Consumo de insumo - Comanda Nro. {comanda_id} (Venta {venta_id})",
                usuario_id, None, nro_comprobante=str(venta_id), es_ilimitado=True,
            )
            continue
        nuevo_stock = (fila[1] or 0) - cantidad_consumida
        cursor.execute("UPDATE productos SET stock = ? WHERE id = ?", (nuevo_stock, producto_id))
        registrar_movimiento_externo(
            cursor, producto_id, "salida", cantidad_consumida,
            f"Consumo de insumo - Comanda Nro. {comanda_id} (Venta {venta_id})",
            usuario_id, nuevo_stock, nro_comprobante=str(venta_id),
        )

    cursor.execute("""
        UPDATE rest_comandas SET estado = 'Cerrada', fecha_cierre = datetime('now', 'localtime'), venta_id = ?
        WHERE id = ?
    """, (venta_id, comanda_id))

    if detalle["mesa_id"]:
        cursor.execute("UPDATE rest_mesas SET estado = 'Para Limpiar' WHERE id = ?", (detalle["mesa_id"],))

    conn.commit()
    conn.close()
    return True, msg, venta_id


def cancelar_comanda(comanda_id: int) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT mesa_id, estado FROM rest_comandas WHERE id = ?", (comanda_id,))
    fila = cursor.fetchone()
    if fila is None:
        conn.close()
        return False, "La comanda no existe."
    if fila[1] != "Abierta":
        conn.close()
        return False, "Esta comanda ya no está abierta."

    cursor.execute("UPDATE rest_comandas SET estado = 'Cancelada', fecha_cierre = datetime('now', 'localtime') WHERE id = ?",
                   (comanda_id,))
    if fila[0]:
        cursor.execute("UPDATE rest_mesas SET estado = 'Libre' WHERE id = ?", (fila[0],))
    conn.commit()
    conn.close()
    return True, "Comanda cancelada."


# ============================================================
# DASHBOARD Y REPORTES
# ============================================================
def conteos_dashboard() -> dict:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM rest_mesas WHERE activa = 1 AND estado = 'Libre'")
    mesas_libres = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM rest_mesas WHERE activa = 1 AND estado = 'Ocupada'")
    mesas_ocupadas = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM rest_comandas WHERE estado = 'Abierta'")
    comandas_abiertas = cursor.fetchone()[0]
    cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(
            (SELECT COALESCE(SUM(cantidad * precio_unitario), 0) FROM rest_comanda_items
             WHERE comanda_id = c.id AND estado_cocina != 'Cancelado')
        ), 0)
        FROM rest_comandas c
        WHERE c.estado = 'Cerrada' AND date(c.fecha_cierre) = date('now', 'localtime')
    """)
    cant_hoy, ingresos_hoy = cursor.fetchone()
    conn.close()
    return {
        "mesas_libres": mesas_libres, "mesas_ocupadas": mesas_ocupadas,
        "comandas_abiertas": comandas_abiertas, "comandas_cerradas_hoy": cant_hoy or 0,
        "ingresos_hoy": ingresos_hoy or 0,
    }


def platos_mas_vendidos(fecha_desde: str, fecha_hasta: str, limite: int = 10) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.nombre, p.categoria, SUM(ci.cantidad) AS cant, SUM(ci.cantidad * ci.precio_unitario) AS ingreso
        FROM rest_comanda_items ci
        JOIN rest_comandas c ON ci.comanda_id = c.id
        JOIN rest_platos p ON ci.plato_id = p.id
        WHERE c.estado = 'Cerrada' AND ci.estado_cocina != 'Cancelado'
              AND date(c.fecha_cierre) BETWEEN date(?) AND date(?)
        GROUP BY ci.plato_id
        ORDER BY cant DESC
        LIMIT ?
    """, (fecha_desde, fecha_hasta, limite))
    filas = cursor.fetchall()
    conn.close()
    return [{"nombre": f[0], "categoria": f[1], "cantidad_vendida": f[2], "ingreso": f[3]} for f in filas]


def margen_por_plato(fecha_desde: str, fecha_hasta: str) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ci.plato_id, p.nombre, SUM(ci.cantidad) AS cant, SUM(ci.cantidad * ci.precio_unitario) AS ingreso
        FROM rest_comanda_items ci
        JOIN rest_comandas c ON ci.comanda_id = c.id
        JOIN rest_platos p ON ci.plato_id = p.id
        WHERE c.estado = 'Cerrada' AND ci.estado_cocina != 'Cancelado'
              AND date(c.fecha_cierre) BETWEEN date(?) AND date(?)
        GROUP BY ci.plato_id
        ORDER BY ingreso DESC
    """, (fecha_desde, fecha_hasta))
    filas = cursor.fetchall()

    resultado = []
    for plato_id, nombre, cant, ingreso in filas:
        cursor.execute("""
            SELECT COALESCE(SUM(ri.cantidad * pr.precio_compra), 0)
            FROM rest_receta_ingredientes ri JOIN productos pr ON ri.producto_id = pr.id
            WHERE ri.plato_id = ?
        """, (plato_id,))
        costo_unitario = cursor.fetchone()[0] or 0
        costo_total = costo_unitario * cant
        margen = ingreso - costo_total
        resultado.append({
            "nombre": nombre, "cantidad_vendida": cant, "ingreso": ingreso,
            "costo": costo_total, "margen": margen,
            "margen_pct": (margen / ingreso * 100) if ingreso else 0,
        })
    conn.close()
    return resultado


def costos_vs_ingresos(fecha_desde: str, fecha_hasta: str) -> dict:
    datos = margen_por_plato(fecha_desde, fecha_hasta)
    ingresos = sum(d["ingreso"] for d in datos)
    costos = sum(d["costo"] for d in datos)
    margen = ingresos - costos
    return {
        "ingresos": ingresos, "costos": costos, "margen": margen,
        "margen_pct": (margen / ingresos * 100) if ingresos else 0,
    }


def ventas_por_turno(fecha_desde: str, fecha_hasta: str) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.turno, COUNT(DISTINCT c.id),
               COALESCE(SUM(ci.cantidad * ci.precio_unitario), 0)
        FROM rest_comandas c
        LEFT JOIN rest_comanda_items ci ON ci.comanda_id = c.id AND ci.estado_cocina != 'Cancelado'
        WHERE c.estado = 'Cerrada' AND date(c.fecha_cierre) BETWEEN date(?) AND date(?)
        GROUP BY c.turno
    """, (fecha_desde, fecha_hasta))
    filas = {f[0]: (f[1], f[2]) for f in cursor.fetchall()}
    conn.close()
    return [
        {"turno": t, "cantidad_comandas": filas.get(t, (0, 0))[0], "ingreso": filas.get(t, (0, 0))[1]}
        for t in TURNOS
    ]
