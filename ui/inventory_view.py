from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialog, QTextEdit, QComboBox, QDateEdit,
    QFrame, QDoubleSpinBox, QSizePolicy, QScrollArea, QInputDialog
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QFont, QColor

from ui.patients_view import perguntar_sim_nao
from ui.custom_date_edit import CustomDateEdit
from services.inventory_service import (
    CATEGORIAS_ODONTO, UNIDADES_MEDIDA,
    list_categories, list_categories_detailed,
    create_category, update_category, delete_category,
    create_item, update_item, delete_item, get_item,
    search_items, add_stock_movement, list_movements,
    get_inventory_kpis
)

INVENTORY_STYLE = """
QWidget {
    font-family: 'Segoe UI', sans-serif;
    color: #0f172a;
}
QDialog {
    background-color: #f8fafc;
}
QLineEdit, QTextEdit, QDoubleSpinBox {
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
    min-width: 140px;
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
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus, QDoubleSpinBox:focus {
    border: 2px solid #2ca5a9;
    background-color: #ffffff;
}
QFrame#infoCardMov {
    background-color: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
}
QFrame#infoCardMov QLabel {
    background: transparent;
    border: none;
    padding: 0px;
}
QTableCornerButton::section {
    background-color: #f8fafc;
    border: none;
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
QPushButton#inBtn {
    background-color: #059669;
    color: #ffffff;
    font-weight: bold;
    padding: 8px 14px;
    border-radius: 6px;
    border: none;
    font-size: 13px;
}
QPushButton#inBtn:hover {
    background-color: #047857;
}
QPushButton#outBtn {
    background-color: #ea580c;
    color: #ffffff;
    font-weight: bold;
    padding: 8px 14px;
    border-radius: 6px;
    border: none;
    font-size: 13px;
}
QPushButton#outBtn:hover {
    background-color: #c2410c;
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
    padding: 7px 16px;
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
"""


class ItemFormDialog(QDialog):
    """Diálogo para Cadastrar ou Editar Material / Insumo no Estoque."""
    def __init__(self, current_user: dict, item: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.item = item
        self.is_edit = item is not None
        self.setWindowTitle("Editar Material" if self.is_edit else "Novo Material no Estoque")
        self.setFixedSize(620, 560)
        self.setStyleSheet(INVENTORY_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)

        title_txt = "Editar Dados do Material" if self.is_edit else "Cadastrar Novo Insumo Odontológico"
        title = QLabel(title_txt)
        title.setStyleSheet("font-size: 17px; font-weight: bold; color: #166260;")
        layout.addWidget(title)

        # 1. Nome do Material
        layout.addWidget(QLabel("Nome do Material / Insumo (*):"))
        self.txt_nome = QLineEdit()
        self.txt_nome.setPlaceholderText("Ex: Resina Z350 XT A2, Anestésico Mepivacaína, Luva P...")
        layout.addWidget(self.txt_nome)

        # 2. Categoria e Unidade
        row_cat = QHBoxLayout()
        v_cat = QVBoxLayout()
        v_cat.addWidget(QLabel("Categoria Odontológica (*):"))
        self.cmb_cat = QComboBox()
        self.cmb_cat.addItems(list_categories())
        v_cat.addWidget(self.cmb_cat)
        row_cat.addLayout(v_cat)

        v_uni = QVBoxLayout()
        v_uni.addWidget(QLabel("Unidade de Medida:"))
        self.cmb_uni = QComboBox()
        self.cmb_uni.addItems(UNIDADES_MEDIDA)
        v_uni.addWidget(self.cmb_uni)
        row_cat.addLayout(v_uni)
        layout.addLayout(row_cat)

        # 3. Quantidade e Estoque Mínimo
        row_qtd = QHBoxLayout()
        v_q1 = QVBoxLayout()
        v_q1.addWidget(QLabel("Quantidade Atual:" if self.is_edit else "Quantidade Inicial (*):"))
        self.spn_qtd = QDoubleSpinBox()
        self.spn_qtd.setRange(0, 99999)
        self.spn_qtd.setDecimals(1)
        self.spn_qtd.setValue(1.0)
        if self.is_edit:
            self.spn_qtd.setEnabled(False)  # Quantidade em edição é alterada via movimentação
            self.spn_qtd.setToolTip("Para alterar o saldo, use os botões de Entrada ou Saída.")
        v_q1.addWidget(self.spn_qtd)
        row_qtd.addLayout(v_q1)

        v_q2 = QVBoxLayout()
        lbl_min = QLabel("Estoque Mínimo:")
        lbl_min.setToolTip("Nível mínimo para disparo de alerta de compra/reposição")
        v_q2.addWidget(lbl_min)
        self.spn_min = QDoubleSpinBox()
        self.spn_min.setRange(0, 99999)
        self.spn_min.setDecimals(1)
        self.spn_min.setValue(2.0)
        self.spn_min.setToolTip("Nível mínimo para disparo de alerta de compra/reposição")
        v_q2.addWidget(self.spn_min)
        row_qtd.addLayout(v_q2)

        v_pr = QVBoxLayout()
        v_pr.addWidget(QLabel("Preço de Custo (R$):"))
        self.spn_preco = QDoubleSpinBox()
        self.spn_preco.setRange(0, 999999.99)
        self.spn_preco.setDecimals(2)
        self.spn_preco.setPrefix("R$ ")
        v_pr.addWidget(self.spn_preco)
        row_qtd.addLayout(v_pr)
        layout.addLayout(row_qtd)

        # 4. Lote e Data de Validade
        row_lot = QHBoxLayout()
        v_lote = QVBoxLayout()
        v_lote.addWidget(QLabel("Lote do Fabricante:"))
        self.txt_lote = QLineEdit()
        self.txt_lote.setPlaceholderText("Ex: L-84920")
        v_lote.addWidget(self.txt_lote)
        row_lot.addLayout(v_lote)

        v_val = QVBoxLayout()
        v_val.addWidget(QLabel("Data de Validade:"))
        self.dt_val = CustomDateEdit()
        self.dt_val.setDate(QDate.currentDate().addYears(2))
        v_val.addWidget(self.dt_val)
        row_lot.addLayout(v_val)
        layout.addLayout(row_lot)

        # 5. Localização e Fornecedor
        row_loc = QHBoxLayout()
        v_loc = QVBoxLayout()
        v_loc.addWidget(QLabel("Local no Consultório:"))
        self.txt_loc = QLineEdit()
        self.txt_loc.setPlaceholderText("Ex: Gaveteiro 2, Geladeira de Resinas...")
        v_loc.addWidget(self.txt_loc)
        row_loc.addLayout(v_loc)

        v_forn = QVBoxLayout()
        v_forn.addWidget(QLabel("Fornecedor / Dental:"))
        self.txt_forn = QLineEdit()
        self.txt_forn.setPlaceholderText("Ex: Dental Cremer, Dental Speed...")
        v_forn.addWidget(self.txt_forn)
        row_loc.addLayout(v_forn)
        layout.addLayout(row_loc)

        # 6. Observações
        layout.addWidget(QLabel("Observações Adicionais:"))
        self.txt_obs = QLineEdit()
        self.txt_obs.setPlaceholderText("Instruções de armazenagem, recomendação clínica...")
        layout.addWidget(self.txt_obs)

        layout.addStretch()

        # Botões
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("secondaryBtn")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_save = QPushButton("Salvar Material")
        btn_save.setObjectName("primaryBtn")
        btn_save.clicked.connect(self.salvar)
        btn_box.addWidget(btn_save)

        layout.addLayout(btn_box)

        # Preenche se for edição
        if self.is_edit and self.item:
            self.txt_nome.setText(self.item.get("nome", ""))
            cat_idx = self.cmb_cat.findText(self.item.get("categoria", ""))
            if cat_idx >= 0:
                self.cmb_cat.setCurrentIndex(cat_idx)
            uni_idx = self.cmb_uni.findText(self.item.get("unidade", "Unidade"))
            if uni_idx >= 0:
                self.cmb_uni.setCurrentIndex(uni_idx)
            self.spn_qtd.setValue(float(self.item.get("quantidade", 0)))
            self.spn_min.setValue(float(self.item.get("estoque_minimo", 1)))
            self.spn_preco.setValue(float(self.item.get("preco_custo", 0)))
            self.txt_lote.setText(self.item.get("lote", "") or "")
            self.txt_loc.setText(self.item.get("localizacao", "") or "")
            self.txt_forn.setText(self.item.get("fornecedor", "") or "")
            self.txt_obs.setText(self.item.get("observacoes", "") or "")

            val_str = self.item.get("data_validade", "")
            if val_str and len(val_str) >= 10:
                try:
                    d = datetime.strptime(val_str[:10], "%Y-%m-%d").date()
                    self.dt_val.setDate(QDate(d.year, d.month, d.day))
                except Exception:
                    pass

    def salvar(self):
        nome = self.txt_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Aviso", "O nome do material é obrigatório.")
            return

        cat = self.cmb_cat.currentText()
        uni = self.cmb_uni.currentText()
        min_est = self.spn_min.value()
        preco = self.spn_preco.value()
        lote = self.txt_lote.text().strip()
        loc = self.txt_loc.text().strip()
        forn = self.txt_forn.text().strip()
        obs = self.txt_obs.text().strip()

        qd = self.dt_val.date()
        val_str = f"{qd.year():04d}-{qd.month():02d}-{qd.day():02d}"

        if self.is_edit:
            ok, msg = update_item(
                self.item["id"], nome, cat, uni, min_est,
                lote, val_str, preco, loc, forn, obs,
                self.current_user["id"], self.current_user["nome"]
            )
        else:
            qtd_ini = self.spn_qtd.value()
            ok, msg, _ = create_item(
                nome, cat, uni, qtd_ini, min_est,
                lote, val_str, preco, loc, forn, obs,
                self.current_user["id"], self.current_user["nome"]
            )

        if ok:
            QMessageBox.information(self, "Sucesso", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Erro", msg)


class StockMovementDialog(QDialog):
    """Diálogo Ágil para Registrar Entrada (+ Compra) ou Saída (- Consumo Clínico)."""
    def __init__(self, item: dict, tipo: str, current_user: dict, parent=None):
        super().__init__(parent)
        self.item = item
        self.tipo = tipo  # "Entrada" ou "Saida"
        self.current_user = current_user
        eh_entrada = (tipo == "Entrada")
        self.setWindowTitle(f"Registrar Entrada (+ Compra)" if eh_entrada else "Registrar Saída (- Consumo Clínico)")
        self.setFixedSize(480, 420)
        self.setStyleSheet(INVENTORY_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        eh_entrada = (self.tipo == "Entrada")
        cor_tema = "#059669" if eh_entrada else "#ea580c"
        icone = "📥" if eh_entrada else "📤"

        title = QLabel(f"{icone} {self.tipo} de Material")
        title.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {cor_tema};")
        layout.addWidget(title)

        # Card de informações do material
        info_frame = QFrame()
        info_frame.setObjectName("infoCardMov")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(14, 12, 14, 12)
        info_layout.setSpacing(6)

        lbl_item = QLabel(f"<b>Material:</b> {self.item['nome']}")
        lbl_item.setStyleSheet("font-size: 14px; color: #1e293b;")
        lbl_item.setWordWrap(True)
        info_layout.addWidget(lbl_item)

        saldo_atual = float(self.item.get("quantidade", 0))
        self.lbl_saldo = QLabel(f"<b>Estoque Atual:</b> {saldo_atual:.1f} {self.item.get('unidade', 'Unidade')}")
        self.lbl_saldo.setStyleSheet("font-size: 13px; color: #475569;")
        info_layout.addWidget(self.lbl_saldo)
        layout.addWidget(info_frame)

        # Quantidade
        layout.addWidget(QLabel(f"Quantidade a {'adicionar' if eh_entrada else 'retirar'} (*):"))
        self.spn_mov = QDoubleSpinBox()
        self.spn_mov.setRange(0.1, 99999)
        self.spn_mov.setDecimals(1)
        self.spn_mov.setValue(1.0)
        self.spn_mov.setSuffix(f" {self.item.get('unidade', 'Unidade')}")
        self.spn_mov.valueChanged.connect(self.atualizar_projecao)
        layout.addWidget(self.spn_mov)

        # Projeção do novo saldo
        self.lbl_projecao = QLabel()
        self.lbl_projecao.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {cor_tema};")
        layout.addWidget(self.lbl_projecao)
        self.atualizar_projecao()

        # Motivo da movimentação
        layout.addWidget(QLabel("Motivo / Justificativa (*):"))
        self.txt_motivo = QLineEdit()
        sugestao = "Compra / Reposição de Estoque" if eh_entrada else "Consumo clínico em atendimento"
        self.txt_motivo.setPlaceholderText(f"Ex: {sugestao}")
        self.txt_motivo.setText(sugestao)
        layout.addWidget(self.txt_motivo)

        layout.addStretch()

        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("secondaryBtn")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_confirm = QPushButton(f"Confirmar {self.tipo}")
        btn_confirm.setObjectName("inBtn" if eh_entrada else "outBtn")
        btn_confirm.clicked.connect(self.confirmar)
        btn_box.addWidget(btn_confirm)

        layout.addLayout(btn_box)

    def atualizar_projecao(self):
        saldo_atual = float(self.item.get("quantidade", 0))
        qtd = self.spn_mov.value()
        uni = self.item.get("unidade", "Unidade")

        if self.tipo == "Entrada":
            novo = saldo_atual + qtd
            self.lbl_projecao.setText(f"✓ Novo estoque passará a ser: {novo:.1f} {uni}")
        else:
            novo = saldo_atual - qtd
            if novo < 0:
                self.lbl_projecao.setText(f"⚠️ Saldo insuficiente! Estoque ficaria negativo ({novo:.1f} {uni})")
                self.lbl_projecao.setStyleSheet("font-size: 13px; font-weight: bold; color: #dc2626;")
            else:
                self.lbl_projecao.setText(f"✓ Novo estoque passará a ser: {novo:.1f} {uni}")
                self.lbl_projecao.setStyleSheet("font-size: 13px; font-weight: bold; color: #ea580c;")

    def confirmar(self):
        qtd = self.spn_mov.value()
        motivo = self.txt_motivo.text().strip()

        ok, msg = add_stock_movement(
            self.item["id"], self.tipo, qtd, motivo,
            self.current_user["id"], self.current_user["nome"]
        )
        if ok:
            QMessageBox.information(self, "Sucesso", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Aviso", msg)


class MovementHistoryDialog(QDialog):
    """Diálogo para Visualizar o Extrato Completo de Movimentações de um Material."""
    def __init__(self, item: dict, parent=None):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle(f"Histórico de Movimentações: {item['nome']}")
        self.resize(720, 480)
        self.setStyleSheet(INVENTORY_STYLE)
        self.init_ui()
        self.carregar_historico()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel(f"Extrato de Movimentações • {self.item['nome']}")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #166260;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Data / Hora", "Tipo", "Quantidade", "Saldo Ant.", "Novo Saldo", "Motivo", "Responsável"
        ])
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Interactive)
        h.setSectionResizeMode(1, QHeaderView.Interactive)
        h.setSectionResizeMode(2, QHeaderView.Interactive)
        h.setSectionResizeMode(3, QHeaderView.Interactive)
        h.setSectionResizeMode(4, QHeaderView.Interactive)
        h.setSectionResizeMode(5, QHeaderView.Stretch)
        h.setSectionResizeMode(6, QHeaderView.Interactive)
        self.table.setColumnWidth(0, 140)
        self.table.setColumnWidth(1, 85)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 85)
        self.table.setColumnWidth(4, 85)
        self.table.setColumnWidth(6, 120)

        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
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

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_close = QPushButton("Fechar")
        btn_close.setObjectName("secondaryBtn")
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)

    def carregar_historico(self):
        movs = list_movements(self.item["id"])
        self.table.setRowCount(len(movs))

        for row_idx, m in enumerate(movs):
            # Data / Hora formatada
            raw_dt = str(m["data_hora"])
            try:
                dt_obj = datetime.strptime(raw_dt[:19], "%Y-%m-%d %H:%M:%S")
                dt_fmt = dt_obj.strftime("%d/%m/%Y %H:%M")
            except Exception:
                dt_fmt = raw_dt

            self.table.setItem(row_idx, 0, QTableWidgetItem(dt_fmt))

            # Tipo com cor
            tipo_item = QTableWidgetItem(m["tipo"])
            tipo_item.setTextAlignment(Qt.AlignCenter)
            tipo_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            if m["tipo"] == "Entrada":
                tipo_item.setForeground(QColor("#059669"))
            elif m["tipo"] == "Saida":
                tipo_item.setForeground(QColor("#ea580c"))
            else:
                tipo_item.setForeground(QColor("#0284c7"))
            self.table.setItem(row_idx, 1, tipo_item)

            uni = m.get("unidade", "")
            item_qtd = QTableWidgetItem(f"{float(m['quantidade']):.1f} {uni}")
            item_qtd.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 2, item_qtd)

            item_ant = QTableWidgetItem(f"{float(m['quantidade_anterior']):.1f}")
            item_ant.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 3, item_ant)

            item_novo = QTableWidgetItem(f"{float(m['quantidade_nova']):.1f}")
            item_novo.setTextAlignment(Qt.AlignCenter)
            item_novo.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table.setItem(row_idx, 4, item_novo)

            self.table.setItem(row_idx, 5, QTableWidgetItem(m.get("motivo", "") or "-"))
            self.table.setItem(row_idx, 6, QTableWidgetItem(m.get("usuario_nome", "") or "-"))


# -------------------------------------------------------------
# GERENCIAMENTO DINÂMICO DE CATEGORIAS
# -------------------------------------------------------------

class ManageCategoriesDialog(QDialog):
    """Diálogo para Criar, Renomear ou Remover Categorias de Materiais."""
    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.setWindowTitle("Gerenciar Categorias de Materiais")
        self.setFixedSize(580, 500)
        self.setStyleSheet(INVENTORY_STYLE)
        self.init_ui()
        self.carregar_categorias()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        title = QLabel("🏷️ Categorias de Insumos e Materiais")
        title.setStyleSheet("font-size: 17px; font-weight: bold; color: #166260;")
        layout.addWidget(title)

        desc = QLabel("Crie novas categorias, renomeie existentes ou remova as que não utiliza mais.")
        desc.setStyleSheet("color: #64748b; font-size: 13px;")
        layout.addWidget(desc)

        # Adicionar nova categoria
        add_box = QHBoxLayout()
        self.txt_nova = QLineEdit()
        self.txt_nova.setPlaceholderText("Nome da nova categoria...")
        add_box.addWidget(self.txt_nova)

        btn_add = QPushButton("+ Adicionar Categoria")
        btn_add.setObjectName("primaryBtn")
        btn_add.clicked.connect(self.adicionar_categoria)
        add_box.addWidget(btn_add)
        layout.addLayout(add_box)

        # Tabela de categorias
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Nome da Categoria", "Materiais Vinculados"])
        self.table.setColumnHidden(0, True)

        h = self.table.horizontalHeader()
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.Interactive)
        self.table.setColumnWidth(2, 160)

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
        btn_renomear = QPushButton("✏️ Renomear")
        btn_renomear.setObjectName("secondaryBtn")
        btn_renomear.clicked.connect(self.renomear_selecionada)
        act_box.addWidget(btn_renomear)

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
        cats = list_categories_detailed()
        self.table.setRowCount(len(cats))
        for row_idx, c in enumerate(cats):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(c["id"])))
            
            item_nome = QTableWidgetItem(c["nome"])
            item_nome.setFont(QFont("Segoe UI", 10, QFont.Bold if c["nome"] == "Geral / Outros" else QFont.Normal))
            self.table.setItem(row_idx, 1, item_nome)

            total = c.get("total_itens", 0)
            item_tot = QTableWidgetItem(f"{total} material(is)" if total > 0 else "0 (livre)")
            item_tot.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 2, item_tot)
            self.table.item(row_idx, 0).setData(Qt.UserRole, c)

    def adicionar_categoria(self):
        nome = self.txt_nova.text().strip()
        if not nome:
            QMessageBox.warning(self, "Aviso", "Digite o nome da categoria para adicionar.")
            return

        ok, msg, _ = create_category(nome, self.current_user["id"], self.current_user["nome"])
        if ok:
            self.txt_nova.clear()
            self.carregar_categorias()
        else:
            QMessageBox.warning(self, "Aviso", msg)

    def renomear_selecionada(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione uma categoria para renomear.")
            return
        row = selected[0].row()
        c = self.table.item(row, 0).data(Qt.UserRole)
        cat_id = c["id"]
        cat_atual = c["nome"]

        novo_nome, ok = QInputDialog.getText(
            self, "Renomear Categoria", f"Novo nome para '{cat_atual}':",
            QLineEdit.Normal, cat_atual
        )
        if ok and novo_nome.strip():
            sucesso, msg = update_category(cat_id, novo_nome.strip(), self.current_user["id"], self.current_user["nome"])
            if sucesso:
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
        total_itens = c.get("total_itens", 0)

        if cat_nome == "Geral / Outros":
            QMessageBox.warning(self, "Aviso", "A categoria padrão 'Geral / Outros' não pode ser removida.")
            return

        aviso_extra = ""
        if total_itens > 0:
            aviso_extra = f"\n\n⚠️ Atenção: Há {total_itens} material(is) vinculado(s) a esta categoria. Eles serão automaticamente transferidos para 'Geral / Outros'."

        msg = f"Deseja realmente remover a categoria '{cat_nome}'?{aviso_extra}"
        if perguntar_sim_nao(self, "Remover Categoria", msg):
            ok, msg_res = delete_category(cat_id, self.current_user["id"], self.current_user["nome"])
            if ok:
                self.carregar_categorias()
            else:
                QMessageBox.warning(self, "Aviso", msg_res)


# -------------------------------------------------------------
# TELA PRINCIPAL DO MÓDULO DE ESTOQUE
# -------------------------------------------------------------

class InventoryView(QWidget):
    """Tela Principal de Controle de Estoque e Materiais da Clínica."""
    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.filtro_alerta = "todos"
        self.init_ui()
        self.carregar_dados()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        self.setStyleSheet(INVENTORY_STYLE)

        # 1. Cabeçalho Superior
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Controle de Estoque e Insumos Odontológicos")
        title.setStyleSheet("font-size: 19px; font-weight: bold; color: #166260;")
        sub = QLabel("Rastreabilidade de materiais, alertas de validade, estoque mínimo e consumo clínico.")
        sub.setStyleSheet("color: #64748b; font-size: 13px;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.btn_novo_material = QPushButton("+ Novo Material")
        self.btn_novo_material.setObjectName("primaryBtn")
        self.btn_novo_material.setStyleSheet("""
            background-color: #2ca5a9;
            color: #ffffff;
            font-weight: bold;
            font-size: 14px;
            padding: 9px 18px;
            border-radius: 6px;
            border: none;
        """)
        self.btn_novo_material.clicked.connect(self.abrir_novo_material)
        header_layout.addWidget(self.btn_novo_material)
        layout.addLayout(header_layout)

        # 2. Cards Superiores de Indicadores (KPIs)
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(10)

        # Card 1: Total
        self.card_total = self.criar_card_kpi("📦 Total de Materiais", "0", "Itens cadastrados no acervo", "#0f766e")
        kpi_layout.addWidget(self.card_total)

        # Card 2: Estoque Baixo
        self.card_baixo = self.criar_card_kpi("⚠️ Estoque Baixo", "0", "Itens no limite ou para compra", "#d97706")
        kpi_layout.addWidget(self.card_baixo)

        # Card 3: Vencimento
        self.card_venc = self.criar_card_kpi("⏰ Atenção Validade", "0", "Vencidos ou a vencer em 30d", "#dc2626")
        kpi_layout.addWidget(self.card_venc)

        # Card 4: Valor em Estoque
        self.card_valor = self.criar_card_kpi("💰 Patrimônio em Estoque", "R$ 0,00", "Valor total investido", "#0369a1")
        kpi_layout.addWidget(self.card_valor)

        layout.addLayout(kpi_layout)

        # 3. Pílulas de Filtro Rápido
        pills_layout = QHBoxLayout()
        pills_layout.setSpacing(8)

        self.pill_todos = QPushButton("🌐 Todos os Materiais")
        self.pill_todos.setObjectName("pillBtn")
        self.pill_todos.setCheckable(True)
        self.pill_todos.setChecked(True)
        self.pill_todos.clicked.connect(lambda: self.mudar_filtro_alerta("todos"))
        pills_layout.addWidget(self.pill_todos)

        self.pill_baixo = QPushButton("⚠️ Estoque Baixo")
        self.pill_baixo.setObjectName("pillBtn")
        self.pill_baixo.setCheckable(True)
        self.pill_baixo.clicked.connect(lambda: self.mudar_filtro_alerta("baixo"))
        pills_layout.addWidget(self.pill_baixo)

        self.pill_avencer = QPushButton("⏰ Próximos do Vencimento")
        self.pill_avencer.setObjectName("pillBtn")
        self.pill_avencer.setCheckable(True)
        self.pill_avencer.clicked.connect(lambda: self.mudar_filtro_alerta("avencer"))
        pills_layout.addWidget(self.pill_avencer)

        self.pill_vencido = QPushButton("⛔ Vencidos")
        self.pill_vencido.setObjectName("pillBtn")
        self.pill_vencido.setCheckable(True)
        self.pill_vencido.clicked.connect(lambda: self.mudar_filtro_alerta("vencido"))
        pills_layout.addWidget(self.pill_vencido)

        pills_layout.addStretch()
        layout.addLayout(pills_layout)

        # 4. Barra de Pesquisa e Categoria
        search_bar = QFrame()
        search_bar.setObjectName("barNav")
        search_layout = QHBoxLayout(search_bar)
        search_layout.setContentsMargins(10, 6, 10, 6)
        search_layout.setSpacing(8)

        lbl_icon = QLabel("🔍")
        search_layout.addWidget(lbl_icon)

        # Debounce de 250ms na busca
        self.timer_busca = QTimer(self)
        self.timer_busca.setSingleShot(True)
        self.timer_busca.setInterval(250)
        self.timer_busca.timeout.connect(self.carregar_dados)

        self.txt_busca = QLineEdit()
        self.txt_busca.setPlaceholderText("Pesquisar por nome do material, lote, localização ou dental...")
        self.txt_busca.setStyleSheet("border: none; background: transparent; font-size: 13px;")
        self.txt_busca.textChanged.connect(self.timer_busca.start)
        search_layout.addWidget(self.txt_busca)

        lbl_cat = QLabel("Categoria:")
        lbl_cat.setStyleSheet("color: #475569; font-weight: 600; font-size: 12px;")
        search_layout.addWidget(lbl_cat)

        self.cmb_filtro_cat = QComboBox()
        self.cmb_filtro_cat.setFixedWidth(200)
        self.atualizar_combos_categorias()
        self.cmb_filtro_cat.currentIndexChanged.connect(self.carregar_dados)
        search_layout.addWidget(self.cmb_filtro_cat)

        btn_cat = QPushButton("🏷️ Gerenciar Categorias")
        btn_cat.setObjectName("secondaryBtn")
        btn_cat.setToolTip("Criar, renomear ou remover categorias de materiais")
        btn_cat.clicked.connect(self.abrir_gerenciar_categorias)
        search_layout.addWidget(btn_cat)

        btn_limpar = QPushButton("Limpar")
        btn_limpar.setObjectName("secondaryBtn")
        btn_limpar.clicked.connect(self.limpar_filtros)
        search_layout.addWidget(btn_limpar)

        layout.addWidget(search_bar)

        # 5. Tabela de Estoque
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Material / Insumo", "Categoria", "Estoque Atual",
            "Validade", "Custo (R$)", "Status / Situação"
        ])
        self.table.setColumnHidden(0, True)  # Oculta ID

        h = self.table.horizontalHeader()
        h.setMinimumSectionSize(95)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.Interactive)
        h.setSectionResizeMode(3, QHeaderView.Interactive)
        h.setSectionResizeMode(4, QHeaderView.Interactive)
        h.setSectionResizeMode(5, QHeaderView.Interactive)
        h.setSectionResizeMode(6, QHeaderView.Interactive)

        self.table.setColumnWidth(2, 165)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 110)
        self.table.setColumnWidth(5, 105)
        self.table.setColumnWidth(6, 145)

        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self.abrir_historico_selecionado)
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

        btn_in = QPushButton("📥 + Entrada (Compra)")
        btn_in.setObjectName("inBtn")
        btn_in.clicked.connect(self.abrir_entrada_selecionada)
        bottom_bar.addWidget(btn_in)

        btn_out = QPushButton("📤 - Saída (Consumo Clínico)")
        btn_out.setObjectName("outBtn")
        btn_out.clicked.connect(self.abrir_saida_selecionada)
        bottom_bar.addWidget(btn_out)

        btn_hist = QPushButton("📋 Histórico / Extrato")
        btn_hist.setObjectName("secondaryBtn")
        btn_hist.clicked.connect(self.abrir_historico_selecionado)
        bottom_bar.addWidget(btn_hist)

        btn_edit = QPushButton("✏️ Editar Cadastro")
        btn_edit.setObjectName("secondaryBtn")
        btn_edit.clicked.connect(self.abrir_editar_selecionado)
        bottom_bar.addWidget(btn_edit)

        bottom_bar.addStretch()

        btn_del = QPushButton("Excluir Material")
        btn_del.setObjectName("dangerBtn")
        btn_del.clicked.connect(self.excluir_material_selecionado)
        bottom_bar.addWidget(btn_del)

        layout.addLayout(bottom_bar)

    def atualizar_combos_categorias(self):
        atual = self.cmb_filtro_cat.currentText() if hasattr(self, "cmb_filtro_cat") else ""
        if hasattr(self, "cmb_filtro_cat"):
            self.cmb_filtro_cat.blockSignals(True)
            self.cmb_filtro_cat.clear()
            self.cmb_filtro_cat.addItem("Todas as Categorias")
            for c in list_categories():
                self.cmb_filtro_cat.addItem(c)
            idx = self.cmb_filtro_cat.findText(atual)
            if idx >= 0:
                self.cmb_filtro_cat.setCurrentIndex(idx)
            else:
                self.cmb_filtro_cat.setCurrentIndex(0)
            self.cmb_filtro_cat.blockSignals(False)

    def abrir_gerenciar_categorias(self):
        dialog = ManageCategoriesDialog(self.current_user, parent=self)
        dialog.exec()
        self.atualizar_combos_categorias()
        self.carregar_dados()

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

    def mudar_filtro_alerta(self, modo: str):
        self.filtro_alerta = modo
        self.pill_todos.setChecked(modo == "todos")
        self.pill_baixo.setChecked(modo == "baixo")
        self.pill_avencer.setChecked(modo == "avencer")
        self.pill_vencido.setChecked(modo == "vencido")
        self.carregar_dados()

    def limpar_filtros(self):
        self.txt_busca.clear()
        self.cmb_filtro_cat.setCurrentIndex(0)
        self.mudar_filtro_alerta("todos")

    def carregar_dados(self):
        # 1. Atualiza KPIs
        kpis = get_inventory_kpis()
        self.card_total.lbl_valor.setText(str(kpis["total_itens"]))
        self.card_baixo.lbl_valor.setText(str(kpis["estoque_baixo"]))
        self.card_venc.lbl_valor.setText(str(kpis["vencidos_ou_avencer"]))
        val_fmt = f"{kpis['valor_total']:.2f}".replace('.', ',')
        self.card_valor.lbl_valor.setText(f"R$ {val_fmt}")

        # 2. Busca Itens
        termo = self.txt_busca.text()
        cat = self.cmb_filtro_cat.currentText()
        cat_filtro = "Todas" if cat == "Todas as Categorias" else cat

        itens = search_items(termo, categoria=cat_filtro, filtro_alerta=self.filtro_alerta)

        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(itens))

        hoje = date.today()

        for row_idx, item in enumerate(itens):
            # Coluna 0: ID
            item_id = QTableWidgetItem(str(item["id"]))
            self.table.setItem(row_idx, 0, item_id)

            # Coluna 1: Nome do Material
            item_nome = QTableWidgetItem(item["nome"])
            item_nome.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table.setItem(row_idx, 1, item_nome)

            # Coluna 2: Categoria
            item_cat = QTableWidgetItem(item["categoria"])
            self.table.setItem(row_idx, 2, item_cat)

            # Coluna 3: Quantidade Atual
            qtd = float(item["quantidade"])
            uni = item.get("unidade", "Unidade")
            item_qtd = QTableWidgetItem(f"{qtd:.1f} {uni}")
            item_qtd.setTextAlignment(Qt.AlignCenter)
            item_qtd.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table.setItem(row_idx, 3, item_qtd)

            # Coluna 4: Validade
            val_txt = item.get("data_validade") or ""
            dias_restantes: Optional[int] = None
            if val_txt and len(val_txt) >= 10:
                try:
                    d_val = datetime.strptime(val_txt[:10], "%Y-%m-%d").date()
                    val_fmt = d_val.strftime("%d/%m/%Y")
                    dias_restantes = (d_val - hoje).days
                except Exception:
                    val_fmt = val_txt
            else:
                val_fmt = "-"

            item_val = QTableWidgetItem(val_fmt)
            item_val.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 4, item_val)

            # Coluna 5: Preço de Custo
            pr = float(item.get("preco_custo", 0.0))
            pr_fmt = f"{pr:.2f}".replace('.', ',')
            item_pr = QTableWidgetItem(f"R$ {pr_fmt}")
            item_pr.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 5, item_pr)

            # Coluna 6: Status / Alerta (Badge inteligente)
            st = item.get("status_alerta", "ok")
            if st == "vencido":
                status_label = "⛔ Vencido"
                cor_badge = "#dc2626"
            elif st == "avencer":
                d_str = f" ({dias_restantes}d)" if dias_restantes is not None else ""
                status_label = f"⏰ A Vencer{d_str}"
                cor_badge = "#d97706"
            elif st == "zerado":
                status_label = "⚪ Sem Estoque"
                cor_badge = "#dc2626"
            elif st == "baixo":
                status_label = "⚠️ Repor Estoque"
                cor_badge = "#d97706"
            else:
                status_label = "✓ Normal"
                cor_badge = "#059669"

            item_st = QTableWidgetItem(status_label)
            item_st.setTextAlignment(Qt.AlignCenter)
            item_st.setFont(QFont("Segoe UI", 9, QFont.Bold))
            item_st.setForeground(QColor(cor_badge))
            self.table.setItem(row_idx, 6, item_st)

            # Armazena o dict do item no UserRole
            self.table.item(row_idx, 0).setData(Qt.UserRole, item)

        self.table.setUpdatesEnabled(True)

    def get_selected_item(self) -> Optional[dict]:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione um material na tabela.")
            return None
        row = selected[0].row()
        item_zero = self.table.item(row, 0)
        return item_zero.data(Qt.UserRole) if item_zero else None

    def abrir_novo_material(self):
        dialog = ItemFormDialog(self.current_user, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.carregar_dados()

    def abrir_editar_selecionado(self):
        item = self.get_selected_item()
        if not item:
            return
        # Busca do banco para pegar versão fresca
        item_fresh = get_item(item["id"])
        dialog = ItemFormDialog(self.current_user, item=item_fresh or item, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.carregar_dados()

    def abrir_entrada_selecionada(self):
        item = self.get_selected_item()
        if not item:
            return
        item_fresh = get_item(item["id"]) or item
        dialog = StockMovementDialog(item_fresh, "Entrada", self.current_user, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.carregar_dados()

    def abrir_saida_selecionada(self):
        item = self.get_selected_item()
        if not item:
            return
        item_fresh = get_item(item["id"]) or item
        dialog = StockMovementDialog(item_fresh, "Saida", self.current_user, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.carregar_dados()

    def abrir_historico_selecionado(self):
        item = self.get_selected_item()
        if not item:
            return
        item_fresh = get_item(item["id"]) or item
        dialog = MovementHistoryDialog(item_fresh, parent=self)
        dialog.exec()

    def excluir_material_selecionado(self):
        item = self.get_selected_item()
        if not item:
            return

        msg = (
            f"Deseja realmente remover o material '{item['nome']}' do catálogo de estoque?\n\n"
            f"• O histórico de movimentações passadas continuará preservado na auditoria.\n"
            f"• Deseja continuar?"
        )
        if perguntar_sim_nao(self, "Excluir Material", msg):
            ok, msg_res = delete_item(item["id"], self.current_user["id"], self.current_user["nome"])
            if ok:
                QMessageBox.information(self, "Sucesso", msg_res)
                self.carregar_dados()
            else:
                QMessageBox.critical(self, "Erro", msg_res)
