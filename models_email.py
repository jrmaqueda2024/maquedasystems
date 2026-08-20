"""
models_email.py
Lógica de negocio para la configuración y el envío de correos por SMTP:
guardar/leer la configuración de la cuenta remitente y enviar un correo
con asunto, cuerpo de texto y un adjunto opcional.

Admite cualquier proveedor de correo, no solo Gmail: Gmail, Outlook/
Hotmail/Live, Yahoo, ProtonMail (a través de ProtonMail Bridge) o
cualquier otro servidor SMTP personalizado.

IMPORTANTE sobre contraseñas: la mayoría de los proveedores grandes
(Gmail, Outlook, Yahoo) ya NO aceptan la contraseña normal de la cuenta
para este tipo de envío por seguridad. Se necesita una "contraseña de
aplicación" generada desde la configuración de seguridad de la cuenta.
Esto se le explica al usuario en la propia pantalla de configuración,
con instrucciones específicas según el proveedor elegido.
"""
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from database import conectar

# Proveedores conocidos con su configuración SMTP típica. 'personalizado'
# permite ingresar cualquier otro servidor (ej. el de una empresa, un
# hosting propio, etc.), para no limitar el sistema a una lista cerrada.
PROVEEDORES = {
    "gmail": {
        "etiqueta": "Gmail / Google Workspace",
        "servidor": "smtp.gmail.com", "puerto": 465, "seguridad": "ssl",
        "ayuda": (
            "Gmail no acepta tu contraseña normal para esto.\n\n"
            "Necesitas una CONTRASEÑA DE APLICACIÓN:\n"
            "1. Activa la Verificación en 2 pasos en tu cuenta de Google.\n"
            "2. Ve a myaccount.google.com → Seguridad → Contraseñas de aplicaciones.\n"
            "3. Genera una y pégala abajo (16 caracteres, con o sin espacios)."
        ),
    },
    "outlook": {
        "etiqueta": "Outlook / Hotmail / Live / Microsoft 365",
        "servidor": "smtp.office365.com", "puerto": 587, "seguridad": "starttls",
        "ayuda": (
            "Con la contraseña normal suele alcanzar si tu cuenta no tiene\n"
            "verificación en 2 pasos. Si la tiene activada, necesitas generar\n"
            "una CONTRASEÑA DE APLICACIÓN desde account.microsoft.com →\n"
            "Seguridad → Opciones de seguridad avanzadas."
        ),
    },
    "yahoo": {
        "etiqueta": "Yahoo Mail",
        "servidor": "smtp.mail.yahoo.com", "puerto": 465, "seguridad": "ssl",
        "ayuda": (
            "Yahoo requiere una CONTRASEÑA DE APLICACIÓN:\n"
            "1. Ingresa a tu cuenta de Yahoo → Seguridad de la cuenta.\n"
            "2. Genera una 'Contraseña de aplicación' y pégala abajo."
        ),
    },
    "protonmail": {
        "etiqueta": "ProtonMail (con Bridge)",
        "servidor": "127.0.0.1", "puerto": 1025, "seguridad": "starttls",
        "ayuda": (
            "ProtonMail no permite SMTP directo por seguridad: necesitas\n"
            "tener instalada y abierta la aplicación 'ProtonMail Bridge'\n"
            "en esta computadora. Ahí vas a encontrar el servidor, puerto\n"
            "y la contraseña específica que Bridge genera para este programa."
        ),
    },
    "personalizado": {
        "etiqueta": "Otro / Servidor SMTP personalizado",
        "servidor": "", "puerto": 587, "seguridad": "starttls",
        "ayuda": (
            "Ingresa el servidor SMTP, puerto y seguridad que te haya\n"
            "indicado tu proveedor de correo o tu departamento de sistemas."
        ),
    },
}


def listar_cuentas_email() -> list[dict]:
    """Todas las cuentas de correo guardadas, la activa primero."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, correo_remitente, contrasena_aplicacion, nombre_remitente,
               proveedor, servidor_smtp, puerto_smtp, seguridad, activa, ultimo_destinatario
        FROM configuracion_email
        ORDER BY activa DESC, id ASC
    """)
    filas = cursor.fetchall()
    conn.close()
    cuentas = []
    for f in filas:
        proveedor = f[4] or "gmail"
        info_proveedor = PROVEEDORES.get(proveedor, PROVEEDORES["personalizado"])
        cuentas.append({
            "id": f[0],
            "correo_remitente": f[1],
            "contrasena_aplicacion": f[2],
            "nombre_remitente": f[3] or "Sistema de Gestión de Ventas",
            "proveedor": proveedor,
            "servidor_smtp": f[5] or info_proveedor["servidor"],
            "puerto_smtp": f[6] or info_proveedor["puerto"],
            "seguridad": f[7] or info_proveedor["seguridad"],
            "activa": bool(f[8]),
            "ultimo_destinatario": f[9] or "",
        })
    return cuentas


def obtener_cuenta_email(cuenta_id: int) -> dict | None:
    for cuenta in listar_cuentas_email():
        if cuenta["id"] == cuenta_id:
            return cuenta
    return None


def obtener_configuracion_email() -> dict | None:
    """Devuelve la cuenta de correo ACTIVA (la que se usa para enviar), o
    None si no hay ninguna cuenta configurada todavía."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, correo_remitente, contrasena_aplicacion, nombre_remitente,
               proveedor, servidor_smtp, puerto_smtp, seguridad, ultimo_destinatario
        FROM configuracion_email WHERE activa = 1 LIMIT 1
    """)
    fila = cursor.fetchone()
    conn.close()
    if fila is None or not fila[1]:
        return None
    proveedor = fila[4] or "gmail"
    info_proveedor = PROVEEDORES.get(proveedor, PROVEEDORES["personalizado"])
    return {
        "id": fila[0],
        "correo_remitente": fila[1],
        "contrasena_aplicacion": fila[2],
        "nombre_remitente": fila[3] or "Sistema de Gestión de Ventas",
        "proveedor": proveedor,
        "servidor_smtp": fila[5] or info_proveedor["servidor"],
        "puerto_smtp": fila[6] or info_proveedor["puerto"],
        "seguridad": fila[7] or info_proveedor["seguridad"],
        "ultimo_destinatario": fila[8] or "",
    }


def _validar_datos_cuenta(correo_remitente: str, contrasena_aplicacion: str,
                           proveedor: str, servidor_smtp, puerto_smtp, seguridad):
    correo_remitente = correo_remitente.strip()
    contrasena_aplicacion = contrasena_aplicacion.strip().replace(" ", "")

    if not correo_remitente or "@" not in correo_remitente:
        return None, "Ingresa un correo válido."
    if not contrasena_aplicacion:
        return None, "Falta la contraseña (o contraseña de aplicación)."

    info_proveedor = PROVEEDORES.get(proveedor, PROVEEDORES["personalizado"])
    servidor_smtp = (servidor_smtp or info_proveedor["servidor"]).strip()
    seguridad = seguridad or info_proveedor["seguridad"]
    if not servidor_smtp:
        return None, "Ingresa el servidor SMTP."
    try:
        puerto_smtp = int(puerto_smtp or info_proveedor["puerto"])
    except (TypeError, ValueError):
        return None, "El puerto SMTP debe ser un número."

    return {
        "correo_remitente": correo_remitente, "contrasena_aplicacion": contrasena_aplicacion,
        "servidor_smtp": servidor_smtp, "puerto_smtp": puerto_smtp, "seguridad": seguridad,
    }, None


def agregar_cuenta_email(correo_remitente: str, contrasena_aplicacion: str,
                          nombre_remitente: str = "Sistema de Gestión de Ventas",
                          proveedor: str = "gmail", servidor_smtp: str = None,
                          puerto_smtp: int = None, seguridad: str = None) -> tuple[bool, str, int | None]:
    """Agrega una cuenta de correo NUEVA (no reemplaza ninguna existente —
    se pueden tener varias guardadas a la vez). La cuenta recién agregada
    queda como la ACTIVA automáticamente, ya que agregarla normalmente
    significa que se la quiere usar a partir de ahora."""
    datos, error = _validar_datos_cuenta(correo_remitente, contrasena_aplicacion,
                                          proveedor, servidor_smtp, puerto_smtp, seguridad)
    if error:
        return False, error, None

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE configuracion_email SET activa = 0")
    cursor.execute("""
        INSERT INTO configuracion_email
            (correo_remitente, contrasena_aplicacion, nombre_remitente,
             proveedor, servidor_smtp, puerto_smtp, seguridad, activa)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
    """, (datos["correo_remitente"], datos["contrasena_aplicacion"], nombre_remitente.strip(),
          proveedor, datos["servidor_smtp"], datos["puerto_smtp"], datos["seguridad"]))
    nuevo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return True, "Cuenta de correo agregada y activada correctamente.", nuevo_id


def editar_cuenta_email(cuenta_id: int, correo_remitente: str, contrasena_aplicacion: str,
                         nombre_remitente: str = "Sistema de Gestión de Ventas",
                         proveedor: str = "gmail", servidor_smtp: str = None,
                         puerto_smtp: int = None, seguridad: str = None) -> tuple[bool, str]:
    """Actualiza los datos de una cuenta ya guardada, sin crear una nueva
    ni cambiar cuál está activa."""
    datos, error = _validar_datos_cuenta(correo_remitente, contrasena_aplicacion,
                                          proveedor, servidor_smtp, puerto_smtp, seguridad)
    if error:
        return False, error

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE configuracion_email
        SET correo_remitente = ?, contrasena_aplicacion = ?, nombre_remitente = ?,
            proveedor = ?, servidor_smtp = ?, puerto_smtp = ?, seguridad = ?
        WHERE id = ?
    """, (datos["correo_remitente"], datos["contrasena_aplicacion"], nombre_remitente.strip(),
          proveedor, datos["servidor_smtp"], datos["puerto_smtp"], datos["seguridad"], cuenta_id))
    conn.commit()
    conn.close()
    return True, "Cuenta de correo actualizada correctamente."


def activar_cuenta_email(cuenta_id: int) -> tuple[bool, str]:
    """Marca una cuenta ya guardada como la activa (la que se usa para
    enviar), desactivando cualquier otra."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, correo_remitente FROM configuracion_email WHERE id = ?", (cuenta_id,))
    fila = cursor.fetchone()
    if not fila:
        conn.close()
        return False, "Esa cuenta ya no existe."
    cursor.execute("UPDATE configuracion_email SET activa = 0")
    cursor.execute("UPDATE configuracion_email SET activa = 1 WHERE id = ?", (cuenta_id,))
    conn.commit()
    conn.close()
    return True, f"Ahora se usa {fila[1]} para enviar correos."


def eliminar_cuenta_email(cuenta_id: int) -> tuple[bool, str]:
    """Desvincula (borra) una cuenta de correo guardada. Si era la activa
    y quedan otras cuentas, activa automáticamente la más reciente de las
    que quedan, para no dejar el sistema sin ninguna cuenta utilizable
    mientras haya alguna disponible."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT activa FROM configuracion_email WHERE id = ?", (cuenta_id,))
    fila = cursor.fetchone()
    if not fila:
        conn.close()
        return False, "Esa cuenta ya no existe."
    era_activa = bool(fila[0])

    cursor.execute("DELETE FROM configuracion_email WHERE id = ?", (cuenta_id,))

    if era_activa:
        cursor.execute("SELECT id FROM configuracion_email ORDER BY id DESC LIMIT 1")
        siguiente = cursor.fetchone()
        if siguiente:
            cursor.execute("UPDATE configuracion_email SET activa = 1 WHERE id = ?", (siguiente[0],))

    conn.commit()
    conn.close()
    return True, "Se desvinculó la cuenta de correo."


def guardar_ultimo_destinatario(correo_destinatario: str):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE configuracion_email SET ultimo_destinatario = ? WHERE activa = 1", (correo_destinatario,))
    conn.commit()
    conn.close()



def enviar_correo(destinatario: str, asunto: str, cuerpo_texto: str,
                   ruta_adjunto: str = None, nombre_adjunto: str = None) -> tuple[bool, str]:
    """Envía un correo vía SMTP usando la configuración guardada (cualquier
    proveedor). Devuelve (exito, mensaje). Errores comunes (credenciales
    inválidas, falta de conexión) se traducen a mensajes claros para el
    usuario, con indicaciones específicas según el proveedor configurado."""
    config = obtener_configuracion_email()
    if config is None:
        return False, (
            "No hay una cuenta de correo configurada todavía. "
            "Ve a 'Configurar Email' para ingresar tu cuenta y la contraseña de aplicación."
        )

    if not destinatario.strip() or "@" not in destinatario:
        return False, "Ingresa un correo de destinatario válido."

    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = formataddr((config["nombre_remitente"], config["correo_remitente"]))
    mensaje["To"] = destinatario.strip()
    mensaje.set_content(cuerpo_texto)

    if ruta_adjunto:
        try:
            with open(ruta_adjunto, "rb") as f:
                datos_adjunto = f.read()
            mensaje.add_attachment(
                datos_adjunto, maintype="application", subtype="pdf",
                filename=nombre_adjunto or "reporte.pdf",
            )
        except FileNotFoundError:
            return False, f"No se encontró el archivo adjunto: {ruta_adjunto}"

    servidor_smtp = config["servidor_smtp"]
    puerto_smtp = config["puerto_smtp"]
    usa_ssl_directo = config["seguridad"] == "ssl"

    try:
        contexto_ssl = ssl.create_default_context()
        if usa_ssl_directo:
            with smtplib.SMTP_SSL(servidor_smtp, puerto_smtp, context=contexto_ssl, timeout=20) as servidor:
                servidor.login(config["correo_remitente"], config["contrasena_aplicacion"])
                servidor.send_message(mensaje)
        else:
            with smtplib.SMTP(servidor_smtp, puerto_smtp, timeout=20) as servidor:
                servidor.starttls(context=contexto_ssl)
                servidor.login(config["correo_remitente"], config["contrasena_aplicacion"])
                servidor.send_message(mensaje)
        guardar_ultimo_destinatario(destinatario.strip())
        return True, f"Correo enviado correctamente a {destinatario.strip()}."
    except smtplib.SMTPAuthenticationError:
        info_proveedor = PROVEEDORES.get(config["proveedor"], PROVEEDORES["personalizado"])
        return False, (
            f"El servidor rechazó las credenciales. Verifica que:\n"
            f"1. El correo esté bien escrito.\n"
            f"2. Estés usando la CONTRASEÑA DE APLICACIÓN correcta (no siempre es la contraseña normal).\n\n"
            f"Ayuda para {info_proveedor['etiqueta']}:\n{info_proveedor['ayuda']}"
        )
    except smtplib.SMTPException as e:
        return False, f"Error al enviar el correo: {e}"
    except OSError as e:
        return False, f"No se pudo conectar al servidor de correo ({servidor_smtp}:{puerto_smtp}).\n" \
                      f"Verifica tu conexión a internet y los datos del servidor.\n({e})"
