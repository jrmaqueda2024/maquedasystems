"""
models_catalogo.py
Funciones de negocio para el catálogo: Productos, Marcas, Categorías y Proveedores.
"""
from database import conectar


# ---------------- MARCAS ----------------
def listar_marcas() -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM marcas ORDER BY nombre")
    filas = cursor.fetchall()
    conn.close()
    return [{"id": f[0], "nombre": f[1]} for f in filas]


def crear_marca(nombre: str) -> tuple[bool, str]:
    if not nombre.strip():
        return False, "El nombre no puede estar vacío."
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO marcas (nombre) VALUES (?)", (nombre.strip(),))
        conn.commit()
        return True, "Marca creada."
    except Exception:
        return False, "Esa marca ya existe."
    finally:
        conn.close()


def editar_marca(marca_id: int, nombre: str) -> tuple[bool, str]:
    if not nombre.strip():
        return False, "El nombre no puede estar vacío."
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE marcas SET nombre = ? WHERE id = ?", (nombre.strip(), marca_id))
        conn.commit()
        return True, "Marca actualizada."
    except Exception:
        return False, "Esa marca ya existe."
    finally:
        conn.close()


def marca_en_uso(marca_id: int) -> bool:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM productos WHERE marca_id = ?", (marca_id,))
    en_uso = cursor.fetchone()[0] > 0
    conn.close()
    return en_uso


def eliminar_marca(marca_id: int) -> tuple[bool, str]:
    if marca_en_uso(marca_id):
        return False, "No se puede eliminar: hay productos asociados a esta marca."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM marcas WHERE id = ?", (marca_id,))
    conn.commit()
    conn.close()
    return True, "Marca eliminada."


# ---------------- CATEGORÍAS ----------------
def listar_categorias() -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM categorias ORDER BY nombre")
    filas = cursor.fetchall()
    conn.close()
    return [{"id": f[0], "nombre": f[1]} for f in filas]


def crear_categoria(nombre: str) -> tuple[bool, str]:
    if not nombre.strip():
        return False, "El nombre no puede estar vacío."
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre.strip(),))
        conn.commit()
        return True, "Categoría creada."
    except Exception:
        return False, "Esa categoría ya existe."
    finally:
        conn.close()


def editar_categoria(categoria_id: int, nombre: str) -> tuple[bool, str]:
    if not nombre.strip():
        return False, "El nombre no puede estar vacío."
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE categorias SET nombre = ? WHERE id = ?", (nombre.strip(), categoria_id))
        conn.commit()
        return True, "Categoría actualizada."
    except Exception:
        return False, "Esa categoría ya existe."
    finally:
        conn.close()


def categoria_en_uso(categoria_id: int) -> bool:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM productos WHERE categoria_id = ?", (categoria_id,))
    en_uso = cursor.fetchone()[0] > 0
    conn.close()
    return en_uso


def eliminar_categoria(categoria_id: int) -> tuple[bool, str]:
    if categoria_en_uso(categoria_id):
        return False, "No se puede eliminar: hay productos asociados a esta categoría."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categorias WHERE id = ?", (categoria_id,))
    conn.commit()
    conn.close()
    return True, "Categoría eliminada."


# ---------------- PROVEEDORES ----------------
def listar_proveedores(texto_busqueda: str = "") -> list[dict]:
    conn = conectar()
    cursor = conn.cursor()
    if texto_busqueda.strip():
        patron = f"%{texto_busqueda.strip()}%"
        cursor.execute(
            """SELECT id, nombre, telefono, direccion, ruc, contacto FROM proveedores
               WHERE nombre LIKE ? OR ruc LIKE ? OR contacto LIKE ?
               ORDER BY nombre""",
            (patron, patron, patron),
        )
    else:
        cursor.execute("SELECT id, nombre, telefono, direccion, ruc, contacto FROM proveedores ORDER BY nombre")
    filas = cursor.fetchall()
    conn.close()
    return [
        {"id": f[0], "nombre": f[1], "telefono": f[2], "direccion": f[3], "ruc": f[4], "contacto": f[5]}
        for f in filas
    ]


def crear_proveedor(nombre: str, telefono: str = "", direccion: str = "", ruc: str = "",
                     contacto: str = "") -> tuple[bool, str]:
    if not nombre.strip():
        return False, "El nombre del proveedor es obligatorio."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO proveedores (nombre, telefono, direccion, ruc, contacto) VALUES (?, ?, ?, ?, ?)",
        (nombre.strip(), telefono.strip(), direccion.strip(), ruc.strip(), contacto.strip()),
    )
    conn.commit()
    conn.close()
    return True, "Proveedor creado."


def editar_proveedor(proveedor_id: int, nombre: str, telefono: str = "", direccion: str = "",
                      ruc: str = "", contacto: str = "") -> tuple[bool, str]:
    if not nombre.strip():
        return False, "El nombre del proveedor es obligatorio."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE proveedores SET nombre = ?, telefono = ?, direccion = ?, ruc = ?, contacto = ? WHERE id = ?",
        (nombre.strip(), telefono.strip(), direccion.strip(), ruc.strip(), contacto.strip(), proveedor_id),
    )
    conn.commit()
    conn.close()
    return True, "Proveedor actualizado."


def proveedor_en_uso(proveedor_id: int) -> bool:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM productos WHERE proveedor_id = ?", (proveedor_id,))
    en_productos = cursor.fetchone()[0] > 0
    cursor.execute("SELECT COUNT(*) FROM compras WHERE proveedor_id = ?", (proveedor_id,))
    en_compras = cursor.fetchone()[0] > 0
    conn.close()
    return en_productos or en_compras


def eliminar_proveedor(proveedor_id: int) -> tuple[bool, str]:
    if proveedor_en_uso(proveedor_id):
        return False, "No se puede eliminar: hay productos o compras asociados a este proveedor."
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM proveedores WHERE id = ?", (proveedor_id,))
    conn.commit()
    conn.close()
    return True, "Proveedor eliminado."


# ---------------- PRODUCTOS ----------------
def listar_productos(solo_activos: bool = True, texto_busqueda: str = "",
                      proveedor_id: int | None = None, marca_id: int | None = None,
                      categoria_id: int | None = None) -> list[dict]:
    """Devuelve productos con info de marca y proveedor (joins), filtrando por
    activos/inactivos, por texto de búsqueda en código o descripción, y
    opcionalmente por proveedor, marca y/o categoría (se pueden combinar
    los tres filtros con el texto de búsqueda al mismo tiempo)."""
    conn = conectar()
    cursor = conn.cursor()

    condiciones = []
    parametros = []
    if solo_activos:
        condiciones.append("p.activo = 1")
    if texto_busqueda.strip():
        condiciones.append("(p.nombre LIKE ? OR CAST(p.id AS TEXT) LIKE ? OR p.codigo_barras LIKE ? OR p.codigo_secundario LIKE ?)")
        comodin = f"%{texto_busqueda.strip()}%"
        parametros.extend([comodin, comodin, comodin, comodin])
    if proveedor_id:
        condiciones.append("p.proveedor_id = ?")
        parametros.append(proveedor_id)
    if marca_id:
        condiciones.append("p.marca_id = ?")
        parametros.append(marca_id)
    if categoria_id:
        condiciones.append("p.categoria_id = ?")
        parametros.append(categoria_id)

    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    cursor.execute(f"""
        SELECT p.id, p.nombre, m.nombre, p.precio_compra, p.precio, p.precio_credito,
               p.precio_mayorista, p.stock, p.comprometido, p.stock_minimo,
               p.activo, p.categoria_id, p.marca_id, p.proveedor_id, pr.nombre,
               p.codigo_secundario, p.codigo_barras, p.unidad_medida, p.tipo_impuesto,
               p.tipo_producto, p.control_stock, p.imagen_ruta, c.nombre, p.es_articulo_comun
        FROM productos p
        LEFT JOIN marcas m ON p.marca_id = m.id
        LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
        LEFT JOIN categorias c ON p.categoria_id = c.id
        {where}
        ORDER BY p.nombre
    """, parametros)
    filas = cursor.fetchall()
    conn.close()

    resultado = []
    for f in filas:
        stock = f[7] or 0
        comprometido = f[8] or 0
        es_ilimitado = (f[20] or "Cantidad") == "Ilimitado"
        resultado.append({
            "id": f[0],
            "nombre": f[1],
            "marca": f[2] or "",
            "precio_compra": f[3] or 0,
            "precio_venta": f[4] or 0,
            "precio_credito": f[5] or 0,
            "precio_mayorista": f[6] or 0,
            "stock": stock,
            "comprometido": comprometido,
            "disponible": "Ilimitado" if es_ilimitado else stock - comprometido,
            "stock_minimo": f[9] or 0,
            "activo": bool(f[10]),
            "categoria_id": f[11],
            "marca_id": f[12],
            "proveedor_id": f[13],
            "proveedor": f[14] or "",
            "codigo_secundario": f[15] or "",
            "codigo_barras": f[16] or "",
            "unidad_medida": f[17] or "Unidad",
            "tipo_impuesto": f[18] or "IVA 10%",
            "tipo_producto": f[19] or "Producto",
            "control_stock": f[20] or "Cantidad",
            "imagen_ruta": f[21] or "",
            "categoria": f[22] or "",
            "es_articulo_comun": bool(f[23]),
        })
    return resultado


def listar_articulos_comunes() -> list[dict]:
    """Productos marcados como 'Artículo Común' (para Ctrl+P en Ventas)."""
    return [p for p in listar_productos(solo_activos=True) if p["es_articulo_comun"]]


def obtener_producto(producto_id: int) -> dict | None:
    productos = [p for p in listar_productos(solo_activos=False) if p["id"] == producto_id]
    return productos[0] if productos else None


def buscar_producto_por_codigo(codigo: str) -> dict | None:
    """Busca un único producto para la pantalla de Ventas al escanear con
    lector de código de barras o al escribir el código y presionar Enter.

    Prioridad de búsqueda:
      1) Coincidencia exacta con el 'Código de Barras' registrado en el
         producto (lo que carga un lector de código de barras real).
      2) Coincidencia exacta con el 'Código Secundario'.
      3) Si lo escrito es numérico, coincidencia con el ID interno del
         sistema (código manual de toda la vida, ej. escribir '15' y Enter).
    """
    codigo = codigo.strip()
    if not codigo:
        return None

    productos = listar_productos(solo_activos=False)

    for p in productos:
        if p["codigo_barras"] and p["codigo_barras"] == codigo:
            return p
    for p in productos:
        if p["codigo_secundario"] and p["codigo_secundario"] == codigo:
            return p
    try:
        producto_id = int(codigo)
    except ValueError:
        return None
    for p in productos:
        if p["id"] == producto_id:
            return p
    return None


def _validar_codigo_unico(cursor, campo: str, valor: str, producto_id: int = None) -> bool:
    """Devuelve True si el valor es único (o vacío). producto_id se excluye de la
    comparación para permitir guardar sin cambios en una edición."""
    if not valor or not valor.strip():
        return True
    if producto_id is None:
        cursor.execute(f"SELECT COUNT(*) FROM productos WHERE {campo} = ?", (valor.strip(),))
    else:
        cursor.execute(f"SELECT COUNT(*) FROM productos WHERE {campo} = ? AND id != ?", (valor.strip(), producto_id))
    return cursor.fetchone()[0] == 0


def crear_producto(nombre: str, precio_compra: float, precio_venta: float,
                    precio_credito: float, precio_mayorista: float, stock: float,
                    stock_minimo: float = 0, marca_id: int = None,
                    categoria_id: int = None, proveedor_id: int = None,
                    codigo_secundario: str = "", codigo_barras: str = "",
                    unidad_medida: str = "Unidad", tipo_impuesto: str = "IVA 10%",
                    tipo_producto: str = "Producto", control_stock: str = "Cantidad",
                    imagen_ruta: str = "", es_articulo_comun: bool = False,
                    usuario_id: int = None) -> tuple[bool, str, int | None]:
    if not nombre.strip():
        return False, "La descripción del producto es obligatoria.", None
    if precio_venta < 0 or precio_compra < 0:
        return False, "Los precios no pueden ser negativos.", None

    conn = conectar()
    cursor = conn.cursor()

    if not _validar_codigo_unico(cursor, "codigo_secundario", codigo_secundario):
        conn.close()
        return False, "Ese código secundario ya está en uso por otro producto.", None
    if not _validar_codigo_unico(cursor, "codigo_barras", codigo_barras):
        conn.close()
        return False, "Ese código de barras ya está en uso por otro producto.", None

    cursor.execute("""
        INSERT INTO productos (nombre, precio, stock, activo, marca_id, categoria_id,
                                proveedor_id, precio_compra, precio_credito,
                                precio_mayorista, stock_minimo, comprometido,
                                codigo_secundario, codigo_barras, unidad_medida,
                                tipo_impuesto, tipo_producto, control_stock, imagen_ruta,
                                es_articulo_comun)
        VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (nombre.strip(), precio_venta, stock, marca_id, categoria_id, proveedor_id,
          precio_compra, precio_credito, precio_mayorista, stock_minimo,
          codigo_secundario.strip() or None, codigo_barras.strip() or None,
          unidad_medida, tipo_impuesto, tipo_producto, control_stock, imagen_ruta or None,
          1 if es_articulo_comun else 0))
    nuevo_id = cursor.lastrowid

    # Si el producto se crea con stock inicial mayor a cero, dejamos
    # registro de ello en el historial de movimientos de inventario,
    # para que el historial arranque desde el momento exacto en que se
    # dio de alta el producto (y no aparezca "vacío" pese a tener stock).
    # Cuando el control de stock es "Ilimitado" no hay una cantidad real
    # que registrar (ese producto no descuenta inventario), pero igual se
    # deja constancia de la carga inicial marcada como "Ilimitado", para
    # que el historial de ese artículo no empiece vacío.
    if tipo_producto != "Servicio":
        from models_inventario import registrar_movimiento_externo
        if control_stock == "Ilimitado":
            registrar_movimiento_externo(
                cursor, nuevo_id, "entrada", 1, "Stock Inicial",
                usuario_id=usuario_id, stock_resultante=None, es_ilimitado=True,
            )
        elif stock and stock > 0:
            registrar_movimiento_externo(
                cursor, nuevo_id, "entrada", stock, "Stock Inicial",
                usuario_id=usuario_id, stock_resultante=stock,
            )

    conn.commit()
    conn.close()
    return True, "Producto creado correctamente.", nuevo_id


def editar_producto(producto_id: int, nombre: str, precio_compra: float, precio_venta: float,
                     precio_credito: float, precio_mayorista: float, stock: float,
                     stock_minimo: float = 0, marca_id: int = None,
                     categoria_id: int = None, proveedor_id: int = None,
                     codigo_secundario: str = "", codigo_barras: str = "",
                     unidad_medida: str = "Unidad", tipo_impuesto: str = "IVA 10%",
                     tipo_producto: str = "Producto", control_stock: str = "Cantidad",
                     imagen_ruta: str = None, es_articulo_comun: bool = False,
                     usuario_id: int = None) -> tuple[bool, str]:
    if not nombre.strip():
        return False, "La descripción del producto es obligatoria."

    conn = conectar()
    cursor = conn.cursor()

    if not _validar_codigo_unico(cursor, "codigo_secundario", codigo_secundario, producto_id):
        conn.close()
        return False, "Ese código secundario ya está en uso por otro producto."
    if not _validar_codigo_unico(cursor, "codigo_barras", codigo_barras, producto_id):
        conn.close()
        return False, "Ese código de barras ya está en uso por otro producto."

    # Si imagen_ruta es None, no se modifica la imagen ya guardada
    if imagen_ruta is None:
        cursor.execute("SELECT imagen_ruta FROM productos WHERE id = ?", (producto_id,))
        fila = cursor.fetchone()
        imagen_ruta = fila[0] if fila else None

    # Capturamos el stock ANTES de actualizar, para poder detectar si el
    # usuario lo cambió manualmente desde este formulario y, en ese caso,
    # dejar registro en el historial de movimientos de inventario.
    cursor.execute("SELECT stock FROM productos WHERE id = ?", (producto_id,))
    fila_stock = cursor.fetchone()
    stock_anterior = (fila_stock[0] or 0) if fila_stock else 0

    cursor.execute("""
        UPDATE productos
        SET nombre = ?, precio_compra = ?, precio = ?, precio_credito = ?,
            precio_mayorista = ?, stock = ?, stock_minimo = ?, marca_id = ?,
            categoria_id = ?, proveedor_id = ?, codigo_secundario = ?, codigo_barras = ?,
            unidad_medida = ?, tipo_impuesto = ?, tipo_producto = ?, control_stock = ?,
            imagen_ruta = ?, es_articulo_comun = ?
        WHERE id = ?
    """, (nombre.strip(), precio_compra, precio_venta, precio_credito, precio_mayorista,
          stock, stock_minimo, marca_id, categoria_id, proveedor_id,
          codigo_secundario.strip() or None, codigo_barras.strip() or None,
          unidad_medida, tipo_impuesto, tipo_producto, control_stock, imagen_ruta,
          1 if es_articulo_comun else 0, producto_id))

    diferencia = (stock or 0) - stock_anterior
    if diferencia != 0 and tipo_producto != "Servicio" and control_stock != "Ilimitado":
        from models_inventario import registrar_movimiento_externo
        tipo_mov = "entrada" if diferencia > 0 else "salida"
        registrar_movimiento_externo(
            cursor, producto_id, tipo_mov, abs(diferencia),
            "Ajuste Manual (Editar Producto)", usuario_id, stock,
        )

    conn.commit()
    conn.close()
    return True, "Producto actualizado."


def cambiar_codigo_producto(producto_id: int, nuevo_codigo: int) -> tuple[bool, str]:
    """Herramienta 'Cambiar Código' de la pestaña Datos: reasigna el ID (código
    principal) de un producto a otro número, siempre que no esté ya en uso.
    Actualiza también las tablas relacionadas (detalle_ventas, detalle_compras,
    movimientos_inventario) para no romper la integridad referencial."""
    if nuevo_codigo == producto_id:
        return False, "El nuevo código es igual al actual."

    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM productos WHERE id = ?", (nuevo_codigo,))
        if cursor.fetchone()[0] > 0:
            return False, f"El código {nuevo_codigo} ya está en uso por otro producto."

        # Se desactiva temporalmente la verificación de llaves foráneas para poder
        # reordenar el id y sus referencias dentro de una misma transacción segura.
        cursor.execute("PRAGMA foreign_keys = OFF")

        cursor.execute("UPDATE productos SET id = ? WHERE id = ?", (nuevo_codigo, producto_id))
        cursor.execute("UPDATE detalle_ventas SET producto_id = ? WHERE producto_id = ?", (nuevo_codigo, producto_id))
        cursor.execute("UPDATE detalle_compras SET producto_id = ? WHERE producto_id = ?", (nuevo_codigo, producto_id))
        cursor.execute("UPDATE movimientos_inventario SET producto_id = ? WHERE producto_id = ?", (nuevo_codigo, producto_id))

        conn.commit()
        cursor.execute("PRAGMA foreign_keys = ON")
        return True, "Código actualizado correctamente."
    except Exception as e:
        conn.rollback()
        return False, f"No se pudo cambiar el código: {e}"
    finally:
        conn.close()


def producto_tiene_movimientos(producto_id: int) -> bool:
    """Indica si el producto ya tiene ventas o compras registradas (para advertir
    antes de cambios sensibles como cambiar el código o el tipo)."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM detalle_ventas WHERE producto_id = ?", (producto_id,))
    en_ventas = cursor.fetchone()[0] > 0
    cursor.execute("SELECT COUNT(*) FROM detalle_compras WHERE producto_id = ?", (producto_id,))
    en_compras = cursor.fetchone()[0] > 0
    conn.close()
    return en_ventas or en_compras


def cambiar_estado_producto(producto_id: int, activo: bool) -> tuple[bool, str]:
    """Activa o desactiva un producto. Para DESACTIVAR, exige que el stock
    y lo comprometido estén en cero (hay que darle salida de inventario
    antes), evitando que un producto con existencias quede oculto del
    sistema sin haberse descargado correctamente."""
    conn = conectar()
    cursor = conn.cursor()

    if not activo:
        cursor.execute(
            "SELECT stock, comprometido, nombre FROM productos WHERE id = ?",
            (producto_id,),
        )
        fila = cursor.fetchone()
        if fila is None:
            conn.close()
            return False, "El producto no existe."
        stock, comprometido, nombre = fila
        stock = stock or 0
        comprometido = comprometido or 0
        if stock != 0:
            conn.close()
            return False, (
                f"No se puede desactivar '{nombre}': todavía tiene {stock:g} "
                "unidad(es) en stock. Registra una Salida de Inventario hasta "
                "dejarlo en cero antes de desactivarlo."
            )
        if comprometido != 0:
            conn.close()
            return False, (
                f"No se puede desactivar '{nombre}': tiene {comprometido:g} "
                "unidad(es) comprometidas en ventas pendientes."
            )

    cursor.execute("UPDATE productos SET activo = ? WHERE id = ?", (1 if activo else 0, producto_id))
    conn.commit()
    conn.close()
    return True, "Estado actualizado."


def puede_eliminarse_producto(producto_id: int) -> tuple[bool, str]:
    """Verifica las condiciones para poder eliminar definitivamente un
    producto, sin borrar nada todavía. Reglas:
      1. El producto debe estar INACTIVO (desactivado primero).
      2. Su stock disponible debe estar en CERO (hay que darle salida antes).
      3. Si ya fue vendido, se permite igual: la venta queda intacta porque
         detalle_ventas guarda el nombre/precio de la línea independiente
         del producto, y solo se elimina la fila de 'productos'.
    Devuelve (puede, motivo_si_no_puede)."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT activo, stock, comprometido, nombre FROM productos WHERE id = ?",
        (producto_id,),
    )
    fila = cursor.fetchone()
    conn.close()

    if fila is None:
        return False, "El producto no existe."

    activo, stock, comprometido, nombre = fila
    stock = stock or 0
    comprometido = comprometido or 0

    if activo:
        return False, "Primero debes desactivar el producto antes de poder eliminarlo."
    if stock != 0:
        return False, (
            f"El producto todavía tiene {stock:g} unidad(es) en stock. "
            "Registra una Salida de Inventario hasta dejarlo en cero antes de eliminarlo."
        )
    if comprometido != 0:
        return False, (
            f"El producto tiene {comprometido:g} unidad(es) comprometidas en ventas pendientes. "
            "Resuelve esas ventas antes de eliminarlo."
        )
    return True, ""


def eliminar_producto(producto_id: int) -> tuple[bool, str]:
    """Elimina definitivamente un producto de la base de datos, liberando
    el espacio que ocupaba para que el sistema lo pueda reutilizar.

    Condiciones obligatorias (ver puede_eliminarse_producto):
      - El producto debe estar inactivo.
      - Su stock y lo comprometido deben estar en cero.

    El historial se preserva siempre:
      - Las ventas ya registradas (detalle_ventas) NO se tocan ni se ven
        afectadas: la línea de venta guarda su propio nombre/precio y
        seguirá mostrándose igual aunque el producto ya no exista.
      - Los movimientos de inventario (entradas/salidas) NO se borran: se
        desvinculan del producto (producto_id = NULL) pero conservan el
        nombre del producto en 'producto_nombre_historico', para que el
        historial general de movimientos de inventario siga siendo legible.
    """
    puede, motivo = puede_eliminarse_producto(producto_id)
    if not puede:
        return False, motivo

    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT nombre FROM productos WHERE id = ?", (producto_id,))
        fila = cursor.fetchone()
        nombre_producto = fila[0] if fila else ""

        # Desvincular (no borrar) las líneas de venta históricas: se les
        # asigna producto_id = NULL pero se rellena descripcion_libre con
        # el nombre del producto eliminado. Todos los reportes y vistas de
        # detalle ya usan COALESCE(p.nombre, dv.descripcion_libre), así que
        # la venta sigue mostrando el nombre correcto sin ningún cambio.
        cursor.execute("""
            UPDATE detalle_ventas
            SET producto_id = NULL,
                descripcion_libre = COALESCE(NULLIF(descripcion_libre, ''), ?)
            WHERE producto_id = ?
        """, (nombre_producto, producto_id))

        # Desvincular (no borrar) los movimientos de inventario históricos,
        # preservando el nombre del producto como referencia textual.
        cursor.execute("""
            UPDATE movimientos_inventario
            SET producto_id = NULL, producto_nombre_historico = ?
            WHERE producto_id = ?
        """, (nombre_producto, producto_id))

        # Desvincular (no borrar) las líneas de compras históricas.
        cursor.execute("""
            UPDATE detalle_compras
            SET producto_id = NULL, producto_nombre_historico = ?
            WHERE producto_id = ?
        """, (nombre_producto, producto_id))

        # Desvincular (no borrar) las devoluciones históricas.
        cursor.execute("""
            UPDATE devoluciones
            SET producto_id = NULL, producto_nombre_historico = ?
            WHERE producto_id = ?
        """, (nombre_producto, producto_id))

        cursor.execute("DELETE FROM productos WHERE id = ?", (producto_id,))

        conn.commit()
        return True, f"Producto '{nombre_producto}' eliminado definitivamente. Su historial de ventas y movimientos se conservó."
    except Exception as e:
        conn.rollback()
        return False, f"No se pudo eliminar el producto: {e}"
    finally:
        conn.close()


def productos_bajo_stock_minimo() -> list[dict]:
    """Para el filtro 'Mostrar Productos Bajos en Inventario' del módulo Inventario."""
    return [p for p in listar_productos() if p["stock"] <= p["stock_minimo"]]


def resumen_inventario() -> dict:
    """Calcula los totales del panel 'Resumen de Inventario', separados
    individualmente por cada unidad de medida (Unidad, Caja, Paquete,
    Docena, Kilogramo, Litro, Metro, o cualquier otra que se use), en vez
    de agruparlas en dos grandes bloques."""
    orden_unidades = ["Unidad", "Kilogramo", "Litro", "Metro", "Caja", "Paquete", "Docena"]
    por_unidad = {u: {"cantidad": 0, "valor_compra": 0, "valor_venta": 0} for u in orden_unidades}

    productos = listar_productos()
    for p in productos:
        if p["tipo_producto"] == "Servicio":
            continue
        stock = p.get("stock", 0) or 0
        unidad = p.get("unidad_medida") or "Unidad"
        if unidad not in por_unidad:
            por_unidad[unidad] = {"cantidad": 0, "valor_compra": 0, "valor_venta": 0}
            orden_unidades.append(unidad)
        por_unidad[unidad]["cantidad"]      += stock
        por_unidad[unidad]["valor_compra"]  += stock * p["precio_compra"]
        por_unidad[unidad]["valor_venta"]   += stock * p["precio_venta"]

    cantidad_total = sum(v["cantidad"] for v in por_unidad.values())
    valor_total_compra = sum(v["valor_compra"] for v in por_unidad.values())

    return {
        # Desglose individual por unidad, en el orden en que deben mostrarse
        "por_unidad": por_unidad,
        "orden_unidades": orden_unidades,
        # Totales globales (compatibilidad con reportes_datos.py / reporte_inventario_pdf.py)
        "cantidad_total":     cantidad_total,
        "valor_inventario":   valor_total_compra,
        "valor_comprometido": 0,
    }


def registrar_producto_comun_rapido(nombre: str, precio_unitario: float) -> tuple[bool, str, dict | None]:
    """Crea (o reutiliza) un producto rápido para el diálogo 'Producto Común'
    (Ctrl+P) en Ventas: el cajero escribe libremente la descripción y el
    precio unitario, sin tener que pasar antes por el alta completa de
    productos. Se guarda como tipo_producto='Servicio' y
    control_stock='Ilimitado' para que nunca valide ni descuente stock.

    Si ya existe un producto activo con el mismo nombre (sin importar
    mayúsculas/espacios) creado por esta vía, se reutiliza y se actualiza
    su precio al ingresado, en vez de crear un duplicado.

    Devuelve (exito, mensaje, producto) donde 'producto' ya viene con el
    shape esperado por la pantalla de Ventas (el mismo dict de listar_productos).
    """
    nombre = nombre.strip()
    if not nombre:
        return False, "La descripción del producto es obligatoria.", None
    if precio_unitario is None or precio_unitario < 0:
        return False, "El precio unitario no puede ser negativo.", None

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM productos
        WHERE activo = 1 AND tipo_producto = 'Servicio' AND control_stock = 'Ilimitado'
              AND LOWER(TRIM(nombre)) = LOWER(?)
        LIMIT 1
    """, (nombre,))
    fila = cursor.fetchone()

    if fila:
        producto_id = fila[0]
        cursor.execute("""
            UPDATE productos SET precio = ?, precio_compra = ?, precio_credito = ?,
                                  precio_mayorista = ?
            WHERE id = ?
        """, (precio_unitario, precio_unitario, precio_unitario, precio_unitario, producto_id))
        conn.commit()
        conn.close()
        producto = obtener_producto(producto_id)
        return True, "Producto común actualizado.", producto

    conn.close()
    ok, msg, nuevo_id = crear_producto(
        nombre=nombre, precio_compra=precio_unitario, precio_venta=precio_unitario,
        precio_credito=precio_unitario, precio_mayorista=precio_unitario, stock=0,
        tipo_producto="Servicio", control_stock="Ilimitado", es_articulo_comun=True,
    )
    if not ok:
        return False, msg, None
    return True, "Producto común creado.", obtener_producto(nuevo_id)


def top_productos_por_valor_inventario(limite: int = 10) -> list[dict]:
    """Ranking de productos con mayor valor de inventario (stock × precio de
    compra), usado en el Reporte General de Inventario."""
    productos = listar_productos()
    con_valor = [
        {
            "nombre": p["nombre"],
            "stock": p["stock"],
            "precio_compra": p["precio_compra"],
            "valor": p["stock"] * p["precio_compra"],
        }
        for p in productos if p["tipo_producto"] != "Servicio"
    ]
    con_valor.sort(key=lambda x: x["valor"], reverse=True)
    return con_valor[:limite]
