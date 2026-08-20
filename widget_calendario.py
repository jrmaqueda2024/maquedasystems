"""
widget_calendario.py
Selector de fecha tipo calendario emergente, reutilizable en cualquier
ventana del sistema (Resumen de Ventas, Reporte por Rango, etc.).
No depende de tkcalendar (puede no estar instalado); se construye con
Tkinter puro usando el módulo estándar `calendar`.
"""
import tkinter as tk
from tkinter import ttk
import calendar
import datetime

AZUL_RIBBON = "#1d5fd6"
GRIS_CLARO = "#f4f5f7"

MESES_ES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]
DIAS_ES = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"]

# Rango de años que se ofrece en el selector rápido: bastante amplio hacia
# atrás para poder elegir fechas de nacimiento o de ingreso antiguas, y
# unos años hacia adelante para vigencias de timbrado, vencimientos, etc.
ANIOS_ATRAS = 100
ANIOS_ADELANTE = 10


class _VentanaCalendario(tk.Toplevel):
    """Ventana emergente con el calendario de un mes navegable, con
    selectores rápidos de mes y de año además de las flechas.

    Tiene dos modos:
    - Selección simple (modo_rango=False): un click en un día elige esa
      fecha y cierra la ventana. Es el comportamiento de siempre.
    - Selección de rango (modo_rango=True): el primer click marca el
      'Desde', el segundo marca el 'Hasta' (los días intermedios quedan
      resaltados); un botón 'Aplicar' confirma el rango elegido.
    """

    def __init__(self, parent, fecha_inicial: datetime.date, on_fecha_elegida,
                 modo_rango: bool = False, fecha_desde_inicial: datetime.date | None = None,
                 fecha_hasta_inicial: datetime.date | None = None):
        super().__init__(parent)
        self.on_fecha_elegida = on_fecha_elegida
        self.modo_rango = modo_rango
        self.anio = fecha_inicial.year
        self.mes = fecha_inicial.month

        if modo_rango:
            self.fecha_desde_sel = fecha_desde_inicial
            self.fecha_hasta_sel = fecha_hasta_inicial

        self.title("Seleccionar fecha" if not modo_rango else "Seleccionar rango de fechas")
        self.resizable(False, False)
        self.configure(bg="white")
        self.grab_set()
        self.transient(parent)

        anio_actual = datetime.date.today().year
        self._anios_disponibles = list(range(anio_actual - ANIOS_ATRAS, anio_actual + ANIOS_ADELANTE + 1))
        if self.anio not in self._anios_disponibles:
            # Si la fecha inicial trae un año fuera del rango típico,
            # lo agregamos igual para no perderlo.
            self._anios_disponibles.append(self.anio)
            self._anios_disponibles.sort()

        self._construir()

    def _construir(self):
        for widget in self.winfo_children():
            widget.destroy()

        if self.modo_rango:
            info = tk.Frame(self, bg=GRIS_CLARO)
            info.pack(fill="x")
            texto_desde = self.fecha_desde_sel.strftime("%d/%m/%Y") if self.fecha_desde_sel else "—"
            texto_hasta = self.fecha_hasta_sel.strftime("%d/%m/%Y") if self.fecha_hasta_sel else "—"
            tk.Label(info, text=f"Desde: {texto_desde}    Hasta: {texto_hasta}",
                     font=("Segoe UI", 9, "bold"), bg=GRIS_CLARO, fg=AZUL_RIBBON
                     ).pack(pady=6, padx=8)

        barra = tk.Frame(self, bg=AZUL_RIBBON)
        barra.pack(fill="x")

        tk.Button(barra, text="◀", font=("Segoe UI", 10, "bold"), bg=AZUL_RIBBON, fg="white",
                  relief="flat", command=self._mes_anterior).pack(side="left", padx=(4, 2), pady=4)

        estilo = ttk.Style()
        estilo.configure("Calendario.TCombobox", font=("Segoe UI", 9))

        var_mes = tk.StringVar(value=MESES_ES[self.mes - 1])
        combo_mes = ttk.Combobox(barra, textvariable=var_mes, values=MESES_ES,
                                 state="readonly", width=10, style="Calendario.TCombobox")
        combo_mes.pack(side="left", padx=2, pady=4)
        combo_mes.bind("<<ComboboxSelected>>",
                       lambda e: self._ir_a_mes(MESES_ES.index(var_mes.get()) + 1))

        var_anio = tk.StringVar(value=str(self.anio))
        combo_anio = ttk.Combobox(barra, textvariable=var_anio, values=[str(a) for a in self._anios_disponibles],
                                  state="readonly", width=6, style="Calendario.TCombobox")
        combo_anio.pack(side="left", padx=2, pady=4)
        combo_anio.bind("<<ComboboxSelected>>",
                        lambda e: self._ir_a_anio(int(var_anio.get())))

        tk.Button(barra, text="▶", font=("Segoe UI", 10, "bold"), bg=AZUL_RIBBON, fg="white",
                  relief="flat", command=self._mes_siguiente).pack(side="right", padx=(2, 4), pady=4)

        frame_dias = tk.Frame(self, bg="white")
        frame_dias.pack(padx=8, pady=(8, 2))
        for i, dia in enumerate(DIAS_ES):
            tk.Label(frame_dias, text=dia, font=("Segoe UI", 8, "bold"), bg="white", fg="#888",
                     width=4).grid(row=0, column=i)

        hoy = datetime.date.today()
        semanas = calendar.monthcalendar(self.anio, self.mes)
        for fila, semana in enumerate(semanas, start=1):
            for col, dia in enumerate(semana):
                if dia == 0:
                    continue
                fecha_celda = datetime.date(self.anio, self.mes, dia)
                es_hoy = (dia == hoy.day and self.mes == hoy.month and self.anio == hoy.year)
                bg = "#dbeafe" if es_hoy else "white"
                fg = "black"
                if self.modo_rango:
                    if self.fecha_desde_sel and fecha_celda == self.fecha_desde_sel:
                        bg, fg = AZUL_RIBBON, "white"
                    elif self.fecha_hasta_sel and fecha_celda == self.fecha_hasta_sel:
                        bg, fg = AZUL_RIBBON, "white"
                    elif (self.fecha_desde_sel and self.fecha_hasta_sel
                          and self.fecha_desde_sel < fecha_celda < self.fecha_hasta_sel):
                        bg = "#dbeafe"
                btn = tk.Button(
                    frame_dias, text=str(dia), font=("Segoe UI", 9),
                    bg=bg, fg=fg, width=4, relief="flat",
                    command=lambda d=dia: self._elegir_dia(d),
                )
                btn.grid(row=fila, column=col, pady=1)

        pie = tk.Frame(self, bg="white")
        pie.pack(pady=(4, 8))
        tk.Button(pie, text="Hoy", font=("Segoe UI", 8), bg=GRIS_CLARO,
                  command=self._ir_a_hoy).pack(side="left", padx=4)
        if self.modo_rango:
            tk.Button(pie, text="✔ Aplicar", font=("Segoe UI", 8, "bold"), bg=AZUL_RIBBON, fg="white",
                      relief="flat", padx=10, command=self._aplicar_rango).pack(side="left", padx=4)
            tk.Button(pie, text="✕ Cancelar", font=("Segoe UI", 8), bg=GRIS_CLARO,
                      command=self.destroy).pack(side="left", padx=4)

    def _mes_anterior(self):
        self.mes -= 1
        if self.mes == 0:
            self.mes = 12
            self.anio -= 1
        self._construir()

    def _mes_siguiente(self):
        self.mes += 1
        if self.mes == 13:
            self.mes = 1
            self.anio += 1
        self._construir()

    def _ir_a_mes(self, mes: int):
        self.mes = mes
        self._construir()

    def _ir_a_anio(self, anio: int):
        self.anio = anio
        # Si el mes actual no tiene ese día en el nuevo año (29 de febrero
        # en año no bisiesto) igual da lo mismo, porque acá solo cambiamos
        # de año/mes, no de día.
        self._construir()

    def _ir_a_hoy(self):
        hoy = datetime.date.today()
        self.anio, self.mes = hoy.year, hoy.month
        self._construir()

    def _elegir_dia(self, dia):
        fecha = datetime.date(self.anio, self.mes, dia)
        if not self.modo_rango:
            self.destroy()
            self.on_fecha_elegida(fecha)
            return

        # Modo rango: primer click = Desde; segundo click = Hasta (si el
        # segundo click cae antes del primero, se intercambian); un tercer
        # click reinicia la selección desde cero.
        if self.fecha_desde_sel is None or (self.fecha_desde_sel and self.fecha_hasta_sel):
            self.fecha_desde_sel = fecha
            self.fecha_hasta_sel = None
        elif fecha < self.fecha_desde_sel:
            self.fecha_hasta_sel = self.fecha_desde_sel
            self.fecha_desde_sel = fecha
        else:
            self.fecha_hasta_sel = fecha
        self._construir()

    def _aplicar_rango(self):
        if self.fecha_desde_sel is None:
            return
        fecha_hasta_final = self.fecha_hasta_sel or self.fecha_desde_sel
        self.destroy()
        self.on_fecha_elegida(self.fecha_desde_sel, fecha_hasta_final)


def abrir_selector_fecha(parent, fecha_actual: datetime.date, on_fecha_elegida):
    """Abre el calendario emergente. on_fecha_elegida(fecha: datetime.date) se
    llama cuando el usuario hace click en un día."""
    _VentanaCalendario(parent, fecha_actual, on_fecha_elegida)


def abrir_selector_rango_fechas(parent, fecha_desde_actual: datetime.date,
                                 fecha_hasta_actual: datetime.date, on_rango_elegido):
    """Abre un calendario que permite elegir un rango Desde/Hasta en una
    sola ventana: primer click marca el inicio, segundo click marca el
    fin (resaltando los días intermedios), y el botón 'Aplicar' confirma.
    on_rango_elegido(fecha_desde, fecha_hasta) se llama al aplicar."""
    _VentanaCalendario(parent, fecha_desde_actual, on_rango_elegido, modo_rango=True,
                       fecha_desde_inicial=fecha_desde_actual, fecha_hasta_inicial=fecha_hasta_actual)


def formatear_fecha_es(fecha: datetime.date) -> str:
    """Formatea una fecha como 'domingo, 28 de junio de 2026', igual al
    estilo de MetaVentas."""
    dias_semana = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    dia_semana = dias_semana[fecha.weekday()]
    mes = MESES_ES[fecha.month - 1].lower()
    return f"{dia_semana}, {fecha.day} de {mes} de {fecha.year}"
