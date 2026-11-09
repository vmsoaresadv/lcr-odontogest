"""
Módulo de Odontograma Clínico Interativo (Padrão FDI)
Suporte para Dentição Adulta (Permanente), Pediátrica (Decídua) e Mista.
Desenho anatômico das 5 faces dentárias e representação em arco da arcada dentária.
LCR OdontoGest - LCR Clínica Odontológica
"""

from typing import Dict, Optional, List, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QComboBox, QCheckBox, QLineEdit, QFrame,
    QMessageBox, QScrollArea, QGroupBox, QButtonGroup, QRadioButton
)
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import (
    QFont, QColor, QPainter, QBrush, QPen, QPolygonF,
    QPainterPath, QLinearGradient
)

from services.patient_service import (
    DENTES_FDI_SUPERIORES, DENTES_FDI_INFERIORES,
    DENTES_DECIDUOS_SUPERIORES, DENTES_DECIDUOS_INFERIORES,
    NOMES_DENTES, STATUS_DENTE_CORES,
    get_patient_odontograma, save_tooth_status, reset_odontograma
)


class ToothAnatomicalWidget(QWidget):
    """
    Widget que renderiza o desenho anatômico de um dente com as 5 faces oclusais:
    - Centro: Face Oclusal / Incisal
    - Superior: Face Vestibular (para dentes superiores) ou Lingual (inferiores)
    - Inferior: Face Palatina (para dentes superiores) ou Vestibular (inferiores)
    - Esquerda e Direita: Faces Mesial e Distal (ajustadas pelo quadrante da linha média)
    """
    clicked = Signal(int)

    def __init__(self, numero: int, is_superior: bool = True, parent=None):
        super().__init__(parent)
        self.numero = numero
        self.is_superior = is_superior
        self.status = "higido"
        self.faces: List[str] = []
        self.observacoes = ""
        self.is_selected = False
        self.is_hovered = False

        self.setFixedSize(48, 68)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self.atualizar_tooltip()

    def set_dados(self, dados: dict):
        self.status = dados.get("status", "higido")
        raw_faces = dados.get("faces", "")
        self.faces = [f.strip().upper() for f in raw_faces.split(",") if f.strip()]
        self.observacoes = dados.get("observacoes", "")
        self.atualizar_tooltip()
        self.update()

    def set_selecionado(self, sel: bool):
        self.is_selected = sel
        self.update()

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.numero)
        super().mousePressEvent(event)

    def atualizar_tooltip(self):
        nome_completo = NOMES_DENTES.get(self.numero, f"Dente {self.numero}")
        cfg = STATUS_DENTE_CORES.get(self.status, STATUS_DENTE_CORES["higido"])
        faces_str = f"\nFaces afetadas: {', '.join(self.faces)}" if self.faces else ""
        obs_str = f"\nObservações: {self.observacoes}" if self.observacoes else ""
        self.setToolTip(f"Dente {self.numero} — {nome_completo}\nCondição: {cfg['nome']}{faces_str}{obs_str}")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Fundo de seleção ou hover
        if self.is_selected:
            painter.setPen(QPen(QColor("#0f766e"), 2))
            painter.setBrush(QBrush(QColor("#ccfbf1")))
            painter.drawRoundedRect(1, 1, w - 2, h - 2, 6, 6)
        elif self.is_hovered:
            painter.setPen(QPen(QColor("#14b8a6"), 1.5))
            painter.setBrush(QBrush(QColor("#f0fdfa")))
            painter.drawRoundedRect(1, 1, w - 2, h - 2, 6, 6)

        # 1. Desenho do Número FDI (acima para superiores, abaixo para inferiores)
        painter.setPen(QColor("#0f172a" if not self.is_selected else "#0f766e"))
        font_num = QFont("Segoe UI", 8, QFont.Bold)
        painter.setFont(font_num)

        if self.is_superior:
            rect_num = QRectF(0, 2, w, 14)
            y_offset = 18
        else:
            rect_num = QRectF(0, h - 16, w, 14)
            y_offset = 6

        painter.drawText(rect_num, Qt.AlignCenter, str(self.numero))

        # 2. Desenho Anatômico das 5 Faces do Dente (Geometria Cruz/Oclusal)
        box_size = 32.0
        x_start = (w - box_size) / 2.0
        y_start = float(y_offset)

        # Cores de status
        cfg = STATUS_DENTE_CORES.get(self.status, STATUS_DENTE_CORES["higido"])
        cor_status = QColor(cfg["cor"])
        cor_esmalte = QColor("#ffffff")
        pen_face = QPen(QColor("#64748b"), 1.0)

        # Se ausente, desenha caixa cinza suave e depois o "X"
        if self.status == "ausente":
            painter.setPen(QPen(QColor("#94a3b8"), 1.5))
            painter.setBrush(QBrush(QColor("#f1f5f9")))
            painter.drawRoundedRect(x_start, y_start, box_size, box_size, 4, 4)
            # Desenhar X de ausência
            painter.setPen(QPen(QColor("#64748b"), 2))
            painter.drawLine(int(x_start + 4), int(y_start + 4), int(x_start + box_size - 4), int(y_start + box_size - 4))
            painter.drawLine(int(x_start + box_size - 4), int(y_start + 4), int(x_start + 4), int(y_start + box_size - 4))
            return

        # Identificação das faces no plano:
        # Superior: V=Topo, P=Base | Inferior: L=Topo, V=Base
        # Mesial fica voltada para a linha média (entre 11/21, 51/61, etc)
        is_lado_direito_paciente = str(self.numero)[0] in ["1", "4", "5", "8"]

        face_topo = "V" if self.is_superior else "L"
        face_base = "P" if self.is_superior else "V"
        face_esq = "D" if is_lado_direito_paciente else "M"
        face_dir = "M" if is_lado_direito_paciente else "D"

        # Helpers para cor de cada face:
        def get_face_color(face_sigla: str) -> QColor:
            if not self.faces:
                # Se não especificou faces, mas o dente tem status alterado, preenche sutilmente
                if self.status == "higido":
                    return cor_esmalte
                return cor_status.lighter(135)
            # Se especificou faces
            if face_sigla in self.faces:
                return cor_status
            if face_sigla == "P" and "L" in self.faces:
                return cor_status
            return cor_esmalte

        # Centro: Oclusal / Incisal
        c_cor = get_face_color("O")
        # Topo
        t_cor = get_face_color(face_topo)
        # Base
        b_cor = get_face_color(face_base)
        # Esquerda
        e_cor = get_face_color(face_esq)
        # Direita
        d_cor = get_face_color(face_dir)

        # Polígonos das 5 faces:
        p_c1 = QPointF(x_start + 9, y_start + 9)
        p_c2 = QPointF(x_start + box_size - 9, y_start + 9)
        p_c3 = QPointF(x_start + box_size - 9, y_start + box_size - 9)
        p_c4 = QPointF(x_start + 9, y_start + box_size - 9)

        # Face Topo (Trapézio superior)
        poly_topo = QPolygonF([
            QPointF(x_start, y_start),
            QPointF(x_start + box_size, y_start),
            p_c2, p_c1
        ])
        # Face Base (Trapézio inferior)
        poly_base = QPolygonF([
            p_c4, p_c3,
            QPointF(x_start + box_size, y_start + box_size),
            QPointF(x_start, y_start + box_size)
        ])
        # Face Esquerda (Trapézio lateral esquerdo)
        poly_esq = QPolygonF([
            QPointF(x_start, y_start),
            p_c1, p_c4,
            QPointF(x_start, y_start + box_size)
        ])
        # Face Direita (Trapézio lateral direito)
        poly_dir = QPolygonF([
            p_c2,
            QPointF(x_start + box_size, y_start),
            QPointF(x_start + box_size, y_start + box_size),
            p_c3
        ])
        # Face Centro (Quadrado Oclusal/Incisal)
        poly_centro = QPolygonF([p_c1, p_c2, p_c3, p_c4])

        painter.setPen(pen_face)

        # Pintura das faces
        painter.setBrush(QBrush(t_cor))
        painter.drawPolygon(poly_topo)

        painter.setBrush(QBrush(b_cor))
        painter.drawPolygon(poly_base)

        painter.setBrush(QBrush(e_cor))
        painter.drawPolygon(poly_esq)

        painter.setBrush(QBrush(d_cor))
        painter.drawPolygon(poly_dir)

        painter.setBrush(QBrush(c_cor))
        painter.drawPolygon(poly_centro)

        # Casos especiais de marcadores clínicos
        if self.status == "canal":
            # Linha vertical amarela/dourada no centro (representando obturação do conduto)
            painter.setPen(QPen(QColor("#b45309"), 2))
            painter.drawLine(int(x_start + box_size / 2), int(y_start + 4),
                             int(x_start + box_size / 2), int(y_start + box_size - 4))

        elif self.status == "implante":
            # Ícone geométrico de pino de implante no centro
            painter.setPen(QPen(QColor("#0891b2"), 1.5))
            for iy in range(int(y_start + 11), int(y_start + box_size - 11), 3):
                painter.drawLine(int(x_start + 12), iy, int(x_start + box_size - 12), iy)

        elif self.status == "protese":
            # Borda externa reforçada indicando coroa protética
            painter.setPen(QPen(QColor("#7c3aed"), 2.0))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(x_start - 1, y_start - 1, box_size + 2, box_size + 2, 2, 2)

        # 3. Micro-indicador de status em texto no rodapé (para dentes superiores) ou topo (para inferiores)
        if self.status != "higido":
            font_st = QFont("Segoe UI", 7, QFont.Bold)
            painter.setFont(font_st)
            painter.setPen(cor_status)
            txt_st = cfg["nome"].split(" / ")[0]
            if self.is_superior:
                rect_st = QRectF(0, h - 14, w, 12)
            else:
                rect_st = QRectF(0, 2, w, 12)
            painter.drawText(rect_st, Qt.AlignCenter, txt_st[:7])


class OdontogramaWidget(QWidget):
    """
    Componente visual e interativo completo do Odontograma Clínico:
    - Alternância entre Dentição Adulta (Permanente), Pediátrica (Decídua) e Mista.
    - Disposição das arcadas em arco parabólico natural.
    - Desenho anatômico das 5 faces com renderização de alta precisão.
    - Painel Inspetor de Dente com vínculo direto ao prontuário.
    """
    procedimento_solicitado = Signal(int, str)  # (numero_dente, procedimento_sugerido)

    def __init__(self, patient_id: int, current_user: dict, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.current_user = current_user
        self.dentes_widgets: Dict[int, ToothAnatomicalWidget] = {}
        self.dente_selecionado: Optional[int] = None
        self.modo_denticao = "adulto"  # "adulto", "infantil", "misto"

        self.init_ui()
        self.carregar_odontograma()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(14)

        # -------------------------------------------------------------
        # COLUNA ESQUERDA: ARCADAS DENTÁRIAS ANATÔMICAS EM ARCO
        # -------------------------------------------------------------
        col_mapa = QVBoxLayout()
        col_mapa.setSpacing(10)

        # Barra Superior: Modo de Dentição + Resumo + Botão Reset
        top_bar = QFrame(self)
        top_bar.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 6px 12px;
            }
        """)
        h_top = QHBoxLayout(top_bar)
        h_top.setContentsMargins(8, 4, 8, 4)
        h_top.setSpacing(12)

        # Seletor de Dentição (Segmented Control limpo)
        lbl_modo = QLabel("Dentição:", top_bar)
        lbl_modo.setStyleSheet("font-weight: bold; font-size: 12px; color: #334155;")
        h_top.addWidget(lbl_modo)

        self.btn_modo_adulto = QPushButton("Adulto (Permanente - 32)", top_bar)
        self.btn_modo_infantil = QPushButton("Infantil (Decíduo - 20)", top_bar)
        self.btn_modo_misto = QPushButton("Mista (Completo)", top_bar)

        for btn in [self.btn_modo_adulto, self.btn_modo_infantil, self.btn_modo_misto]:
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)

        self.btn_modo_adulto.setChecked(True)
        self.atualizar_estilo_botoes_modo()

        self.btn_modo_adulto.clicked.connect(lambda: self.mudar_modo_denticao("adulto"))
        self.btn_modo_infantil.clicked.connect(lambda: self.mudar_modo_denticao("infantil"))
        self.btn_modo_misto.clicked.connect(lambda: self.mudar_modo_denticao("misto"))

        h_top.addWidget(self.btn_modo_adulto)
        h_top.addWidget(self.btn_modo_infantil)
        h_top.addWidget(self.btn_modo_misto)

        h_top.addStretch()

        # Resumo
        self.lbl_stats = QLabel("32 dentes mapeados", top_bar)
        self.lbl_stats.setStyleSheet("font-size: 12px; font-weight: 600; color: #0f766e;")
        h_top.addWidget(self.lbl_stats)

        btn_reset = QPushButton("Redefinir Hígidos", top_bar)
        btn_reset.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #64748b;
                border: 1px solid #cbd5e1;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #fee2e2;
                color: #b91c1c;
                border-color: #fca5a5;
            }
        """)
        btn_reset.clicked.connect(self.ao_resetar_odontograma)
        h_top.addWidget(btn_reset)

        col_mapa.addWidget(top_bar)

        # Área de Rolagem das Arcadas Anatômicas
        scroll_arcadas = QScrollArea(self)
        scroll_arcadas.setWidgetResizable(True)
        scroll_arcadas.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; background-color: #ffffff;")

        self.content_arcadas = QWidget()
        self.content_arcadas.setStyleSheet("background-color: #ffffff;")
        self.layout_arcadas = QVBoxLayout(self.content_arcadas)
        self.layout_arcadas.setContentsMargins(14, 16, 14, 16)
        self.layout_arcadas.setSpacing(12)

        # Montar as arcadas
        self.construir_arcadas_visuais()

        scroll_arcadas.setWidget(self.content_arcadas)
        col_mapa.addWidget(scroll_arcadas)

        # Legenda Clínica no Rodapé
        legenda_frame = QFrame(self)
        legenda_frame.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 4px;")
        leg_layout = QHBoxLayout(legenda_frame)
        leg_layout.setContentsMargins(10, 4, 10, 4)
        leg_layout.setSpacing(14)

        for k, v in STATUS_DENTE_CORES.items():
            item_lbl = QLabel(f"<span style='color:{v['cor']}; font-size:13px;'>■</span> {v['nome'].split(' / ')[0]}")
            item_lbl.setStyleSheet("font-size: 11px; font-weight: 500; color: #334155;")
            leg_layout.addWidget(item_lbl)
        leg_layout.addStretch()
        col_mapa.addWidget(legenda_frame)

        main_layout.addLayout(col_mapa, stretch=3)

        # -------------------------------------------------------------
        # COLUNA DIREITA: INSPETOR E EDITOR CLÍNICO DO DENTE
        # -------------------------------------------------------------
        self.panel_edit = QFrame(self)
        self.panel_edit.setFixedWidth(300)
        self.panel_edit.setStyleSheet("""
            QFrame#panelEdit {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        self.panel_edit.setObjectName("panelEdit")
        p_layout = QVBoxLayout(self.panel_edit)
        p_layout.setContentsMargins(14, 14, 14, 14)
        p_layout.setSpacing(10)

        # Cabeçalho do Painel
        self.lbl_dente_titulo = QLabel("Selecione um Dente", self.panel_edit)
        self.lbl_dente_titulo.setStyleSheet("font-size: 15px; font-weight: bold; color: #0f766e;")
        p_layout.addWidget(self.lbl_dente_titulo)

        self.lbl_dente_nome = QLabel("Clique em qualquer dente no arco anatômico para visualizar ou registrar sua condição clínica.", self.panel_edit)
        self.lbl_dente_nome.setStyleSheet("font-size: 12px; color: #64748b; line-height: 1.4;")
        self.lbl_dente_nome.setWordWrap(True)
        p_layout.addWidget(self.lbl_dente_nome)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("color: #f1f5f9; margin: 4px 0;")
        p_layout.addWidget(sep1)

        # Diagnóstico / Status
        lbl_st = QLabel("Condição / Diagnóstico:", self.panel_edit)
        lbl_st.setStyleSheet("font-weight: 600; font-size: 12px; color: #1e293b;")
        p_layout.addWidget(lbl_st)

        self.cmb_status = QComboBox(self.panel_edit)
        for k, v in STATUS_DENTE_CORES.items():
            self.cmb_status.addItem(f"{v['badge']} — {v['nome'].split(' / ')[0]}", k)
        self.cmb_status.setStyleSheet("""
            QComboBox {
                padding: 6px 10px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                background-color: #ffffff;
                font-size: 12px;
            }
        """)
        p_layout.addWidget(self.cmb_status)

        # Faces Dentárias
        lbl_fc = QLabel("Faces Anatômicas Envolvidas:", self.panel_edit)
        lbl_fc.setStyleSheet("font-weight: 600; font-size: 12px; color: #1e293b;")
        p_layout.addWidget(lbl_fc)

        faces_frame = QFrame(self.panel_edit)
        faces_frame.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px;")
        grid_faces = QGridLayout(faces_frame)
        grid_faces.setContentsMargins(6, 6, 6, 6)
        grid_faces.setSpacing(6)

        self.chk_v = QCheckBox("V — Vestibular")
        self.chk_l = QCheckBox("L/P — Lingual / Palatina")
        self.chk_m = QCheckBox("M — Mesial")
        self.chk_d = QCheckBox("D — Distal")
        self.chk_o = QCheckBox("O/I — Oclusal / Incisal")

        for chk in [self.chk_v, self.chk_l, self.chk_m, self.chk_d, self.chk_o]:
            chk.setStyleSheet("font-size: 11px; font-weight: 500; color: #334155;")

        grid_faces.addWidget(self.chk_v, 0, 0)
        grid_faces.addWidget(self.chk_l, 0, 1)
        grid_faces.addWidget(self.chk_m, 1, 0)
        grid_faces.addWidget(self.chk_d, 1, 1)
        grid_faces.addWidget(self.chk_o, 2, 0, 1, 2)
        p_layout.addWidget(faces_frame)

        # Observações
        lbl_ob = QLabel("Observações Clínicas:", self.panel_edit)
        lbl_ob.setStyleSheet("font-weight: 600; font-size: 12px; color: #1e293b;")
        p_layout.addWidget(lbl_ob)

        self.txt_obs_dente = QLineEdit(self.panel_edit)
        self.txt_obs_dente.setPlaceholderText("Ex: Restauração ocluso-mesial profunda")
        self.txt_obs_dente.setStyleSheet("""
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                font-size: 12px;
            }
        """)
        p_layout.addWidget(self.txt_obs_dente)

        # Botão Salvar Dente
        self.btn_salvar_dente = QPushButton("Salvar Situação do Dente", self.panel_edit)
        self.btn_salvar_dente.setStyleSheet("""
            QPushButton {
                background-color: #0f766e;
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 14px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #115e59;
            }
        """)
        self.btn_salvar_dente.clicked.connect(self.salvar_dente_atual)
        p_layout.addWidget(self.btn_salvar_dente)

        # Divisor
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color: #e2e8f0; margin: 6px 0;")
        p_layout.addWidget(sep2)

        # Ação Direta com Prontuário
        self.btn_lancar_procedimento = QPushButton("Registrar Procedimento no Prontuário", self.panel_edit)
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

        self.set_painel_habilitado(False)

    def atualizar_estilo_botoes_modo(self):
        estilo_ativo = """
            QPushButton {
                background-color: #0f766e;
                color: #ffffff;
                border: 1px solid #0f766e;
                border-radius: 5px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: bold;
            }
        """
        estilo_inativo = """
            QPushButton {
                background-color: #ffffff;
                color: #475569;
                border: 1px solid #cbd5e1;
                border-radius: 5px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                color: #0f766e;
            }
        """
        self.btn_modo_adulto.setStyleSheet(estilo_ativo if self.modo_denticao == "adulto" else estilo_inativo)
        self.btn_modo_infantil.setStyleSheet(estilo_ativo if self.modo_denticao == "infantil" else estilo_inativo)
        self.btn_modo_misto.setStyleSheet(estilo_ativo if self.modo_denticao == "misto" else estilo_inativo)

    def mudar_modo_denticao(self, modo: str):
        if self.modo_denticao == modo:
            return
        self.modo_denticao = modo
        self.btn_modo_adulto.setChecked(modo == "adulto")
        self.btn_modo_infantil.setChecked(modo == "infantil")
        self.btn_modo_misto.setChecked(modo == "misto")
        self.atualizar_estilo_botoes_modo()

        # Limpar widgets anteriores e reconstruir
        self.dentes_widgets.clear()
        self.dente_selecionado = None
        self.set_painel_habilitado(False)
        self.lbl_dente_titulo.setText("Selecione um Dente")
        self.lbl_dente_nome.setText("Clique em qualquer dente no arco anatômico para visualizar ou registrar sua condição clínica.")

        # Limpar layout
        while self.layout_arcadas.count():
            item = self.layout_arcadas.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.construir_arcadas_visuais()
        self.carregar_odontograma()

    def construir_arcadas_visuais(self):
        """Constrói as arcadas em arco parabólico natural simulando a boca aberta."""

        # Guia Anatômica Superior: Direita do Paciente à esquerda | Esquerda do Paciente à direita
        h_guia = QHBoxLayout()
        lbl_dir = QLabel("◀ Lado Direito do Paciente", self.content_arcadas)
        lbl_dir.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748b;")
        lbl_esq = QLabel("Lado Esquerdo do Paciente ▶", self.content_arcadas)
        lbl_esq.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748b;")
        h_guia.addWidget(lbl_dir)
        h_guia.addStretch()
        h_guia.addWidget(lbl_esq)
        self.layout_arcadas.addLayout(h_guia)

        # Se for Misto ou Adulto: Arcada Superior Permanente
        if self.modo_denticao in ["adulto", "misto"]:
            box_sup_perm = self._criar_grupo_arcada(
                "Arcada Superior Permanente (Maxila — Dentes 18 a 28)",
                q_dir=[18, 17, 16, 15, 14, 13, 12, 11],
                q_esq=[21, 22, 23, 24, 25, 26, 27, 28],
                is_superior=True,
                curvatura=True
            )
            self.layout_arcadas.addWidget(box_sup_perm)

        # Se for Misto ou Infantil: Arcada Superior Decídua
        if self.modo_denticao in ["infantil", "misto"]:
            box_sup_dec = self._criar_grupo_arcada(
                "Arcada Superior Decídua / Pediátrica (Dentes 55 a 65)",
                q_dir=[55, 54, 53, 52, 51],
                q_esq=[61, 62, 63, 64, 65],
                is_superior=True,
                curvatura=False
            )
            self.layout_arcadas.addWidget(box_sup_dec)

        # Faixa Central da Oclusão / Mordida
        faixa_oclusao = QFrame()
        faixa_oclusao.setStyleSheet("background-color: #f1f5f9; border-radius: 4px; padding: 4px;")
        h_ocl = QHBoxLayout(faixa_oclusao)
        h_ocl.setContentsMargins(10, 2, 10, 2)
        lbl_ocl = QLabel("LINHA DE OCLUSÃO E MORDIDA", faixa_oclusao)
        lbl_ocl.setAlignment(Qt.AlignCenter)
        lbl_ocl.setStyleSheet("font-size: 10px; font-weight: bold; color: #94a3b8; letter-spacing: 2px;")
        h_ocl.addWidget(lbl_ocl)
        self.layout_arcadas.addWidget(faixa_oclusao)

        # Se for Misto ou Infantil: Arcada Inferior Decídua
        if self.modo_denticao in ["infantil", "misto"]:
            box_inf_dec = self._criar_grupo_arcada(
                "Arcada Inferior Decídua / Pediátrica (Dentes 85 a 75)",
                q_dir=[85, 84, 83, 82, 81],
                q_esq=[71, 72, 73, 74, 75],
                is_superior=False,
                curvatura=False
            )
            self.layout_arcadas.addWidget(box_inf_dec)

        # Se for Misto ou Adulto: Arcada Inferior Permanente
        if self.modo_denticao in ["adulto", "misto"]:
            box_inf_perm = self._criar_grupo_arcada(
                "Arcada Inferior Permanente (Mandíbula — Dentes 48 a 38)",
                q_dir=[48, 47, 46, 45, 44, 43, 42, 41],
                q_esq=[31, 32, 33, 34, 35, 36, 37, 38],
                is_superior=False,
                curvatura=True
            )
            self.layout_arcadas.addWidget(box_inf_perm)

    def _criar_grupo_arcada(self, titulo: str, q_dir: List[int], q_esq: List[int],
                            is_superior: bool, curvatura: bool = True) -> QGroupBox:
        """Cria um grupo de arcada com dentes dispostos em arco parabólico suave."""
        box = QGroupBox(titulo)
        box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #0f766e;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 14px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
        """)

        v_box = QVBoxLayout(box)
        v_box.setContentsMargins(6, 12, 6, 8)

        row = QHBoxLayout()
        row.setSpacing(2)
        row.addStretch()

        # Deslocamento vertical para simular a curvatura anatômica do arco
        # Nos dentes centrais (11, 21), a maxila faz um ápice superior (menor Y)
        # Nos molares (18, 28), os dentes ficam mais baixos (maior Y)
        n_dir = len(q_dir)
        offsets_dir = [int((n_dir - 1 - i) * 2.5) for i in range(n_dir)] if curvatura else [0] * n_dir
        offsets_esq = [int(i * 2.5) for i in range(len(q_esq))] if curvatura else [0] * len(q_esq)

        # Lado Direito do Paciente
        for i, num in enumerate(q_dir):
            container = QWidget()
            c_layout = QVBoxLayout(container)
            c_layout.setContentsMargins(0, 0, 0, 0)
            c_layout.setSpacing(0)

            pad = offsets_dir[i]
            if is_superior:
                # Nos superiores, molares descem
                c_layout.addSpacing(pad)
            else:
                # Nos inferiores, centrais descem
                c_layout.addSpacing(int((n_dir - 1) * 2.5) - pad if curvatura else 0)

            tooth = ToothAnatomicalWidget(num, is_superior=is_superior, parent=container)
            tooth.clicked.connect(self.ao_clicar_dente)
            self.dentes_widgets[num] = tooth
            c_layout.addWidget(tooth)
            c_layout.addStretch()

            row.addWidget(container)

        # Divisor da Linha Média Anatômica
        divisor = QFrame()
        divisor.setFrameShape(QFrame.VLine)
        divisor.setStyleSheet("color: #0d9488; width: 2px; margin: 4px 6px;")
        row.addWidget(divisor)

        # Lado Esquerdo do Paciente
        for i, num in enumerate(q_esq):
            container = QWidget()
            c_layout = QVBoxLayout(container)
            c_layout.setContentsMargins(0, 0, 0, 0)
            c_layout.setSpacing(0)

            pad = offsets_esq[i]
            if is_superior:
                c_layout.addSpacing(pad)
            else:
                c_layout.addSpacing(int((len(q_esq) - 1) * 2.5) - pad if curvatura else 0)

            tooth = ToothAnatomicalWidget(num, is_superior=is_superior, parent=container)
            tooth.clicked.connect(self.ao_clicar_dente)
            self.dentes_widgets[num] = tooth
            c_layout.addWidget(tooth)
            c_layout.addStretch()

            row.addWidget(container)

        row.addStretch()
        v_box.addLayout(row)
        return box

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

        contagem = {"higido": 0, "carie": 0, "restaurado": 0, "outros": 0}
        for num, widget in self.dentes_widgets.items():
            if num in dados:
                widget.set_dados(dados[num])
                st = dados[num]["status"]
                if st in contagem:
                    contagem[st] += 1
                else:
                    contagem["outros"] += 1
            else:
                widget.set_dados({"status": "higido", "faces": "", "observacoes": ""})
                contagem["higido"] += 1

        total_visivel = len(self.dentes_widgets)
        resumo_txt = f"{total_visivel} Dentes  •  Hígidos: {contagem['higido']}  •  Cáries: {contagem['carie']}  •  Restaurados: {contagem['restaurado']}  •  Outros: {contagem['outros']}"
        self.lbl_stats.setText(resumo_txt)

        if self.dente_selecionado and self.dente_selecionado in self.dentes_widgets:
            self.ao_clicar_dente(self.dente_selecionado)

    def ao_clicar_dente(self, numero: int):
        self.dente_selecionado = numero

        # Atualiza o foco visual
        for num, widget in self.dentes_widgets.items():
            widget.set_selecionado(num == numero)

        nome_dente = NOMES_DENTES.get(numero, f"Dente {numero}")
        self.lbl_dente_titulo.setText(f"Dente {numero}")
        self.lbl_dente_nome.setText(nome_dente)

        widget_atual = self.dentes_widgets.get(numero)
        if widget_atual:
            idx = self.cmb_status.findData(widget_atual.status)
            if idx >= 0:
                self.cmb_status.setCurrentIndex(idx)

            faces = widget_atual.faces
            self.chk_v.setChecked("V" in faces)
            self.chk_l.setChecked("L" in faces or "P" in faces)
            self.chk_m.setChecked("M" in faces)
            self.chk_d.setChecked("D" in faces)
            self.chk_o.setChecked("O" in faces or "I" in faces)

            self.txt_obs_dente.setText(widget_atual.observacoes)

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
            widget = self.dentes_widgets.get(self.dente_selecionado)
            if widget:
                widget.set_dados({"status": status, "faces": faces_str, "observacoes": obs})
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
            "Confirmar Redefinição",
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
                self.lbl_dente_nome.setText("Clique em qualquer dente no arco anatômico para visualizar ou registrar sua condição clínica.")
            else:
                QMessageBox.critical(self, "Erro", msg)
