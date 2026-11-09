from typing import Dict, Optional, Callable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QComboBox, QCheckBox, QLineEdit, QFrame,
    QMessageBox, QScrollArea, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from services.patient_service import (
    DENTES_FDI_SUPERIORES, DENTES_FDI_INFERIORES,
    NOMES_DENTES, STATUS_DENTE_CORES,
    get_patient_odontograma, save_tooth_status, reset_odontograma
)


class ToothCard(QFrame):
    """Card interativo representando um dente individual no Odontograma."""
    clicked = Signal(int)

    def __init__(self, numero: int, parent=None):
        super().__init__(parent)
        self.numero = numero
        self.status = "higido"
        self.faces = ""
        self.observacoes = ""
        self.is_selected = False

        self.setFixedSize(52, 70)
        self.setCursor(Qt.PointingHandCursor)
        self.init_ui()
        self.atualizar_estilo()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 4, 2, 4)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignCenter)

        # Número do Dente (Padrão FDI)
        self.lbl_numero = QLabel(str(self.numero), self)
        self.lbl_numero.setAlignment(Qt.AlignCenter)
        self.lbl_numero.setStyleSheet("font-size: 13px; font-weight: bold; color: #0f172a;")
        layout.addWidget(self.lbl_numero)

        # Indicador visual do dente / ícone
        self.lbl_icone = QLabel("🦷", self)
        self.lbl_icone.setAlignment(Qt.AlignCenter)
        self.lbl_icone.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.lbl_icone)

        # Rótulo de status / faces
        self.lbl_status = QLabel("Hígido", self)
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("font-size: 9px; font-weight: 600; color: #065f46;")
        layout.addWidget(self.lbl_status)

    def set_dados(self, dados: dict):
        self.status = dados.get("status", "higido")
        self.faces = dados.get("faces", "")
        self.observacoes = dados.get("observacoes", "")
        self.atualizar_estilo()

    def set_selecionado(self, sel: bool):
        self.is_selected = sel
        self.atualizar_estilo()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.numero)
        super().mousePressEvent(event)

    def atualizar_estilo(self):
        cfg = STATUS_DENTE_CORES.get(self.status, STATUS_DENTE_CORES["higido"])
        cor_base = cfg["cor"]

        # Configurações visuais por status
        bgs = {
            "higido": "#f0fdf4",
            "carie": "#fef2f2",
            "restaurado": "#eff6ff",
            "canal": "#fffbeb",
            "protese": "#faf5ff",
            "implante": "#ecfeff",
            "ausente": "#f1f5f9"
        }
        bg = bgs.get(self.status, "#f8fafc")
        borda_cor = "#0f766e" if self.is_selected else cor_base
        borda_largura = "3px" if self.is_selected else "1.5px"

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: {borda_largura} solid {borda_cor};
                border-radius: 6px;
            }}
            QFrame:hover {{
                border: 2.5px solid #0d9488;
                background-color: #ffffff;
            }}
        """)

        # Texto do rótulo
        txt = cfg["nome"].split(" / ")[0]
        if self.faces:
            txt = f"{self.faces}"
        self.lbl_status.setText(txt[:8])
        self.lbl_status.setStyleSheet(f"font-size: 9px; font-weight: bold; color: {cor_base};")

        # Tooltip explicativo completo
        nome_completo = NOMES_DENTES.get(self.numero, f"Dente {self.numero}")
        faces_str = f" • Faces: {self.faces}" if self.faces else ""
        obs_str = f"\nObs: {self.observacoes}" if self.observacoes else ""
        self.setToolTip(f"Dente {self.numero} - {nome_completo}\nSituação: {cfg['nome']}{faces_str}{obs_str}")


class OdontogramaWidget(QWidget):
    """Componente visual e interativo completo do Odontograma Clínico FDI."""
    procedimento_solicitado = Signal(int, str)  # (numero_dente, procedimento_sugerido)

    def __init__(self, patient_id: int, current_user: dict, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.current_user = current_user
        self.dentes_cards: Dict[int, ToothCard] = {}
        self.dente_selecionado: Optional[int] = None

        self.init_ui()
        self.carregar_odontograma()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(14)

        # -------------------------------------------------------------
        # COLUNA ESQUERDA: MAPA ANATÔMICO DOS DENTES
        # -------------------------------------------------------------
        col_mapa = QVBoxLayout()
        col_mapa.setSpacing(10)

        # Resumo Estatístico Rápido
        self.bar_stats = QFrame(self)
        self.bar_stats.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 6px 12px;
            }
        """)
        h_stats = QHBoxLayout(self.bar_stats)
        h_stats.setContentsMargins(8, 6, 8, 6)

        self.lbl_stats = QLabel("Resumo: 32 Dentes mapeados", self.bar_stats)
        self.lbl_stats.setStyleSheet("font-size: 13px; font-weight: bold; color: #0f766e;")
        h_stats.addWidget(self.lbl_stats)
        h_stats.addStretch()

        btn_reset = QPushButton("↺ Restaurar Todos Hígidos", self.bar_stats)
        btn_reset.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #64748b;
                border: 1px solid #cbd5e1;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                color: #b91c1c;
                border-color: #fca5a5;
            }
        """)
        btn_reset.clicked.connect(self.ao_resetar_odontograma)
        h_stats.addWidget(btn_reset)
        col_mapa.addWidget(self.bar_stats)

        # Área de Rolagem do Odontograma
        scroll_arcadas = QScrollArea(self)
        scroll_arcadas.setWidgetResizable(True)
        scroll_arcadas.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; background-color: #ffffff;")

        content_arcadas = QWidget()
        layout_arcadas = QVBoxLayout(content_arcadas)
        layout_arcadas.setContentsMargins(12, 14, 12, 14)
        layout_arcadas.setSpacing(14)

        # --- ARCADA SUPERIOR ---
        box_sup = QGroupBox("Arcada Superior (Maxila)")
        box_sup.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                color: #0f766e;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 4px;
            }
        """)
        v_sup = QVBoxLayout(box_sup)
        v_sup.setContentsMargins(8, 12, 8, 8)

        row_sup = QHBoxLayout()
        row_sup.setSpacing(3)
        row_sup.addStretch()

        # Quadrante 1 (Direito: 18..11)
        for num in [18, 17, 16, 15, 14, 13, 12, 11]:
            card = ToothCard(num, self)
            card.clicked.connect(self.ao_clicar_dente)
            self.dentes_cards[num] = card
            row_sup.addWidget(card)

        # Divisor da Linha Média
        divisor_sup = QFrame()
        divisor_sup.setFrameShape(QFrame.VLine)
        divisor_sup.setStyleSheet("color: #0d9488; width: 2px; margin: 4px 6px;")
        row_sup.addWidget(divisor_sup)

        # Quadrante 2 (Esquerdo: 21..28)
        for num in [21, 22, 23, 24, 25, 26, 27, 28]:
            card = ToothCard(num, self)
            card.clicked.connect(self.ao_clicar_dente)
            self.dentes_cards[num] = card
            row_sup.addWidget(card)

        row_sup.addStretch()
        v_sup.addLayout(row_sup)
        layout_arcadas.addWidget(box_sup)

        # Indicador de Divisão Oclusal
        lbl_oclusao = QLabel("─── OCLUSÃO / LINHA MÉDIA DA MORDIDA ───")
        lbl_oclusao.setAlignment(Qt.AlignCenter)
        lbl_oclusao.setStyleSheet("font-size: 11px; font-weight: bold; color: #94a3b8; letter-spacing: 1px;")
        layout_arcadas.addWidget(lbl_oclusao)

        # --- ARCADA INFERIOR ---
        box_inf = QGroupBox("Arcada Inferior (Mandíbula)")
        box_inf.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                color: #0f766e;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 4px;
            }
        """)
        v_inf = QVBoxLayout(box_inf)
        v_inf.setContentsMargins(8, 12, 8, 8)

        row_inf = QHBoxLayout()
        row_inf.setSpacing(3)
        row_inf.addStretch()

        # Quadrante 4 (Direito: 48..41)
        for num in [48, 47, 46, 45, 44, 43, 42, 41]:
            card = ToothCard(num, self)
            card.clicked.connect(self.ao_clicar_dente)
            self.dentes_cards[num] = card
            row_inf.addWidget(card)

        # Divisor da Linha Média
        divisor_inf = QFrame()
        divisor_inf.setFrameShape(QFrame.VLine)
        divisor_inf.setStyleSheet("color: #0d9488; width: 2px; margin: 4px 6px;")
        row_inf.addWidget(divisor_inf)

        # Quadrante 3 (Esquerdo: 31..38)
        for num in [31, 32, 33, 34, 35, 36, 37, 38]:
            card = ToothCard(num, self)
            card.clicked.connect(self.ao_clicar_dente)
            self.dentes_cards[num] = card
            row_inf.addWidget(card)

        row_inf.addStretch()
        v_inf.addLayout(row_inf)
        layout_arcadas.addWidget(box_inf)

        scroll_arcadas.setWidget(content_arcadas)
        col_mapa.addWidget(scroll_arcadas)

        # Legenda Colorida no Rodapé
        legenda_frame = QFrame(self)
        legenda_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px;")
        leg_layout = QHBoxLayout(legenda_frame)
        leg_layout.setContentsMargins(8, 4, 8, 4)
        leg_layout.setSpacing(10)

        for k, v in STATUS_DENTE_CORES.items():
            lbl = QLabel(f"<span style='color:{v['cor']}; font-size:14px;'>●</span> {v['nome'].split(' / ')[0]}")
            lbl.setStyleSheet("font-size: 11px; font-weight: 500;")
            leg_layout.addWidget(lbl)
        leg_layout.addStretch()
        col_mapa.addWidget(legenda_frame)

        main_layout.addLayout(col_mapa, stretch=3)

        # -------------------------------------------------------------
        # COLUNA DIREITA: PAINEL DE EDIÇÃO DO DENTE SELECIONADO
        # -------------------------------------------------------------
        self.panel_edit = QFrame(self)
        self.panel_edit.setFixedWidth(290)
        self.panel_edit.setStyleSheet("""
            QFrame#panelEdit {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        self.panel_edit.setObjectName("panelEdit")
        p_layout = QVBoxLayout(self.panel_edit)
        p_layout.setContentsMargins(12, 12, 12, 12)
        p_layout.setSpacing(10)

        self.lbl_dente_titulo = QLabel("Selecione um Dente", self.panel_edit)
        self.lbl_dente_titulo.setStyleSheet("font-size: 15px; font-weight: bold; color: #0f766e;")
        p_layout.addWidget(self.lbl_dente_titulo)

        self.lbl_dente_nome = QLabel("Clique em qualquer dente no mapa para editar sua condição clínica.", self.panel_edit)
        self.lbl_dente_nome.setStyleSheet("font-size: 12px; color: #64748b;")
        self.lbl_dente_nome.setWordWrap(True)
        p_layout.addWidget(self.lbl_dente_nome)

        p_layout.addSpacing(6)

        # Seletor de Situação Clínica
        p_layout.addWidget(QLabel("Condição / Situação do Dente:"))
        self.cmb_status = QComboBox(self.panel_edit)
        for k, v in STATUS_DENTE_CORES.items():
            self.cmb_status.addItem(f"{v['badge']} - {v['nome']}", k)
        p_layout.addWidget(self.cmb_status)

        # Checkboxes de Faces Dentárias
        p_layout.addWidget(QLabel("Faces Envolvidas:"))
        faces_box = QFrame()
        faces_box.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px;")
        grid_faces = QGridLayout(faces_box)
        grid_faces.setContentsMargins(8, 6, 8, 6)
        grid_faces.setSpacing(6)

        self.chk_v = QCheckBox("V - Vestibular")
        self.chk_l = QCheckBox("L/P - Lingual/Palatina")
        self.chk_m = QCheckBox("M - Mesial")
        self.chk_d = QCheckBox("D - Distal")
        self.chk_o = QCheckBox("O/I - Oclusal/Incisal")

        for chk in [self.chk_v, self.chk_l, self.chk_m, self.chk_d, self.chk_o]:
            chk.setStyleSheet("font-size: 11px; font-weight: 500;")

        grid_faces.addWidget(self.chk_v, 0, 0)
        grid_faces.addWidget(self.chk_l, 0, 1)
        grid_faces.addWidget(self.chk_m, 1, 0)
        grid_faces.addWidget(self.chk_d, 1, 1)
        grid_faces.addWidget(self.chk_o, 2, 0, 1, 2)
        p_layout.addWidget(faces_box)

        # Observações do Dente
        p_layout.addWidget(QLabel("Observações do Dente:"))
        self.txt_obs_dente = QLineEdit(self.panel_edit)
        self.txt_obs_dente.setPlaceholderText("Ex: Cárie ocluso-mesial profunda")
        p_layout.addWidget(self.txt_obs_dente)

        # Botão Salvar Dente
        self.btn_salvar_dente = QPushButton("💾 Salvar Situação do Dente", self.panel_edit)
        self.btn_salvar_dente.setStyleSheet("""
            QPushButton {
                background-color: #0d9488;
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 14px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0f766e;
            }
        """)
        self.btn_salvar_dente.clicked.connect(self.salvar_dente_atual)
        p_layout.addWidget(self.btn_salvar_dente)

        p_layout.addSpacing(10)

        # Ação Rápida: Lançar Procedimento
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #e2e8f0;")
        p_layout.addWidget(sep)

        self.btn_lancar_procedimento = QPushButton("➕ Registrar Procedimento", self.panel_edit)
        self.btn_lancar_procedimento.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 14px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        self.btn_lancar_procedimento.clicked.connect(self.ao_solicitar_procedimento)
        p_layout.addWidget(self.btn_lancar_procedimento)

        p_layout.addStretch()
        main_layout.addWidget(self.panel_edit, stretch=1)

        # Desabilita o painel até selecionar um dente
        self.set_painel_habilitado(False)

    def set_painel_habilitado(self, habilitado: bool):
        self.cmb_status.setEnabled(habilitado)
        self.chk_v.setEnabled(habilitado)
        self.chk_l.setEnabled(habilitado)
        self.chk_m.setEnabled(habilitado)
        self.chk_d.setEnabled(habilitado)
        self.chk_o.setEnabled(habilitado)
        self.txt_obs_dente.setEnabled(habilitado)
        self.btn_salvar_dente.setEnabled(habilitado)
        self.btn_lancar_procedimento.setEnabled(habilitado)

    def carregar_odontograma(self):
        dados = get_patient_odontograma(self.patient_id)
        
        # Atualiza todos os cards com os dados do banco
        contagem = {"higido": 0, "carie": 0, "restaurado": 0, "outros": 0}
        for num, card in self.dentes_cards.items():
            if num in dados:
                card.set_dados(dados[num])
                st = dados[num]["status"]
                if st in contagem:
                    contagem[st] += 1
                else:
                    contagem["outros"] += 1
            else:
                card.set_dados({"status": "higido", "faces": "", "observacoes": ""})
                contagem["higido"] += 1

        resumo_txt = f"Hígidos: {contagem['higido']}  •  Cáries: {contagem['carie']}  •  Restaurados: {contagem['restaurado']}  •  Intervenções: {contagem['outros']}"
        self.lbl_stats.setText(f"Resumo: {resumo_txt}")

        # Se havia um dente selecionado, atualiza o formulário
        if self.dente_selecionado:
            self.ao_clicar_dente(self.dente_selecionado)

    def ao_clicar_dente(self, numero: int):
        self.dente_selecionado = numero

        # Atualiza seleção visual dos cards
        for num, card in self.dentes_cards.items():
            card.set_selecionado(num == numero)

        nome_dente = NOMES_DENTES.get(numero, f"Dente {numero}")
        self.lbl_dente_titulo.setText(f"🦷 Dente {numero}")
        self.lbl_dente_nome.setText(nome_dente)

        # Preenche os dados atuais do card
        card_atual = self.dentes_cards.get(numero)
        if card_atual:
            idx = self.cmb_status.findData(card_atual.status)
            if idx >= 0:
                self.cmb_status.setCurrentIndex(idx)

            faces = [f.strip().upper() for f in card_atual.faces.split(",") if f.strip()]
            self.chk_v.setChecked("V" in faces)
            self.chk_l.setChecked("L" in faces or "P" in faces)
            self.chk_m.setChecked("M" in faces)
            self.chk_d.setChecked("D" in faces)
            self.chk_o.setChecked("O" in faces or "I" in faces)

            self.txt_obs_dente.setText(card_atual.observacoes)

        self.set_painel_habilitado(True)

    def salvar_dente_atual(self):
        if not self.dente_selecionado:
            return

        status = self.cmb_status.currentData()
        faces_list = []
        if self.chk_v.isChecked(): faces_list.append("V")
        if self.chk_l.isChecked(): faces_list.append("L")
        if self.chk_m.isChecked(): faces_list.append("M")
        if self.chk_d.isChecked(): faces_list.append("D")
        if self.chk_o.isChecked(): faces_list.append("O")
        faces_str = ",".join(faces_list)

        obs = self.txt_obs_dente.text().strip()

        ok, msg = save_tooth_status(
            self.patient_id, self.dente_selecionado, status,
            faces_str, obs, self.current_user["id"], self.current_user["nome"]
        )
        if ok:
            # Atualiza o card imediatamente
            card = self.dentes_cards.get(self.dente_selecionado)
            if card:
                card.set_dados({"status": status, "faces": faces_str, "observacoes": obs})
            self.carregar_odontograma()
        else:
            QMessageBox.critical(self, "Erro", msg)

    def ao_solicitar_procedimento(self):
        if not self.dente_selecionado:
            return
        status = self.cmb_status.currentData()
        procedimento_sugerido = ""
        if status == "carie":
            procedimento_sugerido = "Restauração em Resina"
        elif status == "canal":
            procedimento_sugerido = "Tratamento Endodôntico (Canal)"
        elif status == "protese":
            procedimento_sugerido = "Coroa / Prótese Fixa"
        elif status == "implante":
            procedimento_sugerido = "Implante Dentário"
        elif status == "ausente":
            procedimento_sugerido = "Extração Dentária"

        self.procedimento_solicitado.emit(self.dente_selecionado, procedimento_sugerido)

    def ao_resetar_odontograma(self):
        resposta = QMessageBox.warning(
            self,
            "Confirmar Restauração",
            "Deseja resetar todo o odontograma deste paciente para o estado inicial hígido?\n"
            "Esta ação apagará todas as marcações de dentes salvas.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if resposta == QMessageBox.Yes:
            ok, msg = reset_odontograma(self.patient_id, self.current_user["id"], self.current_user["nome"])
            if ok:
                self.carregar_odontograma()
                self.set_painel_habilitado(False)
                self.lbl_dente_titulo.setText("Selecione um Dente")
                self.lbl_dente_nome.setText("Clique em qualquer dente no mapa para editar sua condição clínica.")
            else:
                QMessageBox.critical(self, "Erro", msg)
