"""
ventana_prestamos.py
Módulo Préstamos: una financiera completa dentro del sistema.

Tres pestañas:
  - Banco (Fondo): saldo disponible para prestar, carga de nuevos fondos,
    e historial completo de movimientos (cargas, desembolsos y cobros).
  - Nuevo Préstamo: alta de un préstamo a un cliente, con vista previa
    del cronograma de cuotas antes de desembolsar.
  - Préstamos: listado de préstamos otorgados (activos/pagados/todos),
    con detalle de cuotas, registro de pagos e historial de cada uno.
"""
import datetime
import tkinter as tk
from tkinter import ttk, messagebox

from models_prestamos import (
    SISTEMAS_AMORTIZACION, NOMBRES_SISTEMA, FRECUENCIAS, NOMBRES_FRECUENCIA,
    calcular_cronograma, generar_fechas_cuotas, saldo_fondo, cargar_fondo,
    listar_movimientos_fondo, crear_prestamo, listar_prestamos,
    obtener_detalle_prestamo, registrar_pago_cuota, resumen_financiero,
)
from models_clientes import listar_clientes
from utilidades_ui import forzar_mayusculas, ajustar_tamaño_ventana, formatear_gs, habilitar_deseleccion_treeview
from traducciones import t
from widget_calendario import abrir_selector_fecha

AZUL_RIBBON = "#1d5fd6"
AZUL_OSC    = "#163d8c"
GRIS_FONDO  = "#f4f5f7"
GRIS_BORDE  = "#e2e8f0"
BLANCO      = "#ffffff"
VERDE       = "#16a34a"
ROJO        = "#dc2626"
NARANJA     = "#d97706"
NEGRO       = "#1e293b"
GRIS_TEXTO  = "#6b7280"


def _formatear_fecha(fecha) -> str:
    if not fecha:
        return "—"
    if isinstance(fecha, datetime.date):
        return fecha.strftime("%d/%m/%Y")
    try:
        return datetime.date.fromisoformat(str(fecha)[:10]).strftime("%d/%m/%Y")
    except ValueError:
        return str(fecha)


def _texto_a_monto(texto: str) -> float:
    texto = (texto or "").strip().replace("Gs.", "").replace(".", "").replace(",", ".")
    return float(texto) if texto else 0.0


# ============================================================
# Diálogo: Cargar Fondos al Banco Central
# ============================================================
class VentanaCargarFondos(tk.Toplevel):
    def __init__(self, parent, usuario_actual, on_guardado=None):
        super().__init__(parent)
        self.usuario_actual = usuario_actual
        self.on_guardado = on_guardado

        self.title("Cargar Fondos")
        self.minsize(340, 300)
        self.configure(bg=BLANCO)
        self.grab_set()

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text="🏦 Cargar Fondos al Banco Central", font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

        contenedor = tk.Frame(self, bg=BLANCO)
        contenedor.grid(row=1, column=0, sticky="nsew", padx=20, pady=15)

        tk.Label(contenedor, text=f"Saldo actual disponible: {formatear_gs(saldo_fondo())}",
                 font=("Segoe UI", 9), bg=BLANCO, fg=GRIS_TEXTO).pack(anchor="w", pady=(0, 12))

        tk.Label(contenedor, text="Monto a cargar (Gs.):", font=("Segoe UI", 9, "bold"),
                 bg=BLANCO).pack(anchor="w", pady=(0, 2))
        self.var_monto = tk.StringVar()
        entry_monto = tk.Entry(contenedor, textvariable=self.var_monto, font=("Segoe UI", 11))
        entry_monto.pack(fill="x")
        entry_monto.focus()

        tk.Label(contenedor, text="Descripción:", font=("Segoe UI", 9, "bold"),
                 bg=BLANCO).pack(anchor="w", pady=(14, 2))
        self.var_descripcion = tk.StringVar(value="Carga de capital")
        entry_desc = tk.Entry(contenedor, textvariable=self.var_descripcion, font=("Segoe UI", 10))
        entry_desc.pack(fill="x")
        forzar_mayusculas(entry_desc, self.var_descripcion)

        frame_botones = tk.Frame(contenedor, bg=BLANCO)
        frame_botones.pack(fill="x", pady=(25, 0))
        tk.Button(frame_botones, text="✔ Cargar", font=("Segoe UI", 10, "bold"), bg=BLANCO,
                  fg=VERDE, relief="solid", bd=1, padx=14, pady=8, cursor="hand2",
                  command=self._aceptar).pack(side="left", padx=(0, 8))
        tk.Button(frame_botones, text="✕ Cancelar", font=("Segoe UI", 10, "bold"), bg=BLANCO,
                  fg=ROJO, relief="solid", bd=1, padx=14, pady=8, cursor="hand2",
                  command=self.destroy).pack(side="left")

        entry_monto.bind("<Return>", lambda e: self._aceptar())
        entry_desc.bind("<Return>", lambda e: self._aceptar())
        ajustar_tamaño_ventana(self, ancho_min=340, alto_min=300)

    def _aceptar(self):
        try:
            monto = _texto_a_monto(self.var_monto.get())
        except ValueError:
            messagebox.showerror("Monto inválido", "Ingresa un monto numérico válido.", parent=self)
            return
        ok, msg = cargar_fondo(monto, self.var_descripcion.get(), self.usuario_actual["id"])
        if ok:
            messagebox.showinfo("Fondo actualizado", msg, parent=self)
            if self.on_guardado:
                self.on_guardado()
            self.destroy()
        else:
            messagebox.showerror("No se pudo cargar", msg, parent=self)


# ============================================================
# Diálogo: seleccionar cliente para el préstamo
# ============================================================
class VentanaSeleccionarClientePrestamo(tk.Toplevel):
    def __init__(self, parent, on_seleccionado):
        super().__init__(parent)
        self.on_seleccionado = on_seleccionado
        self.title("Seleccionar Cliente")
        self.geometry("600x420")
        self.minsize(460, 340)
        self.configure(bg=BLANCO)
        self.grab_set()

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text="Seleccionar Cliente", font=("Segoe UI", 11, "bold"),
                 bg=AZUL_RIBBON, fg="white").pack(side="left", padx=15, pady=6)

        frame_busqueda = tk.Frame(self, bg=BLANCO)
        frame_busqueda.grid(row=1, column=0, sticky="ew", padx=10, pady=8)
        tk.Label(frame_busqueda, text="Buscar:", font=("Segoe UI", 9), bg=BLANCO).pack(side="left")
        self.var_busqueda = tk.StringVar()
        entry = tk.Entry(frame_busqueda, textvariable=self.var_busqueda, font=("Segoe UI", 10), width=30)
        entry.pack(side="left", padx=8, fill="x", expand=True)
        entry.bind("<KeyRelease>", lambda e: self._buscar())
        entry.focus()
        tk.Button(frame_busqueda, text="＋ Cliente Nuevo", font=("Segoe UI", 9), bg=BLANCO,
                  relief="solid", bd=1, command=self._abrir_alta_rapida).pack(side="right")

        contenedor = tk.Frame(self, bg=BLANCO)
        contenedor.grid(row=2, column=0, sticky="nsew", padx=10)
        columnas = ("id", "nombre", "documento", "telefono")
        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc, w in zip(columnas, ("CÓDIGO", "NOMBRE", "N° DOCUMENTO", "TELÉFONO"),
                                (70, 220, 140, 120)):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=w, anchor="center" if col != "nombre" else "w")
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        scrollbar_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=scrollbar.set, xscrollcommand=scrollbar_h.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        scrollbar_h.grid(row=1, column=0, sticky="ew")
        self.tabla.bind("<Double-1>", lambda e: self._confirmar())

        frame_botones = tk.Frame(self, bg=BLANCO, height=46)
        frame_botones.grid(row=3, column=0, sticky="ew", pady=6)
        tk.Button(frame_botones, text="Seleccionar", font=("Segoe UI", 9, "bold"), bg=BLANCO,
                  relief="solid", bd=1, command=self._confirmar).pack()

        self.clientes_por_id = {}
        self._buscar()

    def _buscar(self):
        for f in self.tabla.get_children():
            self.tabla.delete(f)
        self.clientes_por_id = {}
        for c in listar_clientes(texto_busqueda=self.var_busqueda.get()):
            self.tabla.insert("", "end", iid=str(c["id"]),
                               values=(c["id"], c["nombre"], c["nro_documento"], c["telefono"]))
            self.clientes_por_id[str(c["id"])] = c

    def _confirmar(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Selecciona un cliente", "Elige un cliente de la lista.", parent=self)
            return
        cliente = self.clientes_por_id[seleccion[0]]
        self.destroy()
        self.on_seleccionado(cliente)

    def _abrir_alta_rapida(self):
        from ventana_clientes import VentanaFormularioCliente
        VentanaFormularioCliente(self, cliente=None, on_guardado=self._buscar)


# ============================================================
# Diálogo: registrar pago de una cuota
# ============================================================
class VentanaRegistrarPago(tk.Toplevel):
    def __init__(self, parent, cuota: dict, usuario_actual, on_guardado=None):
        super().__init__(parent)
        self.cuota = cuota
        self.usuario_actual = usuario_actual
        self.on_guardado = on_guardado

        self.title(f"Registrar Pago — Cuota Nro. {cuota['nro_cuota']}")
        self.minsize(380, 420)
        self.configure(bg=BLANCO)
        self.grab_set()

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        barra = tk.Frame(self, bg=AZUL_RIBBON, height=34)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(barra, text=f"Registrar Pago — Cuota Nro. {cuota['nro_cuota']}",
                 font=("Segoe UI", 11, "bold"), bg=AZUL_RIBBON, fg="white").pack(
            side="left", padx=15, pady=6)

        cont = tk.Frame(self, bg=BLANCO)
        cont.grid(row=1, column=0, sticky="nsew", padx=20, pady=15)

        filas_info = [
            ("Vencimiento:", _formatear_fecha(cuota["fecha_venc"])),
            ("Capital + Interés pendiente:", formatear_gs(cuota["saldo_capital_interes"])),
            ("Días de atraso:", str(cuota["dias_atraso"])),
            ("Mora acumulada:", formatear_gs(cuota["mora_pendiente"])),
        ]
        for etiqueta, valor in filas_info:
            fila = tk.Frame(cont, bg=BLANCO)
            fila.pack(fill="x", pady=2)
            tk.Label(fila, text=etiqueta, font=("Segoe UI", 9), bg=BLANCO,
                     fg=GRIS_TEXTO).pack(side="left")
            color = ROJO if etiqueta.startswith("Mora") and cuota["mora_pendiente"] > 0 else NEGRO
            tk.Label(fila, text=valor, font=("Segoe UI", 9, "bold"), bg=BLANCO,
                     fg=color).pack(side="right")

        tk.Frame(cont, bg=GRIS_BORDE, height=1).pack(fill="x", pady=10)

        fila_total = tk.Frame(cont, bg=BLANCO)
        fila_total.pack(fill="x", pady=(0, 14))
        tk.Label(fila_total, text="TOTAL A PAGAR:", font=("Segoe UI", 11, "bold"),
                 bg=BLANCO).pack(side="left")
        tk.Label(fila_total, text=formatear_gs(cuota["total_a_pagar"]), font=("Segoe UI", 14, "bold"),
                 bg=BLANCO, fg=AZUL_RIBBON).pack(side="right")

        tk.Label(cont, text="Monto a pagar (Gs.):", font=("Segoe UI", 9, "bold"),
                 bg=BLANCO).pack(anchor="w", pady=(0, 2))
        self.var_monto = tk.StringVar(value=f"{cuota['total_a_pagar']:.0f}")
        entry_monto = tk.Entry(cont, textvariable=self.var_monto, font=("Segoe UI", 12))
        entry_monto.pack(fill="x")
        entry_monto.focus()
        entry_monto.select_range(0, "end")
        tk.Label(cont, text="(Podés ingresar un monto menor para hacer un pago parcial)",
                 font=("Segoe UI", 8, "italic"), bg=BLANCO, fg=GRIS_TEXTO).pack(anchor="w", pady=(2, 0))

        frame_botones = tk.Frame(cont, bg=BLANCO)
        frame_botones.pack(fill="x", pady=(20, 0))
        tk.Button(frame_botones, text="✔ Registrar Pago", font=("Segoe UI", 10, "bold"), bg=BLANCO,
                  fg=VERDE, relief="solid", bd=1, padx=14, pady=8, cursor="hand2",
                  command=self._aceptar).pack(side="left", padx=(0, 8))
        tk.Button(frame_botones, text="✕ Cancelar", font=("Segoe UI", 10, "bold"), bg=BLANCO,
                  fg=ROJO, relief="solid", bd=1, padx=14, pady=8, cursor="hand2",
                  command=self.destroy).pack(side="left")

        entry_monto.bind("<Return>", lambda e: self._aceptar())
        ajustar_tamaño_ventana(self, ancho_min=380, alto_min=420)

    def _aceptar(self):
        try:
            monto = _texto_a_monto(self.var_monto.get())
        except ValueError:
            messagebox.showerror("Monto inválido", "Ingresa un monto numérico válido.", parent=self)
            return
        ok, msg = registrar_pago_cuota(self.cuota["id"], monto, self.usuario_actual["id"])
        if ok:
            messagebox.showinfo("Pago registrado", msg, parent=self)
            if self.on_guardado:
                self.on_guardado()
            self.destroy()
        else:
            messagebox.showerror("No se pudo registrar el pago", msg, parent=self)


# ============================================================
# Ventana: Detalle de un préstamo (cronograma + pagos)
# ============================================================
class VentanaDetallePrestamo(tk.Toplevel):
    def __init__(self, parent, prestamo_id: int, usuario_actual, on_cambio=None):
        super().__init__(parent)
        self.prestamo_id = prestamo_id
        self.usuario_actual = usuario_actual
        self.on_cambio = on_cambio

        self.title(f"Préstamo Nro. {prestamo_id}")
        self.geometry("880x620")
        self.minsize(720, 500)
        self.configure(bg=BLANCO)

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_encabezado()
        self._construir_tabla_cuotas()
        self._construir_historial_pagos()
        self._cargar()

    def _construir_encabezado(self):
        self.barra = tk.Frame(self, bg=AZUL_RIBBON, height=64)
        self.barra.grid(row=0, column=0, sticky="ew")
        self.barra.grid_propagate(False)
        self.lbl_titulo = tk.Label(self.barra, font=("Segoe UI", 13, "bold"),
                                    bg=AZUL_RIBBON, fg="white", justify="left", anchor="w")
        self.lbl_titulo.pack(side="left", padx=15, pady=8, fill="both", expand=True)

        self.frame_info = tk.Frame(self, bg=GRIS_FONDO)
        self.frame_info.grid(row=1, column=0, sticky="ew")
        self.lbl_info = tk.Label(self.frame_info, font=("Segoe UI", 9), bg=GRIS_FONDO,
                                  fg=GRIS_TEXTO, justify="left", anchor="w", wraplength=860)
        self.lbl_info.pack(side="top", anchor="w", padx=15, pady=(8, 0))
        self.lbl_saldo = tk.Label(self.frame_info, font=("Segoe UI", 11, "bold"),
                                   bg=GRIS_FONDO, fg=AZUL_RIBBON)
        self.lbl_saldo.pack(side="top", anchor="w", padx=15, pady=(2, 8))

    def _construir_tabla_cuotas(self):
        contenedor = tk.Frame(self, bg=BLANCO)
        contenedor.grid(row=2, column=0, sticky="nsew", padx=10, pady=(10, 4))
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        columnas = ("nro", "vencimiento", "capital", "interes", "mora", "total", "estado")
        encabezados = ("CUOTA", "VENCIMIENTO", "CAPITAL", "INTERÉS", "MORA", "TOTAL A PAGAR", "ESTADO")
        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        habilitar_deseleccion_treeview(self.tabla)
        for col, enc in zip(columnas, encabezados):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=110, anchor="center")
        self.tabla.column("vencimiento", width=100)
        self.tabla.column("estado", width=90)

        self.tabla.tag_configure("vencida", background="#fde8e8", foreground=ROJO)
        self.tabla.tag_configure("pagada", background="#e8f7ee", foreground=VERDE)
        self.tabla.tag_configure("pendiente", background=BLANCO)

        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scrollbar.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        scrollbar_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(xscrollcommand=scrollbar_h.set)
        scrollbar_h.grid(row=1, column=0, sticky="ew")

        self.tabla.bind("<Double-1>", lambda e: self._pagar_seleccionada())

        frame_botones = tk.Frame(self, bg=BLANCO)
        frame_botones.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 6))
        tk.Button(frame_botones, text="💵 Registrar Pago de la cuota seleccionada",
                  font=("Segoe UI", 9, "bold"), bg=BLANCO, fg=VERDE, relief="solid", bd=1,
                  padx=10, pady=6, cursor="hand2", command=self._pagar_seleccionada
                  ).pack(side="left")
        tk.Button(frame_botones, text="📄 Exportar Extracto PDF",
                  font=("Segoe UI", 9, "bold"), bg=BLANCO, fg=AZUL_RIBBON, relief="solid", bd=1,
                  padx=10, pady=6, cursor="hand2", command=self._exportar_pdf
                  ).pack(side="left", padx=(8, 0))

    def _construir_historial_pagos(self):
        tk.Label(self, text="Historial de Pagos", font=("Segoe UI", 10, "bold"),
                 bg=BLANCO, fg=NEGRO).grid(row=4, column=0, sticky="w", padx=12, pady=(6, 0))
        contenedor = tk.Frame(self, bg=BLANCO)
        contenedor.grid(row=5, column=0, sticky="nsew", padx=10, pady=(2, 10))
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        columnas = ("fecha", "capital", "interes", "mora", "total")
        encabezados = ("FECHA", "CAPITAL", "INTERÉS", "MORA", "TOTAL PAGADO")
        self.tabla_pagos = ttk.Treeview(contenedor, columns=columnas, show="headings", height=5)
        habilitar_deseleccion_treeview(self.tabla_pagos)
        for col, enc in zip(columnas, encabezados):
            self.tabla_pagos.heading(col, text=enc)
            self.tabla_pagos.column(col, width=120, anchor="center")
        sb_pagos = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla_pagos.yview)
        sb_pagos_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla_pagos.xview)
        self.tabla_pagos.configure(yscrollcommand=sb_pagos.set, xscrollcommand=sb_pagos_h.set)
        self.tabla_pagos.grid(row=0, column=0, sticky="nsew")
        sb_pagos.grid(row=0, column=1, sticky="ns")
        sb_pagos_h.grid(row=1, column=0, sticky="ew")

    def _cargar(self):
        detalle = obtener_detalle_prestamo(self.prestamo_id)
        if detalle is None:
            messagebox.showerror("Error", "El préstamo no existe.", parent=self)
            self.destroy()
            return
        self._detalle = detalle

        self.lbl_titulo.config(
            text=f"Préstamo Nro. {detalle['id']}  —  {detalle['cliente']}\n"
                 f"{NOMBRES_SISTEMA.get(detalle['sistema'], detalle['sistema'])}")
        self.lbl_info.config(
            text=f"Capital: {formatear_gs(detalle['capital'])}   |   "
                 f"Tasa: {detalle['tasa_interes']}% {NOMBRES_FRECUENCIA.get(detalle['frecuencia'], '')}   |   "
                 f"Mora diaria: {detalle['tasa_mora_diaria']}%   |   "
                 f"Desembolsado: {_formatear_fecha(detalle['fecha_desembolso'])}   |   "
                 f"Estado: {detalle['estado'].capitalize()}")
        self.lbl_saldo.config(text=f"Saldo pendiente: {formatear_gs(detalle['saldo_total'])}")

        for f in self.tabla.get_children():
            self.tabla.delete(f)
        self._cuotas_por_fila = {}
        for c in detalle["cuotas"]:
            tag = {"Vencida": "vencida", "Pagada": "pagada", "Pendiente": "pendiente"}[c["estado"]]
            iid = str(c["id"])
            self.tabla.insert("", "end", iid=iid, tags=(tag,), values=(
                c["nro_cuota"], _formatear_fecha(c["fecha_venc"]), formatear_gs(c["capital"]),
                formatear_gs(c["interes"]), formatear_gs(c["mora_pendiente"]),
                formatear_gs(c["total_a_pagar"]), c["estado"],
            ))
            self._cuotas_por_fila[iid] = c

        for f in self.tabla_pagos.get_children():
            self.tabla_pagos.delete(f)
        for p in detalle["pagos"]:
            self.tabla_pagos.insert("", "end", values=(
                _formatear_fecha(p["fecha"]), formatear_gs(p["capital"]),
                formatear_gs(p["interes"]), formatear_gs(p["mora"]), formatear_gs(p["total"]),
            ))

        if self.on_cambio:
            self.on_cambio()

    def _exportar_pdf(self):
        from tkinter import filedialog
        try:
            from reporte_prestamo_pdf import generar_extracto_prestamo_pdf
        except ImportError:
            messagebox.showerror("Falta una librería",
                                 "Para generar el PDF se necesita instalar 'reportlab'.\n\n"
                                 "Abre una terminal y ejecutá:\n\npip install reportlab",
                                 parent=self)
            return
        nombre_cliente = self._detalle["cliente"].replace(" ", "_")
        ruta = filedialog.asksaveasfilename(
            title="Guardar Extracto del Préstamo",
            initialfile=f"extracto_prestamo_{self.prestamo_id}_{nombre_cliente}.pdf",
            defaultextension=".pdf", filetypes=[("Archivo PDF", "*.pdf")],
        )
        if not ruta:
            return
        try:
            generar_extracto_prestamo_pdf(ruta, self._detalle)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n{e}", parent=self)
            return
        if messagebox.askyesno("PDF generado", f"El extracto se guardó en:\n{ruta}\n\n"
                                               "¿Querés abrirlo ahora?", parent=self):
            import os, sys, subprocess
            try:
                if sys.platform == "win32":
                    os.startfile(ruta)
                elif sys.platform == "darwin":
                    subprocess.run(["open", ruta])
                else:
                    subprocess.run(["xdg-open", ruta])
            except Exception:
                pass

    def _pagar_seleccionada(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Selecciona una cuota", "Elige una cuota de la lista para pagar.",
                                    parent=self)
            return
        cuota = self._cuotas_por_fila[seleccion[0]]
        if cuota["estado"] == "Pagada":
            messagebox.showinfo("Cuota ya pagada", "Esta cuota ya está saldada.", parent=self)
            return
        VentanaRegistrarPago(self, cuota, self.usuario_actual, on_guardado=self._cargar)


# ============================================================
# PANEL PRINCIPAL
# ============================================================
class PanelPrestamos(tk.Frame):
    def __init__(self, parent, usuario_actual):
        super().__init__(parent, bg=BLANCO)
        self.usuario_actual = usuario_actual

        enc = tk.Frame(self, bg=AZUL_RIBBON, height=54)
        enc.pack(fill="x")
        enc.pack_propagate(False)
        tk.Label(enc, text=t("prestamos_titulo"), font=("Segoe UI", 15, "bold"),
                 bg=AZUL_RIBBON, fg=BLANCO).pack(side="left", padx=20, pady=12)

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=8, pady=6)

        self.tab_fondo = tk.Frame(self.nb, bg=BLANCO)
        self.tab_nuevo = tk.Frame(self.nb, bg=BLANCO)
        self.tab_lista = tk.Frame(self.nb, bg=BLANCO)

        self.nb.add(self.tab_fondo, text=t("prestamos_tab_fondo"))
        self.nb.add(self.tab_nuevo, text=t("prestamos_tab_nuevo"))
        self.nb.add(self.tab_lista, text=t("prestamos_tab_lista"))

        self._construir_tab_fondo()
        self._construir_tab_nuevo()
        self._construir_tab_lista()

        self.nb.bind("<<NotebookTabChanged>>", lambda e: self._al_cambiar_tab())

    def _al_cambiar_tab(self):
        indice = self.nb.index(self.nb.select())
        if indice == 0:
            self._cargar_fondo()
        elif indice == 2:
            self._cargar_lista()

    # ──────────────────────── TAB: FONDO ────────────────────────
    def _construir_tab_fondo(self):
        marco = self.tab_fondo
        cabecera = tk.Frame(marco, bg=BLANCO)
        cabecera.pack(fill="x", padx=14, pady=(14, 6))

        tarjeta = tk.Frame(cabecera, bg="#eef2ff", bd=0)
        tarjeta.pack(side="left", fill="y")
        tk.Label(tarjeta, text=t("prestamos_saldo_disponible"), font=("Segoe UI", 9, "bold"),
                 bg="#eef2ff", fg=AZUL_RIBBON).pack(anchor="w", padx=16, pady=(10, 0))
        self.lbl_saldo_fondo = tk.Label(tarjeta, font=("Segoe UI", 22, "bold"),
                                          bg="#eef2ff", fg=NEGRO)
        self.lbl_saldo_fondo.pack(anchor="w", padx=16, pady=(0, 10))

        tk.Button(cabecera, text=t("prestamos_cargar_fondos"), font=("Segoe UI", 10, "bold"),
                  bg=BLANCO, fg=VERDE, relief="solid", bd=1, padx=14, pady=10,
                  cursor="hand2", command=self._abrir_cargar_fondos).pack(side="left", padx=20)

        marco_resumen = tk.Frame(cabecera, bg=BLANCO)
        marco_resumen.pack(side="right", fill="y")
        self.lbl_resumen = tk.Label(marco_resumen, font=("Segoe UI", 9), bg=BLANCO,
                                     fg=GRIS_TEXTO, justify="right")
        self.lbl_resumen.pack(anchor="e")

        tk.Label(marco, text=t("prestamos_historial_fondo"), font=("Segoe UI", 10, "bold"),
                 bg=BLANCO, fg=NEGRO).pack(anchor="w", padx=14, pady=(10, 2))

        frame_busqueda = tk.Frame(marco, bg=BLANCO)
        frame_busqueda.pack(fill="x", padx=14)
        self.var_busqueda_fondo = tk.StringVar()
        entry = tk.Entry(frame_busqueda, textvariable=self.var_busqueda_fondo, font=("Segoe UI", 9))
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<KeyRelease>", lambda e: self._cargar_fondo())
        tk.Label(frame_busqueda, text="🔎", bg=BLANCO).pack(side="left", padx=(6, 0))

        contenedor = tk.Frame(marco, bg=BLANCO)
        contenedor.pack(fill="both", expand=True, padx=14, pady=8)
        columnas = ("fecha", "tipo", "descripcion", "monto", "saldo")
        encabezados = ("FECHA", "TIPO", "DESCRIPCIÓN", "MONTO", "SALDO RESULTANTE")
        self.tabla_fondo = ttk.Treeview(contenedor, columns=columnas, show="headings")
        habilitar_deseleccion_treeview(self.tabla_fondo)
        for col, enc, w in zip(columnas, encabezados, (140, 100, 320, 130, 150)):
            self.tabla_fondo.heading(col, text=enc)
            self.tabla_fondo.column(col, width=w,
                                     anchor="w" if col == "descripcion" else "center")
        self.tabla_fondo.tag_configure("carga", foreground=VERDE)
        self.tabla_fondo.tag_configure("cobro", foreground=VERDE)
        self.tabla_fondo.tag_configure("desembolso", foreground=AZUL_RIBBON)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla_fondo.yview)
        scrollbar_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla_fondo.xview)
        self.tabla_fondo.configure(yscrollcommand=scrollbar.set, xscrollcommand=scrollbar_h.set)
        self.tabla_fondo.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        scrollbar_h.grid(row=1, column=0, sticky="ew")

        self._cargar_fondo()

    def _cargar_fondo(self):
        saldo = saldo_fondo()
        self.lbl_saldo_fondo.config(text=formatear_gs(saldo))

        r = resumen_financiero()
        self.lbl_resumen.config(
            text=f"Préstamos activos: {r['cantidad_prestamos_activos']}\n"
                 f"Prestado (activo): {formatear_gs(r['total_prestado_activo'])}\n"
                 f"Por cobrar: {formatear_gs(r['total_por_cobrar'])}   |   "
                 f"Cartera vencida: {formatear_gs(r['cartera_vencida'])}")

        for f in self.tabla_fondo.get_children():
            self.tabla_fondo.delete(f)
        etiquetas_tipo = {"carga": "Carga", "desembolso": "Desembolso", "cobro": "Cobro", "ajuste": "Ajuste"}
        for m in listar_movimientos_fondo(texto_busqueda=self.var_busqueda_fondo.get()):
            desc = m["descripcion"]
            if m["cliente"]:
                desc = f"{desc} ({m['cliente']})"
            self.tabla_fondo.insert("", "end", tags=(m["tipo"],), values=(
                _formatear_fecha(m["fecha"]), etiquetas_tipo.get(m["tipo"], m["tipo"]),
                desc, formatear_gs(m["monto"]), formatear_gs(m["saldo_resultante"]),
            ))

    def _abrir_cargar_fondos(self):
        VentanaCargarFondos(self, self.usuario_actual, on_guardado=self._cargar_fondo)

    # ──────────────────────── TAB: NUEVO PRÉSTAMO ────────────────────────
    def _construir_tab_nuevo(self):
        marco = self.tab_nuevo
        self._cliente_seleccionado = None

        contenedor = tk.Frame(marco, bg=BLANCO)
        contenedor.pack(fill="both", expand=True, padx=16, pady=14)
        contenedor.grid_columnconfigure(0, weight=1)
        contenedor.grid_columnconfigure(1, weight=1)

        # --- Cliente ---
        tk.Label(contenedor, text="Cliente:", font=("Segoe UI", 9, "bold"), bg=BLANCO).grid(
            row=0, column=0, columnspan=2, sticky="w")
        frame_cliente = tk.Frame(contenedor, bg=BLANCO)
        frame_cliente.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 12))
        self.lbl_cliente = tk.Label(frame_cliente, text="Ningún cliente seleccionado",
                                     font=("Segoe UI", 10), bg=GRIS_FONDO, fg=GRIS_TEXTO,
                                     anchor="w", padx=10, pady=8)
        self.lbl_cliente.pack(side="left", fill="x", expand=True)
        tk.Button(frame_cliente, text="Buscar Cliente...", font=("Segoe UI", 9), bg=BLANCO,
                  relief="solid", bd=1, command=self._elegir_cliente).pack(side="left", padx=(8, 0))

        def _campo(fila, col, etiqueta):
            tk.Label(contenedor, text=etiqueta, font=("Segoe UI", 9, "bold"), bg=BLANCO).grid(
                row=fila, column=col, sticky="w", pady=(0, 2))

        _campo(2, 0, "Capital a prestar (Gs.):")
        self.var_capital = tk.StringVar()
        tk.Entry(contenedor, textvariable=self.var_capital, font=("Segoe UI", 11)).grid(
            row=3, column=0, sticky="ew", padx=(0, 8), pady=(0, 12))

        _campo(2, 1, "Tasa de interés (% por período):")
        self.var_tasa = tk.StringVar(value="5")
        tk.Entry(contenedor, textvariable=self.var_tasa, font=("Segoe UI", 11)).grid(
            row=3, column=1, sticky="ew", pady=(0, 12))

        _campo(4, 0, "Frecuencia de pago:")
        combo_frec = ttk.Combobox(contenedor, state="readonly",
                                   values=[v for _, v in FRECUENCIAS])
        combo_frec.grid(row=5, column=0, sticky="ew", padx=(0, 8), pady=(0, 12))
        combo_frec.set(NOMBRES_FRECUENCIA["mensual"])
        self._combo_frec = combo_frec

        _campo(4, 1, "Cantidad de cuotas:")
        self.var_cuotas = tk.StringVar(value="12")
        tk.Entry(contenedor, textvariable=self.var_cuotas, font=("Segoe UI", 11)).grid(
            row=5, column=1, sticky="ew", pady=(0, 12))

        _campo(6, 0, "Sistema de amortización:")
        combo_sist = ttk.Combobox(contenedor, state="readonly",
                                   values=[v for _, v in SISTEMAS_AMORTIZACION])
        combo_sist.set(NOMBRES_SISTEMA["frances"])
        combo_sist.grid(row=7, column=0, sticky="ew", padx=(0, 8), pady=(0, 12))
        self._combo_sist = combo_sist

        _campo(6, 1, "Interés moratorio diario (%):")
        self.var_mora = tk.StringVar(value="0.5")
        tk.Entry(contenedor, textvariable=self.var_mora, font=("Segoe UI", 11)).grid(
            row=7, column=1, sticky="ew", pady=(0, 12))

        _campo(8, 0, "Fecha de desembolso:")
        frame_fecha = tk.Frame(contenedor, bg=BLANCO)
        frame_fecha.grid(row=9, column=0, sticky="w", pady=(0, 12))
        self._fecha_desembolso = datetime.date.today()
        self.lbl_fecha = tk.Label(frame_fecha, text=_formatear_fecha(self._fecha_desembolso),
                                   font=("Segoe UI", 10), bg=GRIS_FONDO, padx=10, pady=6,
                                   cursor="hand2")
        self.lbl_fecha.pack(side="left")
        self.lbl_fecha.bind("<Button-1>", lambda e: self._elegir_fecha())

        _campo(8, 1, "Observaciones:")
        self.var_observaciones = tk.StringVar()
        entry_obs = tk.Entry(contenedor, textvariable=self.var_observaciones, font=("Segoe UI", 10))
        entry_obs.grid(row=9, column=1, sticky="ew", pady=(0, 12))
        forzar_mayusculas(entry_obs, self.var_observaciones)

        frame_botones = tk.Frame(contenedor, bg=BLANCO)
        frame_botones.grid(row=10, column=0, columnspan=2, sticky="w", pady=(6, 14))
        tk.Button(frame_botones, text="👁 Vista Previa del Cronograma", font=("Segoe UI", 9, "bold"),
                  bg=BLANCO, fg=AZUL_RIBBON, relief="solid", bd=1, padx=12, pady=8,
                  cursor="hand2", command=self._vista_previa).pack(side="left", padx=(0, 8))
        tk.Button(frame_botones, text="✔ Desembolsar Préstamo", font=("Segoe UI", 9, "bold"),
                  bg=BLANCO, fg=VERDE, relief="solid", bd=1, padx=12, pady=8,
                  cursor="hand2", command=self._desembolsar).pack(side="left")

        tk.Label(contenedor, text="Cronograma (vista previa)", font=("Segoe UI", 10, "bold"),
                 bg=BLANCO).grid(row=11, column=0, columnspan=2, sticky="w")
        contenedor_tabla = tk.Frame(contenedor, bg=BLANCO)
        contenedor_tabla.grid(row=12, column=0, columnspan=2, sticky="nsew", pady=(4, 0))
        contenedor.grid_rowconfigure(12, weight=1)
        columnas = ("nro", "vencimiento", "capital", "interes", "cuota")
        encabezados = ("CUOTA", "VENCIMIENTO", "CAPITAL", "INTERÉS", "TOTAL CUOTA")
        self.tabla_preview = ttk.Treeview(contenedor_tabla, columns=columnas, show="headings", height=8)
        habilitar_deseleccion_treeview(self.tabla_preview)
        for col, enc in zip(columnas, encabezados):
            self.tabla_preview.heading(col, text=enc)
            self.tabla_preview.column(col, width=120, anchor="center")
        contenedor_tabla.grid_rowconfigure(0, weight=1)
        contenedor_tabla.grid_columnconfigure(0, weight=1)
        scrollbar = ttk.Scrollbar(contenedor_tabla, orient="vertical", command=self.tabla_preview.yview)
        scrollbar_h = ttk.Scrollbar(contenedor_tabla, orient="horizontal", command=self.tabla_preview.xview)
        self.tabla_preview.configure(yscrollcommand=scrollbar.set, xscrollcommand=scrollbar_h.set)
        self.tabla_preview.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        scrollbar_h.grid(row=1, column=0, sticky="ew")

    def _elegir_cliente(self):
        def _al_elegir(cliente):
            self._cliente_seleccionado = cliente
            self.lbl_cliente.config(
                text=f"{cliente['nombre']}  (Doc. {cliente['nro_documento'] or 's/d'})",
                fg=NEGRO)
        VentanaSeleccionarClientePrestamo(self, _al_elegir)

    def _elegir_fecha(self):
        def _al_elegir(fecha):
            self._fecha_desembolso = fecha
            self.lbl_fecha.config(text=_formatear_fecha(fecha))
        abrir_selector_fecha(self, self._fecha_desembolso, _al_elegir)

    def _clave_sistema_actual(self) -> str:
        etiqueta = self._combo_sist.get()
        for clave, et in SISTEMAS_AMORTIZACION:
            if et == etiqueta:
                return clave
        return "frances"

    def _clave_frecuencia_actual(self) -> str:
        etiqueta = self._combo_frec.get()
        for clave, et in FRECUENCIAS:
            if et == etiqueta:
                return clave
        return "mensual"

    def _leer_formulario(self):
        capital = _texto_a_monto(self.var_capital.get())
        tasa = float((self.var_tasa.get() or "0").replace(",", "."))
        cuotas = int(float(self.var_cuotas.get() or "0"))
        mora = float((self.var_mora.get() or "0").replace(",", "."))
        return capital, tasa, cuotas, mora

    def _vista_previa(self):
        try:
            capital, tasa, cuotas, mora = self._leer_formulario()
        except ValueError:
            messagebox.showwarning("Datos inválidos", "Revisa los montos y números ingresados.", parent=self)
            return
        if capital <= 0 or cuotas <= 0:
            messagebox.showwarning("Datos incompletos",
                                    "Ingresa un capital y una cantidad de cuotas mayores a cero.", parent=self)
            return
        sistema = self._clave_sistema_actual()
        frecuencia = self._clave_frecuencia_actual()
        cronograma = calcular_cronograma(capital, tasa, cuotas, sistema)
        fechas = generar_fechas_cuotas(self._fecha_desembolso, frecuencia, cuotas)

        for f in self.tabla_preview.get_children():
            self.tabla_preview.delete(f)
        for fila, fecha in zip(cronograma, fechas):
            self.tabla_preview.insert("", "end", values=(
                fila["nro"], _formatear_fecha(fecha), formatear_gs(fila["capital"]),
                formatear_gs(fila["interes"]), formatear_gs(fila["cuota"]),
            ))

    def _desembolsar(self):
        if not self._cliente_seleccionado:
            messagebox.showwarning("Falta el cliente", "Selecciona un cliente para el préstamo.", parent=self)
            return
        try:
            capital, tasa, cuotas, mora = self._leer_formulario()
        except ValueError:
            messagebox.showwarning("Datos inválidos", "Revisa los montos y números ingresados.", parent=self)
            return

        sistema = self._clave_sistema_actual()
        frecuencia = self._clave_frecuencia_actual()
        if not messagebox.askyesno(
                "Confirmar desembolso",
                f"¿Confirmás el desembolso de {formatear_gs(capital)} a "
                f"{self._cliente_seleccionado['nombre']} en {cuotas} cuotas "
                f"({NOMBRES_SISTEMA.get(sistema, sistema)})?", parent=self):
            return

        ok, msg, prestamo_id = crear_prestamo(
            self._cliente_seleccionado["id"], capital, tasa, frecuencia, cuotas, sistema,
            mora, self._fecha_desembolso, self.var_observaciones.get(), self.usuario_actual["id"])

        if ok:
            messagebox.showinfo("Préstamo desembolsado", msg, parent=self)
            self._limpiar_formulario_nuevo()
            self._cargar_fondo()
            self._cargar_lista()
            self.nb.select(self.tab_lista)
        else:
            messagebox.showerror("No se pudo desembolsar", msg, parent=self)

    def _limpiar_formulario_nuevo(self):
        self._cliente_seleccionado = None
        self.lbl_cliente.config(text="Ningún cliente seleccionado", fg=GRIS_TEXTO)
        self.var_capital.set("")
        self.var_observaciones.set("")
        for f in self.tabla_preview.get_children():
            self.tabla_preview.delete(f)

    # ──────────────────────── TAB: LISTADO DE PRÉSTAMOS ────────────────────────
    def _construir_tab_lista(self):
        marco = self.tab_lista
        barra = tk.Frame(marco, bg=BLANCO)
        barra.pack(fill="x", padx=14, pady=(12, 6))

        self.var_vista_prestamos = tk.StringVar(value="activos")
        for valor, etiqueta in (("activos", "Activos"), ("pagados", "Pagados"), ("todos", "Todos")):
            tk.Radiobutton(barra, text=etiqueta, variable=self.var_vista_prestamos, value=valor,
                          bg=BLANCO, font=("Segoe UI", 9), command=self._cargar_lista
                          ).pack(side="left", padx=(0, 10))

        self.var_busqueda_prestamos = tk.StringVar()
        entry = tk.Entry(barra, textvariable=self.var_busqueda_prestamos, font=("Segoe UI", 9), width=28)
        entry.pack(side="right")
        entry.bind("<KeyRelease>", lambda e: self._cargar_lista())
        tk.Label(barra, text="🔎 Buscar cliente:", bg=BLANCO, font=("Segoe UI", 9)).pack(side="right", padx=(0, 6))

        contenedor = tk.Frame(marco, bg=BLANCO)
        contenedor.pack(fill="both", expand=True, padx=14, pady=6)
        columnas = ("id", "cliente", "capital", "sistema", "cuotas", "proximo", "saldo", "estado")
        encabezados = ("ID", "CLIENTE", "CAPITAL", "SISTEMA", "CUOTAS PAGADAS", "PRÓX. VENCIMIENTO",
                        "SALDO PENDIENTE", "ESTADO")
        self.tabla_prestamos = ttk.Treeview(contenedor, columns=columnas, show="headings")
        habilitar_deseleccion_treeview(self.tabla_prestamos)
        anchos = (50, 200, 120, 170, 110, 130, 140, 90)
        for col, enc, w in zip(columnas, encabezados, anchos):
            self.tabla_prestamos.heading(col, text=enc)
            self.tabla_prestamos.column(col, width=w,
                                         anchor="w" if col == "cliente" else "center")
        self.tabla_prestamos.tag_configure("vencido", background="#fde8e8", foreground=ROJO)
        self.tabla_prestamos.tag_configure("pagado", background="#e8f7ee", foreground=VERDE)
        self.tabla_prestamos.tag_configure("al_dia", background=BLANCO)

        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla_prestamos.yview)
        scrollbar_h = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla_prestamos.xview)
        self.tabla_prestamos.configure(yscrollcommand=scrollbar.set, xscrollcommand=scrollbar_h.set)
        self.tabla_prestamos.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        scrollbar_h.grid(row=1, column=0, sticky="ew")

        self.tabla_prestamos.bind("<Double-1>", lambda e: self._abrir_detalle())

        frame_botones = tk.Frame(marco, bg=BLANCO)
        frame_botones.pack(fill="x", padx=14, pady=(0, 10))
        tk.Button(frame_botones, text="🔍 Ver Detalle / Registrar Pago", font=("Segoe UI", 9, "bold"),
                  bg=BLANCO, fg=AZUL_RIBBON, relief="solid", bd=1, padx=10, pady=6,
                  cursor="hand2", command=self._abrir_detalle).pack(side="left")

        self._cargar_lista()

    def _cargar_lista(self):
        for f in self.tabla_prestamos.get_children():
            self.tabla_prestamos.delete(f)
        etiquetas_estado = {"Al día": "al_dia", "Vencido": "vencido", "Pagado": "pagado", "Cancelado": "al_dia"}
        for p in listar_prestamos(vista=self.var_vista_prestamos.get(),
                                   texto_busqueda=self.var_busqueda_prestamos.get()):
            tag = etiquetas_estado.get(p["estado_calculado"], "al_dia")
            self.tabla_prestamos.insert("", "end", iid=str(p["id"]), tags=(tag,), values=(
                p["id"], p["cliente"], formatear_gs(p["capital"]),
                NOMBRES_SISTEMA.get(p["sistema"], p["sistema"]),
                f"{p['cuotas_pagadas']}/{p['cantidad_cuotas']}",
                _formatear_fecha(p["proxima_fecha_vencimiento"]) if p["proxima_fecha_vencimiento"] else "—",
                formatear_gs(p["saldo_total"]), p["estado_calculado"],
            ))

    def _abrir_detalle(self):
        seleccion = self.tabla_prestamos.selection()
        if not seleccion:
            messagebox.showwarning("Selecciona un préstamo", "Elige un préstamo de la lista.", parent=self)
            return
        prestamo_id = int(seleccion[0])
        VentanaDetallePrestamo(self, prestamo_id, self.usuario_actual,
                               on_cambio=lambda: (self._cargar_lista(), self._cargar_fondo()))
