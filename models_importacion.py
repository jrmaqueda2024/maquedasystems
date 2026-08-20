"""
models_importacion.py
Lógica de negocio del módulo Importaciones: compras hechas en plataformas
del exterior (eBay, AliExpress, Temu, Shein, Alibaba, Made in China, etc.)
que se reciben en un casillero (Miami o Shenzhen) antes de llegar a
Paraguay a través de un courier.

Idea central del cálculo de costos:
  - Cada compra registrada es "una caja": puede traer 1 o varios
    productos distintos, en 1 o varias unidades cada uno.
  - Al retirar la caja del courier se paga por el PESO TOTAL de la caja
    (no por unidad), así que ese costo de envío hay que repartirlo entre
    todas las unidades que venían adentro.
  - El costo de envío total de la caja se calcula automáticamente como
    peso_caja_kg * tarifa_por_kg del courier (aérea o marítima, según lo
    elegido), o se puede cargar un monto manual (por ejemplo cuando el
    envío hasta el casillero salió gratis o vino incluido).
  - Ese costo de envío total se reparte proporcionalmente entre todas las
    unidades de todos los productos de la caja (a prorrata de cantidad),
    así que en una caja con un solo producto (ej. 10 auriculares, caja de
    1 kg) el resultado es sencillamente costo_envio_total / 10 por
    unidad; si la caja trae varios productos distintos, cada uno recibe
    su parte según cuántas unidades ocupa dentro del total de la caja.
  - costo_total_unitario = costo_unitario_compra (lo pagado en la
    plataforma) + costo_envio_unitario (la parte del flete que le toca).
  - Con el precio_venta_publico que el usuario carga, se calcula la
    ganancia y el margen por unidad, y al "enviar a inventario" ese costo
    y precio quedan cargados en el producto para poder venderlo desde el
    módulo Ventas de siempre.
"""
import datetime
import json
import urllib.request

from database import conectar

PLATAFORMAS_INICIALES = ["eBay", "AliExpress", "Temu", "Shein", "Alibaba", "Made in China", "Amazon", "Otro"]
TIPOS_ENVIO = ["Aéreo", "Marítimo"]
CASILLEROS = ["Miami, FL (EE.UU.)", "Shenzhen (China)", "Otro"]
ESTADOS_COMPRA = [
    "Pendiente", "Comprado", "En camino al casillero", "En casillero",
    "En camino a Paraguay", "Recibido",
]
COLOR_ESTADO = {
    "Pendiente": "#6b7280",
    "Comprado": "#2563eb",
    "En camino al casillero": "#d97706",
    "En casillero": "#7c3aed",
    "En camino a Paraguay": "#0f766e",
    "Recibido": "#16a34a",
}


class ErrorDeImportacion(Exception):
    pass


# ============================================================
# PLATAFORMAS / TIENDAS (editable desde la UI)
# ============================================================
def listar_plataformas(solo_activas: bool = True) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    where = "WHERE activa = 1" if solo_activas else ""
    cursor.execute(f"SELECT id, nombre, activa FROM import_plataformas {where} ORDER BY nombre")
    filas = cursor.fetchall()
    conn.close()
    return [{"id": f[0], "nombre": f[1], "activa": bool(f[2])} for f in filas]


def crear_plataforma(nombre: str) -> tuple[bool, str]:
    if not nombre.strip():
        return False, "El nombre de la tienda es obligatorio."
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO import_plataformas (nombre) VALUES (?)", (nombre.strip(),))
        conn.commit()
        return True, f"Tienda '{nombre.strip()}' agregada."
    except Exception:
        return False, "Ya existe una tienda con ese nombre."
    finally:
        conn.close()


def cambiar_estado_plataforma(plataforma_id: int, activa: bool) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE import_plataformas SET activa = ? WHERE id = ?", (1 if activa else 0, plataforma_id))
    conn.commit()
    conn.close()
    return True, "Tienda activada." if activa else "Tienda desactivada."


def eliminar_plataforma(plataforma_id: int) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre FROM import_plataformas WHERE id = ?", (plataforma_id,))
    fila = cursor.fetchone()
    if not fila:
        conn.close()
        return False, "La tienda no existe."
    cursor.execute("SELECT COUNT(*) FROM import_compras WHERE plataforma = ?", (fila[0],))
    if cursor.fetchone()[0] > 0:
        conn.close()
        return False, "No se puede eliminar: hay compras registradas con esta tienda. Podés desactivarla."
    cursor.execute("DELETE FROM import_plataformas WHERE id = ?", (plataforma_id,))
    conn.commit()
    conn.close()
    return True, "Tienda eliminada."


# ============================================================
# TIPO DE CAMBIO (US$ -> Gs.), para mostrar todo también en guaraníes
# ============================================================
def obtener_tasa_cambio() -> float:
    """Devuelve cuántos guaraníes vale 1 dólar, según lo cargado a mano o
    la última actualización automática. Si por algún motivo no hay fila
    de configuración todavía, devuelve un valor de referencia razonable."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT tasa_cambio_usd_gs FROM import_configuracion WHERE id = 1")
    fila = cursor.fetchone()
    conn.close()
    return float(fila[0]) if fila else 7300.0


def obtener_info_tasa_cambio() -> dict:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT tasa_cambio_usd_gs, fecha_actualizacion FROM import_configuracion WHERE id = 1")
    fila = cursor.fetchone()
    conn.close()
    if not fila:
        return {"tasa": 7300.0, "fecha_actualizacion": None}
    return {"tasa": float(fila[0]), "fecha_actualizacion": fila[1]}


def guardar_tasa_cambio(valor: float) -> tuple[bool, str]:
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        return False, "El tipo de cambio debe ser un número."
    if valor <= 0:
        return False, "El tipo de cambio debe ser mayor a cero."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE import_configuracion SET tasa_cambio_usd_gs = ?, fecha_actualizacion = datetime('now', 'localtime')
        WHERE id = 1
    """, (valor,))
    conn.commit()
    conn.close()
    return True, "Tipo de cambio actualizado."


def actualizar_tasa_cambio_automatica() -> tuple[bool, str, float | None]:
    """Descarga la cotización USD → PYG desde Frankfurter (mismo servicio
    que usa el módulo Cotizaciones, con datos de referencia del BCE) y la
    guarda como tipo de cambio del módulo. Requiere conexión a Internet."""
    try:
        req = urllib.request.Request(
            "https://api.frankfurter.app/latest?from=USD&to=PYG",
            headers={"User-Agent": "MaquedaSystems/1.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        tasa = data.get("rates", {}).get("PYG")
        if not tasa:
            return False, "El servicio de cotizaciones no devolvió un valor para guaraníes.", None
        guardar_tasa_cambio(tasa)
        return True, f"Tipo de cambio actualizado: 1 US$ = Gs. {tasa:,.0f}".replace(",", "."), float(tasa)
    except Exception as e:
        return False, f"No se pudo descargar el tipo de cambio (¿hay conexión a Internet?): {e}", None


# ============================================================
# COURIERS / CASILLEROS
# ============================================================
def listar_couriers(solo_activos: bool = False) -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    where = "WHERE activo = 1" if solo_activos else ""
    cursor.execute(f"""
        SELECT id, nombre, email, ruc, telefono, costo_kg_aereo, costo_kg_maritimo,
               direccion_casillero_miami, direccion_casillero_shenzhen, notas, activo
        FROM import_couriers {where}
        ORDER BY nombre
    """)
    filas = cursor.fetchall()
    conn.close()
    campos = ["id", "nombre", "email", "ruc", "telefono", "costo_kg_aereo", "costo_kg_maritimo",
              "direccion_casillero_miami", "direccion_casillero_shenzhen", "notas", "activo"]
    resultado = []
    for f in filas:
        d = dict(zip(campos, f))
        d["activo"] = bool(d["activo"])
        resultado.append(d)
    return resultado


def obtener_courier(courier_id: int) -> dict | None:
    for c in listar_couriers():
        if c["id"] == courier_id:
            return c
    return None


def crear_courier(nombre: str, email: str = "", ruc: str = "", telefono: str = "",
                   costo_kg_aereo: float = 0, costo_kg_maritimo: float = 0,
                   direccion_casillero_miami: str = "", direccion_casillero_shenzhen: str = "",
                   notas: str = "") -> tuple[bool, str]:
    if not nombre.strip():
        return False, "El nombre del courier es obligatorio."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO import_couriers
            (nombre, email, ruc, telefono, costo_kg_aereo, costo_kg_maritimo,
             direccion_casillero_miami, direccion_casillero_shenzhen, notas)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (nombre.strip(), email.strip(), ruc.strip(), telefono.strip(),
          costo_kg_aereo, costo_kg_maritimo, direccion_casillero_miami.strip(),
          direccion_casillero_shenzhen.strip(), notas.strip()))
    conn.commit()
    conn.close()
    return True, f"Courier '{nombre.strip()}' agregado."


def editar_courier(courier_id: int, nombre: str, email: str, ruc: str, telefono: str,
                    costo_kg_aereo: float, costo_kg_maritimo: float,
                    direccion_casillero_miami: str, direccion_casillero_shenzhen: str,
                    notas: str) -> tuple[bool, str]:
    if not nombre.strip():
        return False, "El nombre del courier es obligatorio."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE import_couriers SET nombre=?, email=?, ruc=?, telefono=?, costo_kg_aereo=?,
               costo_kg_maritimo=?, direccion_casillero_miami=?, direccion_casillero_shenzhen=?, notas=?
        WHERE id=?
    """, (nombre.strip(), email.strip(), ruc.strip(), telefono.strip(),
          costo_kg_aereo, costo_kg_maritimo, direccion_casillero_miami.strip(),
          direccion_casillero_shenzhen.strip(), notas.strip(), courier_id))
    conn.commit()
    conn.close()
    # Recalcula las compras que usan este courier y no tienen costo manual,
    # por si cambió la tarifa por kilo.
    _recalcular_compras_de_courier(courier_id)
    return True, "Courier actualizado."


def cambiar_estado_courier(courier_id: int, activo: bool) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE import_couriers SET activo = ? WHERE id = ?", (1 if activo else 0, courier_id))
    conn.commit()
    conn.close()
    return True, "Courier activado." if activo else "Courier desactivado."


def eliminar_courier(courier_id: int) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM import_compras WHERE courier_id = ?", (courier_id,))
    if cursor.fetchone()[0] > 0:
        conn.close()
        return False, "No se puede eliminar: hay compras registradas con este courier. Podés desactivarlo."
    cursor.execute("DELETE FROM import_couriers WHERE id = ?", (courier_id,))
    conn.commit()
    conn.close()
    return True, "Courier eliminado."


# ============================================================
# CÁLCULO DE COSTOS (motor central)
# ============================================================
def _tarifa_kg(courier: dict | None, tipo_envio: str) -> float:
    if not courier:
        return 0.0
    return courier["costo_kg_aereo"] if tipo_envio == "Aéreo" else courier["costo_kg_maritimo"]


def calcular_costo_envio(peso_caja_kg: float, courier_id: int | None, tipo_envio: str,
                          costo_envio_manual: float | None) -> float:
    """Costo de envío total de la caja hasta el casillero. Si se cargó un
    monto manual (por ejemplo porque vino gratis o ya incluido), ese manda;
    si no, se calcula automáticamente como peso x tarifa por kilo del
    courier elegido."""
    if costo_envio_manual is not None:
        return round(float(costo_envio_manual), 2)
    courier = obtener_courier(courier_id) if courier_id else None
    tarifa = _tarifa_kg(courier, tipo_envio)
    return round(float(peso_caja_kg or 0) * tarifa, 2)


def _recalcular_items(items: list[dict], costo_envio_total: float) -> list[dict]:
    """Reparte el costo_envio_total proporcionalmente entre las unidades de
    todos los items (a prorrata de cantidad) y calcula el costo total
    unitario, la ganancia y el margen de cada uno."""
    total_unidades = sum(float(it.get("cantidad") or 0) for it in items) or 0
    envio_por_unidad = (costo_envio_total / total_unidades) if total_unidades > 0 else 0.0

    resultado = []
    for it in items:
        cantidad = float(it.get("cantidad") or 0)
        costo_unitario_compra = float(it.get("costo_unitario_compra") or 0)
        costo_total_unitario = round(costo_unitario_compra + envio_por_unidad, 4)
        precio_venta = it.get("precio_venta_publico")
        precio_venta = float(precio_venta) if precio_venta not in (None, "") else None
        ganancia_unitaria = round(precio_venta - costo_total_unitario, 4) if precio_venta is not None else None
        margen_pct = (round((ganancia_unitaria / precio_venta) * 100, 2)
                      if (precio_venta and ganancia_unitaria is not None and precio_venta > 0) else None)
        nuevo = dict(it)
        nuevo["costo_envio_unitario"] = round(envio_por_unidad, 4)
        nuevo["costo_total_unitario"] = costo_total_unitario
        nuevo["ganancia_unitaria"] = ganancia_unitaria
        nuevo["margen_pct"] = margen_pct
        resultado.append(nuevo)
    return resultado


def _recalcular_compras_de_courier(courier_id: int):
    """Cuando cambia la tarifa por kg de un courier, recalcula (sin tocar
    fechas/estado) las compras que lo usan y no tienen costo manual."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, peso_caja_kg, tipo_envio, costo_envio_manual
        FROM import_compras WHERE courier_id = ?
    """, (courier_id,))
    compras = cursor.fetchall()
    conn.close()
    for compra_id, peso, tipo_envio, manual in compras:
        if manual is not None:
            continue  # respeta el override manual
        _recalcular_y_guardar_compra(compra_id)


def _recalcular_y_guardar_compra(compra_id: int):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT peso_caja_kg, courier_id, tipo_envio, costo_envio_manual
        FROM import_compras WHERE id = ?
    """, (compra_id,))
    fila = cursor.fetchone()
    if not fila:
        conn.close()
        return
    peso, courier_id, tipo_envio, manual = fila
    costo_envio_total = calcular_costo_envio(peso, courier_id, tipo_envio, manual)
    cursor.execute("UPDATE import_compras SET costo_envio_total = ? WHERE id = ?",
                    (costo_envio_total, compra_id))

    cursor.execute("""
        SELECT id, cantidad, costo_unitario_compra, precio_venta_publico
        FROM import_detalle WHERE compra_id = ?
    """, (compra_id,))
    items = [{"id": f[0], "cantidad": f[1], "costo_unitario_compra": f[2],
              "precio_venta_publico": f[3]} for f in cursor.fetchall()]
    items_recalc = _recalcular_items(items, costo_envio_total)
    for it in items_recalc:
        cursor.execute("""
            UPDATE import_detalle SET costo_envio_unitario=?, costo_total_unitario=?
            WHERE id=?
        """, (it["costo_envio_unitario"], it["costo_total_unitario"], it["id"]))
    conn.commit()
    conn.close()


def previsualizar_costos(peso_caja_kg: float, courier_id: int | None, tipo_envio: str,
                          costo_envio_manual: float | None, items: list[dict]) -> tuple[float, list[dict]]:
    """Igual que el cálculo que hace crear_compra/editar_compra, pero sin
    tocar la base de datos: para mostrar en vivo en la ficha, mientras el
    usuario todavía está cargando los datos."""
    costo_envio_total = calcular_costo_envio(peso_caja_kg, courier_id, tipo_envio, costo_envio_manual)
    return costo_envio_total, _recalcular_items(items, costo_envio_total)


# ============================================================
# COMPRAS (cabecera + detalle)
# ============================================================
def listar_compras(texto_busqueda: str = "", estado: str = "", plataforma: str = "") -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    condiciones, parametros = [], []
    if texto_busqueda.strip():
        condiciones.append("(c.referencia LIKE ? OR co.nombre LIKE ? OR CAST(c.id AS TEXT) LIKE ?)")
        comodin = f"%{texto_busqueda.strip()}%"
        parametros.extend([comodin, comodin, comodin])
    if estado:
        condiciones.append("c.estado = ?")
        parametros.append(estado)
    if plataforma:
        condiciones.append("c.plataforma = ?")
        parametros.append(plataforma)
    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    cursor.execute(f"""
        SELECT c.id, c.plataforma, c.referencia, c.courier_id, co.nombre, c.casillero,
               c.tipo_envio, c.peso_caja_kg, c.costo_envio_total, c.estado,
               c.fecha_compra, c.fecha_envio_casillero, c.fecha_recepcion,
               (SELECT COALESCE(SUM(cantidad), 0) FROM import_detalle WHERE compra_id = c.id),
               (SELECT COALESCE(SUM(cantidad * costo_unitario_compra), 0) FROM import_detalle WHERE compra_id = c.id)
        FROM import_compras c
        LEFT JOIN import_couriers co ON c.courier_id = co.id
        {where}
        ORDER BY c.id DESC
    """, parametros)
    filas = cursor.fetchall()
    conn.close()

    resultado = []
    for f in filas:
        total_unidades = f[13]
        costo_productos = f[14]
        inversion_total = round(costo_productos + (f[8] or 0), 2)
        resultado.append({
            "id": f[0], "plataforma": f[1], "referencia": f[2] or "", "courier_id": f[3],
            "courier": f[4] or "Sin courier", "casillero": f[5], "tipo_envio": f[6],
            "peso_caja_kg": f[7], "costo_envio_total": f[8], "estado": f[9],
            "fecha_compra": f[10], "fecha_envio_casillero": f[11], "fecha_recepcion": f[12],
            "total_unidades": total_unidades, "costo_productos": costo_productos,
            "inversion_total": inversion_total,
            "dias_transcurridos": _dias_entre(f[10], f[12]),
        })
    return resultado


def _dias_entre(fecha_desde: str, fecha_hasta: str | None) -> int | None:
    if not fecha_desde:
        return None
    try:
        d1 = datetime.date.fromisoformat(fecha_desde[:10])
    except ValueError:
        return None
    if fecha_hasta:
        try:
            d2 = datetime.date.fromisoformat(fecha_hasta[:10])
        except ValueError:
            return None
    else:
        d2 = datetime.date.today()
    return (d2 - d1).days


def obtener_compra_detalle(compra_id: int) -> dict | None:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.plataforma, c.referencia, c.courier_id, co.nombre, c.casillero,
               c.tipo_envio, c.peso_caja_kg, c.costo_envio_manual, c.costo_envio_total,
               c.estado, c.fecha_compra, c.fecha_envio_casillero, c.fecha_recepcion, c.notas
        FROM import_compras c
        LEFT JOIN import_couriers co ON c.courier_id = co.id
        WHERE c.id = ?
    """, (compra_id,))
    f = cursor.fetchone()
    if not f:
        conn.close()
        return None
    cabecera = {
        "id": f[0], "plataforma": f[1], "referencia": f[2] or "", "courier_id": f[3],
        "courier": f[4] or "Sin courier", "casillero": f[5], "tipo_envio": f[6],
        "peso_caja_kg": f[7], "costo_envio_manual": f[8], "costo_envio_total": f[9],
        "estado": f[10], "fecha_compra": f[11], "fecha_envio_casillero": f[12],
        "fecha_recepcion": f[13], "notas": f[14] or "",
    }
    cursor.execute("""
        SELECT id, producto_nombre, cantidad, costo_unitario_compra, costo_envio_unitario,
               costo_total_unitario, precio_venta_publico, producto_id_generado,
               enviado_inventario, notas
        FROM import_detalle WHERE compra_id = ? ORDER BY id
    """, (compra_id,))
    campos = ["id", "producto_nombre", "cantidad", "costo_unitario_compra", "costo_envio_unitario",
              "costo_total_unitario", "precio_venta_publico", "producto_id_generado",
              "enviado_inventario", "notas"]
    items = []
    for fila in cursor.fetchall():
        it = dict(zip(campos, fila))
        it["enviado_inventario"] = bool(it["enviado_inventario"])
        precio = it["precio_venta_publico"]
        if precio:
            it["ganancia_unitaria"] = round(precio - it["costo_total_unitario"], 4)
            it["margen_pct"] = round((it["ganancia_unitaria"] / precio) * 100, 2) if precio > 0 else None
        else:
            it["ganancia_unitaria"] = None
            it["margen_pct"] = None
        items.append(it)
    conn.close()
    cabecera["items"] = items
    cabecera["total_unidades"] = sum(it["cantidad"] for it in items)
    cabecera["costo_productos"] = round(sum(it["cantidad"] * it["costo_unitario_compra"] for it in items), 2)
    cabecera["inversion_total"] = round(cabecera["costo_productos"] + (cabecera["costo_envio_total"] or 0), 2)
    cabecera["dias_transcurridos"] = _dias_entre(cabecera["fecha_compra"], cabecera["fecha_recepcion"])
    return cabecera


def crear_compra(plataforma: str, referencia: str, courier_id: int | None, casillero: str,
                  tipo_envio: str, peso_caja_kg: float, costo_envio_manual: float | None,
                  estado: str, fecha_compra: str, fecha_envio_casillero: str | None,
                  fecha_recepcion: str | None, notas: str, items: list[dict],
                  usuario_id: int | None = None) -> tuple[bool, str, int | None]:
    if not plataforma:
        return False, "Elegí la plataforma donde se hizo la compra.", None
    if not items:
        return False, "Agregá al menos un producto a la caja.", None
    for it in items:
        if not str(it.get("producto_nombre", "")).strip():
            return False, "Todos los productos necesitan un nombre.", None
        if float(it.get("cantidad") or 0) <= 0:
            return False, "La cantidad de cada producto debe ser mayor a cero.", None

    conn = conectar()
    cursor = conn.cursor()
    try:
        costo_envio_total = calcular_costo_envio(peso_caja_kg, courier_id, tipo_envio, costo_envio_manual)
        items_recalc = _recalcular_items(items, costo_envio_total)

        cursor.execute("""
            INSERT INTO import_compras
                (plataforma, referencia, courier_id, casillero, tipo_envio, peso_caja_kg,
                 costo_envio_manual, costo_envio_total, estado, fecha_compra,
                 fecha_envio_casillero, fecha_recepcion, notas, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (plataforma, referencia.strip(), courier_id, casillero, tipo_envio, peso_caja_kg,
              costo_envio_manual, costo_envio_total, estado, fecha_compra,
              fecha_envio_casillero or None, fecha_recepcion or None, notas.strip(), usuario_id))
        compra_id = cursor.lastrowid
        for it in items_recalc:
            cursor.execute("""
                INSERT INTO import_detalle
                    (compra_id, producto_nombre, cantidad, costo_unitario_compra,
                     costo_envio_unitario, costo_total_unitario, precio_venta_publico, notas)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (compra_id, it["producto_nombre"].strip(), it["cantidad"], it["costo_unitario_compra"],
                  it["costo_envio_unitario"], it["costo_total_unitario"], it.get("precio_venta_publico"),
                  it.get("notas", "")))
        conn.commit()
        return True, "Compra de importación registrada.", compra_id
    except Exception as e:
        conn.rollback()
        return False, f"Error al registrar la compra: {e}", None
    finally:
        conn.close()


def editar_compra(compra_id: int, plataforma: str, referencia: str, courier_id: int | None,
                   casillero: str, tipo_envio: str, peso_caja_kg: float,
                   costo_envio_manual: float | None, estado: str, fecha_compra: str,
                   fecha_envio_casillero: str | None, fecha_recepcion: str | None,
                   notas: str, items: list[dict]) -> tuple[bool, str]:
    if not items:
        return False, "Agregá al menos un producto a la caja."
    for it in items:
        if not str(it.get("producto_nombre", "")).strip():
            return False, "Todos los productos necesitan un nombre."
        if float(it.get("cantidad") or 0) <= 0:
            return False, "La cantidad de cada producto debe ser mayor a cero."

    conn = conectar()
    cursor = conn.cursor()
    try:
        costo_envio_total = calcular_costo_envio(peso_caja_kg, courier_id, tipo_envio, costo_envio_manual)
        items_recalc = _recalcular_items(items, costo_envio_total)

        cursor.execute("""
            UPDATE import_compras SET plataforma=?, referencia=?, courier_id=?, casillero=?,
                   tipo_envio=?, peso_caja_kg=?, costo_envio_manual=?, costo_envio_total=?,
                   estado=?, fecha_compra=?, fecha_envio_casillero=?, fecha_recepcion=?, notas=?
            WHERE id=?
        """, (plataforma, referencia.strip(), courier_id, casillero, tipo_envio, peso_caja_kg,
              costo_envio_manual, costo_envio_total, estado, fecha_compra,
              fecha_envio_casillero or None, fecha_recepcion or None, notas.strip(), compra_id))

        # Reemplaza el detalle completo (más simple y seguro que hacer un
        # diff fila por fila); solo se bloquea si alguna unidad ya fue
        # enviada a inventario, para no perder esa trazabilidad.
        cursor.execute("SELECT COUNT(*) FROM import_detalle WHERE compra_id=? AND enviado_inventario=1",
                        (compra_id,))
        if cursor.fetchone()[0] > 0:
            conn.rollback()
            return False, ("No se puede modificar la lista de productos: algunos ya fueron enviados "
                            "a Inventario. Podés seguir editando fechas, courier y estado.")

        cursor.execute("DELETE FROM import_detalle WHERE compra_id=?", (compra_id,))
        for it in items_recalc:
            cursor.execute("""
                INSERT INTO import_detalle
                    (compra_id, producto_nombre, cantidad, costo_unitario_compra,
                     costo_envio_unitario, costo_total_unitario, precio_venta_publico, notas)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (compra_id, it["producto_nombre"].strip(), it["cantidad"], it["costo_unitario_compra"],
                  it["costo_envio_unitario"], it["costo_total_unitario"], it.get("precio_venta_publico"),
                  it.get("notas", "")))
        conn.commit()
        return True, "Compra actualizada."
    except Exception as e:
        conn.rollback()
        return False, f"Error al actualizar la compra: {e}"
    finally:
        conn.close()


def cambiar_estado_compra(compra_id: int, nuevo_estado: str, fecha: str | None = None) -> tuple[bool, str]:
    if nuevo_estado not in ESTADOS_COMPRA:
        return False, "Estado inválido."
    conn = conectar()
    cursor = conn.cursor()
    if nuevo_estado == "En camino al casillero" and fecha:
        cursor.execute("UPDATE import_compras SET estado=?, fecha_envio_casillero=? WHERE id=?",
                        (nuevo_estado, fecha, compra_id))
    elif nuevo_estado == "Recibido" and fecha:
        cursor.execute("UPDATE import_compras SET estado=?, fecha_recepcion=? WHERE id=?",
                        (nuevo_estado, fecha, compra_id))
    else:
        cursor.execute("UPDATE import_compras SET estado=? WHERE id=?", (nuevo_estado, compra_id))
    conn.commit()
    conn.close()
    return True, f"Estado actualizado a '{nuevo_estado}'."


def eliminar_compra(compra_id: int) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM import_detalle WHERE compra_id=? AND enviado_inventario=1",
                    (compra_id,))
    if cursor.fetchone()[0] > 0:
        conn.close()
        return False, "No se puede eliminar: tiene productos ya enviados a Inventario."
    cursor.execute("DELETE FROM import_compras WHERE id=?", (compra_id,))
    conn.commit()
    conn.close()
    return True, "Compra eliminada."


def set_precio_venta(item_id: int, precio_venta_publico: float | None) -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE import_detalle SET precio_venta_publico=? WHERE id=?",
                    (precio_venta_publico, item_id))
    conn.commit()
    conn.close()
    return True, "Precio de venta actualizado."


# ============================================================
# ENVIAR A INVENTARIO (deja el producto listo para venderse desde Ventas)
# ============================================================
def enviar_a_inventario(item_id: int, producto_existente_id: int | None = None,
                         categoria: str = "Importación") -> tuple[bool, str]:
    """Suma el stock de este ítem al inventario. Si se indica un producto
    ya existente, le actualiza el precio de compra/venta y le suma stock;
    si no, crea un producto nuevo. Deja constancia en movimientos_inventario,
    igual que hace el módulo Compras local."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT producto_nombre, cantidad, costo_total_unitario, precio_venta_publico, enviado_inventario
        FROM import_detalle WHERE id=?
    """, (item_id,))
    fila = cursor.fetchone()
    if not fila:
        conn.close()
        return False, "El producto de la importación no existe."
    nombre, cantidad, costo_unitario, precio_venta, ya_enviado = fila
    if ya_enviado:
        conn.close()
        return False, "Este producto ya fue enviado a Inventario anteriormente."

    try:
        if producto_existente_id:
            cursor.execute("SELECT stock, nombre FROM productos WHERE id=?", (producto_existente_id,))
            p = cursor.fetchone()
            if not p:
                raise ErrorDeImportacion("El producto elegido ya no existe.")
            stock_actual, nombre_producto = p
            nuevo_stock = (stock_actual or 0) + cantidad
            cursor.execute("""
                UPDATE productos SET stock=?, precio_compra=?, precio=COALESCE(?, precio)
                WHERE id=?
            """, (nuevo_stock, costo_unitario, precio_venta, producto_existente_id))
            producto_id = producto_existente_id
            stock_resultante = nuevo_stock
        else:
            cursor.execute("""
                INSERT INTO productos (nombre, categoria, precio, stock, precio_compra, tipo_producto, control_stock)
                VALUES (?, ?, ?, ?, ?, 'Producto', 'Cantidad')
            """, (nombre, categoria, precio_venta or 0, cantidad, costo_unitario))
            producto_id = cursor.lastrowid
            stock_resultante = cantidad

        cursor.execute("""
            INSERT INTO movimientos_inventario
                (producto_id, producto_nombre_historico, tipo, cantidad, motivo, stock_resultante)
            VALUES (?, ?, 'entrada', ?, ?, ?)
        """, (producto_id, nombre, cantidad, f"Importación #{item_id} - ítem recibido en casillero",
              stock_resultante))

        cursor.execute("""
            UPDATE import_detalle SET producto_id_generado=?, enviado_inventario=1 WHERE id=?
        """, (producto_id, item_id))

        conn.commit()
        return True, f"'{nombre}' enviado a Inventario ({cantidad} unidad(es))."
    except Exception as e:
        conn.rollback()
        return False, f"Error al enviar a inventario: {e}"
    finally:
        conn.close()


def buscar_productos_similares(texto: str) -> list[dict]:
    """Para el selector de 'producto ya existente' al enviar a inventario."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nombre, stock, precio, precio_compra FROM productos
        WHERE activo=1 AND nombre LIKE ? ORDER BY nombre LIMIT 30
    """, (f"%{texto.strip()}%",))
    filas = cursor.fetchall()
    conn.close()
    return [{"id": f[0], "nombre": f[1], "stock": f[2], "precio": f[3], "precio_compra": f[4]} for f in filas]


# ============================================================
# DASHBOARD
# ============================================================
def conteos_dashboard() -> dict:
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM import_compras")
    total_compras = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM import_compras WHERE estado != 'Recibido'")
    en_proceso = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(cantidad), 0) FROM import_detalle")
    total_unidades = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(cantidad * costo_unitario_compra), 0) FROM import_detalle
    """)
    total_costo_productos = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(costo_envio_total), 0) FROM import_compras")
    total_envios = cursor.fetchone()[0]

    inversion_total = round(total_costo_productos + total_envios, 2)

    cursor.execute("""
        SELECT COALESCE(SUM(cantidad * (precio_venta_publico - costo_total_unitario)), 0)
        FROM import_detalle WHERE precio_venta_publico IS NOT NULL
    """)
    ganancia_potencial = round(cursor.fetchone()[0], 2)

    cursor.execute("""
        SELECT COALESCE(SUM(cantidad * costo_total_unitario), 0) FROM import_detalle
        WHERE precio_venta_publico IS NOT NULL
    """)
    base_costo_con_precio = cursor.fetchone()[0]
    margen_promedio_pct = round((ganancia_potencial / base_costo_con_precio) * 100, 1) if base_costo_con_precio else None

    cursor.execute("""
        SELECT COALESCE(SUM(cantidad), 0) FROM import_detalle WHERE precio_venta_publico IS NULL
    """)
    unidades_sin_precio = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(cantidad), 0) FROM import_detalle WHERE enviado_inventario = 1
    """)
    unidades_en_inventario = cursor.fetchone()[0]

    conn.close()

    fechas = listar_compras()
    dias = [c["dias_transcurridos"] for c in fechas if c["estado"] == "Recibido" and c["dias_transcurridos"] is not None]
    tiempo_promedio = round(sum(dias) / len(dias), 1) if dias else None

    return {
        "total_compras": total_compras,
        "en_proceso": en_proceso,
        "total_unidades": total_unidades,
        "total_costo_productos": round(total_costo_productos, 2),
        "total_envios": round(total_envios, 2),
        "inversion_total": inversion_total,
        "ganancia_potencial": ganancia_potencial,
        "margen_promedio_pct": margen_promedio_pct,
        "unidades_sin_precio": unidades_sin_precio,
        "unidades_en_inventario": unidades_en_inventario,
        "tiempo_promedio_dias": tiempo_promedio,
    }


def rentabilidad_por_plataforma() -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.plataforma,
               COALESCE(SUM(d.cantidad * d.costo_total_unitario), 0) AS costo,
               COALESCE(SUM(CASE WHEN d.precio_venta_publico IS NOT NULL
                            THEN d.cantidad * d.precio_venta_publico ELSE 0 END), 0) AS ingreso_potencial,
               COALESCE(SUM(d.cantidad), 0) AS unidades
        FROM import_compras c
        LEFT JOIN import_detalle d ON d.compra_id = c.id
        GROUP BY c.plataforma
        HAVING unidades > 0
        ORDER BY costo DESC
    """)
    filas = cursor.fetchall()
    conn.close()
    resultado = []
    for f in filas:
        plataforma, costo, ingreso, unidades = f
        margen = round(ingreso - costo, 2)
        resultado.append({
            "plataforma": plataforma, "costo": round(costo, 2),
            "ingreso_potencial": round(ingreso, 2), "margen": margen, "unidades": unidades,
        })
    return resultado


def rentabilidad_por_producto() -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.producto_nombre, SUM(d.cantidad) AS unidades,
               SUM(d.cantidad * d.costo_total_unitario) AS costo_total,
               SUM(CASE WHEN d.precio_venta_publico IS NOT NULL
                        THEN d.cantidad * d.precio_venta_publico ELSE 0 END) AS ingreso_potencial,
               AVG(d.costo_total_unitario) AS costo_unit_prom,
               AVG(d.precio_venta_publico) AS precio_venta_prom
        FROM import_detalle d
        GROUP BY d.producto_nombre
        ORDER BY costo_total DESC
    """)
    filas = cursor.fetchall()
    conn.close()
    resultado = []
    for nombre, unidades, costo_total, ingreso, costo_prom, precio_prom in filas:
        ganancia = round((ingreso or 0) - (costo_total or 0), 2)
        resultado.append({
            "producto": nombre, "unidades": unidades, "costo_total": round(costo_total or 0, 2),
            "ingreso_potencial": round(ingreso or 0, 2), "ganancia": ganancia,
            "costo_unitario_promedio": round(costo_prom or 0, 2),
            "precio_venta_promedio": round(precio_prom or 0, 2) if precio_prom else None,
        })
    return resultado
