from pathlib import Path
import sys
from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from database.connection import init_db, fazer_backup_diario
from services.auth_service import has_any_user
from ui.login_window import LoginWindow, FirstAccessDialog
from ui.main_window import MainWindow
from version import get_asset_path

LOGO_PATH = get_asset_path("logo_clean.png")
ICO_PATH = get_asset_path("app_icon.ico")


class AppController:
    """Controlador principal do ciclo de vida da aplicação."""
    def __init__(self):
        self.login_window = None
        self.main_window = None

    def start(self):
        # 1. Garante que as tabelas do banco de dados estejam criadas e faz backup diário de segurança
        init_db()
        fazer_backup_diario()

        # 2. Se for o primeiríssimo acesso (sem nenhum usuário cadastrado), abre o assistente
        if not has_any_user():
            first_dialog = FirstAccessDialog()
            if first_dialog.exec() != QDialog.Accepted:
                # Se fechar sem cadastrar, encerra
                sys.exit(0)

        # 3. Abre a tela de login
        self.show_login()

    def show_login(self):
        self.login_window = LoginWindow()
        self.login_window.login_successful.connect(self.show_main)
        self.login_window.show()

    def show_main(self, user_dict: dict):
        self.main_window = MainWindow(user_dict)
        self.main_window.logout_requested.connect(self.show_login)
        self.main_window.show()


GLOBAL_APP_STYLE = """
QWidget {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: #0f172a;
}
QLineEdit, QTextEdit, QPlainTextEdit {
    color: #0f172a;
    background-color: #ffffff;
    selection-background-color: #0d9488;
    selection-color: #ffffff;
}
QComboBox {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 28px 6px 12px;
    font-size: 13px;
    min-height: 22px;
}
QComboBox:hover {
    border-color: #94a3b8;
}
QComboBox:focus, QComboBox:on {
    border: 2px solid #2ca5a9;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid #cbd5e1;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
    background-color: #f8fafc;
}
QComboBox::down-arrow {
    width: 0px;
    height: 0px;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #64748b;
    margin-top: 2px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 4px;
    outline: none;
    selection-background-color: #f0fdfa;
    selection-color: #0f766e;
}
QComboBox QAbstractItemView::item {
    min-height: 28px;
    padding: 4px 10px;
    border-radius: 4px;
}
QComboBox QAbstractItemView::item:hover {
    background-color: #f1f5f9;
    color: #0f766e;
}
QComboBox QAbstractItemView::item:selected {
    background-color: #ccfbf1;
    color: #0f766e;
    font-weight: 600;
}

/* Scrollbars modernas, arredondadas e discretas */
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

QLabel {
    color: #0f172a;
}
QTableWidget {
    color: #0f172a;
    background-color: #ffffff;
}
QHeaderView::section {
    color: #334155;
    background-color: #f8fafc;
}
QMessageBox {
    background-color: #ffffff;
}
QMessageBox QLabel {
    color: #0f172a;
}
"""


def main():
    # No Windows, define o AppUserModelID para que o ícone oficial apareça na Barra de Tarefas
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("lcrodontogest.app.1.0")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("LCR OdontoGest")
    app.setApplicationDisplayName("LCR OdontoGest - Dra. Lara Camila")
    # Desativa animações nativas que causam 'engasgos' / flickering nos combos no Windows
    app.setEffectEnabled(Qt.UI_AnimateCombo, False)
    app.setEffectEnabled(Qt.UI_AnimateTooltip, False)

    icon_to_use = ICO_PATH if ICO_PATH.exists() else LOGO_PATH
    if icon_to_use.exists():
        app.setWindowIcon(QIcon(str(icon_to_use)))
    app.setStyleSheet(GLOBAL_APP_STYLE)

    controller = AppController()
    controller.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
