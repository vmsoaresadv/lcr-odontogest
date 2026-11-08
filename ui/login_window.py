from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame, QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon, QPixmap
from services.auth_service import (
    authenticate, create_user, has_any_user,
    recover_admin_password, get_user_by_login
)

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo_clean.png"
ICO_PATH = Path(__file__).resolve().parent.parent / "assets" / "app_icon.ico"

# Paleta Oficial LCR Clínica Odontológica (Instagram @clinica.lcr)
# Primária: #2ca5a9 | Escura: #166260 | Fundo: #f8fafc | Texto: #0f172a
STYLE_SHEET = """
QWidget {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: #0f172a;
    background-color: #f8fafc;
}

QFrame#cardFrame {
    background-color: #ffffff;
    border-radius: 14px;
    border: 1px solid #e2e8f0;
}

QLabel#titleLabel {
    color: #166260;
    font-size: 21px;
    font-weight: bold;
}

QLabel#subtitleLabel {
    color: #64748b;
    font-size: 13px;
}

QLabel#fieldLabel {
    font-weight: 600;
    font-size: 13px;
    color: #334155;
    margin-top: 4px;
}

QLineEdit {
    background-color: #f8fafc;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 14px;
    min-height: 24px;
}

QLineEdit:focus {
    border: 2px solid #2ca5a9;
    background-color: #ffffff;
}

QPushButton#primaryButton {
    background-color: #2ca5a9;
    color: white;
    font-weight: bold;
    font-size: 14px;
    border: none;
    border-radius: 8px;
    padding: 12px;
    margin-top: 10px;
}

QPushButton#primaryButton:hover {
    background-color: #248a8d;
}

QPushButton#primaryButton:pressed {
    background-color: #166260;
}
"""


class FirstAccessDialog(QDialog):
    """Diálogo exibido apenas no primeiro acesso para criar a Administradora inicial."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LCR Clínica Odontológica - Configuração Inicial")
        self.setFixedSize(460, 520)
        self.setStyleSheet(STYLE_SHEET)
        if LOGO_PATH.exists():
            self.setWindowIcon(QIcon(str(LOGO_PATH)))
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        card = QFrame(self)
        card.setObjectName("cardFrame")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(8)

        # Logo
        if LOGO_PATH.exists():
            lbl_logo = QLabel(card)
            pix = QPixmap(str(LOGO_PATH)).scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_logo.setPixmap(pix)
            lbl_logo.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(lbl_logo)

        title = QLabel("Configuração Inicial", card)
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)

        sub = QLabel("Cadastre o usuário Administrador (Dentista / Proprietária):", card)
        sub.setObjectName("subtitleLabel")
        sub.setWordWrap(True)
        sub.setAlignment(Qt.AlignCenter)

        card_layout.addWidget(title)
        card_layout.addWidget(sub)
        card_layout.addSpacing(6)

        card_layout.addWidget(QLabel("Nome Completo:", objectName="fieldLabel"))
        self.txt_nome = QLineEdit(card)
        self.txt_nome.setPlaceholderText("Ex: Dra. Lara Camila")
        card_layout.addWidget(self.txt_nome)

        card_layout.addWidget(QLabel("Login de Acesso:", objectName="fieldLabel"))
        self.txt_login = QLineEdit(card)
        self.txt_login.setPlaceholderText("Ex: admin ou lara")
        card_layout.addWidget(self.txt_login)

        card_layout.addWidget(QLabel("Senha (mínimo 6 caracteres):", objectName="fieldLabel"))
        self.txt_senha = QLineEdit(card)
        self.txt_senha.setEchoMode(QLineEdit.Password)
        self.txt_senha.setPlaceholderText("••••••••")
        card_layout.addWidget(self.txt_senha)

        card_layout.addWidget(QLabel("Confirme a Senha:", objectName="fieldLabel"))
        self.txt_confirma = QLineEdit(card)
        self.txt_confirma.setEchoMode(QLineEdit.Password)
        self.txt_confirma.setPlaceholderText("••••••••")
        card_layout.addWidget(self.txt_confirma)

        self.btn_salvar = QPushButton("Salvar e Iniciar", card)
        self.btn_salvar.setObjectName("primaryButton")
        self.btn_salvar.clicked.connect(self.salvar_primeiro_admin)
        card_layout.addWidget(self.btn_salvar)

        layout.addWidget(card)

    def salvar_primeiro_admin(self):
        nome = self.txt_nome.text().strip()
        login = self.txt_login.text().strip()
        senha = self.txt_senha.text()
        confirma = self.txt_confirma.text()

        if not nome or not login or not senha:
            QMessageBox.warning(self, "Aviso", "Preencha todos os campos.")
            return

        if senha != confirma:
            QMessageBox.warning(self, "Aviso", "As senhas não coincidem.")
            return

        sucesso, msg = create_user(nome, login, senha, "admin")
        if sucesso:
            QMessageBox.information(self, "Sucesso", "Administrador cadastrado com sucesso!\nFaça login para continuar.")
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", msg)


class PasswordRecoveryDialog(QDialog):
    """Diálogo para recuperação de senha com Chave de Segurança."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Recuperação de Senha - LCR Odontologia")
        self.setFixedSize(450, 480)
        self.setStyleSheet(STYLE_SHEET)
        if LOGO_PATH.exists():
            self.setWindowIcon(QIcon(str(LOGO_PATH)))
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        card = QFrame(self)
        card.setObjectName("cardFrame")
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(22, 18, 22, 18)
        card_l.setSpacing(8)

        title = QLabel("Recuperação de Acesso", card)
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        card_l.addWidget(title)

        info = QLabel(
            "• Administradora: utilize a Chave de Segurança da clínica para definir nova senha.<br>"
            "• Secretárias: solicite a redefinição à Dra. Lara no menu de Usuários.", card
        )
        info.setStyleSheet("color: #64748b; font-size: 11px; line-height: 130%;")
        info.setWordWrap(True)
        card_l.addWidget(info)

        card_l.addWidget(QLabel("Usuário / Login (*):", objectName="fieldLabel"))
        self.txt_login = QLineEdit(card)
        self.txt_login.setPlaceholderText("Digite seu usuário")
        card_l.addWidget(self.txt_login)

        card_l.addWidget(QLabel("Chave de Segurança (*):", objectName="fieldLabel"))
        self.txt_chave = QLineEdit(card)
        self.txt_chave.setEchoMode(QLineEdit.Password)
        self.txt_chave.setPlaceholderText("Chave da clínica (Padrão: LCR2026)")
        card_l.addWidget(self.txt_chave)

        card_l.addWidget(QLabel("Nova Senha (*):", objectName="fieldLabel"))
        self.txt_nova_senha = QLineEdit(card)
        self.txt_nova_senha.setEchoMode(QLineEdit.Password)
        self.txt_nova_senha.setPlaceholderText("Mínimo de 6 caracteres")
        card_l.addWidget(self.txt_nova_senha)

        card_l.addWidget(QLabel("Confirmar Nova Senha (*):", objectName="fieldLabel"))
        self.txt_confirma = QLineEdit(card)
        self.txt_confirma.setEchoMode(QLineEdit.Password)
        self.txt_confirma.setPlaceholderText("Repita a nova senha")
        card_l.addWidget(self.txt_confirma)

        card_l.addStretch()

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("""
            background-color: #f1f5f9;
            color: #334155;
            font-weight: 600;
            padding: 8px 14px;
            border-radius: 6px;
            border: 1px solid #cbd5e1;
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_salvar = QPushButton("Redefinir Senha")
        btn_salvar.setStyleSheet("""
            background-color: #2ca5a9;
            color: #ffffff;
            font-weight: bold;
            padding: 8px 16px;
            border-radius: 6px;
            border: none;
        """)
        btn_salvar.clicked.connect(self.salvar)
        btn_box.addWidget(btn_salvar)

        card_l.addLayout(btn_box)
        layout.addWidget(card)

    def salvar(self):
        login = self.txt_login.text().strip()
        chave = self.txt_chave.text().strip()
        nova = self.txt_nova_senha.text()
        confirma = self.txt_confirma.text()

        if not login or not chave or not nova:
            QMessageBox.warning(self, "Aviso", "Preencha todos os campos obrigatórios.")
            return

        if nova != confirma:
            QMessageBox.warning(self, "Aviso", "A nova senha e a confirmação não coincidem.")
            return

        if len(nova) < 6:
            QMessageBox.warning(self, "Aviso", "A nova senha deve ter no mínimo 6 caracteres.")
            return

        ok, msg = recover_admin_password(login, chave, nova)
        if ok:
            QMessageBox.information(self, "Sucesso", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Aviso", msg)


class LoginWindow(QWidget):
    """Janela de Login do Sistema com a identidade visual da LCR."""
    login_successful = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LCR OdontoGest - Acesso")
        self.setFixedSize(430, 520)
        self.setStyleSheet(STYLE_SHEET)
        icon_to_use = ICO_PATH if ICO_PATH.exists() else LOGO_PATH
        if icon_to_use.exists():
            self.setWindowIcon(QIcon(str(icon_to_use)))
        screen = QApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            geo = self.frameGeometry()
            geo.moveCenter(avail.center())
            self.move(geo.topLeft())
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)

        card = QFrame(self)
        card.setObjectName("cardFrame")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(26, 24, 26, 24)
        card_layout.setSpacing(10)

        # Logo da LCR Odontologia
        if LOGO_PATH.exists():
            lbl_logo = QLabel(card)
            pix = QPixmap(str(LOGO_PATH)).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_logo.setPixmap(pix)
            lbl_logo.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(lbl_logo)

        title = QLabel("LCR Odontologia", card)
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)

        sub = QLabel("Dra. Lara Camila • CRO-BA 15247\nIrecê - Bahia", card)
        sub.setObjectName("subtitleLabel")
        sub.setAlignment(Qt.AlignCenter)

        card_layout.addWidget(title)
        card_layout.addWidget(sub)
        card_layout.addSpacing(6)

        card_layout.addWidget(QLabel("Usuário / Login:", objectName="fieldLabel"))
        self.txt_login = QLineEdit(card)
        self.txt_login.setPlaceholderText("Digite seu usuário")
        card_layout.addWidget(self.txt_login)

        card_layout.addWidget(QLabel("Senha:", objectName="fieldLabel"))
        self.txt_senha = QLineEdit(card)
        self.txt_senha.setEchoMode(QLineEdit.Password)
        self.txt_senha.setPlaceholderText("Digite sua senha")
        self.txt_senha.returnPressed.connect(self.executar_login)
        self.txt_login.returnPressed.connect(lambda: self.txt_senha.setFocus())
        card_layout.addWidget(self.txt_senha)

        self.btn_entrar = QPushButton("Acessar Sistema", card)
        self.btn_entrar.setObjectName("primaryButton")
        self.btn_entrar.clicked.connect(self.executar_login)
        card_layout.addWidget(self.btn_entrar)

        self.btn_esqueci = QPushButton("Esqueceu sua senha?", card)
        self.btn_esqueci.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #2ca5a9;
                font-size: 12px;
                border: none;
                padding: 4px;
                font-weight: 600;
            }
            QPushButton:hover {
                color: #166260;
                text-decoration: underline;
            }
        """)
        self.btn_esqueci.clicked.connect(self.abrir_recuperacao_senha)
        card_layout.addWidget(self.btn_esqueci)

        card_layout.addStretch()

        footer = QLabel("Uso interno protegido por senha • LGPD", card)
        footer.setStyleSheet("color: #94a3b8; font-size: 11px;")
        footer.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(footer)

        main_layout.addWidget(card)

    def abrir_recuperacao_senha(self):
        dlg = PasswordRecoveryDialog(self)
        dlg.exec()

    def executar_login(self):
        login = self.txt_login.text()
        senha = self.txt_senha.text()

        user, msg = authenticate(login, senha)
        if user:
            self.login_successful.emit(user)
            self.close()
        else:
            QMessageBox.warning(self, "Falha no Login", msg)
            self.txt_senha.clear()
            self.txt_senha.setFocus()
