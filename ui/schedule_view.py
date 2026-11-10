from datetime import date, datetime, timedelta
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialog, QTabWidget, QTextEdit, QComboBox,
    QDateEdit, QFrame, QScrollArea, QGridLayout, QSizePolicy, QListView,
    QCheckBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor

from services.patient_service import search_patients
from ui.patients_view import perguntar_sim_nao
from ui.custom_date_edit import CustomDateEdit
from services.schedule_service import (
    create_appointment, list_appointments_by_date,
    update_appointment_status, delete_appointment,
    get_return_reminders, open_whatsapp,
    build_confirmation_message, build_return_message,
    get_post_operative_patients, get_birthday_patients,
    build_post_operative_message, build_birthday_message,
    get_setting, set_setting,
    DEFAULT_MSG_CONFIRMACAO, DEFAULT_MSG_RETORNO,
    DEFAULT_MSG_POS_OPERATORIO, DEFAULT_MSG_ANIVERSARIO
)

SCHEDULE_STYLE = """
QWidget {
    font-family: 'Segoe UI', sans-serif;
    color: #0f172a;
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
QLineEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox, QTextEdit {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
    selection-background-color: #2ca5a9;
    selection-color: #ffffff;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus, QSpinBox:focus, QTextEdit:focus {
    border: 2px solid #2ca5a9;
}
QComboBox {
    padding-right: 28px;
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


class AppointmentConclusionDialog(QDialog):
    """Diálogo de fluxo inteligente (Workflow 360°) acionado ao concluir um atendimento na Agenda."""
    def __init__(self, appointment_data: dict, current_user: dict, parent=None):
        super().__init__(parent)
        self.app = appointment_data
        self.current_user = current_user
        self.setWindowTitle("Atendimento Concluído • Workflow 360°")
        self.resize(540, 390)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8fafc;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                color: #1e293b;
            }
            QPushButton#primaryBtn {
                background-color: #0f766e;
                color: #ffffff;
                font-weight: bold;
                border-radius: 6px;
                border: none;
            }
            QPushButton#primaryBtn:hover {
                background-color: #115e59;
            }
            QPushButton#secondaryBtn {
                background-color: #ffffff;
                color: #334155;
                font-weight: 600;
                border-radius: 6px;
                border: 1px solid #cbd5e1;
            }
            QPushButton#secondaryBtn:hover {
                background-color: #f1f5f9;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        # Cabeçalho de Sucesso
        top_frame = QFrame()
        top_frame.setStyleSheet("background-color: #f0fdfa; border: 1px solid #99f6e4; border-radius: 8px; padding: 12px;")
        t_lay = QVBoxLayout(top_frame)
        t_lay.setSpacing(4)
        lbl_sucesso = QLabel("✨ Consulta Concluída com Sucesso!")
        lbl_sucesso.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f766e;")
        t_lay.addWidget(lbl_sucesso)

        pac_nome = self.app.get("paciente_nome", "Paciente")
        proc = self.app.get("procedimento", "Procedimento Clínico")
        lbl_pac = QLabel(f"Paciente: <b>{pac_nome}</b> &nbsp;|&nbsp; Procedimento: <b>{proc}</b>")
        lbl_pac.setStyleSheet("font-size: 13px; color: #334155;")
        t_lay.addWidget(lbl_pac)
        layout.addWidget(top_frame)

        lbl_pergunta = QLabel("Selecione a ação seguinte desejada para este atendimento:")
        lbl_pergunta.setStyleSheet("font-weight: 600; color: #475569; font-size: 13px;")
        layout.addWidget(lbl_pergunta)

        # Botões de Ação Rápida
        btn_fin = QPushButton("💰 Lançar Receita no Financeiro")
        btn_fin.setObjectName("primaryBtn")
        btn_fin.setStyleSheet("font-size: 13px; padding: 10px; font-weight: bold;")
        btn_fin.clicked.connect(self.abrir_financeiro)
        layout.addWidget(btn_fin)

        btn_rec = QPushButton("💊 Emitir Receita ou Atestado Oficial Timbrado")
        btn_rec.setObjectName("secondaryBtn")
        btn_rec.setStyleSheet("font-size: 13px; padding: 10px; font-weight: 600;")
        btn_rec.clicked.connect(self.abrir_receita)
        layout.addWidget(btn_rec)

        btn_ficha = QPushButton("🌐 Abrir Ficha do Paciente (Linha do Tempo 360°)")
        btn_ficha.setObjectName("secondaryBtn")
        btn_ficha.setStyleSheet("font-size: 13px; padding: 10px; font-weight: 600;")
        btn_ficha.clicked.connect(self.abrir_ficha)
        layout.addWidget(btn_ficha)

        layout.addStretch()

        btn_fechar = QPushButton("Apenas Concluir")
        btn_fechar.setObjectName("secondaryBtn")
        btn_fechar.clicked.connect(self.accept)
        layout.addWidget(btn_fechar, alignment=Qt.AlignRight)

    def abrir_financeiro(self):
        from ui.financial_view import TransactionFormDialog
        p_id = self.app.get("patient_id")
        p_nome = self.app.get("paciente_nome", "")
        proc = self.app.get("procedimento", "Consulta Odontológica")
        init_data = {
            "descricao": f"Atendimento: {proc} - {p_nome}",
            "categoria": "Procedimentos Clínicos / Consultas",
            "patient_id": p_id,
            "tipo": "Receita"
        }
        self.accept()
        dlg = TransactionFormDialog(self.current_user, tipo="Receita", initial_data=init_data, parent=self.parent())
        dlg.exec()

    def abrir_receita(self):
        from ui.clinical_docs_widget import PrescriptionFormDialog
        p_id = self.app.get("patient_id")
        p_nome = self.app.get("paciente_nome", "")
        p_cpf = self.app.get("paciente_cpf", "")
        self.accept()
        dlg = PrescriptionFormDialog(p_id, p_nome, p_cpf, self.current_user, parent=self.parent())
        dlg.exec()

    def abrir_ficha(self):
        from ui.patients_view import PatientDetailDialog
        p_id = self.app.get("patient_id")
        self.accept()
        dlg = PatientDetailDialog(p_id, self.current_user, parent=self.parent())
        dlg.exec()


class WhatsAppSettingsDialog(QDialog):
    """Diálogo para personalizar todos os modelos de mensagens do WhatsApp."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Mensagens do WhatsApp • LCR OdontoGest")
        self.setFixedSize(620, 560)
        self.setStyleSheet(SCHEDULE_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        title = QLabel("Modelos de Mensagens Padrão do WhatsApp")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f766e;")
        layout.addWidget(title)

        dica = QLabel("Tags automáticas: {paciente}, {paciente_completo}, {data}, {horario}, {procedimento}, {clinica}, {dentista}")
        dica.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(dica)

        tabs_msg = QTabWidget()

        # Aba 1: Confirmação
        tab1 = QWidget()
        l1 = QVBoxLayout(tab1)
        l1.addWidget(QLabel("Mensagem de Confirmação de Consulta:"))
        self.txt_confirmacao = QTextEdit()
        self.txt_confirmacao.setPlainText(get_setting("msg_confirmacao", DEFAULT_MSG_CONFIRMACAO))
        l1.addWidget(self.txt_confirmacao)
        tabs_msg.addTab(tab1, "Confirmação")

        # Aba 2: Retorno Semestral
        tab2 = QWidget()
        l2 = QVBoxLayout(tab2)
        l2.addWidget(QLabel("Mensagem de Retorno Semestral (6 Meses):"))
        self.txt_retorno = QTextEdit()
        self.txt_retorno.setPlainText(get_setting("msg_retorno", DEFAULT_MSG_RETORNO))
        l2.addWidget(self.txt_retorno)
        tabs_msg.addTab(tab2, "Retorno 6 Meses")

        # Aba 3: Pós-Operatório
        tab3 = QWidget()
        l3 = QVBoxLayout(tab3)
        l3.addWidget(QLabel("Mensagem de Acompanhamento Pós-Operatório (D+1):"))
        self.txt_pos_op = QTextEdit()
        self.txt_pos_op.setPlainText(get_setting("msg_pos_operatorio", DEFAULT_MSG_POS_OPERATORIO))
        l3.addWidget(self.txt_pos_op)
        tabs_msg.addTab(tab3, "Pós-Operatório")

        # Aba 4: Aniversário
        tab4 = QWidget()
        l4 = QVBoxLayout(tab4)
        l4.addWidget(QLabel("Mensagem de Felicitações de Aniversário:"))
        self.txt_aniversario = QTextEdit()
        self.txt_aniversario.setPlainText(get_setting("msg_aniversario", DEFAULT_MSG_ANIVERSARIO))
        l4.addWidget(self.txt_aniversario)
        tabs_msg.addTab(tab4, "Aniversário")

        layout.addWidget(tabs_msg)

        btn_box = QHBoxLayout()
        btn_restaurar = QPushButton("Restaurar Padrões")
        btn_restaurar.setObjectName("secondaryBtn")
        btn_restaurar.clicked.connect(self.restaurar_padrao)
        btn_box.addWidget(btn_restaurar)
        btn_box.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("secondaryBtn")
        btn_cancelar.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancelar)

        btn_salvar = QPushButton("Salvar Todas as Mensagens")
        btn_salvar.setObjectName("primaryBtn")
        btn_salvar.clicked.connect(self.salvar)
        btn_box.addWidget(btn_salvar)

        layout.addLayout(btn_box)

    def restaurar_padrao(self):
        self.txt_confirmacao.setPlainText(DEFAULT_MSG_CONFIRMACAO)
        self.txt_retorno.setPlainText(DEFAULT_MSG_RETORNO)
        self.txt_pos_op.setPlainText(DEFAULT_MSG_POS_OPERATORIO)
        self.txt_aniversario.setPlainText(DEFAULT_MSG_ANIVERSARIO)

    def salvar(self):
        set_setting("msg_confirmacao", self.txt_confirmacao.toPlainText().strip())
        set_setting("msg_retorno", self.txt_retorno.toPlainText().strip())
        set_setting("msg_pos_operatorio", self.txt_pos_op.toPlainText().strip())
        set_setting("msg_aniversario", self.txt_aniversario.toPlainText().strip())
        QMessageBox.information(self, "Sucesso", "Modelos de mensagens do WhatsApp atualizados com sucesso!")
        self.accept()


class SendWhatsAppPreviewDialog(QDialog):
    """Pré-visualização e edição rápida da mensagem antes de abrir o WhatsApp."""
    def __init__(self, telefone: str, mensagem_inicial: str, parent=None):
        super().__init__(parent)
        self.telefone = telefone
        self.setWindowTitle("Confirmar Envio pelo WhatsApp")
        self.setFixedSize(480, 340)
        self.setStyleSheet(SCHEDULE_STYLE)
        self.init_ui(mensagem_inicial)

    def init_ui(self, mensagem_inicial: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        lbl = QLabel(f"Destinatário: <b>{self.telefone}</b>")
        lbl.setStyleSheet("font-size: 14px; color: #166260;")
        layout.addWidget(lbl)

        layout.addWidget(QLabel("Você pode revisar ou ajustar o texto antes de abrir o WhatsApp:"))
        self.txt_msg = QTextEdit()
        self.txt_msg.setPlainText(mensagem_inicial)
        layout.addWidget(self.txt_msg)

        btn_box = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("secondaryBtn")
        btn_cancelar.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancelar)
        btn_box.addStretch()

        btn_enviar = QPushButton("📲 Abrir WhatsApp Agora")
        btn_enviar.setObjectName("whatsappBtn")
        btn_enviar.clicked.connect(self.abrir)
        btn_box.addWidget(btn_enviar)

        layout.addLayout(btn_box)

    def abrir(self):
        msg_final = self.txt_msg.toPlainText().strip()
        ok, retorno = open_whatsapp(self.telefone, msg_final)
        if ok:
            self.accept()
        else:
            QMessageBox.warning(self, "Aviso", retorno)


class NewAppointmentDialog(QDialog):
    """Diálogo para agendamento de nova consulta."""
    def __init__(self, current_user: dict, preselected_patient_id: int = None, initial_date: Optional[QDate] = None, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.preselected_patient_id = preselected_patient_id
        self.initial_date = initial_date
        self.setWindowTitle("Novo Agendamento de Consulta")
        self.setFixedSize(520, 520)
        self.setStyleSheet(SCHEDULE_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        title = QLabel("Agendar Consulta Odontológica")
        title.setStyleSheet("font-size: 17px; font-weight: bold; color: #166260;")
        layout.addWidget(title)

        lbl_pac = QLabel("Paciente (*):")
        lbl_pac.setStyleSheet("font-weight: 600; color: #334155;")
        layout.addWidget(lbl_pac)
        self.cmb_paciente = QComboBox()
        self.cmb_paciente.setEditable(True)
        self.cmb_paciente.setInsertPolicy(QComboBox.NoInsert)
        self.carregar_pacientes()
        layout.addWidget(self.cmb_paciente)

        row_dt = QHBoxLayout()
        row_dt.setSpacing(14)

        v_data = QVBoxLayout()
        v_data.setSpacing(4)
        lbl_data = QLabel("Data da Consulta (*):")
        lbl_data.setStyleSheet("font-weight: 600; color: #334155;")
        v_data.addWidget(lbl_data)
        self.dt_data = CustomDateEdit()
        data_padrao = self.initial_date if self.initial_date else QDate.currentDate()
        self.dt_data.setDate(data_padrao)
        v_data.addWidget(self.dt_data)
        row_dt.addLayout(v_data, 6)

        v_hora = QVBoxLayout()
        v_hora.setSpacing(4)
        lbl_hora = QLabel("Horário (*):")
        lbl_hora.setStyleSheet("font-weight: 600; color: #334155;")
        v_hora.addWidget(lbl_hora)
        self.cmb_horario = QComboBox()
        self.cmb_horario.setView(QListView())
        self.cmb_horario.setMinimumWidth(130)
        self.cmb_horario.setFixedHeight(34)
        self.cmb_horario.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                color: #0f766e;
                font-size: 13px;
                font-weight: bold;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding-left: 12px;
                padding-right: 28px;
            }
            QComboBox:focus {
                border: 2px solid #0f766e;
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
        """)
        for h in range(7, 21):
            for m in (0, 15, 30, 45):
                self.cmb_horario.addItem(f"{h:02d}:{m:02d}")

        # Sugestão inteligente de horário baseada no horário local atual da clínica
        agora = datetime.now()
        min_arredondado = 30 if agora.minute < 30 else 0
        hora_arredondada = agora.hour if agora.minute < 30 else agora.hour + 1
        if 7 <= hora_arredondada <= 19:
            hora_sugerida = f"{hora_arredondada:02d}:{min_arredondado:02d}"
        else:
            hora_sugerida = "08:00"

        idx_hora = self.cmb_horario.findText(hora_sugerida)
        if idx_hora >= 0:
            self.cmb_horario.setCurrentIndex(idx_hora)

        v_hora.addWidget(self.cmb_horario)
        row_dt.addLayout(v_hora, 4)
        layout.addLayout(row_dt)

        lbl_proc = QLabel("Procedimento Previsto:")
        lbl_proc.setStyleSheet("font-weight: 600; color: #334155;")
        layout.addWidget(lbl_proc)
        self.cmb_procedimento = QComboBox()
        self.cmb_procedimento.setEditable(True)
        procs = [
            "Consulta / Avaliação Inicial",
            "Profilaxia / Limpeza Preventiva",
            "Restauração",
            "Tratamento de Canal (Endodontia)",
            "Exodontia (Extração)",
            "Clareamento Dental",
            "Manutenção de Aparelho Ortodôntico",
            "Moldagem / Prótese",
            "Retorno de 6 Meses",
            "Urgência"
        ]
        self.cmb_procedimento.addItems(procs)
        layout.addWidget(self.cmb_procedimento)

        layout.addWidget(QLabel("Observações do Agendamento:"))
        self.txt_obs = QTextEdit()
        self.txt_obs.setMaximumHeight(70)
        self.txt_obs.setPlaceholderText("Ex: Paciente prefere atendimento matutino...")
        layout.addWidget(self.txt_obs)

        layout.addSpacing(10)

        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("secondaryBtn")
        btn_cancelar.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancelar)

        btn_salvar = QPushButton("Confirmar Agendamento")
        btn_salvar.setObjectName("primaryBtn")
        btn_salvar.clicked.connect(self.salvar)
        btn_box.addWidget(btn_salvar)

        layout.addLayout(btn_box)

    def carregar_pacientes(self):
        pacientes = search_patients("")
        self.cmb_paciente.clear()
        selected_idx = 0
        for idx, p in enumerate(pacientes):
            cpf_txt = f" - CPF: {p['cpf']}" if p.get('cpf') else ""
            label = f"{p['nome']}{cpf_txt}"
            self.cmb_paciente.addItem(label, p['id'])
            if self.preselected_patient_id and p['id'] == self.preselected_patient_id:
                selected_idx = idx
        self.cmb_paciente.setCurrentIndex(selected_idx)

    def salvar(self):
        patient_id = self.cmb_paciente.currentData()
        if not patient_id:
            QMessageBox.warning(self, "Aviso", "Selecione um paciente cadastrado.")
            return

        qdate = self.dt_data.date()
        data_str = f"{qdate.year():04d}-{qdate.month():02d}-{qdate.day():02d}"
        horario = self.cmb_horario.currentText().strip()
        procedimento = self.cmb_procedimento.currentText().strip()
        obs = self.txt_obs.toPlainText().strip()

        ok, msg = create_appointment(
            patient_id, data_str, horario, procedimento, obs,
            self.current_user["id"], self.current_user["nome"]
        )

        if ok:
            QMessageBox.information(self, "Sucesso", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", msg)


class ScheduleView(QWidget):
    """Módulo Principal de Agenda com Visão Semanal, Diária e Lembretes."""
    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        hoje = date.today()
        self.inicio_semana = hoje - timedelta(days=hoje.weekday())
        self.init_ui()
        self.carregar_agenda_semanal()
        self.carregar_agenda_do_dia()
        self.carregar_lembretes_retorno()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        self.setStyleSheet(SCHEDULE_STYLE)

        # Cabeçalho Superior
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Agenda e Lembretes de Retorno")
        title.setStyleSheet("font-size: 19px; font-weight: bold; color: #166260;")
        sub = QLabel("Visão semanal, controle diário e contato preventivo no WhatsApp.")
        sub.setStyleSheet("color: #64748b; font-size: 13px;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        btn_config_zap = QPushButton("⚙️ Configurar Mensagens")
        btn_config_zap.setObjectName("secondaryBtn")
        btn_config_zap.clicked.connect(self.abrir_configuracoes_whatsapp)
        header.addWidget(btn_config_zap)

        btn_novo_agendamento = QPushButton("+ Novo Agendamento")
        btn_novo_agendamento.setObjectName("primaryBtn")
        btn_novo_agendamento.clicked.connect(self.abrir_novo_agendamento)
        header.addWidget(btn_novo_agendamento)
        layout.addLayout(header)

        # Abas
        self.tabs = QTabWidget(self)

        # -------------------------------------------------------------
        # ABA 1: VISÃO SEMANAL (PADRÃO AO ABRIR)
        # -------------------------------------------------------------
        tab_semana = QWidget()
        layout_tab_semana = QVBoxLayout(tab_semana)
        layout_tab_semana.setSpacing(10)

        week_bar = QFrame()
        week_bar.setObjectName("barNav")
        week_bar_layout = QHBoxLayout(week_bar)
        week_bar_layout.setContentsMargins(10, 6, 10, 6)
        week_bar_layout.setSpacing(8)

        btn_sem_ant = QPushButton("◀ Anterior")
        btn_sem_ant.setObjectName("secondaryBtn")
        btn_sem_ant.clicked.connect(self.semana_anterior)
        week_bar_layout.addWidget(btn_sem_ant)

        self.lbl_semana_titulo = QLabel("Semana: --")
        self.lbl_semana_titulo.setStyleSheet("font-size: 14px; font-weight: bold; color: #166260;")
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
        lbl_hint_sem = QLabel("💡 Clique em 'Ver Dia' para detalhar.")
        lbl_hint_sem.setStyleSheet("color: #64748b; font-size: 12px;")
        week_bar_layout.addWidget(lbl_hint_sem)

        layout_tab_semana.addWidget(week_bar)

        scroll_semana = QScrollArea()
        scroll_semana.setWidgetResizable(True)
        scroll_semana.setStyleSheet("background: transparent; border: none;")

        self.cards_semana_widget = QWidget()
        self.grid_semana = QGridLayout(self.cards_semana_widget)
        self.grid_semana.setSpacing(10)
        scroll_semana.setWidget(self.cards_semana_widget)
        layout_tab_semana.addWidget(scroll_semana)

        self.tabs.addTab(tab_semana, "📊 Panorama Semanal")

        # -------------------------------------------------------------
        # ABA 2: CONSULTAS DO DIA
        # -------------------------------------------------------------
        tab_dia = QWidget()
        layout_tab_dia = QVBoxLayout(tab_dia)
        layout_tab_dia.setSpacing(10)

        date_bar = QFrame()
        date_bar.setObjectName("barNav")
        date_layout = QHBoxLayout(date_bar)
        date_layout.setContentsMargins(10, 6, 10, 6)
        date_layout.setSpacing(8)

        btn_ant = QPushButton("◀ Anterior")
        btn_ant.setObjectName("secondaryBtn")
        btn_ant.clicked.connect(self.dia_anterior)
        date_layout.addWidget(btn_ant)

        self.dt_filtro = CustomDateEdit()
        self.dt_filtro.setDate(QDate.currentDate())
        self.dt_filtro.setFixedWidth(160)
        self.dt_filtro.dateChanged.connect(self.carregar_agenda_do_dia)
        date_layout.addWidget(self.dt_filtro)

        btn_prox = QPushButton("Próximo ▶")
        btn_prox.setObjectName("secondaryBtn")
        btn_prox.clicked.connect(self.dia_seguinte)
        date_layout.addWidget(btn_prox)

        btn_hoje = QPushButton("Hoje")
        btn_hoje.setObjectName("secondaryBtn")
        btn_hoje.clicked.connect(lambda: self.dt_filtro.setDate(QDate.currentDate()))
        date_layout.addWidget(btn_hoje)

        date_layout.addStretch()

        self.lbl_resumo = QLabel("Total: 0 | Confirmadas: 0 | Realizadas: 0")
        self.lbl_resumo.setStyleSheet("font-weight: bold; color: #166260; font-size: 13px;")
        date_layout.addWidget(self.lbl_resumo)

        layout_tab_dia.addWidget(date_bar)

        self.table_agenda = QTableWidget()
        self.table_agenda.setColumnCount(6)
        self.table_agenda.setHorizontalHeaderLabels(["Horário", "Paciente", "Telefone", "Procedimento", "Status", "Observações"])
        self.table_agenda.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_agenda.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_agenda.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_agenda.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_agenda.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_agenda.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table_agenda.setAlternatingRowColors(True)
        self.table_agenda.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_agenda.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_agenda.setStyleSheet("""
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
        layout_tab_dia.addWidget(self.table_agenda)

        # Botões Inferiores Reestruturados (sem corte de texto)
        agenda_bottom = QHBoxLayout()
        agenda_bottom.setSpacing(6)

        btn_confirmar = QPushButton("✓ Confirmado")
        btn_confirmar.setObjectName("secondaryBtn")
        btn_confirmar.clicked.connect(lambda: self.alterar_status_selecionado("Confirmado"))
        agenda_bottom.addWidget(btn_confirmar)

        btn_realizado = QPushButton("🦷 Realizado")
        btn_realizado.setObjectName("secondaryBtn")
        btn_realizado.clicked.connect(lambda: self.alterar_status_selecionado("Realizado"))
        agenda_bottom.addWidget(btn_realizado)

        btn_remarcar = QPushButton("🔄 Remarcado")
        btn_remarcar.setObjectName("secondaryBtn")
        btn_remarcar.clicked.connect(lambda: self.alterar_status_selecionado("Remarcado"))
        agenda_bottom.addWidget(btn_remarcar)

        btn_falta = QPushButton("✖ Cancelado")
        btn_falta.setObjectName("secondaryBtn")
        btn_falta.clicked.connect(lambda: self.alterar_status_selecionado("Cancelado"))
        agenda_bottom.addWidget(btn_falta)

        agenda_bottom.addStretch()

        btn_zap_confirmar = QPushButton("📲 WhatsApp")
        btn_zap_confirmar.setObjectName("whatsappBtn")
        btn_zap_confirmar.clicked.connect(self.enviar_confirmacao_whatsapp)
        agenda_bottom.addWidget(btn_zap_confirmar)

        btn_excluir_app = QPushButton("Excluir")
        btn_excluir_app.setObjectName("dangerBtn")
        btn_excluir_app.clicked.connect(self.excluir_agendamento_selecionado)
        agenda_bottom.addWidget(btn_excluir_app)

        layout_tab_dia.addLayout(agenda_bottom)
        self.tabs.addTab(tab_dia, "📆 Visão do Dia")

        # -------------------------------------------------------------
        # ABA 3: RETORNO DE 6 MESES
        # -------------------------------------------------------------
        tab_retorno = QWidget()
        layout_tab_retorno = QVBoxLayout(tab_retorno)
        layout_tab_retorno.setSpacing(10)

        banner = QFrame()
        banner.setStyleSheet("background-color: #f0fdfa; border-radius: 8px; border: 1px solid #ccfbf1; padding: 10px;")
        banner_layout = QHBoxLayout(banner)
        banner_layout.setSpacing(12)

        lbl_icone_zap = QLabel("🔔")
        lbl_icone_zap.setStyleSheet("font-size: 24px;")
        banner_layout.addWidget(lbl_icone_zap)

        banner_text = QLabel(
            "<b>Pacientes para Retorno Semestral (6 meses da última visita):</b><br>"
            "Lista automática de quem não consulta há mais de 180 dias e não possui agendamento futuro. "
            "Clique no botão verde para abrir o WhatsApp com mensagem acolhedora pré-formatada."
        )
        banner_text.setWordWrap(True)
        banner_text.setStyleSheet("color: #115e59; font-size: 13px;")
        banner_layout.addWidget(banner_text, stretch=1)

        self.btn_atualizar_retorno = QPushButton("🔄 Atualizar Lista")
        self.btn_atualizar_retorno.setObjectName("secondaryBtn")
        self.btn_atualizar_retorno.clicked.connect(self.carregar_lembretes_retorno)
        banner_layout.addWidget(self.btn_atualizar_retorno)

        layout_tab_retorno.addWidget(banner)

        self.table_retorno = QTableWidget()
        self.table_retorno.setColumnCount(5)
        self.table_retorno.setHorizontalHeaderLabels(["ID", "Paciente", "Telefone / WhatsApp", "Última Consulta", "Tempo Decorrido"])
        self.table_retorno.setColumnHidden(0, True)
        self.table_retorno.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_retorno.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_retorno.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_retorno.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_retorno.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_retorno.setAlternatingRowColors(True)
        self.table_retorno.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_retorno.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_retorno.setStyleSheet("""
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
                padding: 7px;
            }
        """)
        layout_tab_retorno.addWidget(self.table_retorno)

        retorno_bottom = QHBoxLayout()
        retorno_bottom.addStretch()

        btn_agendar_retorno = QPushButton("📅 Agendar Retorno")
        btn_agendar_retorno.setObjectName("primaryBtn")
        btn_agendar_retorno.clicked.connect(self.agendar_para_paciente_retorno)
        retorno_bottom.addWidget(btn_agendar_retorno)

        btn_chamar_zap = QPushButton("📲 Enviar Mensagem de Retorno")
        btn_chamar_zap.setObjectName("whatsappBtn")
        btn_chamar_zap.clicked.connect(self.enviar_retorno_whatsapp)
        retorno_bottom.addWidget(btn_chamar_zap)

        layout_tab_retorno.addLayout(retorno_bottom)
        self.tabs.addTab(tab_retorno, "🔔 Lembretes de Retorno (6 Meses)")

        # ---------------------------------------------------------
        # ABA 4: ACOMPANHAMENTO PÓS-OPERATÓRIO (D+1 / D+2)
        # ---------------------------------------------------------
        tab_pos_op = QWidget()
        layout_pos_op = QVBoxLayout(tab_pos_op)
        layout_pos_op.setContentsMargins(14, 14, 14, 14)
        layout_pos_op.setSpacing(12)

        banner_pos = QFrame()
        banner_pos.setStyleSheet("background-color: #f0fdfa; border: 1px solid #99f6e4; border-radius: 8px; padding: 12px;")
        b_lay_pos = QVBoxLayout(banner_pos)
        b_lay_pos.setSpacing(4)
        lbl_b_pos_tit = QLabel("🩺 Acompanhamento Humanizado Pós-Operatório (D+1)")
        lbl_b_pos_tit.setStyleSheet("font-size: 15px; font-weight: bold; color: #0f766e;")
        lbl_b_pos_sub = QLabel("Lista pacientes que realizaram consultas e procedimentos cirúrgicos ou invasivos nos últimos dias para contato preventivo e acolhimento via WhatsApp.")
        lbl_b_pos_sub.setStyleSheet("font-size: 12px; color: #475569;")
        b_lay_pos.addWidget(lbl_b_pos_tit)
        b_lay_pos.addWidget(lbl_b_pos_sub)
        layout_pos_op.addWidget(banner_pos)

        self.table_pos_op = QTableWidget()
        self.table_pos_op.setColumnCount(5)
        self.table_pos_op.setHorizontalHeaderLabels(["ID", "Paciente", "Telefone", "Data Atendimento", "Procedimento Realizado"])
        self.table_pos_op.setColumnHidden(0, True)
        self.table_pos_op.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_pos_op.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_pos_op.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_pos_op.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table_pos_op.setAlternatingRowColors(True)
        self.table_pos_op.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_pos_op.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_pos_op.setStyleSheet("""
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
            QTableWidget::item { padding: 7px; }
        """)
        layout_pos_op.addWidget(self.table_pos_op)

        pos_bottom = QHBoxLayout()
        pos_bottom.addStretch()
        btn_zap_pos = QPushButton("📲 Enviar Mensagem Pós-Operatória (WhatsApp)")
        btn_zap_pos.setObjectName("whatsappBtn")
        btn_zap_pos.clicked.connect(self.enviar_pos_operatorio_whatsapp)
        pos_bottom.addWidget(btn_zap_pos)
        layout_pos_op.addLayout(pos_bottom)

        self.tabs.addTab(tab_pos_op, "🩺 Pós-Operatório (D+1)")

        # ---------------------------------------------------------
        # ABA 5: ANIVERSARIANTES E FELICITAÇÕES
        # ---------------------------------------------------------
        tab_niver = QWidget()
        layout_niver = QVBoxLayout(tab_niver)
        layout_niver.setContentsMargins(14, 14, 14, 14)
        layout_niver.setSpacing(12)

        banner_niver = QFrame()
        banner_niver.setStyleSheet("background-color: #fdf4ff; border: 1px solid #f0abfc; border-radius: 8px; padding: 12px;")
        b_lay_niv = QHBoxLayout(banner_niver)
        b_v = QVBoxLayout()
        b_v.setSpacing(4)
        lbl_b_niv_tit = QLabel("🎉 Central de Felicitações e Aniversariantes")
        lbl_b_niv_tit.setStyleSheet("font-size: 15px; font-weight: bold; color: #a21caf;")
        lbl_b_niv_sub = QLabel("Fidelize pacientes enviando mensagens de carinho e felicitações com um clique.")
        lbl_b_niv_sub.setStyleSheet("font-size: 12px; color: #701a75;")
        b_v.addWidget(lbl_b_niv_tit)
        b_v.addWidget(lbl_b_niv_sub)
        b_lay_niv.addLayout(b_v)
        b_lay_niv.addStretch()

        self.chk_niver_hoje = QCheckBox("Apenas Aniversariantes de Hoje")
        self.chk_niver_hoje.setChecked(False)
        self.chk_niver_hoje.setStyleSheet("font-weight: 600; color: #a21caf;")
        self.chk_niver_hoje.toggled.connect(self.carregar_aniversariantes)
        b_lay_niv.addWidget(self.chk_niver_hoje)

        layout_niver.addWidget(banner_niver)

        self.table_niver = QTableWidget()
        self.table_niver.setColumnCount(5)
        self.table_niver.setHorizontalHeaderLabels(["ID", "Paciente", "Dia / Mês", "Idade", "Telefone"])
        self.table_niver.setColumnHidden(0, True)
        self.table_niver.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_niver.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_niver.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_niver.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_niver.setAlternatingRowColors(True)
        self.table_niver.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_niver.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_niver.setStyleSheet("""
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
            QTableWidget::item { padding: 7px; }
        """)
        layout_niver.addWidget(self.table_niver)

        niver_bottom = QHBoxLayout()
        niver_bottom.addStretch()
        btn_zap_niver = QPushButton("🎂 Enviar Felicitações (WhatsApp)")
        btn_zap_niver.setObjectName("whatsappBtn")
        btn_zap_niver.clicked.connect(self.enviar_aniversario_whatsapp)
        niver_bottom.addWidget(btn_zap_niver)
        layout_niver.addLayout(niver_bottom)

        self.tabs.addTab(tab_niver, "🎉 Aniversariantes")

        self.tabs.currentChanged.connect(self.ao_mudar_aba)
        layout.addWidget(self.tabs)

    def ao_mudar_aba(self, indice: int):
        """Atualiza a aba correspondente sempre que o usuário alternar entre as abas."""
        if indice == 0:
            self.carregar_agenda_semanal()
        elif indice == 1:
            self.carregar_agenda_do_dia()
        elif indice == 2:
            self.carregar_lembretes_retorno()
        elif indice == 3:
            self.carregar_pos_operatorio()
        elif indice == 4:
            self.carregar_aniversariantes()

    # -------------------------------------------------------------
    # MÉTODOS DA VISÃO SEMANAL
    # -------------------------------------------------------------

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
            card.setObjectName(f"schCard_{i}")
            border_color = "#2ca5a9" if eh_hoje else "#cbd5e1"
            bg_color = "#f0fdfa" if eh_hoje else "#ffffff"
            card.setStyleSheet(f"""
                QFrame#schCard_{i} {{
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

            consultas_dia = list_appointments_by_date(dia_str)
            if consultas_dia:
                lbl_qtd = QLabel(f"<b>{len(consultas_dia)} consulta(s)</b> agendada(s)")
                lbl_qtd.setStyleSheet("color: #0f766e; font-size: 12px;")
                card_layout.addWidget(lbl_qtd)

                for c in consultas_dia[:4]:
                    status_cor = "#059669" if c["status"] == "Confirmado" else ("#0d9488" if c["status"] == "Realizado" else ("#b45309" if c["status"] == "Remarcado" else "#0284c7"))
                    item_txt = f"• <b>{c['horario']}</b> - {c['paciente_nome'].split()[0]} ({c['procedimento'] or 'Consulta'})"
                    lbl_item = QLabel(item_txt)
                    lbl_item.setStyleSheet(f"color: {status_cor}; font-size: 11px;")
                    card_layout.addWidget(lbl_item)

                if len(consultas_dia) > 4:
                    lbl_mais = QLabel(f"+ {len(consultas_dia) - 4} consulta(s)...")
                    lbl_mais.setStyleSheet("color: #64748b; font-size: 11px; font-style: italic;")
                    card_layout.addWidget(lbl_mais)
            else:
                lbl_vazio = QLabel("Sem consultas marcadas")
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
    # MÉTODOS DA VISÃO DIÁRIA
    # -------------------------------------------------------------

    def get_data_selecionada_str(self) -> str:
        qdate = self.dt_filtro.date()
        return f"{qdate.year():04d}-{qdate.month():02d}-{qdate.day():02d}"

    def dia_anterior(self):
        self.dt_filtro.setDate(self.dt_filtro.date().addDays(-1))

    def dia_seguinte(self):
        self.dt_filtro.setDate(self.dt_filtro.date().addDays(1))

    def carregar_agenda_do_dia(self):
        data_str = self.get_data_selecionada_str()
        consultas = list_appointments_by_date(data_str)
        self.table_agenda.setRowCount(len(consultas))

        confirmados = 0
        realizados = 0

        for row_idx, c in enumerate(consultas):
            item_hora = QTableWidgetItem(c["horario"])
            item_hora.setTextAlignment(Qt.AlignCenter)
            item_hora.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table_agenda.setItem(row_idx, 0, item_hora)

            item_nome = QTableWidgetItem(c["paciente_nome"])
            item_nome.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table_agenda.setItem(row_idx, 1, item_nome)

            item_tel = QTableWidgetItem(c["paciente_telefone"] or "-")
            item_tel.setTextAlignment(Qt.AlignCenter)
            self.table_agenda.setItem(row_idx, 2, item_tel)

            item_proc = QTableWidgetItem(c["procedimento"] or "Geral")
            self.table_agenda.setItem(row_idx, 3, item_proc)

            status = c["status"]
            item_status = QTableWidgetItem(status)
            item_status.setTextAlignment(Qt.AlignCenter)
            item_status.setFont(QFont("Segoe UI", 9, QFont.Bold))

            if status == "Confirmado":
                item_status.setForeground(QColor("#059669"))
                confirmados += 1
            elif status == "Realizado":
                item_status.setForeground(QColor("#0d9488"))
                realizados += 1
            elif status == "Remarcado":
                item_status.setForeground(QColor("#b45309"))
            elif status in ("Cancelado", "Faltou"):
                item_status.setForeground(QColor("#dc2626"))
            else:
                item_status.setForeground(QColor("#0284c7"))

            self.table_agenda.setItem(row_idx, 4, item_status)
            self.table_agenda.setItem(row_idx, 5, QTableWidgetItem(c["observacoes"] or ""))

            self.table_agenda.item(row_idx, 0).setData(Qt.UserRole, c)

        self.lbl_resumo.setText(
            f"Total: {len(consultas)}  |  "
            f"✓ Confirmadas: {confirmados}  |  "
            f"🦷 Realizadas: {realizados}"
        )

    def get_selected_appointment(self) -> dict:
        selected = self.table_agenda.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione uma consulta na tabela da agenda.")
            return None
        row = selected[0].row()
        return self.table_agenda.item(row, 0).data(Qt.UserRole)

    def abrir_novo_agendamento(self, data_previa: Optional[date] = None):
        data_ini = QDate(data_previa.year, data_previa.month, data_previa.day) if data_previa else self.dt_filtro.date()
        dialog = NewAppointmentDialog(self.current_user, initial_date=data_ini, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.carregar_agenda_semanal()
            self.carregar_agenda_do_dia()
            self.carregar_lembretes_retorno()

    # -------------------------------------------------------------
    # MÉTODOS DO ACOMPANHAMENTO PÓS-OPERATÓRIO (D+1)
    # -------------------------------------------------------------

    def carregar_pos_operatorio(self):
        pacientes = get_post_operative_patients(dias_max=2)
        self.table_pos_op.setRowCount(len(pacientes))

        for row_idx, r in enumerate(pacientes):
            item_id = QTableWidgetItem(str(r["patient_id"]))
            item_id.setTextAlignment(Qt.AlignCenter)
            self.table_pos_op.setItem(row_idx, 0, item_id)

            item_nome = QTableWidgetItem(r["nome"])
            item_nome.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table_pos_op.setItem(row_idx, 1, item_nome)

            item_tel = QTableWidgetItem(r["telefone"] or "Sem telefone")
            item_tel.setTextAlignment(Qt.AlignCenter)
            self.table_pos_op.setItem(row_idx, 2, item_tel)

            item_dt = QTableWidgetItem(f"{r['data_atendimento']} ({r['dias_passados']}d atrás)")
            item_dt.setTextAlignment(Qt.AlignCenter)
            item_dt.setForeground(QColor("#0f766e"))
            self.table_pos_op.setItem(row_idx, 3, item_dt)

            item_proc = QTableWidgetItem(r["procedimento"])
            item_proc.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table_pos_op.setItem(row_idx, 4, item_proc)

            self.table_pos_op.item(row_idx, 0).setData(Qt.UserRole, r)

    def enviar_pos_operatorio_whatsapp(self):
        selected = self.table_pos_op.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione um paciente na tabela de pós-operatório.")
            return
        row = selected[0].row()
        p = self.table_pos_op.item(row, 0).data(Qt.UserRole)
        if not p:
            return

        tel = p.get("telefone")
        if not tel:
            QMessageBox.warning(self, "Aviso", f"O paciente '{p['nome']}' não possui telefone cadastrado.")
            return

        msg = build_post_operative_message(p["nome"], p["procedimento"])
        preview_dialog = SendWhatsAppPreviewDialog(tel, msg, parent=self)
        preview_dialog.exec()

    # -------------------------------------------------------------
    # MÉTODOS DA CENTRAL DE ANIVERSARIANTES
    # -------------------------------------------------------------

    def carregar_aniversariantes(self):
        apenas_hoje = self.chk_niver_hoje.isChecked()
        aniversariantes = get_birthday_patients(apenas_hoje=apenas_hoje)
        self.table_niver.setRowCount(len(aniversariantes))

        for row_idx, r in enumerate(aniversariantes):
            item_id = QTableWidgetItem(str(r["patient_id"]))
            item_id.setTextAlignment(Qt.AlignCenter)
            self.table_niver.setItem(row_idx, 0, item_id)

            nome_txt = r["nome"]
            if r["e_hoje"]:
                nome_txt = f"🎂 {nome_txt} (HOJE!)"

            item_nome = QTableWidgetItem(nome_txt)
            item_nome.setFont(QFont("Segoe UI", 10, QFont.Bold))
            if r["e_hoje"]:
                item_nome.setForeground(QColor("#a21caf"))
            self.table_niver.setItem(row_idx, 1, item_nome)

            item_dia = QTableWidgetItem(r["dia_mes"])
            item_dia.setTextAlignment(Qt.AlignCenter)
            self.table_niver.setItem(row_idx, 2, item_dia)

            item_idade = QTableWidgetItem(f"{r['idade']} anos")
            item_idade.setTextAlignment(Qt.AlignCenter)
            self.table_niver.setItem(row_idx, 3, item_idade)

            item_tel = QTableWidgetItem(r["telefone"] or "Sem telefone")
            item_tel.setTextAlignment(Qt.AlignCenter)
            self.table_niver.setItem(row_idx, 4, item_tel)

            self.table_niver.item(row_idx, 0).setData(Qt.UserRole, r)

    def enviar_aniversario_whatsapp(self):
        selected = self.table_niver.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione um paciente na tabela de aniversariantes.")
            return
        row = selected[0].row()
        p = self.table_niver.item(row, 0).data(Qt.UserRole)
        if not p:
            return

        tel = p.get("telefone")
        if not tel:
            QMessageBox.warning(self, "Aviso", f"O paciente '{p['nome']}' não possui telefone cadastrado.")
            return

        msg = build_birthday_message(p["nome"])
        preview_dialog = SendWhatsAppPreviewDialog(tel, msg, parent=self)
        preview_dialog.exec()

    def alterar_status_selecionado(self, novo_status: str):
        app = self.get_selected_appointment()
        if not app:
            return

        ok, msg = update_appointment_status(
            app["id"], novo_status,
            self.current_user["id"], self.current_user["nome"]
        )
        if ok:
            self.carregar_agenda_semanal()
            self.carregar_agenda_do_dia()
            self.carregar_lembretes_retorno()
            self.carregar_pos_operatorio()

            # Dispara automação de conclusão inteligente (Workflow 360°)
            if novo_status == "Realizado":
                dlg_concl = AppointmentConclusionDialog(app, self.current_user, parent=self)
                dlg_concl.exec()
        else:
            QMessageBox.critical(self, "Erro", msg)

    def excluir_agendamento_selecionado(self):
        app = self.get_selected_appointment()
        if not app:
            return

        msg = f"Deseja realmente excluir o agendamento de '{app['paciente_nome']}' ({app['horario']})?"
        if perguntar_sim_nao(self, "Confirmação de Exclusão", msg):
            ok, msg_res = delete_appointment(app["id"], self.current_user["id"], self.current_user["nome"])
            if ok:
                self.carregar_agenda_semanal()
                self.carregar_agenda_do_dia()
            else:
                QMessageBox.critical(self, "Erro", msg_res)

    def enviar_confirmacao_whatsapp(self):
        app = self.get_selected_appointment()
        if not app:
            return

        tel = app.get("paciente_telefone")
        if not tel:
            QMessageBox.warning(self, "Aviso", f"O paciente '{app['paciente_nome']}' não possui telefone cadastrado.")
            return

        qdate = self.dt_filtro.date()
        data_formatada = f"{qdate.day():02d}/{qdate.month():02d}/{qdate.year():04d}"
        msg = build_confirmation_message(app["paciente_nome"], data_formatada, app["horario"])

        preview_dialog = SendWhatsAppPreviewDialog(tel, msg, parent=self)
        preview_dialog.exec()

    def abrir_configuracoes_whatsapp(self):
        dialog = WhatsAppSettingsDialog(self)
        dialog.exec()

    # -------------------------------------------------------------
    # MÉTODOS DOS LEMBRETES DE RETORNO (6 MESES)
    # -------------------------------------------------------------

    def carregar_lembretes_retorno(self):
        lembretes = get_return_reminders(dias_minimos=180)
        self.table_retorno.setRowCount(len(lembretes))

        for row_idx, r in enumerate(lembretes):
            item_id = QTableWidgetItem(str(r["patient_id"]))
            item_id.setTextAlignment(Qt.AlignCenter)
            self.table_retorno.setItem(row_idx, 0, item_id)

            item_nome = QTableWidgetItem(r["nome"])
            item_nome.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table_retorno.setItem(row_idx, 1, item_nome)

            item_tel = QTableWidgetItem(r["telefone"] or "Sem telefone")
            item_tel.setTextAlignment(Qt.AlignCenter)
            self.table_retorno.setItem(row_idx, 2, item_tel)

            item_data = QTableWidgetItem(r["ultima_data_formatada"])
            item_data.setTextAlignment(Qt.AlignCenter)
            self.table_retorno.setItem(row_idx, 3, item_data)

            tempo_txt = f"{r['dias_decorridos']} dias"
            item_tempo = QTableWidgetItem(tempo_txt)
            item_tempo.setTextAlignment(Qt.AlignCenter)
            item_tempo.setForeground(QColor("#b45309"))
            item_tempo.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table_retorno.setItem(row_idx, 4, item_tempo)

            self.table_retorno.item(row_idx, 0).setData(Qt.UserRole, r)

        if hasattr(self, 'btn_atualizar_retorno'):
            self.btn_atualizar_retorno.setText(f"✓ Atualizado ({len(lembretes)})")

    def get_selected_retorno_patient(self) -> dict:
        selected = self.table_retorno.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione um paciente na tabela de retornos.")
            return None
        row = selected[0].row()
        return self.table_retorno.item(row, 0).data(Qt.UserRole)

    def enviar_retorno_whatsapp(self):
        p = self.get_selected_retorno_patient()
        if not p:
            return

        tel = p.get("telefone")
        if not tel:
            QMessageBox.warning(self, "Aviso", f"O paciente '{p['nome']}' não possui telefone cadastrado.")
            return

        msg = build_return_message(p["nome"], p["ultima_data_formatada"])
        preview_dialog = SendWhatsAppPreviewDialog(tel, msg, parent=self)
        preview_dialog.exec()

    def agendar_para_paciente_retorno(self):
        p = self.get_selected_retorno_patient()
        if not p:
            return

        dialog = NewAppointmentDialog(self.current_user, preselected_patient_id=p["patient_id"], parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.carregar_agenda_semanal()
            self.carregar_agenda_do_dia()
            self.carregar_lembretes_retorno()

    # -------------------------------------------------------------
    # MÉTODOS DO ACOMPANHAMENTO PÓS-OPERATÓRIO (D+1)
    # -------------------------------------------------------------

    def carregar_pos_operatorio(self):
        pacientes = get_post_operative_patients(dias_max=2)
        self.table_pos_op.setRowCount(len(pacientes))

        for row_idx, r in enumerate(pacientes):
            item_id = QTableWidgetItem(str(r["patient_id"]))
            item_id.setTextAlignment(Qt.AlignCenter)
            self.table_pos_op.setItem(row_idx, 0, item_id)

            item_nome = QTableWidgetItem(r["nome"])
            item_nome.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table_pos_op.setItem(row_idx, 1, item_nome)

            item_tel = QTableWidgetItem(r["telefone"] or "Sem telefone")
            item_tel.setTextAlignment(Qt.AlignCenter)
            self.table_pos_op.setItem(row_idx, 2, item_tel)

            item_dt = QTableWidgetItem(f"{r['data_atendimento']} ({r['dias_passados']}d atrás)")
            item_dt.setTextAlignment(Qt.AlignCenter)
            item_dt.setForeground(QColor("#0f766e"))
            self.table_pos_op.setItem(row_idx, 3, item_dt)

            item_proc = QTableWidgetItem(r["procedimento"])
            item_proc.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table_pos_op.setItem(row_idx, 4, item_proc)

            self.table_pos_op.item(row_idx, 0).setData(Qt.UserRole, r)

    def enviar_pos_operatorio_whatsapp(self):
        selected = self.table_pos_op.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione um paciente na tabela de pós-operatório.")
            return
        row = selected[0].row()
        p = self.table_pos_op.item(row, 0).data(Qt.UserRole)
        if not p:
            return

        tel = p.get("telefone")
        if not tel:
            QMessageBox.warning(self, "Aviso", f"O paciente '{p['nome']}' não possui telefone cadastrado.")
            return

        msg = build_post_operative_message(p["nome"], p["procedimento"])
        preview_dialog = SendWhatsAppPreviewDialog(tel, msg, parent=self)
        preview_dialog.exec()

    # -------------------------------------------------------------
    # MÉTODOS DA CENTRAL DE ANIVERSARIANTES
    # -------------------------------------------------------------

    def carregar_aniversariantes(self):
        apenas_hoje = self.chk_niver_hoje.isChecked()
        aniversariantes = get_birthday_patients(apenas_hoje=apenas_hoje)
        self.table_niver.setRowCount(len(aniversariantes))

        for row_idx, r in enumerate(aniversariantes):
            item_id = QTableWidgetItem(str(r["patient_id"]))
            item_id.setTextAlignment(Qt.AlignCenter)
            self.table_niver.setItem(row_idx, 0, item_id)

            nome_txt = r["nome"]
            if r["e_hoje"]:
                nome_txt = f"🎂 {nome_txt} (HOJE!)"

            item_nome = QTableWidgetItem(nome_txt)
            item_nome.setFont(QFont("Segoe UI", 10, QFont.Bold))
            if r["e_hoje"]:
                item_nome.setForeground(QColor("#a21caf"))
            self.table_niver.setItem(row_idx, 1, item_nome)

            item_dia = QTableWidgetItem(r["dia_mes"])
            item_dia.setTextAlignment(Qt.AlignCenter)
            self.table_niver.setItem(row_idx, 2, item_dia)

            item_idade = QTableWidgetItem(f"{r['idade']} anos")
            item_idade.setTextAlignment(Qt.AlignCenter)
            self.table_niver.setItem(row_idx, 3, item_idade)

            item_tel = QTableWidgetItem(r["telefone"] or "Sem telefone")
            item_tel.setTextAlignment(Qt.AlignCenter)
            self.table_niver.setItem(row_idx, 4, item_tel)

            self.table_niver.item(row_idx, 0).setData(Qt.UserRole, r)

    def enviar_aniversario_whatsapp(self):
        selected = self.table_niver.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione um paciente na tabela de aniversariantes.")
            return
        row = selected[0].row()
        p = self.table_niver.item(row, 0).data(Qt.UserRole)
        if not p:
            return

        tel = p.get("telefone")
        if not tel:
            QMessageBox.warning(self, "Aviso", f"O paciente '{p['nome']}' não possui telefone cadastrado.")
            return

        msg = build_birthday_message(p["nome"])
        preview_dialog = SendWhatsAppPreviewDialog(tel, msg, parent=self)
        preview_dialog.exec()
