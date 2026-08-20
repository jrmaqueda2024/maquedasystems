"""
models_clima.py
Datos de ubicaciones de Paraguay (los 17 departamentos + Asunción como
Distrito Capital, con sus principales ciudades/distritos) y la lógica
para consultar el clima actual de cualquiera de ellas.

Fuente de datos climáticos: Open-Meteo (https://open-meteo.com), una API
pública, gratuita y sin necesidad de clave de API, con muy buena
cobertura para Sudamérica. Se evaluó usar directamente el sitio de la
Dirección de Meteorología e Hidrología de Paraguay (DINAC,
meteorologia.gov.py), pero ese sitio está pensado para consulta humana
(HTML), no publica una API pública y estable para uso automatizado —
usarlo implicaría "scrapear" su página, algo frágil que se rompe con
cualquier cambio de diseño del sitio. Open-Meteo, en cambio, es una API
diseñada específicamente para este uso, gratuita y confiable.

Nota sobre las ubicaciones: se incluye una lista amplia y curada de
ciudades/distritos (los 17 departamentos completos, cada uno con su
capital departamental y varios de sus distritos más poblados/conocidos),
pero no es un listado oficial exhaustivo de los ~260 distritos del país
— para distritos muy pequeños que no estén en la lista, se puede elegir
la ciudad más cercana del mismo departamento.
"""
import json
import urllib.request
import urllib.error

TIMEOUT_SEGUNDOS = 15

# ============================================================
# DEPARTAMENTOS Y DISTRITOS DE PARAGUAY (con coordenadas aprox.)
# ============================================================
DEPARTAMENTOS = {
    "Distrito Capital": {
        "capital": "Asunción",
        "distritos": [
            ("Asunción", -25.2867, -57.3333),
        ],
    },
    "Central": {
        "capital": "Areguá",
        "distritos": [
            ("Areguá", -25.3167, -57.4000),
            ("Asunción (Área Metro.)", -25.2867, -57.3333),
            ("Luque", -25.2711, -57.4875),
            ("San Lorenzo", -25.3400, -57.5083),
            ("Fernando de la Mora", -25.3258, -57.5347),
            ("Lambaré", -25.3450, -57.6072),
            ("Capiatá", -25.3550, -57.4453),
            ("Ñemby", -25.3961, -57.5347),
            ("Villa Elisa", -25.3667, -57.5967),
            ("Itauguá", -25.3956, -57.3550),
            ("Ypacaraí", -25.4083, -57.2903),
            ("Mariano Roque Alonso", -25.2000, -57.5167),
            ("Limpio", -25.1667, -57.4917),
            ("Guarambaré", -25.4500, -57.4667),
            ("J. Augusto Saldívar", -25.4333, -57.5333),
            ("Villeta", -25.5117, -57.5606),
            ("San Antonio", -25.4167, -57.5583),
        ],
    },
    "Alto Paraná": {
        "capital": "Ciudad del Este",
        "distritos": [
            ("Ciudad del Este", -25.5163, -54.6114),
            ("Hernandarias", -25.4083, -54.6333),
            ("Presidente Franco", -25.5833, -54.6000),
            ("Minga Guazú", -25.4833, -54.7167),
            ("Santa Rita", -25.0833, -54.8500),
            ("Naranjal", -25.4167, -54.8833),
            ("Dr. Juan León Mallorquín", -25.3333, -54.9167),
        ],
    },
    "Itapúa": {
        "capital": "Encarnación",
        "distritos": [
            ("Encarnación", -27.3306, -55.8664),
            ("Coronel Bogado", -27.1167, -56.2500),
            ("Cambyretá", -27.2833, -55.8167),
            ("Carmen del Paraná", -27.2167, -56.0500),
            ("Hohenau", -27.0833, -55.9167),
            ("Obligado", -27.0500, -55.9167),
            ("Bella Vista", -27.0667, -55.5500),
            ("Capitán Miranda", -27.2833, -55.9333),
            ("Jesús", -27.1333, -55.7333),
            ("Trinidad", -27.0333, -55.6667),
        ],
    },
    "Caaguazú": {
        "capital": "Coronel Oviedo",
        "distritos": [
            ("Coronel Oviedo", -25.4167, -56.4333),
            ("Caaguazú", -25.4667, -56.0333),
            ("Repatriación", -25.5500, -55.9333),
            ("Yhú", -25.0000, -55.9333),
            ("Nueva Londres", -25.6667, -56.2833),
            ("Juan Manuel Frutos (Dr. Cecilio Báez)", -25.5333, -55.8000),
        ],
    },
    "San Pedro": {
        "capital": "San Pedro del Ycuamandiyú",
        "distritos": [
            ("San Pedro del Ycuamandiyú", -24.0655, -57.0752),
            ("San Estanislao", -24.6500, -56.4333),
            ("Santa Rosa del Aguaray", -23.9833, -56.6167),
            ("Choré", -24.3833, -56.4333),
            ("Guayaibí", -24.3333, -56.4500),
            ("Lima", -23.8833, -56.4833),
        ],
    },
    "Cordillera": {
        "capital": "Caacupé",
        "distritos": [
            ("Caacupé", -25.3859, -57.0083),
            ("Piribebuy", -25.4667, -57.0333),
            ("Atyrá", -25.2667, -57.1000),
            ("Tobatí", -25.2667, -57.0667),
            ("Eusebio Ayala", -25.4167, -56.9667),
            ("Altos", -25.2833, -57.2000),
        ],
    },
    "Guairá": {
        "capital": "Villarrica",
        "distritos": [
            ("Villarrica", -25.7500, -56.4333),
            ("Independencia", -25.6833, -56.2833),
            ("Borja", -25.7833, -56.3667),
            ("Mbocayaty", -25.9167, -56.4167),
        ],
    },
    "Caazapá": {
        "capital": "Caazapá",
        "distritos": [
            ("Caazapá", -26.1967, -56.3711),
            ("San Juan Nepomuceno", -25.9917, -55.8778),
            ("Yuty", -26.5667, -56.2500),
            ("Abaí", -26.0000, -55.9500),
        ],
    },
    "Misiones": {
        "capital": "San Juan Bautista",
        "distritos": [
            ("San Juan Bautista", -26.6708, -57.1483),
            ("San Ignacio", -26.8667, -57.0333),
            ("Ayolas", -27.4000, -56.9000),
            ("Santiago", -27.0333, -56.8500),
        ],
    },
    "Paraguarí": {
        "capital": "Paraguarí",
        "distritos": [
            ("Paraguarí", -25.6294, -57.1497),
            ("Yaguarón", -25.7833, -57.1500),
            ("Carapeguá", -25.7333, -57.2333),
            ("Quiindy", -25.9667, -57.2500),
            ("Ybycuí", -26.0167, -56.9000),
        ],
    },
    "Ñeembucú": {
        "capital": "Pilar",
        "distritos": [
            ("Pilar", -26.8667, -58.3000),
            ("Alberdi", -26.1667, -58.2167),
            ("Humaitá", -27.0500, -58.5333),
            ("Villa Franca", -26.9000, -58.2833),
        ],
    },
    "Amambay": {
        "capital": "Pedro Juan Caballero",
        "distritos": [
            ("Pedro Juan Caballero", -22.5667, -55.7333),
            ("Bella Vista Norte", -22.1167, -56.5167),
            ("Capitán Bado", -23.2667, -55.5167),
        ],
    },
    "Canindeyú": {
        "capital": "Salto del Guairá",
        "distritos": [
            ("Salto del Guairá", -24.0667, -54.3333),
            ("Curuguaty", -24.5167, -55.7000),
            ("Ygatimí", -24.1000, -55.5333),
            ("Katueté", -24.1000, -54.7167),
        ],
    },
    "Presidente Hayes": {
        "capital": "Villa Hayes",
        "distritos": [
            ("Villa Hayes", -25.0833, -57.5333),
            ("Benjamín Aceval", -24.9667, -57.5667),
            ("Nanawa", -25.2833, -57.6000),
        ],
    },
    "Alto Paraguay": {
        "capital": "Fuerte Olimpo",
        "distritos": [
            ("Fuerte Olimpo", -21.0333, -57.8667),
            ("Bahía Negra", -20.2333, -58.1667),
            ("Puerto Casado", -22.2833, -57.9333),
        ],
    },
    "Boquerón": {
        "capital": "Filadelfia",
        "distritos": [
            ("Filadelfia", -22.3500, -60.0333),
            ("Loma Plata", -22.3833, -59.8333),
            ("Mariscal Estigarribia", -22.0333, -60.6167),
        ],
    },
}


def listar_departamentos() -> list[str]:
    return list(DEPARTAMENTOS.keys())


def listar_distritos(departamento: str) -> list[str]:
    info = DEPARTAMENTOS.get(departamento)
    if not info:
        return []
    return [nombre for nombre, _, _ in info["distritos"]]


def obtener_coordenadas(departamento: str, distrito: str) -> tuple[float, float] | None:
    info = DEPARTAMENTOS.get(departamento)
    if not info:
        return None
    for nombre, lat, lon in info["distritos"]:
        if nombre == distrito:
            return lat, lon
    return None


# ============================================================
# CÓDIGOS DE CLIMA (estándar WMO, usados por Open-Meteo)
# ============================================================
# Cada código se agrupa en una categoría visual/textual simplificada.
def _categoria_desde_codigo(codigo: int) -> str:
    if codigo == 0:
        return "despejado"
    if codigo in (1, 2):
        return "parcial"
    if codigo == 3:
        return "nublado"
    if codigo in (45, 48):
        return "niebla"
    if codigo in (51, 53, 55, 56, 57):
        return "llovizna"
    if codigo in (61, 63, 65, 66, 67, 80, 81, 82):
        return "lluvia"
    if codigo in (71, 73, 75, 77, 85, 86):
        return "nieve"
    if codigo in (95, 96, 99):
        return "tormenta"
    return "nublado"


DESCRIPCIONES = {
    "despejado": "Despejado",
    "parcial": "Parcialmente nublado",
    "nublado": "Nublado",
    "niebla": "Niebla",
    "llovizna": "Llovizna",
    "lluvia": "Lluvia",
    "nieve": "Nieve",
    "tormenta": "Tormenta eléctrica",
}

DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# 16 direcciones de la rosa de los vientos, en español.
_DIRECCIONES_VIENTO = [
    "Norte", "Norte Noreste", "Noreste", "Este Noreste",
    "Este", "Este Sureste", "Sureste", "Sur Sureste",
    "Sur", "Sur Suroeste", "Suroeste", "Oeste Suroeste",
    "Oeste", "Oeste Noroeste", "Noroeste", "Norte Noroeste",
]


def _direccion_viento(grados) -> str:
    if grados is None:
        return ""
    indice = round(grados / 22.5) % 16
    return _DIRECCIONES_VIENTO[indice]


def _descriptor_temperatura(temp: float) -> str:
    if temp >= 33:
        return "Caluroso"
    if temp >= 27:
        return "Cálido"
    if temp >= 18:
        return "Templado"
    if temp >= 10:
        return "Fresco"
    return "Frío"


def _texto_pronostico(temp_ref: float, categoria: str, direccion_viento: str,
                       prob_lluvia: float | None) -> str:
    """Arma una oración corta al estilo 'Fresco, cielo mayormente nublado,
    vientos del sureste. Lluvias dispersas.', combinando temperatura,
    estado del cielo, viento y probabilidad de lluvia."""
    cielo = {
        "despejado": "cielo despejado",
        "parcial": "cielo parcialmente nublado",
        "nublado": "cielo mayormente nublado",
        "niebla": "niebla",
        "llovizna": "cielo cubierto con llovizna",
        "lluvia": "cielo cubierto",
        "nieve": "nevadas",
        "tormenta": "tormentas eléctricas",
    }.get(categoria, "cielo nublado")
    partes = [_descriptor_temperatura(temp_ref)]
    frase = f"{partes[0]}, {cielo}"
    if direccion_viento:
        frase += f", vientos del {direccion_viento.lower()}"
    frase += "."
    if prob_lluvia is not None and prob_lluvia >= 60:
        frase += " Lluvias probables."
    elif prob_lluvia is not None and prob_lluvia >= 25:
        frase += " Lluvias dispersas."
    return frase


def obtener_clima_actual(lat: float, lon: float) -> dict:
    """Compatibilidad hacia atrás: solo el clima actual (sin pronóstico
    extendido). Internamente usa obtener_pronostico_completo."""
    return obtener_pronostico_completo(lat, lon)["actual"]


def obtener_pronostico_completo(lat: float, lon: float) -> dict:
    """Consulta el clima actual, el pronóstico por períodos de hoy
    (Tarde/Noche/Madrugada), el pronóstico de los próximos 5 días, y la
    serie horaria de cada día (para graficar). Lanza una excepción si
    falla la consulta."""
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
        "precipitation,weather_code,wind_speed_10m,wind_direction_10m,surface_pressure"
        "&hourly=temperature_2m,weather_code,precipitation_probability,wind_speed_10m"
        "&daily=weather_code,temperature_2m_max,temperature_2m_min"
        "&forecast_days=6&timezone=America%2FAsuncion"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "MaquedaSystems/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SEGUNDOS) as resp:
        datos = json.loads(resp.read().decode("utf-8"))

    # ── Clima actual ─────────────────────────────────────────
    actual = datos["current"]
    codigo_actual = int(actual["weather_code"])
    categoria_actual = _categoria_desde_codigo(codigo_actual)
    direccion_actual = _direccion_viento(actual.get("wind_direction_10m"))

    resultado_actual = {
        "temperatura": actual["temperature_2m"],
        "sensacion_termica": actual["apparent_temperature"],
        "humedad": actual["relative_humidity_2m"],
        "viento_kmh": actual["wind_speed_10m"],
        "direccion_viento": direccion_actual,
        "presion_hpa": actual.get("surface_pressure"),
        "precipitacion_mm": actual.get("precipitation", 0),
        "categoria": categoria_actual,
        "descripcion": DESCRIPCIONES.get(categoria_actual, "Nublado"),
        "hora_actualizacion": actual["time"],
    }

    # ── Serie horaria completa (para períodos de hoy y el gráfico) ──
    horas = datos["hourly"]["time"]
    temps = datos["hourly"]["temperature_2m"]
    codigos = datos["hourly"]["weather_code"]
    prob_lluvia = datos["hourly"].get("precipitation_probability", [None] * len(horas))

    import datetime as _dt
    fecha_hoy = _dt.date.fromisoformat(actual["time"][:10])
    fecha_manana = fecha_hoy + _dt.timedelta(days=1)

    def _entradas_en_rango(fecha: "_dt.date", hora_desde: int, hora_hasta: int):
        salida = []
        for i, h in enumerate(horas):
            fecha_h = _dt.date.fromisoformat(h[:10])
            hora_h = int(h[11:13])
            if fecha_h == fecha and hora_desde <= hora_h < hora_hasta:
                salida.append((temps[i], codigos[i], prob_lluvia[i]))
        return salida

    def _resumen_periodo(nombre: str, entradas: list):
        if not entradas:
            return {"nombre": nombre, "temp_max": None, "temp_min": None,
                     "categoria": "nublado", "texto": "Sin datos disponibles."}
        t_vals = [e[0] for e in entradas]
        cod_vals = [e[1] for e in entradas]
        prob_vals = [e[2] for e in entradas if e[2] is not None]
        # Código "dominante": el más severo del período (mismo criterio
        # que usa Open-Meteo para el resumen diario).
        codigo_dominante = max(cod_vals, key=lambda c: _SEVERIDAD.get(_categoria_desde_codigo(c), 0))
        categoria = _categoria_desde_codigo(codigo_dominante)
        temp_prom = sum(t_vals) / len(t_vals)
        prob_max = max(prob_vals) if prob_vals else None
        return {
            "nombre": nombre,
            "temp_max": round(max(t_vals)),
            "temp_min": round(min(t_vals)),
            "categoria": categoria,
            "texto": _texto_pronostico(temp_prom, categoria, "", prob_max),
        }

    periodos_hoy = [
        _resumen_periodo("Tarde", _entradas_en_rango(fecha_hoy, 12, 18)),
        _resumen_periodo("Noche", _entradas_en_rango(fecha_hoy, 18, 24)),
        _resumen_periodo("Madrugada", _entradas_en_rango(fecha_manana, 0, 6)),
    ]

    # ── Serie horaria por día, para el gráfico (hora 0 a 23 de cada día) ──
    horas_por_dia: dict[str, list[tuple[int, float]]] = {}
    for i, h in enumerate(horas):
        fecha_h = h[:10]
        hora_h = int(h[11:13])
        horas_por_dia.setdefault(fecha_h, []).append((hora_h, temps[i]))

    # ── Pronóstico de 5 días ──────────────────────────────────
    dias = []
    fechas_diarias = datos["daily"]["time"]
    cod_diarios = datos["daily"]["weather_code"]
    max_diarios = datos["daily"]["temperature_2m_max"]
    min_diarios = datos["daily"]["temperature_2m_min"]
    for i, fecha_str in enumerate(fechas_diarias[:5]):
        fecha_d = _dt.date.fromisoformat(fecha_str)
        categoria_d = _categoria_desde_codigo(int(cod_diarios[i]))
        temp_prom_d = (max_diarios[i] + min_diarios[i]) / 2
        dias.append({
            "fecha": fecha_str,
            "nombre_dia": DIAS_SEMANA[fecha_d.weekday()],
            "dia_mes": fecha_d.day,
            "temp_max": round(max_diarios[i]),
            "temp_min": round(min_diarios[i]),
            "categoria": categoria_d,
            "texto": _texto_pronostico(temp_prom_d, categoria_d, "", None),
        })

    return {
        "actual": resultado_actual,
        "periodos_hoy": periodos_hoy,
        "dias": dias,
        "horas_por_dia": horas_por_dia,
    }


# Orden de severidad usado para elegir el código "dominante" de un
# período/día cuando hay varias condiciones distintas en el mismo tramo.
_SEVERIDAD = {
    "despejado": 0, "parcial": 1, "nublado": 2, "niebla": 3,
    "llovizna": 4, "lluvia": 5, "nieve": 6, "tormenta": 7,
}
