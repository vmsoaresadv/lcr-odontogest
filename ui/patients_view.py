import os
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialog, QTabWidget, QTextEdit, QComboBox,
    QFileDialog, QFrame, QSplitter, QDateEdit, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont, QIcon, QColor

from services.patient_service import (
    search_patients, get_patient, create_patient,
    update_patient, delete_patient, restore_patient,
    delete_patient_permanently, add_record, update_record, get_record,
    list_records, delete_record, add_attachment,
    list_attachments, open_attachment, delete_attachment,
    format_cpf, format_telefone, format_data_br
)
from ui.custom_date_edit import CustomDateEdit

def aplicar_mascara_cpf(texto: str) -> str:
    """Aplica máscara progressiva de CPF: 000.000.000-00."""
    nums = "".join(c for c in texto if c.isdigit())[:11]
    if len(nums) <= 3:
        return nums
    elif len(nums) <= 6:
        return f"{nums[:3]}.{nums[3:]}"
    elif len(nums) <= 9:
        return f"{nums[:3]}.{nums[3:6]}.{nums[6:]}"
    else:
        return f"{nums[:3]}.{nums[3:6]}.{nums[6:9]}-{nums[9:]}"

def aplicar_mascara_telefone(texto: str) -> str:
    """Aplica máscara progressiva de telefone: (00) 00000-0000."""
    nums = "".join(c for c in texto if c.isdigit())[:11]
    if not nums:
        return ""
    if len(nums) <= 2:
        return f"({nums}"
    elif len(nums) <= 6:
        return f"({nums[:2]}) {nums[2:]}"
    elif len(nums) <= 10:
        return f"({nums[:2]}) {nums[2:6]}-{nums[6:]}"
    else:
        return f"({nums[:2]}) {nums[2:7]}-{nums[7:]}"

def aplicar_mascara_data(texto: str) -> str:
    """Aplica máscara progressiva de data: DD/MM/AAAA."""
    nums = "".join(c for c in texto if c.isdigit())[:8]
    if not nums:
        return ""
    if len(nums) <= 2:
        return nums
    elif len(nums) <= 4:
        return f"{nums[:2]}/{nums[2:]}"
    else:
        return f"{nums[:2]}/{nums[2:4]}/{nums[4:]}"

def format_datetime_br(val: str) -> str:
    """Formata datas/horas do banco para exibição elegante no padrão brasileiro (DD/MM/AAAA HH:MM)."""
    if not val:
        return "-"
    val_str = str(val).strip()
    try:
        val_clean = val_str.replace("T", " ")
        if len(val_clean) >= 19:
            dt = datetime.strptime(val_clean[:19], "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d/%m/%Y %H:%M")
        elif len(val_clean) == 16:
            dt = datetime.strptime(val_clean[:16], "%Y-%m-%d %H:%M")
            return dt.strftime("%d/%m/%Y %H:%M")
        elif len(val_clean) == 10:
            dt = datetime.strptime(val_clean, "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
    except Exception:
        pass
    return val_str

def perguntar_sim_nao(parent, titulo: str, mensagem: str, eh_aviso: bool = False) -> bool:
    """Exibe caixa de confirmação com botões 'Sim' e 'Não' em português."""
    box = QMessageBox(parent)
    box.setWindowTitle(titulo)
    box.setText(mensagem)
    box.setIcon(QMessageBox.Warning if eh_aviso else QMessageBox.Question)
    btn_sim = box.addButton("Sim", QMessageBox.YesRole)
    btn_nao = box.addButton("Não", QMessageBox.NoRole)
    btn_sim.setStyleSheet("""
        background-color: #2ca5a9;
        color: white;
        font-weight: bold;
        padding: 6px 18px;
        border-radius: 4px;
        min-width: 60px;
    """)
    btn_nao.setStyleSheet("""
        background-color: #e2e8f0;
        color: #334155;
        font-weight: bold;
        padding: 6px 18px;
        border-radius: 4px;
        min-width: 60px;
    """)
    box.setDefaultButton(btn_nao)
    box.exec()
    return box.clickedButton() == btn_sim

# Estilo compartilhado com a paleta da LCR Odontologia
PATIENT_STYLE = """
QDialog {
    background-color: #f8fafc;
    font-family: 'Segoe UI', sans-serif;
}
QLabel {
    color: #1e293b;
    font-size: 13px;
    font-weight: 600;
}
QLineEdit, QTextEdit, QComboBox {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 7px 12px;
    font-size: 13px;
    selection-background-color: #2ca5a9;
    selection-color: #ffffff;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 2px solid #2ca5a9;
    background-color: #ffffff;
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
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #0f172a;
    selection-background-color: #2ca5a9;
    selection-color: #ffffff;
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
    padding: 10px 18px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
}
QTabBar::tab:selected {
    background-color: #2ca5a9;
    color: #ffffff;
}
QPushButton#primaryBtn {
    background-color: #2ca5a9;
    color: #ffffff;
    font-weight: bold;
    padding: 8px 16px;
    border-radius: 6px;
    border: none;
    font-size: 13px;
}
QPushButton#primaryBtn:hover {
    background-color: #248a8d;
}
QPushButton#secondaryBtn {
    background-color: #e2e8f0;
    color: #334155;
    font-weight: 600;
    padding: 8px 14px;
    border-radius: 6px;
    border: none;
    font-size: 13px;
}
QPushButton#secondaryBtn:hover {
    background-color: #cbd5e1;
}
QPushButton#dangerBtn {
    background-color: #fee2e2;
    color: #b91c1c;
    font-weight: 600;
    padding: 8px 14px;
    border-radius: 6px;
    border: 1px solid #fca5a5;
    font-size: 13px;
}
QPushButton#dangerBtn:hover {
    background-color: #fecaca;
}
"""


class PatientFormDialog(QDialog):
    """Diálogo para Cadastrar ou Editar Dados Básicos do Paciente."""
    def __init__(self, current_user: dict, patient: dict = None, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.patient = patient
        self.is_edit = patient is not None
        self.setWindowTitle("Editar Paciente" if self.is_edit else "Novo Paciente")
        self.setFixedSize(560, 690)
        self.setStyleSheet(PATIENT_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        title = QLabel("Editar Ficha do Paciente" if self.is_edit else "Cadastro de Novo Paciente")
        title.setStyleSheet("font-size: 17px; font-weight: bold; color: #166260;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Nome Completo (*):"))
        self.txt_nome = QLineEdit()
        self.txt_nome.setPlaceholderText("Ex: João da Silva")
        layout.addWidget(self.txt_nome)

        row_cpf_nasc = QHBoxLayout()
        v_cpf = QVBoxLayout()
        v_cpf.addWidget(QLabel("CPF:"))
        self.txt_cpf = QLineEdit()
        self.txt_cpf.setPlaceholderText("000.000.000-00")
        self.txt_cpf.textEdited.connect(lambda t: self._aplicar_mascara_campo(self.txt_cpf, aplicar_mascara_cpf))
        self.txt_cpf.editingFinished.connect(lambda: self._finalizar_formatacao_campo(self.txt_cpf, format_cpf))
        v_cpf.addWidget(self.txt_cpf)
        row_cpf_nasc.addLayout(v_cpf)

        v_nasc = QVBoxLayout()
        v_nasc.addWidget(QLabel("Data de Nascimento:"))
        self.txt_nascimento = QLineEdit()
        self.txt_nascimento.setPlaceholderText("DD/MM/AAAA")
        self.txt_nascimento.textEdited.connect(lambda t: self._aplicar_mascara_campo(self.txt_nascimento, aplicar_mascara_data))
        self.txt_nascimento.editingFinished.connect(lambda: self._finalizar_formatacao_campo(self.txt_nascimento, format_data_br))
        v_nasc.addWidget(self.txt_nascimento)
        row_cpf_nasc.addLayout(v_nasc)
        layout.addLayout(row_cpf_nasc)

        row_contato = QHBoxLayout()
        v_tel = QVBoxLayout()
        v_tel.addWidget(QLabel("Telefone / WhatsApp:"))
        self.txt_telefone = QLineEdit()
        self.txt_telefone.setPlaceholderText("(74) 99999-9999")
        self.txt_telefone.textEdited.connect(lambda t: self._aplicar_mascara_campo(self.txt_telefone, aplicar_mascara_telefone))
        self.txt_telefone.editingFinished.connect(lambda: self._finalizar_formatacao_campo(self.txt_telefone, format_telefone))
        v_tel.addWidget(self.txt_telefone)
        row_contato.addLayout(v_tel)

        v_email = QVBoxLayout()
        v_email.addWidget(QLabel("E-mail:"))
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("paciente@email.com")
        v_email.addWidget(self.txt_email)
        row_contato.addLayout(v_email)
        layout.addLayout(row_contato)

        layout.addWidget(QLabel("Endereço Completo:"))
        self.txt_endereco = QLineEdit()
        self.txt_endereco.setPlaceholderText("Rua, Número, Bairro, Cidade")
        layout.addWidget(self.txt_endereco)

        # Campo de Alergias com destaque
        lbl_alergia = QLabel("⚠️ Alergias e Restrições (Medicamentos / Látex):")
        lbl_alergia.setStyleSheet("color: #b91c1c; font-weight: bold;")
        layout.addWidget(lbl_alergia)
        self.txt_alergias = QLineEdit()
        self.txt_alergias.setStyleSheet("border-color: #fca5a5; background-color: #fffaf0;")
        self.txt_alergias.setPlaceholderText("Ex: Alérgico a Dipirona, Penicilina, Látex (ou Nenhuma)")
        layout.addWidget(self.txt_alergias)

        layout.addWidget(QLabel("Histórico Médico / Observações Importantes:"))
        self.txt_obs = QTextEdit()
        self.txt_obs.setMaximumHeight(65)
        self.txt_obs.setPlaceholderText("Hipertensão, diabetes, uso de anticoagulantes, gestação...")
        layout.addWidget(self.txt_obs)

        # Card Interativo para Última Consulta Anterior (Ficha Física de Papel)
        card_hist = QFrame()
        card_hist.setStyleSheet("background-color: #f0fdfa; border: 1px solid #ccfbf1; border-radius: 8px; padding: 8px;")
        v_hist = QVBoxLayout(card_hist)
        v_hist.setContentsMargins(10, 8, 10, 8)
        v_hist.setSpacing(6)

        lbl_hist_title = QLabel("📅 Histórico de Atendimento Anterior (Ficha Física de Papel)")
        lbl_hist_title.setStyleSheet("color: #0f766e; font-weight: bold; font-size: 13px;")
        v_hist.addWidget(lbl_hist_title)

        row_picker = QHBoxLayout()
        self.chk_historico = QCheckBox("Paciente já possui consulta antiga registrada no papel")
        self.chk_historico.setStyleSheet("color: #334155; font-size: 12px; font-weight: 500;")
        self.chk_historico.stateChanged.connect(self.alternar_historico_ativo)
        row_picker.addWidget(self.chk_historico)

        self.dt_data_manual = CustomDateEdit()
        self.dt_data_manual.setDate(QDate.currentDate().addDays(-180))  # Sugere 6 meses atrás por padrão
        self.dt_data_manual.setEnabled(False)
        self.dt_data_manual.setFixedWidth(135)
        row_picker.addWidget(self.dt_data_manual)
        v_hist.addLayout(row_picker)

        layout.addWidget(card_hist)
        layout.addSpacing(6)

        # Botões
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("secondaryBtn")
        btn_cancelar.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancelar)

        btn_salvar = QPushButton("Salvar Paciente")
        btn_salvar.setObjectName("primaryBtn")
        btn_salvar.clicked.connect(self.salvar)
        btn_box.addWidget(btn_salvar)

        layout.addLayout(btn_box)

        # Se for edição, preenche os campos com formatação aplicada
        if self.is_edit:
            self.txt_nome.setText(self.patient.get("nome", ""))
            self.txt_cpf.setText(format_cpf(self.patient.get("cpf", "")))
            self.txt_nascimento.setText(format_data_br(self.patient.get("data_nascimento", "")))
            self.txt_telefone.setText(format_telefone(self.patient.get("telefone", "")))
            self.txt_email.setText(self.patient.get("email", ""))
            self.txt_endereco.setText(self.patient.get("endereco", ""))
            self.txt_alergias.setText(self.patient.get("alergias", ""))
            self.txt_obs.setPlainText(self.patient.get("observacoes_medicas", ""))

            dt_antiga = self.patient.get("data_ultimo_atendimento_manual", "")
            if dt_antiga:
                self.chk_historico.setChecked(True)
                self.dt_data_manual.setEnabled(True)
                # Aceita tanto AAAA-MM-DD quanto DD/MM/AAAA
                try:
                    if "/" in dt_antiga:
                        d, m, y = dt_antiga.split("/")
                        self.dt_data_manual.setDate(QDate(int(y), int(m), int(d)))
                    elif "-" in dt_antiga:
                        y, m, d = dt_antiga.split("-")
                        self.dt_data_manual.setDate(QDate(int(y), int(m), int(d)))
                except Exception:
                    pass

    def _aplicar_mascara_campo(self, widget: QLineEdit, func_mascara):
        texto = widget.text()
        formatado = func_mascara(texto)
        if texto != formatado:
            widget.blockSignals(True)
            widget.setText(formatado)
            widget.blockSignals(False)
            widget.setCursorPosition(len(formatado))

    def _finalizar_formatacao_campo(self, widget: QLineEdit, func_final):
        texto = widget.text().strip()
        if texto:
            formatado = func_final(texto)
            widget.setText(formatado)

    def alternar_historico_ativo(self, state):
        self.dt_data_manual.setEnabled(self.chk_historico.isChecked())

    def salvar(self):
        nome = self.txt_nome.text().strip()
        cpf = self.txt_cpf.text().strip()
        nasc = self.txt_nascimento.text().strip()
        tel = self.txt_telefone.text().strip()
        email = self.txt_email.text().strip()
        end = self.txt_endereco.text().strip()
        alergias = self.txt_alergias.text().strip()
        obs = self.txt_obs.toPlainText().strip()

        data_manual = ""
        if self.chk_historico.isChecked():
            qd = self.dt_data_manual.date()
            data_manual = f"{qd.year():04d}-{qd.month():02d}-{qd.day():02d}"

        if not nome:
            QMessageBox.warning(self, "Aviso", "O nome do paciente é obrigatório.")
            return

        if self.is_edit:
            ok, msg = update_patient(
                self.patient["id"], nome, cpf, nasc, tel,
                email, end, alergias, obs,
                self.current_user["id"], self.current_user["nome"],
                data_ultimo_atendimento_manual=data_manual
            )
        else:
            ok, msg, pid = create_patient(
                nome, cpf, nasc, tel, email,
                end, alergias, obs,
                self.current_user["id"], self.current_user["nome"],
                data_ultimo_atendimento_manual=data_manual
            )

        if ok:
            QMessageBox.information(self, "Sucesso", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Aviso", msg)


class RecordFormDialog(QDialog):
    """Diálogo completo para cadastrar ou editar Procedimento / Evolução Clínica Odontológica."""
    def __init__(self, patient_id: int, current_user: dict, record: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.current_user = current_user
        self.record = record
        self.is_edit = record is not None
        titulo = f"Editar Procedimento #{record['id']}" if self.is_edit else "Cadastrar Procedimento do Paciente"
        self.setWindowTitle(titulo)
        self.setFixedSize(500, 440)
        self.setStyleSheet(PATIENT_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)

        titulo_lbl = "Editar Procedimento Clínico" if self.is_edit else "Cadastrar Procedimento Clínico"
        title = QLabel(titulo_lbl)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #166260;")
        layout.addWidget(title)

        row_dt = QHBoxLayout()
        v_data = QVBoxLayout()
        v_data.addWidget(QLabel("Data do Atendimento:"))
        self.dt_proc = CustomDateEdit()
        self.dt_proc.setDate(QDate.currentDate())
        v_data.addWidget(self.dt_proc)
        row_dt.addLayout(v_data)

        v_dente = QVBoxLayout()
        v_dente.addWidget(QLabel("Dente / Região:"))
        self.txt_dente = QLineEdit()
        self.txt_dente.setPlaceholderText("Ex: 16, 21, 38, Arcada Sup...")
        v_dente.addWidget(self.txt_dente)
        row_dt.addLayout(v_dente)
        layout.addLayout(row_dt)

        layout.addWidget(QLabel("Procedimento Realizado (*):"))
        self.cmb_procedimento = QComboBox()
        self.cmb_procedimento.setEditable(True)
        opcoes = [
            "Consulta / Avaliação Inicial",
            "Profilaxia / Limpeza Dental",
            "Restauração em Resina Composta",
            "Exodontia (Extração Dental)",
            "Tratamento Endodôntico (Canal)",
            "Clareamento Dental",
            "Raspagem e Alisamento Radicular",
            "Instalação / Ajuste de Aparelho Ortodôntico",
            "Moldagem e Prótese",
            "Urgência Odontológica"
        ]
        self.cmb_procedimento.addItems(opcoes)
        layout.addWidget(self.cmb_procedimento)

        layout.addWidget(QLabel("Detalhamento Clínico / Observações:"))
        self.txt_descricao = QTextEdit()
        self.txt_descricao.setPlaceholderText("Descreva materiais utilizados, anestésico, evolução clínica, conduta...")
        layout.addWidget(self.txt_descricao)

        # Se for edição, preenche com os dados existentes
        if self.is_edit and self.record:
            rec = self.record
            self.txt_dente.setText(rec.get("dente_regiao") or "")
            self.cmb_procedimento.setCurrentText(rec.get("procedimento") or "")
            self.txt_descricao.setText(rec.get("descricao") or "")
            if rec.get("data_hora"):
                self.dt_proc.setDate(str(rec["data_hora"])[:10])

        layout.addSpacing(10)

        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("secondaryBtn")
        btn_cancelar.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancelar)

        btn_salvar_txt = "Salvar Alterações" if self.is_edit else "Salvar no Prontuário"
        btn_salvar = QPushButton(btn_salvar_txt)
        btn_salvar.setObjectName("primaryBtn")
        btn_salvar.clicked.connect(self.salvar)
        btn_box.addWidget(btn_salvar)

        layout.addLayout(btn_box)

    def salvar(self):
        dente = self.txt_dente.text().strip()
        procedimento = self.cmb_procedimento.currentText().strip()
        descricao = self.txt_descricao.toPlainText().strip()

        if not procedimento:
            QMessageBox.warning(self, "Aviso", "Informe o procedimento realizado.")
            return

        qdate = self.dt_proc.date()
        data_hora_str = f"{qdate.year():04d}-{qdate.month():02d}-{qdate.day():02d} 10:00:00"

        if self.is_edit and self.record:
            ok, msg = update_record(
                self.record["id"], dente, procedimento, descricao,
                self.current_user["nome"], self.current_user["id"],
                data_hora=data_hora_str
            )
        else:
            ok, msg = add_record(
                self.patient_id, dente, procedimento, descricao,
                self.current_user["nome"], self.current_user["id"],
                data_hora=data_hora_str
            )

        if ok:
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", msg)


# Alias para retrocompatibilidade
NewRecordDialog = RecordFormDialog


class PatientDetailDialog(QDialog):
    """Ficha Clínica Completa com Prontuário, Anexos (Raio-X) e Atestados."""
    def __init__(self, patient_id: int, current_user: dict, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.current_user = current_user
        self.patient = get_patient(patient_id)
        self.setWindowTitle(f"Ficha Clínica - {self.patient['nome']}")
        self.resize(900, 650)
        self.setStyleSheet(PATIENT_STYLE)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)

        # Cabeçalho do Paciente
        header_card = QFrame(self)
        header_card.setStyleSheet("background-color: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; padding: 12px;")
        h_layout = QHBoxLayout(header_card)
        h_layout.setContentsMargins(12, 8, 12, 8)

        info_box = QVBoxLayout()
        info_box.setSpacing(4)
        lbl_nome = QLabel(f"👤 {self.patient['nome']}")
        lbl_nome.setStyleSheet("font-size: 18px; font-weight: bold; color: #166260;")
        
        detalhes = f"CPF: {self.patient['cpf'] or 'Não informado'}  •  Nascimento: {self.patient['data_nascimento'] or 'Não informada'}  •  Tel: {self.patient['telefone'] or 'Não informado'}"
        lbl_detalhes = QLabel(detalhes)
        lbl_detalhes.setStyleSheet("color: #64748b; font-size: 13px;")

        info_box.addWidget(lbl_nome)
        info_box.addWidget(lbl_detalhes)
        h_layout.addLayout(info_box)
        h_layout.addStretch()

        # Alerta de Alergia em Destaque se houver
        if self.patient.get("alergias"):
            alergia_badge = QLabel(f"⚠️ Alergia: {self.patient['alergias']}")
            alergia_badge.setStyleSheet("""
                background-color: #fef2f2;
                color: #b91c1c;
                font-weight: bold;
                border: 1px solid #fecaca;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            """)
            h_layout.addWidget(alergia_badge)

        btn_editar_cadastro = QPushButton("Editar Dados")
        btn_editar_cadastro.setObjectName("secondaryBtn")
        btn_editar_cadastro.clicked.connect(self.abrir_edicao_cadastro)
        h_layout.addWidget(btn_editar_cadastro)

        main_layout.addWidget(header_card)

        # Abas
        self.tabs = QTabWidget(self)

        # Aba 1: Prontuário Odontológico
        tab_prontuario = QWidget()
        layout_pront = QVBoxLayout(tab_prontuario)
        layout_pront.setSpacing(10)

        pront_actions = QHBoxLayout()
        lbl_pront_title = QLabel("Procedimentos Realizados no Paciente")
        lbl_pront_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #166260;")
        pront_actions.addWidget(lbl_pront_title)
        pront_actions.addStretch()

        btn_novo_procedimento = QPushButton("➕ Cadastrar Procedimento")
        btn_novo_procedimento.setObjectName("primaryBtn")
        btn_novo_procedimento.clicked.connect(self.abrir_novo_procedimento)
        pront_actions.addWidget(btn_novo_procedimento)

        btn_editar_procedimento = QPushButton("✏️ Editar Procedimento")
        btn_editar_procedimento.setObjectName("secondaryBtn")
        btn_editar_procedimento.clicked.connect(self.abrir_editar_procedimento)
        pront_actions.addWidget(btn_editar_procedimento)

        btn_remover_rec = QPushButton("🗑️ Excluir Procedimento")
        btn_remover_rec.setObjectName("dangerBtn")
        btn_remover_rec.clicked.connect(self.excluir_procedimento_selecionado)
        pront_actions.addWidget(btn_remover_rec)
        layout_pront.addLayout(pront_actions)

        self.table_records = QTableWidget()
        self.table_records.setColumnCount(5)
        self.table_records.setHorizontalHeaderLabels(["Data / Hora", "Profissional", "Dente / Região", "Procedimento", "Descrição / Conduta"])
        self.table_records.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_records.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_records.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_records.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_records.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table_records.setAlternatingRowColors(True)
        self.table_records.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_records.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_records.doubleClicked.connect(self.abrir_editar_procedimento)
        self.table_records.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                color: #0f172a;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
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
        layout_pront.addWidget(self.table_records)

        self.tabs.addTab(tab_prontuario, "🦷 Procedimentos e Prontuário")

        # Aba 2: Anexos e Exames (Raio-X)
        tab_anexos = QWidget()
        layout_anexos = QVBoxLayout(tab_anexos)
        layout_anexos.setSpacing(10)

        anexos_actions = QHBoxLayout()
        lbl_anexos_title = QLabel("Galeria de Exames, Raio-X e Documentos")
        lbl_anexos_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #166260;")
        anexos_actions.addWidget(lbl_anexos_title)
        anexos_actions.addStretch()

        btn_anexar = QPushButton("+ Anexar Arquivo (Raio-X, Foto, PDF)")
        btn_anexar.setObjectName("primaryBtn")
        btn_anexar.clicked.connect(self.anexar_arquivo)
        anexos_actions.addWidget(btn_anexar)
        layout_anexos.addLayout(anexos_actions)

        self.table_anexos = QTableWidget()
        self.table_anexos.setColumnCount(4)
        self.table_anexos.setHorizontalHeaderLabels(["ID", "Nome do Arquivo", "Data de Envio", "Tamanho"])
        self.table_anexos.setColumnHidden(0, True)
        self.table_anexos.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_anexos.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_anexos.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_anexos.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_anexos.setAlternatingRowColors(True)
        self.table_anexos.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_anexos.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_anexos.doubleClicked.connect(self.abrir_anexo_selecionado)
        self.table_anexos.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                color: #0f172a;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
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
        layout_anexos.addWidget(self.table_anexos)

        anexos_bottom_bar = QHBoxLayout()
        lbl_dica = QLabel("💡 Dica: Duplo clique na linha para abrir o arquivo no visualizador do Windows.")
        lbl_dica.setStyleSheet("color: #64748b; font-size: 12px;")
        anexos_bottom_bar.addWidget(lbl_dica)
        anexos_bottom_bar.addStretch()

        btn_abrir_anexo = QPushButton("👁️ Abrir / Visualizar")
        btn_abrir_anexo.setObjectName("primaryBtn")
        btn_abrir_anexo.clicked.connect(self.abrir_anexo_selecionado)
        anexos_bottom_bar.addWidget(btn_abrir_anexo)

        btn_excluir_anexo = QPushButton("Excluir Anexo")
        btn_excluir_anexo.setObjectName("dangerBtn")
        btn_excluir_anexo.clicked.connect(self.excluir_anexo_selecionado)
        anexos_bottom_bar.addWidget(btn_excluir_anexo)

        layout_anexos.addLayout(anexos_bottom_bar)
        self.tabs.addTab(tab_anexos, "📁 Raio-X e Anexos")

        # Aba 3: Declaração / Atestado Odontológico
        tab_atestado = QWidget()
        layout_atestado = QVBoxLayout(tab_atestado)
        layout_atestado.setSpacing(10)

        lbl_atestado_title = QLabel("Emissão Rápida de Declaração / Atestado")
        lbl_atestado_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #166260;")
        layout_atestado.addWidget(lbl_atestado_title)

        self.txt_atestado = QTextEdit()
        hoje = datetime.now().strftime("%d/%m/%Y")
        hora = datetime.now().strftime("%H:%M")
        texto_padrao = (
            f"DECLARAÇÃO DE COMPARECIMENTO ODONTOLÓGICO\n\n"
            f"Declaro para os devidos fins que o(a) paciente {self.patient['nome']}, "
            f"portador(a) do CPF nº {self.patient['cpf'] or '___________________'}, compareceu a esta clínica odontológica "
            f"no dia {hoje}, às {hora} horas, para realização de procedimento odontológico.\n\n\n"
            f"_____________________________________________\n"
            f"Dra. Lara Camila • Cirurgiã-Dentista\n"
            f"CRO-BA 15247 • LCR Clínica Odontológica\n"
            f"Irecê - Bahia"
        )
        self.txt_atestado.setPlainText(texto_padrao)
        layout_atestado.addWidget(self.txt_atestado)

        btn_copiar = QPushButton("📋 Copiar Texto do Atestado")
        btn_copiar.setObjectName("primaryBtn")
        btn_copiar.clicked.connect(self.copiar_atestado)
        layout_atestado.addWidget(btn_copiar, alignment=Qt.AlignRight)

        self.tabs.addTab(tab_atestado, "📄 Atestado / Declaração")

        main_layout.addWidget(self.tabs)

        self.carregar_prontuario()
        self.carregar_anexos()

    def carregar_prontuario(self):
        records = list_records(self.patient_id)
        self.table_records.setRowCount(len(records))
        for row_idx, r in enumerate(records):
            item_dt = QTableWidgetItem(format_datetime_br(r["data_hora"]))
            item_dt.setTextAlignment(Qt.AlignCenter)
            self.table_records.setItem(row_idx, 0, item_dt)
            self.table_records.setItem(row_idx, 1, QTableWidgetItem(str(r["profissional_nome"])))
            
            dente_txt = r["dente_regiao"] or "Geral"
            item_dente = QTableWidgetItem(dente_txt)
            item_dente.setTextAlignment(Qt.AlignCenter)
            item_dente.setForeground(QColor("#0d9488"))
            self.table_records.setItem(row_idx, 2, item_dente)

            item_proc = QTableWidgetItem(r["procedimento"])
            item_proc.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table_records.setItem(row_idx, 3, item_proc)

            self.table_records.setItem(row_idx, 4, QTableWidgetItem(r["descricao"] or ""))
            # Armazena o ID na primeira coluna
            self.table_records.item(row_idx, 0).setData(Qt.UserRole, r["id"])

    def carregar_anexos(self):
        anexos = list_attachments(self.patient_id)
        self.table_anexos.setRowCount(len(anexos))
        for row_idx, a in enumerate(anexos):
            item_id = QTableWidgetItem(str(a["id"]))
            item_id.setTextAlignment(Qt.AlignCenter)
            self.table_anexos.setItem(row_idx, 0, item_id)

            self.table_anexos.setItem(row_idx, 1, QTableWidgetItem(a["nome_arquivo"]))
            
            item_upload = QTableWidgetItem(format_datetime_br(a["data_upload"]))
            item_upload.setTextAlignment(Qt.AlignCenter)
            self.table_anexos.setItem(row_idx, 2, item_upload)

            kb = (a["tamanho_bytes"] or 0) / 1024
            tam_txt = f"{kb:.1f} KB" if kb < 1024 else f"{(kb/1024):.1f} MB"
            item_tam = QTableWidgetItem(tam_txt)
            item_tam.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_anexos.setItem(row_idx, 3, item_tam)

    def abrir_novo_procedimento(self):
        dialog = RecordFormDialog(self.patient_id, self.current_user, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.carregar_prontuario()

    def abrir_editar_procedimento(self):
        selected = self.table_records.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione um procedimento para editar.")
            return

        row = selected[0].row()
        record_id = self.table_records.item(row, 0).data(Qt.UserRole)
        rec = get_record(record_id)
        if not rec:
            QMessageBox.warning(self, "Aviso", "Procedimento não encontrado.")
            return

        dialog = RecordFormDialog(self.patient_id, self.current_user, record=rec, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.carregar_prontuario()

    def excluir_procedimento_selecionado(self):
        selected = self.table_records.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione um procedimento para excluir.")
            return

        row = selected[0].row()
        record_id = self.table_records.item(row, 0).data(Qt.UserRole)

        confirm = QMessageBox.question(
            self, "Confirmação",
            "Tem certeza que deseja excluir este procedimento do prontuário?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            ok, msg = delete_record(record_id, self.current_user["id"], self.current_user["nome"])
            if ok:
                self.carregar_prontuario()
            else:
                QMessageBox.critical(self, "Erro", msg)

    def anexar_arquivo(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Arquivo / Exame",
            "", "Arquivos de Imagem e Documentos (*.png *.jpg *.jpeg *.pdf *.dcm *.zip);;Todos os Arquivos (*.*)"
        )
        if filepath:
            ok, msg = add_attachment(self.patient_id, filepath, self.current_user["id"], self.current_user["nome"])
            if ok:
                QMessageBox.information(self, "Sucesso", msg)
                self.carregar_anexos()
            else:
                QMessageBox.critical(self, "Erro", msg)

    def abrir_anexo_selecionado(self):
        selected = self.table_anexos.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione um anexo na tabela.")
            return

        row = selected[0].row()
        attachment_id = int(self.table_anexos.item(row, 0).text())
        ok, msg = open_attachment(attachment_id)
        if not ok:
            QMessageBox.warning(self, "Erro", msg)

    def excluir_anexo_selecionado(self):
        selected = self.table_anexos.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione um anexo para excluir.")
            return

        row = selected[0].row()
        attachment_id = int(self.table_anexos.item(row, 0).text())
        if perguntar_sim_nao(self, "Excluir Anexo", "Deseja realmente excluir este anexo permanentemente?"):
            ok, msg = delete_attachment(attachment_id, self.current_user["id"], self.current_user["nome"])
            if ok:
                self.carregar_anexos()
            else:
                QMessageBox.critical(self, "Erro", msg)

    def copiar_atestado(self):
        from PySide6.QtGui import QGuiApplication
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.txt_atestado.toPlainText())
        QMessageBox.information(self, "Copiado", "Texto do atestado copiado para a área de transferência!")

    def abrir_edicao_cadastro(self):
        dialog = PatientFormDialog(self.current_user, self.patient, self)
        if dialog.exec() == QDialog.Accepted:
            self.patient = get_patient(self.patient_id)
            self.init_ui()


class PatientsView(QWidget):
    """Tela Principal de Pacientes com Busca Rápida e Gestão de Ativos/Inativos (Lixeira Segura)."""
    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.filtro_status = "ativos"
        self.init_ui()
        self.carregar_pacientes()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        self.setStyleSheet(PATIENT_STYLE)

        # Cabeçalho Superior
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Gestão de Pacientes e Prontuários")
        title.setStyleSheet("font-size: 19px; font-weight: bold; color: #166260;")
        sub = QLabel("Fichas clínicas individuais, histórico odontológico e anexos de exames.")
        sub.setStyleSheet("color: #64748b; font-size: 13px;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.btn_novo = QPushButton("+ Novo Paciente")
        self.btn_novo.setObjectName("primaryBtn")
        self.btn_novo.setStyleSheet("""
            background-color: #2ca5a9;
            color: #ffffff;
            font-weight: bold;
            font-size: 14px;
            padding: 10px 18px;
            border-radius: 6px;
            border: none;
        """)
        self.btn_novo.clicked.connect(self.abrir_novo_paciente)
        header_layout.addWidget(self.btn_novo)

        layout.addLayout(header_layout)

        # Seletor de Abas de Status: Ativos x Inativos / Lixeira
        status_bar = QHBoxLayout()
        status_bar.setSpacing(10)

        self.btn_filtro_ativos = QPushButton("🟢 Pacientes Ativos")
        self.btn_filtro_ativos.setCheckable(True)
        self.btn_filtro_ativos.setChecked(True)
        self.btn_filtro_ativos.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                font-weight: 600;
                padding: 8px 24px;
                min-width: 195px;
                border-radius: 6px;
                border: 1px solid #cbd5e1;
                font-size: 13px;
            }
            QPushButton:checked {
                background-color: #2ca5a9;
                color: #ffffff;
                border: 1px solid #248a8d;
                font-weight: bold;
            }
        """)
        self.btn_filtro_ativos.clicked.connect(lambda: self.mudar_filtro_status("ativos"))
        status_bar.addWidget(self.btn_filtro_ativos)

        self.btn_filtro_inativos = QPushButton("🗄️ Inativos / Lixeira")
        self.btn_filtro_inativos.setCheckable(True)
        self.btn_filtro_inativos.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                font-weight: 600;
                padding: 8px 24px;
                min-width: 195px;
                border-radius: 6px;
                border: 1px solid #cbd5e1;
                font-size: 13px;
            }
            QPushButton:checked {
                background-color: #64748b;
                color: #ffffff;
                border: 1px solid #475569;
                font-weight: bold;
            }
        """)
        self.btn_filtro_inativos.clicked.connect(lambda: self.mudar_filtro_status("inativos"))
        status_bar.addWidget(self.btn_filtro_inativos)

        status_bar.addStretch()
        layout.addLayout(status_bar)

        # Barra de Pesquisa Rápida (Nome ou CPF)
        search_card = QFrame()
        search_card.setStyleSheet("background-color: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; padding: 8px;")
        search_layout = QHBoxLayout(search_card)
        search_layout.setContentsMargins(10, 4, 10, 4)

        lbl_icone = QLabel("🔍")
        search_layout.addWidget(lbl_icone)

        self.txt_busca = QLineEdit()
        self.txt_busca.setPlaceholderText("Pesquisar paciente em tempo real por Nome ou CPF...")
        self.txt_busca.setStyleSheet("border: none; background: transparent; font-size: 14px;")
        self.txt_busca.textChanged.connect(self.carregar_pacientes)
        search_layout.addWidget(self.txt_busca)

        btn_limpar = QPushButton("Limpar")
        btn_limpar.setObjectName("secondaryBtn")
        btn_limpar.clicked.connect(lambda: self.txt_busca.clear())
        search_layout.addWidget(btn_limpar)

        layout.addWidget(search_card)

        # Tabela de Pacientes
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Nome do Paciente", "CPF", "Telefone / WhatsApp", "Alergias", "Último Atendimento"])
        self.table.setColumnHidden(0, True)  # Oculta coluna técnica de ID para visual limpo
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemSelectionChanged.connect(self.ao_mudar_selecao_paciente)
        self.table.doubleClicked.connect(self.abrir_prontuario_selecionado)
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
                padding: 8px;
            }
        """)
        layout.addWidget(self.table)

        # Barra de Ações Inferior
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch()

        self.btn_abrir = QPushButton("🦷 Abrir Prontuário e Procedimentos")
        self.btn_abrir.setObjectName("primaryBtn")
        self.btn_abrir.clicked.connect(self.abrir_prontuario_selecionado)
        bottom_bar.addWidget(self.btn_abrir)

        self.btn_novo_proc = QPushButton("➕ Cadastrar Procedimento")
        self.btn_novo_proc.setObjectName("secondaryBtn")
        self.btn_novo_proc.setToolTip("Cadastrar diretamente um novo procedimento para o paciente selecionado")
        self.btn_novo_proc.clicked.connect(self.abrir_novo_procedimento_direto)
        bottom_bar.addWidget(self.btn_novo_proc)

        # Botão de Inativação / Arquivamento
        self.btn_excluir = QPushButton("🗑️ Enviar para Lixeira")
        self.btn_excluir.setObjectName("dangerBtn")
        self.btn_excluir.clicked.connect(self.excluir_paciente_selecionado)
        bottom_bar.addWidget(self.btn_excluir)

        # Botão de Restauração (visível na lixeira)
        self.btn_restaurar = QPushButton("♻️ Restaurar Paciente")
        self.btn_restaurar.setStyleSheet("""
            background-color: #059669;
            color: #ffffff;
            font-weight: bold;
            padding: 8px 16px;
            border-radius: 6px;
            border: none;
            font-size: 13px;
        """)
        self.btn_restaurar.clicked.connect(self.restaurar_paciente_selecionado)
        self.btn_restaurar.setVisible(False)
        bottom_bar.addWidget(self.btn_restaurar)

        # Botão de Exclusão Permanente (apenas admin na lixeira)
        if self.current_user["perfil"] == "admin":
            self.btn_excluir_definitivo = QPushButton("Excluir Permanentemente")
            self.btn_excluir_definitivo.setObjectName("dangerBtn")
            self.btn_excluir_definitivo.clicked.connect(self.excluir_paciente_definitivo)
            self.btn_excluir_definitivo.setVisible(False)
            bottom_bar.addWidget(self.btn_excluir_definitivo)

        layout.addLayout(bottom_bar)

    def mudar_filtro_status(self, novo_status: str):
        self.filtro_status = novo_status
        eh_ativo = (novo_status == "ativos")
        self.btn_filtro_ativos.setChecked(eh_ativo)
        self.btn_filtro_inativos.setChecked(not eh_ativo)

        self.btn_excluir.setVisible(eh_ativo)
        self.btn_restaurar.setVisible(not eh_ativo)
        self.btn_novo_proc.setVisible(eh_ativo)
        if hasattr(self, "btn_excluir_definitivo"):
            self.btn_excluir_definitivo.setVisible(not eh_ativo and self.current_user["perfil"] == "admin")

        if eh_ativo:
            self.btn_abrir.setText("🦷 Abrir Prontuário e Procedimentos")
        else:
            self.btn_abrir.setText("👁️ Ver Prontuário (Histórico)")

        self.carregar_pacientes()

    def ao_mudar_selecao_paciente(self):
        """Atualiza dinamicamente os botões de ação conforme o status do paciente selecionado (Ativo ou Inativo)."""
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            eh_ativo = (self.filtro_status == "ativos")
            self.btn_excluir.setVisible(eh_ativo)
            self.btn_restaurar.setVisible(not eh_ativo)
            self.btn_novo_proc.setVisible(eh_ativo)
            if hasattr(self, "btn_excluir_definitivo"):
                self.btn_excluir_definitivo.setVisible(not eh_ativo and self.current_user["perfil"] == "admin")
            self.btn_abrir.setText("🦷 Abrir Prontuário e Procedimentos" if eh_ativo else "👁️ Ver Prontuário (Histórico)")
            return

        row = selected[0].row()
        item_zero = self.table.item(row, 0)
        p_data = item_zero.data(Qt.UserRole) if item_zero else None
        
        # Determina se o paciente selecionado está ativo ou inativo
        eh_ativo = True
        if isinstance(p_data, dict):
            eh_ativo = bool(p_data.get("ativo", 1))
        elif self.filtro_status == "inativos":
            eh_ativo = False

        self.btn_excluir.setVisible(eh_ativo)
        self.btn_restaurar.setVisible(not eh_ativo)
        self.btn_novo_proc.setVisible(eh_ativo)
        if hasattr(self, "btn_excluir_definitivo"):
            self.btn_excluir_definitivo.setVisible(not eh_ativo and self.current_user["perfil"] == "admin")

        if eh_ativo:
            self.btn_abrir.setText("🦷 Abrir Prontuário e Procedimentos")
        else:
            self.btn_abrir.setText("👁️ Ver Prontuário (Inativo)")

    def carregar_pacientes(self):
        termo = self.txt_busca.text().strip()
        # Se estiver pesquisando por termo, busca em TODOS (incluindo inativos)
        # Se a busca estiver vazia, respeita a aba selecionada (Ativos ou Inativos)
        status_para_busca = "todos" if termo else self.filtro_status
        pacientes = search_patients(termo, status_filtro=status_para_busca)
        self.table.setRowCount(len(pacientes))

        for row_idx, p in enumerate(pacientes):
            eh_inativo = (p.get("ativo", 1) == 0)

            item_id = QTableWidgetItem(str(p["id"]))
            item_id.setTextAlignment(Qt.AlignCenter)
            item_id.setData(Qt.UserRole, p)  # Guarda o dict do paciente
            self.table.setItem(row_idx, 0, item_id)

            nome_display = f"{p['nome']} [Inativo / Lixeira]" if eh_inativo else p["nome"]
            item_nome = QTableWidgetItem(nome_display)
            if eh_inativo:
                item_nome.setFont(QFont("Segoe UI", 10, QFont.Bold))
                item_nome.setForeground(QColor("#64748b"))  # Destaque acinzentado para inativo
            else:
                item_nome.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table.setItem(row_idx, 1, item_nome)

            item_cpf = QTableWidgetItem(format_cpf(p["cpf"]) if p["cpf"] else "-")
            item_cpf.setTextAlignment(Qt.AlignCenter)
            if eh_inativo:
                item_cpf.setForeground(QColor("#64748b"))
            self.table.setItem(row_idx, 2, item_cpf)

            item_tel = QTableWidgetItem(format_telefone(p["telefone"]) if p["telefone"] else "-")
            item_tel.setTextAlignment(Qt.AlignCenter)
            if eh_inativo:
                item_tel.setForeground(QColor("#64748b"))
            self.table.setItem(row_idx, 3, item_tel)

            # Alergia com destaque
            alergia_txt = p["alergias"] or "Nenhuma"
            item_alergia = QTableWidgetItem(alergia_txt)
            if p["alergias"]:
                item_alergia.setForeground(QColor("#b91c1c"))
                item_alergia.setFont(QFont("Segoe UI", 9, QFont.Bold))
            elif eh_inativo:
                item_alergia.setForeground(QColor("#64748b"))
            self.table.setItem(row_idx, 4, item_alergia)

            ultimo = p["ultimo_atendimento"] or "Sem registros"
            item_ultimo = QTableWidgetItem(str(ultimo))
            item_ultimo.setTextAlignment(Qt.AlignCenter)
            if eh_inativo:
                item_ultimo.setForeground(QColor("#64748b"))
            self.table.setItem(row_idx, 5, item_ultimo)

        # Atualiza contadores dos botões de filtro
        try:
            total_ativos = len(search_patients("", status_filtro="ativos"))
            total_inativos = len(search_patients("", status_filtro="inativos"))
            self.btn_filtro_ativos.setText(f"🟢 Pacientes Ativos ({total_ativos})")
            self.btn_filtro_inativos.setText(f"🗄️ Inativos / Lixeira ({total_inativos})")
        except Exception:
            pass

        self.ao_mudar_selecao_paciente()

    def get_selected_patient_id(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione um paciente na lista.")
            return None
        row = selected[0].row()
        return int(self.table.item(row, 0).text())

    def abrir_novo_paciente(self):
        dialog = PatientFormDialog(self.current_user, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.carregar_pacientes()

    def abrir_prontuario_selecionado(self):
        patient_id = self.get_selected_patient_id()
        if not patient_id:
            return
        dialog = PatientDetailDialog(patient_id, self.current_user, self)
        dialog.exec()
        self.carregar_pacientes()

    def abrir_novo_procedimento_direto(self):
        patient_id = self.get_selected_patient_id()
        if not patient_id:
            return

        dialog = RecordFormDialog(patient_id, self.current_user, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.carregar_pacientes()

    def excluir_paciente_selecionado(self):
        patient_id = self.get_selected_patient_id()
        if not patient_id:
            return

        msg = (
            "Deseja enviar este paciente para a Lixeira / Inativos?\n\n"
            "• O cadastro deixará de aparecer na busca ativa e na agenda.\n"
            "• Todos os prontuários e exames de Raio-X ficam preservados com segurança.\n"
            "• Você poderá restaurá-lo a qualquer momento na aba 'Inativos / Lixeira'.\n\n"
            "Deseja continuar?"
        )
        if perguntar_sim_nao(self, "Enviar Paciente para Lixeira", msg):
            ok, msg_res = delete_patient(patient_id, self.current_user["id"], self.current_user["nome"])
            if ok:
                QMessageBox.information(self, "Arquivado com Sucesso", msg_res)
                self.carregar_pacientes()
            else:
                QMessageBox.critical(self, "Erro", msg_res)

    def restaurar_paciente_selecionado(self):
        patient_id = self.get_selected_patient_id()
        if not patient_id:
            return

        ok, msg = restore_patient(patient_id, self.current_user["id"], self.current_user["nome"])
        if ok:
            QMessageBox.information(self, "Paciente Restaurado", msg)
            self.carregar_pacientes()
        else:
            QMessageBox.critical(self, "Erro", msg)

    def excluir_paciente_definitivo(self):
        patient_id = self.get_selected_patient_id()
        if not patient_id:
            return

        msg = (
            "ATENÇÃO: Esta ação é permanente e irreversível!\n\n"
            "Todos os dados cadastrais, histórico de prontuários, agendamentos e arquivos de Raio-X deste paciente serão completamente destruídos.\n\n"
            "Tem certeza absoluta de que deseja excluir permanentemente?"
        )
        if perguntar_sim_nao(self, "Exclusão Definitiva Irreversível", msg, eh_aviso=True):
            ok, msg_res = delete_patient_permanently(patient_id, self.current_user["id"], self.current_user["nome"])
            if ok:
                QMessageBox.information(self, "Excluído com Sucesso", msg_res)
                self.carregar_pacientes()
            else:
                QMessageBox.critical(self, "Erro", msg_res)
