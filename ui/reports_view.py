import os
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextBrowser, QComboBox, QFileDialog, QMessageBox,
    QFrame, QApplication
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QIcon

from ui.custom_date_edit import CustomDateEdit
from services.report_service import (
    gerar_html_dre_financeiro, gerar_html_ficha_paciente,
    gerar_html_relatorio_estoque, exportar_html_para_pdf
)
from services.audit_service import log_action
from database.connection import get_db_connection

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo_clean.png"
ICO_PATH = Path(__file__).resolve().parent.parent / "assets" / "app_icon.ico"


class ReportsView(QWidget):
    """Central de Relatórios Gerenciais e Emissão de Documentos em PDF."""
    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Cabeçalho
        header_card = QFrame(self)
        header_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 12px 18px;
            }
        """)
        h_layout = QHBoxLayout(header_card)
        h_layout.setContentsMargins(0, 0, 0, 0)

        titulo_box = QVBoxLayout()
        lbl_titulo = QLabel("📊 Central de Relatórios e Impressão")
        lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f766e;")
        lbl_sub = QLabel("Demonstrativos financeiros, prontuários clínicos da Dra. Lara Camila e inventário de estoque prontos para PDF.")
        lbl_sub.setStyleSheet("font-size: 13px; color: #64748b;")
        titulo_box.addWidget(lbl_titulo)
        titulo_box.addWidget(lbl_sub)
        h_layout.addLayout(titulo_box)
        h_layout.addStretch()

        main_layout.addWidget(header_card)

        # Abas de Relatórios
        self.tabs = QTabWidget(self)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #f1f5f9;
                color: #475569;
                font-weight: 600;
                padding: 10px 18px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #0f766e;
                border-bottom: 3px solid #0d9488;
            }
        """)

        # Aba 1: DRE Financeiro
        self.tab_financeiro = QWidget()
        self.init_tab_financeiro()
        self.tabs.addTab(self.tab_financeiro, "💰 Demonstrativo Financeiro (DRE)")

        # Aba 2: Ficha do Paciente
        self.tab_paciente = QWidget()
        self.init_tab_paciente()
        self.tabs.addTab(self.tab_paciente, "👤 Ficha Clínica do Paciente")

        # Aba 3: Relatório de Estoque
        self.tab_estoque = QWidget()
        self.init_tab_estoque()
        self.tabs.addTab(self.tab_estoque, "📦 Inventário de Estoque")

        main_layout.addWidget(self.tabs)

    # -------------------------------------------------------------
    # ABA 1: FINANCEIRO (DRE)
    # -------------------------------------------------------------
    def init_tab_financeiro(self):
        layout = QVBoxLayout(self.tab_financeiro)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Filtros de Período
        filtros_bar = QHBoxLayout()
        filtros_bar.setSpacing(10)

        filtros_bar.addWidget(QLabel("Período:"))
        self.cmb_periodo = QComboBox()
        self.cmb_periodo.addItem("Este Mês", "mes_atual")
        self.cmb_periodo.addItem("Mês Anterior", "mes_anterior")
        self.cmb_periodo.addItem("Este Ano", "ano_atual")
        self.cmb_periodo.addItem("Personalizado", "custom")
        self.cmb_periodo.currentIndexChanged.connect(self.ao_mudar_periodo_dre)
        filtros_bar.addWidget(self.cmb_periodo)

        self.lbl_de = QLabel("De:")
        self.dt_dre_ini = CustomDateEdit()
        self.lbl_ate = QLabel("Até:")
        self.dt_dre_fim = CustomDateEdit()

        hoje = date.today()
        primeiro_dia_mes = date(hoje.year, hoje.month, 1)
        self.dt_dre_ini.setDate(QDate(primeiro_dia_mes.year, primeiro_dia_mes.month, primeiro_dia_mes.day))
        self.dt_dre_fim.setDate(QDate(hoje.year, hoje.month, hoje.day))

        filtros_bar.addWidget(self.lbl_de)
        filtros_bar.addWidget(self.dt_dre_ini)
        filtros_bar.addWidget(self.lbl_ate)
        filtros_bar.addWidget(self.dt_dre_fim)

        btn_gerar_dre = QPushButton("🔍 Atualizar Relatório")
        btn_gerar_dre.setStyleSheet("""
            QPushButton {
                background-color: #0d9488;
                color: #ffffff;
                font-weight: bold;
                padding: 7px 14px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0f766e;
            }
        """)
        btn_gerar_dre.clicked.connect(self.carregar_dre_preview)
        filtros_bar.addWidget(btn_gerar_dre)

        filtros_bar.addStretch()

        btn_exportar_dre = QPushButton("📄 Salvar Demonstrativo em PDF")
        btn_exportar_dre.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                font-weight: bold;
                padding: 7px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        btn_exportar_dre.clicked.connect(self.exportar_dre_pdf)
        filtros_bar.addWidget(btn_exportar_dre)

        layout.addLayout(filtros_bar)

        # Visualizador HTML
        self.browser_dre = QTextBrowser()
        self.browser_dre.setStyleSheet("border: 1px solid #cbd5e1; border-radius: 6px; background: #ffffff;")
        layout.addWidget(self.browser_dre)

        # Carrega relatório inicial
        self.ao_mudar_periodo_dre()

    def ao_mudar_periodo_dre(self):
        modo = self.cmb_periodo.currentData()
        hoje = date.today()
        if modo == "mes_atual":
            d_ini = date(hoje.year, hoje.month, 1)
            d_fim = hoje
            self.dt_dre_ini.setDate(QDate(d_ini.year, d_ini.month, d_ini.day))
            self.dt_dre_fim.setDate(QDate(d_fim.year, d_fim.month, d_fim.day))
        elif modo == "mes_anterior":
            mes = hoje.month - 1 or 12
            ano = hoje.year if hoje.month > 1 else hoje.year - 1
            import calendar
            ult_dia = calendar.monthrange(ano, mes)[1]
            d_ini = date(ano, mes, 1)
            d_fim = date(ano, mes, ult_dia)
            self.dt_dre_ini.setDate(QDate(d_ini.year, d_ini.month, d_ini.day))
            self.dt_dre_fim.setDate(QDate(d_fim.year, d_fim.month, d_fim.day))
        elif modo == "ano_atual":
            d_ini = date(hoje.year, 1, 1)
            d_fim = hoje
            self.dt_dre_ini.setDate(QDate(d_ini.year, d_ini.month, d_ini.day))
            self.dt_dre_fim.setDate(QDate(d_fim.year, d_fim.month, d_fim.day))

        self.carregar_dre_preview()

    def carregar_dre_preview(self):
        d_ini = self.dt_dre_ini.date().toString("yyyy-MM-dd")
        d_fim = self.dt_dre_fim.date().toString("yyyy-MM-dd")
        html = gerar_html_dre_financeiro(d_ini, d_fim)
        self.browser_dre.setHtml(html)

    def exportar_dre_pdf(self):
        d_ini = self.dt_dre_ini.date().toString("yyyy-MM-dd")
        d_fim = self.dt_dre_fim.date().toString("yyyy-MM-dd")
        html = gerar_html_dre_financeiro(d_ini, d_fim)

        sugestao = f"DRE_Financeiro_{d_ini}_a_{d_fim}.pdf"
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Demonstrativo Financeiro em PDF",
            str(Path.home() / "Documents" / sugestao),
            "Arquivo PDF (*.pdf)"
        )
        if not caminho:
            return

        if not caminho.lower().endswith(".pdf"):
            caminho += ".pdf"

        sucesso = exportar_html_para_pdf(html, caminho)
        if sucesso:
            log_action(
                self.current_user["id"],
                self.current_user["nome"],
                "Exportação de Relatório PDF",
                f"Demonstrativo Financeiro ({d_ini} a {d_fim}) exportado em PDF"
            )
            QMessageBox.information(self, "Sucesso", f"Relatório PDF salvo com sucesso em:\n{caminho}")
        else:
            QMessageBox.critical(self, "Erro", "Não foi possível gerar o arquivo PDF.")

    # -------------------------------------------------------------
    # ABA 2: FICHA DO PACIENTE
    # -------------------------------------------------------------
    def init_tab_paciente(self):
        layout = QVBoxLayout(self.tab_paciente)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        filtros_bar = QHBoxLayout()
        filtros_bar.setSpacing(10)

        filtros_bar.addWidget(QLabel("Selecione o Paciente:"))
        self.cmb_paciente = QComboBox()
        self.cmb_paciente.setMinimumWidth(320)
        self.cmb_paciente.currentIndexChanged.connect(self.carregar_paciente_preview)
        filtros_bar.addWidget(self.cmb_paciente)

        btn_atualizar = QPushButton("🔄 Recarregar Pacientes")
        btn_atualizar.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #334155;
                font-weight: 600;
                padding: 7px 12px;
                border-radius: 6px;
                border: 1px solid #cbd5e1;
            }
        """)
        btn_atualizar.clicked.connect(self.atualizar_lista_pacientes)
        filtros_bar.addWidget(btn_atualizar)

        filtros_bar.addStretch()

        btn_exportar_pac = QPushButton("📄 Salvar Ficha em PDF")
        btn_exportar_pac.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                font-weight: bold;
                padding: 7px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        btn_exportar_pac.clicked.connect(self.exportar_paciente_pdf)
        filtros_bar.addWidget(btn_exportar_pac)

        layout.addLayout(filtros_bar)

        self.browser_paciente = QTextBrowser()
        self.browser_paciente.setStyleSheet("border: 1px solid #cbd5e1; border-radius: 6px; background: #ffffff;")
        layout.addWidget(self.browser_paciente)

        self.atualizar_lista_pacientes()

    def atualizar_lista_pacientes(self):
        self.cmb_paciente.blockSignals(True)
        self.cmb_paciente.clear()
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id, nome, cpf FROM patients WHERE ativo = 1 ORDER BY nome ASC")
            rows = c.fetchall()
            for r in rows:
                cpf_str = f" • CPF: {r['cpf']}" if r['cpf'] else ""
                self.cmb_paciente.addItem(f"{r['nome']}{cpf_str}", r["id"])
        self.cmb_paciente.blockSignals(False)
        self.carregar_paciente_preview()

    def carregar_paciente_preview(self):
        paciente_id = self.cmb_paciente.currentData()
        if not paciente_id:
            self.browser_paciente.setHtml("<p style='text-align:center; color:#64748b;'>Nenhum paciente cadastrado.</p>")
            return
        html = gerar_html_ficha_paciente(paciente_id)
        self.browser_paciente.setHtml(html)

    def exportar_paciente_pdf(self):
        paciente_id = self.cmb_paciente.currentData()
        if not paciente_id:
            return
        nome_paciente = self.cmb_paciente.currentText().split(" • ")[0].replace(" ", "_")
        html = gerar_html_ficha_paciente(paciente_id)

        sugestao = f"Prontuario_{nome_paciente}.pdf"
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Prontuário em PDF",
            str(Path.home() / "Documents" / sugestao),
            "Arquivo PDF (*.pdf)"
        )
        if not caminho:
            return

        if not caminho.lower().endswith(".pdf"):
            caminho += ".pdf"

        sucesso = exportar_html_para_pdf(html, caminho)
        if sucesso:
            log_action(
                self.current_user["id"],
                self.current_user["nome"],
                "Exportação de Prontuário PDF",
                f"Prontuário do paciente #{paciente_id} exportado em PDF"
            )
            QMessageBox.information(self, "Sucesso", f"Prontuário PDF salvo com sucesso em:\n{caminho}")
        else:
            QMessageBox.critical(self, "Erro", "Não foi possível gerar o arquivo PDF.")

    # -------------------------------------------------------------
    # ABA 3: ESTOQUE
    # -------------------------------------------------------------
    def init_tab_estoque(self):
        layout = QVBoxLayout(self.tab_estoque)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        filtros_bar = QHBoxLayout()
        filtros_bar.addWidget(QLabel("Inventário Físico e Financeiro de Materiais Odontológicos"))
        filtros_bar.addStretch()

        btn_atualizar_est = QPushButton("🔄 Atualizar Estoque")
        btn_atualizar_est.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #334155;
                font-weight: 600;
                padding: 7px 12px;
                border-radius: 6px;
                border: 1px solid #cbd5e1;
            }
        """)
        btn_atualizar_est.clicked.connect(self.carregar_estoque_preview)
        filtros_bar.addWidget(btn_atualizar_est)

        btn_exportar_est = QPushButton("📄 Salvar Relatório em PDF")
        btn_exportar_est.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                font-weight: bold;
                padding: 7px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        btn_exportar_est.clicked.connect(self.exportar_estoque_pdf)
        filtros_bar.addWidget(btn_exportar_est)

        layout.addLayout(filtros_bar)

        self.browser_estoque = QTextBrowser()
        self.browser_estoque.setStyleSheet("border: 1px solid #cbd5e1; border-radius: 6px; background: #ffffff;")
        layout.addWidget(self.browser_estoque)

        self.carregar_estoque_preview()

    def carregar_estoque_preview(self):
        html = gerar_html_relatorio_estoque()
        self.browser_estoque.setHtml(html)

    def exportar_estoque_pdf(self):
        html = gerar_html_relatorio_estoque()
        hoje_str = date.today().strftime("%Y%m%d")
        sugestao = f"Inventario_Estoque_{hoje_str}.pdf"
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Relatório de Estoque em PDF",
            str(Path.home() / "Documents" / sugestao),
            "Arquivo PDF (*.pdf)"
        )
        if not caminho:
            return

        if not caminho.lower().endswith(".pdf"):
            caminho += ".pdf"

        sucesso = exportar_html_para_pdf(html, caminho)
        if sucesso:
            log_action(
                self.current_user["id"],
                self.current_user["nome"],
                "Exportação de Estoque PDF",
                "Inventário de estoque exportado em PDF"
            )
            QMessageBox.information(self, "Sucesso", f"Relatório de estoque salvo com sucesso em:\n{caminho}")
        else:
            QMessageBox.critical(self, "Erro", "Não foi possível gerar o arquivo PDF.")
