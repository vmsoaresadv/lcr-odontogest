from datetime import datetime, date, timedelta
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QDateEdit
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor, QFont
from services.audit_service import get_audit_logs
from ui.custom_date_edit import CustomDateEdit


class LogsView(QWidget):
    """Visualizador de trilha de auditoria (LGPD) com filtros por período e navegação diária."""
    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.periodo_modo = "hoje"  # "hoje", "7d", "mes", "personalizado", "todos"
        self.dia_selecionado = date.today()
        self.init_ui()
        self.carregar_logs()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit {
                background-color: #ffffff;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                min-height: 22px;
            }
            QLineEdit:focus {
                border: 2px solid #2ca5a9;
            }
            QDateEdit {
                background-color: #ffffff;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 5px 28px 5px 10px;
                font-size: 13px;
                min-height: 22px;
                min-width: 135px;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border-left: 1px solid #cbd5e1;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
            }
            QDateEdit:focus {
                border: 2px solid #2ca5a9;
            }
            QScrollBar:vertical {
                border: none;
                background: #f1f5f9;
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1;
                min-height: 24px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94a3b8;
            }
            QScrollBar::handle:vertical:pressed {
                background: #2ca5a9;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                border: none;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                border: none;
                background: #f1f5f9;
                height: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: #cbd5e1;
                min-width: 24px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #94a3b8;
            }
            QScrollBar::handle:horizontal:pressed {
                background: #2ca5a9;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
                border: none;
                background: none;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
            QPushButton#periodBtn {
                background-color: #f1f5f9;
                color: #475569;
                font-weight: 600;
                padding: 7px 16px;
                border-radius: 6px;
                border: 1px solid #cbd5e1;
                font-size: 13px;
            }
            QPushButton#periodBtn:hover {
                background-color: #e2e8f0;
                color: #1e293b;
            }
            QPushButton#periodBtn:checked {
                background-color: #2ca5a9;
                color: #ffffff;
                border: 1px solid #248a8d;
                font-weight: bold;
            }
            QPushButton#navBtn {
                background-color: #ffffff;
                color: #334155;
                font-size: 12px;
                font-weight: 600;
                padding: 5px 12px;
                border-radius: 6px;
                border: 1px solid #cbd5e1;
            }
            QPushButton#navBtn:hover {
                background-color: #f1f5f9;
                border-color: #94a3b8;
            }
            QFrame#boxNavLogs {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)

        # 1. Cabeçalho Superior
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Trilha de Auditoria e Rastreabilidade (LGPD)")
        title.setStyleSheet("font-size: 19px; font-weight: bold; color: #166260;")
        desc = QLabel("Registro imutável de todas as ações executadas no sistema para segurança, conformidade e governança.")
        desc.setStyleSheet("color: #64748b; font-size: 13px;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Barra de Pesquisa com debounce de 250ms
        self.timer_busca = QTimer(self)
        self.timer_busca.setSingleShot(True)
        self.timer_busca.setInterval(250)
        self.timer_busca.timeout.connect(self.carregar_logs)

        self.txt_busca = QLineEdit()
        self.txt_busca.setPlaceholderText("🔍 Filtrar por usuário, ação ou detalhe...")
        self.txt_busca.setFixedWidth(290)
        self.txt_busca.textChanged.connect(self.timer_busca.start)
        header_layout.addWidget(self.txt_busca)

        btn_atualizar = QPushButton("🔄 Atualizar")
        btn_atualizar.setObjectName("navBtn")
        btn_atualizar.setStyleSheet("""
            background-color: #0d9488;
            color: #ffffff;
            font-weight: bold;
            padding: 7px 14px;
            border-radius: 6px;
            border: none;
        """)
        btn_atualizar.clicked.connect(self.carregar_logs)
        header_layout.addWidget(btn_atualizar)

        layout.addLayout(header_layout)

        # 2. Submenu de Período (Pílulas de Tempo)
        bar_periodos = QHBoxLayout()
        bar_periodos.setSpacing(8)

        self.btn_hoje = QPushButton("📅 Hoje")
        self.btn_hoje.setObjectName("periodBtn")
        self.btn_hoje.setCheckable(True)
        self.btn_hoje.setChecked(True)
        self.btn_hoje.clicked.connect(lambda: self.selecionar_periodo("hoje"))
        bar_periodos.addWidget(self.btn_hoje)

        self.btn_7d = QPushButton("🗓️ Últimos 7 dias")
        self.btn_7d.setObjectName("periodBtn")
        self.btn_7d.setCheckable(True)
        self.btn_7d.clicked.connect(lambda: self.selecionar_periodo("7d"))
        bar_periodos.addWidget(self.btn_7d)

        self.btn_mes = QPushButton("📆 Este Mês")
        self.btn_mes.setObjectName("periodBtn")
        self.btn_mes.setCheckable(True)
        self.btn_mes.clicked.connect(lambda: self.selecionar_periodo("mes"))
        bar_periodos.addWidget(self.btn_mes)

        self.btn_custom = QPushButton("🔍 Personalizado")
        self.btn_custom.setObjectName("periodBtn")
        self.btn_custom.setCheckable(True)
        self.btn_custom.clicked.connect(lambda: self.selecionar_periodo("personalizado"))
        bar_periodos.addWidget(self.btn_custom)

        self.btn_todos = QPushButton("🌐 Todos os Logs")
        self.btn_todos.setObjectName("periodBtn")
        self.btn_todos.setCheckable(True)
        self.btn_todos.clicked.connect(lambda: self.selecionar_periodo("todos"))
        bar_periodos.addWidget(self.btn_todos)

        bar_periodos.addStretch()

        self.lbl_contador = QLabel("📊 Carregando...")
        self.lbl_contador.setStyleSheet("""
            background-color: #f0fdfa;
            color: #0f766e;
            font-weight: bold;
            font-size: 12px;
            padding: 4px 10px;
            border: 1px solid #ccfbf1;
            border-radius: 6px;
        """)
        bar_periodos.addWidget(self.lbl_contador)

        layout.addLayout(bar_periodos)

        # 3. Barra de Navegação Diária (visível no modo "Hoje" / dia específico)
        self.box_nav_dia = QFrame()
        self.box_nav_dia.setObjectName("boxNavLogs")
        nav_dia_layout = QHBoxLayout(self.box_nav_dia)
        nav_dia_layout.setContentsMargins(10, 6, 10, 6)
        nav_dia_layout.setSpacing(8)

        btn_dia_ant = QPushButton("◀ Dia Anterior")
        btn_dia_ant.setObjectName("navBtn")
        btn_dia_ant.clicked.connect(self.dia_anterior)
        nav_dia_layout.addWidget(btn_dia_ant)

        self.dt_filtro_dia = CustomDateEdit()
        self.dt_filtro_dia.setFixedWidth(160)
        self.dt_filtro_dia.setDate(QDate.currentDate())
        self.dt_filtro_dia.dateChanged.connect(self.ao_mudar_data_dia)
        nav_dia_layout.addWidget(self.dt_filtro_dia)

        btn_dia_prox = QPushButton("Dia Seguinte ▶")
        btn_dia_prox.setObjectName("navBtn")
        btn_dia_prox.clicked.connect(self.dia_seguinte)
        nav_dia_layout.addWidget(btn_dia_prox)

        btn_ir_hoje = QPushButton("Hoje")
        btn_ir_hoje.setObjectName("navBtn")
        btn_ir_hoje.clicked.connect(self.ir_hoje)
        nav_dia_layout.addWidget(btn_ir_hoje)

        nav_dia_layout.addStretch()

        self.lbl_info_dia = QLabel("💡 Navegue pelos dias para auditar ações específicas.")
        self.lbl_info_dia.setStyleSheet("color: #64748b; font-size: 12px;")
        nav_dia_layout.addWidget(self.lbl_info_dia)

        layout.addWidget(self.box_nav_dia)

        # 4. Barra de Período Personalizado (visível no modo "personalizado")
        self.box_custom_period = QFrame()
        self.box_custom_period.setObjectName("boxNavLogs")
        custom_layout = QHBoxLayout(self.box_custom_period)
        custom_layout.setContentsMargins(10, 6, 10, 6)
        custom_layout.setSpacing(8)

        custom_layout.addWidget(QLabel("De:"))
        self.dt_custom_ini = CustomDateEdit()
        self.dt_custom_ini.setFixedWidth(135)
        self.dt_custom_ini.setDate(QDate.currentDate().addDays(-7))
        custom_layout.addWidget(self.dt_custom_ini)

        custom_layout.addWidget(QLabel("Até:"))
        self.dt_custom_fim = CustomDateEdit()
        self.dt_custom_fim.setFixedWidth(135)
        self.dt_custom_fim.setDate(QDate.currentDate())
        custom_layout.addWidget(self.dt_custom_fim)

        btn_aplicar_custom = QPushButton("Filtrar Período")
        btn_aplicar_custom.setObjectName("navBtn")
        btn_aplicar_custom.setStyleSheet("""
            background-color: #2ca5a9;
            color: #ffffff;
            font-weight: bold;
            padding: 5px 14px;
            border-radius: 6px;
            border: none;
        """)
        btn_aplicar_custom.clicked.connect(self.carregar_logs)
        custom_layout.addWidget(btn_aplicar_custom)

        custom_layout.addStretch()
        self.box_custom_period.setVisible(False)
        layout.addWidget(self.box_custom_period)

        # 5. Tabela de Logs (colunas otimizadas para carregamento instantâneo)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Data / Hora", "Usuário", "Ação", "Detalhes"])
        self.table.setColumnHidden(0, True)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Interactive)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 165)
        self.table.setColumnWidth(2, 145)
        self.table.setColumnWidth(3, 185)

        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                color: #0f172a;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                gridline-color: #f1f5f9;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                font-weight: bold;
                color: #334155;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #cbd5e1;
            }
            QTableWidget::item {
                padding: 6px;
            }
        """)

        layout.addWidget(self.table)

    def selecionar_periodo(self, modo: str):
        self.periodo_modo = modo
        self.btn_hoje.setChecked(modo == "hoje")
        self.btn_7d.setChecked(modo == "7d")
        self.btn_mes.setChecked(modo == "mes")
        self.btn_custom.setChecked(modo == "personalizado")
        self.btn_todos.setChecked(modo == "todos")

        # Exibe/Oculta as barras secundárias conforme o modo
        self.box_nav_dia.setVisible(modo == "hoje")
        self.box_custom_period.setVisible(modo == "personalizado")

        if modo == "hoje":
            # Sincroniza a data do seletor
            hoje = date.today()
            self.dia_selecionado = hoje
            self.dt_filtro_dia.setDate(QDate(hoje.year, hoje.month, hoje.day))

        self.carregar_logs()

    def dia_anterior(self):
        self.dia_selecionado -= timedelta(days=1)
        self.dt_filtro_dia.setDate(QDate(self.dia_selecionado.year, self.dia_selecionado.month, self.dia_selecionado.day))

    def dia_seguinte(self):
        self.dia_selecionado += timedelta(days=1)
        self.dt_filtro_dia.setDate(QDate(self.dia_selecionado.year, self.dia_selecionado.month, self.dia_selecionado.day))

    def ir_hoje(self):
        hoje = date.today()
        self.dia_selecionado = hoje
        self.dt_filtro_dia.setDate(QDate(hoje.year, hoje.month, hoje.day))

    def ao_mudar_data_dia(self, qdate: QDate):
        self.dia_selecionado = date(qdate.year(), qdate.month(), qdate.day())
        self.carregar_logs()

    def carregar_logs(self):
        termo = self.txt_busca.text().strip()
        data_ini: Optional[str] = None
        data_fim: Optional[str] = None

        hoje = date.today()

        if self.periodo_modo == "hoje":
            dia_str = self.dia_selecionado.strftime("%Y-%m-%d")
            data_ini = dia_str
            data_fim = dia_str
        elif self.periodo_modo == "7d":
            data_ini = (hoje - timedelta(days=7)).strftime("%Y-%m-%d")
            data_fim = hoje.strftime("%Y-%m-%d")
        elif self.periodo_modo == "mes":
            data_ini = date(hoje.year, hoje.month, 1).strftime("%Y-%m-%d")
            data_fim = hoje.strftime("%Y-%m-%d")
        elif self.periodo_modo == "personalizado":
            q_ini = self.dt_custom_ini.date()
            q_fim = self.dt_custom_fim.date()
            data_ini = f"{q_ini.year():04d}-{q_ini.month():02d}-{q_ini.day():02d}"
            data_fim = f"{q_fim.year():04d}-{q_fim.month():02d}-{q_fim.day():02d}"
        elif self.periodo_modo == "todos":
            data_ini = None
            data_fim = None

        logs = get_audit_logs(limit=400, search=termo if termo else None, data_inicio=data_ini, data_fim=data_fim)

        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(logs))

        for row_idx, log in enumerate(logs):
            item_id = QTableWidgetItem(str(log["id"]))
            item_id.setTextAlignment(Qt.AlignCenter)

            # Formata data/hora brasileira (DD/MM/AAAA HH:MM:SS)
            raw_dt = str(log["data_hora"])
            try:
                # Converte ISO para BR
                dt_obj = datetime.strptime(raw_dt, "%Y-%m-%d %H:%M:%S")
                dt_fmt = dt_obj.strftime("%d/%m/%Y %H:%M:%S")
            except Exception:
                dt_fmt = raw_dt

            item_data = QTableWidgetItem(dt_fmt)
            item_data.setTextAlignment(Qt.AlignCenter)

            item_user = QTableWidgetItem(str(log["usuario_nome"]))
            item_user.setTextAlignment(Qt.AlignCenter)

            acao_txt = str(log["acao"])
            item_acao = QTableWidgetItem(acao_txt)
            item_acao.setTextAlignment(Qt.AlignCenter)
            item_acao.setFont(QFont("Segoe UI", 9, QFont.Bold))

            # Destaques visuais inteligentes por categoria de ação
            if any(k in acao_txt for k in ["FALHA", "ERRO", "BLOQUEADO", "EXCLUIDO", "EXCLUIDA"]):
                item_acao.setForeground(QColor("#b91c1c"))  # Vermelho
            elif any(k in acao_txt for k in ["SUCESSO", "CRIADO", "CRIADA", "RESTAURADO"]):
                item_acao.setForeground(QColor("#059669"))  # Verde
            elif any(k in acao_txt for k in ["ATUALIZADO", "EDITADO"]):
                item_acao.setForeground(QColor("#0284c7"))  # Azul
            elif any(k in acao_txt for k in ["LOGIN", "LOGOUT"]):
                item_acao.setForeground(QColor("#0d9488"))  # Turquesa
            else:
                item_acao.setForeground(QColor("#475569"))

            item_detalhe = QTableWidgetItem(str(log["detalhe"] or ""))

            self.table.setItem(row_idx, 0, item_id)
            self.table.setItem(row_idx, 1, item_data)
            self.table.setItem(row_idx, 2, item_user)
            self.table.setItem(row_idx, 3, item_acao)
            self.table.setItem(row_idx, 4, item_detalhe)

        self.table.setUpdatesEnabled(True)

        # Atualiza a pílula de contador com o período ativo
        total = len(logs)
        if self.periodo_modo == "hoje":
            data_br = self.dia_selecionado.strftime("%d/%m/%Y")
            self.lbl_contador.setText(f"📊 {total} evento(s) em {data_br}")
        elif self.periodo_modo == "7d":
            self.lbl_contador.setText(f"📊 {total} evento(s) nos últimos 7 dias")
        elif self.periodo_modo == "mes":
            self.lbl_contador.setText(f"📊 {total} evento(s) neste mês")
        elif self.periodo_modo == "personalizado":
            self.lbl_contador.setText(f"📊 {total} evento(s) no período selecionado")
        else:
            self.lbl_contador.setText(f"📊 {total} evento(s) registrados")
