from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QIcon, QPixmap
from services.audit_service import log_action
from ui.logs_view import LogsView
from ui.users_view import UsersView
from ui.patients_view import PatientsView
from ui.schedule_view import ScheduleView
from ui.sublocacao_view import SublocacaoView
from ui.inventory_view import InventoryView
from ui.financial_view import FinancialView
from ui.reports_view import ReportsView
from ui.backup_dialog import BackupDialog
from ui.updater_dialog import UpdaterDialog
from services.financial_service import gerar_transacoes_recorrentes_pendentes, verificar_alertas_vencimento
from version import __version__, APP_NAME

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo_clean.png"
ICO_PATH = Path(__file__).resolve().parent.parent / "assets" / "app_icon.ico"


def criar_placeholder_view(titulo: str, descricao: str) -> QWidget:
    """Cria uma tela limpa de espaço reservado para as fases futuras."""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setAlignment(Qt.AlignCenter)

    card = QFrame()
    card.setStyleSheet("""
        background-color: #ffffff;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        padding: 40px;
    """)
    card_layout = QVBoxLayout(card)
    card_layout.setAlignment(Qt.AlignCenter)
    card_layout.setSpacing(12)

    lbl_title = QLabel(titulo)
    lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0f766e;")
    lbl_title.setAlignment(Qt.AlignCenter)

    lbl_desc = QLabel(descricao)
    lbl_desc.setStyleSheet("font-size: 14px; color: #64748b;")
    lbl_desc.setAlignment(Qt.AlignCenter)

    card_layout.addWidget(lbl_title)
    card_layout.addWidget(lbl_desc)
    layout.addWidget(card)
    return widget


class MainWindow(QMainWindow):
    """Janela Principal com navegação e controle de perfil de acesso."""
    logout_requested = Signal()

    def __init__(self, current_user: dict):
        super().__init__()
        self.current_user = current_user
        self.setWindowTitle(f"{APP_NAME} - Dra. Lara Camila (CRO-BA 15247)")
        self.setMinimumSize(1000, 650)
        self.ajustar_tamanho_inicial()
        self.init_ui()
        # Gera lançamentos recorrentes e verifica contas a vencer após 800ms
        QTimer.singleShot(800, self.checar_vencimentos_ao_iniciar)
        # Checa atualizações silenciosamente em 2º plano após 3 segundos
        QTimer.singleShot(3000, self.checar_atualizacoes_silencioso)

    def checar_atualizacoes_silencioso(self):
        try:
            self._updater_dialog = UpdaterDialog(silensioso=True, parent=self)
        except Exception:
            pass

    def ajustar_tamanho_inicial(self):
        screen = QApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            # Dimensão espaçosa e elegante, com limite máximo inteligente para monitores ultrawide
            largura_alvo = min(max(int(avail.width() * 0.75), 1260), 1540)
            altura_alvo = min(max(int(avail.height() * 0.82), 750), 920)
            largura = min(largura_alvo, avail.width() - 50)
            altura = min(altura_alvo, avail.height() - 50)
            self.resize(largura, altura)
            # Centraliza perfeitamente no monitor
            geo = self.frameGeometry()
            geo.moveCenter(avail.center())
            self.move(geo.topLeft())
        else:
            self.resize(1360, 820)

    def init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        icon_to_use = ICO_PATH if ICO_PATH.exists() else LOGO_PATH
        if icon_to_use.exists():
            self.setWindowIcon(QIcon(str(icon_to_use)))

        # 1. Barra Superior (Header)
        header = QFrame(self)
        header.setFixedHeight(68)
        header.setStyleSheet("""
            background-color: #238b8e;
            border-bottom: 2px solid #1a6d70;
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 24, 0)
        header_layout.setSpacing(12)

        # Logo LCR
        if LOGO_PATH.exists():
            lbl_logo = QLabel(header)
            pix = QPixmap(str(LOGO_PATH)).scaled(46, 46, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_logo.setPixmap(pix)
            header_layout.addWidget(lbl_logo)

        brand_box = QVBoxLayout()
        brand_box.setSpacing(1)
        clinic_title = QLabel(APP_NAME, header)
        clinic_title.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: bold;")
        clinic_sub = QLabel("Dra. Lara Camila • CRO-BA 15247 • Irecê/BA", header)
        clinic_sub.setStyleSheet("color: #e0f2f1; font-size: 11px;")
        brand_box.addWidget(clinic_title)
        brand_box.addWidget(clinic_sub)
        header_layout.addLayout(brand_box)

        header_layout.addStretch()

        # Informações do Usuário Logado e Alertas
        user_info_layout = QHBoxLayout()
        user_info_layout.setSpacing(10)

        # Botão de Central de Vencimentos
        self.btn_vencimentos = QPushButton("🔔 Vencimentos", header)
        self.btn_vencimentos.setCursor(Qt.PointingHandCursor)
        self.btn_vencimentos.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.15);
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
                padding: 6px 14px;
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.35);
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.25);
            }
        """)
        self.btn_vencimentos.clicked.connect(self.abrir_central_vencimentos)
        user_info_layout.addWidget(self.btn_vencimentos)
        user_info_layout.addSpacing(6)

        lbl_user = QLabel(f"Olá, {self.current_user['nome']}", header)
        lbl_user.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 500;")

        perfil_txt = "Administradora" if self.current_user["perfil"] == "admin" else "Secretária"
        lbl_perfil = QLabel(perfil_txt, header)
        lbl_perfil.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.18);
            color: #ffffff;
            font-size: 12px;
            font-weight: 600;
            padding: 4px 12px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.35);
        """)

        btn_logout = QPushButton("Sair", header)
        btn_logout.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.15);
            color: #ffffff;
            font-weight: bold;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 6px;
            padding: 6px 14px;
        """)
        btn_logout.clicked.connect(self.executar_logout)

        user_info_layout.addWidget(lbl_user)
        user_info_layout.addWidget(lbl_perfil)
        user_info_layout.addSpacing(14)
        user_info_layout.addWidget(btn_logout)

        header_layout.addLayout(user_info_layout)
        main_layout.addWidget(header)

        # 2. Corpo (Menu Lateral + Conteúdo Dinâmico)
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Menu Lateral
        sidebar = QFrame(self)
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            background-color: #1e293b;
            border-right: 1px solid #334155;
        """)
        self.sidebar_layout = QVBoxLayout(sidebar)
        self.sidebar_layout.setContentsMargins(12, 20, 12, 20)
        self.sidebar_layout.setSpacing(8)

        # Stack de Páginas
        self.pages_stack = QStackedWidget(self)
        self.pages_stack.setStyleSheet("background-color: #f8fafc;")

        # Mapeamento de botões e páginas
        self.nav_buttons = []

        # Ordem do menu lateral solicitada pela clínica:
        # 1. Agenda
        # 2. Pacientes
        # 3. Sublocação Sala 2
        # 4. Financeiro
        # 5. Estoque
        # 6. Usuários (admin)
        # 7. Auditoria LGPD (admin)

        # 1. Módulo da Agenda & Retornos (Fase 3)
        self.schedule_view = ScheduleView(self.current_user, self)
        self.adicionar_menu_item("📅 Agenda", 0, self.schedule_view)

        # 2. Módulo de Pacientes (Fase 2)
        self.patients_view = PatientsView(self.current_user, self)
        self.adicionar_menu_item("👤 Pacientes", 1, self.patients_view)

        # 3. Módulo de Sublocação (Fase 4)
        self.sublocacao_view = SublocacaoView(self.current_user, self)
        self.adicionar_menu_item("🏢 Sublocação", 2, self.sublocacao_view)

        # 4. Módulo Financeiro (Fase 6)
        self.financial_view = FinancialView(self.current_user, self)
        self.adicionar_menu_item("💰 Financeiro", 3, self.financial_view)

        # 5. Módulo de Estoque (Fase 5)
        self.inventory_view = InventoryView(self.current_user, self)
        self.adicionar_menu_item("📦 Estoque", 4, self.inventory_view)

        # Telas Exclusivas do Perfil 'admin'
        if self.current_user["perfil"] == "admin":
            # 6. Central de Relatórios em PDF
            self.reports_view = ReportsView(self.current_user, self)
            self.adicionar_menu_item("📊 Relatórios", 5, self.reports_view)

            # 7. Gestão de Usuários
            self.users_view = UsersView(self.current_user, self)
            self.adicionar_menu_item("⚙️ Usuários", 6, self.users_view)

            # 8. Auditoria e Rastreabilidade LGPD
            self.logs_view = LogsView(self.current_user, self)
            self.adicionar_menu_item("🔒 Auditoria (LGPD)", 7, self.logs_view)

        self.sidebar_layout.addStretch()

        # Separador e Botões Utilitários da Clínica (Backup & Atualizações)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #334155; margin-top: 6px; margin-bottom: 6px;")
        self.sidebar_layout.addWidget(sep)

        btn_backup = QPushButton("💾 Backup em 1 Clique")
        btn_backup.setStyleSheet("""
            QPushButton {
                background-color: #0f766e;
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                text-align: left;
                padding: 9px 14px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #115e59;
            }
        """)
        btn_backup.clicked.connect(self.abrir_backup_dialog)
        self.sidebar_layout.addWidget(btn_backup)

        btn_update = QPushButton(f"🔄 Atualizações (v{__version__})")
        btn_update.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #94a3b8;
                font-size: 12px;
                text-align: left;
                padding: 7px 14px;
                border-radius: 6px;
                border: 1px solid #334155;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #ffffff;
            }
        """)
        btn_update.clicked.connect(self.abrir_updater_dialog)
        self.sidebar_layout.addWidget(btn_update)

        body_layout.addWidget(sidebar)
        body_layout.addWidget(self.pages_stack)
        main_layout.addLayout(body_layout)

        # Abre diretamente na tela de Agenda (índice 0) por padrão
        if self.nav_buttons:
            self.navegar_para(0)

    def adicionar_menu_item(self, texto: str, indice: int, widget_pagina: QWidget):
        btn = QPushButton(texto)
        btn.setCheckable(True)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #cbd5e1;
                font-size: 14px;
                font-weight: 500;
                text-align: left;
                padding: 10px 14px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #ffffff;
            }
            QPushButton:checked {
                background-color: #2ca5a9;
                color: #ffffff;
                font-weight: bold;
            }
        """)
        btn.clicked.connect(lambda checked=False, i=indice: self.navegar_para(i))
        self.sidebar_layout.addWidget(btn)
        self.nav_buttons.append((btn, indice))
        self.pages_stack.addWidget(widget_pagina)

    def navegar_para(self, indice: int):
        self.pages_stack.setCurrentIndex(indice)
        for btn, idx in self.nav_buttons:
            btn.setChecked(idx == indice)

        # Se navegou para alguma aba com dados dinâmicos, recarrega
        current_w = self.pages_stack.currentWidget()
        if hasattr(self, "schedule_view") and current_w == self.schedule_view:
            self.schedule_view.carregar_agenda_semanal()
            self.schedule_view.carregar_agenda_do_dia()
            self.schedule_view.carregar_lembretes_retorno()
        elif hasattr(self, "patients_view") and current_w == self.patients_view:
            self.patients_view.carregar_pacientes()
        elif hasattr(self, "sublocacao_view") and current_w == self.sublocacao_view:
            self.sublocacao_view.carregar_agenda_semanal()
            self.sublocacao_view.carregar_reservas_do_dia()
        elif hasattr(self, "inventory_view") and current_w == self.inventory_view:
            self.inventory_view.carregar_dados()
        elif hasattr(self, "users_view") and current_w == self.users_view:
            self.users_view.carregar_usuarios()
        elif hasattr(self, "logs_view") and current_w == self.logs_view:
            self.logs_view.carregar_logs()
        elif hasattr(self, "reports_view") and current_w == self.reports_view:
            self.reports_view.carregar_dre_preview()
            self.reports_view.atualizar_lista_pacientes()
            self.reports_view.carregar_estoque_preview()

    def abrir_backup_dialog(self):
        dlg = BackupDialog(self.current_user, self)
        dlg.exec()

    def abrir_updater_dialog(self):
        dlg = UpdaterDialog(silensioso=False, parent=self)
        dlg.exec()

    def checar_vencimentos_ao_iniciar(self):
        try:
            gerar_transacoes_recorrentes_pendentes()
            self.atualizar_contador_vencimentos(abrir_modal_se_houver=True)
        except Exception as e:
            print("Erro ao verificar vencimentos na inicialização:", e)

    def atualizar_contador_vencimentos(self, abrir_modal_se_houver: bool = False):
        try:
            bills = verificar_alertas_vencimento(dias_antecedencia=1)
            qtd = len(bills)
            if qtd > 0:
                self.btn_vencimentos.setText(f"🔔 Vencimentos ({qtd})")
                self.btn_vencimentos.setStyleSheet("""
                    QPushButton {
                        background-color: #ea580c;
                        color: #ffffff;
                        font-size: 12px;
                        font-weight: bold;
                        padding: 6px 14px;
                        border-radius: 6px;
                        border: 1px solid #ffedd5;
                    }
                    QPushButton:hover {
                        background-color: #c2410c;
                    }
                """)
                if abrir_modal_se_houver:
                    self.abrir_central_vencimentos()
            else:
                self.btn_vencimentos.setText("🔔 Vencimentos")
                self.btn_vencimentos.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(255, 255, 255, 0.15);
                        color: #ffffff;
                        font-size: 12px;
                        font-weight: bold;
                        padding: 6px 14px;
                        border-radius: 6px;
                        border: 1px solid rgba(255, 255, 255, 0.35);
                    }
                    QPushButton:hover {
                        background-color: rgba(255, 255, 255, 0.25);
                    }
                """)
        except Exception as e:
            print("Erro ao atualizar contador de vencimentos:", e)

    def abrir_central_vencimentos(self):
        from ui.due_bills_dialog import DueBillsDialog
        bills = verificar_alertas_vencimento(dias_antecedencia=1)
        dialog = DueBillsDialog(self.current_user, bills, parent=self)
        dialog.exec()
        if dialog.abrir_financeiro_solicitado:
            # 3 é o índice do Financeiro
            self.navegar_para(3)
        self.atualizar_contador_vencimentos(abrir_modal_se_houver=False)

    def executar_logout(self):
        log_action(self.current_user["id"], self.current_user["nome"], "LOGOUT", "Sessão finalizada pelo usuário")
        self.logout_requested.emit()
        self.close()
