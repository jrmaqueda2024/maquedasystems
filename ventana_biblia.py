"""
ventana_biblia.py
Módulo "Biblia": permite leer el Antiguo Testamento, el Nuevo Testamento
o la Santa Biblia completa, organizados en pestañas. Los textos se
descargan de Internet (Reina-Valera, dominio público) la primera vez que
se abre cada libro, y quedan guardados en caché local para poder seguir
leyendo sin conexión luego de eso. Incluye buscador de palabras dentro
de los libros ya descargados de cada pestaña.
"""
import threading
import tkinter as tk
from tkinter import ttk, messagebox

import models_biblia as mb

AZUL_RIBBON = "#1d5fd6"
BLANCO = "#ffffff"
GRIS_FONDO = "#f4f5f7"
GRIS_BORDE = "#e2e8f0"
GRIS_TEXTO = "#374151"
VERDE = "#16a34a"
ROJO = "#dc2626"

# Colores de acento por pestaña, para diferenciarlas visualmente.
COLOR_AT = "#92400e"      # marrón/dorado -> Antiguo Testamento
COLOR_NT = "#1d4ed8"      # azul -> Nuevo Testamento
COLOR_COMPLETA = "#6d28d9"  # violeta -> Biblia completa


class PanelBiblia(tk.Frame):
    def __init__(self, parent, usuario_actual):
        super().__init__(parent, bg=GRIS_FONDO)
        self.usuario_actual = usuario_actual
        self._construir_ui()

    def _construir_ui(self):
        encabezado = tk.Frame(self, bg=AZUL_RIBBON, height=54)
        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)
        tk.Label(encabezado, text="📖 Biblia", font=("Segoe UI", 15, "bold"),
                 bg=AZUL_RIBBON, fg=BLANCO).pack(side="left", padx=20, pady=12)
        tk.Label(encabezado,
                 text="Reina-Valera · los textos se descargan de Internet y quedan guardados para leer sin conexión",
                 font=("Segoe UI", 8, "italic"), bg=AZUL_RIBBON, fg="#dbeafe"
                 ).pack(side="left", padx=(0, 20))

        estilo = ttk.Style(self)
        try:
            estilo.configure("Biblia.TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=(14, 8))
        except tk.TclError:
            pass

        nb = ttk.Notebook(self, style="Biblia.TNotebook")
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        tab_at = PanelLectorBiblia(nb, mb.LIBROS_ANTIGUO_TESTAMENTO, COLOR_AT,
                                    "Antiguo Testamento", "📜")
        tab_nt = PanelLectorBiblia(nb, mb.LIBROS_NUEVO_TESTAMENTO, COLOR_NT,
                                    "Nuevo Testamento", "✝")
        tab_completa = PanelLectorBiblia(nb, mb.LIBROS_BIBLIA_COMPLETA, COLOR_COMPLETA,
                                          "Santa Biblia Completa", "📕")

        nb.add(tab_at, text="📜 Antiguo Testamento")
        nb.add(tab_nt, text="✝ Nuevo Testamento")
        nb.add(tab_completa, text="📕 Santa Biblia Completa")


class PanelLectorBiblia(tk.Frame):
    """Un lector completo (lista de libros + capítulos + texto + buscador)
    para un conjunto de libros determinado (AT, NT, o los 66 completos)."""

    def __init__(self, parent, lista_libros: list, color: str, titulo: str, icono: str):
        super().__init__(parent, bg=GRIS_FONDO)
        self.lista_libros = lista_libros
        self.color = color
        self.titulo = titulo
        self.icono = icono
        self.libro_actual = None
        self.datos_libro_actual = None
        self._construir_ui()

    # ---------------------------------------------------------- UI ----
    def _construir_ui(self):
        franja = tk.Frame(self, bg=self.color, height=40)
        franja.pack(fill="x")
        franja.pack_propagate(False)
        tk.Label(franja, text=f"{self.icono} {self.titulo} — {len(self.lista_libros)} libros",
                 font=("Segoe UI", 11, "bold"), bg=self.color, fg=BLANCO
                 ).pack(side="left", padx=14, pady=6)
        self.lbl_progreso_cache = tk.Label(
            franja, text="", font=("Segoe UI", 9), bg=self.color, fg="#e5e7eb")
        self.lbl_progreso_cache.pack(side="right", padx=14)

        tk.Button(franja, text="⬇ Descargar todos los libros faltantes",
                  font=("Segoe UI", 9, "bold"), bg=BLANCO, fg=self.color,
                  relief="flat", cursor="hand2", padx=10,
                  command=self._descargar_todos).pack(side="right", padx=8, pady=5)

        cuerpo = tk.Frame(self, bg=GRIS_FONDO)
        cuerpo.pack(fill="both", expand=True, padx=10, pady=10)

        # ---- Columna izquierda: lista de libros + buscador ----
        col_izq = tk.Frame(cuerpo, bg=BLANCO, relief="solid", bd=1,
                            highlightbackground=GRIS_BORDE, width=240)
        col_izq.pack(side="left", fill="y")
        col_izq.pack_propagate(False)

        tk.Label(col_izq, text="Libros", font=("Segoe UI", 10, "bold"),
                 bg=BLANCO, fg=GRIS_TEXTO).pack(anchor="w", padx=10, pady=(10, 4))

        marco_lista = tk.Frame(col_izq, bg=BLANCO)
        marco_lista.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        scroll_libros = tk.Scrollbar(marco_lista)
        scroll_libros.pack(side="right", fill="y")
        self.lista_box = tk.Listbox(
            marco_lista, font=("Segoe UI", 10), relief="flat",
            selectbackground=self.color, selectforeground=BLANCO,
            highlightthickness=0, yscrollcommand=scroll_libros.set, activestyle="none")
        self.lista_box.pack(side="left", fill="both", expand=True)
        scroll_libros.config(command=self.lista_box.yview)
        for libro in self.lista_libros:
            self.lista_box.insert("end", libro)
        self._refrescar_marcas_cache()
        self.lista_box.bind("<<ListboxSelect>>", self._al_elegir_libro)

        # ---- Buscador ----
        marco_buscar = tk.Frame(col_izq, bg=BLANCO)
        marco_buscar.pack(fill="x", padx=10, pady=(4, 10))
        self.var_busqueda = tk.StringVar()
        entry_buscar = tk.Entry(marco_buscar, textvariable=self.var_busqueda,
                                 font=("Segoe UI", 9), relief="solid", bd=1)
        entry_buscar.pack(side="left", fill="x", expand=True, ipady=3)
        entry_buscar.bind("<Return>", lambda e: self._buscar())
        tk.Button(marco_buscar, text="🔎", font=("Segoe UI", 9), bg=self.color, fg=BLANCO,
                  relief="flat", cursor="hand2", command=self._buscar).pack(side="left", padx=(4, 0))

        # ---- Columna derecha: encabezado de libro/capítulo + texto ----
        col_der = tk.Frame(cuerpo, bg=BLANCO, relief="solid", bd=1,
                            highlightbackground=GRIS_BORDE)
        col_der.pack(side="left", fill="both", expand=True, padx=(10, 0))

        barra_libro = tk.Frame(col_der, bg="#f8fafc")
        barra_libro.pack(fill="x")
        self.lbl_libro = tk.Label(barra_libro, text="Elegí un libro de la lista →",
                                   font=("Segoe UI", 12, "bold"), bg="#f8fafc", fg=GRIS_TEXTO)
        self.lbl_libro.pack(side="left", padx=14, pady=10)

        self.var_capitulo = tk.StringVar()
        self.combo_capitulo = ttk.Combobox(barra_libro, textvariable=self.var_capitulo,
                                            state="disabled", width=6, font=("Segoe UI", 10))
        self.combo_capitulo.pack(side="right", padx=(0, 14))
        self.combo_capitulo.bind("<<ComboboxSelected>>", lambda e: self._mostrar_capitulo())
        tk.Label(barra_libro, text="Capítulo:", font=("Segoe UI", 9), bg="#f8fafc",
                 fg=GRIS_TEXTO).pack(side="right")

        self.btn_actualizar = tk.Button(
            barra_libro, text="🔄 Actualizar de Internet", font=("Segoe UI", 8, "bold"),
            bg=BLANCO, fg=self.color, relief="solid", bd=1, cursor="hand2",
            state="disabled", command=self._forzar_actualizacion)
        self.btn_actualizar.pack(side="right", padx=8)

        # ---- Área de texto ----
        marco_texto = tk.Frame(col_der, bg=BLANCO)
        marco_texto.pack(fill="both", expand=True, padx=14, pady=12)
        scroll_texto = tk.Scrollbar(marco_texto)
        scroll_texto.pack(side="right", fill="y")
        self.texto = tk.Text(marco_texto, font=("Georgia", 11), wrap="word", relief="flat",
                              bg=BLANCO, fg="#111827", yscrollcommand=scroll_texto.set,
                              padx=6, pady=4, state="disabled", cursor="arrow")
        self.texto.pack(side="left", fill="both", expand=True)
        scroll_texto.config(command=self.texto.yview)
        self.texto.tag_configure("numero", font=("Segoe UI", 9, "bold"), foreground=self.color)
        self.texto.tag_configure("verso", font=("Georgia", 11), foreground="#111827",
                                  spacing1=2, spacing3=6)
        self.texto.tag_configure("aviso", font=("Segoe UI", 9, "italic"), foreground="#92400e")

        self.lbl_estado = tk.Label(col_der, text="", font=("Segoe UI", 8, "italic"),
                                    bg=BLANCO, fg="#6b7280", anchor="w")
        self.lbl_estado.pack(fill="x", padx=14, pady=(0, 8))

    # -------------------------------------------------- utilidades ----
    def _refrescar_marcas_cache(self):
        """Marca con 📥 los libros ya descargados, para que el usuario
        vea de un vistazo qué le falta bajar de Internet."""
        for i, libro in enumerate(self.lista_libros):
            marca = "📥 " if mb.libro_en_cache(libro) else "☁ "
            self.lista_box.delete(i)
            self.lista_box.insert(i, f"{marca}{libro}")
        descargados = mb.cantidad_libros_en_cache(self.lista_libros)
        self.lbl_progreso_cache.config(
            text=f"{descargados}/{len(self.lista_libros)} libros descargados")

    def _escribir_texto(self, contenido: str, tag: str = "verso", limpiar=True):
        self.texto.config(state="normal")
        if limpiar:
            self.texto.delete("1.0", "end")
        self.texto.insert("end", contenido, tag)
        self.texto.config(state="disabled")

    # --------------------------------------------------- selección ----
    def _al_elegir_libro(self, event=None):
        seleccion = self.lista_box.curselection()
        if not seleccion:
            return
        libro = self.lista_libros[seleccion[0]]
        self.libro_actual = libro
        self.lbl_libro.config(text=libro)
        self.combo_capitulo.set("")
        self.combo_capitulo.config(state="disabled")
        self.btn_actualizar.config(state="disabled")
        self._escribir_texto("Cargando…", "aviso")
        self.lbl_estado.config(text="")
        self._cargar_libro(libro, forzar=False)

    def _cargar_libro(self, libro: str, forzar: bool):
        def _tarea():
            datos, origen = mb.obtener_libro(libro, forzar_descarga=forzar)

            def _ui():
                if self.libro_actual != libro:
                    return  # el usuario ya cambió de libro mientras bajaba
                if datos is None:
                    self._escribir_texto(f"⚠ {origen}", "aviso")
                    self.lbl_estado.config(text="")
                    return
                self.datos_libro_actual = datos
                capitulos = [str(c["chapter"]) for c in datos.get("chapters", [])]
                self.combo_capitulo.config(values=capitulos, state="readonly")
                if capitulos:
                    self.combo_capitulo.set(capitulos[0])
                self.btn_actualizar.config(state="normal")
                self._refrescar_marcas_cache()
                if origen == "cache":
                    self.lbl_estado.config(text="Mostrando versión ya descargada (guardada localmente).")
                elif origen == "descargado":
                    self.lbl_estado.config(text="✓ Descargado ahora desde Internet.")
                else:
                    self.lbl_estado.config(text=origen)
                self._mostrar_capitulo()

            self.after(0, _ui)

        threading.Thread(target=_tarea, daemon=True).start()

    def _forzar_actualizacion(self):
        if not self.libro_actual:
            return
        self._escribir_texto("Actualizando desde Internet…", "aviso")
        self._cargar_libro(self.libro_actual, forzar=True)

    def _mostrar_capitulo(self):
        if not self.datos_libro_actual or not self.var_capitulo.get():
            return
        num_cap = int(self.var_capitulo.get())
        capitulos = self.datos_libro_actual.get("chapters", [])
        capitulo = next((c for c in capitulos if c.get("chapter") == num_cap), None)
        if not capitulo:
            return
        self.texto.config(state="normal")
        self.texto.delete("1.0", "end")
        for v in capitulo.get("verses", []):
            self.texto.insert("end", f" {v.get('verse')} ", "numero")
            self.texto.insert("end", f"{v.get('text', '').strip()}\n", "verso")
        self.texto.config(state="disabled")
        self.texto.see("1.0")

    # ----------------------------------------------------- descargas ----
    def _descargar_todos(self):
        faltantes = mb.libros_faltantes(self.lista_libros)
        if not faltantes:
            messagebox.showinfo("Biblia", "Ya tenés todos los libros de esta pestaña descargados.",
                                 parent=self)
            return
        respuesta = messagebox.askyesno(
            "Descargar de Internet",
            f"Se van a descargar {len(faltantes)} libro(s) que todavía no tenés guardados.\n"
            "Esto puede tardar un momento según tu conexión. ¿Continuar?",
            parent=self,
        )
        if not respuesta:
            return

        self.lbl_progreso_cache.config(text=f"Descargando 0/{len(faltantes)}…")

        def _progreso(i, total, libro):
            self.after(0, lambda: self.lbl_progreso_cache.config(
                text=f"Descargando {i}/{total}: {libro}"))

        def _tarea():
            exitosos, fallidos, errores = mb.descargar_todos(self.lista_libros, _progreso)

            def _ui():
                self._refrescar_marcas_cache()
                mensaje = f"Descarga finalizada: {exitosos} libro(s) correctos"
                if fallidos:
                    mensaje += f", {fallidos} con error.\n\n" + "\n".join(errores[:5])
                    messagebox.showwarning("Descarga de la Biblia", mensaje, parent=self)
                else:
                    messagebox.showinfo("Descarga de la Biblia", mensaje + ".", parent=self)

            self.after(0, _ui)

        threading.Thread(target=_tarea, daemon=True).start()

    # ------------------------------------------------------- buscar ----
    def _buscar(self):
        termino = self.var_busqueda.get().strip()
        if not termino:
            return
        resultados = mb.buscar_texto(termino, self.lista_libros)
        self.texto.config(state="normal")
        self.texto.delete("1.0", "end")
        if not resultados:
            self.texto.insert(
                "end",
                f"Sin resultados para «{termino}» en los libros ya descargados de esta pestaña.\n"
                "Probá descargar más libros con el botón 'Descargar todos los libros faltantes'.",
                "aviso",
            )
        else:
            self.texto.insert("end", f"{len(resultados)} resultado(s) para «{termino}»:\n\n", "aviso")
            for r in resultados:
                self.texto.insert("end", f" {r['libro']} {r['capitulo']}:{r['versiculo']} ", "numero")
                self.texto.insert("end", f"{r['texto'].strip()}\n", "verso")
        self.texto.config(state="disabled")
        self.texto.see("1.0")
        self.lbl_libro.config(text=f"Resultados de búsqueda: «{termino}»")
