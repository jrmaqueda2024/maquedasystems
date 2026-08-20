"""
models_prestamos.py
Lógica de negocio del módulo Préstamos (financiera): un "Banco Central"
interno con el dinero disponible para prestar, los préstamos otorgados a
clientes (con su cronograma de cuotas calculado según el sistema de
amortización elegido), el registro de pagos, y el interés moratorio que
se genera día a día sobre las cuotas vencidas e impagas.

Sistemas de amortización disponibles (los que se usan en Paraguay):
  - Francés  : cuota fija; el interés se calcula sobre el saldo y va
               bajando, la porción de capital va subiendo. Es el más
               usado por bancos y financieras para préstamos personales.
  - Alemán   : capital fijo en cada cuota; el interés baja junto con el
               saldo, por lo que la cuota total es decreciente.
  - Americano: solo se pagan intereses sobre el capital original en cada
               cuota, y el capital completo se devuelve en la última
               cuota ("pago bullet"). Se usa en préstamos puente y
               algunos créditos agropecuarios/comerciales (ej. a cosecha).
  - Directo / Flat: el interés total se calcula una sola vez sobre el
               capital original (capital × tasa × cantidad de cuotas) y
               se reparte en partes iguales entre todas las cuotas, junto
               con el capital también en partes iguales. Es el método
               que más usan las financieras y casas de crédito paraguayas
               para microcréditos ("a sola firma"), porque dando cuotas
               fijas de igual manera que el francés, es más simple de
               calcular y deja un costo financiero más alto para la
               financiera con la misma tasa nominal.

El interés moratorio (art. 44 de la Ley 2339 y normativa del BCP) se
calcula sobre el saldo de la deuda vencida, sin capitalizarse sobre sí
mismo, y no se recalcula por lotes: se obtiene siempre "al vuelo" en
base a la fecha de hoy, así que nunca queda desactualizado aunque el
sistema haya estado cerrado varios días.
"""
import calendar
import datetime
from database import conectar

SISTEMAS_AMORTIZACION = [
    ("frances",   "Sistema Francés (cuota fija)"),
    ("aleman",    "Sistema Alemán (capital fijo)"),
    ("americano", "Sistema Americano (pago único al final)"),
    ("directo",   "Sistema Directo / Flat (interés fijo)"),
]
NOMBRES_SISTEMA = dict(SISTEMAS_AMORTIZACION)

FRECUENCIAS = [
    ("diaria",    "Diaria"),
    ("semanal",   "Semanal"),
    ("quincenal", "Quincenal"),
    ("mensual",   "Mensual"),
]
NOMBRES_FRECUENCIA = dict(FRECUENCIAS)


class ErrorDePrestamo(Exception):
    pass


# ============================================================
# UTILIDADES DE FECHA
# ============================================================
def _sumar_meses(fecha: datetime.date, n: int) -> datetime.date:
    mes_total = fecha.month - 1 + n
    anio = fecha.year + mes_total // 12
    mes = mes_total % 12 + 1
    dia = min(fecha.day, calendar.monthrange(anio, mes)[1])
    return datetime.date(anio, mes, dia)


def _sumar_periodo(fecha: datetime.date, frecuencia: str, veces: int = 1) -> datetime.date:
    if frecuencia == "diaria":
        return fecha + datetime.timedelta(days=1 * veces)
    if frecuencia == "semanal":
        return fecha + datetime.timedelta(days=7 * veces)
    if frecuencia == "quincenal":
        return fecha + datetime.timedelta(days=15 * veces)
    return _sumar_meses(fecha, veces)  # mensual


def generar_fechas_cuotas(fecha_inicio: datetime.date, frecuencia: str, cantidad: int) -> list:
    return [_sumar_periodo(fecha_inicio, frecuencia, k) for k in range(1, cantidad + 1)]


# ============================================================
# CÁLCULO DE CRONOGRAMA (sin fechas todavía, solo montos)
# ============================================================
def calcular_cronograma(capital: float, tasa_pct: float, cantidad_cuotas: int,
                        sistema: str) -> list:
    """Devuelve una lista de {nro, capital, interes, cuota} ya redondeada
    a guaraníes enteros, con el ajuste de redondeo aplicado en la última
    cuota para que la suma de capital cierre exacto."""
    n = cantidad_cuotas
    i = (tasa_pct or 0) / 100

    filas_exactas = []  # valores sin redondear, para no arrastrar error
    saldo = float(capital)

    if sistema == "frances":
        cuota_fija = (capital * i / (1 - (1 + i) ** -n)) if i > 0 else (capital / n)
        for k in range(1, n + 1):
            interes_k = saldo * i
            capital_k = cuota_fija - interes_k
            if k == n:
                capital_k = saldo  # la última cuota cierra el saldo exacto
            saldo -= capital_k
            filas_exactas.append((capital_k, interes_k))

    elif sistema == "aleman":
        capital_k = capital / n
        for k in range(1, n + 1):
            interes_k = saldo * i
            cap = capital_k if k < n else saldo
            saldo -= cap
            filas_exactas.append((cap, interes_k))

    elif sistema == "americano":
        for k in range(1, n + 1):
            interes_k = capital * i
            cap = 0.0 if k < n else capital
            filas_exactas.append((cap, interes_k))

    elif sistema == "directo":
        interes_total = capital * i * n
        capital_k = capital / n
        interes_k = interes_total / n
        for k in range(1, n):
            filas_exactas.append((capital_k, interes_k))
        capital_acumulado = capital_k * (n - 1)
        filas_exactas.append((capital - capital_acumulado, interes_k))

    else:
        raise ErrorDePrestamo(f"Sistema de amortización desconocido: {sistema}")

    resultado = []
    suma_capital_redondeado = 0
    for idx, (cap, interes) in enumerate(filas_exactas, start=1):
        cap_r = round(cap)
        interes_r = round(interes)
        if idx == len(filas_exactas):
            cap_r = round(capital) - suma_capital_redondeado
        suma_capital_redondeado += cap_r
        resultado.append({
            "nro": idx, "capital": cap_r, "interes": max(interes_r, 0),
            "cuota": cap_r + max(interes_r, 0),
        })
    return resultado


# ============================================================
# FONDO CENTRAL (Banco)
# ============================================================
def saldo_fondo() -> float:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(CASE WHEN tipo IN ('carga', 'cobro') THEN monto
                                  WHEN tipo IN ('desembolso') THEN -monto
                                  ELSE monto END), 0)
        FROM fondo_prestamos_movimientos
    """)
    saldo = cursor.fetchone()[0] or 0
    conn.close()
    return saldo


def _registrar_movimiento_fondo(conn, tipo: str, monto: float, descripcion: str,
                                 prestamo_id, usuario_id) -> float:
    """Inserta un movimiento y devuelve el saldo resultante. Recibe una
    conexión ya abierta para que quede dentro de la misma transacción que
    el resto de la operación (ej. crear el préstamo y descontar el fondo
    son atómicos: si algo falla, no queda ninguno de los dos aplicado)."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(CASE WHEN tipo IN ('carga', 'cobro') THEN monto
                                  WHEN tipo IN ('desembolso') THEN -monto
                                  ELSE monto END), 0)
        FROM fondo_prestamos_movimientos
    """)
    saldo_previo = cursor.fetchone()[0] or 0
    saldo_nuevo = saldo_previo + monto if tipo in ("carga", "cobro") else saldo_previo - monto
    cursor.execute("""
        INSERT INTO fondo_prestamos_movimientos
            (tipo, monto, descripcion, prestamo_id, usuario_id, saldo_resultante)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (tipo, monto, descripcion, prestamo_id, usuario_id, saldo_nuevo))
    return saldo_nuevo


def cargar_fondo(monto: float, descripcion: str, usuario_id=None):
    """Ingresa capital nuevo al Banco Central de préstamos (ej. cuando el
    dueño del negocio deposita más dinero para poder prestar a más
    clientes)."""
    if monto is None or monto <= 0:
        return False, "El monto a cargar debe ser mayor a cero."
    conn = conectar()
    try:
        saldo_nuevo = _registrar_movimiento_fondo(
            conn, "carga", monto, descripcion or "Carga de fondos", None, usuario_id)
        conn.commit()
        return True, (f"Se cargaron Gs. {monto:,.0f} al fondo. "
                       f"Saldo disponible: Gs. {saldo_nuevo:,.0f}.").replace(",", ".")
    except Exception as e:
        conn.rollback()
        return False, f"Error al cargar el fondo: {e}"
    finally:
        conn.close()


def listar_movimientos_fondo(texto_busqueda: str = "") -> list:
    conn = conectar()
    cursor = conn.cursor()
    condiciones = []
    parametros: list = []
    if texto_busqueda.strip():
        condiciones.append("(COALESCE(m.descripcion,'') LIKE ? OR COALESCE(cl.nombre,'') LIKE ?)")
        q = f"%{texto_busqueda.strip()}%"
        parametros += [q, q]
    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
    cursor.execute(f"""
        SELECT m.id, m.fecha, m.tipo, m.monto, m.descripcion, m.prestamo_id,
               m.saldo_resultante, u.nombre_completo, cl.nombre
        FROM fondo_prestamos_movimientos m
        LEFT JOIN usuarios u ON m.usuario_id = u.id
        LEFT JOIN prestamos p ON m.prestamo_id = p.id
        LEFT JOIN clientes cl ON p.cliente_id = cl.id
        {where}
        ORDER BY m.id DESC
    """, parametros)
    filas = cursor.fetchall()
    conn.close()
    return [{
        "id": f[0], "fecha": f[1], "tipo": f[2], "monto": f[3],
        "descripcion": f[4] or "", "prestamo_id": f[5],
        "saldo_resultante": f[6] or 0, "usuario": f[7] or "",
        "cliente": f[8] or "",
    } for f in filas]


# ============================================================
# CUOTAS: cálculo dinámico de mora y estado (siempre "al vuelo")
# ============================================================
def _calcular_estado_cuota(cuota_fila: dict, hoy: datetime.date, tasa_mora_diaria: float) -> dict:
    capital, interes = cuota_fila["capital"], cuota_fila["interes"]
    pagado_capital = cuota_fila["pagado_capital"]
    pagado_interes = cuota_fila["pagado_interes"]
    pagado_mora = cuota_fila["pagado_mora"]

    saldo_capital_interes = round(capital + interes - pagado_capital - pagado_interes, 2)
    if saldo_capital_interes < 0:
        saldo_capital_interes = 0.0

    fecha_venc = datetime.date.fromisoformat(cuota_fila["fecha_vencimiento"][:10])
    dias_atraso = max(0, (hoy - fecha_venc).days) if saldo_capital_interes > 1 else 0

    mora_generada = saldo_capital_interes * (tasa_mora_diaria / 100) * dias_atraso
    mora_pendiente = max(0.0, round(mora_generada - pagado_mora, 2))

    if saldo_capital_interes <= 1:
        estado = "Pagada"
    elif dias_atraso > 0:
        estado = "Vencida"
    else:
        estado = "Pendiente"

    resultado = dict(cuota_fila)
    resultado.update({
        "fecha_venc": fecha_venc,
        "dias_atraso": dias_atraso,
        "saldo_capital_interes": saldo_capital_interes,
        "mora_pendiente": mora_pendiente,
        "total_a_pagar": round(saldo_capital_interes + mora_pendiente, 2),
        "estado": estado,
    })
    return resultado


def _obtener_cuotas_crudas(conn, prestamo_id: int) -> list:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nro_cuota, fecha_vencimiento, capital, interes,
               pagado_capital, pagado_interes, pagado_mora, fecha_pago_completo
        FROM cuotas_prestamo WHERE prestamo_id = ? ORDER BY nro_cuota
    """, (prestamo_id,))
    return [{
        "id": f[0], "nro_cuota": f[1], "fecha_vencimiento": f[2],
        "capital": f[3], "interes": f[4], "pagado_capital": f[5],
        "pagado_interes": f[6], "pagado_mora": f[7], "fecha_pago_completo": f[8],
    } for f in cursor.fetchall()]


# ============================================================
# PRÉSTAMOS
# ============================================================
def crear_prestamo(cliente_id, capital, tasa_interes, frecuencia, cantidad_cuotas,
                    sistema, tasa_mora_diaria, fecha_desembolso,
                    observaciones="", usuario_id=None):
    if not cliente_id:
        return False, "Selecciona un cliente para el préstamo.", None
    if capital is None or capital <= 0:
        return False, "El capital a prestar debe ser mayor a cero.", None
    if cantidad_cuotas is None or cantidad_cuotas <= 0:
        return False, "La cantidad de cuotas debe ser mayor a cero.", None
    if sistema not in NOMBRES_SISTEMA:
        return False, "Sistema de amortización inválido.", None
    if frecuencia not in NOMBRES_FRECUENCIA:
        return False, "Frecuencia de pago inválida.", None

    saldo_disponible = saldo_fondo()
    if capital > saldo_disponible + 1:
        return False, (f"Fondo insuficiente. Disponible: Gs. {saldo_disponible:,.0f}, "
                        f"se necesita Gs. {capital:,.0f}. Carga más fondos primero."
                        ).replace(",", "."), None

    cronograma = calcular_cronograma(capital, tasa_interes, cantidad_cuotas, sistema)
    fechas = generar_fechas_cuotas(fecha_desembolso, frecuencia, cantidad_cuotas)

    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO prestamos (cliente_id, fecha_desembolso, capital, tasa_interes,
                                    frecuencia, cantidad_cuotas, sistema, tasa_mora_diaria,
                                    observaciones, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cliente_id, fecha_desembolso.isoformat(), capital, tasa_interes,
              frecuencia, cantidad_cuotas, sistema, tasa_mora_diaria,
              observaciones, usuario_id))
        prestamo_id = cursor.lastrowid

        for fila, fecha_venc in zip(cronograma, fechas):
            cursor.execute("""
                INSERT INTO cuotas_prestamo (prestamo_id, nro_cuota, fecha_vencimiento,
                                              capital, interes)
                VALUES (?, ?, ?, ?, ?)
            """, (prestamo_id, fila["nro"], fecha_venc.isoformat(), fila["capital"], fila["interes"]))

        _registrar_movimiento_fondo(
            conn, "desembolso", capital,
            f"Desembolso de préstamo Nro. {prestamo_id}", prestamo_id, usuario_id)

        conn.commit()
        return True, (f"Préstamo Nro. {prestamo_id} desembolsado por "
                       f"Gs. {capital:,.0f}.").replace(",", "."), prestamo_id
    except Exception as e:
        conn.rollback()
        return False, f"Error al crear el préstamo: {e}", None
    finally:
        conn.close()


def listar_prestamos(vista: str = "activos", texto_busqueda: str = "") -> list:
    """vista: 'activos', 'pagados' o 'todos'."""
    conn = conectar()
    cursor = conn.cursor()
    condiciones = []
    parametros: list = []
    if vista == "activos":
        condiciones.append("p.estado = 'activo'")
    elif vista == "pagados":
        condiciones.append("p.estado = 'pagado'")
    if texto_busqueda.strip():
        condiciones.append("(cl.nombre LIKE ? OR CAST(p.id AS TEXT) LIKE ?)")
        q = f"%{texto_busqueda.strip()}%"
        parametros += [q, q]
    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    cursor.execute(f"""
        SELECT p.id, p.cliente_id, cl.nombre, p.fecha_desembolso, p.capital,
               p.tasa_interes, p.frecuencia, p.cantidad_cuotas, p.sistema,
               p.tasa_mora_diaria, p.estado
        FROM prestamos p
        LEFT JOIN clientes cl ON p.cliente_id = cl.id
        {where}
        ORDER BY p.id DESC
    """, parametros)
    filas = cursor.fetchall()

    hoy = datetime.date.today()
    resultado = []
    for f in filas:
        prestamo_id, tasa_mora = f[0], f[9]
        cuotas_crudas = _obtener_cuotas_crudas(conn, prestamo_id)
        cuotas = [_calcular_estado_cuota(c, hoy, tasa_mora) for c in cuotas_crudas]
        saldo_total = sum(c["total_a_pagar"] for c in cuotas)
        cuotas_pagadas = sum(1 for c in cuotas if c["estado"] == "Pagada")
        vencidas = [c for c in cuotas if c["estado"] == "Vencida"]
        proxima = next((c for c in cuotas if c["estado"] != "Pagada"), None)

        if f[10] == "cancelado":
            estado_calc = "Cancelado"
        elif saldo_total <= 1:
            estado_calc = "Pagado"
        elif vencidas:
            estado_calc = "Vencido"
        else:
            estado_calc = "Al día"

        resultado.append({
            "id": prestamo_id, "cliente_id": f[1], "cliente": f[2] or "Sin cliente",
            "fecha_desembolso": f[3], "capital": f[4], "tasa_interes": f[5],
            "frecuencia": f[6], "cantidad_cuotas": f[7], "sistema": f[8],
            "tasa_mora_diaria": tasa_mora, "estado": f[10],
            "saldo_total": round(saldo_total, 2), "cuotas_pagadas": cuotas_pagadas,
            "dias_atraso_max": max((c["dias_atraso"] for c in vencidas), default=0),
            "proxima_fecha_vencimiento": proxima["fecha_vencimiento"] if proxima else None,
            "estado_calculado": estado_calc,
        })
    conn.close()
    return resultado


def obtener_detalle_prestamo(prestamo_id: int):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.cliente_id, cl.nombre, cl.nro_documento, cl.telefono,
               p.fecha_desembolso, p.capital, p.tasa_interes, p.frecuencia,
               p.cantidad_cuotas, p.sistema, p.tasa_mora_diaria, p.estado,
               p.observaciones
        FROM prestamos p
        LEFT JOIN clientes cl ON p.cliente_id = cl.id
        WHERE p.id = ?
    """, (prestamo_id,))
    f = cursor.fetchone()
    if f is None:
        conn.close()
        return None

    hoy = datetime.date.today()
    cuotas_crudas = _obtener_cuotas_crudas(conn, prestamo_id)
    cuotas = [_calcular_estado_cuota(c, hoy, f[11]) for c in cuotas_crudas]

    cursor.execute("""
        SELECT fecha, monto_capital, monto_interes, monto_mora, monto_total
        FROM pagos_prestamo WHERE prestamo_id = ? ORDER BY id DESC
    """, (prestamo_id,))
    pagos = [{"fecha": p[0], "capital": p[1], "interes": p[2], "mora": p[3], "total": p[4]}
              for p in cursor.fetchall()]
    conn.close()

    saldo_total = round(sum(c["total_a_pagar"] for c in cuotas), 2)
    return {
        "id": f[0], "cliente_id": f[1], "cliente": f[2] or "Sin cliente",
        "nro_documento": f[3] or "", "telefono": f[4] or "",
        "fecha_desembolso": f[5], "capital": f[6], "tasa_interes": f[7],
        "frecuencia": f[8], "cantidad_cuotas": f[9], "sistema": f[10],
        "tasa_mora_diaria": f[11], "estado": f[12], "observaciones": f[13] or "",
        "cuotas": cuotas, "pagos": pagos, "saldo_total": saldo_total,
    }


def registrar_pago_cuota(cuota_id: int, monto: float, usuario_id=None):
    """Aplica un pago a una cuota siguiendo el orden habitual de cobranza:
    primero la mora (penalidad por atraso), después el interés, y por
    último el capital. Si el monto pagado alcanza a cubrir toda la cuota,
    la marca como pagada; y si con esto TODAS las cuotas del préstamo ya
    están saldadas, el préstamo completo pasa a estado 'pagado'. El monto
    cobrado vuelve a sumarse al Banco Central."""
    if monto is None or monto <= 0:
        return False, "El monto a pagar debe ser mayor a cero."

    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT prestamo_id, nro_cuota, fecha_vencimiento, capital, interes,
                   pagado_capital, pagado_interes, pagado_mora
            FROM cuotas_prestamo WHERE id = ?
        """, (cuota_id,))
        fila = cursor.fetchone()
        if fila is None:
            conn.close()
            return False, "La cuota no existe."
        (prestamo_id, nro_cuota, fecha_venc, capital, interes,
         pagado_capital, pagado_interes, pagado_mora) = fila

        cursor.execute("SELECT tasa_mora_diaria FROM prestamos WHERE id = ?", (prestamo_id,))
        tasa_mora = cursor.fetchone()[0] or 0

        cuota_calc = _calcular_estado_cuota({
            "capital": capital, "interes": interes, "pagado_capital": pagado_capital,
            "pagado_interes": pagado_interes, "pagado_mora": pagado_mora,
            "fecha_vencimiento": fecha_venc,
        }, datetime.date.today(), tasa_mora)

        total_pendiente = cuota_calc["total_a_pagar"]
        if monto > total_pendiente + 1:
            conn.close()
            return False, (f"El monto supera lo pendiente de esta cuota "
                            f"(Gs. {total_pendiente:,.0f}).").replace(",", ".")

        restante = monto
        pago_mora = min(restante, cuota_calc["mora_pendiente"])
        restante -= pago_mora

        interes_pendiente = max(0.0, interes - pagado_interes)
        pago_interes = min(restante, interes_pendiente)
        restante -= pago_interes

        capital_pendiente = max(0.0, capital - pagado_capital)
        pago_capital = min(restante, capital_pendiente)
        restante -= pago_capital

        nuevo_pagado_capital = pagado_capital + pago_capital
        nuevo_pagado_interes = pagado_interes + pago_interes
        nuevo_pagado_mora = pagado_mora + pago_mora

        cuota_saldada = (capital + interes - nuevo_pagado_capital - nuevo_pagado_interes) <= 1
        fecha_pago_completo = datetime.date.today().isoformat() if cuota_saldada else None

        cursor.execute("""
            UPDATE cuotas_prestamo
            SET pagado_capital = ?, pagado_interes = ?, pagado_mora = ?,
                fecha_pago_completo = COALESCE(fecha_pago_completo, ?)
            WHERE id = ?
        """, (nuevo_pagado_capital, nuevo_pagado_interes, nuevo_pagado_mora,
              fecha_pago_completo, cuota_id))

        cursor.execute("""
            INSERT INTO pagos_prestamo
                (prestamo_id, cuota_id, monto_capital, monto_interes, monto_mora, monto_total, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (prestamo_id, cuota_id, pago_capital, pago_interes, pago_mora, monto, usuario_id))

        _registrar_movimiento_fondo(
            conn, "cobro", monto,
            f"Cobro cuota Nro. {nro_cuota} del préstamo Nro. {prestamo_id}",
            prestamo_id, usuario_id)

        cuotas_crudas = _obtener_cuotas_crudas(conn, prestamo_id)
        for c in cuotas_crudas:
            if c["id"] == cuota_id:
                c["pagado_capital"] = nuevo_pagado_capital
                c["pagado_interes"] = nuevo_pagado_interes
        todas_saldadas = all(
            (c["capital"] + c["interes"] - c["pagado_capital"] - c["pagado_interes"]) <= 1
            for c in cuotas_crudas
        )
        if todas_saldadas:
            cursor.execute("UPDATE prestamos SET estado = 'pagado' WHERE id = ?", (prestamo_id,))

        conn.commit()
        mensaje = f"Pago de Gs. {monto:,.0f} registrado.".replace(",", ".")
        if todas_saldadas:
            mensaje += f" El préstamo Nro. {prestamo_id} quedó totalmente saldado."
        elif cuota_saldada:
            mensaje += f" La cuota Nro. {nro_cuota} quedó saldada."
        return True, mensaje
    except Exception as e:
        conn.rollback()
        return False, f"Error al registrar el pago: {e}"
    finally:
        conn.close()


def resumen_financiero() -> dict:
    saldo = saldo_fondo()
    prestamos_activos = listar_prestamos(vista="activos")
    total_prestado_activo = sum(p["capital"] for p in prestamos_activos)
    total_por_cobrar = sum(p["saldo_total"] for p in prestamos_activos)
    cartera_vencida = sum(p["saldo_total"] for p in prestamos_activos if p["estado_calculado"] == "Vencido")
    return {
        "saldo_fondo": saldo, "cantidad_prestamos_activos": len(prestamos_activos),
        "total_prestado_activo": total_prestado_activo,
        "total_por_cobrar": total_por_cobrar, "cartera_vencida": cartera_vencida,
    }
