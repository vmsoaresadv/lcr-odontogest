from typing import Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QCheckBox, QLineEdit, QTextEdit, QFrame,
    QMessageBox, QScrollArea, QGroupBox
)
from PySide6.QtCore import Qt, Signal

from services.patient_service import get_patient_anamnese, save_patient_anamnese


class AnamneseWidget(QWidget):
    """Componente completo de Anamnese Odontológica Clínica."""
    anamnese_atualizada = Signal(dict)

    def __init__(self, patient_id: int, current_user: dict, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.current_user = current_user
        self.init_ui()
        self.carregar_anamnese()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Barra de Ações do Topo
        top_bar = QHBoxLayout()
        lbl_titulo = QLabel("Questionário e Histórico de Saúde Odontológica")
        lbl_titulo.setStyleSheet("font-size: 15px; font-weight: bold; color: #0f766e;")
        top_bar.addWidget(lbl_titulo)
        top_bar.addStretch()

        self.btn_salvar_top = QPushButton("Salvar Anamnese")
        self.btn_salvar_top.setStyleSheet("""
            QPushButton {
                background-color: #0f766e;
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                padding: 7px 18px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #115e59;
            }
        """)
        self.btn_salvar_top.clicked.connect(self.salvar_anamnese)
        top_bar.addWidget(self.btn_salvar_top)
        main_layout.addLayout(top_bar)

        # Scroll Area com todos os campos
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; background-color: #ffffff;")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # 1. QUEIXA PRINCIPAL & MOTIVO DA CONSULTA
        box_queixa = QGroupBox("1. Queixa Principal e Motivo da Consulta")
        box_queixa.setStyleSheet(self._estilo_box("#0f766e"))
        v_queixa = QVBoxLayout(box_queixa)
        v_queixa.setSpacing(8)

        v_queixa.addWidget(QLabel("Qual o principal motivo da visita ou tratamento procurado?"))
        self.txt_queixa = QLineEdit()
        self.txt_queixa.setPlaceholderText("Ex: Dor ao mastigar no lado direito, restauração solta, limpeza/avaliação, dor espontânea...")
        v_queixa.addWidget(self.txt_queixa)

        v_queixa.addWidget(QLabel("Histórico do início do problema ou sintomas:"))
        self.txt_hist_atual = QLineEdit()
        self.txt_hist_atual.setPlaceholderText("Ex: Início há 1 semana, sensibilidade a alimentos frios/doces, sem sangramento...")
        v_queixa.addWidget(self.txt_hist_atual)
        layout.addWidget(box_queixa)

        # 2. CONDIÇÕES MÉDICAS E DOENÇAS SISTÊMICAS
        box_doencas = QGroupBox("2. Histórico Médico e Doenças Sistêmicas")
        box_doencas.setStyleSheet(self._estilo_box("#b91c1c"))
        v_doencas = QVBoxLayout(box_doencas)

        lbl_aviso = QLabel("Atenção: Marque as condições que o paciente apresenta (gera alertas na tela e prontuário):")
        lbl_aviso.setStyleSheet("color: #b91c1c; font-size: 11px; font-weight: 600; margin-bottom: 4px;")
        v_doencas.addWidget(lbl_aviso)

        grid_doencas = QGridLayout()
        grid_doencas.setSpacing(10)

        self.chk_hipertensao = QCheckBox("Hipertensão Arterial (Pressão Alta)")
        self.chk_diabetes = QCheckBox("Diabetes Mellitus")
        self.chk_cardiopatia = QCheckBox("Cardiopatias / Problemas Cardíacos")
        self.chk_coagulacao = QCheckBox("Distúrbio de Coagulação / Hemorragias")
        self.chk_renal_hepatica = QCheckBox("Doença Renal ou Hepática")
        self.chk_gestante = QCheckBox("Gestante ou Lactante")
        self.chk_fumante = QCheckBox("Fumante / Uso de Tabaco")
        self.chk_bruxismo = QCheckBox("Bruxismo / Apertamento Dental")

        for chk in [
            self.chk_hipertensao, self.chk_diabetes, self.chk_cardiopatia,
            self.chk_coagulacao, self.chk_renal_hepatica, self.chk_gestante,
            self.chk_fumante, self.chk_bruxismo
        ]:
            chk.setStyleSheet("font-size: 12px; font-weight: 600; color: #1e293b;")

        grid_doencas.addWidget(self.chk_hipertensao, 0, 0)
        grid_doencas.addWidget(self.chk_diabetes, 0, 1)
        grid_doencas.addWidget(self.chk_cardiopatia, 1, 0)
        grid_doencas.addWidget(self.chk_coagulacao, 1, 1)
        grid_doencas.addWidget(self.chk_renal_hepatica, 2, 0)
        grid_doencas.addWidget(self.chk_gestante, 2, 1)
        grid_doencas.addWidget(self.chk_fumante, 3, 0)
        grid_doencas.addWidget(self.chk_bruxismo, 3, 1)

        v_doencas.addLayout(grid_doencas)
        layout.addWidget(box_doencas)

        # 3. ALERGIAS E RESTRIÇÕES
        box_alergias = QGroupBox("3. Alergias e Restrições Médicas")
        box_alergias.setStyleSheet(self._estilo_box("#c2410c"))
        v_alergias = QVBoxLayout(box_alergias)
        v_alergias.setSpacing(8)

        v_alergias.addWidget(QLabel("Alergias a Medicamentos (Penicilina, Dipirona, AINEs, Anestésicos locais...):"))
        self.txt_alergias_med = QLineEdit()
        self.txt_alergias_med.setStyleSheet("border-color: #fca5a5; background-color: #fffaf0;")
        self.txt_alergias_med.setPlaceholderText("Ex: Alérgico a Dipirona e Amoxicilina (ou deixe em branco se não houver)")
        v_alergias.addWidget(self.txt_alergias_med)

        self.chk_latex = QCheckBox("Alergia a Látex (Requer luvas de nitrilo / biossegurança especial)")
        self.chk_latex.setStyleSheet("font-size: 12px; font-weight: 600; color: #9a3412;")
        v_alergias.addWidget(self.chk_latex)
        layout.addWidget(box_alergias)

        # 4. MEDICAMENTOS DE USO CONTÍNUO & CIRURGIAS
        box_meds = QGroupBox("4. Medicamentos de Uso Contínuo e Cirurgias")
        box_meds.setStyleSheet(self._estilo_box("#0369a1"))
        v_meds = QVBoxLayout(box_meds)
        v_meds.setSpacing(8)

        v_meds.addWidget(QLabel("Medicamentos que o paciente toma regularmente (Anticoagulantes, Bifosfonatos, Insulina, etc.):"))
        self.txt_meds_uso = QLineEdit()
        self.txt_meds_uso.setPlaceholderText("Ex: Losartana 50mg, AAS 100mg diário, Metformina...")
        v_meds.addWidget(self.txt_meds_uso)

        v_meds.addWidget(QLabel("Histórico de cirurgias prévias ou internações hospitalares:"))
        self.txt_cirurgias = QLineEdit()
        self.txt_cirurgias.setPlaceholderText("Ex: Cirurgia cardíaca prévia, retirada de vesícula, apendicectomia...")
        v_meds.addWidget(self.txt_cirurgias)
        layout.addWidget(box_meds)

        # 5. OBSERVAÇÕES GERAIS
        box_obs = QGroupBox("5. Observações Clínicas Gerais e Conduta")
        box_obs.setStyleSheet(self._estilo_box("#475569"))
        v_obs = QVBoxLayout(box_obs)
        self.txt_observacoes = QTextEdit()
        self.txt_observacoes.setMinimumHeight(70)
        self.txt_observacoes.setPlaceholderText("Informações adicionais relevantes, cuidados especiais durante a anestesia ou recomendações da Dra. Lara...")
        v_obs.addWidget(self.txt_observacoes)
        layout.addWidget(box_obs)

        # Botão Salvar Rodapé
        btn_salvar_bottom = QPushButton("Salvar Anamnese do Paciente")
        btn_salvar_bottom.setStyleSheet("""
            QPushButton {
                background-color: #0f766e;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                padding: 10px 22px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #115e59;
            }
        """)
        btn_salvar_bottom.clicked.connect(self.salvar_anamnese)
        layout.addWidget(btn_salvar_bottom)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _estilo_box(self, cor: str) -> str:
        return f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 13px;
                color: {cor};
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 14px;
                background-color: #ffffff;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }}
        """

    def carregar_anamnese(self):
        dados = get_patient_anamnese(self.patient_id)
        self.txt_queixa.setText(dados.get("queixa_principal", ""))
        self.txt_hist_atual.setText(dados.get("historico_doenca_atual", ""))

        self.chk_hipertensao.setChecked(bool(dados.get("hipertensao")))
        self.chk_diabetes.setChecked(bool(dados.get("diabetes")))
        self.chk_cardiopatia.setChecked(bool(dados.get("cardiopatia")))
        self.chk_coagulacao.setChecked(bool(dados.get("problema_coagulacao")))
        self.chk_renal_hepatica.setChecked(bool(dados.get("doenca_renal_hepatica")))
        self.chk_gestante.setChecked(bool(dados.get("gestante_lactante")))
        self.chk_fumante.setChecked(bool(dados.get("fumante")))
        self.chk_bruxismo.setChecked(bool(dados.get("bruxismo")))

        self.txt_alergias_med.setText(dados.get("alergias_medicamentos", ""))
        self.chk_latex.setChecked(bool(dados.get("alergia_latex")))

        self.txt_meds_uso.setText(dados.get("medicamentos_uso", ""))
        self.txt_cirurgias.setText(dados.get("historico_cirurgico", ""))
        self.txt_observacoes.setPlainText(dados.get("observacoes", ""))

    def salvar_anamnese(self):
        dados = {
            "queixa_principal": self.txt_queixa.text(),
            "historico_doenca_atual": self.txt_hist_atual.text(),
            "hipertensao": self.chk_hipertensao.isChecked(),
            "diabetes": self.chk_diabetes.isChecked(),
            "cardiopatia": self.chk_cardiopatia.isChecked(),
            "problema_coagulacao": self.chk_coagulacao.isChecked(),
            "doenca_renal_hepatica": self.chk_renal_hepatica.isChecked(),
            "gestante_lactante": self.chk_gestante.isChecked(),
            "fumante": self.chk_fumante.isChecked(),
            "bruxismo": self.chk_bruxismo.isChecked(),
            "alergias_medicamentos": self.txt_alergias_med.text(),
            "alergia_latex": self.chk_latex.isChecked(),
            "medicamentos_uso": self.txt_meds_uso.text(),
            "historico_cirurgico": self.txt_cirurgias.text(),
            "observacoes": self.txt_observacoes.toPlainText()
        }

        ok, msg = save_patient_anamnese(
            self.patient_id, dados,
            self.current_user["id"], self.current_user["nome"]
        )
        if ok:
            QMessageBox.information(self, "Sucesso", "Anamnese odontológica salva com sucesso!")
            self.anamnese_atualizada.emit(dados)
        else:
            QMessageBox.critical(self, "Erro", msg)
