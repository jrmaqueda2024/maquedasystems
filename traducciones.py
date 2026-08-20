"""
traducciones.py
Diccionario de textos traducidos para la interfaz del sistema (menú
lateral, barra superior, y textos comunes compartidos por varias
pantallas). NO traduce los datos ya cargados por el usuario (nombres de
clientes, productos, observaciones, etc.) — solo los textos fijos que
vienen con el propio sistema.

Idiomas soportados: Español (por defecto), Guaraní, Português, English,
Русский (ruso), 中文 (chino simplificado), 한국어 (coreano), Українська
(ucraniano) y العربية (árabe).

Notas importantes sobre calidad y limitaciones técnicas:
  - Las traducciones al Guaraní son una primera versión hecha con buen
    criterio pero sin revisión de un hablante nativo.
  - Las traducciones a ruso, chino, coreano, ucraniano y árabe fueron
    generadas por esta misma IA, sin revisión de un hablante nativo de
    cada idioma — se recomienda que alguien nativo las revise antes de
    un uso 100% oficial, sobre todo en textos legales o de cara al
    cliente.
  - Para términos técnicos modernos sin equivalente natural en un
    idioma (Terminal SQL, Asistente IA, etc.) se optó por una traducción
    descriptiva razonable en vez de forzar un calco artificial.
  - Árabe se escribe de derecha a izquierda (RTL). Tkinter (la librería
    gráfica de este sistema) NO soporta nativamente el cambio automático
    de dirección de texto: el árabe se va a VER correctamente escrito
    letra por letra, pero alineado a la izquierda en vez de a la
    derecha, y los menús no invierten su disposición como sí lo hacen
    las apps que sí tienen soporte RTL completo (por ejemplo Windows o
    Word). Es una limitación conocida, no un error de la traducción en
    sí.
  - Chino, coreano y ruso/ucraniano (alfabeto cirílico) necesitan que
    Windows tenga instalados los paquetes de idioma/fuentes
    correspondientes para mostrarse correctamente (la mayoría de las
    instalaciones de Windows 10/11 ya los traen). Si en vez de texto se
    ven cuadros vacíos ("tofu"), hay que instalar el paquete de idioma
    correspondiente desde la Configuración de Windows.
"""

IDIOMAS = {
    "es": "Español",
    "gn": "Guaraní",
    "pt": "Português",
    "en": "English",
    "ru": "Русский",
    "zh": "中文",
    "ko": "한국어",
    "uk": "Українська",
    "ar": "العربية",
}

TEXTOS = {
    # ── Chrome general ──────────────────────────────────────────
    "app_titulo": {
        "es": "Sistema de Gestión de Ventas",
        "gn": "Atyha Ñemuha Sistema",
        "pt": "Sistema de Gestão de Vendas",
        "en": "Sales Management System",
        "ru": "Система управления продажами",
        "zh": "销售管理系统",
        "ko": "판매 관리 시스템",
        "uk": "Система управління продажами",
        "ar": "نظام إدارة المبيعات",
    },
    "cerrar_sesion": {
        "es": "Cerrar sesión", "gn": "Emboty Sesión", "pt": "Sair", "en": "Log Out",
        "ru": "Выйти", "zh": "退出登录", "ko": "로그아웃", "uk": "Вийти", "ar": "تسجيل الخروج",
    },
    "confirmar_cerrar_sesion_titulo": {
        "es": "Cerrar sesión", "gn": "Emboty Sesión", "pt": "Sair", "en": "Log Out",
        "ru": "Выйти", "zh": "退出登录", "ko": "로그아웃", "uk": "Вийти", "ar": "تسجيل الخروج",
    },
    "confirmar_cerrar_sesion_texto": {
        "es": "¿Seguro que quieres cerrar sesión?",
        "gn": "¿Reimoãpa remboty sesión?",
        "pt": "Tem certeza que deseja sair?",
        "en": "Are you sure you want to log out?",
        "ru": "Вы уверены, что хотите выйти?",
        "zh": "您确定要退出登录吗？",
        "ko": "로그아웃 하시겠습니까?",
        "uk": "Ви впевнені, що хочете вийти?",
        "ar": "هل أنت متأكد من تسجيل الخروج؟",
    },
    "admin": {
        "es": "Admin", "gn": "Admin", "pt": "Admin", "en": "Admin",
        "ru": "Админ", "zh": "管理员", "ko": "관리자", "uk": "Адмін", "ar": "مدير",
    },
    "gerente": {
        "es": "Gerente", "gn": "Sã'iha", "pt": "Gerente", "en": "Manager",
        "ru": "Менеджер", "zh": "经理", "ko": "매니저", "uk": "Менеджер", "ar": "مدير الفرع",
    },
    "vendedor": {
        "es": "Vendedor", "gn": "Ñemuhára", "pt": "Vendedor", "en": "Salesperson",
        "ru": "Продавец", "zh": "销售员", "ko": "판매원", "uk": "Продавець", "ar": "بائع",
    },

    # ── Módulos del menú lateral ─────────────────────────────────
    "modulo_ventas": {
        "es": "Ventas", "gn": "Ñemuha", "pt": "Vendas", "en": "Sales",
        "ru": "Продажи", "zh": "销售", "ko": "판매", "uk": "Продажі", "ar": "المبيعات",
    },
    "modulo_preventa": {
        "es": "Pre-Venta", "gn": "Ñemuha Mboyve", "pt": "Pré-Venda", "en": "Pre-Sale",
        "ru": "Предпродажа", "zh": "预售", "ko": "사전 판매", "uk": "Передпродаж", "ar": "البيع المسبق",
    },
    "modulo_creditos": {
        "es": "Créditos", "gn": "Créditos", "pt": "Créditos", "en": "Credits",
        "ru": "Кредиты", "zh": "信用", "ko": "신용", "uk": "Кредити", "ar": "الائتمانات",
    },
    "modulo_prestamos": {
        "es": "Préstamos", "gn": "Ame'ẽ", "pt": "Empréstimos", "en": "Loans",
        "ru": "Займы", "zh": "贷款", "ko": "대출", "uk": "Позики", "ar": "القروض",
    },
    "modulo_presupuestos": {
        "es": "Presupuestos", "gn": "Presupuesto", "pt": "Orçamentos", "en": "Quotes",
        "ru": "Сметы", "zh": "报价单", "ko": "견적", "uk": "Кошториси", "ar": "عروض الأسعار",
    },
    "modulo_productos": {
        "es": "Productos", "gn": "Mba'e", "pt": "Produtos", "en": "Products",
        "ru": "Товары", "zh": "产品", "ko": "상품", "uk": "Товари", "ar": "المنتجات",
    },
    "modulo_inventario": {
        "es": "Inventario", "gn": "Mba'e Papapy", "pt": "Estoque", "en": "Inventory",
        "ru": "Склад", "zh": "库存", "ko": "재고", "uk": "Склад", "ar": "المخزون",
    },
    "modulo_compras": {
        "es": "Compras", "gn": "Jejogua", "pt": "Compras", "en": "Purchases",
        "ru": "Закупки", "zh": "采购", "ko": "구매", "uk": "Закупівлі", "ar": "المشتريات",
    },
    "modulo_asistencia": {
        "es": "Asistencia Técnica", "gn": "Pytyvõ Técnica",
        "pt": "Assistência Técnica", "en": "Technical Support",
        "ru": "Техническая поддержка", "zh": "技术支持", "ko": "기술 지원",
        "uk": "Технічна підтримка", "ar": "الدعم الفني",
    },
    "modulo_veterinaria": {
        "es": "Veterinaria", "gn": "Mymba Rekávo", "pt": "Veterinária", "en": "Veterinary",
        "ru": "Ветеринария", "zh": "兽医", "ko": "수의학", "uk": "Ветеринарія", "ar": "بيطري",
    },
    "modulo_restaurante": {
        "es": "Restaurante/Comedor", "gn": "Karu Renda",
        "pt": "Restaurante/Refeitório", "en": "Restaurant/Diner",
        "ru": "Ресторан/Столовая", "zh": "餐厅/食堂", "ko": "레스토랑/식당",
        "uk": "Ресторан/Їдальня", "ar": "مطعم",
    },
    "modulo_streaming": {
        "es": "Alquiler de Streaming", "gn": "Streaming Alquiler",
        "pt": "Aluguel de Streaming", "en": "Streaming Rental",
        "ru": "Аренда стриминга", "zh": "流媒体租赁", "ko": "스트리밍 대여",
        "uk": "Оренда стрімінгу", "ar": "تأجير البث",
    },
    "modulo_importacion": {
        "es": "Importaciones", "gn": "Okarugua Guive Oguerúva",
        "pt": "Importações", "en": "Imports",
        "ru": "Импорт товаров", "zh": "进口商品", "ko": "수입 상품",
        "uk": "Імпорт товарів", "ar": "الواردات",
    },
    "modulo_clientes": {
        "es": "Clientes", "gn": "Cliente-kuéra", "pt": "Clientes", "en": "Clients",
        "ru": "Клиенты", "zh": "客户", "ko": "고객", "uk": "Клієнти", "ar": "العملاء",
    },
    "modulo_reportes": {
        "es": "Reportes", "gn": "Reporte", "pt": "Relatórios", "en": "Reports",
        "ru": "Отчёты", "zh": "报表", "ko": "보고서", "uk": "Звіти", "ar": "التقارير",
    },
    "modulo_cotizaciones": {
        "es": "Cotizaciones", "gn": "Viru Jehepyme'ẽ", "pt": "Cotações", "en": "Exchange Rates",
        "ru": "Курсы валют", "zh": "汇率", "ko": "환율", "uk": "Курси валют", "ar": "أسعار الصرف",
    },
    "modulo_clima": {
        "es": "Clima", "gn": "Ára", "pt": "Clima", "en": "Weather",
        "ru": "Погода", "zh": "天气", "ko": "날씨", "uk": "Погода", "ar": "الطقس",
    },
    "modulo_usuarios": {
        "es": "Usuarios", "gn": "Puruhára", "pt": "Usuários", "en": "Users",
        "ru": "Пользователи", "zh": "用户", "ko": "사용자", "uk": "Користувачі", "ar": "المستخدمون",
    },
    "modulo_rrhh": {
        "es": "Recursos Humanos", "gn": "Recursos Humanos",
        "pt": "Recursos Humanos", "en": "Human Resources",
        "ru": "Кадры (HR)", "zh": "人力资源", "ko": "인사 (HR)", "uk": "Кадри (HR)", "ar": "الموارد البشرية",
    },
    "modulo_configlocal": {
        "es": "Config. Local", "gn": "Rendaguépe Ñemboheko",
        "pt": "Config. Local", "en": "Store Settings",
        "ru": "Настройки магазина", "zh": "门店设置", "ko": "매장 설정",
        "uk": "Налаштування магазину", "ar": "إعدادات المتجر",
    },
    "modulo_licencia": {
        "es": "Licencias", "gn": "Licencia", "pt": "Licenças", "en": "Licenses",
        "ru": "Лицензии", "zh": "许可证", "ko": "라이선스", "uk": "Ліцензії", "ar": "التراخيص",
    },
    "modulo_uso": {
        "es": "Uso del sistema", "gn": "Sistema Puru", "pt": "Uso do sistema", "en": "System Usage",
        "ru": "Использование системы", "zh": "系统使用情况", "ko": "시스템 사용량",
        "uk": "Використання системи", "ar": "استخدام النظام",
    },
    "modulo_datos": {
        "es": "Gestión de Datos", "gn": "Datos Ñemongu'e", "pt": "Gestão de Dados", "en": "Data Management",
        "ru": "Управление данными", "zh": "数据管理", "ko": "데이터 관리",
        "uk": "Керування даними", "ar": "إدارة البيانات",
    },
    "modulo_terminal": {
        "es": "Terminal SQL", "gn": "Terminal SQL", "pt": "Terminal SQL", "en": "SQL Terminal",
        "ru": "SQL-терминал", "zh": "SQL终端", "ko": "SQL 터미널", "uk": "SQL-термінал", "ar": "طرفية SQL",
    },
    "modulo_ia": {
        "es": "Asistente IA", "gn": "Pytyvõhára IA", "pt": "Assistente IA", "en": "AI Assistant",
        "ru": "ИИ-помощник", "zh": "AI助手", "ko": "AI 비서", "uk": "ШІ-помічник", "ar": "مساعد الذكاء الاصطناعي",
    },
    "modulo_idioma": {
        "es": "Idioma", "gn": "Ñe'ẽ", "pt": "Idioma", "en": "Language",
        "ru": "Язык", "zh": "语言", "ko": "언어", "uk": "Мова", "ar": "اللغة",
    },
    "modulo_juegos": {
        "es": "Juegos", "gn": "Ñembosarái", "pt": "Jogos", "en": "Games",
        "ru": "Игры", "zh": "游戏", "ko": "게임", "uk": "Ігри", "ar": "الألعاب",
    },
    "modulo_biblia": {
        "es": "Biblia", "gn": "Biblia", "pt": "Bíblia", "en": "Bible",
        "ru": "Библия", "zh": "圣经", "ko": "성경", "uk": "Біблія", "ar": "الكتاب المقدس",
    },
    "modulo_novedades": {
        "es": "Novedades", "gn": "Mba'e Pyahu", "pt": "Novidades", "en": "What's New",
        "ru": "Новости", "zh": "更新日志", "ko": "업데이트 소식", "uk": "Новини", "ar": "التحديثات",
    },
    "modulo_ayuda": {
        "es": "Ayuda", "gn": "Pytyvõ", "pt": "Ajuda", "en": "Help",
        "ru": "Помощь", "zh": "帮助", "ko": "도움말", "uk": "Допомога", "ar": "مساعدة",
    },
    "modulo_reinicio": {
        "es": "Reinicio del Sistema", "gn": "Sistema Ñepyrũjey",
        "pt": "Reinício do Sistema", "en": "System Reset",
        "ru": "Сброс системы", "zh": "系统重置", "ko": "시스템 초기화",
        "uk": "Скидання системи", "ar": "إعادة تعيين النظام",
    },

    # ── Botones/acciones comunes (reutilizables en varias pantallas) ──
    "guardar": {
        "es": "Guardar", "gn": "Ñongatu", "pt": "Salvar", "en": "Save",
        "ru": "Сохранить", "zh": "保存", "ko": "저장", "uk": "Зберегти", "ar": "حفظ",
    },
    "cancelar": {
        "es": "Cancelar", "gn": "Heja", "pt": "Cancelar", "en": "Cancel",
        "ru": "Отмена", "zh": "取消", "ko": "취소", "uk": "Скасувати", "ar": "إلغاء",
    },
    "buscar": {
        "es": "Buscar", "gn": "Heka", "pt": "Buscar", "en": "Search",
        "ru": "Поиск", "zh": "搜索", "ko": "검색", "uk": "Пошук", "ar": "بحث",
    },
    "actualizar": {
        "es": "Actualizar", "gn": "Mbopyahu", "pt": "Atualizar", "en": "Refresh",
        "ru": "Обновить", "zh": "刷新", "ko": "새로고침", "uk": "Оновити", "ar": "تحديث",
    },
    "editar": {
        "es": "Editar", "gn": "Mbosako'i", "pt": "Editar", "en": "Edit",
        "ru": "Редактировать", "zh": "编辑", "ko": "편집", "uk": "Редагувати", "ar": "تعديل",
    },
    "eliminar": {
        "es": "Eliminar", "gn": "Mboguete", "pt": "Excluir", "en": "Delete",
        "ru": "Удалить", "zh": "删除", "ko": "삭제", "uk": "Видалити", "ar": "حذف",
    },
    "cerrar": {
        "es": "Cerrar", "gn": "Mboty", "pt": "Fechar", "en": "Close",
        "ru": "Закрыть", "zh": "关闭", "ko": "닫기", "uk": "Закрити", "ar": "إغلاق",
    },
    "confirmar": {
        "es": "Confirmar", "gn": "Confirmar", "pt": "Confirmar", "en": "Confirm",
        "ru": "Подтвердить", "zh": "确认", "ko": "확인", "uk": "Підтвердити", "ar": "تأكيد",
    },
    "cliente_label": {
        "es": "Cliente:", "gn": "Cliente:", "pt": "Cliente:", "en": "Client:",
        "ru": "Клиент:", "zh": "客户：", "ko": "고객:", "uk": "Клієнт:", "ar": "العميل:",
    },
    "ocasional": {
        "es": "Ocasional", "gn": "Ocasional", "pt": "Ocasional", "en": "Occasional",
        "ru": "Разовый", "zh": "临时客户", "ko": "임시 고객", "uk": "Разовий", "ar": "عارض",
    },
    "contado": {
        "es": "Contado", "gn": "Tainungára", "pt": "À Vista", "en": "Cash",
        "ru": "Наличные", "zh": "现金", "ko": "현금", "uk": "Готівка", "ar": "نقدًا",
    },
    "credito_label": {
        "es": "Crédito", "gn": "Crédito", "pt": "Crédito", "en": "Credit",
        "ru": "Кредит", "zh": "赊账", "ko": "신용", "uk": "Кредит", "ar": "بالأجل",
    },

    # ── Encabezados de columna reutilizables ──────────────────────
    "col_codigo": {
        "es": "Código", "gn": "Código", "pt": "Código", "en": "Code",
        "ru": "Код", "zh": "代码", "ko": "코드", "uk": "Код", "ar": "الرمز",
    },
    "col_descripcion": {
        "es": "Descripción", "gn": "Mba'e Rehegua", "pt": "Descrição", "en": "Description",
        "ru": "Описание", "zh": "描述", "ko": "설명", "uk": "Опис", "ar": "الوصف",
    },
    "col_precio_venta": {
        "es": "Precio Venta", "gn": "Precio Ñemuha", "pt": "Preço de Venda", "en": "Sale Price",
        "ru": "Цена продажи", "zh": "销售价格", "ko": "판매 가격", "uk": "Ціна продажу", "ar": "سعر البيع",
    },
    "col_cantidad": {
        "es": "Cant.", "gn": "Hetakue", "pt": "Qtd.", "en": "Qty.",
        "ru": "Кол-во", "zh": "数量", "ko": "수량", "uk": "К-сть", "ar": "الكمية",
    },
    "col_importe": {
        "es": "Importe", "gn": "Viru", "pt": "Valor", "en": "Amount",
        "ru": "Сумма", "zh": "金额", "ko": "금액", "uk": "Сума", "ar": "المبلغ",
    },
    "col_existencia": {
        "es": "Existencia", "gn": "Oĩva", "pt": "Estoque", "en": "Stock",
        "ru": "Наличие", "zh": "库存", "ko": "재고", "uk": "Наявність", "ar": "المخزون",
    },

    # ── Módulo Ventas (pantalla principal) ─────────────────────────
    "ventas_codigo_barra": {
        "es": "Código de Barra:", "gn": "Código de Barra:", "pt": "Código de Barras:", "en": "Barcode:",
        "ru": "Штрих-код:", "zh": "条形码：", "ko": "바코드:", "uk": "Штрих-код:", "ar": "الرمز الشريطي:",
    },
    "ventas_codigo_secundario": {
        "es": "Código Secundario:", "gn": "Código Secundario:", "pt": "Código Secundário:",
        "en": "Secondary Code:", "ru": "Дополнительный код:", "zh": "次要代码：", "ko": "보조 코드:",
        "uk": "Додатковий код:", "ar": "الرمز الثانوي:",
    },
    "ventas_agregar_producto": {
        "es": "✔ ENTER - Agregar Producto", "gn": "✔ ENTER - Embojoapy Mba'e",
        "pt": "✔ ENTER - Adicionar Produto", "en": "✔ ENTER - Add Product",
        "ru": "✔ ENTER - Добавить товар", "zh": "✔ 回车 - 添加产品", "ko": "✔ ENTER - 상품 추가",
        "uk": "✔ ENTER - Додати товар", "ar": "✔ إدخال - إضافة منتج",
    },
    "ventas_selecciona_producto": {
        "es": "Selecciona un producto de la lista para ajustar su cantidad",
        "gn": "Eiporavo peteĩ mba'e lista-gui embosako'i hag̃ua hetakue",
        "pt": "Selecione um produto da lista para ajustar a quantidade",
        "en": "Select a product from the list to adjust its quantity",
        "ru": "Выберите товар из списка, чтобы изменить количество",
        "zh": "从列表中选择一个产品以调整数量",
        "ko": "목록에서 상품을 선택하여 수량을 조정하세요",
        "uk": "Виберіть товар зі списку, щоб змінити кількість",
        "ar": "اختر منتجًا من القائمة لتعديل الكمية",
    },
    "ventas_productos_en_venta": {
        "es": "{n} Productos en la venta actual.",
        "gn": "{n} Mba'e ñemuha ko'ág̃aitépe.",
        "pt": "{n} Produtos na venda atual.",
        "en": "{n} Products in the current sale.",
        "ru": "{n} товаров в текущей продаже.",
        "zh": "当前销售中有{n}件产品。",
        "ko": "현재 판매에 {n}개 상품.",
        "uk": "{n} товарів у поточному продажі.",
        "ar": "{n} منتج في عملية البيع الحالية.",
    },
    "ventas_f12_procesar": {
        "es": "🛒 F12 - Procesar", "gn": "🛒 F12 - Ñemuha", "pt": "🛒 F12 - Processar",
        "en": "🛒 F12 - Process", "ru": "🛒 F12 - Оформить", "zh": "🛒 F12 - 处理",
        "ko": "🛒 F12 - 처리", "uk": "🛒 F12 - Оформити", "ar": "🛒 F12 - معالجة",
    },
    "ventas_ci_ruc": {
        "es": "CI/RUC:", "gn": "CI/RUC:", "pt": "CI/RUC:", "en": "ID/Tax ID:",
        "ru": "Удост./НалНомер:", "zh": "身份证/税号：", "ko": "신분증/세금ID:",
        "uk": "Посвідч./ІПН:", "ar": "الهوية/الرقم الضريبي:",
    },
    "ventas_condicion_venta": {
        "es": "Condición de Venta:", "gn": "Ñemuha Mba'éichapa:", "pt": "Condição de Venda:",
        "en": "Sale Condition:", "ru": "Условие продажи:", "zh": "销售条件：",
        "ko": "판매 조건:", "uk": "Умова продажу:", "ar": "شرط البيع:",
    },
    "ventas_tab_resumen": {
        "es": "📊  Resumen", "gn": "📊  Resumen", "pt": "📊  Resumo", "en": "📊  Summary",
        "ru": "📊  Сводка", "zh": "📊  汇总", "ko": "📊  요약", "uk": "📊  Зведення", "ar": "📊  ملخص",
    },
    "ventas_nueva_venta": {
        "es": "Nueva Venta", "gn": "Ñemuha Pyahu", "pt": "Nova Venda", "en": "New Sale",
        "ru": "Новая продажа", "zh": "新销售", "ko": "새 판매", "uk": "Новий продаж", "ar": "بيع جديد",
    },

    # ── Módulo Productos ─────────────────────────────────────────
    "activos": {
        "es": "Activos", "gn": "Oikóva", "pt": "Ativos", "en": "Active",
        "ru": "Активные", "zh": "启用", "ko": "활성", "uk": "Активні", "ar": "نشط",
    },
    "inactivos": {
        "es": "Inactivos", "gn": "Ndoikovéiva", "pt": "Inativos", "en": "Inactive",
        "ru": "Неактивные", "zh": "停用", "ko": "비활성", "uk": "Неактивні", "ar": "غير نشط",
    },
    "productos_nuevo": {
        "es": "＋ Nuevo Producto", "gn": "＋ Mba'e Pyahu", "pt": "＋ Novo Produto", "en": "＋ New Product",
        "ru": "＋ Новый товар", "zh": "＋ 新产品", "ko": "＋ 새 상품", "uk": "＋ Новий товар", "ar": "＋ منتج جديد",
    },
    "productos_categorias": {
        "es": "🏷  Categorías", "gn": "🏷  Categoría", "pt": "🏷  Categorias", "en": "🏷  Categories",
        "ru": "🏷  Категории", "zh": "🏷  类别", "ko": "🏷  카테고리", "uk": "🏷  Категорії", "ar": "🏷  الفئات",
    },
    "productos_marcas": {
        "es": "🔖  Marcas", "gn": "🔖  Marca", "pt": "🔖  Marcas", "en": "🔖  Brands",
        "ru": "🔖  Бренды", "zh": "🔖  品牌", "ko": "🔖  브랜드", "uk": "🔖  Бренди", "ar": "🔖  العلامات التجارية",
    },
    "productos_proveedores": {
        "es": "🚚  Proveedores", "gn": "🚚  Proveedor", "pt": "🚚  Fornecedores", "en": "🚚  Suppliers",
        "ru": "🚚  Поставщики", "zh": "🚚  供应商", "ko": "🚚  공급업체", "uk": "🚚  Постачальники", "ar": "🚚  الموردون",
    },
    "col_codigo_mayus": {
        "es": "CÓDIGO", "gn": "CÓDIGO", "pt": "CÓDIGO", "en": "CODE",
        "ru": "КОД", "zh": "代码", "ko": "코드", "uk": "КОД", "ar": "الرمز",
    },
    "col_descripcion_mayus": {
        "es": "DESCRIPCIÓN", "gn": "MBA'E REHEGUA", "pt": "DESCRIÇÃO", "en": "DESCRIPTION",
        "ru": "ОПИСАНИЕ", "zh": "描述", "ko": "설명", "uk": "ОПИС", "ar": "الوصف",
    },
    "col_marca": {
        "es": "MARCA", "gn": "MARCA", "pt": "MARCA", "en": "BRAND",
        "ru": "БРЕНД", "zh": "品牌", "ko": "브랜드", "uk": "БРЕНД", "ar": "العلامة التجارية",
    },
    "col_p_compra": {
        "es": "P. COMPRA", "gn": "P. JOGUA", "pt": "P. COMPRA", "en": "PURCH. PRICE",
        "ru": "ЦЕНА ЗАКУПКИ", "zh": "进货价", "ko": "구매가", "uk": "ЦІНА ЗАКУПІВЛІ", "ar": "سعر الشراء",
    },
    "col_p_venta": {
        "es": "P. VENTA", "gn": "P. ÑEMUHA", "pt": "P. VENDA", "en": "SALE PRICE",
        "ru": "ЦЕНА ПРОДАЖИ", "zh": "售价", "ko": "판매가", "uk": "ЦІНА ПРОДАЖУ", "ar": "سعر البيع",
    },
    "col_p_credito": {
        "es": "P. CRÉDITO", "gn": "P. CRÉDITO", "pt": "P. CRÉDITO", "en": "CREDIT PRICE",
        "ru": "ЦЕНА В КРЕДИТ", "zh": "赊账价", "ko": "신용가", "uk": "ЦІНА В КРЕДИТ", "ar": "سعر بالأجل",
    },
    "col_p_mayorista": {
        "es": "P. MAYORISTA", "gn": "P. MAYORISTA", "pt": "P. ATACADO", "en": "WHOLESALE PRICE",
        "ru": "ОПТОВАЯ ЦЕНА", "zh": "批发价", "ko": "도매가", "uk": "ОПТОВА ЦІНА", "ar": "سعر الجملة",
    },
    "col_stock_mayus": {
        "es": "STOCK", "gn": "STOCK", "pt": "ESTOQUE", "en": "STOCK",
        "ru": "ОСТАТОК", "zh": "库存", "ko": "재고", "uk": "ЗАЛИШОК", "ar": "المخزون",
    },
    "col_comprometido": {
        "es": "COMPROMETIDO", "gn": "OME'ẼMBYRE", "pt": "COMPROMETIDO", "en": "COMMITTED",
        "ru": "ЗАРЕЗЕРВИРОВАНО", "zh": "已预留", "ko": "예약됨", "uk": "ЗАРЕЗЕРВОВАНО", "ar": "محجوز",
    },
    "col_disponible": {
        "es": "DISPONIBLE", "gn": "OĨVA", "pt": "DISPONÍVEL", "en": "AVAILABLE",
        "ru": "ДОСТУПНО", "zh": "可用", "ko": "사용 가능", "uk": "ДОСТУПНО", "ar": "متاح",
    },
    "col_adjunto": {
        "es": "ADJUNTO", "gn": "MOĨNGE", "pt": "ANEXO", "en": "ATTACHMENT",
        "ru": "ВЛОЖЕНИЕ", "zh": "附件", "ko": "첨부", "uk": "ВКЛАДЕННЯ", "ar": "المرفق",
    },

    # ── Módulo Inventario ────────────────────────────────────────
    "inv_mostrar_bajo_stock": {
        "es": "⚠ Mostrar Productos Bajos en Inventario", "gn": "⚠ Ehechauka Mba'e Sy'a",
        "pt": "⚠ Mostrar Produtos com Estoque Baixo", "en": "⚠ Show Low Stock Products",
        "ru": "⚠ Показать товары с низким остатком", "zh": "⚠ 显示低库存产品",
        "ko": "⚠ 재고 부족 상품 표시", "uk": "⚠ Показати товари з низьким залишком",
        "ar": "⚠ عرض المنتجات منخفضة المخزون",
    },
    "inv_volver_todos": {
        "es": "✅ Volver a Todos los Productos", "gn": "✅ Jevy Mba'e Paite",
        "pt": "✅ Voltar a Todos os Produtos", "en": "✅ Back to All Products",
        "ru": "✅ Вернуться ко всем товарам", "zh": "✅ 返回所有产品",
        "ko": "✅ 전체 상품으로 돌아가기", "uk": "✅ Повернутися до всіх товарів",
        "ar": "✅ العودة إلى جميع المنتجات",
    },
    "inv_mostrar_con_stock": {
        "es": "📦 Mostrar Solamente Productos en Stock", "gn": "📦 Ehechauka Mba'e Oĩva",
        "pt": "📦 Mostrar Apenas Produtos em Estoque", "en": "📦 Show Only Products In Stock",
        "ru": "📦 Показать только товары в наличии", "zh": "📦 仅显示有库存的产品",
        "ko": "📦 재고 있는 상품만 표시", "uk": "📦 Показати лише товари в наявності",
        "ar": "📦 عرض المنتجات المتوفرة فقط",
    },
    "inv_volver_activos": {
        "es": "✅ Volver a Productos Activos", "gn": "✅ Jevy Mba'e Oikóva",
        "pt": "✅ Voltar a Produtos Ativos", "en": "✅ Back to Active Products",
        "ru": "✅ Вернуться к активным товарам", "zh": "✅ 返回启用的产品",
        "ko": "✅ 활성 상품으로 돌아가기", "uk": "✅ Повернутися до активних товарів",
        "ar": "✅ العودة إلى المنتجات النشطة",
    },
    "inv_mostrar_inactivos": {
        "es": "🚫 Mostrar Productos Inactivos", "gn": "🚫 Ehechauka Mba'e Ndoikovéiva",
        "pt": "🚫 Mostrar Produtos Inativos", "en": "🚫 Show Inactive Products",
        "ru": "🚫 Показать неактивные товары", "zh": "🚫 显示停用产品",
        "ko": "🚫 비활성 상품 표시", "uk": "🚫 Показати неактивні товари",
        "ar": "🚫 عرض المنتجات غير النشطة",
    },
    "inv_ocultar_resumen": {
        "es": "🙈 Ocultar Resumen", "gn": "🙈 Ñomi Resumen", "pt": "🙈 Ocultar Resumo",
        "en": "🙈 Hide Summary", "ru": "🙈 Скрыть сводку", "zh": "🙈 隐藏汇总",
        "ko": "🙈 요약 숨기기", "uk": "🙈 Приховати зведення", "ar": "🙈 إخفاء الملخص",
    },
    "inv_mostrar_resumen": {
        "es": "👁 Mostrar Resumen", "gn": "👁 Ehechauka Resumen", "pt": "👁 Mostrar Resumo",
        "en": "👁 Show Summary", "ru": "👁 Показать сводку", "zh": "👁 显示汇总",
        "ko": "👁 요약 표시", "uk": "👁 Показати зведення", "ar": "👁 عرض الملخص",
    },
    "inv_buscar_ctrl_b": {
        "es": "🔎 Buscar (Ctrl+B):", "gn": "🔎 Heka (Ctrl+B):", "pt": "🔎 Buscar (Ctrl+B):",
        "en": "🔎 Search (Ctrl+B):", "ru": "🔎 Поиск (Ctrl+B):", "zh": "🔎 搜索 (Ctrl+B)：",
        "ko": "🔎 검색 (Ctrl+B):", "uk": "🔎 Пошук (Ctrl+B):", "ar": "🔎 بحث (Ctrl+B):",
    },
    "col_proveedor": {
        "es": "PROVEEDOR", "gn": "PROVEEDOR", "pt": "FORNECEDOR", "en": "SUPPLIER",
        "ru": "ПОСТАВЩИК", "zh": "供应商", "ko": "공급업체", "uk": "ПОСТАЧАЛЬНИК", "ar": "المورد",
    },
    "col_precio_compra_mayus": {
        "es": "PRECIO COMPRA", "gn": "PRECIO JOGUA", "pt": "PREÇO DE COMPRA", "en": "PURCHASE PRICE",
        "ru": "ЦЕНА ЗАКУПКИ", "zh": "进货价", "ko": "구매 가격", "uk": "ЦІНА ЗАКУПІВЛІ", "ar": "سعر الشراء",
    },
    "col_precio_venta_mayus": {
        "es": "PRECIO VENTA", "gn": "PRECIO ÑEMUHA", "pt": "PREÇO DE VENDA", "en": "SALE PRICE",
        "ru": "ЦЕНА ПРОДАЖИ", "zh": "销售价", "ko": "판매 가격", "uk": "ЦІНА ПРОДАЖУ", "ar": "سعر البيع",
    },
    "inv_resumen_titulo": {
        "es": "Resumen de Inventario", "gn": "Mba'e Papapy Resumen", "pt": "Resumo do Estoque",
        "en": "Inventory Summary", "ru": "Сводка по складу", "zh": "库存汇总",
        "ko": "재고 요약", "uk": "Зведення по складу", "ar": "ملخص المخزون",
    },
    "col_precio_mayorista_mayus": {
        "es": "PRECIO MAYORISTA", "gn": "PRECIO MAYORISTA", "pt": "PREÇO ATACADO", "en": "WHOLESALE PRICE",
        "ru": "ОПТОВАЯ ЦЕНА", "zh": "批发价", "ko": "도매 가격", "uk": "ОПТОВА ЦІНА", "ar": "سعر الجملة",
    },
    "col_stock_minimo": {
        "es": "STOCK MÍNIMO", "gn": "STOCK MÍNIMO", "pt": "ESTOQUE MÍNIMO", "en": "MINIMUM STOCK",
        "ru": "МИН. ОСТАТОК", "zh": "最低库存", "ko": "최소 재고", "uk": "МІН. ЗАЛИШОК", "ar": "الحد الأدنى للمخزون",
    },

    # ── Módulo Clientes ──────────────────────────────────────────
    "clientes_nuevo": {
        "es": "＋ Nuevo Cliente", "gn": "＋ Cliente Pyahu", "pt": "＋ Novo Cliente", "en": "＋ New Client",
        "ru": "＋ Новый клиент", "zh": "＋ 新客户", "ko": "＋ 새 고객", "uk": "＋ Новий клієнт", "ar": "＋ عميل جديد",
    },
    "editar_boton": {
        "es": "✏ Editar", "gn": "✏ Mbosako'i", "pt": "✏ Editar", "en": "✏ Edit",
        "ru": "✏ Редактировать", "zh": "✏ 编辑", "ko": "✏ 편집", "uk": "✏ Редагувати", "ar": "✏ تعديل",
    },
    "eliminar_boton": {
        "es": "🗑 Eliminar", "gn": "🗑 Mboguete", "pt": "🗑 Excluir", "en": "🗑 Delete",
        "ru": "🗑 Удалить", "zh": "🗑 删除", "ko": "🗑 삭제", "uk": "🗑 Видалити", "ar": "🗑 حذف",
    },
    "col_codigo_cap": {
        "es": "Código", "gn": "Código", "pt": "Código", "en": "Code",
        "ru": "Код", "zh": "代码", "ko": "코드", "uk": "Код", "ar": "الرمز",
    },
    "col_nombre": {
        "es": "Nombre", "gn": "Téra", "pt": "Nome", "en": "Name",
        "ru": "Имя", "zh": "姓名", "ko": "이름", "uk": "Ім'я", "ar": "الاسم",
    },
    "col_razon_social": {
        "es": "Razón Social", "gn": "Razón Social", "pt": "Razão Social", "en": "Business Name",
        "ru": "Юр. название", "zh": "公司名称", "ko": "상호명", "uk": "Юр. назва", "ar": "الاسم التجاري",
    },
    "col_documento": {
        "es": "N° Documento", "gn": "N° Documento", "pt": "N° Documento", "en": "ID Number",
        "ru": "Номер документа", "zh": "证件号码", "ko": "문서 번호", "uk": "Номер документа", "ar": "رقم الوثيقة",
    },
    "col_direccion": {
        "es": "Dirección", "gn": "Oĩha", "pt": "Endereço", "en": "Address",
        "ru": "Адрес", "zh": "地址", "ko": "주소", "uk": "Адреса", "ar": "العنوان",
    },
    "col_telefono": {
        "es": "Teléfono", "gn": "Pumbyry", "pt": "Telefone", "en": "Phone",
        "ru": "Телефон", "zh": "电话", "ko": "전화", "uk": "Телефон", "ar": "الهاتف",
    },
    "clientes_seleccion_detalle": {
        "es": "Selecciona un cliente\npara ver su detalle",
        "gn": "Eiporavo peteĩ cliente\neheka hag̃ua hetakue",
        "pt": "Selecione um cliente\npara ver seu detalhe",
        "en": "Select a client\nto see their details",
        "ru": "Выберите клиента,\nчтобы увидеть детали",
        "zh": "选择一个客户\n查看详情",
        "ko": "고객을 선택하면\n상세정보가 표시됩니다",
        "uk": "Виберіть клієнта,\nщоб побачити деталі",
        "ar": "اختر عميلًا\nلعرض التفاصيل",
    },
    "clientes_resumen": {
        "es": "RESUMEN", "gn": "RESUMEN", "pt": "RESUMO", "en": "SUMMARY",
        "ru": "СВОДКА", "zh": "汇总", "ko": "요약", "uk": "ЗВЕДЕННЯ", "ar": "ملخص",
    },
    "clientes_historial_compras": {
        "es": "HISTORIAL DE COMPRAS", "gn": "JOGUA REKO ÁRA", "pt": "HISTÓRICO DE COMPRAS",
        "en": "PURCHASE HISTORY", "ru": "ИСТОРИЯ ПОКУПОК", "zh": "购买历史",
        "ko": "구매 내역", "uk": "ІСТОРІЯ ПОКУПОК", "ar": "سجل المشتريات",
    },
    "col_fecha": {
        "es": "Fecha", "gn": "Ára", "pt": "Data", "en": "Date",
        "ru": "Дата", "zh": "日期", "ko": "날짜", "uk": "Дата", "ar": "التاريخ",
    },
    "col_total": {
        "es": "Total", "gn": "Manterei", "pt": "Total", "en": "Total",
        "ru": "Итого", "zh": "总计", "ko": "합계", "uk": "Разом", "ar": "الإجمالي",
    },
    "col_estado": {
        "es": "Estado", "gn": "Mba'éichapa", "pt": "Status", "en": "Status",
        "ru": "Статус", "zh": "状态", "ko": "상태", "uk": "Статус", "ar": "الحالة",
    },
    "clientes_sin_compras": {
        "es": "Sin compras registradas todavía.", "gn": "Ndaipóri jogua ojehaíva gueteri.",
        "pt": "Nenhuma compra registrada ainda.", "en": "No purchases recorded yet.",
        "ru": "Пока нет зарегистрированных покупок.", "zh": "尚无购买记录。",
        "ko": "아직 등록된 구매가 없습니다.", "uk": "Ще немає зареєстрованих покупок.",
        "ar": "لا توجد مشتريات مسجلة بعد.",
    },

    # ── Módulo Compras ───────────────────────────────────────────
    "compras_nueva": {
        "es": "🛒 Nueva Compra", "gn": "🛒 Jejogua Pyahu", "pt": "🛒 Nova Compra", "en": "🛒 New Purchase",
        "ru": "🛒 Новая закупка", "zh": "🛒 新采购", "ko": "🛒 새 구매", "uk": "🛒 Нова закупівля", "ar": "🛒 شراء جديد",
    },
    "col_fecha_hora": {
        "es": "FECHA Y HORA", "gn": "ÁRA HA ARY'I", "pt": "DATA E HORA", "en": "DATE AND TIME",
        "ru": "ДАТА И ВРЕМЯ", "zh": "日期和时间", "ko": "날짜 및 시간", "uk": "ДАТА І ЧАС", "ar": "التاريخ والوقت",
    },
    "compras_fecha_compra": {
        "es": "FECHA COMPRA", "gn": "ÁRA JOGUA", "pt": "DATA DA COMPRA", "en": "PURCHASE DATE",
        "ru": "ДАТА ЗАКУПКИ", "zh": "采购日期", "ko": "구매 날짜", "uk": "ДАТА ЗАКУПІВЛІ", "ar": "تاريخ الشراء",
    },
    "compras_nro_comprobante": {
        "es": "NRO. COMPROBANTE", "gn": "NRO. COMPROBANTE", "pt": "N° COMPROVANTE", "en": "RECEIPT NO.",
        "ru": "№ ЧЕКА", "zh": "凭证号", "ko": "영수증 번호", "uk": "№ ЧЕКА", "ar": "رقم الإيصال",
    },
    "col_proveedor_mayus": {
        "es": "PROVEEDOR", "gn": "PROVEEDOR", "pt": "FORNECEDOR", "en": "SUPPLIER",
        "ru": "ПОСТАВЩИК", "zh": "供应商", "ko": "공급업체", "uk": "ПОСТАЧАЛЬНИК", "ar": "المورد",
    },
    "col_importe_mayus": {
        "es": "IMPORTE", "gn": "VIRU", "pt": "VALOR", "en": "AMOUNT",
        "ru": "СУММА", "zh": "金额", "ko": "금액", "uk": "СУМА", "ar": "المبلغ",
    },
    "col_cantidad_cap": {
        "es": "Cantidad", "gn": "Hetakue", "pt": "Quantidade", "en": "Quantity",
        "ru": "Количество", "zh": "数量", "ko": "수량", "uk": "Кількість", "ar": "الكمية",
    },
    "col_precio_unit": {
        "es": "Precio Unit.", "gn": "Precio Peteĩ", "pt": "Preço Unit.", "en": "Unit Price",
        "ru": "Цена за ед.", "zh": "单价", "ko": "단가", "uk": "Ціна за од.", "ar": "سعر الوحدة",
    },
    "col_importe_cap": {
        "es": "Importe", "gn": "Viru", "pt": "Valor", "en": "Amount",
        "ru": "Сумма", "zh": "金额", "ko": "금액", "uk": "Сума", "ar": "المبلغ",
    },
    "total_label": {
        "es": "Total:", "gn": "Manterei:", "pt": "Total:", "en": "Total:",
        "ru": "Итого:", "zh": "总计：", "ko": "합계:", "uk": "Разом:", "ar": "الإجمالي:",
    },

    # ── Módulo Créditos ──────────────────────────────────────────
    "creditos_estado_cuenta": {
        "es": "📄 Estado de\nCuenta", "gn": "📄 Estado de\nCuenta", "pt": "📄 Extrato de\nConta",
        "en": "📄 Account\nStatement", "ru": "📄 Выписка по\nсчёту", "zh": "📄 账户\n对账单",
        "ko": "📄 계정\n명세서", "uk": "📄 Виписка по\nрахунку", "ar": "📄 كشف\nالحساب",
    },
    "creditos_agrupar_cliente": {
        "es": "👥 Agrupar por\nCliente", "gn": "👥 Agrupar por\nCliente", "pt": "👥 Agrupar por\nCliente",
        "en": "👥 Group by\nClient", "ru": "👥 Группировать по\nклиенту", "zh": "👥 按客户\n分组",
        "ko": "👥 고객별\n그룹화", "uk": "👥 Групувати за\nклієнтом", "ar": "👥 تجميع حسب\nالعميل",
    },
    "creditos_agrupar_venta": {
        "es": "👥 Agrupar por\nVenta", "gn": "👥 Agrupar por\nÑemuha", "pt": "👥 Agrupar por\nVenda",
        "en": "👥 Group by\nSale", "ru": "👥 Группировать по\nпродаже", "zh": "👥 按销售\n分组",
        "ko": "👥 판매별\n그룹화", "uk": "👥 Групувати за\nпродажем", "ar": "👥 تجميع حسب\nالبيع",
    },
    "creditos_mostrar_resumen": {
        "es": "👁 Mostrar Resumen", "gn": "👁 Ehechauka Resumen", "pt": "👁 Mostrar Resumo",
        "en": "👁 Show Summary", "ru": "👁 Показать сводку", "zh": "👁 显示汇总",
        "ko": "👁 요약 표시", "uk": "👁 Показати зведення", "ar": "👁 عرض الملخص",
    },
    "creditos_ocultar_resumen": {
        "es": "🕶 Ocultar Resumen", "gn": "🕶 Ñomi Resumen", "pt": "🕶 Ocultar Resumo",
        "en": "🕶 Hide Summary", "ru": "🕶 Скрыть сводку", "zh": "🕶 隐藏汇总",
        "ko": "🕶 요약 숨기기", "uk": "🕶 Приховати зведення", "ar": "🕶 إخفاء الملخص",
    },
    "creditos_mostrar_pendientes": {
        "es": "Mostrar Pendientes", "gn": "Ehechauka Ojehepyme'ẽva'erã",
        "pt": "Mostrar Pendentes", "en": "Show Pending",
        "ru": "Показать неоплаченные", "zh": "显示未结清",
        "ko": "미결제 표시", "uk": "Показати неоплачені", "ar": "عرض المعلقة",
    },
    "creditos_mostrar_todos": {
        "es": "Mostrar Todos", "gn": "Ehechauka Opavave", "pt": "Mostrar Todos", "en": "Show All",
        "ru": "Показать все", "zh": "显示全部", "ko": "전체 표시", "uk": "Показати всі", "ar": "عرض الكل",
    },
    "col_cod_cliente": {
        "es": "CÓD. CLIENTE", "gn": "CÓD. CLIENTE", "pt": "CÓD. CLIENTE", "en": "CLIENT CODE",
        "ru": "КОД КЛИЕНТА", "zh": "客户代码", "ko": "고객 코드", "uk": "КОД КЛІЄНТА", "ar": "رمز العميل",
    },
    "col_nombre_cliente": {
        "es": "NOMBRE CLIENTE", "gn": "TÉRA CLIENTE", "pt": "NOME CLIENTE", "en": "CLIENT NAME",
        "ru": "ИМЯ КЛИЕНТА", "zh": "客户姓名", "ko": "고객 이름", "uk": "ІМ'Я КЛІЄНТА", "ar": "اسم العميل",
    },
    "creditos_deuda_total": {
        "es": "DEUDA TOTAL", "gn": "MYENYHẼ MANTEREI", "pt": "DÍVIDA TOTAL", "en": "TOTAL DEBT",
        "ru": "ОБЩИЙ ДОЛГ", "zh": "总欠款", "ko": "총 부채", "uk": "ЗАГАЛЬНИЙ БОРГ", "ar": "إجمالي الدين",
    },
    "creditos_pagado": {
        "es": "PAGADO", "gn": "OJEHEPYME'Ẽ MA", "pt": "PAGO", "en": "PAID",
        "ru": "ОПЛАЧЕНО", "zh": "已付", "ko": "지불됨", "uk": "СПЛАЧЕНО", "ar": "مدفوع",
    },
    "creditos_saldo": {
        "es": "SALDO", "gn": "SALDO", "pt": "SALDO", "en": "BALANCE",
        "ru": "ОСТАТОК", "zh": "余额", "ko": "잔액", "uk": "ЗАЛИШОК", "ar": "الرصيد",
    },
    "creditos_credito_num": {
        "es": "CRÉDITO N°", "gn": "CRÉDITO N°", "pt": "CRÉDITO N°", "en": "CREDIT NO.",
        "ru": "КРЕДИТ №", "zh": "赊账编号", "ko": "신용 번호", "uk": "КРЕДИТ №", "ar": "رقم الائتمان",
    },
    "col_fecha_mayus": {
        "es": "FECHA", "gn": "ÁRA", "pt": "DATA", "en": "DATE",
        "ru": "ДАТА", "zh": "日期", "ko": "날짜", "uk": "ДАТА", "ar": "التاريخ",
    },
    "col_cliente_mayus": {
        "es": "CLIENTE", "gn": "CLIENTE", "pt": "CLIENTE", "en": "CLIENT",
        "ru": "КЛИЕНТ", "zh": "客户", "ko": "고객", "uk": "КЛІЄНТ", "ar": "العميل",
    },
    "creditos_fecha_venc": {
        "es": "FECHA VENC.", "gn": "ÁRA OPÁTA", "pt": "DATA VENC.", "en": "DUE DATE",
        "ru": "СРОК ОПЛАТЫ", "zh": "到期日", "ko": "만기일", "uk": "ТЕРМІН СПЛАТИ", "ar": "تاريخ الاستحقاق",
    },
    "col_descripcion_mayus2": {
        "es": "DESCRIPCIÓN", "gn": "MBA'E REHEGUA", "pt": "DESCRIÇÃO", "en": "DESCRIPTION",
        "ru": "ОПИСАНИЕ", "zh": "描述", "ko": "설명", "uk": "ОПИС", "ar": "الوصف",
    },
    "creditos_resumen_titulo": {
        "es": "Resumen de Créditos", "gn": "Créditos Resumen", "pt": "Resumo de Créditos",
        "en": "Credit Summary", "ru": "Сводка по кредитам", "zh": "赊账汇总",
        "ko": "신용 요약", "uk": "Зведення по кредитах", "ar": "ملخص الائتمان",
    },
    "creditos_total_pendientes": {
        "es": "Total Ventas Créditos Pendientes", "gn": "Total Ñemuha Créditos Ojehepyme'ẽva'erã",
        "pt": "Total Vendas Créditos Pendentes", "en": "Total Pending Credit Sales",
        "ru": "Всего неоплаченных продаж в кредит", "zh": "待处理赊账销售总额",
        "ko": "총 미결제 신용 판매", "uk": "Всього неоплачених продажів у кредит",
        "ar": "إجمالي مبيعات الائتمان المعلقة",
    },
    "creditos_total_pendiente_pago": {
        "es": "Total Crédito Pendientes Pago", "gn": "Total Crédito Ojehepyme'ẽva'erã",
        "pt": "Total Crédito Pendente Pagamento", "en": "Total Credit Pending Payment",
        "ru": "Общая сумма к оплате по кредиту", "zh": "待付款赊账总额",
        "ko": "총 미결제 신용 금액", "uk": "Загальна сума до оплати по кредиту",
        "ar": "إجمالي الائتمان المستحق الدفع",
    },
    "creditos_historial_pagos": {
        "es": "Historial de pagos", "gn": "Jehepyme'ẽ Ára", "pt": "Histórico de pagamentos",
        "en": "Payment history", "ru": "История платежей", "zh": "付款历史",
        "ko": "결제 내역", "uk": "Історія платежів", "ar": "سجل الدفعات",
    },
    "col_monto": {
        "es": "Monto", "gn": "Viru", "pt": "Valor", "en": "Amount",
        "ru": "Сумма", "zh": "金额", "ko": "금액", "uk": "Сума", "ar": "المبلغ",
    },
    "creditos_sin_pagos": {
        "es": "Todavía no se registró ningún pago para este crédito.",
        "gn": "Ndaipóri jehepyme'ẽ ojehaíva gueteri ko crédito-pe.",
        "pt": "Ainda não foi registrado nenhum pagamento para este crédito.",
        "en": "No payment has been recorded for this credit yet.",
        "ru": "По этому кредиту ещё не зарегистрировано ни одного платежа.",
        "zh": "此赊账尚无任何付款记录。",
        "ko": "이 신용에 대해 아직 등록된 결제가 없습니다.",
        "uk": "За цим кредитом ще не зареєстровано жодного платежу.",
        "ar": "لم يتم تسجيل أي دفعة لهذا الائتمان بعد.",
    },
    "creditos_monto_a_pagar": {
        "es": "Monto a pagar:", "gn": "Viru ojehepyme'ẽva:", "pt": "Valor a pagar:",
        "en": "Amount to pay:", "ru": "Сумма к оплате:", "zh": "应付金额：",
        "ko": "지불할 금액:", "uk": "Сума до сплати:", "ar": "المبلغ المستحق:",
    },
    "creditos_pagar_saldo_total": {
        "es": "Pagar Saldo Total", "gn": "Hepyme'ẽ Saldo Manterei", "pt": "Pagar Saldo Total",
        "en": "Pay Full Balance", "ru": "Оплатить весь остаток", "zh": "支付全部余额",
        "ko": "전체 잔액 지불", "uk": "Сплатити весь залишок", "ar": "دفع الرصيد بالكامل",
    },
    "creditos_registrar_pago": {
        "es": "✔ Registrar Pago", "gn": "✔ Ñemongu'e Jehepyme'ẽ", "pt": "✔ Registrar Pagamento",
        "en": "✔ Record Payment", "ru": "✔ Зарегистрировать платёж", "zh": "✔ 登记付款",
        "ko": "✔ 결제 등록", "uk": "✔ Зареєструвати платіж", "ar": "✔ تسجيل الدفعة",
    },
    "creditos_ya_saldado": {
        "es": "✔ Este crédito ya está saldado por completo.",
        "gn": "✔ Ko crédito ohepyme'ẽ mba'e paite ma.",
        "pt": "✔ Este crédito já está totalmente quitado.",
        "en": "✔ This credit is already fully paid off.",
        "ru": "✔ Этот кредит уже полностью погашен.",
        "zh": "✔ 此赊账已全部结清。",
        "ko": "✔ 이 신용은 이미 완전히 상환되었습니다.",
        "uk": "✔ Цей кредит уже повністю погашено.",
        "ar": "✔ تم سداد هذا الائتمان بالكامل بالفعل.",
    },
    "creditos_sin_creditos_cliente": {
        "es": "Este cliente no tiene créditos registrados.",
        "gn": "Ko cliente ndorekói créditos ojehaíva.",
        "pt": "Este cliente não tem créditos registrados.",
        "en": "This client has no credits on record.",
        "ru": "У этого клиента нет зарегистрированных кредитов.",
        "zh": "该客户没有已登记的赊账。",
        "ko": "이 고객은 등록된 신용이 없습니다.",
        "uk": "У цього клієнта немає зареєстрованих кредитів.",
        "ar": "لا يوجد ائتمان مسجل لهذا العميل.",
    },
    "numero_simbolo": {
        "es": "N°", "gn": "N°", "pt": "N°", "en": "No.",
        "ru": "№", "zh": "编号", "ko": "번호", "uk": "№", "ar": "الرقم",
    },
    "vencimiento_label": {
        "es": "Vencimiento", "gn": "Opáta Ára", "pt": "Vencimento", "en": "Due Date",
        "ru": "Срок оплаты", "zh": "到期日", "ko": "만기일", "uk": "Термін сплати", "ar": "تاريخ الاستحقاق",
    },
    "factura_label": {
        "es": "Factura", "gn": "Factura", "pt": "Fatura", "en": "Invoice",
        "ru": "Счёт-фактура", "zh": "发票", "ko": "청구서", "uk": "Рахунок-фактура", "ar": "الفاتورة",
    },
    "deuda_label": {
        "es": "Deuda", "gn": "Myenyhẽ", "pt": "Dívida", "en": "Debt",
        "ru": "Долг", "zh": "欠款", "ko": "부채", "uk": "Борг", "ar": "الدين",
    },
    "pagado_cap": {
        "es": "Pagado", "gn": "Ojehepyme'ẽ ma", "pt": "Pago", "en": "Paid",
        "ru": "Оплачено", "zh": "已付", "ko": "지불됨", "uk": "Сплачено", "ar": "مدفوع",
    },
    "saldo_cap": {
        "es": "Saldo", "gn": "Saldo", "pt": "Saldo", "en": "Balance",
        "ru": "Остаток", "zh": "余额", "ko": "잔액", "uk": "Залишок", "ar": "الرصيد",
    },

    # ── Módulo Presupuestos ──────────────────────────────────────
    "presup_nuevo": {
        "es": "➕ Nuevo Presupuesto", "gn": "➕ Presupuesto Pyahu", "pt": "➕ Novo Orçamento",
        "en": "➕ New Quote", "ru": "➕ Новая смета", "zh": "➕ 新报价单",
        "ko": "➕ 새 견적", "uk": "➕ Новий кошторис", "ar": "➕ عرض سعر جديد",
    },
    "presup_generar_pdf": {
        "es": "📄 Generar PDF", "gn": "📄 Mongu'e PDF", "pt": "📄 Gerar PDF", "en": "📄 Generate PDF",
        "ru": "📄 Создать PDF", "zh": "📄 生成PDF", "ko": "📄 PDF 생성", "uk": "📄 Створити PDF", "ar": "📄 إنشاء PDF",
    },
    "estado_label": {
        "es": "Estado:", "gn": "Mba'éichapa:", "pt": "Status:", "en": "Status:",
        "ru": "Статус:", "zh": "状态：", "ko": "상태:", "uk": "Статус:", "ar": "الحالة:",
    },
    "presup_col_valido_hasta": {
        "es": "VÁLIDO HASTA", "gn": "OĨVA'ERÃ", "pt": "VÁLIDO ATÉ", "en": "VALID UNTIL",
        "ru": "ДЕЙСТВИТЕЛЕН ДО", "zh": "有效期至", "ko": "유효 기간", "uk": "ДІЙСНИЙ ДО", "ar": "صالح حتى",
    },
    "col_estado_mayus": {
        "es": "ESTADO", "gn": "MBA'ÉICHAPA", "pt": "STATUS", "en": "STATUS",
        "ru": "СТАТУС", "zh": "状态", "ko": "상태", "uk": "СТАТУС", "ar": "الحالة",
    },
    "col_total_mayus": {
        "es": "TOTAL", "gn": "MANTEREI", "pt": "TOTAL", "en": "TOTAL",
        "ru": "ИТОГО", "zh": "总计", "ko": "합계", "uk": "РАЗОМ", "ar": "الإجمالي",
    },
    "col_vendedor_mayus": {
        "es": "VENDEDOR", "gn": "ÑEMUHÁRA", "pt": "VENDEDOR", "en": "SALESPERSON",
        "ru": "ПРОДАВЕЦ", "zh": "销售员", "ko": "판매원", "uk": "ПРОДАВЕЦЬ", "ar": "البائع",
    },
    "presup_generar_pdf_boton": {
        "es": "📄 Generar PDF", "gn": "📄 Mongu'e PDF", "pt": "📄 Gerar PDF", "en": "📄 Generate PDF",
        "ru": "📄 Создать PDF", "zh": "📄 生成PDF", "ko": "📄 PDF 생성", "uk": "📄 Створити PDF", "ar": "📄 إنشاء PDF",
    },
    "presup_editar": {
        "es": "✏ Editar", "gn": "✏ Mbosako'i", "pt": "✏ Editar", "en": "✏ Edit",
        "ru": "✏ Редактировать", "zh": "✏ 编辑", "ko": "✏ 편집", "uk": "✏ Редагувати", "ar": "✏ تعديل",
    },
    "presup_aprobar": {
        "es": "✔ Aprobar", "gn": "✔ Ohovyũ", "pt": "✔ Aprovar", "en": "✔ Approve",
        "ru": "✔ Утвердить", "zh": "✔ 批准", "ko": "✔ 승인", "uk": "✔ Затвердити", "ar": "✔ الموافقة",
    },
    "presup_rechazar": {
        "es": "✕ Rechazar", "gn": "✕ Mboyke", "pt": "✕ Rejeitar", "en": "✕ Reject",
        "ru": "✕ Отклонить", "zh": "✕ 拒绝", "ko": "✕ 거부", "uk": "✕ Відхилити", "ar": "✕ رفض",
    },
    "presup_convertir_venta": {
        "es": "💰 Convertir a Venta", "gn": "💰 Moambue Ñemuha", "pt": "💰 Converter em Venda",
        "en": "💰 Convert to Sale", "ru": "💰 Преобразовать в продажу", "zh": "💰 转换为销售",
        "ko": "💰 판매로 전환", "uk": "💰 Перетворити на продаж", "ar": "💰 تحويل إلى بيع",
    },

    # ── Módulo Pre-Venta ─────────────────────────────────────────
    "preventa_modificar": {
        "es": "✏ Modificar", "gn": "✏ Mbosako'i", "pt": "✏ Modificar", "en": "✏ Modify",
        "ru": "✏ Изменить", "zh": "✏ 修改", "ko": "✏ 수정", "uk": "✏ Змінити", "ar": "✏ تعديل",
    },
    "preventa_codigo_producto": {
        "es": "Código del Producto:", "gn": "Mba'e Código:", "pt": "Código do Produto:",
        "en": "Product Code:", "ru": "Код товара:", "zh": "产品代码：",
        "ko": "상품 코드:", "uk": "Код товару:", "ar": "رمز المنتج:",
    },
    "atajo_f1_cliente": {
        "es": "F1 Asignar Cliente", "gn": "F1 Ame'ẽ Cliente", "pt": "F1 Atribuir Cliente",
        "en": "F1 Assign Client", "ru": "F1 Назначить клиента", "zh": "F1 分配客户",
        "ko": "F1 고객 지정", "uk": "F1 Призначити клієнта", "ar": "F1 تعيين عميل",
    },
    "atajo_f2_buscar": {
        "es": "F2 Buscar", "gn": "F2 Heka", "pt": "F2 Buscar", "en": "F2 Search",
        "ru": "F2 Поиск", "zh": "F2 搜索", "ko": "F2 검색", "uk": "F2 Пошук", "ar": "F2 بحث",
    },
    "atajo_del_borrar": {
        "es": "DEL Borrar Artículo", "gn": "DEL Mboguete Mba'e", "pt": "DEL Excluir Item",
        "en": "DEL Delete Item", "ru": "DEL Удалить позицию", "zh": "DEL 删除项目",
        "ko": "DEL 항목 삭제", "uk": "DEL Видалити позицію", "ar": "DEL حذف العنصر",
    },
    "preventa_cobrar_finalizar": {
        "es": "💰 Cobrar (Finalizar Venta)", "gn": "💰 Ñemuha (Mohu'ã)", "pt": "💰 Cobrar (Finalizar Venda)",
        "en": "💰 Charge (Finish Sale)", "ru": "💰 Оформить (завершить продажу)", "zh": "💰 收款（完成销售）",
        "ko": "💰 결제 (판매 완료)", "uk": "💰 Оформити (завершити продаж)", "ar": "💰 تحصيل (إنهاء البيع)",
    },
    "guardar_cambios": {
        "es": "💾 Guardar Cambios", "gn": "💾 Ñongatu Ambue", "pt": "💾 Salvar Alterações",
        "en": "💾 Save Changes", "ru": "💾 Сохранить изменения", "zh": "💾 保存更改",
        "ko": "💾 변경 사항 저장", "uk": "💾 Зберегти зміни", "ar": "💾 حفظ التغييرات",
    },
    "cancelar_x": {
        "es": "❌ Cancelar", "gn": "❌ Heja", "pt": "❌ Cancelar", "en": "❌ Cancel",
        "ru": "❌ Отмена", "zh": "❌ 取消", "ko": "❌ 취소", "uk": "❌ Скасувати", "ar": "❌ إلغاء",
    },

    # ── Módulo Reportes ──────────────────────────────────────────
    "reportes_titulo": {
        "es": "📊  Reportes de Ventas", "gn": "📊  Ñemuha Reporte", "pt": "📊  Relatórios de Vendas",
        "en": "📊  Sales Reports", "ru": "📊  Отчёты о продажах", "zh": "📊  销售报表",
        "ko": "📊  판매 보고서", "uk": "📊  Звіти про продажі", "ar": "📊  تقارير المبيعات",
    },
    "desde_label": {
        "es": "Desde:", "gn": "Guive:", "pt": "De:", "en": "From:",
        "ru": "С:", "zh": "从：", "ko": "부터:", "uk": "Від:", "ar": "من:",
    },
    "hasta_label": {
        "es": "Hasta:", "gn": "Peve:", "pt": "Até:", "en": "To:",
        "ru": "По:", "zh": "至：", "ko": "까지:", "uk": "До:", "ar": "إلى:",
    },
    "reportes_elegir_rango": {
        "es": "📅 Elegir Rango", "gn": "📅 Eiporavo Rango", "pt": "📅 Escolher Período",
        "en": "📅 Choose Range", "ru": "📅 Выбрать период", "zh": "📅 选择范围",
        "ko": "📅 범위 선택", "uk": "📅 Вибрати період", "ar": "📅 اختر النطاق",
    },
    "vendedor_label": {
        "es": "Vendedor:", "gn": "Ñemuhára:", "pt": "Vendedor:", "en": "Salesperson:",
        "ru": "Продавец:", "zh": "销售员：", "ko": "판매원:", "uk": "Продавець:", "ar": "البائع:",
    },
    "reportes_solo_tus_ventas": {
        "es": "🔒 solo tus ventas", "gn": "🔒 nde ñemuha año", "pt": "🔒 apenas suas vendas",
        "en": "🔒 only your sales", "ru": "🔒 только ваши продажи", "zh": "🔒 仅您的销售",
        "ko": "🔒 내 판매만", "uk": "🔒 лише ваші продажі", "ar": "🔒 مبيعاتك فقط",
    },
    "reportes_total_vendido": {
        "es": "Total Vendido", "gn": "Ñemuha Manterei", "pt": "Total Vendido", "en": "Total Sold",
        "ru": "Всего продано", "zh": "总销售额", "ko": "총 판매액", "uk": "Всього продано", "ar": "إجمالي المبيعات",
    },
    "reportes_canceladas": {
        "es": "Canceladas", "gn": "Ojehejáva", "pt": "Canceladas", "en": "Cancelled",
        "ru": "Отменённые", "zh": "已取消", "ko": "취소됨", "uk": "Скасовані", "ar": "ملغاة",
    },
    "col_id": {
        "es": "ID", "gn": "ID", "pt": "ID", "en": "ID",
        "ru": "ID", "zh": "编号", "ko": "ID", "uk": "ID", "ar": "المعرف",
    },
    "col_condicion": {
        "es": "Condición", "gn": "Mba'éichapa", "pt": "Condição", "en": "Condition",
        "ru": "Условие", "zh": "条件", "ko": "조건", "uk": "Умова", "ar": "الشرط",
    },
    "col_forma_pago": {
        "es": "Forma de Pago", "gn": "Jehepyme'ẽ Reko", "pt": "Forma de Pagamento", "en": "Payment Method",
        "ru": "Способ оплаты", "zh": "付款方式", "ko": "결제 방법", "uk": "Спосіб оплати", "ar": "طريقة الدفع",
    },
    "col_factura": {
        "es": "Factura", "gn": "Factura", "pt": "Fatura", "en": "Invoice",
        "ru": "Счёт-фактура", "zh": "发票", "ko": "청구서", "uk": "Рахунок-фактура", "ar": "الفاتورة",
    },
    "reportes_no_detalle": {
        "es": "No se pudo cargar el detalle.", "gn": "Ndaikatúi ojegueru mba'e rehegua.",
        "pt": "Não foi possível carregar o detalhe.", "en": "Could not load the detail.",
        "ru": "Не удалось загрузить детали.", "zh": "无法加载详情。",
        "ko": "세부정보를 불러올 수 없습니다.", "uk": "Не вдалося завантажити деталі.",
        "ar": "تعذر تحميل التفاصيل.",
    },
    "reportes_articulos": {
        "es": "Artículos", "gn": "Mba'e", "pt": "Artigos", "en": "Items",
        "ru": "Товары", "zh": "商品", "ko": "품목", "uk": "Товари", "ar": "العناصر",
    },
    "reportes_tab_ventas": {
        "es": "🧾  Ventas", "gn": "🧾  Ñemuha", "pt": "🧾  Vendas", "en": "🧾  Sales",
        "ru": "🧾  Продажи", "zh": "🧾  销售", "ko": "🧾  판매", "uk": "🧾  Продажі", "ar": "🧾  المبيعات",
    },
    "reportes_tab_compras": {
        "es": "🛒  Compras", "gn": "🛒  Jejogua", "pt": "🛒  Compras", "en": "🛒  Purchases",
        "ru": "🛒  Закупки", "zh": "🛒  采购", "ko": "🛒  구매", "uk": "🛒  Закупівлі", "ar": "🛒  المشتريات",
    },
    "reportes_tab_presupuestos": {
        "es": "📝  Presupuestos", "gn": "📝  Presupuesto", "pt": "📝  Orçamentos", "en": "📝  Quotes",
        "ru": "📝  Сметы", "zh": "📝  报价单", "ko": "📝  견적", "uk": "📝  Кошториси", "ar": "📝  عروض الأسعار",
    },
    "forma_pago_efectivo": {
        "es": "Efectivo", "gn": "Viru", "pt": "Dinheiro", "en": "Cash",
        "ru": "Наличные", "zh": "现金", "ko": "현금", "uk": "Готівка", "ar": "نقدًا",
    },
    "forma_pago_transferencia": {
        "es": "Transferencia", "gn": "Moambue Viru", "pt": "Transferência", "en": "Transfer",
        "ru": "Перевод", "zh": "转账", "ko": "이체", "uk": "Переказ", "ar": "تحويل",
    },
    "forma_pago_cripto": {
        "es": "Criptomonedas", "gn": "Criptomonedas", "pt": "Criptomoedas", "en": "Cryptocurrency",
        "ru": "Криптовалюта", "zh": "加密货币", "ko": "암호화폐", "uk": "Криптовалюта", "ar": "العملات المشفرة",
    },

    # ── Módulo Asistencia Técnica ────────────────────────────────
    "asist_entrada_equipo": {
        "es": "🖥➕ Entrada de Equipo", "gn": "🖥➕ Mba'e Jeike", "pt": "🖥➕ Entrada de Equipamento",
        "en": "🖥➕ Equipment Check-In", "ru": "🖥➕ Приём оборудования", "zh": "🖥➕ 设备入库",
        "ko": "🖥➕ 장비 접수", "uk": "🖥➕ Прийом обладнання", "ar": "🖥➕ استلام الجهاز",
    },
    "asist_tab_casos": {
        "es": "Casos", "gn": "Mba'e Reko", "pt": "Casos", "en": "Cases",
        "ru": "Заявки", "zh": "案例", "ko": "케이스", "uk": "Заявки", "ar": "الحالات",
    },
    "asist_tab_pendientes": {
        "es": "Pendientes", "gn": "Ojehepyme'ẽva'erã", "pt": "Pendentes", "en": "Pending",
        "ru": "В ожидании", "zh": "待处理", "ko": "대기 중", "uk": "В очікуванні", "ar": "معلقة",
    },
    "asist_tab_dashboard": {
        "es": "Dashboard", "gn": "Dashboard", "pt": "Painel", "en": "Dashboard",
        "ru": "Панель", "zh": "仪表板", "ko": "대시보드", "uk": "Панель", "ar": "لوحة المعلومات",
    },
    "asist_tab_equipos": {
        "es": "Equipos", "gn": "Mba'e Kuéra", "pt": "Equipamentos", "en": "Equipment",
        "ru": "Оборудование", "zh": "设备", "ko": "장비", "uk": "Обладнання", "ar": "الأجهزة",
    },

    # ── Módulo Veterinaria ───────────────────────────────────────
    "vet_nueva_mascota": {
        "es": "🐾➕ Nueva Mascota", "gn": "🐾➕ Mymba Pyahu", "pt": "🐾➕ Novo Animal",
        "en": "🐾➕ New Pet", "ru": "🐾➕ Новый питомец", "zh": "🐾➕ 新宠物",
        "ko": "🐾➕ 새 반려동물", "uk": "🐾➕ Нова тваринка", "ar": "🐾➕ حيوان أليف جديد",
    },
    "vet_tab_mascotas": {
        "es": "Mascotas", "gn": "Mymba Kuéra", "pt": "Animais", "en": "Pets",
        "ru": "Питомцы", "zh": "宠物", "ko": "반려동물", "uk": "Тваринки", "ar": "الحيوانات الأليفة",
    },
    "vet_tab_vacunas_proximas": {
        "es": "Vacunas Próximas", "gn": "Vacuna Ag̃uãva", "pt": "Vacinas Próximas", "en": "Upcoming Vaccines",
        "ru": "Предстоящие прививки", "zh": "即将接种的疫苗", "ko": "다가오는 백신",
        "uk": "Майбутні щеплення", "ar": "اللقاحات القادمة",
    },
    "vet_tab_historial_clinico": {
        "es": "Historial Clínico", "gn": "Ára Rehegua Mymba", "pt": "Histórico Clínico",
        "en": "Medical History", "ru": "История болезни", "zh": "病历",
        "ko": "진료 기록", "uk": "Медична історія", "ar": "السجل الطبي",
    },
    "vet_tab_vacunas": {
        "es": "Vacunas", "gn": "Vacuna", "pt": "Vacinas", "en": "Vaccines",
        "ru": "Прививки", "zh": "疫苗", "ko": "백신", "uk": "Щеплення", "ar": "اللقاحات",
    },
    "vet_tab_tratamientos": {
        "es": "Tratamientos", "gn": "Poñe'ẽ", "pt": "Tratamentos", "en": "Treatments",
        "ru": "Лечение", "zh": "治疗", "ko": "치료", "uk": "Лікування", "ar": "العلاجات",
    },

    # ── Módulo Restaurante/Comedor ───────────────────────────────
    "rest_tab_mesas": {
        "es": "🍽 Mesas", "gn": "🍽 Mesa", "pt": "🍽 Mesas", "en": "🍽 Tables",
        "ru": "🍽 Столы", "zh": "🍽 桌台", "ko": "🍽 테이블", "uk": "🍽 Столи", "ar": "🍽 الطاولات",
    },
    "rest_tab_comandas": {
        "es": "📋 Comandas Activas", "gn": "📋 Comanda Oĩva", "pt": "📋 Comandas Ativas",
        "en": "📋 Active Orders", "ru": "📋 Активные заказы", "zh": "📋 进行中的订单",
        "ko": "📋 진행 중인 주문", "uk": "📋 Активні замовлення", "ar": "📋 الطلبات النشطة",
    },
    "rest_tab_delivery": {
        "es": "🛵 Delivery", "gn": "🛵 Delivery", "pt": "🛵 Entrega", "en": "🛵 Delivery",
        "ru": "🛵 Доставка", "zh": "🛵 外送", "ko": "🛵 배달", "uk": "🛵 Доставка", "ar": "🛵 التوصيل",
    },
    "rest_tab_platos": {
        "es": "🍔 Platos", "gn": "🍔 Tembi'u", "pt": "🍔 Pratos", "en": "🍔 Dishes",
        "ru": "🍔 Блюда", "zh": "🍔 菜品", "ko": "🍔 메뉴", "uk": "🍔 Страви", "ar": "🍔 الأطباق",
    },
    "rest_tab_dashboard": {
        "es": "📊 Dashboard", "gn": "📊 Dashboard", "pt": "📊 Painel", "en": "📊 Dashboard",
        "ru": "📊 Панель", "zh": "📊 仪表板", "ko": "📊 대시보드", "uk": "📊 Панель", "ar": "📊 لوحة المعلومات",
    },
    "rest_receta_insumos": {
        "es": "Receta (insumos)", "gn": "Tembi'u Apoha", "pt": "Receita (insumos)", "en": "Recipe (ingredients)",
        "ru": "Рецепт (ингредиенты)", "zh": "食谱（原料）", "ko": "레시피 (재료)",
        "uk": "Рецепт (інгредієнти)", "ar": "الوصفة (المكونات)",
    },
    "rest_tamanos_variantes": {
        "es": "Tamaños / Variantes", "gn": "Tuichakue / Ambue", "pt": "Tamanhos / Variantes",
        "en": "Sizes / Variants", "ru": "Размеры / Варианты", "zh": "尺寸／规格",
        "ko": "크기 / 옵션", "uk": "Розміри / Варіанти", "ar": "الأحجام / الأنواع",
    },

    # ── Módulo Alquiler de Streaming ─────────────────────────────
    "stream_tab_suscripciones": {
        "es": "👥 Clientes / Suscripciones", "gn": "👥 Cliente / Suscripción",
        "pt": "👥 Clientes / Assinaturas", "en": "👥 Clients / Subscriptions",
        "ru": "👥 Клиенты / Подписки", "zh": "👥 客户／订阅",
        "ko": "👥 고객 / 구독", "uk": "👥 Клієнти / Підписки", "ar": "👥 العملاء / الاشتراكات",
    },
    "stream_tab_cuentas": {
        "es": "🔐 Cuentas", "gn": "🔐 Cuenta", "pt": "🔐 Contas", "en": "🔐 Accounts",
        "ru": "🔐 Аккаунты", "zh": "🔐 账户", "ko": "🔐 계정", "uk": "🔐 Акаунти", "ar": "🔐 الحسابات",
    },
    "stream_tab_combos": {
        "es": "📦 Combos", "gn": "📦 Combo", "pt": "📦 Combos", "en": "📦 Bundles",
        "ru": "📦 Пакеты", "zh": "📦 套餐", "ko": "📦 패키지", "uk": "📦 Пакети", "ar": "📦 الباقات",
    },
    "stream_tab_dashboard": {
        "es": "📊 Dashboard", "gn": "📊 Dashboard", "pt": "📊 Painel", "en": "📊 Dashboard",
        "ru": "📊 Панель", "zh": "📊 仪表板", "ko": "📊 대시보드", "uk": "📊 Панель", "ar": "📊 لوحة المعلومات",
    },

    # ── Módulo Préstamos ─────────────────────────────────────────
    "prestamos_titulo": {
        "es": "🏦  Préstamos", "gn": "🏦  Ame'ẽ", "pt": "🏦  Empréstimos", "en": "🏦  Loans",
        "ru": "🏦  Займы", "zh": "🏦  贷款", "ko": "🏦  대출", "uk": "🏦  Позики", "ar": "🏦  القروض",
    },
    "prestamos_tab_fondo": {
        "es": "🏦  Banco / Fondo", "gn": "🏦  Banco / Fondo", "pt": "🏦  Banco / Fundo",
        "en": "🏦  Bank / Fund", "ru": "🏦  Банк / Фонд", "zh": "🏦  银行／资金",
        "ko": "🏦  은행 / 자금", "uk": "🏦  Банк / Фонд", "ar": "🏦  البنك / الصندوق",
    },
    "prestamos_tab_nuevo": {
        "es": "➕  Nuevo Préstamo", "gn": "➕  Ame'ẽ Pyahu", "pt": "➕  Novo Empréstimo",
        "en": "➕  New Loan", "ru": "➕  Новый займ", "zh": "➕  新贷款",
        "ko": "➕  새 대출", "uk": "➕  Нова позика", "ar": "➕  قرض جديد",
    },
    "prestamos_tab_lista": {
        "es": "📋  Préstamos", "gn": "📋  Ame'ẽ", "pt": "📋  Empréstimos", "en": "📋  Loans",
        "ru": "📋  Займы", "zh": "📋  贷款", "ko": "📋  대출", "uk": "📋  Позики", "ar": "📋  القروض",
    },
    "prestamos_saldo_disponible": {
        "es": "SALDO DISPONIBLE PARA PRESTAR", "gn": "SALDO OĨVA AME'Ẽ HAG̃UA",
        "pt": "SALDO DISPONÍVEL PARA EMPRESTAR", "en": "AVAILABLE BALANCE TO LEND",
        "ru": "ДОСТУПНЫЙ БАЛАНС ДЛЯ ВЫДАЧИ", "zh": "可放贷余额",
        "ko": "대출 가능 잔액", "uk": "ДОСТУПНИЙ БАЛАНС ДЛЯ ВИДАЧІ", "ar": "الرصيد المتاح للإقراض",
    },
    "prestamos_cargar_fondos": {
        "es": "➕ Cargar Fondos", "gn": "➕ Ñemoĩ Viru", "pt": "➕ Carregar Fundos", "en": "➕ Add Funds",
        "ru": "➕ Пополнить фонд", "zh": "➕ 注入资金", "ko": "➕ 자금 추가",
        "uk": "➕ Поповнити фонд", "ar": "➕ إضافة أموال",
    },
    "prestamos_historial_fondo": {
        "es": "Historial de Movimientos del Fondo", "gn": "Fondo Rekoveta Ára",
        "pt": "Histórico de Movimentos do Fundo", "en": "Fund Movement History",
        "ru": "История движений фонда", "zh": "资金流水记录",
        "ko": "자금 이동 내역", "uk": "Історія руху коштів фонду", "ar": "سجل حركة الصندوق",
    },

    # ── Módulo Recursos Humanos ──────────────────────────────────
    "rrhh_titulo": {
        "es": "👥  Recursos Humanos", "gn": "👥  Recursos Humanos", "pt": "👥  Recursos Humanos",
        "en": "👥  Human Resources", "ru": "👥  Кадры", "zh": "👥  人力资源",
        "ko": "👥  인사", "uk": "👥  Кадри", "ar": "👥  الموارد البشرية",
    },
    "rrhh_tab_personal": {
        "es": "👤  Personal", "gn": "👤  Mba'apohára", "pt": "👤  Pessoal", "en": "👤  Staff",
        "ru": "👤  Персонал", "zh": "👤  员工", "ko": "👤  직원", "uk": "👤  Персонал", "ar": "👤  الموظفون",
    },
    "rrhh_tab_asistencia": {
        "es": "📅  Asistencia", "gn": "📅  Jeike", "pt": "📅  Assiduidade", "en": "📅  Attendance",
        "ru": "📅  Посещаемость", "zh": "📅  考勤", "ko": "📅  출석", "uk": "📅  Відвідуваність", "ar": "📅  الحضور",
    },
    "rrhh_tab_adelantos": {
        "es": "💵  Adelantos / Vales", "gn": "💵  Ame'ẽ Ymaite / Vale", "pt": "💵  Adiantamentos / Vales",
        "en": "💵  Advances / Vouchers", "ru": "💵  Авансы / Талоны", "zh": "💵  预支／代金券",
        "ko": "💵  선지급 / 상품권", "uk": "💵  Аванси / Талони", "ar": "💵  السلف / القسائم",
    },

    # ── Módulo Usuarios ──────────────────────────────────────────
    "usuarios_titulo": {
        "es": "⚙  Gestión de Usuarios", "gn": "⚙  Puruhára Ñemboheko", "pt": "⚙  Gestão de Usuários",
        "en": "⚙  User Management", "ru": "⚙  Управление пользователями", "zh": "⚙  用户管理",
        "ko": "⚙  사용자 관리", "uk": "⚙  Керування користувачами", "ar": "⚙  إدارة المستخدمين",
    },
    "usuarios_nuevo": {
        "es": "＋ Nuevo Usuario", "gn": "＋ Puruhára Pyahu", "pt": "＋ Novo Usuário", "en": "＋ New User",
        "ru": "＋ Новый пользователь", "zh": "＋ 新用户", "ko": "＋ 새 사용자", "uk": "＋ Новий користувач", "ar": "＋ مستخدم جديد",
    },
    "col_usuario_mayus": {
        "es": "USUARIO", "gn": "PURUHÁRA", "pt": "USUÁRIO", "en": "USERNAME",
        "ru": "ПОЛЬЗОВАТЕЛЬ", "zh": "用户名", "ko": "사용자명", "uk": "КОРИСТУВАЧ", "ar": "المستخدم",
    },
    "usuarios_nombre_completo": {
        "es": "NOMBRE COMPLETO", "gn": "TÉRA MYENYHẼ", "pt": "NOME COMPLETO", "en": "FULL NAME",
        "ru": "ПОЛНОЕ ИМЯ", "zh": "全名", "ko": "전체 이름", "uk": "ПОВНЕ ІМ'Я", "ar": "الاسم الكامل",
    },
    "usuarios_rol_mayus": {
        "es": "ROL", "gn": "TEKO", "pt": "PAPEL", "en": "ROLE",
        "ru": "РОЛЬ", "zh": "角色", "ko": "역할", "uk": "РОЛЬ", "ar": "الدور",
    },
    "usuarios_permisos_mayus": {
        "es": "PERMISOS", "gn": "AJEHECHAKUAA", "pt": "PERMISSÕES", "en": "PERMISSIONS",
        "ru": "РАЗРЕШЕНИЯ", "zh": "权限", "ko": "권한", "uk": "ДОЗВОЛИ", "ar": "الصلاحيات",
    },
    "usuarios_seleccion_detalle": {
        "es": "Seleccioná un usuario\nde la lista para ver sus detalles",
        "gn": "Eiporavo peteĩ puruhára\nlista-gui ehecha hag̃ua hetakue",
        "pt": "Selecione um usuário\nda lista para ver seus detalhes",
        "en": "Select a user\nfrom the list to see their details",
        "ru": "Выберите пользователя\nиз списка, чтобы увидеть детали",
        "zh": "从列表中选择一个用户\n查看详情",
        "ko": "목록에서 사용자를 선택하면\n상세정보가 표시됩니다",
        "uk": "Виберіть користувача\nзі списку, щоб побачити деталі",
        "ar": "اختر مستخدمًا\nمن القائمة لعرض التفاصيل",
    },
    "usuarios_permisos_modulos": {
        "es": "Permisos de módulos:", "gn": "Módulo Ajehechakuaa:", "pt": "Permissões de módulos:",
        "en": "Module permissions:", "ru": "Разрешения модулей:", "zh": "模块权限：",
        "ko": "모듈 권한:", "uk": "Дозволи модулів:", "ar": "أذونات الوحدات:",
    },
    "usuarios_acceso_total": {
        "es": "✓ Acceso TOTAL (administrador)", "gn": "✓ Jeike MYENYHẼ (admin)",
        "pt": "✓ Acesso TOTAL (administrador)", "en": "✓ FULL Access (administrator)",
        "ru": "✓ ПОЛНЫЙ доступ (администратор)", "zh": "✓ 完全权限（管理员）",
        "ko": "✓ 전체 접근 (관리자)", "uk": "✓ ПОВНИЙ доступ (адміністратор)", "ar": "✓ صلاحية كاملة (مدير)",
    },
    "usuarios_sin_modulos": {
        "es": "⚠ Sin módulos asignados", "gn": "⚠ Ndaipóri módulo ome'ẽva",
        "pt": "⚠ Sem módulos atribuídos", "en": "⚠ No modules assigned",
        "ru": "⚠ Модули не назначены", "zh": "⚠ 未分配模块",
        "ko": "⚠ 할당된 모듈 없음", "uk": "⚠ Модулі не призначені", "ar": "⚠ لا توجد وحدات مخصصة",
    },

    # ── Módulo Cotizaciones ──────────────────────────────────────
    "cotiz_titulo": {
        "es": "💱  Cotizaciones de Monedas", "gn": "💱  Viru Jehepyme'ẽ", "pt": "💱  Cotações de Moedas",
        "en": "💱  Currency Exchange Rates", "ru": "💱  Курсы валют", "zh": "💱  货币汇率",
        "ko": "💱  환율", "uk": "💱  Курси валют", "ar": "💱  أسعار صرف العملات",
    },
    "cargando": {
        "es": "Cargando...", "gn": "Oñemboheko...", "pt": "Carregando...", "en": "Loading...",
        "ru": "Загрузка...", "zh": "加载中...", "ko": "로딩 중...", "uk": "Завантаження...", "ar": "جارٍ التحميل...",
    },
    "cotiz_tab_fiat": {
        "es": "💵  Dinero Fiduciario", "gn": "💵  Viru", "pt": "💵  Moeda Fiduciária", "en": "💵  Fiat Money",
        "ru": "💵  Фиатные деньги", "zh": "💵  法定货币", "ko": "💵  법정 화폐", "uk": "💵  Фіатні гроші", "ar": "💵  العملة الورقية",
    },
    "cotiz_tab_cripto": {
        "es": "🪙  Cripto", "gn": "🪙  Cripto", "pt": "🪙  Cripto", "en": "🪙  Crypto",
        "ru": "🪙  Крипто", "zh": "🪙  加密货币", "ko": "🪙  암호화폐", "uk": "🪙  Крипто", "ar": "🪙  العملات المشفرة",
    },
    "cotiz_base": {
        "es": "Base:", "gn": "Ypy:", "pt": "Base:", "en": "Base:",
        "ru": "База:", "zh": "基准：", "ko": "기준:", "uk": "База:", "ar": "الأساس:",
    },
    "cotiz_convertir": {
        "es": "💰 Convertir:", "gn": "💰 Moambue:", "pt": "💰 Converter:", "en": "💰 Convert:",
        "ru": "💰 Конвертировать:", "zh": "💰 换算：", "ko": "💰 변환:", "uk": "💰 Конвертувати:", "ar": "💰 تحويل:",
    },
    "cotiz_ver_equivalencias": {
        "es": "→ ver equivalencias en la grilla", "gn": "→ ehecha equivalencia mesa-pe",
        "pt": "→ ver equivalências na grade", "en": "→ see equivalents in the grid",
        "ru": "→ см. эквиваленты в таблице", "zh": "→ 在表格中查看等值",
        "ko": "→ 표에서 환산 값 보기", "uk": "→ див. еквіваленти в таблиці", "ar": "→ عرض المعادلات في الجدول",
    },
    "cotiz_moneda": {
        "es": "Moneda:", "gn": "Viru:", "pt": "Moeda:", "en": "Currency:",
        "ru": "Валюта:", "zh": "货币：", "ko": "통화:", "uk": "Валюта:", "ar": "العملة:",
    },
    "cotiz_pyg_no_disponible": {
        "es": "(PYG no disponible en cripto — usá Dinero Fiduciario para convertir)",
        "gn": "(PYG ndaipóri cripto-pe — eiporu Viru Moambue hag̃ua)",
        "pt": "(PYG não disponível em cripto — use Moeda Fiduciária para converter)",
        "en": "(PYG not available in crypto — use Fiat Money to convert)",
        "ru": "(PYG недоступен в крипто — используйте фиатные деньги для конвертации)",
        "zh": "（加密货币中不支持PYG — 请使用法定货币进行换算）",
        "ko": "(암호화폐에서는 PYG를 사용할 수 없음 — 법정 화폐로 변환하세요)",
        "uk": "(PYG недоступний у крипто — використовуйте фіатні гроші для конвертації)",
        "ar": "(PYG غير متاح في العملات المشفرة — استخدم العملة الورقية للتحويل)",
    },
    "cotiz_ver_col_equivalente": {
        "es": "→ ver col. EQUIVALENTE", "gn": "→ ehecha col. EQUIVALENTE", "pt": "→ ver col. EQUIVALENTE",
        "en": "→ see EQUIVALENT column", "ru": "→ см. столбец ЭКВИВАЛЕНТ", "zh": "→ 查看「等值」列",
        "ko": "→ '환산값' 열 참조", "uk": "→ див. стовпець ЕКВІВАЛЕНТ", "ar": "→ انظر عمود المعادل",
    },
    "cotiz_actualizando": {
        "es": "⏳ Actualizando...", "gn": "⏳ Oñembopyahu...", "pt": "⏳ Atualizando...",
        "en": "⏳ Refreshing...", "ru": "⏳ Обновление...", "zh": "⏳ 正在更新...",
        "ko": "⏳ 새로고침 중...", "uk": "⏳ Оновлення...", "ar": "⏳ جارٍ التحديث...",
    },
    "cotiz_descargando_datos": {
        "es": "Descargando datos...", "gn": "Oñemboguejy datos...", "pt": "Baixando dados...",
        "en": "Downloading data...", "ru": "Загрузка данных...", "zh": "正在下载数据...",
        "ko": "데이터 다운로드 중...", "uk": "Завантаження даних...", "ar": "جارٍ تنزيل البيانات...",
    },
    "cotiz_descargando": {
        "es": "Descargando...", "gn": "Oñemboguejy...", "pt": "Baixando...", "en": "Downloading...",
        "ru": "Загрузка...", "zh": "正在下载...", "ko": "다운로드 중...", "uk": "Завантаження...", "ar": "جارٍ التنزيل...",
    },
    "cotiz_col_moneda": {
        "es": "MONEDA", "gn": "VIRU", "pt": "MOEDA", "en": "CURRENCY",
        "ru": "ВАЛЮТА", "zh": "货币", "ko": "통화", "uk": "ВАЛЮТА", "ar": "العملة",
    },
    "cotiz_col_tasa": {
        "es": "TASA", "gn": "TASA", "pt": "TAXA", "en": "RATE",
        "ru": "КУРС", "zh": "汇率", "ko": "환율", "uk": "КУРС", "ar": "السعر",
    },
    "cotiz_col_inversa": {
        "es": "INVERSA", "gn": "AMBUE GOTYO", "pt": "INVERSA", "en": "INVERSE",
        "ru": "ОБРАТНЫЙ", "zh": "反向汇率", "ko": "역환율", "uk": "ОБЕРНЕНИЙ", "ar": "معكوس",
    },
    "cotiz_col_equivalente": {
        "es": "EQUIVALENTE", "gn": "OJOJÁVA", "pt": "EQUIVALENTE", "en": "EQUIVALENT",
        "ru": "ЭКВИВАЛЕНТ", "zh": "等值", "ko": "환산액", "uk": "ЕКВІВАЛЕНТ", "ar": "المعادل",
    },
    "cotiz_col_simbolo": {
        "es": "SÍMBOLO", "gn": "SÍMBOLO", "pt": "SÍMBOLO", "en": "SYMBOL",
        "ru": "СИМВОЛ", "zh": "代号", "ko": "심볼", "uk": "СИМВОЛ", "ar": "الرمز",
    },
    "cotiz_col_nombre": {
        "es": "NOMBRE", "gn": "TÉRA", "pt": "NOME", "en": "NAME",
        "ru": "НАЗВАНИЕ", "zh": "名称", "ko": "이름", "uk": "НАЗВА", "ar": "الاسم",
    },
    "cotiz_col_precio": {
        "es": "PRECIO", "gn": "VIRU", "pt": "PREÇO", "en": "PRICE",
        "ru": "ЦЕНА", "zh": "价格", "ko": "가격", "uk": "ЦІНА", "ar": "السعر",
    },
    "cotiz_col_variacion24h": {
        "es": "VARIACIÓN 24H", "gn": "AMBUE 24H", "pt": "VARIAÇÃO 24H", "en": "24H CHANGE",
        "ru": "ИЗМЕНЕНИЕ ЗА 24Ч", "zh": "24小时涨跌", "ko": "24시간 변동", "uk": "ЗМІНА ЗА 24Г", "ar": "تغيّر 24 ساعة",
    },
    "cotiz_col_marketcap": {
        "es": "MARKET CAP", "gn": "MARKET CAP", "pt": "MARKET CAP", "en": "MARKET CAP",
        "ru": "РЫН. КАПИТАЛИЗАЦИЯ", "zh": "市值", "ko": "시가총액", "uk": "РИН. КАПІТАЛІЗАЦІЯ", "ar": "القيمة السوقية",
    },
    "cotiz_col_volumen24h": {
        "es": "VOLUMEN 24H", "gn": "VOLUMEN 24H", "pt": "VOLUME 24H", "en": "24H VOLUME",
        "ru": "ОБЪЁМ ЗА 24Ч", "zh": "24小时交易量", "ko": "24시간 거래량", "uk": "ОБСЯГ ЗА 24Г", "ar": "حجم التداول 24 ساعة",
    },

    # ── Módulo Config. Local ─────────────────────────────────────
    "configlocal_titulo": {
        "es": "🏪  Configuración del Local y Comprobantes",
        "gn": "🏪  Rendaguépe Ñemboheko",
        "pt": "🏪  Configuração da Loja e Comprovantes",
        "en": "🏪  Store and Receipt Settings",
        "ru": "🏪  Настройки магазина и чеков",
        "zh": "🏪  门店与凭证设置",
        "ko": "🏪  매장 및 영수증 설정",
        "uk": "🏪  Налаштування магазину та чеків",
        "ar": "🏪  إعدادات المتجر والإيصالات",
    },
    "configlocal_tab_datos": {
        "es": "🏪  Datos del Local", "gn": "🏪  Rendaguépe Mba'e", "pt": "🏪  Dados da Loja",
        "en": "🏪  Store Data", "ru": "🏪  Данные магазина", "zh": "🏪  门店信息",
        "ko": "🏪  매장 정보", "uk": "🏪  Дані магазину", "ar": "🏪  بيانات المتجر",
    },
    "configlocal_tab_comprobante": {
        "es": "🧾  Comprobante de Venta", "gn": "🧾  Comprobante Ñemuha", "pt": "🧾  Comprovante de Venda",
        "en": "🧾  Sales Receipt", "ru": "🧾  Товарный чек", "zh": "🧾  销售凭证",
        "ko": "🧾  판매 영수증", "uk": "🧾  Товарний чек", "ar": "🧾  إيصال البيع",
    },
    "configlocal_tab_factura": {
        "es": "📄  Factura Legal", "gn": "📄  Factura Legal", "pt": "📄  Fatura Legal",
        "en": "📄  Legal Invoice", "ru": "📄  Официальный счёт-фактура", "zh": "📄  正式发票",
        "ko": "📄  법정 청구서", "uk": "📄  Офіційний рахунок-фактура", "ar": "📄  الفاتورة الرسمية",
    },
    "configlocal_tab_numeracion": {
        "es": "🔢  Numeración", "gn": "🔢  Papapy", "pt": "🔢  Numeração", "en": "🔢  Numbering",
        "ru": "🔢  Нумерация", "zh": "🔢  编号", "ko": "🔢  번호 매기기", "uk": "🔢  Нумерація", "ar": "🔢  الترقيم",
    },

    # ── Módulo Licencias ─────────────────────────────────────────
    "licencia_generador_titulo": {
        "es": "🔑  Generador de Licencias", "gn": "🔑  Licencia Apoha", "pt": "🔑  Gerador de Licenças",
        "en": "🔑  License Generator", "ru": "🔑  Генератор лицензий", "zh": "🔑  许可证生成器",
        "ko": "🔑  라이선스 생성기", "uk": "🔑  Генератор ліцензій", "ar": "🔑  مولّد التراخيص",
    },
    "licencia_col_serial": {
        "es": "SERIAL", "gn": "SERIAL", "pt": "SERIAL", "en": "SERIAL",
        "ru": "СЕРИЙНЫЙ №", "zh": "序列号", "ko": "시리얼", "uk": "СЕРІЙНИЙ №", "ar": "الرقم التسلسلي",
    },
    "licencia_col_duracion": {
        "es": "DURACIÓN", "gn": "ÁRA PUKUKUE", "pt": "DURAÇÃO", "en": "DURATION",
        "ru": "СРОК", "zh": "时长", "ko": "기간", "uk": "ТРИВАЛІСТЬ", "ar": "المدة",
    },
    "licencia_col_generado": {
        "es": "GENERADO", "gn": "OJEJAPO", "pt": "GERADO", "en": "GENERATED",
        "ru": "СОЗДАНО", "zh": "已生成", "ko": "생성됨", "uk": "СТВОРЕНО", "ar": "تم الإنشاء",
    },
    "licencia_col_usada": {
        "es": "ESTADO", "gn": "MBA'ÉICHAPA", "pt": "STATUS", "en": "STATUS",
        "ru": "СТАТУС", "zh": "状态", "ko": "상태", "uk": "СТАТУС", "ar": "الحالة",
    },
    "licencia_col_fecha_uso": {
        "es": "FECHA DE USO", "gn": "ÁRA PURU", "pt": "DATA DE USO", "en": "DATE USED",
        "ru": "ДАТА ИСПОЛЬЗОВАНИЯ", "zh": "使用日期", "ko": "사용 날짜", "uk": "ДАТА ВИКОРИСТАННЯ", "ar": "تاريخ الاستخدام",
    },

    # ── Módulo Uso del Sistema ───────────────────────────────────
    "uso_titulo": {
        "es": "⏱  Estadísticas de Uso", "gn": "⏱  Puru Rehegua", "pt": "⏱  Estatísticas de Uso",
        "en": "⏱  Usage Statistics", "ru": "⏱  Статистика использования", "zh": "⏱  使用统计",
        "ko": "⏱  사용 통계", "uk": "⏱  Статистика використання", "ar": "⏱  إحصائيات الاستخدام",
    },
    "uso_actividad_por_hora": {
        "es": "Actividad por hora del día (segundos acumulados)",
        "gn": "Jejapo ára aravo rupive (segundo oñembyatýva)",
        "pt": "Atividade por hora do dia (segundos acumulados)",
        "en": "Activity by hour of day (accumulated seconds)",
        "ru": "Активность по часам дня (накопленные секунды)",
        "zh": "按小时统计的活动（累计秒数）",
        "ko": "시간대별 활동 (누적 초)",
        "uk": "Активність за годинами дня (накопичені секунди)",
        "ar": "النشاط حسب ساعة اليوم (الثواني المتراكمة)",
    },
    "uso_ultimas_sesiones": {
        "es": "Últimas sesiones", "gn": "Sesión Ypy Guive", "pt": "Últimas sessões",
        "en": "Latest sessions", "ru": "Последние сеансы", "zh": "最近的会话",
        "ko": "최근 세션", "uk": "Останні сеанси", "ar": "آخر الجلسات",
    },
    "uso_col_usuario": {
        "es": "USUARIO", "gn": "PURUHÁRA", "pt": "USUÁRIO", "en": "USER",
        "ru": "ПОЛЬЗОВАТЕЛЬ", "zh": "用户", "ko": "사용자", "uk": "КОРИСТУВАЧ", "ar": "المستخدم",
    },
    "uso_col_inicio": {
        "es": "INICIO", "gn": "ÑEPYRŨ", "pt": "INÍCIO", "en": "START",
        "ru": "НАЧАЛО", "zh": "开始", "ko": "시작", "uk": "ПОЧАТОК", "ar": "البداية",
    },
    "uso_col_fin": {
        "es": "FIN", "gn": "OPA", "pt": "FIM", "en": "END",
        "ru": "КОНЕЦ", "zh": "结束", "ko": "종료", "uk": "КІНЕЦЬ", "ar": "النهاية",
    },
    "uso_sin_datos": {
        "es": "Aún no hay datos suficientes.", "gn": "Ndaipóri gueteri mba'e heta.",
        "pt": "Ainda não há dados suficientes.", "en": "Not enough data yet.",
        "ru": "Пока недостаточно данных.", "zh": "数据尚不足。",
        "ko": "아직 충분한 데이터가 없습니다.", "uk": "Поки що недостатньо даних.", "ar": "لا توجد بيانات كافية بعد.",
    },

    # ── Módulo Gestión de Datos ──────────────────────────────────
    "datos_titulo": {
        "es": "💾  Gestión de Datos", "gn": "💾  Datos Ñemongu'e", "pt": "💾  Gestão de Dados",
        "en": "💾  Data Management", "ru": "💾  Управление данными", "zh": "💾  数据管理",
        "ko": "💾  데이터 관리", "uk": "💾  Керування даними", "ar": "💾  إدارة البيانات",
    },
    "datos_seccion_bd": {
        "es": "🗄  Base de datos", "gn": "🗄  Datos Renda", "pt": "🗄  Banco de dados",
        "en": "🗄  Database", "ru": "🗄  База данных", "zh": "🗄  数据库",
        "ko": "🗄  데이터베이스", "uk": "🗄  База даних", "ar": "🗄  قاعدة البيانات",
    },
    "datos_seccion_excel": {
        "es": "📊  Excel", "gn": "📊  Excel", "pt": "📊  Excel", "en": "📊  Excel",
        "ru": "📊  Excel", "zh": "📊  Excel", "ko": "📊  Excel", "uk": "📊  Excel", "ar": "📊  Excel",
    },
    "datos_seccion_csv": {
        "es": "📄  CSV", "gn": "📄  CSV", "pt": "📄  CSV", "en": "📄  CSV",
        "ru": "📄  CSV", "zh": "📄  CSV", "ko": "📄  CSV", "uk": "📄  CSV", "ar": "📄  CSV",
    },
    "datos_seccion_avanzado": {
        "es": "⚡  Avanzado", "gn": "⚡  Ambue", "pt": "⚡  Avançado", "en": "⚡  Advanced",
        "ru": "⚡  Дополнительно", "zh": "⚡  高级", "ko": "⚡  고급", "uk": "⚡  Розширено", "ar": "⚡  متقدم",
    },

    # ── Módulo Terminal SQL ──────────────────────────────────────
    "sql_titulo": {
        "es": "🖥  Terminal SQL", "gn": "🖥  Terminal SQL", "pt": "🖥  Terminal SQL",
        "en": "🖥  SQL Terminal", "ru": "🖥  SQL-терминал", "zh": "🖥  SQL终端",
        "ko": "🖥  SQL 터미널", "uk": "🖥  SQL-термінал", "ar": "🖥  طرفية SQL",
    },
    "sql_tablas": {
        "es": "📋 Tablas", "gn": "📋 Tabla", "pt": "📋 Tabelas", "en": "📋 Tables",
        "ru": "📋 Таблицы", "zh": "📋 数据表", "ko": "📋 테이블", "uk": "📋 Таблиці", "ar": "📋 الجداول",
    },
    "sql_doble_clic": {
        "es": "Doble clic: SELECT * (100 filas)", "gn": "Joykéke mokõi jey: SELECT * (100 tape)",
        "pt": "Clique duplo: SELECT * (100 linhas)", "en": "Double-click: SELECT * (100 rows)",
        "ru": "Двойной клик: SELECT * (100 строк)", "zh": "双击：SELECT *（100行）",
        "ko": "더블클릭: SELECT * (100행)", "uk": "Подвійний клік: SELECT * (100 рядків)",
        "ar": "نقر مزدوج: SELECT * (100 صف)",
    },
    "sql_historial": {
        "es": "🕑 Historial", "gn": "🕑 Ára Guare", "pt": "🕑 Histórico", "en": "🕑 History",
        "ru": "🕑 История", "zh": "🕑 历史记录", "ko": "🕑 기록", "uk": "🕑 Історія", "ar": "🕑 السجل",
    },
    "sql_ejecutar": {
        "es": "▶ Ejecutar  (F5 / Ctrl+Enter)", "gn": "▶ Mongu'e  (F5 / Ctrl+Enter)",
        "pt": "▶ Executar  (F5 / Ctrl+Enter)", "en": "▶ Run  (F5 / Ctrl+Enter)",
        "ru": "▶ Выполнить (F5 / Ctrl+Enter)", "zh": "▶ 运行  (F5 / Ctrl+Enter)",
        "ko": "▶ 실행  (F5 / Ctrl+Enter)", "uk": "▶ Виконати (F5 / Ctrl+Enter)", "ar": "▶ تنفيذ (F5 / Ctrl+Enter)",
    },
    "sql_limpiar": {
        "es": "🗑 Limpiar", "gn": "🗑 Mopotĩ", "pt": "🗑 Limpar", "en": "🗑 Clear",
        "ru": "🗑 Очистить", "zh": "🗑 清除", "ko": "🗑 지우기", "uk": "🗑 Очистити", "ar": "🗑 مسح",
    },
    "sql_modo_lectura": {
        "es": "🔒 Modo solo lectura (bloquea INSERT/UPDATE/DELETE/DDL)",
        "gn": "🔒 Ojehecha año (ombotove INSERT/UPDATE/DELETE/DDL)",
        "pt": "🔒 Modo somente leitura (bloqueia INSERT/UPDATE/DELETE/DDL)",
        "en": "🔒 Read-only mode (blocks INSERT/UPDATE/DELETE/DDL)",
        "ru": "🔒 Режим только для чтения (блокирует INSERT/UPDATE/DELETE/DDL)",
        "zh": "🔒 只读模式（阻止 INSERT/UPDATE/DELETE/DDL）",
        "ko": "🔒 읽기 전용 모드 (INSERT/UPDATE/DELETE/DDL 차단)",
        "uk": "🔒 Режим лише читання (блокує INSERT/UPDATE/DELETE/DDL)",
        "ar": "🔒 وضع القراءة فقط (يمنع INSERT/UPDATE/DELETE/DDL)",
    },
    "sql_error_consulta": {
        "es": "✖ Error al ejecutar la consulta", "gn": "✖ Ndaikatúi ojejapo consulta",
        "pt": "✖ Erro ao executar a consulta", "en": "✖ Error running the query",
        "ru": "✖ Ошибка выполнения запроса", "zh": "✖ 查询执行出错",
        "ko": "✖ 쿼리 실행 오류", "uk": "✖ Помилка виконання запиту", "ar": "✖ خطأ في تنفيذ الاستعلام",
    },

    # ── Módulo Asistente IA ──────────────────────────────────────
    "ia_titulo": {
        "es": "🤖  Asistente IA", "gn": "🤖  Pytyvõhára IA", "pt": "🤖  Assistente IA",
        "en": "🤖  AI Assistant", "ru": "🤖  ИИ-помощник", "zh": "🤖  AI助手",
        "ko": "🤖  AI 비서", "uk": "🤖  ШІ-помічник", "ar": "🤖  مساعد الذكاء الاصطناعي",
    },
    "ia_configurar": {
        "es": "⚙ Configurar", "gn": "⚙ Ñemboheko", "pt": "⚙ Configurar", "en": "⚙ Configure",
        "ru": "⚙ Настроить", "zh": "⚙ 配置", "ko": "⚙ 설정", "uk": "⚙ Налаштувати", "ar": "⚙ إعداد",
    },
    "ia_no_configurado": {
        "es": "El Asistente IA todavía no está configurado", "gn": "Pytyvõhára IA ndojembohekóiva gueteri",
        "pt": "O Assistente IA ainda não está configurado", "en": "The AI Assistant is not configured yet",
        "ru": "ИИ-помощник ещё не настроен", "zh": "AI助手尚未配置",
        "ko": "AI 비서가 아직 설정되지 않았습니다", "uk": "ШІ-помічник ще не налаштовано", "ar": "مساعد الذكاء الاصطناعي غير مُعد بعد",
    },
    "ia_configurar_asistente": {
        "es": "⚙ Configurar Asistente IA", "gn": "⚙ Ñemboheko Pytyvõhára IA", "pt": "⚙ Configurar Assistente IA",
        "en": "⚙ Configure AI Assistant", "ru": "⚙ Настроить ИИ-помощника", "zh": "⚙ 配置AI助手",
        "ko": "⚙ AI 비서 설정", "uk": "⚙ Налаштувати ШІ-помічника", "ar": "⚙ إعداد مساعد الذكاء الاصطناعي",
    },
    "ia_analizar_ventas": {
        "es": "📊 Analizar mis ventas", "gn": "📊 Ehecha che ñemuha", "pt": "📊 Analisar minhas vendas",
        "en": "📊 Analyze my sales", "ru": "📊 Анализ моих продаж", "zh": "📊 分析我的销售",
        "ko": "📊 내 판매 분석", "uk": "📊 Аналіз моїх продажів", "ar": "📊 تحليل مبيعاتي",
    },
    "ia_generar_descripcion": {
        "es": "✨ Generar descripción de producto", "gn": "✨ Ñemongu'e mba'e rehegua",
        "pt": "✨ Gerar descrição de produto", "en": "✨ Generate product description",
        "ru": "✨ Создать описание товара", "zh": "✨ 生成产品描述",
        "ko": "✨ 상품 설명 생성", "uk": "✨ Створити опис товару", "ar": "✨ إنشاء وصف المنتج",
    },
    "ia_traducir_texto": {
        "es": "🌐 Traducir texto", "gn": "🌐 Traducir Moñe'ẽ", "pt": "🌐 Traduzir texto",
        "en": "🌐 Translate text", "ru": "🌐 Перевести текст", "zh": "🌐 翻译文本",
        "ko": "🌐 텍스트 번역", "uk": "🌐 Перекласти текст", "ar": "🌐 ترجمة النص",
    },
    "ia_nueva_conversacion": {
        "es": "🧹 Nueva conversación", "gn": "🧹 Ñemongeta Pyahu", "pt": "🧹 Nova conversa",
        "en": "🧹 New conversation", "ru": "🧹 Новый разговор", "zh": "🧹 新对话",
        "ko": "🧹 새 대화", "uk": "🧹 Нова розмова", "ar": "🧹 محادثة جديدة",
    },
    "ia_enviar": {
        "es": "➤ Enviar\n(Enter)", "gn": "➤ Mondo\n(Enter)", "pt": "➤ Enviar\n(Enter)",
        "en": "➤ Send\n(Enter)", "ru": "➤ Отправить\n(Enter)", "zh": "➤ 发送\n(回车)",
        "ko": "➤ 보내기\n(Enter)", "uk": "➤ Надіслати\n(Enter)", "ar": "➤ إرسال\n(إدخال)",
    },
    "ia_pensando": {
        "es": "🤖 El Asistente IA está pensando...", "gn": "🤖 Pytyvõhára IA opensa...",
        "pt": "🤖 O Assistente IA está pensando...", "en": "🤖 The AI Assistant is thinking...",
        "ru": "🤖 ИИ-помощник думает...", "zh": "🤖 AI助手正在思考...",
        "ko": "🤖 AI 비서가 생각 중...", "uk": "🤖 ШІ-помічник думає...", "ar": "🤖 مساعد الذكاء الاصطناعي يفكر...",
    },
    "cancelar_simple": {
        "es": "Cancelar", "gn": "Heja", "pt": "Cancelar", "en": "Cancel",
        "ru": "Отмена", "zh": "取消", "ko": "취소", "uk": "Скасувати", "ar": "إلغاء",
    },

    # ── Módulo Idioma ────────────────────────────────────────────
    "idioma_titulo": {
        "es": "🌐  Idioma del Sistema", "gn": "🌐  Sistema Ñe'ẽ", "pt": "🌐  Idioma do Sistema",
        "en": "🌐  System Language", "ru": "🌐  Язык системы", "zh": "🌐  系统语言",
        "ko": "🌐  시스템 언어", "uk": "🌐  Мова системи", "ar": "🌐  لغة النظام",
    },
    "idioma_elegir": {
        "es": "Elegí el idioma de la interfaz:", "gn": "Eiporavo sistema ñe'ẽ:",
        "pt": "Escolha o idioma da interface:", "en": "Choose the interface language:",
        "ru": "Выберите язык интерфейса:", "zh": "选择界面语言：",
        "ko": "인터페이스 언어를 선택하세요:", "uk": "Виберіть мову інтерфейсу:", "ar": "اختر لغة الواجهة:",
    },
    "idioma_aplicar": {
        "es": "💾 Aplicar Idioma", "gn": "💾 Ñemboheko Ñe'ẽ", "pt": "💾 Aplicar Idioma",
        "en": "💾 Apply Language", "ru": "💾 Применить язык", "zh": "💾 应用语言",
        "ko": "💾 언어 적용", "uk": "💾 Застосувати мову", "ar": "💾 تطبيق اللغة",
    },
    "idioma_actual_badge": {
        "es": "✔ Actual", "gn": "✔ Ko'ág̃a", "pt": "✔ Atual", "en": "✔ Current",
        "ru": "✔ Текущий", "zh": "✔ 当前", "ko": "✔ 현재", "uk": "✔ Поточна", "ar": "✔ الحالية",
    },

    # ── Módulo Reinicio del Sistema ──────────────────────────────
    "reinicio_titulo": {
        "es": "♻  Reinicio del Sistema", "gn": "♻  Sistema Ñepyrũjey", "pt": "♻  Reinício do Sistema",
        "en": "♻  System Reset", "ru": "♻  Сброс системы", "zh": "♻  系统重置",
        "ko": "♻  시스템 초기화", "uk": "♻  Скидання системи", "ar": "♻  إعادة تعيين النظام",
    },
    "reinicio_estado_bd": {
        "es": "📊  Estado actual de la base de datos", "gn": "📊  Datos Rekove Ko'ág̃a",
        "pt": "📊  Estado atual do banco de dados", "en": "📊  Current database status",
        "ru": "📊  Текущее состояние базы данных", "zh": "📊  数据库当前状态",
        "ko": "📊  현재 데이터베이스 상태", "uk": "📊  Поточний стан бази даних", "ar": "📊  الحالة الحالية لقاعدة البيانات",
    },
    "reinicio_usuario_admin": {
        "es": "Usuario administrador:", "gn": "Puruhára admin:", "pt": "Usuário administrador:",
        "en": "Administrator user:", "ru": "Пользователь-администратор:", "zh": "管理员用户：",
        "ko": "관리자 사용자:", "uk": "Користувач-адміністратор:", "ar": "المستخدم المسؤول:",
    },
    "contrasena_label": {
        "es": "Contraseña:", "gn": "Ñe'ẽñemi:", "pt": "Senha:", "en": "Password:",
        "ru": "Пароль:", "zh": "密码：", "ko": "비밀번호:", "uk": "Пароль:", "ar": "كلمة المرور:",
    },
    "reinicio_confirmar_ejecutar": {
        "es": "⚠ Confirmar y ejecutar", "gn": "⚠ Confirmar ha Mongu'e", "pt": "⚠ Confirmar e executar",
        "en": "⚠ Confirm and run", "ru": "⚠ Подтвердить и выполнить", "zh": "⚠ 确认并执行",
        "ko": "⚠ 확인 및 실행", "uk": "⚠ Підтвердити і виконати", "ar": "⚠ تأكيد وتنفيذ",
    },
    "reinicio_error_credenciales": {
        "es": "⚠ Usuario o contraseña incorrectos. Verificá e intentá de nuevo.",
        "gn": "⚠ Puruhára térã ñe'ẽñemi ndoikóiva. Ehecha jey ha eñeha'ã jey.",
        "pt": "⚠ Usuário ou senha incorretos. Verifique e tente novamente.",
        "en": "⚠ Incorrect username or password. Check and try again.",
        "ru": "⚠ Неверный пользователь или пароль. Проверьте и попробуйте снова.",
        "zh": "⚠ 用户名或密码错误。请检查后重试。",
        "ko": "⚠ 사용자 이름 또는 비밀번호가 잘못되었습니다. 확인 후 다시 시도하세요.",
        "uk": "⚠ Невірний користувач або пароль. Перевірте і спробуйте ще раз.",
        "ar": "⚠ اسم المستخدم أو كلمة المرور غير صحيحة. تحقق وحاول مرة أخرى.",
    },
    "reinicio_error_permisos": {
        "es": "⚠ El usuario ingresado no tiene permisos de administrador.",
        "gn": "⚠ Puruhára oñemoĩva ndorekói admin permiso.",
        "pt": "⚠ O usuário informado não tem permissões de administrador.",
        "en": "⚠ The entered user does not have administrator permissions.",
        "ru": "⚠ У введённого пользователя нет прав администратора.",
        "zh": "⚠ 输入的用户没有管理员权限。",
        "ko": "⚠ 입력한 사용자는 관리자 권한이 없습니다.",
        "uk": "⚠ Введений користувач не має прав адміністратора.",
        "ar": "⚠ المستخدم المدخل ليس لديه صلاحيات المسؤول.",
    },

    # ── Módulo Clima ─────────────────────────────────────────────
    "clima_titulo": {
        "es": "⛅  Clima — Paraguay", "gn": "⛅  Ára — Paraguay", "pt": "⛅  Clima — Paraguai",
        "en": "⛅  Weather — Paraguay", "ru": "⛅  Погода — Парагвай", "zh": "⛅  天气 — 巴拉圭",
        "ko": "⛅  날씨 — 파라과이", "uk": "⛅  Погода — Парагвай", "ar": "⛅  الطقس — باراغواي",
    },
    "clima_departamento": {
        "es": "Departamento:", "gn": "Tetã Ryepy:", "pt": "Departamento:", "en": "Department:",
        "ru": "Департамент:", "zh": "省份：", "ko": "주(도):", "uk": "Департамент:", "ar": "المقاطعة:",
    },
    "clima_ciudad_distrito": {
        "es": "Ciudad/Distrito:", "gn": "Táva/Distrito:", "pt": "Cidade/Distrito:", "en": "City/District:",
        "ru": "Город/Район:", "zh": "城市／地区：", "ko": "도시 / 지구:", "uk": "Місто/Район:", "ar": "المدينة / المقاطعة:",
    },
    "clima_hoy": {
        "es": "Hoy", "gn": "Ko'ág̃a", "pt": "Hoje", "en": "Today",
        "ru": "Сегодня", "zh": "今天", "ko": "오늘", "uk": "Сьогодні", "ar": "اليوم",
    },
    "clima_pronostico_5dias": {
        "es": "Pronóstico 5 días", "gn": "Ára Mombyry 5 Ára", "pt": "Previsão 5 dias",
        "en": "5-Day Forecast", "ru": "Прогноз на 5 дней", "zh": "5天预报",
        "ko": "5일 예보", "uk": "Прогноз на 5 днів", "ar": "توقعات 5 أيام",
    },
    "clima_evolucion_horaria": {
        "es": "Evolución horaria", "gn": "Ára Aravo Rupive", "pt": "Evolução horária",
        "en": "Hourly forecast", "ru": "Почасовой прогноз", "zh": "逐小时变化",
        "ko": "시간별 추이", "uk": "Погодинний прогноз", "ar": "التطور بالساعة",
    },
    "clima_sin_coordenadas": {
        "es": "No se encontraron coordenadas para esa ubicación.",
        "gn": "Ndojejuhúi coordenadas ko tenda peguarã.",
        "pt": "Não foram encontradas coordenadas para esse local.",
        "en": "No coordinates were found for that location.",
        "ru": "Координаты для этого места не найдены.",
        "zh": "未找到该位置的坐标。",
        "ko": "해당 위치의 좌표를 찾을 수 없습니다.",
        "uk": "Координати для цього місця не знайдено.",
        "ar": "لم يتم العثور على إحداثيات لهذا الموقع.",
    },
    "clima_actualizando": {
        "es": "⏳ Actualizando...", "gn": "⏳ Ojejapo...", "pt": "⏳ Atualizando...",
        "en": "⏳ Updating...", "ru": "⏳ Обновление...", "zh": "⏳ 更新中...",
        "ko": "⏳ 업데이트 중...", "uk": "⏳ Оновлення...", "ar": "⏳ جارٍ التحديث...",
    },
    "clima_descargando_datos": {
        "es": "Descargando datos...", "gn": "Ojegueru datos...", "pt": "Baixando dados...",
        "en": "Downloading data...", "ru": "Загрузка данных...", "zh": "正在下载数据...",
        "ko": "데이터 다운로드 중...", "uk": "Завантаження даних...", "ar": "جارٍ تحميل البيانات...",
    },
    "actualizar_icono": {
        "es": "🔄 Actualizar", "gn": "🔄 Mbopyahu", "pt": "🔄 Atualizar", "en": "🔄 Refresh",
        "ru": "🔄 Обновить", "zh": "🔄 刷新", "ko": "🔄 새로고침", "uk": "🔄 Оновити", "ar": "🔄 تحديث",
    },

    # ── Módulo Novedades (encabezado; el contenido del historial sigue en español) ──
    "novedades_titulo": {
        "es": "🆕  Novedades del Sistema", "gn": "🆕  Mba'e Pyahu Sistema", "pt": "🆕  Novidades do Sistema",
        "en": "🆕  What's New", "ru": "🆕  Новости системы", "zh": "🆕  系统更新日志",
        "ko": "🆕  시스템 업데이트 소식", "uk": "🆕  Новини системи", "ar": "🆕  تحديثات النظام",
    },
    "novedades_subtitulo": {
        "es": "Enterate qué cambió y qué funciones nuevas hay",
        "gn": "Ehecha mba'épa oñemoambue ha mba'e pyahu oĩ",
        "pt": "Fique por dentro do que mudou e das novidades",
        "en": "Find out what changed and what's new",
        "ru": "Узнайте, что изменилось и что нового",
        "zh": "了解有哪些变化和新功能",
        "ko": "무엇이 바뀌었고 어떤 새 기능이 있는지 확인하세요",
        "uk": "Дізнайтеся, що змінилося і що нового",
        "ar": "اكتشف ما تغيّر وما هو الجديد",
    },

    # ── Módulo Ayuda (encabezado; el contenido de cada tema sigue en español) ──
    "ayuda_titulo": {
        "es": "❓  Ayuda del Sistema", "gn": "❓  Sistema Pytyvõ", "pt": "❓  Ajuda do Sistema",
        "en": "❓  System Help", "ru": "❓  Справка системы", "zh": "❓  系统帮助",
        "ko": "❓  시스템 도움말", "uk": "❓  Довідка системи", "ar": "❓  مساعدة النظام",
    },

    # ── Veterinaria (contenido interno) ──────────────────────────
    "vet_incluir_fallecidos": {
        "es": "Incluir fallecidos", "gn": "Omoĩve omanóva", "pt": "Incluir falecidos",
        "en": "Include deceased", "ru": "Включить умерших", "zh": "包括已故的",
        "ko": "사망한 동물 포함", "uk": "Включити померлих", "ar": "تضمين النافقة",
    },
    "vet_generar_pdf": {
        "es": "🖨 Generar PDF", "gn": "🖨 Mongu'e PDF", "pt": "🖨 Gerar PDF", "en": "🖨 Generate PDF",
        "ru": "🖨 Создать PDF", "zh": "🖨 生成PDF", "ko": "🖨 PDF 생성", "uk": "🖨 Створити PDF", "ar": "🖨 إنشاء PDF",
    },
    "vet_enviar_correo": {
        "es": "✉ Enviar por Correo", "gn": "✉ Mondo Correo", "pt": "✉ Enviar por E-mail",
        "en": "✉ Send by Email", "ru": "✉ Отправить по почте", "zh": "✉ 通过邮件发送",
        "ko": "✉ 이메일로 보내기", "uk": "✉ Надіслати поштою", "ar": "✉ إرسال بالبريد",
    },
    "vet_buscar_mascota": {
        "es": "Buscar (mascota, dueño, raza, chip):",
        "gn": "Heka (mymba, hentekuéra, raza, chip):",
        "pt": "Buscar (animal, dono, raça, chip):",
        "en": "Search (pet, owner, breed, chip):",
        "ru": "Поиск (питомец, владелец, порода, чип):",
        "zh": "搜索（宠物、主人、品种、芯片）：",
        "ko": "검색 (반려동물, 보호자, 품종, 칩):",
        "uk": "Пошук (тваринка, власник, порода, чіп):",
        "ar": "بحث (الحيوان، المالك، السلالة، الرقاقة):",
    },
    "col_mascota": {
        "es": "MASCOTA", "gn": "MYMBA", "pt": "ANIMAL", "en": "PET",
        "ru": "ПИТОМЕЦ", "zh": "宠物", "ko": "반려동물", "uk": "ТВАРИНКА", "ar": "الحيوان",
    },
    "col_especie": {
        "es": "ESPECIE", "gn": "MYMBA REI", "pt": "ESPÉCIE", "en": "SPECIES",
        "ru": "ВИД", "zh": "物种", "ko": "종", "uk": "ВИД", "ar": "النوع",
    },
    "col_raza": {
        "es": "RAZA", "gn": "RAZA", "pt": "RAÇA", "en": "BREED",
        "ru": "ПОРОДА", "zh": "品种", "ko": "품종", "uk": "ПОРОДА", "ar": "السلالة",
    },
    "col_sexo": {
        "es": "SEXO", "gn": "KUIMBA'E/KUÑA", "pt": "SEXO", "en": "SEX",
        "ru": "ПОЛ", "zh": "性别", "ko": "성별", "uk": "СТАТЬ", "ar": "الجنس",
    },
    "col_edad": {
        "es": "EDAD", "gn": "ARY", "pt": "IDADE", "en": "AGE",
        "ru": "ВОЗРАСТ", "zh": "年龄", "ko": "나이", "uk": "ВІК", "ar": "العمر",
    },
    "col_dueno": {
        "es": "DUEÑO", "gn": "IYÁRA", "pt": "DONO", "en": "OWNER",
        "ru": "ВЛАДЕЛЕЦ", "zh": "主人", "ko": "보호자", "uk": "ВЛАСНИК", "ar": "المالك",
    },
    "col_vacuna": {
        "es": "VACUNA", "gn": "VACUNA", "pt": "VACINA", "en": "VACCINE",
        "ru": "ПРИВИВКА", "zh": "疫苗", "ko": "백신", "uk": "ЩЕПЛЕННЯ", "ar": "اللقاح",
    },
    "col_vencimiento": {
        "es": "VENCIMIENTO", "gn": "OPÁTA ÁRA", "pt": "VENCIMENTO", "en": "DUE DATE",
        "ru": "СРОК", "zh": "到期日", "ko": "만료일", "uk": "ТЕРМІН", "ar": "تاريخ الاستحقاق",
    },
    "col_hora": {
        "es": "HORA", "gn": "ARY'I", "pt": "HORA", "en": "TIME",
        "ru": "ВРЕМЯ", "zh": "时间", "ko": "시간", "uk": "ЧАС", "ar": "الوقت",
    },
    "col_motivo": {
        "es": "MOTIVO", "gn": "MBA'ÉRE", "pt": "MOTIVO", "en": "REASON",
        "ru": "ПРИЧИНА", "zh": "原因", "ko": "사유", "uk": "ПРИЧИНА", "ar": "السبب",
    },
    "col_prox_visita": {
        "es": "PRÓX. VISITA", "gn": "VISITA OU'ÁVA", "pt": "PRÓX. VISITA", "en": "NEXT VISIT",
        "ru": "СЛЕД. ВИЗИТ", "zh": "下次就诊", "ko": "다음 방문", "uk": "НАСТУПНИЙ ВІЗИТ", "ar": "الزيارة القادمة",
    },
    "col_diagnostico": {
        "es": "DIAGNÓSTICO", "gn": "MBA'ASY REKO", "pt": "DIAGNÓSTICO", "en": "DIAGNOSIS",
        "ru": "ДИАГНОЗ", "zh": "诊断", "ko": "진단", "uk": "ДІАГНОЗ", "ar": "التشخيص",
    },
    "col_peso": {
        "es": "PESO", "gn": "POHYI", "pt": "PESO", "en": "WEIGHT",
        "ru": "ВЕС", "zh": "体重", "ko": "체중", "uk": "ВАГА", "ar": "الوزن",
    },
    "col_costo": {
        "es": "COSTO", "gn": "VIRU", "pt": "CUSTO", "en": "COST",
        "ru": "СТОИМОСТЬ", "zh": "费用", "ko": "비용", "uk": "ВАРТІСТЬ", "ar": "التكلفة",
    },
    "col_fecha_aplicacion": {
        "es": "FECHA APLICACIÓN", "gn": "ÁRA OJEME'Ẽ", "pt": "DATA APLICAÇÃO", "en": "APPLICATION DATE",
        "ru": "ДАТА ВВЕДЕНИЯ", "zh": "接种日期", "ko": "접종일", "uk": "ДАТА ВВЕДЕННЯ", "ar": "تاريخ التطعيم",
    },
    "col_proxima_dosis": {
        "es": "PRÓXIMA DOSIS", "gn": "DOSIS OU'ÁVA", "pt": "PRÓXIMA DOSE", "en": "NEXT DOSE",
        "ru": "СЛЕД. ДОЗА", "zh": "下次剂量", "ko": "다음 접종", "uk": "НАСТУПНА ДОЗА", "ar": "الجرعة القادمة",
    },
    "col_lote": {
        "es": "LOTE", "gn": "LOTE", "pt": "LOTE", "en": "BATCH",
        "ru": "ПАРТИЯ", "zh": "批次", "ko": "배치", "uk": "ПАРТІЯ", "ar": "الدفعة",
    },
    "col_veterinario": {
        "es": "VETERINARIO", "gn": "MYMBA POHÃNOHÁRA", "pt": "VETERINÁRIO", "en": "VETERINARIAN",
        "ru": "ВЕТЕРИНАР", "zh": "兽医", "ko": "수의사", "uk": "ВЕТЕРИНАР", "ar": "الطبيب البيطري",
    },
    "col_tipo": {
        "es": "TIPO", "gn": "TEKO", "pt": "TIPO", "en": "TYPE",
        "ru": "ТИП", "zh": "类型", "ko": "유형", "uk": "ТИП", "ar": "النوع",
    },
    "col_producto_mayus": {
        "es": "PRODUCTO", "gn": "MBA'E", "pt": "PRODUTO", "en": "PRODUCT",
        "ru": "ТОВАР", "zh": "产品", "ko": "제품", "uk": "ТОВАР", "ar": "المنتج",
    },
    "col_inicio_mayus": {
        "es": "INICIO", "gn": "ÑEPYRŨ", "pt": "INÍCIO", "en": "START",
        "ru": "НАЧАЛО", "zh": "开始", "ko": "시작", "uk": "ПОЧАТОК", "ar": "البداية",
    },
    "col_fin_mayus": {
        "es": "FIN", "gn": "OPA", "pt": "FIM", "en": "END",
        "ru": "КОНЕЦ", "zh": "结束", "ko": "종료", "uk": "КІНЕЦЬ", "ar": "النهاية",
    },
    "col_dosis": {
        "es": "DOSIS", "gn": "DOSIS", "pt": "DOSE", "en": "DOSE",
        "ru": "ДОЗА", "zh": "剂量", "ko": "용량", "uk": "ДОЗА", "ar": "الجرعة",
    },
    "col_frecuencia": {
        "es": "FRECUENCIA", "gn": "OJEHU JEVY", "pt": "FREQUÊNCIA", "en": "FREQUENCY",
        "ru": "ЧАСТОТА", "zh": "频率", "ko": "빈도", "uk": "ЧАСТОТА", "ar": "التكرار",
    },
    "vet_sin_cuenta_correo": {
        "es": "Todavía no configuraste una cuenta de correo.",
        "gn": "Ndaikatúi gueteri ñemboheko cuenta correo.",
        "pt": "Você ainda não configurou uma conta de e-mail.",
        "en": "You haven't set up an email account yet.",
        "ru": "Вы ещё не настроили учётную запись электронной почты.",
        "zh": "您尚未设置电子邮件账户。",
        "ko": "아직 이메일 계정을 설정하지 않았습니다.",
        "uk": "Ви ще не налаштували обліковий запис електронної пошти.",
        "ar": "لم تقم بإعداد حساب بريد إلكتروني بعد.",
    },
    "vet_configurar_email_ahora": {
        "es": "⚙ Configurar Email Ahora", "gn": "⚙ Ñemboheko Email Ko'ág̃a",
        "pt": "⚙ Configurar E-mail Agora", "en": "⚙ Configure Email Now",
        "ru": "⚙ Настроить почту сейчас", "zh": "⚙ 立即配置邮箱",
        "ko": "⚙ 지금 이메일 설정", "uk": "⚙ Налаштувати пошту зараз", "ar": "⚙ إعداد البريد الآن",
    },
    "vet_cambiar_cuenta": {
        "es": "Cambiar cuenta", "gn": "Moambue Cuenta", "pt": "Trocar conta", "en": "Change account",
        "ru": "Сменить аккаунт", "zh": "更换账户", "ko": "계정 변경", "uk": "Змінити акаунт", "ar": "تغيير الحساب",
    },
    "vet_para_destinatario": {
        "es": "Para (destinatario):", "gn": "Peguarã:", "pt": "Para (destinatário):",
        "en": "To (recipient):", "ru": "Кому (получатель):", "zh": "收件人：",
        "ko": "받는 사람:", "uk": "Кому (отримувач):", "ar": "إلى (المستلم):",
    },
    "asunto_label": {
        "es": "Asunto:", "gn": "Mba'e Rehegua:", "pt": "Assunto:", "en": "Subject:",
        "ru": "Тема:", "zh": "主题：", "ko": "제목:", "uk": "Тема:", "ar": "الموضوع:",
    },
    "mensaje_label": {
        "es": "Mensaje:", "gn": "Ñe'ẽ:", "pt": "Mensagem:", "en": "Message:",
        "ru": "Сообщение:", "zh": "消息：", "ko": "메시지:", "uk": "Повідомлення:", "ar": "الرسالة:",
    },
    "vet_se_adjuntara_pdf": {
        "es": "📎 Se adjuntará el PDF del reporte automáticamente.",
        "gn": "📎 PDF reporte oñemoĩta ijehegui.",
        "pt": "📎 O PDF do relatório será anexado automaticamente.",
        "en": "📎 The report PDF will be attached automatically.",
        "ru": "📎 PDF-отчёт будет прикреплён автоматически.",
        "zh": "📎 报告PDF将自动附加。",
        "ko": "📎 보고서 PDF가 자동으로 첨부됩니다.",
        "uk": "📎 PDF-звіт буде додано автоматично.",
        "ar": "📎 سيتم إرفاق ملف PDF للتقرير تلقائيًا.",
    },
    "enviar_avion": {
        "es": "✈ Enviar", "gn": "✈ Mondo", "pt": "✈ Enviar", "en": "✈ Send",
        "ru": "✈ Отправить", "zh": "✈ 发送", "ko": "✈ 보내기", "uk": "✈ Надіслати", "ar": "✈ إرسال",
    },
    "enviando": {
        "es": "Enviando...", "gn": "Omondo...", "pt": "Enviando...", "en": "Sending...",
        "ru": "Отправка...", "zh": "发送中...", "ko": "전송 중...", "uk": "Надсилання...", "ar": "جارٍ الإرسال...",
    },
    "vet_vacunas_vencidas": {
        "es": "Vacunas vencidas o próximas a vencer (30 días)",
        "gn": "Vacuna opáva térã oú mboyve (30 ára)",
        "pt": "Vacinas vencidas ou próximas do vencimento (30 dias)",
        "en": "Vaccines overdue or expiring soon (30 days)",
        "ru": "Просроченные или скоро истекающие прививки (30 дней)",
        "zh": "已过期或即将到期的疫苗（30天）",
        "ko": "만료되었거나 곧 만료될 백신 (30일)",
        "uk": "Прострочені або ті, що незабаром закінчуються щеплення (30 днів)",
        "ar": "اللقاحات المنتهية أو التي على وشك الانتهاء (30 يومًا)",
    },
    "vet_consultas_hoy": {
        "es": "Consultas de hoy", "gn": "Ko árape Jehecha", "pt": "Consultas de hoje",
        "en": "Today's appointments", "ru": "Приёмы на сегодня", "zh": "今日就诊",
        "ko": "오늘의 진료", "uk": "Прийоми на сьогодні", "ar": "استشارات اليوم",
    },
    "vet_seccion_dueno": {
        "es": "Dueño", "gn": "Iyára", "pt": "Dono", "en": "Owner",
        "ru": "Владелец", "zh": "主人", "ko": "보호자", "uk": "Власник", "ar": "المالك",
    },
    "nombre_label": {
        "es": "Nombre:", "gn": "Téra:", "pt": "Nome:", "en": "Name:",
        "ru": "Имя:", "zh": "姓名：", "ko": "이름:", "uk": "Ім'я:", "ar": "الاسم:",
    },
    "telefono_label": {
        "es": "Teléfono:", "gn": "Pumbyry:", "pt": "Telefone:", "en": "Phone:",
        "ru": "Телефон:", "zh": "电话：", "ko": "전화:", "uk": "Телефон:", "ar": "الهاتف:",
    },
    "vet_buscar_cliente": {
        "es": "🔍 Buscar Cliente", "gn": "🔍 Heka Cliente", "pt": "🔍 Buscar Cliente",
        "en": "🔍 Search Client", "ru": "🔍 Найти клиента", "zh": "🔍 搜索客户",
        "ko": "🔍 고객 검색", "uk": "🔍 Знайти клієнта", "ar": "🔍 بحث عن عميل",
    },
    "vet_seccion_mascota": {
        "es": "Mascota", "gn": "Mymba", "pt": "Animal", "en": "Pet",
        "ru": "Питомец", "zh": "宠物", "ko": "반려동물", "uk": "Тваринка", "ar": "الحيوان الأليف",
    },
    "especie_label": {
        "es": "Especie:", "gn": "Mymba Rei:", "pt": "Espécie:", "en": "Species:",
        "ru": "Вид:", "zh": "物种：", "ko": "종:", "uk": "Вид:", "ar": "النوع:",
    },
    "raza_label": {
        "es": "Raza:", "gn": "Raza:", "pt": "Raça:", "en": "Breed:",
        "ru": "Порода:", "zh": "品种：", "ko": "품종:", "uk": "Порода:", "ar": "السلالة:",
    },
    "color_label": {
        "es": "Color:", "gn": "Sa'y:", "pt": "Cor:", "en": "Color:",
        "ru": "Цвет:", "zh": "颜色：", "ko": "색상:", "uk": "Колір:", "ar": "اللون:",
    },
    "sexo_label": {
        "es": "Sexo:", "gn": "Kuimba'e/Kuña:", "pt": "Sexo:", "en": "Sex:",
        "ru": "Пол:", "zh": "性别：", "ko": "성별:", "uk": "Стать:", "ar": "الجنس:",
    },
    "vet_fecha_nacimiento": {
        "es": "Fecha Nacimiento:", "gn": "Ára Heñói:", "pt": "Data de Nascimento:",
        "en": "Birth Date:", "ru": "Дата рождения:", "zh": "出生日期：",
        "ko": "생년월일:", "uk": "Дата народження:", "ar": "تاريخ الميلاد:",
    },
    "vet_peso_kg": {
        "es": "Peso (Kg):", "gn": "Pohyi (Kg):", "pt": "Peso (Kg):", "en": "Weight (Kg):",
        "ru": "Вес (кг):", "zh": "体重（千克）：", "ko": "체중 (kg):", "uk": "Вага (кг):", "ar": "الوزن (كجم):",
    },
    "vet_microchip": {
        "es": "N° Microchip:", "gn": "N° Microchip:", "pt": "N° Microchip:", "en": "Microchip No.:",
        "ru": "№ микрочипа:", "zh": "芯片号：", "ko": "마이크로칩 번호:", "uk": "№ мікрочіпа:", "ar": "رقم الشريحة:",
    },
    "vet_esterilizado": {
        "es": "Esterilizado/a", "gn": "Ojekytĩmbyre", "pt": "Castrado(a)", "en": "Neutered/Spayed",
        "ru": "Стерилизован(а)", "zh": "已绝育", "ko": "중성화됨", "uk": "Стерилізовано", "ar": "معقّم",
    },
    "observaciones_label": {
        "es": "Observaciones:", "gn": "Mba'e Jehai:", "pt": "Observações:", "en": "Notes:",
        "ru": "Примечания:", "zh": "备注：", "ko": "비고:", "uk": "Примітки:", "ar": "ملاحظات:",
    },
    "guardar_icono": {
        "es": "💾 Guardar", "gn": "💾 Ñongatu", "pt": "💾 Salvar", "en": "💾 Save",
        "ru": "💾 Сохранить", "zh": "💾 保存", "ko": "💾 저장", "uk": "💾 Зберегти", "ar": "💾 حفظ",
    },
    "vet_marcar_fallecido": {
        "es": "🕊 Marcar Fallecido", "gn": "🕊 Ehai Omano", "pt": "🕊 Marcar Falecido",
        "en": "🕊 Mark Deceased", "ru": "🕊 Отметить как умершего", "zh": "🕊 标记为已故",
        "ko": "🕊 사망 표시", "uk": "🕊 Позначити як померлого", "ar": "🕊 وضع علامة نافق",
    },
    "vet_reactivar_ficha": {
        "es": "↩ Reactivar Ficha", "gn": "↩ Mbojevy Ficha", "pt": "↩ Reativar Ficha",
        "en": "↩ Reactivate Record", "ru": "↩ Восстановить карточку", "zh": "↩ 重新激活档案",
        "ko": "↩ 기록 재활성화", "uk": "↩ Відновити картку", "ar": "↩ إعادة تفعيل السجل",
    },
    "vet_nueva_consulta": {
        "es": "➕ Nueva Consulta", "gn": "➕ Jehecha Pyahu", "pt": "➕ Nova Consulta",
        "en": "➕ New Visit", "ru": "➕ Новый приём", "zh": "➕ 新就诊",
        "ko": "➕ 새 진료", "uk": "➕ Новий прийом", "ar": "➕ استشارة جديدة",
    },
    "vet_nueva_vacuna": {
        "es": "➕ Nueva Vacuna", "gn": "➕ Vacuna Pyahu", "pt": "➕ Nova Vacina",
        "en": "➕ New Vaccine", "ru": "➕ Новая прививка", "zh": "➕ 新疫苗",
        "ko": "➕ 새 백신", "uk": "➕ Нове щеплення", "ar": "➕ لقاح جديد",
    },
    "vet_nuevo_tratamiento": {
        "es": "➕ Nuevo Tratamiento", "gn": "➕ Poñe'ẽ Pyahu", "pt": "➕ Novo Tratamento",
        "en": "➕ New Treatment", "ru": "➕ Новое лечение", "zh": "➕ 新治疗",
        "ko": "➕ 새 치료", "uk": "➕ Нове лікування", "ar": "➕ علاج جديد",
    },
    "vet_finalizar_seleccionado": {
        "es": "✔ Finalizar Seleccionado", "gn": "✔ Mohu'ã Poravopyre", "pt": "✔ Finalizar Selecionado",
        "en": "✔ Finish Selected", "ru": "✔ Завершить выбранное", "zh": "✔ 完成所选",
        "ko": "✔ 선택 항목 종료", "uk": "✔ Завершити вибране", "ar": "✔ إنهاء المحدد",
    },
    "vet_titulo_nueva_consulta": {
        "es": "🩺 Nueva Consulta", "gn": "🩺 Jehecha Pyahu", "pt": "🩺 Nova Consulta",
        "en": "🩺 New Visit", "ru": "🩺 Новый приём", "zh": "🩺 新就诊",
        "ko": "🩺 새 진료", "uk": "🩺 Новий прийом", "ar": "🩺 استشارة جديدة",
    },
    "motivo_label": {
        "es": "Motivo:", "gn": "Mba'ére:", "pt": "Motivo:", "en": "Reason:",
        "ru": "Причина:", "zh": "原因：", "ko": "사유:", "uk": "Причина:", "ar": "السبب:",
    },
    "vet_temperatura": {
        "es": "Temperatura (°C):", "gn": "Aku'i (°C):", "pt": "Temperatura (°C):",
        "en": "Temperature (°C):", "ru": "Температура (°C):", "zh": "体温（°C）：",
        "ko": "체온 (°C):", "uk": "Температура (°C):", "ar": "درجة الحرارة (°م):",
    },
    "diagnostico_label": {
        "es": "Diagnóstico:", "gn": "Mba'asy Reko:", "pt": "Diagnóstico:", "en": "Diagnosis:",
        "ru": "Диагноз:", "zh": "诊断：", "ko": "진단:", "uk": "Діагноз:", "ar": "التشخيص:",
    },
    "vet_tratamiento_indicado": {
        "es": "Tratamiento indicado:", "gn": "Poñe'ẽ Oje'éva:", "pt": "Tratamento indicado:",
        "en": "Prescribed treatment:", "ru": "Назначенное лечение:", "zh": "建议治疗：",
        "ko": "처방된 치료:", "uk": "Призначене лікування:", "ar": "العلاج الموصوف:",
    },
    "vet_proxima_visita": {
        "es": "Próxima visita:", "gn": "Visita Ou'áva:", "pt": "Próxima visita:", "en": "Next visit:",
        "ru": "Следующий визит:", "zh": "下次就诊：", "ko": "다음 방문:", "uk": "Наступний візит:", "ar": "الزيارة القادمة:",
    },
    "vet_costo_gs": {
        "es": "Costo (Gs):", "gn": "Viru (Gs):", "pt": "Custo (Gs):", "en": "Cost (Gs):",
        "ru": "Стоимость (Gs):", "zh": "费用（Gs）：", "ko": "비용 (Gs):", "uk": "Вартість (Gs):", "ar": "التكلفة (Gs):",
    },
    "vet_titulo_nueva_vacuna": {
        "es": "💉 Nueva Vacuna", "gn": "💉 Vacuna Pyahu", "pt": "💉 Nova Vacina",
        "en": "💉 New Vaccine", "ru": "💉 Новая прививка", "zh": "💉 新疫苗",
        "ko": "💉 새 백신", "uk": "💉 Нове щеплення", "ar": "💉 لقاح جديد",
    },
    "vacuna_label": {
        "es": "Vacuna:", "gn": "Vacuna:", "pt": "Vacina:", "en": "Vaccine:",
        "ru": "Прививка:", "zh": "疫苗：", "ko": "백신:", "uk": "Щеплення:", "ar": "اللقاح:",
    },
    "vet_fecha_aplicacion_label": {
        "es": "Fecha aplicación:", "gn": "Ára Ojeme'ẽ:", "pt": "Data aplicação:",
        "en": "Application date:", "ru": "Дата введения:", "zh": "接种日期：",
        "ko": "접종일:", "uk": "Дата введення:", "ar": "تاريخ التطعيم:",
    },
    "vet_proxima_dosis_label": {
        "es": "Próxima dosis:", "gn": "Dosis Ou'áva:", "pt": "Próxima dose:", "en": "Next dose:",
        "ru": "Следующая доза:", "zh": "下次剂量：", "ko": "다음 접종:", "uk": "Наступна доза:", "ar": "الجرعة القادمة:",
    },
    "lote_label": {
        "es": "Lote:", "gn": "Lote:", "pt": "Lote:", "en": "Batch:",
        "ru": "Партия:", "zh": "批次：", "ko": "배치:", "uk": "Партія:", "ar": "الدفعة:",
    },
    "veterinario_label": {
        "es": "Veterinario:", "gn": "Mymba Pohãnohára:", "pt": "Veterinário:", "en": "Veterinarian:",
        "ru": "Ветеринар:", "zh": "兽医：", "ko": "수의사:", "uk": "Ветеринар:", "ar": "الطبيب البيطري:",
    },
    "vet_titulo_nuevo_tratamiento": {
        "es": "💊 Nuevo Tratamiento", "gn": "💊 Poñe'ẽ Pyahu", "pt": "💊 Novo Tratamento",
        "en": "💊 New Treatment", "ru": "💊 Новое лечение", "zh": "💊 新治疗",
        "ko": "💊 새 치료", "uk": "💊 Нове лікування", "ar": "💊 علاج جديد",
    },
    "tipo_label": {
        "es": "Tipo:", "gn": "Teko:", "pt": "Tipo:", "en": "Type:",
        "ru": "Тип:", "zh": "类型：", "ko": "유형:", "uk": "Тип:", "ar": "النوع:",
    },
    "vet_producto_medicamento": {
        "es": "Producto/Medicamento:", "gn": "Mba'e/Pohã:", "pt": "Produto/Medicamento:",
        "en": "Product/Medication:", "ru": "Товар/Лекарство:", "zh": "产品／药物：",
        "ko": "제품 / 약물:", "uk": "Товар/Ліки:", "ar": "المنتج / الدواء:",
    },
    "dosis_label": {
        "es": "Dosis:", "gn": "Dosis:", "pt": "Dose:", "en": "Dose:",
        "ru": "Доза:", "zh": "剂量：", "ko": "용량:", "uk": "Доза:", "ar": "الجرعة:",
    },
    "frecuencia_label": {
        "es": "Frecuencia:", "gn": "Ojehu Jevy:", "pt": "Frequência:", "en": "Frequency:",
        "ru": "Частота:", "zh": "频率：", "ko": "빈도:", "uk": "Частота:", "ar": "التكرار:",
    },
    "vet_fecha_fin_estimada": {
        "es": "Fecha fin estimada:", "gn": "Ára Opáta Ha'ãva:", "pt": "Data fim estimada:",
        "en": "Estimated end date:", "ru": "Ориентировочная дата окончания:", "zh": "预计结束日期：",
        "ko": "예상 종료일:", "uk": "Орієнтовна дата закінчення:", "ar": "تاريخ الانتهاء المتوقع:",
    },

    # ── Restaurante (contenido interno) ──────────────────────────
    "rest_nueva_mesa": {
        "es": "➕ Nueva Mesa", "gn": "➕ Mesa Pyahu", "pt": "➕ Nova Mesa", "en": "➕ New Table",
        "ru": "➕ Новый стол", "zh": "➕ 新桌台", "ko": "➕ 새 테이블", "uk": "➕ Новий стіл", "ar": "➕ طاولة جديدة",
    },
    "rest_nuevo_pedido": {
        "es": "🛵 Nuevo Pedido (Delivery / Para Llevar / Mostrador)",
        "gn": "🛵 Jehepyme'ẽ Pyahu (Delivery / Reraha / Mostrador)",
        "pt": "🛵 Novo Pedido (Entrega / Para Levar / Balcão)",
        "en": "🛵 New Order (Delivery / Takeout / Counter)",
        "ru": "🛵 Новый заказ (Доставка / На вынос / Стойка)",
        "zh": "🛵 新订单（外送／外带／柜台）",
        "ko": "🛵 새 주문 (배달 / 포장 / 카운터)",
        "uk": "🛵 Нове замовлення (Доставка / На винос / Стійка)",
        "ar": "🛵 طلب جديد (توصيل / تيك أواي / كاونتر)",
    },
    "rest_sin_mesas": {
        "es": "Todavía no agregaste ninguna mesa.", "gn": "Ndaipóri mesa emoĩva gueteri.",
        "pt": "Você ainda não adicionou nenhuma mesa.", "en": "You haven't added any tables yet.",
        "ru": "Вы ещё не добавили ни одного стола.", "zh": "您尚未添加任何桌台。",
        "ko": "아직 추가된 테이블이 없습니다.", "uk": "Ви ще не додали жодного столу.", "ar": "لم تقم بإضافة أي طاولة بعد.",
    },
    "rest_gestionar_repartidores": {
        "es": "🏍 Gestionar Repartidores", "gn": "🏍 Ñemboheko Reraháva",
        "pt": "🏍 Gerenciar Entregadores", "en": "🏍 Manage Couriers",
        "ru": "🏍 Управление курьерами", "zh": "🏍 管理送货员",
        "ko": "🏍 배달원 관리", "uk": "🏍 Керування кур'єрами", "ar": "🏍 إدارة موصلي الطلبات",
    },
    "rest_asignar_repartidor": {
        "es": "👤 Asignar Repartidor", "gn": "👤 Ame'ẽ Reraháva", "pt": "👤 Atribuir Entregador",
        "en": "👤 Assign Courier", "ru": "👤 Назначить курьера", "zh": "👤 分配送货员",
        "ko": "👤 배달원 지정", "uk": "👤 Призначити кур'єра", "ar": "👤 تعيين موصل",
    },
    "rest_cambiar_estado": {
        "es": "🔄 Cambiar Estado", "gn": "🔄 Moambue Mba'éichapa", "pt": "🔄 Mudar Status",
        "en": "🔄 Change Status", "ru": "🔄 Изменить статус", "zh": "🔄 更改状态",
        "ko": "🔄 상태 변경", "uk": "🔄 Змінити статус", "ar": "🔄 تغيير الحالة",
    },
    "rest_nuevo_plato": {
        "es": "🍔➕ Nuevo Plato", "gn": "🍔➕ Tembi'u Pyahu", "pt": "🍔➕ Novo Prato", "en": "🍔➕ New Dish",
        "ru": "🍔➕ Новое блюдо", "zh": "🍔➕ 新菜品", "ko": "🍔➕ 새 메뉴", "uk": "🍔➕ Нова страва", "ar": "🍔➕ طبق جديد",
    },
    "rest_incluir_inactivos": {
        "es": "Incluir inactivos", "gn": "Omoĩve ndoikovéiva", "pt": "Incluir inativos",
        "en": "Include inactive", "ru": "Включить неактивные", "zh": "包括停用项",
        "ko": "비활성 포함", "uk": "Включити неактивні", "ar": "تضمين غير النشطة",
    },
    "rest_col_tipo": {
        "es": "TIPO", "gn": "TEKO", "pt": "TIPO", "en": "TYPE",
        "ru": "ТИП", "zh": "类型", "ko": "유형", "uk": "ТИП", "ar": "النوع",
    },
    "col_mesa": {
        "es": "MESA", "gn": "MESA", "pt": "MESA", "en": "TABLE",
        "ru": "СТОЛ", "zh": "桌台", "ko": "테이블", "uk": "СТІЛ", "ar": "الطاولة",
    },
    "col_cliente_mayus2": {
        "es": "CLIENTE", "gn": "CLIENTE", "pt": "CLIENTE", "en": "CLIENT",
        "ru": "КЛИЕНТ", "zh": "客户", "ko": "고객", "uk": "КЛІЄНТ", "ar": "العميل",
    },
    "rest_col_mozo": {
        "es": "MOZO/A", "gn": "MBOJERE", "pt": "GARÇOM", "en": "WAITER",
        "ru": "ОФИЦИАНТ", "zh": "服务员", "ko": "웨이터", "uk": "ОФІЦІАНТ", "ar": "النادل",
    },
    "rest_col_items": {
        "es": "ÍTEMS", "gn": "MBA'E", "pt": "ITENS", "en": "ITEMS",
        "ru": "ПОЗИЦИИ", "zh": "项目", "ko": "항목", "uk": "ПОЗИЦІЇ", "ar": "العناصر",
    },
    "col_total_mayus2": {
        "es": "TOTAL", "gn": "MANTEREI", "pt": "TOTAL", "en": "TOTAL",
        "ru": "ИТОГО", "zh": "总计", "ko": "합계", "uk": "РАЗОМ", "ar": "الإجمالي",
    },
    "rest_col_turno": {
        "es": "TURNO", "gn": "TURNO", "pt": "TURNO", "en": "SHIFT",
        "ru": "СМЕНА", "zh": "班次", "ko": "교대", "uk": "ЗМІНА", "ar": "الوردية",
    },
    "rest_col_apertura": {
        "es": "APERTURA", "gn": "ÑEPYRŨ", "pt": "ABERTURA", "en": "OPENED",
        "ru": "ОТКРЫТО", "zh": "开台时间", "ko": "개점", "uk": "ВІДКРИТО", "ar": "الفتح",
    },
    "rest_col_direccion_entrega": {
        "es": "DIRECCIÓN DE ENTREGA", "gn": "OĨHA OJEHUPYTY HAG̃UA", "pt": "ENDEREÇO DE ENTREGA",
        "en": "DELIVERY ADDRESS", "ru": "АДРЕС ДОСТАВКИ", "zh": "送货地址",
        "ko": "배달 주소", "uk": "АДРЕСА ДОСТАВКИ", "ar": "عنوان التوصيل",
    },
    "rest_col_repartidor": {
        "es": "REPARTIDOR", "gn": "RERAHÁVA", "pt": "ENTREGADOR", "en": "COURIER",
        "ru": "КУРЬЕР", "zh": "送货员", "ko": "배달원", "uk": "КУР'ЄР", "ar": "الموصل",
    },
    "rest_col_hora_pedido": {
        "es": "HORA PEDIDO", "gn": "ARY'I JEHEPYME'Ẽ", "pt": "HORA DO PEDIDO", "en": "ORDER TIME",
        "ru": "ВРЕМЯ ЗАКАЗА", "zh": "下单时间", "ko": "주문 시간", "uk": "ЧАС ЗАМОВЛЕННЯ", "ar": "وقت الطلب",
    },
    "rest_col_plato": {
        "es": "PLATO", "gn": "TEMBI'U", "pt": "PRATO", "en": "DISH",
        "ru": "БЛЮДО", "zh": "菜品", "ko": "메뉴", "uk": "СТРАВА", "ar": "الطبق",
    },
    "rest_col_categoria": {
        "es": "CATEGORÍA", "gn": "CATEGORÍA", "pt": "CATEGORIA", "en": "CATEGORY",
        "ru": "КАТЕГОРИЯ", "zh": "分类", "ko": "카테고리", "uk": "КАТЕГОРІЯ", "ar": "الفئة",
    },
    "rest_col_margen": {
        "es": "MARGEN", "gn": "MARGEN", "pt": "MARGEM", "en": "MARGIN",
        "ru": "МАРЖА", "zh": "利润", "ko": "마진", "uk": "МАРЖА", "ar": "الهامش",
    },
    "rest_col_margen_pct": {
        "es": "MARGEN %", "gn": "MARGEN %", "pt": "MARGEM %", "en": "MARGIN %",
        "ru": "МАРЖА %", "zh": "利润率", "ko": "마진율", "uk": "МАРЖА %", "ar": "نسبة الهامش",
    },
    "rest_agregar_plato": {
        "es": "🍔➕ Agregar Plato", "gn": "🍔➕ Ñemoĩ Tembi'u", "pt": "🍔➕ Adicionar Prato",
        "en": "🍔➕ Add Dish", "ru": "🍔➕ Добавить блюдо", "zh": "🍔➕ 添加菜品",
        "ko": "🍔➕ 메뉴 추가", "uk": "🍔➕ Додати страву", "ar": "🍔➕ إضافة طبق",
    },
    "rest_quitar": {
        "es": "🗑 Quitar", "gn": "🗑 Mboguete", "pt": "🗑 Remover", "en": "🗑 Remove",
        "ru": "🗑 Удалить", "zh": "🗑 移除", "ko": "🗑 제거", "uk": "🗑 Видалити", "ar": "🗑 إزالة",
    },
    "rest_personalizar": {
        "es": "🎨 Personalizar", "gn": "🎨 Mbojoja", "pt": "🎨 Personalizar", "en": "🎨 Customize",
        "ru": "🎨 Настроить", "zh": "🎨 自定义", "ko": "🎨 커스터마이즈", "uk": "🎨 Налаштувати", "ar": "🎨 تخصيص",
    },
    "rest_cancelar_comanda": {
        "es": "✕ Cancelar Comanda", "gn": "✕ Heja Comanda", "pt": "✕ Cancelar Comanda",
        "en": "✕ Cancel Order", "ru": "✕ Отменить заказ", "zh": "✕ 取消订单",
        "ko": "✕ 주문 취소", "uk": "✕ Скасувати замовлення", "ar": "✕ إلغاء الطلب",
    },
    "cerrar_ventana": {
        "es": "Cerrar Ventana", "gn": "Mboty Ovetã", "pt": "Fechar Janela", "en": "Close Window",
        "ru": "Закрыть окно", "zh": "关闭窗口", "ko": "창 닫기", "uk": "Закрити вікно", "ar": "إغلاق النافذة",
    },
    "rest_cerrar_cuenta_cobrar": {
        "es": "💳 Cerrar Cuenta / Cobrar", "gn": "💳 Mboty Cuenta / Ñemuha",
        "pt": "💳 Fechar Conta / Cobrar", "en": "💳 Close Bill / Charge",
        "ru": "💳 Закрыть счёт / Оплата", "zh": "💳 结账／收款",
        "ko": "💳 계산서 마감 / 결제", "uk": "💳 Закрити рахунок / Оплата", "ar": "💳 إغلاق الفاتورة / تحصيل",
    },
    "rest_col_tamano": {
        "es": "TAMAÑO", "gn": "TUICHAKUE", "pt": "TAMANHO", "en": "SIZE",
        "ru": "РАЗМЕР", "zh": "尺寸", "ko": "크기", "uk": "РОЗМІР", "ar": "الحجم",
    },
    "rest_col_precio": {
        "es": "PRECIO", "gn": "VIRU", "pt": "PREÇO", "en": "PRICE",
        "ru": "ЦЕНА", "zh": "价格", "ko": "가격", "uk": "ЦІНА", "ar": "السعر",
    },
    "rest_col_estado_cocina": {
        "es": "ESTADO COCINA", "gn": "COCINA MBA'ÉICHAPA", "pt": "STATUS COZINHA",
        "en": "KITCHEN STATUS", "ru": "СТАТУС КУХНИ", "zh": "厨房状态",
        "ko": "주방 상태", "uk": "СТАТУС КУХНІ", "ar": "حالة المطبخ",
    },
    "rest_col_tiempo": {
        "es": "TIEMPO", "gn": "ÁRA", "pt": "TEMPO", "en": "TIME",
        "ru": "ВРЕМЯ", "zh": "时间", "ko": "시간", "uk": "ЧАС", "ar": "الوقت",
    },
    "rest_col_observaciones": {
        "es": "OBSERVACIONES", "gn": "MBA'E JEHAI", "pt": "OBSERVAÇÕES", "en": "NOTES",
        "ru": "ПРИМЕЧАНИЯ", "zh": "备注", "ko": "비고", "uk": "ПРИМІТКИ", "ar": "ملاحظات",
    },
    "rest_nueva_mesa_titulo": {
        "es": "Nueva Mesa", "gn": "Mesa Pyahu", "pt": "Nova Mesa", "en": "New Table",
        "ru": "Новый стол", "zh": "新桌台", "ko": "새 테이블", "uk": "Новий стіл", "ar": "طاولة جديدة",
    },
    "rest_editar_mesa_titulo": {
        "es": "Editar Mesa", "gn": "Mesa Mbosako'i", "pt": "Editar Mesa", "en": "Edit Table",
        "ru": "Изменить стол", "zh": "编辑桌台", "ko": "테이블 편집", "uk": "Редагувати стіл", "ar": "تعديل الطاولة",
    },
    "rest_numero_nombre": {
        "es": "Número/Nombre:", "gn": "Papapy/Téra:", "pt": "Número/Nome:", "en": "Number/Name:",
        "ru": "Номер/Название:", "zh": "编号／名称：", "ko": "번호 / 이름:", "uk": "Номер/Назва:", "ar": "الرقم/الاسم:",
    },
    "rest_capacidad": {
        "es": "Capacidad (personas):", "gn": "Ikatúva (yvypóra):", "pt": "Capacidade (pessoas):",
        "en": "Capacity (people):", "ru": "Вместимость (человек):", "zh": "容量（人数）：",
        "ko": "수용 인원:", "uk": "Місткість (осіб):", "ar": "السعة (أشخاص):",
    },
    "rest_zona_sector": {
        "es": "Zona/Sector:", "gn": "Zona/Sector:", "pt": "Zona/Setor:", "en": "Zone/Section:",
        "ru": "Зона/Секция:", "zh": "区域／分区：", "ko": "구역 / 섹션:", "uk": "Зона/Секція:", "ar": "المنطقة/القسم:",
    },
    "rest_titulo_nuevo_pedido": {
        "es": "🛵 Nuevo Pedido", "gn": "🛵 Jehepyme'ẽ Pyahu", "pt": "🛵 Novo Pedido", "en": "🛵 New Order",
        "ru": "🛵 Новый заказ", "zh": "🛵 新订单", "ko": "🛵 새 주문", "uk": "🛵 Нове замовлення", "ar": "🛵 طلب جديد",
    },
    "rest_tipo_pedido": {
        "es": "Tipo de pedido:", "gn": "Jehepyme'ẽ Teko:", "pt": "Tipo de pedido:", "en": "Order type:",
        "ru": "Тип заказа:", "zh": "订单类型：", "ko": "주문 유형:", "uk": "Тип замовлення:", "ar": "نوع الطلب:",
    },
    "rest_direccion_entrega_label": {
        "es": "Dirección de entrega:", "gn": "Oĩha Ojehupyty Hag̃ua:", "pt": "Endereço de entrega:",
        "en": "Delivery address:", "ru": "Адрес доставки:", "zh": "送货地址：",
        "ko": "배달 주소:", "uk": "Адреса доставки:", "ar": "عنوان التوصيل:",
    },
    "rest_cliente_opcional": {
        "es": "Cliente (opcional):", "gn": "Cliente (ndaha'éiva tekotevẽ):", "pt": "Cliente (opcional):",
        "en": "Client (optional):", "ru": "Клиент (необязательно):", "zh": "客户（可选）：",
        "ko": "고객 (선택):", "uk": "Клієнт (необов'язково):", "ar": "العميل (اختياري):",
    },
    "rest_consumidor_final": {
        "es": "Consumidor Final", "gn": "Consumidor Final", "pt": "Consumidor Final", "en": "Final Consumer",
        "ru": "Конечный потребитель", "zh": "最终消费者", "ko": "최종 소비자", "uk": "Кінцевий споживач", "ar": "المستهلك النهائي",
    },
    "rest_abrir_comanda": {
        "es": "Abrir Comanda ➜", "gn": "Ehecha Comanda ➜", "pt": "Abrir Comanda ➜", "en": "Open Order ➜",
        "ru": "Открыть заказ ➜", "zh": "打开订单 ➜", "ko": "주문 열기 ➜", "uk": "Відкрити замовлення ➜", "ar": "فتح الطلب ➜",
    },
    "rest_agregar_plato_comanda": {
        "es": "🍔 Agregar Plato a la Comanda", "gn": "🍔 Ñemoĩ Tembi'u Comanda-pe",
        "pt": "🍔 Adicionar Prato à Comanda", "en": "🍔 Add Dish to Order",
        "ru": "🍔 Добавить блюдо к заказу", "zh": "🍔 添加菜品到订单",
        "ko": "🍔 주문에 메뉴 추가", "uk": "🍔 Додати страву до замовлення", "ar": "🍔 إضافة طبق إلى الطلب",
    },
    "rest_tamano_label": {
        "es": "Tamaño:", "gn": "Tuichakue:", "pt": "Tamanho:", "en": "Size:",
        "ru": "Размер:", "zh": "尺寸：", "ko": "크기:", "uk": "Розмір:", "ar": "الحجم:",
    },
    "cantidad_label": {
        "es": "Cantidad:", "gn": "Hetakue:", "pt": "Quantidade:", "en": "Quantity:",
        "ru": "Количество:", "zh": "数量：", "ko": "수량:", "uk": "Кількість:", "ar": "الكمية:",
    },
    "rest_agregar_boton": {
        "es": "➕ Agregar", "gn": "➕ Ñemoĩ", "pt": "➕ Adicionar", "en": "➕ Add",
        "ru": "➕ Добавить", "zh": "➕ 添加", "ko": "➕ 추가", "uk": "➕ Додати", "ar": "➕ إضافة",
    },
    "rest_cliente_label": {
        "es": "Cliente:", "gn": "Cliente:", "pt": "Cliente:", "en": "Client:",
        "ru": "Клиент:", "zh": "客户：", "ko": "고객:", "uk": "Клієнт:", "ar": "العميل:",
    },
    "rest_cambiar_cliente": {
        "es": "🔍 Cambiar Cliente", "gn": "🔍 Moambue Cliente", "pt": "🔍 Trocar Cliente",
        "en": "🔍 Change Client", "ru": "🔍 Сменить клиента", "zh": "🔍 更换客户",
        "ko": "🔍 고객 변경", "uk": "🔍 Змінити клієнта", "ar": "🔍 تغيير العميل",
    },
    "rest_condicion_venta": {
        "es": "Condición de venta:", "gn": "Ñemuha Mba'éichapa:", "pt": "Condição de venda:",
        "en": "Sale condition:", "ru": "Условие продажи:", "zh": "销售条件：",
        "ko": "판매 조건:", "uk": "Умова продажу:", "ar": "شرط البيع:",
    },
    "rest_forma_pago_label": {
        "es": "Forma de pago:", "gn": "Jehepyme'ẽ Reko:", "pt": "Forma de pagamento:",
        "en": "Payment method:", "ru": "Способ оплаты:", "zh": "付款方式：",
        "ko": "결제 방법:", "uk": "Спосіб оплати:", "ar": "طريقة الدفع:",
    },
    "rest_confirmar_cobro": {
        "es": "✔ Confirmar Cobro", "gn": "✔ Confirmar Ñemuha", "pt": "✔ Confirmar Cobrança",
        "en": "✔ Confirm Payment", "ru": "✔ Подтвердить оплату", "zh": "✔ 确认收款",
        "ko": "✔ 결제 확인", "uk": "✔ Підтвердити оплату", "ar": "✔ تأكيد الدفع",
    },
    "rest_procesando": {
        "es": "Procesando...", "gn": "Ojejapo...", "pt": "Processando...", "en": "Processing...",
        "ru": "Обработка...", "zh": "处理中...", "ko": "처리 중...", "uk": "Обробка...", "ar": "جارٍ المعالجة...",
    },
    "rest_precio_venta_gs": {
        "es": "Precio de Venta (Gs):", "gn": "Precio Ñemuha (Gs):", "pt": "Preço de Venda (Gs):",
        "en": "Sale Price (Gs):", "ru": "Цена продажи (Gs):", "zh": "销售价格 (Gs)：",
        "ko": "판매 가격 (Gs):", "uk": "Ціна продажу (Gs):", "ar": "سعر البيع (Gs):",
    },
    "rest_tiempo_prep": {
        "es": "Tiempo Prep. (min):", "gn": "Ára Apo (min):", "pt": "Tempo Preparo (min):",
        "en": "Prep Time (min):", "ru": "Время приготовления (мин):", "zh": "准备时间（分钟）：",
        "ko": "조리 시간 (분):", "uk": "Час приготування (хв):", "ar": "وقت التحضير (دقيقة):",
    },
    "descripcion_label": {
        "es": "Descripción:", "gn": "Mba'e Rehegua:", "pt": "Descrição:", "en": "Description:",
        "ru": "Описание:", "zh": "描述：", "ko": "설명:", "uk": "Опис:", "ar": "الوصف:",
    },
    "rest_insumos_consume": {
        "es": "Insumos que consume este plato (tamaño base)",
        "gn": "Mba'e ojeporúva ko tembi'u-pe (tuichakue base)",
        "pt": "Insumos que este prato consome (tamanho base)",
        "en": "Ingredients this dish uses (base size)",
        "ru": "Ингредиенты этого блюда (базовый размер)",
        "zh": "该菜品所用原料（基础份量）",
        "ko": "이 메뉴가 사용하는 재료 (기본 사이즈)",
        "uk": "Інгредієнти цієї страви (базовий розмір)",
        "ar": "المكونات التي يستخدمها هذا الطبق (الحجم الأساسي)",
    },
    "rest_agregar_insumo": {
        "es": "➕ Agregar Insumo", "gn": "➕ Ñemoĩ Mba'e", "pt": "➕ Adicionar Insumo",
        "en": "➕ Add Ingredient", "ru": "➕ Добавить ингредиент", "zh": "➕ 添加原料",
        "ko": "➕ 재료 추가", "uk": "➕ Додати інгредієнт", "ar": "➕ إضافة مكوّن",
    },
    "rest_quitar_insumo": {
        "es": "🗑 Quitar Insumo", "gn": "🗑 Mboguete Mba'e", "pt": "🗑 Remover Insumo",
        "en": "🗑 Remove Ingredient", "ru": "🗑 Удалить ингредиент", "zh": "🗑 移除原料",
        "ko": "🗑 재료 제거", "uk": "🗑 Видалити інгредієнт", "ar": "🗑 إزالة مكوّن",
    },
    "rest_tamanos_disponibles": {
        "es": "Tamaños disponibles (ej. Individual, Mediana, Familiar). Si no cargás ninguno, el plato se vende solo al precio y receta base.",
        "gn": "Tuichakue oĩva (techapyrã Individual, Mediana, Familiar). Ndereikuaái mba'eve, tembi'u ojeguerúta precio ha receta base-pe año.",
        "pt": "Tamanhos disponíveis (ex. Individual, Média, Família). Se não cadastrar nenhum, o prato é vendido apenas pelo preço e receita base.",
        "en": "Available sizes (e.g. Single, Medium, Family). If you don't add any, the dish is sold only at the base price and recipe.",
        "ru": "Доступные размеры (напр. Одна порция, Средняя, Семейная). Если не добавить ни одного, блюдо продаётся только по базовой цене и рецепту.",
        "zh": "可选尺寸（例如：单人、中份、家庭份）。如果不添加任何尺寸，该菜品将仅按基础价格和配方销售。",
        "ko": "사용 가능한 사이즈 (예: 1인분, 중, 패밀리). 추가하지 않으면 메뉴는 기본 가격과 레시피로만 판매됩니다.",
        "uk": "Доступні розміри (напр. Одна порція, Середня, Сімейна). Якщо не додати жодного, страва продається лише за базовою ціною і рецептом.",
        "ar": "الأحجام المتاحة (مثال: فردي، متوسط، عائلي). إذا لم تُضف أيًا، يُباع الطبق بالسعر والوصفة الأساسية فقط.",
    },
    "rest_agregar_tamano": {
        "es": "➕ Agregar Tamaño", "gn": "➕ Ñemoĩ Tuichakue", "pt": "➕ Adicionar Tamanho",
        "en": "➕ Add Size", "ru": "➕ Добавить размер", "zh": "➕ 添加尺寸",
        "ko": "➕ 사이즈 추가", "uk": "➕ Додати розмір", "ar": "➕ إضافة حجم",
    },
    "rest_quitar_tamano": {
        "es": "🗑 Quitar Tamaño", "gn": "🗑 Mboguete Tuichakue", "pt": "🗑 Remover Tamanho",
        "en": "🗑 Remove Size", "ru": "🗑 Удалить размер", "zh": "🗑 移除尺寸",
        "ko": "🗑 사이즈 제거", "uk": "🗑 Видалити розмір", "ar": "🗑 إزالة الحجم",
    },
    "rest_desactivar_plato": {
        "es": "🚫 Desactivar Plato", "gn": "🚫 Mboguepa Tembi'u", "pt": "🚫 Desativar Prato",
        "en": "🚫 Deactivate Dish", "ru": "🚫 Деактивировать блюдо", "zh": "🚫 停用菜品",
        "ko": "🚫 메뉴 비활성화", "uk": "🚫 Деактивувати страву", "ar": "🚫 إلغاء تفعيل الطبق",
    },
    "rest_activar_plato": {
        "es": "✔ Activar Plato", "gn": "✔ Moĩmba'e Tembi'u", "pt": "✔ Ativar Prato",
        "en": "✔ Activate Dish", "ru": "✔ Активировать блюдо", "zh": "✔ 启用菜品",
        "ko": "✔ 메뉴 활성화", "uk": "✔ Активувати страву", "ar": "✔ تفعيل الطبق",
    },
    "rest_repartidores_titulo": {
        "es": "🏍 Repartidores", "gn": "🏍 Reraháva", "pt": "🏍 Entregadores", "en": "🏍 Couriers",
        "ru": "🏍 Курьеры", "zh": "🏍 送货员", "ko": "🏍 배달원", "uk": "🏍 Кур'єри", "ar": "🏍 الموصلون",
    },
    "vehiculo_label": {
        "es": "Vehículo:", "gn": "Ta'angambyry:", "pt": "Veículo:", "en": "Vehicle:",
        "ru": "Транспорт:", "zh": "车辆：", "ko": "차량:", "uk": "Транспорт:", "ar": "المركبة:",
    },
    "rest_activar_desactivar_sel": {
        "es": "🚫 Activar/Desactivar Seleccionado", "gn": "🚫 Moĩmba'e/Mboguepa Poravopyre",
        "pt": "🚫 Ativar/Desativar Selecionado", "en": "🚫 Activate/Deactivate Selected",
        "ru": "🚫 Активировать/Деактивировать выбранное", "zh": "🚫 启用／停用所选",
        "ko": "🚫 선택 항목 활성화/비활성화", "uk": "🚫 Активувати/Деактивувати вибране", "ar": "🚫 تفعيل/إلغاء تفعيل المحدد",
    },
    "col_nombre_mayus": {
        "es": "NOMBRE", "gn": "TÉRA", "pt": "NOME", "en": "NAME",
        "ru": "ИМЯ", "zh": "姓名", "ko": "이름", "uk": "ІМ'Я", "ar": "الاسم",
    },
    "col_vehiculo_mayus": {
        "es": "VEHÍCULO", "gn": "TA'ANGAMBYRY", "pt": "VEÍCULO", "en": "VEHICLE",
        "ru": "ТРАНСПОРТ", "zh": "车辆", "ko": "차량", "uk": "ТРАНСПОРТ", "ar": "المركبة",
    },
    "rest_elegir_quien_entrega": {
        "es": "Elegí quién va a entregar este pedido:", "gn": "Eiporavo mávapa oreraháta ko jehepyme'ẽ:",
        "pt": "Escolha quem vai entregar este pedido:", "en": "Choose who will deliver this order:",
        "ru": "Выберите, кто доставит этот заказ:", "zh": "选择谁来配送此订单：",
        "ko": "이 주문을 배달할 사람을 선택하세요:", "uk": "Виберіть, хто доставить це замовлення:",
        "ar": "اختر من سيقوم بتوصيل هذا الطلب:",
    },
    "rest_asignar": {
        "es": "✔ Asignar", "gn": "✔ Ame'ẽ", "pt": "✔ Atribuir", "en": "✔ Assign",
        "ru": "✔ Назначить", "zh": "✔ 分配", "ko": "✔ 지정", "uk": "✔ Призначити", "ar": "✔ تعيين",
    },
    "rest_nombre_ej_tamano": {
        "es": "Nombre (ej. Individual, Familiar):", "gn": "Téra (techapyrã Individual, Familiar):",
        "pt": "Nome (ex. Individual, Família):", "en": "Name (e.g. Single, Family):",
        "ru": "Название (напр. Одна порция, Семейная):", "zh": "名称（例如：单人、家庭份）：",
        "ko": "이름 (예: 1인분, 패밀리):", "uk": "Назва (напр. Одна порція, Сімейна):", "ar": "الاسم (مثال: فردي، عائلي):",
    },
    "rest_precio_venta_gs2": {
        "es": "Precio de venta (Gs):", "gn": "Precio ñemuha (Gs):", "pt": "Preço de venda (Gs):",
        "en": "Sale price (Gs):", "ru": "Цена продажи (Gs):", "zh": "销售价格 (Gs)：",
        "ko": "판매 가격 (Gs):", "uk": "Ціна продажу (Gs):", "ar": "سعر البيع (Gs):",
    },
    "rest_multiplicador_receta": {
        "es": "Multiplicador de receta:", "gn": "Multiplicador Receta:", "pt": "Multiplicador de receita:",
        "en": "Recipe multiplier:", "ru": "Множитель рецепта:", "zh": "配方倍数：",
        "ko": "레시피 배수:", "uk": "Множник рецепта:", "ar": "مضاعف الوصفة:",
    },
    "rest_multiplicador_ayuda": {
        "es": "(cuánto más/menos insumo consume que el tamaño base; ej. 1.8 para Familiar)",
        "gn": "(mboyve/mboyvéve mba'e ojeporu tuichakue base-gui; techapyrã 1.8 Familiar-pe)",
        "pt": "(quanto mais/menos insumo consome que o tamanho base; ex. 1.8 para Família)",
        "en": "(how much more/less ingredient it uses than the base size; e.g. 1.8 for Family)",
        "ru": "(насколько больше/меньше ингредиентов расходуется по сравнению с базовым размером; напр. 1.8 для Семейной)",
        "zh": "（相比基础份量多用或少用多少原料；例如家庭份为1.8）",
        "ko": "(기본 사이즈보다 재료를 얼마나 더/덜 쓰는지; 예: 패밀리는 1.8)",
        "uk": "(наскільки більше/менше інгредієнтів витрачається порівняно з базовим розміром; напр. 1.8 для Сімейної)",
        "ar": "(مقدار المكوّن الأكثر/الأقل المستخدم مقارنة بالحجم الأساسي؛ مثال: 1.8 للعائلي)",
    },
    "rest_elegir_insumo_titulo": {
        "es": "🥕 Elegir Insumo", "gn": "🥕 Eiporavo Mba'e", "pt": "🥕 Escolher Insumo",
        "en": "🥕 Choose Ingredient", "ru": "🥕 Выбрать ингредиент", "zh": "🥕 选择原料",
        "ko": "🥕 재료 선택", "uk": "🥕 Вибрати інгредієнт", "ar": "🥕 اختيار مكوّن",
    },
    "rest_crear_insumo_nuevo": {
        "es": "➕ Crear Insumo Nuevo", "gn": "➕ Mba'e Pyahu Apo", "pt": "➕ Criar Insumo Novo",
        "en": "➕ Create New Ingredient", "ru": "➕ Создать новый ингредиент", "zh": "➕ 创建新原料",
        "ko": "➕ 새 재료 만들기", "uk": "➕ Створити новий інгредієнт", "ar": "➕ إنشاء مكوّن جديد",
    },
    "rest_sin_insumos": {
        "es": "Todavía no tenés ningún insumo cargado en Productos.\nUsá el botón '➕ Crear Insumo Nuevo' de arriba para cargar el primero\n(harina, queso, salsa, una gaseosa, un jugo, lo que necesites).",
        "gn": "Ndaipóri gueteri mba'e emoĩva Productos-pe.\nEipuru '➕ Mba'e Pyahu Apo' yvate guive emoĩ hag̃ua peteĩha\n(harina, queso, salsa, gaseosa, jugo, mba'épa reikotevẽva).",
        "pt": "Você ainda não tem nenhum insumo cadastrado em Produtos.\nUse o botão '➕ Criar Insumo Novo' acima para cadastrar o primeiro\n(farinha, queijo, molho, um refrigerante, um suco, o que precisar).",
        "en": "You don't have any ingredients loaded in Products yet.\nUse the '➕ Create New Ingredient' button above to add the first one\n(flour, cheese, sauce, a soda, a juice, whatever you need).",
        "ru": "У вас пока нет ни одного ингредиента в разделе Товары.\nИспользуйте кнопку «➕ Создать новый ингредиент» выше, чтобы добавить первый\n(мука, сыр, соус, газировка, сок — что угодно).",
        "zh": "您在产品中尚未添加任何原料。\n使用上方的\"➕ 创建新原料\"按钮添加第一个\n（面粉、奶酪、酱料、汽水、果汁，任何您需要的）。",
        "ko": "아직 상품에 등록된 재료가 없습니다.\n위의 '➕ 새 재료 만들기' 버튼을 사용해 첫 재료를 추가하세요\n(밀가루, 치즈, 소스, 탄산음료, 주스 등 필요한 것).",
        "uk": "У вас ще немає жодного інгредієнта в розділі Товари.\nВикористайте кнопку «➕ Створити новий інгредієнт» вище, щоб додати перший\n(борошно, сир, соус, газована вода, сік — що завгодно).",
        "ar": "ليس لديك أي مكوّن محمّل في المنتجات بعد.\nاستخدم زر '➕ إنشاء مكوّن جديد' أعلاه لإضافة الأول\n(دقيق، جبن، صلصة، مشروب غازي، عصير، أي شيء تحتاجه).",
    },
    "rest_cantidad_que_usa": {
        "es": "Cantidad que usa este plato:", "gn": "Hetakue ojeporúva ko tembi'u-pe:",
        "pt": "Quantidade que este prato usa:", "en": "Quantity this dish uses:",
        "ru": "Количество, используемое этим блюдом:", "zh": "此菜品使用的数量：",
        "ko": "이 메뉴가 사용하는 수량:", "uk": "Кількість, яку використовує ця страва:", "ar": "الكمية التي يستخدمها هذا الطبق:",
    },
    "col_insumo_mayus": {
        "es": "INSUMO", "gn": "MBA'E", "pt": "INSUMO", "en": "INGREDIENT",
        "ru": "ИНГРЕДИЕНТ", "zh": "原料", "ko": "재료", "uk": "ІНГРЕДІЄНТ", "ar": "المكوّن",
    },
    "col_unidad_mayus": {
        "es": "UNIDAD", "gn": "PETEĨTEĨ", "pt": "UNIDADE", "en": "UNIT",
        "ru": "ЕДИНИЦА", "zh": "单位", "ko": "단위", "uk": "ОДИНИЦЯ", "ar": "الوحدة",
    },
    "col_costo_unit": {
        "es": "COSTO UNIT.", "gn": "VIRU PETEĨTEĨ", "pt": "CUSTO UNIT.", "en": "UNIT COST",
        "ru": "СТОИМ. ЗА ЕД.", "zh": "单位成本", "ko": "단가", "uk": "ВАРТІСТЬ ЗА ОД.", "ar": "تكلفة الوحدة",
    },
    "col_stock_mayus2": {
        "es": "STOCK", "gn": "STOCK", "pt": "ESTOQUE", "en": "STOCK",
        "ru": "ОСТАТОК", "zh": "库存", "ko": "재고", "uk": "ЗАЛИШОК", "ar": "المخزون",
    },
    "rest_agregar_ingrediente_extra": {
        "es": "➕ Agregar Ingrediente Extra", "gn": "➕ Ñemoĩ Mba'e Hetave",
        "pt": "➕ Adicionar Ingrediente Extra", "en": "➕ Add Extra Ingredient",
        "ru": "➕ Добавить доп. ингредиент", "zh": "➕ 添加额外原料",
        "ko": "➕ 추가 재료 넣기", "uk": "➕ Додати додатковий інгредієнт", "ar": "➕ إضافة مكوّن إضافي",
    },
    "rest_quitar_ingrediente_receta": {
        "es": "➖ Quitar un Ingrediente de la Receta", "gn": "➖ Mboguete Mba'e Receta-gui",
        "pt": "➖ Remover um Ingrediente da Receita", "en": "➖ Remove an Ingredient from the Recipe",
        "ru": "➖ Убрать ингредиент из рецепта", "zh": "➖ 从配方中移除原料",
        "ko": "➖ 레시피에서 재료 제거", "uk": "➖ Прибрати інгредієнт з рецепта", "ar": "➖ إزالة مكوّن من الوصفة",
    },
    "rest_col_tipo2": {
        "es": "TIPO", "gn": "TEKO", "pt": "TIPO", "en": "TYPE",
        "ru": "ТИП", "zh": "类型", "ko": "유형", "uk": "ТИП", "ar": "النوع",
    },
    "col_ingrediente_mayus": {
        "es": "INGREDIENTE", "gn": "MBA'E", "pt": "INGREDIENTE", "en": "INGREDIENT",
        "ru": "ИНГРЕДИЕНТ", "zh": "配料", "ko": "재료", "uk": "ІНГРЕДІЄНТ", "ar": "المكوّن",
    },
    "rest_col_recargo": {
        "es": "RECARGO", "gn": "MOÎVEVE", "pt": "ACRÉSCIMO", "en": "SURCHARGE",
        "ru": "НАДБАВКА", "zh": "附加费", "ko": "추가 요금", "uk": "НАДБАВКА", "ar": "الرسم الإضافي",
    },
    "rest_quitar_personalizacion": {
        "es": "🗑 Quitar esta personalización", "gn": "🗑 Mboguete ko mbojoja",
        "pt": "🗑 Remover esta personalização", "en": "🗑 Remove this customization",
        "ru": "🗑 Удалить эту настройку", "zh": "🗑 移除此定制",
        "ko": "🗑 이 커스터마이즈 제거", "uk": "🗑 Видалити це налаштування", "ar": "🗑 إزالة هذا التخصيص",
    },
    "rest_que_ingrediente_quitar": {
        "es": "¿Qué ingrediente de la receta querés quitar de este pedido?",
        "gn": "Mba'e ingrediente receta-gui reipotápa emboguete ko jehepyme'ẽ-gui?",
        "pt": "Que ingrediente da receita você quer remover deste pedido?",
        "en": "Which recipe ingredient do you want to remove from this order?",
        "ru": "Какой ингредиент рецепта убрать из этого заказа?",
        "zh": "您想从此订单中移除哪种配方原料？",
        "ko": "이 주문에서 어떤 레시피 재료를 제거하시겠습니까?",
        "uk": "Який інгредієнт рецепта прибрати з цього замовлення?",
        "ar": "ما هو مكوّن الوصفة الذي تريد إزالته من هذا الطلب؟",
    },
    "rest_quitar_confirmar": {
        "es": "✔ Quitar", "gn": "✔ Mboguete", "pt": "✔ Remover", "en": "✔ Remove",
        "ru": "✔ Удалить", "zh": "✔ 移除", "ko": "✔ 제거", "uk": "✔ Видалити", "ar": "✔ إزالة",
    },
    "rest_recargo_a_cobrar": {
        "es": "Recargo a cobrar (Gs):", "gn": "Moîveve ojehepyme'ẽva (Gs):", "pt": "Acréscimo a cobrar (Gs):",
        "en": "Surcharge to charge (Gs):", "ru": "Взимаемая надбавка (Gs):", "zh": "应收附加费 (Gs)：",
        "ko": "청구할 추가 요금 (Gs):", "uk": "Надбавка до сплати (Gs):", "ar": "الرسم الإضافي المطلوب (Gs):",
    },
    "confirmar_icono": {
        "es": "✔ Confirmar", "gn": "✔ Confirmar", "pt": "✔ Confirmar", "en": "✔ Confirm",
        "ru": "✔ Подтвердить", "zh": "✔ 确认", "ko": "✔ 확인", "uk": "✔ Підтвердити", "ar": "✔ تأكيد",
    },
    "rest_crear_insumo_titulo": {
        "es": "➕ Crear Insumo Nuevo", "gn": "➕ Mba'e Pyahu Apo", "pt": "➕ Criar Insumo Novo",
        "en": "➕ Create New Ingredient", "ru": "➕ Создать новый ингредиент", "zh": "➕ 创建新原料",
        "ko": "➕ 새 재료 만들기", "uk": "➕ Створити новий інгредієнт", "ar": "➕ إنشاء مكوّن جديد",
    },
    "rest_nombre_ej_insumo": {
        "es": "Nombre (ej. HARINA, QUESO MUZZARELLA, SALSA DE TOMATE):",
        "gn": "Téra (techapyrã HARINA, QUESO MUZZARELLA, SALSA DE TOMATE):",
        "pt": "Nome (ex. FARINHA, QUEIJO MUÇARELA, MOLHO DE TOMATE):",
        "en": "Name (e.g. FLOUR, MOZZARELLA CHEESE, TOMATO SAUCE):",
        "ru": "Название (напр. МУКА, СЫР МОЦАРЕЛЛА, ТОМАТНЫЙ СОУС):",
        "zh": "名称（例如：面粉、马苏里拉奶酪、番茄酱）：",
        "ko": "이름 (예: 밀가루, 모짜렐라 치즈, 토마토 소스):",
        "uk": "Назва (напр. БОРОШНО, СИР МОЦАРЕЛА, ТОМАТНИЙ СОУС):",
        "ar": "الاسم (مثال: دقيق، جبن موزاريلا، صلصة طماطم):",
    },
    "rest_se_mide_por": {
        "es": "Se mide por:", "gn": "Ojejapyhy péicha:", "pt": "É medido por:", "en": "Measured by:",
        "ru": "Измеряется в:", "zh": "计量单位：", "ko": "측정 단위:", "uk": "Вимірюється в:", "ar": "يُقاس بـ:",
    },
    "rest_se_mide_por_ayuda": {
        "es": "('Litro' para bebidas/jugos a granel; 'Unidad' si se compra por paquete/pieza y se usa de a botellas/latas enteras)",
        "gn": "('Litro' y'uhéi/jugo granel-pe; 'Unidad' ojejogua paquete/peteĩ-cha ha ojeporu botella/lata mbytépe)",
        "pt": "('Litro' para bebidas/sucos a granel; 'Unidade' se comprado por pacote/peça e usado em garrafas/latas inteiras)",
        "en": "('Liter' for bulk drinks/juices; 'Unit' if bought by package/piece and used as whole bottles/cans)",
        "ru": "(«Литр» для напитков/соков на разлив; «Единица» при покупке упаковками/штуками и использовании целыми бутылками/банками)",
        "zh": "（散装饮料/果汁用\"升\"；按包装/件购买且以整瓶/整罐使用用\"件\"）",
        "ko": "('리터'는 벌크 음료/주스용; '단위'는 포장/개당 구매 후 병/캔 단위로 사용할 때)",
        "uk": "(«Літр» для напоїв/соків на розлив; «Одиниця», якщо купується упаковками/штуками і використовується цілими пляшками/банками)",
        "ar": "('لتر' للمشروبات/العصائر السائبة؛ 'وحدة' إذا اشتُريت بالعبوة/القطعة واستُخدمت كزجاجات/علب كاملة)",
    },
    "rest_costo_compra": {
        "es": "Costo de compra (Gs, por unidad/litro/kg):", "gn": "Viru jejogua (Gs, peteĩteĩ/litro/kg-pe):",
        "pt": "Custo de compra (Gs, por unidade/litro/kg):", "en": "Purchase cost (Gs, per unit/liter/kg):",
        "ru": "Закупочная стоимость (Gs, за ед./литр/кг):", "zh": "采购成本（Gs，每单位／升／千克）：",
        "ko": "구매 비용 (Gs, 단위/리터/kg당):", "uk": "Закупівельна вартість (Gs, за од./літр/кг):", "ar": "تكلفة الشراء (Gs، لكل وحدة/لتر/كجم):",
    },
    "rest_stock_inicial": {
        "es": "Stock inicial:", "gn": "Stock ñepyrũha:", "pt": "Estoque inicial:", "en": "Initial stock:",
        "ru": "Начальный остаток:", "zh": "初始库存：", "ko": "초기 재고:", "uk": "Початковий залишок:", "ar": "المخزون الأولي:",
    },
    "rest_crear_insumo_boton": {
        "es": "💾 Crear Insumo", "gn": "💾 Mba'e Apo", "pt": "💾 Criar Insumo", "en": "💾 Create Ingredient",
        "ru": "💾 Создать ингредиент", "zh": "💾 创建原料", "ko": "💾 재료 만들기", "uk": "💾 Створити інгредієнт", "ar": "💾 إنشاء مكوّن",
    },
    "ventas_total_del_dia": {
        "es": "Total del día: {signo} Gs. {total}", "gn": "Ára Manterei: {signo} Gs. {total}",
        "pt": "Total do dia: {signo} Gs. {total}", "en": "Day total: {signo} Gs. {total}",
        "ru": "Итого за день: {signo} Gs. {total}", "zh": "当日总计：{signo} Gs. {total}",
        "ko": "일일 합계: {signo} Gs. {total}", "uk": "Всього за день: {signo} Gs. {total}", "ar": "إجمالي اليوم: {signo} Gs. {total}",
    },

    # ── Compras (formulario interno) ─────────────────────────────
    "compras_titulo_barra": {
        "es": "Compras", "gn": "Jejogua", "pt": "Compras", "en": "Purchases",
        "ru": "Закупки", "zh": "采购", "ko": "구매", "uk": "Закупівлі", "ar": "المشتريات",
    },
    "compras_codigo_producto": {
        "es": "Código del Producto:", "gn": "Mba'e Código:", "pt": "Código do Produto:",
        "en": "Product Code:", "ru": "Код товара:", "zh": "产品代码：",
        "ko": "상품 코드:", "uk": "Код товару:", "ar": "رمز المنتج:",
    },
    "compras_guardar_compra": {
        "es": "💾 Guardar Compra", "gn": "💾 Ñongatu Jejogua", "pt": "💾 Salvar Compra",
        "en": "💾 Save Purchase", "ru": "💾 Сохранить закупку", "zh": "💾 保存采购",
        "ko": "💾 구매 저장", "uk": "💾 Зберегти закупівлю", "ar": "💾 حفظ الشراء",
    },
    "compras_productos_en_compra": {
        "es": "{n} productos en la compra.", "gn": "{n} mba'e jejogua-pe.",
        "pt": "{n} produtos na compra.", "en": "{n} products in the purchase.",
        "ru": "{n} товаров в закупке.", "zh": "采购中有{n}件产品。",
        "ko": "구매에 {n}개 상품.", "uk": "{n} товарів у закупівлі.", "ar": "{n} منتج في عملية الشراء.",
    },
    "compras_fecha_label": {
        "es": "Fecha:", "gn": "Ára:", "pt": "Data:", "en": "Date:",
        "ru": "Дата:", "zh": "日期：", "ko": "날짜:", "uk": "Дата:", "ar": "التاريخ:",
    },
    "compras_fecha_compra_label": {
        "es": "Fecha Compra:", "gn": "Ára Jejogua:", "pt": "Data da Compra:", "en": "Purchase Date:",
        "ru": "Дата закупки:", "zh": "采购日期：", "ko": "구매 날짜:", "uk": "Дата закупівлі:", "ar": "تاريخ الشراء:",
    },
    "compras_nro_comprobante_label": {
        "es": "N° Comprobante:", "gn": "N° Comprobante:", "pt": "N° Comprovante:", "en": "Receipt No.:",
        "ru": "№ чека:", "zh": "凭证号：", "ko": "영수증 번호:", "uk": "№ чека:", "ar": "رقم الإيصال:",
    },
    "compras_proveedor_label": {
        "es": "Proveedor:", "gn": "Proveedor:", "pt": "Fornecedor:", "en": "Supplier:",
        "ru": "Поставщик:", "zh": "供应商：", "ko": "공급업체:", "uk": "Постачальник:", "ar": "المورد:",
    },
    "compras_nuevo_proveedor": {
        "es": "+ Nuevo", "gn": "+ Pyahu", "pt": "+ Novo", "en": "+ New",
        "ru": "+ Новый", "zh": "+ 新建", "ko": "+ 신규", "uk": "+ Новий", "ar": "+ جديد",
    },
    "compras_precio_de_compra": {
        "es": "Precio de Compra:", "gn": "Precio Jejogua:", "pt": "Preço de Compra:", "en": "Purchase Price:",
        "ru": "Цена закупки:", "zh": "进货价格：", "ko": "구매 가격:", "uk": "Ціна закупівлі:", "ar": "سعر الشراء:",
    },
    "aceptar_icono": {
        "es": "✔ Aceptar", "gn": "✔ Ehẽ", "pt": "✔ Aceitar", "en": "✔ Accept",
        "ru": "✔ Принять", "zh": "✔ 接受", "ko": "✔ 수락", "uk": "✔ Прийняти", "ar": "✔ قبول",
    },
    "compras_buscar_producto_titulo": {
        "es": "Buscar Producto", "gn": "Heka Mba'e", "pt": "Buscar Produto", "en": "Search Product",
        "ru": "Поиск товара", "zh": "搜索产品", "ko": "상품 검색", "uk": "Пошук товару", "ar": "بحث عن منتج",
    },
    "compras_enter_agregar": {
        "es": "ENTER - Agregar", "gn": "ENTER - Ñemoĩ", "pt": "ENTER - Adicionar", "en": "ENTER - Add",
        "ru": "ENTER - Добавить", "zh": "回车 - 添加", "ko": "ENTER - 추가", "uk": "ENTER - Додати", "ar": "إدخال - إضافة",
    },
    "compras_esc_cancelar": {
        "es": "ESC - Cancelar", "gn": "ESC - Heja", "pt": "ESC - Cancelar", "en": "ESC - Cancel",
        "ru": "ESC - Отмена", "zh": "ESC - 取消", "ko": "ESC - 취소", "uk": "ESC - Скасувати", "ar": "ESC - إلغاء",
    },

    # ── Ventanas auxiliares de Ventas (Buscar Producto, Asignar Cliente, etc.) ──
    "aux_buscar_producto_f2": {
        "es": "Buscar Producto (F2)", "gn": "Heka Mba'e (F2)", "pt": "Buscar Produto (F2)",
        "en": "Search Product (F2)", "ru": "Поиск товара (F2)", "zh": "搜索产品 (F2)",
        "ko": "상품 검색 (F2)", "uk": "Пошук товару (F2)", "ar": "بحث عن منتج (F2)",
    },
    "col_p_mayorista_mayus": {
        "es": "P. MAYORISTA", "gn": "P. MAYORISTA", "pt": "P. ATACADO", "en": "WHOLESALE PRICE",
        "ru": "ОПТ. ЦЕНА", "zh": "批发价", "ko": "도매가", "uk": "ОПТ. ЦІНА", "ar": "سعر الجملة",
    },
    "aux_p_minorista": {
        "es": "P. MINORISTA", "gn": "P. MINORISTA", "pt": "P. VAREJO", "en": "RETAIL PRICE",
        "ru": "РОЗН. ЦЕНА", "zh": "零售价", "ko": "소매가", "uk": "РОЗД. ЦІНА", "ar": "سعر التجزئة",
    },
    "seleccionar_boton": {
        "es": "Seleccionar", "gn": "Eiporavo", "pt": "Selecionar", "en": "Select",
        "ru": "Выбрать", "zh": "选择", "ko": "선택", "uk": "Вибрати", "ar": "اختيار",
    },
    "aux_producto_comun": {
        "es": "Producto Común", "gn": "Mba'e Ojeporúva", "pt": "Produto Comum", "en": "Common Product",
        "ru": "Обычный товар", "zh": "常用产品", "ko": "일반 상품", "uk": "Звичайний товар", "ar": "منتج عام",
    },
    "aux_descripcion_producto": {
        "es": "Descripción del Producto:", "gn": "Mba'e Rehegua:", "pt": "Descrição do Produto:",
        "en": "Product Description:", "ru": "Описание товара:", "zh": "产品描述：",
        "ko": "상품 설명:", "uk": "Опис товару:", "ar": "وصف المنتج:",
    },
    "precio_unitario_label": {
        "es": "Precio Unitario:", "gn": "Precio Peteĩ:", "pt": "Preço Unitário:", "en": "Unit Price:",
        "ru": "Цена за ед.:", "zh": "单价：", "ko": "단가:", "uk": "Ціна за од.:", "ar": "سعر الوحدة:",
    },
    "aceptar_boton": {
        "es": "✔ Aceptar", "gn": "✔ Ehecha", "pt": "✔ Aceitar", "en": "✔ Accept",
        "ru": "✔ Принять", "zh": "✔ 接受", "ko": "✔ 확인", "uk": "✔ Прийняти", "ar": "✔ قبول",
    },
    "aux_asignar_cliente_f1": {
        "es": "Asignar Cliente (F1)", "gn": "Ame'ẽ Cliente (F1)", "pt": "Atribuir Cliente (F1)",
        "en": "Assign Client (F1)", "ru": "Назначить клиента (F1)", "zh": "分配客户 (F1)",
        "ko": "고객 지정 (F1)", "uk": "Призначити клієнта (F1)", "ar": "تعيين عميل (F1)",
    },
    "aux_cliente_nuevo": {
        "es": "＋ Cliente Nuevo", "gn": "＋ Cliente Pyahu", "pt": "＋ Cliente Novo", "en": "＋ New Client",
        "ru": "＋ Новый клиент", "zh": "＋ 新客户", "ko": "＋ 새 고객", "uk": "＋ Новий клієнт", "ar": "＋ عميل جديد",
    },
    "aux_cliente_ocasional_sin_registro": {
        "es": "Cliente Ocasional (sin registro)", "gn": "Cliente Ocasional (ndaha'éiva ojehaipyre)",
        "pt": "Cliente Ocasional (sem cadastro)", "en": "Occasional Client (unregistered)",
        "ru": "Разовый клиент (без регистрации)", "zh": "临时客户（未登记）",
        "ko": "임시 고객 (미등록)", "uk": "Разовий клієнт (без реєстрації)", "ar": "عميل عارض (غير مسجل)",
    },
    "aux_consultar_stock": {
        "es": "📦  Consultar Stock de Productos", "gn": "📦  Ehecha Mba'e Stock",
        "pt": "📦  Consultar Estoque de Produtos", "en": "📦  Check Product Stock",
        "ru": "📦  Проверить остаток товаров", "zh": "📦  查询产品库存",
        "ko": "📦  상품 재고 조회", "uk": "📦  Перевірити залишок товарів", "ar": "📦  الاستعلام عن مخزون المنتجات",
    },
    "aux_solo_con_stock": {
        "es": "Solo con stock disponible", "gn": "Oĩva año", "pt": "Apenas com estoque disponível",
        "en": "Only with available stock", "ru": "Только с наличием на складе", "zh": "仅显示有库存的",
        "ko": "재고 있는 것만", "uk": "Лише з наявним залишком", "ar": "فقط المتوفر بالمخزون",
    },
    "aux_bajo_stock_sin_stock": {
        "es": "🔴 Bajo stock mínimo   ⬜ Sin stock", "gn": "🔴 Stock Sy'a   ⬜ Stock Ỹre",
        "pt": "🔴 Abaixo do estoque mínimo   ⬜ Sem estoque", "en": "🔴 Below minimum stock   ⬜ Out of stock",
        "ru": "🔴 Ниже мин. остатка   ⬜ Нет в наличии", "zh": "🔴 低于最低库存   ⬜ 无库存",
        "ko": "🔴 최소 재고 미만   ⬜ 재고 없음", "uk": "🔴 Нижче мін. залишку   ⬜ Немає в наявності",
        "ar": "🔴 أقل من الحد الأدنى   ⬜ نفد المخزون",
    },
    "col_categoria_mayus": {
        "es": "CATEGORÍA", "gn": "CATEGORÍA", "pt": "CATEGORIA", "en": "CATEGORY",
        "ru": "КАТЕГОРИЯ", "zh": "分类", "ko": "카테고리", "uk": "КАТЕГОРІЯ", "ar": "الفئة",
    },
    "col_precio_mayor": {
        "es": "PRECIO MAYOR.", "gn": "PRECIO MAYOR.", "pt": "PREÇO ATACADO", "en": "WHOLESALE PRICE",
        "ru": "ОПТ. ЦЕНА", "zh": "批发价", "ko": "도매가", "uk": "ОПТ. ЦІНА", "ar": "سعر الجملة",
    },

    # ── Formulario interno de Presupuestos ───────────────────────
    "presup_valido_hasta": {
        "es": "Válido hasta:", "gn": "Oĩva'erã peve:", "pt": "Válido até:", "en": "Valid until:",
        "ru": "Действителен до:", "zh": "有效期至：", "ko": "유효 기간:", "uk": "Дійсний до:", "ar": "صالح حتى:",
    },
    "presup_productos_contador": {
        "es": "{n} productos.", "gn": "{n} mba'e.", "pt": "{n} produtos.", "en": "{n} products.",
        "ru": "{n} товаров.", "zh": "{n}件产品。", "ko": "{n}개 상품.", "uk": "{n} товарів.", "ar": "{n} منتج.",
    },
    "presup_cancelar_x": {
        "es": "❌ Cancelar", "gn": "❌ Heja", "pt": "❌ Cancelar", "en": "❌ Cancel",
        "ru": "❌ Отмена", "zh": "❌ 取消", "ko": "❌ 취소", "uk": "❌ Скасувати", "ar": "❌ إلغاء",
    },
    "presup_guardar_presupuesto": {
        "es": "💾 Guardar Presupuesto", "gn": "💾 Ñongatu Presupuesto", "pt": "💾 Salvar Orçamento",
        "en": "💾 Save Quote", "ru": "💾 Сохранить смету", "zh": "💾 保存报价单",
        "ko": "💾 견적 저장", "uk": "💾 Зберегти кошторис", "ar": "💾 حفظ عرض السعر",
    },
    "presup_tipo_precio": {
        "es": "Tipo de Precio:", "gn": "Precio Teko:", "pt": "Tipo de Preço:", "en": "Price Type:",
        "ru": "Тип цены:", "zh": "价格类型：", "ko": "가격 유형:", "uk": "Тип ціни:", "ar": "نوع السعر:",
    },
    "col_total_mayus3": {
        "es": "TOTAL", "gn": "MANTEREI", "pt": "TOTAL", "en": "TOTAL",
        "ru": "ИТОГО", "zh": "总计", "ko": "합계", "uk": "РАЗОМ", "ar": "الإجمالي",
    },

    # ── Filtros por Proveedor/Marca/Categoría (Productos, Inventario,
    # Buscar Producto F2 y Consultar Stock F3) ─────────────────────
    "filtro_proveedor": {
        "es": "Proveedor:", "gn": "Proveedor:", "pt": "Fornecedor:", "en": "Supplier:",
        "ru": "Поставщик:", "zh": "供应商：", "ko": "공급업체:", "uk": "Постачальник:", "ar": "المورد:",
    },
    "filtro_marca": {
        "es": "Marca:", "gn": "Marca:", "pt": "Marca:", "en": "Brand:",
        "ru": "Бренд:", "zh": "品牌：", "ko": "브랜드:", "uk": "Бренд:", "ar": "العلامة التجارية:",
    },
    "filtro_categoria": {
        "es": "Categoría:", "gn": "Categoría:", "pt": "Categoria:", "en": "Category:",
        "ru": "Категория:", "zh": "类别：", "ko": "카테고리:", "uk": "Категорія:", "ar": "الفئة:",
    },
    "filtro_todos": {
        "es": "Todos", "gn": "Opavave", "pt": "Todos", "en": "All",
        "ru": "Все", "zh": "全部", "ko": "전체", "uk": "Усі", "ar": "الكل",
    },
    "filtro_limpiar": {
        "es": "✕ Limpiar filtros", "gn": "✕ Mopotĩ ñemboheko", "pt": "✕ Limpar filtros",
        "en": "✕ Clear filters", "ru": "✕ Сбросить фильтры", "zh": "✕ 清除筛选",
        "ko": "✕ 필터 지우기", "uk": "✕ Очистити фільтри", "ar": "✕ مسح الفلاتر",
    },
}


def t(clave: str, idioma: str | None = None) -> str:
    """Devuelve el texto traducido para 'clave' en el idioma indicado (o el
    idioma actual configurado en el sistema, si no se especifica). Si la
    clave no existe, o falta esa traducción puntual, cae de nuevo al
    español para no dejar nunca un espacio vacío en la interfaz."""
    if idioma is None:
        from models_idioma import obtener_idioma_actual
        idioma = obtener_idioma_actual()
    entradas = TEXTOS.get(clave)
    if not entradas:
        return clave
    return entradas.get(idioma) or entradas.get("es") or clave
