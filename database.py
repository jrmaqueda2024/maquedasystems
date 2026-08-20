"""
database.py
Maneja la conexión a la base de datos SQLite y la creación de tablas.
"""
import sqlite3
import os

NOMBRE_BD = "ventas.db"bbfbfbfbffbffvfbffbfbfbfbfbfbfffbbvbbfbffbfbffbfbfbfbff
bfbfbvf
bfbfbfbfbfbfbf
def obtener_ruta_bd():
    """Devuelve la ruta absoluta del archivo de base de datos. En desarrollo
    queda junto a los .py; empaquetado con PyInstaller queda junto al .exe,
    para que persista entre ejecuciones (ver utilidades_ui.obtener_carpeta_base)."""
    from utilidades_ui import obtener_carpeta_base
    return os.path.join(obtener_carpeta_base(), NOMBRE_BD)


def conectar():
    """Crea y devuelve una conexión a la base de datos.
    check_same_thread=False permite usarla desde la interfaz gráfica sin problemas."""
    conn = sqlite3.connect(obtener_ruta_bd(), check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")  # Activa integridad referencial
    return conn


def inicializar_bd():
    """Crea todas las tablas si no existen todavía."""
    conn = conectar()
    cursor = conn.cursor()

    # Tabla de usuarios del sistema (login)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_completo TEXT NOT NULL,
            usuario TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            rol TEXT NOT NULL CHECK(rol IN ('admin', 'gerente', 'vendedor')),
            activo INTEGER NOT NULL DEFAULT 1,
            fecha_creacion TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # Tabla de productos / inventario
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria TEXT,
            precio REAL NOT NULL CHECK(precio >= 0),
            stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
            activo INTEGER NOT NULL DEFAULT 1
        )
    """)

    # Tabla de clientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            email TEXT,
            direccion TEXT,
            fecha_creacion TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # Tabla de ventas (cabecera)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            usuario_id INTEGER NOT NULL,
            fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            total REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    # Tabla de detalle de ventas (líneas de cada venta)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalle_ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER NOT NULL,
            producto_id INTEGER,
            descripcion_libre TEXT,
            cantidad REAL NOT NULL CHECK(cantidad > 0),
            precio_unitario REAL NOT NULL,
            FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    """)

    conn.commit()
    conn.close()
    _crear_tablas_extendidas()


def _crear_tablas_extendidas():
    """Crea las tablas adicionales para el sistema completo tipo MetaVentas:
    marcas, categorías, proveedores, créditos, pagos, compras y facturación."""
    conn = conectar()
    cursor = conn.cursor()

    # --- Marcas y Categorías de productos ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marcas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    """)

    # --- Proveedores ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            direccion TEXT,
            ruc TEXT
        )
    """)
    # Persona de contacto (agregada luego de la creación original de la tabla).
    columnas_proveedores = [
        ("contacto", "TEXT"),
    ]
    cursor.execute("PRAGMA table_info(proveedores)")
    columnas_existentes = {fila[1] for fila in cursor.fetchall()}
    for nombre_col, definicion in columnas_proveedores:
        if nombre_col not in columnas_existentes:
            cursor.execute(f"ALTER TABLE proveedores ADD COLUMN {nombre_col} {definicion}")

    # --- Migración: si la tabla usuarios viene de una versión vieja con
    # CHECK(rol IN ('admin','vendedor')), la recreamos permitiendo también
    # 'gerente' — el rol "Gerente" ya existe en la interfaz y en la lógica
    # de permisos (auth.usuario_tiene_acceso) desde hace tiempo, pero sin
    # este ajuste el guardado fallaba con un error de la base de datos
    # apenas se elegía ese rol. Se preservan todas las columnas y datos
    # existentes, cualquiera sea el estado de la tabla al momento de migrar.
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='usuarios'")
    fila_sql = cursor.fetchone()
    sql_usuarios = (fila_sql[0] if fila_sql else "") or ""
    sql_compacto = "".join(sql_usuarios.split()).lower()
    if "check(rolin(" in sql_compacto and "'gerente'" not in sql_compacto:
        cursor.execute("PRAGMA table_info(usuarios)")
        columnas_actuales = [fila[1] for fila in cursor.fetchall()]
        columnas_csv = ", ".join(columnas_actuales)
        cursor.execute("ALTER TABLE usuarios RENAME TO _usuarios_old")
        cursor.execute("""
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_completo TEXT NOT NULL,
                usuario TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                rol TEXT NOT NULL CHECK(rol IN ('admin', 'gerente', 'vendedor')),
                activo INTEGER NOT NULL DEFAULT 1,
                fecha_creacion TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
        """)
        # Volvemos a agregar cualquier columna extra que ya tuviera la
        # tabla vieja (permisos, email, etc.), antes de copiar los datos.
        cursor.execute("PRAGMA table_info(usuarios)")
        columnas_base = {fila[1] for fila in cursor.fetchall()}
        definiciones_extra = {
            "permisos":         "TEXT NOT NULL DEFAULT ''",
            "email":            "TEXT",
            "telefono":         "TEXT",
            "fecha_nacimiento": "TEXT",
            "foto_ruta":        "TEXT",
            "direccion":        "TEXT",
            "observaciones":    "TEXT",
        }
        for nombre_col in columnas_actuales:
            if nombre_col not in columnas_base:
                definicion = definiciones_extra.get(nombre_col, "TEXT")
                cursor.execute(f"ALTER TABLE usuarios ADD COLUMN {nombre_col} {definicion}")
        cursor.execute(f"INSERT INTO usuarios ({columnas_csv}) SELECT {columnas_csv} FROM _usuarios_old")
        cursor.execute("DROP TABLE _usuarios_old")

    # --- Ampliar tabla usuarios: permisos por módulo ---
    columnas_usuarios = [
        ("permisos",        "TEXT NOT NULL DEFAULT ''"),
        ("email",           "TEXT"),
        ("telefono",        "TEXT"),
        ("fecha_nacimiento","TEXT"),
        ("foto_ruta",       "TEXT"),
        ("direccion",       "TEXT"),
        ("observaciones",   "TEXT"),
    ]
    cursor.execute("PRAGMA table_info(usuarios)")
    columnas_existentes = {fila[1] for fila in cursor.fetchall()}
    for nombre_col, definicion in columnas_usuarios:
        if nombre_col not in columnas_existentes:
            cursor.execute(f"ALTER TABLE usuarios ADD COLUMN {nombre_col} {definicion}")

    # --- Ampliar tabla productos con columnas nuevas (si no existen) ---
    columnas_productos = [
        ("marca_id", "INTEGER REFERENCES marcas(id)"),
        ("categoria_id", "INTEGER REFERENCES categorias(id)"),
        ("proveedor_id", "INTEGER REFERENCES proveedores(id)"),
        ("precio_compra", "REAL NOT NULL DEFAULT 0"),
        ("precio_credito", "REAL NOT NULL DEFAULT 0"),
        ("precio_mayorista", "REAL NOT NULL DEFAULT 0"),
        ("stock_minimo", "REAL NOT NULL DEFAULT 0"),
        ("comprometido", "REAL NOT NULL DEFAULT 0"),
        ("codigo_secundario", "TEXT"),
        ("codigo_barras", "TEXT"),
        ("unidad_medida", "TEXT NOT NULL DEFAULT 'Unidad'"),
        ("tipo_impuesto", "TEXT NOT NULL DEFAULT 'IVA 10%'"),
        ("tipo_producto", "TEXT NOT NULL DEFAULT 'Producto'"),  # 'Producto' o 'Servicio'
        ("control_stock", "TEXT NOT NULL DEFAULT 'Cantidad'"),  # 'Cantidad' o 'Ilimitado'
        ("imagen_ruta", "TEXT"),
        ("es_articulo_comun", "INTEGER NOT NULL DEFAULT 0"),
    ]
    cursor.execute("PRAGMA table_info(productos)")
    columnas_existentes = {fila[1] for fila in cursor.fetchall()}
    for nombre_col, definicion in columnas_productos:
        if nombre_col not in columnas_existentes:
            cursor.execute(f"ALTER TABLE productos ADD COLUMN {nombre_col} {definicion}")

    # Índices únicos parciales: solo exigen unicidad cuando el código no está vacío/nulo,
    # así varios productos pueden no tener código secundario o de barras sin chocar entre sí.
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_productos_codigo_secundario
        ON productos(codigo_secundario)
        WHERE codigo_secundario IS NOT NULL AND codigo_secundario != ''
    """)
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_productos_codigo_barras
        ON productos(codigo_barras)
        WHERE codigo_barras IS NOT NULL AND codigo_barras != ''
    """)

    # --- Zonas y Cobradores (listas gestionables, igual que Marca/Categoría) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS zonas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cobradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    """)

    # --- Ampliar tabla clientes con todos los datos del formulario completo ---
    columnas_clientes = [
        ("razon_social", "TEXT"),
        ("nro_documento", "TEXT"),
        ("tipo_persona", "TEXT NOT NULL DEFAULT 'Física'"),  # 'Física' o 'Jurídica'
        ("nacionalidad", "TEXT NOT NULL DEFAULT 'Paraguaya'"),  # 'Paraguaya' o 'Extranjera'
        ("ruc", "TEXT"),
        ("fecha_nacimiento", "TEXT"),
        ("observaciones", "TEXT"),
        ("credito_permitido", "INTEGER NOT NULL DEFAULT 0"),
        ("dia_cobro", "TEXT NOT NULL DEFAULT 'Sin Asignar'"),
        ("zona_id", "INTEGER REFERENCES zonas(id)"),
        ("cobrador_id", "INTEGER REFERENCES cobradores(id)"),
    ]
    cursor.execute("PRAGMA table_info(clientes)")
    columnas_existentes = {fila[1] for fila in cursor.fetchall()}
    for nombre_col, definicion in columnas_clientes:
        if nombre_col not in columnas_existentes:
            cursor.execute(f"ALTER TABLE clientes ADD COLUMN {nombre_col} {definicion}")

    # --- Ampliar tabla ventas: condición de venta, estado, vendedor texto ---
    columnas_ventas = [
        ("condicion", "TEXT NOT NULL DEFAULT 'contado'"),  # 'contado' o 'credito'
        ("forma_pago", "TEXT NOT NULL DEFAULT 'Efectivo'"),
        ("estado", "TEXT NOT NULL DEFAULT 'Pagado'"),  # Pagado / Cancelado
        ("es_pre_venta", "INTEGER NOT NULL DEFAULT 0"),
        # Documento elegido en la ventana Cobrar: 'comprobante' (ticket sin
        # datos fiscales) o 'factura' (Factura Legal con RUC/Timbrado/IVA).
        ("tipo_documento", "TEXT NOT NULL DEFAULT 'comprobante'"),
        # Número correlativo del Comprobante de Venta (formato
        # ESTABLECIMIENTO-PUNTO_EXP-NÚMERO), tomado de la numeración
        # configurada en Config. Local → Numeración y fijado una sola vez
        # al procesar la venta (no se recalcula cada vez que se reimprime).
        ("nro_comprobante", "TEXT"),
    ]
    cursor.execute("PRAGMA table_info(ventas)")
    columnas_existentes = {fila[1] for fila in cursor.fetchall()}
    for nombre_col, definicion in columnas_ventas:
        if nombre_col not in columnas_existentes:
            cursor.execute(f"ALTER TABLE ventas ADD COLUMN {nombre_col} {definicion}")

    # --- Créditos (se generan cuando una venta es 'credito') ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS creditos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER NOT NULL,
            cliente_id INTEGER,
            fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            fecha_vencimiento TEXT,
            descripcion TEXT,
            deuda_total REAL NOT NULL,
            pagado REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (venta_id) REFERENCES ventas(id),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    """)

    # --- Pagos parciales a créditos ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pagos_credito (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            credito_id INTEGER NOT NULL,
            fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            monto REAL NOT NULL,
            FOREIGN KEY (credito_id) REFERENCES creditos(id) ON DELETE CASCADE
        )
    """)

    # --- Facturas (una por venta procesada, numeración correlativa) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER NOT NULL UNIQUE,
            nro_factura TEXT NOT NULL UNIQUE,
            fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            razon_social TEXT,
            ruc TEXT,
            valor_total REAL NOT NULL,
            estado TEXT NOT NULL DEFAULT 'Vigente',
            FOREIGN KEY (venta_id) REFERENCES ventas(id)
        )
    """)

    # --- Compras (cabecera) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor_id INTEGER,
            fecha_y_hora TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            fecha_compra TEXT NOT NULL,
            nro_comprobante TEXT,
            importe REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
        )
    """)

    # --- Detalle de compras (líneas) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalle_compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            compra_id INTEGER NOT NULL,
            producto_id INTEGER,
            producto_nombre_historico TEXT,
            cantidad REAL NOT NULL CHECK(cantidad > 0),
            precio_unitario REAL NOT NULL,
            FOREIGN KEY (compra_id) REFERENCES compras(id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    """)
    cursor.execute("PRAGMA table_info(detalle_compras)")
    columnas_detalle_compras = {fila[1] for fila in cursor.fetchall()}
    if "producto_nombre_historico" not in columnas_detalle_compras:
        cursor.execute("ALTER TABLE detalle_compras ADD COLUMN producto_nombre_historico TEXT")
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='detalle_compras'")
    sql_tabla_dc = cursor.fetchone()
    if sql_tabla_dc and "producto_id INTEGER NOT NULL" in sql_tabla_dc[0]:
        cursor.executescript("""
            PRAGMA foreign_keys = OFF;
            ALTER TABLE detalle_compras RENAME TO _detalle_compras_old;
            CREATE TABLE detalle_compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                compra_id INTEGER NOT NULL,
                producto_id INTEGER,
                producto_nombre_historico TEXT,
                cantidad REAL NOT NULL CHECK(cantidad > 0),
                precio_unitario REAL NOT NULL,
                FOREIGN KEY (compra_id) REFERENCES compras(id) ON DELETE CASCADE,
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            );
            INSERT INTO detalle_compras
                (id, compra_id, producto_id, cantidad, precio_unitario)
            SELECT id, compra_id, producto_id, cantidad, precio_unitario
            FROM _detalle_compras_old;
            DROP TABLE _detalle_compras_old;
            PRAGMA foreign_keys = ON;
        """)

    # --- Movimientos de inventario (entradas/salidas manuales, distinto de ventas/compras) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimientos_inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER,
            producto_nombre_historico TEXT,
            tipo TEXT NOT NULL CHECK(tipo IN ('entrada', 'salida')),
            cantidad REAL NOT NULL CHECK(cantidad > 0),
            motivo TEXT,
            fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            usuario_id INTEGER,
            FOREIGN KEY (producto_id) REFERENCES productos(id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)
    columnas_movimientos = [
        ("nro_comprobante", "TEXT"),
        ("observaciones", "TEXT"),
        ("stock_resultante", "REAL"),
        ("producto_nombre_historico", "TEXT"),
        ("es_ilimitado", "INTEGER NOT NULL DEFAULT 0"),
    ]
    cursor.execute("PRAGMA table_info(movimientos_inventario)")
    columnas_existentes = {fila[1] for fila in cursor.fetchall()}
    for nombre_col, definicion in columnas_movimientos:
        if nombre_col not in columnas_existentes:
            cursor.execute(f"ALTER TABLE movimientos_inventario ADD COLUMN {nombre_col} {definicion}")

    # --- Migración: hacer producto_id nullable en movimientos_inventario,
    # para poder desvincular (no borrar) el historial de un producto
    # eliminado definitivamente, preservando su nombre como referencia. ---
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='movimientos_inventario'")
    sql_tabla_mov = cursor.fetchone()
    if sql_tabla_mov and "producto_id INTEGER NOT NULL" in sql_tabla_mov[0]:
        cursor.executescript("""
            PRAGMA foreign_keys = OFF;
            ALTER TABLE movimientos_inventario RENAME TO _movimientos_inventario_old;
            CREATE TABLE movimientos_inventario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER,
                producto_nombre_historico TEXT,
                tipo TEXT NOT NULL CHECK(tipo IN ('entrada', 'salida')),
                cantidad REAL NOT NULL CHECK(cantidad > 0),
                motivo TEXT,
                fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                usuario_id INTEGER,
                nro_comprobante TEXT,
                observaciones TEXT,
                stock_resultante REAL,
                FOREIGN KEY (producto_id) REFERENCES productos(id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            );
            INSERT INTO movimientos_inventario
                (id, producto_id, tipo, cantidad, motivo, fecha, usuario_id,
                 nro_comprobante, observaciones, stock_resultante)
            SELECT id, producto_id, tipo, cantidad, motivo, fecha, usuario_id,
                   nro_comprobante, observaciones, stock_resultante
            FROM _movimientos_inventario_old;
            DROP TABLE _movimientos_inventario_old;
            PRAGMA foreign_keys = ON;
        """)

    # --- Caja: saldo inicial diario y movimientos manuales ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS caja_movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            tipo TEXT NOT NULL CHECK(tipo IN ('entrada', 'salida', 'saldo_inicial')),
            monto REAL NOT NULL,
            descripcion TEXT
        )
    """)
    cursor.execute("PRAGMA table_info(caja_movimientos)")
    columnas_existentes_caja = {fila[1] for fila in cursor.fetchall()}
    if "usuario_id" not in columnas_existentes_caja:
        cursor.execute("ALTER TABLE caja_movimientos ADD COLUMN usuario_id INTEGER REFERENCES usuarios(id)")

    # --- Ampliar detalle_ventas: cuánto de cada línea ya fue devuelto ---
    cursor.execute("PRAGMA table_info(detalle_ventas)")
    columnas_existentes = {fila[1] for fila in cursor.fetchall()}
    if "cantidad_devuelta" not in columnas_existentes:
        cursor.execute("ALTER TABLE detalle_ventas ADD COLUMN cantidad_devuelta REAL NOT NULL DEFAULT 0")
    # --- Soporte para "Venta Libre" (Producto Común sin BD): descripción manual ---
    if "descripcion_libre" not in columnas_existentes:
        cursor.execute("ALTER TABLE detalle_ventas ADD COLUMN descripcion_libre TEXT")

    # --- Migración: hacer producto_id nullable para soportar ventas libres ---
    # SQLite no permite ALTER COLUMN, así que recreamos la tabla si es necesario.
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='detalle_ventas'")
    sql_tabla = cursor.fetchone()
    if sql_tabla and "producto_id INTEGER NOT NULL" in sql_tabla[0]:
        cursor.executescript("""
            PRAGMA foreign_keys = OFF;
            ALTER TABLE detalle_ventas RENAME TO _detalle_ventas_old;
            CREATE TABLE detalle_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER NOT NULL,
                producto_id INTEGER,
                descripcion_libre TEXT,
                cantidad REAL NOT NULL CHECK(cantidad > 0),
                precio_unitario REAL NOT NULL,
                cantidad_devuelta REAL NOT NULL DEFAULT 0,
                FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            );
            INSERT INTO detalle_ventas
                (id, venta_id, producto_id, cantidad, precio_unitario, cantidad_devuelta)
            SELECT id, venta_id, producto_id, cantidad, precio_unitario,
                   COALESCE(cantidad_devuelta, 0)
            FROM _detalle_ventas_old;
            DROP TABLE _detalle_ventas_old;
            PRAGMA foreign_keys = ON;
        """)

    # --- Devoluciones: historial de devoluciones de artículos específicos ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS devoluciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER NOT NULL,
            detalle_venta_id INTEGER NOT NULL,
            producto_id INTEGER,
            producto_nombre_historico TEXT,
            cantidad REAL NOT NULL CHECK(cantidad > 0),
            importe REAL NOT NULL,
            fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            usuario_id INTEGER,
            FOREIGN KEY (venta_id) REFERENCES ventas(id),
            FOREIGN KEY (detalle_venta_id) REFERENCES detalle_ventas(id),
            FOREIGN KEY (producto_id) REFERENCES productos(id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)
    cursor.execute("PRAGMA table_info(devoluciones)")
    columnas_devoluciones = {fila[1] for fila in cursor.fetchall()}
    if "producto_nombre_historico" not in columnas_devoluciones:
        cursor.execute("ALTER TABLE devoluciones ADD COLUMN producto_nombre_historico TEXT")
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='devoluciones'")
    sql_tabla_dev = cursor.fetchone()
    if sql_tabla_dev and "producto_id INTEGER NOT NULL" in sql_tabla_dev[0]:
        cursor.executescript("""
            PRAGMA foreign_keys = OFF;
            ALTER TABLE devoluciones RENAME TO _devoluciones_old;
            CREATE TABLE devoluciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER NOT NULL,
                detalle_venta_id INTEGER NOT NULL,
                producto_id INTEGER,
                producto_nombre_historico TEXT,
                cantidad REAL NOT NULL CHECK(cantidad > 0),
                importe REAL NOT NULL,
                fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                usuario_id INTEGER,
                FOREIGN KEY (venta_id) REFERENCES ventas(id),
                FOREIGN KEY (detalle_venta_id) REFERENCES detalle_ventas(id),
                FOREIGN KEY (producto_id) REFERENCES productos(id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            );
            INSERT INTO devoluciones
                (id, venta_id, detalle_venta_id, producto_id, cantidad,
                 importe, fecha, usuario_id)
            SELECT id, venta_id, detalle_venta_id, producto_id, cantidad,
                   importe, fecha, usuario_id
            FROM _devoluciones_old;
            DROP TABLE _devoluciones_old;
            PRAGMA foreign_keys = ON;
        """)

    conn.commit()
    conn.close()
    _crear_tabla_configuracion_email()
    _crear_tabla_configuracion_ia()
    _crear_tabla_configuracion_idioma()
    _crear_tabla_configuracion_apariencia()
    _crear_tablas_licencia_y_sesion()
    _crear_tablas_asistencia_tecnica()
    _crear_tablas_presupuestos()
    _crear_tablas_prestamos()
    _crear_tablas_veterinaria()
    _crear_tablas_restaurante()
    _crear_tablas_extension_pizzeria()
    _crear_tablas_streaming()
    _crear_tablas_juegos()
    _crear_tablas_biblia()
    _crear_tablas_importacion()


def _crear_tablas_licencia_y_sesion():
    """Tablas para el sistema de licenciamiento y el cronómetro de uso."""
    conn = conectar()
    cursor = conn.cursor()

    # --- Catálogo de seriales generados por el sistema ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS licencias_generadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial TEXT NOT NULL UNIQUE,
            tipo TEXT NOT NULL,
            duracion_meses INTEGER NOT NULL DEFAULT 0,
            fecha_generacion TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            usada INTEGER NOT NULL DEFAULT 0,
            fecha_uso TEXT
        )
    """)

    # --- Licencia activa actualmente en el sistema (fila única id=1) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS licencia_activa (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            serial TEXT NOT NULL,
            tipo TEXT NOT NULL,
            duracion_meses INTEGER NOT NULL,
            fecha_activacion TEXT NOT NULL,
            fecha_vencimiento TEXT NOT NULL
        )
    """)

    # --- Migración: si la tabla licencias_generadas viene de una versión
    # vieja con CHECK(tipo IN ('mensual','anual')), la recreamos sin esa
    # restricción para poder guardar nuevos tipos (Ilimitado, días, horas...).
    cursor.execute("SELECT sql FROM sqlite_master WHERE name='licencias_generadas'")
    fila_sql = cursor.fetchone()
    sql_actual = (fila_sql[0] if fila_sql else "") or ""
    # Detectamos la restricción CHECK(tipo IN ...) en cualquier formato razonable
    sql_compacto = "".join(sql_actual.split()).lower()
    necesita_recrear = ("check(tipoin(" in sql_compacto
                        or "check(duracion_meses>" in sql_compacto)
    if necesita_recrear:
        cursor.execute("ALTER TABLE licencias_generadas RENAME TO _licencias_generadas_old")
        cursor.execute("""
            CREATE TABLE licencias_generadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serial TEXT NOT NULL UNIQUE,
                tipo TEXT NOT NULL,
                duracion_meses INTEGER NOT NULL DEFAULT 0,
                fecha_generacion TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                usada INTEGER NOT NULL DEFAULT 0,
                fecha_uso TEXT
            )
        """)
        cursor.execute("""
            INSERT INTO licencias_generadas
                (id, serial, tipo, duracion_meses, fecha_generacion, usada, fecha_uso)
            SELECT id, serial, tipo, duracion_meses, fecha_generacion, usada, fecha_uso
            FROM _licencias_generadas_old
        """)
        cursor.execute("DROP TABLE _licencias_generadas_old")

    # --- Añadir columnas nuevas para soportar más unidades ---
    # duracion_valor: cantidad numérica (ej: 30)
    # duracion_unidad: 'minutos','horas','dias','semanas','meses','anios','ilimitado'
    for tabla in ("licencias_generadas", "licencia_activa"):
        cursor.execute(f"PRAGMA table_info({tabla})")
        cols = {f[1] for f in cursor.fetchall()}
        if "duracion_valor" not in cols:
            cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN duracion_valor INTEGER NOT NULL DEFAULT 0")
        if "duracion_unidad" not in cols:
            cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN duracion_unidad TEXT NOT NULL DEFAULT 'meses'")
        if "duracion_componentes" not in cols:
            # JSON opcional con la duración combinada, ej: {"meses":1,"dias":15}
            # Si está vacío, se usa el par duracion_valor/duracion_unidad de siempre.
            cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN duracion_componentes TEXT NOT NULL DEFAULT ''")
        # Rellenar filas antiguas que no tengan los datos nuevos
        cursor.execute(f"""
            UPDATE {tabla}
            SET duracion_unidad = 'meses',
                duracion_valor = duracion_meses
            WHERE (duracion_unidad = '' OR duracion_unidad IS NULL OR duracion_valor = 0)
              AND duracion_meses > 0
        """)

    # --- Sesiones de uso (cronómetro) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sesiones_uso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            usuario_nombre TEXT,
            fecha_inicio TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            fecha_fin TEXT,
            duracion_segundos INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def _crear_tabla_configuracion_email():
    """Tabla de cuentas de correo remitente, usada por el botón 'Email' del
    Resumen de Ventas y por los reportes del módulo Veterinaria. Admite
    cualquier proveedor SMTP (Gmail, Outlook/Hotmail, Yahoo, ProtonMail con
    Bridge, o un servidor personalizado), y VARIAS cuentas guardadas a la
    vez (antes solo se podía tener una): se pueden agregar todas las que
    hagan falta y elegir cuál es la 'activa' (la que se usa para enviar),
    sin tener que borrar las demás para cambiar de cuenta."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracion_email (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            correo_remitente TEXT NOT NULL,
            contrasena_aplicacion TEXT,
            nombre_remitente TEXT DEFAULT 'Sistema de Gestión de Ventas',
            proveedor TEXT NOT NULL DEFAULT 'gmail',
            servidor_smtp TEXT,
            puerto_smtp INTEGER,
            seguridad TEXT NOT NULL DEFAULT 'ssl',
            activa INTEGER NOT NULL DEFAULT 0,
            ultimo_destinatario TEXT,
            fecha_creacion TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # --- Migración: la versión vieja tenía una única fila fija (id=1,
    # CHECK(id=1)) y sin columna 'activa'. Si detectamos ese esquema,
    # migramos la cuenta que hubiera configurada (si había alguna) a la
    # nueva tabla, marcándola como activa, preservando todos sus datos. ---
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='configuracion_email'")
    fila_sql = cursor.fetchone()
    sql_actual = (fila_sql[0] if fila_sql else "") or ""
    sql_compacto = "".join(sql_actual.split()).lower()
    if "check(id=1)" in sql_compacto:
        cursor.execute("ALTER TABLE configuracion_email RENAME TO _configuracion_email_old")
        cursor.execute("""
            CREATE TABLE configuracion_email (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                correo_remitente TEXT NOT NULL,
                contrasena_aplicacion TEXT,
                nombre_remitente TEXT DEFAULT 'Sistema de Gestión de Ventas',
                proveedor TEXT NOT NULL DEFAULT 'gmail',
                servidor_smtp TEXT,
                puerto_smtp INTEGER,
                seguridad TEXT NOT NULL DEFAULT 'ssl',
                activa INTEGER NOT NULL DEFAULT 0,
                ultimo_destinatario TEXT,
                fecha_creacion TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
        """)
        cursor.execute("PRAGMA table_info(_configuracion_email_old)")
        cols_viejas = {f[1] for f in cursor.fetchall()}
        if "correo_remitente" in cols_viejas:
            col_proveedor = "COALESCE(proveedor, 'gmail')" if "proveedor" in cols_viejas else "'gmail'"
            col_servidor = "servidor_smtp" if "servidor_smtp" in cols_viejas else "NULL"
            col_puerto = "puerto_smtp" if "puerto_smtp" in cols_viejas else "NULL"
            col_seguridad = "COALESCE(seguridad, 'ssl')" if "seguridad" in cols_viejas else "'ssl'"
            col_destinatario = "ultimo_destinatario" if "ultimo_destinatario" in cols_viejas else "NULL"
            cursor.execute(f"""
                SELECT correo_remitente, contrasena_aplicacion, nombre_remitente,
                       {col_proveedor}, {col_servidor}, {col_puerto},
                       {col_seguridad}, {col_destinatario}
                FROM _configuracion_email_old WHERE id = 1
            """)
            vieja = cursor.fetchone()
            if vieja and vieja[0]:
                cursor.execute("""
                    INSERT INTO configuracion_email
                        (correo_remitente, contrasena_aplicacion, nombre_remitente,
                         proveedor, servidor_smtp, puerto_smtp, seguridad, activa,
                         ultimo_destinatario)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                """, vieja)
        cursor.execute("DROP TABLE _configuracion_email_old")

    conn.commit()
    conn.close()


def _crear_tabla_configuracion_ia():
    """Tabla de una sola fila (id=1) con la configuración del módulo
    Asistente IA: proveedor (openai/anthropic/personalizado), clave de
    API, modelo elegido y, para proveedores compatibles con la API de
    OpenAI pero no oficiales (DeepSeek, Groq, OpenRouter, etc.), la URL
    base personalizada."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracion_ia (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            proveedor TEXT NOT NULL DEFAULT 'openai',
            api_key TEXT,
            modelo TEXT,
            url_base_personalizada TEXT,
            activo INTEGER NOT NULL DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()


def _crear_tabla_configuracion_idioma():
    """Tabla de una sola fila (id=1) con el idioma actual de la interfaz
    del sistema (no traduce los datos ya cargados, solo los textos fijos
    de menús, botones y títulos). Ver traducciones.py."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracion_idioma (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            idioma TEXT NOT NULL DEFAULT 'es'
        )
    """)
    conn.commit()
    conn.close()


def _crear_tabla_configuracion_apariencia():
    """Tabla de una sola fila (id=1) con la apariencia elegida en 'Ajustes
    del Sistema': tema (claro/oscuro), familia de fuente y escala de
    tamaño de letra. Ver models_configuracion.py y fuentes.py."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracion_apariencia (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            tema TEXT NOT NULL DEFAULT 'claro',
            fuente_familia TEXT NOT NULL DEFAULT 'Segoe UI',
            fuente_escala INTEGER NOT NULL DEFAULT 100
        )
    """)
    conn.commit()
    conn.close()


def _crear_tablas_asistencia_tecnica():
    """Tablas del módulo Asistencia Técnica: catálogo de Tipos de Equipo,
    catálogo de Equipos Registrados (para F3 - Buscar Equipo y la pestaña
    Equipos) y los Casos técnicos en sí (cabecera de cada ingreso de
    equipo, con su estado dentro del flujo de reparación)."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipos_equipo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipos_registrados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            tipo_equipo_id INTEGER,
            nro_serie TEXT,
            descripcion TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL,
            FOREIGN KEY (tipo_equipo_id) REFERENCES tipos_equipo(id) ON DELETE SET NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS casos_tecnicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            cliente_nombre TEXT NOT NULL DEFAULT '',
            cliente_documento TEXT,
            cliente_direccion TEXT,
            cliente_telefono TEXT,
            tipo_equipo_id INTEGER,
            tipo_equipo_texto TEXT,
            nro_serie TEXT,
            descripcion_equipo TEXT NOT NULL DEFAULT '',
            prioridad TEXT NOT NULL DEFAULT 'Media',
            estado TEXT NOT NULL DEFAULT 'Entrada',
            observaciones TEXT,
            fecha_entrada TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            fecha_estado TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            fecha_retiro TEXT,
            anulado INTEGER NOT NULL DEFAULT 0,
            usuario_id INTEGER,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL,
            FOREIGN KEY (tipo_equipo_id) REFERENCES tipos_equipo(id) ON DELETE SET NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    conn.commit()
    conn.close()


def _crear_tablas_presupuestos():
    """Tablas del módulo Presupuestos: cabecera (cliente, fecha, validez,
    estado, total) y detalle (artículos cotizados). Cuando un presupuesto
    se convierte en venta real, queda vinculado vía 'venta_id' y su estado
    pasa a 'Convertido' — pero no se borra, para conservar el historial de
    lo cotizado."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS presupuestos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            cliente_nombre TEXT NOT NULL DEFAULT '',
            cliente_documento TEXT,
            cliente_direccion TEXT,
            cliente_telefono TEXT,
            fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            fecha_validez TEXT,
            estado TEXT NOT NULL DEFAULT 'Pendiente',
            observaciones TEXT,
            total REAL NOT NULL DEFAULT 0,
            usuario_id INTEGER,
            venta_id INTEGER,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE SET NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalle_presupuestos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            presupuesto_id INTEGER NOT NULL,
            producto_id INTEGER,
            descripcion_libre TEXT,
            cantidad REAL NOT NULL,
            precio_unitario REAL NOT NULL,
            FOREIGN KEY (presupuesto_id) REFERENCES presupuestos(id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE SET NULL
        )
    """)

    conn.commit()
    conn.close()


def _crear_tablas_prestamos():
    """Módulo Préstamos (financiera): un 'Banco Central' interno (fondo de
    dinero disponible para prestar), los préstamos otorgados (con su
    sistema de amortización: Francés, Alemán, Americano o Directo/Flat),
    el cronograma de cuotas de cada uno, y el registro granular de pagos.

    El saldo del fondo NUNCA se guarda como un número suelto: siempre se
    calcula sumando fondo_movimientos, igual que el patrón usado en
    movimientos_inventario, para que quede un historial auditable completo
    de cada carga de capital y cada préstamo desembolsado/cobrado."""
    conn = conectar()
    cursor = conn.cursor()

    # --- Fondo central de préstamos: ledger de cargas, desembolsos y cobros ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fondo_prestamos_movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            tipo TEXT NOT NULL CHECK(tipo IN ('carga', 'desembolso', 'cobro', 'ajuste')),
            monto REAL NOT NULL CHECK(monto > 0),
            descripcion TEXT,
            prestamo_id INTEGER,
            usuario_id INTEGER,
            saldo_resultante REAL,
            FOREIGN KEY (prestamo_id) REFERENCES prestamos(id) ON DELETE SET NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    # --- Préstamos otorgados ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prestamos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            fecha_desembolso TEXT NOT NULL,
            capital REAL NOT NULL CHECK(capital > 0),
            tasa_interes REAL NOT NULL CHECK(tasa_interes >= 0),
            frecuencia TEXT NOT NULL CHECK(frecuencia IN ('diaria', 'semanal', 'quincenal', 'mensual')),
            cantidad_cuotas INTEGER NOT NULL CHECK(cantidad_cuotas > 0),
            sistema TEXT NOT NULL CHECK(sistema IN ('frances', 'aleman', 'americano', 'directo')),
            tasa_mora_diaria REAL NOT NULL DEFAULT 0,
            estado TEXT NOT NULL DEFAULT 'activo' CHECK(estado IN ('activo', 'pagado', 'cancelado')),
            observaciones TEXT,
            usuario_id INTEGER,
            fecha_creacion TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    # --- Cronograma de cuotas de cada préstamo ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cuotas_prestamo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prestamo_id INTEGER NOT NULL,
            nro_cuota INTEGER NOT NULL,
            fecha_vencimiento TEXT NOT NULL,
            capital REAL NOT NULL,
            interes REAL NOT NULL,
            pagado_capital REAL NOT NULL DEFAULT 0,
            pagado_interes REAL NOT NULL DEFAULT 0,
            pagado_mora REAL NOT NULL DEFAULT 0,
            fecha_pago_completo TEXT,
            FOREIGN KEY (prestamo_id) REFERENCES prestamos(id) ON DELETE CASCADE
        )
    """)

    # --- Registro granular de pagos (historial tipo "movimientos_inventario") ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pagos_prestamo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prestamo_id INTEGER NOT NULL,
            cuota_id INTEGER NOT NULL,
            fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            monto_capital REAL NOT NULL DEFAULT 0,
            monto_interes REAL NOT NULL DEFAULT 0,
            monto_mora REAL NOT NULL DEFAULT 0,
            monto_total REAL NOT NULL DEFAULT 0,
            usuario_id INTEGER,
            FOREIGN KEY (prestamo_id) REFERENCES prestamos(id) ON DELETE CASCADE,
            FOREIGN KEY (cuota_id) REFERENCES cuotas_prestamo(id) ON DELETE CASCADE,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    conn.commit()
    conn.close()



def _crear_tablas_veterinaria():
    """Tablas del módulo Veterinaria: catálogo de Especies (editable, igual
    que Tipos de Equipo), Mascotas (ficha del paciente, ligada opcionalmente
    a un Cliente = dueño), Consultas (historial clínico de cada visita),
    Vacunas aplicadas y Tratamientos/desparasitaciones en curso."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS especies_mascota (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mascotas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            dueño_nombre TEXT NOT NULL DEFAULT '',
            dueño_telefono TEXT,
            nombre TEXT NOT NULL,
            especie_id INTEGER,
            especie_texto TEXT,
            raza TEXT,
            sexo TEXT NOT NULL DEFAULT 'Desconocido' CHECK(sexo IN ('Macho', 'Hembra', 'Desconocido')),
            fecha_nacimiento TEXT,
            color TEXT,
            peso_kg REAL,
            microchip TEXT,
            esterilizado INTEGER NOT NULL DEFAULT 0,
            fallecido INTEGER NOT NULL DEFAULT 0,
            observaciones TEXT,
            fecha_creacion TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL,
            FOREIGN KEY (especie_id) REFERENCES especies_mascota(id) ON DELETE SET NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consultas_veterinarias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mascota_id INTEGER NOT NULL,
            fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            motivo TEXT NOT NULL DEFAULT '',
            diagnostico TEXT,
            tratamiento_indicado TEXT,
            peso_kg REAL,
            temperatura REAL,
            observaciones TEXT,
            proxima_visita TEXT,
            costo REAL NOT NULL DEFAULT 0,
            usuario_id INTEGER,
            FOREIGN KEY (mascota_id) REFERENCES mascotas(id) ON DELETE CASCADE,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vacunas_mascota (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mascota_id INTEGER NOT NULL,
            vacuna TEXT NOT NULL,
            fecha_aplicacion TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            proxima_dosis TEXT,
            lote TEXT,
            veterinario TEXT,
            observaciones TEXT,
            usuario_id INTEGER,
            FOREIGN KEY (mascota_id) REFERENCES mascotas(id) ON DELETE CASCADE,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tratamientos_mascota (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mascota_id INTEGER NOT NULL,
            tipo TEXT NOT NULL DEFAULT 'Desparasitación',
            producto TEXT NOT NULL DEFAULT '',
            fecha_inicio TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            fecha_fin TEXT,
            dosis TEXT,
            frecuencia TEXT,
            estado TEXT NOT NULL DEFAULT 'Activo' CHECK(estado IN ('Activo', 'Finalizado')),
            observaciones TEXT,
            usuario_id INTEGER,
            FOREIGN KEY (mascota_id) REFERENCES mascotas(id) ON DELETE CASCADE,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    conn.commit()
    conn.close()


def _crear_tablas_restaurante():
    """Tablas del módulo Restaurante/Comedor:
    - rest_platos / rest_receta_ingredientes: el plato y su receta (qué
      insumos del catálogo de Productos consume y en qué cantidad), para
      calcular el costo y el margen de cada plato automáticamente.
    - rest_mesas: las mesas del salón, con su estado.
    - rest_comandas / rest_comanda_items: el pedido de una mesa (o
      delivery/para llevar/mostrador), con sus platos. Al cerrar la
      comanda se genera una venta real (reutilizando models_ventas.
      procesar_venta) y se descuentan los insumos de cada plato del
      inventario (reutilizando productos ya existentes como insumos, sin
      necesidad de una tabla de insumos aparte)."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rest_platos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria TEXT NOT NULL DEFAULT 'Plato Principal',
            precio_venta REAL NOT NULL DEFAULT 0,
            descripcion TEXT,
            tiempo_preparacion_min INTEGER,
            activo INTEGER NOT NULL DEFAULT 1,
            fecha_creacion TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rest_receta_ingredientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plato_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (plato_id) REFERENCES rest_platos(id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rest_mesas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL UNIQUE,
            capacidad INTEGER NOT NULL DEFAULT 4,
            zona TEXT,
            estado TEXT NOT NULL DEFAULT 'Libre' CHECK(estado IN ('Libre','Ocupada','Reservada','Para Limpiar')),
            activa INTEGER NOT NULL DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rest_comandas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mesa_id INTEGER,
            tipo TEXT NOT NULL DEFAULT 'Mesa' CHECK(tipo IN ('Mesa','Delivery','Para Llevar','Mostrador')),
            cliente_id INTEGER,
            mozo_usuario_id INTEGER,
            estado TEXT NOT NULL DEFAULT 'Abierta' CHECK(estado IN ('Abierta','Cerrada','Cancelada')),
            turno TEXT NOT NULL DEFAULT 'Mañana',
            fecha_apertura TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            fecha_cierre TEXT,
            venta_id INTEGER,
            observaciones TEXT,
            FOREIGN KEY (mesa_id) REFERENCES rest_mesas(id) ON DELETE SET NULL,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL,
            FOREIGN KEY (mozo_usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY (venta_id) REFERENCES ventas(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rest_comanda_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comanda_id INTEGER NOT NULL,
            plato_id INTEGER NOT NULL,
            cantidad REAL NOT NULL DEFAULT 1,
            precio_unitario REAL NOT NULL DEFAULT 0,
            estado_cocina TEXT NOT NULL DEFAULT 'Pendiente' CHECK(
                estado_cocina IN ('Pendiente','Preparando','Listo','Entregado','Cancelado')),
            observaciones TEXT,
            fecha_agregado TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (comanda_id) REFERENCES rest_comandas(id) ON DELETE CASCADE,
            FOREIGN KEY (plato_id) REFERENCES rest_platos(id)
        )
    """)

    conn.commit()
    conn.close()


def _crear_tablas_extension_pizzeria():
    """Extiende el módulo Restaurante con lo específico de una pizzería:
    - rest_variantes_plato: tamaños de un plato (Individual/Mediana/
      Familiar, etc.), cada uno con su propio precio y un multiplicador
      que escala la receta base (para calcular costo/consumo de insumos
      correctamente según el tamaño elegido).
    - rest_comanda_item_extras: personalización por pedido — ingredientes
      agregados o quitados en un ítem puntual de una comanda, sin afectar
      la receta base del plato. Los agregados se cobran aparte y también
      se descuentan del inventario al cerrar la comanda.
    - rest_repartidores: personal de delivery.
    - Columnas nuevas en rest_comandas (repartidor, dirección y estado de
      entrega) y en rest_comanda_items (hora de inicio de preparación,
      para poder controlar el tiempo de horneado)."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rest_variantes_plato (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plato_id INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL DEFAULT 0,
            multiplicador_receta REAL NOT NULL DEFAULT 1,
            orden INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (plato_id) REFERENCES rest_platos(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rest_comanda_item_extras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comanda_item_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('Agregado', 'Quitado')),
            cantidad REAL NOT NULL DEFAULT 1,
            costo_extra REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (comanda_item_id) REFERENCES rest_comanda_items(id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rest_repartidores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            vehiculo TEXT,
            activo INTEGER NOT NULL DEFAULT 1
        )
    """)

    columnas_comandas = [
        ("repartidor_id", "INTEGER REFERENCES rest_repartidores(id)"),
        ("direccion_entrega", "TEXT"),
        ("estado_delivery", "TEXT"),  # NULL si no es Delivery; si no, 'Preparando'/'En Camino'/'Entregado'
    ]
    cursor.execute("PRAGMA table_info(rest_comandas)")
    existentes = {f[1] for f in cursor.fetchall()}
    for nombre_col, definicion in columnas_comandas:
        if nombre_col not in existentes:
            cursor.execute(f"ALTER TABLE rest_comandas ADD COLUMN {nombre_col} {definicion}")

    columnas_items = [
        ("variante_id", "INTEGER REFERENCES rest_variantes_plato(id)"),
        ("variante_nombre", "TEXT"),
        ("hora_inicio_preparacion", "TEXT"),
    ]
    cursor.execute("PRAGMA table_info(rest_comanda_items)")
    existentes = {f[1] for f in cursor.fetchall()}
    for nombre_col, definicion in columnas_items:
        if nombre_col not in existentes:
            cursor.execute(f"ALTER TABLE rest_comanda_items ADD COLUMN {nombre_col} {definicion}")

    conn.commit()
    conn.close()


def _crear_tablas_streaming():
    """Tablas del módulo Alquiler de Cuentas de Streaming (Netflix, HBO
    Max, Disney+, YouTube Premium, etc.):
    - stream_plataformas: catálogo de plataformas.
    - stream_cuentas: cada cuenta que el negocio compra (email/contraseña,
      plan, cuántas pantallas/perfiles admite, cuánto cuesta el plan).
    - stream_perfiles: los "cupos" dentro de una cuenta (un perfil de
      Netflix, o el cupo único de una cuenta de 'Acceso Completo').
    - stream_combos / stream_combo_plataformas: paquetes de varias
      plataformas a precio combinado (ej. "Netflix + Disney+").
    - stream_suscripciones / stream_suscripcion_perfiles: qué cliente
      tiene alquilado qué perfil(es), desde cuándo y hasta cuándo.
    - stream_pagos: cada cobro/renovación registrado (vinculado a una
      venta real del sistema, igual que en Veterinaria/Restaurante)."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stream_plataformas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            activa INTEGER NOT NULL DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stream_cuentas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plataforma_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            contrasena TEXT,
            plan_nombre TEXT,
            max_perfiles INTEGER NOT NULL DEFAULT 1,
            costo_mensual REAL NOT NULL DEFAULT 0,
            fecha_compra TEXT NOT NULL DEFAULT (date('now', 'localtime')),
            fecha_proximo_pago_proveedor TEXT,
            fecha_ultimo_cambio_password TEXT NOT NULL DEFAULT (date('now', 'localtime')),
            estado TEXT NOT NULL DEFAULT 'Activa' CHECK(estado IN ('Activa', 'Vencida', 'Suspendida')),
            notas TEXT,
            FOREIGN KEY (plataforma_id) REFERENCES stream_plataformas(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stream_perfiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cuenta_id INTEGER NOT NULL,
            nombre_perfil TEXT NOT NULL,
            pin TEXT,
            estado TEXT NOT NULL DEFAULT 'Libre' CHECK(estado IN ('Libre', 'Ocupado')),
            FOREIGN KEY (cuenta_id) REFERENCES stream_cuentas(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stream_combos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio_mensual REAL NOT NULL DEFAULT 0,
            activo INTEGER NOT NULL DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stream_combo_plataformas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            combo_id INTEGER NOT NULL,
            plataforma_id INTEGER NOT NULL,
            FOREIGN KEY (combo_id) REFERENCES stream_combos(id) ON DELETE CASCADE,
            FOREIGN KEY (plataforma_id) REFERENCES stream_plataformas(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stream_suscripciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            combo_id INTEGER,
            modalidad TEXT NOT NULL DEFAULT 'Perfil Individual' CHECK(
                modalidad IN ('Perfil Individual', 'Acceso Completo', 'Combo')),
            fecha_inicio TEXT NOT NULL DEFAULT (date('now', 'localtime')),
            fecha_vencimiento TEXT NOT NULL,
            precio_mensual REAL NOT NULL DEFAULT 0,
            estado TEXT NOT NULL DEFAULT 'Activa' CHECK(estado IN ('Activa', 'Vencida', 'Cancelada')),
            forma_pago TEXT NOT NULL DEFAULT 'Efectivo',
            dispositivos_conectados INTEGER NOT NULL DEFAULT 1,
            max_dispositivos INTEGER NOT NULL DEFAULT 1,
            notas TEXT,
            fecha_creacion TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (combo_id) REFERENCES stream_combos(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stream_suscripcion_perfiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            suscripcion_id INTEGER NOT NULL,
            perfil_id INTEGER NOT NULL,
            FOREIGN KEY (suscripcion_id) REFERENCES stream_suscripciones(id) ON DELETE CASCADE,
            FOREIGN KEY (perfil_id) REFERENCES stream_perfiles(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stream_pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            suscripcion_id INTEGER NOT NULL,
            fecha_pago TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            periodo_desde TEXT NOT NULL,
            periodo_hasta TEXT NOT NULL,
            monto REAL NOT NULL DEFAULT 0,
            venta_id INTEGER,
            usuario_id INTEGER,
            FOREIGN KEY (suscripcion_id) REFERENCES stream_suscripciones(id) ON DELETE CASCADE,
            FOREIGN KEY (venta_id) REFERENCES ventas(id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    conn.commit()

    # Sembramos las plataformas más comunes, para no arrancar de cero
    # (el usuario puede agregar o quitar las que quiera desde la UI).
    plataformas_iniciales = ["Netflix", "HBO Max", "Disney+", "YouTube Premium",
                             "Spotify", "Amazon Prime Video", "Star+", "Paramount+"]
    for nombre in plataformas_iniciales:
        cursor.execute("INSERT OR IGNORE INTO stream_plataformas (nombre) VALUES (?)", (nombre,))
    conn.commit()
    conn.close()


def _crear_tablas_juegos():
    """Tablas del módulo 'Juegos y Entretenimiento': historial de puntajes
    obtenidos por cada usuario en cada uno de los juegos disponibles
    (Solitario, Buscaminas, Tetris, Snake, Pong, Pac-Man)."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS juegos_puntajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            usuario_nombre TEXT NOT NULL,
            juego TEXT NOT NULL,
            puntaje INTEGER NOT NULL DEFAULT 0,
            detalle TEXT,
            fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_juegos_puntajes_juego ON juegos_puntajes(juego)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_juegos_puntajes_usuario ON juegos_puntajes(usuario_id)")

    conn.commit()
    conn.close()


def _crear_tablas_biblia():
    """Tabla de caché del módulo 'Biblia': guarda localmente el texto de
    cada libro ya descargado de Internet, para poder seguir leyendo sin
    conexión luego de la primera descarga."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS biblia_cache (
            libro TEXT PRIMARY KEY,
            contenido TEXT NOT NULL,
            fecha_descarga TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)

    conn.commit()
    conn.close()


def _crear_tablas_importacion():
    """Tablas del módulo 'Importaciones': compras hechas en plataformas del
    exterior (eBay, AliExpress, Temu, Shein, Alibaba, Made-in-China, etc.)
    que llegan en caja a un casillero (Miami o Shenzhen) antes de venir a
    Paraguay.

    - import_couriers: empresas de courier/casillero, con su tarifa por
      kilo vía aérea y vía marítima, para calcular el flete automáticamente
      a partir del peso de la caja.
    - import_plataformas: tiendas/plataformas del exterior donde se compra
      (eBay, AliExpress, Amazon, etc.), editable desde la interfaz para
      poder agregar nuevas tiendas sin tocar código.
    - import_configuracion: fila única con el tipo de cambio US$ → Gs.
      usado para mostrar todos los montos también en guaraníes.
    - import_compras: cabecera de cada compra/caja (plataforma, fechas,
      courier, casillero, peso, tipo de envío, costo de envío total).
    - import_detalle: cada producto dentro de la caja, con su cantidad,
      costo unitario pagado en la plataforma, y el costo de envío que le
      corresponde (repartido proporcionalmente entre todas las unidades
      de la caja), más el precio de venta al público y la ganancia.
    """
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS import_couriers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT,
            ruc TEXT,
            telefono TEXT,
            costo_kg_aereo REAL NOT NULL DEFAULT 0,
            costo_kg_maritimo REAL NOT NULL DEFAULT 0,
            direccion_casillero_miami TEXT,
            direccion_casillero_shenzhen TEXT,
            notas TEXT,
            activo INTEGER NOT NULL DEFAULT 1,
            fecha_creacion TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS import_plataformas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            activa INTEGER NOT NULL DEFAULT 1,
            fecha_creacion TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS import_configuracion (
            id INTEGER PRIMARY KEY CHECK(id = 1),
            tasa_cambio_usd_gs REAL NOT NULL DEFAULT 7300,
            fecha_actualizacion TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS import_compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plataforma TEXT NOT NULL,
            referencia TEXT,
            courier_id INTEGER,
            casillero TEXT NOT NULL DEFAULT 'Miami, FL (EE.UU.)',
            tipo_envio TEXT NOT NULL DEFAULT 'Aéreo' CHECK(tipo_envio IN ('Aéreo', 'Marítimo')),
            peso_caja_kg REAL NOT NULL DEFAULT 0,
            costo_envio_manual REAL,
            costo_envio_total REAL NOT NULL DEFAULT 0,
            estado TEXT NOT NULL DEFAULT 'Pendiente' CHECK(estado IN (
                'Pendiente', 'Comprado', 'En camino al casillero', 'En casillero',
                'En camino a Paraguay', 'Recibido')),
            fecha_compra TEXT NOT NULL DEFAULT (date('now', 'localtime')),
            fecha_envio_casillero TEXT,
            fecha_recepcion TEXT,
            notas TEXT,
            usuario_id INTEGER,
            fecha_registro TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (courier_id) REFERENCES import_couriers(id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS import_detalle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            compra_id INTEGER NOT NULL,
            producto_nombre TEXT NOT NULL,
            cantidad REAL NOT NULL DEFAULT 1 CHECK(cantidad > 0),
            costo_unitario_compra REAL NOT NULL DEFAULT 0,
            costo_envio_unitario REAL NOT NULL DEFAULT 0,
            costo_total_unitario REAL NOT NULL DEFAULT 0,
            precio_venta_publico REAL,
            producto_id_generado INTEGER,
            enviado_inventario INTEGER NOT NULL DEFAULT 0,
            notas TEXT,
            FOREIGN KEY (compra_id) REFERENCES import_compras(id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id_generado) REFERENCES productos(id)
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_import_detalle_compra ON import_detalle(compra_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_import_compras_courier ON import_compras(courier_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_import_compras_estado ON import_compras(estado)")

    conn.commit()

    # Sembramos las tiendas más comunes, para no arrancar de cero (el
    # usuario puede agregar o desactivar las que quiera desde la UI).
    plataformas_iniciales = ["eBay", "AliExpress", "Temu", "Shein", "Alibaba",
                              "Made in China", "Amazon", "Otro"]
    for nombre in plataformas_iniciales:
        cursor.execute("INSERT OR IGNORE INTO import_plataformas (nombre) VALUES (?)", (nombre,))

    # Fila única de configuración (tipo de cambio). El valor por defecto es
    # solo un punto de partida razonable; el usuario lo puede editar a mano
    # o actualizar automáticamente desde el Dashboard del módulo.
    cursor.execute("INSERT OR IGNORE INTO import_configuracion (id, tasa_cambio_usd_gs) VALUES (1, 7300)")

    conn.commit()

    conn.commit()
    conn.close()
