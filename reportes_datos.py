"""
reportes_datos.py
Capa neutral que prepara los datos de un reporte (Inventario o Ventas por
rango) en una estructura común e independiente del formato de salida.
Todos los generadores (PDF, Word, ODT, Excel, CSV, JSON) consumen esta
misma estructura, evitando duplicar la lógica de negocio en cada formato.

Estructura devuelta por ambas funciones:
{
    "titulo": str,
    "subtitulo": str,
    "generado_por": str,
    "secciones": [
        {"tipo": "resumen", "titulo": str, "filas": [(etiqueta, valor_texto), ...]},
        {"tipo": "grafico_barras", "titulo": str, "categorias": [...], "valores": [...]},  # opcional
        {"tipo": "tabla", "titulo": str, "encabezados": [...], "filas": [[...], ...]},
    ]
}
"""
import datetime

from models_catalogo import listar_productos, productos_bajo_stock_minimo, top_productos_por_valor_inventario, resumen_inventario
from models_ventas import resumen_financiero_en_rango, ventas_por_dia_en_rango, productos_mas_vendidos_en_rango, listar_movimientos_caja


def _formato_gs(monto) -> str:
    return f"Gs. {monto:,.0f}"


def _fecha_legible(fecha_iso: str) -> str:
    try:
        return datetime.date.fromisoformat(fecha_iso).strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return str(fecha_iso)


def preparar_datos_reporte_inventario(generado_por: str = "") -> dict:
    resumen = resumen_inventario()
    bajo_stock = productos_bajo_stock_minimo()
    top_valor = top_productos_por_valor_inventario(limite=10)
    productos = listar_productos()

    secciones = [
        {
            "tipo": "resumen",
            "titulo": "RESUMEN GENERAL",
            "filas": [
                ("Cantidad de Productos Distintos", str(len(productos))),
                ("Cantidad Total de Unidades en Stock", f"{resumen['cantidad_total']:,.2f}"),
                ("Valor del Inventario (a Precio de Compra)", _formato_gs(resumen["valor_inventario"])),
                ("Valor Comprometido (a Precio de Compra)", _formato_gs(resumen["valor_comprometido"])),
                ("Productos Bajo Stock Mínimo", str(len(bajo_stock))),
            ],
        },
        {
            "tipo": "tabla",
            "titulo": "PRODUCTOS BAJO STOCK MÍNIMO",
            "encabezados": ["Código", "Descripción", "Stock Actual", "Stock Mínimo", "Faltante"],
            "filas": [
                [str(p["id"]), p["nombre"], f"{p['stock']:,.2f}", f"{p['stock_minimo']:,.2f}",
                 f"{p['stock_minimo'] - p['stock']:,.2f}"]
                for p in bajo_stock
            ],
        },
        {
            "tipo": "tabla",
            "titulo": "TOP PRODUCTOS POR VALOR DE INVENTARIO",
            "encabezados": ["#", "Producto", "Stock", "Precio Compra", "Valor en Inventario"],
            "filas": [
                [str(i + 1), p["nombre"], f"{p['stock']:,.2f}", _formato_gs(p["precio_compra"]), _formato_gs(p["valor"])]
                for i, p in enumerate(top_valor)
            ],
        },
        {
            "tipo": "tabla",
            "titulo": "LISTADO COMPLETO DE PRODUCTOS",
            "encabezados": ["Código", "Descripción", "P. Compra", "P. Venta", "Stock", "Disponible"],
            "filas": [
                [
                    str(p["id"]), p["nombre"], _formato_gs(p["precio_compra"]), _formato_gs(p["precio_venta"]),
                    "—" if p["tipo_producto"] == "Servicio" else f"{p['stock']:,.2f}",
                    p["disponible"] if isinstance(p["disponible"], str) else f"{p['disponible']:,.2f}",
                ]
                for p in productos
            ],
        },
    ]

    return {
        "titulo": "Reporte General de Inventario",
        "subtitulo": f"Generado el {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "generado_por": generado_por,
        "secciones": secciones,
    }


def preparar_datos_reporte_ventas(fecha_desde: str, fecha_hasta: str, generado_por: str = "",
                                   usuario_id: int | None = None) -> dict:
    """usuario_id: si se indica, limita las ventas y sus totales derivados
    (Ventas Totales, Ganancia, Efectivo, Transferencia, gráfico y ranking
    de productos) a las de ese usuario — para que un Vendedor solo vea/
    reciba en el reporte sus propias ventas. El desglose de caja (Entradas,
    Salidas, Dinero en Caja) y sus movimientos siguen siendo el total real
    y compartido del cajón, sin filtrar."""
    resumen = resumen_financiero_en_rango(fecha_desde, fecha_hasta, usuario_id=usuario_id)
    ventas_dias = ventas_por_dia_en_rango(fecha_desde, fecha_hasta, usuario_id=usuario_id)
    top_productos = productos_mas_vendidos_en_rango(fecha_desde, fecha_hasta, limite=10, usuario_id=usuario_id)
    movimientos_caja = listar_movimientos_caja(fecha_desde, fecha_hasta)

    secciones = [
        {
            "tipo": "resumen",
            "titulo": "RESUMEN GENERAL",
            "filas": [
                ("Cantidad de Ventas", str(len(resumen["ventas"]))),
                ("Ventas Totales", _formato_gs(resumen["ventas_totales"])),
                ("Ganancia Estimada", _formato_gs(resumen["ganancia"])),
                ("Ventas en Efectivo", _formato_gs(resumen["ventas_efectivo"])),
                ("Ventas por Transferencia", _formato_gs(resumen["ventas_transferencia"])),
                ("Entradas de Efectivo", _formato_gs(resumen["entradas"])),
                ("Salidas de Efectivo", _formato_gs(resumen["salidas"])),
                ("Devoluciones", _formato_gs(resumen["devoluciones"])),
                ("Dinero en Caja", _formato_gs(resumen["dinero_en_caja"])),
            ],
        },
        {
            "tipo": "grafico_barras",
            "titulo": "VENTAS POR DÍA",
            "categorias": [_fecha_legible(d["fecha"])[:5] for d in ventas_dias],
            "valores": [d["total"] for d in ventas_dias],
        },
        {
            "tipo": "tabla",
            "titulo": "PRODUCTOS MÁS VENDIDOS",
            "encabezados": ["#", "Producto", "Cantidad", "Importe"],
            "filas": [
                [str(i + 1), p["nombre"], f"{p['cantidad']:g}", _formato_gs(p["importe"])]
                for i, p in enumerate(top_productos)
            ],
        },
        {
            "tipo": "tabla",
            "titulo": "ENTRADAS Y SALIDAS DE EFECTIVO",
            "encabezados": ["Fecha", "Tipo", "Monto", "Motivo", "Registrado por"],
            "filas": [
                [
                    m["fecha"], "Entrada" if m["tipo"] == "entrada" else "Salida",
                    _formato_gs(m["monto"]), m["descripcion"], m["usuario"],
                ]
                for m in movimientos_caja
            ],
        },
        {
            "tipo": "tabla",
            "titulo": "DETALLE DE VENTAS DEL PERÍODO",
            "encabezados": ["Código", "Fecha y Hora", "Cliente", "Importe", "Estado", "Forma de Pago"],
            "filas": [
                [str(v["id"]), v["fecha"], v["cliente"], _formato_gs(v["importe"]), v["estado"], v["forma_pago"]]
                for v in resumen["ventas"]
            ],
        },
    ]

    periodo_texto = f"Período: {_fecha_legible(fecha_desde)} al {_fecha_legible(fecha_hasta)}"
    return {
        "titulo": "Reporte de Ventas",
        "subtitulo": periodo_texto,
        "generado_por": generado_por,
        "secciones": secciones,
    }
