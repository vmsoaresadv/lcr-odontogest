"""
Módulo Visual de Orçamentos e Planos de Tratamento Odontológico
LCR OdontoGest - Dra. Lara Camila (CRO-BA 15247)
"""

from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QLineEdit, QDoubleSpinBox, QComboBox, QTextEdit, QFrame,
    QMessageBox, QFileDialog, QSpinBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

from services.budget_service import (
    create_budget, list_budgets, get_budget_details,
    update_budget_status, aprovar_orcamento, delete_budget,
    gerar_html_orcamento
)
from services.report_service import exportar_html_para_pdf


class BudgetFormDialog(QDialog):
    """Diálogo de criação e composição de novo Orçamento / Plano de Tratamento."""
    def __init__(self, patient_id: int, current_user: dict, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.current_user = current_user
        self.setWindowTitle("Novo Orçamento / Plano de Tratamento")
        self.resize(780, 560)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Cabeçalho
        lbl_titulo = QLabel("Composição do Plano de Tratamento")
        lbl_titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f766e;")
        layout.addWidget(lbl_titulo)

        # Informações Básicas
        h_info = QHBoxLayout()
        v_tit = QVBoxLayout()
        v_tit.addWidget(QLabel("Título / Descrição do Plano:"))
        self.txt_titulo = QLineEdit()
        self.txt_titulo.setPlaceholderText("Ex: Tratamento Restaurador e Profilaxia Completa")
        v_tit.addWidget(self.txt_titulo)
        h_info.addLayout(v_tit, stretch=2)

        v_pag = QVBoxLayout()
        v_pag.addWidget(QLabel("Forma de Pagamento Sugerida:"))
        self.cmb_pag = QComboBox()
        self.cmb_pag.addItems([
            "À Vista (Pix / Dinheiro)",
            "Cartão de Débito",
            "Cartão de Crédito (1x sem juros)",
            "Cartão de Crédito (2x)",
            "Cartão de Crédito (3x)",
            "Cartão de Crédito (4x a 6x)",
            "Cartão de Crédito (10x a 12x)",
            "Boleto Bancário",
            "Entrada + Parcelas"
        ])
        v_pag.addWidget(self.cmb_pag)
        h_info.addLayout(v_pag, stretch=1)
        layout.addLayout(h_info)

        # Tabela de Itens / Procedimentos Propostos
        h_tb_head = QHBoxLayout()
        lbl_itens = QLabel("Procedimentos Propostos:")
        lbl_itens.setStyleSheet("font-weight: 600; font-size: 13px; color: #1e293b;")
        h_tb_head.addWidget(lbl_itens)
        h_tb_head.addStretch()

        btn_add_item = QPushButton("+ Adicionar Procedimento")
        btn_add_item.setStyleSheet("""
            QPushButton {
                background-color: #0f766e;
                color: #ffffff;
                font-weight: bold;
                padding: 5px 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #115e59;
            }
        """)
        btn_add_item.clicked.connect(self.adicionar_linha_item)
        h_tb_head.addWidget(btn_add_item)

        btn_rem_item = QPushButton("Remover Linha")
        btn_rem_item.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #b91c1c;
                border: 1px solid #fca5a5;
                font-weight: 500;
                padding: 5px 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #fee2e2;
            }
        """)
        btn_rem_item.clicked.connect(self.remover_linha_item)
        h_tb_head.addWidget(btn_rem_item)
        layout.addLayout(h_tb_head)

        self.table_itens = QTableWidget()
        self.table_itens.setColumnCount(5)
        self.table_itens.setHorizontalHeaderLabels(["Dente / Região", "Procedimento", "Qtd", "Valor Unit. (R$)", "Subtotal (R$)"])
        self.table_itens.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_itens.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_itens.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_itens.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_itens.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_itens.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                font-weight: bold;
                padding: 6px;
                border: none;
                border-bottom: 2px solid #cbd5e1;
            }
        """)
        layout.addWidget(self.table_itens)

        # Adiciona 1 linha inicial padrão
        self.adicionar_linha_item()

        # Bloco de Totais e Desconto
        h_totais = QHBoxLayout()
        v_obs = QVBoxLayout()
        v_obs.addWidget(QLabel("Observações do Orçamento:"))
        self.txt_obs = QTextEdit()
        self.txt_obs.setMaximumHeight(70)
        self.txt_obs.setPlaceholderText("Validade da proposta, condições clínicas ou orientações...")
        v_obs.addWidget(self.txt_obs)
        h_totais.addLayout(v_obs, stretch=2)

        card_valores = QFrame()
        card_valores.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px;")
        v_val = QVBoxLayout(card_valores)
        v_val.setSpacing(6)

        self.lbl_bruto = QLabel("Subtotal: R$ 0,00")
        self.lbl_bruto.setStyleSheet("font-size: 13px; color: #475569;")
        v_val.addWidget(self.lbl_bruto)

        h_desc = QHBoxLayout()
        h_desc.addWidget(QLabel("Desconto (R$):"))
        self.spin_desconto = QDoubleSpinBox()
        self.spin_desconto.setMaximum(999999.0)
        self.spin_desconto.setPrefix("R$ ")
        self.spin_desconto.valueChanged.connect(self.recalcular_totais)
        h_desc.addWidget(self.spin_desconto)
        v_val.addLayout(h_desc)

        self.lbl_final = QLabel("TOTAL: R$ 0,00")
        self.lbl_final.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f766e;")
        v_val.addWidget(self.lbl_final)

        h_totais.addWidget(card_valores, stretch=1)
        layout.addLayout(h_totais)

        # Botões de Ação
        h_botoes = QHBoxLayout()
        h_botoes.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("padding: 7px 16px; background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px;")
        btn_cancelar.clicked.connect(self.reject)
        h_botoes.addWidget(btn_cancelar)

        btn_salvar = QPushButton("Salvar Orçamento")
        btn_salvar.setStyleSheet("padding: 7px 20px; background-color: #0f766e; color: #ffffff; font-weight: bold; border-radius: 6px; border: none;")
        btn_salvar.clicked.connect(self.salvar)
        h_botoes.addWidget(btn_salvar)

        layout.addLayout(h_botoes)

    def adicionar_linha_item(self, dente: str = "Geral", proc: str = "", vu: float = 0.0):
        row = self.table_itens.rowCount()
        self.table_itens.insertRow(row)

        txt_dente = QLineEdit(dente)
        txt_dente.setPlaceholderText("Ex: 16")
        self.table_itens.setCellWidget(row, 0, txt_dente)

        txt_proc = QLineEdit(proc)
        txt_proc.setPlaceholderText("Ex: Restauração em Resina Composta")
        self.table_itens.setCellWidget(row, 1, txt_proc)

        spin_qtd = QSpinBox()
        spin_qtd.setMinimum(1)
        spin_qtd.setValue(1)
        spin_qtd.valueChanged.connect(self.recalcular_totais)
        self.table_itens.setCellWidget(row, 2, spin_qtd)

        spin_vu = QDoubleSpinBox()
        spin_vu.setMaximum(99999.0)
        spin_vu.setValue(vu)
        spin_vu.valueChanged.connect(self.recalcular_totais)
        self.table_itens.setCellWidget(row, 3, spin_vu)

        lbl_sub = QLabel("R$ 0,00")
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setStyleSheet("font-weight: 600; color: #334155;")
        self.table_itens.setCellWidget(row, 4, lbl_sub)

        self.recalcular_totais()

    def remover_linha_item(self):
        row = self.table_itens.currentRow()
        if row >= 0:
            self.table_itens.removeRow(row)
            self.recalcular_totais()
        elif self.table_itens.rowCount() > 1:
            self.table_itens.removeRow(self.table_itens.rowCount() - 1)
            self.recalcular_totais()

    def recalcular_totais(self):
        total_bruto = 0.0
        for r in range(self.table_itens.rowCount()):
            spin_qtd = self.table_itens.cellWidget(r, 2)
            spin_vu = self.table_itens.cellWidget(r, 3)
            lbl_sub = self.table_itens.cellWidget(r, 4)

            qtd = spin_qtd.value() if spin_qtd else 1
            vu = spin_vu.value() if spin_vu else 0.0
            sub = qtd * vu
            total_bruto += sub

            if lbl_sub:
                lbl_sub.setText(f"R$ {sub:,.2f}")

        desconto = self.spin_desconto.value()
        total_final = max(0.0, total_bruto - desconto)

        self.lbl_bruto.setText(f"Subtotal: R$ {total_bruto:,.2f}")
        self.lbl_final.setText(f"TOTAL: R$ {total_final:,.2f}")

    def salvar(self):
        titulo = self.txt_titulo.text().strip()
        if not titulo:
            QMessageBox.warning(self, "Aviso", "Por favor, informe o título do plano de tratamento.")
            return

        itens = []
        for r in range(self.table_itens.rowCount()):
            txt_dente = self.table_itens.cellWidget(r, 0)
            txt_proc = self.table_itens.cellWidget(r, 1)
            spin_qtd = self.table_itens.cellWidget(r, 2)
            spin_vu = self.table_itens.cellWidget(r, 3)

            proc_str = txt_proc.text().strip() if txt_proc else ""
            if not proc_str:
                continue

            itens.append({
                "dente_regiao": txt_dente.text().strip() if txt_dente else "Geral",
                "procedimento": proc_str,
                "quantidade": spin_qtd.value() if spin_qtd else 1,
                "valor_unitario": spin_vu.value() if spin_vu else 0.0
            })

        if not itens:
            QMessageBox.warning(self, "Aviso", "Adicione pelo menos um procedimento com nome preenchido.")
            return

        ok, msg, budget_id = create_budget(
            patient_id=self.patient_id,
            titulo=titulo,
            itens=itens,
            desconto=self.spin_desconto.value(),
            forma_pagamento=self.cmb_pag.currentText(),
            observacoes=self.txt_obs.toPlainText(),
            user_id=self.current_user["id"],
            user_nome=self.current_user["nome"]
        )

        if ok:
            QMessageBox.information(self, "Sucesso", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", msg)


class BudgetWidget(QWidget):
    """Aba oficial de Orçamentos e Planos de Tratamento dentro da ficha do paciente."""
    def __init__(self, patient_id: int, current_user: dict, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.current_user = current_user
        self.init_ui()
        self.carregar_orcamentos()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Barra de Ações Superior
        top_bar = QHBoxLayout()
        lbl_tit = QLabel("Planos de Tratamento e Propostas de Orçamento")
        lbl_tit.setStyleSheet("font-size: 15px; font-weight: bold; color: #0f766e;")
        top_bar.addWidget(lbl_tit)
        top_bar.addStretch()

        btn_novo = QPushButton("+ Novo Orçamento")
        btn_novo.setStyleSheet("""
            QPushButton {
                background-color: #0f766e;
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                padding: 6px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #115e59;
            }
        """)
        btn_novo.clicked.connect(self.abrir_novo_orcamento)
        top_bar.addWidget(btn_novo)
        layout.addLayout(top_bar)

        # Tabela de Orçamentos
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Data", "Título do Plano", "Itens", "Valor Final", "Forma de Pagamento", "Situação"
        ])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setStyleSheet("""
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
        layout.addWidget(self.table)

        # Barra de Operações Inferior
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(8)

        btn_aprovar = QPushButton("Aprovar Orçamento")
        btn_aprovar.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: #ffffff;
                font-weight: bold;
                padding: 6px 14px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #047857;
            }
        """)
        btn_aprovar.clicked.connect(self.aprovar_selecionado)
        bottom_bar.addWidget(btn_aprovar)

        btn_recusar = QPushButton("Recusar / Cancelar")
        btn_recusar.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #b91c1c;
                border: 1px solid #fca5a5;
                font-weight: 500;
                padding: 6px 12px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #fee2e2;
            }
        """)
        btn_recusar.clicked.connect(self.recusar_selecionado)
        bottom_bar.addWidget(btn_recusar)

        btn_imprimir = QPushButton("Imprimir / Salvar PDF")
        btn_imprimir.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                font-weight: bold;
                padding: 6px 14px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        btn_imprimir.clicked.connect(self.imprimir_selecionado)
        bottom_bar.addWidget(btn_imprimir)

        bottom_bar.addStretch()

        btn_excluir = QPushButton("Excluir")
        btn_excluir.setStyleSheet("""
            QPushButton {
                background-color: #fee2e2;
                color: #991b1b;
                border: 1px solid #fca5a5;
                font-weight: 500;
                padding: 6px 12px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #fecaca;
            }
        """)
        btn_excluir.clicked.connect(self.excluir_selecionado)
        bottom_bar.addWidget(btn_excluir)

        layout.addLayout(bottom_bar)

    def carregar_orcamentos(self):
        orcamentos = list_budgets(self.patient_id)
        self.table.setRowCount(len(orcamentos))

        status_styles = {
            "Pendente": ("#fef3c7", "#b45309"),
            "Aprovado": ("#dcfce7", "#15803d"),
            "Recusado": ("#fee2e2", "#b91c1c"),
            "Concluído": ("#dbeafe", "#1d4ed8")
        }

        for r_idx, b in enumerate(orcamentos):
            # ID
            self.table.setItem(r_idx, 0, QTableWidgetItem(str(b["id"])))

            # Data
            item_data = QTableWidgetItem(b.get("data_criacao", "-"))
            item_data.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r_idx, 1, item_data)

            # Título
            item_tit = QTableWidgetItem(b.get("titulo", ""))
            item_tit.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table.setItem(r_idx, 2, item_tit)

            # Itens
            item_it = QTableWidgetItem(f"{b.get('total_itens', 0)} procedimento(s)")
            item_it.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r_idx, 3, item_it)

            # Valor Final
            val = b.get("valor_final", 0.0)
            item_val = QTableWidgetItem(f"R$ {val:,.2f}")
            item_val.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_val.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table.setItem(r_idx, 4, item_val)

            # Forma de Pagamento
            self.table.setItem(r_idx, 5, QTableWidgetItem(b.get("forma_pagamento", "A combinar")))

            # Situação
            st = b.get("status", "Pendente")
            bg_c, text_c = status_styles.get(st, ("#f1f5f9", "#475569"))
            lbl_badge = QLabel(f" {st} ")
            lbl_badge.setAlignment(Qt.AlignCenter)
            lbl_badge.setStyleSheet(f"""
                background-color: {bg_c};
                color: {text_c};
                font-weight: bold;
                font-size: 11px;
                border-radius: 4px;
                padding: 3px 6px;
            """)
            self.table.setCellWidget(r_idx, 6, lbl_badge)

    def get_selected_budget_id(self) -> Optional[int]:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um orçamento na tabela.")
            return None
        item_id = self.table.item(row, 0)
        return int(item_id.text()) if item_id else None

    def abrir_novo_orcamento(self):
        diag = BudgetFormDialog(self.patient_id, self.current_user, self)
        if diag.exec():
            self.carregar_orcamentos()

    def aprovar_selecionado(self):
        b_id = self.get_selected_budget_id()
        if not b_id:
            return

        box = QMessageBox(self)
        box.setWindowTitle("Aprovar Orçamento")
        box.setText("Deseja aprovar este orçamento?\n\nVocê também deseja lançar automaticamente os procedimentos propostos na evolução do prontuário?")
        btn_sim_pront = box.addButton("Aprovar e Lançar no Prontuário", QMessageBox.YesRole)
        btn_apenas_aprovar = box.addButton("Apenas Aprovar", QMessageBox.NoRole)
        btn_cancel = box.addButton("Cancelar", QMessageBox.RejectRole)

        box.exec()
        clicado = box.clickedButton()

        if clicado == btn_cancel:
            return

        lancar = (clicado == btn_sim_pront)
        ok, msg = aprovar_orcamento(b_id, lancar, self.current_user["id"], self.current_user["nome"])
        if ok:
            QMessageBox.information(self, "Sucesso", msg)
            self.carregar_orcamentos()
        else:
            QMessageBox.critical(self, "Erro", msg)

    def recusar_selecionado(self):
        b_id = self.get_selected_budget_id()
        if not b_id:
            return

        ok, msg = update_budget_status(b_id, "Recusado", self.current_user["id"], self.current_user["nome"])
        if ok:
            QMessageBox.information(self, "Atualizado", "Orçamento marcado como recusado.")
            self.carregar_orcamentos()
        else:
            QMessageBox.critical(self, "Erro", msg)

    def imprimir_selecionado(self):
        b_id = self.get_selected_budget_id()
        if not b_id:
            return

        html = gerar_html_orcamento(b_id)
        caminho_sugestao = f"Orcamento_{b_id}_LCR_Clinica.pdf"
        dest, _ = QFileDialog.getSaveFileName(self, "Salvar Orçamento em PDF", caminho_sugestao, "Documentos PDF (*.pdf)")
        if dest:
            ok = exportar_html_para_pdf(html, dest)
            if ok:
                QMessageBox.information(self, "PDF Gerado", f"Orçamento exportado com sucesso em:\n{dest}")
                import os
                try:
                    os.startfile(dest)
                except Exception:
                    pass
            else:
                QMessageBox.critical(self, "Erro", "Falha ao gerar arquivo PDF do orçamento.")

    def excluir_selecionado(self):
        b_id = self.get_selected_budget_id()
        if not b_id:
            return

        resp = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            "Tem certeza que deseja excluir permanentemente este orçamento?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            ok, msg = delete_budget(b_id, self.current_user["id"], self.current_user["nome"])
            if ok:
                self.carregar_orcamentos()
            else:
                QMessageBox.critical(self, "Erro", msg)
