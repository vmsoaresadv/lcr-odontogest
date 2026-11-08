# ui/users_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QLineEdit, QComboBox, QFrame
)
from PySide6.QtCore import Qt
from services.auth_service import list_users, create_user, toggle_user_active, reset_user_password


DIALOG_STYLESHEET = """
QDialog {
    background-color: #ffffff;
    font-family: 'Segoe UI', sans-serif;
}
QLabel {
    color: #1e293b;
    font-size: 13px;
    font-weight: 600;
}
QLineEdit {
    background-color: #f8fafc;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 13px;
    min-height: 22px;
    selection-background-color: #0d9488;
}
QLineEdit:focus {
    border: 2px solid #0d9488;
    background-color: #ffffff;
}
QComboBox {
    background-color: #f8fafc;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 32px 6px 12px;
    font-size: 13px;
    min-height: 22px;
}
QComboBox:focus {
    border: 2px solid #0d9488;
    background-color: #ffffff;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 26px;
    border-left: 1px solid #cbd5e1;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #0f172a;
    selection-background-color: #0d9488;
    selection-color: #ffffff;
    padding: 4px;
}
QPushButton#btnSalvar {
    background-color: #0d9488;
    color: #ffffff;
    font-weight: bold;
    padding: 10px 18px;
    border-radius: 6px;
    border: none;
    font-size: 13px;
}
QPushButton#btnSalvar:hover {
    background-color: #0f766e;
}
QPushButton#btnCancelar {
    background-color: #e2e8f0;
    color: #334155;
    font-weight: 600;
    padding: 10px 18px;
    border-radius: 6px;
    border: none;
    font-size: 13px;
}
QPushButton#btnCancelar:hover {
    background-color: #cbd5e1;
}
"""


class NewUserDialog(QDialog):
    """Diálogo para o Administrador cadastrar um novo usuário."""
    def __init__(self, current_admin: dict, parent=None):
        super().__init__(parent)
        self.current_admin = current_admin
        self.setWindowTitle("Cadastrar Novo Usuário")
        self.setFixedSize(450, 440)
        self.setStyleSheet(DIALOG_STYLESHEET)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Novo Usuário do Sistema")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f766e; margin-bottom: 6px;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Nome Completo:"))
        self.txt_nome = QLineEdit()
        self.txt_nome.setPlaceholderText("Ex: Maria Oliveira")
        layout.addWidget(self.txt_nome)

        layout.addWidget(QLabel("Login de Acesso:"))
        self.txt_login = QLineEdit()
        self.txt_login.setPlaceholderText("Ex: maria.recepcao")
        layout.addWidget(self.txt_login)

        layout.addWidget(QLabel("Perfil de Acesso:"))
        self.cmb_perfil = QComboBox()
        self.cmb_perfil.addItem("Secretária (Acesso Operacional)", "secretaria")
        self.cmb_perfil.addItem("Administrador (Acesso Total)", "admin")
        layout.addWidget(self.cmb_perfil)

        layout.addWidget(QLabel("Senha Inicial (mínimo 6 caracteres):"))
        self.txt_senha = QLineEdit()
        self.txt_senha.setEchoMode(QLineEdit.Password)
        self.txt_senha.setPlaceholderText("••••••••")
        layout.addWidget(self.txt_senha)

        layout.addSpacing(14)

        btn_box = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("btnCancelar")
        btn_cancelar.clicked.connect(self.reject)

        btn_salvar = QPushButton("Salvar Usuário")
        btn_salvar.setObjectName("btnSalvar")
        btn_salvar.clicked.connect(self.salvar)

        btn_box.addWidget(btn_cancelar)
        btn_box.addWidget(btn_salvar)
        layout.addLayout(btn_box)

    def salvar(self):
        nome = self.txt_nome.text().strip()
        login = self.txt_login.text().strip()
        perfil = self.cmb_perfil.currentData()
        senha = self.txt_senha.text()

        if not nome or not login or not senha:
            QMessageBox.warning(self, "Aviso", "Preencha todos os campos.")
            return

        sucesso, msg = create_user(
            nome, login, senha, perfil,
            current_admin_id=self.current_admin["id"],
            current_admin_nome=self.current_admin["nome"]
        )
        if sucesso:
            QMessageBox.information(self, "Sucesso", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", msg)


class ResetPasswordDialog(QDialog):
    """Diálogo para redefinir senha de um usuário."""
    def __init__(self, user_id: int, user_login: str, current_admin: dict, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.user_login = user_login
        self.current_admin = current_admin
        self.setWindowTitle(f"Redefinir Senha - {user_login}")
        self.setFixedSize(360, 220)
        self.setStyleSheet(DIALOG_STYLESHEET)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(10)

        lbl = QLabel(f"Nova senha para '{self.user_login}':")
        lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #0f766e;")
        layout.addWidget(lbl)

        self.txt_senha = QLineEdit()
        self.txt_senha.setEchoMode(QLineEdit.Password)
        self.txt_senha.setPlaceholderText("Mínimo 6 caracteres")
        layout.addWidget(self.txt_senha)

        layout.addSpacing(12)

        btn_box = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("btnCancelar")
        btn_cancelar.clicked.connect(self.reject)

        btn_salvar = QPushButton("Alterar Senha")
        btn_salvar.setObjectName("btnSalvar")
        btn_salvar.clicked.connect(self.salvar)

        btn_box.addWidget(btn_cancelar)
        btn_box.addWidget(btn_salvar)
        layout.addLayout(btn_box)

    def salvar(self):
        nova_senha = self.txt_senha.text()
        sucesso, msg = reset_user_password(
            self.user_id, nova_senha,
            self.current_admin["id"],
            self.current_admin["nome"]
        )
        if sucesso:
            QMessageBox.information(self, "Sucesso", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Aviso", msg)


class UsersView(QWidget):
    """Gerenciamento de usuários exclusivo da Administradora."""
    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.init_ui()
        self.carregar_usuarios()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header_layout = QHBoxLayout()
        title = QLabel("Controle de Usuários e Permissões")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f766e;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        btn_novo = QPushButton("+ Novo Usuário")
        btn_novo.setStyleSheet("""
            background-color: #0d9488;
            color: #ffffff;
            font-weight: bold;
            padding: 8px 16px;
            border-radius: 6px;
            border: none;
        """)
        btn_novo.clicked.connect(self.abrir_dialogo_novo_usuario)
        header_layout.addWidget(btn_novo)

        layout.addLayout(header_layout)

        desc = QLabel("Gerencie os acessos da clínica. O perfil 'Secretária' não tem acesso a relatórios e logs.")
        desc.setStyleSheet("color: #64748b; font-size: 13px;")
        layout.addWidget(desc)

        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Nome Completo", "Login", "Perfil", "Status", "Criado Em"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
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
                padding: 8px;
                border: none;
                border-bottom: 2px solid #cbd5e1;
            }
            QTableWidget::item {
                color: #0f172a;
                padding: 6px;
            }
        """)
        layout.addWidget(self.table)

        # Botões de Ação na Linha Selecionada
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()

        btn_status = QPushButton("Ativar / Desativar Selecionado")
        btn_status.setStyleSheet("""
            background-color: #e2e8f0;
            color: #334155;
            font-weight: bold;
            padding: 8px 14px;
            border-radius: 6px;
            border: none;
        """)
        btn_status.clicked.connect(self.alternar_status_usuario)
        actions_layout.addWidget(btn_status)

        btn_reset_senha = QPushButton("Redefinir Senha")
        btn_reset_senha.setStyleSheet("""
            background-color: #e2e8f0;
            color: #334155;
            font-weight: bold;
            padding: 8px 14px;
            border-radius: 6px;
            border: none;
        """)
        btn_reset_senha.clicked.connect(self.redefinir_senha_usuario)
        actions_layout.addWidget(btn_reset_senha)

        layout.addLayout(actions_layout)

    def carregar_usuarios(self):
        usuarios = list_users()
        self.table.setRowCount(len(usuarios))

        for row_idx, user in enumerate(usuarios):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(user["id"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(user["nome"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(user["login"]))
            
            perfil_txt = "Administradora" if user["perfil"] == "admin" else "Secretária"
            item_perfil = QTableWidgetItem(perfil_txt)
            self.table.setItem(row_idx, 3, item_perfil)

            status_txt = "Ativo" if user["ativo"] else "Inativo"
            item_status = QTableWidgetItem(status_txt)
            if user["ativo"]:
                item_status.setForeground(Qt.darkGreen)
            else:
                item_status.setForeground(Qt.red)
            self.table.setItem(row_idx, 4, item_status)

            self.table.setItem(row_idx, 5, QTableWidgetItem(str(user["criado_em"])))

    def get_selected_user_id_and_login(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Aviso", "Selecione um usuário na tabela.")
            return None, None
        row = selected_rows[0].row()
        user_id = int(self.table.item(row, 0).text())
        user_login = self.table.item(row, 2).text()
        return user_id, user_login

    def abrir_dialogo_novo_usuario(self):
        dialog = NewUserDialog(self.current_user, self)
        if dialog.exec() == QDialog.Accepted:
            self.carregar_usuarios()

    def alternar_status_usuario(self):
        user_id, login = self.get_selected_user_id_and_login()
        if not user_id:
            return

        sucesso, msg = toggle_user_active(user_id, self.current_user["id"], self.current_user["nome"])
        if sucesso:
            QMessageBox.information(self, "Sucesso", msg)
            self.carregar_usuarios()
        else:
            QMessageBox.warning(self, "Aviso", msg)

    def redefinir_senha_usuario(self):
        user_id, login = self.get_selected_user_id_and_login()
        if not user_id:
            return

        dialog = ResetPasswordDialog(user_id, login, self.current_user, self)
        if dialog.exec() == QDialog.Accepted:
            self.carregar_usuarios()

