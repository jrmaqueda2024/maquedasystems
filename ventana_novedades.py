"""
ventana_novedades.py
Módulo de Novedades: muestra, a modo de historial/changelog, las mejoras
y funciones nuevas que se van agregando al sistema. Pensado para que
cualquier usuario (admin o vendedor) se entere rápido de qué cambió,
sin tener que leer manuales largos.

Accesible para todos los usuarios (no está en MODULOS_SOLO_ADMIN), igual
que el módulo de Ayuda.
"""
import tkinter as tk
from tkinter import ttk
import fuentes
import temas
from traducciones import t

AZUL        = "#1d5fd6"
AZUL_OSC    = "#163d8c"
MORADO      = "#7c3aed"
GRIS_FONDO  = "#f4f5f7"
GRIS_BORDE  = "#e2e8f0"
BLANCO      = "#ffffff"
VERDE       = "#16a34a"
NARANJA     = "#d97706"
GRIS_TEXTO  = "#6b7280"
NEGRO       = "#1e293b"


# ─────────────────────────────────────────────────────────────
#  CONTENIDO DE NOVEDADES
# Cada entrada representa una actualización del sistema. Se muestran
# de la más reciente a la más antigua. Al agregar una función nueva al
# sistema, se debe sumar una entrada nueva ARRIBA de esta lista.
#
# Campos:
#   fecha      -> texto libre, ej. "Julio 2026"
#   titulo     -> resumen corto de la novedad
#   etiqueta   -> "Nuevo", "Mejora" o "Corrección" (define el color)
#   version    -> número de versión del sistema en ese momento (ver
#                 abajo cómo se calcula)
#   detalles   -> lista de puntos explicando el cambio
#
# VERSIONADO: la primera entrada histórica (la última de esta lista,
# la más antigua) es la versión 1.0.0. A partir de ahí, cada entrada
# nueva que se agrega ARRIBA sube la versión según el tipo de cambio,
# siguiendo versionado semántico (MAJOR.MINOR.PATCH):
#   • etiqueta "Nuevo"                    -> sube MINOR, reinicia PATCH a 0
#     (ej. 1.5.3 -> 1.6.0)
#   • etiqueta "Mejora" o "Corrección"     -> sube PATCH
#     (ej. 1.6.0 -> 1.6.1)
# La versión de la entrada de más arriba es siempre la versión ACTUAL
# del sistema (ver VERSION_ACTUAL más abajo, que se toma automáticamente
# de esta lista para no tener que mantenerla a mano en dos lugares).
# ─────────────────────────────────────────────────────────────
NOVEDADES = [
    {
        "fecha": "Agosto 2026",
        "titulo": "Corrección: precios podían guardarse mal en Nuevo Producto tras usar el lector de código de barras",
        "etiqueta": "Corrección",
        "version": "1.40.1",
        "detalles": [
            "Se agregó validación en tiempo real a los 4 campos de precio "
            "(Compra, Venta, Crédito y Mayorista): ahora descartan al "
            "instante cualquier carácter que no sea un dígito, igual que "
            "ya hacían los campos de Stock. Antes eran los únicos campos "
            "numéricos del formulario sin ese filtro, lo que en casos "
            "puntuales — por ejemplo, si el lector de código de barras "
            "dejaba el teclado en un estado inesperado por un instante — "
            "podía dejar un precio mal cargado sin que se notara hasta "
            "guardarlo.",
            "Además, justo antes de guardar, el sistema ahora relee el "
            "valor real mostrado en cada campo de precio directamente del "
            "cuadro de texto (no solo de la variable interna), como capa "
            "extra de seguridad para que lo que se guarda sea siempre "
            "exactamente lo que se ve en pantalla.",
            "Se reforzó también el manejo del Enter automático que envían "
            "los lectores de código de barras al terminar de escanear, "
            "con una segunda verificación explícita para garantizar que "
            "nunca dispare un guardado a mitad de carga.",
        ],
    },
    {
        "fecha": "Agosto 2026",
        "titulo": "Nuevo: filtros por Proveedor, Marca y Categoría en Productos, Inventario y Ventas (F2/F3)",
        "etiqueta": "Nuevo",
        "version": "1.40.0",
        "detalles": [
            "Se agregó una fila de filtros por Proveedor, Marca y "
            "Categoría (con 'Todos' como valor por defecto) en cuatro "
            "pantallas donde se busca un producto: el módulo Productos, "
            "el módulo Inventario, el buscador 'F2 — Buscar Producto' y "
            "'F3 — Consultar Stock' dentro de Ventas.",
            "Los tres filtros se pueden combinar entre sí y con el texto "
            "de búsqueda existente al mismo tiempo (por ejemplo: "
            "proveedor 'Distribuidora X' + categoría 'Bebidas' + texto "
            "'cola'), y hay un botón '✕ Limpiar filtros' para resetearlos "
            "los tres de un solo click.",
            "Si se crea, edita o elimina un proveedor, marca o categoría "
            "mientras la pantalla de Productos o Inventario está abierta "
            "(incluido desde el propio formulario de producto), las "
            "opciones de los combos de filtro se actualizan solas, sin "
            "tener que cerrar y volver a abrir el módulo.",
            "F3 — Consultar Stock, que antes no tenía filtros propios más "
            "allá de 'Solo con stock disponible', ahora los tiene "
            "igual que las otras tres pantallas.",
        ],
    },
    {
        "fecha": "Agosto 2026",
        "titulo": "Corrección: Reinicio del Sistema — clasificación de tablas y desplazamiento lateral",
        "etiqueta": "Corrección",
        "version": "1.39.3",
        "detalles": [
            "Se corrigió el aviso en rojo que aparecía en Reinicio del "
            "Sistema indicando 'tabla(s) nueva(s) sin clasificar: "
            "config_local, numeracion_comprobante'. Ambas tablas, del "
            "módulo de comprobantes, ya están clasificadas correctamente: "
            "'config_local' (nombre del local, RUC, timbrado, formato e "
            "impresora) queda protegida y se conserva en ambas modalidades "
            "de reinicio, y 'numeracion_comprobante' (el correlativo de "
            "comprobantes y facturas) se reinicia a 0 junto con el resto "
            "de los datos del negocio.",
            "El resumen 'Estado actual de la base de datos', en la parte "
            "superior de Reinicio del Sistema, ahora tiene su propia barra "
            "de desplazamiento lateral: con cada módulo nuevo que se suma "
            "al sistema, la fila de números ya no corta los últimos "
            "bloques (como 'Compras Importación' o 'Usuarios') en "
            "pantallas angostas, sino que se puede recorrer arrastrando la "
            "barra o con Shift + rueda del mouse.",
        ],
    },
    {
        "fecha": "Agosto 2026",
        "titulo": "Mejora: Usuarios, Productos, Inventario y Calculadora",
        "etiqueta": "Mejora",
        "version": "1.39.2",
        "detalles": [
            "Usuarios: el panel de detalle (datos y permisos del usuario "
            "seleccionado) ahora tiene scroll propio, así que un usuario "
            "con muchos módulos asignados ya no se corta sin poder verse "
            "completo.",
            "Usuarios: al crear o editar un Gerente o Vendedor, ahora es "
            "obligatorio asignarle al menos un módulo en la pestaña "
            "Permisos — si no se marca ninguno, el sistema avisa con un "
            "mensaje claro y salta directo a esa pestaña en vez de dejar "
            "guardar un usuario sin ningún acceso.",
            "Productos: en la pestaña Opciones, al elegir stock "
            "'Ilimitado' los campos 'Stock Inicial'/'Stock Actual' y "
            "'Stock Mínimo' se inhabilitan automáticamente (ya que no "
            "aplican), y se rehabilitan solos si se vuelve a 'Cantidad'.",
            "Inventario: los productos con stock 'Ilimitado' ahora también "
            "quedan registrados en su Historial de Movimientos — la carga "
            "inicial al crearlos y cada venta o salida posterior — "
            "mostrando 'Ilimitado' en vez de un número en Cantidad y "
            "Stock Resultante. Antes esos productos no dejaban ningún "
            "rastro en el historial. Esto también se refleja en la "
            "exportación a Excel/CSV desde Gestión de Datos.",
            "Calculadora: ventana más compacta (antes ocupaba demasiado "
            "espacio en pantalla) y ahora se puede usar por completo con "
            "el teclado además del mouse — números, operadores, Enter "
            "para '=', Backspace, Supr y Escape — en todos sus modos "
            "(Estándar, Científica, Programador, Moneda y los "
            "convertidores de unidades). Antes solo se podía tocar con "
            "el mouse.",
            "Compilación: además del .exe de Windows, ahora también se "
            "puede generar un ejecutable nativo para Linux y una "
            "aplicación .app para macOS, con los nuevos scripts "
            "'compilar_linux.sh' y 'compilar_mac.sh' (mismo archivo "
            "MaquedaSystems.spec para las tres plataformas). Se probó "
            "compilando y ejecutando realmente el binario de Linux, con "
            "resultado exitoso.",
        ],
    },
    {
        "fecha": "Agosto 2026",
        "titulo": "Mejora: Reporte General en Importaciones, y RRHH más rápido y en tiempo real",
        "etiqueta": "Mejora",
        "version": "1.39.1",
        "detalles": [
            "El módulo Importaciones ahora tiene el botón '📄 Reporte "
            "General' (igual que Recursos Humanos e Inventario): exporta "
            "el resumen del Dashboard, las compras, la rentabilidad por "
            "plataforma y por producto, y los couriers, en 7 formatos "
            "(PDF con y sin dashboard, Word, LibreOffice, Excel, CSV y "
            "JSON).",
            "Corrección de rendimiento en Recursos Humanos: la pestaña "
            "Personal calculaba el adelanto pendiente de cada empleado "
            "abriendo una conexión nueva a la base de datos por cada fila "
            "de la grilla, lo que se sentía lento apenas había varios "
            "empleados cargados. Ahora se hace con una sola consulta para "
            "todos los empleados a la vez — probado con 30 empleados: la "
            "grilla pasó a cargar en milisegundos.",
            "Corrección de sincronización en Recursos Humanos: agregar un "
            "empleado o registrar/marcar/eliminar un adelanto ahora se ve "
            "reflejado al instante en la pestaña Personal (columna "
            "'Adelantos pend.' y el resumen inferior), sin tener que "
            "cambiar de pestaña ni salir y volver a entrar al módulo como "
            "pasaba antes.",
            "Se agregó una cuarta tarjeta al resumen inferior de la "
            "pestaña Personal: 'Resta del sueldo' (el total de sueldos "
            "menos los adelantos pendientes), también incluida en el "
            "Reporte General y en el Excel de RRHH.",
        ],
    },
    {
        "fecha": "Agosto 2026",
        "titulo": "Nuevo módulo: Importaciones (eBay, AliExpress, Temu, Shein, Alibaba, Made in China, Amazon)",
        "etiqueta": "Nuevo",
        "version": "1.39.0",
        "detalles": [
            "Pensado para negocios que importan mercadería del exterior: "
            "registra cada compra como 'una caja', con uno o varios "
            "productos adentro, que se retira de un courier en un "
            "casillero (Miami o Shenzhen) antes de llegar a Paraguay.",
            "Cálculo automático del flete: se carga el peso total de la "
            "caja y la tarifa por kg del courier (vía aérea o marítima), y "
            "el sistema reparte ese costo proporcionalmente entre todas "
            "las unidades de la caja — por ejemplo, 10 unidades en una "
            "caja de 1 kg con flete de US$ 8 quedan con US$ 0,80 de envío "
            "cada una. También se puede cargar un costo de envío manual "
            "para los casos en que salió gratis o ya venía incluido.",
            "Couriers con su email, RUC, teléfono y tarifa por kg (aérea y "
            "marítima); si se les cambia la tarifa, las compras ya "
            "cargadas se recalculan solas.",
            "Tiendas/plataformas totalmente editables (ya no una lista "
            "fija): vienen precargadas eBay, AliExpress, Temu, Shein, "
            "Alibaba, Made in China y Amazon, y se pueden agregar nuevas "
            "desde un gestor dedicado o al vuelo con un botón '+' dentro "
            "de la ficha de compra.",
            "Todos los montos se muestran en dólares y también "
            "convertidos a guaraníes, con un tipo de cambio editable a "
            "mano desde el Dashboard (por si el automático no coincide "
            "con el real) o actualizable por Internet con un clic.",
            "Con el precio de venta al público que se cargue por "
            "producto, calcula la ganancia y el margen automáticamente, y "
            "permite 'Enviar a Inventario' cada unidad ya recibida — crea "
            "el producto (o suma stock a uno existente) con el costo real "
            "ya calculado, listo para venderse desde el módulo Ventas de "
            "siempre.",
            "Dashboard con inversión total, ganancia potencial, tiempo "
            "promedio entre compra y recepción, y rentabilidad por "
            "plataforma y por producto — con tarjetas que se reacomodan "
            "solas según el ancho de la ventana para que ninguna quede "
            "cortada, y tablas con scroll horizontal.",
            "Se agregó también a Ayuda, Gestión de Datos (exportación a "
            "Excel/CSV) y Reinicio del Sistema, para que quede cubierto "
            "igual que el resto de los módulos del sistema.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Corrección: 'Reinicio del Sistema' no borraba Préstamos ni varios módulos más",
        "etiqueta": "Corrección",
        "version": "1.38.1",
        "detalles": [
            "Se detectó que 'Reiniciar datos del negocio' y 'Reinicio total de "
            "fábrica' solo vaciaban las tablas del núcleo original (ventas, "
            "productos, clientes, créditos, compras, etc.) y se habían quedado "
            "desactualizados: los módulos agregados después —Presupuestos, "
            "Préstamos (incluidas sus cuotas y pagos), Asistencia Técnica, "
            "Veterinaria, Restaurante/Comedor y Alquiler de Streaming— NO se "
            "borraban aunque el sistema dijera que 'reinició todo'.",
            "Se corrigió agregando las ~35 tablas que faltaban, clasificadas "
            "correctamente según corresponda: se borran en ambos reinicios "
            "(datos del negocio), se borran solo en el reinicio total "
            "(vinculadas a usuarios), o nunca se tocan (configuraciones y la "
            "Biblia ya descargada, que no son datos del negocio).",
            "También se agregó una verificación automática en la pantalla de "
            "Reinicio del Sistema que detecta si en el futuro se agrega un "
            "módulo nuevo y sus tablas quedan sin clasificar, para que este "
            "problema no se repita.",
            "De paso se corrigió otro error encontrado en la misma revisión: "
            "la tabla de configuración de Apariencia (tema claro/oscuro, "
            "fuente) nunca se creaba en la base de datos.",
            "Se probó con datos reales: se cargó un préstamo con cuotas, se "
            "ejecutó el reinicio, y se confirmó que ahora sí quedan en cero, "
            "junto con presupuestos, casos técnicos, mascotas, comandas y "
            "suscripciones de streaming.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nuevo módulo: Juegos y Entretenimiento",
        "etiqueta": "Nuevo",
        "version": "1.38.0",
        "detalles": [
            "Un mini arcade a color dentro del sistema, con 6 juegos clásicos "
            "para una pausa recreativa: Solitario (Klondike completo), "
            "Buscaminas (3 dificultades), Tetris, Snake, Pong y Pac-Man.",
            "Cada juego guarda automáticamente el puntaje obtenido al "
            "finalizar la partida, por usuario.",
            "Incluye un Ranking de Usuarios con una pestaña general (suma de "
            "los mejores puntajes de cada usuario en todos los juegos que "
            "jugó) y una pestaña por cada juego con su propia tabla de "
            "líderes.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nuevo módulo: Biblia (Antiguo Testamento, Nuevo Testamento y Completa)",
        "etiqueta": "Nuevo",
        "version": "1.37.0",
        "detalles": [
            "Lector de la Biblia completa (Reina-Valera, 66 libros) "
            "organizado en 3 pestañas: Antiguo Testamento, Nuevo Testamento "
            "y Santa Biblia Completa.",
            "Los textos se descargan de Internet la primera vez que se abre "
            "cada libro, y quedan guardados localmente para seguir leyendo "
            "sin conexión después de eso.",
            "Incluye selector de capítulo, buscador de palabras dentro de lo "
            "ya descargado, y un botón para descargar de una sola vez todos "
            "los libros faltantes de una pestaña.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Mejora: 'Cargar por monto' para productos por Kg/Litro/Metro en Ventas",
        "etiqueta": "Mejora",
        "version": "1.36.3",
        "detalles": [
            "En Ventas y en Armar Venta por Locales, al seleccionar en la "
            "grilla un producto que se vende por Kilogramo, Litro o Metro, "
            "aparece un campo adicional '💰 Cargar por monto' junto al "
            "control de cantidad.",
            "Permite escribir cuánto dinero (Gs.) va a llevar el cliente, y "
            "calcula automáticamente a cuántos Kg/Lt/Mt equivale, mostrando "
            "el resultado en vivo antes de aplicarlo.",
            "Como el precio por gramo/mililitro/milímetro no siempre da un "
            "monto exacto en guaraníes, la vista previa también muestra el "
            "monto real que se va a cobrar (por ejemplo, '≈ 0,789 Kg → Gs. "
            "14.991' si se pidieron Gs. 15.000 y no hay una cantidad exacta "
            "posible), para que no haya sorpresas al confirmar.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Corrección: la numeración configurada en Config. Local no se reflejaba al vender ni imprimir",
        "etiqueta": "Corrección",
        "version": "1.36.2",
        "detalles": [
            "Se encontraron y corrigieron 3 errores reales relacionados "
            "con Config. Local → Numeración:",
            "1) 'guardar_numeracion' podía fallar directamente si nunca "
            "se había abierto antes la pestaña de Numeración (la tabla "
            "todavía no existía), y además no cerraba la conexión a la "
            "base de datos al terminar.",
            "2) El más importante: al procesar una venta, el sistema "
            "abría una SEGUNDA conexión de escritura mientras la "
            "transacción de la venta todavía estaba abierta, para "
            "asegurar que la tabla de numeración existiera — eso "
            "chocaba con SQLite y hacía fallar la venta directamente "
            "con 'database is locked' en cuanto se guardaba una "
            "numeración y se intentaba vender.",
            "3) El botón '📄 Generar Factura PDF' del Resumen de Ventas "
            "sacaba un número de factura NUEVO cada vez que se tocaba, "
            "en vez de reutilizar el que ya había quedado asignado a esa "
            "venta al procesarla — esto además de ser incorrecto para "
            "una factura legal (el número no puede cambiar al "
            "reimprimir), iba 'quemando' numeración configurada sin que "
            "se reflejara consistentemente.",
            "Con las 3 correcciones, el establecimiento, punto de "
            "expedición y último número configurados en Config. Local "
            "ahora sí se ven reflejados correctamente tanto en el "
            "Comprobante de Venta como en la Factura Legal, al generar "
            "la venta y al imprimir/regenerar el PDF las veces que haga "
            "falta (siempre con el mismo número para la misma venta).",
            "Se probó de punta a punta con datos reales: configurar una "
            "numeración nueva, procesar una venta inmediatamente después "
            "(antes fallaba), confirmar que el comprobante y la factura "
            "usan el establecimiento/punto de expedición configurados, y "
            "generar la Factura PDF dos veces seguidas para la misma "
            "venta confirmando que el número no cambia.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Corrección: escanear un código de barras cerraba y guardaba 'Nuevo Producto'",
        "etiqueta": "Corrección",
        "version": "1.36.1",
        "detalles": [
            "En el formulario Nuevo/Editar Producto, Enter guarda el "
            "producto desde cualquier campo (una comodidad para no "
            "tener que ir hasta el botón Guardar). El problema: un "
            "lector de código de barras 'escribe' el código escaneado y "
            "termina con un Enter automático, como si lo hubiera "
            "tecleado el usuario — eso disparaba el guardado a mitad de "
            "carga, cerrando la ventana antes de terminar de completar "
            "el producto.",
            "Se corrigió puntualmente los campos 'Código de Barras' y "
            "'Código Secundario' (ambos se suelen cargar con la pistola "
            "lectora en la práctica): ahora, al escanear (o tipear y "
            "presionar Enter ahí), solo completan el campo — no guardan "
            "ni cierran la ventana. El resto de los campos del "
            "formulario (precios, Descripción, etc.) siguen guardando "
            "con Enter exactamente igual que antes.",
            "El cambio se aplicó solo en este formulario, tal como se "
            "pidió, sin tocar el atajo de Enter en ninguna otra "
            "pantalla del sistema.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Formularios internos de Ventas, Compras, Créditos y Presupuestos completados",
        "etiqueta": "Nuevo",
        "version": "1.36.0",
        "detalles": [
            "Ventas: se tradujeron las 4 ventanas auxiliares "
            "compartidas (Buscar Producto, Producto Común, Asignar "
            "Cliente, Consultar Stock de Productos), incluidos sus 15 "
            "encabezados de columna repartidos entre ellas.",
            "Compras y Créditos: se confirmó que ya estaban "
            "prácticamente completos de tandas anteriores — se "
            "terminaron los últimos botones sueltos (Aceptar/Cancelar) "
            "que quedaban en Compras.",
            "Presupuestos: se tradujo el formulario completo de carga/"
            "edición (Código del Producto, atajos F1/F2/DEL, Válido "
            "hasta, Observaciones, contador de productos, Guardar "
            "Presupuesto/Cancelar), y el diálogo de editar cantidad de "
            "un ítem (Tipo de Precio, Cantidad, Precio Unitario).",
            "Se probó con datos reales en Español, English, "
            "Русский, 中文 y Українська — Ventas, Compras, Créditos y "
            "Presupuestos quedan con sus formularios internos "
            "completamente traducidos.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Restaurante/Comedor: traducción profunda completada (100% de las ventanas)",
        "etiqueta": "Nuevo",
        "version": "1.35.0",
        "detalles": [
            "Se tradujeron las últimas 5 ventanas del módulo: Elegir "
            "Insumo (con su grilla de 4 columnas), Personalizar Ítem "
            "(agregar/quitar ingredientes, recargos), Elegir "
            "Ingrediente Base a quitar, Confirmar Recargo, y Crear "
            "Insumo Rápido (alta de un insumo nuevo sin salir del "
            "módulo).",
            "Con esto, Restaurante/Comedor queda con sus 20 ventanas "
            "traducidas: de 122 textos fijos que tenía originalmente el "
            "módulo, quedan apenas 16 sin traducir (íconos aislados y "
            "detalles menores).",
            "Se probó con datos reales en Español, English, "
            "Русский y 中文, incluidas Elegir Insumo (con sus 4 "
            "encabezados de columna) y Crear Insumo Rápido.",
            "Segundo módulo (después de Veterinaria) llevado a una "
            "traducción prácticamente total, no solo la navegación.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Restaurante/Comedor: traducción profunda en curso (parte 2 de varias)",
        "etiqueta": "Nuevo",
        "version": "1.34.0",
        "detalles": [
            "Se tradujeron 7 ventanas más del módulo: Ficha de Mesa "
            "(nueva/editar), Nuevo Pedido sin Mesa (tipo, dirección de "
            "entrega, cliente, observaciones), Seleccionar Plato para "
            "agregar a una comanda, Cobro de Comanda (condición de "
            "venta, forma de pago, confirmar cobro), Ficha de Plato "
            "completa (datos, insumos de receta, tamaños/variantes, "
            "activar/desactivar), Gestión de Repartidores, Elegir "
            "Repartidor, y Ficha de Variante (tamaño).",
            "De los 122 textos fijos que tenía originalmente el módulo, "
            "ya quedan solo 35 sin traducir — las ventanas de menor uso "
            "(Elegir Insumo, Personalizar Ítem, Confirmar Recargo, "
            "Crear Insumo Rápido, Elegir Ingrediente Base).",
            "Se probó con datos reales en Español, English, "
            "Русский y 中文, incluida la ventana de Ficha de Mesa y la "
            "grilla de Repartidores.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Restaurante/Comedor: traducción profunda en curso (parte 1 de varias)",
        "etiqueta": "Nuevo",
        "version": "1.33.0",
        "detalles": [
            "Se tradujo el contenido interno de las 5 pestañas "
            "principales (Mesas, Comandas Activas, Delivery, Platos, "
            "Dashboard): botones de acción (Nueva Mesa, Nuevo Pedido, "
            "Gestionar/Asignar Repartidores, Cambiar Estado, Nuevo "
            "Plato) y los 21 encabezados de columna repartidos en sus "
            "grillas.",
            "También la ventana de Comanda completa: Agregar Plato, "
            "Cambiar Estado, Quitar, Personalizar, Cancelar Comanda, "
            "Cerrar Ventana, Cerrar Cuenta/Cobrar, y sus 8 encabezados "
            "de columna.",
            "Este es un módulo muy grande (más de 20 ventanas "
            "distintas): todavía quedan por traducir la Ficha de Plato, "
            "Personalizar Ítem, Elegir Insumo, Gestión de Repartidores, "
            "Ficha de Variante, y varias ventanas más — se sigue en "
            "próximas actualizaciones.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Veterinaria: traducción profunda de todo su contenido interno",
        "etiqueta": "Nuevo",
        "version": "1.32.0",
        "detalles": [
            "A diferencia de la tanda anterior (que tradujo solo la "
            "navegación principal de los módulos grandes), esta vez se "
            "tradujo el CONTENIDO INTERNO completo de Veterinaria: la "
            "grilla de Mascotas (8 columnas), Vacunas Próximas (6 "
            "columnas), Dashboard con las consultas del día (5 "
            "columnas), Historial Clínico (6 columnas), Vacunas (5 "
            "columnas) y Tratamientos (7 columnas).",
            "También el formulario completo de Ficha de Mascota (dueño, "
            "nombre, especie, raza, color, sexo, fecha de nacimiento, "
            "peso, microchip, esterilizado, observaciones, marcar/"
            "reactivar fallecido), y las 3 ventanas de carga rápida: "
            "Nueva Consulta, Nueva Vacuna y Nuevo Tratamiento, con todos "
            "sus campos.",
            "Y el diálogo de enviar reportes por correo (cuenta, "
            "destinatario, asunto, mensaje, enviar/cancelar).",
            "De 88 textos fijos que tenía el módulo, quedaron apenas 4 "
            "sin traducir (algunos íconos aislados sin texto "
            "descriptivo). Se probó con datos reales en Español, "
            "English, Русский y 中文, incluyendo el formulario completo "
            "de ficha de mascota.",
            "Este es el primer módulo llevado a una traducción "
            "prácticamente total (no solo la navegación); el resto de "
            "los módulos grandes (Restaurante, Streaming, y los "
            "formularios internos de Ventas/Compras/Créditos/etc.) "
            "sigue pendiente de este mismo nivel de profundidad.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "10 módulos más con su navegación traducida: Licencias, Uso del Sistema, Gestión de Datos, Terminal SQL, Asistente IA, Idioma, Reinicio del Sistema, Clima, Novedades y Ayuda",
        "etiqueta": "Nuevo",
        "version": "1.31.0",
        "detalles": [
            "Licencias: título del generador y los 5 encabezados de la "
            "grilla de seriales.",
            "Uso del Sistema: título, gráfico de actividad por hora, "
            "tabla de últimas sesiones, y botón Cerrar.",
            "Gestión de Datos: título y las 4 secciones (Base de datos, "
            "Excel, CSV, Avanzado).",
            "Terminal SQL: título, Tablas, Historial, Ejecutar, "
            "Limpiar, modo solo lectura, y mensaje de error.",
            "Asistente IA: título, botón Configurar, mensajes de estado "
            "sin configurar, las 4 acciones rápidas (Analizar ventas, "
            "Generar descripción, Traducir, Nueva conversación), botón "
            "Enviar, y el estado 'pensando'.",
            "Idioma: título, 'Elegí el idioma', botón Aplicar Idioma, y "
            "el indicador 'Actual'.",
            "Reinicio del Sistema: título, estado de la base de datos, "
            "todo el formulario de confirmación (usuario, contraseña, "
            "confirmar y ejecutar), y los mensajes de error.",
            "Clima: título, Departamento/Ciudad-Distrito, Hoy, "
            "Pronóstico 5 días, Evolución horaria, y los mensajes de "
            "actualización.",
            "Novedades y Ayuda: el encabezado de cada pantalla (título "
            "y subtítulo) — el contenido de cada entrada del historial "
            "y de cada tema de ayuda, al ser párrafos extensos, sigue "
            "en español.",
            "De regalo: al probar Licencias con datos reales, se "
            "encontró y corrigió un error real que hacía fallar por "
            "completo la ventana 'Generador de Licencias' al abrirla "
            "(un conflicto interno de la grilla de seriales, sin "
            "relación con el idioma).",
            "Con esto, 27 de los 28 módulos del sistema ya tienen su "
            "navegación principal traducida a los 9 idiomas.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "10 módulos más con su navegación traducida: Reportes, Asistencia Técnica, Veterinaria, Restaurante, Streaming, Préstamos, RRHH, Usuarios, Cotizaciones y Config. Local",
        "etiqueta": "Nuevo",
        "version": "1.30.0",
        "detalles": [
            "Reportes: título, filtros (Desde/Hasta/Elegir Rango/"
            "Vendedor/Estado/Buscar), las 7 tarjetas de resumen, los 9 "
            "encabezados de la grilla principal, y las 3 pestañas del "
            "Reporte General (Ventas/Compras/Presupuestos).",
            "Asistencia Técnica, Veterinaria, Restaurante/Comedor y "
            "Alquiler de Streaming: el botón principal de cada uno y "
            "todas sus pestañas de navegación (por ejemplo, en "
            "Veterinaria: Mascotas, Vacunas Próximas, Dashboard, "
            "Historial Clínico, Vacunas y Tratamientos).",
            "Préstamos: título, las 3 pestañas (Banco/Fondo, Nuevo "
            "Préstamo, Préstamos), tarjeta de saldo disponible, botón "
            "Cargar Fondos, e Historial de Movimientos del Fondo.",
            "RRHH: título y las 3 pestañas (Personal, Asistencia, "
            "Adelantos/Vales).",
            "Usuarios: título, botón Nuevo Usuario, los 6 encabezados "
            "de la grilla, mensaje de selección, permisos de módulos, y "
            "los botones Editar/Eliminar.",
            "Cotizaciones: los encabezados de columna que faltaban en "
            "ambas grillas (Fiat y Cripto) — el resto del módulo ya "
            "venía traducido de una actualización anterior.",
            "Config. Local: título y las 4 pestañas (Datos del Local, "
            "Comprobante de Venta, Factura Legal, Numeración).",
            "Se probó cada uno con datos reales en al menos 3 idiomas "
            "distintos, incluidos alfabetos no latinos (ruso, coreano, "
            "árabe, ucraniano, chino) según el módulo.",
            "Nota sobre el alcance: en los módulos más grandes y con "
            "muchas pestañas (Veterinaria, Restaurante, Streaming), se "
            "tradujo la navegación principal (botones y pestañas "
            "siempre visibles); el contenido interno de cada pestaña "
            "específica (formularios de carga, sub-diálogos) sigue en "
            "español por ahora.",
            "Con esto ya son 18 de los 28 módulos con su navegación "
            "principal traducida.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Corrección: no se podía desplazar con la rueda del mouse/touchpad en Clima",
        "etiqueta": "Corrección",
        "version": "1.29.1",
        "detalles": [
            "En el módulo Clima, la rueda del mouse (o el touchpad) solo "
            "hacía scroll si el cursor estaba exactamente sobre un "
            "espacio vacío del panel — apenas se pasaba por encima de "
            "una tarjeta, un botón o cualquier otro contenido (que es "
            "prácticamente toda la pantalla), dejaba de funcionar.",
            "Se corrigió para que el scroll funcione sin importar sobre "
            "qué parte del contenido esté el cursor, con el mismo "
            "mecanismo ya usado en otros módulos del sistema (como "
            "Inventario).",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "5 módulos más traducidos: Clientes, Compras, Créditos, Presupuestos y Pre-Venta",
        "etiqueta": "Nuevo",
        "version": "1.29.0",
        "detalles": [
            "Clientes: búsqueda, botones Nuevo/Editar/Eliminar, los 6 "
            "encabezados de la grilla, y el panel de detalle completo "
            "(mensaje de selección, Resumen, Historial de Compras).",
            "Compras: botón 'Nueva Compra', buscador, los 6 encabezados "
            "de la grilla principal, y el diálogo de detalle de una "
            "compra (grilla de artículos, Total, Cerrar).",
            "Créditos: botones de agrupar y estado de cuenta, los "
            "filtros 'Mostrar Pendientes/Todos', ambos modos de vista de "
            "la grilla (por cliente y por crédito), el panel de Resumen "
            "de Créditos, y el diálogo completo de pago (historial de "
            "pagos, monto a pagar, registrar pago).",
            "Presupuestos: botón 'Nuevo Presupuesto', filtro de Estado, "
            "los 7 encabezados de columna, y los botones de acción del "
            "detalle (Generar PDF, Editar, Aprobar, Rechazar, Convertir "
            "a Venta, Eliminar, Cerrar).",
            "Pre-Venta: botones Modificar/Eliminar, buscador, los 5 "
            "encabezados de la grilla principal, y la pantalla de carga/"
            "edición (Código del Producto, atajos F1/F2/DEL, Cobrar/"
            "Guardar Cambios/Cancelar, nombre del cliente).",
            "Se probó cada uno con datos reales en al menos 3 idiomas "
            "distintos (incluidos alfabetos no latinos como ruso, "
            "árabe, coreano, ucraniano y chino según el módulo).",
            "Con esto ya son 8 de los 28 módulos completamente "
            "traducidos: Ventas, Productos, Inventario, Clientes, "
            "Compras, Créditos, Presupuestos y Pre-Venta.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Módulo Clima ampliado: más datos, pronóstico por períodos, 5 días y gráfico horario",
        "etiqueta": "Nuevo",
        "version": "1.28.0",
        "detalles": [
            "El clima actual ahora también muestra presión atmosférica y "
            "la dirección del viento (ej. 'Sur Suroeste'), además de lo "
            "que ya tenía (temperatura, sensación térmica, humedad, "
            "precipitación).",
            "Nueva sección 'Hoy': pronóstico de la Tarde, la Noche y la "
            "Madrugada, cada una con su ícono, rango de temperatura y una "
            "descripción corta (ej. 'Fresco, cielo mayormente nublado, "
            "vientos del sureste. Lluvias dispersas.').",
            "Nueva sección 'Pronóstico 5 días': una tarjeta por día con "
            "ícono, máxima/mínima y descripción — se puede tocar "
            "cualquier día para ver su detalle horario.",
            "Nuevo gráfico 'Evolución horaria': una curva de temperatura "
            "hora por hora (00h a 23h) del día elegido, dibujada "
            "directamente por el sistema (sin librerías externas de "
            "gráficos), marcando la hora actual con un punto naranja "
            "cuando corresponde al día de hoy.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "El módulo Idioma ahora también traduce Productos e Inventario",
        "etiqueta": "Nuevo",
        "version": "1.27.0",
        "detalles": [
            "Se sumaron dos módulos más a la traducción completa: "
            "Productos (buscador, filtros Activos/Inactivos, botón "
            "'Nuevo Producto', accesos a Categorías/Marcas/Proveedores, "
            "y los 11 encabezados de la grilla) e Inventario (los 4 "
            "botones de filtro con sus dos estados cada uno — activado y "
            "desactivado —, el buscador, el título 'Resumen de "
            "Inventario' y los 11 encabezados de su grilla).",
            "Se probó en Español, English, 中文 (chino), العربية (árabe) "
            "y Русский (ruso), incluidos los botones que cambian de "
            "texto según su estado (por ejemplo, 'Mostrar Productos "
            "Bajos en Inventario' que pasa a 'Volver a Todos los "
            "Productos' al activarlo).",
            "Con esto ya son 3 de los 28 módulos completamente "
            "traducidos (Ventas, Productos, Inventario); el resto sigue "
            "en español y se irá sumando de a poco.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "El módulo Idioma ahora también traduce el contenido interno de Ventas",
        "etiqueta": "Nuevo",
        "version": "1.26.0",
        "detalles": [
            "Hasta ahora, elegir un idioma solo traducía el menú lateral "
            "y la barra superior — el contenido de cada módulo seguía en "
            "español. Como primer paso de un trabajo más grande, se "
            "tradujo por completo la pantalla principal de Ventas: el "
            "campo Código de Barra/Secundario, el botón de agregar "
            "producto, los encabezados de la grilla (Código, "
            "Descripción, Precio Venta, Cant., Importe, Existencia), el "
            "contador de productos, 'F12 - Procesar', el nombre del "
            "cliente, CI/RUC, Condición de Venta (Contado/Crédito), la "
            "pestaña 'Resumen' y el nombre de cada pestaña 'Nueva Venta "
            "N'.",
            "Se probó en Español, English, Português y Русский, "
            "incluyendo un alfabeto no latino, y funciona correctamente "
            "en los cuatro.",
            "Importante: el resto de los 27 módulos (Productos, "
            "Inventario, Clientes, Reportes, Veterinaria, Restaurante, "
            "etc.) todavía muestran su contenido interno en español — "
            "traducir cada uno implica revisar y traducir sus textos "
            "fijos uno por uno, un trabajo bastante más grande que se "
            "puede ir sumando módulo por módulo en próximas actualizaciones.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Corrección: el idioma configurado no estaba protegido en Reinicio del Sistema",
        "etiqueta": "Corrección",
        "version": "1.25.2",
        "detalles": [
            "Al igual que la configuración de Email y del Asistente IA, "
            "el idioma elegido en el módulo Idioma ahora queda "
            "explícitamente protegido en ambas modalidades de Reinicio "
            "del Sistema: no tiene sentido volver a Español cada vez que "
            "se reinician los datos operativos del negocio.",
            "Se probó con datos reales: se configuró el idioma en "
            "English, se ejecutó tanto el 'Reinicio de datos del "
            "negocio' como el 'Reinicio total de fábrica', y en ambos "
            "casos el idioma se mantuvo en English después.",
            "Se actualizó también el texto de Ayuda de Reinicio del "
            "Sistema para dejarlo explícito.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Verificación: la compilación a .exe ya incluye todos los módulos nuevos automáticamente",
        "etiqueta": "Mejora",
        "version": "1.25.1",
        "detalles": [
            "Se revisó la configuración de compilación (MaquedaSystems."
            "spec y compilar_exe.bat) tras las últimas incorporaciones "
            "(Terminal SQL, Asistente IA, Idioma, Clima, multi-cuenta de "
            "correo): no hicieron falta cambios funcionales, porque "
            "PyInstaller detecta automáticamente todos los módulos que "
            "'main.py' termina importando, sin necesidad de listarlos "
            "uno por uno.",
            "Se confirmó además que ninguno de los módulos nuevos "
            "necesita paquetes adicionales en requirements.txt: todos "
            "usan únicamente la librería estándar de Python (urllib, "
            "json, sqlite3, threading, math, etc.), igual que Cotizaciones.",
            "Se agregó una nota aclaratoria en el encabezado del archivo "
            ".spec sobre esto, y se verificó (importando los 91 archivos "
            "del proyecto uno por uno) que no falta ninguna dependencia.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nuevo módulo: Clima (los 17 departamentos de Paraguay, con íconos animados)",
        "etiqueta": "Nuevo",
        "version": "1.25.0",
        "detalles": [
            "Nuevo módulo accesible para todos los usuarios (igual que "
            "Cotizaciones): muestra el clima actual de cualquier "
            "departamento y ciudad/distrito de Paraguay — temperatura, "
            "sensación térmica, humedad, viento y precipitación de la "
            "última hora.",
            "Incluye un ícono animado del estado del cielo, dibujado "
            "directamente por el sistema (sin imágenes ni GIFs): sol con "
            "rayos girando si está despejado, nubes que flotan si está "
            "nublado, gotas cayendo si llueve o llovizna, copos si nieva, "
            "niebla ondulante, y rayos que destellan en tormenta "
            "eléctrica.",
            "Se actualiza automáticamente cada 10 minutos, con botón "
            "'🔄 Actualizar' para forzarlo en cualquier momento — mismo "
            "esquema que Cotizaciones.",
            "Los datos vienen de Open-Meteo, un servicio meteorológico "
            "público y gratuito con buena cobertura para Paraguay. Se "
            "evaluó usar el sitio de la Dirección de Meteorología e "
            "Hidrología (DINAC), pero no publica una API estable para "
            "uso automatizado — 'scrapear' su página HTML sería frágil y "
            "se rompería con cualquier cambio de diseño del sitio.",
            "La lista de ciudades/distritos cubre los 17 departamentos "
            "completos con varias de sus ciudades más conocidas (90 "
            "ubicaciones en total), pero no es un listado oficial "
            "exhaustivo de los cerca de 260 distritos del país.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Módulo Idioma: 5 idiomas nuevos (Ruso, Chino, Coreano, Ucraniano, Árabe)",
        "etiqueta": "Nuevo",
        "version": "1.24.0",
        "detalles": [
            "El módulo Idioma pasó de 4 a 9 idiomas disponibles: Español, "
            "Guaraní, Português, English, Русский (ruso), 中文 (chino), "
            "한국어 (coreano), Українська (ucraniano) y العربية (árabe).",
            "Se tradujeron las mismas 41 claves ya existentes (menú "
            "lateral, título de la ventana, botón 'Cerrar sesión', "
            "etiquetas de rol) para los 5 idiomas nuevos.",
            "La pantalla de selección de idioma pasó de una sola fila a "
            "una grilla de varias filas, para que las 9 tarjetas entren "
            "cómodas sin quedar apretadas.",
            "Dos cosas a tener en cuenta: el árabe se escribe de derecha "
            "a izquierda (RTL), y el sistema no invierte automáticamente "
            "la disposición de los menús (el texto se lee bien, pero "
            "queda alineado a la izquierda) — es una limitación de la "
            "librería gráfica usada, no un error de traducción. Además, "
            "chino/coreano/ruso/ucraniano necesitan que Windows tenga "
            "instalados sus paquetes de idioma para mostrarse "
            "correctamente (casi todas las instalaciones de Windows "
            "10/11 ya los traen).",
            "Al igual que con el Guaraní, estas 5 traducciones nuevas son "
            "una primera versión hecha por la IA, sin revisión de un "
            "hablante nativo — se recomienda esa revisión antes de un "
            "uso 100% oficial.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nuevo módulo: Idioma (interfaz en Español, Guaraní, Português o English)",
        "etiqueta": "Nuevo",
        "version": "1.23.0",
        "detalles": [
            "Nuevo módulo exclusivo para Administradores: permite elegir "
            "el idioma de la interfaz del sistema entre Español (por "
            "defecto), Guaraní, Português e English. Es una "
            "configuración de todo el sistema (no por usuario) y se "
            "aplica la próxima vez que cada quien inicia sesión.",
            "Por ahora traduce el menú lateral, el título de la ventana, "
            "el botón 'Cerrar sesión' y las etiquetas de rol de la barra "
            "superior. El contenido interno de cada módulo (campos y "
            "botones específicos de Ventas, Productos, Reportes, etc.) "
            "sigue en español — es un trabajo que se irá ampliando.",
            "Importante: NO traduce los datos que ya cargaste (nombres de "
            "clientes, descripciones de productos, observaciones, etc.), "
            "solo los textos fijos que trae el propio sistema.",
            "Las traducciones al Guaraní son una primera versión hecha "
            "con criterio, no revisada todavía por un hablante nativo; "
            "para términos técnicos modernos sin equivalente natural se "
            "mantuvo el préstamo del español, como se usa en el habla "
            "real del Paraguay.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nuevo: traducir un texto puntual con el Asistente IA",
        "etiqueta": "Nuevo",
        "version": "1.22.0",
        "detalles": [
            "Nuevo botón '🌐 Traducir texto' en el Asistente IA: se pega o "
            "escribe cualquier texto (una descripción de producto, una "
            "observación, etc.), se elige el idioma destino de una lista "
            "(o se escribe uno libre) y la IA devuelve la traducción.",
            "Es independiente del módulo Idioma: sirve para traducir un "
            "dato puntual bajo pedido, sin cambiar nada de la interfaz "
            "del sistema.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Mejora: color a los botones 'Generar PDF' y 'Enviar por Correo' en Veterinaria",
        "etiqueta": "Mejora",
        "version": "1.21.5",
        "detalles": [
            "En las distintas pantallas del módulo Veterinaria donde "
            "aparecen juntos (historial clínico, reportes, vacunas), "
            "'🖨 Generar PDF' pasó a ser azul y '✉ Enviar por Correo' a "
            "ser verde, para distinguirlos de un vistazo — antes ambos "
            "eran blancos sin distinción.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Mejora: color al botón 'Actualizar' en Resumen de Ventas",
        "etiqueta": "Mejora",
        "version": "1.21.4",
        "detalles": [
            "El botón '🔄 Actualizar' de Resumen de Ventas pasó de blanco "
            "sin estilo a azul (borde y texto), a juego con el resto de "
            "los botones de esa pantalla.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Mejora: color a los botones de Resumen de Ventas",
        "etiqueta": "Mejora",
        "version": "1.21.3",
        "detalles": [
            "Los botones del panel de detalle de una venta pasaron de "
            "blanco/gris plano a tener color según su función: "
            "'↩ Devolver artículo seleccionado' en naranja, "
            "'✕ Cancelar Venta' en rojo, 'Reimprimir Comprobante/Factura' "
            "e 'Imprimir Factura' en azul (a juego con 'Generar Factura "
            "PDF', que ya era azul).",
            "Los botones 'Email' e 'Imprimir Resumen' de la parte "
            "superior también pasaron a tener el mismo estilo azul.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Mejora: se puede deseleccionar una fila en todas las grillas del sistema",
        "etiqueta": "Mejora",
        "version": "1.21.2",
        "detalles": [
            "Antes, una vez seleccionada una fila en cualquier grilla "
            "(tabla) del sistema, no había forma de deseleccionarla sin "
            "elegir otra fila.",
            "Ahora, en absolutamente todas las grillas del sistema (77 en "
            "total, en los 28 módulos), se puede deseleccionar haciendo "
            "click en un espacio en blanco dentro de la grilla (fuera de "
            "cualquier fila), o presionando Escape con el foco en la "
            "grilla.",
            "Si una pantalla ya usaba Escape para otra cosa (por ejemplo, "
            "cerrar una ventana de búsqueda), eso se respeta: el primer "
            "Escape solo deselecciona la fila; recién si no hay ninguna "
            "fila seleccionada, Escape vuelve a hacer lo de siempre "
            "(cerrar, cancelar, etc.).",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Mejora: color al botón 'F12 - Procesar' en Ventas",
        "etiqueta": "Mejora",
        "version": "1.21.1",
        "detalles": [
            "El botón '🛒 F12 - Procesar' de la pantalla de Ventas (el que "
            "abre Cobrar) pasó de blanco con borde negro a azul con texto "
            "blanco, para destacarlo como la acción principal de la "
            "pantalla, igual que los demás botones de acción del sistema.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nueva forma de pago: Criptomonedas",
        "etiqueta": "Nuevo",
        "version": "1.21.0",
        "detalles": [
            "En la pantalla de Cobro (F12), ahora se puede elegir "
            "'Criptomonedas' como forma de pago, junto a Efectivo, "
            "Crédito, Tarjeta/QR y Transferencia Bancaria. No exige "
            "cargar un monto en el campo Efectivo, igual que Tarjeta/QR "
            "o Transferencia.",
            "En el módulo Reportes → pestaña Ventas, las ventas cobradas "
            "en Criptomonedas ahora tienen su propia tarjeta de resumen y "
            "su propio total, en vez de mezclarse con otras formas de "
            "pago — se refleja igual en las exportaciones a PDF y Excel.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Mejora: se quitó la '✕' duplicada en la barra de título de Cobrar",
        "etiqueta": "Mejora",
        "version": "1.20.5",
        "detalles": [
            "La ventana Cobrar tenía dos formas de cerrarla: la '✕' nativa "
            "de la barra de título del sistema (junto con Minimizar y "
            "Maximizar) y una segunda '✕' dibujada en la franja azul de "
            "abajo, que quedaba redundante.",
            "Se quitó la '✕' duplicada de la franja azul; la '✕' nativa "
            "sigue cerrando la ventana exactamente igual que antes (con "
            "la misma confirmación de cancelar la venta en curso).",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Corrección y mejoras en la pantalla de Cobrar: minimizar, radios y botones de acción",
        "etiqueta": "Corrección",
        "version": "1.20.4",
        "detalles": [
            "Se corrigió que el botón nativo de 'Minimizar' de la ventana "
            "Cobrar no respondiera: mientras la ventana retiene el modo "
            "modal (necesario para que no se pueda interactuar con el "
            "resto del sistema mientras se cobra), Windows no la dejaba "
            "minimizar. Ahora el modo modal se libera automáticamente al "
            "minimizar y se retoma solo al restaurar la ventana, sin "
            "perder el comportamiento habitual el resto del tiempo.",
            "Se corrigió que las dos opciones de 'Tipo de Documento a "
            "Emitir' (Comprobante de Venta / Factura Legal) se vieran "
            "ambas como marcadas de entrada, aunque en realidad ninguna "
            "estaba seleccionada — era un problema visual de Windows, no "
            "de datos. Ahora ambas aparecen correctamente sin marcar "
            "hasta que el usuario elija una.",
            "Se les dio color a los botones de acción de la derecha para "
            "distinguirlos de un vistazo: 'F12 - Cobrar e Imprimir' en "
            "azul, 'F11 - Cobrar sin Imprimir' en verde, 'F8 - Generar "
            "Preventa' en naranja, y 'ESC - Cancelar' se mantiene en "
            "blanco con borde y texto rojo.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Corrección: 'Mi Perfil' no guardaba ni actualizaba la foto (ni ningún otro cambio)",
        "etiqueta": "Corrección",
        "version": "1.20.3",
        "detalles": [
            "Al editar el propio perfil desde la barra superior (nombre o "
            "foto), el botón 'Guardar' parecía no hacer nada: la ventana "
            "no se cerraba, la foto/nombre no se actualizaba en la barra "
            "superior, y daba la sensación de que no se había guardado "
            "nada.",
            "En realidad, los datos SÍ se guardaban correctamente en el "
            "sistema; el problema era un error interno que impedía que la "
            "ventana terminara de cerrarse y que la barra superior se "
            "refrescara con los cambios, por lo que nunca se veía "
            "reflejado.",
            "Ya está corregido para todos los usuarios, sin importar su "
            "rol (Vendedor, Gerente o Administrador): ahora al guardar el "
            "propio perfil, la ventana se cierra normalmente y la foto, "
            "el nombre y el rol se actualizan al instante en la barra "
            "superior.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Mejora: pantalla de Cobrar más compacta y más rápida para cobrar en efectivo",
        "etiqueta": "Mejora",
        "version": "1.20.2",
        "detalles": [
            "La sección 'Formas de Pago' pasó de mostrarse en una lista "
            "vertical de 4 filas a una grilla de 2 columnas, y se ajustó "
            "el espaciado de la sección 'Pago' — la ventana de Cobrar "
            "ahora ocupa menos alto en pantalla, con menos espacio vacío "
            "alrededor de los botones de la derecha.",
            "Nuevo atajo: presionar Enter dentro del campo 'Efectivo' "
            "cobra e imprime directamente (como F12), sin necesidad de "
            "tocar el mouse. Si el campo se deja vacío, se completa solo "
            "con el Total exacto antes de cobrar — pensado para el caso "
            "más común de pago justo, sin vuelto.",
            "Las validaciones de siempre se mantienen intactas: si falta "
            "elegir el Tipo de Documento, o el efectivo ingresado no "
            "alcanza, Enter avisa igual que antes y no procesa la venta.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Corrección: la configuración del Asistente IA no estaba protegida en Reinicio del Sistema",
        "etiqueta": "Corrección",
        "version": "1.20.1",
        "detalles": [
            "Al igual que la configuración de Email, la configuración del "
            "Asistente IA (proveedor y clave de API) ahora queda "
            "explícitamente protegida en ambas modalidades de Reinicio "
            "del Sistema (reinicio de datos del negocio y reinicio total "
            "de fábrica): no tiene sentido perder una clave de API paga "
            "al reiniciar los datos operativos.",
            "Se actualizó también el texto de Ayuda de Reinicio del "
            "Sistema para dejar explícito que las cuentas de correo y la "
            "configuración del Asistente IA se conservan siempre.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nuevo: se pueden guardar VARIAS cuentas de correo, no solo una",
        "etiqueta": "Nuevo",
        "version": "1.20.0",
        "detalles": [
            "Antes, 'Configurar Email' solo permitía tener una única "
            "cuenta remitente: para cambiarla, primero había que sacar la "
            "que ya estaba con '✕ Cerrar esta cuenta' y recién ahí cargar "
            "otra.",
            "Ahora se pueden guardar varias cuentas a la vez (por ejemplo, "
            "una de Gmail y otra de Outlook) y elegir cuál está activa "
            "(la que se usa para enviar) con el botón 'Usar esta cuenta', "
            "sin perder ninguna de las otras.",
            "Se agregó '➕ Agregar otra cuenta de correo' para sumar "
            "cuentas nuevas, '✎ Editar' para corregir los datos de una ya "
            "guardada (por ejemplo, tras generar una nueva contraseña de "
            "aplicación), y '✕ Desvincular' para quitar una cuenta en "
            "particular sin afectar a las demás — si se desvincula la "
            "activa y quedan otras, el sistema activa automáticamente la "
            "más reciente de las que quedan.",
            "Si ya tenías una cuenta de correo configurada, la migración "
            "es automática y transparente: se conserva tal cual, marcada "
            "como la cuenta activa, sin necesidad de volver a cargarla.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Corrección: la columna 'Documento' se veía cortada en la grilla de Resumen de Ventas",
        "etiqueta": "Corrección",
        "version": "1.19.2",
        "detalles": [
            "En la grilla de ventas del día (pestaña Resumen), la columna "
            "'Documento' era demasiado angosta para mostrar el número "
            "completo de comprobante o factura (ej. 'Comprobante "
            "001-001-0000003' quedaba cortado en '001-001-0...').",
            "Se ensanchó esa columna para que el texto completo se vea de "
            "entrada, sin depender de desplazarse. La grilla también "
            "cuenta con barra de desplazamiento horizontal por si la "
            "ventana queda angosta y hace falta desplazarse para ver el "
            "resto de las columnas.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Mejora: nuevas opciones 10.000 y 100.000 en Historial de Movimientos",
        "etiqueta": "Mejora",
        "version": "1.19.1",
        "detalles": [
            "El filtro 'Mostrar los últimos movimientos' del Historial de "
            "Movimientos de Inventario ahora incluye también las opciones "
            "10.000 y 100.000, además de las que ya había (25, 50, 100, "
            "250, 500, 1.000 y Todos) — útil para productos con muchísimo "
            "movimiento acumulado.",
            "De paso, los números del filtro ahora se muestran con punto "
            "separador de miles (ej. '10.000' en vez de '10000') para "
            "leerse más rápido de un vistazo.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nuevo módulo: Asistente IA (chat con inteligencia artificial real)",
        "etiqueta": "Nuevo",
        "version": "1.19.0",
        "detalles": [
            "Nuevo módulo exclusivo para Administradores (asignable también "
            "a Gerentes): un chat con una IA real conectada por API "
            "(OpenAI/ChatGPT, Anthropic/Claude, u otro proveedor "
            "compatible como DeepSeek/Groq/OpenRouter/un servidor propio), "
            "para responder preguntas sobre el sistema, analizar el "
            "negocio, generar descripciones de productos, o charlar "
            "libremente.",
            "Botón '📊 Analizar mis ventas': arma automáticamente un "
            "resumen de los últimos 30 días (total vendido, ganancia, "
            "productos más vendidos) y le pide recomendaciones concretas "
            "a la IA.",
            "Botón '✨ Generar descripción de producto': redacta una "
            "descripción breve y lista para usar a partir de los datos "
            "del producto que se le indiquen.",
            "Requiere que un Administrador lo configure primero con la "
            "clave de API de su propia cuenta en el proveedor elegido "
            "(botón '🔌 Probar Conexión' para verificarla antes de "
            "guardar). El uso tiene un costo real cobrado por ese "
            "proveedor — MaquedaSystems no cobra nada por esto — y "
            "requiere conexión a internet.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nuevo módulo: Terminal SQL (acceso directo a la base de datos)",
        "etiqueta": "Nuevo",
        "version": "1.18.0",
        "detalles": [
            "Nuevo módulo exclusivo para Administradores: permite ejecutar "
            "consultas SQL directamente sobre la base de datos del "
            "sistema, para correcciones puntuales o consultas de "
            "diagnóstico que las pantallas normales no cubren.",
            "Panel de 'Tablas' (doble click carga y ejecuta un SELECT * "
            "de esa tabla) y de 'Historial' de las últimas consultas "
            "ejecutadas, además del editor SQL con resultados en grilla "
            "para SELECT, o cantidad de filas afectadas para INSERT/"
            "UPDATE/DELETE/CREATE/ALTER/DROP. Se ejecuta con el botón "
            "'▶ Ejecutar', F5 o Ctrl+Enter.",
            "Incluye varias protecciones activas: 'Modo solo lectura' "
            "activado por defecto (solo permite SELECT/PRAGMA/EXPLAIN, "
            "hay que destildarlo a propósito para poder escribir), "
            "confirmación obligatoria mostrando la consulta completa "
            "antes de cualquier cambio, backup automático de toda la "
            "base de datos justo antes de ejecutar una consulta de "
            "escritura, alerta reforzada si un UPDATE o DELETE no tiene "
            "cláusula WHERE, y un límite de una sola sentencia por "
            "ejecución.",
            "También se agregó un acceso directo a esta herramienta desde "
            "Gestión de Datos, sección 'Avanzado'.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Mejora: botones de Guardar/Cancelar y tecla Enter en Nuevo/Editar Producto",
        "etiqueta": "Mejora",
        "version": "1.17.4",
        "detalles": [
            "El botón 'Guardar' de la ventana Nuevo/Editar Producto ahora "
            "se ve como el resto del sistema: relleno en azul con texto "
            "blanco, más grande y fácil de identificar como la acción "
            "principal. 'Cancelar' se mantiene en blanco, para "
            "diferenciarlo claramente.",
            "Antes, presionar Enter solo guardaba el producto si el foco "
            "estaba justo en el botón 'Guardar'. Ahora Enter guarda el "
            "producto desde cualquier campo de cualquiera de las 5 "
            "pestañas (Datos, Datos Adicionales, Imágenes, Proveedor y "
            "Opciones) — por ejemplo, desde el Código de Barras, un "
            "precio, el stock de la pestaña Opciones, etc.",
            "Dos excepciones a propósito: dentro del campo Descripción "
            "(multilínea), Enter sigue insertando un salto de línea como "
            "siempre, sin guardar; y con el foco en el botón 'Cancelar', "
            "Enter cierra la ventana sin guardar, en vez de guardar por "
            "error.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Corrección: 'Armar Venta por Locales' no se reiniciaba después de cobrar una venta",
        "etiqueta": "Corrección",
        "version": "1.17.3",
        "detalles": [
            "Cada pestaña de venta ('Nueva Venta 1', 'Nueva Venta 2', "
            "etc.) ya tenía su propia sesión de 'Armar Venta por "
            "Locales', totalmente independiente de las demás pestañas "
            "— eso ya funcionaba bien.",
            "El problema estaba al cobrar: una vez finalizada y cobrada "
            "la venta, esa pestaña quedaba lista para una venta nueva "
            "(sin productos), pero si se volvía a abrir 'Armar Venta por "
            "Locales' en esa misma pestaña, todavía aparecían los "
            "locales y productos de la venta que ya se había cobrado.",
            "Ahora, al cobrar una venta con éxito, 'Armar Venta por "
            "Locales' se reinicia por completo para esa pestaña: si "
            "estaba abierta en ese momento, se vacía en el acto; y si no "
            "estaba abierta, la próxima vez que se abra en esa misma "
            "pestaña empieza desde cero, sin rastro de la venta ya "
            "cerrada.",
            "Se aplicó la misma corrección al botón '🗑 Limpiar Todo' de "
            "la venta, que tenía el mismo problema en el caso de que "
            "'Armar Venta por Locales' no estuviera abierta en ese "
            "momento.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Corrección: el monto Total podía quedar cortado en 'Nueva Compra'",
        "etiqueta": "Corrección",
        "version": "1.17.2",
        "detalles": [
            "En la pantalla de Nueva Compra, el bloque de Fecha/N° "
            "Comprobante/Proveedor (a la izquierda del pie) se llevaba "
            "todo el espacio disponible antes de que el sistema "
            "reservara lugar para el Total y los botones, así que en "
            "compras con montos grandes (más dígitos) o con la ventana "
            "no maximizada, el 'Gs. ...' del total podía verse cortado o "
            "directamente no entrar en pantalla.",
            "Ahora el Total, el contador de productos y los botones "
            "'Cancelar'/'Guardar Compra' siempre reservan su espacio "
            "completo primero; si hace falta ceder espacio en una "
            "ventana angosta, lo cede el bloque de Fecha/Comprobante/"
            "Proveedor, nunca el monto Total.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Mejora: barras de desplazamiento vertical y horizontal en todas las grillas del sistema",
        "etiqueta": "Mejora",
        "version": "1.17.1",
        "detalles": [
            "Se revisaron las grillas (tablas) de los 28 módulos del "
            "sistema: muchas solo tenían barra de desplazamiento "
            "vertical, así que si una tabla tenía más columnas de las "
            "que entraban en el ancho de la ventana, no había forma de "
            "desplazarse para ver las columnas de más a la derecha.",
            "Ahora prácticamente todas las grillas del sistema (Ventas, "
            "Clientes, Productos, Inventario, Compras, Créditos, "
            "Préstamos, Presupuestos, Pre-Venta, Asistencia Técnica, "
            "Veterinaria, Restaurante/Comedor, Streaming, Reportes, "
            "Usuarios, RRHH, Cotizaciones, Licencias, Gestión de Datos, "
            "entre otras) tienen ambas barras: vertical y horizontal.",
            "También se agregó scroll a algunas tablas más chicas que no "
            "tenían ninguna barra todavía (historial de compras en la "
            "ficha de un cliente, historial de pagos de un préstamo, y "
            "el detalle de artículos del ticket en Resumen de Ventas), "
            "para poder ver todas las filas aunque no entren todas a la "
            "vez en el espacio visible.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nuevo: cada Vendedor ve solo sus propias ventas; Gerente y Administrador ven las de todos",
        "etiqueta": "Nuevo",
        "version": "1.17.0",
        "detalles": [
            "En Resumen de Ventas (la 'Caja' del día) y en el módulo "
            "Reportes, un usuario con rol Vendedor ahora solo ve las "
            "ventas que él mismo generó — ya no aparecen en su pantalla "
            "las ventas de otros vendedores.",
            "El filtro 'Vendedor' del módulo Reportes queda bloqueado en "
            "el propio nombre para un Vendedor (no puede elegir 'Todos' "
            "ni a otro compañero); Gerente y Administrador conservan el "
            "filtro libre, con 'Todos' como opción por defecto para ver "
            "las ventas de cualquier vendedor, incluidas las propias.",
            "El 'Reporte por Rango de Fechas' (desde Resumen de Ventas) y "
            "todas las exportaciones (PDF simple, PDF con dashboard, "
            "Word, ODT, Excel, CSV, JSON, y el envío por correo) respetan "
            "el mismo filtro: lo que exporta o envía un Vendedor son "
            "siempre sus propias ventas.",
            "El arqueo de caja (Saldo Inicial, Entradas, Salidas y Dinero "
            "en Caja) NO se filtra por vendedor: sigue mostrando el total "
            "real del cajón compartido, para que el arqueo del día "
            "siempre cuadre con el efectivo físico, sin importar quién "
            "hizo cada venta.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Corrección: el rol 'Gerente' no se podía guardar (error de base de datos)",
        "etiqueta": "Corrección",
        "version": "1.16.4",
        "detalles": [
            "El rol 'Gerente' ya existía en el formulario de Usuarios y en "
            "la lógica de permisos, pero la base de datos todavía no lo "
            "aceptaba como valor válido: al elegirlo y guardar, el sistema "
            "mostraba un error técnico y no se guardaba nada.",
            "Se corrigió la base de datos para aceptar el rol Gerente, con "
            "una migración automática y transparente que se aplica solo "
            "y una única vez la primera vez que se abre el sistema con "
            "esta actualización, sin necesidad de ninguna acción manual "
            "ni pérdida de datos (usuarios, permisos y el resto de la "
            "información existente quedan exactamente igual).",
            "Recordatorio de cómo funciona el rol Gerente: a diferencia "
            "del Vendedor, puede recibir acceso a módulos administrativos "
            "(por ejemplo RRHH o Gestión de Datos) si el Administrador se "
            "lo asigna explícitamente desde el módulo Usuarios.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Corrección de seguridad: un usuario ya no puede otorgarse a sí mismo un rol o permisos distintos",
        "etiqueta": "Corrección",
        "version": "1.16.3",
        "detalles": [
            "Al editar el propio perfil desde la barra superior (click en "
            "el nombre o en la foto), el formulario reutilizaba la misma "
            "ventana que usa un Administrador para editar a otros "
            "usuarios, incluyendo el selector de Rol y la pestaña de "
            "Permisos de módulos — lo que permitía que cualquier usuario "
            "se auto-asignara el rol de Administrador o marcara permisos "
            "que no le correspondían.",
            "Ahora, al editar el propio perfil, el Rol se muestra "
            "únicamente como información de solo lectura y la pestaña de "
            "Permisos no aparece. Cambiar el rol o los permisos de "
            "acceso a módulos de un usuario sigue siendo posible "
            "únicamente para un Administrador, desde el módulo Usuarios.",
            "Se agregó además una segunda verificación al guardar: aunque "
            "se manipulara la ventana, el rol, el estado (activo/"
            "inactivo) y los permisos de un usuario editando su propio "
            "perfil siempre se guardan exactamente igual a como estaban "
            "antes de abrir el formulario.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Mejora: Ayuda y Gestión de Datos actualizados con Préstamos, Restaurante, Streaming, RRHH y Cotizaciones",
        "etiqueta": "Mejora",
        "version": "1.16.2",
        "detalles": [
            "El módulo Ayuda ahora incluye explicaciones completas de "
            "Préstamos, Restaurante/Comedor, Alquiler de Streaming, "
            "Recursos Humanos y Cotizaciones, que ya existían en el "
            "sistema pero todavía no estaban documentadas.",
            "Gestión de Datos → Exportar CSV suma tablas de Mascotas, "
            "Consultas y Vacunas (Veterinaria), Préstamos, Cuotas y "
            "Movimientos del Fondo, Comandas y Platos (Restaurante), y "
            "Cuentas y Suscripciones (Streaming), para poder respaldar o "
            "analizar esa información por separado.",
            "La copia de seguridad completa (Exportar/Importar BD) ya "
            "incluía todos estos datos desde que se creó cada módulo, ya "
            "que copia el archivo completo de la base de datos.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Corrección: 'Armar Venta por Locales' podía dejar cantidades desactualizadas en la venta",
        "etiqueta": "Corrección",
        "version": "1.16.1",
        "detalles": [
            "En ciertos casos, tras corregir una cantidad en un local y "
            "sincronizar, la grilla de la venta podía quedar mostrando un "
            "valor anterior en vez del total actualizado.",
            "La sincronización ahora reconstruye desde cero, en cada "
            "actualización, las líneas de los productos que administra "
            "'Armar Venta por Locales', en vez de calcular la diferencia "
            "contra la vez anterior — así el resultado siempre es exacto, "
            "sin arrastrar ninguna diferencia acumulada.",
            "Se verificó que las cantidades cargadas manualmente en la "
            "venta (antes de usar Locales) se sigan sumando correctamente, "
            "sin perderse.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nuevo: sincronización en tiempo real entre 'Armar Venta por Locales' y la grilla de venta",
        "etiqueta": "Nuevo",
        "version": "1.16.0",
        "detalles": [
            "Cualquier cambio en un local (agregar producto, ajustar "
            "cantidad, Mayoreo, cerrar un local) se refleja al instante en "
            "la grilla de 'Nueva Venta N', sin necesidad de presionar "
            "'Cargar en Venta'.",
            "También funciona al revés: editar la cantidad de un producto "
            "directamente en la grilla de la venta actualiza el/los "
            "local(es) correspondientes. Si el mismo producto viene de "
            "varios locales, el cambio se reparte manteniendo la "
            "proporción entre ellos.",
            "El botón '🗑 Limpiar Todo' de la venta ahora también vacía "
            "por completo los locales de 'Armar Venta por Locales'.",
            "Se evita abrir dos ventanas de 'Armar Venta por Locales' para "
            "la misma pestaña de venta: si ya está abierta, se trae al "
            "frente en vez de duplicarla.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Mejora: 'Armar Venta por Locales' recuerda la sesión, permite renombrar y usar Mayoreo",
        "etiqueta": "Mejora",
        "version": "1.15.1",
        "detalles": [
            "Cada pestaña de venta ('Nueva Venta 1', 'Nueva Venta 2', "
            "etc.) recuerda su propia sesión de locales: si se cierra la "
            "ventana y se vuelve a abrir, aparece tal cual quedó, lista "
            "para seguir agregando o corrigiendo productos.",
            "Se puede corregir el nombre de un local ya agregado con el "
            "ícono '✏' de su pestaña (antes solo se podía definir al "
            "crearlo).",
            "Se agregó el botón 'Mayoreo' dentro de cada local, para "
            "aplicar el precio mayorista a un producto igual que en la "
            "venta normal (F11), preservando ese precio al cargarlo en la "
            "venta.",
            "Se corrigió un error por el cual, al seleccionar un producto "
            "para ponerle cantidad justo después de cargar otro, el "
            "artículo podía desaparecer de la grilla. Se aplicó la misma "
            "corrección en la pantalla principal de Ventas, donde también "
            "podía ocurrir.",
            "El error 'Permission denied' al generar el PDF (cuando el "
            "archivo ya estaba abierto en otro programa) ahora muestra un "
            "mensaje claro explicando la causa, en vez del error técnico "
            "de Windows.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nuevo: botón 'Armar Venta por Locales' en Ventas",
        "etiqueta": "Nuevo",
        "version": "1.15.0",
        "detalles": [
            "Pensado para dividir una venta grande entre varios locales o "
            "sucursales a los que se les provee, cargando los productos "
            "de cada uno por separado.",
            "Cada local que se agrega tiene su propia grilla de productos "
            "independiente (buscador, código de barra, control de "
            "cantidad), en pestañas dentro de la misma ventana.",
            "Botón 'Generar PDF': arma un pedido con el detalle de cada "
            "local y un resumen consolidado con las cantidades sumadas "
            "entre locales.",
            "Botón 'Cargar en Venta': carga todo lo armado en la venta "
            "actual, sumando automáticamente las cantidades cuando un "
            "mismo producto se repite entre locales.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nuevo módulo: Alquiler de Streaming",
        "etiqueta": "Nuevo",
        "version": "1.14.0",
        "detalles": [
            "Pensado para negocios que revenden accesos a cuentas de "
            "streaming (Netflix, HBO Max, Disney+, YouTube Premium, "
            "Spotify, etc.).",
            "Se administra el catálogo de Plataformas, las Cuentas "
            "compradas (email, contraseña, plan y costo mensual) y sus "
            "Perfiles individuales, que se alquilan sueltos o en Combos de "
            "varias plataformas juntas.",
            "Las Suscripciones de los clientes admiten tres modalidades: "
            "Perfil Individual, Acceso Completo o Combo, y su cobro/"
            "renovación reutiliza el mismo motor de Ventas de siempre.",
            "El Dashboard incluye alertas de seguridad: cuentas que "
            "necesitan rotación de contraseña y suscripciones próximas a "
            "vencer, además de un reporte de rentabilidad por plataforma.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nuevo módulo: Restaurante/Comedor",
        "etiqueta": "Nuevo",
        "version": "1.13.0",
        "detalles": [
            "Pensado para restaurantes, comedores y pizzerías: mapa de "
            "Mesas, Comandas (Mesa, Delivery, Para Llevar o Mostrador) y "
            "Platos con Receta.",
            "Cada plato define qué insumos del catálogo de Productos "
            "consume y en qué cantidad; el costo y el margen se calculan "
            "automáticamente. Para pizzerías se pueden definir Variantes "
            "de tamaño (Individual/Mediana/Familiar) y agregados/quitados "
            "por pedido.",
            "Al cerrar una comanda se genera una venta real (misma "
            "factura, caja y Resumen de Ventas de siempre) y se descuentan "
            "automáticamente los insumos consumidos.",
            "Las comandas de Delivery se pueden asignar a un repartidor y "
            "seguir su estado hasta la entrega.",
            "El Dashboard reúne platos más vendidos, margen por plato, "
            "costos vs. ingresos y ventas por turno (Mañana/Tarde/Noche).",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nuevo módulo: Préstamos",
        "etiqueta": "Nuevo",
        "version": "1.12.0",
        "detalles": [
            "Una pequeña financiera dentro del sistema: pestaña 'Banco "
            "(Fondo)' para cargar capital disponible, 'Nuevo Préstamo' "
            "para dar de alta un préstamo con vista previa del cronograma "
            "de cuotas, y 'Préstamos' para el listado y seguimiento de los "
            "otorgados.",
            "Admite cuatro sistemas de amortización paraguayos: Francés, "
            "Alemán, Americano y Directo/Flat, con frecuencia de cuotas "
            "diaria, semanal, quincenal o mensual.",
            "Calcula automáticamente la mora por atraso según la tasa de "
            "mora diaria configurada en cada préstamo, y permite pagos "
            "parciales o totales de cada cuota.",
            "Incluye reporte en PDF ('Extracto') con el estado completo de "
            "cada préstamo.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nuevo: módulo Veterinaria",
        "etiqueta": "Nuevo",
        "version": "1.11.0",
        "detalles": [
            "Ficha completa de Mascotas: datos del dueño (con vínculo a "
            "Clientes), especie (catálogo editable), raza, sexo, fecha de "
            "nacimiento, peso, microchip y esterilización.",
            "Historial Clínico: registro de consultas con motivo, "
            "diagnóstico, tratamiento indicado, peso, temperatura, "
            "próxima visita y costo.",
            "Vacunas: registro de aplicaciones con lote y veterinario, "
            "más una pestaña 'Vacunas Próximas' que avisa cuáles están "
            "vencidas o por vencer dentro de 30 días.",
            "Tratamientos: desparasitaciones y medicación en curso, con "
            "dosis, frecuencia y opción de marcarlos como finalizados.",
            "Dashboard con tarjetas resumen (mascotas activas, consultas "
            "de hoy, tratamientos activos, vacunas próximas) y el listado "
            "de consultas del día.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nuevo: reportes en PDF y envío por correo desde Veterinaria",
        "etiqueta": "Nuevo",
        "version": "1.10.0",
        "detalles": [
            "Se puede generar un PDF de la ficha completa de una mascota "
            "(historial, vacunas y tratamientos), de una vacuna puntual "
            "(certificado de vacunación), o de una consulta puntual "
            "(constancia de consulta), cada uno con su botón propio.",
            "Botón 'Enviar por Correo' junto a cada PDF: arma el mensaje "
            "con el reporte adjunto, listo para enviar al dueño.",
            "El envío de correos ahora admite cualquier proveedor (Gmail, "
            "Outlook/Hotmail, Yahoo, ProtonMail con Bridge, o un servidor "
            "SMTP personalizado), no solo Gmail como antes. La pantalla de "
            "configuración muestra instrucciones específicas según el "
            "proveedor elegido, y permite cerrar la cuenta configurada "
            "para cargar una distinta.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Corrección: ventana de la Ficha de Mascota — botones ocultos y sin minimizar/maximizar",
        "etiqueta": "Corrección",
        "version": "1.9.5",
        "detalles": [
            "En pantallas más chicas o con mucho contenido cargado, los "
            "botones de la ficha (Marcar Fallecido, Generar PDF, Guardar "
            "Cambios) podían quedar fuera del área visible de la ventana, "
            "sin ninguna forma de llegar a ellos.",
            "La sección de datos del dueño y la mascota ahora tiene su "
            "propio desplazamiento (scroll) independiente, mientras que "
            "la barra de botones quedó fija y siempre visible.",
            "La ventana ya no oculta los botones de minimizar y maximizar "
            "en gestores de ventanas que antes se los quitaban a este tipo "
            "de ventana.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Mejora de diseño: botones con color en Presupuestos, Inventario, Clientes y Pre-Venta",
        "etiqueta": "Mejora",
        "version": "1.9.4",
        "detalles": [
            "Presupuestos: el botón 'Generar PDF' (tanto en la lista como "
            "en el detalle) ahora se muestra en rojo cuando está "
            "disponible, en vez del diseño blanco plano anterior.",
            "Inventario: los botones 'Mostrar Productos Bajos en "
            "Inventario', 'Mostrar Solamente Productos en Stock', "
            "'Mostrar Productos Inactivos' y 'Ocultar/Mostrar Resumen' "
            "ahora tienen colores propios (ámbar, azul, rojo e índigo) que "
            "se intensifican cuando el filtro está aplicado, para "
            "distinguirlos mejor de un vistazo.",
            "Clientes: los botones 'Editar' y 'Eliminar' ahora tienen "
            "color (azul y rojo claro) en vez de texto simple sin fondo.",
            "Pre-Venta: los botones 'Modificar' y 'Eliminar' también "
            "pasaron a tener color (azul y rojo claro).",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Corrección: botones que no respondían al hacer click",
        "etiqueta": "Corrección",
        "version": "1.9.3",
        "detalles": [
            "El botón 'Generar PDF' de Presupuestos y los botones "
            "'Modificar'/'Eliminar' de Pre-Venta quedaban deshabilitados "
            "(en gris) hasta seleccionar una fila de la lista, pero al "
            "hacer click sin seleccionar nada no pasaba absolutamente "
            "nada, dando la sensación de que estaban rotos.",
            "Ahora esos botones siempre responden al click: si no hay "
            "nada seleccionado, el sistema muestra un aviso pidiendo "
            "elegir primero un elemento de la lista.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Corrección: buscador de Inventario casi invisible",
        "etiqueta": "Corrección",
        "version": "1.9.2",
        "detalles": [
            "En ventanas más angostas, el campo de búsqueda de Inventario "
            "quedaba comprimido a un tamaño casi ilegible porque competía "
            "por espacio con los botones de filtro en la misma fila.",
            "Ahora el buscador tiene su propia fila, ocupando todo el "
            "ancho disponible, así siempre se ve bien sin importar "
            "cuántos botones haya arriba.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Mejora: scroll horizontal en la tabla de Resumen de Ventas",
        "etiqueta": "Mejora",
        "version": "1.9.1",
        "detalles": [
            "La tabla de la pestaña 'Resumen' del módulo Ventas ahora "
            "tiene una barra de desplazamiento horizontal además de la "
            "vertical, para poder ver todas las columnas (Código, Fecha y "
            "Hora, Cliente, Importe, Estado Cuenta, Forma de Pago, "
            "Documento) aunque la ventana no sea lo suficientemente ancha "
            "para mostrarlas todas de una vez.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nuevo módulo: Presupuestos",
        "etiqueta": "Nuevo",
        "version": "1.9.0",
        "detalles": [
            "Se agregó el módulo '📝 Presupuestos' para armar cotizaciones "
            "para clientes (existentes o walk-in) sin afectar el stock: "
            "código + Enter, F1 Asignar Cliente, F2 Buscar Producto, DEL "
            "Borrar Artículo — igual que en Ventas — más una Fecha de "
            "Validez y observaciones.",
            "Estados con seguimiento: Pendiente, Aprobado, Rechazado, "
            "Vencido (se calcula solo cuando pasa la fecha de validez) y "
            "Convertido.",
            "Con el presupuesto Aprobado, el botón 'Convertir a Venta' "
            "abre la misma pantalla de Cobro de Ventas ya cargada; recién "
            "al confirmar el cobro se descuenta stock y se genera la "
            "venta real, quedando el presupuesto vinculado a ella.",
            "Botón 'Generar PDF' para entregar el presupuesto al cliente, "
            "con los datos del local si están configurados.",
            "Nueva pestaña 'Presupuestos' en el módulo Reportes, con "
            "tarjetas de resumen que incluyen la Tasa de Conversión (% de "
            "presupuestos que terminaron en una venta), y exportación en "
            "los mismos 7 formatos que Ventas y Compras.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nuevo módulo: Créditos",
        "etiqueta": "Nuevo",
        "version": "1.8.0",
        "detalles": [
            "Se agregó el módulo '💳 Créditos': cada venta procesada con "
            "condición 'Crédito' aparece acá automáticamente, sin carga "
            "manual.",
            "Filtros 'Mostrar Pendientes' / 'Mostrar Todos', botón "
            "'Agrupar por Cliente' (cambia a una vista agregada por "
            "cliente; se puede volver atrás con 'Agrupar por Venta'), y "
            "un panel 'Mostrar/Ocultar Resumen' con los totales generales "
            "de créditos pendientes.",
            "Doble click en un crédito para ver su historial de pagos y "
            "registrar un pago nuevo (parcial o total, con el botón "
            "'Pagar Saldo Total').",
            "Botón 'Estado de Cuenta': arma un resumen completo de todos "
            "los créditos de un cliente, exportable a PDF.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Corrección: 'Editar perfil' y 'Cambiar foto de perfil' no funcionaban",
        "etiqueta": "Corrección",
        "version": "1.7.3",
        "detalles": [
            "Al hacer click en el nombre de usuario (arriba a la derecha) "
            "y elegir 'Editar perfil' o 'Cambiar foto de perfil', el "
            "sistema tiraba un error y no pasaba nada, por una referencia "
            "rota en el código. Ya se corrigió: 'Editar perfil' abre el "
            "formulario en la pestaña Datos básicos, y 'Cambiar foto de "
            "perfil' (o tocar directamente el ícono de la foto) lo abre "
            "directo en la pestaña Foto.",
            "De paso, se agrandó la ventana de Usuario para que la fila "
            "de opciones de Rol (Vendedor / Gerente / Administrador) no "
            "quede cortada, y la lista de Permisos ahora tiene scroll "
            "propio para que nunca falten módulos por mostrar.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Corrección: vistas previas y paneles cortados en Config. Local y RRHH",
        "etiqueta": "Corrección",
        "version": "1.7.2",
        "detalles": [
            "En 'Config. Local', las pestañas 'Comprobante de Venta' y "
            "'Factura Legal' ahora tienen scroll en su columna de "
            "explicación, para que el botón de generar el PDF de ejemplo "
            "ya no quede fuera de la vista en ventanas más chicas.",
            "La vista previa de 'Factura Legal' ahora se comporta igual "
            "que la de 'Comprobante de Venta' al cambiar entre Hoja A4, "
            "Ticketera 80mm y Ticketera 58mm (tenían distinta fuente y "
            "ancho configurados, lo que rompía el formato del recibo).",
            "En Recursos Humanos → Asistencia, la barra de carga rápida "
            "('Ningún empleado seleccionado / Estado / Entrada / Salida / "
            "Guardar') estaba ubicada en la misma fila que la tabla por "
            "un error de configuración, dejando un espacio en blanco "
            "enorme debajo. Ahora queda pegada al fondo de la ventana, "
            "como corresponde.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Mejora: el menú lateral ahora se adapta automáticamente a cualquier pantalla",
        "etiqueta": "Mejora",
        "version": "1.7.1",
        "detalles": [
            "El ancho del menú lateral ya no es fijo: se ajusta automáticamente "
            "al texto más largo entre los módulos que cada usuario tiene "
            "asignados, sin dejar espacio de sobra.",
            "Si la pantalla es chica o hay muchos módulos asignados, el menú "
            "ahora se puede desplazar (con la rueda del mouse, con el "
            "touchpad, o arrastrando con el mouse) para llegar a todos los "
            "módulos, incluso a los últimos de la lista, que antes podían "
            "quedar cortados sin forma de alcanzarlos.",
            "La barra de desplazamiento (scrollbar) es fina y usa los colores "
            "del tema oscuro del menú, y solo aparece cuando realmente hace "
            "falta.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nuevo módulo: Asistencia Técnica",
        "etiqueta": "Nuevo",
        "version": "1.7.0",
        "detalles": [
            "Se agregó el módulo '🖥 Asistencia Técnica' para gestionar el "
            "ingreso de equipos a reparación: botón 'Entrada de Equipo' con "
            "un asistente de 2 pasos (datos del cliente + F2 Buscar Cliente, "
            "datos del equipo + F3 Buscar Equipo, y luego prioridad y "
            "observaciones del ingreso).",
            "Pestaña 'Casos': listado completo con filtros por cantidad a "
            "mostrar y checkboxes de Pendientes/Anulados/Retirados, más "
            "buscador.",
            "Pestaña 'Pendientes': solo los casos activos, con prioridad y "
            "quién los recibió.",
            "Pestaña 'Dashboard': resumen desplegable por estado (Entrada, "
            "En Espera, En Revisión, Disponible para Retiro, Retirados "
            "recientemente) con la cantidad de casos en cada uno.",
            "Pestaña 'Equipos': catálogo de equipos ya registrados, para "
            "encontrarlos rápido la próxima vez que un cliente recurrente "
            "trae el mismo equipo.",
            "Cada caso se puede abrir para cambiar su estado, agregar "
            "observaciones o anularlo.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nuevo: el módulo Pre-Venta ya funciona de punta a punta",
        "etiqueta": "Nuevo",
        "version": "1.6.0",
        "detalles": [
            "El botón 'F8 - Generar Preventa' de la ventana Cobrar (que antes "
            "solo mostraba un aviso) ahora guarda de verdad una pre-venta: "
            "cliente y artículos cargados, sin descontar stock ni generar "
            "ningún comprobante todavía.",
            "Nuevo módulo 'Pre-Venta' en el menú: lista todas las pre-ventas "
            "pendientes, con botones para 'Modificar' (retomar la carga, "
            "agregar o quitar artículos, y finalizar el cobro cuando el "
            "cliente vuelve) y 'Eliminar'.",
            "Al finalizar el cobro de una pre-venta, recién ahí se descuenta "
            "el stock y se genera la venta real; la pre-venta se elimina "
            "automáticamente porque ya cumplió su función.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nuevo módulo: Compras",
        "etiqueta": "Nuevo",
        "version": "1.5.0",
        "detalles": [
            "Se agregó el módulo '🛒 Compras' para registrar compras a "
            "proveedores: código de producto + Enter para agregar, F2 "
            "Buscar Producto, DEL para borrar un artículo, y un popup que "
            "pide cantidad y precio de compra al cargar cada producto.",
            "Cada compra registrada suma el stock del producto automática, "
            "actualiza su precio de compra, y queda registrada en el "
            "historial de movimientos de inventario del producto (igual que "
            "una Entrada manual), con su comprobante y proveedor.",
            "Se puede elegir el proveedor de la compra (con alta rápida de "
            "proveedores nuevos desde la misma pantalla) y la fecha de "
            "compra con calendario.",
            "Nueva pestaña 'Compras' dentro del módulo Reportes: filtros por "
            "rango de fechas y proveedor, tarjetas de resumen (cantidad, "
            "total comprado, promedio, proveedores distintos), detalle de "
            "cada compra, y exportación en 7 formatos (PDF con gráfico, PDF "
            "simple, Word, LibreOffice, Excel, CSV y JSON).",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Corrección: espacio en blanco de sobra en el Historial de Movimientos",
        "etiqueta": "Corrección",
        "version": "1.4.2",
        "detalles": [
            "En 'Historial de Movimientos' de Inventario, la fila con el "
            "filtro 'Mostrar los últimos movimientos' dejaba un espacio en "
            "blanco arriba y abajo por un error de configuración. Ya se "
            "corrigió: esa fila mantiene su tamaño justo y solo la tabla de "
            "movimientos se expande para llenar el resto de la ventana.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Corrección: ventanas del sistema con doble botón de cerrar",
        "etiqueta": "Corrección",
        "version": "1.4.1",
        "detalles": [
            "Algunas ventanas (como 'Compras') mostraban dos botones para "
            "cerrar: el de la barra de título de Windows y otro duplicado "
            "dibujado dentro de la ventana. Se quitó el duplicado, dejando "
            "solo el botón nativo de Windows.",
            "De paso, esas mismas ventanas (Compras, Buscar Producto, Precio "
            "de Compra, Editar Artículo, Nuevo Proveedor, Detalle de "
            "Compra) ahora son redimensionables y se pueden maximizar o "
            "minimizar con los botones normales de la barra de título.",
            "El popup de 'Precio de Compra' ahora también pide la Cantidad "
            "del producto (antes solo pedía el precio), igual que en "
            "'Editar Artículo'.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nuevo: Tema Oscuro para todo el sistema",
        "etiqueta": "Nuevo",
        "version": "1.4.0",
        "detalles": [
            "Desde '🔤 Ajustes del Sistema' ahora se puede elegir entre "
            "tema '☀ Claro' (el diseño original) y '🌙 Oscuro' — fondos "
            "oscuros y texto claro en todas las pantallas, tablas, "
            "botones y formularios, pensado para trabajar con poca luz "
            "o simplemente para quien prefiera esa estética.",
            "El cambio se aplica al instante en cualquier pantalla ya "
            "abierta, sin reiniciar el programa, y queda guardado para "
            "la próxima vez que se use el sistema.",
            "La barra superior y el menú lateral mantienen su diseño "
            "oscuro de siempre en ambos temas (ya estaban pensados para "
            "verse bien con poca luz); lo que cambia con el tema es el "
            "resto de cada pantalla.",
            "Se puede volver al diseño original en cualquier momento "
            "con el botón 'Restablecer valores predeterminados'.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nuevo módulo: Ajustes del Sistema (fuente y tamaño de letra)",
        "etiqueta": "Nuevo",
        "version": "1.3.0",
        "detalles": [
            "Se agregó un nuevo módulo, '🔤 Ajustes del Sistema' (solo "
            "para Administradores), que permite cambiar la tipografía y "
            "el tamaño de letra de TODO el sistema — todas las pantallas, "
            "para todos los usuarios — sin reiniciar el programa.",
            "Se puede elegir entre varias fuentes (Segoe UI, Arial, "
            "Calibri, Verdana, Tahoma, Century Gothic) y agrandar o "
            "achicar el tamaño de letra con botones '－'/'＋', desde 60% "
            "hasta 200%.",
            "Incluye un botón 'Restablecer valores predeterminados' para "
            "volver todo a la configuración original (Segoe UI, 100%) "
            "en un solo click.",
            "El cambio se aplica al instante en cualquier pantalla ya "
            "abierta y queda guardado para la próxima vez que se abra el "
            "sistema.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Corrección: el contenido de Ayuda ya no \"salta\" al cambiar de tema",
        "etiqueta": "Corrección",
        "version": "1.2.7",
        "detalles": [
            "En el módulo Ayuda, si se pasaba de un tema con mucho texto "
            "(desplazado hacia abajo) a otro tema más corto -por ejemplo "
            "arrastrando el mouse sobre el árbol de temas, que selecciona "
            "fila por fila mientras se mueve el cursor-, la posición del "
            "scroll quedaba 'pegada' en la posición anterior y mostraba "
            "un espacio en blanco en vez del contenido nuevo.",
            "Ahora, cada vez que se abre un tema, el scroll vuelve "
            "siempre al principio y se recalcula correctamente según el "
            "tamaño real del texto nuevo.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Resumen de Inventario separado por tipo de Unidad de Medida",
        "etiqueta": "Mejora",
        "version": "1.2.6",
        "detalles": [
            "El panel 'Resumen de Inventario' (y también el Reporte "
            "General en pantalla, PDF y Excel) ya no mezcla en un solo "
            "número las cantidades de productos por Unidad con las de "
            "productos por Kilogramo/Litro/Metro.",
            "Ahora se muestran dos bloques separados: '📦 Por Unidad "
            "(Unidad, Caja, Paquete, Docena)' y '⚖ Por Peso/Medida "
            "(Kilogramo, Litro, Metro)', cada uno con su propia Cantidad "
            "en Stock, Valor a Precio de Compra y Valor a Precio de "
            "Venta.",
            "Esto evita sumas sin sentido como '20 Unidades + 15,3 Kg = "
            "35,3', que no representan una cantidad real.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "La Unidad de Medida ahora se muestra junto al Stock en Productos e Inventario",
        "etiqueta": "Mejora",
        "version": "1.2.5",
        "detalles": [
            "En los módulos Productos e Inventario, las columnas de "
            "cantidad ('STOCK MÍNIMO', 'STOCK', 'COMPROMETIDO' y "
            "'DISPONIBLE') ahora muestran una abreviatura de la Unidad "
            "de Medida del producto junto al número.",
            "Ejemplos: '20 Unid.' para productos por Unidad, '15,3 Kg' "
            "para productos por Kilogramo, '5 Doc.' para productos por "
            "Docena, etc.",
            "Esto ayuda a distinguir de un vistazo si una cantidad "
            "corresponde a unidades enteras o a un peso/medida "
            "fraccionable.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Validación de cantidades decimales en Ventas",
        "etiqueta": "Corrección",
        "version": "1.2.4",
        "detalles": [
            "En la pantalla de Ventas, el campo de cantidad (el que se "
            "edita con los botones '－'/'＋' o escribiendo directamente) "
            "ya no permite cargar decimales en productos cuya Unidad de "
            "Medida es 'Unidad', 'Caja', 'Paquete' o 'Docena'.",
            "Antes, si se escribía '1,5' en un producto por Unidad, el "
            "sistema lo aceptaba igual (redondeándolo a '1.5'). Ahora "
            "muestra un aviso indicando que esa unidad no admite "
            "decimales y pide un número entero.",
            "Los productos con Unidad de Medida 'Kilogramo', 'Litro' o "
            "'Metro' siguen admitiendo cantidades con decimales "
            "normalmente (ej.: 1,5 kg).",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Formato de moneda ajustado al Guaraní Paraguayo",
        "etiqueta": "Corrección",
        "version": "1.2.3",
        "detalles": [
            "Todos los montos en Guaraníes que muestra el sistema (Ventas, "
            "Cobro, Reportes, Clientes, Productos, Inventario, Gestión de "
            "Datos, correos, etc.) ahora usan la convención numérica "
            "paraguaya: punto como separador de miles y sin decimales.",
            "Antes se mostraba, por ejemplo, 'Gs. 24,000' (estilo inglés). "
            "Ahora se muestra 'Gs. 24.000'.",
            "El cambio es solo visual: los valores guardados en la base "
            "de datos no se modificaron.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Formato de cantidades según la Unidad de Medida",
        "etiqueta": "Mejora",
        "version": "1.2.2",
        "detalles": [
            "Las cantidades de stock (en Productos, Inventario y el "
            "formulario de Nuevo/Editar Producto) ahora se muestran con "
            "el formato numérico hispano/paraguayo: punto como separador "
            "de miles y coma como separador decimal.",
            "Para unidades NO fraccionables (Unidad, Caja, Paquete, "
            "Docena): se muestran como número entero. Ej.: 1200 → "
            "'1.200'.",
            "Para unidades fraccionables (Kilogramo, Litro, Metro): se "
            "muestran con decimales usando coma. Ej.: 1200,5 → "
            "'1.200,5'.",
            "El formato se adapta automáticamente al elegir la 'Unidad "
            "de Medida' del producto, y funciona igual al escribir "
            "cantidades a mano (por ejemplo, en Entrada/Salida de "
            "Inventario).",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Resumen de Inventario: valor a precio de venta y a precio de compra",
        "etiqueta": "Mejora",
        "version": "1.2.1",
        "detalles": [
            "En el módulo Inventario, el panel 'Resumen de Inventario' (y "
            "también el Reporte General y las exportaciones a PDF/Excel) "
            "ahora muestra DOS indicadores de valor, calculados sobre el "
            "stock total de todos los productos:",
            "'Valor Total del Inventario (a Precio de Venta)' — stock × precio "
            "de venta de cada producto. Refleja cuánto ingresaría el "
            "negocio si se vendiera todo el stock actual.",
            "'Valor Total del Inventario (a Precio de Compra)' — stock × "
            "precio de compra de cada producto. Refleja el costo de "
            "reposición de todo el stock actual.",
            "Este segundo indicador reemplaza al anterior 'Valor "
            "Comprometido', que calculaba algo distinto (solo las "
            "unidades reservadas en ventas a crédito o preventas) y "
            "generaba confusión.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Nueva forma de pago: Criptomonedas",
        "etiqueta": "Nuevo",
        "version": "1.2.0",
        "detalles": [
            "En la pantalla de Cobro (F12), ahora se puede elegir "
            "'Criptomonedas' como forma de pago, debajo de 'Transferencia "
            "Bancaria'.",
            "Se registra y se filtra en Reportes igual que cualquier otra "
            "forma de pago.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Accesos directos para editar tu perfil desde la barra superior",
        "etiqueta": "Nuevo",
        "version": "1.1.0",
        "detalles": [
            "Ahora se puede hacer click directo en la FOTO de perfil "
            "(arriba a la derecha) para cambiarla al instante: se abre "
            "el formulario de usuario ya en la pestaña 'Foto' y, además, "
            "se abre automáticamente el explorador de archivos para "
            "elegir la nueva imagen.",
            "Al hacer click en el NOMBRE o el ROL del usuario logueado, "
            "se abre directamente el formulario completo 'Editar "
            "Usuario' en la pestaña 'Datos básicos', sin pasar por "
            "ningún paso intermedio.",
            "Este mismo comportamiento (foto → pestaña Foto, nombre → "
            "pestaña Datos básicos) también se agregó al panel de "
            "detalle del módulo Usuarios, para que los administradores "
            "editen más rápido a cualquier usuario de la lista.",
            "Los cambios (foto, nombre, rol) se reflejan de inmediato en "
            "la barra superior al guardar, sin necesidad de cerrar "
            "sesión ni reiniciar el sistema.",
        ],
    },
    {
        "fecha": "Julio 2026",
        "titulo": "Corrección en la edición del perfil propio",
        "etiqueta": "Corrección",
        "version": "1.0.0",
        "detalles": [
            "Se solucionó un error que impedía abrir correctamente el "
            "formulario de 'Editar mi perfil' desde la barra superior.",
        ],
    },
]

# Versión actual del sistema: se toma automáticamente de la primera
# entrada de NOVEDADES (la más reciente), para no tener que mantener el
# número de versión a mano en dos lugares distintos. Si NOVEDADES
# estuviera vacía (no debería pasar nunca), cae a "1.0.0" por defecto.
VERSION_ACTUAL = NOVEDADES[0]["version"] if NOVEDADES else "1.0.0"


def _colores_etiqueta(etiqueta: str):
    """Antes era un diccionario fijo a nivel de módulo, pero eso se
    evaluaba una sola vez al importar el archivo y quedaba "congelado"
    con el tema que estuviera activo en ese momento. Como función, se
    vuelve a evaluar cada vez que se dibuja una tarjeta, así respeta el
    tema (Claro/Oscuro) actual."""
    mapa = {
        "Nuevo":       (temas.c("#16a34a"), temas.c("#dcfce7")),
        "Mejora":      (temas.c("#1d5fd6"), temas.c("#dbeafe")),
        "Corrección":  (temas.c("#d97706"), temas.c("#fef3c7")),
    }
    return mapa.get(etiqueta, (temas.c("#1d5fd6"), temas.c("#e0e7ff")))


# ─────────────────────────────────────────────────────────────
#  PANEL PRINCIPAL
# ─────────────────────────────────────────────────────────────
class PanelNovedades(tk.Frame):
    def __init__(self, parent, usuario_actual):
        super().__init__(parent, bg=temas.c(BLANCO))
        self.usuario_actual = usuario_actual
        self._construir_ui()
        self._cargar_novedades()

    # ── UI raíz ──────────────────────────────────────────────────
    def _construir_ui(self):
        encabezado = tk.Frame(self, bg=temas.c(MORADO), height=54)
        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)
        tk.Label(encabezado, text=t("novedades_titulo"),
                 font=fuentes.f(15, "bold"), bg=temas.c(MORADO), fg=temas.c(BLANCO)
                 ).pack(side="left", padx=20, pady=12)
        tk.Label(encabezado, text=t("novedades_subtitulo"),
                 font=fuentes.f(9), bg=temas.c(MORADO), fg=temas.c("#ede9fe")
                 ).pack(side="left", padx=(0, 20))
        tk.Label(encabezado, text=f"v{VERSION_ACTUAL}",
                 font=fuentes.f(9, "bold"), bg=temas.c(BLANCO), fg=temas.c(MORADO),
                 padx=8, pady=2).pack(side="right", padx=20)

        cont_scroll = tk.Frame(self, bg=temas.c(BLANCO))
        cont_scroll.pack(fill="both", expand=True, padx=20, pady=16)
        cont_scroll.grid_rowconfigure(0, weight=1)
        cont_scroll.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(cont_scroll, bg=temas.c(BLANCO), highlightthickness=0)
        sb = ttk.Scrollbar(cont_scroll, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")

        self.frame_lista = tk.Frame(canvas, bg=temas.c(BLANCO))
        self._ventana_canvas = canvas.create_window(
            (0, 0), window=self.frame_lista, anchor="nw")

        def _scrollregion(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _ajustar_ancho(event):
            canvas.itemconfig(self._ventana_canvas, width=event.width)

        self.frame_lista.bind("<Configure>", _scrollregion)
        canvas.bind("<Configure>", _ajustar_ancho)

        def _rueda(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
            else:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        # Guardamos referencias para poder aplicar el mismo binding, más
        # abajo, a cada tarjeta/label nueva que se genere dinámicamente
        # en _cargar_novedades (ver _bind_rueda_recursivo). Si solo se
        # bindea el canvas y el frame contenedor, el mouse queda "sordo"
        # al scroll en cuanto está posicionado sobre el TEXTO de una
        # tarjeta (que es la mayor parte del área visible), porque en
        # Tkinter los eventos de mouse no burbujean solos hacia el padre.
        self._canvas_novedades = canvas
        self._callback_rueda = _rueda
        self._bind_rueda_recursivo(canvas)
        self._bind_rueda_recursivo(self.frame_lista)

    def _bind_rueda_recursivo(self, widget):
        """Ata el scroll del mouse a `widget` y a TODOS sus descendientes,
        para que funcione sin importar sobre qué elemento esté el cursor
        (label, frame, etc.) dentro del área con scroll."""
        widget.bind("<MouseWheel>", self._callback_rueda)
        widget.bind("<Button-4>", self._callback_rueda)
        widget.bind("<Button-5>", self._callback_rueda)
        for hijo in widget.winfo_children():
            self._bind_rueda_recursivo(hijo)

    # ── Tarjetas de novedades ─────────────────────────────────────
    def _cargar_novedades(self):
        for w in self.frame_lista.winfo_children():
            w.destroy()

        if not NOVEDADES:
            tk.Label(self.frame_lista,
                     text="Todavía no hay novedades cargadas.",
                     font=fuentes.f(10, "italic"), bg=temas.c(BLANCO),
                     fg=temas.c(GRIS_TEXTO)).pack(pady=30)
            self._bind_rueda_recursivo(self.frame_lista)
            return

        for i, item in enumerate(NOVEDADES):
            self._crear_tarjeta(item, es_primera=(i == 0))

        # Las tarjetas se crean DESPUÉS de bindear canvas/frame_lista en
        # _construir_ui, así que hay que repetir el binding recursivo
        # ahora que ya existen (si no, el scroll no funciona al pasar el
        # mouse sobre el texto de las tarjetas).
        self._bind_rueda_recursivo(self.frame_lista)

    def _crear_tarjeta(self, item, es_primera=False):
        tarjeta = tk.Frame(self.frame_lista, bg=temas.c(BLANCO),
                           highlightbackground=temas.c(GRIS_BORDE), highlightthickness=1)
        tarjeta.pack(fill="x", pady=(0, 14))

        cuerpo = tk.Frame(tarjeta, bg=temas.c(BLANCO), padx=18, pady=14)
        cuerpo.pack(fill="x")

        # Fila superior: etiqueta + fecha (+ "Última actualización" en la primera)
        fila_top = tk.Frame(cuerpo, bg=temas.c(BLANCO))
        fila_top.pack(fill="x", anchor="w")

        color_fg, color_bg = _colores_etiqueta(item["etiqueta"])
        tk.Label(fila_top, text=f"  {item['etiqueta']}  ",
                 font=fuentes.f(8, "bold"), bg=color_bg, fg=color_fg
                 ).pack(side="left")
        tk.Label(fila_top, text=f"v{item.get('version', '—')}",
                 font=fuentes.f(8, "bold"), bg=temas.c(GRIS_FONDO), fg=temas.c(GRIS_TEXTO)
                 ).pack(side="left", padx=(6, 0))
        tk.Label(fila_top, text=item["fecha"],
                 font=fuentes.f(9), bg=temas.c(BLANCO), fg=temas.c(GRIS_TEXTO)
                 ).pack(side="left", padx=(10, 0))
        if es_primera:
            tk.Label(fila_top, text="★ Última actualización",
                     font=fuentes.f(8, "bold"), bg=temas.c(BLANCO), fg=temas.c(MORADO)
                     ).pack(side="right")

        # Título
        tk.Label(cuerpo, text=item["titulo"],
                 font=fuentes.f(12, "bold"), bg=temas.c(BLANCO), fg=temas.c(NEGRO),
                 wraplength=760, justify="left"
                 ).pack(anchor="w", pady=(6, 8))

        # Detalles (bullets)
        for punto in item["detalles"]:
            fila = tk.Frame(cuerpo, bg=temas.c(BLANCO))
            fila.pack(fill="x", anchor="w", pady=2)
            tk.Label(fila, text="•", font=fuentes.f(10, "bold"),
                     bg=temas.c(BLANCO), fg=color_fg, width=2, anchor="n"
                     ).pack(side="left")
            tk.Label(fila, text=punto, font=fuentes.f(10), bg=temas.c(BLANCO),
                     fg=temas.c("#374151"), justify="left", anchor="w",
                     wraplength=720).pack(side="left", fill="x", expand=True)
