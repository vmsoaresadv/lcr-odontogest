from datetime import datetime, date
from typing import List, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from ui.financial_view import FINANCIAL_STYLE, MarkAsPaidDialog
from services.financial_service import verificar_alertas_vencimento, get_transaction


class DueBillsDialog(QDialog):
    """
    Central de Alertas de Vencimentos da Clínica.
    Apresentada ao iniciar o sistema ou ao clicar no botão de notificações do topo.
    """
    def __init__(self, current_user: dict, bills: Optional[List[dict]] = None, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.bills = bills if bills is not None else verificar_alertas_vencimento()
        self.abrir_financeiro_solicitado = False

        self.setWindowTitle("🔔 Central de Vencimentos da Clínica — LCR OdontoGest")
        self.resize(920, 500)
        self.setMinimumSize(850, 420)
        self.setStyleSheet(FINANCIAL_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # 1. Cabeçalho Executivo
        top_frame = QFrame()
        top_frame.setStyleSheet("""
            QFrame {
                background-color: #f0fdfa;
                border: 1px solid #ccfbf1;
                border-radius: 8px;
                padding: 10px 14px;
            }
        """)
        top_l = QHBoxLayout(top_frame)
        top_l.setContentsMargins(8, 6, 8, 6)

        v_titles = QVBoxLayout()
        v_titles.setSpacing(2)
        lbl_h1 = QLabel("🔔 Central de Alertas e Vencimentos")
        lbl_h1.setStyleSheet("font-size: 17px; font-weight: bold; color: #0f766e; border: none; background: transparent;")
        v_titles.addWidget(lbl_h1)

        lbl_h2 = QLabel("Lançamentos pendentes que vencem hoje, amanhã ou já se encontram em atraso.")
        lbl_h2.setStyleSheet("font-size: 12px; color: #475569; border: none; background: transparent;")
        v_titles.addWidget(lbl_h2)
        top_l.addLayout(v_titles)

        top_l.addStretch()

        # Resumo de totais
        tot_val = sum(float(b.get("valor", 0)) for b in self.bills if b.get("tipo") == "Despesa")
        v_tot = QVBoxLayout()
        v_tot.setSpacing(1)
        lbl_tot_t = QLabel("Total a Pagar Alerta:")
        lbl_tot_t.setStyleSheet("font-size: 11px; color: #64748b; font-weight: 600; border: none; background: transparent;")
        v_tot.addWidget(lbl_tot_t)

        lbl_tot_v = QLabel(f"R$ {tot_val:.2f}".replace('.', ','))
        lbl_tot_v.setStyleSheet("font-size: 18px; font-weight: bold; color: #dc2626; border: none; background: transparent;")
        v_tot.addWidget(lbl_tot_v)
        top_l.addLayout(v_tot)

        layout.addWidget(top_frame)

        # 2. Tabela de Contas
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Situação", "Vencimento", "Tipo", "Descrição / Categoria",
            "Paciente / Origem", "Valor (R$)", "Ação"
        ])
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Interactive)
        h.setSectionResizeMode(1, QHeaderView.Interactive)
        h.setSectionResizeMode(2, QHeaderView.Interactive)
        h.setSectionResizeMode(3, QHeaderView.Stretch)
        h.setSectionResizeMode(4, QHeaderView.Interactive)
        h.setSectionResizeMode(5, QHeaderView.Interactive)
        h.setSectionResizeMode(6, QHeaderView.Fixed)

        self.table.setColumnWidth(0, 160)
        self.table.setColumnWidth(1, 95)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(4, 130)
        self.table.setColumnWidth(5, 110)
        self.table.setColumnWidth(6, 125)

        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                gridline-color: #f1f5f9;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                color: #334155;
                font-weight: bold;
                font-size: 12px;
                padding: 6px;
                border: 1px solid #e2e8f0;
            }
        """)

        layout.addWidget(self.table)
        self.carregar_dados()

        # 3. Rodapé com Botões de Ação
        btn_box = QHBoxLayout()
        btn_box.setSpacing(12)

        lbl_dica = QLabel("💡 <i>Você pode quitar qualquer conta agora clicando em 'Baixar / Pagar'.</i>")
        lbl_dica.setStyleSheet("color: #64748b; font-size: 12px;")
        btn_box.addWidget(lbl_dica)
        btn_box.addStretch()

        btn_ir_fin = QPushButton("📊 Abrir Módulo Financeiro")
        btn_ir_fin.setObjectName("secondaryBtn")
        btn_ir_fin.clicked.connect(self.ao_abrir_financeiro)
        btn_box.addWidget(btn_ir_fin)

        btn_fechar = QPushButton("Lembrar Depois / Fechar")
        btn_fechar.setObjectName("primaryBtn")
        btn_fechar.clicked.connect(self.accept)
        btn_box.addWidget(btn_fechar)

        layout.addLayout(btn_box)

    def carregar_dados(self):
        self.table.setRowCount(len(self.bills))

        for row_idx, b in enumerate(self.bills):
            # 0: Situação / Badge
            item_urg = QTableWidgetItem(b.get("urgencia_label", "Pendente"))
            item_urg.setTextAlignment(Qt.AlignCenter)
            item_urg.setFont(QFont("Segoe UI", 9, QFont.Bold))
            item_urg.setForeground(QColor(b.get("cor_badge", "#64748b")))
            self.table.setItem(row_idx, 0, item_urg)

            # 1: Data Vencimento
            venc_raw = str(b.get("data_vencimento", ""))[:10]
            try:
                dt_obj = datetime.strptime(venc_raw, "%Y-%m-%d")
                venc_fmt = dt_obj.strftime("%d/%m/%Y")
            except Exception:
                venc_fmt = venc_raw
            item_venc = QTableWidgetItem(venc_fmt)
            item_venc.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 1, item_venc)

            # 2: Tipo
            tipo = b.get("tipo", "Despesa")
            item_tipo = QTableWidgetItem("💸 Despesa" if tipo == "Despesa" else "💰 Receita")
            item_tipo.setTextAlignment(Qt.AlignCenter)
            item_tipo.setFont(QFont("Segoe UI", 9, QFont.Bold))
            item_tipo.setForeground(QColor("#dc2626" if tipo == "Despesa" else "#059669"))
            self.table.setItem(row_idx, 2, item_tipo)

            # 3: Descrição e Categoria
            desc_txt = f"{b.get('descricao', '')} ({b.get('categoria', '')})"
            item_desc = QTableWidgetItem(desc_txt)
            item_desc.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table.setItem(row_idx, 3, item_desc)

            # 4: Paciente / Origem
            origem = b.get("paciente_nome") or "-"
            self.table.setItem(row_idx, 4, QTableWidgetItem(origem))

            # 5: Valor
            val = float(b.get("valor", 0))
            val_fmt = f"{val:.2f}".replace('.', ',')
            item_val = QTableWidgetItem(f"R$ {val_fmt}")
            item_val.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_val.setFont(QFont("Segoe UI", 10, QFont.Bold))
            item_val.setForeground(QColor("#dc2626" if tipo == "Despesa" else "#059669"))
            self.table.setItem(row_idx, 5, item_val)

            # 6: Botão de Ação rápida
            btn_baixar = QPushButton("✓ Baixar / Pagar")
            btn_baixar.setStyleSheet("""
                QPushButton {
                    background-color: #0f766e;
                    color: #ffffff;
                    font-size: 11px;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 5px 8px;
                }
                QPushButton:hover {
                    background-color: #115e59;
                }
            """)
            btn_baixar.setCursor(Qt.PointingHandCursor)
            btn_baixar.clicked.connect(lambda _, trans=b: self.dar_baixa_item(trans))
            self.table.setCellWidget(row_idx, 6, btn_baixar)

    def dar_baixa_item(self, transaction: dict):
        t_fresh = get_transaction(transaction["id"]) or transaction
        dialog = MarkAsPaidDialog(t_fresh, self.current_user, parent=self)
        if dialog.exec() == QDialog.Accepted:
            # Recarrega lista
            self.bills = verificar_alertas_vencimento()
            self.carregar_dados()
            if not self.bills:
                QMessageBox.information(self, "Tudo em dia!", "Todas as contas pendentes do alerta foram liquidadas com sucesso!")
                self.accept()

    def ao_abrir_financeiro(self):
        self.abrir_financeiro_solicitado = True
        self.accept()
