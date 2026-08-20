"""
menu_reporte_general.py
Botón + menú desplegable "Reporte General" reutilizable, con las 7
opciones de exportación agrupadas en 3 bloques (PDF, Documentos, Datos).
Se usa tanto en el módulo Inventario como en el Reporte de Ventas por
Rango; cada módulo solo provee la función que prepara los datos
(preparar_datos) y un nombre de archivo base.
"""
import tkinter as tk
from tkinter import messagebox, filedialog
import os
import subprocess
import sys

AZUL_RIBBON = "#1d5fd6"
VERDE_BOTON = "#16a34a"


class BotonReporteGeneral:
    """No es un widget en sí, sino un controlador: crea el botón y el menú,
    y maneja toda la lógica de exportación a los 7 formatos."""

    def __init__(self, parent_frame, obtener_datos_callback, nombre_archivo_base: str):
        """
        obtener_datos_callback: función sin argumentos que devuelve la
            estructura neutral de reportes_datos.py (se llama recién al
            momento de exportar, así los datos siempre están actualizados).
        nombre_archivo_base: ej. "Reporte_Inventario" o "Reporte_Ventas".
        """
        self.obtener_datos = obtener_datos_callback
        self.nombre_archivo_base = nombre_archivo_base

        self.boton = tk.Button(parent_frame, text="📄 Reporte General ▾", font=("Segoe UI", 9, "bold"),
                                bg=VERDE_BOTON, fg="white", cursor="hand2", command=self._mostrar_menu)
        self._construir_menu(parent_frame)

    def pack(self, **kwargs):
        self.boton.pack(**kwargs)
        return self

    def _construir_menu(self, parent_frame):
        self.menu = tk.Menu(parent_frame, tearoff=0)
        self.menu.add_command(label="🟥  PDF (con dashboard)", command=self._exportar_pdf_dashboard)
        self.menu.add_command(label="📄  PDF simple (sin dashboard)", command=self._exportar_pdf_simple)
        self.menu.add_separator()
        self.menu.add_command(label="🟦  Word (.docx)", command=self._exportar_word)
        self.menu.add_command(label="🟩  LibreOffice (.odt)", command=self._exportar_odt)
        self.menu.add_separator()
        self.menu.add_command(label="🟨  Excel (.xlsx con gráficos)", command=self._exportar_excel)
        self.menu.add_command(label="📋  CSV", command=self._exportar_csv)
        self.menu.add_command(label="🗄  JSON (backup)", command=self._exportar_json)

    def _mostrar_menu(self):
        x = self.boton.winfo_rootx()
        y = self.boton.winfo_rooty() + self.boton.winfo_height()
        self.menu.tk_popup(x, y)

    # ---------------- HELPERS COMUNES ----------------
    def _pedir_ruta(self, extension: str, descripcion: str) -> str | None:
        return filedialog.asksaveasfilename(
            title=f"Guardar {descripcion}",
            initialfile=f"{self.nombre_archivo_base}.{extension}",
            defaultextension=f".{extension}",
            filetypes=[(descripcion, f"*.{extension}")],
        )

    def _avisar_falta_libreria(self, paquete: str):
        messagebox.showerror(
            "Falta una librería",
            f"Para generar este formato se necesita instalar '{paquete}'.\n\n"
            f"Abre una terminal (CMD) y ejecuta:\n\npip install {paquete}"
        )

    def _preguntar_y_abrir(self, ruta: str):
        if messagebox.askyesno("Reporte generado", f"El reporte se guardó en:\n{ruta}\n\n¿Quieres abrirlo ahora?"):
            self._abrir_archivo(ruta)

    def _abrir_archivo(self, ruta: str):
        try:
            if sys.platform == "win32":
                os.startfile(ruta)
            elif sys.platform == "darwin":
                subprocess.run(["open", ruta])
            else:
                subprocess.run(["xdg-open", ruta])
        except Exception:
            messagebox.showinfo("Abrir manualmente", f"No se pudo abrir automáticamente. Está en:\n{ruta}", parent=self)

    # ---------------- EXPORTACIONES ----------------
    def _exportar_pdf_dashboard(self):
        """PDF con dashboard = el reporte PDF ya existente con gráfico de
        barras (módulo-específico: Inventario y Ventas tienen generadores
        propios con su gráfico correspondiente)."""
        if self.generador_pdf_dashboard is None:
            messagebox.showinfo("No disponible", "Este reporte no tiene versión con dashboard.", parent=self)
            return
        # Hook opcional: algunos módulos (ej. Reportes, que tiene filtros
        # de Vendedor/Estado/Búsqueda que el dashboard no respeta) pueden
        # pedir una confirmación previa al usuario. Si el hook devuelve
        # False, se cancela la exportación sin mostrar ningún error.
        if self.confirmar_antes_de_dashboard is not None:
            if not self.confirmar_antes_de_dashboard():
                return
        ruta = self._pedir_ruta("pdf", "Archivo PDF")
        if not ruta:
            return
        try:
            self.generador_pdf_dashboard(ruta)
        except ImportError:
            self._avisar_falta_libreria("reportlab")
            return
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n{e}", parent=self)
            return
        self._preguntar_y_abrir(ruta)

    def _exportar_pdf_simple(self):
        ruta = self._pedir_ruta("pdf", "Archivo PDF")
        if not ruta:
            return
        try:
            from reportes_formatos import generar_pdf_simple
            generar_pdf_simple(ruta, self.obtener_datos())
        except ImportError:
            self._avisar_falta_libreria("reportlab")
            return
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n{e}", parent=self)
            return
        self._preguntar_y_abrir(ruta)

    def _exportar_word(self):
        ruta = self._pedir_ruta("docx", "Documento Word")
        if not ruta:
            return
        try:
            from reportes_formatos import generar_word
            generar_word(ruta, self.obtener_datos())
        except ImportError:
            self._avisar_falta_libreria("python-docx")
            return
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el Word:\n{e}", parent=self)
            return
        self._preguntar_y_abrir(ruta)

    def _exportar_odt(self):
        ruta = self._pedir_ruta("odt", "Documento LibreOffice")
        if not ruta:
            return
        try:
            from reportes_formatos import generar_odt
            generar_odt(ruta, self.obtener_datos())
        except ImportError:
            self._avisar_falta_libreria("odfpy")
            return
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el ODT:\n{e}", parent=self)
            return
        self._preguntar_y_abrir(ruta)

    def _exportar_excel(self):
        if self.generador_excel is None:
            messagebox.showinfo("No disponible", "Este reporte no tiene versión Excel todavía.", parent=self)
            return
        ruta = self._pedir_ruta("xlsx", "Archivo Excel")
        if not ruta:
            return
        try:
            self.generador_excel(ruta)
        except ImportError:
            self._avisar_falta_libreria("openpyxl")
            return
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el Excel:\n{e}", parent=self)
            return
        self._preguntar_y_abrir(ruta)

    def _exportar_csv(self):
        ruta = self._pedir_ruta("csv", "Archivo CSV")
        if not ruta:
            return
        try:
            from reportes_formatos import generar_csv
            generar_csv(ruta, self.obtener_datos())
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el CSV:\n{e}", parent=self)
            return
        self._preguntar_y_abrir(ruta)

    def _exportar_json(self):
        ruta = self._pedir_ruta("json", "Archivo JSON")
        if not ruta:
            return
        try:
            from reportes_formatos import generar_json
            generar_json(ruta, self.obtener_datos())
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el JSON:\n{e}", parent=self)
            return
        self._preguntar_y_abrir(ruta)

    # Estos se asignan desde afuera (Inventario/Ventas) tras crear el botón,
    # porque cada módulo tiene su propio generador "con dashboard" y Excel.
    generador_pdf_dashboard = None
    generador_excel = None
    # Hook opcional: confirmación previa antes de exportar el PDF con
    # dashboard, para módulos donde ese formato no respeta todos los
    # filtros activos en pantalla (ver ventana_reportes.py).
    confirmar_antes_de_dashboard = None