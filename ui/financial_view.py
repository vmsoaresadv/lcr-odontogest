import os
import shutil
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialog, QTextEdit, QComboBox, QDateEdit,
    QFrame, QDoubleSpinBox, QSizePolicy, QScrollArea, QFileDialog,
    QInputDialog, QListView, QCheckBox, QSpinBox
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QFont, QColor, QDesktopServices
from PySide6.QtCore import QUrl

from ui.patients_view import perguntar_sim_nao
from ui.custom_date_edit import CustomDateEdit
from version import get_asset_path
from services.patient_service import search_patients
from services.financial_service import (
    FORMAS_PAGAMENTO,
    list_financial_categories, list_financial_categories_detailed,
    create_financial_category, delete_financial_category,
    create_transaction, update_transaction, delete_transaction,
    marcar_como_pago, get_transaction, search_transactions,
    get_financial_kpis, get_dre_resumido
)

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads" / "financial"
CHECK_ICON_PATH = get_asset_path("check_white.png").as_posix()

FINANCIAL_STYLE = """
QWidget {
    font-family: 'Segoe UI', sans-serif;
    color: #0f172a;
}
QDialog {
    background-color: #f8fafc;
}
QLineEdit, QTextEdit, QDoubleSpinBox, QSpinBox {
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

QDateEdit {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 28px 6px 10px;
    font-size: 13px;
    min-height: 24px;
    min-width: 135px;
    selection-background-color: #2ca5a9;
    selection-color: #ffffff;
}
QDateEdit::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid #cbd5e1;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus {
    border: 2px solid #2ca5a9;
    background-color: #ffffff;
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
QPushButton#revenueBtn {
    background-color: #059669;
    color: #ffffff;
    font-weight: bold;
    padding: 8px 16px;
    border-radius: 6px;
    border: none;
    font-size: 13px;
}
QPushButton#revenueBtn:hover {
    background-color: #047857;
}
QPushButton#expenseBtn {
    background-color: #dc2626;
    color: #ffffff;
    font-weight: bold;
    padding: 8px 16px;
    border-radius: 6px;
    border: none;
    font-size: 13px;
}
QPushButton#expenseBtn:hover {
    background-color: #b91c1c;
}
QPushButton#secondaryBtn {
    background-color: #f1f5f9;
    color: #334155;
    font-weight: 600;
    padding: 8px 14px;
    border-radius: 6px;
    border: 1px solid #cbd5e1;
    font-size: 13px;
}
QPushButton#secondaryBtn:hover {
    background-color: #e2e8f0;
    color: #0f172a;
}
QPushButton#dangerBtn {
    background-color: #ef4444;
    color: #ffffff;
    font-weight: bold;
    padding: 8px 14px;
    border-radius: 6px;
    border: none;
    font-size: 13px;
}
QPushButton#dangerBtn:hover {
    background-color: #dc2626;
}
QPushButton#pillBtn {
    background-color: #f1f5f9;
    color: #475569;
    font-weight: 600;
    padding: 7px 14px;
    border-radius: 6px;
    border: 1px solid #cbd5e1;
    font-size: 13px;
}
QPushButton#pillBtn:hover {
    background-color: #e2e8f0;
    color: #0f172a;
}
QPushButton#pillBtn:checked {
    background-color: #2ca5a9;
    color: #ffffff;
    border: 1px solid #248a8d;
    font-weight: bold;
}
QFrame#kpiCard {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px 14px;
}
QFrame#barNav {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
}
QScrollArea#scrollDRE {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
}
QScrollArea#scrollDRE QLabel {
    border: none;
    background: transparent;
}
QScrollArea#scrollDRE QWidget {
    background-color: #ffffff;
}
QFrame#cardResDRE {
    background-color: #f8fafc;
    border-radius: 8px;
}
QFrame#cardResDRE QLabel {
    border: none;
    background: transparent;
}
QTableCornerButton::section {
    background-color: #f8fafc;
    border: none;
}
QCheckBox {
    font-size: 13px;
    color: #0f766e;
    font-weight: 600;
    spacing: 8px;
    background: transparent;
}
QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border: 2px solid #0f766e;
    border-radius: 4px;
    background-color: #ffffff;
}
QCheckBox::indicator:hover {
    border-color: #0d9488;
    background-color: #f0fdfa;
}
QCheckBox::indicator:checked {
    background-color: #0f766e;
    border: 2px solid #0f766e;
    image: url(""" + CHECK_ICON_PATH + """);
}
"""


# -------------------------------------------------------------
# FORMULÁRIO DE LANÇAMENTO (RECEITA OU DESPESA)
# -------------------------------------------------------------

class TransactionFormDialog(QDialog):
    """Diálogo completo para Inserir ou Editar Lançamento Financeiro."""
    def __init__(self, current_user: dict, tipo: str = "Receita", transaction: Optional[dict] = None, initial_data: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.tipo_inicial = tipo
        self.transaction = transaction
        self.initial_data = initial_data
        self.is_edit = transaction is not None
        self.anexo_caminho: Optional[str] = None

        titulo = f"Editar Lançamento #{transaction['id']}" if self.is_edit else f"Novo Lançamento ({tipo})"
        self.setWindowTitle(titulo)
        self.setFixedSize(700, 625)
        self.setStyleSheet(FINANCIAL_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(11)

        # Cabeçalho com seletor de Tipo (Receita / Despesa)
        top_box = QHBoxLayout()
        title = QLabel("Editar Lançamento" if self.is_edit else "Registrar Lançamento Financeiro")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f766e;")
        top_box.addWidget(title)
        top_box.addStretch()

        self.cmb_tipo = QComboBox()
        self.cmb_tipo.setView(QListView())
        self.cmb_tipo.addItems(["Receita", "Despesa"])
        self.cmb_tipo.setFixedWidth(130)
        self.cmb_tipo.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.cmb_tipo.setCurrentText(self.transaction["tipo"] if self.is_edit else self.tipo_inicial)
        self.cmb_tipo.currentIndexChanged.connect(self.ao_mudar_tipo)
        top_box.addWidget(self.cmb_tipo)
        layout.addLayout(top_box)

        # Linha 1: Descrição (flex 6) e Categoria Financeira (flex 4)
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        v_desc = QVBoxLayout()
        v_desc.setSpacing(4)
        lbl_desc = QLabel("Descrição do Lançamento (*):")
        lbl_desc.setStyleSheet("font-weight: 600; color: #334155;")
        v_desc.addWidget(lbl_desc)
        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("Ex: Consulta Dra. Lara, Restauração Resina, Compra Luvas...")
        v_desc.addWidget(self.txt_desc)
        row1.addLayout(v_desc, 6)

        v_cat = QVBoxLayout()
        v_cat.setSpacing(4)
        lbl_cat = QLabel("Categoria Financeira (*):")
        lbl_cat.setStyleSheet("font-weight: 600; color: #334155;")
        v_cat.addWidget(lbl_cat)
        self.cmb_cat = QComboBox()
        self.cmb_cat.setView(QListView())
        self.carregar_categorias()
        v_cat.addWidget(self.cmb_cat)
        row1.addLayout(v_cat, 4)

        layout.addLayout(row1)

        # Linha 2: Paciente Vinculado (flex 6) e Valor Total (flex 4)
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        v_pac = QVBoxLayout()
        v_pac.setSpacing(4)
        lbl_pac = QLabel("Paciente Vinculado (Opcional):")
        lbl_pac.setStyleSheet("font-weight: 600; color: #334155;")
        v_pac.addWidget(lbl_pac)
        self.cmb_paciente = QComboBox()
        self.cmb_paciente.setView(QListView())
        self.cmb_paciente.setEditable(True)
        self.cmb_paciente.setInsertPolicy(QComboBox.NoInsert)
        self.carregar_pacientes()
        completer = self.cmb_paciente.completer()
        if completer:
            completer.setFilterMode(Qt.MatchContains)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
        v_pac.addWidget(self.cmb_paciente)
        row2.addLayout(v_pac, 6)

        v_val = QVBoxLayout()
        v_val.setSpacing(4)
        lbl_val = QLabel("Valor Total (R$) (*):")
        lbl_val.setStyleSheet("font-weight: 600; color: #334155;")
        v_val.addWidget(lbl_val)
        self.spn_valor = QDoubleSpinBox()
        self.spn_valor.setRange(0.01, 999999.99)
        self.spn_valor.setDecimals(2)
        self.spn_valor.setPrefix("R$ ")
        self.spn_valor.setValue(100.0)
        v_val.addWidget(self.spn_valor)
        row2.addLayout(v_val, 4)

        layout.addLayout(row2)

        # Linha 3: Forma de Pagamento (4), Parcelas (2), Status (4)
        row3 = QHBoxLayout()
        row3.setSpacing(12)

        v_f = QVBoxLayout()
        v_f.setSpacing(4)
        lbl_forma = QLabel("Forma de Pagamento:")
        lbl_forma.setStyleSheet("font-weight: 600; color: #334155;")
        v_f.addWidget(lbl_forma)
        self.cmb_forma = QComboBox()
        self.cmb_forma.setView(QListView())
        self.cmb_forma.addItems(FORMAS_PAGAMENTO)
        v_f.addWidget(self.cmb_forma)
        row3.addLayout(v_f, 4)

        v_parc = QVBoxLayout()
        v_parc.setSpacing(4)
        lbl_parc = QLabel("Parcelas:")
        lbl_parc.setStyleSheet("font-weight: 600; color: #334155;")
        v_parc.addWidget(lbl_parc)
        self.cmb_parcelas = QComboBox()
        self.cmb_parcelas.setView(QListView())
        for i in range(1, 13):
            self.cmb_parcelas.addItem(f"{i}x")
        v_parc.addWidget(self.cmb_parcelas)
        row3.addLayout(v_parc, 2)

        v_st = QVBoxLayout()
        v_st.setSpacing(4)
        lbl_st = QLabel("Status do Lançamento:")
        lbl_st.setStyleSheet("font-weight: 600; color: #334155;")
        v_st.addWidget(lbl_st)
        self.cmb_status = QComboBox()
        self.cmb_status.setView(QListView())
        self.cmb_status.addItems(["Pago", "Pendente"])
        self.cmb_status.currentIndexChanged.connect(self.ao_mudar_status)
        v_st.addWidget(self.cmb_status)
        row3.addLayout(v_st, 4)

        layout.addLayout(row3)

        # Linha 4: Datas (Atendimento / Procedimento, Vencimento, Pagamento)
        row4 = QHBoxLayout()
        row4.setSpacing(12)

        v_comp = QVBoxLayout()
        v_comp.setSpacing(4)
        self.lbl_comp = QLabel("Data do Atendimento (*):")
        self.lbl_comp.setStyleSheet("font-weight: 600; color: #334155;")
        v_comp.addWidget(self.lbl_comp)
        self.dt_comp = CustomDateEdit()
        self.dt_comp.setDate(QDate.currentDate())
        self.dt_comp.setToolTip("Data em que o atendimento clínico ou procedimento odontológico foi realizado")
        v_comp.addWidget(self.dt_comp)
        row4.addLayout(v_comp, 1)

        v_venc = QVBoxLayout()
        v_venc.setSpacing(4)
        lbl_venc = QLabel("Data de Vencimento:")
        lbl_venc.setStyleSheet("font-weight: 600; color: #334155;")
        v_venc.addWidget(lbl_venc)
        self.dt_venc = CustomDateEdit()
        self.dt_venc.setDate(QDate.currentDate())
        v_venc.addWidget(self.dt_venc)
        row4.addLayout(v_venc, 1)

        v_pag = QVBoxLayout()
        v_pag.setSpacing(4)
        lbl_pag = QLabel("Data do Pagamento:")
        lbl_pag.setStyleSheet("font-weight: 600; color: #334155;")
        v_pag.addWidget(lbl_pag)
        self.dt_pag = CustomDateEdit()
        self.dt_pag.setDate(QDate.currentDate())
        v_pag.addWidget(self.dt_pag)
        row4.addLayout(v_pag, 1)

        layout.addLayout(row4)

        # Linha 5: Painel de Recorrência Mensal
        rec_frame = QFrame()
        rec_frame.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
            }
        """)
        row_rec = QHBoxLayout(rec_frame)
        row_rec.setContentsMargins(12, 6, 12, 6)
        row_rec.setSpacing(10)

        self.chk_recorrente = QCheckBox("Lançamento Recorrente Mensal")
        self.chk_recorrente.setCursor(Qt.PointingHandCursor)
        self.chk_recorrente.stateChanged.connect(self.ao_alternar_recorrente)
        row_rec.addWidget(self.chk_recorrente)

        self.lbl_dia_venc = QLabel("Dia do Vencimento Mensal:")
        self.lbl_dia_venc.setStyleSheet("font-size: 12px; color: #475569; font-weight: 600; border: none; background: transparent;")
        row_rec.addWidget(self.lbl_dia_venc)

        self.spn_dia_venc = QSpinBox()
        self.spn_dia_venc.setRange(1, 31)
        self.spn_dia_venc.setValue(10)
        self.spn_dia_venc.setFixedWidth(80)
        self.spn_dia_venc.setFixedHeight(32)
        self.spn_dia_venc.setAlignment(Qt.AlignCenter)
        self.spn_dia_venc.setStyleSheet("""
            QSpinBox {
                background-color: #ffffff;
                color: #0f766e;
                font-size: 13px;
                font-weight: bold;
                border: 1px solid #0f766e;
                border-radius: 6px;
                padding: 2px 4px;
            }
            QSpinBox:focus {
                border: 2px solid #0d9488;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 18px;
                background-color: #f1f5f9;
                border: 1px solid #cbd5e1;
                border-radius: 2px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #e2e8f0;
            }
        """)
        self.spn_dia_venc.setToolTip("Dia do mês em que este lançamento deve vencer e gerar alerta prévio (1 a 31)")
        row_rec.addWidget(self.spn_dia_venc)

        row_rec.addStretch()
        layout.addWidget(rec_frame)

        # Linha 6: Painel Documental (Nota Fiscal e Comprovante de Anexo)
        doc_frame = QFrame()
        doc_frame.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
            }
        """)
        row_doc = QHBoxLayout(doc_frame)
        row_doc.setContentsMargins(12, 6, 12, 6)
        row_doc.setSpacing(10)

        self.chk_nota_fiscal = QCheckBox("Nota Fiscal (NF-e)")
        self.chk_nota_fiscal.setFixedWidth(165)
        self.chk_nota_fiscal.setCursor(Qt.PointingHandCursor)
        row_doc.addWidget(self.chk_nota_fiscal)

        self.txt_num_nf = QLineEdit()
        self.txt_num_nf.setPlaceholderText("Nº NF-e (opcional)")
        self.txt_num_nf.setFixedWidth(130)
        row_doc.addWidget(self.txt_num_nf)

        row_doc.addSpacing(10)

        self.lbl_anexo_status = QLabel("Nenhum arquivo anexado")
        self.lbl_anexo_status.setStyleSheet("color: #64748b; font-size: 12px; border: none; background: transparent;")
        self.lbl_anexo_status.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        row_doc.addWidget(self.lbl_anexo_status)

        btn_anexar = QPushButton("📎 Anexar Arquivo")
        btn_anexar.setObjectName("secondaryBtn")
        btn_anexar.setStyleSheet("padding: 5px 12px; font-size: 12px;")
        btn_anexar.setFixedWidth(130)
        btn_anexar.clicked.connect(self.selecionar_anexo)
        row_doc.addWidget(btn_anexar)

        layout.addWidget(doc_frame)

        # Linha 6: Observações
        v_obs = QVBoxLayout()
        v_obs.setSpacing(4)
        lbl_obs = QLabel("Observações Adicionais:")
        lbl_obs.setStyleSheet("font-weight: 600; color: #334155;")
        v_obs.addWidget(lbl_obs)
        self.txt_obs = QLineEdit()
        self.txt_obs.setPlaceholderText("Informações sobre banco, conta, código de autorização...")
        v_obs.addWidget(self.txt_obs)
        layout.addLayout(v_obs)

        layout.addStretch()

        # Botões de Ação
        btn_box = QHBoxLayout()
        btn_box.setSpacing(12)
        btn_box.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("secondaryBtn")
        btn_cancel.setFixedWidth(110)
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_save = QPushButton("Salvar Lançamento")
        btn_save.setObjectName("primaryBtn")
        btn_save.setFixedWidth(160)
        btn_save.clicked.connect(self.salvar)
        btn_box.addWidget(btn_save)

        layout.addLayout(btn_box)

        # Configura estado inicial dos seletores
        self.ao_mudar_tipo()
        self.ao_mudar_status()

        # Se for edição, preenche dados existentes
        if self.is_edit and self.transaction:
            t = self.transaction
            self.txt_desc.setText(t["descricao"])
            self.cmb_tipo.blockSignals(True)
            self.cmb_tipo.setCurrentText(t["tipo"])
            self.cmb_tipo.blockSignals(False)

            self.carregar_categorias(selecionar=t.get("categoria"))

            self.spn_valor.setValue(float(t["valor"]))
            self.cmb_status.setCurrentText(t.get("status", "Pago"))
            self.cmb_forma.setCurrentText(t.get("forma_pagamento", "Pix"))
            self.cmb_parcelas.setCurrentText(f"{t.get('parcelas', 1)}x")

            # Datas
            try:
                d_c = datetime.strptime(str(t["data_competencia"])[:10], "%Y-%m-%d").date()
                self.dt_comp.setDate(QDate(d_c.year, d_c.month, d_c.day))
            except Exception:
                pass

            if t.get("data_vencimento"):
                try:
                    d_v = datetime.strptime(str(t["data_vencimento"])[:10], "%Y-%m-%d").date()
                    self.dt_venc.setDate(QDate(d_v.year, d_v.month, d_v.day))
                except Exception:
                    pass

            if t.get("data_pagamento"):
                try:
                    d_p = datetime.strptime(str(t["data_pagamento"])[:10], "%Y-%m-%d").date()
                    self.dt_pag.setDate(QDate(d_p.year, d_p.month, d_p.day))
                except Exception:
                    pass

            # Paciente
            p_id = t.get("patient_id")
            if p_id:
                for idx in range(self.cmb_paciente.count()):
                    if self.cmb_paciente.itemData(idx) == p_id:
                        self.cmb_paciente.setCurrentIndex(idx)
                        break

            # Recorrência
            rec = bool(t.get("recorrente", 0))
            self.chk_recorrente.setChecked(rec)
            if t.get("data_vencimento"):
                try:
                    self.spn_dia_venc.setValue(int(str(t["data_vencimento"])[8:10]))
                except Exception:
                    pass

            # Nota Fiscal
            self.chk_nota_fiscal.setChecked(bool(t.get("nota_fiscal_emitida", 0)))
            self.txt_num_nf.setText(t.get("numero_nota_fiscal") or "")

            # Anexo
            comp = t.get("comprovante_path")
            if comp:
                self.anexo_caminho = comp
                self.lbl_anexo_status.setText(f"✓ {Path(comp).name}")

            self.txt_obs.setText(t.get("observacoes") or "")

        elif not self.is_edit and self.initial_data:
            init = self.initial_data
            if "descricao" in init:
                self.txt_desc.setText(init["descricao"])
            if "categoria" in init:
                self.carregar_categorias(selecionar=init["categoria"])
            if "valor" in init and init["valor"]:
                self.spn_valor.setValue(float(init["valor"]))
            if "patient_id" in init and init["patient_id"]:
                p_id = init["patient_id"]
                for idx in range(self.cmb_paciente.count()):
                    if self.cmb_paciente.itemData(idx) == p_id:
                        self.cmb_paciente.setCurrentIndex(idx)
                        break

        self.ao_alternar_recorrente()

    def ao_alternar_recorrente(self):
        ativo = self.chk_recorrente.isChecked()
        self.lbl_dia_venc.setVisible(ativo)
        self.spn_dia_venc.setVisible(ativo)

    def ao_mudar_tipo(self):
        cat_atual = self.cmb_cat.currentText() if self.cmb_cat.count() > 0 else None
        self.carregar_categorias(selecionar=cat_atual)
        eh_rec = (self.cmb_tipo.currentText() == "Receita")
        if eh_rec:
            self.lbl_comp.setText("Data do Atendimento (*):")
            self.dt_comp.setToolTip("Data em que o atendimento clínico ou procedimento odontológico foi realizado")
        else:
            self.lbl_comp.setText("Data da Compra / Despesa (*):")
            self.dt_comp.setToolTip("Data em que o insumo odontológico foi comprado ou a despesa/custo ocorreu")

    def ao_mudar_status(self):
        eh_pago = (self.cmb_status.currentText() == "Pago")
        self.dt_pag.setEnabled(eh_pago)

    def carregar_categorias(self, selecionar: Optional[str] = None):
        tipo = self.cmb_tipo.currentText()
        cats = list_financial_categories(tipo)
        self.cmb_cat.blockSignals(True)
        self.cmb_cat.clear()
        self.cmb_cat.addItems(cats)
        if selecionar:
            idx = self.cmb_cat.findText(selecionar)
            if idx >= 0:
                self.cmb_cat.setCurrentIndex(idx)
            else:
                self.cmb_cat.addItem(selecionar)
                self.cmb_cat.setCurrentText(selecionar)
        self.cmb_cat.blockSignals(False)

    def carregar_pacientes(self):
        self.cmb_paciente.clear()
        self.cmb_paciente.addItem("Nenhum (Lançamento da Clínica / Avulso)", None)
        pacientes = search_patients()
        for p in pacientes:
            self.cmb_paciente.addItem(f"{p['nome']} (CPF: {p.get('cpf') or 'N/I'})", p["id"])

    def selecionar_anexo(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Comprovante / Recibo", "",
            "Documentos e Imagens (*.pdf *.png *.jpg *.jpeg *.webp)"
        )
        if caminho:
            try:
                UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
                ext = Path(caminho).suffix.lower()
                nome_dest = f"comp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{Path(caminho).name}"
                dest_path = UPLOADS_DIR / nome_dest
                shutil.copy2(caminho, dest_path)
                self.anexo_caminho = str(dest_path)
                self.lbl_anexo_status.setText(f"✓ {dest_path.name}")
            except Exception as e:
                QMessageBox.warning(self, "Aviso", f"Erro ao anexar arquivo: {e}")

    def salvar(self):
        desc = self.txt_desc.text().strip()
        if not desc:
            QMessageBox.warning(self, "Aviso", "A descrição do lançamento é obrigatória.")
            return

        tipo = self.cmb_tipo.currentText()
        cat = self.cmb_cat.currentText()
        valor = self.spn_valor.value()
        forma = self.cmb_forma.currentText()
        status = self.cmb_status.currentText()
        parcelas_txt = self.cmb_parcelas.currentText().replace("x", "")
        parcelas = int(parcelas_txt) if parcelas_txt.isdigit() else 1

        d_comp = self.dt_comp.date()
        str_comp = f"{d_comp.year():04d}-{d_comp.month():02d}-{d_comp.day():02d}"

        d_venc = self.dt_venc.date()
        str_venc = f"{d_venc.year():04d}-{d_venc.month():02d}-{d_venc.day():02d}"

        str_pag = None
        if status == "Pago":
            d_pag = self.dt_pag.date()
            str_pag = f"{d_pag.year():04d}-{d_pag.month():02d}-{d_pag.day():02d}"

        patient_id = None
        txt_pac = self.cmb_paciente.currentText().strip()
        if txt_pac and not txt_pac.startswith("Nenhum"):
            for idx in range(self.cmb_paciente.count()):
                if self.cmb_paciente.itemText(idx).lower() == txt_pac.lower():
                    patient_id = self.cmb_paciente.itemData(idx)
                    break
            else:
                patient_id = self.cmb_paciente.currentData()
        obs = self.txt_obs.text().strip()
        nf_emitida = 1 if self.chk_nota_fiscal.isChecked() else 0
        num_nf = self.txt_num_nf.text().strip() or None
        recorrente = 1 if self.chk_recorrente.isChecked() else 0
        dia_venc_rec = self.spn_dia_venc.value() if recorrente else None

        if self.is_edit and self.transaction:
            ok, msg = update_transaction(
                self.transaction["id"], tipo, cat, desc, valor, str_comp,
                str_venc, str_pag, status, forma, parcelas, patient_id,
                self.anexo_caminho, nf_emitida, num_nf, obs,
                self.current_user["id"], self.current_user["nome"]
            )
        else:
            ok, msg, _ = create_transaction(
                tipo, cat, desc, valor, str_comp, str_venc, str_pag,
                status, forma, parcelas, patient_id, None, self.anexo_caminho,
                nf_emitida, num_nf, recorrente, dia_venc_rec, obs,
                self.current_user["id"], self.current_user["nome"]
            )

        if ok:
            QMessageBox.information(self, "Sucesso", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Erro", msg)


# -------------------------------------------------------------
# DIÁLOGO DE BAIXA RÁPIDA (MARCAR COMO PAGO)
# -------------------------------------------------------------

class MarkAsPaidDialog(QDialog):
    """Diálogo ágil para confirmar recebimento / pagamento de lançamento pendente."""
    def __init__(self, transaction: dict, current_user: dict, parent=None):
        super().__init__(parent)
        self.transaction = transaction
        self.current_user = current_user
        self.setWindowTitle(f"Confirmar Baixa: {transaction['descricao']}")
        self.setFixedSize(460, 340)
        self.setStyleSheet(FINANCIAL_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        tipo = self.transaction["tipo"]
        cor_tema = "#059669" if tipo == "Receita" else "#dc2626"
        icone = "💰" if tipo == "Receita" else "💸"

        title = QLabel(f"{icone} Confirmar {'Recebimento' if tipo == 'Receita' else 'Pagamento'}")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {cor_tema};")
        layout.addWidget(title)

        val_fmt = f"{self.transaction['valor']:.2f}".replace('.', ',')
        lbl_info = QLabel(
            f"<b>Lançamento:</b> {self.transaction['descricao']}<br>"
            f"<b>Categoria:</b> {self.transaction['categoria']}<br>"
            f"<b>Valor:</b> <span style='font-size: 15px; font-weight: bold; color: {cor_tema};'>R$ {val_fmt}</span>"
        )
        lbl_info.setStyleSheet("font-size: 13px; line-height: 140%;")
        layout.addWidget(lbl_info)

        row_f = QHBoxLayout()
        v_f = QVBoxLayout()
        v_f.addWidget(QLabel("Forma de Pagamento:"))
        self.cmb_forma = QComboBox()
        self.cmb_forma.setView(QListView())
        self.cmb_forma.addItems(FORMAS_PAGAMENTO)
        self.cmb_forma.setCurrentText(self.transaction.get("forma_pagamento", "Pix"))
        v_f.addWidget(self.cmb_forma)
        row_f.addLayout(v_f)

        v_d = QVBoxLayout()
        v_d.addWidget(QLabel("Data Efetiva:"))
        self.dt_pag = CustomDateEdit()
        self.dt_pag.setDate(QDate.currentDate())
        v_d.addWidget(self.dt_pag)
        row_f.addLayout(v_d)

        layout.addLayout(row_f)

        # Opção Nota Fiscal na Baixa
        row_nf = QHBoxLayout()
        self.chk_nf = QCheckBox("Nota Fiscal (NF-e)")
        self.chk_nf.setCursor(Qt.PointingHandCursor)
        self.chk_nf.setChecked(bool(self.transaction.get("nota_fiscal_emitida", 0)))
        row_nf.addWidget(self.chk_nf)

        self.txt_num_nf = QLineEdit()
        self.txt_num_nf.setPlaceholderText("Nº NF-e (opcional)")
        self.txt_num_nf.setText(self.transaction.get("numero_nota_fiscal") or "")
        self.txt_num_nf.setMaximumWidth(160)
        row_nf.addWidget(self.txt_num_nf)
        row_nf.addStretch()
        layout.addLayout(row_nf)

        layout.addStretch()

        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("secondaryBtn")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_confirm = QPushButton("✓ Confirmar Baixa")
        btn_confirm.setObjectName("revenueBtn" if tipo == "Receita" else "expenseBtn")
        btn_confirm.clicked.connect(self.confirmar)
        btn_box.addWidget(btn_confirm)

        layout.addLayout(btn_box)

    def confirmar(self):
        forma = self.cmb_forma.currentText()
        d_pag = self.dt_pag.date()
        str_pag = f"{d_pag.year():04d}-{d_pag.month():02d}-{d_pag.day():02d}"
        nf_emitida = 1 if self.chk_nf.isChecked() else 0
        num_nf = self.txt_num_nf.text().strip() or None

        ok, msg = marcar_como_pago(
            self.transaction["id"], str_pag, forma,
            nf_emitida, num_nf,
            self.current_user["id"], self.current_user["nome"]
        )
        if ok:
            QMessageBox.information(self, "Sucesso", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Aviso", msg)


# -------------------------------------------------------------
# DEMONSTRATIVO FINANCEIRO / DRE RESUMIDO
# -------------------------------------------------------------

class FinancialSummaryDialog(QDialog):
    """Diálogo Gerencial com DRE Simplificado e Totais por Meio de Pagamento."""
    def __init__(self, data_inicio: Optional[str] = None, data_fim: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.data_inicio = data_inicio
        self.data_fim = data_fim
        self.setWindowTitle("Demonstrativo Financeiro e DRE Simplificado")
        self.setFixedSize(650, 560)
        self.setStyleSheet(FINANCIAL_STYLE)
        self.init_ui()
        self.carregar_dados()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        title = QLabel("📊 Demonstrativo de Resultados (DRE)")
        title.setStyleSheet("font-size: 17px; font-weight: bold; color: #166260;")
        layout.addWidget(title)

        per_txt = f"Período: {self.formatar_data_br(self.data_inicio)} até {self.formatar_data_br(self.data_fim)}" if self.data_inicio else "Período: Geral acumulado"
        self.lbl_periodo = QLabel(per_txt)
        self.lbl_periodo.setStyleSheet("color: #64748b; font-size: 13px;")
        layout.addWidget(self.lbl_periodo)

        # Área de Rolagem com Resumo
        scroll = QScrollArea()
        scroll.setObjectName("scrollDRE")
        scroll.setWidgetResizable(True)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(16, 16, 16, 16)
        self.content_layout.setSpacing(14)
        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_close = QPushButton("Fechar")
        btn_close.setObjectName("primaryBtn")
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)

    def formatar_data_br(self, d_str: Optional[str]) -> str:
        if not d_str:
            return ""
        try:
            return datetime.strptime(d_str[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            return d_str

    def carregar_dados(self):
        dre = get_dre_resumido(self.data_inicio, self.data_fim)

        # 1. Seção de Receitas
        lbl_rec_h = QLabel("<b>(+) RECEITAS REALIZADAS</b>")
        lbl_rec_h.setStyleSheet("font-size: 14px; color: #059669; border-bottom: 2px solid #a7f3d0; padding-bottom: 4px;")
        self.content_layout.addWidget(lbl_rec_h)

        if dre["receitas_por_categoria"]:
            for r in dre["receitas_por_categoria"]:
                pct = (r["total"] / dre["total_receitas"] * 100) if dre["total_receitas"] > 0 else 0
                lbl = QLabel(f"• {r['categoria']}: <b>R$ {r['total']:.2f}</b> ({pct:.1f}%)")
                lbl.setStyleSheet("font-size: 13px; color: #334155; margin-left: 10px;")
                self.content_layout.addWidget(lbl)
        else:
            lbl_vazio = QLabel("<i>Nenhuma receita realizada no período selecionado.</i>")
            lbl_vazio.setStyleSheet("color: #94a3b8; margin-left: 10px;")
            self.content_layout.addWidget(lbl_vazio)

        lbl_tot_rec = QLabel(f"<b>TOTAL DE RECEITAS: R$ {dre['total_receitas']:.2f}</b>")
        lbl_tot_rec.setStyleSheet("font-size: 13px; color: #059669; font-weight: bold; margin-left: 10px; margin-top: 4px;")
        self.content_layout.addWidget(lbl_tot_rec)

        self.content_layout.addSpacing(10)

        # 2. Seção de Despesas
        lbl_desp_h = QLabel("<b>(-) DESPESAS E CUSTOS OPERACIONAIS</b>")
        lbl_desp_h.setStyleSheet("font-size: 14px; color: #dc2626; border-bottom: 2px solid #fecaca; padding-bottom: 4px;")
        self.content_layout.addWidget(lbl_desp_h)

        if dre["despesas_por_categoria"]:
            for d in dre["despesas_por_categoria"]:
                pct = (d["total"] / dre["total_despesas"] * 100) if dre["total_despesas"] > 0 else 0
                lbl = QLabel(f"• {d['categoria']}: <b>R$ {d['total']:.2f}</b> ({pct:.1f}%)")
                lbl.setStyleSheet("font-size: 13px; color: #334155; margin-left: 10px;")
                self.content_layout.addWidget(lbl)
        else:
            lbl_vazio = QLabel("<i>Nenhuma despesa paga no período selecionado.</i>")
            lbl_vazio.setStyleSheet("color: #94a3b8; margin-left: 10px;")
            self.content_layout.addWidget(lbl_vazio)

        lbl_tot_desp = QLabel(f"<b>TOTAL DE DESPESAS: R$ {dre['total_despesas']:.2f}</b>")
        lbl_tot_desp.setStyleSheet("font-size: 13px; color: #dc2626; font-weight: bold; margin-left: 10px; margin-top: 4px;")
        self.content_layout.addWidget(lbl_tot_desp)

        self.content_layout.addSpacing(10)

        # 3. Resultado Líquido
        res = dre["resultado_liquido"]
        cor_res = "#0f766e" if res >= 0 else "#dc2626"
        sinal = "+" if res >= 0 else ""
        card_res = QFrame()
        card_res.setObjectName("cardResDRE")
        card_res.setStyleSheet(f"""
            QFrame#cardResDRE {{
                background-color: #f8fafc;
                border: 2px solid {cor_res};
                border-radius: 8px;
            }}
            QFrame#cardResDRE QLabel {{
                border: none;
                background: transparent;
                padding: 0px;
            }}
        """)
        l_res = QVBoxLayout(card_res)
        lbl_res_t = QLabel("<b>(=) RESULTADO LÍQUIDO DO PERÍODO</b>")
        lbl_res_t.setStyleSheet("font-size: 12px; color: #475569;")
        l_res.addWidget(lbl_res_t)

        lbl_res_v = QLabel(f"{sinal}R$ {res:.2f}".replace('.', ','))
        lbl_res_v.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {cor_res};")
        l_res.addWidget(lbl_res_v)
        self.content_layout.addWidget(card_res)

        self.content_layout.addSpacing(10)

        # 4. Totais por Forma de Pagamento
        lbl_forma_h = QLabel("<b>💳 RECEBIMENTOS POR MEIO DE PAGAMENTO</b>")
        lbl_forma_h.setStyleSheet("font-size: 14px; color: #0284c7; border-bottom: 2px solid #bae6fd; padding-bottom: 4px;")
        self.content_layout.addWidget(lbl_forma_h)

        if dre["formas_pagamento"]:
            for f in dre["formas_pagamento"]:
                lbl = QLabel(f"• {f['forma_pagamento']}: <b>R$ {f['total']:.2f}</b>")
                lbl.setStyleSheet("font-size: 13px; color: #334155; margin-left: 10px;")
                self.content_layout.addWidget(lbl)
        else:
            lbl_vazio = QLabel("<i>Nenhum pagamento liquidado no período.</i>")
            lbl_vazio.setStyleSheet("color: #94a3b8; margin-left: 10px;")
            self.content_layout.addWidget(lbl_vazio)

        self.content_layout.addStretch()


# -------------------------------------------------------------
# GERENCIAMENTO DE CATEGORIAS FINANCEIRAS
# -------------------------------------------------------------

class ManageFinancialCategoriesDialog(QDialog):
    """Diálogo para Criar ou Remover Categorias Financeiras."""
    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.setWindowTitle("Gerenciar Categorias Financeiras")
        self.setFixedSize(580, 500)
        self.setStyleSheet(FINANCIAL_STYLE)
        self.init_ui()
        self.carregar_categorias()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        title = QLabel("🏷️ Categorias de Receitas e Despesas")
        title.setStyleSheet("font-size: 17px; font-weight: bold; color: #166260;")
        layout.addWidget(title)

        # Adicionar nova categoria
        add_box = QHBoxLayout()
        self.txt_nova = QLineEdit()
        self.txt_nova.setPlaceholderText("Nome da nova categoria...")
        add_box.addWidget(self.txt_nova)

        self.cmb_tipo_novo = QComboBox()
        self.cmb_tipo_novo.addItems(["Receita", "Despesa"])
        self.cmb_tipo_novo.setFixedWidth(110)
        add_box.addWidget(self.cmb_tipo_novo)

        btn_add = QPushButton("+ Adicionar")
        btn_add.setObjectName("primaryBtn")
        btn_add.clicked.connect(self.adicionar_categoria)
        add_box.addWidget(btn_add)
        layout.addLayout(add_box)

        # Tabela de categorias
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Tipo", "Nome da Categoria", "Lançamentos"])
        self.table.setColumnHidden(0, True)

        h = self.table.horizontalHeader()
        h.setSectionResizeMode(1, QHeaderView.Interactive)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        h.setSectionResizeMode(3, QHeaderView.Interactive)
        self.table.setColumnWidth(1, 95)
        self.table.setColumnWidth(3, 110)

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                font-weight: bold;
                color: #334155;
                padding: 6px;
                border: none;
                border-bottom: 2px solid #cbd5e1;
            }
        """)
        layout.addWidget(self.table)

        # Ações na categoria selecionada
        act_box = QHBoxLayout()
        btn_excluir = QPushButton("🗑️ Remover Categoria")
        btn_excluir.setObjectName("dangerBtn")
        btn_excluir.clicked.connect(self.remover_selecionada)
        act_box.addWidget(btn_excluir)

        act_box.addStretch()

        btn_fechar = QPushButton("Concluir")
        btn_fechar.setObjectName("primaryBtn")
        btn_fechar.clicked.connect(self.accept)
        act_box.addWidget(btn_fechar)

        layout.addLayout(act_box)

    def carregar_categorias(self):
        cats = list_financial_categories_detailed()
        self.table.setRowCount(len(cats))
        for row_idx, c in enumerate(cats):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(c["id"])))

            tipo_item = QTableWidgetItem(c["tipo"])
            tipo_item.setTextAlignment(Qt.AlignCenter)
            tipo_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            tipo_item.setForeground(QColor("#059669" if c["tipo"] == "Receita" else "#dc2626"))
            self.table.setItem(row_idx, 1, tipo_item)

            item_nome = QTableWidgetItem(c["nome"])
            self.table.setItem(row_idx, 2, item_nome)

            total = c.get("total_lancamentos", 0)
            item_tot = QTableWidgetItem(f"{total}")
            item_tot.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 3, item_tot)

            self.table.item(row_idx, 0).setData(Qt.UserRole, c)

    def adicionar_categoria(self):
        nome = self.txt_nova.text().strip()
        tipo = self.cmb_tipo_novo.currentText()
        if not nome:
            QMessageBox.warning(self, "Aviso", "Digite o nome da categoria para adicionar.")
            return

        ok, msg, _ = create_financial_category(nome, tipo, self.current_user["id"], self.current_user["nome"])
        if ok:
            self.txt_nova.clear()
            self.carregar_categorias()
        else:
            QMessageBox.warning(self, "Aviso", msg)

    def remover_selecionada(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione uma categoria para remover.")
            return
        row = selected[0].row()
        c = self.table.item(row, 0).data(Qt.UserRole)
        cat_id = c["id"]
        cat_nome = c["nome"]

        if cat_nome in ("Outras Receitas", "Outras Despesas", "Sublocação", "Sublocação de Consultório (Sala 2)"):
            QMessageBox.warning(self, "Aviso", f"A categoria padrão '{cat_nome}' não pode ser removida.")
            return

        msg = f"Deseja realmente remover a categoria '{cat_nome}'? Os lançamentos existentes serão transferidos para a categoria padrão."
        if perguntar_sim_nao(self, "Remover Categoria", msg):
            ok, msg_res = delete_financial_category(cat_id, self.current_user["id"], self.current_user["nome"])
            if ok:
                self.carregar_categorias()
            else:
                QMessageBox.warning(self, "Aviso", msg_res)


# -------------------------------------------------------------
# DIÁLOGO DE PERÍODO PERSONALIZADO
# -------------------------------------------------------------

class CustomPeriodDialog(QDialog):
    """Diálogo limpo e dedicado para escolher o período personalizado sem quebrar o layout."""
    def __init__(self, data_inicio: Optional[str] = None, data_fim: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecionar Período Personalizado")
        self.setFixedSize(400, 220)
        self.setStyleSheet(FINANCIAL_STYLE)
        self.data_ini_res = data_inicio
        self.data_fim_res = data_fim
        self.init_ui(data_inicio, data_fim)

    def init_ui(self, data_inicio, data_fim):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        title = QLabel("📅 Filtrar por Período Personalizado")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #166260;")
        layout.addWidget(title)

        form_l = QHBoxLayout()
        v_de = QVBoxLayout()
        v_de.addWidget(QLabel("Data Inicial:"))
        self.dt_ini = CustomDateEdit()
        try:
            d_i = datetime.strptime(data_inicio[:10], "%Y-%m-%d").date() if data_inicio else date.today().replace(day=1)
        except Exception:
            d_i = date.today().replace(day=1)
        self.dt_ini.setDate(QDate(d_i.year, d_i.month, d_i.day))
        v_de.addWidget(self.dt_ini)
        form_l.addLayout(v_de)

        v_ate = QVBoxLayout()
        v_ate.addWidget(QLabel("Data Final:"))
        self.dt_fim = CustomDateEdit()
        try:
            d_f = datetime.strptime(data_fim[:10], "%Y-%m-%d").date() if data_fim else date.today()
        except Exception:
            d_f = date.today()
        self.dt_fim.setDate(QDate(d_f.year, d_f.month, d_f.day))
        v_ate.addWidget(self.dt_fim)
        form_l.addLayout(v_ate)
        layout.addLayout(form_l)

        layout.addStretch()

        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("secondaryBtn")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_ok = QPushButton("Aplicar Filtro")
        btn_ok.setObjectName("primaryBtn")
        btn_ok.clicked.connect(self.aplicar)
        btn_box.addWidget(btn_ok)
        layout.addLayout(btn_box)

    def aplicar(self):
        d_i = self.dt_ini.date()
        d_f = self.dt_fim.date()
        if d_i > d_f:
            QMessageBox.warning(self, "Aviso", "A data inicial não pode ser posterior à data final.")
            return
        self.data_ini_res = f"{d_i.year():04d}-{d_i.month():02d}-{d_i.day():02d}"
        self.data_fim_res = f"{d_f.year():04d}-{d_f.month():02d}-{d_f.day():02d}"
        self.accept()


# -------------------------------------------------------------
# TELA PRINCIPAL DO MÓDULO FINANCEIRO
# -------------------------------------------------------------

class FinancialView(QWidget):
    """Tela Principal de Gestão Financeira, Fluxo de Caixa e Meios de Pagamento."""
    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.filtro_tipo = "Todos"
        self.init_ui()
        self.definir_periodo("mes_atual")
        self.carregar_dados()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        self.setStyleSheet(FINANCIAL_STYLE)

        # 1. Cabeçalho Superior
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Gestão Financeira e Fluxo de Caixa")
        title.setStyleSheet("font-size: 19px; font-weight: bold; color: #166260;")
        sub = QLabel("Central de receitas, sublocação de consultório, custos e controle de pagamentos.")
        sub.setStyleSheet("color: #64748b; font-size: 13px;")
        sub.setWordWrap(True)
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        btn_nova_receita = QPushButton("💰 + Nova Receita")
        btn_nova_receita.setObjectName("revenueBtn")
        btn_nova_receita.clicked.connect(lambda: self.abrir_novo_lancamento("Receita"))
        header_layout.addWidget(btn_nova_receita)

        btn_nova_despesa = QPushButton("💸 - Nova Despesa")
        btn_nova_despesa.setObjectName("expenseBtn")
        btn_nova_despesa.clicked.connect(lambda: self.abrir_novo_lancamento("Despesa"))
        header_layout.addWidget(btn_nova_despesa)

        layout.addLayout(header_layout)

        # 2. Cards Superiores de Indicadores (KPIs)
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(10)

        self.card_rec = self.criar_card_kpi("💰 Total de Receitas", "R$ 0,00", "Entradas liquidadas", "#059669")
        kpi_layout.addWidget(self.card_rec)

        self.card_desp = self.criar_card_kpi("💸 Total de Despesas", "R$ 0,00", "Saídas e custos pagos", "#dc2626")
        kpi_layout.addWidget(self.card_desp)

        self.card_saldo = self.criar_card_kpi("📈 Saldo Líquido", "R$ 0,00", "Receitas - Despesas", "#0f766e")
        kpi_layout.addWidget(self.card_saldo)

        self.card_pend = self.criar_card_kpi("⏳ A Receber / Pagar", "R$ 0,00", "Pendências em aberto", "#0284c7")
        kpi_layout.addWidget(self.card_pend)

        layout.addLayout(kpi_layout)

        # 3. Barra de Seleção de Período e Pílulas Rápidas
        period_bar = QHBoxLayout()
        period_bar.setSpacing(8)

        lbl_per = QLabel("Período:")
        lbl_per.setStyleSheet("color: #475569; font-weight: bold; font-size: 13px;")
        period_bar.addWidget(lbl_per)

        self.cmb_periodo = QComboBox()
        self.cmb_periodo.setView(QListView())
        self.cmb_periodo.addItems([
            "Este Mês",
            "Hoje",
            "Esta Semana",
            "Mês Anterior",
            "Este Ano",
            "Todo o Histórico",
            "Personalizado..."
        ])
        self.cmb_periodo.setFixedWidth(170)
        self.cmb_periodo.currentIndexChanged.connect(self.ao_mudar_periodo_combo)
        period_bar.addWidget(self.cmb_periodo)

        period_bar.addSpacing(10)

        # Pílulas
        self.pill_todos = QPushButton("🌐 Todos")
        self.pill_todos.setObjectName("pillBtn")
        self.pill_todos.setCheckable(True)
        self.pill_todos.setChecked(True)
        self.pill_todos.clicked.connect(lambda: self.mudar_filtro_tipo("Todos"))
        period_bar.addWidget(self.pill_todos)

        self.pill_rec = QPushButton("💰 Receitas")
        self.pill_rec.setObjectName("pillBtn")
        self.pill_rec.setCheckable(True)
        self.pill_rec.clicked.connect(lambda: self.mudar_filtro_tipo("Receita"))
        period_bar.addWidget(self.pill_rec)

        self.pill_desp = QPushButton("💸 Despesas")
        self.pill_desp.setObjectName("pillBtn")
        self.pill_desp.setCheckable(True)
        self.pill_desp.clicked.connect(lambda: self.mudar_filtro_tipo("Despesa"))
        period_bar.addWidget(self.pill_desp)

        self.pill_pend = QPushButton("⏳ Pendentes")
        self.pill_pend.setObjectName("pillBtn")
        self.pill_pend.setCheckable(True)
        self.pill_pend.clicked.connect(lambda: self.mudar_filtro_tipo("Pendente"))
        period_bar.addWidget(self.pill_pend)

        period_bar.addStretch()

        self.btn_dre = QPushButton("DRE Simplificado")
        self.btn_dre.setObjectName("secondaryBtn")
        self.btn_dre.setToolTip("Visualizar demonstrativo de resultados e receitas por meio de pagamento")
        self.btn_dre.clicked.connect(self.abrir_dre)
        period_bar.addWidget(self.btn_dre)

        # Restrição de Perfil: Secretária não tem acesso a relatórios e DRE da clínica
        if self.current_user.get("perfil") == "secretaria":
            self.btn_dre.setVisible(False)
            self.card_rec.setVisible(False)
            self.card_saldo.setVisible(False)

        layout.addLayout(period_bar)

        # 4. Barra de Pesquisa, Categoria e Meio de Pagamento
        search_bar = QFrame()
        search_bar.setObjectName("barNav")
        search_layout = QHBoxLayout(search_bar)
        search_layout.setContentsMargins(10, 6, 10, 6)
        search_layout.setSpacing(8)

        lbl_icon = QLabel("🔍")
        search_layout.addWidget(lbl_icon)

        self.timer_busca = QTimer(self)
        self.timer_busca.setSingleShot(True)
        self.timer_busca.setInterval(250)
        self.timer_busca.timeout.connect(self.carregar_dados)

        self.txt_busca = QLineEdit()
        self.txt_busca.setPlaceholderText("Pesquisar por descrição, paciente ou categoria...")
        self.txt_busca.setStyleSheet("border: none; background: transparent; font-size: 13px;")
        self.txt_busca.textChanged.connect(self.timer_busca.start)
        search_layout.addWidget(self.txt_busca)

        lbl_c = QLabel("Categoria:")
        lbl_c.setStyleSheet("color: #475569; font-weight: 600; font-size: 12px;")
        search_layout.addWidget(lbl_c)

        self.cmb_filtro_cat = QComboBox()
        self.cmb_filtro_cat.setView(QListView())
        self.cmb_filtro_cat.setFixedWidth(190)
        self.atualizar_combos_categorias()
        self.cmb_filtro_cat.currentIndexChanged.connect(self.carregar_dados)
        search_layout.addWidget(self.cmb_filtro_cat)

        lbl_f = QLabel("Pagamento:")
        lbl_f.setStyleSheet("color: #475569; font-weight: 600; font-size: 12px;")
        search_layout.addWidget(lbl_f)

        self.cmb_filtro_forma = QComboBox()
        self.cmb_filtro_forma.setView(QListView())
        self.cmb_filtro_forma.addItem("Todas")
        self.cmb_filtro_forma.addItems(FORMAS_PAGAMENTO)
        self.cmb_filtro_forma.setFixedWidth(145)
        self.cmb_filtro_forma.currentIndexChanged.connect(self.carregar_dados)
        search_layout.addWidget(self.cmb_filtro_forma)

        btn_cat = QPushButton("🏷️ Categorias")
        btn_cat.setObjectName("secondaryBtn")
        btn_cat.clicked.connect(self.abrir_gerenciar_categorias)
        search_layout.addWidget(btn_cat)

        btn_limpar = QPushButton("Limpar")
        btn_limpar.setObjectName("secondaryBtn")
        btn_limpar.clicked.connect(self.limpar_filtros)
        search_layout.addWidget(btn_limpar)

        layout.addWidget(search_bar)

        # 5. Tabela de Lançamentos Financeiros
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Data", "Tipo", "Descrição / Categoria",
            "Paciente / Origem", "Valor (R$)", "Forma Pagto", "Status"
        ])
        self.table.setColumnHidden(0, True)

        h = self.table.horizontalHeader()
        h.setMinimumSectionSize(80)
        h.setSectionResizeMode(1, QHeaderView.Interactive)
        h.setSectionResizeMode(2, QHeaderView.Interactive)
        h.setSectionResizeMode(3, QHeaderView.Stretch)
        h.setSectionResizeMode(4, QHeaderView.Interactive)
        h.setSectionResizeMode(5, QHeaderView.Interactive)
        h.setSectionResizeMode(6, QHeaderView.Interactive)
        h.setSectionResizeMode(7, QHeaderView.Interactive)

        self.table.setColumnWidth(1, 95)
        self.table.setColumnWidth(2, 95)
        self.table.setColumnWidth(4, 140)
        self.table.setColumnWidth(5, 115)
        self.table.setColumnWidth(6, 120)
        self.table.setColumnWidth(7, 120)

        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self.abrir_editar_selecionado)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                color: #0f172a;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                font-weight: bold;
                color: #334155;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #cbd5e1;
            }
            QTableWidget::item {
                padding: 6px;
            }
        """)
        layout.addWidget(self.table)

        # 6. Barra de Ações Inferior
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(8)

        self.btn_baixa = QPushButton("✓ Marcar como Pago")
        self.btn_baixa.setObjectName("primaryBtn")
        self.btn_baixa.clicked.connect(self.abrir_baixa_selecionada)
        bottom_bar.addWidget(self.btn_baixa)

        btn_edit = QPushButton("✏️ Editar Lançamento")
        btn_edit.setObjectName("secondaryBtn")
        btn_edit.clicked.connect(self.abrir_editar_selecionado)
        bottom_bar.addWidget(btn_edit)

        self.btn_ver_anexo = QPushButton("📎 Ver Comprovante")
        self.btn_ver_anexo.setObjectName("secondaryBtn")
        self.btn_ver_anexo.clicked.connect(self.abrir_comprovante_selecionado)
        bottom_bar.addWidget(self.btn_ver_anexo)

        bottom_bar.addStretch()

        btn_del = QPushButton("Excluir Lançamento")
        btn_del.setObjectName("dangerBtn")
        btn_del.clicked.connect(self.excluir_selecionado)
        bottom_bar.addWidget(btn_del)

        layout.addLayout(bottom_bar)

    def criar_card_kpi(self, titulo: str, valor: str, subtitulo: str, cor_destaque: str) -> QFrame:
        card = QFrame()
        card.setObjectName("kpiCard")
        l = QVBoxLayout(card)
        l.setContentsMargins(12, 10, 12, 10)
        l.setSpacing(2)

        lbl_t = QLabel(titulo)
        lbl_t.setStyleSheet("font-size: 12px; font-weight: 600; color: #64748b;")
        l.addWidget(lbl_t)

        lbl_v = QLabel(valor)
        lbl_v.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {cor_destaque};")
        card.lbl_valor = lbl_v
        l.addWidget(lbl_v)

        lbl_s = QLabel(subtitulo)
        lbl_s.setStyleSheet("font-size: 11px; color: #94a3b8;")
        card.lbl_sub = lbl_s
        l.addWidget(lbl_s)
        return card

    def atualizar_combos_categorias(self):
        atual = self.cmb_filtro_cat.currentText() if hasattr(self, "cmb_filtro_cat") else ""
        if hasattr(self, "cmb_filtro_cat"):
            self.cmb_filtro_cat.blockSignals(True)
            self.cmb_filtro_cat.clear()
            self.cmb_filtro_cat.addItem("Todas as Categorias")
            for c in list_financial_categories():
                self.cmb_filtro_cat.addItem(c)
            idx = self.cmb_filtro_cat.findText(atual)
            if idx >= 0:
                self.cmb_filtro_cat.setCurrentIndex(idx)
            else:
                self.cmb_filtro_cat.setCurrentIndex(0)
            self.cmb_filtro_cat.blockSignals(False)

    def mudar_filtro_tipo(self, tipo: str):
        self.filtro_tipo = tipo
        self.pill_todos.setChecked(tipo == "Todos")
        self.pill_rec.setChecked(tipo == "Receita")
        self.pill_desp.setChecked(tipo == "Despesa")
        self.pill_pend.setChecked(tipo == "Pendente")
        self.carregar_dados()

    def ao_mudar_periodo_combo(self):
        texto = self.cmb_periodo.currentText()
        if texto.startswith("Personalizado"):
            dlg = CustomPeriodDialog(self.data_inicio, self.data_fim, parent=self)
            if dlg.exec() == QDialog.Accepted:
                self.data_inicio = dlg.data_ini_res
                self.data_fim = dlg.data_fim_res
                try:
                    d_i_fmt = datetime.strptime(self.data_inicio[:10], "%Y-%m-%d").strftime("%d/%m")
                    d_f_fmt = datetime.strptime(self.data_fim[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
                    label_custom = f"Personalizado ({d_i_fmt} a {d_f_fmt})"
                except Exception:
                    label_custom = "Personalizado..."

                self.cmb_periodo.blockSignals(True)
                idx = self.cmb_periodo.currentIndex()
                self.cmb_periodo.setItemText(idx, label_custom)
                self.cmb_periodo.blockSignals(False)
            else:
                self.cmb_periodo.blockSignals(True)
                self.cmb_periodo.setCurrentIndex(0)
                self.definir_periodo("mes_atual")
                self.cmb_periodo.blockSignals(False)
        else:
            mapa = {
                "Este Mês": "mes_atual",
                "Hoje": "hoje",
                "Esta Semana": "esta_semana",
                "Mês Anterior": "mes_anterior",
                "Este Ano": "ano_atual",
                "Todo o Histórico": "tudo"
            }
            self.definir_periodo(mapa.get(texto, "mes_atual"))
        self.carregar_dados()

    def definir_periodo(self, modo: str):
        hoje = date.today()
        if modo == "hoje":
            self.data_inicio = hoje.strftime("%Y-%m-%d")
            self.data_fim = hoje.strftime("%Y-%m-%d")
        elif modo == "esta_semana":
            d_ini = hoje - timedelta(days=hoje.weekday())
            d_fim = d_ini + timedelta(days=6)
            self.data_inicio = d_ini.strftime("%Y-%m-%d")
            self.data_fim = d_fim.strftime("%Y-%m-%d")
        elif modo == "mes_atual":
            self.data_inicio = f"{hoje.year:04d}-{hoje.month:02d}-01"
            proximo_mes = hoje.replace(day=28) + timedelta(days=4)
            ultimo_dia = (proximo_mes - timedelta(days=proximo_mes.day)).day
            self.data_fim = f"{hoje.year:04d}-{hoje.month:02d}-{ultimo_dia:02d}"
        elif modo == "mes_anterior":
            primeiro_deste_mes = hoje.replace(day=1)
            ultimo_mes_ant = primeiro_deste_mes - timedelta(days=1)
            self.data_inicio = f"{ultimo_mes_ant.year:04d}-{ultimo_mes_ant.month:02d}-01"
            self.data_fim = f"{ultimo_mes_ant.year:04d}-{ultimo_mes_ant.month:02d}-{ultimo_mes_ant.day:02d}"
        elif modo == "ano_atual":
            self.data_inicio = f"{hoje.year:04d}-01-01"
            self.data_fim = f"{hoje.year:04d}-12-31"
        else:
            self.data_inicio = None
            self.data_fim = None

    def limpar_filtros(self):
        self.txt_busca.clear()
        self.cmb_filtro_cat.setCurrentIndex(0)
        self.cmb_filtro_forma.setCurrentIndex(0)
        self.cmb_periodo.blockSignals(True)
        self.cmb_periodo.setCurrentIndex(0)
        self.cmb_periodo.setItemText(6, "Personalizado...")
        self.cmb_periodo.blockSignals(False)
        self.definir_periodo("mes_atual")
        self.mudar_filtro_tipo("Todos")

    def carregar_dados(self):
        d_ini_str = self.data_inicio
        d_fim_str = self.data_fim

        # 2. Atualiza Indicadores KPIs
        kpis = get_financial_kpis(d_ini_str, d_fim_str)
        if self.current_user.get("perfil") == "secretaria":
            self.card_rec.setVisible(False)
            self.card_saldo.setVisible(False)
            self.card_rec.lbl_valor.setText("---")
            self.card_saldo.lbl_valor.setText("---")
        else:
            self.card_rec.lbl_valor.setText(f"R$ {kpis['total_receitas']:.2f}".replace('.', ','))
            saldo = kpis["saldo_liquido"]
            sinal = "+" if saldo >= 0 else ""
            cor_saldo = "#0f766e" if saldo >= 0 else "#dc2626"
            self.card_saldo.lbl_valor.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {cor_saldo};")
            self.card_saldo.lbl_valor.setText(f"{sinal}R$ {saldo:.2f}".replace('.', ','))

        self.card_desp.lbl_valor.setText(f"R$ {kpis['total_despesas']:.2f}".replace('.', ','))

        pend_rec = kpis["pendente_receber"]
        pend_pag = kpis["pendente_pagar"]
        self.card_pend.lbl_valor.setText(f"R$ {pend_rec:.2f}".replace('.', ','))
        self.card_pend.lbl_sub.setText(f"A Receber: R$ {pend_rec:.2f} | A Pagar: R$ {pend_pag:.2f}")

        # 3. Consulta Lançamentos
        tipo_filtro = self.filtro_tipo
        status_filtro = None
        if tipo_filtro == "Pendente":
            tipo_filtro = None
            status_filtro = "Pendente"
        elif tipo_filtro == "Todos":
            tipo_filtro = None

        cat_filtro = self.cmb_filtro_cat.currentText()
        if cat_filtro == "Todas as Categorias":
            cat_filtro = None

        forma_filtro = self.cmb_filtro_forma.currentText()
        if forma_filtro == "Todas":
            forma_filtro = None

        termo = self.txt_busca.text()

        transactions = search_transactions(
            tipo=tipo_filtro,
            categoria=cat_filtro,
            status=status_filtro,
            forma_pagamento=forma_filtro,
            data_inicio=d_ini_str,
            data_fim=d_fim_str,
            termo=termo
        )

        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(transactions))

        for row_idx, t in enumerate(transactions):
            # Coluna 0: ID
            item_id = QTableWidgetItem(str(t["id"]))
            self.table.setItem(row_idx, 0, item_id)

            # Coluna 1: Data (Competência)
            raw_d = str(t["data_competencia"])
            try:
                dt_obj = datetime.strptime(raw_d[:10], "%Y-%m-%d")
                d_fmt = dt_obj.strftime("%d/%m/%Y")
            except Exception:
                d_fmt = raw_d
            item_data = QTableWidgetItem(d_fmt)
            item_data.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 1, item_data)

            # Coluna 2: Tipo com Badge
            tipo = t["tipo"]
            item_tipo = QTableWidgetItem("💰 Receita" if tipo == "Receita" else "💸 Despesa")
            item_tipo.setTextAlignment(Qt.AlignCenter)
            item_tipo.setFont(QFont("Segoe UI", 9, QFont.Bold))
            item_tipo.setForeground(QColor("#059669" if tipo == "Receita" else "#dc2626"))
            self.table.setItem(row_idx, 2, item_tipo)

            # Coluna 3: Descrição e Categoria
            desc_txt = f"{t['descricao']}  ({t['categoria']})"
            item_desc = QTableWidgetItem(desc_txt)
            item_desc.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table.setItem(row_idx, 3, item_desc)

            # Coluna 4: Paciente / Origem
            origem_txt = t.get("paciente_nome") or "-"
            if t.get("rental_id"):
                origem_txt = "🏢 Sublocação"
            item_origem = QTableWidgetItem(origem_txt)
            self.table.setItem(row_idx, 4, item_origem)

            # Coluna 5: Valor com cor
            val = float(t["valor"])
            val_fmt = f"{val:.2f}".replace('.', ',')
            sinal_val = "+" if tipo == "Receita" else "-"
            item_val = QTableWidgetItem(f"{sinal_val} R$ {val_fmt}")
            item_val.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_val.setFont(QFont("Segoe UI", 10, QFont.Bold))
            item_val.setForeground(QColor("#059669" if tipo == "Receita" else "#dc2626"))
            self.table.setItem(row_idx, 5, item_val)

            # Coluna 6: Meio de Pagamento
            forma_txt = t.get("forma_pagamento", "Pix")
            if t.get("parcelas", 1) > 1:
                forma_txt += f" ({t['parcelas']}x)"
            item_forma = QTableWidgetItem(forma_txt)
            item_forma.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 6, item_forma)

            # Coluna 7: Status (diferencia se tem Nota Fiscal emitida)
            st = t.get("status", "Pago")
            if st == "Pago":
                has_nf = bool(t.get("nota_fiscal_emitida"))
                texto_st = "✓ Pago / NF" if has_nf else "✓ Pago"
                cor_st = "#0284c7" if has_nf else "#059669"
            else:
                texto_st = "⏳ Pendente"
                cor_st = "#d97706"

            item_st = QTableWidgetItem(texto_st)
            item_st.setTextAlignment(Qt.AlignCenter)
            item_st.setFont(QFont("Segoe UI", 9, QFont.Bold))
            item_st.setForeground(QColor(cor_st))
            if t.get("numero_nota_fiscal"):
                item_st.setToolTip(f"Nota Fiscal: {t.get('numero_nota_fiscal')}")
            elif t.get("nota_fiscal_emitida"):
                item_st.setToolTip("Nota Fiscal emitida (NF-e)")
            self.table.setItem(row_idx, 7, item_st)

            self.table.item(row_idx, 0).setData(Qt.UserRole, t)

        self.table.setUpdatesEnabled(True)

    def get_selected_transaction(self) -> Optional[dict]:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione um lançamento financeiro na tabela.")
            return None
        row = selected[0].row()
        item_zero = self.table.item(row, 0)
        return item_zero.data(Qt.UserRole) if item_zero else None

    def abrir_novo_lancamento(self, tipo: str):
        dialog = TransactionFormDialog(self.current_user, tipo=tipo, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.carregar_dados()

    def abrir_editar_selecionado(self):
        t = self.get_selected_transaction()
        if not t:
            return
        t_fresh = get_transaction(t["id"]) or t
        dialog = TransactionFormDialog(self.current_user, transaction=t_fresh, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.carregar_dados()

    def abrir_baixa_selecionada(self):
        t = self.get_selected_transaction()
        if not t:
            return
        if t.get("status") == "Pago":
            QMessageBox.information(self, "Informação", "Este lançamento já consta como Pago.")
            return
        dialog = MarkAsPaidDialog(t, self.current_user, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.carregar_dados()

    def abrir_comprovante_selecionado(self):
        t = self.get_selected_transaction()
        if not t:
            return
        caminho = t.get("comprovante_path")
        if not caminho or not Path(caminho).exists():
            QMessageBox.information(self, "Aviso", "Este lançamento não possui arquivo de comprovante anexado.")
            return

        # Abre o arquivo com o visualizador padrão do Windows
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(caminho))
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível abrir o arquivo: {e}")

    def abrir_dre(self):
        if self.current_user.get("perfil") == "secretaria":
            QMessageBox.warning(
                self,
                "Acesso Restrito",
                "O Demonstrativo de Resultados (DRE) e relatórios financeiros globais são restritos à administração da clínica."
            )
            return

        if self.cmb_periodo.currentText() == "Personalizado":
            d_ini = self.dt_filtro_ini.date()
            d_fim = self.dt_filtro_fim.date()
            d_ini_str = f"{d_ini.year():04d}-{d_ini.month():02d}-{d_ini.day():02d}"
            d_fim_str = f"{d_fim.year():04d}-{d_fim.month():02d}-{d_fim.day():02d}"
        else:
            d_ini_str = self.data_inicio
            d_fim_str = self.data_fim

        dialog = FinancialSummaryDialog(d_ini_str, d_fim_str, parent=self)
        dialog.exec()

    def abrir_gerenciar_categorias(self):
        dialog = ManageFinancialCategoriesDialog(self.current_user, parent=self)
        dialog.exec()
        self.atualizar_combos_categorias()
        self.carregar_dados()

    def excluir_selecionado(self):
        t = self.get_selected_transaction()
        if not t:
            return

        msg = (
            f"Deseja realmente excluir o lançamento #{t['id']}?\n\n"
            f"• Descrição: {t['descricao']}\n"
            f"• Valor: R$ {t['valor']:.2f}\n\n"
            f"Esta operação será registrada na auditoria LGPD."
        )
        if perguntar_sim_nao(self, "Excluir Lançamento", msg):
            ok, msg_res = delete_transaction(t["id"], self.current_user["id"], self.current_user["nome"])
            if ok:
                QMessageBox.information(self, "Sucesso", msg_res)
                self.carregar_dados()
            else:
                QMessageBox.critical(self, "Erro", msg_res)
