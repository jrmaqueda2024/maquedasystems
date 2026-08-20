"""
models_ia.py
Lógica de negocio del módulo Asistente IA: guardar/leer la configuración
(proveedor, clave de API, modelo) y enviar mensajes a un proveedor de IA
real por su API, sin depender de ningún SDK externo (igual que
ventana_cotizaciones.py, usando solo urllib de la librería estándar).

Proveedores soportados:
  - "openai"       → api.openai.com, formato Chat Completions.
  - "anthropic"    → api.anthropic.com, formato Messages.
  - "personalizado" → cualquier servidor compatible con el formato Chat
                      Completions de OpenAI (DeepSeek, Groq, OpenRouter,
                      Together, un servidor local tipo Ollama/LM Studio,
                      etc.), indicando su URL base.

IMPORTANTE sobre la clave de API: se guarda en texto plano en la base de
datos local (igual que la contraseña de aplicación de Email), porque hace
falta enviarla tal cual en cada pedido a la API. Nunca se envía a nadie
más que al proveedor de IA elegido.
"""
import json
import urllib.request
import urllib.error

from database import conectar

PROVEEDORES = {
    "openai": {
        "etiqueta": "OpenAI (ChatGPT)",
        "modelo_sugerido": "gpt-4o-mini",
        "modelos": ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "o4-mini"],
        "ayuda": (
            "1. Entrá a platform.openai.com y creá una cuenta (o iniciá sesión).\n"
            "2. Cargá crédito en Billing (con tarjeta) — el uso se descuenta de ahí.\n"
            "3. Andá a 'API keys' → 'Create new secret key'.\n"
            "4. Copiá la clave (empieza con 'sk-') y pegala abajo.\n"
            "   Ojo: solo se muestra una vez; si la perdés, generá una nueva."
        ),
    },
    "anthropic": {
        "etiqueta": "Anthropic (Claude)",
        "modelo_sugerido": "claude-haiku-4-5",
        "modelos": ["claude-haiku-4-5", "claude-sonnet-4-5", "claude-opus-4-5"],
        "ayuda": (
            "1. Entrá a console.anthropic.com y creá una cuenta (o iniciá sesión).\n"
            "2. Cargá crédito en 'Billing' (con tarjeta) — el uso se descuenta de ahí.\n"
            "3. Andá a 'API Keys' → 'Create Key'.\n"
            "4. Copiá la clave (empieza con 'sk-ant-') y pegala abajo."
        ),
    },
    "personalizado": {
        "etiqueta": "Otro proveedor compatible (DeepSeek, Groq, OpenRouter, servidor propio, etc.)",
        "modelo_sugerido": "",
        "modelos": [],
        "ayuda": (
            "Para cualquier proveedor que use el mismo formato de API que OpenAI "
            "(la gran mayoría de las alternativas económicas lo usan). Necesitás "
            "3 datos del proveedor elegido: la URL base de su API, tu clave de "
            "API, y el nombre exacto del modelo a usar. Revisá la documentación "
            "de 'API' de ese proveedor para conseguirlos."
        ),
    },
}

TIMEOUT_SEGUNDOS = 45


# ============================================================
# CONFIGURACIÓN
# ============================================================
def obtener_configuracion_ia() -> dict | None:
    """Devuelve la configuración guardada, o None si nunca se configuró
    o si se guardó sin clave de API (equivalente a 'sin configurar')."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT proveedor, api_key, modelo, url_base_personalizada, activo
        FROM configuracion_ia WHERE id = 1
    """)
    fila = cursor.fetchone()
    conn.close()
    if not fila or not fila[1]:
        return None
    return {
        "proveedor": fila[0],
        "api_key": fila[1],
        "modelo": fila[2] or PROVEEDORES.get(fila[0], {}).get("modelo_sugerido", ""),
        "url_base_personalizada": fila[3] or "",
        "activo": bool(fila[4]),
    }


def guardar_configuracion_ia(proveedor: str, api_key: str, modelo: str,
                              url_base_personalizada: str = "") -> tuple[bool, str]:
    if proveedor not in PROVEEDORES:
        return False, "Proveedor inválido."
    if not api_key.strip():
        return False, "La clave de API es obligatoria."
    if proveedor == "personalizado" and not url_base_personalizada.strip():
        return False, "Para un proveedor personalizado hace falta indicar la URL base de su API."
    if not modelo.strip():
        modelo = PROVEEDORES[proveedor]["modelo_sugerido"]
        if not modelo:
            return False, "Indicá el nombre del modelo a usar."

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO configuracion_ia (id, proveedor, api_key, modelo, url_base_personalizada, activo)
        VALUES (1, ?, ?, ?, ?, 1)
        ON CONFLICT(id) DO UPDATE SET
            proveedor = excluded.proveedor,
            api_key = excluded.api_key,
            modelo = excluded.modelo,
            url_base_personalizada = excluded.url_base_personalizada,
            activo = 1
    """, (proveedor, api_key.strip(), modelo.strip(), url_base_personalizada.strip()))
    conn.commit()
    conn.close()
    return True, "Configuración de IA guardada correctamente."


def eliminar_configuracion_ia() -> tuple[bool, str]:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM configuracion_ia WHERE id = 1")
    conn.commit()
    conn.close()
    return True, "Se quitó la configuración de IA."


# ============================================================
# ENVÍO DE MENSAJES A LA IA
# ============================================================
def enviar_mensaje_ia(mensajes: list[dict], config: dict) -> tuple[bool, str]:
    """mensajes: lista de {"role": "system"|"user"|"assistant", "content": str},
    en orden cronológico. Devuelve (ok, texto_respuesta_o_error)."""
    proveedor = config["proveedor"]
    try:
        if proveedor == "anthropic":
            return _enviar_anthropic(mensajes, config)
        else:  # "openai" o "personalizado" (compatible con formato OpenAI)
            return _enviar_openai_compatible(mensajes, config)
    except urllib.error.HTTPError as e:
        cuerpo = ""
        try:
            cuerpo = e.read().decode("utf-8", errors="replace")
            datos = json.loads(cuerpo)
            mensaje_error = (
                datos.get("error", {}).get("message")
                or datos.get("message")
                or cuerpo
            )
        except (ValueError, AttributeError):
            mensaje_error = cuerpo or str(e)
        if e.code == 401:
            mensaje_error = "Clave de API inválida o vencida. Revisá la configuración de IA."
        elif e.code == 429:
            mensaje_error = "Se alcanzó el límite de uso o de crédito del proveedor de IA."
        return False, f"Error del proveedor de IA ({e.code}): {mensaje_error}"
    except urllib.error.URLError as e:
        return False, f"No se pudo conectar con el proveedor de IA. Verificá tu conexión a internet.\n({e.reason})"
    except Exception as e:
        return False, f"Error inesperado al consultar la IA: {e}"


def _enviar_openai_compatible(mensajes: list[dict], config: dict) -> tuple[bool, str]:
    if config["proveedor"] == "openai":
        url = "https://api.openai.com/v1/chat/completions"
    else:
        base = config.get("url_base_personalizada", "").rstrip("/")
        url = f"{base}/chat/completions" if not base.endswith("/chat/completions") else base

    cuerpo = json.dumps({
        "model": config["modelo"],
        "messages": mensajes,
        "temperature": 0.4,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=cuerpo, method="POST", headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['api_key']}",
        "User-Agent": "MaquedaSystems/1.0",
    })
    with urllib.request.urlopen(req, timeout=TIMEOUT_SEGUNDOS) as resp:
        datos = json.loads(resp.read().decode("utf-8"))
    texto = datos["choices"][0]["message"]["content"].strip()
    return True, texto


def _enviar_anthropic(mensajes: list[dict], config: dict) -> tuple[bool, str]:
    # Anthropic separa el mensaje "system" del resto de la conversación.
    system_texto = "\n".join(m["content"] for m in mensajes if m["role"] == "system")
    turnos = [m for m in mensajes if m["role"] != "system"]

    cuerpo = json.dumps({
        "model": config["modelo"],
        "max_tokens": 1500,
        "system": system_texto,
        "messages": turnos,
    }).encode("utf-8")

    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=cuerpo,
                                  method="POST", headers={
        "Content-Type": "application/json",
        "x-api-key": config["api_key"],
        "anthropic-version": "2023-06-01",
        "User-Agent": "MaquedaSystems/1.0",
    })
    with urllib.request.urlopen(req, timeout=TIMEOUT_SEGUNDOS) as resp:
        datos = json.loads(resp.read().decode("utf-8"))
    texto = "".join(bloque.get("text", "") for bloque in datos.get("content", [])).strip()
    return True, texto


def probar_conexion(config: dict) -> tuple[bool, str]:
    """Envía un mensaje mínimo de prueba, usado por el botón 'Probar conexión'
    de la pantalla de configuración."""
    return enviar_mensaje_ia(
        [{"role": "user", "content": "Respondé únicamente con la palabra: OK"}],
        config,
    )
