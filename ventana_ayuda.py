"""
ventana_ayuda.py
Módulo de Ayuda: explica el funcionamiento de cada módulo del sistema,
sus atajos de teclado y las funciones disponibles. Pensado como
referencia rápida para cualquier usuario, con un árbol de temas a la
izquierda, contenido detallado a la derecha, y un buscador que filtra
los temas por palabra clave.

Accesible para todos los usuarios (no está en MODULOS_SOLO_ADMIN), pero
cada usuario solo ve en el árbol los temas de los módulos a los que
tiene acceso según sus permisos.
"""
import tkinter as tk
from tkinter import ttk
from utilidades_ui import habilitar_deseleccion_treeview
from traducciones import t

AZUL        = "#1d5fd6"
AZUL_OSC    = "#163d8c"
GRIS_FONDO  = "#f4f5f7"
GRIS_BORDE  = "#e2e8f0"
BLANCO      = "#ffffff"
VERDE       = "#16a34a"
ROJO        = "#dc2626"
NARANJA     = "#d97706"
GRIS_TEXTO  = "#6b7280"
NEGRO       = "#1e293b"


# ─────────────────────────────────────────────────────────────
#  CONTENIDO DE AYUDA
# Cada entrada: clave única, título visible, módulo al que pertenece
# (None = no requiere permiso, siempre visible), y el texto explicativo.
# ─────────────────────────────────────────────────────────────

TEMAS_AYUDA = [
    # ── Primeros pasos ──────────────────────────────────────────
    {
        "categoria": "🚀 Primeros pasos",
        "clave": "intro",
        "titulo": "¿Qué es MAQUEDASYSTEMS?",
        "modulo": None,
        "texto": (
            "MAQUEDASYSTEMS es un sistema de gestión de ventas, inventario y "
            "clientes pensado para comercios. Permite registrar ventas, "
            "controlar el stock de productos, administrar clientes, generar "
            "reportes y mantener un historial completo de toda la actividad "
            "del negocio.\n\n"
            "El sistema se organiza en módulos, accesibles desde el menú "
            "lateral izquierdo. Cada usuario ve solo los módulos a los que "
            "tiene permiso de acceso, definidos por un administrador desde "
            "el módulo Usuarios.\n\n"
            "Roles disponibles:\n"
            "• Administrador (Admin): acceso total a todos los módulos, "
            "incluida la gestión de usuarios, licencias, datos del sistema "
            "y reinicio.\n"
            "• Gerente: acceso a los módulos que el administrador le "
            "habilite, pudiendo incluir también módulos administrativos "
            "(por ejemplo, Usuarios o RRHH) si así se decide.\n"
            "• Vendedor: acceso limitado a los módulos operativos que el "
            "administrador le haya habilitado individualmente (por "
            "ejemplo, solo Ventas y Clientes); nunca a los módulos "
            "exclusivos de administración."
        ),
    },
    {
        "categoria": "🚀 Primeros pasos",
        "clave": "primer_arranque",
        "titulo": "Primer arranque del sistema",
        "modulo": None,
        "texto": (
            "La primera vez que se abre el sistema (cuando todavía no existe "
            "ningún usuario administrador), la pantalla de inicio pide crear "
            "el primer administrador en lugar de mostrar el login normal.\n\n"
            "Datos solicitados: nombre completo, usuario, contraseña y "
            "confirmación de contraseña. Ese usuario queda creado con rol "
            "Administrador automáticamente.\n\n"
            "A partir de ese momento, el sistema pide usuario y contraseña "
            "normalmente en cada inicio."
        ),
    },
    {
        "categoria": "🚀 Primeros pasos",
        "clave": "barra_superior",
        "titulo": "La barra superior",
        "modulo": None,
        "texto": (
            "En la parte superior de la ventana principal siempre se ve:\n\n"
            "• Logo y nombre del sistema, a la izquierda.\n"
            "• Cronómetro de sesión: muestra cuánto tiempo lleva conectado el "
            "usuario actual. Se puede hacer click para ver estadísticas de "
            "uso (solo administradores).\n"
            "• Estado de la licencia: muestra el tipo y los días restantes. "
            "Se puede hacer click para ver más detalles o activar una nueva.\n"
            "• Foto de perfil, nombre y rol del usuario logueado, a la "
            "derecha. Al hacer click se abre un menú con 'Editar perfil' "
            "(abre el formulario en la pestaña Datos básicos) y 'Cambiar "
            "foto de perfil' (lo abre directo en la pestaña Foto); "
            "también se puede tocar el ícono de la foto para ir directo a "
            "cambiarla.\n"
            "• Botón 'Cerrar sesión': vuelve a la pantalla de login."
        ),
    },

    # ── Ventas ───────────────────────────────────────────────────
    {
        "categoria": "🧾 Ventas",
        "clave": "ventas_general",
        "titulo": "Cómo funciona el módulo Ventas",
        "modulo": "ventas",
        "texto": (
            "El módulo Ventas es la pantalla principal para registrar ventas "
            "al público. Funciona con pestañas, igual que un navegador: cada "
            "pestaña es una venta independiente en curso, y se puede tener "
            "varias abiertas al mismo tiempo con el botón '➕'.\n\n"
            "La pestaña 'Resumen' (siempre presente) muestra el listado de "
            "ventas del día seleccionado, junto con el panel de 'Dinero en "
            "Caja': saldo inicial, ventas en efectivo, entradas, salidas, "
            "devoluciones y el total en caja resultante.\n\n"
            "Para vender: escribí o escaneá el código del producto en el "
            "campo superior y presioná Enter (o el botón verde), el producto "
            "se agrega a la lista con su precio y existencia. Repetí para "
            "cada artículo. Al finalizar, presioná F12 o el botón 'Procesar' "
            "para cobrar."
        ),
    },
    {
        "categoria": "🧾 Ventas",
        "clave": "ventas_cargar_por_monto",
        "titulo": "Cargar por monto (productos por Kg, Litro o Metro)",
        "modulo": "ventas",
        "texto": (
            "Al seleccionar en la grilla de la venta un producto que se "
            "vende por Kilogramo, Litro o Metro, aparece un campo extra "
            "'💰 Cargar por monto' junto al control de cantidad (－ / "
            "cantidad / ＋), tanto en Ventas como en Armar Venta por "
            "Locales.\n\n"
            "Sirve para el caso típico de 'quiero Gs. 20.000 de esto': se "
            "escribe el monto en guaraníes, y en vivo se muestra a cuántos "
            "Kg/Lt/Mt equivale. Al presionar Enter (o hacer click afuera) "
            "esa cantidad se aplica a la línea de venta, igual que si se "
            "hubiera escrito a mano.\n\n"
            "Como el precio por gramo/mililitro/milímetro no siempre "
            "resulta en un monto exacto en guaraníes, la vista previa "
            "también muestra el monto real que se va a cobrar cuando hay "
            "una diferencia (por ejemplo: '≈ 0,789 Kg → Gs. 14.991' si se "
            "pidieron Gs. 15.000 exactos y esa cantidad no es posible), "
            "para no llevarse una sorpresa al confirmar. Si se escribe un "
            "monto que da cantidad 0, el producto se quita de la venta."
        ),
    },
    {
        "categoria": "🧾 Ventas",
        "clave": "ventas_atajos",
        "titulo": "Atajos de teclado en Ventas",
        "modulo": "ventas",
        "texto": (
            "Estos atajos funcionan en cualquier pestaña de venta activa:\n\n"
            "• F1 — Asignar Cliente: vincula la venta actual a un cliente "
            "registrado (en vez de 'Cliente Ocasional').\n"
            "• F2 — Buscar Producto: abre un buscador con lista completa de "
            "productos, útil cuando no se sabe el código exacto. Incluye "
            "filtros por Proveedor, Marca y Categoría (además del texto de "
            "búsqueda) para acotar rápido la lista cuando hay muchos "
            "productos cargados.\n"
            "• F3 — Consultar Stock: abre una consulta de solo lectura con "
            "todos los productos (código, categoría, precios, stock, "
            "comprometido y disponible), disponible incluso para vendedores "
            "sin acceso al módulo Inventario. Tiene los mismos filtros por "
            "Proveedor, Marca y Categoría, más la casilla 'Solo con stock "
            "disponible' y columnas ordenables haciendo click en el "
            "encabezado.\n"
            "• F7 — Entrada de Efectivo: registra un ingreso manual de "
            "dinero a la caja del día (por ejemplo, un aporte inicial).\n"
            "• F8 — Salida de Efectivo: registra un retiro manual de dinero "
            "de la caja (por ejemplo, un gasto). No es lo mismo que una "
            "salida de inventario.\n"
            "• F11 — Mayoreo: aplica el precio mayorista a la línea de "
            "producto seleccionada en la venta actual.\n"
            "• F12 — Procesar Venta: abre la pantalla de cobro para "
            "finalizar la venta actual.\n"
            "• Ctrl+P — Artículo Común: agrega un artículo libre escrito a "
            "mano (descripción y precio), sin necesidad de que esté dado de "
            "alta como producto. Útil para ventas puntuales o servicios.\n"
            "• Supr (Delete) — Borrar Artículo: elimina de la venta actual "
            "el artículo seleccionado en la lista.\n"
            "• Botón '🗑 Limpiar Todo': vacía por completo la venta actual "
            "(todos los artículos), sin procesarla."
        ),
    },
    {
        "categoria": "🧾 Ventas",
        "clave": "ventas_cobrar",
        "titulo": "Pantalla de Cobro",
        "modulo": "ventas",
        "texto": (
            "Al presionar F12 se abre la pantalla de cobro, donde se elige:\n\n"
            "• Condición de venta: Contado o Crédito (el crédito requiere "
            "que el cliente tenga el crédito habilitado).\n"
            "• Forma de pago: Efectivo, Transferencia Bancaria, u otras "
            "configuradas en el sistema.\n"
            "• Si es en efectivo, se puede ingresar el monto recibido y el "
            "sistema calcula el vuelto automáticamente. Doble click en el "
            "campo Efectivo lo completa solo con el Total exacto.\n\n"
            "Atajo rápido: presionando Enter dentro del campo Efectivo se "
            "cobra e imprime directo (como F12), sin tocar el mouse. Si el "
            "campo está vacío, se completa antes con el Total exacto y "
            "cobra en el mismo paso — ideal para el pago justo, sin "
            "vuelto. Si falta elegir el Tipo de Documento o el efectivo no "
            "alcanza, avisa igual que al usar F12.\n\n"
            "Al confirmar, se genera la venta con su número de factura "
            "correlativo, se descuenta el stock de cada producto vendido "
            "(con excepción de Servicios o productos de control 'Ilimitado'), "
            "y queda reflejada de inmediato en el Resumen del día."
        ),
    },
    {
        "categoria": "🧾 Ventas",
        "clave": "ventas_resumen",
        "titulo": "Resumen de Ventas y Dinero en Caja",
        "modulo": "ventas",
        "texto": (
            "La pestaña 'Resumen' muestra todas las ventas del día "
            "seleccionado (se puede cambiar de fecha con el calendario), "
            "con código, fecha/hora, cliente, importe, estado de cuenta, "
            "forma de pago y número de factura. La tabla tiene scroll "
            "vertical y también horizontal (barra debajo de la tabla), por "
            "si alguna columna queda fuera de la vista.\n\n"
            "Debajo, el panel 'Dinero en Caja' desglosa:\n"
            "• Saldo Inicial Caja — el monto con el que se abrió la caja.\n"
            "• Ventas en Efectivo — suma de ventas cobradas en efectivo.\n"
            "• Entradas — ingresos manuales de dinero (F7), con link "
            "'Ver detalle' para ver cada movimiento.\n"
            "• Salidas — retiros manuales de dinero (F8), también con "
            "detalle.\n"
            "• Devoluciones — importe devuelto a clientes en el día.\n"
            "• Total en Caja — el resultado final de todo lo anterior.\n\n"
            "Desde aquí también se puede generar un 'Reporte por Rango de "
            "Fechas', enviar el resumen por email, o imprimirlo."
        ),
    },
    {
        "categoria": "🧾 Ventas",
        "clave": "ventas_devoluciones",
        "titulo": "Devoluciones y cancelación de ventas",
        "modulo": "ventas",
        "texto": (
            "Desde el detalle de una venta (haciendo click sobre ella en el "
            "Resumen) se puede devolver una cantidad específica de un "
            "artículo vendido. Al devolver:\n\n"
            "• El stock del producto se repone automáticamente.\n"
            "• El importe se descuenta del total de la venta y de la "
            "factura.\n"
            "• Queda un registro de la devolución para trazabilidad, visible "
            "en el historial de movimientos de inventario del producto.\n"
            "• Si se devuelven todas las unidades de todos los artículos de "
            "una venta, esta pasa automáticamente a estado 'Cancelado'."
        ),
    },
    {
        "categoria": "🧾 Ventas",
        "clave": "ventas_armar_por_locales",
        "titulo": "Armar Venta por Locales (pedidos a varias sucursales/clientes)",
        "modulo": "ventas",
        "texto": (
            "Pensado para cuando una misma venta hay que dividirla y "
            "cargarla por separado para distintos locales a los que se "
            "les provee. Botón '🏬 Armar Venta por Locales' (barra de "
            "atajos de Ventas).\n\n"
            "• Escribí el nombre del local (o buscalo con 'Buscar Cliente' "
            "si ya está registrado) y presioná '➕ Agregar Local': se crea "
            "una pestaña con una grilla de productos totalmente "
            "independiente, con su propio buscador, botón 'Mayoreo' y "
            "control de cantidad (respeta si el producto es por Unidad, "
            "Kg, Litro, etc., igual que en la venta normal).\n"
            "• Se pueden agregar tantos locales como haga falta, cargando "
            "los productos de cada uno en su propia pestaña. El nombre de "
            "un local se puede corregir en cualquier momento con el ícono "
            "'✏' de su pestaña.\n"
            "• Todo lo que se carga acá se refleja EN TIEMPO REAL en la "
            "grilla de la venta (pestaña 'Nueva Venta N') de la que se "
            "abrió esta ventana, sumando automáticamente las cantidades "
            "cuando un mismo producto se repite entre locales. También "
            "funciona al revés: si se edita la cantidad de un producto "
            "directamente en la grilla de la venta, ese cambio se reparte "
            "de vuelta hacia el/los local(es) que lo habían aportado. "
            "'🗑 Limpiar Todo' en la venta también vacía todos los locales.\n"
            "• '📄 Generar PDF' arma un pedido con el detalle de cada local "
            "y un resumen consolidado (cantidades sumadas), con opción de "
            "enviarlo por correo o abrirlo al instante.\n"
            "• Esta ventana se puede cerrar y volver a abrir en cualquier "
            "momento (botón '✕ Cerrar'): recuerda exactamente los locales "
            "y productos que tenía armados esa pestaña de venta, para "
            "seguir editando sin perder nada."
        ),
    },
    {
        "categoria": "🧾 Ventas",
        "clave": "ventas_configurar_email",
        "titulo": "Configurar el envío de correos (Gmail, Outlook, Yahoo, etc.)",
        "modulo": "ventas",
        "texto": (
            "Para poder enviar el Resumen de Ventas, o cualquier reporte "
            "en PDF de otros módulos (por ejemplo, Veterinaria), hay que "
            "tener configurada al menos una cuenta de correo remitente. "
            "Botón 'Configurar Email' (aparece cuando se intenta enviar "
            "algo por correo sin tener ninguna cuenta configurada "
            "todavía).\n\n"
            "Admite cualquier proveedor: Gmail, Outlook/Hotmail/Live, "
            "Yahoo o un servidor SMTP personalizado (por ejemplo el de una "
            "empresa). Al elegir un proveedor conocido, el servidor y "
            "puerto se completan solos; con 'Otro' se pueden ingresar a "
            "mano.\n\n"
            "Importante: la mayoría de los proveedores (Gmail, Outlook, "
            "Yahoo) ya no aceptan la contraseña normal de la cuenta para "
            "esto — hace falta generar una 'contraseña de aplicación' "
            "desde la configuración de seguridad de esa cuenta de correo. "
            "La pantalla de configuración muestra instrucciones "
            "específicas según el proveedor elegido.\n\n"
            "Se pueden guardar VARIAS cuentas a la vez (por ejemplo, una "
            "de Gmail y otra de Outlook), sin tener que borrar ninguna "
            "para cargar otra:\n"
            "▸ '➕ Agregar otra cuenta de correo' — suma una cuenta nueva "
            "sin tocar las que ya estaban, y la deja como la activa (la "
            "que se usa para enviar).\n"
            "▸ 'Usar esta cuenta' — cambia cuál de las cuentas guardadas "
            "está activa, sin necesidad de volver a cargar sus datos.\n"
            "▸ '✎ Editar' — corrige los datos de una cuenta ya guardada "
            "(por ejemplo, si se generó una contraseña de aplicación "
            "nueva).\n"
            "▸ '✕ Desvincular' — quita una cuenta guardada por completo. "
            "Si era la que estaba activa y quedan otras, el sistema activa "
            "automáticamente la más reciente de las que quedan."
        ),
    },

    # ── Pre-Venta ────────────────────────────────────────────────
    {
        "categoria": "🕑 Pre-Venta",
        "clave": "preventa_general",
        "titulo": "Cómo funciona el módulo Pre-Venta",
        "modulo": "preventa",
        "texto": (
            "Una pre-venta es una venta \"guardada para después\": se "
            "cargan los artículos (y opcionalmente el cliente) sin "
            "descontar stock ni generar ningún comprobante todavía, para "
            "retomarla más tarde cuando el cliente vuelva a confirmar o a "
            "pagar.\n\n"
            "Se genera desde Ventas → pantalla de Cobro → botón 'F8 - "
            "Generar Preventa'. Ahí se guarda tal cual estaba cargada la "
            "venta en ese momento, y la pestaña de venta se limpia para "
            "empezar una nueva.\n\n"
            "El módulo Pre-Venta muestra el listado de todas las "
            "pre-ventas pendientes, con código, fecha y hora, cliente, "
            "importe y vendedor."
        ),
    },
    {
        "categoria": "🕑 Pre-Venta",
        "clave": "preventa_modificar",
        "titulo": "Modificar y finalizar una Pre-Venta",
        "modulo": "preventa",
        "texto": (
            "En la parte superior están los botones 'Modificar' (azul) y "
            "'Eliminar' (rojo); si se hace click en cualquiera de los dos "
            "sin haber seleccionado antes una pre-venta de la lista, el "
            "sistema avisa que primero hay que elegir una.\n\n"
            "• Modificar — abre un editor con los mismos atajos que "
            "Ventas (código + Enter, F1 Asignar Cliente, F2 Buscar "
            "Producto, Supr Borrar Artículo, doble click para editar "
            "cantidad/precio). Desde ahí se puede:\n"
            "   - 'Guardar Cambios' para actualizar la pre-venta sin "
            "finalizarla (sigue sin afectar el stock).\n"
            "   - 'Cobrar (Finalizar Venta)' para abrir la pantalla normal "
            "de Cobro; recién ahí se descuenta el stock, se genera la "
            "venta real con su comprobante, y la pre-venta se elimina "
            "automáticamente porque ya cumplió su función.\n"
            "• Eliminar — borra la pre-venta directamente (no hay nada que "
            "revertir, porque nunca afectó el stock)."
        ),
    },

    # ── Créditos ─────────────────────────────────────────────────
    {
        "categoria": "💳 Créditos",
        "clave": "creditos_general",
        "titulo": "Cómo funciona el módulo Créditos",
        "modulo": "creditos",
        "texto": (
            "Cada venta que se procesa con condición 'Crédito' (desde la "
            "pantalla de Cobro) genera automáticamente un crédito en este "
            "módulo — no hace falta cargar nada manualmente.\n\n"
            "El listado muestra Crédito N°, Fecha, Cliente, Fecha de "
            "Vencimiento, Descripción, N° de Factura, Deuda Total, Pagado "
            "y Saldo. Los radio buttons 'Mostrar Pendientes' / 'Mostrar "
            "Todos' filtran si se incluyen o no los créditos ya saldados "
            "por completo (que aparecen en gris)."
        ),
    },
    {
        "categoria": "💳 Créditos",
        "clave": "creditos_agrupar_resumen",
        "titulo": "Agrupar por Cliente y el panel de Resumen",
        "modulo": "creditos",
        "texto": (
            "• 'Agrupar por Cliente' — cambia la tabla a una vista "
            "agregada, con un renglón por cliente (Código, Nombre, Deuda "
            "Total, Pagado, Saldo) en vez de los créditos individuales. El "
            "botón pasa a decir 'Agrupar por Venta'; tocándolo de nuevo "
            "volvés a la tabla detallada.\n"
            "• 'Mostrar Resumen' / 'Ocultar Resumen' — muestra u oculta un "
            "panel al pie con dos totales generales: cantidad de ventas a "
            "crédito pendientes, y el monto total que falta cobrar en todo "
            "el sistema."
        ),
    },
    {
        "categoria": "💳 Créditos",
        "clave": "creditos_pago_estado_cuenta",
        "titulo": "Registrar un pago y el Estado de Cuenta",
        "modulo": "creditos",
        "texto": (
            "Haciendo doble click en un crédito individual se abre su "
            "detalle, con el historial de pagos ya registrados y un campo "
            "para cargar un pago nuevo (con el botón 'Pagar Saldo Total' "
            "para completarlo de una vez). No se puede pagar más del "
            "saldo pendiente.\n\n"
            "El botón 'Estado de Cuenta' (se habilita al seleccionar "
            "cualquier renglón con un cliente asociado) abre un resumen "
            "completo de todos los créditos de ese cliente, con opción de "
            "exportarlo a PDF para entregárselo."
        ),
    },

    # ── Préstamos ────────────────────────────────────────────────
    {
        "categoria": "🏦 Préstamos",
        "clave": "prestamos_general",
        "titulo": "Cómo funciona el módulo Préstamos",
        "modulo": "prestamos",
        "texto": (
            "Es una pequeña financiera dentro del sistema, para prestar "
            "dinero a clientes y llevar el cronograma de cobro. Tiene tres "
            "pestañas:\n\n"
            "• Banco (Fondo) — el saldo disponible para prestar, con carga "
            "de nuevos fondos e historial de movimientos.\n"
            "• Nuevo Préstamo — alta de un préstamo a un cliente, con vista "
            "previa del cronograma de cuotas antes de desembolsar.\n"
            "• Préstamos — listado de préstamos otorgados (activos, "
            "pagados o todos), con el detalle de cuotas y pagos de cada "
            "uno.\n\n"
            "Al dar de alta un préstamo se pueden elegir cuatro sistemas "
            "de amortización paraguayos: Francés (cuota fija), Alemán "
            "(cuota decreciente, capital fijo), Americano (solo interés en "
            "cada cuota y el capital entero al final) y Directo/Flat "
            "(interés fijo sobre el capital original). La frecuencia de "
            "las cuotas puede ser diaria, semanal, quincenal o mensual."
        ),
    },
    {
        "categoria": "🏦 Préstamos",
        "clave": "prestamos_fondo",
        "titulo": "El Fondo (Banco) y sus movimientos",
        "modulo": "prestamos",
        "texto": (
            "El Fondo es el 'banco' interno del negocio: el dinero "
            "disponible para prestar. Desde la pestaña 'Banco (Fondo)' se "
            "puede cargar dinero nuevo (por ejemplo, un aporte de "
            "capital), y ahí queda reflejado en el saldo disponible.\n\n"
            "Cada préstamo desembolsado descuenta el capital del saldo del "
            "fondo automáticamente, y cada cobro de cuota lo vuelve a "
            "sumar. El historial de movimientos muestra, en orden, cada "
            "carga, desembolso y cobro, con el saldo resultante después de "
            "cada uno — así siempre se puede saber cuánto dinero hay "
            "disponible para prestar en un momento dado."
        ),
    },
    {
        "categoria": "🏦 Préstamos",
        "clave": "prestamos_pagos_mora",
        "titulo": "Registrar un pago y la mora por atraso",
        "modulo": "prestamos",
        "texto": (
            "Dentro del detalle de un préstamo se ve el cronograma completo "
            "de cuotas, con su fecha de vencimiento, capital e interés. Al "
            "registrar un pago se puede cargar el monto pagado; si la "
            "cuota está vencida y el préstamo tiene una tasa de mora "
            "diaria configurada, el sistema calcula automáticamente el "
            "interés moratorio acumulado por los días de atraso y lo suma "
            "al monto a cobrar.\n\n"
            "Los pagos pueden ser parciales (se registran a cuenta de la "
            "cuota) o totales. Cada préstamo lleva su propio historial de "
            "pagos, y el reporte en PDF ('Extracto') resume el estado "
            "completo: cuotas pagadas, pendientes, atrasadas y el saldo "
            "restante."
        ),
    },

    # ── Presupuestos ─────────────────────────────────────────────
    {
        "categoria": "📝 Presupuestos",
        "clave": "presupuestos_general",
        "titulo": "Cómo funciona el módulo Presupuestos",
        "modulo": "presupuestos",
        "texto": (
            "Un presupuesto es una cotización para un cliente (existente "
            "o walk-in) que no afecta el stock ni genera ningún "
            "comprobante hasta que se convierte en una venta real.\n\n"
            "Botón 'Nuevo Presupuesto' → mismo flujo que Ventas: código + "
            "Enter para agregar productos, F1 Asignar Cliente, F2 Buscar "
            "Producto, DEL Borrar Artículo. Además se define la Fecha de "
            "Validez de la oferta y observaciones opcionales."
        ),
    },
    {
        "categoria": "📝 Presupuestos",
        "clave": "presupuestos_estados",
        "titulo": "Estados: Pendiente, Aprobado, Rechazado, Vencido, Convertido",
        "modulo": "presupuestos",
        "texto": (
            "• Pendiente — recién creado, todavía se puede editar "
            "libremente.\n"
            "• Vencido — un presupuesto Pendiente cuya Fecha de Validez ya "
            "pasó; se calcula solo, no hay que hacer nada manualmente.\n"
            "• Aprobado / Rechazado — se define desde el detalle del "
            "presupuesto, según la respuesta del cliente.\n"
            "• Convertido — una vez que un presupuesto Aprobado se pasa a "
            "una venta real, queda marcado así de forma permanente (ya no "
            "se puede editar ni eliminar), y queda vinculado a esa venta "
            "para no perder el historial."
        ),
    },
    {
        "categoria": "📝 Presupuestos",
        "clave": "presupuestos_convertir_pdf",
        "titulo": "Convertir a Venta y generar el PDF para el cliente",
        "modulo": "presupuestos",
        "texto": (
            "Con el presupuesto en estado 'Aprobado', el botón 'Convertir "
            "a Venta' abre la misma pantalla de Cobro que usa Ventas, ya "
            "cargada con los mismos artículos y cliente. Recién al "
            "confirmar el cobro se descuenta stock y se genera la venta "
            "real.\n\n"
            "El botón 'Generar PDF' arma el documento del presupuesto "
            "(con los datos del local si están configurados en 'Config. "
            "Local') para entregar o enviar al cliente. No tiene validez "
            "fiscal, es solo una cotización.\n\n"
            "Desde la lista de presupuestos, el botón 'Generar PDF' de la "
            "barra superior se pone rojo cuando hay un presupuesto "
            "seleccionado; si se hace click sin seleccionar ninguno, el "
            "sistema avisa que primero hay que elegir uno de la lista."
        ),
    },

    # ── Productos ────────────────────────────────────────────────
    {
        "categoria": "📦 Productos",
        "clave": "productos_general",
        "titulo": "Cómo funciona el módulo Productos",
        "modulo": "productos",
        "texto": (
            "El módulo Productos es el catálogo completo del negocio: acá se "
            "dan de alta, editan y consultan todos los artículos que se "
            "pueden vender. La grilla muestra código, descripción, "
            "categoría, marca, precios y stock de cada producto.\n\n"
            "Para crear un producto nuevo, usá el botón '+ Nuevo Producto'. "
            "Para editar uno existente, hacé doble click sobre la fila o "
            "usá el menú contextual (click derecho).\n\n"
            "Además del buscador por texto, hay una fila de filtros por "
            "Proveedor, Marca y Categoría (con 'Todos' como opción por "
            "defecto): se pueden combinar entre sí y con el texto de "
            "búsqueda al mismo tiempo, y el botón '✕ Limpiar filtros' los "
            "resetea todos de un solo click."
        ),
    },
    {
        "categoria": "📦 Productos",
        "clave": "productos_formulario",
        "titulo": "Formulario de producto (pestañas)",
        "modulo": "productos",
        "texto": (
            "El formulario de alta/edición de producto está organizado en "
            "pestañas:\n\n"
            "▸ Datos — código, descripción, unidad de medida, tipo de "
            "impuesto, y los 4 precios: Compra, Venta, Crédito y "
            "Mayorista. El Precio Crédito se autocompleta con el Precio "
            "Venta mientras no se edite manualmente. Los 4 campos de "
            "precio solo aceptan dígitos — cualquier otro carácter se "
            "descarta automáticamente mientras se escribe, ya que el "
            "Guaraní no tiene decimales.\n"
            "▸ Datos Adicionales — categoría, marca, proveedor y stock "
            "mínimo (para alertas de bajo stock).\n"
            "▸ Imágenes — foto del producto, se recorta automáticamente.\n"
            "▸ Proveedor — datos de contacto del proveedor asociado.\n"
            "▸ Opciones — tipo de producto (Producto o Servicio) y control "
            "de stock (Cantidad o Ilimitado). Los Servicios y los productos "
            "con control 'Ilimitado' nunca descuentan ni validan stock, "
            "ideales para servicios o artículos que no se gestionan por "
            "unidad. Al elegir 'Ilimitado', los campos 'Stock Inicial' (o "
            "'Stock Actual' al editar) y 'Stock Mínimo' se inhabilitan "
            "automáticamente (quedan en gris, sin poder tocarse) porque "
            "no aplican; vuelven a habilitarse solos si se cambia de "
            "nuevo a 'Cantidad'."
        ),
    },
    {
        "categoria": "📦 Productos",
        "clave": "productos_activar_desactivar",
        "titulo": "Desactivar y eliminar productos",
        "modulo": "productos",
        "texto": (
            "Un producto se puede Desactivar (queda oculto de Ventas e "
            "Inventario, pero se conserva en la base de datos) o, en casos "
            "específicos, Eliminar Definitivamente.\n\n"
            "Reglas para poder DESACTIVAR un producto:\n"
            "• El stock debe estar en cero (si tiene stock, primero hay que "
            "registrar una Salida de Inventario para descargarlo).\n\n"
            "Reglas para poder ELIMINAR DEFINITIVAMENTE un producto:\n"
            "• Debe estar previamente desactivado.\n"
            "• Su stock y lo comprometido deben estar en cero.\n\n"
            "Al eliminar un producto, su historial de ventas y movimientos "
            "de inventario pasados NO se borra: queda preservado mostrando "
            "el nombre del producto como referencia, aunque el producto ya "
            "no exista en el catálogo."
        ),
    },

    # ── Inventario ───────────────────────────────────────────────
    {
        "categoria": "📋 Inventario",
        "clave": "inventario_general",
        "titulo": "Cómo funciona el módulo Inventario",
        "modulo": "inventario",
        "texto": (
            "El módulo Inventario muestra el stock de cada producto: precio "
            "de compra/venta/mayorista, stock mínimo, stock actual, "
            "comprometido (reservado en ventas pendientes) y disponible.\n\n"
            "Botones superiores (cada uno con su propio color para "
            "distinguirlos de un vistazo — ámbar, azul, rojo e índigo — y "
            "que se ponen sólidos cuando el filtro está aplicado):\n"
            "• Mostrar Productos Bajos en Inventario — filtra solo los "
            "productos con stock igual o menor al mínimo configurado.\n"
            "• Mostrar Solamente Productos en Stock — oculta los que están "
            "en cero.\n"
            "• Mostrar Productos Inactivos — muestra los productos "
            "desactivados (en gris), para poder reactivarlos o eliminarlos.\n"
            "• Ocultar/Mostrar Resumen — panel inferior con cantidad total "
            "de productos, valor del inventario y valor comprometido.\n"
            "• Reporte General — exporta un reporte completo en PDF o Excel.\n\n"
            "El buscador (Ctrl+B) está en su propia fila debajo de estos "
            "botones, ocupando todo el ancho disponible, para que siempre "
            "se vea bien sin importar cuántos botones haya arriba. Debajo "
            "del buscador hay una fila de filtros por Proveedor, Marca y "
            "Categoría, combinables entre sí y con el texto de búsqueda, "
            "con un botón para limpiarlos todos de una vez."
        ),
    },
    {
        "categoria": "📋 Inventario",
        "clave": "inventario_menu_contextual",
        "titulo": "Menú contextual (click derecho)",
        "modulo": "inventario",
        "texto": (
            "Haciendo click derecho sobre un producto en la grilla de "
            "Inventario se despliega:\n\n"
            "• Entrada — suma stock al producto (por ejemplo, una compra), "
            "con motivo, número de comprobante y observaciones.\n"
            "• Salida — descuenta stock (ajustes, pérdidas, uso interno).\n"
            "• Editar Stock Mínimo — define el umbral de alerta de bajo "
            "stock.\n"
            "• Historial Movimientos — ver el historial completo a "
            "continuación.\n"
            "• Editar Producto — abre el formulario completo del producto.\n"
            "• Desactivar/Activar Producto — alterna el estado del "
            "producto.\n"
            "• Eliminar Producto Definitivamente — borrado permanente, solo "
            "habilitado cuando se cumplen las condiciones (ver el tema "
            "'Desactivar y eliminar productos')."
        ),
    },
    {
        "categoria": "📋 Inventario",
        "clave": "inventario_historial",
        "titulo": "Historial de Movimientos",
        "modulo": "inventario",
        "texto": (
            "El Historial de Movimientos de un producto registra, en orden "
            "cronológico, TODO lo que afectó su stock desde que fue creado:\n\n"
            "• Stock Inicial — al dar de alta el producto, si se cargó con "
            "stock mayor a cero.\n"
            "• Entradas y Salidas manuales — registradas desde el menú "
            "contextual (compras, ajustes, etc.).\n"
            "• Compras — cada compra registrada en el módulo Compras suma "
            "stock y queda como entrada, con el proveedor y el número de "
            "comprobante como referencia.\n"
            "• Ventas — cada venta del producto descuenta stock y queda "
            "registrada como salida, con el número de venta como "
            "referencia.\n"
            "• Devoluciones — cada devolución repone stock y queda "
            "registrada como entrada.\n"
            "• Ajustes manuales al editar el producto — si se cambia el "
            "stock directamente desde el formulario de edición.\n\n"
            "Se puede filtrar por tipo (Entrada/Salida) y por cantidad de "
            "registros a mostrar. Las entradas aparecen en verde y las "
            "salidas en rojo, con totales acumulados al pie.\n\n"
            "Productos con control de stock 'Ilimitado': también quedan "
            "en este historial, tanto la carga inicial al crear el "
            "producto como cada venta o salida posterior, pero mostrando "
            "'Ilimitado' en vez de un número en las columnas Cantidad y "
            "Stock Resultante (ya que ese producto no descuenta stock "
            "real). Esos movimientos no se suman a los totales de "
            "Entradas/Salidas del pie, que reflejan solo unidades reales "
            "de inventario. Lo mismo aplica al exportar a Excel/CSV desde "
            "Gestión de Datos."
        ),
    },

    # ── Compras ──────────────────────────────────────────────────
    {
        "categoria": "🛒 Compras",
        "clave": "compras_general",
        "titulo": "Cómo funciona el módulo Compras",
        "modulo": "compras",
        "texto": (
            "El módulo Compras registra las compras a proveedores. Botón "
            "'Nueva Compra' → se abre la carga con código de producto + "
            "Enter (o F2 Buscar), igual que en Ventas.\n\n"
            "Al agregar cada producto se pide la Cantidad y el Precio de "
            "Compra en un popup; se puede editar después haciendo doble "
            "click sobre la línea ya cargada, o quitarla con 'DEL Borrar "
            "Artículo'.\n\n"
            "Antes de guardar se elige el Proveedor (con alta rápida si es "
            "nuevo, botón '+ Nuevo'), la Fecha de Compra (con calendario) y "
            "el N° de Comprobante."
        ),
    },
    {
        "categoria": "🛒 Compras",
        "clave": "compras_efecto",
        "titulo": "Qué pasa al guardar una Compra",
        "modulo": "compras",
        "texto": (
            "Al presionar 'Guardar Compra' pasan tres cosas automáticamente, "
            "sin que haya que hacer nada más:\n\n"
            "• Se suma el stock de cada producto comprado (visible al "
            "instante en Productos e Inventario).\n"
            "• Se actualiza el Precio de Compra del producto, con el valor "
            "cargado en esta compra.\n"
            "• Queda registrado un movimiento de tipo 'entrada' en el "
            "Historial de Movimientos de cada producto, con el proveedor y "
            "el número de comprobante como referencia — igual que una "
            "Entrada de Inventario manual.\n\n"
            "La compra NO mueve caja/efectivo ni genera comprobante fiscal "
            "(eso es exclusivo de las Facturas de venta)."
        ),
    },
    {
        "categoria": "🛒 Compras",
        "clave": "compras_reportes",
        "titulo": "Reporte de Compras",
        "modulo": "compras",
        "texto": (
            "Dentro del módulo Reportes hay una pestaña 'Compras' dedicada, "
            "con el mismo nivel de detalle que la de Ventas: filtros por "
            "rango de fechas y proveedor, tarjetas de resumen (cantidad, "
            "total comprado, promedio por compra, proveedores distintos), "
            "detalle de cada compra al hacer click, y exportación en 7 "
            "formatos (PDF con gráfico, PDF simple, Word, LibreOffice, "
            "Excel, CSV y JSON)."
        ),
    },

    # ── Asistencia Técnica ───────────────────────────────────────
    {
        "categoria": "🖥 Asistencia Técnica",
        "clave": "asistencia_general",
        "titulo": "Cómo funciona el módulo Asistencia Técnica",
        "modulo": "asistencia",
        "texto": (
            "El módulo Asistencia Técnica lleva el seguimiento de equipos "
            "que ingresan a reparación. Botón 'Entrada de Equipo' → "
            "asistente de 2 pasos:\n\n"
            "1) Cliente (Nombre, CI/RUC, Dirección, Teléfono, con F2 "
            "Buscar Cliente para autocompletar si ya está registrado) y "
            "Equipo (Tipo de Equipo, N° Serie, Descripción, con F3 Buscar "
            "Equipo para encontrarlo rápido si es un cliente recurrente).\n"
            "2) Prioridad (Baja/Media/Alta/Urgente) y observaciones del "
            "motivo de ingreso.\n\n"
            "Al guardar, el caso queda creado en estado 'Entrada', con "
            "quien lo recibió registrado automáticamente."
        ),
    },
    {
        "categoria": "🖥 Asistencia Técnica",
        "clave": "asistencia_pestañas",
        "titulo": "Pestañas: Casos, Pendientes, Dashboard y Equipos",
        "modulo": "asistencia",
        "texto": (
            "• Casos — listado completo, con filtro de cantidad a mostrar "
            "y checkboxes combinables Pendientes/Anulados/Retirados, más "
            "buscador.\n"
            "• Pendientes — solo los casos activos (no retirados ni "
            "anulados), con su prioridad y quién los recibió.\n"
            "• Dashboard — un desplegable por cada estado (Entrada, En "
            "Espera, En Revisión, Disponible para Retiro, Retirados "
            "recientemente) con la cantidad de casos en cada uno; al "
            "expandir se listan los casos de ese estado.\n"
            "• Equipos — catálogo de equipos ya registrados alguna vez, "
            "para encontrarlos con F3 la próxima vez que el mismo cliente "
            "traiga el mismo equipo."
        ),
    },
    {
        "categoria": "🖥 Asistencia Técnica",
        "clave": "asistencia_gestionar_caso",
        "titulo": "Gestionar un caso: cambiar estado, observaciones y anular",
        "modulo": "asistencia",
        "texto": (
            "Haciendo doble click en cualquier caso (desde Casos o "
            "Pendientes, o desde el Dashboard) se abre su detalle, donde "
            "se puede:\n\n"
            "• Cambiar el estado, avanzando el flujo de reparación: "
            "Entrada → En Espera → En Revisión → Disponible para Retiro → "
            "Retirado (se pide confirmación al marcar 'Retirado', porque "
            "significa que el cliente se está llevando el equipo).\n"
            "• Editar las observaciones del caso.\n"
            "• Anular el caso, si corresponde (queda marcado como anulado, "
            "no se borra del historial)."
        ),
    },

    # ── Veterinaria ──────────────────────────────────────────────
    {
        "categoria": "🐾 Veterinaria",
        "clave": "veterinaria_general",
        "titulo": "Cómo funciona el módulo Veterinaria",
        "modulo": "veterinaria",
        "texto": (
            "El módulo Veterinaria lleva la ficha clínica de las mascotas: "
            "datos del dueño y del animal, historial de consultas, vacunas "
            "aplicadas y tratamientos en curso (desparasitaciones, "
            "medicación).\n\n"
            "Se organiza en 3 pestañas:\n"
            "• Mascotas — listado con buscador (por mascota, dueño, raza o "
            "microchip) y casillero 'Incluir fallecidos'. Doble click abre "
            "la ficha completa.\n"
            "• Vacunas Próximas — avisa qué vacunas están vencidas (en "
            "rojo) o próximas a vencer dentro de 30 días (en naranja).\n"
            "• Dashboard — tarjetas resumen (mascotas activas, consultas de "
            "hoy, tratamientos activos, vacunas próx./vencidas) y el "
            "listado de consultas registradas en el día."
        ),
    },
    {
        "categoria": "🐾 Veterinaria",
        "clave": "veterinaria_ficha_mascota",
        "titulo": "Ficha de la Mascota: datos, historial, vacunas y tratamientos",
        "modulo": "veterinaria",
        "texto": (
            "Botón '🐾➕ Nueva Mascota' (o doble click sobre una mascota ya "
            "cargada) abre la ficha completa:\n\n"
            "• Dueño — nombre y teléfono, con 'Buscar Cliente' para "
            "vincularla a un cliente ya registrado.\n"
            "• Mascota — nombre, especie (lista editable: si escribís una "
            "especie nueva, se agrega sola al catálogo), raza, color, "
            "sexo, fecha de nacimiento (con selector de calendario), peso, "
            "N° de microchip y si está esterilizado/a.\n\n"
            "Al guardar una mascota nueva, la ventana se transforma "
            "automáticamente en la ficha completa (sin cerrarse), donde "
            "aparecen 3 sub-pestañas:\n"
            "• Historial Clínico — botón 'Nueva Consulta': motivo, "
            "diagnóstico, tratamiento indicado, peso, temperatura, "
            "próxima visita y costo.\n"
            "• Vacunas — botón 'Nueva Vacuna': vacuna, fecha de "
            "aplicación, próxima dosis, lote y veterinario.\n"
            "• Tratamientos — botón 'Nuevo Tratamiento' (Desparasitación/"
            "Medicación/Otro) con dosis, frecuencia y fecha fin estimada; "
            "botón 'Finalizar Seleccionado' para marcarlo como terminado.\n\n"
            "El botón '🕊 Marcar Fallecido' (que pasa a '↩ Reactivar Ficha') "
            "permite dar de baja a una mascota sin borrar su historial."
        ),
    },
    {
        "categoria": "🐾 Veterinaria",
        "clave": "veterinaria_pdf_email",
        "titulo": "Generar reportes en PDF y enviarlos por correo",
        "modulo": "veterinaria",
        "texto": (
            "Se puede generar un PDF en 3 niveles de detalle distintos, "
            "cada uno con su botón '🖨 Generar PDF' y '✉ Enviar por Correo':\n\n"
            "• Ficha completa de la mascota — desde la lista de Mascotas "
            "(seleccionando una fila) o desde dentro de su ficha: incluye "
            "todo el historial clínico, vacunas y tratamientos.\n"
            "• Certificado de una vacuna puntual — desde la pestaña "
            "'Vacunas Próximas', seleccionando la fila correspondiente.\n"
            "• Constancia de una consulta puntual — desde el Dashboard, "
            "seleccionando una consulta del listado del día.\n\n"
            "'Enviar por Correo' arma el mensaje (destinatario, asunto y "
            "cuerpo editables) y adjunta el PDF automáticamente. Si "
            "todavía no se configuró ninguna cuenta de correo, ofrece "
            "abrir la configuración ahí mismo (ver 'Configurar el envío "
            "de correos' en Ventas)."
        ),
    },

    # ── Restaurante/Comedor ──────────────────────────────────────
    {
        "categoria": "🍽 Restaurante/Comedor",
        "clave": "restaurante_general",
        "titulo": "Cómo funciona el módulo Restaurante/Comedor",
        "modulo": "restaurante",
        "texto": (
            "Pensado para restaurantes, comedores y pizzerías. Se organiza "
            "en un mapa de Mesas (Libre / Ocupada / Reservada / Para "
            "Limpiar), Comandas (el pedido de una mesa, delivery, para "
            "llevar o mostrador), Platos con su receta, y un Dashboard con "
            "los reportes del día.\n\n"
            "Al abrir una comanda en una mesa, esta pasa a 'Ocupada' "
            "automáticamente. Se le van agregando platos, cada uno con su "
            "propio estado de cocina (Pendiente → Preparando → Listo → "
            "Entregado), para llevar el control de la cocina en tiempo "
            "real. Al cerrar la comanda se genera una venta real — con su "
            "factura, su lugar en Caja y en el Resumen de Ventas de "
            "siempre — y se descuentan automáticamente del inventario los "
            "insumos consumidos por cada plato, según su receta.\n\n"
            "El personal (mozos, cocineros) y sus turnos se administran en "
            "el módulo Rec. Humanos; acá solo se registra qué usuario "
            "atendió cada comanda."
        ),
    },
    {
        "categoria": "🍽 Restaurante/Comedor",
        "clave": "restaurante_platos_recetas",
        "titulo": "Platos, Recetas y Variantes",
        "modulo": "restaurante",
        "texto": (
            "Cada plato se define con nombre, categoría (Entrada, Plato "
            "Principal, Pizza, Combo, Guarnición, Postre, Bebida, Otro), "
            "precio de venta y su receta: qué productos del catálogo "
            "consume como insumo y en qué cantidad. No hace falta cargar "
            "los insumos aparte — se reutilizan los productos que ya "
            "existen en Productos/Inventario, con el mismo control de "
            "stock y alertas de reposición.\n\n"
            "El costo y el margen de cada plato se calculan "
            "automáticamente a partir del precio de compra de sus "
            "insumos. Para pizzerías, un plato puede tener Variantes "
            "(por ejemplo, Individual/Mediana/Familiar), cada una con su "
            "propio precio y un multiplicador que escala la receta base "
            "según el tamaño. Al armar una comanda también se pueden "
            "agregar o quitar ingredientes puntuales de un ítem "
            "('Agregados'/'Quitados'), que se cobran y descuentan del "
            "inventario aparte de la receta estándar."
        ),
    },
    {
        "categoria": "🍽 Restaurante/Comedor",
        "clave": "restaurante_delivery_dashboard",
        "titulo": "Delivery y Dashboard de reportes",
        "modulo": "restaurante",
        "texto": (
            "Las comandas de tipo 'Delivery' se pueden asignar a un "
            "repartidor y seguir su estado (Preparando → En Camino → "
            "Entregado) hasta la entrega, con la dirección de entrega "
            "cargada en la comanda.\n\n"
            "El Dashboard reúne los reportes típicos del día a día: "
            "platos más vendidos, margen por plato (para detectar cuáles "
            "convienen más), costos operativos (insumos consumidos) "
            "frente a los ingresos, y ventas separadas por turno (Mañana, "
            "Tarde, Noche)."
        ),
    },

    # ── Alquiler de Streaming ────────────────────────────────────
    {
        "categoria": "📺 Alquiler de Streaming",
        "clave": "streaming_general",
        "titulo": "Cómo funciona el módulo Alquiler de Streaming",
        "modulo": "streaming",
        "texto": (
            "Para negocios que revenden accesos a cuentas de streaming "
            "(Netflix, HBO Max, Disney+, YouTube Premium, Spotify, etc.). "
            "Se administra por niveles:\n\n"
            "• Plataformas — el catálogo de servicios (Netflix, Disney+, "
            "etc.).\n"
            "• Cuentas — cada cuenta comprada, con su email, contraseña, "
            "plan, costo mensual y cupo máximo de perfiles.\n"
            "• Perfiles — los cupos individuales de cada cuenta (Libre / "
            "Ocupado), que son lo que efectivamente se le alquila a un "
            "cliente.\n"
            "• Combos — paquetes de varias plataformas juntas a un precio "
            "fijo.\n\n"
            "El Dashboard incluye alertas de seguridad: cuentas que "
            "necesitan rotación de contraseña y suscripciones próximas a "
            "vencer, para anticiparse antes de que el cliente se quede "
            "sin acceso."
        ),
    },
    {
        "categoria": "📺 Alquiler de Streaming",
        "clave": "streaming_suscripciones",
        "titulo": "Suscripciones de clientes: modalidades, cobro y renovación",
        "modulo": "streaming",
        "texto": (
            "Una Suscripción es lo que contrata un cliente, en alguna de "
            "tres modalidades: 'Perfil Individual' (un solo perfil de una "
            "cuenta), 'Acceso Completo' (toda la cuenta) o 'Combo' "
            "(varias plataformas juntas). Cada suscripción tiene fecha de "
            "inicio, fecha de vencimiento, precio mensual y una cantidad "
            "máxima de dispositivos conectados simultáneamente.\n\n"
            "El cobro y la renovación reutilizan el mismo motor de Ventas "
            "de siempre: cada pago de renovación queda registrado en el "
            "historial de pagos de la suscripción y también genera su "
            "venta correspondiente. El reporte de rentabilidad por "
            "plataforma compara lo que se cobra a los clientes contra el "
            "costo mensual de las cuentas, para saber qué plataformas dan "
            "más margen."
        ),
    },

    # ── Importaciones ────────────────────────────────────────────
    {
        "categoria": "📦 Importaciones",
        "clave": "importacion_general",
        "titulo": "Cómo funciona el módulo Importaciones",
        "modulo": "importacion",
        "texto": (
            "Para llevar el control de las compras hechas en plataformas "
            "del exterior (eBay, AliExpress, Temu, Shein, Alibaba, Made in "
            "China, Amazon, o cualquier otra tienda que agregues) que "
            "llegan en una caja a un casillero (Miami o Shenzhen) antes de "
            "venir a Paraguay a través de un courier.\n\n"
            "Cada Compra registrada representa 'una caja', que puede traer "
            "uno o varios productos, en una o varias unidades cada uno. Al "
            "retirar la caja del courier se paga por el PESO TOTAL, así "
            "que el sistema calcula el flete automáticamente (peso × "
            "tarifa por kg del courier elegido, vía aérea o marítima) y lo "
            "reparte proporcionalmente entre todas las unidades de la "
            "caja — por ejemplo, 10 auriculares en una caja de 1 kg con "
            "flete de US$ 8 quedan con US$ 0,80 de envío cada uno.\n\n"
            "El costo total de cada unidad es lo pagado en la plataforma "
            "más la parte de flete que le corresponde. Con el precio de "
            "venta al público que cargues, el sistema calcula la ganancia "
            "y el margen automáticamente.\n\n"
            "El Dashboard muestra la inversión total, la ganancia "
            "potencial, el tiempo promedio entre la compra y la recepción "
            "final, y la rentabilidad por plataforma y por producto.\n\n"
            "Arriba a la derecha, el botón '📄 Reporte General' exporta "
            "todo (resumen, compras, rentabilidad por plataforma y por "
            "producto, y couriers) en 7 formatos distintos: PDF, Word, "
            "LibreOffice, Excel, CSV o JSON — igual que en Recursos "
            "Humanos e Inventario."
        ),
    },
    {
        "categoria": "📦 Importaciones",
        "clave": "importacion_couriers_tiendas_cambio",
        "titulo": "Couriers, tiendas y el tipo de cambio en guaraníes",
        "modulo": "importacion",
        "texto": (
            "En la pestaña 'Couriers / Casilleros' se registra cada "
            "empresa de courier con su email, RUC, teléfono y — lo más "
            "importante — su tarifa por kilo vía aérea y vía marítima. Esa "
            "tarifa es la que el sistema usa para calcular el flete de "
            "cada compra automáticamente según el peso de la caja; si "
            "cambiás la tarifa de un courier, las compras que ya tenía "
            "cargadas se recalculan solas. También se puede cargar un "
            "costo de envío manual en una compra puntual, para los casos "
            "en que el envío hasta el casillero salió gratis o ya venía "
            "incluido.\n\n"
            "Las tiendas/plataformas (eBay, Amazon, etc.) se administran "
            "con el botón '🏪 Tiendas' en la pestaña Compras, o agregando "
            "una nueva al vuelo con el botón '+' junto al combo de "
            "Plataforma dentro de la ficha de una compra.\n\n"
            "Todos los montos del módulo se cargan en dólares (US$, la "
            "moneda habitual de estas plataformas y couriers), pero se "
            "muestran también convertidos a guaraníes en todas las "
            "pantallas. El tipo de cambio usado se ve y se edita desde la "
            "barra celeste arriba del Dashboard: con '✏ Editar' se carga "
            "a mano (por si no coincide con el real), y con '🔄 "
            "Actualizar automático' se descarga de Internet."
        ),
    },
    {
        "categoria": "📦 Importaciones",
        "clave": "importacion_inventario",
        "titulo": "Enviar a Inventario y vender lo importado",
        "modulo": "importacion",
        "texto": (
            "Una vez que una compra está en estado 'Recibido', cada "
            "producto de la caja se puede enviar al Inventario del "
            "sistema con el botón '📥 Enviar a Inventario' dentro de la "
            "ficha de la compra: se puede crear como producto nuevo, o "
            "sumar el stock a un producto que ya existe en el catálogo. "
            "Al enviarlo, el costo de compra y el precio de venta público "
            "calculados en la importación quedan cargados en el producto "
            "automáticamente.\n\n"
            "A partir de ahí, ese producto se vende de forma totalmente "
            "normal desde el módulo Ventas, como cualquier otro producto "
            "del catálogo — el módulo Importaciones no reemplaza a "
            "Ventas, solo se encarga de calcular bien el costo real de lo "
            "importado antes de que entre al stock."
        ),
    },

    # ── Clientes ─────────────────────────────────────────────────
    {
        "categoria": "👥 Clientes",
        "clave": "clientes_general",
        "titulo": "Cómo funciona el módulo Clientes",
        "modulo": "clientes",
        "texto": (
            "El módulo Clientes administra la base de clientes del negocio: "
            "nombre, razón social, documento, teléfono, email, dirección y "
            "configuración de crédito.\n\n"
            "En la barra superior: 'Nuevo Cliente' (azul), 'Editar' (azul "
            "claro) y 'Eliminar' (rojo claro), para identificar rápido cada "
            "acción por su color.\n\n"
            "Cada cliente puede tener el crédito habilitado o no; si está "
            "habilitado, se le puede asignar un límite de crédito, y desde "
            "Ventas se le pueden hacer ventas en condición 'Crédito' que "
            "generan una deuda pendiente de pago.\n\n"
            "Los pagos de crédito se registran desde la ficha del cliente, "
            "descontando el saldo pendiente."
        ),
    },

    # ── Reportes ─────────────────────────────────────────────────
    {
        "categoria": "📊 Reportes",
        "clave": "reportes_visibilidad_por_rol",
        "titulo": "Qué ventas ve cada usuario (Vendedor vs. Gerente/Admin)",
        "modulo": "reportes",
        "texto": (
            "Un usuario con rol Vendedor solo ve, en Resumen de Ventas y "
            "en Reportes, las ventas que él mismo generó — nunca las de "
            "otro vendedor. El filtro 'Vendedor' de Reportes queda fijo "
            "en su propio nombre y bloqueado, con el aviso '🔒 solo tus "
            "ventas'.\n\n"
            "Gerente y Administrador, en cambio, ven las ventas de TODOS "
            "los usuarios (incluidas las propias) y sí pueden usar el "
            "filtro 'Vendedor' libremente para ver 'Todos' o elegir a "
            "cualquiera en particular.\n\n"
            "Esta regla se aplica también a todo lo que se exporta o "
            "envía por correo desde esas pantallas (PDF, Excel, Word, "
            "CSV, JSON): un Vendedor solo exporta o envía sus propias "
            "ventas.\n\n"
            "El arqueo de caja (Saldo Inicial, Entradas, Salidas, Dinero "
            "en Caja) es la única excepción: siempre muestra el total "
            "real del cajón compartido por todos, sin filtrar por "
            "usuario, para que el arqueo del día cuadre con el efectivo "
            "físico."
        ),
    },
    {
        "categoria": "📊 Reportes",
        "clave": "reportes_general",
        "titulo": "Cómo funciona el módulo Reportes",
        "modulo": "reportes",
        "texto": (
            "El módulo Reportes tiene tres pestañas: 'Ventas', 'Compras' "
            "y 'Presupuestos', cada una con su propio registro completo, "
            "filtros, tarjetas de resumen y exportación — independientes "
            "entre sí.\n\n"
            "En la pestaña Ventas se ven TODAS las ventas de TODOS los "
            "usuarios del sistema, no solo las propias.\n\n"
            "Filtros disponibles:\n"
            "• Rango de fechas (Desde/Hasta), con accesos rápidos: Hoy, "
            "Esta semana, Este mes, Este año.\n"
            "• Vendedor — filtra por el usuario que realizó la venta.\n"
            "• Estado — Todos, Pagado, Cancelado.\n"
            "• Búsqueda libre por cliente, factura o ID de venta.\n\n"
            "Tarjetas de resumen: cantidad de ventas, total vendido, "
            "efectivo, transferencia, crédito y canceladas, calculadas "
            "según los filtros activos.\n\n"
            "Al hacer click en una venta de la tabla se abre un panel "
            "lateral con el detalle completo: artículos, cantidades, "
            "devoluciones e importe total."
        ),
    },
    {
        "categoria": "📊 Reportes",
        "clave": "reportes_compras",
        "titulo": "Pestaña Compras del módulo Reportes",
        "modulo": "reportes",
        "texto": (
            "La pestaña 'Compras' funciona igual que la de Ventas, pero "
            "para las compras a proveedores:\n\n"
            "• Filtros por rango de fechas (con los mismos accesos "
            "rápidos), proveedor y búsqueda libre.\n"
            "• Tarjetas de resumen: cantidad de compras, total comprado, "
            "promedio por compra y proveedores distintos.\n"
            "• Al hacer click en una compra se ve el detalle completo de "
            "sus artículos.\n"
            "• Exportación en 7 formatos: PDF con dashboard (gráfico de "
            "compras por día, ranking de proveedores y de productos más "
            "comprados), PDF simple, Word, LibreOffice, Excel (con hojas "
            "de Resumen, Detalle de Compras y Detalle de Artículos), CSV "
            "y JSON."
        ),
    },
    {
        "categoria": "📊 Reportes",
        "clave": "reportes_presupuestos",
        "titulo": "Pestaña Presupuestos del módulo Reportes",
        "modulo": "reportes",
        "texto": (
            "La pestaña 'Presupuestos' sigue el mismo formato que las "
            "otras dos:\n\n"
            "• Filtros por rango de fechas y estado (Pendiente, Aprobado, "
            "Rechazado, Vencido, Convertido) y búsqueda libre por "
            "cliente.\n"
            "• Tarjetas de resumen: cantidad de presupuestos, total "
            "cotizado, cantidad convertidos en venta, y la Tasa de "
            "Conversión (% de presupuestos que terminaron en una venta "
            "real) — útil para medir qué tan efectivas son las "
            "cotizaciones del negocio.\n"
            "• Exportación en los mismos 7 formatos, incluido el PDF con "
            "dashboard (gráfico de presupuestos por día y ranking de "
            "productos más cotizados)."
        ),
    },

    # ── Cotizaciones ─────────────────────────────────────────────
    {
        "categoria": "💱 Cotizaciones",
        "clave": "cotizaciones_general",
        "titulo": "Tipos de cambio en tiempo real",
        "modulo": "cotizaciones",
        "texto": (
            "Muestra las cotizaciones del día, actualizadas automáticamente "
            "cada 10 minutos (y con un botón para forzar la actualización "
            "en cualquier momento). Se divide en dos sub-pestañas:\n\n"
            "• Dinero Fiduciario — cotización del Dólar, Real, Peso "
            "Argentino y otras monedas frente al Guaraní, con datos del "
            "Banco Central Europeo.\n"
            "• Cripto — cotización de las criptomonedas más usadas "
            "(Bitcoin, Ethereum, USDT, etc.), con datos de CoinGecko.\n\n"
            "Es una consulta informativa: no crea ni afecta ninguna venta "
            "ni movimiento del sistema, sirve como referencia rápida para "
            "quien necesite cotizar algo en otra moneda."
        ),
    },

    # ── Clima ────────────────────────────────────────────────────
    {
        "categoria": "⛅ Clima",
        "clave": "clima_general",
        "titulo": "Cómo funciona el módulo Clima",
        "modulo": "clima",
        "texto": (
            "Muestra el clima actual de cualquier departamento y ciudad/"
            "distrito de Paraguay, con un ícono animado del estado del "
            "cielo (sol con rayos girando, nubes que flotan, lluvia o "
            "nieve cayendo, rayos de tormenta que destellan), la "
            "temperatura, sensación térmica, humedad, viento (con "
            "dirección, ej. 'Sur Suroeste'), presión atmosférica y "
            "precipitación de la última hora.\n\n"
            "Debajo del clima actual hay tres secciones más:\n"
            "▸ 'Hoy' — pronóstico de la Tarde, la Noche y la Madrugada, "
            "cada una con su propio ícono, rango de temperatura y una "
            "descripción corta.\n"
            "▸ 'Pronóstico 5 días' — una tarjeta por día con su ícono, "
            "temperatura máxima/mínima y descripción. Se puede tocar "
            "cualquier día para ver su gráfico horario más abajo.\n"
            "▸ 'Evolución horaria' — un gráfico de línea con la "
            "temperatura hora por hora (00h a 23h) del día elegido "
            "arriba, marcando con un punto naranja la hora actual si "
            "corresponde al día de hoy.\n\n"
            "Se elige primero el Departamento y después la Ciudad/"
            "Distrito de la lista (los 17 departamentos de Paraguay, con "
            "sus principales ciudades y distritos). Se actualiza "
            "automáticamente cada 10 minutos, igual que Cotizaciones, y "
            "el botón '🔄 Actualizar' fuerza una actualización inmediata "
            "en cualquier momento.\n\n"
            "Los datos vienen de Open-Meteo, un servicio meteorológico "
            "público y gratuito con muy buena cobertura para Paraguay y "
            "el resto de Sudamérica. Necesita conexión a internet para "
            "actualizar; si falla la consulta, muestra un aviso claro en "
            "vez de datos inventados.\n\n"
            "Nota: la lista de ciudades/distritos es una selección amplia "
            "y curada (los 17 departamentos completos, con varias de sus "
            "ciudades más conocidas), no un listado oficial exhaustivo de "
            "los cerca de 260 distritos del país — para un distrito muy "
            "pequeño que no esté en la lista, se puede elegir la ciudad "
            "más cercana del mismo departamento."
        ),
    },

    # ── Calculadora ──────────────────────────────────────────────
    {
        "categoria": "🧮 Calculadora",
        "clave": "calculadora_general",
        "titulo": "Cómo funciona la Calculadora",
        "modulo": None,
        "texto": (
            "Se abre desde el ícono de calculadora en la barra superior, "
            "disponible para cualquier usuario logueado sin importar su "
            "rol o permisos. Es una ventana independiente, inspirada en "
            "la app Calculadora de Windows 11, con un menú lateral (☰) "
            "para elegir entre varios modos:\n\n"
            "▸ Estándar y Científica — con operaciones básicas y "
            "avanzadas (trigonometría, logaritmos, potencias, etc.).\n"
            "▸ Programador — conversión entre HEX, DEC, OCT y BIN, con "
            "operadores AND/OR/XOR y desplazamiento de bits.\n"
            "▸ Gráfica — grafica una función f(x) ingresada a mano.\n"
            "▸ Cálculo de fecha — diferencia en días entre dos fechas.\n"
            "▸ Convertidor — moneda (con tipo de cambio en tiempo real) y "
            "más de una decena de unidades (volumen, longitud, peso, "
            "temperatura, energía, área, velocidad, tiempo, potencia, "
            "datos, presión y ángulo).\n\n"
            "El botón 🕐 muestra el historial de resultados (en Estándar "
            "y Científica), y el botón ⤢ fija la ventana 'siempre "
            "encima' de las demás.\n\n"
            "Se puede operar tanto con el mouse (botones en pantalla) "
            "como con el teclado: números, +, -, *, /, punto/coma "
            "decimal, Enter para '=', Backspace para borrar el último "
            "carácter, Supr para CE y Escape para C — funciona apenas se "
            "abre la ventana, sin necesidad de hacer clic primero en "
            "ningún botón."
        ),
    },

    # ── Usuarios (admin) ─────────────────────────────────────────
    {
        "categoria": "⚙ Usuarios (Administrador)",
        "clave": "usuarios_general",
        "titulo": "Cómo funciona el módulo Usuarios",
        "modulo": "usuarios",
        "texto": (
            "Solo accesible para Administradores. Permite crear, editar, "
            "habilitar/deshabilitar y eliminar usuarios del sistema.\n\n"
            "El formulario de usuario tiene 4 pestañas:\n"
            "▸ Datos básicos — nombre, usuario de login, contraseña, rol "
            "(Administrador, Gerente o Vendedor) y estado (activo/"
            "inactivo).\n"
            "▸ Perfil — correo electrónico, teléfono, fecha de nacimiento "
            "(con cálculo automático de edad), dirección y observaciones.\n"
            "▸ Foto — foto de perfil con vista previa circular, visible "
            "luego en la barra superior del sistema.\n"
            "▸ Permisos — qué módulos puede ver un usuario con rol "
            "Gerente o Vendedor. Los Administradores tienen acceso total "
            "automáticamente, sin necesidad de marcar permisos "
            "individuales.\n\n"
            "Al crear o editar un usuario Gerente o Vendedor, hay que "
            "marcarle al menos un módulo en la pestaña Permisos: si se "
            "intenta guardar sin ninguno marcado, el sistema avisa con un "
            "mensaje de error y salta directo a esa pestaña, sin permitir "
            "guardar hasta asignar algo. Solo un Administrador puede "
            "marcar o cambiar esos permisos, desde este módulo — un "
            "usuario nunca puede auto-asignarse módulos, ni siquiera "
            "editando su propio perfil ('Mi Perfil' desde la barra "
            "superior no muestra la pestaña Permisos).\n\n"
            "El panel de detalle (a la derecha de la grilla, con los "
            "datos y la lista de permisos del usuario seleccionado) tiene "
            "scroll propio, así que aunque un usuario tenga muchos "
            "módulos asignados siempre se pueden ver todos desplazándose "
            "hacia abajo."
        ),
    },
    {
        "categoria": "⚙ Usuarios (Administrador)",
        "clave": "usuarios_permisos",
        "titulo": "Sistema de permisos y roles",
        "modulo": "usuarios",
        "texto": (
            "Hay tres roles: Administrador, Gerente y Vendedor.\n\n"
            "Administrador: acceso a TODOS los módulos sin excepción, "
            "incluidos los exclusivos de administración (Usuarios, "
            "Licencias, Uso del sistema, Gestión de Datos y Reinicio del "
            "Sistema).\n\n"
            "Gerente: solo ve los módulos que el administrador le haya "
            "marcado explícitamente, igual que el Vendedor, pero con una "
            "diferencia clave: SÍ puede recibir acceso a módulos "
            "administrativos si el administrador se lo asigna (por "
            "ejemplo, RRHH o Gestión de Datos), a diferencia del "
            "Vendedor.\n\n"
            "Vendedor: solo ve los módulos operativos que el administrador "
            "le haya marcado explícitamente (Ventas, Productos, Inventario, "
            "Clientes, Reportes). Nunca tiene acceso a los módulos "
            "exclusivos de administración, sin importar los permisos "
            "marcados."
        ),
    },

    # ── Recursos Humanos (admin) ─────────────────────────────────
    {
        "categoria": "🧑‍💼 Recursos Humanos (Administrador)",
        "clave": "rrhh_general",
        "titulo": "Cómo funciona el módulo Recursos Humanos",
        "modulo": "rrhh",
        "texto": (
            "Solo accesible para Administradores. Permite llevar la ficha "
            "de cada empleado (cargo, departamento, teléfono, email, fecha "
            "de ingreso, sueldo mensual y horas por día), registrar su "
            "asistencia día a día (Presente, Falta, Tardanza, Licencia, "
            "etc., con hora de entrada y salida) y adelantos de sueldo, "
            "con su estado (Pendiente/Descontado) y la fecha en que se "
            "descontó.\n\n"
            "El resumen de un período calcula automáticamente la "
            "liquidación de cada empleado (sueldo proporcional según "
            "asistencia, menos los adelantos pendientes de descuento), "
            "para tener el número listo a la hora de pagar."
        ),
    },
    {
        "categoria": "🧑‍💼 Recursos Humanos (Administrador)",
        "clave": "rrhh_asistencia_adelantos",
        "titulo": "Registrar asistencia y adelantos",
        "modulo": "rrhh",
        "texto": (
            "La asistencia se carga por empleado y por día, eligiendo el "
            "estado correspondiente; si el empleado marcó entrada y "
            "salida, se puede cargar el horario real trabajado ese día.\n\n"
            "Los adelantos de sueldo se registran con fecha, monto y "
            "descripción; quedan en estado 'Pendiente' hasta que se marcan "
            "como descontados (por ejemplo, al liquidar el sueldo del "
            "período), momento en que se guarda la fecha de descuento. "
            "El resumen de RRHH muestra el total de adelantos pendientes "
            "de cada empleado, para no perder ese dato a la hora de "
            "calcular cuánto corresponde pagarle.\n\n"
            "El panel inferior de la pestaña Personal muestra 4 datos: "
            "empleados activos, total de sueldos del mes, adelantos "
            "pendientes, y 'Resta del sueldo' (lo que efectivamente "
            "quedaría por pagar después de descontar los adelantos "
            "pendientes). Todo esto se actualiza al instante apenas se "
            "agrega un empleado o se registra/marca/elimina un adelanto, "
            "sin importar en qué pestaña estés parado."
        ),
    },

    # ── Licencias (admin) ────────────────────────────────────────
    {
        "categoria": "🔑 Licencias (Administrador)",
        "clave": "licencias_general",
        "titulo": "Cómo funciona el módulo Licencias",
        "modulo": "licencia",
        "texto": (
            "Solo accesible para Administradores. Permite generar y "
            "administrar los seriales de licencia que habilitan el uso del "
            "sistema durante un período determinado.\n\n"
            "Cada licencia tiene una duración (mensual, anual, días, horas, "
            "o ilimitada) y un serial único. Al activarse, el sistema queda "
            "habilitado hasta la fecha de vencimiento correspondiente.\n\n"
            "Sin una licencia vigente, el sistema obliga a activar una "
            "antes de poder iniciar sesión."
        ),
    },

    # ── Uso del sistema (admin) ──────────────────────────────────
    {
        "categoria": "⏱ Uso del sistema (Administrador)",
        "clave": "uso_general",
        "titulo": "Cómo funciona Uso del sistema",
        "modulo": "uso",
        "texto": (
            "Solo accesible para Administradores. Muestra estadísticas de "
            "uso del sistema: tiempo total conectado por usuario, horarios "
            "de mayor actividad, y el historial de sesiones (cuándo entró y "
            "salió cada usuario, y por cuánto tiempo)."
        ),
    },

    # ── Gestión de Datos (admin) ─────────────────────────────────
    {
        "categoria": "💾 Gestión de Datos (Administrador)",
        "clave": "datos_general",
        "titulo": "Cómo funciona Gestión de Datos",
        "modulo": "datos",
        "texto": (
            "Solo accesible para Administradores. Permite hacer copias de "
            "seguridad y exportar/importar información:\n\n"
            "▸ Exportar copia de seguridad — guarda el archivo completo de "
            "la base de datos (.db) en una ubicación elegida.\n"
            "▸ Importar copia de seguridad — restaura la base de datos "
            "desde un archivo .db previo (hace un respaldo automático antes "
            "de reemplazar, por seguridad).\n"
            "▸ Exportar/Importar Excel — genera o lee un libro .xlsx con "
            "hojas de Productos, Clientes, Ventas, Detalle de Ventas, "
            "Inventario y Movimientos de Inventario (en esta última, los "
            "movimientos de productos con stock 'Ilimitado' muestran "
            "'Ilimitado' en vez de un número en Cantidad y Stock "
            "Resultante, igual que en la pantalla de Historial de "
            "Movimientos).\n"
            "▸ Exportar/Importar CSV — mismo concepto que Excel, pero en "
            "archivos .csv individuales por tabla, con detección automática "
            "del separador al importar.\n"
            "▸ Terminal SQL — en la sección 'Avanzado', un acceso directo "
            "para abrir el Terminal SQL sin salir de esta pantalla (ver "
            "categoría 'Terminal SQL' en este mismo panel de Ayuda)."
        ),
    },

    # ── Terminal SQL (admin) ──────────────────────────────────────
    {
        "categoria": "🖥 Terminal SQL (Administrador)",
        "clave": "terminal_sql_general",
        "titulo": "Cómo funciona el Terminal SQL",
        "modulo": "terminal",
        "texto": (
            "Solo accesible para Administradores. Permite ejecutar consultas "
            "SQL directamente sobre la base de datos del sistema — una "
            "herramienta avanzada para correcciones puntuales o consultas de "
            "diagnóstico que las pantallas normales no cubren.\n\n"
            "A la izquierda, la lista de 'Tablas' (doble click en una carga "
            "y ejecuta automáticamente un 'SELECT * FROM esa tabla LIMIT "
            "100') y el 'Historial' de las últimas consultas ejecutadas "
            "(doble click para volver a cargarlas en el editor).\n\n"
            "A la derecha, el editor SQL: se escribe la consulta y se "
            "ejecuta con el botón '▶ Ejecutar', la tecla F5, o Ctrl+Enter. "
            "Los resultados de un SELECT aparecen en la grilla de abajo "
            "(hasta 500 filas a la vez); para INSERT/UPDATE/DELETE/CREATE/"
            "ALTER/DROP, se muestra la cantidad de filas afectadas.\n\n"
            "Solo se puede ejecutar UNA sentencia por vez (no se admiten "
            "varias separadas por ';' en una sola ejecución)."
        ),
    },
    {
        "categoria": "🖥 Terminal SQL (Administrador)",
        "clave": "terminal_sql_seguridad",
        "titulo": "Medidas de seguridad: modo solo lectura y backup automático",
        "modulo": "terminal",
        "texto": (
            "Por ser una herramienta tan directa, el Terminal SQL incluye "
            "varias protecciones activas:\n\n"
            "▸ 'Modo solo lectura' — viene activado por defecto (candado "
            "🔒 tildado) y solo permite SELECT, PRAGMA, EXPLAIN y WITH. "
            "Cualquier consulta que modifique datos o el esquema (INSERT, "
            "UPDATE, DELETE, CREATE, ALTER, DROP, etc.) queda bloqueada "
            "hasta destildar el candado a propósito.\n"
            "▸ Confirmación obligatoria — con el modo solo lectura "
            "destildado, toda consulta de escritura pide confirmación "
            "mostrando el texto completo antes de ejecutarla.\n"
            "▸ Backup automático — justo antes de ejecutar cualquier "
            "consulta de escritura confirmada, el sistema genera solo, sin "
            "pedirlo, una copia de seguridad completa de la base de datos "
            "(el mismo mecanismo de Gestión de Datos), para poder "
            "restaurarla si algo sale mal.\n"
            "▸ Alerta reforzada sin WHERE — si un UPDATE o DELETE no tiene "
            "cláusula WHERE (lo que afectaría TODAS las filas de la "
            "tabla), el aviso de confirmación lo remarca especialmente "
            "antes de dejar continuar."
        ),
    },

    # ── Asistente IA (admin) ──────────────────────────────────────
    {
        "categoria": "🤖 Asistente IA (Administrador)",
        "clave": "asistente_ia_general",
        "titulo": "Cómo funciona el Asistente IA",
        "modulo": "ia",
        "texto": (
            "Chat con una IA real (no reglas fijas) integrada al sistema, para "
            "cuatro cosas principales:\n\n"
            "▸ Responder preguntas sobre cómo usar MaquedaSystems, en lenguaje "
            "natural.\n"
            "▸ Analizar el negocio — botón '📊 Analizar mis ventas': arma "
            "automáticamente un resumen de los últimos 30 días (total vendido, "
            "ganancia, productos más vendidos) y le pide a la IA "
            "recomendaciones concretas.\n"
            "▸ Generar descripciones de productos — botón '✨ Generar "
            "descripción de producto': se cuentan las características del "
            "producto y la IA redacta un texto breve, listo para pegar en el "
            "campo Descripción.\n"
            "▸ Traducir un texto puntual — botón '🌐 Traducir texto': se "
            "pega o escribe cualquier texto (una descripción, una "
            "observación, etc.), se elige el idioma destino de una lista o "
            "se escribe uno libre, y la IA devuelve la traducción. Es "
            "independiente del módulo Idioma: sirve para traducir un dato "
            "puntual bajo pedido, no cambia nada de la interfaz.\n"
            "▸ Chat libre para cualquier otra consulta.\n\n"
            "El botón '🧹 Nueva conversación' borra el historial del chat "
            "actual (no borra nada de la base de datos, solo reinicia la "
            "charla). Enter envía el mensaje; Shift+Enter inserta un salto de "
            "línea sin enviar."
        ),
    },
    {
        "categoria": "🤖 Asistente IA (Administrador)",
        "clave": "asistente_ia_configuracion",
        "titulo": "Configurar el Asistente IA: proveedor, costo y privacidad",
        "modulo": "ia",
        "texto": (
            "Antes de poder usarlo, un Administrador tiene que configurarlo "
            "con el botón '⚙ Configurar' (arriba a la derecha del propio "
            "módulo Asistente IA), o desde el botón '⚙ Configurar Asistente "
            "IA' que aparece en el módulo mientras no haya ninguna "
            "configuración guardada.\n\n"
            "Se elige un proveedor (OpenAI/ChatGPT, Anthropic/Claude, u otro "
            "compatible como DeepSeek/Groq/OpenRouter/un servidor propio) y "
            "se pega una clave de API propia, generada desde la web de ese "
            "proveedor (la pantalla de configuración explica los pasos según "
            "cuál se elija). El botón '🔌 Probar Conexión' permite verificar "
            "que la clave funciona antes de guardarla.\n\n"
            "Importante:\n"
            "• Tiene un costo real, cobrado por el proveedor elegido según el "
            "uso — MaquedaSystems no cobra nada por esto ni administra ese "
            "pago.\n"
            "• Necesita conexión a internet.\n"
            "• Lo que se le pregunte o los datos de ventas que se le pidan "
            "analizar viajan al proveedor de IA elegido.\n"
            "• Solo el Administrador puede ver/cambiar la clave de API "
            "configurada; a un Gerente se le puede dar acceso al chat sin "
            "darle acceso a la configuración."
        ),
    },

    # ── Idioma (admin) ────────────────────────────────────────────
    {
        "categoria": "🌐 Idioma (Administrador)",
        "clave": "idioma_general",
        "titulo": "Cómo funciona el módulo Idioma",
        "modulo": "idioma",
        "texto": (
            "Solo accesible para Administradores. Permite elegir el idioma "
            "de la interfaz del sistema (menús, botones, títulos) entre "
            "Español, Guaraní, Português, English, Русский (ruso), 中文 "
            "(chino), 한국어 (coreano), Українська (ucraniano) y العربية "
            "(árabe). Es una configuración del sistema completo (una "
            "sola, no por usuario): al elegir un idioma, se aplica para "
            "todos los que inicien sesión después.\n\n"
            "El cambio se ve reflejado la próxima vez que se inicia sesión "
            "(no hace falta reinstalar nada, solo cerrar sesión y volver a "
            "entrar).\n\n"
            "Importante — qué SÍ traduce y qué NO:\n"
            "▸ SÍ traduce: el menú lateral, el título de la ventana, el "
            "botón 'Cerrar sesión' y las etiquetas de rol (Admin/Gerente/"
            "Vendedor) de la barra superior.\n"
            "▸ NO traduce los datos que ya cargaste en el sistema (nombres "
            "de clientes, descripciones de productos, observaciones, "
            "etc.) — esos quedan tal cual los escribiste, en el idioma que "
            "sea. Para traducir un dato puntual, usá el botón "
            "'🌐 Traducir texto' del Asistente IA.\n"
            "▸ Por ahora, el contenido interno de cada módulo (los campos y "
            "botones específicos de Ventas, Productos, Reportes, etc.) "
            "sigue en español; la traducción completa pantalla por "
            "pantalla es un trabajo en curso.\n\n"
            "Nota sobre calidad: las traducciones al Guaraní, ruso, chino, "
            "coreano, ucraniano y árabe son una primera versión hecha con "
            "criterio por esta misma IA, no revisada por un hablante "
            "nativo de cada idioma — se recomienda que alguien nativo las "
            "revise antes de un uso 100% oficial. Para términos técnicos "
            "modernos sin equivalente natural (Terminal SQL, Asistente "
            "IA, Reportes) se optó por una traducción descriptiva "
            "razonable en vez de forzar un calco artificial.\n\n"
            "El árabe se escribe de derecha a izquierda (RTL); el sistema "
            "NO invierte automáticamente la disposición de los menús "
            "(limitación de la librería gráfica usada), así que el texto "
            "se lee bien pero queda alineado a la izquierda. Chino, "
            "coreano, ruso y ucraniano necesitan que Windows tenga "
            "instalados sus paquetes de idioma/fuentes correspondientes "
            "(la mayoría de instalaciones de Windows 10/11 ya los traen); "
            "si en vez de texto aparecen cuadros vacíos, hay que "
            "instalar el paquete de idioma correspondiente desde la "
            "Configuración de Windows."
        ),
    },

    # ── Novedades ────────────────────────────────────────────────
    {
        "categoria": "🗒 Novedades",
        "clave": "novedades_general",
        "titulo": "Cómo funciona el módulo Novedades y el versionado",
        "modulo": "novedades",
        "texto": (
            "Novedades es el historial/changelog del sistema: cada tarjeta "
            "representa una actualización, mostrando fecha, una etiqueta "
            "de color (🟢 Nuevo, 🔵 Mejora, 🟠 Corrección) y el detalle de "
            "qué cambió. Se muestran de la más reciente a la más antigua, "
            "y la primera tarjeta lleva la marca '★ Última actualización'.\n\n"
            "Desde esta versión, cada tarjeta también muestra su número de "
            "versión (por ejemplo 'v1.40.0'), siguiendo versionado "
            "semántico MAJOR.MINOR.PATCH:\n\n"
            "▸ Cada novedad etiquetada 'Nuevo' sube el número MINOR (ej. "
            "1.5.3 → 1.6.0): significa que se agregó una función o módulo "
            "nuevo.\n"
            "▸ Cada novedad etiquetada 'Mejora' o 'Corrección' sube el "
            "número PATCH (ej. 1.6.0 → 1.6.1): son cambios más chicos "
            "sobre algo que ya existía.\n\n"
            "La numeración arrancó en la versión 1.0.0 (la primera entrada "
            "histórica, al final de la lista) y la versión de la tarjeta "
            "de arriba de todo es siempre la versión ACTUAL del sistema — "
            "se muestra también como una etiqueta 'v X.X.X' en la esquina "
            "superior derecha del propio módulo Novedades."
        ),
    },

    # ── Reinicio del Sistema (admin) ─────────────────────────────
    {
        "categoria": "♻ Reinicio del Sistema (Administrador)",
        "clave": "reinicio_general",
        "titulo": "Cómo funciona Reinicio del Sistema",
        "modulo": "reinicio",
        "texto": (
            "Solo accesible para Administradores. Permite borrar datos de "
            "forma PERMANENTE para volver a empezar. Dos modalidades:\n\n"
            "▸ Reiniciar datos del negocio — borra productos, ventas, "
            "clientes, inventario, caja, compras, créditos, devoluciones, "
            "presupuestos, préstamos (con sus cuotas y pagos), asistencia "
            "técnica, veterinaria, restaurante/comedor y alquiler de "
            "streaming. Conserva los usuarios, la licencia activa, los "
            "puntajes de Juegos y la Biblia ya descargada.\n\n"
            "▸ Reinicio total de fábrica — borra absolutamente todo lo "
            "anterior Y TAMBIÉN los usuarios (y sus puntajes de Juegos). El "
            "sistema queda como recién instalado: pedirá crear el primer "
            "administrador al volver a abrirse. La licencia activa se "
            "conserva siempre.\n\n"
            "En ambas modalidades se conservan además las configuraciones "
            "de servicios externos y preferencias del sistema que no "
            "tiene sentido perder en un reinicio de datos: las cuentas de "
            "correo guardadas en Configurar Email, la configuración del "
            "Asistente IA (proveedor y clave de API), el idioma elegido "
            "en el módulo Idioma, la apariencia (tema y fuente), la "
            "Configuración del Local para comprobantes y facturas (nombre, "
            "RUC, timbrado, formato e impresora elegidos), y los libros de "
            "la Biblia ya descargados (para no tener que volver a "
            "bajarlos). En cambio, la numeración correlativa de "
            "comprobantes y facturas SÍ se reinicia a 0 en ambas "
            "modalidades, ya que está directamente ligada a las ventas "
            "que se acaban de borrar.\n\n"
            "La pantalla de Reinicio muestra un resumen con la cantidad de "
            "registros actuales de cada módulo — con desplazamiento lateral "
            "si no entran todos en el ancho de la ventana — y una "
            "verificación automática que avisa si alguna vez queda una "
            "tabla nueva sin cubrir por el reinicio (para detectar rápido "
            "cualquier módulo futuro que se agregue).\n\n"
            "Ambas opciones requieren, como confirmación de seguridad, "
            "escribir una palabra exacta e ingresar usuario y contraseña de "
            "un administrador antes de ejecutarse. Esta acción NO se puede "
            "deshacer."
        ),
    },

    # ── Juegos y Entretenimiento ──────────────────────────────────
    {
        "categoria": "🎮 Juegos",
        "clave": "juegos_general",
        "titulo": "Cómo funciona el módulo Juegos",
        "modulo": "juegos",
        "texto": (
            "Un mini arcade a color con 6 juegos clásicos para una pausa "
            "recreativa: Solitario, Buscaminas, Tetris, Snake, Pong y "
            "Pac-Man.\n\n"
            "Al abrir el módulo se ve un lanzador con una tarjeta por "
            "juego, mostrando tu mejor puntaje personal en cada uno. Al "
            "elegir un juego se abre a pantalla completa dentro del "
            "módulo, con sus propios controles e instrucciones.\n\n"
            "Cada partida guarda automáticamente el puntaje obtenido al "
            "finalizar (ganes o pierdas), asociado al usuario que tiene la "
            "sesión iniciada."
        ),
    },
    {
        "categoria": "🎮 Juegos",
        "clave": "juegos_ranking",
        "titulo": "Ranking de Usuarios",
        "modulo": "juegos",
        "texto": (
            "Desde el botón '🏆 Ver ranking de usuarios' en la parte "
            "superior del lanzador se accede a la tabla de posiciones.\n\n"
            "▸ Pestaña 'Ranking general' — suma, para cada usuario, su "
            "MEJOR puntaje en cada uno de los juegos que jugó (no premia "
            "solo por jugar mucho un único juego). Los primeros 3 puestos "
            "se resaltan con medalla de oro, plata y bronce.\n\n"
            "▸ Una pestaña por cada juego — la tabla de líderes de ESE "
            "juego en particular, con el mejor puntaje de cada usuario y "
            "la fecha en que lo logró."
        ),
    },

    # ── Biblia ───────────────────────────────────────────────────
    {
        "categoria": "📖 Biblia",
        "clave": "biblia_general",
        "titulo": "Cómo funciona el módulo Biblia",
        "modulo": "biblia",
        "texto": (
            "Permite leer la Biblia completa (versión Reina-Valera, 66 "
            "libros), organizada en 3 pestañas: Antiguo Testamento (39 "
            "libros), Nuevo Testamento (27 libros) y Santa Biblia Completa "
            "(los 66 juntos).\n\n"
            "En cada pestaña, la lista de la izquierda muestra todos los "
            "libros: los que ya se descargaron aparecen marcados con 📥 y "
            "los que todavía no, con ☁. Al elegir un libro se descarga "
            "automáticamente la primera vez (necesita conexión a "
            "Internet) y después queda guardado localmente: las próximas "
            "veces se abre al instante, sin conexión.\n\n"
            "Elegido el libro, un selector permite moverse entre "
            "capítulos. El botón '🔄 Actualizar de Internet' vuelve a "
            "descargar ese libro puntual si hiciera falta."
        ),
    },
    {
        "categoria": "📖 Biblia",
        "clave": "biblia_descargas_buscador",
        "titulo": "Descargar todo y buscar texto",
        "modulo": "biblia",
        "texto": (
            "▸ '⬇ Descargar todos los libros faltantes' — descarga de una "
            "sola vez todos los libros de ESA pestaña que todavía no se "
            "hayan bajado, mostrando el progreso libro por libro. Útil "
            "para dejar todo un testamento disponible sin conexión de "
            "antemano.\n\n"
            "▸ Buscador (🔎, abajo de la lista de libros) — busca una "
            "palabra dentro de los libros YA DESCARGADOS de esa pestaña, y "
            "muestra cada versículo donde aparece con su referencia "
            "(libro, capítulo y versículo). No busca en libros que "
            "todavía no se bajaron: si no aparece lo que buscás, probá "
            "descargar más libros primero."
        ),
    },
]


# ─────────────────────────────────────────────────────────────
#  PANEL PRINCIPAL DE AYUDA
# ─────────────────────────────────────────────────────────────
class PanelAyuda(tk.Frame):
    def __init__(self, parent, usuario_actual):
        super().__init__(parent, bg=BLANCO)
        self.usuario_actual = usuario_actual
        self.tema_actual = None
        self._construir_ui()
        self._cargar_arbol()
        self._seleccionar_primer_tema_disponible()

    # ── UI raíz ──────────────────────────────────────────────────
    def _construir_ui(self):
        encabezado = tk.Frame(self, bg=AZUL, height=54)
        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)
        tk.Label(encabezado, text=t("ayuda_titulo"),
                 font=("Segoe UI", 15, "bold"), bg=AZUL, fg=BLANCO
                 ).pack(side="left", padx=20, pady=12)

        cuerpo = tk.Frame(self, bg=BLANCO)
        cuerpo.pack(fill="both", expand=True)
        cuerpo.grid_columnconfigure(0, weight=0, minsize=300)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)

        self._construir_panel_izquierdo(cuerpo)
        self._construir_panel_derecho(cuerpo)

    # ── Panel izquierdo: buscador + árbol de temas ──────────────
    def _construir_panel_izquierdo(self, parent):
        panel = tk.Frame(parent, bg=GRIS_FONDO)
        panel.grid(row=0, column=0, sticky="nsew")

        f_busq = tk.Frame(panel, bg=GRIS_FONDO)
        f_busq.pack(fill="x", padx=10, pady=10)
        tk.Label(f_busq, text="🔍", font=("Segoe UI", 11),
                 bg=GRIS_FONDO).pack(side="left")
        self.var_busqueda = tk.StringVar()
        entry = tk.Entry(f_busq, textvariable=self.var_busqueda,
                         font=("Segoe UI", 9))
        entry.pack(side="left", fill="x", expand=True, padx=(4, 0), ipady=4)
        self.var_busqueda.trace_add("write", lambda *_: self._cargar_arbol())

        frame_arbol = tk.Frame(panel, bg=GRIS_FONDO)
        frame_arbol.pack(fill="both", expand=True, padx=(8, 0), pady=(0, 8))

        style = ttk.Style()
        style.configure("Ayuda.Treeview", font=("Segoe UI", 9), rowheight=26,
                        background=BLANCO, fieldbackground=BLANCO)

        self.arbol = ttk.Treeview(frame_arbol, show="tree",
                                   style="Ayuda.Treeview", selectmode="browse")
        habilitar_deseleccion_treeview(self.arbol)
        frame_arbol.grid_rowconfigure(0, weight=1)
        frame_arbol.grid_columnconfigure(0, weight=1)
        sb = ttk.Scrollbar(frame_arbol, orient="vertical", command=self.arbol.yview)
        sb_h = ttk.Scrollbar(frame_arbol, orient="horizontal", command=self.arbol.xview)
        self.arbol.configure(yscrollcommand=sb.set, xscrollcommand=sb_h.set)
        self.arbol.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        sb_h.grid(row=1, column=0, sticky="ew")

        self.arbol.bind("<<TreeviewSelect>>", self._al_seleccionar_tema)

    # ── Panel derecho: contenido del tema seleccionado ──────────
    def _construir_panel_derecho(self, parent):
        panel = tk.Frame(parent, bg=BLANCO)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        self.frame_titulo = tk.Frame(panel, bg=BLANCO)
        self.frame_titulo.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))
        self.lbl_categoria = tk.Label(self.frame_titulo, text="",
                                      font=("Segoe UI", 9), bg=BLANCO, fg=AZUL)
        self.lbl_categoria.pack(anchor="w")
        self.lbl_titulo_tema = tk.Label(self.frame_titulo, text="",
                                        font=("Segoe UI", 16, "bold"),
                                        bg=BLANCO, fg=NEGRO)
        self.lbl_titulo_tema.pack(anchor="w")
        tk.Frame(self.frame_titulo, bg=GRIS_BORDE, height=1).pack(
            fill="x", pady=(10, 0))

        cont_scroll = tk.Frame(panel, bg=BLANCO)
        cont_scroll.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        cont_scroll.grid_rowconfigure(0, weight=1)
        cont_scroll.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(cont_scroll, bg=BLANCO, highlightthickness=0)
        sb2 = ttk.Scrollbar(cont_scroll, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb2.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        sb2.grid(row=0, column=1, sticky="ns")

        self.frame_contenido_texto = tk.Frame(canvas, bg=BLANCO)
        self._ventana_canvas = canvas.create_window(
            (0, 0), window=self.frame_contenido_texto, anchor="nw")

        def _scrollregion(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _ajustar_ancho(event):
            canvas.itemconfig(self._ventana_canvas, width=event.width)
            self.lbl_cuerpo_texto.configure(wraplength=max(event.width - 10, 200))

        self.frame_contenido_texto.bind("<Configure>", _scrollregion)
        canvas.bind("<Configure>", _ajustar_ancho)

        def _rueda(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
            else:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        for w in (canvas, self.frame_contenido_texto):
            w.bind("<MouseWheel>", _rueda)
            w.bind("<Button-4>", _rueda)
            w.bind("<Button-5>", _rueda)

        self.lbl_cuerpo_texto = tk.Label(
            self.frame_contenido_texto, text="",
            font=("Segoe UI", 10), bg=BLANCO, fg="#374151",
            justify="left", anchor="nw", wraplength=600,
        )
        self.lbl_cuerpo_texto.pack(fill="x", anchor="nw")

    # ── Filtrado por permisos y búsqueda ─────────────────────────
    def _temas_visibles(self):
        from auth import usuario_tiene_acceso

        texto_busqueda = self.var_busqueda.get().strip().lower()
        resultado = []
        for tema in TEMAS_AYUDA:
            modulo = tema["modulo"]
            if modulo is not None and not usuario_tiene_acceso(self.usuario_actual, modulo):
                continue
            if texto_busqueda:
                if (texto_busqueda not in tema["titulo"].lower()
                        and texto_busqueda not in tema["texto"].lower()
                        and texto_busqueda not in tema["categoria"].lower()):
                    continue
            resultado.append(tema)
        return resultado

    # ── Construcción del árbol ───────────────────────────────────
    def _cargar_arbol(self):
        seleccion_previa = self.tema_actual
        for item in self.arbol.get_children():
            self.arbol.delete(item)

        temas = self._temas_visibles()
        categorias_creadas = {}
        for tema in temas:
            cat = tema["categoria"]
            if cat not in categorias_creadas:
                nodo_cat = self.arbol.insert("", "end", text=cat, open=True,
                                             tags=("categoria",))
                categorias_creadas[cat] = nodo_cat
            self.arbol.insert(categorias_creadas[cat], "end",
                              iid=tema["clave"], text="    " + tema["titulo"])

        self.arbol.tag_configure("categoria", font=("Segoe UI", 9, "bold"))

        if seleccion_previa and self.arbol.exists(seleccion_previa):
            self.arbol.selection_set(seleccion_previa)
            self.arbol.see(seleccion_previa)

    def _seleccionar_primer_tema_disponible(self):
        temas = self._temas_visibles()
        if temas:
            self.arbol.selection_set(temas[0]["clave"])
            self._mostrar_tema(temas[0])

    def _al_seleccionar_tema(self, event=None):
        seleccion = self.arbol.selection()
        if not seleccion:
            return
        clave = seleccion[0]
        tema = next((t for t in TEMAS_AYUDA if t["clave"] == clave), None)
        if tema:
            self._mostrar_tema(tema)

    def _mostrar_tema(self, tema: dict):
        self.tema_actual = tema["clave"]
        self.lbl_categoria.config(text=tema["categoria"])
        self.lbl_titulo_tema.config(text=tema["titulo"])
        self.lbl_cuerpo_texto.config(text=tema["texto"])
