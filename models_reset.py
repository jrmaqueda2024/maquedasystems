"""
models_reset.py
Lógica de "Reinicio del Sistema": borra de forma persistente los datos
operativos del negocio (ventas, productos, clientes, inventario, caja,
créditos, compras, devoluciones, facturas, presupuestos, préstamos,
asistencia técnica, veterinaria, restaurante/comedor, alquiler de
streaming e importaciones) y libera el espacio ocupado en la base de datos para que el
sistema lo reutilice, como si arrancara desde cero.

Dos modalidades:
  - reiniciar_datos_de_negocio(): borra todo lo operativo de TODOS los
    módulos de negocio, PERO conserva los usuarios y la licencia activa,
    para no perder el acceso al sistema ni tener que reactivar la
    licencia.
  - reinicio_total_de_fabrica(): borra absolutamente todo, incluyendo
    usuarios, dejando el sistema exactamente como recién instalado (la
    próxima vez que arranque, pedirá crear el primer administrador). La
    licencia activa SÍ se conserva, porque depende de un serial externo
    y no tiene sentido forzar una reactivación.

IMPORTANTE — mantenimiento: cada vez que se agregue un módulo nuevo con
tablas propias, hay que sumarlas a una de las tres listas de abajo
(_TABLAS_DATOS_NEGOCIO, _TABLAS_SOLO_RESET_TOTAL o _TABLAS_PROTEGIDAS).
Si no se hace, el reinicio del sistema NO va a borrar esos datos aunque
diga que "reinició todo" — que es justo el bug que tenían las tablas de
Préstamos, Presupuestos, Asistencia Técnica, Veterinaria, Restaurante y
Streaming antes de esta corrección, y que también tenían (más adelante)
"config_local" y "numeracion_comprobante" del módulo de comprobantes,
ya clasificadas. La función tablas_sin_categoria(), al final de este
archivo, detecta automáticamente si vuelve a pasar.

Después de cada borrado se ejecuta VACUUM, que reconstruye físicamente
el archivo .db, recupera el espacio en disco de las filas eliminadas y
reinicia los contadores AUTOINCREMENT, para que los próximos registros
vuelvan a empezar desde el ID 1.
"""
from database import conectar, obtener_ruta_bd

# Tablas operativas del negocio: se vacían en AMBAS modalidades de reset.
_TABLAS_DATOS_NEGOCIO = [
    # Ventas / Créditos / Compras / Inventario / Caja (núcleo original)
    "devoluciones",
    "pagos_credito",
    "creditos",
    "facturas",
    "detalle_ventas",
    "ventas",
    "detalle_compras",
    "compras",
    "movimientos_inventario",
    "caja_movimientos",
    "productos",
    "categorias",
    "marcas",
    "proveedores",
    "clientes",
    "zonas",
    "cobradores",
    # Presupuestos
    "detalle_presupuestos",
    "presupuestos",
    # Préstamos (fondo, cuotas, pagos y los préstamos en sí)
    "pagos_prestamo",
    "cuotas_prestamo",
    "prestamos",
    "fondo_prestamos_movimientos",
    # Asistencia Técnica
    "casos_tecnicos",
    "equipos_registrados",
    "tipos_equipo",
    # Veterinaria
    "vacunas_mascota",
    "tratamientos_mascota",
    "consultas_veterinarias",
    "mascotas",
    "especies_mascota",
    # Restaurante / Comedor (incluye extensión Pizzería: variantes y extras)
    "rest_comanda_item_extras",
    "rest_comanda_items",
    "rest_comandas",
    "rest_variantes_plato",
    "rest_receta_ingredientes",
    "rest_platos",
    "rest_mesas",
    "rest_repartidores",
    # Alquiler de Streaming
    "stream_pagos",
    "stream_suscripcion_perfiles",
    "stream_suscripciones",
    "stream_combo_plataformas",
    "stream_combos",
    "stream_perfiles",
    "stream_cuentas",
    "stream_plataformas",
    # Importaciones (compras en plataformas del exterior)
    "import_detalle",
    "import_compras",
    "import_couriers",
    "import_plataformas",
    # Numeración correlativa de comprobantes y facturas: es un contador
    # operativo ligado a las ventas emitidas, así que se reinicia junto
    # con ellas (vuelve a partir de 0 en ambas modalidades).
    "numeracion_comprobante",
]

# Tablas adicionales que SOLO se vacían en el reinicio total de fábrica
# (dependen de los usuarios, o son historial de uso de cada cuenta).
_TABLAS_SOLO_RESET_TOTAL = [
    "usuarios",
    "sesiones_uso",
    "juegos_puntajes",
]

# Tablas que NUNCA se tocan, sin importar la modalidad: la licencia
# activada (depende de un serial externo), las configuraciones de
# servicios externos o preferencias del sistema (email, IA, idioma,
# apariencia) que no tiene sentido perder en un reinicio de datos del
# negocio, y la caché de textos de la Biblia (contenido descargado de
# Internet, no es un dato del negocio: perderla solo obligaría a
# volver a descargar los mismos libros de nuevo).
_TABLAS_PROTEGIDAS = {
    "licencia_activa", "licencias_generadas", "configuracion_email",
    "configuracion_ia", "configuracion_idioma", "configuracion_apariencia",
    "biblia_cache", "import_configuracion",
    # Configuración del local para comprobantes/facturas (nombre, RUC,
    # timbrado, formato e impresora elegidos): es un dato de configuración
    # del negocio, no una transacción, así que no tiene sentido perderlo
    # en ningún reinicio (se volvería a tener que tipear todo de nuevo).
    "config_local",
}


def tablas_sin_categoria() -> list[str]:
    """Función de diagnóstico interno: compara TODAS las tablas que
    existen de verdad en la base de datos contra las tres listas de
    arriba (datos del negocio, solo-reinicio-total, protegidas) y
    devuelve las que no están en NINGUNA de las tres.

    Sirve para detectar automáticamente, la próxima vez que se agregue
    un módulo nuevo (con sus tablas nuevas), si alguien se olvidó de
    clasificarlas acá — que es exactamente lo que había pasado con las
    tablas de Préstamos, Presupuestos, Asistencia Técnica, Veterinaria,
    Restaurante y Streaming: existían en la base de datos pero el
    reinicio del sistema no las tocaba, así que 'reiniciar todo' no las
    vaciaba de verdad."""
    conocidas = set(_TABLAS_DATOS_NEGOCIO) | set(_TABLAS_SOLO_RESET_TOTAL) | _TABLAS_PROTEGIDAS
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
    """)
    todas = {f[0] for f in cursor.fetchall()}
    conn.close()
    return sorted(todas - conocidas)


def _contar_registros_totales() -> int:
    """Suma la cantidad de filas en todas las tablas que el reset puede
    llegar a borrar, para mostrarle al usuario una idea clara de impacto
    antes de confirmar la operación."""
    conn = conectar()
    cursor = conn.cursor()
    total = 0
    for tabla in _TABLAS_DATOS_NEGOCIO + _TABLAS_SOLO_RESET_TOTAL:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
            total += cursor.fetchone()[0]
        except Exception:
            pass  # tabla inexistente en versiones muy viejas de la BD
    conn.close()
    return total


def obtener_resumen_antes_de_reset() -> dict:
    """Devuelve un resumen legible de cuántos registros hay en las tablas
    principales, para mostrarlo en el diálogo de confirmación."""
    conn = conectar()
    cursor = conn.cursor()

    def _contar(tabla):
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
            return cursor.fetchone()[0]
        except Exception:
            return 0

    resumen = {
        "productos": _contar("productos"),
        "clientes": _contar("clientes"),
        "ventas": _contar("ventas"),
        "movimientos_inventario": _contar("movimientos_inventario"),
        "usuarios": _contar("usuarios"),
        "compras": _contar("compras"),
        "prestamos": _contar("prestamos"),
        "presupuestos": _contar("presupuestos"),
        "casos_tecnicos": _contar("casos_tecnicos"),
        "mascotas": _contar("mascotas"),
        "rest_comandas": _contar("rest_comandas"),
        "stream_suscripciones": _contar("stream_suscripciones"),
        "import_compras": _contar("import_compras"),
    }
    conn.close()
    return resumen


def _vaciar_tablas(cursor, tablas: list[str]):
    """Vacía cada tabla con DELETE (no DROP, para no perder su estructura
    ni romper triggers/índices) y reinicia su contador AUTOINCREMENT en
    sqlite_sequence, para que el próximo INSERT vuelva a empezar en 1."""
    for tabla in tablas:
        try:
            cursor.execute(f"DELETE FROM {tabla}")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name = ?", (tabla,))
        except Exception:
            pass  # tabla inexistente en esta versión de la BD; se ignora


def reiniciar_datos_de_negocio() -> tuple[bool, str]:
    """Borra TODOS los datos operativos (ventas, productos, clientes,
    inventario, caja, compras, créditos, devoluciones, facturas, zonas,
    cobradores) de forma persistente y libera el espacio para reutilizar.

    CONSERVA: usuarios (para no perder el acceso al sistema), la
    licencia activa, y la configuración de email.
    """
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys = OFF")
        _vaciar_tablas(cursor, _TABLAS_DATOS_NEGOCIO)
        conn.commit()
        cursor.execute("PRAGMA foreign_keys = ON")
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"No se pudo reiniciar los datos: {e}"
    conn.close()

    # VACUUM reconstruye el archivo físico, liberando el espacio en disco
    # que ocupaban las filas eliminadas. Necesita su propia conexión, sin
    # una transacción abierta encima.
    try:
        conn2 = conectar()
        conn2.execute("VACUUM")
        conn2.close()
    except Exception:
        pass  # el VACUUM es una optimización; si falla, los datos ya se borraron igual

    return True, (
        "Se reiniciaron todos los datos del negocio: productos, ventas, clientes, "
        "inventario, caja, compras, créditos, devoluciones, presupuestos, "
        "préstamos (cuotas y pagos incluidos), asistencia técnica, veterinaria, "
        "restaurante/comedor, alquiler de streaming e importaciones.\n\n"
        "Los usuarios, la licencia activa, tus puntajes de Juegos y la Biblia "
        "ya descargada se conservaron."
    )


def reinicio_total_de_fabrica() -> tuple[bool, str]:
    """Borra ABSOLUTAMENTE TODO, incluyendo los usuarios, dejando el
    sistema en el mismo estado que recién instalado: al reiniciar la
    aplicación, pedirá crear el primer administrador.

    CONSERVA únicamente: la licencia activa (depende de un serial externo)
    y la configuración de email guardada.
    """
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys = OFF")
        _vaciar_tablas(cursor, _TABLAS_DATOS_NEGOCIO + _TABLAS_SOLO_RESET_TOTAL)
        conn.commit()
        cursor.execute("PRAGMA foreign_keys = ON")
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"No se pudo realizar el reinicio total: {e}"
    conn.close()

    try:
        conn2 = conectar()
        conn2.execute("VACUUM")
        conn2.close()
    except Exception:
        pass

    return True, (
        "Reinicio de fábrica completado. Todos los datos de todos los módulos "
        "(ventas, préstamos, presupuestos, asistencia técnica, veterinaria, "
        "restaurante, streaming, juegos, importaciones), incluyendo usuarios, fueron eliminados "
        "de forma permanente.\n\n"
        "La próxima vez que se inicie el sistema, pedirá crear el primer "
        "administrador, como una instalación nueva.\n\n"
        "La licencia activa y la Biblia ya descargada se conservaron."
    )
