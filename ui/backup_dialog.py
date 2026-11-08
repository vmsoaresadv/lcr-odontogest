from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QFrame, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from services.backup_service import (
    criar_backup_completo, restaurar_backup_completo, listar_backups_locais
)

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo_clean.png"
ICO_PATH = Path(__file__).resolve().parent.parent / "assets" / "app_icon.ico"


class BackupDialog(QDialog):
    """Diálogo de gerenciamento de backup e restauração do LCR OdontoGest."""
    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.setWindowTitle("LCR OdontoGest - Backup e Segurança em 1 Clique")
        self.setMinimumSize(680, 520)
        self.resize(720, 550)

        icon_to_use = ICO_PATH if ICO_PATH.exists() else LOGO_PATH
        if icon_to_use.exists():
            self.setWindowIcon(QIcon(str(icon_to_use)))

        self.init_ui()
        self.carregar_historico()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header Card
        card_header = QFrame(self)
        card_header.setStyleSheet("""
            QFrame {
                background-color: #f0fdfa;
                border: 1px solid #99f6e4;
                border-radius: 10px;
                padding: 14px;
            }
        """)
        card_layout = QVBoxLayout(card_header)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(6)

        title = QLabel("💾 Central de Backup e Proteção de Dados (LGPD)")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f766e;")
        card_layout.addWidget(title)

        desc = QLabel(
            "Gera uma cópia completa e compactada (.zip) com o banco de dados seguro da clínica e todos os "
            "anexos/exames cadastrados. Você pode salvar em um pendrive, HD externo ou pasta do Google Drive/OneDrive."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 13px; color: #334155;")
        card_layout.addWidget(desc)

        layout.addWidget(card_header)

        # Botões de Ação Rápida
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)

        self.btn_fazer_backup = QPushButton("⚡ Fazer Backup Completo Agora")
        self.btn_fazer_backup.setStyleSheet("""
            QPushButton {
                background-color: #0d9488;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                padding: 10px 18px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0f766e;
            }
        """)
        self.btn_fazer_backup.clicked.connect(self.executar_backup)
        actions_layout.addWidget(self.btn_fazer_backup)

        self.btn_restaurar = QPushButton("🔄 Restaurar Backup do Arquivo...")
        self.btn_restaurar.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #475569;
                font-weight: 600;
                font-size: 13px;
                padding: 10px 16px;
                border-radius: 6px;
                border: 1px solid #cbd5e1;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                color: #0f172a;
            }
        """)
        self.btn_restaurar.clicked.connect(self.executar_restauracao)
        actions_layout.addWidget(self.btn_restaurar)

        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        # Tabela de Histórico de Backups Locais
        lbl_historico = QLabel("Cópias de Segurança Salvas na Pasta do Sistema:")
        lbl_historico.setStyleSheet("font-weight: bold; color: #0f172a; font-size: 13px; margin-top: 6px;")
        layout.addWidget(lbl_historico)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Arquivo de Backup", "Data / Hora", "Tamanho"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                color: #0f172a;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                color: #334155;
                font-weight: bold;
                padding: 6px;
                border: none;
                border-bottom: 2px solid #cbd5e1;
            }
        """)
        layout.addWidget(self.table)

        # Rodapé com botão Fechar
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setStyleSheet("""
            background-color: #f1f5f9;
            color: #334155;
            font-weight: 600;
            padding: 8px 18px;
            border-radius: 6px;
            border: 1px solid #cbd5e1;
        """)
        btn_fechar.clicked.connect(self.accept)
        footer_layout.addWidget(btn_fechar)

        layout.addLayout(footer_layout)

    def carregar_historico(self):
        backups = listar_backups_locais()
        self.table.setRowCount(len(backups))
        for row, bkp in enumerate(backups):
            item_id = QTableWidgetItem(str(row + 1))
            item_id.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, item_id)

            item_nome = QTableWidgetItem(f"📦 {bkp['nome']}")
            self.table.setItem(row, 1, item_nome)

            item_data = QTableWidgetItem(bkp["data"])
            item_data.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, item_data)

            item_tam = QTableWidgetItem(f"{bkp['tamanho_mb']} MB")
            item_tam.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, item_tam)

    def executar_backup(self):
        # Permite escolher onde salvar (com opção padrão na pasta de documentos ou pendrive)
        default_dir = str(Path.home() / "Documents")
        caminho_escolhido, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Cópia de Segurança Completa",
            default_dir,
            "Arquivo Compactado ZIP (*.zip)"
        )
        if not caminho_escolhido:
            # Usuário cancelou
            return

        if not caminho_escolhido.lower().endswith(".zip"):
            caminho_escolhido += ".zip"

        QApplication.setOverrideCursor(Qt.WaitCursor)
        sucesso, msg = criar_backup_completo(caminho_escolhido, user_info=self.current_user)
        QApplication.restoreOverrideCursor()

        if sucesso:
            QMessageBox.information(
                self,
                "Backup Realizado com Sucesso!",
                f"A cópia de segurança foi gravada com sucesso em:\n\n{caminho_escolhido}\n\n"
                "Guarde este arquivo em local seguro (pendrive ou nuvem) para proteção dos dados da clínica."
            )
            self.carregar_historico()
        else:
            QMessageBox.critical(self, "Erro ao Gerar Backup", msg)

    def executar_restauracao(self):
        resposta = QMessageBox.warning(
            self,
            "Atenção - Restauração de Dados",
            "A restauração substituirá todos os dados atuais pelo arquivo selecionado.\n\n"
            "O sistema fará automaticamente uma cópia de segurança emergencial antes da restauração.\n\n"
            "Deseja prosseguir?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if resposta != QMessageBox.Yes:
            return

        caminho_zip, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Arquivo de Backup para Restauração",
            str(Path.home() / "Documents"),
            "Arquivo Compactado ZIP (*.zip)"
        )
        if not caminho_zip:
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        sucesso, msg = restaurar_backup_completo(caminho_zip, user_info=self.current_user)
        QApplication.restoreOverrideCursor()

        if sucesso:
            QMessageBox.information(
                self,
                "Restauração Concluída",
                f"{msg}\n\nRecomendamos reiniciar o aplicativo para que todos os dados restaurados sejam recarregados."
            )
            self.carregar_historico()
        else:
            QMessageBox.critical(self, "Falha na Restauração", msg)
