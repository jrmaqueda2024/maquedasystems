"""
ventana_enviar_email.py
Ventana para enviar el Resumen de Ventas del día por correo: pide el
destinatario, genera el PDF del resumen, y lo envía adjunto junto con un
cuerpo de texto con los totales. Si no hay una cuenta de Gmail configurada
todavía, ofrece abrir la configuración directamente.
"""
import tkinter as tk
from tkinter import messagebox
import tempfile
import os
import datetime

from models_email import obtener_configuracion_email, enviar_correo
from utilidades_ui import ajustar_tamaño_ventana, formatear_gs

AZUL_RIBBON = "#1d5fd6"
GRIS_FONDO = "#f4f5f7"


class VentanaEnviarEmail(tk.Toplevel):
    def __init__(self, parent, fecha: datetime.date, resumen: dict, usuario_actual: dict):
        super().__init__(parent)
        self.fecha = fecha
        self.resumen = resumen
        self.usuario_actual = usuario_actual
        self.ruta_pdf_temporal = None

        self.title("Enviar Resumen por Email")
        self.minsize(420, 400)
        self.configure(bg="white")
        self.grab_set()

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_barra_titulo()

        config = obtener_configuracion_email()
        if config is None:
            self._mostrar_aviso_sin_configurar()
        else:
            self._construir_formulario(config)

        ajustar_tamaño_ventana(self, ancho_min=420, alto_min=400)

    def _construir_barra_titulo(self):
        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text="📧 Enviar Resumen por Email", font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

    def _mostrar_aviso_sin_configurar(self):
        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)

        tk.Label(contenedor, text="Todavía no configuraste una cuenta de correo.",
                 font=("Segoe UI", 11, "bold"), bg="white", wraplength=400).pack(pady=(20, 10))
        tk.Label(contenedor, text="Necesitas configurar tu cuenta de correo (Gmail, Outlook, Yahoo, "
                                  "ProtonMail u otra) una sola vez antes de poder enviar reportes.",
                 font=("Segoe UI", 9), bg="white", fg="#555", wraplength=400, justify="center").pack(pady=(0, 20))

        tk.Button(contenedor, text="⚙ Configurar Email Ahora", font=("Segoe UI", 10, "bold"),
                  bg=AZUL_RIBBON, fg="white", relief="flat", padx=14, pady=8, cursor="hand2",
                  command=self._abrir_configuracion).pack()

    def _abrir_configuracion(self):
        from ventana_configurar_email import VentanaConfigurarEmail
        self.destroy()
        VentanaConfigurarEmail(self.master)

    def _construir_formulario(self, config):
        contenedor = tk.Frame(self, bg="white")
        contenedor.grid(row=1, column=0, sticky="nsew", padx=20, pady=15)

        tk.Label(contenedor, text="Para (destinatario):", font=("Segoe UI", 9, "bold"), bg="white").pack(
            anchor="w", pady=(5, 2))
        self.var_destinatario = tk.StringVar(value=config.get("ultimo_destinatario", ""))
        entry_destinatario = tk.Entry(contenedor, textvariable=self.var_destinatario, font=("Segoe UI", 10), width=40)
        entry_destinatario.pack(anchor="w", fill="x")
        entry_destinatario.focus()

        tk.Label(contenedor, text="Asunto:", font=("Segoe UI", 9, "bold"), bg="white").pack(anchor="w", pady=(12, 2))
        fecha_legible = self.fecha.strftime("%d/%m/%Y")
        self.var_asunto = tk.StringVar(value=f"Resumen de Ventas - {fecha_legible}")
        tk.Entry(contenedor, textvariable=self.var_asunto, font=("Segoe UI", 10), width=40).pack(
            anchor="w", fill="x")

        tk.Label(contenedor, text="Vista previa del mensaje:", font=("Segoe UI", 9, "bold"), bg="white").pack(
            anchor="w", pady=(12, 2))
        cuerpo_texto = self._construir_cuerpo_correo()
        texto_preview = tk.Text(contenedor, font=("Consolas", 8), bg=GRIS_FONDO, height=8, wrap="word")
        texto_preview.insert("1.0", cuerpo_texto)
        texto_preview.config(state="disabled")
        texto_preview.pack(fill="both", expand=True, pady=(0, 4))

        tk.Label(contenedor, text="📎 Se adjuntará el PDF del resumen automáticamente.",
                 font=("Segoe UI", 8), bg="white", fg="#16a34a").pack(anchor="w", pady=(0, 10))

        frame_botones = tk.Frame(contenedor, bg="white")
        frame_botones.pack(fill="x")
        self.boton_enviar = tk.Button(frame_botones, text="✈ Enviar", font=("Segoe UI", 10, "bold"),
                                       bg=AZUL_RIBBON, fg="white", relief="flat", padx=16, pady=8,
                                       cursor="hand2", command=self._enviar)
        self.boton_enviar.pack(side="left")
        tk.Button(frame_botones, text="Cancelar", font=("Segoe UI", 10), bg="white",
                  relief="solid", bd=1, padx=14, pady=8, command=self.destroy).pack(side="left", padx=8)

    def _construir_cuerpo_correo(self) -> str:
        r = self.resumen
        fecha_legible = self.fecha.strftime("%d/%m/%Y")
        return (
            f"Resumen de Ventas del {fecha_legible}\n"
            f"{'-' * 40}\n\n"
            f"Ventas Totales: Gs. {r['ventas_totales']:,.0f}\n\n"
            f"Dinero en Caja:\n"
            f"  Saldo Inicial Caja: Gs. {r['saldo_inicial']:,.0f}\n"
            f"  Ventas en Efectivo: + Gs. {r['ventas_efectivo']:,.0f}\n"
            f"  Entradas: Gs. {r['entradas']:,.0f}\n"
            f"  Salidas: - Gs. {r['salidas']:,.0f}\n"
            f"  Devoluciones: - Gs. {r['devoluciones']:,.0f}\n"
            f"  {'-' * 30}\n"
            f"  Total en Caja: Gs. {r['dinero_en_caja']:,.0f}\n\n"
            f"Se adjunta el detalle completo en PDF.\n\n"
            f"Enviado automáticamente desde el Sistema de Gestión de Ventas."
        )

    def _enviar(self):
        destinatario = self.var_destinatario.get().strip()
        if not destinatario or "@" not in destinatario:
            messagebox.showwarning("Destinatario requerido", "Ingresa un correo de destinatario válido.")
            return

        self.boton_enviar.config(state="disabled", text="Enviando...")
        self.update_idletasks()

        try:
            ruta_pdf = self._generar_pdf_temporal()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF del resumen:\n{e}")
            self.boton_enviar.config(state="normal", text="✈ Enviar")
            return

        ok, msg = enviar_correo(
            destinatario=destinatario,
            asunto=self.var_asunto.get().strip(),
            cuerpo_texto=self._construir_cuerpo_correo(),
            ruta_adjunto=ruta_pdf,
            nombre_adjunto=f"Resumen_Ventas_{self.fecha.isoformat()}.pdf",
        )

        self._limpiar_pdf_temporal()

        if ok:
            messagebox.showinfo("Enviado", msg)
            self.destroy()
        else:
            messagebox.showerror("No se pudo enviar", msg)
            self.boton_enviar.config(state="normal", text="✈ Enviar")

    def _generar_pdf_temporal(self) -> str:
        from reportes_datos import preparar_datos_reporte_ventas
        from reportes_formatos import generar_pdf_simple

        nombre_usuario = self.usuario_actual.get("nombre_completo", "")
        datos = preparar_datos_reporte_ventas(
            self.fecha.isoformat(), self.fecha.isoformat(), generado_por=nombre_usuario,
        )

        carpeta_temporal = tempfile.gettempdir()
        self.ruta_pdf_temporal = os.path.join(carpeta_temporal, f"resumen_ventas_temp_{self.fecha.isoformat()}.pdf")
        generar_pdf_simple(self.ruta_pdf_temporal, datos)
        return self.ruta_pdf_temporal

    def _limpiar_pdf_temporal(self):
        if self.ruta_pdf_temporal and os.path.exists(self.ruta_pdf_temporal):
            try:
                os.remove(self.ruta_pdf_temporal)
            except OSError:
                pass
