"""
ventana_cotizaciones.py
Módulo de Cotizaciones: muestra en tiempo real los tipos de cambio de
monedas fiduciarias (Frankfurter / BCE) y criptomonedas (CoinGecko),
con actualización automática cada 10 minutos y posibilidad de forzarla
manualmente. Se subdivide en dos sub-pestañas: Dinero Fiduciario y Cripto.

Fuentes:
  - Fiat: https://api.frankfurter.dev  (sin API key, datos del BCE)
  - Cripto: https://api.coingecko.com  (sin API key, plan público)
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import datetime
import json
from utilidades_ui import habilitar_deseleccion_treeview
from traducciones import t

try:
    from urllib.request import urlopen, Request
    from urllib.error import URLError
except ImportError:
    urlopen = None

AZUL       = "#1d5fd6"
AZUL_OSC   = "#163d8c"
GRIS_FONDO = "#f4f5f7"
GRIS_BORDE = "#e2e8f0"
BLANCO     = "#ffffff"
VERDE      = "#16a34a"
ROJO       = "#dc2626"
NARANJA    = "#d97706"
NEGRO      = "#1e293b"
GRIS_TEXT  = "#6b7280"

# Intervalo de actualización automática: 10 minutos en ms
INTERVALO_MS = 10 * 60 * 1000

# Monedas fiat base para mostrar (Frankfurter devuelve tasas relativas a EUR por defecto)
MONEDAS_FIAT_NOMBRES = {
    "AED": "Dírham Emiratos Árabes",  "AFN": "Afgani Afgano",
    "ALL": "Lek Albanés",             "AMD": "Dram Armenio",
    "ANG": "Florín Antillano",        "AOA": "Kwanza Angoleño",
    "ARS": "Peso Argentino",          "AUD": "Dólar Australiano",
    "AWG": "Florín Arubeño",          "AZN": "Manat Azerbaiyano",
    "BAM": "Marco Bosnio",            "BBD": "Dólar de Barbados",
    "BDT": "Taka Bangladesí",         "BGN": "Lev Búlgaro",
    "BHD": "Dinar Bareiní",           "BIF": "Franco Burundés",
    "BMD": "Dólar de Bermudas",       "BND": "Dólar de Brunéi",
    "BOB": "Boliviano",               "BRL": "Real Brasileño",
    "BSD": "Dólar Bahameño",          "BTN": "Ngultrum Butanés",
    "BWP": "Pula Botsuanesa",         "BYN": "Rublo Bielorruso",
    "BZD": "Dólar de Belice",         "CAD": "Dólar Canadiense",
    "CDF": "Franco Congoleño",        "CHF": "Franco Suizo",
    "CLP": "Peso Chileno",            "CNY": "Yuan Chino",
    "COP": "Peso Colombiano",         "CRC": "Colón Costarricense",
    "CUP": "Peso Cubano",             "CVE": "Escudo Caboverdiano",
    "CZK": "Corona Checa",            "DJF": "Franco Yibutiano",
    "DKK": "Corona Danesa",           "DOP": "Peso Dominicano",
    "DZD": "Dinar Argelino",          "EGP": "Libra Egipcia",
    "ERN": "Nakfa Eritreo",           "ETB": "Birr Etíope",
    "EUR": "Euro",                    "FJD": "Dólar Fiyiano",
    "FKP": "Libra de Malvinas",       "GBP": "Libra Esterlina",
    "GEL": "Lari Georgiano",          "GHS": "Cedi Ghanés",
    "GIP": "Libra gibraltareña",      "GMD": "Dalasi Gambiano",
    "GNF": "Franco Guineano",         "GTQ": "Quetzal Guatemalteco",
    "GYD": "Dólar Guyanés",           "HKD": "Dólar de Hong Kong",
    "HNL": "Lempira Hondureño",       "HTG": "Gourde Haitiano",
    "HUF": "Forinto Húngaro",         "IDR": "Rupia Indonesia",
    "ILS": "Séquel Israelí",          "INR": "Rupia India",
    "IQD": "Dinar Iraquí",            "IRR": "Rial Iraní",
    "ISK": "Corona Islandesa",        "JMD": "Dólar Jamaicano",
    "JOD": "Dinar Jordano",           "JPY": "Yen Japonés",
    "KES": "Chelín Keniano",          "KGS": "Som Kirguís",
    "KHR": "Riel Camboyano",          "KMF": "Franco Comorense",
    "KPW": "Won Norcoreano",          "KRW": "Won Surcoreano",
    "KWD": "Dinar Kuwaití",           "KYD": "Dólar Caimán",
    "KZT": "Tenge Kazajo",            "LAK": "Kip Laosiano",
    "LBP": "Libra Libanesa",          "LKR": "Rupia de Sri Lanka",
    "LRD": "Dólar Liberiano",         "LSL": "Loti Lesotense",
    "LYD": "Dinar Libio",             "MAD": "Dírham Marroquí",
    "MDL": "Leu Moldavo",             "MGA": "Ariary Malgache",
    "MKD": "Denar Macedonio",         "MMK": "Kyat Birmano",
    "MNT": "Tugrik Mongol",           "MOP": "Pataca Macaense",
    "MRU": "Uguiya Mauritana",        "MUR": "Rupia Mauriciana",
    "MVR": "Rufiyaa Maldiva",         "MWK": "Kwacha Malauí",
    "MXN": "Peso Mexicano",           "MYR": "Ringgit Malayo",
    "MZN": "Metical Mozambiqueño",    "NAD": "Dólar Namibio",
    "NGN": "Naira Nigeriana",         "NIO": "Córdoba Nicaragüense",
    "NOK": "Corona Noruega",          "NPR": "Rupia Nepalesa",
    "NZD": "Dólar Neozelandés",       "OMR": "Rial Omaní",
    "PAB": "Balboa Panameño",         "PEN": "Sol Peruano",
    "PGK": "Kina Papú",               "PHP": "Peso Filipino",
    "PKR": "Rupia Pakistaní",         "PLN": "Esloti Polaco",
    "PYG": "Guaraní Paraguayo",       "QAR": "Riyal Catarí",
    "RON": "Leu Rumano",              "RSD": "Dinar Serbio",
    "RUB": "Rublo Ruso",              "RWF": "Franco Ruandés",
    "SAR": "Riyal Saudí",             "SBD": "Dólar de Salomón",
    "SCR": "Rupia de Seychelles",     "SDG": "Libra Sudanesa",
    "SEK": "Corona Sueca",            "SGD": "Dólar de Singapur",
    "SHP": "Libra de Santa Elena",    "SLE": "Leone Sierraleonés",
    "SOS": "Chelín Somalí",           "SRD": "Dólar Surinamés",
    "STN": "Dobra Santomense",        "SVC": "Colón Salvadoreño",
    "SYP": "Libra Siria",             "SZL": "Lilangeni Suazi",
    "THB": "Baht Tailandés",          "TJS": "Somoni Tayiko",
    "TMT": "Manat Turcomano",         "TND": "Dinar Tunecino",
    "TOP": "Paʻanga Tongano",         "TRY": "Lira Turca",
    "TTD": "Dólar de Trinidad",       "TWD": "Dólar Taiwanés",
    "TZS": "Chelín Tanzano",          "UAH": "Grivna Ucraniana",
    "UGX": "Chelín Ugandés",          "USD": "Dólar Estadounidense",
    "UYU": "Peso Uruguayo",           "UZS": "Som Uzbeko",
    "VES": "Bolívar Venezolano",      "VND": "Dong Vietnamita",
    "VUV": "Vatu Vanuatense",         "WST": "Tālā Samoano",
    "XAF": "Franco CFA Central",      "XCD": "Dólar Caribeño Oriental",
    "XOF": "Franco CFA Occidental",   "XPF": "Franco CFP",
    "YER": "Rial Yemení",             "ZAR": "Rand Sudafricano",
    "ZMW": "Kwacha Zambiano",         "ZWL": "Dólar Zimbabuense",
}

# Top 50 criptos por defecto (CoinGecko IDs)
CRIPTO_IDS_DEFAULT = [
    "bitcoin", "ethereum", "tether", "binancecoin", "solana",
    "usd-coin", "xrp", "dogecoin", "toncoin", "cardano",
    "shiba-inu", "avalanche-2", "chainlink", "polkadot", "matic-network",
    "bitcoin-cash", "litecoin", "uniswap", "cosmos", "stellar",
    "monero", "ethereum-classic", "okb", "cronos", "filecoin",
    "near", "vechain", "internet-computer", "arbitrum", "aptos",
    "optimism", "hedera-hashgraph", "the-graph", "aave", "quant-network",
    "algorand", "elrond-erd-2", "eos", "flow", "tezos",
    "theta-token", "axie-infinity", "gala", "decentraland", "the-sandbox",
    "chiliz", "floki", "pepe", "bonk", "worldcoin-wld",
]


def _fetch_json(url: str, timeout=15) -> dict:
    """Descarga JSON desde una URL. Lanza excepción si falla."""
    req = Request(url, headers={"User-Agent": "MaquedaSystems/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ═════════════════════════════════════════════════════════════
#  PANEL PRINCIPAL
# ═════════════════════════════════════════════════════════════
class PanelCotizaciones(tk.Frame):
    def __init__(self, parent, usuario_actual=None):
        super().__init__(parent, bg=BLANCO)
        self.usuario_actual = usuario_actual
        self._job_actualizacion = None   # ID del after() para cancelarlo al destruir
        self._construir_ui()
        self._actualizar_todo()          # Primera carga inmediata
        self.bind("<Destroy>", self._al_destruir)

    def _al_destruir(self, event=None):
        if self._job_actualizacion:
            try:
                self.after_cancel(self._job_actualizacion)
            except Exception:
                pass

    # ── UI raíz ────────────────────────────────────────────────
    def _construir_ui(self):
        # Encabezado
        enc = tk.Frame(self, bg=AZUL, height=54)
        enc.pack(fill="x")
        enc.pack_propagate(False)
        tk.Label(enc, text=t("cotiz_titulo"),
                 font=("Segoe UI", 15, "bold"), bg=AZUL, fg=BLANCO
                 ).pack(side="left", padx=20, pady=12)

        # Info de última actualización + botón de actualización manual
        self.lbl_update = tk.Label(enc, text=t("cargando"),
                                    font=("Segoe UI", 8), bg=AZUL,
                                    fg="#93c5fd")
        self.lbl_update.pack(side="right", padx=8)

        self.btn_refresh = tk.Button(
            enc, text=f"🔄 {t('actualizar')}", font=("Segoe UI", 9),
            bg=AZUL_OSC, fg=BLANCO, relief="flat", padx=10, pady=4,
            cursor="hand2", command=self._actualizar_todo)
        self.btn_refresh.pack(side="right", padx=(0, 8), pady=12)

        # Notebook: dos sub-pestañas
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=8, pady=6)

        self._frame_fiat   = tk.Frame(self.nb, bg=BLANCO)
        self._frame_cripto = tk.Frame(self.nb, bg=BLANCO)
        self.nb.add(self._frame_fiat,   text=t("cotiz_tab_fiat"))
        self.nb.add(self._frame_cripto, text=t("cotiz_tab_cripto"))

        self._construir_tab_fiat()
        self._construir_tab_cripto()

    # ══════════════════════════════════════════════════════════
    #  TAB FIAT
    # ══════════════════════════════════════════════════════════
    def _construir_tab_fiat(self):
        f = self._frame_fiat
        f.grid_rowconfigure(1, weight=1)
        f.grid_columnconfigure(0, weight=1)

        # Barra de controles
        barra = tk.Frame(f, bg=GRIS_FONDO)
        barra.grid(row=0, column=0, sticky="ew", padx=6, pady=6)

        tk.Label(barra, text=t("cotiz_base"), font=("Segoe UI", 9, "bold"),
                 bg=GRIS_FONDO).pack(side="left", padx=(8, 4))

        monedas_base = ["USD", "EUR", "PYG", "BRL", "ARS", "GBP", "JPY",
                        "CHF", "CAD", "AUD", "CNY", "MXN", "CLP", "UYU",
                        "BOB", "COP", "PEN", "VES"]
        self.var_base_fiat = tk.StringVar(value="USD")
        combo_base = ttk.Combobox(barra, textvariable=self.var_base_fiat,
                                   values=monedas_base, width=8,
                                   state="readonly")
        combo_base.pack(side="left", padx=(0, 8))
        combo_base.bind("<<ComboboxSelected>>",
                        lambda e: self._cargar_fiat())

        # Separador visual
        tk.Frame(barra, bg=GRIS_BORDE, width=1).pack(
            side="left", fill="y", padx=8, pady=2)

        # Campo de conversión rápida
        tk.Label(barra, text=t("cotiz_convertir"),
                 font=("Segoe UI", 9, "bold"),
                 bg=GRIS_FONDO).pack(side="left", padx=(0, 4))

        self.var_monto_conv = tk.StringVar(value="1")
        entry_conv = tk.Entry(barra, textvariable=self.var_monto_conv,
                              font=("Segoe UI", 10, "bold"), width=14,
                              justify="right")
        entry_conv.pack(side="left", ipady=3)

        self.lbl_moneda_conv = tk.Label(
            barra, text="USD", font=("Segoe UI", 9, "bold"),
            bg=GRIS_FONDO, fg=AZUL)
        self.lbl_moneda_conv.pack(side="left", padx=(4, 4))

        tk.Label(barra, text=t("cotiz_ver_equivalencias"),
                 font=("Segoe UI", 8), bg=GRIS_FONDO,
                 fg=GRIS_TEXT).pack(side="left", padx=(0, 12))

        # Al cambiar el monto o la base, recalcular la columna Equivalente
        self.var_monto_conv.trace_add("write",
            lambda *_: self._recalcular_equivalente())
        self.var_base_fiat.trace_add("write",
            lambda *_: self.lbl_moneda_conv.config(
                text=self.var_base_fiat.get()))

        tk.Label(barra, text=f"🔍 {t('buscar')}:", font=("Segoe UI", 9),
                 bg=GRIS_FONDO).pack(side="left")
        self.var_busq_fiat = tk.StringVar()
        tk.Entry(barra, textvariable=self.var_busq_fiat,
                 font=("Segoe UI", 9), width=16).pack(
                     side="left", padx=4, ipady=3)
        self.var_busq_fiat.trace_add("write", lambda *_: self._filtrar_fiat())

        self.lbl_estado_fiat = tk.Label(barra, text="", font=("Segoe UI", 8),
                                         bg=GRIS_FONDO, fg=GRIS_TEXT)
        self.lbl_estado_fiat.pack(side="right", padx=8)

        # Grilla fiat
        cont = tk.Frame(f, bg=BLANCO)
        cont.grid(row=1, column=0, sticky="nsew", padx=6)
        cont.grid_rowconfigure(0, weight=1)
        cont.grid_columnconfigure(0, weight=1)

        cols   = ("codigo", "nombre", "tasa", "inversa", "equivalente")
        encabs = (t("col_codigo_mayus"), t("cotiz_col_moneda"), t("cotiz_col_tasa"), t("cotiz_col_inversa"), t("cotiz_col_equivalente"))
        anchos = (70, 240, 160, 160, 160)

        self._tabla_fiat = ttk.Treeview(cont, columns=cols, show="headings",
                                         selectmode="browse")
        habilitar_deseleccion_treeview(self._tabla_fiat)
        for col, enc, ancho in zip(cols, encabs, anchos):
            self._tabla_fiat.heading(col, text=enc,
                                      command=lambda c=col: self._ordenar_fiat(c))
            self._tabla_fiat.column(col, width=ancho,
                                     anchor="w" if col == "nombre" else "center")

        self._tabla_fiat.tag_configure("par",   background="#f8f9fa")
        self._tabla_fiat.tag_configure("impar", background=BLANCO)

        sb_y = ttk.Scrollbar(cont, orient="vertical",   command=self._tabla_fiat.yview)
        sb_x = ttk.Scrollbar(cont, orient="horizontal", command=self._tabla_fiat.xview)
        self._tabla_fiat.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        self._tabla_fiat.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x.grid(row=1, column=0, sticky="ew")

        self._datos_fiat = []
        self._ord_fiat_col = "codigo"
        self._ord_fiat_asc = True

    # ══════════════════════════════════════════════════════════
    #  TAB CRIPTO
    # ══════════════════════════════════════════════════════════
    def _construir_tab_cripto(self):
        f = self._frame_cripto
        f.grid_rowconfigure(1, weight=1)
        f.grid_columnconfigure(0, weight=1)

        # Barra de controles
        barra = tk.Frame(f, bg=GRIS_FONDO)
        barra.grid(row=0, column=0, sticky="ew", padx=6, pady=6)

        tk.Label(barra, text=t("cotiz_moneda"), font=("Segoe UI", 9, "bold"),
                 bg=GRIS_FONDO).pack(side="left", padx=(8, 4))
        self.var_moneda_cripto = tk.StringVar(value="usd")
        combo_mc = ttk.Combobox(
            barra, textvariable=self.var_moneda_cripto,
            values=["usd", "eur", "brl", "ars", "gbp",
                    "jpy", "cny", "mxn", "clp", "btc"],
            width=7, state="readonly")
        combo_mc.pack(side="left", padx=(0, 4))
        combo_mc.bind("<<ComboboxSelected>>", lambda e: self._cargar_cripto())

        tk.Label(barra, text=t("cotiz_pyg_no_disponible"),
                 font=("Segoe UI", 8), bg=GRIS_FONDO, fg=GRIS_TEXT
                 ).pack(side="left", padx=(2, 8))

        tk.Frame(barra, bg=GRIS_BORDE, width=1).pack(
            side="left", fill="y", padx=8, pady=2)

        # Campo de conversión rápida
        tk.Label(barra, text="💰 Convertir:",
                 font=("Segoe UI", 9, "bold"),
                 bg=GRIS_FONDO).pack(side="left", padx=(0, 4))

        self.var_monto_cripto = tk.StringVar(value="1")
        tk.Entry(barra, textvariable=self.var_monto_cripto,
                 font=("Segoe UI", 10, "bold"), width=12,
                 justify="right").pack(side="left", ipady=3)

        self.lbl_moneda_cripto_conv = tk.Label(
            barra, text="USD", font=("Segoe UI", 9, "bold"),
            bg=GRIS_FONDO, fg=AZUL)
        self.lbl_moneda_cripto_conv.pack(side="left", padx=(4, 4))

        tk.Label(barra, text=t("cotiz_ver_col_equivalente"),
                 font=("Segoe UI", 8), bg=GRIS_FONDO,
                 fg=GRIS_TEXT).pack(side="left", padx=(0, 12))

        self.var_monto_cripto.trace_add("write",
            lambda *_: self._recalcular_equivalente_cripto())
        self.var_moneda_cripto.trace_add("write",
            lambda *_: self.lbl_moneda_cripto_conv.config(
                text=self.var_moneda_cripto.get().upper()))

        tk.Label(barra, text="🔍 Buscar:", font=("Segoe UI", 9),
                 bg=GRIS_FONDO).pack(side="left")
        self.var_busq_cripto = tk.StringVar()
        tk.Entry(barra, textvariable=self.var_busq_cripto,
                 font=("Segoe UI", 9), width=16).pack(side="left", padx=4, ipady=3)
        self.var_busq_cripto.trace_add("write", lambda *_: self._filtrar_cripto())

        self.lbl_estado_cripto = tk.Label(barra, text="", font=("Segoe UI", 8),
                                           bg=GRIS_FONDO, fg=GRIS_TEXT)
        self.lbl_estado_cripto.pack(side="right", padx=8)

        # Grilla cripto
        cont = tk.Frame(f, bg=BLANCO)
        cont.grid(row=1, column=0, sticky="nsew", padx=6)
        cont.grid_rowconfigure(0, weight=1)
        cont.grid_columnconfigure(0, weight=1)

        cols   = ("rank", "simbolo", "nombre", "precio",
                  "var24h", "marketcap", "volumen24h", "equivalente")
        encabs = (t("numero_simbolo"), t("cotiz_col_simbolo"), t("cotiz_col_nombre"), t("cotiz_col_precio"),
                  t("cotiz_col_variacion24h"), t("cotiz_col_marketcap"), t("cotiz_col_volumen24h"), t("cotiz_col_equivalente"))
        anchos = (45, 80, 180, 130, 100, 150, 150, 160)

        self._tabla_cripto = ttk.Treeview(cont, columns=cols, show="headings",
                                           selectmode="browse")
        habilitar_deseleccion_treeview(self._tabla_cripto)
        for col, enc, ancho in zip(cols, encabs, anchos):
            self._tabla_cripto.heading(col, text=enc,
                                        command=lambda c=col: self._ordenar_cripto(c))
            self._tabla_cripto.column(col, width=ancho,
                                       anchor="w" if col == "nombre" else "center")

        self._tabla_cripto.tag_configure("positivo", foreground=VERDE)
        self._tabla_cripto.tag_configure("negativo", foreground=ROJO)
        self._tabla_cripto.tag_configure("neutro",   foreground=GRIS_TEXT)

        sb_y = ttk.Scrollbar(cont, orient="vertical",   command=self._tabla_cripto.yview)
        sb_x = ttk.Scrollbar(cont, orient="horizontal", command=self._tabla_cripto.xview)
        self._tabla_cripto.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        self._tabla_cripto.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x.grid(row=1, column=0, sticky="ew")

        self._datos_cripto = []
        self._ord_cripto_col = "rank"
        self._ord_cripto_asc = True

    # ══════════════════════════════════════════════════════════
    #  ACTUALIZACIÓN DE DATOS (hilo secundario)
    # ══════════════════════════════════════════════════════════
    def _actualizar_todo(self):
        """Lanza la descarga en hilo secundario y actualiza la UI via after().
        Tkinter NO es thread-safe: NUNCA tocar widgets desde un hilo secundario.
        Toda modificación de UI se despacha al hilo principal con after()."""
        if self._job_actualizacion:
            try:
                self.after_cancel(self._job_actualizacion)
            except Exception:
                pass
        if not self.winfo_exists():
            return

        self.btn_refresh.config(state="disabled", text=t("cotiz_actualizando"))
        self.lbl_update.config(text=t("cotiz_descargando_datos"))

        # Capturar los valores de los combos ANTES de lanzar el hilo
        base_fiat   = self.var_base_fiat.get()
        vs_cripto   = self.var_moneda_cripto.get()

        def _tarea():
            # ── Fiat ──────────────────────────────────────────
            filas_fiat  = []
            error_fiat  = None
            try:
                # Intentar Frankfurter v1 (más compatible)
                url = f"https://api.frankfurter.app/latest?from={base_fiat}"
                data = _fetch_json(url)
                tasas = data.get("rates", {})
                tasas[base_fiat] = 1.0
                for cod, tasa in sorted(tasas.items()):
                    if tasa and tasa > 0:
                        filas_fiat.append({
                            "codigo":  cod,
                            "nombre":  MONEDAS_FIAT_NOMBRES.get(cod, cod),
                            "tasa":    tasa,
                            "inversa": 1.0 / tasa,
                        })
            except Exception as e:
                error_fiat = str(e)

            # ── Cripto ────────────────────────────────────────
            filas_cripto = []
            error_cripto = None
            try:
                ids = ",".join(CRIPTO_IDS_DEFAULT)
                url = (f"https://api.coingecko.com/api/v3/coins/markets"
                       f"?vs_currency={vs_cripto}&ids={ids}"
                       f"&order=market_cap_desc&per_page=50&page=1"
                       f"&sparkline=false&price_change_percentage=24h")
                data = _fetch_json(url)
                for i, c in enumerate(data, 1):
                    filas_cripto.append({
                        "rank":       i,
                        "simbolo":    c.get("symbol", "").upper(),
                        "nombre":     c.get("name", ""),
                        "precio":     c.get("current_price", 0) or 0,
                        "var24h":     c.get("price_change_percentage_24h", 0) or 0,
                        "marketcap":  c.get("market_cap", 0) or 0,
                        "volumen24h": c.get("total_volume", 0) or 0,
                        "id":         c.get("id", ""),
                    })
            except Exception as e:
                error_cripto = str(e)

            # ── Despachar actualización al hilo principal ─────
            def _ui_update():
                if not self.winfo_exists():
                    return
                # Fiat
                if filas_fiat:
                    self._datos_fiat = filas_fiat
                    self._filtrar_fiat()
                    self._tabla_fiat.heading("tasa",    text=f"1 {base_fiat} = ? MON.")
                    self._tabla_fiat.heading("inversa", text=f"1 MON. = ? {base_fiat}")
                    self.lbl_estado_fiat.config(
                        text=f"{len(filas_fiat)} monedas  •  Fuente: Frankfurter / BCE",
                        fg=GRIS_TEXT)
                elif error_fiat:
                    self.lbl_estado_fiat.config(
                        text=f"Sin conexión: {error_fiat[:60]}", fg=NARANJA)

                # Cripto
                if filas_cripto:
                    self._datos_cripto = filas_cripto
                    self._filtrar_cripto()
                    self.lbl_estado_cripto.config(
                        text=f"{len(filas_cripto)} criptos  •  Fuente: CoinGecko",
                        fg=GRIS_TEXT)
                elif error_cripto:
                    self.lbl_estado_cripto.config(
                        text=f"Sin conexión: {error_cripto[:60]}", fg=NARANJA)

                # Restaurar botón y programar próxima actualización
                ahora = datetime.datetime.now().strftime("%H:%M:%S")
                self.btn_refresh.config(state="normal", text=f"🔄 {t('actualizar')}")
                self.lbl_update.config(
                    text=f"Actualizado: {ahora}  •  Próxima en 10 min")
                self._job_actualizacion = self.after(INTERVALO_MS, self._actualizar_todo)

            # after() es thread-safe: despacha _ui_update al hilo principal
            if self.winfo_exists():
                self.after(0, _ui_update)

        threading.Thread(target=_tarea, daemon=True).start()

    def _cargar_fiat(self):
        """Recarga fiat con la base actual. Thread-safe via after()."""
        base_fiat = self.var_base_fiat.get()
        self.lbl_estado_fiat.config(text=t("cotiz_descargando"), fg=GRIS_TEXT)

        def _tarea():
            filas = []
            error = None
            try:
                url  = f"https://api.frankfurter.app/latest?from={base_fiat}"
                data = _fetch_json(url)
                tasas = data.get("rates", {})
                tasas[base_fiat] = 1.0
                for cod, tasa in sorted(tasas.items()):
                    if tasa and tasa > 0:
                        filas.append({
                            "codigo":  cod,
                            "nombre":  MONEDAS_FIAT_NOMBRES.get(cod, cod),
                            "tasa":    tasa,
                            "inversa": 1.0 / tasa,
                        })
            except Exception as e:
                error = str(e)

            def _ui():
                if not self.winfo_exists():
                    return
                if filas:
                    self._datos_fiat = filas
                    self._filtrar_fiat()
                    self._tabla_fiat.heading("tasa",    text=f"1 {base_fiat} = ? MON.")
                    self._tabla_fiat.heading("inversa", text=f"1 MON. = ? {base_fiat}")
                    self.lbl_estado_fiat.config(
                        text=f"{len(filas)} monedas  •  Fuente: Frankfurter / BCE",
                        fg=GRIS_TEXT)
                else:
                    self.lbl_estado_fiat.config(
                        text=f"Sin conexión: {(error or '')[:70]}", fg=NARANJA)

            if self.winfo_exists():
                self.after(0, _ui)

        threading.Thread(target=_tarea, daemon=True).start()

    def _cargar_cripto(self):
        """Recarga cripto con la moneda actual. Thread-safe via after()."""
        vs = self.var_moneda_cripto.get()
        self.lbl_estado_cripto.config(text=t("cotiz_descargando"), fg=GRIS_TEXT)

        def _tarea():
            filas = []
            error = None
            try:
                ids = ",".join(CRIPTO_IDS_DEFAULT)
                url = (f"https://api.coingecko.com/api/v3/coins/markets"
                       f"?vs_currency={vs}&ids={ids}"
                       f"&order=market_cap_desc&per_page=50&page=1"
                       f"&sparkline=false&price_change_percentage=24h")
                data = _fetch_json(url)
                for i, c in enumerate(data, 1):
                    filas.append({
                        "rank":       i,
                        "simbolo":    c.get("symbol", "").upper(),
                        "nombre":     c.get("name", ""),
                        "precio":     c.get("current_price", 0) or 0,
                        "var24h":     c.get("price_change_percentage_24h", 0) or 0,
                        "marketcap":  c.get("market_cap", 0) or 0,
                        "volumen24h": c.get("total_volume", 0) or 0,
                        "id":         c.get("id", ""),
                    })
            except Exception as e:
                error = str(e)

            def _ui():
                if not self.winfo_exists():
                    return
                if filas:
                    self._datos_cripto = filas
                    self._filtrar_cripto()
                    self.lbl_estado_cripto.config(
                        text=f"{len(filas)} criptos  •  Fuente: CoinGecko",
                        fg=GRIS_TEXT)
                else:
                    self.lbl_estado_cripto.config(
                        text=f"Sin conexión: {(error or '')[:70]}", fg=NARANJA)

            if self.winfo_exists():
                self.after(0, _ui)

        threading.Thread(target=_tarea, daemon=True).start()

    # ══════════════════════════════════════════════════════════
    #  FILTRADO Y POBLADO DE TABLAS
    # ══════════════════════════════════════════════════════════
    def _filtrar_fiat(self):
        texto = self.var_busq_fiat.get().lower()
        filas = [f for f in self._datos_fiat
                 if not texto or texto in f["codigo"].lower()
                 or texto in f["nombre"].lower()]
        self._poblar_fiat(filas)

    def _poblar_fiat(self, filas):
        for r in self._tabla_fiat.get_children():
            self._tabla_fiat.delete(r)
        base = self.var_base_fiat.get()

        # Parsear el monto de conversión
        try:
            monto = float(
                self.var_monto_conv.get().replace(".", "").replace(",", "."))
        except (ValueError, AttributeError):
            monto = 1.0

        for i, f in enumerate(filas):
            tag = "par" if i % 2 == 0 else "impar"
            tasa    = f["tasa"]
            inversa = f["inversa"]

            def _fmt(n):
                if n >= 1000:    return f"{n:,.2f}"
                if n >= 1:       return f"{n:,.4f}"
                return f"{n:,.6f}"

            equiv = tasa * monto
            if equiv >= 1_000_000:
                equiv_str = f"{equiv:,.2f}"
            elif equiv >= 1:
                equiv_str = f"{equiv:,.2f}"
            elif equiv >= 0.0001:
                equiv_str = f"{equiv:,.6f}"
            else:
                equiv_str = f"{equiv:.4e}"

            self._tabla_fiat.insert("", "end", values=(
                f["codigo"], f["nombre"],
                f"1 {base} = {_fmt(tasa)} {f['codigo']}",
                f"1 {f['codigo']} = {_fmt(inversa)} {base}",
                f"{monto:,.2f} {base} = {equiv_str} {f['codigo']}",
            ), tags=(tag,))

    def _recalcular_equivalente(self):
        """Recalcula la columna Equivalente con el monto actual sin recargar la API."""
        texto = self.var_busq_fiat.get().lower()
        filas = [f for f in self._datos_fiat
                 if not texto or texto in f["codigo"].lower()
                 or texto in f["nombre"].lower()]
        self._poblar_fiat(filas)

    def _filtrar_cripto(self):
        texto = self.var_busq_cripto.get().lower()
        filas = [f for f in self._datos_cripto
                 if not texto or texto in f["nombre"].lower()
                 or texto in f["simbolo"].lower()]
        self._poblar_cripto(filas)

    def _recalcular_equivalente_cripto(self):
        texto = self.var_busq_cripto.get().lower()
        filas = [f for f in self._datos_cripto
                 if not texto or texto in f["nombre"].lower()
                 or texto in f["simbolo"].lower()]
        self._poblar_cripto(filas)

    def _poblar_cripto(self, filas):
        for r in self._tabla_cripto.get_children():
            self._tabla_cripto.delete(r)
        vs = self.var_moneda_cripto.get().upper()

        try:
            monto = float(
                self.var_monto_cripto.get().replace(".", "").replace(",", "."))
        except (ValueError, AttributeError):
            monto = 1.0

        for f in filas:
            precio = f["precio"]
            var24h = f["var24h"]

            if var24h > 0:
                var_txt = f"▲ {var24h:.2f}%"
                tag = "positivo"
            elif var24h < 0:
                var_txt = f"▼ {abs(var24h):.2f}%"
                tag = "negativo"
            else:
                var_txt = f"— {var24h:.2f}%"
                tag = "neutro"

            def _fmt_precio(p):
                if p >= 1_000:    return f"{vs} {p:,.2f}"
                if p >= 1:        return f"{vs} {p:,.4f}"
                if p >= 0.0001:   return f"{vs} {p:,.6f}"
                return f"{vs} {p:.2e}"

            def _fmt_grande(n):
                if n >= 1_000_000_000: return f"{vs} {n/1_000_000_000:.2f}B"
                if n >= 1_000_000:     return f"{vs} {n/1_000_000:.2f}M"
                return f"{vs} {n:,.0f}"

            # Equivalente: monto / precio = cantidad de cripto
            # O precio * monto = monto en moneda fiat
            # El campo dice "💰 Convertir X moneda" → cuánta cripto comprás
            if precio > 0:
                cantidad_cripto = monto / precio
                if cantidad_cripto >= 1:
                    equiv_str = f"{monto:,.2f} {vs} = {cantidad_cripto:,.4f} {f['simbolo']}"
                elif cantidad_cripto >= 0.0001:
                    equiv_str = f"{monto:,.2f} {vs} = {cantidad_cripto:,.6f} {f['simbolo']}"
                else:
                    equiv_str = f"{monto:,.2f} {vs} = {cantidad_cripto:.4e} {f['simbolo']}"
            else:
                equiv_str = "—"

            self._tabla_cripto.insert("", "end", values=(
                f["rank"], f["simbolo"], f["nombre"],
                _fmt_precio(precio), var_txt,
                _fmt_grande(f["marketcap"]),
                _fmt_grande(f["volumen24h"]),
                equiv_str,
            ), tags=(tag,))

    # ══════════════════════════════════════════════════════════
    #  ORDENAMIENTO POR COLUMNA
    # ══════════════════════════════════════════════════════════
    def _ordenar_fiat(self, col):
        if self._ord_fiat_col == col:
            self._ord_fiat_asc = not self._ord_fiat_asc
        else:
            self._ord_fiat_col = col
            self._ord_fiat_asc = True
        clave = {"codigo": "codigo", "nombre": "nombre",
                 "tasa": "tasa", "inversa": "inversa"}.get(col, "codigo")
        self._datos_fiat.sort(
            key=lambda x: x.get(clave, "") or 0,
            reverse=not self._ord_fiat_asc)
        self._filtrar_fiat()

    def _ordenar_cripto(self, col):
        if self._ord_cripto_col == col:
            self._ord_cripto_asc = not self._ord_cripto_asc
        else:
            self._ord_cripto_col = col
            self._ord_cripto_asc = True
        clave = {"rank": "rank", "simbolo": "simbolo", "nombre": "nombre",
                 "precio": "precio", "var24h": "var24h",
                 "marketcap": "marketcap", "volumen24h": "volumen24h"}.get(col, "rank")
        self._datos_cripto.sort(
            key=lambda x: x.get(clave, 0) or 0,
            reverse=not self._ord_cripto_asc)
        self._filtrar_cripto()
