"""
Módulo de Interface Gráfica da Linha do Tempo Visual 360° do Paciente
LCR OdontoGest - Dra. Lara Camila (CRO-BA 15247)
"""

import os
import webbrowser
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QButtonGroup, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from services.patient_service import get_patient_timeline_events, open_attachment
from services.clinical_docs_service import get_issued_document, gerar_html_receituario, gerar_html_atestado
from ui.clinical_docs_widget import ClinicalDocPreviewDialog

TIMELINE_STYLE = """
Timeline360Widget, QWidget {
    font-family: 'Segoe UI', sans-serif;
    color: #1e293b;
    background-color: #f8fafc;
}
QScrollArea {
    border: none;
    background-color: transparent;
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
QPushButton#filterBtn {
    background-color: #ffffff;
    color: #475569;
    font-weight: 600;
    font-size: 12px;
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid #cbd5e1;
    min-height: 20px;
}
QPushButton#filterBtn:hover {
    background-color: #f1f5f9;
    color: #0f766e;
    border-color: #0f766e;
}
QPushButton#filterBtn:checked {
    background-color: #0f766e;
    color: #ffffff;
    font-weight: bold;
    border: 1px solid #0f766e;
}
QPushButton#secondaryBtn {
    background-color: #ffffff;
    color: #334155;
    font-weight: 600;
    padding: 6px 12px;
    border-radius: 6px;
    border: 1px solid #cbd5e1;
}
QPushButton#secondaryBtn:hover {
    background-color: #f1f5f9;
}
"""


class TimelineCard(QFrame):
    """Card individual de evento na Linha do Tempo 360°."""
    def __init__(self, evento: dict, parent_widget, parent=None):
        super().__init__(parent)
        self.evento = evento
        self.parent_widget = parent_widget
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            TimelineCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
            }
            TimelineCard:hover {
                border: 1px solid #0d9488;
                background-color: #ffffff;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(14)

        # Ícone do evento em círculo
        icon_box = QFrame()
        icon_box.setFixedSize(44, 44)
        cor_tag = self.evento.get("cor_tag", "#0f766e")
        icon_box.setStyleSheet(f"""
            QFrame {{
                background-color: #f8fafc;
                border: 2px solid {cor_tag};
                border-radius: 22px;
            }}
        """)
        icon_lay = QVBoxLayout(icon_box)
        icon_lay.setContentsMargins(0, 0, 0, 0)
        lbl_icon = QLabel(self.evento.get("icone", "📌"))
        lbl_icon.setAlignment(Qt.AlignCenter)
        lbl_icon.setFont(QFont("Segoe UI Emoji", 15))
        icon_lay.addWidget(lbl_icon)
        layout.addWidget(icon_box, alignment=Qt.AlignTop)

        # Corpo do Card
        body = QVBoxLayout()
        body.setSpacing(4)

        # Linha Superior: Tag + Data
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        lbl_tag = QLabel(f" {self.evento.get('tag', 'Evento')} ")
        lbl_tag.setStyleSheet(f"""
            QLabel {{
                background-color: #f1f5f9;
                color: {cor_tag};
                font-weight: 700;
                font-size: 11px;
                padding: 2px 8px;
                border-radius: 4px;
                border: 1px solid {cor_tag}33;
            }}
        """)
        top_row.addWidget(lbl_tag)
        top_row.addStretch()

        lbl_data = QLabel(self.evento.get("data_formatada", ""))
        lbl_data.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 500;")
        top_row.addWidget(lbl_data)
        body.addLayout(top_row)

        # Título
        lbl_tit = QLabel(self.evento.get("titulo", ""))
        lbl_tit.setStyleSheet("font-size: 14px; font-weight: 700; color: #0f172a;")
        body.addWidget(lbl_tit)

        # Descrição principal
        desc = self.evento.get("descricao", "")
        if desc:
            lbl_desc = QLabel(desc)
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet("color: #334155; font-size: 13px; line-height: 1.3;")
            body.addWidget(lbl_desc)

        # Detalhes complementares
        det = self.evento.get("detalhes", "")
        if det and det != desc:
            lbl_det = QLabel(det)
            lbl_det.setWordWrap(True)
            lbl_det.setStyleSheet("color: #64748b; font-size: 12px; font-style: italic;")
            body.addWidget(lbl_det)

        # Ações contextuais de acordo com o tipo
        tipo = self.evento.get("tipo")
        if tipo == "documento":
            btn_ver = QPushButton("👁️ Visualizar Documento Timbrado")
            btn_ver.setObjectName("secondaryBtn")
            btn_ver.setCursor(Qt.PointingHandCursor)
            btn_ver.clicked.connect(self.abrir_documento)
            body.addWidget(btn_ver, alignment=Qt.AlignLeft)
        elif tipo == "anexo":
            btn_arq = QPushButton("🔍 Abrir Arquivo / Radiografia")
            btn_arq.setObjectName("secondaryBtn")
            btn_arq.setCursor(Qt.PointingHandCursor)
            btn_arq.clicked.connect(self.abrir_anexo)
            body.addWidget(btn_arq, alignment=Qt.AlignLeft)

        layout.addLayout(body, 1)

    def abrir_documento(self):
        doc_id = self.evento.get("id")
        doc = get_issued_document(doc_id)
        if doc:
            html = gerar_html_receituario(doc) if doc["tipo_documento"] == "Receituario" else gerar_html_atestado(doc)
            dlg = ClinicalDocPreviewDialog(doc, html, self)
            dlg.exec()

    def abrir_anexo(self):
        att_id = self.evento.get("id")
        ok, msg = open_attachment(att_id)
        if not ok:
            QMessageBox.warning(self, "Aviso", msg)


class Timeline360Widget(QWidget):
    """Aba principal da Linha do Tempo 360° dentro da Ficha do Paciente."""
    def __init__(self, patient_id: int, current_user: dict, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.current_user = current_user
        self.categoria_filtro = "todos"
        self.eventos_carregados: List[dict] = []
        self.setStyleSheet(TIMELINE_STYLE)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(10)

        # Barra Superior de Controles e Filtros
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        lbl_tit = QLabel("Linha do Tempo 360°")
        lbl_tit.setStyleSheet("font-size: 15px; font-weight: bold; color: #0f766e;")
        top_bar.addWidget(lbl_tit)

        top_bar.addSpacing(10)

        # Botões de Filtro
        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)

        filtros = [
            ("🌐 Todos (360°)", "todos"),
            ("🩺 Clínico & Consultas", "clinico"),
            ("💰 Financeiro", "financeiro"),
            ("📄 Receitas / Atestados", "documentos"),
            ("🖼️ Exames & Raio-X", "exames"),
        ]

        for idx, (label, chave) in enumerate(filtros):
            btn = QPushButton(label)
            btn.setObjectName("filterBtn")
            btn.setCheckable(True)
            if idx == 0:
                btn.setChecked(True)
            btn.clicked.connect(lambda _, c=chave: self.aplicar_filtro(c))
            self.filter_group.addButton(btn, idx)
            top_bar.addWidget(btn)

        top_bar.addStretch()

        btn_atualizar = QPushButton("🔄 Atualizar")
        btn_atualizar.setObjectName("secondaryBtn")
        btn_atualizar.clicked.connect(self.carregar_eventos)
        top_bar.addWidget(btn_atualizar)

        main_layout.addLayout(top_bar)

        # Área de Rolagem Vertical
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.timeline_layout = QVBoxLayout(self.scroll_content)
        self.timeline_layout.setContentsMargins(12, 10, 12, 10)
        self.timeline_layout.setSpacing(12)
        self.timeline_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll)

        self.carregar_eventos()

    def carregar_eventos(self):
        """Busca do banco e renderiza todos os eventos unificados."""
        self.eventos_carregados = get_patient_timeline_events(self.patient_id)
        self.renderizar_timeline()

    def aplicar_filtro(self, categoria: str):
        self.categoria_filtro = categoria
        self.renderizar_timeline()

    def renderizar_timeline(self):
        # Limpa itens anteriores
        while self.timeline_layout.count() > 0:
            item = self.timeline_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        filtrados = [
            e for e in self.eventos_carregados
            if self.categoria_filtro == "todos" or e.get("categoria") == self.categoria_filtro
        ]

        if not filtrados:
            empty_box = QFrame()
            empty_box.setStyleSheet("background-color: #ffffff; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 30px;")
            e_lay = QVBoxLayout(empty_box)
            lbl_empty = QLabel("Nenhum evento registrado nesta categoria para a Linha do Tempo.")
            lbl_empty.setAlignment(Qt.AlignCenter)
            lbl_empty.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 500;")
            e_lay.addWidget(lbl_empty)
            self.timeline_layout.addWidget(empty_box)
            return

        for ev in filtrados:
            card = TimelineCard(ev, self, self.scroll_content)
            self.timeline_layout.addWidget(card)
