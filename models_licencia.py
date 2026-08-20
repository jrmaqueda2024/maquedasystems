"""
models_licencia.py
Sistema de licenciamiento por seriales de 16 dígitos con duraciones flexibles:
- Minutos / Horas / Días / Semanas / Meses / Años / Ilimitado (permanente).
- Los seriales se generan desde el sistema (admin/admin).
- Al activar un serial, se calcula la fecha de vencimiento.
- 'ilimitado' = licencia permanente (vencimiento simbólico en el año 9999).
- Al vencer, el sistema vuelve a pedir un nuevo serial.
"""
import secrets
import json
from datetime import datetime, timedelta
from database import conectar

# Caracteres usados para los seriales (sin O, 0, I, 1, L para evitar confusión)
ALFABETO_SERIAL = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"

# Credenciales fijas para acceder al generador de licencias
ADMIN_LIC_USUARIO = "admin"
ADMIN_LIC_PASSWORD = "admin"

# Fecha simbólica para licencias ilimitadas/permanentes
FECHA_PERMANENTE = "9999-12-31 23:59:59"

# Unidades disponibles (clave interna → etiquetas visibles)
UNIDADES = [
    ("minutos",   "Minutos",   "minuto",   "minutos"),
    ("horas",     "Horas",     "hora",     "horas"),
    ("dias",      "Días",      "día",      "días"),
    ("semanas",   "Semanas",   "semana",   "semanas"),
    ("meses",     "Meses",     "mes",      "meses"),
    ("anios",     "Años",      "año",      "años"),
    ("ilimitado", "Ilimitado / Permanente", "Ilimitado", "Ilimitado"),
]
UNIDADES_INFO = {u[0]: {"label": u[1], "singular": u[2], "plural": u[3]} for u in UNIDADES}
CLAVES_UNIDADES = [u[0] for u in UNIDADES]
ETIQUETAS_UNIDADES = [u[1] for u in UNIDADES]


# ---------------- HELPERS DE TIEMPO ----------------
def calcular_vencimiento(inicio: datetime, valor: int, unidad: str) -> datetime:
    """Devuelve la fecha de vencimiento dado un inicio + cantidad + unidad."""
    if unidad == "ilimitado":
        return datetime(9999, 12, 31, 23, 59, 59)
    if unidad == "minutos":
        return inicio + timedelta(minutes=valor)
    if unidad == "horas":
        return inicio + timedelta(hours=valor)
    if unidad == "dias":
        return inicio + timedelta(days=valor)
    if unidad == "semanas":
        return inicio + timedelta(weeks=valor)
    if unidad == "meses":
        return inicio + timedelta(days=valor * 30)
    if unidad == "anios":
        return inicio + timedelta(days=valor * 365)
    # default: meses
    return inicio + timedelta(days=valor * 30)


def describir_duracion(valor: int, unidad: str) -> str:
    """Texto humano: '30 minutos', '5 semanas', '2 horas', 'Ilimitado'."""
    if unidad == "ilimitado":
        return "Ilimitado"
    info = UNIDADES_INFO.get(unidad, UNIDADES_INFO["meses"])
    nombre = info["singular"] if valor == 1 else info["plural"]
    return f"{valor} {nombre}"


def etiqueta_a_clave(etiqueta: str) -> str:
    """Convierte la etiqueta visible (ej 'Días') a la clave interna (ej 'dias')."""
    for clave, label, *_ in UNIDADES:
        if label == etiqueta:
            return clave
    return "meses"


def clave_a_etiqueta(clave: str) -> str:
    """Devuelve la etiqueta visible (ej 'Días') a partir de la clave (ej 'dias')."""
    return UNIDADES_INFO.get(clave, UNIDADES_INFO["meses"])["label"]


# Componentes combinables (todo menos 'ilimitado', que es exclusivo y excluyente)
COMPONENTES_COMBINABLES = ["anios", "meses", "semanas", "dias", "horas", "minutos"]


def calcular_vencimiento_componentes(inicio: datetime, componentes: dict) -> datetime:
    """Igual que calcular_vencimiento(), pero suma varias unidades a la vez,
    ej: {"meses": 1, "dias": 15} = 1 mes y 15 días desde el inicio."""
    if componentes.get("ilimitado"):
        return datetime(9999, 12, 31, 23, 59, 59)
    resultado = inicio
    resultado += timedelta(days=(componentes.get("anios", 0) or 0) * 365)
    resultado += timedelta(days=(componentes.get("meses", 0) or 0) * 30)
    resultado += timedelta(weeks=componentes.get("semanas", 0) or 0)
    resultado += timedelta(days=componentes.get("dias", 0) or 0)
    resultado += timedelta(hours=componentes.get("horas", 0) or 0)
    resultado += timedelta(minutes=componentes.get("minutos", 0) or 0)
    return resultado


def describir_duracion_componentes(componentes: dict) -> str:
    """Texto humano de una duración combinada: '1 mes, 15 días' o
    '1 hora, 1 minuto'. Devuelve 'Ilimitado' si ese flag está presente."""
    if componentes.get("ilimitado"):
        return "Ilimitado"
    etiquetas = {
        "anios": ("año", "años"), "meses": ("mes", "meses"), "semanas": ("semana", "semanas"),
        "dias": ("día", "días"), "horas": ("hora", "horas"), "minutos": ("minuto", "minutos"),
    }
    partes = []
    for clave in ["anios", "meses", "semanas", "dias", "horas", "minutos"]:
        valor = componentes.get(clave, 0) or 0
        if valor > 0:
            singular, plural = etiquetas[clave]
            partes.append(f"{valor} {singular if valor == 1 else plural}")
    return ", ".join(partes) if partes else "0 minutos"


def componentes_tienen_duracion(componentes: dict) -> bool:
    """True si el dict de componentes representa algo más que un único
    valor en una sola unidad (es decir, realmente amerita guardarse como
    duración combinada en vez del par valor/unidad de siempre)."""
    if not componentes:
        return False
    if componentes.get("ilimitado"):
        return True
    cantidad_unidades_con_valor = sum(1 for c in COMPONENTES_COMBINABLES if (componentes.get(c, 0) or 0) > 0)
    return cantidad_unidades_con_valor >= 1


# ---------------- GENERACIÓN DE SERIALES ----------------
def generar_serial_aleatorio() -> str:
    """Genera un serial de 16 caracteres en formato XXXX-XXXX-XXXX-XXXX."""
    grupos = []
    for _ in range(4):
        grupo = "".join(secrets.choice(ALFABETO_SERIAL) for _ in range(4))
        grupos.append(grupo)
    return "-".join(grupos)


def normalizar_serial(serial: str) -> str:
    """Quita espacios y normaliza a mayúsculas con guiones cada 4 caracteres."""
    if not serial:
        return ""
    limpio = "".join(c for c in serial.upper() if c.isalnum())
    if len(limpio) != 16:
        return limpio
    return f"{limpio[0:4]}-{limpio[4:8]}-{limpio[8:12]}-{limpio[12:16]}"


def generar_y_guardar_serial(valor: int, unidad: str, componentes: dict | None = None) -> tuple[bool, str, str]:
    """Genera un serial único y lo guarda como disponible.
    Devuelve (ok, mensaje, serial_generado).

    Si 'componentes' viene con datos (ej {"meses": 1, "dias": 15}), esa
    duración combinada tiene prioridad. Si no, se usa el par valor/unidad
    de siempre (una sola unidad), para no romper compatibilidad."""
    if componentes and componentes_tienen_duracion(componentes):
        tipo_legible = describir_duracion_componentes(componentes)
        duracion_meses_compat = componentes.get("meses", 0) or 0
        valor_guardar = 0
        unidad_guardar = "ilimitado" if componentes.get("ilimitado") else "compuesto"
        componentes_json = json.dumps(componentes)
    else:
        if unidad not in UNIDADES_INFO:
            return False, "Unidad de tiempo inválida.", ""
        if unidad != "ilimitado":
            if valor <= 0:
                return False, "El valor debe ser mayor a 0.", ""
        else:
            valor = 0  # convencional para licencia permanente

        tipo_legible = describir_duracion(valor, unidad)
        duracion_meses_compat = valor if unidad == "meses" else (
            valor * 12 if unidad == "anios" else 0
        )
        valor_guardar = valor
        unidad_guardar = unidad
        componentes_json = ""

    conn = conectar()
    cursor = conn.cursor()
    for _ in range(20):
        serial = generar_serial_aleatorio()
        try:
            cursor.execute("""
                INSERT INTO licencias_generadas
                    (serial, tipo, duracion_meses, duracion_valor, duracion_unidad, duracion_componentes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (serial, tipo_legible, duracion_meses_compat, valor_guardar, unidad_guardar,
                  componentes_json))
            conn.commit()
            conn.close()
            return True, "Serial generado correctamente.", serial
        except Exception:
            continue
    conn.close()
    return False, "No se pudo generar un serial único, intentá de nuevo.", ""


def generar_seriales_en_lote(cantidad: int, valor: int, unidad: str,
                              componentes: dict | None = None) -> list[str]:
    """Genera 'cantidad' seriales con la misma duración."""
    generados = []
    for _ in range(max(1, int(cantidad))):
        ok, _, serial = generar_y_guardar_serial(valor, unidad, componentes=componentes)
        if ok:
            generados.append(serial)
    return generados


def listar_seriales_generados(limit: int = 200) -> list[dict]:
    """Lista los últimos seriales generados, ordenados por fecha desc."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, serial, tipo, duracion_meses, duracion_valor, duracion_unidad,
               fecha_generacion, usada, fecha_uso, duracion_componentes
        FROM licencias_generadas
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    filas = cursor.fetchall()
    conn.close()
    resultado = []
    for f in filas:
        valor = f[4] or f[3] or 0
        unidad = f[5] or "meses"
        componentes = json.loads(f[9]) if f[9] else None
        duracion_legible = (describir_duracion_componentes(componentes) if componentes
                            else describir_duracion(valor, unidad))
        resultado.append({
            "id": f[0],
            "serial": f[1],
            "tipo": f[2] or duracion_legible,
            "duracion_meses": f[3],
            "duracion_valor": valor,
            "duracion_unidad": unidad,
            "duracion_componentes": componentes,
            "duracion_legible": duracion_legible,
            "fecha_generacion": f[6],
            "usada": bool(f[7]),
            "fecha_uso": f[8],
        })
    return resultado


# ---------------- ACTIVACIÓN ----------------
def activar_licencia(serial: str) -> tuple[bool, str]:
    """Activa una licencia usando un serial generado previamente."""
    serial = normalizar_serial(serial)
    if len(serial.replace("-", "")) != 16:
        return False, "El serial debe tener 16 caracteres."

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, tipo, duracion_meses, duracion_valor, duracion_unidad, usada, duracion_componentes
        FROM licencias_generadas WHERE serial = ?
    """, (serial,))
    fila = cursor.fetchone()
    if fila is None:
        conn.close()
        return False, "Serial inválido. Verificá los caracteres ingresados."

    id_lic, tipo, duracion_meses, duracion_valor, duracion_unidad, usada, componentes_raw = fila
    if usada:
        conn.close()
        return False, "Este serial ya fue usado y no puede reutilizarse."

    componentes = json.loads(componentes_raw) if componentes_raw else None

    # Backwards-compat: si la fila viene de antes de la migración (y no es
    # una duración combinada), completar valores razonables.
    if componentes is None:
        if not duracion_unidad:
            duracion_unidad = "meses"
            duracion_valor = duracion_meses or 1
        if duracion_valor == 0 and duracion_unidad != "ilimitado":
            duracion_valor = duracion_meses or 1

    ahora = datetime.now()
    if componentes:
        vencimiento = calcular_vencimiento_componentes(ahora, componentes)
        duracion_legible = describir_duracion_componentes(componentes)
        es_ilimitada = bool(componentes.get("ilimitado"))
    else:
        vencimiento = calcular_vencimiento(ahora, duracion_valor, duracion_unidad)
        duracion_legible = describir_duracion(duracion_valor, duracion_unidad)
        es_ilimitada = (duracion_unidad == "ilimitado")
    fmt = "%Y-%m-%d %H:%M:%S"

    cursor.execute(
        "UPDATE licencias_generadas SET usada = 1, fecha_uso = ? WHERE id = ?",
        (ahora.strftime(fmt), id_lic),
    )

    cursor.execute("DELETE FROM licencia_activa WHERE id = 1")
    cursor.execute("""
        INSERT INTO licencia_activa
            (id, serial, tipo, duracion_meses, duracion_valor, duracion_unidad,
             duracion_componentes, fecha_activacion, fecha_vencimiento)
        VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (serial, tipo or duracion_legible,
          duracion_meses or 0, duracion_valor, duracion_unidad, componentes_raw or "",
          ahora.strftime(fmt), vencimiento.strftime(fmt)))
    conn.commit()
    conn.close()

    if es_ilimitada:
        return True, "Licencia activada: Ilimitada / Permanente."
    return True, f"Licencia activada. Vence el {vencimiento.strftime('%d/%m/%Y %H:%M')}."


def obtener_licencia_activa() -> dict | None:
    """Devuelve la licencia activa actual o None si no hay ninguna."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT serial, tipo, duracion_meses, duracion_valor, duracion_unidad,
               fecha_activacion, fecha_vencimiento, duracion_componentes
        FROM licencia_activa WHERE id = 1
    """)
    fila = cursor.fetchone()
    conn.close()
    if not fila:
        return None
    valor = fila[3] or fila[2] or 0
    unidad = fila[4] or "meses"
    componentes = json.loads(fila[7]) if fila[7] else None
    duracion_legible = (describir_duracion_componentes(componentes) if componentes
                        else describir_duracion(valor, unidad))
    return {
        "serial": fila[0],
        "tipo": fila[1] or duracion_legible,
        "duracion_meses": fila[2],
        "duracion_valor": valor,
        "duracion_unidad": unidad,
        "duracion_componentes": componentes,
        "duracion_legible": duracion_legible,
        "fecha_activacion": fila[5],
        "fecha_vencimiento": fila[6],
    }


def licencia_vigente() -> bool:
    """True si la licencia activa no venció todavía (o es ilimitada)."""
    lic = obtener_licencia_activa()
    if not lic:
        return False
    if lic["duracion_unidad"] == "ilimitado":
        return True
    try:
        venc = datetime.strptime(lic["fecha_vencimiento"], "%Y-%m-%d %H:%M:%S")
    except (ValueError, KeyError):
        return False
    return datetime.now() < venc


def es_ilimitada() -> bool:
    """True si la licencia activa es ilimitada/permanente."""
    lic = obtener_licencia_activa()
    return bool(lic and lic["duracion_unidad"] == "ilimitado")


def dias_restantes() -> int:
    """Cuántos días le quedan a la licencia activa (-1 si ilimitada, 0 si vencida)."""
    lic = obtener_licencia_activa()
    if not lic:
        return 0
    if lic["duracion_unidad"] == "ilimitado":
        return -1
    try:
        venc = datetime.strptime(lic["fecha_vencimiento"], "%Y-%m-%d %H:%M:%S")
    except (ValueError, KeyError):
        return 0
    delta = venc - datetime.now()
    return max(0, delta.days)


def tiempo_restante_legible() -> str:
    """Tiempo restante en formato legible: '5 días 3h', '45m 12s', 'Permanente'."""
    lic = obtener_licencia_activa()
    if not lic:
        return "Sin licencia"
    if lic["duracion_unidad"] == "ilimitado":
        return "Permanente ∞"
    try:
        venc = datetime.strptime(lic["fecha_vencimiento"], "%Y-%m-%d %H:%M:%S")
    except (ValueError, KeyError):
        return "Vencida"
    delta = venc - datetime.now()
    total = int(delta.total_seconds())
    if total <= 0:
        return "Vencida"
    d, total = divmod(total, 86400)
    h, total = divmod(total, 3600)
    m, s = divmod(total, 60)
    if d > 0:
        return f"{d} día{'s' if d != 1 else ''} {h}h"
    if h > 0:
        return f"{h}h {m}m"
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"


def descripcion_licencia() -> str:
    """Texto corto para mostrar en la barra superior."""
    lic = obtener_licencia_activa()
    if not lic:
        return "Sin licencia"
    componentes = lic.get("duracion_componentes")
    es_ilimitada = (lic["duracion_unidad"] == "ilimitado") or bool(componentes and componentes.get("ilimitado"))
    if es_ilimitada:
        return "Licencia Permanente / Ilimitada ∞"
    try:
        venc = datetime.strptime(lic["fecha_vencimiento"], "%Y-%m-%d %H:%M:%S")
    except (ValueError, KeyError):
        return "Licencia inválida"
    restante = tiempo_restante_legible()
    # Para licencias cortas (minutos/horas), mostrar hora exacta de vencimiento
    if componentes:
        es_corta = bool((componentes.get("minutos", 0) or 0) or (componentes.get("horas", 0) or 0))
    else:
        es_corta = lic["duracion_unidad"] in ("minutos", "horas")
    if es_corta:
        venc_fmt = venc.strftime("%d/%m/%Y %H:%M")
    else:
        venc_fmt = venc.strftime("%d/%m/%Y")
    return f"Licencia {lic['duracion_legible']} — vence {venc_fmt} ({restante})"


def verificar_credenciales_admin(usuario: str, password: str) -> bool:
    """Verifica las credenciales fijas para acceder al generador."""
    return (usuario or "").strip().lower() == ADMIN_LIC_USUARIO and \
           (password or "") == ADMIN_LIC_PASSWORD


def eliminar_serial(serial_id: int) -> tuple[bool, str, bool]:
    """Elimina un serial del catálogo. Si el serial estaba activo en el
    sistema (licencia_activa), también lo desvincula.

    Devuelve (ok, mensaje, era_la_licencia_activa).
    """
    conn = conectar()
    cursor = conn.cursor()

    # Obtener el serial que se está borrando
    cursor.execute("SELECT serial FROM licencias_generadas WHERE id = ?", (serial_id,))
    fila = cursor.fetchone()
    if not fila:
        conn.close()
        return False, "El serial no existe.", False
    serial_borrar = fila[0]

    # ¿Es el serial actualmente activo?
    cursor.execute("SELECT serial FROM licencia_activa WHERE id = 1")
    activa = cursor.fetchone()
    era_activa = bool(activa and activa[0] == serial_borrar)

    try:
        cursor.execute("DELETE FROM licencias_generadas WHERE id = ?", (serial_id,))
        if era_activa:
            cursor.execute("DELETE FROM licencia_activa WHERE id = 1")
        conn.commit()
        if era_activa:
            return True, "Serial eliminado y licencia desvinculada del sistema.", True
        return True, "Serial eliminado.", False
    except Exception as e:
        return False, f"Error al eliminar: {e}", False
    finally:
        conn.close()


def eliminar_seriales(ids: list[int]) -> tuple[int, bool]:
    """Elimina varios seriales por ID. Devuelve (cantidad_eliminada, alguna_era_activa)."""
    eliminados = 0
    alguna_activa = False
    for sid in ids:
        ok, _, era_activa = eliminar_serial(sid)
        if ok:
            eliminados += 1
            if era_activa:
                alguna_activa = True
    return eliminados, alguna_activa
