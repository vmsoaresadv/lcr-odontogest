from datetime import datetime, date, timedelta
from typing import Optional, List, Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialog, QTabWidget, QTextEdit, QComboBox,
    QDateEdit, QFrame, QScrollArea, QGridLayout, QSizePolicy,
    QDoubleSpinBox, QCheckBox, QTimeEdit
)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QFont, QColor, QPixmap, QGuiApplication
from ui.custom_date_edit import CustomDateEdit

from services.sublocacao_service import (
    get_sublocacao_settings, save_sublocacao_settings,
    list_partners, get_partner, create_partner, update_partner, delete_partner, restore_partner,
    create_rental, list_rentals_by_date, list_all_rentals, get_rental,
    checkin_rental, checkout_rental, update_rental_final_value,
    mark_rental_as_paid, cancel_rental, delete_rental,
    build_sublocacao_whatsapp_message, build_partner_whatsapp_message
)
from services.pix_service import generate_pix_copy_paste, generate_pix_qr_pixmap
from services.patient_service import format_telefone, format_cpf
from services.schedule_service import open_whatsapp
from ui.schedule_view import SendWhatsAppPreviewDialog
from ui.patients_view import perguntar_sim_nao, aplicar_mascara_telefone, aplicar_mascara_cpf

SUBLOCACAO_STYLE = """
QDialog {
    background-color: #f8fafc;
    font-family: 'Segoe UI', sans-serif;
}
QWidget {
    font-family: 'Segoe UI', sans-serif;
    color: #0f172a;
}
QLabel {
    color: #1e293b;
    font-size: 13px;
    font-weight: 600;
    background: transparent;
    border: none;
}
QTabWidget::pane {
    border: 1px solid #e2e8f0;
    background-color: #ffffff;
    border-radius: 8px;
    padding: 10px;
}
QTabBar::tab {
    background-color: #f1f5f9;
    color: #475569;
    font-weight: 600;
    padding: 9px 18px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
}
QTabBar::tab:selected {
    background-color: #2ca5a9;
    color: #ffffff;
}
QLineEdit, QTextEdit {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 7px 10px;
    font-size: 13px;
    min-height: 24px;
    selection-background-color: #2ca5a9;
    selection-color: #ffffff;
}
QComboBox {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 28px 6px 12px;
    font-size: 13px;
    min-height: 24px;
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

QDateEdit, QTimeEdit, QDoubleSpinBox {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 13px;
    min-height: 28px;
    selection-background-color: #2ca5a9;
    selection-color: #ffffff;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus, QTextEdit:focus, QDoubleSpinBox:focus {
    border: 2px solid #2ca5a9;
    background-color: #ffffff;
}
QFrame#boxTarifas {
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
}
QFrame#boxPix {
    background-color: #f0fdfa;
    border: 1px solid #ccfbf1;
    border-radius: 8px;
}
QFrame#cardPreco {
    background-color: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
}
QFrame#cardResumo {
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
}
QFrame#cardValor {
    background-color: #f0fdfa;
    border: 2px solid #2ca5a9;
    border-radius: 8px;
}
QFrame#barNav {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
}
QPushButton#primaryBtn {
    background-color: #2ca5a9;
    color: #ffffff;
    font-weight: bold;
    padding: 8px 14px;
    border-radius: 6px;
    border: none;
    font-size: 13px;
}
QPushButton#primaryBtn:hover {
    background-color: #248a8d;
}
QPushButton#whatsappBtn {
    background-color: #25d366;
    color: #ffffff;
    font-weight: bold;
    padding: 8px 14px;
    border-radius: 6px;
    border: none;
    font-size: 13px;
}
QPushButton#whatsappBtn:hover {
    background-color: #1eb857;
}
QPushButton#secondaryBtn {
    background-color: #f1f5f9;
    color: #334155;
    font-weight: 600;
    padding: 7px 12px;
    border-radius: 6px;
    border: 1px solid #cbd5e1;
    font-size: 12px;
}
QPushButton#secondaryBtn:hover {
    background-color: #e2e8f0;
}
QPushButton#dangerBtn {
    background-color: #fee2e2;
    color: #b91c1c;
    font-weight: 600;
    padding: 7px 12px;
    border-radius: 6px;
    border: 1px solid #fca5a5;
    font-size: 12px;
}
QPushButton#dangerBtn:hover {
    background-color: #fecaca;
}
"""


# -------------------------------------------------------------
# DIÁLOGO DE CONFIGURAÇÕES DA SALA 2 E DADOS DO PIX
# -------------------------------------------------------------

class SublocacaoSettingsDialog(QDialog):
    """Configuração de Tarifas Padrão, Chave Pix e Mensagem para a Sala 2."""
    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.setWindowTitle("Configurar Sublocação e Pix")
        self.resize(550, 650)
        self.setMinimumSize(520, 600)
        self.setStyleSheet(SUBLOCACAO_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        title = QLabel("Configurações da Sublocação")
        title.setStyleSheet("font-size: 17px; font-weight: bold; color: #166260;")
        layout.addWidget(title)

        # 1. Tarifas Padrão
        box_tarifas = QFrame()
        box_tarifas.setObjectName("boxTarifas")
        v_tarifas = QVBoxLayout(box_tarifas)
        v_tarifas.setContentsMargins(14, 12, 14, 12)
        v_tarifas.setSpacing(8)

        lbl_t_header = QLabel("Tarifas Padrão da Clínica:")
        lbl_t_header.setStyleSheet("color: #0f766e; font-weight: bold; font-size: 14px;")
        v_tarifas.addWidget(lbl_t_header)

        row_t1 = QHBoxLayout()
        row_t1.addWidget(QLabel("Tarifa por Hora (R$):"))
        self.spn_hora = QDoubleSpinBox()
        self.spn_hora.setRange(0, 5000)
        self.spn_hora.setDecimals(2)
        self.spn_hora.setMinimumHeight(32)
        self.spn_hora.setMinimumWidth(120)
        row_t1.addWidget(self.spn_hora)
        v_tarifas.addLayout(row_t1)

        row_t2 = QHBoxLayout()
        row_t2.addWidget(QLabel("Tarifa por Turno (R$):"))
        self.spn_turno = QDoubleSpinBox()
        self.spn_turno.setRange(0, 5000)
        self.spn_turno.setDecimals(2)
        self.spn_turno.setMinimumHeight(32)
        self.spn_turno.setMinimumWidth(120)
        row_t2.addWidget(self.spn_turno)
        v_tarifas.addLayout(row_t2)

        row_t3 = QHBoxLayout()
        row_t3.addWidget(QLabel("Tarifa por Diária (R$):"))
        self.spn_diaria = QDoubleSpinBox()
        self.spn_diaria.setRange(0, 5000)
        self.spn_diaria.setDecimals(2)
        self.spn_diaria.setMinimumHeight(32)
        self.spn_diaria.setMinimumWidth(120)
        row_t3.addWidget(self.spn_diaria)
        v_tarifas.addLayout(row_t3)
        layout.addWidget(box_tarifas)

        # 2. Dados do Pix
        box_pix = QFrame()
        box_pix.setObjectName("boxPix")
        v_pix = QVBoxLayout(box_pix)
        v_pix.setContentsMargins(14, 12, 14, 12)
        v_pix.setSpacing(8)

        lbl_p_header = QLabel("Dados da Conta Pix para Recebimento:")
        lbl_p_header.setStyleSheet("color: #0f766e; font-weight: bold; font-size: 14px;")
        v_pix.addWidget(lbl_p_header)

        v_pix.addWidget(QLabel("Chave Pix (Celular, CPF, CNPJ, Email):"))
        self.txt_chave = QLineEdit()
        self.txt_chave.setPlaceholderText("Ex: 749991266602")
        self.txt_chave.setMinimumHeight(32)
        v_pix.addWidget(self.txt_chave)

        row_p2 = QHBoxLayout()
        v_tit = QVBoxLayout()
        v_tit.addWidget(QLabel("Nome do Titular:"))
        self.txt_titular = QLineEdit()
        self.txt_titular.setPlaceholderText("Ex: Dra. Lara Camila")
        self.txt_titular.setMinimumHeight(32)
        v_tit.addWidget(self.txt_titular)
        row_p2.addLayout(v_tit)

        v_cid = QVBoxLayout()
        v_cid.addWidget(QLabel("Cidade da Conta:"))
        self.txt_cidade = QLineEdit()
        self.txt_cidade.setPlaceholderText("Ex: Irecê")
        self.txt_cidade.setMinimumHeight(32)
        v_cid.addWidget(self.txt_cidade)
        row_p2.addLayout(v_cid)
        v_pix.addLayout(row_p2)
        layout.addWidget(box_pix)

        # 3. Mensagem Padrão de Contato com Parceiro (WhatsApp)
        layout.addWidget(QLabel("Mensagem Padrão para Chamar Parceiro no WhatsApp:"))
        self.txt_msg_parceiro = QTextEdit()
        self.txt_msg_parceiro.setMaximumHeight(85)
        self.txt_msg_parceiro.setPlaceholderText("Use {parceiro} para o nome automático...")
        layout.addWidget(self.txt_msg_parceiro)

        layout.addStretch()

        # Botões
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("secondaryBtn")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_save = QPushButton("Salvar Configurações")
        btn_save.setObjectName("primaryBtn")
        btn_save.clicked.connect(self.salvar)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

        # Carrega dados atuais
        self.carregar_dados()

    def carregar_dados(self):
        cfg = get_sublocacao_settings()
        self.spn_hora.setValue(cfg["tarifa_hora"])
        self.spn_turno.setValue(cfg["tarifa_turno"])
        self.spn_diaria.setValue(cfg["tarifa_diaria"])
        self.txt_chave.setText(cfg["pix_chave"])
        self.txt_titular.setText(cfg["pix_titular"])
        self.txt_cidade.setText(cfg["pix_cidade"])
        self.txt_msg_parceiro.setPlainText(cfg.get("msg_parceiro", ""))

    def salvar(self):
        chave = self.txt_chave.text().strip()
        titular = self.txt_titular.text().strip()
        cidade = self.txt_cidade.text().strip()
        msg_parceiro = self.txt_msg_parceiro.toPlainText().strip()
        if not chave:
            QMessageBox.warning(self, "Aviso", "A Chave Pix é obrigatória para gerar o QR Code.")
            return

        ok, msg = save_sublocacao_settings(
            self.spn_hora.value(),
            self.spn_turno.value(),
            self.spn_diaria.value(),
            chave, titular or "LCR CLINICA", cidade or "IRECE",
            self.current_user["id"], self.current_user["nome"],
            msg_parceiro=msg_parceiro
        )
        if ok:
            QMessageBox.information(self, "Sucesso", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", msg)


# -------------------------------------------------------------
# DIÁLOGO DE CADASTRO / EDIÇÃO DE PARCEIRO
# -------------------------------------------------------------

class PartnerFormDialog(QDialog):
    """Diálogo para Cadastrar ou Editar Profissional Parceiro."""
    def __init__(self, current_user: dict, partner: dict = None, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.partner = partner
        self.is_edit = partner is not None
        self.setWindowTitle("Editar Profissional Parceiro" if self.is_edit else "Novo Profissional Parceiro")
        self.resize(540, 620)
        self.setMinimumSize(520, 580)
        self.setStyleSheet(SUBLOCACAO_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        title = QLabel("Editar Parceiro" if self.is_edit else "Cadastrar Profissional Parceiro")
        title.setStyleSheet("font-size: 17px; font-weight: bold; color: #166260;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Nome Completo (*):"))
        self.txt_nome = QLineEdit()
        self.txt_nome.setPlaceholderText("Ex: Dra. Juliana Santos")
        self.txt_nome.setMinimumHeight(32)
        layout.addWidget(self.txt_nome)

        row_esp = QHBoxLayout()
        v_esp = QVBoxLayout()
        v_esp.addWidget(QLabel("Profissão / Especialidade:"))
        self.txt_esp = QLineEdit()
        self.txt_esp.setPlaceholderText("Ex: Fisioterapia, Biomédica, Psicologia...")
        self.txt_esp.setMinimumHeight(32)
        v_esp.addWidget(self.txt_esp)
        row_esp.addLayout(v_esp)

        v_cpf = QVBoxLayout()
        v_cpf.addWidget(QLabel("CPF:"))
        self.txt_cpf = QLineEdit()
        self.txt_cpf.setPlaceholderText("000.000.000-00")
        self.txt_cpf.setMinimumHeight(32)
        self.txt_cpf.textEdited.connect(lambda t: self._aplicar_mascara(self.txt_cpf, aplicar_mascara_cpf))
        self.txt_cpf.editingFinished.connect(lambda: self.txt_cpf.setText(format_cpf(self.txt_cpf.text())))
        v_cpf.addWidget(self.txt_cpf)
        row_esp.addLayout(v_cpf)
        layout.addLayout(row_esp)

        row_contato = QHBoxLayout()
        v_tel = QVBoxLayout()
        v_tel.addWidget(QLabel("Telefone / WhatsApp (*):"))
        self.txt_tel = QLineEdit()
        self.txt_tel.setPlaceholderText("(74) 99999-9999")
        self.txt_tel.setMinimumHeight(32)
        self.txt_tel.textEdited.connect(lambda t: self._aplicar_mascara(self.txt_tel, aplicar_mascara_telefone))
        self.txt_tel.editingFinished.connect(lambda: self.txt_tel.setText(format_telefone(self.txt_tel.text())))
        v_tel.addWidget(self.txt_tel)
        row_contato.addLayout(v_tel)

        v_email = QVBoxLayout()
        v_email.addWidget(QLabel("E-mail:"))
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("parceiro@email.com")
        self.txt_email.setMinimumHeight(32)
        v_email.addWidget(self.txt_email)
        row_contato.addLayout(v_email)
        layout.addLayout(row_contato)

        # Regra de Precificação
        card_preco = QFrame()
        card_preco.setObjectName("cardPreco")
        v_preco = QVBoxLayout(card_preco)
        v_preco.setContentsMargins(14, 12, 14, 12)
        v_preco.setSpacing(10)

        lbl_preco_h = QLabel("Modelo de Cobrança da Sublocação:")
        lbl_preco_h.setStyleSheet("color: #0f766e; font-weight: bold; font-size: 14px;")
        v_preco.addWidget(lbl_preco_h)

        row_tipo = QHBoxLayout()
        row_tipo.addWidget(QLabel("Tipo de Locação:"))
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(["Por Hora", "Por Turno", "Por Diária", "Valor Fixo Fechado"])
        self.cmb_tipo.setMinimumHeight(32)
        row_tipo.addWidget(self.cmb_tipo)
        v_preco.addLayout(row_tipo)

        self.chk_padrao = QCheckBox("Seguir tarifa padrão da clínica")
        self.chk_padrao.setChecked(True)
        self.chk_padrao.setStyleSheet("font-size: 13px; font-weight: 500; color: #334155;")
        self.chk_padrao.stateChanged.connect(self.ao_mudar_chk_padrao)
        v_preco.addWidget(self.chk_padrao)

        row_val = QHBoxLayout()
        self.lbl_val = QLabel("Valor Personalizado Acordado (R$):")
        self.spn_valor = QDoubleSpinBox()
        self.spn_valor.setRange(0, 10000)
        self.spn_valor.setDecimals(2)
        self.spn_valor.setValue(50.0)
        self.spn_valor.setMinimumHeight(32)
        self.spn_valor.setEnabled(False)
        row_val.addWidget(self.lbl_val)
        row_val.addWidget(self.spn_valor)
        v_preco.addLayout(row_val)
        layout.addWidget(card_preco)

        layout.addWidget(QLabel("Observações / Acordo:"))
        self.txt_obs = QLineEdit()
        self.txt_obs.setPlaceholderText("Ex: Utiliza toda terça-feira à tarde.")
        self.txt_obs.setMinimumHeight(32)
        layout.addWidget(self.txt_obs)

        layout.addStretch()

        # Botões
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("secondaryBtn")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_save = QPushButton("Salvar Profissional")
        btn_save.setObjectName("primaryBtn")
        btn_save.clicked.connect(self.salvar)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

        if self.is_edit:
            self.txt_nome.setText(self.partner.get("nome", ""))
            self.txt_esp.setText(self.partner.get("especialidade", ""))
            self.txt_cpf.setText(self.partner.get("cpf", ""))
            self.txt_tel.setText(self.partner.get("telefone", ""))
            self.txt_email.setText(self.partner.get("email", ""))
            self.txt_obs.setText(self.partner.get("observacoes", ""))

            tipo = self.partner.get("tipo_cobranca", "hora")
            mapa_tipo = {"hora": 0, "turno": 1, "diaria": 2, "fixo": 3}
            self.cmb_tipo.setCurrentIndex(mapa_tipo.get(tipo, 0))

            usar_padrao = bool(self.partner.get("usar_valor_padrao", 1))
            self.chk_padrao.setChecked(usar_padrao)
            self.spn_valor.setValue(float(self.partner.get("valor_acordado", 50.0)))
            self.spn_valor.setEnabled(not usar_padrao)

    def _aplicar_mascara(self, widget: QLineEdit, func_mascara):
        texto = widget.text()
        formatado = func_mascara(texto)
        if texto != formatado:
            widget.blockSignals(True)
            widget.setText(formatado)
            widget.blockSignals(False)
            widget.setCursorPosition(len(formatado))

    def ao_mudar_chk_padrao(self, state):
        self.spn_valor.setEnabled(not self.chk_padrao.isChecked())

    def salvar(self):
        nome = self.txt_nome.text().strip()
        tel = self.txt_tel.text().strip()
        if not nome:
            QMessageBox.warning(self, "Aviso", "O nome do profissional é obrigatório.")
            return

        mapa_tipo = {0: "hora", 1: "turno", 2: "diaria", 3: "fixo"}
        tipo_cobranca = mapa_tipo.get(self.cmb_tipo.currentIndex(), "hora")
        usar_padrao = self.chk_padrao.isChecked()
        valor = self.spn_valor.value() if not usar_padrao else 0.0

        if self.is_edit:
            ok, msg = update_partner(
                self.partner["id"], nome, self.txt_esp.text(), tel,
                self.txt_cpf.text(), self.txt_email.text(), tipo_cobranca,
                valor, usar_padrao, self.txt_obs.text(),
                self.current_user["id"], self.current_user["nome"]
            )
        else:
            ok, msg, pid = create_partner(
                nome, self.txt_esp.text(), tel, self.txt_cpf.text(),
                self.txt_email.text(), tipo_cobranca, valor, usar_padrao,
                self.txt_obs.text(), self.current_user["id"], self.current_user["nome"]
            )

        if ok:
            QMessageBox.information(self, "Sucesso", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", msg)


# -------------------------------------------------------------
# DIÁLOGO DE NOVA RESERVA DA SALA 2
# -------------------------------------------------------------

class NewRentalDialog(QDialog):
    """Diálogo para Agendar ou Reservar Horário na Sala 2."""
    def __init__(self, current_user: dict, data_padrao: QDate = None, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.data_padrao = data_padrao or QDate.currentDate()
        self.setWindowTitle("Nova Reserva de Sublocação")
        self.resize(500, 440)
        self.setMinimumSize(480, 400)
        self.setStyleSheet(SUBLOCACAO_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        title = QLabel("Agendar Sublocação")
        title.setStyleSheet("font-size: 17px; font-weight: bold; color: #166260;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Profissional Parceiro (*):"))
        self.cmb_parceiro = QComboBox()
        self.cmb_parceiro.setMinimumHeight(34)
        self.parceiros = list_partners(status_filtro="ativos")
        if not self.parceiros:
            self.cmb_parceiro.addItem("Nenhum parceiro cadastrado")
            self.cmb_parceiro.setEnabled(False)
        else:
            for p in self.parceiros:
                esp = f" ({p['especialidade']})" if p['especialidade'] else ""
                self.cmb_parceiro.addItem(f"{p['nome']}{esp}", p["id"])
        layout.addWidget(self.cmb_parceiro)

        layout.addWidget(QLabel("Data do Uso:"))
        self.dt_data = CustomDateEdit()
        self.dt_data.setDate(self.data_padrao)
        self.dt_data.setMinimumHeight(34)
        layout.addWidget(self.dt_data)

        row_horarios = QHBoxLayout()
        v_h1 = QVBoxLayout()
        v_h1.addWidget(QLabel("Horário Previsto Início:"))
        self.tm_inicio = QTimeEdit()
        self.tm_inicio.setDisplayFormat("HH:mm")

        # Horário local sugerido inteligente da clínica
        agora = datetime.now()
        hora_ini = agora.hour if agora.minute < 15 else agora.hour + 1
        hora_ini = max(7, min(20, hora_ini))
        hora_fim = min(22, hora_ini + 2)

        self.tm_inicio.setTime(QTime(hora_ini, 0))
        self.tm_inicio.setMinimumHeight(34)
        v_h1.addWidget(self.tm_inicio)
        row_horarios.addLayout(v_h1)

        v_h2 = QVBoxLayout()
        v_h2.addWidget(QLabel("Horário Previsto Fim:"))
        self.tm_fim = QTimeEdit()
        self.tm_fim.setDisplayFormat("HH:mm")
        self.tm_fim.setTime(QTime(hora_fim, 0))
        self.tm_fim.setMinimumHeight(34)
        v_h2.addWidget(self.tm_fim)
        row_horarios.addLayout(v_h2)
        layout.addLayout(row_horarios)

        layout.addWidget(QLabel("Observações do Agendamento:"))
        self.txt_obs = QLineEdit()
        self.txt_obs.setPlaceholderText("Ex: Paciente próprio, necessita de maca esterilizada...")
        self.txt_obs.setMinimumHeight(34)
        layout.addWidget(self.txt_obs)

        layout.addStretch()

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("secondaryBtn")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_save = QPushButton("Confirmar Reserva")
        btn_save.setObjectName("primaryBtn")
        btn_save.clicked.connect(self.salvar)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def salvar(self):
        if not self.parceiros:
            QMessageBox.warning(self, "Aviso", "Cadastre pelo menos um profissional parceiro antes de reservar.")
            return

        partner_id = self.cmb_parceiro.currentData()
        qd = self.dt_data.date()
        data_str = f"{qd.year():04d}-{qd.month():02d}-{qd.day():02d}"

        h_ini = self.tm_inicio.time().toString("HH:mm")
        h_fim = self.tm_fim.time().toString("HH:mm")

        if h_fim <= h_ini:
            QMessageBox.warning(self, "Aviso", "O horário de término deve ser após o horário de início.")
            return

        ok, msg, rid = create_rental(
            partner_id, data_str, h_ini, h_fim,
            self.txt_obs.text(), self.current_user["id"], self.current_user["nome"]
        )
        if ok:
            QMessageBox.information(self, "Sucesso", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", msg)


# -------------------------------------------------------------
# DIÁLOGO DE COBRANÇA & QR CODE PIX (A ESTRELA DA FASE 4)
# -------------------------------------------------------------

class CheckoutAndPixDialog(QDialog):
    """
    Diálogo para Conferência, Ajuste Manual de Valores e
    Cobrança com QR Code Pix + WhatsApp.
    """
    def __init__(self, rental_id: int, current_user: dict, parent=None):
        super().__init__(parent)
        self.rental_id = rental_id
        self.current_user = current_user
        self.rental = get_rental(rental_id)
        self.setWindowTitle("Cobrança de Sublocação - QR Code Pix")
        self.resize(540, 700)
        self.setMinimumSize(520, 660)
        self.setStyleSheet(SUBLOCACAO_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 1. Cabeçalho com Resumo do Atendimento
        card_resumo = QFrame()
        card_resumo.setObjectName("cardResumo")
        v_resumo = QVBoxLayout(card_resumo)
        v_resumo.setContentsMargins(14, 12, 14, 12)
        v_resumo.setSpacing(4)

        nome = self.rental.get("partner_nome", "Profissional")
        esp = self.rental.get("partner_especialidade", "")
        esp_txt = f" • {esp}" if esp else ""

        lbl_prof = QLabel(f"<b>Profissional:</b> {nome}{esp_txt}")
        lbl_prof.setStyleSheet("font-size: 14px; color: #166260;")
        v_resumo.addWidget(lbl_prof)

        d_obj = datetime.strptime(self.rental["data_locacao"], "%Y-%m-%d").date()
        data_br = d_obj.strftime("%d/%m/%Y")
        h_in = self.rental.get("horario_checkin") or self.rental.get("horario_previsto_inicio") or "--:--"
        h_out = self.rental.get("horario_checkout") or self.rental.get("horario_previsto_fim") or "--:--"
        dur_min = self.rental.get("duracao_minutos", 0)
        horas = dur_min // 60
        mins = dur_min % 60
        dur_txt = f"{horas}h{mins:02d}min ({dur_min} minutos)" if dur_min > 0 else "A calcular"

        v_resumo.addWidget(QLabel(f"<b>Data:</b> {data_br}  |  <b>Horário:</b> {h_in} às {h_out}"))
        v_resumo.addWidget(QLabel(f"<b>Tempo Efetivo de Uso:</b> <span style='color: #0f766e;'>{dur_txt}</span>"))
        layout.addWidget(card_resumo)

        # 2. Seção de Valor (Totalmente Editável Manualmente)
        card_valor = QFrame()
        card_valor.setObjectName("cardValor")
        h_val = QHBoxLayout(card_valor)
        h_val.setContentsMargins(14, 10, 14, 10)
        h_val.setSpacing(12)

        lbl_val_title = QLabel("VALOR A PAGAR:")
        lbl_val_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #0f766e;")
        h_val.addWidget(lbl_val_title)

        h_val.addWidget(QLabel("R$"))
        self.spn_valor_final = QDoubleSpinBox()
        self.spn_valor_final.setRange(0, 50000)
        self.spn_valor_final.setDecimals(2)
        self.spn_valor_final.setValue(float(self.rental.get("valor_final", 0.0)))
        self.spn_valor_final.setStyleSheet("font-size: 17px; font-weight: bold; color: #0f766e; min-height: 32px;")
        self.spn_valor_final.valueChanged.connect(self.atualizar_qrcode_pix)
        h_val.addWidget(self.spn_valor_final)

        btn_atualizar_val = QPushButton("Salvar Valor")
        btn_atualizar_val.setObjectName("primaryBtn")
        btn_atualizar_val.clicked.connect(self.salvar_valor_manual)
        h_val.addWidget(btn_atualizar_val)
        layout.addWidget(card_valor)

        # 3. Exibição do QR Code Pix
        self.lbl_qrcode = QLabel()
        self.lbl_qrcode.setAlignment(Qt.AlignCenter)
        self.lbl_qrcode.setFixedSize(210, 210)
        self.lbl_qrcode.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px;")

        h_qr_center = QHBoxLayout()
        h_qr_center.addStretch()
        h_qr_center.addWidget(self.lbl_qrcode)
        h_qr_center.addStretch()
        layout.addLayout(h_qr_center)

        # 4. Código Pix Copia e Cola com botão Copiar
        layout.addWidget(QLabel("Pix Copia e Cola (código gerado para o valor acima):"))
        h_copia = QHBoxLayout()
        self.txt_pix_code = QLineEdit()
        self.txt_pix_code.setReadOnly(True)
        self.txt_pix_code.setStyleSheet("font-size: 11px; background-color: #f1f5f9;")
        h_copia.addWidget(self.txt_pix_code)

        btn_copiar = QPushButton("📋 Copiar Código")
        btn_copiar.setObjectName("secondaryBtn")
        btn_copiar.clicked.connect(self.copiar_pix_code)
        h_copia.addWidget(btn_copiar)
        layout.addLayout(h_copia)

        layout.addSpacing(6)

        # 5. Barra Inferior de Ações
        bottom_actions = QHBoxLayout()
        bottom_actions.setSpacing(8)

        btn_zap = QPushButton("📲 Enviar Cobrança no WhatsApp")
        btn_zap.setObjectName("whatsappBtn")
        btn_zap.clicked.connect(self.enviar_cobranca_whatsapp)
        bottom_actions.addWidget(btn_zap)

        bottom_actions.addStretch()

        status_pgto = self.rental.get("status_pagamento", "Pendente")
        if status_pgto != "Pago":
            btn_pago = QPushButton("✓ Marcar como Pago")
            btn_pago.setStyleSheet("""
                background-color: #059669;
                color: #ffffff;
                font-weight: bold;
                padding: 8px 14px;
                border-radius: 6px;
                border: none;
                font-size: 13px;
            """)
            btn_pago.clicked.connect(self.confirmar_pagamento)
            bottom_actions.addWidget(btn_pago)
        else:
            lbl_ja_pago = QLabel("✓ PAGO")
            lbl_ja_pago.setStyleSheet("color: #059669; font-weight: bold; font-size: 14px;")
            bottom_actions.addWidget(lbl_ja_pago)

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setObjectName("secondaryBtn")
        btn_fechar.clicked.connect(self.accept)
        bottom_actions.addWidget(btn_fechar)
        layout.addLayout(bottom_actions)

        # Gera o QR Code inicial
        self.atualizar_qrcode_pix()

    def atualizar_qrcode_pix(self):
        valor = self.spn_valor_final.value()
        cfg = get_sublocacao_settings()
        chave = cfg["pix_chave"]
        titular = cfg["pix_titular"]
        cidade = cfg["pix_cidade"]

        self.pix_code_atual = generate_pix_copy_paste(
            chave_pix=chave,
            titular=titular,
            cidade=cidade,
            valor=valor,
            identificador=f"SALA2-{self.rental_id}"
        )
        self.txt_pix_code.setText(self.pix_code_atual)

        pixmap = generate_pix_qr_pixmap(self.pix_code_atual, box_size=6, border=2)
        pixmap_scaled = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.lbl_qrcode.setPixmap(pixmap_scaled)

    def salvar_valor_manual(self):
        novo_valor = self.spn_valor_final.value()
        ok, msg = update_rental_final_value(
            self.rental_id, novo_valor, self.rental.get("observacoes", ""),
            self.current_user["id"], self.current_user["nome"]
        )
        if ok:
            QMessageBox.information(self, "Sucesso", msg)
            self.rental["valor_final"] = novo_valor
            self.atualizar_qrcode_pix()
        else:
            QMessageBox.critical(self, "Erro", msg)

    def copiar_pix_code(self):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.pix_code_atual)
        QMessageBox.information(self, "Copiado", "Código Pix Copia e Cola copiado com sucesso!\nVocê já pode colar no banco ou enviar.")

    def enviar_cobranca_whatsapp(self):
        tel = self.rental.get("partner_telefone")
        if not tel:
            QMessageBox.warning(self, "Aviso", f"O profissional '{self.rental['partner_nome']}' não possui telefone cadastrado.")
            return

        # Garante que o valor final está salvo
        self.salvar_valor_manual()
        msg = build_sublocacao_whatsapp_message(self.rental, self.pix_code_atual)
        dialog = SendWhatsAppPreviewDialog(tel, msg, parent=self)
        dialog.exec()

    def confirmar_pagamento(self):
        nome_p = self.rental.get("partner_nome", "Profissional")
        dialog = PaymentConfirmDialog(self.spn_valor_final.value(), nome_p, parent=self)
        if dialog.exec() == QDialog.Accepted:
            forma = dialog.forma_selecionada
            ok, msg = mark_rental_as_paid(self.rental_id, forma, self.current_user["id"], self.current_user["nome"])
            if ok:
                QMessageBox.information(self, "Sucesso", msg)
                self.accept()
            else:
                QMessageBox.critical(self, "Erro", msg)


# -------------------------------------------------------------
# DIÁLOGO DE CONFIRMAÇÃO DE PAGAMENTO COM FORMA DE PAGAMENTO
# -------------------------------------------------------------

class PaymentConfirmDialog(QDialog):
    """Diálogo para confirmação de recebimento com seleção da forma de pagamento."""
    def __init__(self, valor: float, parceiro_nome: str, parent=None):
        super().__init__(parent)
        self.valor = valor
        self.parceiro_nome = parceiro_nome
        self.forma_selecionada = "Pix"
        self.setWindowTitle("Confirmar Recebimento de Pagamento")
        self.setFixedSize(440, 270)
        self.setStyleSheet(SUBLOCACAO_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        title = QLabel("Registrar Pagamento da Sublocação")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #166260;")
        layout.addWidget(title)

        val_fmt = f"{self.valor:.2f}".replace(".", ",")
        lbl_info = QLabel(
            f"Profissional: <b>{self.parceiro_nome}</b><br>"
            f"Valor da Locação: <b style='color: #059669; font-size: 16px;'>R$ {val_fmt}</b>"
        )
        lbl_info.setStyleSheet("font-size: 13px; color: #334155; line-height: 140%;")
        layout.addWidget(lbl_info)

        layout.addWidget(QLabel("Forma de Pagamento Recebida:"))
        self.cmb_forma = QComboBox()
        self.cmb_forma.addItems([
            "Pix",
            "Dinheiro",
            "Cartão de Débito",
            "Cartão de Crédito",
            "Transferência Bancária"
        ])
        self.cmb_forma.setMinimumHeight(34)
        layout.addWidget(self.cmb_forma)

        layout.addStretch()

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("secondaryBtn")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_confirm = QPushButton("✓ Confirmar Pagamento")
        btn_confirm.setStyleSheet("""
            background-color: #059669;
            color: #ffffff;
            font-weight: bold;
            padding: 8px 16px;
            border-radius: 6px;
            border: none;
            font-size: 13px;
        """)
        btn_confirm.clicked.connect(self.confirmar)
        btn_box.addWidget(btn_confirm)
        layout.addLayout(btn_box)

    def confirmar(self):
        self.forma_selecionada = self.cmb_forma.currentText()
        self.accept()


# -------------------------------------------------------------
# TELA PRINCIPAL DO MÓDULO DE SUBLOCAÇÃO DA SALA 2
# -------------------------------------------------------------

class SublocacaoView(QWidget):
    """Tela Principal de Gestão da Sublocação da Sala 2."""
    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        hoje = date.today()
        self.inicio_semana = hoje - timedelta(days=hoje.weekday())
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        self.setStyleSheet(SUBLOCACAO_STYLE)

        # Cabeçalho Superior
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Gestão de Sublocação")
        title.setStyleSheet("font-size: 19px; font-weight: bold; color: #166260;")
        sub = QLabel("Controle de parceiros, tempo de uso e cobrança (Pix/Dinheiro/Cartão).")
        sub.setStyleSheet("color: #64748b; font-size: 13px;")
        sub.setWordWrap(True)
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        btn_settings = QPushButton("⚙️ Tarifas e Chave Pix")
        btn_settings.setObjectName("secondaryBtn")
        btn_settings.clicked.connect(self.abrir_configuracoes)
        header_layout.addWidget(btn_settings)

        btn_nova_reserva = QPushButton("+ Nova Reserva")
        btn_nova_reserva.setObjectName("primaryBtn")
        btn_nova_reserva.setStyleSheet("""
            background-color: #2ca5a9;
            color: #ffffff;
            font-weight: bold;
            font-size: 14px;
            padding: 9px 18px;
            border-radius: 6px;
            border: none;
        """)
        btn_nova_reserva.clicked.connect(self.abrir_nova_reserva)
        header_layout.addWidget(btn_nova_reserva)
        layout.addLayout(header_layout)

        # Abas do Módulo
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.ao_mudar_aba)

        # ABA 1: Panorama Semanal
        self.tab_semana = QWidget()
        self.init_tab_semana()
        self.tabs.addTab(self.tab_semana, "📊 Panorama Semanal")

        # ABA 2: Reservas e Painel do Dia
        self.tab_dia = QWidget()
        self.init_tab_dia()
        self.tabs.addTab(self.tab_dia, "📆 Reservas e Uso do Dia")

        # ABA 3: Profissionais Parceiros
        self.tab_parceiros = QWidget()
        self.init_tab_parceiros()
        self.tabs.addTab(self.tab_parceiros, "👥 Profissionais Parceiros")

        # ABA 4: Histórico Financeiro
        self.tab_financeiro = QWidget()
        self.init_tab_financeiro()
        self.tabs.addTab(self.tab_financeiro, "💰 Histórico e Faturamento")

        layout.addWidget(self.tabs)

        # Carrega dados iniciais da semana
        self.carregar_agenda_semanal()

    # -------------------------------------------------------------
    # ABA 1: PANORAMA SEMANAL DA SALA 2
    # -------------------------------------------------------------

    def init_tab_semana(self):
        layout = QVBoxLayout(self.tab_semana)
        layout.setSpacing(10)

        # Barra de navegação semanal
        week_bar = QFrame()
        week_bar.setObjectName("barNav")
        week_bar_layout = QHBoxLayout(week_bar)
        week_bar_layout.setContentsMargins(10, 6, 10, 6)
        week_bar_layout.setSpacing(8)

        btn_sem_ant = QPushButton("◀ Anterior")
        btn_sem_ant.setObjectName("secondaryBtn")
        btn_sem_ant.clicked.connect(self.semana_anterior)
        week_bar_layout.addWidget(btn_sem_ant)

        self.lbl_semana_titulo = QLabel()
        self.lbl_semana_titulo.setStyleSheet("font-weight: bold; color: #166260; font-size: 14px;")
        week_bar_layout.addWidget(self.lbl_semana_titulo)

        btn_sem_prox = QPushButton("Próximo ▶")
        btn_sem_prox.setObjectName("secondaryBtn")
        btn_sem_prox.clicked.connect(self.semana_seguinte)
        week_bar_layout.addWidget(btn_sem_prox)

        btn_sem_atual = QPushButton("Semana Atual")
        btn_sem_atual.setObjectName("secondaryBtn")
        btn_sem_atual.clicked.connect(self.ir_semana_atual)
        week_bar_layout.addWidget(btn_sem_atual)

        week_bar_layout.addStretch()
        lbl_hint_sem = QLabel("💡 Dica: Use 'Ver Dia' nos cards abaixo.")
        lbl_hint_sem.setStyleSheet("color: #64748b; font-size: 11px;")
        week_bar_layout.addWidget(lbl_hint_sem)

        layout.addWidget(week_bar)

        scroll_semana = QScrollArea()
        scroll_semana.setWidgetResizable(True)
        scroll_semana.setStyleSheet("background: transparent; border: none;")

        self.cards_semana_widget = QWidget()
        self.grid_semana = QGridLayout(self.cards_semana_widget)
        self.grid_semana.setSpacing(10)
        scroll_semana.setWidget(self.cards_semana_widget)
        layout.addWidget(scroll_semana)

    def semana_anterior(self):
        self.inicio_semana -= timedelta(days=7)
        self.carregar_agenda_semanal()

    def semana_seguinte(self):
        self.inicio_semana += timedelta(days=7)
        self.carregar_agenda_semanal()

    def ir_semana_atual(self):
        hoje = date.today()
        self.inicio_semana = hoje - timedelta(days=hoje.weekday())
        self.carregar_agenda_semanal()

    def carregar_agenda_semanal(self):
        fim_semana = self.inicio_semana + timedelta(days=5)
        self.lbl_semana_titulo.setText(
            f"Semana: {self.inicio_semana.strftime('%d/%m/%Y')} a {fim_semana.strftime('%d/%m/%Y')}"
        )

        while self.grid_semana.count():
            item = self.grid_semana.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        dias_semana_nomes = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado"]

        for i in range(6):
            dia_corrente = self.inicio_semana + timedelta(days=i)
            dia_str = dia_corrente.strftime("%Y-%m-%d")
            dia_formatado = dia_corrente.strftime("%d/%m")
            nome_dia = dias_semana_nomes[i]
            eh_hoje = dia_corrente == date.today()

            card = QFrame()
            card.setObjectName(f"dayCard_{i}")
            border_color = "#2ca5a9" if eh_hoje else "#cbd5e1"
            bg_color = "#f0fdfa" if eh_hoje else "#ffffff"
            card.setStyleSheet(f"""
                QFrame#dayCard_{i} {{
                    background-color: {bg_color};
                    border: 2px solid {border_color};
                    border-radius: 8px;
                }}
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 12, 12, 12)
            card_layout.setSpacing(6)

            header_dia = QHBoxLayout()
            lbl_dia_titulo = QLabel(f"<b>{nome_dia}</b> ({dia_formatado})")
            lbl_dia_titulo.setStyleSheet("color: #166260; font-size: 13px;")
            header_dia.addWidget(lbl_dia_titulo)
            header_dia.addStretch()

            if eh_hoje:
                lbl_hoje_tag = QLabel("HOJE")
                lbl_hoje_tag.setAlignment(Qt.AlignCenter)
                lbl_hoje_tag.setStyleSheet("background-color: #2ca5a9; color: white; font-size: 10px; font-weight: bold; padding: 2px 8px; border-radius: 4px;")
                header_dia.addWidget(lbl_hoje_tag)

            card_layout.addLayout(header_dia)

            reservas_dia = list_rentals_by_date(dia_str)
            if reservas_dia:
                lbl_qtd = QLabel(f"<b>{len(reservas_dia)} locação(ões)</b> agendada(s)")
                lbl_qtd.setStyleSheet("color: #0f766e; font-size: 12px;")
                card_layout.addWidget(lbl_qtd)

                for r in reservas_dia[:4]:
                    st_s = r["status_sessao"]
                    st_p = r["status_pagamento"]
                    forma = r.get("forma_pagamento") or "Pix"
                    if st_s == "Em Uso":
                        cor = "#0284c7"
                    elif st_p == "Pago":
                        cor = "#059669"
                    elif st_s == "Finalizado":
                        cor = "#b45309"
                    else:
                        cor = "#475569"

                    h_ini = r.get("horario_previsto_inicio", "--:--")
                    h_fim = r.get("horario_previsto_fim", "--:--")
                    nome_parceiro = r["partner_nome"].split()[0]
                    esp = f" ({r['partner_especialidade']})" if r.get("partner_especialidade") else ""
                    st_label = f"Pago ({forma})" if st_p == "Pago" else st_s
                    item_txt = f"• <b>{h_ini}-{h_fim}</b>: {nome_parceiro}{esp} <span style='font-size:10px;'>({st_label})</span>"
                    lbl_item = QLabel(item_txt)
                    lbl_item.setStyleSheet(f"color: {cor}; font-size: 11px;")
                    card_layout.addWidget(lbl_item)

                if len(reservas_dia) > 4:
                    lbl_mais = QLabel(f"+ {len(reservas_dia) - 4} locação(ões)...")
                    lbl_mais.setStyleSheet("color: #64748b; font-size: 11px; font-style: italic;")
                    card_layout.addWidget(lbl_mais)
            else:
                lbl_vazio = QLabel("Sem reservas de sublocação")
                lbl_vazio.setStyleSheet("color: #94a3b8; font-size: 12px; font-style: italic;")
                card_layout.addWidget(lbl_vazio)

            card_layout.addStretch()

            btn_ver_dia = QPushButton("Ver Dia ▶")
            btn_ver_dia.setObjectName("secondaryBtn")
            btn_ver_dia.clicked.connect(lambda checked=False, d=dia_corrente: self.navegar_para_dia(d))
            card_layout.addWidget(btn_ver_dia)

            col = i % 3
            row = i // 3
            self.grid_semana.addWidget(card, row, col)

    def navegar_para_dia(self, dia: date):
        self.dt_filtro.setDate(QDate(dia.year, dia.month, dia.day))
        self.tabs.setCurrentIndex(1)

    # -------------------------------------------------------------
    # ABA 2: RESERVAS & USO DO DIA
    # -------------------------------------------------------------

    def init_tab_dia(self):
        layout = QVBoxLayout(self.tab_dia)
        layout.setSpacing(10)

        # Barra de Navegação de Data
        date_bar = QFrame()
        date_bar.setObjectName("barNav")
        date_layout = QHBoxLayout(date_bar)
        date_layout.setContentsMargins(8, 6, 8, 6)
        date_layout.setSpacing(6)

        btn_ant = QPushButton("◀ Anterior")
        btn_ant.setObjectName("secondaryBtn")
        btn_ant.setStyleSheet("padding: 5px 10px; font-size: 12px;")
        btn_ant.clicked.connect(self.dia_anterior)
        date_layout.addWidget(btn_ant)

        self.dt_filtro = CustomDateEdit()
        self.dt_filtro.setFixedWidth(150)
        self.dt_filtro.setDate(QDate.currentDate())
        self.dt_filtro.dateChanged.connect(self.carregar_reservas_do_dia)
        date_layout.addWidget(self.dt_filtro)

        btn_prox = QPushButton("Próximo ▶")
        btn_prox.setObjectName("secondaryBtn")
        btn_prox.setStyleSheet("padding: 5px 10px; font-size: 12px;")
        btn_prox.clicked.connect(self.dia_seguinte)
        date_layout.addWidget(btn_prox)

        btn_hoje = QPushButton("Hoje")
        btn_hoje.setObjectName("secondaryBtn")
        btn_hoje.setStyleSheet("padding: 5px 10px; font-size: 12px;")
        btn_hoje.clicked.connect(lambda: self.dt_filtro.setDate(QDate.currentDate()))
        date_layout.addWidget(btn_hoje)

        date_layout.addStretch()

        self.lbl_resumo_dia = QLabel("Total: 0  |  ✓ R$ 0,00  |  ⏳ Pendentes: 0")
        self.lbl_resumo_dia.setStyleSheet("""
            background-color: #f0fdfa;
            color: #0f766e;
            font-weight: bold;
            font-size: 12px;
            padding: 4px 8px;
            border: 1px solid #ccfbf1;
            border-radius: 6px;
        """)
        date_layout.addWidget(self.lbl_resumo_dia)
        layout.addWidget(date_bar)

        # Tabela de Reservas da Sala 2
        self.table_dia = QTableWidget()
        self.table_dia.setColumnCount(8)
        self.table_dia.setHorizontalHeaderLabels([
            "ID", "Horário Previsto", "Profissional", "Check-in", "Check-out", "Tempo Total", "Valor Final", "Status"
        ])
        self.table_dia.setColumnHidden(0, True)  # Oculta ID
        self.table_dia.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_dia.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_dia.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_dia.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_dia.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table_dia.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table_dia.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.table_dia.setAlternatingRowColors(True)
        self.table_dia.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_dia.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_dia.doubleClicked.connect(self.abrir_cobranca_pix_selecionada)
        self.table_dia.setStyleSheet("""
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
                padding: 6px;
            }
        """)
        layout.addWidget(self.table_dia)

        # Botões Inferiores
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(6)

        btn_checkin = QPushButton("▶ Iniciar (Check-in)")
        btn_checkin.setObjectName("secondaryBtn")
        btn_checkin.clicked.connect(self.fazer_checkin_selecionado)
        bottom_bar.addWidget(btn_checkin)

        btn_checkout = QPushButton("⏹ Encerrar (Check-out)")
        btn_checkout.setObjectName("secondaryBtn")
        btn_checkout.clicked.connect(self.fazer_checkout_selecionado)
        bottom_bar.addWidget(btn_checkout)

        btn_pix = QPushButton("📲 Cobrança Pix e WhatsApp")
        btn_pix.setObjectName("whatsappBtn")
        btn_pix.clicked.connect(self.abrir_cobranca_pix_selecionada)
        bottom_bar.addWidget(btn_pix)

        btn_pago = QPushButton("✓ Marcar como Pago")
        btn_pago.setObjectName("secondaryBtn")
        btn_pago.clicked.connect(self.marcar_pago_selecionado)
        bottom_bar.addWidget(btn_pago)

        bottom_bar.addStretch()

        btn_excluir = QPushButton("Excluir / Cancelar")
        btn_excluir.setObjectName("dangerBtn")
        btn_excluir.clicked.connect(self.excluir_reserva_selecionada)
        bottom_bar.addWidget(btn_excluir)
        layout.addLayout(bottom_bar)

    def dia_anterior(self):
        self.dt_filtro.setDate(self.dt_filtro.date().addDays(-1))

    def dia_seguinte(self):
        self.dt_filtro.setDate(self.dt_filtro.date().addDays(1))

    def get_data_selecionada_str(self) -> str:
        qd = self.dt_filtro.date()
        return f"{qd.year():04d}-{qd.month():02d}-{qd.day():02d}"

    def carregar_reservas_do_dia(self):
        data_str = self.get_data_selecionada_str()
        reservas = list_rentals_by_date(data_str)
        self.table_dia.setRowCount(len(reservas))

        total_faturado = 0.0
        pendentes = 0

        for row_idx, r in enumerate(reservas):
            # Coluna 0: ID
            item_id = QTableWidgetItem(str(r["id"]))
            self.table_dia.setItem(row_idx, 0, item_id)

            # Coluna 1: Horário Previsto
            h_prev = f"{r['horario_previsto_inicio']} às {r['horario_previsto_fim']}"
            item_h = QTableWidgetItem(h_prev)
            item_h.setTextAlignment(Qt.AlignCenter)
            self.table_dia.setItem(row_idx, 1, item_h)

            # Coluna 2: Profissional
            esp = f" ({r['partner_especialidade']})" if r['partner_especialidade'] else ""
            item_nome = QTableWidgetItem(f"{r['partner_nome']}{esp}")
            item_nome.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table_dia.setItem(row_idx, 2, item_nome)

            # Coluna 3: Check-in
            item_in = QTableWidgetItem(r["horario_checkin"] or "-")
            item_in.setTextAlignment(Qt.AlignCenter)
            self.table_dia.setItem(row_idx, 3, item_in)

            # Coluna 4: Check-out
            item_out = QTableWidgetItem(r["horario_checkout"] or "-")
            item_out.setTextAlignment(Qt.AlignCenter)
            self.table_dia.setItem(row_idx, 4, item_out)

            # Coluna 5: Tempo Total
            dur = r.get("duracao_minutos", 0)
            if dur > 0:
                h = dur // 60
                m = dur % 60
                dur_txt = f"{h}h{m:02d}min" if h > 0 else f"{m}min"
            else:
                dur_txt = "-"
            item_dur = QTableWidgetItem(dur_txt)
            item_dur.setTextAlignment(Qt.AlignCenter)
            self.table_dia.setItem(row_idx, 5, item_dur)

            # Coluna 6: Valor Final
            val = float(r.get("valor_final", 0.0))
            val_fmt = f"{val:.2f}".replace('.', ',')
            item_val = QTableWidgetItem(f"R$ {val_fmt}")
            item_val.setTextAlignment(Qt.AlignCenter)
            item_val.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table_dia.setItem(row_idx, 6, item_val)

            # Coluna 7: Status com forma de pagamento
            status_s = r["status_sessao"]
            status_p = r["status_pagamento"]
            forma = r.get("forma_pagamento") or "Pix"
            if status_p == "Pago":
                status_txt = f"{status_s} • Pago ({forma})"
            else:
                status_txt = f"{status_s} • {status_p}"

            item_status = QTableWidgetItem(status_txt)
            item_status.setTextAlignment(Qt.AlignCenter)
            item_status.setFont(QFont("Segoe UI", 9, QFont.Bold))

            if status_s == "Em Uso":
                item_status.setForeground(QColor("#0284c7"))  # Azul em uso
            elif status_p == "Pago":
                item_status.setForeground(QColor("#059669"))  # Verde pago
                total_faturado += val
            elif status_s == "Finalizado":
                item_status.setForeground(QColor("#b45309"))  # Laranja pendente pgto
                pendentes += 1
            else:
                item_status.setForeground(QColor("#64748b"))

            self.table_dia.setItem(row_idx, 7, item_status)
            self.table_dia.item(row_idx, 0).setData(Qt.UserRole, r)

        val_tot_fmt = f"{total_faturado:.2f}".replace('.', ',')
        self.lbl_resumo_dia.setText(
            f"Total: {len(reservas)}  |  "
            f"✓ R$ {val_tot_fmt}  |  "
            f"⏳ Pendentes: {pendentes}"
        )

    def get_selected_rental(self) -> Optional[dict]:
        selected = self.table_dia.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione uma reserva na tabela.")
            return None
        row = selected[0].row()
        return self.table_dia.item(row, 0).data(Qt.UserRole)

    def fazer_checkin_selecionado(self):
        r = self.get_selected_rental()
        if not r:
            return
        agora = datetime.now().strftime("%H:%M")
        ok, msg = checkin_rental(r["id"], agora, self.current_user["id"], self.current_user["nome"])
        if ok:
            QMessageBox.information(self, "Sucesso", msg)
            self.carregar_reservas_do_dia()
            self.carregar_agenda_semanal()
        else:
            QMessageBox.critical(self, "Erro", msg)

    def fazer_checkout_selecionado(self):
        r = self.get_selected_rental()
        if not r:
            return
        agora = datetime.now().strftime("%H:%M")
        ok, msg, val_calc = checkout_rental(r["id"], agora, self.current_user["id"], self.current_user["nome"])
        if ok:
            QMessageBox.information(self, "Check-out Realizado", msg)
            self.carregar_reservas_do_dia()
            self.carregar_agenda_semanal()
            # Abre imediatamente o diálogo do Pix com o valor calculado
            dialog = CheckoutAndPixDialog(r["id"], self.current_user, parent=self)
            dialog.exec()
            self.carregar_reservas_do_dia()
            self.carregar_agenda_semanal()
        else:
            QMessageBox.critical(self, "Erro", msg)

    def abrir_cobranca_pix_selecionada(self):
        r = self.get_selected_rental()
        if not r:
            return
        dialog = CheckoutAndPixDialog(r["id"], self.current_user, parent=self)
        dialog.exec()
        self.carregar_reservas_do_dia()
        self.carregar_agenda_semanal()

    def marcar_pago_selecionado(self):
        r = self.get_selected_rental()
        if not r:
            return
        dialog = PaymentConfirmDialog(r["valor_final"], r["partner_nome"], parent=self)
        if dialog.exec() == QDialog.Accepted:
            forma = dialog.forma_selecionada
            ok, msg = mark_rental_as_paid(r["id"], forma, self.current_user["id"], self.current_user["nome"])
            if ok:
                QMessageBox.information(self, "Sucesso", msg)
                self.carregar_reservas_do_dia()
                self.carregar_agenda_semanal()
            else:
                QMessageBox.critical(self, "Erro", msg)

    def excluir_reserva_selecionada(self):
        r = self.get_selected_rental()
        if not r:
            return
        if perguntar_sim_nao(self, "Excluir Reserva", f"Deseja realmente excluir a reserva de '{r['partner_nome']}'?"):
            ok, msg = delete_rental(r["id"], self.current_user["id"], self.current_user["nome"])
            if ok:
                self.carregar_reservas_do_dia()
                self.carregar_agenda_semanal()
            else:
                QMessageBox.critical(self, "Erro", msg)

    # -------------------------------------------------------------
    # ABA 3: PROFISSIONAIS PARCEIROS
    # -------------------------------------------------------------

    def init_tab_parceiros(self):
        layout = QVBoxLayout(self.tab_parceiros)
        layout.setSpacing(10)

        top_bar = QHBoxLayout()
        lbl_info = QLabel("Profissionais parceiros cadastrados para sublocação do consultório:")
        lbl_info.setStyleSheet("color: #475569; font-size: 13px;")
        top_bar.addWidget(lbl_info)
        top_bar.addStretch()

        btn_novo_p = QPushButton("+ Cadastrar Profissional")
        btn_novo_p.setObjectName("primaryBtn")
        btn_novo_p.clicked.connect(self.abrir_novo_parceiro)
        top_bar.addWidget(btn_novo_p)
        layout.addLayout(top_bar)

        self.table_parceiros = QTableWidget()
        self.table_parceiros.setColumnCount(6)
        self.table_parceiros.setHorizontalHeaderLabels([
            "ID", "Nome do Profissional", "Especialidade", "Telefone / WhatsApp", "Modelo de Cobrança", "Status"
        ])
        self.table_parceiros.setColumnHidden(0, True)
        self.table_parceiros.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_parceiros.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_parceiros.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_parceiros.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_parceiros.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table_parceiros.setAlternatingRowColors(True)
        self.table_parceiros.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_parceiros.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_parceiros.doubleClicked.connect(self.editar_parceiro_selecionado)
        self.table_parceiros.setStyleSheet("""
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
                padding: 8px;
            }
        """)
        layout.addWidget(self.table_parceiros)

        bot_bar = QHBoxLayout()
        btn_edit = QPushButton("✏️ Editar Cadastro")
        btn_edit.setObjectName("primaryBtn")
        btn_edit.clicked.connect(self.editar_parceiro_selecionado)
        bot_bar.addWidget(btn_edit)

        btn_zap = QPushButton("📲 Chamar no WhatsApp")
        btn_zap.setObjectName("whatsappBtn")
        btn_zap.clicked.connect(self.chamar_parceiro_whatsapp)
        bot_bar.addWidget(btn_zap)

        bot_bar.addStretch()

        btn_inativar = QPushButton("Inativar / Ativar")
        btn_inativar.setObjectName("dangerBtn")
        btn_inativar.clicked.connect(self.alternar_status_parceiro)
        bot_bar.addWidget(btn_inativar)
        layout.addLayout(bot_bar)

    def carregar_parceiros(self):
        parceiros = list_partners(status_filtro="todos")
        self.table_parceiros.setRowCount(len(parceiros))

        cfg = get_sublocacao_settings()

        for row_idx, p in enumerate(parceiros):
            item_id = QTableWidgetItem(str(p["id"]))
            self.table_parceiros.setItem(row_idx, 0, item_id)

            item_nome = QTableWidgetItem(p["nome"])
            item_nome.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table_parceiros.setItem(row_idx, 1, item_nome)

            item_esp = QTableWidgetItem(p["especialidade"] or "-")
            self.table_parceiros.setItem(row_idx, 2, item_esp)

            item_tel = QTableWidgetItem(p["telefone"] or "-")
            item_tel.setTextAlignment(Qt.AlignCenter)
            self.table_parceiros.setItem(row_idx, 3, item_tel)

            # Modelo de cobrança
            tipo = p.get("tipo_cobranca", "hora")
            if p.get("usar_valor_padrao", 1):
                preco_txt = f"Padrão (R$ {cfg['tarifa_hora']:.2f}/h)"
            else:
                val = float(p.get("valor_acordado", 0.0))
                preco_txt = f"R$ {val:.2f} ({tipo})"

            item_preco = QTableWidgetItem(preco_txt)
            item_preco.setTextAlignment(Qt.AlignCenter)
            item_preco.setForeground(QColor("#0f766e"))
            self.table_parceiros.setItem(row_idx, 4, item_preco)

            status_txt = "Ativo" if p.get("ativo", 1) else "Inativo"
            item_st = QTableWidgetItem(status_txt)
            item_st.setTextAlignment(Qt.AlignCenter)
            item_st.setFont(QFont("Segoe UI", 9, QFont.Bold))
            if p.get("ativo", 1):
                item_st.setForeground(QColor("#059669"))
            else:
                item_st.setForeground(QColor("#94a3b8"))
            self.table_parceiros.setItem(row_idx, 5, item_st)

            self.table_parceiros.item(row_idx, 0).setData(Qt.UserRole, p)

    def get_selected_partner(self) -> Optional[dict]:
        selected = self.table_parceiros.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione um profissional parceiro na tabela.")
            return None
        row = selected[0].row()
        return self.table_parceiros.item(row, 0).data(Qt.UserRole)

    def abrir_novo_parceiro(self):
        dialog = PartnerFormDialog(self.current_user, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.carregar_parceiros()

    def editar_parceiro_selecionado(self):
        p = self.get_selected_partner()
        if not p:
            return
        dialog = PartnerFormDialog(self.current_user, partner=p, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.carregar_parceiros()

    def alternar_status_parceiro(self):
        p = self.get_selected_partner()
        if not p:
            return
        ativo = p.get("ativo", 1)
        if ativo:
            if perguntar_sim_nao(self, "Inativar Parceiro", f"Deseja inativar o parceiro '{p['nome']}'?"):
                delete_partner(p["id"], self.current_user["id"], self.current_user["nome"])
                self.carregar_parceiros()
        else:
            restore_partner(p["id"], self.current_user["id"], self.current_user["nome"])
            self.carregar_parceiros()

    def chamar_parceiro_whatsapp(self):
        p = self.get_selected_partner()
        if not p:
            return
        tel = p.get("telefone")
        if not tel:
            QMessageBox.warning(self, "Aviso", f"O profissional '{p['nome']}' não possui telefone cadastrado.")
            return
        msg = build_partner_whatsapp_message(p["nome"])
        dialog = SendWhatsAppPreviewDialog(tel, msg, parent=self)
        dialog.exec()

    # -------------------------------------------------------------
    # ABA 4: HISTÓRICO FINANCEIRO & FATURAMENTO
    # -------------------------------------------------------------

    def init_tab_financeiro(self):
        layout = QVBoxLayout(self.tab_financeiro)
        layout.setSpacing(10)

        card_metricas = QFrame()
        card_metricas.setStyleSheet("background-color: #f0fdfa; border: 1px solid #ccfbf1; border-radius: 8px; padding: 12px;")
        h_met = QHBoxLayout(card_metricas)

        self.lbl_fat_total = QLabel("Total Recebido: R$ 0,00")
        self.lbl_fat_total.setStyleSheet("font-size: 14px; font-weight: bold; color: #059669;")
        h_met.addWidget(self.lbl_fat_total)
        h_met.addStretch()

        self.lbl_fat_pendente = QLabel("Total a Receber: R$ 0,00")
        self.lbl_fat_pendente.setStyleSheet("font-size: 14px; font-weight: bold; color: #b45309;")
        h_met.addWidget(self.lbl_fat_pendente)
        h_met.addStretch()

        self.lbl_total_horas = QLabel("Horas Totais Sublocadas: 0h")
        self.lbl_total_horas.setStyleSheet("font-size: 14px; font-weight: bold; color: #0f766e;")
        h_met.addWidget(self.lbl_total_horas)
        layout.addWidget(card_metricas)

        self.table_historico = QTableWidget()
        self.table_historico.setColumnCount(7)
        self.table_historico.setHorizontalHeaderLabels([
            "ID", "Data", "Profissional", "Horários", "Duração", "Valor Final", "Pagamento"
        ])
        self.table_historico.setColumnHidden(0, True)
        self.table_historico.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_historico.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_historico.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_historico.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_historico.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table_historico.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table_historico.setAlternatingRowColors(True)
        self.table_historico.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_historico.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_historico.doubleClicked.connect(self.abrir_pix_do_historico)
        self.table_historico.setStyleSheet("""
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
                padding: 6px;
            }
        """)
        layout.addWidget(self.table_historico)

        bot_hist = QHBoxLayout()
        btn_ver_pix = QPushButton("👁️ Ver Cobrança Pix / Comprovante")
        btn_ver_pix.setObjectName("primaryBtn")
        btn_ver_pix.clicked.connect(self.abrir_pix_do_historico)
        bot_hist.addWidget(btn_ver_pix)

        bot_hist.addStretch()

        btn_atualizar_h = QPushButton("🔄 Atualizar Relatório")
        btn_atualizar_h.setObjectName("secondaryBtn")
        btn_atualizar_h.clicked.connect(self.carregar_historico_financeiro)
        bot_hist.addWidget(btn_atualizar_h)
        layout.addLayout(bot_hist)

    def carregar_historico_financeiro(self):
        todas = list_all_rentals(limit=300)
        self.table_historico.setRowCount(len(todas))

        total_rec = 0.0
        total_pen = 0.0
        total_min = 0

        for row_idx, r in enumerate(todas):
            self.table_historico.setItem(row_idx, 0, QTableWidgetItem(str(r["id"])))

            d_obj = datetime.strptime(r["data_locacao"], "%Y-%m-%d").date()
            data_br = d_obj.strftime("%d/%m/%Y")
            item_d = QTableWidgetItem(data_br)
            item_d.setTextAlignment(Qt.AlignCenter)
            self.table_historico.setItem(row_idx, 1, item_d)

            item_nome = QTableWidgetItem(r["partner_nome"])
            item_nome.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table_historico.setItem(row_idx, 2, item_nome)

            h_in = r.get("horario_checkin") or r.get("horario_previsto_inicio")
            h_out = r.get("horario_checkout") or r.get("horario_previsto_fim")
            item_h = QTableWidgetItem(f"{h_in} às {h_out}")
            item_h.setTextAlignment(Qt.AlignCenter)
            self.table_historico.setItem(row_idx, 3, item_h)

            dur = r.get("duracao_minutos", 0)
            total_min += dur
            h = dur // 60
            m = dur % 60
            dur_txt = f"{h}h{m:02d}min" if dur > 0 else "-"
            item_dur = QTableWidgetItem(dur_txt)
            item_dur.setTextAlignment(Qt.AlignCenter)
            self.table_historico.setItem(row_idx, 4, item_dur)

            val = float(r.get("valor_final", 0.0))
            val_fmt = f"{val:.2f}".replace('.', ',')
            item_val = QTableWidgetItem(f"R$ {val_fmt}")
            item_val.setTextAlignment(Qt.AlignCenter)
            item_val.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table_historico.setItem(row_idx, 5, item_val)

            st_pgto = r.get("status_pagamento", "Pendente")
            forma = r.get("forma_pagamento") or "Pix"
            if st_pgto == "Pago":
                txt_pg = f"Pago ({forma})"
                item_pg = QTableWidgetItem(txt_pg)
                item_pg.setForeground(QColor("#059669"))
                total_rec += val
            else:
                txt_pg = "Pendente"
                item_pg = QTableWidgetItem(txt_pg)
                item_pg.setForeground(QColor("#b45309"))
                total_pen += val

            item_pg.setTextAlignment(Qt.AlignCenter)
            item_pg.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table_historico.setItem(row_idx, 6, item_pg)

            self.table_historico.item(row_idx, 0).setData(Qt.UserRole, r)

        t_h = total_min // 60
        t_m = total_min % 60
        rec_fmt = f"{total_rec:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        pen_fmt = f"{total_pen:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        self.lbl_fat_total.setText(f"Total Recebido: R$ {rec_fmt}")
        self.lbl_fat_pendente.setText(f"Total a Receber: R$ {pen_fmt}")
        self.lbl_total_horas.setText(f"Horas Sublocadas: {t_h}h{t_m:02d}min")

    def abrir_pix_do_historico(self):
        selected = self.table_historico.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione uma locação na tabela.")
            return
        row = selected[0].row()
        r = self.table_historico.item(row, 0).data(Qt.UserRole)
        dialog = CheckoutAndPixDialog(r["id"], self.current_user, parent=self)
        dialog.exec()
        self.carregar_historico_financeiro()
        self.carregar_agenda_semanal()
        self.carregar_reservas_do_dia()

    # -------------------------------------------------------------
    # EVENTOS GERAIS
    # -------------------------------------------------------------

    def ao_mudar_aba(self, indice: int):
        if indice == 0:
            self.carregar_agenda_semanal()
        elif indice == 1:
            self.carregar_reservas_do_dia()
        elif indice == 2:
            self.carregar_parceiros()
        elif indice == 3:
            self.carregar_historico_financeiro()

    def abrir_configuracoes(self):
        dialog = SublocacaoSettingsDialog(self.current_user, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.carregar_agenda_semanal()
            self.carregar_reservas_do_dia()

    def abrir_nova_reserva(self):
        data_padrao = self.dt_filtro.date() if hasattr(self, "dt_filtro") else QDate.currentDate()
        dialog = NewRentalDialog(self.current_user, data_padrao=data_padrao, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.carregar_agenda_semanal()
            self.carregar_reservas_do_dia()
